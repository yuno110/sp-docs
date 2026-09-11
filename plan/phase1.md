---
title: 1차 작업 계획
type: plan
status: living
version: v2
updated: 2026-09-11
read_when: "작업 항목의 범위·의존·완료 기준을 확인하거나 다음 할 일을 고를 때. 상태는 담당 저장소의 checklist.md를 본다"
related: [README.md, integration.md, ../process/dev-workflow.md, ../requirements/member.md, ../requirements/board.md]
---
# 1차 작업 계획

작업 항목 20개(M 11 + B 9)와 통합 검증 4개로 구성한다. 통합 검증은 [integration.md](integration.md)에 있다.

절차는 [../process/dev-workflow.md](../process/dev-workflow.md)를 따른다. **상태는 이 문서에 적지 않는다.**

> **v2 변경**: 항목을 **기반 단계**와 **기능 단계**로 나누고 내용을 재배정했다. 착수 전(코드 0줄, 전 항목 `todo`)이므로 ID는 유지하고 내용을 옮겼다. **M-03·M-04, B-03·B-04의 의미가 v1과 다르다.** v1 기준으로 기억하고 있는 내용을 쓰지 말고 이 문서를 다시 읽는다.

## 1. 단계와 워커 구성

### 1.1 두 단계

| 단계 | 항목 | 성격 |
| --- | --- | --- |
| **기반** | M-01~M-04, B-01~B-04 | 순차. 뒤의 모든 항목이 의존한다 |
| **기능** | M-05~M-11, B-05~B-09 | 기반 산출물을 **읽기만** 하고 자기 파일을 만든다 |

기반 단계에 **순서 의존과 공유 상태를 몰아서 제거한다.** 엔티티 도메인 메서드, 전체 경로 인가 설정, 마이그레이션, 공통 빈이 모두 여기서 끝난다.

이 구조의 값어치는 병렬화가 아니다. **작업이 앞 항목의 미완성에 걸려 멈추는 일이 없어지는 것**이다. 워커가 하나여도 이득이 있다.

```
member 저장소                      board 저장소
─────────────                      ────────────
M-01 스캐폴딩          [기반]       B-01 스캐폴딩          [기반]
M-02 공통 기반         [기반]       B-02 공통 기반         [기반]
M-03 도메인 기반       [기반]       B-03 도메인 기반       [기반]
M-04 보안 기반         [기반]       B-04 보안 기반         [기반]
─────────────────────────────      ─────────────────────────────
M-05 회원가입          [기능]       B-05 게시글 작성·상세  [기능]
M-06 로그인            [기능]       B-06 목록·검색         [기능]
M-07 재발급·로그아웃   [기능]       B-07 수정·삭제         [기능]
M-08 내 정보           [기능]       B-08 댓글              [기능]
M-09 비밀번호·탈퇴     [기능]       B-09 내가 쓴 글·마무리 [기능]
M-10 프로필·내부 API   [기능]
M-11 마무리            [기능]
        \                              /
         \____ I-01 ~ I-04 통합 검증 __/
```

### 1.2 워커 구성 — 저장소별 1개로 시작

**1차는 구현 워커 2개로 시작한다.** member 저장소에 1개, board 저장소에 1개다.

두 저장소는 완전히 병렬이다. 소스가 겹칠 수 없고, 계약이 [../api-contract.md §5](../api-contract.md)에 확정되어 있어 서로를 기다리지 않는다. B-04(JWT 검증)는 M-04(JWT 발급)를 기다리지 않는다 — board는 테스트용 키 페어로 자체 검증하고 실제 키 교환은 I-01에서 한다.

**저장소 안에서 워커를 더 늘리는 것은 지금 결정하지 않는다.** 늘린다면 트랙은 아래 하나뿐이며, 이미 그어진 소유 경계([../adr/0006](../adr/0006-auth-inside-member-service.md)) 위에 있어 설계 변경이 필요 없다.

| 트랙 | 소유 경로 | 항목 |
| --- | --- | --- |
| member 트랙 | `member/*`, `internal/*` | M-05, M-08, M-09, M-10 |
| auth 트랙 | `auth/*` | M-06, M-07 |

**board는 쪼개지 않는다.** member 기능 단계가 임계 경로이므로 board를 병렬화해도 전체 소요가 줄지 않는다.

**확대는 측정 후에 정한다.** 한 사이클을 돌려 병합·전체 테스트·리뷰에 실제 몇 분이 드는지 재고, 그 비용이 절약분보다 크면 그대로 둔다.

### 1.3 워크트리의 주된 쓰임 — 구현 ∥ 리뷰

구현 워커가 2개뿐이어도 워크트리는 값어치가 있다. **리뷰 워커를 동시에 돌리는 것**이다.

```
구현 워커:  M-05 ──> M-06 ──> M-07 ──> ...
리뷰 워커:        M-05 리뷰 ──> M-06 리뷰 ──> ...
```

리뷰 워커는 읽기만 하므로 충돌이 구조적으로 불가능하고, [../process/review-policy.md §1](../process/review-policy.md)의 작성자≠리뷰어 요구를 자동으로 만족한다. 구현 워커를 늘리는 것보다 위험 대비 효용이 크다.

### 1.4 병합 순서

같은 저장소에서 두 워커를 돌릴 경우에만 해당한다.

**member 트랙을 먼저 병합하고 auth 트랙이 리베이스한다.** 충돌 해소 책임자를 미리 확정하는 것이며, 순서를 정하지 않으면 양쪽이 서로를 기다린다.

병합 후에는 반드시 전체 테스트를 다시 돌린다. 각자의 워크트리에서 통과했어도 합친 뒤 깨질 수 있다.

## 2. 경로 소유

각 경로에는 소유 항목이 하나다. 워커는 자기 항목이 소유한 경로에만 쓴다.

### 2.1 기반이 만들고 기능이 읽는 것

아래는 기반 단계에서 완성된다. **기능 단계는 읽기만 하고 수정하지 않는다.**

| 경로 | 소유 | 기능 단계의 접근 |
| --- | --- | --- |
| `build.gradle`, `settings.gradle`, `.gitignore` | M-01 / B-01 | 읽기 전용 |
| `global/common/`, `global/error/` | M-02 / B-02 | 읽기 전용 |
| `global/config/` 전부 (`SecurityConfig` 포함) | M-04 / B-04 | 읽기 전용 |
| `global/security/` 전부 | M-04 / B-04 | 읽기 전용 |
| `*/entity/`, `*/repository/`, `*/support/` | M-03 / B-03 | 읽기 전용 |
| `db/migration/V1`, `V2` | M-03 / B-03 | 읽기 전용 |

**기능 워커가 이 경로의 파일을 고쳐야 한다면 계획에 없던 일이다.** 진행하지 말고 BLOCKED로 보고한다([../process/dev-workflow.md §4](../process/dev-workflow.md)).

### 2.2 기능 단계의 경로 소유

| 경로 | 소유 항목 |
| --- | --- |
| `member/dto/`, `member/service/`, `member/controller/` | M-05, M-08, M-09, M-10 (§2.3) |
| `db/migration/V3__seed_admin.sql` | M-05 |
| `auth/dto/`, `auth/service/`, `auth/controller/` | M-06, M-07 |
| `internal/` | M-10 |
| `post/dto/`, `post/service/`, `post/controller/` | B-05, B-06, B-07, B-09 (§2.3) |
| `post/repository/PostQueryRepository` | B-06 |
| `comment/dto/`, `comment/service/`, `comment/controller/` | B-08 |

### 2.3 공유 지점

기반 확대 후 남은 것은 아래 셋뿐이다.

| 파일 | 생성 | 확장 | 규칙 |
| --- | --- | --- | --- |
| `member/service/MemberService`, `member/controller/MemberController` | M-05 | M-08, M-09, M-10 | 같은 트랙 안이므로 순차 |
| `post/service/PostService`, `post/controller/PostController` | B-05 | B-06, B-07, B-09 | board는 단일 워커이므로 순차 |
| `docs/checklist.md` | - | 모든 항목 | 자기 줄만 ([../process/orchestration.md §6](../process/orchestration.md)) |

**v1에서 이 표에 있던 `SecurityConfig`·`build.gradle`·`db/migration`은 기반 단계로 옮겨져 사라졌다.** 근거는 각각 M-04(전체 경로 인가 선반영), M-01(의존성 확정), M-03(V1·V2 통합)이다.

`member/dto/`와 `post/dto/`는 여러 항목이 쓰지만 **각자 새 파일만 추가**하므로 공유 지점이 아니다. 기존 DTO 파일을 수정해야 하면 계획에 없던 일이므로 BLOCKED로 보고한다.

> **이 표가 완전하다고 보증하지 않는다.** 목록 밖의 파일에서 충돌이 났다면 (a) 누군가 소유 경계를 넘었거나 (b) 이 표가 빠뜨린 것이다. 어느 쪽인지 판단이 서지 않으면 BLOCKED로 보고한다. **워커의 잘못으로 단정하지 않는다.**

### 2.4 마이그레이션 번호

Flyway 버전은 서비스마다 하나의 순번이다. 번호는 계획이 배정한다. **워커가 스스로 정하지 않는다.**

| 서비스 | 기반 | 기능 |
| --- | --- | --- |
| member | `V1__create_member.sql`, `V2__create_refresh_token.sql` (M-03) | `V3__seed_admin.sql` (M-05) |
| board | `V1__create_post.sql`, `V2__create_comment.sql` (B-03) | 없음 |

배정되지 않은 마이그레이션이 필요하면 임의로 번호를 붙이지 말고 BLOCKED로 보고한다.

### 2.5 소유 경계를 넘어야 할 때

진행하지 말고 BLOCKED로 보고한다. 계획이 항목을 분할하거나 기반 단계에 선반영하는 방식으로 해결한다.

**이미 해결된 것 둘** — 워커가 다시 판단할 필요 없다.

| 상황 | 처리 |
| --- | --- |
| M-09가 `RefreshTokenRepository`(auth 소유)를 참조해야 함 | [../adr/0006 §예외](../adr/0006-auth-inside-member-service.md)가 허용한다. 삭제 연산에 한정 |
| B-07(게시글 삭제)이 댓글을 연쇄 삭제해야 함 | B-03이 `CommentRepository.softDeleteByPostId()`를 미리 만든다. B-08을 기다리지 않는다 |

## 3. member-service 작업 항목

### M-01 프로젝트 스캐폴딩 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | 없음 |
| 참조 | [../tech-stack.md §1 §3](../tech-stack.md), [../conventions.md §1.1](../conventions.md) |

**산출물**
- `build.gradle`, `settings.gradle`, Gradle Wrapper
- `src/main/java/com/example/member/MemberApplication.java`
- `src/main/resources/application.yml`, `application-local.yml`
- `.gitignore` (`private.pem`, `*.env`, `build/`, `.gradle/`, QueryDSL 생성 경로)

**의존성을 여기서 전부 확정한다.** [../tech-stack.md §3](../tech-stack.md)의 목록을 빠짐없이 넣어 기능 단계에서 `build.gradle`을 고칠 일이 없게 한다.

**완료 기준**
- [ ] `./gradlew build`가 성공한다
- [ ] `./gradlew bootRun`으로 8081 포트에 기동된다
- [ ] [../tech-stack.md §3.1 §3.2](../tech-stack.md)의 의존성이 전부 선언되어 있다
- [ ] DB 접속 정보가 환경변수로 외부화되어 있다 ([../tech-stack.md §4.3](../tech-stack.md))
- [ ] `.gitignore`에 `private.pem`, `*.env`가 있다
- [ ] 시간대가 `Asia/Seoul`로 명시 설정되어 있다

**검증** — `MemberApplicationTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 컨텍스트 로딩 | 예외 없이 기동 |
| `TimeZone.getDefault()` | `Asia/Seoul` |

---

### M-02 공통 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-01 |
| 참조 | [../api-contract.md §6 §7.1 §7.2](../api-contract.md), [../domain-model.md §1.1](../domain-model.md), [../conventions.md §6 §7](../conventions.md) |

**산출물**
- `global/common/ApiResponse.java`, `ErrorResponse.java`, `PageResponse.java`
- `global/common/BaseTimeEntity.java`
- `global/error/ErrorCode.java` (C001~C005, A001~A004, M001~M005)
- `global/error/BusinessException.java`, `GlobalExceptionHandler.java`
- `global/config/JpaConfig.java` (`@EnableJpaAuditing`), `SwaggerConfig.java`

복제 대상 파일 상단에 정본 주석을 남긴다([../conventions.md §7.1](../conventions.md)).

**완료 기준**
- [ ] `ErrorCode`의 코드·HTTP 상태·메시지가 [../api-contract.md §7](../api-contract.md)과 정확히 일치한다
- [ ] `BusinessException`을 던지면 해당 코드의 HTTP 상태와 응답 본문이 나온다
- [ ] `@Valid` 검증 실패가 `C001`로 변환되고 `fieldErrors`에 필드별 메시지가 담긴다
- [ ] 응답 본문에 스택트레이스·SQL이 포함되지 않는다
- [ ] `/swagger-ui.html`이 열린다

**검증** — `GlobalExceptionHandlerTest` (`@WebMvcTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| `BusinessException(M002)` | 409, `error.code = "M002"` |
| `BusinessException(A004)` | 403, `A004` |
| `@Valid` 실패 | 400, `C001`, `fieldErrors` 비어있지 않음 |
| 성공 응답 | `success = true`, `error = null` |
| 예상치 못한 `RuntimeException` | 500, `C005`, 스택트레이스 없음 |

---

### M-03 도메인 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-02 |
| 참조 | [../domain-model.md §1 §2](../domain-model.md), [../conventions.md §2](../conventions.md), [../requirements/member.md §3](../requirements/member.md) |

**두 엔티티와 도메인 메서드를 여기서 전부 만든다.** [../conventions.md §2](../conventions.md)가 "도메인 로직은 Entity 메서드로 둔다"를 규칙으로 정했으므로, 기능 단계에 남겨두면 여러 항목이 같은 엔티티 파일을 고치게 된다.

**산출물**
- `member/entity/Member.java`, `Role.java`
- `member/repository/MemberRepository.java`
- `member/support/MemberReader.java` (find or throw — `M001`)
- `auth/entity/RefreshToken.java`
- `auth/repository/RefreshTokenRepository.java`
- `db/migration/V1__create_member.sql`, `V2__create_refresh_token.sql`

**`Member`의 도메인 메서드** — 전부 이 항목에서 구현한다.

| 메서드 | 동작 |
| --- | --- |
| `updateNickname(String)` | 닉네임 변경 |
| `changePassword(String encoded)` | 해시된 비밀번호로 교체 |
| `withdraw()` | `deleted = true` |

**완료 기준**
- [ ] 기동 시 Flyway가 `member`, `refresh_token` 테이블을 생성한다
- [ ] 컬럼 타입·길이·NULL 여부가 [../domain-model.md §2](../domain-model.md)와 일치한다
- [ ] `member.email`, `member.nickname`, `refresh_token.member_id`, `refresh_token.token`에 UNIQUE 제약이 있다
- [ ] `created_at`, `updated_at`이 `DATETIME`이고 자동 기록된다
- [ ] `role`이 문자열(`USER`/`ADMIN`)로 저장된다
- [ ] 위 표의 도메인 메서드 3개가 모두 구현되어 있다
- [ ] `MemberReader`가 없는 id 조회 시 `BusinessException(M001)`을 던진다
- [ ] Entity에 `@Setter`·`@Data`가 없다

**검증** — `MemberRepositoryTest`, `RefreshTokenRepositoryTest` (`@DataJpaTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| 저장 후 조회 | 모든 필드 일치 |
| 중복 email / nickname 저장 | `DataIntegrityViolationException` |
| 저장 시 | `createdAt`, `updatedAt` null 아님 |
| `role` 미지정 저장 | `USER` |
| `deleted` 미지정 저장 | `false` |
| `updateNickname()` 호출 | 닉네임만 변경, `createdAt` 불변 |
| `changePassword()` 호출 | 비밀번호만 변경 |
| `withdraw()` 호출 | `deleted = true`, 행 존재 |
| 같은 `member_id`로 refresh token 2개 저장 | `DataIntegrityViolationException` |
| `MemberReader`로 없는 id 조회 | `BusinessException(M001)` |

---

### M-04 보안 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-03 |
| 참조 | [../security.md](../security.md) 전체, [../api-contract.md §2 §5](../api-contract.md), [../tech-stack.md §2.2 §4.2](../tech-stack.md) |

**인증·인가 기반을 여기서 전부 끝낸다.** 경로별 인가 설정까지 포함하므로 기능 단계에서 `SecurityConfig`를 고칠 일이 없다.

**산출물**
- `global/config/JwtConfig.java` (개인키 로딩, `kid`)
- `global/security/JwtTokenProvider.java` (`NimbusJwtEncoder`)
- `global/config/SecurityConfig.java` — **[../api-contract.md §2](../api-contract.md)의 전체 경로 인가**, `PasswordEncoder` 빈, CORS, STATELESS
- `global/security/LoginMember.java`, `@LoginMember` ArgumentResolver
- `auth/dto/TokenResponse.java`
- `application.yml`에 토큰 만료 시간

**⚠ 경로 선언 순서** — `GET /api/v1/members/{id}`는 `permitAll`, `/api/v1/members/me`는 `authenticated`다([../api-contract.md §2.2](../api-contract.md)). Spring Security의 `requestMatchers`는 **먼저 선언된 규칙이 이긴다.** `/members/*`를 `/members/me`보다 위에 두면 **내 정보가 인증 없이 열린다.** `/me`를 반드시 먼저 선언한다.

**의존성 빈 선제 준비** — `MemberService`·`AuthService`가 쓸 빈(`MemberRepository`, `MemberReader`, `PasswordEncoder`, `JwtTokenProvider`, `RefreshTokenRepository`)이 이 항목 완료 시점에 전부 존재해야 한다. 기능 단계에서 새 빈을 만들 일이 없게 한다.

**완료 기준**
- [ ] 발급된 토큰의 Claim이 [../api-contract.md §5](../api-contract.md)와 정확히 일치한다
- [ ] 서명 알고리즘이 RS256이고 header에 `kid`가 있다
- [ ] Access Token 만료 30분, Refresh Token 14일
- [ ] 개인키가 환경변수로 주입되며 **기본값이 없다** (없으면 기동 실패)
- [ ] 개인키 파일이 커밋되지 않았다
- [ ] jjwt 의존성을 사용하지 않는다
- [ ] [../api-contract.md §2](../api-contract.md)의 **모든 경로**에 인가 규칙이 선언되어 있다
- [ ] **`/members/me`가 `/members/{id}`보다 먼저 선언되어 있다**
- [ ] 세션이 생성되지 않는다
- [ ] CORS 설정에 `*`가 없다

**검증** — `JwtTokenProviderTest`, `SecurityConfigTest` (`@SpringBootTest` + MockMvc)

| 케이스 | 기대 결과 |
| --- | --- |
| Access Token 발급 후 디코딩 | `sub`, `nickname`, `role`, `iss` 일치 |
| 토큰 header | `alg = RS256`, `kid` 존재 |
| Access Token `exp - iat` | 1800초 |
| Refresh Token `exp - iat` | 1209600초 |
| 공개키로 서명 검증 | 통과 |
| payload 변조 후 검증 | 실패 |
| 개인키 환경변수 없이 기동 | 기동 실패 |
| **토큰 없이 `GET /api/v1/members/me`** | **401 `A001`** |
| **토큰 없이 `GET /api/v1/members/1`** | **401이 아님** (컨트롤러가 없으므로 404 허용) |
| 토큰 없이 `POST /api/v1/auth/login` | 401이 아님 |
| 응답 헤더 | `Set-Cookie` 세션 쿠키 없음 |

> `/members/me`와 `/members/{id}` 두 케이스를 **반드시 함께** 검증한다. 하나만 보면 순서 결함을 놓친다.

---

### M-05 회원가입과 중복 확인 [기능 · member 트랙]

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-04 |
| 참조 | [../requirements/member.md §1 §2 §3 §6](../requirements/member.md) (M-01~M-03), [../api-contract.md §2.2 §8.1](../api-contract.md) |

**산출물**
- `member/dto/SignUpRequest.java`, `MemberResponse.java`, `CheckResponse.java`
- `member/service/MemberService.java` (생성)
- `member/controller/MemberController.java` (생성)
- `db/migration/V3__seed_admin.sql` (관리자 1개, BCrypt 해시)

`PasswordEncoder`와 `SecurityConfig`는 M-04 산출물이다. **이 항목에서 만들거나 고치지 않는다.**

**완료 기준**
- [ ] `POST /api/v1/members`가 201과 `{id, email, nickname}`을 반환한다
- [ ] 응답에 `password`가 포함되지 않는다
- [ ] 비밀번호가 BCrypt로 해싱되어 저장된다
- [ ] 중복 이메일 409 `M002`, 중복 닉네임 409 `M003`
- [ ] 검증 규칙이 [../requirements/member.md §2](../requirements/member.md)와 일치한다
- [ ] `check-email`, `check-nickname`이 동작한다
- [ ] **탈퇴 회원의 이메일로 재가입할 수 없다** (409 `M002`)
- [ ] seed 관리자 비밀번호가 BCrypt 해시로 저장되어 있다 (평문 아님)

**검증** — `MemberServiceTest`, `MemberControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 가입 | 201, DB 저장됨 |
| 저장된 비밀번호 | 평문과 다르고 `BCrypt.matches`로 검증됨 |
| 응답 본문 | `password` 키 없음 |
| 중복 이메일 / 닉네임 | 409 `M002` / `M003` |
| 탈퇴 회원(`deleted=true`) 이메일로 가입 | 409 `M002` |
| 이메일 형식 오류 | 400 `C001` |
| 비밀번호 7자 / 특수문자 없음 | 400 `C001` |
| 닉네임 1자 / 11자 | 400 `C001` |
| 미사용 이메일 중복 확인 | 사용 가능 응답 |

---

### M-06 로그인 [기능 · auth 트랙]

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-04 |
| 병렬 | M-05와 동시 진행 가능 (`auth/*` vs `member/*`) |
| 참조 | [../requirements/member.md §1](../requirements/member.md) (M-04), [../api-contract.md §2.1 §8.2](../api-contract.md), [../security.md §4](../security.md) |

**산출물**
- `auth/dto/LoginRequest.java`
- `auth/service/AuthService.java` (생성)
- `auth/controller/AuthController.java` (생성)

`SecurityConfig`·`JwtTokenProvider`·`PasswordEncoder`는 M-04 산출물이다. 테스트용 회원은 `MemberRepository`로 직접 만든다 — **M-05를 기다리지 않는다.**

**완료 기준**
- [ ] `POST /api/v1/auth/login`이 200과 `TokenResponse`를 반환한다
- [ ] 비밀번호 불일치·없는 이메일 **모두** 401 `M004` (어느 쪽이 틀렸는지 노출하지 않는다)
- [ ] 탈퇴 회원은 로그인할 수 없다
- [ ] 발급된 토큰의 `nickname`·`role` Claim이 회원 정보와 일치한다

**검증** — `AuthServiceTest`, `AuthControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 로그인 | 200, accessToken·refreshToken 존재 |
| 비밀번호 불일치 | 401 `M004` |
| 없는 이메일 | 401 `M004` (메시지가 위와 동일) |
| 탈퇴 회원 로그인 | 401 |
| 발급 토큰의 Claim | 회원의 `nickname`·`role`과 일치 |
| 유효 토큰으로 `/members/me` 접근 | 401이 아님 |

---

### M-07 토큰 재발급과 로그아웃 [기능 · auth 트랙]

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-06 |
| 참조 | [../requirements/member.md §1](../requirements/member.md) (M-05, M-06), [../domain-model.md §2.2](../domain-model.md), [../security.md §4](../security.md) |

**산출물**
- `auth/dto/ReissueRequest.java`
- `AuthService`·`AuthController` 확장

`RefreshToken` 엔티티와 리포지토리는 M-03 산출물이다. **이 항목에서 만들지 않는다.**

**완료 기준**
- [ ] 로그인 시 Refresh Token이 DB에 저장된다 (회원당 1행, 재로그인 시 갱신)
- [ ] `POST /api/v1/auth/reissue`가 새 Access·Refresh Token을 반환한다 (Rotation)
- [ ] **재발급 후 이전 Refresh Token은 사용할 수 없다**
- [ ] DB에 없는 Refresh Token → 401 `A002`
- [ ] 만료된 Refresh Token → 401 `A003`
- [ ] `POST /api/v1/auth/logout`이 DB의 Refresh Token을 삭제한다
- [ ] 로그아웃 후 그 Refresh Token으로 재발급할 수 없다

**검증** — `AuthServiceTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 로그인 2회 | `refresh_token` 행이 1개 |
| 정상 재발급 | 200, 새 토큰 반환 |
| 재발급 후 이전 토큰 재사용 | 401 `A002` |
| DB에 없는 토큰으로 재발급 | 401 `A002` |
| 만료 토큰으로 재발급 | 401 `A003` |
| 로그아웃 후 재발급 | 401 `A002` |

---

### M-08 내 정보 조회·수정 [기능 · member 트랙]

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-05 |
| 공유 파일 | `MemberService`, `MemberController` (M-05 생성) |
| 참조 | [../requirements/member.md §1 §4](../requirements/member.md) (M-07, M-08), [../architecture.md §4.2](../architecture.md) |

**산출물**
- `member/dto/MemberUpdateRequest.java`, `MemberUpdateResponse.java`
- `MemberService`·`MemberController` 확장

**완료 기준**
- [ ] `GET /api/v1/members/me`가 본인 정보를 반환한다 (`password` 제외)
- [ ] `PATCH /api/v1/members/me`가 닉네임을 변경한다 (`Member.updateNickname()` 사용)
- [ ] **응답에 새 Access Token이 포함된다**
- [ ] 새 토큰의 `nickname` Claim이 변경된 닉네임이다
- [ ] 중복 닉네임으로 변경 시 409 `M003`
- [ ] **자기 현재 닉네임으로 변경 시 중복 오류가 나지 않는다**

**검증** — `MemberServiceTest`, `MemberControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 내 정보 조회 | 200, `password` 키 없음 |
| 닉네임 변경 | 200, DB 반영됨 |
| 변경 응답의 새 토큰 Claim | `nickname`이 새 값 |
| 타인 닉네임으로 변경 | 409 `M003` |
| 자기 현재 닉네임으로 변경 | 200 |
| 닉네임 1자 | 400 `C001` |
| 토큰 없이 `/me` 접근 | 401 `A001` |

---

### M-09 비밀번호 변경과 탈퇴 [기능 · member 트랙]

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-08 |
| 공유 파일 | `MemberService`, `MemberController` — **M-08 완료 후 시작** |
| 참조 | [../requirements/member.md §1 §3](../requirements/member.md) (M-09, M-10), [../adr/0006 §예외](../adr/0006-auth-inside-member-service.md) |

**산출물**
- `member/dto/PasswordChangeRequest.java`, `WithdrawRequest.java`
- `MemberService`·`MemberController` 확장

**`RefreshTokenRepository` 참조가 허용된다.** [../adr/0006 §예외](../adr/0006-auth-inside-member-service.md)가 토큰 무효화 목적에 한해 명시적으로 허용한다. 삭제 연산만 쓴다.

**완료 기준**
- [ ] `PATCH /api/v1/members/me/password`가 204를 반환한다
- [ ] 현재 비밀번호 불일치 시 400 `M005`
- [ ] 새 비밀번호가 BCrypt로 해싱되어 저장된다 (`Member.changePassword()` 사용)
- [ ] **비밀번호 변경 시 Refresh Token이 삭제된다**
- [ ] `DELETE /api/v1/members/me`가 `deleted = true`로 변경한다 (`Member.withdraw()` 사용, 행 삭제 아님)
- [ ] 탈퇴 시 Refresh Token이 삭제된다
- [ ] `auth`의 서비스·컨트롤러·DTO를 참조하지 않는다 (리포지토리만)

**검증** — `MemberServiceTest`, `MemberControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 비밀번호 변경 | 204, 새 비밀번호로 로그인 가능 |
| 현재 비밀번호 불일치 | 400 `M005` |
| 변경 후 `refresh_token` 행 | 삭제됨 |
| 새 비밀번호 형식 오류 | 400 `C001` |
| 정상 탈퇴 | 204, `deleted = true`, 행 존재 |
| 탈퇴 후 로그인 | 401 |
| 탈퇴 시 `refresh_token` 행 | 삭제됨 |

---

### M-10 회원 프로필 조회와 내부 API [기능 · member 트랙]

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-09 |
| 공유 파일 | `MemberController` — **M-09 완료 후 시작** |
| 참조 | [../requirements/member.md §1 §5](../requirements/member.md) (M-11, M-12), [../api-contract.md §4](../api-contract.md), [../security.md §6](../security.md) |

**산출물**
- `member/dto/MemberProfileResponse.java`
- `internal/dto/MemberBulkRequest.java`, `MemberSummaryResponse.java`
- `internal/controller/InternalMemberController.java`
- `internal/service/InternalMemberService.java`
- `global/security/InternalApiKeyFilter.java`

`/internal/**` 경로의 인가 설정은 M-04 산출물이다. 필터 등록만 이 항목에서 한다.

**완료 기준**
- [ ] `GET /api/v1/members/{id}`가 공개 정보(닉네임, 가입일)만 반환한다. **이메일 미포함**
- [ ] **`GET /members/me`가 `GET /members/{id}`보다 먼저 매칭된다** (`me`가 id로 해석되지 않는다)
- [ ] `POST /internal/v1/members/bulk`가 [../api-contract.md §4](../api-contract.md) 형식으로 응답한다
- [ ] 탈퇴 회원은 `deleted: true`, 닉네임 `"탈퇴한 회원"`
- [ ] 내부 API 응답에 이메일·비밀번호가 없다
- [ ] `X-Internal-Api-Key` 없이 호출하면 거부된다
- [ ] 내부 API 키가 환경변수로 주입된다

**검증** — `MemberControllerTest`, `InternalMemberControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 회원 프로필 조회 | 200, `email` 키 없음 |
| **`GET /members/me` (유효 토큰)** | **내 정보 반환** (`me`를 id로 해석하지 않음) |
| 정상 벌크 조회 (3건) | 200, 3건 반환 |
| 존재하지 않는 id 포함 | 해당 id는 결과에서 제외 |
| 탈퇴 회원 포함 | `deleted: true`, 닉네임 `"탈퇴한 회원"` |
| 응답 본문 | `email`, `password` 키 없음 |
| API 키 없이 / 잘못된 키 | 401 또는 403 |

---

### M-11 마무리 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-07, M-10 |
| 참조 | [../nfr.md](../nfr.md), [../tech-stack.md §5](../tech-stack.md) |

**산출물**
- `README.md` 갱신 (실행 절차, 환경변수 목록)
- Actuator 설정 (`/actuator/health`만 노출)
- `application-prod.yml` (Swagger·SQL 로그 비활성화)

**완료 기준**
- [ ] `README.md`에 로컬 실행 절차와 필요한 환경변수가 모두 적혀 있다
- [ ] `/actuator/health`가 동작하고 그 외 엔드포인트는 노출되지 않는다
- [ ] `prod` 프로파일에서 Swagger UI가 비활성화된다
- [ ] `prod` 프로파일에서 SQL 로그가 꺼진다
- [ ] 전체 테스트가 통과한다 (`./gradlew test`)
- [ ] 커밋된 파일에 비밀 값이 없다

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| `/actuator/health` | 200, `{"status":"UP"}` |
| `/actuator/env` | 404 또는 403 |
| `prod` 프로파일로 `/swagger-ui.html` | 404 |
| `git log -p`에서 키·비밀번호 검색 | 없음 |

## 4. board-service 작업 항목

### B-01 프로젝트 스캐폴딩 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | 없음 |
| 병렬 | M-01과 동시 진행 (다른 저장소) |
| 참조 | [../tech-stack.md §1 §3](../tech-stack.md), [../conventions.md §1.2](../conventions.md) |

**산출물**
- `build.gradle`, `settings.gradle`, Gradle Wrapper
- `src/main/java/com/example/board/BoardApplication.java`
- `application.yml`, `application-local.yml`
- `global/config/QuerydslConfig.java` (`JPAQueryFactory` 빈)
- `.gitignore`

의존성을 여기서 전부 확정한다.

**완료 기준**
- [ ] `./gradlew build`가 성공한다
- [ ] 8082 포트에 기동된다
- [ ] QueryDSL Q타입이 생성되고 `.gitignore`에 생성 경로가 있다
- [ ] [../tech-stack.md §3.1 §3.2](../tech-stack.md)의 의존성이 전부 선언되어 있다
- [ ] DB 접속 정보가 환경변수로 외부화되어 있다
- [ ] 시간대가 `Asia/Seoul`로 명시 설정되어 있다

**검증** — `BoardApplicationTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 컨텍스트 로딩 | 예외 없이 기동 |
| `JPAQueryFactory` 빈 | 주입됨 |
| `TimeZone.getDefault()` | `Asia/Seoul` |

---

### B-02 공통 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-01 |
| 참조 | [../api-contract.md §6 §7.1 §7.3](../api-contract.md), [../domain-model.md §1.1](../domain-model.md), [../conventions.md §6 §7](../conventions.md) |

**산출물**
- `global/common/ApiResponse.java`, `ErrorResponse.java`, `PageResponse.java`
- `global/common/BaseTimeEntity.java`
- `global/error/ErrorCode.java` (C001~C005, A001~A004, **P001, P002, CM001, CM002, S001**)
- `global/error/BusinessException.java`, `GlobalExceptionHandler.java`
- `global/config/JpaConfig.java`, `SwaggerConfig.java`

M-02와 같은 파일을 만들되 `ErrorCode`는 board 전용 코드를 쓴다.

**완료 기준**
- [ ] `ApiResponse`, `ErrorResponse`, `PageResponse`, `BaseTimeEntity`가 member-service와 **구조가 동일**하다
- [ ] `ErrorCode`에 member 전용 코드(`M0xx`)가 **없다**
- [ ] 코드·HTTP·메시지가 [../api-contract.md §7.1 §7.3](../api-contract.md)과 일치한다
- [ ] 복제 파일 상단에 정본 주석이 있다
- [ ] `/swagger-ui.html`이 열린다

**검증** — `GlobalExceptionHandlerTest` (`@WebMvcTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| `BusinessException(P001)` | 404 `P001` |
| `BusinessException(P002)` | 403 `P002` |
| `@Valid` 실패 | 400 `C001`, `fieldErrors` 존재 |
| 성공 응답 | `success = true`, `error = null` |
| 예상치 못한 예외 | 500 `C005`, 스택트레이스 없음 |

---

### B-03 도메인 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-02 |
| 참조 | [../domain-model.md §3 §4](../domain-model.md), [../conventions.md §2](../conventions.md), [../requirements/board.md §3 §5](../requirements/board.md) |

**두 엔티티와 도메인 메서드를 여기서 전부 만든다.** 기능 단계에 남겨두면 여러 항목이 같은 엔티티 파일을 고치게 된다.

**산출물**
- `post/entity/Post.java`, `post/repository/PostRepository.java`
- `post/support/PostReader.java` (find or throw — `P001`)
- `comment/entity/Comment.java`, `comment/repository/CommentRepository.java`
- `db/migration/V1__create_post.sql`, `V2__create_comment.sql`

**도메인 메서드** — 전부 이 항목에서 구현한다.

| 메서드 | 동작 |
| --- | --- |
| `Post.update(title, content)` | 제목·내용 변경. `writerId`·`writerNickname` 불변 |
| `Post.softDelete()` | `deleted = true` |
| `Post.increaseViewCount()` | 조회수 +1 |
| `Post.increaseCommentCount()` / `decreaseCommentCount()` | 댓글 수 증감. **음수가 되지 않는다** |
| `Comment.update(content)` | 내용 변경 |
| `Comment.softDelete()` | `deleted = true` |

**`CommentRepository.softDeleteByPostId(Long postId)`를 여기서 만든다.** B-07(게시글 삭제)이 댓글을 연쇄 삭제할 때 쓴다. 이것이 없으면 B-07이 B-08의 산출물을 기다리게 된다.

**완료 기준**
- [ ] Flyway가 `post`, `comment` 테이블을 생성한다
- [ ] 컬럼이 [../domain-model.md §3](../domain-model.md)과 일치한다
- [ ] **`post.writer_id`, `comment.writer_id`에 FK 제약이 없다**
- [ ] `post.content`가 `TEXT` 타입이다
- [ ] `idx_post_created_at`, `idx_post_writer_id`, `idx_post_title`, `idx_comment_post_id`가 있다
- [ ] `view_count`, `comment_count` 기본값이 0이다
- [ ] 위 표의 도메인 메서드 6개가 모두 구현되어 있다
- [ ] `decreaseCommentCount()`가 0에서 호출돼도 음수가 되지 않는다
- [ ] `CommentRepository.softDeleteByPostId()`가 동작한다
- [ ] Entity에 `@Setter`·`@Data`가 없다

**검증** — `PostRepositoryTest`, `CommentRepositoryTest` (`@DataJpaTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| 저장 후 조회 | 모든 필드 일치 |
| **존재하지 않는 `writer_id`로 저장** | **성공** (FK 제약 없음) |
| 저장 시 | `viewCount=0`, `commentCount=0`, `deleted=false` |
| 10,000자 content 저장 | 성공 |
| `update()` 호출 | 제목·내용만 변경, `writerId` 불변 |
| `increaseViewCount()` 2회 | `viewCount = 2` |
| `increaseCommentCount()` 3회 후 `decrease` 1회 | `commentCount = 2` |
| **`decreaseCommentCount()` (count=0)** | **0 유지, 음수 아님** |
| `softDeleteByPostId()` | 해당 게시글의 댓글 전부 `deleted = true` |
| `PostReader`로 없는 id 조회 | `BusinessException(P001)` |

---

### B-04 보안 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-02 |
| 병렬 | B-03과 동시 진행 가능 (`global/*` vs `post/*`·`comment/*`) |
| 참조 | [../api-contract.md §3 §5](../api-contract.md), [../tech-stack.md §2.1](../tech-stack.md), [../security.md §2 §5](../security.md) |

**산출물**
- `global/security/LoginMember.java` (record: `memberId`, `nickname`, `role`)
- `global/security/RoleClaimConverter.java`
- `global/security/CurrentMemberArgumentResolver.java`, `@CurrentMember`
- `global/config/SecurityConfig.java` — **[../api-contract.md §3](../api-contract.md)의 전체 경로 인가**, CORS, STATELESS
- `src/main/resources/jwt-public.pem` (**테스트용 키 페어의 공개키**)
- `src/test/java/.../TestTokenFactory.java`

**Spring Security `oauth2-resource-server`를 사용한다. JWT 필터를 직접 만들지 않는다.**

실제 member-service 공개키로 교체하는 것은 I-01에서 한다. **M-04를 기다리지 않는다.**

**완료 기준**
- [ ] [../api-contract.md §5](../api-contract.md) 스펙의 토큰에서 `memberId`, `nickname`, `role`을 추출한다
- [ ] 서명이 잘못된 토큰 → 401 `A002`
- [ ] 만료된 토큰 → 401 `A003`
- [ ] 토큰 없이 보호 경로 → 401 `A001`
- [ ] `role` claim이 `GrantedAuthority`로 변환된다
- [ ] JWT 검증 필터를 직접 구현하지 않았다
- [ ] [../api-contract.md §3](../api-contract.md)의 **모든 경로**에 인가 규칙이 선언되어 있다
- [ ] 비로그인 허용 경로(`GET /posts`, `GET /posts/{id}`, 댓글 목록)가 토큰 없이 통과한다
- [ ] 세션이 생성되지 않는다

**검증** — `JwtAuthenticationTest` (`@SpringBootTest` + MockMvc)

| 케이스 | 기대 결과 |
| --- | --- |
| 유효 토큰으로 `POST /posts` | 401이 아님 |
| 토큰 없이 `POST /posts` | 401 `A001` |
| 서명 변조 토큰 | 401 `A002` |
| 만료 토큰 | 401 `A003` |
| `role = ADMIN` 토큰 | `ROLE_ADMIN` 권한 보유 |
| 토큰 없이 `GET /posts` | 401이 아님 |

---

### B-05 게시글 작성·상세 조회 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-03, B-04 |
| 참조 | [../requirements/board.md §1 §3 §4](../requirements/board.md) (P-01, P-04, P-05), [../api-contract.md §3](../api-contract.md) |

**산출물**
- `post/dto/PostCreateRequest.java`, `PostResponse.java`, `PostDetailResponse.java`
- `post/service/PostService.java` (생성)
- `post/controller/PostController.java` (생성)

**완료 기준**
- [ ] `POST /api/v1/posts`가 201을 반환한다
- [ ] **`writer_id`, `writer_nickname`을 JWT Claim에서 가져온다.** 요청 본문의 값을 쓰지 않는다
- [ ] 요청 본문에 `writerId`를 넣어도 무시된다
- [ ] `GET /api/v1/posts/{id}`가 상세를 반환한다 (비로그인 허용)
- [ ] 상세 조회 시 `view_count`가 1 증가한다 (`Post.increaseViewCount()` 사용)
- [ ] 삭제된 게시글·없는 id 조회 시 404 `P001`
- [ ] 제목 201자·내용 10,001자는 400 `C001`

**검증** — `PostServiceTest`, `PostControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 작성 | 201, DB 저장됨 |
| 저장된 `writer_id`/`writer_nickname` | JWT Claim 값과 일치 |
| 요청 본문에 `writerId: 999` 전달 | 저장된 값은 Claim의 `sub` |
| 토큰 없이 작성 | 401 `A001` |
| 상세 조회 (비로그인) | 200 |
| 상세 조회 2회 | `viewCount = 2` |
| 없는 id / 삭제된 게시글 | 404 `P001` |
| 제목 201자 / 공백만 | 400 `C001` |

---

### B-06 게시글 목록과 QueryDSL 검색 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-05 |
| 공유 파일 | `PostService`, `PostController` (B-05 생성) |
| 참조 | [../requirements/board.md §1 §6](../requirements/board.md) (P-02, P-03), [../api-contract.md §3.1 §6.1](../api-contract.md), [../nfr.md §1](../nfr.md) |

**산출물**
- `post/dto/PostSearchCondition.java`, `SearchType.java`, `PostSortType.java`
- `post/repository/PostQueryRepository.java` (QueryDSL)
- `PostService`·`PostController` 확장

**완료 기준**
- [ ] `GET /api/v1/posts`가 페이징 응답을 반환한다 ([../api-contract.md §6.1](../api-contract.md) 형식)
- [ ] 기본 `size` 10, 51 요청 시 50으로 절삭
- [ ] `sort=latest`, `sort=views`가 동작한다
- [ ] 삭제된 게시글이 목록에서 제외된다
- [ ] 4가지 `searchType`이 모두 동작한다
- [ ] `keyword`가 없으면 전체 목록
- [ ] `searchType`만 있고 `keyword`가 없으면 400 `C001`
- [ ] **목록 조회 시 member-service를 호출하지 않는다**
- [ ] 정렬 파라미터로 임의 컬럼명을 넣을 수 없다 (Enum 화이트리스트)

**검증** — `PostQueryRepositoryTest` (`@DataJpaTest`), `PostControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 15건 저장 후 목록 조회 | 10건, `totalElements = 15` |
| `size=51` | 50건 이하 |
| `sort=latest` / `sort=views` | 각각 내림차순 |
| 삭제 게시글 포함 상태 | 삭제분 제외 |
| `searchType=TITLE&keyword=공지` | 제목 포함분만 |
| `searchType=CONTENT` / `TITLE_CONTENT` | 각 기준 |
| `searchType=WRITER&keyword=홍길동` | `writer_nickname` 기준 |
| `keyword` 없이 조회 | 전체 |
| `searchType=TITLE`만 전달 | 400 `C001` |
| `sort=password` | 400 |

---

### B-07 게시글 수정·삭제와 권한 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-06 |
| 공유 파일 | `PostService`, `PostController` — B-06 완료 후 시작 |
| 참조 | [../requirements/board.md §1 §5 §7](../requirements/board.md) (P-06, P-07), [../security.md §5](../security.md) |

**산출물**
- `post/dto/PostUpdateRequest.java`
- `PostService`·`PostController` 확장

**게시글 삭제 시 댓글 연쇄 삭제**는 B-03이 만든 `CommentRepository.softDeleteByPostId()`를 호출한다. **B-08을 기다리지 않는다.**

**완료 기준**
- [ ] `PUT /api/v1/posts/{id}`를 작성자 본인만 수정할 수 있다 (`Post.update()` 사용)
- [ ] 타인이 수정 시 403 `P002`
- [ ] **ADMIN도 수정할 수 없다** (403 `P002`)
- [ ] `DELETE /api/v1/posts/{id}`를 작성자 본인과 ADMIN이 삭제할 수 있다
- [ ] 삭제는 Soft Delete다 (`Post.softDelete()`)
- [ ] **게시글 삭제 시 하위 댓글도 `deleted = true`가 된다**
- [ ] 소유자 검증이 Service 계층에 있다
- [ ] 수정 시 `writer_id`, `writer_nickname`이 바뀌지 않는다

**검증** — `PostServiceTest`, `PostControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 본인 글 수정 | 200, 반영됨 |
| 타인 글 수정 | 403 `P002` |
| **ADMIN이 타인 글 수정** | **403 `P002`** |
| 수정 후 `writer_id` | 변경 없음 |
| 본인 글 삭제 | 204, `deleted = true`, 행 존재 |
| ADMIN이 타인 글 삭제 | 204 |
| 타인(일반)이 삭제 | 403 `P002` |
| **게시글 삭제 후 하위 댓글** | **전부 `deleted = true`** |
| 없는 글 수정 | 404 `P001` |
| 토큰 없이 수정 | 401 `A001` |

---

### B-08 댓글 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-05 |
| 참조 | [../requirements/board.md §2 §5](../requirements/board.md) (C-01~C-04), [../domain-model.md §3.2 §4](../domain-model.md) |

**산출물**
- `comment/dto/*`
- `comment/service/CommentService.java`
- `comment/controller/CommentController.java`

`Comment` 엔티티·리포지토리는 B-03 산출물이다. **이 항목에서 만들지 않는다.** `comment/*`만 쓰므로 `PostService`를 건드리지 않는다.

**완료 기준**
- [ ] 댓글 작성 시 `post.comment_count`가 1 증가한다 (`Post.increaseCommentCount()` 사용)
- [ ] 댓글 삭제 시 1 감소한다
- [ ] **`comment_count`가 음수가 되지 않는다**
- [ ] 작성자 본인만 수정, 본인·ADMIN이 삭제할 수 있다
- [ ] 삭제는 Soft Delete다
- [ ] 작성자 정보를 JWT Claim에서 가져온다
- [ ] 없는 게시글에 댓글 작성 시 404 `P001`
- [ ] 댓글 목록이 등록순 페이징(기본 20)으로 반환된다

**검증** — `CommentServiceTest`, `CommentControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 댓글 작성 | 201, `comment_count = 1` |
| 댓글 3개 작성 후 1개 삭제 | `comment_count = 2` |
| 같은 댓글 2회 삭제 시도 | `comment_count` 음수 안 됨 |
| 목록 조회 | 등록순, 기본 20건 |
| 본인 댓글 수정 | 200 |
| 타인 댓글 수정 | 403 `CM002` |
| ADMIN이 타인 댓글 수정 | 403 `CM002` |
| ADMIN이 타인 댓글 삭제 | 204 |
| 없는 게시글에 댓글 | 404 `P001` |
| 501자 댓글 | 400 `C001` |

---

### B-09 내가 쓴 글과 마무리 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-07, B-08 |
| 공유 파일 | `PostService`, `PostController` |
| 참조 | [../requirements/board.md §1](../requirements/board.md) (P-08), [../nfr.md](../nfr.md) |

**산출물**
- `PostService`·`PostController` 확장 (내가 쓴 글)
- `README.md` 갱신, Actuator·`application-prod.yml`

**완료 기준**
- [ ] 내가 쓴 글 목록이 `writer_id` 기준으로 페이징 조회된다
- [ ] 삭제된 글은 제외된다
- [ ] `README.md`에 실행 절차와 환경변수가 적혀 있다
- [ ] `/actuator/health`만 노출된다
- [ ] `prod` 프로파일에서 Swagger·SQL 로그가 꺼진다
- [ ] 전체 테스트가 통과한다
- [ ] 목록 조회 쿼리에 N+1이 없다

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| 내 글 5건 + 타인 글 3건 | 5건만 반환 |
| 내 글 중 삭제분 포함 | 삭제분 제외 |
| 토큰 없이 호출 | 401 `A001` |
| 목록 조회 쿼리 수 | 게시글 수와 무관하게 일정 |
| `/actuator/env` | 404 또는 403 |

## 5. 다음 단계

M-11과 B-09가 모두 `done`이 되면 [integration.md](integration.md)로 넘어간다.
