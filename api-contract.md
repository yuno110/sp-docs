---
title: API 계약
type: spec
status: frozen
version: v1
updated: 2026-09-11
read_when: "엔드포인트를 구현하거나, 요청·응답 형식·에러 코드·JWT Claim을 확인할 때"
related: [domain-model.md, security.md, requirements/member.md, requirements/board.md]
---
# API 계약

엔드포인트·응답 형식·에러 코드·토큰 Claim의 정본은 이 문서다.

**§5 JWT Claim은 두 서비스가 공유하는 계약 지점이다.** 여기를 바꾸면 양쪽이 함께 바뀌어야 하므로 개정 시 두 서비스 담당이 모두 확인한다.

## 1. 경로 규칙

| 경로 | 서비스 | 주소(1차) |
| --- | --- | --- |
| `/api/v1/auth/**` | member | `http://localhost:8081` |
| `/api/v1/members/**` | member | `http://localhost:8081` |
| `/api/v1/posts/**` | board | `http://localhost:8082` |
| `/api/v1/comments/**` | board | `http://localhost:8082` |
| `/internal/v1/**` | member | 서비스 간 호출 전용. 외부 노출 금지 |

`/api/v1` 버저닝의 이유는 [adr/0008](adr/0008-api-versioning.md)을 본다.

`auth`와 `members`를 나눈 기준은 [adr/0006](adr/0006-auth-inside-member-service.md)에 있다. `auth`는 세션·토큰 행위, `members`는 회원 리소스 관리다.

## 2. member-service API

### 2.1 인증 (`auth` 패키지)

| Method | Path | 설명 | 인증 | 성공 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/auth/login` | 로그인, 토큰 발급 | - | 200 |
| POST | `/api/v1/auth/reissue` | 토큰 재발급(Rotation) | - | 200 |
| POST | `/api/v1/auth/logout` | 로그아웃 | O | 204 |

### 2.2 회원 (`member` 패키지)

| Method | Path | 설명 | 인증 | 성공 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/members` | 회원가입 | - | 201 |
| GET | `/api/v1/members/check-email?email=` | 이메일 중복 확인 | - | 200 |
| GET | `/api/v1/members/check-nickname?nickname=` | 닉네임 중복 확인 | - | 200 |
| GET | `/api/v1/members/me` | 내 정보 조회 | O | 200 |
| PATCH | `/api/v1/members/me` | 닉네임 수정 (신규 토큰 함께 반환) | O | 200 |
| PATCH | `/api/v1/members/me/password` | 비밀번호 변경 | O | 204 |
| DELETE | `/api/v1/members/me` | 회원 탈퇴 | O | 204 |
| GET | `/api/v1/members/{id}` | 특정 회원 프로필 | - | 200 |

## 3. board-service API

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

### 3.1 목록 조회 파라미터

`GET /api/v1/posts`

| 파라미터 | 타입 | 기본 | 설명 |
| --- | --- | --- | --- |
| `page` | int | 0 | 0부터 시작 |
| `size` | int | 10 | 최대 50. 초과 시 50으로 절삭 |
| `sort` | enum | `latest` | `latest`(최신순), `views`(조회순) |
| `searchType` | enum | - | `TITLE`, `CONTENT`, `TITLE_CONTENT`, `WRITER` |
| `keyword` | string | - | `searchType`과 함께 전달 |

`sort`는 화이트리스트 Enum으로 받는다. 임의 컬럼명을 직접 노출하지 않는다.

## 4. 내부 API (외부 미노출)

| Method | Path | 설명 |
| --- | --- | --- |
| POST | `/internal/v1/members/bulk` | 회원 요약 벌크 조회 |
| GET | `/internal/v1/members/{id}` | 회원 요약 단건 조회 |

인증은 `X-Internal-Api-Key` 헤더로 한다.

```json
// POST /internal/v1/members/bulk  Request
{ "memberIds": [1, 2, 5] }

// Response 200
{
  "success": true,
  "data": {
    "members": [
      { "id": 1, "nickname": "홍길동", "deleted": false },
      { "id": 5, "nickname": "탈퇴한 회원", "deleted": true }
    ]
  },
  "error": null
}
```

1차에서 board-service가 이 API를 호출하는 경로는 없다. 스냅샷으로 충분하기 때문이며, 2차 대비로 제공 측만 구현한다.

## 5. JWT Claim 계약

**두 서비스가 공유하는 계약이다.**

| Claim | 타입 | 값 | 용도 |
| --- | --- | --- | --- |
| `sub` | string | `member.id`의 문자열 | 작성자 식별 (`post.writer_id`) |
| `nickname` | string | `member.nickname` | 작성자 스냅샷 (`post.writer_nickname`) |
| `role` | string | `USER` \| `ADMIN` | 권한 판정 |
| `iss` | string | `member-service` | 발급자 |
| `iat` | number | 발급 시각(epoch) | |
| `exp` | number | 만료 시각(epoch) | |

- 서명 알고리즘은 **RS256**이다. header에 `kid`를 포함한다
- payload는 암호화되지 않는다. 이메일 등 불필요한 개인정보를 넣지 않는다
- board-service는 이 Claim만으로 권한을 판정한다. member-service에 되묻지 않는다

토큰 만료 시간과 키 관리는 [security.md](security.md)를 본다.

## 6. 공통 응답 형식

두 서비스가 동일하다.

```java
public record ApiResponse<T>(boolean success, T data, ErrorResponse error) { }
public record ErrorResponse(String code, String message, List<FieldError> fieldErrors) { }
```

| 상황 | success | data | error |
| --- | --- | --- | --- |
| 성공 | true | 실제 데이터 | null |
| 실패 | false | null | `{ code, message, fieldErrors[] }` |

### 6.1 페이징 응답

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

## 7. 에러 코드

### 7.1 공통 (두 서비스)

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

### 7.2 member-service

| 코드 | HTTP | 메시지 |
| --- | --- | --- |
| `M001` | 404 | 회원을 찾을 수 없습니다. |
| `M002` | 409 | 이미 사용 중인 이메일입니다. |
| `M003` | 409 | 이미 사용 중인 닉네임입니다. |
| `M004` | 401 | 이메일 또는 비밀번호가 일치하지 않습니다. |
| `M005` | 400 | 현재 비밀번호가 일치하지 않습니다. |

### 7.3 board-service

| 코드 | HTTP | 메시지 |
| --- | --- | --- |
| `P001` | 404 | 게시글을 찾을 수 없습니다. |
| `P002` | 403 | 게시글에 대한 권한이 없습니다. |
| `CM001` | 404 | 댓글을 찾을 수 없습니다. |
| `CM002` | 403 | 댓글에 대한 권한이 없습니다. |
| `S001` | 503 | 일시적으로 서비스 연동에 실패했습니다. |

접두어로 어느 서비스에서 난 오류인지 식별한다. 응답에 스택트레이스·SQL·내부 호스트명을 포함하지 않는다.

## 8. 요청·응답 예시

### 8.1 회원가입

```json
// POST /api/v1/members
{ "email": "user@example.com", "password": "Passw0rd!", "nickname": "홍길동" }

// 201
{
  "success": true,
  "data": { "id": 1, "email": "user@example.com", "nickname": "홍길동" },
  "error": null
}
```

### 8.2 로그인

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

### 8.3 게시글 목록

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

### 8.4 에러

```json
// 409
{
  "success": false,
  "data": null,
  "error": { "code": "M002", "message": "이미 사용 중인 이메일입니다.", "fieldErrors": [] }
}
```
