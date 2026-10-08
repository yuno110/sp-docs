---
title: 도메인 모델
type: spec
status: frozen
version: v4
updated: 2026-10-08
read_when: "엔티티 필드, 컬럼 타입, 제약, 인덱스, 마이그레이션 스크립트를 작성할 때"
related: [architecture.md, api-contract.md, requirements/member.md, requirements/board.md]
---
# 도메인 모델

테이블·컬럼·제약의 정본은 이 문서다. 세 스키마는 서로 참조하지 않는다.

**전역 식별자는 `account.id`(= `accountId`)다.** auth-service가 발급하고 세 서비스가 공유한다. `member.account_id`, `post.writer_id`, `comment.writer_id`가 모두 이 값을 가리킨다. 서비스 경계를 넘는 참조에는 FK 제약을 두지 않는다([adr/0012](adr/0012-auth-as-separate-service.md)).

## 1. 공통

### 1.1 BaseTimeEntity

세 서비스에 각각 둔다. `@MappedSuperclass`, `@EntityListeners(AuditingEntityListener.class)`.

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| createdAt | LocalDateTime | `@CreatedDate`, `updatable = false` |
| updatedAt | LocalDateTime | `@LastModifiedDate` |

컬럼 타입은 `DATETIME`이고 **둘 다 NOT NULL**이다([tech-stack.md §5](tech-stack.md)). 감사가 INSERT 시점에 둘을 함께 채우므로 NULL이 들어올 경로가 없다.

> `@DataJpaTest` 슬라이스는 `@Configuration`을 스캔하지 않아 `@EnableJpaAuditing`이 빠진다. 그러면 두 컬럼이 NULL로 들어가 NOT NULL 제약에 걸린다. 테스트에서 `@Import(JpaConfig.class)`로 올린다.

### 1.2 명명 규칙

- 테이블·컬럼은 snake_case, 엔티티·필드는 camelCase
- 마이그레이션 파일은 `V<번호>__<설명>.sql` (예: `V1__create_member.sql`)
- Enum은 `@Enumerated(EnumType.STRING)`으로 저장한다. ORDINAL 금지
- **Enum 컬럼은 `VARCHAR(20)`이다.** 세 서비스가 각자 마이그레이션을 쓰므로 길이를 여기서 고정한다
- **제약 이름은 `uk_`(UNIQUE)·`fk_`(FK)·`idx_`(인덱스) + 테이블 + 컬럼**이다. 이름은 각 스키마의 인덱스 절이 배정한다. **배정되지 않은 제약이 필요하면 스스로 정하지 말고 보고한다**([plan/phase1.md](plan/phase1.md) §2.6)

## 2. sp_auth (auth-service 소유)

```
  account                             refresh_token
+---------------------+             +-----------------------+
| PK id               | 1         1 | PK id                 |
|    email        UQ  |-------------| FK account_id     UQ  |
|    password         |             |    token          UQ  |
|    role             |             |    expires_at         |
|    deleted          |             +-----------------------+
|    created_at       |
|    updated_at       |
+---------------------+
```

### 2.1 account

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | Long | PK, IDENTITY | **전역 식별자.** 세 서비스가 공유한다 |
| email | String(100) | NOT NULL, UNIQUE | 로그인 ID |
| password | String(60) | NOT NULL | BCrypt 해시 |
| role | Role | NOT NULL, default `USER` | `USER`, `ADMIN` |
| deleted | boolean | NOT NULL, default false | 탈퇴 여부(Soft Delete) |

`password`는 어떤 API 응답에도 포함하지 않는다.

**탈퇴한 계정의 이메일은 재사용하지 않는다.** 행이 남고 `uk_account_email`이 UNIQUE이므로 자연히 보장된다.

### 2.2 refresh_token

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| id | Long | PK |
| accountId | Long | NOT NULL, UNIQUE |
| token | String(1024), **`CHARACTER SET ascii`** | NOT NULL, UNIQUE |
| expiresAt | LocalDateTime | NOT NULL |

계정당 1행이다. 재로그인 시 갱신(upsert)한다. `account_id`에 FK 제약을 둔다(같은 서비스 내이므로 허용).

#### `token` 길이가 1024이고 ascii인 이유 — 측정값

이 서비스가 발급하는 토큰은 **512자에 들어가지 않는다.** AU-06에서 드러났다.

| 구성 | 길이 |
| --- | --- |
| header (`kid` 43자 포함) | 90 |
| payload (claim 5개, `sub` 자릿수에 따라) | 107 ~ 123 |
| 서명 (RSA 2048비트) | 342 |
| 점 2개 | 2 |
| **합계** | **541 ~ 557** |

`kid`는 RFC 7638 thumbprint(SHA-256)라 **항상 43자**다([security.md §3](security.md)).

**여유를 1024로 두는 이유는 키 크기다.** 4096비트로 회전하면 서명이 683자가 되어 토큰이 약 898자가 된다. 768자로 잡으면 그때 또 막힌다.

**`CHARACTER SET ascii`인 이유는 UNIQUE 인덱스 한계다.** 측정값이다.

| 선언 | UNIQUE 인덱스 |
| --- | --- |
| `VARCHAR(768)` utf8mb4 | 생성됨 |
| `VARCHAR(769)` utf8mb4 | **`ERROR 1071` — max key length is 3072** |
| `VARCHAR(1024)` ascii | 생성됨 |

InnoDB의 인덱스 키 한계가 3072바이트이고 utf8mb4는 문자당 4바이트이므로 **768자가 상한**이다. JWT는 base64url과 점으로만 이뤄져 ASCII이므로, 그 컬럼만 ascii로 선언하면 1024자를 쓸 수 있다.

> **이 프로젝트에서 컬럼별 문자셋을 지정하는 유일한 곳이다.** 나머지는 스키마 기본값(utf8mb4)을 따른다([tech-stack.md §4.1](tech-stack.md)).

**재발급은 이 행 조회와 `account.deleted` 확인을 같은 트랜잭션에서 한다.** 회전은 조건부 UPDATE(affected rows 확인)로 처리한다. 그렇지 않으면 탈퇴와 재발급이 겹칠 때 삭제된 행이 되살아난다([adr/0012](adr/0012-auth-as-separate-service.md) §8).

### 2.3 인덱스

| 이름 | 대상 |
| --- | --- |
| `uk_account_email` | `account(email)` UNIQUE |
| `uk_refresh_account_id` | `refresh_token(account_id)` UNIQUE |
| `uk_refresh_token` | `refresh_token(token)` UNIQUE |
| `fk_refresh_token_account` | `refresh_token(account_id)` → `account(id)` |

**이 표가 제약 이름의 정본이다.** §2.2가 "FK 제약을 둔다"고만 적은 것의 이름이 `fk_refresh_token_account`다.

## 3. sp_member (member-service 소유)

```
  member
+---------------------+
| PK id               |
|    account_id   UQ  |  -> sp_auth.account.id 논리 참조 (FK 없음)
|    nickname     UQ  |     NULL 허용 (탈퇴 시 비운다)
|    deleted          |
|    created_at       |
|    updated_at       |
+---------------------+
```

**member는 프로필만 소유한다.** 이메일·비밀번호·권한은 `sp_auth`에 있다.

### 3.1 member

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | Long | PK, IDENTITY | 프로필 행 식별자. **외부에 노출하지 않는다** |
| accountId | Long | NOT NULL, UNIQUE, **FK 제약 없음** | `account.id` 논리 참조. 외부 식별자는 이것이다 |
| nickname | String(30) | **NULL 허용**, UNIQUE | 표시 이름. 탈퇴 시 NULL |
| deleted | boolean | NOT NULL, default false | 탈퇴 여부(Soft Delete) |

**프로필의 세 가지 상태를 구분한다.** 셋을 섞으면 탈퇴한 프로필이 재생성된다.

| 상태 | 표현 |
| --- | --- |
| 미등록 | 행이 없다 |
| 활성 | 행이 있고 `deleted = false` |
| 탈퇴 | 행이 있고 `deleted = true` (`nickname`은 NULL) |

`account_id` UNIQUE가 탈퇴 계정의 프로필 재생성을 막는다. 별도 묘비 테이블을 두지 않는다.

**soft delete 시 `nickname`을 NULL로 비운다.** 그대로 두면 `uk_member_nickname` 때문에 그 닉네임이 영구 소각되고, `"탈퇴한 회원"`으로 마스킹해 **저장**하는 구현에서는 두 번째 탈퇴가 UNIQUE 위반으로 500이 난다. `"탈퇴한 회원"`은 **응답 시 변환이지 저장이 아니다**([api-contract.md §4](api-contract.md)).

### 3.2 인덱스

| 이름 | 대상 |
| --- | --- |
| `uk_member_account_id` | `member(account_id)` UNIQUE |
| `uk_member_nickname` | `member(nickname)` UNIQUE |

## 4. sp_board (board-service 소유)

```
  post                                   comment
+----------------------------+        +----------------------------+
| PK id                      | 1    * | PK id                      |
|    writer_id      (논리참조)|--------| FK post_id                 |
|    writer_nickname (스냅샷) |        |    writer_id      (논리참조)|
|    title                   |        |    writer_nickname (스냅샷) |
|    content                 |        |    content                 |
|    view_count              |        |    deleted                 |
|    comment_count           |        |    created_at              |
|    deleted                 |        |    updated_at              |
|    created_at / updated_at |        +----------------------------+
+----------------------------+
```

### 4.1 post

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | Long | PK | |
| writerId | Long | NOT NULL, **FK 제약 없음** | `accountId` 논리 참조 |
| writerNickname | String(30) | NOT NULL | 작성 시점 닉네임 스냅샷 |
| title | String(200) | NOT NULL | |
| content | String | NOT NULL, `columnDefinition = "TEXT"` | |
| viewCount | long | NOT NULL, default 0 | |
| commentCount | int | NOT NULL, default 0 | 목록 N+1 방지용 비정규화 |
| deleted | boolean | NOT NULL, default false | |

`writer_id`에 FK 제약을 걸지 않는 이유는 [architecture.md §5](architecture.md)를 본다.

### 4.2 comment

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | Long | PK | |
| post | Post | `@ManyToOne(LAZY)`, NOT NULL | 같은 서비스 내이므로 연관관계 매핑 사용 |
| writerId | Long | NOT NULL, FK 제약 없음 | `accountId` 논리 참조 |
| writerNickname | String(30) | NOT NULL | 작성 시점 스냅샷 |
| content | String(500) | NOT NULL | |
| deleted | boolean | NOT NULL, default false | 삭제 시 "삭제된 댓글입니다" 표시 |

2차에 `parent`(대댓글, `@ManyToOne(LAZY)`, NULL 허용)를 추가한다.

### 4.3 인덱스

| 이름 | 대상 | 용도 |
| --- | --- | --- |
| `idx_post_created_at` | `post(created_at DESC)` | 최신순 목록 |
| `idx_post_writer_id` | `post(writer_id)` | 내가 쓴 글, 2차 이벤트 일괄 갱신 |
| `idx_post_title` | `post(title)` | 제목 검색 |
| `idx_comment_post_id` | `comment(post_id, created_at)` | 게시글별 댓글 목록 |

`idx_post_writer_id`는 2차 Kafka 이벤트의 `UPDATE post SET writer_nickname=? WHERE writer_id=?`를 뒷받침한다.

## 5. commentCount 동기화

댓글 작성·삭제 시 `post.comment_count`를 갱신한다. 같은 트랜잭션 안에서 처리한다.

| 동작 | 처리 |
| --- | --- |
| 댓글 작성 | `comment_count + 1` |
| 댓글 삭제(Soft) | `comment_count - 1` |
| 게시글 삭제(Soft) | 하위 댓글도 `deleted = true`. `comment_count`는 그대로 |

`comment_count`가 음수가 되지 않아야 한다. 회귀 테스트로 확인한다.
