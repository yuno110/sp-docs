---
title: 보안 설계
type: explanation
status: living
version: v1
updated: 2026-09-11
read_when: "인증·인가를 구현하거나, JWT 키를 다루거나, 권한 검증 위치를 정할 때"
related: [api-contract.md, adr/0004-rs256-over-hs256.md, tech-stack.md]
---
# 보안 설계

## 1. 공통 방침

| 항목 | 방침 |
| --- | --- |
| 비밀번호 저장 | BCrypt (`strength = 10`). member-service만 취급 |
| 인증 방식 | JWT Bearer Token, Stateless (`SessionCreationPolicy.STATELESS`) |
| Access Token | 만료 30분. `Authorization: Bearer {token}` |
| Refresh Token | 만료 14일. `member_db` 저장, 재발급 시 회전(Rotation) |
| CSRF | Stateless REST API이므로 비활성화 |
| CORS | 서비스별 화이트리스트로 관리. `*` 금지 |
| SQL Injection | JPA·QueryDSL 파라미터 바인딩. 네이티브 쿼리 문자열 결합 금지 |
| XSS | 서버는 원문 저장, 출력 이스케이프는 클라이언트 책임 |
| 민감정보 로깅 | 비밀번호·토큰·키를 로그에 남기지 않음 |

## 2. 서명 알고리즘 — RS256

member-service가 **개인키로 서명**하고, board-service는 **공개키로 검증만** 한다. board-service에는 서명 권한을 주지 않는다.

| 서비스 | 보유 키 | 가능한 일 |
| --- | --- | --- |
| member | 개인키 (`JWT_PRIVATE_KEY`) | 토큰 발급·검증 |
| board | 공개키 (`jwt-public.pem`) | 검증만 |

HS256을 쓰지 않는 이유는 [adr/0004](adr/0004-rs256-over-hs256.md)에 있다.

**구현은 Spring Security 표준을 쓴다.** JWT 필터·검증기를 직접 만들지 않는다([tech-stack.md §2](tech-stack.md)).

## 3. 키 관리

| 항목 | 규칙 |
| --- | --- |
| 개인키 주입 | 환경변수 `JWT_PRIVATE_KEY`. 기본값을 두지 않는다(없으면 기동 실패) |
| 공개키 배포 | board-service 리소스 파일(`classpath:jwt-public.pem`). 커밋 가능 |
| Git | `private.pem`, `*.env`를 `.gitignore`에 등록한다 (스캐폴딩 시 선행 조치) |
| 환경 분리 | 개발용 키와 운영용 키를 분리한다. 운영 개인키는 시크릿 저장소에서만 주입 |
| 키 회전 | JWT header에 `kid`를 포함한다. 키 재생성 시 기존 토큰은 모두 무효화되어 전 사용자 재로그인이 필요하다 |

공개키가 유출돼도 토큰을 위조할 수 없으므로 저장소에 두어도 된다. **개인키는 어떤 경우에도 커밋하지 않는다.**

## 4. 인증 흐름

```
[로그인]  member-service
  POST /api/v1/auth/login (email, password)
    -> 회원 조회 + BCrypt.matches()
    -> 개인키(RS256)로 Access/Refresh 서명
       Claim: { sub, nickname, role, iss, iat, exp }   <- api-contract.md §5
    -> RefreshToken member_db upsert
    <- TokenResponse

[게시글 작성]  board-service   (member-service 호출 없음)
  POST /api/v1/posts (Authorization: Bearer AT)
    -> Spring Security가 공개키로 서명 검증
    -> Claim에서 LoginMember(memberId, nickname, role) 추출
    -> writerId/writerNickname 스냅샷과 함께 저장
    <- 201 Created

[재발급]  member-service
  POST /api/v1/auth/reissue (refreshToken)
    -> 서명·만료 검증 + member_db 저장값 일치 확인
    -> 새 Access/Refresh 발급, 저장된 Refresh 교체(Rotation)
```

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
    if (!post.getWriterId().equals(member.memberId())) {
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

board-service는 JWT Claim의 `sub`·`role`만으로 판정한다. member-service에 권한을 되묻지 않는다.

## 6. 내부 API 보호

| 계층 | 통제 |
| --- | --- |
| 네트워크 | `/internal/**`을 외부 라우팅에서 제외. 운영은 내부망·보안그룹으로 격리 |
| 애플리케이션 | `X-Internal-Api-Key` 헤더 검증 필터. 키는 환경변수 주입 |

## 7. 구현 시 주의

- 비밀번호는 어떤 응답에도 넣지 않는다. 내부 API 응답도 마찬가지다
- 회원 탈퇴·비밀번호 변경 시 Refresh Token을 삭제한다
- 로그인 실패 5회 잠금은 2차 범위다. 1차에서는 구현하지 않는다
- 실패를 조용히 통과시키지 않는다. 키가 없거나 검증기가 구성되지 않으면 **기동이 실패해야** 한다
