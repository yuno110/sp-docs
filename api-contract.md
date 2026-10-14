---
title: API 계약
type: spec
status: frozen
version: v19
updated: 2026-10-14
read_when: "엔드포인트를 구현하거나, 요청·응답 형식·에러 코드·JWT Claim을 확인할 때"
related: [domain-model.md, security.md, requirements/member.md, requirements/board.md]
---
# API 계약

엔드포인트·응답 형식·에러 코드·토큰 Claim의 정본은 이 문서다.

**§6 JWT Claim은 세 서비스가 공유하는 계약 지점이다.** 발급은 auth 하나, 검증은 member·board 둘이다. 여기를 바꾸면 셋이 함께 바뀌어야 하므로 개정 시 세 서비스 담당이 모두 확인한다.

**§5 내부 API도 board와 member가 공유하는 계약 지점이다.** 1차부터 board가 쓰기 경로에서 호출한다([adr/0012](adr/0012-auth-as-separate-service.md) §6).

## 1. 경로 규칙

| 경로 | 서비스 | 주소(1차) |
| --- | --- | --- |
| `/api/v1/auth/**` | auth | `http://localhost:8083` |
| `/api/v1/accounts/**` | auth | `http://localhost:8083` |
| `/api/v1/members/**` | member | `http://localhost:8081` |
| `/api/v1/posts/**` | board | `http://localhost:8082` |
| `/api/v1/comments/**` | board | `http://localhost:8082` |
| `/internal/v1/members/**` | member | 서비스 간 호출 전용. 외부 노출 금지 |

업무 API가 아닌 경로(`/swagger-ui/**`, `/v3/api-docs/**`, `/actuator/**`)의 인가는 [security.md §5.1.1](security.md)이 정본이다. **선언하지 않으면 Boot 기본 필터가 401로 막는다.**

`/api/v1` 버저닝의 이유는 [adr/0008](adr/0008-api-versioning.md)을 본다.

경로를 셋으로 나눈 기준은 [adr/0012](adr/0012-auth-as-separate-service.md)에 있다.

| 접두어 | 무엇 |
| --- | --- |
| `auth` | 세션·토큰 행위 — 로그인, 재발급, 로그아웃 |
| `accounts` | **계정 리소스** — 생성, 이메일 중복 확인, 계정 조회, 비밀번호 변경, 계정 탈퇴 |
| `members` | **프로필 리소스** — 등록, 닉네임 중복 확인, 조회·수정, 프로필 탈퇴 |

**계정과 프로필은 다른 리소스다.** 이메일·비밀번호·권한은 `accounts`, 닉네임은 `members`다.

## 2. auth-service API

### 2.1 인증 (`auth`)

| Method | Path | 설명 | 인증 | 성공 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/auth/login` | 로그인, 토큰 발급 | - | 200 |
| POST | `/api/v1/auth/reissue` | 토큰 재발급(Rotation) | - | 200 |
| POST | `/api/v1/auth/logout` | 로그아웃 | O | 204 |

재발급의 응답 본문은 **로그인과 같은 `TokenResponse`**다(§9.2). 재발급 거부는 만료만 `A003`이고 나머지는 전부 `A002`다(§8.5) — 세션 없음·저장값 불일치·탈퇴 계정을 가르지 않는다.

`POST /api/v1/auth/logout`은 **멱등이다.** 저장된 Refresh Token이 없어도 204다.

**로그인은 400을 쓰지 않는다.** 자격증명 누락·빈 값·형식 오류도 **401 `AU003`**이다.

`LoginRequest`에 형식 검증을 걸지 않는다. 생성 쪽 규칙([requirements/member.md §2](requirements/member.md))을 복제하면 **규칙이 바뀌는 순간 기존 사용자가 잠긴다** — 옛 규칙으로 만든 비밀번호가 올바른데도 400으로 거부되고, 본인에게는 그것을 고칠 방법이 없다. 게다가 자격증명 필드의 형식 검증은 막을 수 있는 것이 없다. **형식이 틀린 비밀번호는 그냥 틀린 비밀번호이고, 대조가 그것을 끝낸다.**

> **이전 판은 근거를 "숨기려던 것이 드러난다"로 적었다. 그것은 성립하지 않아 정정했다.** `C001`과 `AU003`으로 갈리는 것은 MR-04가 숨기려는 사실(이메일의 존재)을 누출하지 않는다 — 비밀번호 정책은 공개되어 있으므로 "정책을 만족한다"는 정보량이 0이다. 규칙은 그대로 두고 근거만 바꿨다.

> **§2.3의 `check-email`과 다르다.** 그쪽은 형식 오류에 400 `C001`을 쓴다. 비대칭이 의도다 — 중복 확인은 숨길 것이 없고, 로그인은 있다.

로그인·재발급은 **`account.deleted = false`를 검사한다.** 재발급은 RefreshToken 조회와 상태 확인을 같은 트랜잭션에서 하고 회전을 조건부 UPDATE로 처리한다([adr/0012](adr/0012-auth-as-separate-service.md) §8).

### 2.2 계정 (`account`)

| Method | Path | 설명 | 인증 | 성공 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/accounts` | 계정 생성 (가입 1단계) | - | 201 |
| GET | `/api/v1/accounts/check-email?email=` | 이메일 중복 확인 (§2.3) | - | 200 |
| GET | `/api/v1/accounts/me` | 내 계정 조회 (이메일·가입일) | O | 200 |
| PATCH | `/api/v1/accounts/me/password` | 비밀번호 변경 | O | 204 |
| DELETE | `/api/v1/accounts/me` | **계정 탈퇴 (탈퇴 1단계)** | O | 204 |

`GET /api/v1/accounts/me`는 **이메일과 가입일 둘만 반환한다**([requirements/member.md §5](requirements/member.md) MR-07).

```json
// GET /api/v1/accounts/me  -> 200
{
  "success": true,
  "data": { "email": "user@example.com", "createdAt": "2026-09-11T10:00:00" },
  "error": null
}
```

| 필드 | |
| --- | --- |
| `email` | `account.email` |
| `createdAt` | `account.created_at`. 오프셋을 표기하지 않는다([tech-stack.md §6](tech-stack.md)). **소수부는 저장값에 따른다** — 운영에는 없고 H2 테스트에는 있다 |

**`accountId`를 넣지 않는다.** MR-07이 정하는 값은 둘이고, 식별자가 필요한 클라이언트는 `POST /api/v1/accounts`의 응답이나 `GET /api/v1/members/me`에서 이미 받는다(§3). 필드를 **나중에 더하는 것은 호환되지만 빼는 것은 아니므로**, 요구가 생길 때 더한다.

**`password`·`nickname`을 넣지 않는다.** 전자는 [security.md §7](security.md)이 금지하고, 후자는 **auth가 소유하지 않는 값**이다([adr/0012](adr/0012-auth-as-separate-service.md) §1). 닉네임이 필요한 화면은 `GET /api/v1/members/me`를 함께 호출한다.

`DELETE /api/v1/accounts/me`는 **본문에 현재 비밀번호를 받아 재확인한다.** `account.deleted = true`와 해당 계정의 RefreshToken 삭제를 한 로컬 트랜잭션으로 처리한다.

```json
// DELETE /api/v1/accounts/me
{ "password": "Passw0rd!" }
// 204 (본문 없음)
```

**자격증명 필드가 하나면 이름은 `password`다.** `LoginRequest`도 그렇다. `PATCH /me/password`만 `currentPassword`를 쓰는데, 거기에는 비밀번호가 **둘** 있어서 구별이 필요하기 때문이다 — 그것이 예외이고 이쪽이 기본이다.

검증 규칙은 `currentPassword`와 같다. **`@NotBlank`만 붙이고 `@Pattern`은 걸지 않는다**(§2.1의 잠금 이유).

| `password` | 응답 |
| --- | --- |
| 누락 · `null` · 빈 문자열 | **400 `C001`**, `fieldErrors`에 `password` |
| 값이 틀림 | **400 `AU004`.** `deleted`는 그대로 `false` |

**멱등이다 — 이미 탈퇴했으면 204다.** 그리고 **그때는 비밀번호를 검증하지 않는다.**

| 계정 상태 | 비밀번호 | 응답 |
| --- | --- | --- |
| 활성 | 맞음 | 204. `deleted = true`, RefreshToken 삭제 |
| 활성 | 틀림 | 400 `AU004` |
| **이미 탈퇴** | **맞든 틀리든** | **204.** 아무것도 바꾸지 않는다 |
| **행이 없음** (`sub`가 가리키는 계정 부재) | — | **404 `AU001`.** 멱등의 대상이 아니다 |

**"아무것도 바꾸지 않는다"는 RefreshToken도 포함한다.** 이미 탈퇴한 계정에 남은 토큰 행이 있어도 지우지 않는다.

> **그 상태가 생기는 경로는 하나다** — 로그인이 `authenticate()`를 지난 뒤 탈퇴가 커밋되면, 로그인이 탈퇴한 계정에 토큰 행을 INSERT할 수 있다([requirements/member.md §6](requirements/member.md)). **무해하다**: 재발급이 `deleted`를 같은 트랜잭션에서 검사하므로 그 토큰으로는 아무것도 못 한다. 정리 수단을 1차에 두지 않는다 — 탈퇴 재호출로 치우게 하면 "닫힌 계정에는 손대지 않는다"가 깨지고, 틀린 비밀번호로 온 요청이 쓰기를 하게 된다.

**`deleted` 검사가 비밀번호 비교보다 먼저다.** `PATCH /me/password`와 같은 순서이고, 결론만 반대다(그쪽은 404로 거부, 이쪽은 204로 통과). 이유도 같다 — **닫힌 행에 쓰기가 닿지 않아야 하고 `updated_at`이 움직이지 않아야 한다.** 재확인이 요구되는 것(MR-10)은 **계정을 닫는 행위**에 대한 것이고, 이미 닫힌 계정에는 보호할 상태가 없다.

`PATCH /api/v1/accounts/me/password`의 본문은 **현재 비밀번호와 새 비밀번호 둘**이다.

```json
// PATCH /api/v1/accounts/me/password
{ "currentPassword": "Passw0rd!", "newPassword": "NewPassw0rd!" }
// 204 (본문 없음)
```

| 필드 | 검증 |
| --- | --- |
| `currentPassword` | **`@NotBlank`만 붙인다. 형식(`@Pattern`) 검증은 걸지 않는다** |
| `newPassword` | [requirements/member.md §2](requirements/member.md)의 비밀번호 규칙. 위반은 400 `C001`, `fieldErrors`에 `newPassword` |

**자격증명 필드에서 금지되는 것은 형식 검증이고, 빈 값 검사는 아니다.** 둘을 가른다.

| 제약 | 자격증명 필드 | 왜 |
| --- | --- | --- |
| `@Pattern` (정책 규칙) | **금지** | 정책이 바뀌면 옛 규칙으로 만든 **올바른** 비밀번호가 거부된다 (§2.1) |
| `@NotBlank` | **요구** | 빈 값은 어떤 정책에서도 올바른 비밀번호가 아니다. 잠글 사용자가 없다 |

| `currentPassword` | 응답 |
| --- | --- |
| **누락 · `null` · 빈 문자열** | **400 `C001`**, `fieldErrors`에 `currentPassword` |
| 형식 위반 + 값 틀림 | **400 `AU004`** — 형식으로 가르지 않는다 |
| 값이 틀림 | **400 `AU004`** |

**현재 비밀번호 불일치는 400 `AU004`다.** 401이 아니다 — 요청자는 이미 인증되어 있고, 틀린 것은 본문의 값이다.

**누락이 `AU004`가 아닌 이유.** 그것은 형식 문제가 아니라 "필드를 보내지 않았다"이고, 저장된 비밀번호에 대해 아무것도 드러내지 않는다. 또 `AU004`의 메시지("현재 비밀번호가 일치하지 않습니다")는 **아무것도 보내지 않은 요청에는 거짓이다.** `fieldErrors`에 담는 메시지는 정책 메시지가 아니라 "현재 비밀번호를 입력해주세요." 같은 존재 메시지다.

> **`DELETE /api/v1/accounts/me`도 같다**([plan/phase1.md](plan/phase1.md) AU-09의 "비밀번호 없이 요청 → 400 `C001`"). 두 엔드포인트가 같은 성질의 필드를 같은 코드로 처리한다.

**새 비밀번호와 현재 비밀번호가 둘 다 틀리면 `C001`이다.** Bean Validation이 컨트롤러 앞에서 돌기 때문이고, 그 순서는 현재 비밀번호에 대해 아무것도 알려주지 않으므로 그대로 둔다.

**새 비밀번호가 현재와 같아도 거부하지 않는다.** 비교하려면 BCrypt를 한 번 더 돌려야 하고(약 48ms), 같은 값으로 바꾸는 것이 해를 끼치지 않는다 — RefreshToken은 어차피 삭제되어 세션이 끊긴다. 막아야 할 요구가 생기면 그때 정한다.

`PATCH /api/v1/accounts/me/password`도 RefreshToken을 삭제한다. 같은 로컬 트랜잭션이다.

#### 탈퇴한 계정의 토큰으로 `/accounts/me*`를 호출하면

Access Token은 탈퇴 후에도 만료까지 통과하므로([security.md §5.3](security.md)) **이 셋은 실제로 도달 가능한 경로다.** 엔드포인트마다 다르게 정한다.

| 엔드포인트 | 탈퇴한 계정 | 왜 |
| --- | --- | --- |
| `PATCH /accounts/me/password` | **404 `AU001`** | 닫힌 행에 쓰기를 허용할 이유가 없다 |
| `GET /accounts/me` | **404 `AU001`** | 탈퇴한 계정은 API 관점에서 없는 계정이다 |
| `DELETE /accounts/me` | **204** | **멱등이 요구사항이다**(MR-10). 여기만 예외다 |

**비밀번호 변경을 막는 이유는 권한 상승이 아니다.** 바꿔도 새 세션은 못 만든다 — 로그인이 `deleted`를 보고, 재발급도 보고, 이메일은 재사용되지 않는다. 남는 것은 **상태 둘**이다.

| 막지 않으면 | |
| --- | --- |
| `account.password` | 닫힌 행의 자격증명이 요청자가 정한 값으로 덮인다. **계정 복구가 2차에 생기면 원래 소유자의 비밀번호가 아니라 마지막으로 바꾼 쪽의 비밀번호로 복구된다** |
| `account.updated_at` | 갱신되어 **탈퇴 시점의 흔적이 지워진다.** `account`에 `deleted_at` 컬럼이 없다([domain-model.md §2.1](domain-model.md)) |

**그 흔적 자체가 약하다.** MySQL `DATETIME`은 **초 단위**이므로 같은 초 안의 덮어쓰기는 보이지 않고, 어떤 갱신이었는지도 구별되지 않는다([domain-model.md §1.1](domain-model.md)의 측정값). 위 검사는 **쓰기가 닿지 않게 하는 것**이고, `updated_at`을 감사 수단으로 만드는 것이 아니다.

**`deleted_at`이 없는 것은 1차의 알려진 한계다.** 탈퇴 시각을 되짚을 필요가 생기면 컬럼을 추가한다 — 위 검사가 들어가면 비밀번호 변경이 흔적을 지우는 경로는 닫힌다.

**검사를 `AccountReader`에 두지 않는다.** 거기서 일괄 거부하면 `DELETE`의 멱등성이 깨진다. 기능별로 검사한다([requirements/member.md §3](requirements/member.md) 규칙 5).

### 2.3 중복 확인 응답

**두 중복 확인 엔드포인트(`check-email`·`check-nickname`)는 같은 형태를 쓴다.**

```json
// GET /api/v1/accounts/check-email?email=user@example.com  -> 200
{ "success": true, "data": { "available": false }, "error": null }
```

| 필드 | 의미 |
| --- | --- |
| `available` | **쓸 수 있으면 `true`**, 이미 쓰이고 있으면 `false` |

**`duplicated`가 아니라 `available`이다.** 두 서비스가 각자 만들므로 여기서 고정한다. `duplicated: false`처럼 부정형을 쓰면 이중 부정이 생겨 호출 측이 뒤집어 읽는다.

**탈퇴한 계정의 이메일은 `available: false`이고, 탈퇴한 프로필의 닉네임은 `available: true`다.** 이메일은 재사용하지 않지만([requirements/member.md §3](requirements/member.md) 규칙 1) 닉네임은 탈퇴 시 NULL로 비워지므로 다시 쓸 수 있다 — **둘 중 닉네임만 해방된다**([domain-model.md §3.1](domain-model.md)). 닉네임이 비워진 뒤에는 조회에 걸리는 행이 없으므로 `true`는 특별한 분기가 아니라 **자연한 결과**다. 거기에 "탈퇴한 프로필의 닉네임"을 따로 찾아 `false`로 돌리는 코드를 넣지 않는다.

**파라미터를 검증한다.**

| 요청 | 응답 |
| --- | --- |
| 파라미터 누락 | 400 `C001` |
| 빈 문자열 | 400 `C001` |
| 형식 오류 (`check-email`) | 400 `C001` — 생성과 같은 규칙을 적용한다([requirements/member.md §2](requirements/member.md)) |
| 길이 초과 | 400 `C001` |

**`fieldErrors`는 바인딩된 필드의 오류에만 담는다.**

| 경우 | `fieldErrors` |
| --- | --- |
| 파라미터 **누락** | **빈 배열** — 바인딩 자체가 일어나지 않아 담을 필드가 없다 |
| 빈 값·형식 오류·길이 초과 | 해당 필드 1건 (`field`는 파라미터명) |

이것은 요청 수준 오류와 바인딩 수준 오류의 구분이다. 클라이언트는 `fieldErrors`가 빈 경우를 이미 처리해야 한다 — `C005` 같은 코드에는 애초에 없다.

**형식 오류에 `available: true`를 돌려주지 않는다.** 쓸 수 없는 값인데 쓸 수 있다고 답하는 셈이고, 클라이언트가 생성을 시도해 400을 받는다. 같은 판정을 두 번 하게 된다.

**이 엔드포인트는 경합을 막지 못한다.** 확인과 생성 사이에 다른 사용자가 같은 값을 쓸 수 있다. 최종 판정은 UNIQUE 제약이고, 생성 요청이 409를 돌려준다. 중복 확인은 편의 기능이다.

## 3. member-service API

| Method | Path | 설명 | 인증 | 성공 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/members` | **프로필 등록 (가입 3단계)** | O | 201 / 200 |
| GET | `/api/v1/members/check-nickname?nickname=` | 닉네임 중복 확인 ([§2.3](#23-중복-확인-응답)) | - | 200 |
| GET | `/api/v1/members/me` | 내 프로필 조회 | O | 200 |
| PATCH | `/api/v1/members/me` | 닉네임 수정 | O | 200 |
| DELETE | `/api/v1/members/me` | **프로필 탈퇴 (탈퇴 2단계)** | O | 204 |
| GET | `/api/v1/members/{accountId}` | 특정 회원 프로필 | - | 200 |

- `POST /api/v1/members`는 **인증이 필요하다.** `account_id`는 검증된 JWT의 `sub`에서만 가져온다. 요청 본문의 식별자를 신뢰하지 않는다
- **`accountId` 기준으로 멱등이다.** 응답만 유실된 클라이언트가 재시도해도 중복 생성·덮어쓰기가 없다

| 기존 상태 | 응답 |
| --- | --- |
| 행 없음 | 201 생성 |
| 활성 프로필, 닉네임 동일 | 200 기존 반환 |
| 활성 프로필, 닉네임 상이 | 409 `M006` |
| 탈퇴한 프로필 | 409 `M007` |

- `PATCH /api/v1/members/me`는 **토큰을 반환하지 않는다.** Claim에 `nickname`이 없으므로 토큰이 낡을 이유가 없다([adr/0012](adr/0012-auth-as-separate-service.md) §3)
- `GET /api/v1/members/me`는 **프로필이 없으면 404 `M001`**이다. 이것은 오류가 아니라 "가입 3단계가 아직"이라는 뜻이며, 클라이언트는 프로필 등록 화면으로 보낸다
- `GET /api/v1/members/{accountId}`의 경로 변수는 **`accountId`다.** `member.id`는 외부에 노출하지 않는다
- `DELETE /api/v1/members/me`는 멱등이다. 프로필 `deleted = true`, `nickname`은 NULL로 비운다

### 3.1 두 조회의 응답 형태

**`GET /me`와 `GET /{accountId}`가 다른 모양이다.** 요구사항이 다른 값을 배정하기 때문이다.

```json
// GET /api/v1/members/me  -> 200
{ "success": true, "data": { "accountId": 1, "nickname": "홍길동" }, "error": null }

// GET /api/v1/members/1   -> 200
{ "success": true,
  "data": { "accountId": 1, "nickname": "홍길동", "createdAt": "2026-09-11T10:05:00", "deleted": false },
  "error": null }
```

| | 반환 | 근거 |
| --- | --- | --- |
| `GET /me` | `accountId`·`nickname` | [requirements/member.md §5](requirements/member.md) MR-07이 member에 배정한 것은 **닉네임뿐이다** |
| `GET /{accountId}` | `accountId`·`nickname`·`createdAt`·`deleted` | MR-11이 "닉네임, 가입일"을 요구하고, 탈퇴 표기에 `deleted`가 필요하다 |

`POST /api/v1/members`의 응답도 `GET /me`와 같은 모양이다(§9.1).

**두 "가입일"이 다른 값이다.** MR-07의 가입일은 `account.created_at`(계정 생성)이고 `GET /api/v1/accounts/me`가 돌려준다. **MR-11의 가입일은 `member.created_at`(프로필 등록 시각)이다** — 가입이 3단계이므로 사이에 로그인이 끼고, 둘은 같지 않다([adr/0012](adr/0012-auth-as-separate-service.md) §4). 타인의 계정 생성 시각은 **읽을 수 없다** — `GET /accounts/me`는 자기 것만 돌려준다.

#### 탈퇴한 프로필의 공개 조회

| 요청 | 응답 |
| --- | --- |
| `GET /me`, 프로필 없음 **또는 탈퇴** | **404 `M001`** |
| **`GET /{accountId}`, 탈퇴한 프로필** | **200.** `nickname`은 `"탈퇴한 회원"`, `deleted: true` |
| `GET /{accountId}`, 그 `accountId`의 프로필이 **없음** | **404 `M001`** |

**`/me`가 404인데 `/{accountId}`가 200인 것이 의도다.** 앞은 "내 프로필을 고치러 왔다"이고 탈퇴했으면 고칠 것이 없다. 뒤는 **"이 글을 쓴 사람의 표시 이름"**이고, 글이 남아 있으므로 표시할 것이 있다 — 404를 주면 클라이언트가 정상적으로 존재하는 글에 오류를 띄운다.

**마스킹 규칙은 하나다.** `"탈퇴한 회원"`은 §5의 내부 API와 **같은 응답 시 변환**이며 저장값은 NULL이다([domain-model.md §3.1](domain-model.md)). 두 군데서 다르게 변환하지 않는다.

> **없는 `accountId`에 404를 쓰는 것은 여기까지다.** §5.1이 금지한 것은 **내부 API**에서 404를 업무 의미로 쓰는 것이다 — board가 그것을 "프로필 없음"으로 읽으면 경로 오설정이 업무 오류로 위장된다. 공개 조회는 클라이언트를 상대하므로 404가 맞다. **두 경로를 같게 맞추지 않는다.**

## 4. board-service API

| Method | Path | 설명 | 인증 | 성공 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/posts` | 게시글 작성 | O | 201 |
| GET | `/api/v1/posts` | 목록·검색 | - | 200 |
| GET | `/api/v1/posts/{id}` | 상세 조회 | - | 200 |
| PUT | `/api/v1/posts/{id}` | 수정 | O (본인) | 200 |
| DELETE | `/api/v1/posts/{id}` | 삭제 | O (본인/ADMIN) | 204 |
| POST | `/api/v1/posts/{postId}/comments` | 댓글 작성 | O | 201 |
| GET | `/api/v1/posts/{postId}/comments` | 댓글 목록 | - | 200 |
| PUT | `/api/v1/comments/{id}` | 댓글 수정 | O (본인) | 200 |
| DELETE | `/api/v1/comments/{id}` | 댓글 삭제 | O (본인/ADMIN) | 204 |

### 4.1 목록 조회 파라미터

`GET /api/v1/posts`

| 파라미터 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `page` | int | 0 | 0부터 시작 |
| `size` | int | 10 | 최대 50. 초과 시 50으로 절삭 |
| `sort` | enum | `latest` | `latest`(최신순), `views`(조회순) |
| `searchType` | enum | - | `TITLE`, `CONTENT`, `TITLE_CONTENT`, `WRITER` |
| `keyword` | string | - | `searchType`과 함께 전달 |

`sort`는 화이트리스트 Enum으로 받는다. 임의 컬럼명을 직접 노출하지 않는다.

### 4.2 프로필 보유가 필요한 동작

| 동작 | 프로필 필요 | member 호출 |
| --- | --- | --- |
| 글·댓글 조회 | 아니오 (공개) | 없음 |
| 글·댓글 **생성** | 예 | **있음** (§5) |
| 글·댓글 수정 | 아니오 | 없음 |
| 글·댓글 삭제 | 아니오 | 없음 |
| 관리자 삭제 | 아니오 | 없음 |

수정·삭제가 member에 의존하지 않는 것은 "수정 시 스냅샷을 갱신하지 않는다"에서 따라온다. **member 장애 시 새 글만 막히고 기존 글의 수정·삭제는 계속 된다.**

## 5. 내부 API (외부 미노출)

| Method | Path | 설명 |
| --- | --- | --- |
| POST | `/internal/v1/members/bulk` | 프로필 요약 벌크 조회 |

**벌크 하나만 둔다.** 단건 전용 API를 따로 만들지 않는다. 쓰기 경로처럼 1건만 필요한 호출도 이 API에 1건을 담아 호출한다. 그래야 실패 의미론이 하나로 유지된다.

인증은 `X-Internal-Api-Key` 헤더로 한다([security.md §6](security.md)). board는 이 키를 설정으로 주입받는다.

```json
// POST /internal/v1/members/bulk  Request
{ "accountIds": [1, 2, 5] }

// Response 200
{
  "success": true,
  "data": {
    "members": [
      { "accountId": 1, "nickname": "홍길동", "deleted": false },
      { "accountId": 5, "nickname": "탈퇴한 회원", "deleted": true }
    ]
  },
  "error": null
}
```

- **존재하지 않는 `accountId`는 결과에서 제외한다.** 404를 반환하지 않는다
- 탈퇴한 프로필은 `deleted: true` + 닉네임 `"탈퇴한 회원"`으로 반환한다. **저장된 값이 아니라 응답 시 변환이다**(저장값은 NULL, [domain-model.md §3.1](domain-model.md))
- 요청 순서와 응답 순서를 맞추지 않는다. 소비 측이 `accountId`로 매칭한다

### 5.1 board의 실패 판정

**HTTP 404를 업무 의미로 쓰지 않는다.** 프로필 유무는 응답 본문으로만 판정한다.

| member 응답 | board 처리 | board 응답 |
| --- | --- | --- |
| 200, 결과에 `deleted = false` | 진행 | — |
| 200, 결과에서 제외됨 (프로필 미등록) | 업무 오류. 재시도 무의미 | 403 `S002` |
| 200, 결과에 `deleted = true` | 업무 오류. 재시도 무의미 | 403 `S002` |
| **그 밖의 모든 응답** — 4xx, 5xx, 타임아웃, 본문 파싱 실패 | **인프라 오류. 경보 대상** | 503 `S001` |

마지막 행이 핵심이다. 경로 오설정·내부 API 키 거부·미처리 예외가 전부 여기로 떨어진다. **404를 "프로필 없음"으로 해석하면 설정 사고가 업무 오류로 위장되어 전 사용자의 쓰기가 조용히 멈춘다.**

타임아웃은 **connect 1초 / read 3초**다([nfr.md §3](nfr.md)). 1차에서는 재시도·서킷브레이커를 두지 않는다.

## 6. JWT Claim 계약

**세 서비스가 공유하는 계약이다.** 발급은 auth 하나, 검증은 member·board 둘이다.

| Claim | 타입 | 값 | 용도 |
| --- | --- | --- | --- |
| `sub` | string | `account.id`의 문자열 (= `accountId`) | 전역 식별. 작성자 식별 (`post.writer_id`) |
| `role` | string | `USER` \| `ADMIN` | 권한 판정 |
| `iss` | string | `auth-service` | 발급자 |
| `iat` | number | 발급 시각(epoch) | |
| `exp` | number | 만료 시각(epoch) | |

- 서명 알고리즘은 **RS256**이다. header에 `kid`를 포함한다
- **발급은 auth-service만 한다.** member·board는 공개키로 검증만 한다
- payload는 암호화되지 않는다. 이메일 등 불필요한 개인정보를 넣지 않는다
- **`nickname` claim은 없다.** auth는 닉네임을 소유하지 않는다. 작성자 스냅샷은 §5의 내부 API로 얻는다([adr/0012](adr/0012-auth-as-separate-service.md) §3·§6)
- **권한 판정은 이 Claim만으로 한다.** 권한을 다른 서비스에 되묻지 않는다. 프로필 보유 확인(§4.2)은 권한 판정이 아니라 작성자 스냅샷 취득이다
- **검증은 오프라인이다.** 따라서 탈퇴·권한 박탈이 기존 토큰에 즉시 반영되지 않는다. 최대 노출은 Access Token 만료까지이며, 잔여 권한은 그 `role`이 가진 모든 변경 권한이다 — ADMIN이면 **타인 글·댓글 삭제를 포함한다**([security.md §5.2](security.md))

토큰 만료 시간과 키 관리는 [security.md](security.md)를 본다.

## 7. 공통 응답 형식

세 서비스가 동일하다.

```java
public record ApiResponse<T>(boolean success, T data, ErrorResponse error) { }
public record ErrorResponse(String code, String message, List<FieldError> fieldErrors) { }
public record FieldError(String field, String message) { }
```

**`FieldError`의 필드명은 `field`·`message`다.** 세 서비스가 각자 복제하므로([adr/0007](adr/0007-shared-code-policy.md)) 여기서 고정한다. 일치 여부는 [plan/integration.md](plan/integration.md) I-04의 3자 비교에서 확인한다.

**`rejectedValue`(사용자가 보낸 원문)를 담지 않는다.** 비밀번호 검증 실패 시 응답에 평문이 실린다.

| 상황 | success | data | error |
| --- | --- | --- | --- |
| 성공 | true | 실제 데이터 | null |
| 실패 | false | null | `{ code, message, fieldErrors[] }` |

### 7.1 페이징 응답

```json
{
  "success": true,
  "data": {
    "content": [ ... ],
    "page": 0, "size": 10,
    "totalElements": 1, "totalPages": 1,
    "first": true, "last": true
  },
  "error": null
}
```

## 8. 에러 코드

### 8.1 공통 (세 서비스)

| 코드 | HTTP | 메시지 |
| --- | --- | --- |
| `C001` | 400 | 잘못된 입력값입니다. |
| `C002` | 400 | 잘못된 타입의 값입니다. |
| `C003` | 405 | 지원하지 않는 HTTP 메서드입니다. |
| `C004` | 404 | 요청한 리소스를 찾을 수 없습니다. |
| `C005` | 500 | 서버 내부 오류가 발생했습니다. |
| `C006` | 415 | 지원하지 않는 미디어 타입입니다. |
| `C007` | 406 | 응답할 수 있는 형식이 없습니다. |
| `A001` | 401 | 인증이 필요합니다. |
| `A002` | 401 | 유효하지 않은 토큰입니다. |
| `A003` | 401 | 만료된 토큰입니다. |
| `A004` | 403 | 권한이 없습니다. |

**`C006`·`C007`이 없으면 클라이언트 실수가 500이 된다.** `GlobalExceptionHandler`가 `ResponseEntityExceptionHandler`를 상속하지 않으므로, 처리하지 않은 MVC 예외는 마지막 그물(`Exception.class`)로 떨어진다.

| 요청 | 예외 | 다루지 않으면 — **실측값** |
| --- | --- | --- |
| 본문이 있는데 `Content-Type`이 없거나 JSON이 아니다 | `HttpMediaTypeNotSupportedException` | **500 `C005`** |
| `Accept`로 JSON을 받을 수 없다 | `HttpMediaTypeNotAcceptableException` | **406, 본문이 비어 있다** |

**두 번째가 500이 아닌 이유.** 마지막 그물이 만든 `C005` 본문을 **협상할 수 없어** Spring이 빈 406으로 떨어뜨린다. 상태는 맞으면서 **에러 코드가 아예 없는** 응답이 나간다.

> **그래서 `C007` 핸들러는 응답의 `Content-Type`을 `application/json`으로 못박는다.** 그러지 않으면 핸들러 자신의 응답이 같은 협상에 걸려 또 빈 본문이 된다.

**상태 코드보다 로그가 더 문제다.** 마지막 그물은 `log.error`로 스택트레이스를 남기므로, **두 경우 모두 ERROR 경보를 만든다**(실측 2건). 흔한 클라이언트 실수가 원인이 서버에 있는 500과 구별되지 않으면 경보가 쓸모를 잃는다([../AGENTS.md](../AGENTS.md) 불변식 9).

세 서비스가 `GlobalExceptionHandler`를 각자 복제하므로([adr/0007](adr/0007-shared-code-policy.md)) **셋 다 이 둘을 다룬다.** 형식 일치는 [plan/integration.md](plan/integration.md) I-04의 3자 비교에서 확인한다.

### 8.2 member-service

| 코드 | HTTP | 메시지 |
| --- | --- | --- |
| `M001` | 404 | 프로필을 찾을 수 없습니다. |
| `M003` | 409 | 이미 사용 중인 닉네임입니다. |
| `M006` | 409 | 이미 프로필이 등록된 계정입니다. |
| `M007` | 409 | 탈퇴한 프로필입니다. |

`M002`·`M004`·`M005`는 auth로 이동했다(§8.4). **번호는 재사용하지 않는다.**

`M001`은 "프로필이 아직 없음"에도 쓰인다. 오류가 아니라 가입 3단계 미완료를 뜻한다(§3).

### 8.3 board-service

| 코드 | HTTP | 메시지 |
| --- | --- | --- |
| `P001` | 404 | 게시글을 찾을 수 없습니다. |
| `P002` | 403 | 게시글에 대한 권한이 없습니다. |
| `CM001` | 404 | 댓글을 찾을 수 없습니다. |
| `CM002` | 403 | 댓글에 대한 권한이 없습니다. |
| `S001` | 503 | 일시적으로 서비스 연동에 실패했습니다. |
| `S002` | 403 | 프로필 등록이 필요합니다. |

`S002`는 글·댓글 **생성** 시 활성 프로필이 없을 때다. 판정 규칙은 §5.1에 있다.

### 8.4 auth-service

| 코드 | HTTP | 메시지 |
| --- | --- | --- |
| `AU001` | 404 | 계정을 찾을 수 없습니다. |
| `AU002` | 409 | 이미 사용 중인 이메일입니다. |
| `AU003` | 401 | 이메일 또는 비밀번호가 일치하지 않습니다. |
| `AU004` | 400 | 현재 비밀번호가 일치하지 않습니다. |

`AU002`·`AU003`·`AU004`는 각각 이전의 `M002`·`M004`·`M005`다.

### 8.5 `A001`·`A002`·`A003`을 가르는 경계

세 코드가 모두 401이므로 어느 것을 내보낼지 정해 둔다. **경계는 RFC 6750의 `b64token` 문법이다.**

| 요청의 `Authorization` | 코드 | 왜 |
| --- | --- | --- |
| 헤더 없음 | `A001` | 제시된 자격증명이 없다 |
| `Bearer`(값 없음), `Basic …` 등 다른 스킴 | `A001` | 같음 |
| **`Bearer not!a!token`** — `b64token` 문법 위반 | **`A001`** | RFC 6750 §2.1이 허용하는 문자는 `ALPHA / DIGIT / - . _ ~ + /`와 꼬리 `=`뿐이다. 위반한 값은 **애초에 bearer 자격증명이 아니다** |
| **`Bearer <문법은 맞지만 JWT가 아님>`** | **`A002`** | 자격증명은 제시됐고 해석에 실패했다 |
| 서명 불일치·변조 | `A002` | 같음 |
| **`exp` 경과** | **`A003`** | 클라이언트가 토큰을 읽어 이미 아는 사실이므로 가려도 누출이 아니다 |
| 그 밖의 claim 검증 실패 | `A002` | 사유를 가르지 않는다 |

**`A003`만 사유를 드러낸다.** 나머지를 `A002`로 모으는 이유는 세션 존재와 계정 탈퇴 여부가 드러나지 않게 하는 것이다([security.md §4.1](security.md)).

> 문법 위반이 `A001`로 떨어지는 것은 Spring의 `DefaultBearerTokenResolver`가 디코더 앞에서 끊기 때문이고, **그 동작이 RFC와 일치하므로 그대로 둔다.** 구현은 예외 타입만 보고 가른다 — 메시지 문자열을 파싱하면 버전업에 깨진다.

접두어로 어느 서비스에서 난 오류인지 식별한다. 응답에 스택트레이스·SQL·내부 호스트명을 포함하지 않는다.

## 9. 요청·응답 예시

### 9.1 가입 (계정 → 로그인 → 프로필)

계정과 프로필을 따로 만든다. 사이에 로그인이 들어간다([adr/0012](adr/0012-auth-as-separate-service.md) §4).

```json
// 1) POST /api/v1/accounts        (auth, 무인증)
{ "email": "user@example.com", "password": "Passw0rd!" }

// 201
{ "success": true, "data": { "accountId": 1, "email": "user@example.com" }, "error": null }


// 2) POST /api/v1/auth/login      (auth, 무인증)  -> 200  (§9.2)


// 3) POST /api/v1/members         (member, Authorization: Bearer ...)
{ "nickname": "홍길동" }

// 201   accountId는 본문이 아니라 JWT sub에서 가져온다
{ "success": true, "data": { "accountId": 1, "nickname": "홍길동" }, "error": null }
```

**1단계만 끝난 상태는 정상이다.** 로그인·재발급·로그아웃·계정 탈퇴가 모두 가능하고, 글 작성만 `S002`로 막힌다.

### 9.1.1 탈퇴 (계정 → 프로필)

```json
// 1) DELETE /api/v1/accounts/me   (auth, 인증)
{ "password": "Passw0rd!" }          // 비밀번호 재확인
// 204   account.deleted = true + RefreshToken 삭제 (한 트랜잭션)

// 2) DELETE /api/v1/members/me    (member, 1단계에서 쓰던 Access Token)
// 204   프로필 deleted = true, nickname = NULL
```

**순서를 바꾸지 않는다.** 이유는 [adr/0012](adr/0012-auth-as-separate-service.md) §5에 있다.

### 9.2 로그인

```json
// POST /api/v1/auth/login  -> 200
{
  "success": true,
  "data": {
    "grantType": "Bearer",
    "accessToken": "eyJhbGciOiJSUzI1NiIsImtpZCI6...",
    "refreshToken": "eyJhbGciOiJSUzI1NiIsImtpZCI6...",
    "accessTokenExpiresIn": 1800
  },
  "error": null
}
```

### 9.3 게시글 목록

```json
// GET /api/v1/posts?page=0&size=10&sort=latest&searchType=TITLE&keyword=공지  -> 200
{
  "success": true,
  "data": {
    "content": [
      {
        "id": 12, "title": "공지사항입니다",
        "writerId": 3, "writerNickname": "관리자",
        "viewCount": 152, "commentCount": 3,
        "createdAt": "2026-09-11T10:00:00"
      }
    ],
    "page": 0, "size": 10, "totalElements": 1, "totalPages": 1,
    "first": true, "last": true
  },
  "error": null
}
```

시각은 KST 기준이며 오프셋을 표기하지 않는다([tech-stack.md §6](tech-stack.md)).

### 9.4 에러

```json
// 409
{
  "success": false,
  "data": null,
  "error": { "code": "AU002", "message": "이미 사용 중인 이메일입니다.", "fieldErrors": [] }
}
```
