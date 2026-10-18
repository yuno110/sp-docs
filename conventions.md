---
title: 코드 컨벤션
type: spec
status: rule
version: v22
updated: 2026-10-18
read_when: "코드를 작성하거나 리뷰할 때. 패키지를 새로 만들 때"
related: [tech-stack.md, adr/0007-shared-code-policy.md, process/dev-workflow.md]
---
# 코드 컨벤션

## 1. 패키지 구조

**CORS는 `WebConfig`가 아니라 `SecurityConfig`에 둔다.** MVC 쪽에만 두면 preflight(`OPTIONS`)가 인가 필터에 401로 막힌다([security.md §1.1](security.md)). `WebConfig`는 ArgumentResolver 등록만 한다.

`support`는 **도메인 조회 보조**다. "없으면 예외를 던지는 조회"(`AccountReader`·`MemberReader`)처럼 여러 서비스 클래스가 같은 방식으로 쓰는 것을 둔다. 기반 단계가 만들고 기능 단계는 읽기만 한다([plan/phase1.md](plan/phase1.md) §2.1).

도메인형으로 나눈다. 계층형(controller/service/repository를 최상위로)으로 두지 않는다.

### 1.1 auth-service

```
com.example.auth
├── AuthApplication.java
├── global
│   ├── config          # SecurityConfig(인가·CORS), JpaConfig, SwaggerConfig, WebConfig(ArgumentResolver)
│   ├── common          # BaseTimeEntity, ApiResponse, PageResponse
│   ├── error           # ErrorCode, BusinessException, GlobalExceptionHandler
│   └── security        # JwtTokenProvider(서명), LoginAccount(record), @CurrentAccount
├── auth
│   ├── controller / service / repository / entity / dto   # 로그인·재발급·로그아웃, RefreshToken
└── account
    └── controller / service / repository / entity / dto / support   # 계정 생성·조회·비밀번호·탈퇴
```

**`auth`와 `account` 사이에 단방향 제약을 두지 않는다.** 비밀번호 변경·계정 탈퇴가 `account` 갱신과 `RefreshToken` 삭제를 **한 로컬 트랜잭션**으로 묶어야 하기 때문이다. 이전 `adr/0006 §예외`가 우회로 다루던 문제가 같은 서비스 안으로 들어오면서 사라졌다([adr/0012](adr/0012-auth-as-separate-service.md)).

**이 서비스만 개인키를 갖는다.** 서명은 Spring Security 표준(`NimbusJwtEncoder`)을 쓴다. 직접 서명 로직을 만들지 않는다.

### 1.2 member-service

```
com.example.member
├── MemberApplication.java
├── global
│   ├── config          # SecurityConfig(인가·CORS), JpaConfig, SwaggerConfig, WebConfig(ArgumentResolver)
│   ├── common          # BaseTimeEntity, ApiResponse, PageResponse
│   ├── error           # ErrorCode, BusinessException, GlobalExceptionHandler
│   └── security        # RoleClaimConverter, LoginMember(record), @CurrentMember
├── member
│   ├── controller / service / repository / entity / dto / support
└── internal
    └── controller / service / dto   # InternalMemberController (/internal/v1/**)
```

**`auth` 패키지가 없다.** 계정·인증은 auth-service로 옮겨갔다. member는 **공개키로 검증만** 한다 — 서명 의존성을 넣지 않는다([tech-stack.md §3.2](tech-stack.md)).

`LoginMember`는 `(accountId, role)`이다. **`nickname`은 없다** — JWT Claim에 없기 때문이다([api-contract.md §6](api-contract.md)).

### 1.3 board-service

```
com.example.board
├── BoardApplication.java
├── global
│   ├── config          # SecurityConfig(인가·CORS), JpaConfig, QuerydslConfig, SwaggerConfig, WebConfig
│   ├── common          # BaseTimeEntity, ApiResponse, PageResponse
│   ├── error           # ErrorCode, BusinessException, GlobalExceptionHandler
│   └── security        # RoleClaimConverter, LoginMember(record), @CurrentMember
├── post
│   ├── controller / service / repository / entity / dto / support
├── comment
│   ├── controller / service / repository / entity / dto
└── client
    └── MemberClient    # 내부 API 호출 (1차. 글·댓글 생성 경로)
```

**`post`와 `comment` 사이에 단방향 제약을 두지 않는다.** §1.1이 `auth`와 `account`에 같은 면제를 둔 것과 같은 이유다 — **한 로컬 트랜잭션이 두 패키지를 걸친다.** [domain-model.md §5](domain-model.md)가 둘을 요구한다: 게시글 삭제는 `post.deleted`와 하위 댓글 `deleted`를, 댓글 작성은 댓글 INSERT와 `post.comment_count`를 각각 **한 트랜잭션**으로 묶는다. 방향을 끊으려면 그 원자성을 깨거나 두 패키지를 합쳐야 한다.

| 쓰는 쪽 | 참조 | 쓰임 |
| --- | --- | --- |
| `post.service` | `comment.repository.CommentRepository` | 게시글 삭제의 댓글 연쇄 (B-07) |
| `comment.*` | `post.entity.Post`, `post.support.PostReader` | 연관관계 매핑, 게시글 존재 판정 (B-03·B-08) |
| `comment.service` | `post.repository.PostRepository` | **`comment_count` 의 좁은 UPDATE** (B-10) |

**면제는 이 세 줄까지다.** 서로의 **Service**를 참조하지 않는다 — 업무 규칙이 두 곳으로 갈리고 트랜잭션 경계가 어느 쪽 것인지 흐려진다. 게시글 존재 판정은 `PostReader` 한 곳이고([plan/phase1.md §2.5](plan/phase1.md)의 공유 지점), 댓글 연쇄 삭제는 `CommentRepository`의 벌크 UPDATE 한 곳이다.

> **셋째 줄은 B-10이 만들었다.** `comment_count` 갱신이 엔티티 메서드에서 **좁은 UPDATE**로 바뀌면서(소실 갱신 때문이다 — [plan/phase1.md](plan/phase1.md) B-10) 그 문장이 `PostRepository`에 선언됐다. **`CommentRepository`에 두지 않은 이유**는 그 문장이 바꾸는 테이블이 `post`라서다 — `comment` 쪽에 숨기면 `PostRepository`를 읽는 사람이 `comment_count`가 어디서도 바뀌지 않는다고 결론한다. 방향은 첫 줄과 같은 모양이고 금지된 **Service 상호 참조는 아니다.**

`LoginMember`는 `(accountId, role)`이다. **`nickname`은 없다.** 작성자 닉네임은 `MemberClient`로 얻는다.

**`MemberClient`는 1차 범위다.** JWT Claim에 닉네임이 없으므로 다른 취득 경로가 없다([adr/0012](adr/0012-auth-as-separate-service.md) §6). 호출·실패 판정 규칙은 [api-contract.md §5.1](api-contract.md)이 정본이다.

- 응답 DTO는 board가 자체 정의한다(§3)
- 호출은 **`@Transactional` 밖에서 먼저** 한다(§5)
- 생성 경로에서만 호출한다. 조회·수정·삭제 경로에서는 호출하지 않는다

## 2. Entity

- 기본 생성자는 `@NoArgsConstructor(access = AccessLevel.PROTECTED)`
- 생성은 `@Builder`
- **`@Data`, `@Setter`, 연관관계를 포함한 `@ToString` 금지.** 무한 루프와 의도치 않은 변경을 막기 위해서다
- `equals`/`hashCode`는 `id` 기준으로 직접 구현한다
- 도메인 로직은 Entity 메서드로 둔다 (`post.update(...)`, `member.updateNickname(...)`)
- Enum은 `@Enumerated(EnumType.STRING)`

## 3. DTO

- `record`를 우선 사용한다
- **Entity를 Controller 밖으로 노출하지 않는다.** 반드시 DTO로 변환한다
- 원격 호출 결과 DTO는 소비 서비스가 자체 정의한다. 제공 서비스의 DTO 클래스를 공유하지 않는다

## 4. 의존성 주입

생성자 주입만 사용한다.

```java
@Service
@RequiredArgsConstructor
public class PostService {
    private final PostRepository postRepository;
}
```

필드 주입(`@Autowired` 필드), 세터 주입 금지.

## 5. 트랜잭션

- 경계는 Service에 둔다. Controller·Repository에 `@Transactional`을 붙이지 않는다
- 조회는 `@Transactional(readOnly = true)`
- **트랜잭션 안에서 다른 서비스를 호출하지 않는다**([architecture.md §5](architecture.md))

## 6. 예외 처리

- `BusinessException(ErrorCode)`를 던진다
- `@RestControllerAdvice`의 `GlobalExceptionHandler`에서 일괄 변환한다
- 에러 코드는 [api-contract.md §8](api-contract.md)이 정본이다. 코드를 추가하려면 그 문서를 먼저 개정한다
- 응답에 스택트레이스·SQL·내부 호스트명을 넣지 않는다

### 6.1 어느 예외가 어느 코드가 되는지

**`ResponseEntityExceptionHandler`를 상속하지 않는다.** 상속하면 응답 본문이 Spring의 `ProblemDetail` 모양이 되어 [api-contract.md §7](api-contract.md)의 `ApiResponse`와 달라진다. 대신 **다룰 예외를 전부 명시한다** — 빠뜨린 것은 마지막 그물(`Exception`)로 떨어져 **500이 되고 `log.error`를 남긴다.**

| 예외 | 코드 | |
| --- | --- | --- |
| `BusinessException` | 그 코드 그대로 | |
| `MethodArgumentNotValidException` | `C001` | `fieldErrors` 1건 이상 |
| `HandlerMethodValidationException` | `C001` | `fieldErrors` 1건 이상 |
| `MissingServletRequestParameterException` | `C001` | **`fieldErrors` 빈 배열** — 바인딩이 일어나지 않았다([api-contract.md §2.3](api-contract.md)) |
| `HttpMessageNotReadableException` | `C001` | 같음 |
| `MethodArgumentTypeMismatchException` | `C002` | |
| `HttpRequestMethodNotSupportedException` | `C003` | |
| `NoResourceFoundException` | `C004` | |
| `HttpMediaTypeNotSupportedException` | `C006` | |
| `HttpMediaTypeNotAcceptableException` | `C007` | **응답의 `Content-Type`을 `application/json`으로 못박는다** — 안 하면 핸들러 자신의 응답이 같은 협상에 걸려 본문이 빈다 |
| `Exception` | `C005` | 마지막 그물 |

**세 서비스가 이 표를 똑같이 구현한다.** 다만 **클래스 자체는 복제 대상이 아니다**(§7.2) — 서비스별 `ErrorCode`에 의존하므로 각자 쓴다. 같아야 하는 것은 **핸들러 집합·코드·로그 수준·응답 본문**이고, 그 일치를 [plan/integration.md](plan/integration.md) I-04가 3자 비교한다. **표를 먼저 고치지 않고 한 서비스만 늘리지 않는다.**

**로그 수준을 가른다.** 클라이언트 오류는 `warn`, **마지막 그물만 `error`**다. 흔한 클라이언트 실수가 ERROR 경보를 만들면 원인이 서버에 있는 500과 구별되지 않는다([../AGENTS.md](AGENTS.md) 불변식 9).

**양쪽을 다 단언한다.** 클라이언트 오류가 `error`가 아닌 것만 보면 **반대 방향이 열린다** — 마지막 그물을 `warn`으로 낮추면 500이 ERROR 경보를 전혀 만들지 않게 되고, 그것이 더 나쁘다. M-02 리뷰에서 그 변이가 잡히지 않는 것이 측정됐다.

> **`S001`의 경보는 이 두 극 **바깥**에 있고 어느 테스트도 묶지 않는다.** [api-contract.md §5.1](api-contract.md)이 member 호출 실패를 "인프라 오류. 경보 대상"으로 정했는데, `S001`은 **5xx인 `BusinessException`**이라 "클라이언트 오류는 `warn`"에도 "마지막 그물만 `error`"에도 속하지 않는다. 실제로 ERROR를 내는 것은 **호출 지점**(board의 `MemberClient`)이고 핸들러는 다른 `BusinessException`과 같이 `warn`을 남긴다 — **핸들러가 원인을 알 수 없으므로 그 설계가 맞다.** 코드별 분기를 핸들러에 넣으면 세 서비스를 같게 두라는 이 절과 반대 방향이 된다.
>
> **공백은 그 ERROR를 요구하는 완료 기준·검증표가 없다는 것이다**(I-02 리뷰 실측). 호출 지점의 `log.error`를 `warn`으로 낮추면 `S001`의 경보가 조용히 사라지는데 board 스위트에서 빨개지는 것이 **하나도 없다**. **I-04가 이것을 닫아 주지 않는다** — 세 서비스의 `handleBusinessException`이 로그 수준까지 동일하므로 3자 비교를 통과하고, I-04가 보는 것은 위 두 극뿐이다. 닫으려면 **호출 지점의 ERROR를 요구하는 줄이 board 쪽 항목에 있어야 한다.**

> **auth는 동작은 맞지만 그 단언이 없다.** `log.error`를 쓰고 있으나 `log.warn`으로 바꾸는 변이를 잡는 테스트가 없다. auth의 1차 항목이 모두 끝났으므로 지금 고치지 않고, **[plan/integration.md](plan/integration.md) I-04가 세 서비스의 로그 수준을 비교하는 것으로 그 공백을 받는다** — 거기가 auth에 대한 유일한 게이트다. `GlobalExceptionHandler`를 다음에 손대는 사람이 단언을 더하면 그때 닫힌다.

> **`A001`·`A002`·`A003`은 이 표에 없다.** 인증 실패는 `GlobalExceptionHandler`에 닿기 전에 Security 필터 체인이 처리하므로, `AuthenticationEntryPoint`·`AccessDeniedHandler`가 낸다([api-contract.md §8.5](api-contract.md)의 경계). 보안 기반 항목(AU-04·M-04·B-04)의 몫이다.

## 7. 공통 코드 정책

세 서비스가 같은 코드를 갖는 것은 **복제**로 처리한다. 공용 라이브러리 모듈을 만들지 않는다. 근거와 재검토 조건은 [adr/0007](adr/0007-shared-code-policy.md)에 있다.

> 0007의 재검토 조건("서비스가 3개째가 될 때")은 auth 분리로 **이미 발동했고, 재검토 결과 복제를 유지하기로 했다.** 결론은 0007에 기록되어 있다. 복제본이 3벌이 되므로 형식 일치 확인이 2자 비교에서 3자 비교가 된다([plan/integration.md](plan/integration.md) I-04).

### 7.1 복제 대상 (약 75줄)

| 항목 | 정본 |
| --- | --- |
| `ApiResponse`, `ErrorResponse` | [api-contract.md §7](api-contract.md) |
| `PageResponse` | [api-contract.md §7.1](api-contract.md) |
| `BaseTimeEntity` | [domain-model.md §1.1](domain-model.md) |
| `BusinessException` | 이 문서 §6 |

복제본 파일 상단에 정본 위치를 주석으로 남긴다.

```java
// 정본: sp-docs/api-contract.md §7
// 변경 시 세 서비스를 함께 고친다.
public record ApiResponse<T>(boolean success, T data, ErrorResponse error) { }
```

### 7.2 복제하지 않는 것

- `ErrorCode` enum — 서비스마다 코드가 다르다. 공유하면 board 코드가 member에 들어간다
- `GlobalExceptionHandler` — 서비스별 `ErrorCode`에 의존한다. **다루는 예외 집합과 코드 매핑은 §6.1이 고정한다** — 파일은 각자 쓰지만 동작은 같아야 한다
- **JWT 검증·발급 코드** — 직접 만들지 않고 Spring 표준을 쓴다([tech-stack.md §2](tech-stack.md))

## 8. 로깅

- 비밀번호·토큰·개인키를 로그에 남기지 않는다
- 로컬 프로파일만 SQL 로그를 켠다. 운영은 끈다

## 9. 테스트

- 테스트 클래스명은 `<대상>Test`
- 메서드명은 한글 또는 `should_...` 형식으로 무엇을 검증하는지 드러낸다
- 작성 시점과 검증 절차는 [process/dev-workflow.md](process/dev-workflow.md)를 따른다

### 9.1 `@WebMvcTest`는 대상을 지정한다

**`@WebMvcTest(controllers = XxxController.class)`로 좁힌다.** 인자를 비우면 모든 `@Controller`를 올리면서 그 의존(`@Service`)은 올리지 않으므로, **나중에 컨트롤러가 하나 추가될 때마다 기존 테스트가 기동에 실패한다.**

기능 단계가 컨트롤러를 차례로 추가하는 구조([plan/phase1.md](plan/phase1.md) §1.1)에서 이 결함은 반드시 터진다. 처음부터 좁혀 둔다.

### 9.2 길이 제약이 있는 컬럼은 실제 최대 길이로 테스트한다

**짧은 더미로 저장만 확인하면 길이 제약을 못 잡는다.**

`refresh_token.token`이 그랬다. AU-03의 리포지토리 테스트가 `"old.refresh.token"` 같은 17자 문자열로 저장·조회를 확인해 통과했지만, **실제 발급 토큰이 들어가는 첫 지점인 AU-06에서 541자가 512자 컬럼에 막혔다.** 결함은 AU-03에 있었고 발견은 세 항목 뒤였다.

| 컬럼 성격 | 픽스처 |
| --- | --- |
| 길이 제약이 **의미를 갖는** 것 (토큰, 해시, 본문) | **실제로 들어갈 최대 길이**의 값 |
| 길이가 넉넉한 것 (이메일, 닉네임) | 읽기 쉬운 값 + 경계 케이스 별도 테스트 |

**생성 규칙이 있는 값은 그 규칙으로 만든다.** 토큰이면 실제 발급 경로로, 해시면 실제 인코더로. 리터럴을 길게 늘여 적는 것보다 낫다 — 규칙이 바뀌면 함께 바뀐다.

**예외 — 서로 다른 값이 필요할 때는 발급 경로를 쓸 수 없다.** JWT Claim에 `jti`가 없고 `iat`가 초 단위이므로([api-contract.md §6](api-contract.md)), **같은 계정의 두 발급이 같은 초에 일어나면 토큰 문자열이 완전히 같다.**

| 픽스처 용도 | 만드는 법 |
| --- | --- |
| 길이·형식이 중요한 값 1개 | **실제 발급 경로** |
| **서로 달라야 하는 값 2개 이상** (UNIQUE 충돌, 회전 전후 비교) | 같은 문자 집합·모양으로 **조립한다.** 조립한 것임을 주석에 적는다 |

후자를 발급 경로로 만들려고 `Thread.sleep(1000)`을 넣지 않는다. 테스트가 느려지고, 초 경계에 걸리면 여전히 같아진다.

**DTO 의 길이 상한은 유효한 쪽에서도 본다.** 초과 입력이 400 인 것만 보면 **상한을 내리는 어긋남이 조용하다** — 댓글 `content` 의 `500` 을 `499` 로 내려도 B-08 의 테스트가 **전부 통과했다**(실측). 정확히 최대 길이인 입력이 **성공**하는 테스트가 그것을 잡는다. B-05 가 "제목 200자·내용 10,000자는 201 이다" 로 그 자리를 덮었고 B-08 은 비어 있었다.

> **컬럼 폭 테스트가 그것을 대신하지 않는다.** B-03 의 리포지터리 테스트가 500자 댓글을 저장하는 것은 컬럼 폭 검증이고 **DTO 제약과 다른 지점이다.** 둘이 어긋나면 폭은 맞는데 요청이 거부된다 — 거부가 400 이라 정상 응답처럼 보이고, 경계 입력을 넣어 보지 않으면 드러나지 않는다.
>
> **상수를 두 경로가 공유하면 한 경로만 보는 테스트로 부족하다.** 작성과 수정이 같은 상수를 쓰면 상한을 내리는 어긋남이 **두 경로에 동시에 번지므로**, 두 경로 각각에서 경계 입력이 성공하는지 본다.
>
> **하한도 같다. 상한만 생각하기 쉬운 자리다.** 위반하는 쪽(`size=0` → 400)만 보면 **하한을 올리는 어긋남이 조용하다** — `MIN_SIZE` 를 1 에서 2 로 올려도 `size=0` 은 여전히 400 이므로 B-09 의 테스트 263개가 **전부 통과했다**(실측). 정본 하한인 값이 **성공하는** 단언이 있어야 한다. 경계는 **양쪽**이다: 하한 값은 성공하고 하한 미달은 거부되어야 한다.

### 9.3 `@DataJpaTest`의 두 애노테이션

`@AutoConfigureTestDatabase(replace = NONE)`와 `@Import(JpaConfig.class)`다. 전자가 없으면 DataSource URL이 덮이고([tech-stack.md §5.2](tech-stack.md)), 후자가 없으면 감사 컬럼이 NULL로 들어간다([domain-model.md §1.1](domain-model.md)).

| 애노테이션 | 필요한 범위 |
| --- | --- |
| `@AutoConfigureTestDatabase(replace = NONE)` | **모든 `@DataJpaTest`** — URL 덮임은 엔티티를 저장하지 않아도 일어난다 |
| `@Import(JpaConfig.class)` | **엔티티를 저장하는** `@DataJpaTest` — `@EnableJpaAuditing`이 거기 있다 |

**후자를 조건 없이 요구하지 않는다.** DataSource·메타데이터만 읽는 테스트에는 감사가 쓰이지 않으므로, 이유가 적용되지 않는 규칙을 붙이는 것이 된다. 저장하는 테스트에서 빠뜨리면 `created_at NOT NULL`이 깨져 **시끄럽게 실패한다** — 조용히 지나가지 않는다.

### 9.4 코드 주석에 정본의 **버전**을 적지 않는다

주소는 **절 번호**로만 적는다. `(sp-docs/api-contract.md §2.2)` 는 좋고 `(… §2.2 v11)` 은 안 된다.

**정본 버전은 자주 오른다.** `api-contract.md`는 AU-08·AU-09 두 항목에서만 v7 → v12로 다섯 번 올랐다. 코드에 박은 버전은 그때마다 낡고, **낡은 핀은 핀이 없는 것보다 나쁘다** — "이 버전과 대조했다"고 주장하면서 그 버전이 더 이상 없다.

AU-09 리뷰에서 27곳을 전부 열어 측정한 결과다.

| | |
| --- | --- |
| 장식이었다 (지워도 문장이 그대로 성립) | **26곳** |
| 버전이 실제로 일을 했다 | **1곳** — 그리고 **그 한 곳이 거짓 진술이 됐다** |

그 한 곳은 번호를 주소가 아니라 **내용에 대한 수량 주장**으로 썼다 — "§2.2 v11의 표는 둘만 정한다". 표가 네 행이 되자 주석이 거짓이 됐다. **버전을 적어 이득을 본 사례가 0이고 손해를 본 사례가 1이다.**

**"언제 기준으로 쓴 주석인가"는 `git blame`이 답한다.** `git log -L<줄>,<줄>:<파일>`로 그 줄의 커밋을 얻고, 그 날짜로 정본 쪽 상태를 복원한다. blame은 틀릴 수 없고 유지비가 0이다. 손으로 적은 핀은 틀릴 수 있고, 걸러 줄 기계장치도 없다.

### 9.5 주석에 수량·유일성을 주장하지 않는다

**정본에 대해서도, 코드에 대해서도 쓰지 않는다.** 둘 다 다음 항목이 늘린다.

| 쓰지 않는다 | 왜 거짓이 되나 | 대신 |
| --- | --- | --- |
| "표는 **둘만** 정한다" | 정본의 표에 행이 늘었다 | "표가 이 입력을 404로 정한다" |
| "**유일한** 사용처는 …다" | 다음 항목이 두 번째 호출처를 만들었다 | "이 헬퍼를 쓰는 쪽은 … 를 전제한다" |
| "코드는 **넷이다**", "이 셋이 전부다" | 어느 쪽이든 늘어난다 | 성질·조건을 적는다 |

**실제로 셋 다 거짓이 됐다.** AU-08의 "표는 둘만 정한다"가 AU-09의 정본 개정으로, AU-09의 "유일한 사용처"가 AU-10의 새 테스트로 거짓이 됐다. 수량은 **쓴 순간 다음 항목에 대한 예측**이 되고, 그 예측을 지킬 사람이 없다.

**이 절은 "다른 어딘가에 몇 개 있는가"를 겨냥한다.** 호출처 수, 정본의 행 수, 항목 번호 — 다음 항목이 늘리는 것들이다. **당면한 논리의 경우를 열거하는 것은 해당하지 않는다** — "0행이 나오는 경우는 둘이다(행이 없거나 토큰이 다름)" 처럼 구성상 완전한 열거는 다음 항목이 바꿀 수 없다. 정본이 적은 사실을 그대로 인용하는 것도 아니다 — "`deleted_at` 이 없어 `updated_at` 이 탈퇴 시점의 유일한 흔적이다" 는 스키마에 대한 진술이고 정본이 알려진 한계로 기록한 것이다.

**근거를 적을 때는 그 자리에서 실제로 구속하는 것을 적는다.** 그럴듯하지만 그 자리에서 일하지 않는 이유는 수량 주장과 같은 종류의 부채다 — 읽는 사람이 그것을 믿고 고치면 테스트가 조용히 무의미해진다.

## 10. 커밋

메시지

```
<type>(<scope>): <요약>
```

- `type`: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`
- `scope`: `member`, `auth`, `post`, `comment`, `global`, `docs`
- 본문에는 무엇을 왜 바꿨는지 적는다. 비밀 값·개인정보를 넣지 않는다

예: `feat(post): 게시글 목록 QueryDSL 동적 검색 추가`
