---
title: 계정·회원 기능 요구사항
type: requirements
status: frozen
version: v3
updated: 2026-09-15
read_when: "auth-service·member-service의 기능을 구현하거나 완료 기준을 확인할 때"
related: [../api-contract.md, ../domain-model.md, ../security.md, ../adr/0012-auth-as-separate-service.md]
---
# 계정·회원 기능 요구사항

담당 서비스: **auth-service** (`yuno110/sp-auth`) + **member-service** (`yuno110/sp-member`)

**요구사항은 사용자가 보는 기능 단위다.** 가입·탈퇴처럼 한 기능이 두 서비스에 걸치므로 문서를 나누지 않는다. 어느 서비스가 구현하는지는 아래 표의 "담당" 열과 [../plan/phase1.md](../plan/phase1.md)의 작업 항목(`AU-xx` / `M-xx`)이 정한다.

서비스 경계의 근거는 [../adr/0012](../adr/0012-auth-as-separate-service.md)다. **계정**(이메일·비밀번호·권한)은 auth, **프로필**(닉네임)은 member가 소유한다.

## 1. 기능 목록

| ID | 기능 | 담당 | 상세 | 차수 |
| --- | --- | --- | --- | --- |
| MR-01 | 회원가입 | **auth + member** | **2단계.** 계정 생성(이메일·비밀번호) → 로그인 → 프로필 등록(닉네임). §4 | 1차 |
| MR-02 | 이메일 중복 확인 | auth | 계정 생성 전 사용 가능 여부 조회 | 1차 |
| MR-03 | 닉네임 중복 확인 | member | 프로필 등록 전 사용 가능 여부 조회 | 1차 |
| MR-04 | 로그인 | auth | 이메일+비밀번호 검증 후 Access/Refresh 발급. **탈퇴 계정 거부** | 1차 |
| MR-05 | 토큰 재발급 | auth | Refresh 검증 후 재발급, Rotation. **탈퇴 계정 거부**, 경합 방지 §6 | 1차 |
| MR-06 | 로그아웃 | auth | 저장된 Refresh Token 삭제 | 1차 |
| MR-07 | 내 정보 조회 | **auth + member** | 계정 정보(이메일·가입일)와 프로필(닉네임)이 갈라진다. §5 | 1차 |
| MR-08 | 닉네임 변경 | member | 중복 검사 후 갱신. **토큰을 반환하지 않는다.** §7 | 1차 |
| MR-09 | 비밀번호 변경 | auth | 현재 비밀번호 검증 후 변경. Refresh Token 삭제 | 1차 |
| MR-10 | 회원 탈퇴 | **auth + member** | **2단계.** 계정 탈퇴(비밀번호 재확인) → 프로필 탈퇴. §8 | 1차 |
| MR-11 | 특정 회원 프로필 조회 | member | 공개 정보(닉네임, 가입일)만 반환 | 1차 |
| MR-12 | 내부 API — 프로필 벌크 조회 | member | board-service 전용. **1차부터 호출된다.** §9 | 1차 |
| MR-13 | 회원 목록 조회 | member | ADMIN 전용, 페이징(QueryDSL) | 2차 |

엔드포인트는 [../api-contract.md §2·§3](../api-contract.md)이 정본이다.

**MR-01·MR-07·MR-10 셋이 두 서비스에 걸친다.** 나머지는 한 서비스 안에서 끝난다.

## 2. 입력 검증

| 항목 | 규칙 | 메시지 |
| --- | --- | --- |
| email | 이메일 형식, 최대 100자 | "올바른 이메일 형식이 아닙니다." |
| password | 8~20자, 영문·숫자·특수문자 각 1자 이상 | "비밀번호는 8~20자의 영문, 숫자, 특수문자 조합이어야 합니다." |
| nickname | 2~10자, 한글/영문/숫자 | "닉네임은 2~10자여야 합니다." |

검증 실패는 `C001`(400)로 응답하고 `fieldErrors`에 필드별 메시지를 담는다.

## 3. 비즈니스 규칙

| # | 규칙 | 담당 |
| --- | --- | --- |
| 1 | 탈퇴한 계정(`account.deleted = true`)의 이메일은 재가입에 재사용할 수 없다. 행이 남고 `uk_account_email`이 UNIQUE이므로 자연히 보장된다 | auth |
| 2 | 비밀번호는 어떤 응답에도 포함하지 않는다. 내부 API 응답도 마찬가지다 | auth |
| 3 | **"계정만 있고 프로필이 없는 상태"는 정상이다.** 그 상태에서 로그인·재발급·로그아웃·계정 탈퇴가 모두 가능하다. 글·댓글 작성만 막힌다 | 공통 |
| 4 | 비밀번호 변경·계정 탈퇴 시 Refresh Token을 삭제한다. **두 연산은 한 로컬 트랜잭션이다** | auth |
| 5 | 로그인·재발급은 `account.deleted = false`를 검사한다. 검사하지 않으면 탈퇴 계정이 토큰을 계속 갱신한다 | auth |
| 6 | 프로필의 세 상태(미등록 / 활성 / 탈퇴)를 구분한다. 미등록과 탈퇴를 같은 "없음"으로 처리하면 탈퇴한 프로필이 재생성된다 | member |
| 7 | 프로필 등록은 `accountId` 기준 멱등이다. `account_id`는 **검증된 JWT의 `sub`에서만** 가져온다. 요청 본문의 식별자를 신뢰하지 않는다 | member |
| 8 | 프로필 soft delete 시 `nickname`을 NULL로 비운다. `"탈퇴한 회원"`은 **응답 시 변환이지 저장이 아니다** | member |
| 9 | 로그인 실패 5회 잠금은 2차 범위다. 1차에서 구현하지 않는다 | auth |
| 10 | 탈퇴 회원의 게시글은 board-service가 스냅샷 닉네임을 그대로 노출한다. 1차에서 board에 알리지 않는다 | 공통 |

**폐기된 규칙** — 이전 v2의 규칙 3 "닉네임 변경 시 새 Access Token을 함께 반환한다"는 폐기됐다. JWT Claim에 `nickname`이 없으므로([../api-contract.md §6](../api-contract.md)) 토큰이 낡을 이유가 사라졌다. 근거는 [../adr/0012](../adr/0012-auth-as-separate-service.md) §3이다.

## 4. MR-01 상세 — 가입은 2단계다

```
1. POST /api/v1/accounts     (auth,   무인증)  email, password  -> accountId
2. POST /api/v1/auth/login   (auth,   무인증)  -> accessToken, refreshToken
3. POST /api/v1/members      (member, 인증)    nickname
```

**원자적 가입을 요구하지 않는다.** 분산 트랜잭션을 피하는 대신 "계정만 있는 상태"를 정상 상태로 받아들인다(규칙 3).

3단계는 멱등이다. 응답만 유실된 클라이언트가 재시도해도 중복 생성·덮어쓰기가 없다. 상태별 응답은 [../api-contract.md §3](../api-contract.md)에 있다.

**미완료 가입 계정을 정리하지 않는다.** auth는 프로필 존재를 모르므로 스스로 판단할 수 없다. 이메일은 계정 생성 시점에 선점되고 해제되지 않는다. 1차의 알려진 제약이다.

## 5. MR-07 상세 — 내 정보는 두 곳에 있다

| 무엇 | 어디 |
| --- | --- |
| 이메일, 가입일 | `GET /api/v1/accounts/me` (auth) |
| 닉네임 | `GET /api/v1/members/me` (member) |

**member는 이메일을 반환할 수 없다.** 소유하지 않기 때문이다. 화면 하나에 둘 다 필요하면 클라이언트가 두 번 호출한다. member가 auth를 호출해 합치지 않는다 — 호출 방향은 `board → member` 하나뿐이다([../adr/0012](../adr/0012-auth-as-separate-service.md) §1).

`GET /api/v1/members/me`는 **프로필이 없으면 404 `M001`**이다. 이것은 오류가 아니라 가입 3단계 미완료를 뜻한다. 클라이언트는 프로필 등록 화면으로 보낸다.

## 6. MR-05 상세 — 재발급의 경합

재발급은 **RefreshToken 조회와 `account.deleted` 확인을 같은 트랜잭션에서** 한다. 회전은 조건부 UPDATE(affected rows 확인)로 처리한다.

그렇게 하지 않으면 다음이 성립한다.

```
R1) 재발급:  RefreshToken 조회      -> 존재, 계정 활성
D1) 탈퇴:    account.deleted = true;  RefreshToken 삭제;  COMMIT
R2) 재발급:  옛 행 삭제; 새 행 INSERT;  COMMIT      <- 삭제한 행이 되살아난다
```

R2 이후 탈퇴한 계정에 새 RefreshToken(14일)이 생겨, **"탈퇴 후 최대 30분"이라는 경계가 무너진다.**

## 7. MR-08 상세 — 닉네임 변경

```
PATCH /api/v1/members/me   { "nickname": "새닉네임" }

1. 닉네임 중복 검사 (M003)
2. member.nickname 갱신
3. 갱신된 프로필 반환
```

**토큰을 반환하지 않는다.** 일반적인 수정 API와 같다.

이전 v2는 "새 Access Token을 함께 반환"하도록 요구했다. Claim에 `nickname`이 있어서 낡을 수 있었기 때문이다. 이제 Claim에 없으므로 **요구 자체가 소멸했다.** member는 개인키를 갖지 않으므로 토큰을 발급할 수도 없다.

닉네임 변경이 과거 게시글에 반영되지 않는 것은 여전히 **의도된 동작**이다([board.md §3](board.md) 규칙 4, [../adr/0003](../adr/0003-writer-snapshot.md)).

## 8. MR-10 상세 — 탈퇴는 2단계다. 계정이 먼저다

```
1. DELETE /api/v1/accounts/me   (auth)    비밀번호 재확인
                                          -> account.deleted = true + RefreshToken 삭제
                                             [한 로컬 트랜잭션]
2. DELETE /api/v1/members/me    (member)  프로필 deleted = true, nickname = NULL
```

둘 다 멱등이다(이미 삭제됐으면 204).

**순서를 바꾸지 않는다.** 프로필을 먼저 지우면 (a) member는 비밀번호를 갖지 않으므로 **재확인이 구조적으로 불가능해지고**, (b) 중간 실패 시 프로필이 비가역으로 파괴된 채 계정은 영구히 살아 있게 된다. 전체 비교는 [../adr/0012](../adr/0012-auth-as-separate-service.md) §5에 있다.

**2단계는 1단계에서 쓰던 Access Token으로 수행한다.** member는 계정 상태를 모르므로(오프라인 검증) 토큰이 유효한 동안 통과한다.

**탈퇴 완료는 2단계까지다.** 다만 이것은 클라이언트 측 규약이며 서버가 강제하지 못한다. 2단계가 수행되지 않으면 프로필 행이 남아 닉네임이 선점된 채로 남는다. 1차에는 이를 관측·정리하는 수단이 없다(알려진 제약).

## 9. MR-12 상세 — 내부 API

board-service가 호출하는 서비스 간 전용 API다. 요청·응답 형식과 실패 판정은 [../api-contract.md §5](../api-contract.md)가 정본이다.

- **벌크 하나만 제공한다.** 단건 전용 API를 따로 두지 않는다. 1건만 필요한 호출도 벌크에 1건을 담는다
- 키는 `accountId`다
- 탈퇴 프로필은 `deleted: true`와 함께 닉네임을 `"탈퇴한 회원"`으로 반환한다. **응답 시 변환이다**(규칙 8)
- **존재하지 않는 `accountId`는 결과에서 제외한다.** 404를 반환하지 않는다
- 비밀번호·이메일을 반환하지 않는다. member는 애초에 갖고 있지 않다
- **1차부터 board가 호출한다.** 글·댓글 생성 시 작성자 닉네임 스냅샷을 얻기 위해서다([../adr/0012](../adr/0012-auth-as-separate-service.md) §6)

## 10. 기본 관리자 계정 — seed가 두 DB에 걸친다

ADMIN은 **계정과 프로필을 모두** 가져야 한다. 두 스키마에 각각 seed를 넣는다.

| 스키마 | 스크립트 | 내용 |
| --- | --- | --- |
| `sp_auth` | `V3__seed_admin_account.sql` | `account` 1행. **id를 명시적으로 고정한다** |
| `sp_member` | `V2__seed_admin_profile.sql` | `member` 1행. `account_id`는 위에서 고정한 값 |

**`account.id`를 AUTO_INCREMENT에 맡기지 않는다.** 두 스키마가 서로를 조회할 수 없으므로, member의 seed가 참조할 값이 결정적이어야 한다. `INSERT INTO account (id, ...) VALUES (1, ...)`처럼 명시한다.

- 두 seed의 `accountId` 일치는 통합 검증에서 확인한다([../plan/integration.md](../plan/integration.md) I-01)
- 개발용 비밀번호는 운영 배포 전에 교체해야 한다
- seed 스크립트에 평문 비밀번호를 두지 않는다. BCrypt 해시로 넣는다
