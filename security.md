---
title: 보안 설계
type: explanation
status: living
version: v2
updated: 2026-09-15
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
| CORS | 서비스별 화이트리스트로 관리. `*` 금지 |
| SQL Injection | JPA·QueryDSL 파라미터 바인딩. 네이티브 쿼리 문자열 결합 금지 |
| XSS | 서버는 원문 저장, 출력 이스케이프는 클라이언트 책임 |
| 민감정보 로깅 | 비밀번호·토큰·키를 로그에 남기지 않음 |

## 2. 서명 알고리즘 — RS256

**auth-service가 개인키로 서명하고, member·board는 공개키로 검증만** 한다. 발급 주체는 하나여야 한다.

| 서비스 | 보유 키 | 가능한 일 |
| --- | --- | --- |
| auth | 개인키 (`JWT_PRIVATE_KEY`) | 토큰 발급·검증 |
| member | 공개키 (`jwt-public.pem`) | 검증만 |
| board | 공개키 (`jwt-public.pem`) | 검증만 |

**member·board에는 서명 의존성(`spring-security-oauth2-jose`)을 넣지 않는다**([tech-stack.md §3.2](tech-stack.md)). 넣으면 키만 있으면 토큰을 만들 수 있게 되어 이 경계가 흐려진다.

HS256을 쓰지 않는 이유는 [adr/0004](adr/0004-rs256-over-hs256.md)에 있다.

**구현은 Spring Security 표준을 쓴다.** JWT 필터·검증기를 직접 만들지 않는다([tech-stack.md §2](tech-stack.md)).

## 3. 키 관리

| 항목 | 규칙 |
| --- | --- |
| 개인키 주입 | 환경변수 `JWT_PRIVATE_KEY`. 기본값을 두지 않는다(없으면 기동 실패) |
| 개인키 보유 | **auth-service 하나뿐이다.** member·board에 두지 않는다 |
| 공개키 배포 | **member·board 두 곳**의 리소스 파일(`classpath:jwt-public.pem`). 커밋 가능 |
| 공개키 동기 | 두 사본이 같은 키인지 통합 검증에서 확인한다([plan/integration.md](plan/integration.md) I-01) |
| Git | `private.pem`, `*.env`를 `.gitignore`에 등록한다 (스캐폴딩 시 선행 조치) |
| 환경 분리 | 개발용 키와 운영용 키를 분리한다. 운영 개인키는 시크릿 저장소에서만 주입 |
| 키 회전 | JWT header에 `kid`를 포함한다. 키 재생성 시 기존 토큰은 모두 무효화되어 전 사용자 재로그인이 필요하다 |

공개키가 유출돼도 토큰을 위조할 수 없으므로 저장소에 두어도 된다. **개인키는 어떤 경우에도 커밋하지 않는다.**

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

## 5. 인가

### 5.1 판정 위치

| 판정 | 위치 |
| --- | --- |
| 인증 필요 여부(경로별) | `SecurityFilterChain`의 `permitAll` / `authenticated` |
| ADMIN 여부 | `role` claim 기반 `GrantedAuthority` |
| **소유자 검증(본인 글인가)** | **Service 계층** |

소유자 검증을 Controller나 Security 설정에 두지 않는다. 리소스를 조회해야 판정할 수 있기 때문이다.

```java
// PostService
private void validateOwner(Post post, LoginMember member) {
    if (!post.getWriterId().equals(member.accountId())) {
        throw new BusinessException(ErrorCode.POST_FORBIDDEN);   // P002
    }
}
```

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
| 최대 노출 시간 | Access Token 만료까지 (30분) |
| 재발급으로 연장되는가 | 아니다 — 탈퇴 시 RefreshToken 삭제 + `deleted` 검사(§4) |
| 잔여 권한 | 그 `role`이 가진 **모든 변경 권한**. ADMIN이면 **타인 글·댓글 삭제 포함** |
| 새 글 작성 | 통상 막힌다(프로필 `deleted`). 확인–커밋 창에서는 통과할 수 있다 |
| 프로필 재생성 | 막힌다(`uk_member_account_id`) |

**"자기 글만"이 아니다.** ADMIN 계정의 탈퇴·권한 회수는 30분의 노출을 동반한다.

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
