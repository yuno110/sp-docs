---
title: auth를 member-service 내 패키지로
type: adr
status: accepted
version: v1
updated: 2026-09-11
read_when: "인증을 별도 서비스로 분리하지 않은 이유가 궁금할 때"
related: [README.md, ../conventions.md, ../api-contract.md]
---
# 0006. auth를 member-service 내 패키지로

## 상태
accepted

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

## 결과

**API 경로도 이 구분을 반영한다.**

| 경로 | 대상 |
| --- | --- |
| `/api/v1/auth/**` | 순수 인증 행위 — 로그인, 로그아웃, 재발급 |
| `/api/v1/members/**` | 회원 리소스 — 가입, 중복 확인, 내 정보, 탈퇴 |

회원가입은 "회원 리소스 생성"이므로 `POST /api/v1/members`다. 초기 검토안의 `/auth/signup`, `/auth/check-email`을 `members` 쪽으로 옮겼다.

## 재검토 조건

소셜 로그인(OAuth2), SSO, 외부 IdP 연동이 들어오거나 인증 대상 서비스가 여러 개로 늘어날 때. 그때는 Spring Authorization Server 같은 표준 구현을 별도 서비스로 세우는 편이 낫다.
