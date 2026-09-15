---
title: 코드 컨벤션
type: spec
status: rule
version: v2
updated: 2026-09-15
read_when: "코드를 작성하거나 리뷰할 때. 패키지를 새로 만들 때"
related: [tech-stack.md, adr/0007-shared-code-policy.md, process/dev-workflow.md]
---
# 코드 컨벤션

## 1. 패키지 구조

도메인형으로 나눈다. 계층형(controller/service/repository를 최상위로)으로 두지 않는다.

### 1.1 auth-service

```
com.example.auth
├── AuthApplication.java
├── global
│   ├── config          # SecurityConfig, JpaConfig, SwaggerConfig, WebConfig(CORS)
│   ├── common          # BaseTimeEntity, ApiResponse, PageResponse
│   ├── error           # ErrorCode, BusinessException, GlobalExceptionHandler
│   └── security        # JwtTokenProvider(서명), LoginAccount(record), @CurrentAccount
├── auth
│   ├── controller / service / repository / entity / dto   # 로그인·재발급·로그아웃, RefreshToken
└── account
    └── controller / service / repository / entity / dto   # 계정 생성·조회·비밀번호·탈퇴
```

**`auth`와 `account` 사이에 단방향 제약을 두지 않는다.** 비밀번호 변경·계정 탈퇴가 `account` 갱신과 `RefreshToken` 삭제를 **한 로컬 트랜잭션**으로 묶어야 하기 때문이다. 이전 `adr/0006 §예외`가 우회로 다루던 문제가 같은 서비스 안으로 들어오면서 사라졌다([adr/0012](adr/0012-auth-as-separate-service.md)).

**이 서비스만 개인키를 갖는다.** 서명은 Spring Security 표준(`NimbusJwtEncoder`)을 쓴다. 직접 서명 로직을 만들지 않는다.

### 1.2 member-service

```
com.example.member
├── MemberApplication.java
├── global
│   ├── config          # SecurityConfig, JpaConfig, SwaggerConfig, WebConfig(CORS)
│   ├── common          # BaseTimeEntity, ApiResponse, PageResponse
│   ├── error           # ErrorCode, BusinessException, GlobalExceptionHandler
│   └── security        # RoleClaimConverter, LoginMember(record), @CurrentMember
├── member
│   ├── controller / service / repository / entity / dto
└── internal
    └── controller      # InternalMemberController (/internal/v1/**)
```

**`auth` 패키지가 없다.** 계정·인증은 auth-service로 옮겨갔다. member는 **공개키로 검증만** 한다 — 서명 의존성을 넣지 않는다([tech-stack.md §3.2](tech-stack.md)).

`LoginMember`는 `(accountId, role)`이다. **`nickname`은 없다** — JWT Claim에 없기 때문이다([api-contract.md §6](api-contract.md)).

### 1.3 board-service

```
com.example.board
├── BoardApplication.java
├── global
│   ├── config          # SecurityConfig, JpaConfig, QuerydslConfig, SwaggerConfig, WebConfig
│   ├── common          # BaseTimeEntity, ApiResponse, PageResponse
│   ├── error           # ErrorCode, BusinessException, GlobalExceptionHandler
│   └── security        # RoleClaimConverter, LoginMember(record), @CurrentMember
├── post
│   ├── controller / service / repository / entity / dto
├── comment
│   ├── controller / service / repository / entity / dto
└── client
    └── MemberClient    # 내부 API 호출 (1차. 글·댓글 생성 경로)
```

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
- 도메인 로직은 Entity 메서드로 둔다 (`post.update(...)`, `member.changePassword(...)`)
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
- `GlobalExceptionHandler` — 서비스별 `ErrorCode`에 의존한다
- **JWT 검증·발급 코드** — 직접 만들지 않고 Spring 표준을 쓴다([tech-stack.md §2](tech-stack.md))

## 8. 로깅

- 비밀번호·토큰·개인키를 로그에 남기지 않는다
- 로컬 프로파일만 SQL 로그를 켠다. 운영은 끈다

## 9. 테스트

- 테스트 클래스명은 `<대상>Test`
- 메서드명은 한글 또는 `should_...` 형식으로 무엇을 검증하는지 드러낸다
- 작성 시점과 검증 절차는 [process/dev-workflow.md](process/dev-workflow.md)를 따른다

## 10. 커밋

```
<type>(<scope>): <요약>
```

- `type`: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`
- `scope`: `member`, `auth`, `post`, `comment`, `global`, `docs`
- 본문에는 무엇을 왜 바꿨는지 적는다. 비밀 값·개인정보를 넣지 않는다

예: `feat(post): 게시글 목록 QueryDSL 동적 검색 추가`
