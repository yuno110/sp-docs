---
title: API 계약
type: spec
status: frozen
version: v2
updated: 2026-09-15
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

로그인·재발급은 **`account.deleted = false`를 검사한다.** 재발급은 RefreshToken 조회와 상태 확인을 같은 트랜잭션에서 하고 회전을 조건부 UPDATE로 처리한다([adr/0012](adr/0012-auth-as-separate-service.md) §8).

### 2.2 계정 (`account`)

| Method | Path | 설명 | 인증 | 성공 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/accounts` | 계정 생성 (가입 1단계) | - | 201 |
| GET | `/api/v1/accounts/check-email?email=` | 이메일 중복 확인 | - | 200 |
| GET | `/api/v1/accounts/me` | 내 계정 조회 (이메일·가입일) | O | 200 |
| PATCH | `/api/v1/accounts/me/password` | 비밀번호 변경 | O | 204 |
| DELETE | `/api/v1/accounts/me` | **계정 탈퇴 (탈퇴 1단계)** | O | 204 |

`DELETE /api/v1/accounts/me`는 **본문에 현재 비밀번호를 받아 재확인한다.** `account.deleted = true`와 해당 계정의 RefreshToken 삭제를 한 로컬 트랜잭션으로 처리한다. 멱등이다(이미 탈퇴했으면 204).

`PATCH /api/v1/accounts/me/password`도 RefreshToken을 삭제한다. 같은 로컬 트랜잭션이다.

## 3. member-service API

| Method | Path | 설명 | 인증 | 성공 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/members` | **프로필 등록 (가입 3단계)** | O | 201 / 200 |
| GET | `/api/v1/members/check-nickname?nickname=` | 닉네임 중복 확인 | - | 200 |
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
```

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
| `A001` | 401 | 인증이 필요합니다. |
| `A002` | 401 | 유효하지 않은 토큰입니다. |
| `A003` | 401 | 만료된 토큰입니다. |
| `A004` | 403 | 권한이 없습니다. |

### 8.2 member-service

| 코드 | HTTP | 메시지 |
| --- | --- | --- |
| `M001` | 404 | 프로필을 찾을 수 없습니다. |
| `M003` | 409 | 이미 사용 중인 닉네임입니다. |
| `M006` | 409 | 이미 프로필이 등록된 계정입니다. |
| `M007` | 409 | 탈퇴한 계정입니다. |

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

시각은 KST 기준이며 오프셋을 표기하지 않는다([tech-stack.md §5](tech-stack.md)).

### 9.4 에러

```json
// 409
{
  "success": false,
  "data": null,
  "error": { "code": "AU002", "message": "이미 사용 중인 이메일입니다.", "fieldErrors": [] }
}
```
