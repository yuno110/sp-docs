---
title: 도메인 모델
type: spec
status: frozen
version: v17
updated: 2026-11-11
read_when: "엔티티 필드, 컬럼 타입, 제약, 인덱스, 마이그레이션 스크립트를 작성할 때"
related: [architecture.md, api-contract.md, requirements/member.md, requirements/board.md]
---
# 도메인 모델

테이블·컬럼·제약의 정본은 이 문서다. 세 스키마는 서로 참조하지 않는다.

**전역 식별자는 `account.id`(= `accountId`)다.** auth-service가 발급하고 세 서비스가 공유한다. `member.account_id`, `post.writer_id`, `comment.writer_id`, `post_like.account_id`가 모두 이 값을 가리킨다. 서비스 경계를 넘는 참조에는 FK 제약을 두지 않는다([adr/0012](adr/0012-auth-as-separate-service.md)).

## 1. 공통

### 1.1 BaseTimeEntity

세 서비스에 각각 둔다. `@MappedSuperclass`, `@EntityListeners(AuditingEntityListener.class)`.

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| createdAt | LocalDateTime | `@CreatedDate`, `updatable = false` |
| updatedAt | LocalDateTime | `@LastModifiedDate` |

컬럼 타입은 `DATETIME`이고 **둘 다 NOT NULL**이다([tech-stack.md §6](tech-stack.md)). 감사가 INSERT 시점에 둘을 함께 채우므로 NULL이 들어올 경로가 없다.

**`DATETIME`은 초 단위다. 측정값이다.**

| | `datetime_precision` | 저장되는 값 |
| --- | --- | --- |
| MySQL `DATETIME` | **0** | `2026-10-12 16:33:36` — 소수부가 **남지 않는다**(반올림이다) |
| MySQL `DATETIME(6)` | 6 | `2026-10-12 16:33:36.338618` |
| **H2 `DATETIME`** | **6** | 소수부가 남는다 |

> **정확히는 반올림이다. I-03 리뷰 실측.** `…09.5` 이상은 다음 초가 된다 — 그래서 **가까운 시각이 합쳐지고** 같은 초가 반드시 같아지지는 않는다([api-contract.md §7.1](api-contract.md)의 동률 규칙이 그 위에 선다).

**`D-11` 전에는 테스트와 운영이 달랐다.** H2가 마이크로초를 보존해 **가까운 두 갱신**을 구별했고 MySQL은 반올림으로 한 값에 합쳐 구별하지 못했다. **지금은 감사 시각이 초로 잘려 들어가므로 둘이 같다**([api-contract.md §4.3](api-contract.md)) — **H2에서도 같은 초의 두 갱신은 구별되지 않는다.** `updated_at`의 변화 여부를 단언하는 테스트는 **어느 환경에서도 초보다 섬세하지 않다.**

**그래서 `updated_at`을 감사 흔적으로 쓰지 않는다.** 1초 안에 일어난 일은 보이지 않고, 어떤 갱신이었는지도 구별되지 않는다. 탈퇴 시점을 알아야 하면 `deleted_at`을 추가한다(§2.1의 알려진 한계).

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
|    deleted          |             |    previous_token     |
|    created_at       |             |    rotated_at         |
|    updated_at       |             +-----------------------+
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
| token | String(1024). 테이블 문자셋이 **ascii**다 | NOT NULL, UNIQUE |
| expiresAt | LocalDateTime | NOT NULL |
| previousToken | String(1024). `token` 과 같은 폭·문자셋(ascii) | NULL 허용 |
| rotatedAt | LocalDateTime. 컬럼은 `DATETIME(6)` | NULL 허용 |

계정당 1행이다. 재로그인 시 갱신(upsert)한다. `account_id`에 FK 제약을 둔다(같은 서비스 내이므로 허용).

**행 하나가 세션 하나다.** 계정당 1행이므로 같은 계정의 새 로그인은 옛 세션의 행을 새 세션의 값으로 바꾼다. 그래서 그 행을 지우는 로그아웃은 **어느 세션의 요청인지**를 본다 — 제시한 Refresh Token 이 이 행의 `token` 이나 `previousToken` 과 같을 때만 지운다([requirements/member.md §6.4](requirements/member.md)). 2026-11-11 `D-17` 전에는 로그아웃이 그 계정의 행을 통째로 지워, 늦게 처리된 옛 세션의 로그아웃이 새 세션의 Refresh Token 을 지울 수 있었다.

**`previousToken`·`rotatedAt` 은 재발급의 재사용 유예에 쓴다**([requirements/member.md §6.3](requirements/member.md), `D-17` 이 더했다). 재발급의 회전이 성공하면 같은 UPDATE 가 `previousToken` 에 제시된 토큰을, `rotatedAt` 에 그 회전 시각을 넣는다. **로그인은 둘을 비운다** — 새 세션이므로 옛 세션의 토큰이 유예로 새 세션을 얻지 못하게 한다. 두 컬럼에는 인덱스를 두지 않는다 — 재발급은 검증한 Refresh Token 의 `sub` 로, 로그아웃은 Access Token 의 `sub` 로 행을 찾는다.

**`rotatedAt` 은 `DATETIME(6)` 이고, 앱 시계(`LocalDateTime.now()`)의 값을 마이크로초로 잘라 넣는다.** MySQL 은 6자리를 넘는 소수부를 반올림하므로 앱이 먼저 자른다 — 반올림되면 저장값이 실제 회전보다 늦을 수 있다. **유예의 판정 시각은 회전 시각을 기록한 것과 같은 앱 시계의 값이고 자르지 않는다**(DB 의 `NOW()` 를 쓰지 않는다). 판정은 「판정 시각 ≤ `rotatedAt` + 10초」 다. 그래서 **유예는 회전부터 10초에서 1마이크로초 미만 짧을 수 있고 앱 시계 기준으로 길어지지 않는다.**

§1.1 의 초 단위와 `D-11` 의 초 자르기는 감사 시각(`created_at`·`updated_at`)의 규칙이고, `rotatedAt` 은 감사 시각이 아니라 10초 판정의 입력이다 — 초로 자르면 유예가 회전부터 최대 1초 짧아진다.

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

**문자셋은 테이블 단위로 바꾼다.** 컬럼 단위 구문은 H2가 거부하고, 테스트가 같은 마이그레이션을 돌리므로([tech-stack.md §5.3](tech-stack.md)) 양쪽에서 되는 구문이어야 한다. 측정값이다.

| 구문 | MySQL 8.0 | H2 2.3.232 (MySQL 모드) |
| --- | --- | --- |
| `MODIFY COLUMN token VARCHAR(1024) CHARACTER SET ascii` | OK | **Syntax error** |
| `ALTER COLUMN token SET DATA TYPE VARCHAR(1024) CHARACTER SET ascii` | — | **Syntax error** |
| `ALTER TABLE refresh_token CONVERT TO CHARACTER SET ascii` | OK | OK |

**순서가 뒤집히면 실패한다.** utf8mb4 상태에서 먼저 넓히면 `1024 × 4 = 4096`바이트가 되어 `ERROR 1071`이다. **ascii로 바꾼 뒤 넓힌다.**

`AU-03R` 당시 `refresh_token`의 문자 컬럼은 `token` 하나뿐이어서 테이블 단위와 컬럼 단위의 결과가 같았다. **그 테이블에 JWT 가 아닌 문자 컬럼을 두지 않는다** — 두게 되면 ascii가 그것에도 걸린다. `D-17` 이 더한 `previous_token` 은 같은 JWT 를 담으므로 ascii 가 맞다. **그 컬럼은 테이블 문자셋을 물려받는 구문으로 더한다** — 컬럼 단위 `CHARACTER SET` 구문을 H2 가 거부했다(위 표).

> **이 프로젝트에서 테이블 문자셋을 기본값과 다르게 두는 유일한 곳이다.** 나머지는 스키마 기본값(utf8mb4)을 따른다([tech-stack.md §4.1](tech-stack.md)).

**재발급은 이 행 조회와 `account.deleted` 확인을 같은 트랜잭션에서 한다.** 회전은 조건부 UPDATE(affected rows 확인)로 처리한다. 그렇지 않으면 탈퇴와 재발급이 겹칠 때 삭제된 행이 되살아난다([adr/0012](adr/0012-auth-as-separate-service.md) §8). 재사용 유예는 행을 쓰지 않는다 — 그 판정이 읽는 값의 요건은 [requirements/member.md §6.3](requirements/member.md)이 적는다.

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

**입력 규칙은 2~10자인데 컬럼이 30인 것은 의도된 여유다**([requirements/member.md §2](requirements/member.md)). 규칙이 넓어질 때 마이그레이션을 피한다. **넘침 위험은 없다** — 컬럼이 규칙보다 넓다. MySQL `VARCHAR`는 **문자 수**를 세므로 한글 10자도 30 안에 들어가고, `uk_member_nickname`은 utf8mb4로 120바이트라 InnoDB의 3072바이트 인덱스 한계와 무관하다(§2.2의 `refresh_token`과 다르다).

> **`ddl-auto: validate`는 이 폭을 보지 않는다**(§5.2는 [tech-stack.md](tech-stack.md)에 있다). 엔티티와 마이그레이션의 길이가 어긋나도 기동한다 — auth에서 그 때문에 `refresh_token.token`의 512자 결함이 세 항목을 통과했다. **`information_schema`의 실제 폭을 읽어 비교하는 테스트로 고정한다.**

**프로필의 세 가지 상태를 구분한다.** 셋을 섞으면 탈퇴한 프로필이 재생성된다.

| 상태 | 표현 |
| --- | --- |
| 미등록 | 행이 없다 |
| 활성 | 행이 있고 `deleted = false` |
| 탈퇴 | 행이 있고 `deleted = true` (`nickname`은 NULL) |

`account_id` UNIQUE가 탈퇴 계정의 프로필 재생성을 막는다. 별도 묘비 테이블을 두지 않는다.

**soft delete 시 `nickname`을 NULL로 비운다.** 그대로 두면 `uk_member_nickname` 때문에 그 닉네임이 영구 소각되고, `"탈퇴한 회원"`으로 마스킹해 **저장**하는 구현에서는 두 번째 탈퇴가 UNIQUE 위반으로 500이 난다. `"탈퇴한 회원"`은 **응답 시 변환이지 저장이 아니다**([api-contract.md §3.1 §5](api-contract.md)).

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
|    writer_nickname (스냅샷) |        | FK parent_id  (NULL, 자기) |
|    title                   |        |    writer_id      (논리참조)|
|    content                 |        |    writer_nickname (스냅샷) |
|    category                |        |    content                 |
|    view_count              |        |    deleted                 |
|    comment_count           |        |    created_at              |
|    like_count              |        |    updated_at              |
|    attachment_count        |        +----------------------------+
|    deleted                 |
|    created_at / updated_at |
+----------------------------+

  post_like                    post_view                      attachment
+------------------------+   +-------------------------+   +---------------------------+
| PK id                  |   | PK id                   |   | PK id                     |
| FK post_id         UQ* |   |    post_id (FK 없음) UQ* |   | FK post_id                |
|    account_id(논리) UQ* |   |    viewer_key       UQ* |   |    storage_key         UQ |
|    created_at          |   |    viewed_at            |   |    original_filename      |
+------------------------+   +-------------------------+   |    content_type           |
  UQ* = (post_id,               UQ* = (post_id,             |    size                   |
         account_id)                   viewer_key)          |    deleted                |
                                                           |    created_at / updated_at|
                                                           +---------------------------+
```

**`post_like`·`post_view`·`attachment`·`comment.parent_id`·`post` 의 `category`·`like_count`·`attachment_count` 는 2026-11-11 `D-18` 이 설계한 2차 기능 확장의 것이다**([plan/phase2.md §5](plan/phase2.md)). 이 문서는 계약을 적고, 그것을 만드는 마이그레이션과 코드는 `D-20` 이 세울 항목의 일이다 — 그 전의 `sp_board` 에는 없다.

### 4.1 post

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | Long | PK | |
| writerId | Long | NOT NULL, **FK 제약 없음** | `accountId` 논리 참조 |
| writerNickname | String(30) | NOT NULL | 작성 시점 닉네임 스냅샷 |
| title | String(200) | NOT NULL | |
| content | String | NOT NULL, `columnDefinition = "TEXT"` | |
| category | PostCategory | NOT NULL, default `FREE`. 컬럼 `VARCHAR(20)` | `NOTICE`·`FREE`·`QNA`([requirements/board.md §8](requirements/board.md)) |
| viewCount | long | NOT NULL, default 0 | 24시간 판정으로 집계된 조회 수(§4.5, 2차) |
| commentCount | int | NOT NULL, default 0 | 목록 N+1 방지용 비정규화. 답글을 포함한 활성 댓글 수(§5) |
| likeCount | int | NOT NULL, default 0 | `post_like` 행 수의 비정규화(§4.4) |
| attachmentCount | int | NOT NULL, default 0 | 활성 `attachment` 수의 비정규화. 개수 상한의 원자적 판정에 쓴다(§6) |
| deleted | boolean | NOT NULL, default false | |

`writer_id`에 FK 제약을 걸지 않는 이유는 [architecture.md §5](architecture.md)를 본다.

**기존 행의 `category` 는 `FREE` 다** — 컬럼을 더하는 마이그레이션의 기본값이 그것을 채운다. 집계 컬럼(`view_count`·`comment_count`·`like_count`·`attachment_count`)은 **좁은 UPDATE 로만 바꾼다**(§6).

### 4.2 comment

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | Long | PK | |
| post | Post | `@ManyToOne(LAZY)`, NOT NULL | 같은 서비스 내이므로 연관관계 매핑 사용 |
| writerId | Long | NOT NULL, FK 제약 없음 | `accountId` 논리 참조 |
| writerNickname | String(30) | NOT NULL | 작성 시점 스냅샷 |
| content | String(500) | NOT NULL | |
| deleted | boolean | NOT NULL, default false | 삭제 시 "삭제된 댓글입니다" 표시 |
| parent | Comment | `@ManyToOne(LAZY)`, **NULL 허용**. 컬럼 `parent_id BIGINT` | 답글이면 그 부모(최상위 댓글), 최상위면 NULL([requirements/board.md §12](requirements/board.md)) |

**`parent` 는 1차의 이 절이 "2차에 추가한다" 고 예고한 것이고 `D-18` 이 그 모양을 정했다.** 깊이는 1단계다 — 부모의 `parent` 는 언제나 NULL 이다. 그 불변식은 제약이 아니라 작성 경로의 판정(400 `CM003`)이 지킨다. **기존 행의 `parent_id` 는 NULL** 이다 — 1차의 댓글은 모두 최상위다.

> **컬럼 폭에 여유가 없다. member 와 다르다.** `title` 은 입력 규칙이 1~200자인데 컬럼이 `VARCHAR(200)`, 댓글 `content` 는 1~500자인데 `VARCHAR(500)` 이다([requirements/board.md §4](requirements/board.md)). §3.1 의 `nickname` 은 규칙 2~10자에 컬럼 30으로 **의도된 여유**를 뒀지만 여기는 규칙과 폭이 같다. 규칙이 넓어지면 **마이그레이션이 반드시 따라와야 한다.**
>
> **`ddl-auto: validate` 는 이 폭을 보지 않는다**([tech-stack.md §5.2](tech-stack.md)). 엔티티와 마이그레이션이 어긋나도 기동하고, 넘치는 입력이 들어올 때 비로소 `DataIntegrityViolationException` 으로 터진다. auth 에서 그 때문에 `refresh_token.token` 의 512자 결함이 **세 항목을 통과했다.** 여유가 없는 board 는 어긋남의 대가가 더 직접적이다 — **`information_schema` 의 실제 폭을 읽어 비교하는 테스트로 고정한다.** 그 비교는 Flyway 가 스키마를 소유할 때만 뜻이 있다(§5.1).
>
> **`content` 는 `TEXT` 라 폭 비교의 대상이 아니다.** `TEXT` 는 65,535 **바이트**이고 10,000자는 utf8mb4 최악 4바이트로도 40,000바이트이므로 들어간다. 규칙이 16,000자를 넘기면 그 전제가 깨진다.

### 4.3 인덱스

| 이름 | 대상 | 용도 |
| --- | --- | --- |
| `idx_post_created_at` | `post(created_at DESC)` | 최신순 목록 |
| `idx_post_writer_id` | `post(writer_id)` | 내가 쓴 글, 2차 이벤트 일괄 갱신 |
| `idx_post_title` | `post(title)` | 제목 **앞부분** 검색. 아래 주의 |
| `idx_comment_post_id` | `comment(post_id, created_at)` | 게시글별 댓글 목록 |
| `fk_comment_post_id` | `comment(post_id)` → `post(id)` | 같은 서비스 안이므로 참조 무결성을 건다 |
| `idx_post_category` | `post(category, created_at DESC)` | 카테고리별 최신순 목록, 공지 고정 조회 |
| `idx_comment_parent_id` | `comment(parent_id, created_at)` | 최상위 댓글들의 답글을 한 번에 읽는다. FK 가 요구하는 인덱스도 겸한다 |
| `fk_comment_parent_id` | `comment(parent_id)` → `comment(id)` | 답글의 부모 |
| `uk_post_like_post_account` | `post_like(post_id, account_id)` UNIQUE | 회원당 글 하나에 한 번. `liked` 조회와 FK 인덱스를 겸한다 |
| `fk_post_like_post_id` | `post_like(post_id)` → `post(id)` | |
| `uk_post_view_post_viewer` | `post_view(post_id, viewer_key)` UNIQUE | 판정 키당 글 하나에 한 행 |
| `idx_post_view_viewed_at` | `post_view(viewed_at)` | 오래된 판정 행의 주기 삭제 |
| `uk_attachment_storage_key` | `attachment(storage_key)` UNIQUE | 저장 이름이 겹치지 않는다 |
| `idx_attachment_post_id` | `attachment(post_id)` | 상세의 첨부 목록. FK 인덱스를 겸한다 |
| `fk_attachment_post_id` | `attachment(post_id)` → `post(id)` | |

`idx_post_writer_id`는 2차 Kafka 이벤트의 `UPDATE post SET writer_nickname=? WHERE writer_id=?`를 뒷받침한다.

**이 표가 제약 이름의 정본이다.** §4.2가 `post` 를 `@ManyToOne` 으로만 적은 것의 FK 이름이 `fk_comment_post_id` 다. **`writer_id` 에는 FK 가 없으므로 이 표에도 없다** — 그 부재가 의도다(§4.1). **`post_like.account_id` 와 `post_view.post_id` 에도 FK 가 없다** — 앞은 서비스 경계를 넘고(§4.1 과 같은 이유), 뒤는 락 때문이다(§4.5).

**`idx_post_title` 은 `LIKE '%키워드%'` 를 돕지 않는다.** B-트리 인덱스는 선행 와일드카드가 붙으면 쓰이지 않고, [api-contract.md §4.1](api-contract.md)이 `keyword` 를 부분 일치로 고정한다. `searchType=CONTENT` 는 `TEXT` 컬럼이라 인덱스 자체가 없고 `WRITER` 가 보는 `writer_nickname` 에도 인덱스가 없다. **1차는 이 상태로 둔다** — [nfr.md §1](nfr.md)의 기준이 1만 건 p95 300ms 이고 그 규모에서는 전체 스캔으로 충분하다. 인덱스는 **키워드 없는 목록**(`idx_post_created_at`)과 **내가 쓴 글**(`idx_post_writer_id`)을 위한 것이다. 전문 검색이 필요해지면 `FULLTEXT` 를 **명시적 결정으로** 추가한다.

### 4.4 post_like

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | Long | PK, IDENTITY | |
| post | Post | `@ManyToOne(LAZY)`, NOT NULL. 컬럼 `post_id` | FK `fk_post_like_post_id` |
| accountId | Long | NOT NULL, **FK 제약 없음** | 누른 회원. `accountId` 논리 참조 |
| createdAt | LocalDateTime | NOT NULL. 컬럼 `DATETIME` | `@CreatedDate` — 감사 시각과 같은 초 자르기를 받는다(§1.1) |

**행 하나가 "이 회원이 이 글을 눌렀다" 이다.** `uk_post_like_post_account` 가 회원당 한 번을 보장하는 최종 판정이다. 취소하면 행을 **지운다**(물리 삭제) — 갱신할 것이 없으므로 `updated_at` 을 두지 않고 `BaseTimeEntity` 를 상속하지 않는다. **글을 지워도 행은 남는다**([requirements/board.md §10](requirements/board.md)).

### 4.5 post_view

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | Long | PK, IDENTITY | |
| postId | Long | NOT NULL, **FK 제약 없음**. 컬럼 `post_id` | 연관관계 매핑을 두지 않는다 |
| viewerKey | String(80) | NOT NULL | `a:{accountId}` 또는 `i:{HMAC-SHA256 의 소문자 hex 64자}`([requirements/board.md §9.1](requirements/board.md)) |
| viewedAt | LocalDateTime | NOT NULL. 컬럼 `DATETIME` | **마지막으로 집계된 조회의 시각.** 앱 시계의 값이다 |

**행 하나가 "이 조회자의 이 글 조회가 이 시각에 집계됐다" 이다.** 판정은 [requirements/board.md §9.3](requirements/board.md)이 적는다 — 집계될 때만 `viewed_at` 이 바뀌고, 24시간 안의 조회는 행을 건드리지 않는다.

**`post_id` 에 FK 를 두지 않는다.** 판정 INSERT 의 FK 검사가 `post` 행에 공유 락을 잡고 같은 트랜잭션이 이어서 `view_count` 의 좁은 UPDATE 로 배타 락을 요청하므로, 같은 글을 동시에 보는 트랜잭션끼리 승격 교착을 만들 것으로 본다(추정 — 실 MySQL 측정 대상). 좋아요(§4.4)는 `post` 의 배타 락을 **먼저** 잡아 그 문제를 피하지만(§6), 조회 판정은 집계 여부를 판정 행을 쓴 **뒤에야** 알므로, 그 순서를 쓰면 집계되지 않는 조회마다 `post` 의 배타 락을 잡고 되돌려야 해서 쓰지 않는다. FK 가 지키던 것은 "없는 글의 판정 행" 인데, 판정은 상세 조회의 404 판정 뒤에만 일어나고 `post` 행은 물리 삭제되지 않는다(soft delete). **잃는 것은 제약이 없다는 것뿐이다.**

**`viewed_at` 은 감사 시각이 아니다.** `@CreatedDate`·`@LastModifiedDate` 를 쓰지 않고 판정하는 코드가 넣는다. 초 단위(`DATETIME`)로 충분하다 — 24시간 경계에서 1초 미만의 차이는 판정의 의미를 바꾸지 않는다. **`viewer_key` 는 utf8mb4 로 80자다** — 내용은 ASCII 이지만 §2.2 의 `refresh_token` 처럼 문자셋을 바꿀 이유가 없다(`uk_post_view_post_viewer` 가 `8 + 80 × 4` 바이트로 InnoDB 한계 3072 안이다).

**오래된 행은 주기적으로 지운다.** `viewed_at` 이 24시간 전보다 이른 행은 없는 행과 판정이 같으므로 지워도 결과가 같다. 행 수는 그래서 "최근 24시간 남짓 안에 집계된 조회자·글 쌍" 으로 묶인다.

### 4.6 attachment

`BaseTimeEntity` 를 상속한다.

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | Long | PK, IDENTITY | 내려받기 경로의 식별자 |
| post | Post | `@ManyToOne(LAZY)`, NOT NULL. 컬럼 `post_id` | FK `fk_attachment_post_id` |
| storageKey | String(36) | NOT NULL, UNIQUE | **저장 이름.** 서버가 만든 UUID 문자열이다. 원본 파일명을 쓰지 않는다 |
| originalFilename | String(255) | NOT NULL | 원본 파일명. **메타데이터로만** 쓴다 — 저장 경로에 들어가지 않는다 |
| contentType | String(30) | NOT NULL | **매직 바이트로 판정한 형식.** `image/jpeg`·`image/png`·`image/gif`·`image/webp` 중 하나([requirements/board.md §11](requirements/board.md)) |
| size | long | NOT NULL | 바이트 |
| deleted | boolean | NOT NULL, default false | 첨부 삭제 |

**저장 이름이 UUID 인 이유는 경로 탐색 차단이다.** 원본 파일명(예: `../../x`)이 저장 경로에 닿을 길이 없다. 파일은 저장 루트([tech-stack.md §4.5](tech-stack.md)) 바로 아래의 그 이름 하나다.

**`original_filename` 은 규칙과 폭이 같다(255).** §4.2 블록인용의 `title` 처럼 여유가 없으므로 `information_schema` 의 실제 폭을 읽어 비교하는 테스트에 넣는다.

**행과 파일의 수명이 다르다.** 첨부 삭제는 행을 `deleted = true` 로만 바꾸고, 글 삭제는 행을 건드리지 않는다. 내려받기가 첨부와 글이 둘 다 활성일 때만 파일을 주므로 그 경우들은 404 다. **파일은 어느 경우에도 지우지 않고**, DB 트랜잭션이 실패해 지우려던 파일이 남는 경우도 있다 — 정리는 범위 밖이다([requirements/board.md §11](requirements/board.md)).

## 5. commentCount 동기화

댓글 작성·삭제 시 `post.comment_count`를 갱신한다. 같은 트랜잭션 안에서 처리한다.

| 동작 | 처리 |
| --- | --- |
| 댓글 작성 | `comment_count + 1` |
| 댓글 삭제(Soft) | `comment_count - 1` |
| 게시글 삭제(Soft) | 하위 댓글도 `deleted = true`. `comment_count`는 그대로 |
| 답글 작성 | `comment_count + 1` — 답글도 댓글이다 |
| 답글이 달린 댓글 삭제(Soft) | 그 댓글만 `deleted = true`, `comment_count - 1`. **답글은 그대로다** |

**`comment_count` 는 답글을 포함한 활성 댓글 수다**(2026-11-11 `D-18`). 1차에는 답글이 없어 "활성 댓글 수" 가 곧 목록의 `totalElements` 였다. 답글이 생긴 뒤의 목록은 최상위 댓글을 페이징하므로 `totalElements` 는 최상위 항목의 수이고 둘은 다르다([api-contract.md §4.5](api-contract.md)).

**게시글 삭제의 두 효과도 한 트랜잭션이다.** 위 표 셋째 줄의 `post.deleted`와 하위 댓글의 `deleted`가 따로 커밋되면 **둘 중 하나만 반영된 상태가 남는다** — 게시글은 사라졌는데 댓글이 살아 있거나, 댓글만 지워지고 게시글이 목록에 남는다. 첫 문장의 "같은 트랜잭션"은 댓글 작성·삭제의 건수 갱신만 가리키므로 여기서 따로 못박는다.

`comment_count`가 음수가 되지 않아야 한다. 회귀 테스트로 확인한다.

## 6. post 의 집계 컬럼 — 좁은 UPDATE 와 락 순서

**`post` 의 집계 컬럼은 근거 행과 같아야 한다.** `comment_count` 는 활성 댓글(§5), `like_count` 는 `post_like` 행, `attachment_count` 는 활성 `attachment` 의 수다. `view_count` 는 근거 행이 없는 누계이고 판정(§4.5)이 집계한 횟수다.

| 규칙 | 이유 |
| --- | --- |
| **집계는 좁은 UPDATE(`col = col ± 1`)로만 바꾼다.** 엔티티 필드를 바꿔 더티 체킹으로 저장하지 않는다 | 엔티티를 읽어 메모리에서 바꾸면 동시 커밋 사이에서 증가가 소실된다 — 1차 B-10(`comment_count`)·B-11(`view_count`)이 측정하고 고쳤다([plan/phase1.md](plan/phase1.md)) |
| **감소는 0 아래로 내려가지 않는 조건을 문장에 둔다**(`… where col > 0`) | 음수 금지([requirements/board.md §5](requirements/board.md) 규칙 4) |
| **엔티티 갱신이 집계 컬럼을 싣지 않는다** | 아래 블록인용 |
| **집계와 근거 행의 쓰기는 한 로컬 트랜잭션이다** | 둘 중 하나만 커밋되면 어긋난다 — §5 의 댓글과 같다 |
| **집계의 증감은 근거 행의 전환(생김·지워짐·활성→삭제)이 이 트랜잭션에서 실제로 일어났을 때만 남긴다.** 전환은 조건부 쓰기의 영향 행 수로 확인하고, 증감을 먼저 했는데 전환이 0행이면 트랜잭션을 되돌린다. `view_count` 에서는 판정 행이 생기거나 기준 시각이 바뀐 것이 전환이다(§4.5) | 락 전에 읽은 상태로 판정하고 조건 없이 쓰면, 같은 전환을 노린 동시 요청이 둘 다 성공해 증감이 두 번 남는다 |

> **수정(P-06)·삭제(P-07)도 `post` 를 엔티티로 저장한다.** `Post` 에 갱신 컬럼을 좁히는 설정이 없으므로 그 UPDATE 도 B-10 이 측정한 것처럼 **모든 컬럼**을 실을 것으로 본다(코드 읽기 — 그 경로의 문장은 측정하지 않았다). 그렇다면 글 수정이 그 트랜잭션이 읽은 낡은 집계를 다시 써서, 그 사이에 커밋된 댓글·좋아요·첨부의 증감을 지운다. 1차의 `comment_count`·`view_count` 에도 같은 창이 있었을 것이고(추정 — B-10·B-11 은 댓글 쓰기와 상세 조회 경로를 쟀고 이 경로는 그 항목들의 범위가 아니었다), 2차에서는 **`attachment_count` 의 상한 판정까지 무너뜨릴 수 있다** — 낡은 값으로 되돌아가면 상한을 넘는 첨부가 들어갈 수 있다. **그래서 엔티티 갱신이 집계 컬럼을 쓰지 않게 한다**(예: 매핑에서 집계 컬럼을 갱신 대상에서 빼거나, 바뀐 컬럼만 싣는 설정). 수단은 구현이 고르고, 수정과 집계 갱신을 끼워넣은 테스트로 본다.

> **1차의 댓글 삭제 경로가 위 표의 전환 규칙을 지키지 않는다**(2026-11-11 코드 읽기 — 측정하지 않았다). 활성 댓글을 락 없이 읽고, 엔티티의 `deleted` 를 바꿔 더티 체킹으로 조건 없이 저장한 뒤 `comment_count` 를 줄인다. 같은 댓글의 동시 삭제가 둘 다 활성으로 읽으면 둘 다 줄일 것으로 본다(추정 — 실 MySQL 측정 대상, [plan/phase2.md §5.4](plan/phase2.md)). `D-20` 이 결함 수정 항목으로 다룬다. 고칠 때 순서는 §6.2 의 첨부 삭제처럼 `post` 감소를 먼저 한다 — 지금 순서(댓글 행 → `post`)는 답글 작성(`post` → 부모 행의 FK 공유 락)과 반대라 교착할 것으로 본다(추정).

### 6.1 좋아요 — 락 순서와 멱등

**`post` 행의 배타 락을 `post_like` 쓰기보다 먼저 잡는다.**

```
PUT  /posts/{id}/like   한 트랜잭션
  1) UPDATE post SET like_count = like_count + 1 WHERE id = ? AND deleted = false
       0행이면 404 P001. 1행이면 post 행의 배타 락을 쥔다
  2) 이 회원의 post_like 행이 있으면 이미 누른 것 -> 트랜잭션을 되돌린다(1)의 증가도 되돌아간다) 200 liked:true
  3) INSERT post_like (post_id, account_id)
       UNIQUE 충돌이면 2)와 같은 결과

DELETE /posts/{id}/like  한 트랜잭션
  1) UPDATE post SET like_count = like_count - 1 WHERE id = ? AND deleted = false AND like_count > 0
       0행이면: 글이 없거나 지워졌으면 404 P001, 아니면 2)를 그대로 한다
       (행이 있는데 집계가 0 이면 근거 행과 어긋난 상태다 -> 집계는 0 에 두고 WARN 로그)
  2) DELETE post_like WHERE post_id = ? AND account_id = ?
       0행이면 누르지 않은 것 -> 트랜잭션을 되돌린다(1)의 감소도 되돌아간다) 200 liked:false
```

**순서를 뒤집으면 교착할 것으로 본다.** `post_like` 의 INSERT 는 FK 검사로 `post` 행에 **공유 락**을 잡는다. 같은 글에 두 트랜잭션이 먼저 INSERT 하면 둘 다 공유 락을 쥔 채 `like_count` UPDATE 의 **배타 락**을 기다려 서로를 막는다(승격 교착, 추정 — 실 MySQL 측정 대상, [plan/phase2.md §5.4](plan/phase2.md)). 먼저 배타 락을 쥐면 FK 검사의 공유 락은 같은 트랜잭션의 배타 락에 이미 덮여 있다.

**1)의 락이 같은 글의 좋아요를 한 줄로 세운다.** 그래서 2)의 확인이 앞서 커밋된 좋아요를 본다 — **단 그 확인이 락을 잡은 뒤의 읽기일 때다.** 반복 읽기 격리에서 그 트랜잭션이 락 전에 일반 읽기를 했으면 그때의 스냅샷을 읽어 놓칠 수 있다. 그래서 **최종 판정은 UNIQUE 다** — 3)의 충돌을 정상 결과로 다루고 그 응답을 500 으로 만들지 않는다. 충돌의 로그 수준은 조회수 판정과 같은 측정 대상이다([requirements/board.md §9.3](requirements/board.md)). 응답의 `likeCount` 는 쓴 뒤(되돌렸으면 되돌린 뒤) 읽은 값이다.

**위 순서가 오케스트레이터 기본값이다**([plan/phase2.md §5.1](plan/phase2.md)). 1)을 잠금 읽기로 잡고 증가를 근거 행이 생긴 뒤에 하는 모양도 요건을 지킨다. 어느 쪽이든 **"`post` 의 배타 락이 먼저, 증가는 근거 행이 새로 생겼을 때만 남는다"** 가 요건이다.

### 6.2 첨부 — 개수 상한의 원자적 판정

```
POST /posts/{postId}/attachments
  0) 파일을 저장소에 쓴다 (새 UUID 이름)               <- 트랜잭션 밖
  BEGIN
  1) UPDATE post SET attachment_count = attachment_count + 1
       WHERE id = ? AND deleted = false AND attachment_count < 10
       0행이면: 글이 없거나 지워졌으면 404 P001, 아니면 409 AT003
  2) INSERT attachment (...)
  COMMIT
  실패하면 0)의 파일을 지운다 (best effort)
```

**상한은 1)의 조건부 UPDATE 하나가 판정한다.** 세어 보고 넣는 두 단계(`SELECT count` → INSERT)는 동시 업로드에서 상한을 넘는다. 1)이 `post` 행의 배타 락을 먼저 잡으므로 2)의 FK 공유 락은 §6.1 과 같은 이유로 문제가 없다. 상한(10)은 [requirements/board.md §11](requirements/board.md)의 값이다.

**미리 세어 보는 것은 막지 않는다** — 파일을 쓰기 전에 넘는 요청을 거르면 쓰고 지우는 일이 준다. 둔다면 **형식·파일명 판정 뒤**다. 그러나 **판정은 1)이다.** 0바이트 파일(400 `C001`) → 글 확인(404 `P001`) → 소유자 확인(403 `P002`) → 형식 판정(400 `AT002`)·파일명 검증(400 `C001`)은 이 순서로 0) 전에 한다 — 거부될 요청의 파일을 쓰지 않는다. 순서는 [requirements/board.md §11](requirements/board.md)의 판정 순서와 같다. 1)의 404 는 그 확인과 커밋 사이에 글이 지워진 경우다.

**첨부 삭제**는 §6.1 의 `DELETE` 와 같은 모양이다. **어긋난 상태(근거 행은 있는데 집계가 0)는 두 경로 모두 WARN 로그로 드러낸다** — 조용히 흡수하면 집계 결함이 묻힌다.

```
DELETE /attachments/{id}  한 트랜잭션 (404 AT001 -> 403 P002 판정 뒤)
  1) UPDATE post SET attachment_count = attachment_count - 1
       WHERE id = ? AND attachment_count > 0
       0행이면 활성 첨부가 있는데 집계가 이미 0 인, 근거 행과 어긋난 상태다 -> 2)를 그대로 하고 집계는 0 에 둔다(음수로 내리지 않는다), WARN 로그
  2) UPDATE attachment SET deleted = true WHERE id = ? AND deleted = false
       0행이면 이미 지워진 것 -> 트랜잭션을 되돌린다(1)의 감소도 되돌아간다) 404 AT001
```

**판정 순서의 404·403 은 락 전의 읽기라 동시 삭제를 거르지 못한다.** 그래서 2)의 조건부 전환이 최종 판정이다 — 조건 없이 지우면 같은 첨부의 동시 삭제가 둘 다 1행으로 성공해 `attachment_count` 가 두 번 줄고, 활성 첨부보다 작아진 집계 때문에 올리기의 상한 판정(`attachment_count < 10`)을 지나 10개를 넘는 첨부가 들어간다.

## 7. 2차 기능 확장의 마이그레이션 — 할 것

**번호는 `D-20` 이 배정한다**([plan/phase1.md §2.4](plan/phase1.md)). 여기는 무엇을 해야 하는지만 적는다. 이름과 폭은 §4 의 표가 정본이다.

| 대상 | 할 것 |
| --- | --- |
| `post` | `category VARCHAR(20) NOT NULL DEFAULT 'FREE'`, `like_count INT NOT NULL DEFAULT 0`, `attachment_count INT NOT NULL DEFAULT 0` 를 더한다. 기본값이 기존 행을 채운다. `idx_post_category` 를 만든다 |
| `comment` | `parent_id BIGINT NULL` 을 더하고 `fk_comment_parent_id`·`idx_comment_parent_id` 를 만든다. 기존 행은 NULL 이다 |
| `post_like` | §4.4 대로 만든다. `uk_post_like_post_account`·`fk_post_like_post_id` |
| `post_view` | §4.5 대로 만든다. `uk_post_view_post_viewer`·`idx_post_view_viewed_at`. **FK 를 두지 않는다** |
| `attachment` | §4.6 대로 만든다. `uk_attachment_storage_key`·`idx_attachment_post_id`·`fk_attachment_post_id` |

**적용된 마이그레이션(`V1`·`V2`)을 고치지 않는다**([plan/phase1.md §2.4](plan/phase1.md)). 테스트가 같은 마이그레이션을 H2 에서 돌리므로([tech-stack.md §5.3](tech-stack.md)) **두 DB 에서 되는 구문**이어야 한다 — 한 `ALTER TABLE` 에 컬럼을 여럿 더하는 구문처럼 둘이 다르게 받을 수 있는 것은 구현이 H2 에서 확인한다(§2.2 의 문자셋 구문이 그렇게 갈렸다).
