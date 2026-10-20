---
title: 보안 설계
type: explanation
status: living
version: v17
updated: 2026-10-20
read_when: "인증·인가를 구현하거나, JWT 키를 다루거나, 권한 검증 위치를 정할 때"
related: [api-contract.md, adr/0004-rs256-over-hs256.md, tech-stack.md]
---
# 보안 설계

## 1. 공통 방침

| 항목 | 방침 |
| --- | --- |
| 비밀번호 저장 | BCrypt (`strength = 10`). **auth-service만 취급** |
| 인증 방식 | JWT Bearer Token, Stateless (`SessionCreationPolicy.STATELESS`) |
| Access Token | 만료 30분. `Authorization: Bearer {token}` |
| Refresh Token | 만료 14일. **`sp_auth` 저장**, 재발급 시 회전(Rotation) |
| CSRF | Stateless REST API이므로 비활성화 |
| CORS | 허용 오리진은 **환경이 정한다**(§1.1). 메서드·헤더·credentials는 §1.1이 고정한다. `*` 금지 |
| SQL Injection | JPA·QueryDSL 파라미터 바인딩. 네이티브 쿼리 문자열 결합 금지 |
| XSS | 서버는 원문 저장, 출력 이스케이프는 클라이언트 책임 |
| 민감정보 로깅 | 비밀번호·토큰·키를 로그에 남기지 않음. **운영 프로파일의 통제다** — 로컬은 §1.2 가 예외와 조건을 적는다 |

### 1.2 로컬 프로파일의 예외 — 바인드 로그에 비밀번호 해시가 남는다

**통제는 운영을 말한다. 로컬에는 알려진 예외가 하나 있다 — D-03 이 그렇게 정했다(2026-10-18).**

세 저장소의 커밋된 템플릿 `application-local.yml.example` 이 `org.hibernate.orm.jdbc.bind: trace` 를 켠다([conventions.md §8](conventions.md)이 로컬에서 SQL 로그를 켜라고 적는다). 그래서 **auth 의 `account` 에 쓰기가 일어날 때마다 저장된 BCrypt 해시가 로컬 로그에 찍힌다**(I-05 실측: 한 세션에 4건). member·board 에는 비밀 컬럼이 없어 해당하지 않는다.

**운영은 영향이 없다.** `application-prod.yml` 이 세 저장소 모두 `org.hibernate.SQL: warn` 과 `org.hibernate.orm.jdbc.bind: warn` 이다(실측). **평문 비밀번호는 어느 프로파일에서도 남지 않는다** — 바인드 파라미터에 실리는 것은 이미 인코딩된 해시다.

**로컬을 끄지 않는 이유는 그 로거가 학습 수단이기 때문이다.** 끄면 로컬에서 SQL 파라미터를 볼 수 없다. 대신 조건을 둔다.

- **로컬 로그를 공유·업로드·커밋하지 않는다.** 저장소에 로그 파일을 만들지 않는다([conventions.md §8](conventions.md))
- 로그를 보고서나 이슈에 인용할 때 **BCrypt 모양 문자열(`$2[aby]$…`)을 지운다.** I-05 워커가 그렇게 했고 독립 `grep` 으로 0건을 확인했다 — **패턴의 양성 대조를 먼저 세운다**(`$` 가 cost 뒤에 또 오므로 문자 클래스에 `$` 를 넣지 않으면 거짓 0 이 나온다. I-05 리뷰 실측)
- **커밋되는 파일에는 어떤 프로파일에서도 그 모양을 넣지 않는다**

> **이 결정을 관측하는 수단이 없다.** `.example` 은 실행되지 않는 파일이고 `application-local.yml` 은 gitignore 되어 있어, 로거 수준을 되돌리는 변이를 잡는 테스트가 세 저장소에 없다. **그래서 이 절이 그 자리를 대신한다** — 다음 사람이 로컬 로그에서 해시를 보고 결함으로 올리지 않게, 그리고 **운영에서 그 로거를 켜는 것이 통제 위반임을** 알게 한다.

### 1.1 CORS — 무엇을 정본이 정하고 무엇을 환경이 정하는가

| 항목 | 누가 정하는가 | 값 |
| --- | --- | --- |
| 허용 오리진 | **환경** | `cors.allowed-origins`로 **기본값 없이** 주입한다. 비었거나 `*`가 섞이면 **기동을 실패시킨다** |
| 허용 메서드 | **정본** | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` ([api-contract.md §2~§4](api-contract.md)의 합집합) |
| 허용 헤더 | **정본** | `Authorization`, `Content-Type` |
| `allowCredentials` | **정본** | `false`. 토큰을 `Authorization` 헤더로 보내므로 쿠키가 필요 없다 |

> **`PUT` 이 빠져 있었다. B-04 구현 워커가 찾았다.** 목록이 "§2~§4 에서 도출" 이라고 적혀 있었지만 auth·member 만 보고 만들어졌다 — 수정 경로가 member 는 `PATCH`(§3)인데 **board 는 `PUT`**(§4 의 `PUT /api/v1/posts/{id}`·`PUT /api/v1/comments/{id}`)이다. 그대로였다면 브라우저 클라이언트의 게시글·댓글 수정 preflight 가 막혔다. 1차에 프론트엔드가 없어 당장 드러나지 않는 종류다.
>
> **그 "드러나지 않는다" 가 이제는 성립하지 않는다 — 다만 위 문장이 거짓이 된 것은 아니다.** 그 문장은 **"1차에"** 로 시점을 묶었고 1차는 끝났으므로 과거 진술로 참이다. 바뀐 것은 **앞으로**다: 2026-10-20 에 생긴 프론트엔드가 `PUT /api/v1/posts/{id}` 와 `PUT /api/v1/comments/{id}` 를 **실제로 호출한다**(`sp-frontend` 의 board 호출부 — 글 수정과 댓글 수정). 같은 결함이 지금 남아 있었다면 **브라우저에서 바로 드러난다.** 이 자리를 적어 두는 이유는 "관측 수단이 없다" 가 더는 이 경로의 변명이 될 수 없다는 것이다.
>
> **auth·member 는 넷을 단언한 상태로 완료됐다.** 둘에는 `PUT` 엔드포인트가 없으므로 실질 피해가 없어 다시 열지 않는다. **board 는 이 다섯을 쓴다.**
>
> **세 서비스의 CORS 를 비교하는 통합 항목이 없다.** [plan/integration.md](plan/integration.md) I-04 는 **응답 형식**(`ApiResponse` 구조·공통 코드)만 보고 I-01·I-02·I-03·I-05 도 CORS 를 다루지 않는다. 그래서 이 값의 어긋남을 지키는 것은 **각 서비스의 보안 기반 항목(AU-04·M-04·B-04) 테스트뿐**이다 — 한 서비스만 고치면 아무것도 깨지지 않는다는 뜻이고, 이 결함이 그렇게 살아남았다.

**오리진 목록을 정본에 박지 않는다.** 오리진은 배포 환경이 정하는 값이고, 정본이 특정 호스트·포트를 들고 있으면 환경이 바뀔 때마다 계약 문서를 고쳐야 한다.

> **앞 판은 근거를 "이 프로젝트는 프론트엔드가 없는 JSON API이므로 지금 값을 정하면 없는 클라이언트를 상상해 만드는 것이 된다" 로 적었다. 그 근거가 2026-10-20 에 거짓이 됐다** — 프론트엔드 `yuno110/sp-frontend` 가 생겼다([overview.md §3.3](overview.md)). **규칙은 바뀌지 않고 이유만 바뀐다.** 클라이언트가 실재하는 지금도 그 오리진은 환경값이다 — 실제 값은 세 서비스의 `application-local.yml` 에 있고 그 파일은 gitignore 된다([tech-stack.md §4.3](tech-stack.md)). **여기에 그 값을 옮겨 적지 않는다**(바로 아래 "기본값도 두지 않는다" 와 같은 이유다).

**기본값도 두지 않는다.** 비밀 값이 아니지만 **정책값**이다. 임의 기본값을 두면 그 값이 정해진 정책인지 임시값인지 구분할 수 없다. 환경변수는 [tech-stack.md §4.3](tech-stack.md)에 있다.

**CORS 설정은 `SecurityConfig`에 둔다.** MVC(`WebConfig`) 쪽에만 두면 preflight(`OPTIONS`)가 인가 필터에 **401로 막힌다**([conventions.md §1](conventions.md)).

## 2. 서명 알고리즘 — RS256

**auth-service가 개인키로 서명하고, member·board는 공개키로 검증만** 한다. 발급 주체는 하나여야 한다.

| 서비스 | 보유 키 | 가능한 일 |
| --- | --- | --- |
| auth | 개인키 (`JWT_PRIVATE_KEY_LOCATION`) | 토큰 발급·검증 |
| member | 공개키 (`jwt-public.pem`) | 검증만 |
| board | 공개키 (`jwt-public.pem`) | 검증만 |

**member·board는 서명 의존성(`spring-security-oauth2-jose`)을 직접 선언하지 않는다**([tech-stack.md §3.2](tech-stack.md)).

**다만 그것이 서명을 막지는 못한다.** 검증 스타터가 `oauth2-jose`를 추이로 끌고 오므로 **세 서비스 모두 클래스패스에 서명 클래스를 갖는다**([tech-stack.md §2.2](tech-stack.md)의 측정값). 직접 선언을 금지하는 것은 **의도를 선언하지 않게 하는 것**이고, **이 경계를 실제로 지키는 것은 위 표다 — member·board에 개인키가 없다.**

HS256을 쓰지 않는 이유는 [adr/0004](adr/0004-rs256-over-hs256.md)에 있다.

**구현은 Spring Security 표준을 쓴다.** JWT 필터·검증기를 직접 만들지 않는다([tech-stack.md §2](tech-stack.md)).

## 3. 키 관리

| 항목 | 규칙 |
| --- | --- |
| 개인키 주입 | 환경변수 `JWT_PRIVATE_KEY_LOCATION`에 **경로**를 준다 (`file:`·`classpath:`). 기본값을 두지 않는다(없으면 기동 실패) |
| 개인키 보유 | **auth-service 하나뿐이다.** member·board에 두지 않는다 |
| 공개키 배포 | **member·board 두 곳**의 리소스 파일(`classpath:jwt-public.pem`). 커밋 가능 |
| 공개키 동기 | 두 사본이 같은 키인지 통합 검증에서 확인한다([plan/integration.md](plan/integration.md) I-01) |
| Git | `private.pem`, `*.env`를 `.gitignore`에 등록한다 (스캐폴딩 시 선행 조치) |
| 환경 분리 | 개발용 키와 운영용 키를 분리한다. 운영 개인키는 시크릿 저장소에서만 주입하며, **파일로 마운트하고 그 경로를 준다** |
| 키 회전 | JWT header에 `kid`를 포함한다. **값은 발급 측이 정한다** — 공개키 thumbprint(RFC 7638)를 쓴다. 1차의 검증 측(member·board)은 공개키 하나를 설정으로 받으므로 `kid`를 보지 않는다. JWKS와 복수 키가 들어오는 2차에 계약값으로 올린다 |
| 키 재생성 | 키를 다시 만들면 기존 토큰이 모두 무효화되어 전 사용자 재로그인이 필요하다 |

공개키가 유출돼도 토큰을 위조할 수 없으므로 저장소에 두어도 된다. **개인키는 어떤 경우에도 커밋하지 않는다.**

> **PEM 본문이 아니라 경로를 주입한다.** 본문을 환경변수에 넣으면 줄바꿈 이스케이프가 필요해 사고가 난다. 컨테이너·K8s의 시크릿은 파일로 마운트되므로 경로 쪽이 자연스럽다. 변수명이 `JWT_PRIVATE_KEY`가 아니라 `JWT_PRIVATE_KEY_LOCATION`인 이유다.

## 4. 인증 흐름

```
[계정 생성]  auth-service        가입 1단계
  POST /api/v1/accounts (email, password)
    -> 이메일 중복 확인 + BCrypt 해싱
    -> account INSERT
    <- 201 { accountId, email }

[로그인]  auth-service
  POST /api/v1/auth/login (email, password)
    -> 계정 조회 + BCrypt.matches()
    -> account.deleted = false 확인          <- 탈퇴 계정 거부
    -> 개인키(RS256)로 Access/Refresh 서명
       Claim: { sub, role, iss, iat, exp }   <- api-contract.md §6.  nickname 없음
    -> RefreshToken sp_auth upsert
    <- TokenResponse

[프로필 등록]  member-service    가입 3단계
  POST /api/v1/members (Authorization: Bearer AT) { nickname }
    -> 공개키로 서명 검증
    -> account_id = Claim.sub                <- 본문의 식별자를 신뢰하지 않는다
    -> member INSERT (accountId 기준 멱등)
    <- 201

[게시글 작성]  board-service
  POST /api/v1/posts (Authorization: Bearer AT)
    -> 공개키로 서명 검증
    -> Claim에서 LoginMember(accountId, role) 추출
    -> POST /internal/v1/members/bulk { accountIds: [accountId] }   <- 트랜잭션 밖
       실패 판정은 api-contract.md §5.1
    -> writerId(Claim) + writerNickname(내부 API) 스냅샷과 함께 저장
    <- 201 Created

[재발급]  auth-service
  POST /api/v1/auth/reissue (refreshToken)
    -> 서명·만료 검증 + sp_auth 저장값 일치 확인
    -> account.deleted = false 확인          <- 같은 트랜잭션에서
    -> 새 Access/Refresh 발급, 조건부 UPDATE로 회전(Rotation)

[계정 탈퇴]  auth-service        탈퇴 1단계
  DELETE /api/v1/accounts/me (password)
    -> BCrypt.matches()로 비밀번호 재확인    <- 파괴적 동작 앞에 둔다
    -> account.deleted = true + RefreshToken 삭제   [한 로컬 트랜잭션]
    <- 204

[프로필 탈퇴]  member-service    탈퇴 2단계
  DELETE /api/v1/members/me (1단계에서 쓰던 AT)
    -> member.deleted = true, nickname = NULL
    <- 204
```

**재발급이 `account.deleted`를 검사하지 않으면 탈퇴 경계가 무너진다.** 조회와 확인을 같은 트랜잭션에 두고 회전을 조건부 UPDATE로 하지 않으면, 탈퇴와 재발급이 겹칠 때 삭제한 RefreshToken이 되살아나 탈퇴 계정이 14일간 갱신할 수 있다([requirements/member.md §6](requirements/member.md)).

### 4.1 "어느 쪽이 틀렸는지 노출하지 않는다"는 시간도 포함한다

로그인 실패를 **없는 이메일**과 **비밀번호 불일치**로 구별할 수 없어야 한다([requirements/member.md §1](requirements/member.md) MR-04). 응답 본문과 상태 코드를 같게 맞추는 것으로는 부족하다.

**계정이 없을 때 BCrypt 비교를 건너뛰면 응답 시간으로 드러난다.** 측정값이다(strength 10).

| 경로 | 시간 |
| --- | --- |
| 없는 이메일 — `matches` 생략 | **0.0 ms** |
| 비밀번호 불일치 | 48.5 ms |
| 정상 로그인 | 48.5 ms |

불일치와 정상은 구별되지 않는다 — BCrypt의 비교가 그렇게 설계되어 있다. **누출은 오직 비교를 건너뛰는 데서 나오고, 48ms 차이는 네트워크 지터에 묻히지 않는다.**

**계정이 없어도 더미 해시로 `matches`를 한 번 수행한다.** 그 결과는 쓰지 않고 버린다.

```java
// 계정이 없으면 더미 해시와 비교해 시간을 맞춘다. 결과는 쓰지 않는다
Account account = repository.findByEmail(email).orElse(null);
boolean ok = (account != null)
        ? passwordEncoder.matches(raw, account.getPassword())
        : passwordEncoder.matches(raw, DUMMY_HASH) && false;
```

**더미 해시는 실제 비밀번호의 해시가 아니어야 한다.** 기동 시 임의 값으로 한 번 인코딩해 메모리에만 둔다 — 상수로 커밋하면 [requirements/member.md §10.2](requirements/member.md)의 "BCrypt 모양을 커밋하지 않는다"에 걸린다.

**탈퇴 계정도 같은 경로로 처리한다.** 계정을 찾았으나 `deleted = true`인 경우에 비교를 건너뛰면, 그것이 "그 이메일은 존재하되 탈퇴했다"를 알려준다.

> 이 규칙은 로그인에만 적용한다. 비밀번호 변경·계정 탈퇴는 **이미 인증된 요청**이므로 자기 계정의 존재가 전제되어 있고 숨길 것이 없다.

#### 1차에서 이 방어의 실효는 제한적이다

**`GET /api/v1/accounts/check-email`이 같은 사실을 무인증으로 공개한다.** 기존 이메일에 `available: false`를 돌려주므로([api-contract.md §2.3](api-contract.md)), 이메일을 열거하려는 자는 로그인의 응답 시간을 재지 않는다 — 중복 확인을 호출한다.

| 이메일 존재를 알아내는 경로 | 1차 |
| --- | --- |
| 로그인 응답 본문·상태 코드 | 막혀 있다 (MR-04) |
| 로그인 응답 시간 | 막혀 있다 (위 더미 해시) |
| **`check-email`** | **열려 있다. 무인증·무제한** |

그러므로 **"로그인은 이메일의 존재를 숨긴다"는 시스템 전체로는 참이 아니다.** MR-04는 로그인 엔드포인트의 요구사항이고, 그 요구를 지키는 것이 계정 열거를 막지는 않는다.

**그래도 §4.1을 유지한다.** 둘 다 비용이 거의 없고(`matches` 한 번), 중복 확인은 가입 UX가 요구하는 기능이라 1차에서 없앨 수 없다. **제한이 걸리는 순간 로그인이 유일한 누출 경로가 되므로, 그때 급히 넣는 것보다 지금 들어 있는 것이 낫다.**

**2차 — 중복 확인 엔드포인트에 rate limit을 건다**([plan/phase2.md §5](plan/phase2.md)). 그 전까지 계정 열거는 **감수하는 노출이다.**

## 5. 인가

### 5.1 판정 위치

| 판정 | 위치 |
| --- | --- |
| 인증 필요 여부(경로별) | `SecurityFilterChain`의 `permitAll` / `authenticated` |
| ADMIN 여부 | **board 의 Service 계층이 `LoginMember.role()` 문자열을 비교한다** — `"ADMIN".equals(...)` 가 `PostService`·`CommentService` 두 자리에 있다. **`GrantedAuthority` 로 판정하지 않는다** — `hasRole`·`@PreAuthorize`·`hasAuthority` 사용처가 세 저장소에 **0건**이다(D-02 리뷰 실측). **member 는 이 판정을 갖지 않는다** — §5.2 의 매트릭스에서 ADMIN 으로 갈리는 것이 전부 board 기능이다. auth 는 변환을 두지 않고 권한을 `LoginAccount.role` 로만 전달한다 |
| **소유자 검증(본인 글인가)** | **Service 계층** |

> **`RoleClaimConverter` 가 만드는 `ROLE_` 권한은 만들어지고 아무도 읽지 않는다. D-02 리뷰 실측.** 세 저장소에 역할 기반 인가 규칙이 없어서다 — 그래서 열거 밖 `role` 이 와도 **안전한 쪽으로 닫혔다**(타인 글·댓글 삭제가 `role=USER` 와 바이트 동일한 403). **그 닫힘은 설계가 아니라 비교의 모양에 딸려 온 것**이고 `D-02` 가 그래서 값 검증을 요구했다 — 자세한 것은 [tech-stack.md §2.1](tech-stack.md)이 갖는다.
>
> **이 행의 앞 판이 "`role` claim 기반 `GrantedAuthority` — member·board가 갖는다" 였다. 두 겹으로 틀렸다** — 판정 수단이 `GrantedAuthority` 가 아니고(문자열 비교다), member 는 그 판정을 갖지 않는다. **member·board 의 `LoginMember` javadoc 이 그 틀린 문장을 옮겨 적었다** — `M-12`·`B-12` 가 두 저장소에서 각각 고친다(거짓의 종류가 다르다).

소유자 검증을 Controller나 Security 설정에 두지 않는다. 리소스를 조회해야 판정할 수 있기 때문이다.

```java
// PostService
private void validateOwner(Post post, LoginMember member) {
    if (!post.getWriterId().equals(member.accountId())) {
        throw new BusinessException(ErrorCode.POST_FORBIDDEN);   // P002
    }
}
```

### 5.1.1 인프라 경로의 인가

업무 API가 아닌 경로도 인가 규칙이 있어야 한다. **`spring-boot-starter-security`가 클래스패스에 있으면 Boot 기본 필터 체인이 전 경로에 인증을 요구하므로**, 선언하지 않은 경로는 401이 된다.

| 경로 | 인가 | 비고 |
| --- | --- | --- |
| `/swagger-ui/**`, `/swagger-ui.html` | `permitAll` | `prod` 프로파일에서는 **비활성화**한다 |
| `/v3/api-docs/**` | `permitAll` | 같음 |
| `/actuator/health` | `permitAll` | Boot 기본값이 이미 허용한다 |
| `/actuator/**` (health 외) | 차단 | **무토큰 401 `A001`, 유효 토큰 403 `A004`.** 404 가 아니다 — 측정값 |
| `/internal/**` | 외부 인증 체인에서 분리 | `X-Internal-Api-Key` 필터가 담당한다(§6) |

**404 를 기대하지 않는다. 측정값이다.** `management.endpoints.web.exposure.include: health` 가 그 엔드포인트를 등록조차 하지 않지만, **Security 필터 체인이 디스패치보다 먼저 거부하므로** 404 가 아니라 인증·인가 응답이 나간다. 무토큰은 401 `A001`, 유효 토큰은 403 `A004` 다 — auth(AU-11)·member(M-11)에서 각각 관측했다. 그 셋을 "노출되지 않는다" 로 묶어 적되 **404 를 단언하지 않는다.**

**`permitAll`은 `prod`에서 열어 두라는 뜻이 아니다.** springdoc 자체를 `prod` 프로파일에서 끄므로 경로가 사라진다. 그 확인은 각 서비스의 마무리 항목(AU-11·M-11·B-09)에 있다.

> **공통 기반 항목(AU-02·M-02·B-02)에서는 `/swagger-ui.html`이 열리지 않는다.** `SecurityConfig`가 보안 기반 항목(AU-04·M-04·B-04)의 산출물이기 때문이다. 공통 기반에서 확인할 수 있는 것은 **springdoc이 OpenAPI 문서를 생성하는가**까지다.

### 5.2 권한 매트릭스

| 기능 | 비로그인 | USER(타인) | USER(본인) | ADMIN |
| --- | --- | --- | --- | --- |
| 게시글 목록·상세 조회 | O | O | O | O |
| 게시글 작성 | X | O | O | O |
| 게시글 수정 | X | X | O | X |
| 게시글 삭제 | X | X | O | O |
| 댓글 작성 | X | O | O | O |
| 댓글 수정 | X | X | O | X |
| 댓글 삭제 | X | X | O | O |

ADMIN에게 **수정 권한을 주지 않는다.** 타인 글의 내용 변조를 막기 위해서이며, 부적절 게시물은 삭제(블라인드)로만 처리한다.

**게시글·댓글 작성에는 활성 프로필이 추가로 필요하다.** 계정만 만들고 프로필을 등록하지 않았으면 `S002`(403)다. 이것은 **권한 판정이 아니라 작성자 스냅샷 취득의 부수 효과**다([architecture.md §4.2](architecture.md)).

**권한 판정은 JWT Claim의 `sub`·`role`만으로 한다.** 권한을 다른 서비스에 되묻지 않는다.

### 5.3 오프라인 검증의 잔여 노출

검증이 공개키만으로 이뤄지므로 **탈퇴·권한 박탈이 기존 Access Token에 즉시 반영되지 않는다.**

| | 1차 동작 |
| --- | --- |
| 최대 노출 시간 | Access Token 만료까지 (30분) **+ clock skew 60초** |
| 재발급으로 연장되는가 | 아니다 — 탈퇴 시 RefreshToken 삭제 + `deleted` 검사(§4) |
| 잔여 권한 | 그 `role`이 가진 **모든 변경 권한**. ADMIN이면 **타인 글·댓글 삭제 포함** |
| 새 글 작성 | 통상 막힌다(프로필 `deleted`). 확인–커밋 창에서는 통과할 수 있다 |
| 프로필 재생성 | 막힌다(`uk_member_account_id`) |

**"자기 글만"이 아니다.** ADMIN 계정의 탈퇴·권한 회수는 30분의 노출을 동반한다.

**비밀번호 변경도 같은 창을 갖는다.** RefreshToken을 삭제하므로 **새 세션은 만들 수 없지만**, 이미 발급된 Access Token은 만료까지 계속 통과한다.

| 비밀번호 변경 직후 | |
| --- | --- |
| 기존 Refresh Token으로 재발급 | **즉시 막힌다** (저장값이 삭제됐다) |
| 기존 Access Token으로 API 호출 | **만료까지 통과한다** (30분 + skew) |

즉 **"비밀번호를 바꿨으니 안전하다"는 최대 31분 뒤부터 참이다.** 비밀번호 변경이 침해 대응으로 쓰인다면 이 창이 그대로 노출이다. 즉시 차단은 1차 범위 밖이고([adr/0012](adr/0012-auth-as-separate-service.md) 포기 목록 1), 그때 탈퇴·권한 회수·비밀번호 변경 셋을 함께 다룬다.

> **clock skew 60초는 Spring의 기본값이다.** `JwtTimestampValidator`가 `DEFAULT_MAX_CLOCK_SKEW = 60s`로 두고 있어(6.5.11 바이트코드로 확인), **`exp`가 지난 토큰이 60초 더 통과한다.** 분산 환경의 시계 드리프트를 흡수하려는 값이다.
>
> **그 기본값이 이 경로에서 실제로 일한다. I-05 리뷰 실측.** 바이트코드는 "기본값이 60초다" 를 말하고 이것은 "그 60초가 통과시킨다" 를 말한다 — **다른 주장이다.** 2단계까지 탈퇴한 계정의 Access Token 으로 `GET /api/v1/posts/me`(`authenticated()` 경로)를 쳤을 때 `exp`**+7초·+35초에 200**, `exp`**+70초·+130초에 401 `A003`** 이었다(만료 전 200, 무토큰 대조가 여섯 발화 모두 200 이라 서비스 정지가 배제된다). 만료 뒤 쓰기도 board·member 둘 다 401 `A003` 이다.
>
> 1차에서 줄이지 않는다. 노출 창이 30분에서 31분이 되는 것이고, 줄이려면 `JwtConfig`에 validator를 직접 주입해야 한다. **즉시 차단이 요구가 되면 그때 skew와 블랙리스트를 함께 본다**([adr/0012](adr/0012-auth-as-separate-service.md) 포기 목록 1).

즉시 차단은 1차 범위 밖이다. 요구가 되면 토큰 블랙리스트나 introspection을 2차에 도입한다([adr/0012](adr/0012-auth-as-separate-service.md) 포기 목록 1). **오프라인 검증만으로는 불가능하다.**

## 6. 내부 API 보호

| 계층 | 통제 |
| --- | --- |
| 네트워크 | `/internal/**`을 외부 라우팅에서 제외. 운영은 내부망·보안그룹으로 격리 |
| 애플리케이션 | `X-Internal-Api-Key` 헤더 검증 필터. 키는 환경변수 주입 |
| 호출 측 | board가 같은 키를 설정으로 주입받아 헤더에 싣는다([architecture.md §6](architecture.md)) |

**키 거부(401/403)를 "프로필 없음"으로 해석하지 않는다.** 키를 회전하고 board만 갱신을 놓치면 전 사용자의 쓰기가 멈추는데, 업무 오류로 분류하면 경보가 뜨지 않는다. 판정 표는 [api-contract.md §5.1](api-contract.md)에 있다.

**내부 API는 호출자를 막는 게이트가 아니다.** 임의의 `accountId`를 조회할 수 있으므로 "조회 키는 검증된 JWT의 `sub`"라는 규칙의 강제 지점은 board 안에만 있다. 1차의 실질 피해는 닉네임 열람 수준이지만, 원칙이 한 홉 옮겨졌다는 점은 기록해 둔다.

## 7. 구현 시 주의

- 비밀번호는 어떤 응답에도 넣지 않는다. 내부 API 응답도 마찬가지다. member·board는 애초에 갖고 있지 않다
- **계정 탈퇴·비밀번호 변경 시 Refresh Token을 삭제한다.** 둘 다 auth 안에서 한 로컬 트랜잭션으로 처리한다
- **계정 탈퇴는 비밀번호를 재확인한다.** 그래서 탈퇴 순서가 계정 먼저다 — member는 비밀번호를 갖지 않으므로 프로필을 먼저 지우면 재확인이 불가능해진다([architecture.md §4.4](architecture.md))
- **로그인·재발급은 `account.deleted`를 검사한다.** 검사하지 않으면 §5.3의 30분 경계가 성립하지 않는다
- 로그인 실패 5회 잠금은 2차 범위다. 1차에서는 구현하지 않는다
- 실패를 조용히 통과시키지 않는다. 키가 없거나 검증기가 구성되지 않으면 **기동이 실패해야** 한다
