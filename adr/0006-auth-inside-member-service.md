---
title: auth를 member-service 내 패키지로
type: adr
status: superseded
version: v2
updated: 2026-09-15
read_when: "auth를 한때 member 내부에 두기로 했던 이유와 그 결정이 뒤집힌 경위가 궁금할 때"
related: [README.md, ../conventions.md, ../api-contract.md]
---
# 0006. auth를 member-service 내 패키지로

## 상태
**superseded — [0012](0012-auth-as-separate-service.md)가 대체한다 (2026-09-15)**

> 이 문서는 기록으로 남긴다. **현행 결정은 [0012](0012-auth-as-separate-service.md)다.**
>
> 아래 내용은 서비스가 둘이던 시점의 판단이다. 0012가 이 문서의 근거 넷을 하나씩 정산했다 — 첫째(로그인마다 동기 호출)는 해소됐고, 둘째(가입 분산 트랜잭션)는 원자적 가입 요구를 포기해 회피했으며, 셋째(탈퇴 원자성)는 **여전히 미해결**이고, 넷째(운영 부담)는 그대로 남는다.
>
> 아래 **§예외 — 토큰 무효화**는 사문화됐다. 비밀번호 변경·탈퇴 시의 토큰 무효화가 전부 auth-service 내부 연산이 되어, `member`가 `RefreshTokenRepository`를 참조할 이유가 사라졌다.

## 맥락

인증(authentication)과 회원 관리(account management)는 성격이 다른 관심사다. 인증은 "당신이 누구인지 증명"이고 회원 관리는 "계정·프로필 관리"다. 변경 빈도와 보안 요구도 다르다.

그렇다면 auth를 별도 마이크로서비스로 떼야 하는가?

## 결정

**같은 서비스 안에서 패키지로 분리하되, 별도 마이크로서비스로 나누지 않는다.**

## 근거

서비스 경계는 **데이터 소유권**으로 긋는다([0001](0001-msa-adoption.md)). auth와 member는 `member` 테이블 하나를 나눠 가질 수 없다.

| 분리를 시도하면 | 발생하는 문제 |
| --- | --- |
| auth-service가 로그인 처리 | 이메일·비밀번호·role이 member 테이블에 있으므로 **모든 로그인마다** auth → member 동기 호출. 금지하기로 한 강결합이 인증 경로 한복판에 생긴다 |
| auth-service가 credential 별도 소유 | 회원가입이 분산 트랜잭션이 된다. Saga 패턴 필요 — 1차에 과도 |
| 회원 탈퇴 | `member.deleted = true` + Refresh Token 삭제가 한 트랜잭션에서 처리되지 못한다 |
| 운영 | 서비스 3개 = 배포·모니터링 대상 1.5배 |

member/board를 나눈 것은 소유 데이터가 완전히 갈라지기 때문이다. auth는 그렇지 않다.

## 결정 내용

| | `auth` 패키지 | `member` 패키지 |
| --- | --- | --- |
| 관심사 | 인증 | 회원 리소스 관리 |
| 소유 엔티티 | `RefreshToken` | `Member` |
| 기능 | 로그인, 로그아웃, 재발급 | 가입, 조회, 수정, 탈퇴 |
| `Member` 접근 | 읽기 전용 (`MemberService` 경유) | 읽기·쓰기 |

**의존 방향은 `auth → member` 단방향이다.** `member` 패키지는 `auth`를 참조하지 않는다. 이 규칙을 지키면 훗날 auth를 별도 서비스로 승격시킬 때 잘라낼 지점이 이미 정해져 있다.

### 예외 — 토큰 무효화

**`member`는 비밀번호 변경·회원 탈퇴 시의 토큰 무효화에 한해 `auth.repository.RefreshTokenRepository`를 참조할 수 있다.**

[../requirements/member.md §3](../requirements/member.md) 규칙 4가 "비밀번호 변경·탈퇴 시 Refresh Token을 삭제한다"를 요구한다. 이 동작의 주체는 `member`이고 대상 데이터는 `auth` 소유이므로 단방향 규칙과 충돌한다.

대안을 검토했다.

| 방식 | 판단 |
| --- | --- |
| **예외 명시 (채택)** | 한 줄로 끝난다. 참조 지점이 두 곳(비밀번호 변경·탈퇴)으로 한정되어 추적 가능하다 |
| `ApplicationEvent` 구독 | 방향은 지켜지지만 같은 트랜잭션을 보장하려면 `@TransactionalEventListener(BEFORE_COMMIT)`이 필요하다. 1차에 들일 복잡도가 아니다 |
| `auth`가 노출한 메서드로 감싸기 | 참조는 그대로 남으므로 예외 명시와 실익이 같고 간접 계층만 는다 |

**예외의 범위**는 `RefreshTokenRepository`의 삭제 연산뿐이다. `member`가 `auth`의 서비스·컨트롤러·DTO를 참조하는 것은 여전히 금지한다. auth를 별도 서비스로 승격시킬 때 잘라낼 지점은 이 두 호출뿐이며, 그때는 이벤트 방식으로 전환한다.

> 이 예외를 명시하지 않으면 해당 작업 항목이 이 ADR과 [../plan/phase1.md](../plan/phase1.md) §2.5(소유 경계를 넘어야 할 때)에 끼여 반드시 한 번 멈춘다.

## 결과

**API 경로도 이 구분을 반영한다.**

| 경로 | 대상 |
| --- | --- |
| `/api/v1/auth/**` | 순수 인증 행위 — 로그인, 로그아웃, 재발급 |
| `/api/v1/members/**` | 회원 리소스 — 가입, 중복 확인, 내 정보, 탈퇴 |

회원가입은 "회원 리소스 생성"이므로 `POST /api/v1/members`다. 초기 검토안의 `/auth/signup`, `/auth/check-email`을 `members` 쪽으로 옮겼다.

## 재검토 조건

소셜 로그인(OAuth2), SSO, 외부 IdP 연동이 들어오거나 인증 대상 서비스가 여러 개로 늘어날 때. 그때는 Spring Authorization Server 같은 표준 구현을 별도 서비스로 세우는 편이 낫다.
