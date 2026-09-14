---
title: 회원 기능 요구사항
type: requirements
status: frozen
version: v2
updated: 2026-09-14
read_when: "member-service의 기능을 구현하거나 완료 기준을 확인할 때"
related: [../api-contract.md, ../domain-model.md, ../security.md]
---
# 회원 기능 요구사항

담당 서비스: member-service (`yuno110/sp-member`)

패키지 구분은 [../adr/0006-auth-inside-member-service.md](../adr/0006-auth-inside-member-service.md)를 따른다. `auth` = MR-04~MR-06, `member` = 나머지.

## 1. 기능 목록

| ID | 기능 | 상세 | 차수 |
| --- | --- | --- | --- |
| MR-01 | 회원가입 | 이메일·비밀번호·닉네임 입력. 중복 검사, BCrypt 해싱 후 저장 | 1차 |
| MR-02 | 이메일 중복 확인 | 가입 전 사용 가능 여부 조회 | 1차 |
| MR-03 | 닉네임 중복 확인 | 가입 전 사용 가능 여부 조회 | 1차 |
| MR-04 | 로그인 | 이메일+비밀번호 검증 후 Access/Refresh 발급 | 1차 |
| MR-05 | 토큰 재발급 | Refresh 검증 후 재발급, Rotation 적용 | 1차 |
| MR-06 | 로그아웃 | 저장된 Refresh Token 삭제 | 1차 |
| MR-07 | 내 정보 조회 | 인증된 본인 정보 반환 | 1차 |
| MR-08 | 내 정보 수정 | 닉네임 변경. **새 Access Token 함께 반환** | 1차 |
| MR-09 | 비밀번호 변경 | 현재 비밀번호 검증 후 변경. Refresh Token 무효화 | 1차 |
| MR-10 | 회원 탈퇴 | 비밀번호 재확인 → Soft Delete, Refresh Token 삭제 | 1차 |
| MR-11 | 특정 회원 프로필 조회 | 공개 정보(닉네임, 가입일)만 반환 | 1차 |
| MR-12 | 내부 API — 회원 벌크 조회 | board-service 전용 | 1차 |
| MR-13 | 회원 목록 조회 | ADMIN 전용, 페이징(QueryDSL) | 2차 |

엔드포인트는 [../api-contract.md §2](../api-contract.md)가 정본이다.

## 2. 입력 검증

| 항목 | 규칙 | 메시지 |
| --- | --- | --- |
| email | 이메일 형식, 최대 100자 | "올바른 이메일 형식이 아닙니다." |
| password | 8~20자, 영문·숫자·특수문자 각 1자 이상 | "비밀번호는 8~20자의 영문, 숫자, 특수문자 조합이어야 합니다." |
| nickname | 2~10자, 한글/영문/숫자 | "닉네임은 2~10자여야 합니다." |

검증 실패는 `C001`(400)로 응답하고 `fieldErrors`에 필드별 메시지를 담는다.

## 3. 비즈니스 규칙

| # | 규칙 |
| --- | --- |
| 1 | 탈퇴한 회원(`deleted = true`)의 이메일은 재가입에 재사용할 수 없다 |
| 2 | 비밀번호는 어떤 응답에도 포함하지 않는다. 내부 API 응답도 마찬가지다 |
| 3 | 닉네임 변경 시 새 Access Token을 함께 반환한다. Claim의 `nickname`이 낡으면 새 게시글에 옛 닉네임이 박제된다 |
| 4 | 비밀번호 변경·탈퇴 시 Refresh Token을 삭제한다 |
| 5 | 로그인 실패 5회 잠금은 2차 범위다. 1차에서 구현하지 않는다 |
| 6 | 탈퇴 회원의 게시글은 board-service가 스냅샷 닉네임을 그대로 노출한다. 1차에서 member-service가 board에 알리지 않는다 |

## 4. MR-08 상세 — 닉네임 변경

일반적인 수정 API와 다르게 **토큰을 함께 반환**한다.

```
PATCH /api/v1/members/me   { "nickname": "새닉네임" }

1. 닉네임 중복 검사 (M003)
2. member.nickname 갱신
3. 새 Access Token 발급 (Claim.nickname = 새닉네임)
4. 응답에 회원 정보 + 새 accessToken 포함
```

클라이언트는 받은 토큰으로 교체해야 한다. 배경은 [../architecture.md §4.2](../architecture.md)를 본다.

## 5. MR-12 상세 — 내부 API

board-service가 호출하는 서비스 간 전용 API다. 요청·응답 형식은 [../api-contract.md §4](../api-contract.md)가 정본이다.

- 벌크 조회를 제공한다. 단건 반복 호출용 API만 두지 않는다
- 탈퇴 회원은 `deleted: true`와 함께 닉네임을 `"탈퇴한 회원"`으로 반환한다
- 비밀번호·이메일을 반환하지 않는다
- 1차에서 board-service가 이 API를 호출하는 경로는 없다. 제공 측만 구현하고 2차에 대비한다

## 6. 기본 관리자 계정

Flyway seed로 ADMIN 1개를 생성한다.

- 개발용 비밀번호는 운영 배포 전에 교체해야 한다
- seed 스크립트에 평문 비밀번호를 두지 않는다. BCrypt 해시로 넣는다
