---
title: 2차 board 작업 계획
type: plan
status: living
version: v1
updated: 2026-11-12
read_when: "2차 기능 확장의 board 작업 항목(B-14 부터)의 범위·의존·완료 기준을 확인하거나 다음 할 일을 고를 때. 상태는 sp-board 의 docs/checklist.md 를 본다"
related: [phase2.md, phase1.md, phase2-auth-member.md, phase2-frontend-integration.md, ../requirements/board.md, ../domain-model.md, ../api-contract.md, ../nfr.md]
---
# 2차 board 작업 계획

2026-11-12 `D-20` 이 썼다. [phase2.md §5](phase2.md) 표의 board 기능과, 그 설계가 [../domain-model.md §6](../domain-model.md)에서 결함으로 지목한 1차 코드의 자리를 작업 항목으로 쪼갠다. **설계의 정본은 [phase2.md §5.2](phase2.md)의 board 표가 가리키는 곳이다.** 이 문서는 작업 항목(산출물·참조·의존·완료 기준·검증)과 마이그레이션 번호만 갖는다 — 완료 기준이 정본의 값을 옮겨 적은 자리는 읽기 쉽게 하려는 요약이고, 정본과 다르면 정본이 이긴다. 상태는 적지 않는다 — `sp-board` 의 `docs/checklist.md` 가 갖는다([README.md](README.md)).

**1차 계획의 운영 규칙을 그대로 쓴다.** 마이그레이션 번호는 계획이 배정하고([phase1.md §2.4](phase1.md)), 다른 항목의 산출물을 고칠 때와 멈출 때는 [phase1.md §2.5](phase1.md)·§2.6 을 따른다. 1차 항목이 단언한 응답 키 집합·집계·조회수 기준은 그 시점의 계약이다([phase1.md](phase1.md) §6 머리의 블록인용) — 아래 항목이 그 테스트를 지금의 계약으로 고치는 것은 1차의 판정을 뒤집는 것이 아니다.

**ID 는 `B-14` 부터다.** 1차의 `B-13` 다음 번호이고 번호를 재사용하지 않는다([README.md](README.md)의 항목 ID 규칙). auth·member 쪽 항목은 `D-20` 의 다른 계획([phase2-auth-member.md](phase2-auth-member.md))이 갖는다 — 이 문서는 그 항목을 ID 가 아니라 기능 이름(「auth·member 계획의 … 항목」)으로 가리킨다.

## 1. 단계와 병렬 가능성

### 1.1 단계

| 단계 | 항목 | 성격 |
| --- | --- | --- |
| **기반** | B-14, B-15, B-16 | 스키마·엔티티·`post` 집계의 좁은 UPDATE·에러 코드·인가 규칙·설정을 먼저 끝낸다. 기능 항목이 같은 엔티티·설정 파일을 고치지 않게 한다 — [phase1.md §1.1](phase1.md)의 기반 단계와 같은 이유다 |
| **결함 수정** | B-17, B-18 | [../domain-model.md §6](../domain-model.md)의 블록인용이 2026-11-11 코드 읽기로 지목한 1차 코드의 자리다. **완료된 1차 항목의 산출물을 고치므로** 그 항목의 완료 기준과 충돌하지 않는지 먼저 본다 |
| **기능** | B-19 ~ B-24 | 기반 산출물을 읽고 자기 기능의 서비스·컨트롤러·DTO 와 자기 테이블의 리포지토리 문장을 만든다 |

```
기반       B-14 스키마·엔티티             B-15 에러 코드·multipart
                                               |
                                          B-16 인가·선택적 리졸버·환경값 가드
결함 수정  B-17 댓글 삭제 (의존 없음)
           B-18 집계 덮어쓰기 (B-14 뒤)
기능
  글       B-18 -> B-19 카테고리 -> B-21 상세·조회수 -> B-24 내려받기·지우기·첨부 목록
  좋아요   B-20 (B-14·B-16 뒤)
  댓글     B-17 -> B-22 답글
  첨부     B-23 올리기 (B-14·B-15·B-16 뒤) -> B-24
```

### 1.2 의존과 병렬

**저장소당 워커가 하나면 ID 순서대로 하면 된다**([phase1.md §1.2](phase1.md)) — ID 순서가 아래 의존을 만족한다. 워크트리를 나눠 여럿을 동시에 돌릴 때는 **의존이 끝났고 셋째 열의 상대가 돌고 있지 않은 항목**만 같이 돌린다. 예: 기반 동안 B-14·B-15 를(B-17 은 B-14 와 `Comment`·`PostRepository` 를 함께 고친다), 기반 뒤에는 글 줄(B-18 → B-19 → B-21)·좋아요(B-20)·댓글(B-17 → B-22)·첨부 올리기(B-23)를 나란히 돌릴 수 있다 — 다만 B-17 은 B-21 과 `PostRepository` 를 함께 고친다. 셋째 열에는 `docs/checklist.md` 를 넣지 않는다 — 항목마다 자기 줄의 상태만 바꾸고, 병합에서 겹치면 둘 다 남긴다(§2.1).

| 항목 | 의존 | 같은 파일을 고치는 항목 — 같이 돌리지 않는다 |
| --- | --- | --- |
| B-14 | 없음 | B-17 (`Comment`·`PostRepository`), B-18 (`Post`), B-21 (`PostRepository`) |
| B-15 | 없음 | B-16 (`application.yml`) |
| B-16 | B-15 | B-15 |
| B-17 | 없음 | B-14 (`Comment` — `softDelete()` 의 주석, `PostRepository`), B-21 (`PostRepository`), B-22 (`CommentService`·`CommentRepository`·`CommentServiceTest`) |
| B-18 | B-14 | B-14 (`Post`), B-19, B-21, B-24 (`PostServiceTest`) |
| B-19 | B-14, B-15, B-18 | B-18 (`PostServiceTest`), B-21, B-24 (`PostService`·`PostController`·`post/dto`·`PostServiceTest`) |
| B-20 | B-14, B-16 | 없음 |
| B-21 | B-14, B-16, B-19 | B-14 (`PostRepository`), B-17 (`PostRepository`), B-18 (`PostServiceTest`), B-19, B-24 |
| B-22 | B-14, B-15, B-17 | B-17 |
| B-23 | B-14, B-15, B-16 | B-24 (`attachment/*`) |
| B-24 | B-21, B-23 | B-18 (`PostServiceTest`), B-19, B-21, B-23 |

**auth·member 계획과의 의존.** board 항목은 auth·member 계획의 항목을 기다리지 않는다. 걸리는 것은 통합 비교다 — 예: `C008` 매핑의 세 서비스 비교는 B-15 와 auth·member 계획의 multipart 예외 매핑 항목들(서비스마다 하나)이 모두 끝난 뒤다(§4.1).

## 2. 경로 소유와 마이그레이션 번호

### 2.1 공유 지점

[phase1.md §2](phase1.md)와 같은 지도다 — 저장소당 워커가 하나면 경로를 넘는 것 자체는 문제가 아니고, 여럿을 동시에 돌릴 때만 강제다.

| 파일 | 만드는·넓히는 항목 | 이어서 고치는 항목 | 규칙 |
| --- | --- | --- | --- |
| `post/entity/Post`, `comment/entity/Comment`, 새 엔티티 | B-14 | B-17 (`softDelete()` 의 주석), B-18 (`Post` 의 매핑) | 도메인 메서드는 B-14 가 만든다. 기능 항목은 엔티티를 고치지 않는다 |
| `post/repository/PostRepository` | B-14 (`like_count`·`attachment_count` 의 좁은 UPDATE) | B-17 (`increaseCommentCount` 의 javadoc), B-21 (`increaseViewCount` 의 javadoc) | 집계를 바꾸는 문장은 이 리포지토리에 둔다([../conventions.md §1.3](../conventions.md)) |
| 새 테이블의 리포지토리 | B-14 (인터페이스, `PostLikeRepository` 의 존재 확인) | 그 테이블을 쓰는 기능 항목 — `post_like` B-20, `post_view` B-21, `attachment` B-23·B-24 | 존재 확인은 B-20(멱등 판정)과 B-21(`liked`)이 같이 쓰므로 B-14 가 만든다 |
| `comment/service/CommentService`, `comment/repository/CommentRepository` | B-17 | B-22 | 순차 |
| `post/service/PostService`, `post/controller/PostController`, `post/dto/PostResponse`·`PostDetailResponse` | B-19 | B-21, B-24 | 순차 |
| `global/error/ErrorCode`, `global/error/GlobalExceptionHandler` | B-15 | - | 기능 항목은 읽기만 한다 |
| `global/config/SecurityConfig`, `global/security/` | B-16 | - | 같음 |
| `application.yml` | B-15 (multipart·Tomcat) | B-16 (나머지 키) | 순차 |
| `JwtAuthenticationTest` 의 인증 경로 목록 | B-16 (새 인증 경로의 무토큰 401) | - | 핸들러를 만드는 항목은 자기 경로가 목록에 있는지 확인한다([../tech-stack.md §2.1](../tech-stack.md)) |
| `docs/checklist.md` | `D-20` (머리말·2차 줄) | 모든 항목 | 자기 줄의 상태만 |

> **이 표가 완전하다고 보증하지 않는다.** 여럿을 동시에 돌릴 때 표 밖의 파일에서 충돌이 나면 이 표가 빠뜨린 것일 수 있다 — 워커의 잘못으로 단정하지 않는다([phase1.md §2](phase1.md)의 공유 지점 블록인용과 같다).

### 2.2 마이그레이션 번호

**board 의 2차 마이그레이션은 B-14 가 쓴다.** 번호와 적용 순서가 어긋날 여지를 없애려고 한 항목에 모은다.

| 버전 | 파일 | 할 것 — [../domain-model.md §7](../domain-model.md)의 줄 |
| --- | --- | --- |
| `V3` | `V3__add_post_category_and_counts.sql` | `post` — `category`·`like_count`·`attachment_count` 를 더하고 `idx_post_category` 를 만든다 |
| `V4` | `V4__add_comment_parent.sql` | `comment` — `parent_id` 를 더하고 `fk_comment_parent_id`·`idx_comment_parent_id` 를 만든다 |
| `V5` | `V5__create_post_like.sql` | `post_like` |
| `V6` | `V6__create_post_view.sql` | `post_view` — **FK 를 두지 않는다** |
| `V7` | `V7__create_attachment.sql` | `attachment` |

- **한 파일에 한 테이블이다.** 1차의 `V1`·`V2` 와 같다 — 한 파일이 실패하면 어느 테이블의 문제인지 바로 갈리고, 리뷰도 [../domain-model.md §4](../domain-model.md)의 표 하나와 대조한다. `post` 의 새 컬럼은 같은 테이블이라 한 파일이다
- **적용된 마이그레이션을 고치지 않는다**([phase1.md §2.4](phase1.md)) — `V1`·`V2` 를 고치지 않는다
- **H2 와 MySQL 양쪽에서 되는 구문이다**([../domain-model.md §7](../domain-model.md)) — 테스트가 같은 파일을 H2 에서 돌린다. 둘이 다르게 받을 수 있는 구문(예: 한 `ALTER TABLE` 에 컬럼 여럿)은 H2 에서 먼저 확인하고, 갈리면 같은 파일 안에서 문장을 나눈다 — 번호는 그대로다. 새 테이블의 선언은 `V1`·`V2` 의 모양(엔진·문자셋 선언)을 따른다
- 파일 머리 주석에 1차 파일처럼 정본 절과 「번호는 계획이 배정했다」 를 적는다
- **번호가 더 필요하면 스스로 붙이지 않는다** — BLOCKED 로 보고한다([phase1.md §2.6](phase1.md)의 3번)

## 3. 작업 항목

### B-14 2차 스키마와 엔티티 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | 없음 — 1차 board 산출물 위에서 시작한다 |
| 병렬 | §1.2 |
| 마이그레이션 | `V3`~`V7` (§2.2) |
| 참조 | [../domain-model.md §4](../domain-model.md)(§4.1~§4.6)·§6·§7, [../requirements/board.md §8](../requirements/board.md)·§12, [../conventions.md §1.3](../conventions.md)·§9.2, [../tech-stack.md §5.3](../tech-stack.md) |

**엔티티와 공유 문장을 여기서 끝낸다.** 1차 B-03 과 같은 이유다 — 기능 단계에 남기면 여러 항목이 같은 엔티티 파일과 `PostRepository` 를 고친다.

**산출물**
- `db/migration/V3__…`~`V7__…` (§2.2)
- `post/entity/Post` — `category`·`likeCount`·`attachmentCount`. 카테고리 enum(예: `post/entity/PostCategory`)
- `comment/entity/Comment` — `parent`
- `like/entity/PostLike`, `like/repository/PostLikeRepository` — 존재 확인(글·계정)을 포함한다
- `post/entity/PostView`, `post/repository/PostViewRepository` — 조회수 판정은 `post` 안이다([../conventions.md §1.3](../conventions.md))
- `attachment/entity/Attachment`, `attachment/repository/AttachmentRepository`
- `post/repository/PostRepository` — `like_count`·`attachment_count` 의 좁은 UPDATE. 문장과 조건은 [../domain-model.md §6.1](../domain-model.md)·§6.2 의 1) 그대로이고 영향 행 수를 돌려준다

**도메인 메서드** — 엔티티를 고치는 것은 이 항목이 끝낸다.

| 메서드 | 동작 |
| --- | --- |
| `Post` 생성의 카테고리 | 생략이면 `FREE` ([../requirements/board.md §8](../requirements/board.md)) |
| `Post` 의 카테고리 바꾸기 | 생략이면 지금 값을 유지한다. **`Post.update(title, content)` 는 바꾸지 않는다** — B-03 의 도메인 메서드 표가 그 모양을 요구한다. `P003` 판정은 B-19 의 서비스가 한다 |
| `Comment` 생성의 `parent` | 없으면 최상위 |
| `PostLike` 생성 | 글·계정 |
| `PostView` 생성 | 글 id·판정 키·`viewedAt`. `viewedAt` 은 판정하는 코드가 넣는다 — 감사 시각이 아니다([../domain-model.md §4.5](../domain-model.md)) |
| `Attachment` 생성 | 글·저장 이름·원본 파일명·판정한 형식·크기 |

**새 집계(`likeCount`·`attachmentCount`)를 바꾸는 엔티티 메서드를 두지 않는다**([../domain-model.md §6](../domain-model.md)). 1차 집계의 엔티티 메서드는 B-03 이 요구하므로 그대로 둔다(B-10·B-11 의 주석).

**`@Modifying` 의 `flushAutomatically`·`clearAutomatically` 는 부르는 쪽이 `post` 를 다시 읽는지에 달렸다.** 1차에서 `clearAutomatically` 를 B-10 은 껐고 B-11 은 켰다 — 다시 읽어 응답을 만드는 경로에서 끈 쪽이 낡은 사본을 돌려준 것이 그 이유다([phase1.md](phase1.md) B-11 의 블록인용). 이 항목은 고른 설정과 이유를 문장의 주석에 적는다. 응답 값으로 관측하는 것은 응답에 그 집계를 싣는 B-20(`likeCount`)이다 — B-23·B-24 의 응답에는 `attachment_count` 가 없다.

**완료 기준**
- [ ] Flyway 가 `V3`~`V7` 을 적용하고 테이블·컬럼·제약·인덱스의 이름과 모양이 [../domain-model.md §4](../domain-model.md)의 표와 같다
- [ ] **H2 와 실 MySQL 양쪽에 적용된다**([../domain-model.md §7](../domain-model.md)). H2 는 테스트가, MySQL 은 로컬 프로파일 기동이 확인한다 — MySQL 쪽은 **검증표에 넣지 않는다**(테스트가 MySQL 을 쓰지 않는다). 확인한 방법을 보고에 적는다
- [ ] `V1`·`V2` 를 고치지 않았다
- [ ] 기존 행의 `category` 는 `FREE`, `like_count`·`attachment_count` 는 0, `parent_id` 는 NULL 이다 — 컬럼 기본값이 채운다
- [ ] **`post_like.account_id`·`post_view.post_id` 에 FK 가 없다.** `comment.parent_id`·`post_like.post_id`·`attachment.post_id` 의 FK 는 [../domain-model.md §4.3](../domain-model.md)의 이름으로 있다
- [ ] **새 문자열 컬럼의 실제 폭이 엔티티 선언과 같다** — `information_schema` 로 읽어 비교한다([../conventions.md §9.2](../conventions.md)). `attachment.original_filename` 은 규칙과 폭이 같아 여유가 없다([../domain-model.md §4.6](../domain-model.md))
- [ ] `PostLike.createdAt` 이 감사 시각과 같은 초 자르기를 받는다 — `BaseTimeEntity` 를 상속하지 않는다([../domain-model.md §4.4](../domain-model.md)). `Attachment` 는 상속한다
- [ ] 위 표의 도메인 메서드가 있고, 새 집계를 바꾸는 엔티티 메서드가 없다
- [ ] `PostRepository` 의 새 문장이 그 집계 컬럼만 싣는다 — 엔티티 더티 체킹의 전체 컬럼 UPDATE 가 아니다
- [ ] `ddl-auto: validate` 로 기동한다. Entity 에 `@Setter`·`@Data` 가 없다
- [ ] 1차 테스트가 깨지지 않는다

**검증** — `PostRepositoryTest`·`CommentRepositoryTest` 확장, 새 테이블의 `@DataJpaTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 새 컬럼을 생략한 `post` INSERT | `category = FREE`, `like_count = 0`, `attachment_count = 0` |
| `V2` 까지의 스키마에 넣은 행이 나머지를 적용한 뒤 (예: Flyway 의 `target` 으로 나눠 적용) | `FREE`·0·0, 그 글의 댓글 `parent_id` NULL |
| 없는 `account_id` 로 `post_like` 저장 | **성공** (FK 없음) |
| 없는 `post_id` 로 `post_view` 저장 | **성공** (FK 없음) |
| 없는 `parent_id` 로 댓글 저장 | FK 위반 |
| 같은 (글, 계정) `post_like` 두 번 / 같은 (글, 판정 키) `post_view` 두 번 / 같은 `storage_key` 두 번 | UNIQUE 위반 |
| `PostLike` 의 `createdAt` | 소수부가 없다 |
| `information_schema` 의 실제 폭 | `category` 20, `viewer_key` 80, `storage_key` 36, `original_filename` 255, `content_type` 30 — 엔티티 선언과 일치 |
| 지워진 글에 `like_count` +1 | 0행 |
| 지워진 글에 `like_count` −1 | 0행 |
| `like_count = 0` 에서 −1 | 0행, 음수 아님 |
| `attachment_count` 가 상한인 글에 +1 / 지워진 글에 +1 | 0행 |
| `attachment_count = 0` 에서 −1 | 0행, 음수 아님 |
| 새 문장이 발행한 `update post` | 그 집계 컬럼만 싣는다. `title`·`content` 가 없다 (B-10 의 관측 방식) |
| 인덱스·제약 이름 | [../domain-model.md §4.3](../domain-model.md)의 이름과 같다 |

---

### B-15 에러 코드와 multipart 예외 매핑 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | 없음 |
| 병렬 | §1.2 |
| 공유 파일 | `application.yml` — B-16 이 이어서 고친다 |
| 마이그레이션 | 없음 |
| 참조 | [../api-contract.md §8.1](../api-contract.md)·§8.3·§4.7, [../conventions.md §6.1](../conventions.md), [../tech-stack.md §4.5](../tech-stack.md) |

**산출물**
- `global/error/ErrorCode` — [../api-contract.md §8.1](../api-contract.md)·§8.3 에서 `D-18` 이 더한 코드. 코드·HTTP 상태·메시지는 그 절 그대로다
- `global/error/GlobalExceptionHandler` — [../conventions.md §6.1](../conventions.md) 표의 multipart 줄
- `application.yml` — `spring.servlet.multipart.max-file-size`·`max-request-size`, `server.tomcat.max-swallow-size`. 값은 [../tech-stack.md §4.5](../tech-stack.md)의 YAML 블록이 적은 것이다(그 표가 이 키들을 정본 값으로 분류한다. 값이 그 블록에만 있는 갈림은 이 문서 §4.3)

**핸들러를 넣기 전에 한 번 잰다.** [../conventions.md §6.1](../conventions.md)이 「지금은 셋 다 마지막 그물로 떨어질 것으로 본다」 를 측정 대상으로 두었고, 이 항목이 병합되면 board 에서 그 상태가 사라진다. 실제 서블릿 컨테이너(기동한 board 나 내장 Tomcat 을 띄운 테스트)에 인증을 지나는 요청으로(예: 유효한 토큰) 한도를 넘는 multipart 를 보내 상태·코드·로그 수준을 보고에 적는다. 추정과 다르면 다른 그대로 적는다. **검증표에 넣지 않는다** — 핸들러를 넣은 뒤에는 재현되지 않는다. `MockMvc` 는 컨테이너의 한도를 거치지 않으므로 이 측정의 수단이 아니다([../tech-stack.md §4.5](../tech-stack.md)).

**같은 매핑을 auth·member 도 갖는다**([../conventions.md §6.1](../conventions.md) — 세 서비스가 같은 표를 구현한다). 그쪽은 「auth·member 계획의 multipart 예외 매핑 항목」 이고, 세 서비스의 본문·로그 수준 비교는 통합의 몫이다(§4.1).

**완료 기준**
- [ ] 새 코드의 코드·HTTP 상태·메시지가 [../api-contract.md §8.1](../api-contract.md)·§8.3 과 같다
- [ ] `MaxUploadSizeExceededException` 은 413 `C008`, `MultipartException`·`MissingServletRequestPartException` 은 400 `C001` 이다. 셋 다 `fieldErrors` 가 빈 배열이고 로그는 `warn` 이다
- [ ] **크기 위반이 `C001` 이 되지 않는다** — 하위 타입의 핸들러가 고른다([../conventions.md §6.1](../conventions.md))
- [ ] 마지막 그물은 그대로 500 `C005`·`error` 다 — 클라이언트 오류 쪽과 **양쪽을 다 단언한다**([../conventions.md §6.1](../conventions.md))
- [ ] multipart·Tomcat 설정이 [../tech-stack.md §4.5](../tech-stack.md)의 값이다
- [ ] 핸들러를 넣기 전의 응답을 재서 보고에 적었다(위 문단)
- [ ] 1차 테스트가 깨지지 않는다

**검증** — `ErrorCodeTest`, `GlobalExceptionHandlerTest` 확장

| 케이스 | 기대 결과 |
| --- | --- |
| 새 코드마다 | 상태·메시지가 [../api-contract.md §8](../api-contract.md)과 문자열 일치 |
| 핸들러가 `MaxUploadSizeExceededException` 을 던진다 | 413 `C008`, `fieldErrors: []`, `warn` |
| 핸들러가 `MultipartException` 을 던진다 | 400 `C001`, `fieldErrors: []`, `warn` |
| 필요한 파트가 없다 (`MissingServletRequestPartException`) | 400 `C001`, `fieldErrors: []`, `warn` |
| 처리하지 않은 예외 | 500 `C005`, `error` (회귀) |

> **예외를 직접 던져 매핑을 본다.** 한도의 집행은 컨테이너의 일이라 `MockMvc` 로 413 이 나오는지는 재지 못한다([../tech-stack.md §4.5](../tech-stack.md)의 블록인용). 컨테이너를 거친 응답은 통합이 잰다(§4.1).

---

### B-16 인가 규칙·선택적 리졸버·환경값 가드 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-15 (`application.yml`) |
| 병렬 | §1.2 |
| 마이그레이션 | 없음 |
| 참조 | [../security.md §5.2](../security.md)·§9, [../api-contract.md §4](../api-contract.md)·§4.8·§8.5, [../tech-stack.md §2.1](../tech-stack.md)·§4.3·§4.5, [../requirements/board.md §9.1](../requirements/board.md), [../conventions.md §1.3](../conventions.md) |

**산출물**
- `global/config/SecurityConfig` — 새 경로의 인가 규칙(아래 표)
- `global/security/` — 선택적 리졸버([../conventions.md §1.3](../conventions.md)의 「선택적 인증의 리졸버」)
- 설정 바인딩과 기동 가드 — `attachment.storage-root`, `view-count.hmac-secret`, `view-count.cleanup-interval`. 자리는 그 값을 쓰는 패키지다(예: `attachment/storage`, `post/support`)
- `global/config` — 스케줄링 활성화([../tech-stack.md §4.5](../tech-stack.md)의 「정리 작업은 board 의 첫 스케줄러다」)
- `application.yml` — 위 키들과 `server.forward-headers-strategy: none`. `application-test.yml` — 임시 디렉터리와 테스트용 키
- `README.md`·`application-local.yml.example` — 두 환경변수

**인가 규칙** — [../api-contract.md §4](../api-contract.md) 표의 좋아요·첨부 줄과 [../security.md §5.2](../security.md)의 매트릭스다. 작성자·소유자 판정은 서비스의 일이다.

| 경로 | 규칙 |
| --- | --- |
| `PUT`·`DELETE /api/v1/posts/{id}/like` | 인증 |
| `POST /api/v1/posts/{postId}/attachments` | 인증 |
| `DELETE /api/v1/attachments/{id}` | 인증 |
| `GET /api/v1/attachments/{id}` | 공개 |
| `GET /api/v1/posts/{id}` | 공개 그대로 — 실린 토큰은 검증한다([../api-contract.md §4.8](../api-contract.md)) |

**선언 순서를 본다.** `authorizeHttpRequests` 는 선언 순서대로 평가하고, 공개 규칙이 인증 경로를 먼저 잡아도 응답이 같은 401 일 수 있다 — 바뀌는 것은 거부한 계층이다. **선택된 핸들러와 해석된 예외가 비어 있는지로 본다**([../api-contract.md §4](../api-contract.md)의 `/posts/me` 블록인용).

**선택적 리졸버는 `@CurrentMember` 리졸버와 같은 claim 검사를 한다**([../tech-stack.md §2.1](../tech-stack.md)) — `sub` 누락·숫자 아님, `role` 누락·열거 밖은 401 `A002` 다. 토큰이 없을 때만 `null` 이다. 검사에 실패한 토큰을 `null` 로 낮추면 계약 밖 토큰이 익명으로 통과한다.

**기동 가드는 [../tech-stack.md §4.5](../tech-stack.md)대로다.** 저장 루트는 이미 있고 쓸 수 있는 디렉터리여야 하고 서버가 만들지 않는다. 비밀키는 설정 문자열의 UTF-8 바이트가 32 이상이어야 하고 Base64 로 디코드하지 않는다. [../tech-stack.md §4.3](../tech-stack.md)의 측정대로 주입 방식에 따라 미해석 `${…}` 리터럴이나 빈 문자열이 통과할 수 있으므로 가드가 그것을 막는다.

> **이 항목 뒤로 board 는 두 환경값 없이 뜨지 않는다.** `local` 로 띄우는 실행이 그 값을 가져야 한다 — 화면의 실제 서비스 e2e 는 서비스를 띄우지 않고 먼저 뜬 board 를 쓴다(§4.2). `application-local.yml` 이 리터럴로 덮으면 환경변수가 쓰이지 않는 것은 [../tech-stack.md §4.5](../tech-stack.md)가 적는다.

**완료 기준**
- [ ] 새 인증 경로에 토큰 없이 오면 필터 체인이 401 `A001` 을 낸다 — 디스패치되지 않는다(선택된 핸들러와 해석된 예외가 비어 있다)
- [ ] `GET /api/v1/attachments/{id}` 가 토큰 없이 필터 체인을 지난다(핸들러는 B-24)
- [ ] 선택적 리졸버가 `@CurrentMember` 리졸버와 같은 claim 검사를 하고, 토큰이 없을 때만 `null` 이다
- [ ] **`GET /api/v1/posts/{id}` 에 잘못된 토큰이 오면 401 이다** — 익명으로 낮추지 않는다. [../requirements/board.md §9.1](../requirements/board.md)이 「`permitAll` 경로에 잘못된 토큰을 보내는 테스트」 로 적은 줄이고, 2026-11-12 `D-20` 이 이 항목의 테스트 대상으로 세웠다. `A002`·`A003` 의 경계는 [../api-contract.md §8.5](../api-contract.md)
- [ ] 두 가드가 기동을 실패시킨다 — 저장 루트가 비었거나 없거나 디렉터리가 아니거나 쓸 수 없을 때, 비밀키가 비었거나 짧을 때
- [ ] 두 값에 기본값이 없다 — 커밋되는 `application.yml` 에는 placeholder 만 있다
- [ ] `server.forward-headers-strategy` 가 `none` 이다
- [ ] 스케줄링이 켜져 있다(작업은 B-21)
- [ ] `README.md`·`application-local.yml.example` 에 두 환경변수가 있다
- [ ] 1차 테스트가 깨지지 않는다

**검증** — `JwtAuthenticationTest`·보안 설정 테스트 확장, 선택적 리졸버는 테스트 전용 컨트롤러로 본다(1차의 `CurrentMemberProbeController` 와 같은 방식). **토큰 없음 행은 테스트 전용 체인으로 그 경로만 열거나 리졸버를 직접 부른다** — 2026-11-13 코드 읽기로 그 테스트 경로는 운영 `SecurityConfig` 의 `anyRequest().authenticated()` 에 걸려 토큰 없는 요청이 리졸버에 닿기 전에 401 이 된다. 운영 `SecurityConfig` 에 테스트 경로를 열지 않는다

| 케이스 | 기대 결과 |
| --- | --- |
| 토큰 없이 `PUT`·`DELETE /posts/1/like`, `POST /posts/1/attachments`, `DELETE /attachments/1` | 401 `A001`, 핸들러·해석된 예외가 비어 있다 |
| 토큰 없이 `GET /attachments/1` | 필터를 지난다 (401 이 아니다) |
| 선택적 리졸버 — 토큰 없음 | `null` |
| 선택적 리졸버 — 유효한 토큰 | 그 계정과 역할 |
| 선택적 리졸버 — `sub` 누락 / 숫자 아님 / `role` 누락 / `role` 이 열거 밖 | 401 `A002` |
| `GET /posts/{id}` + 서명이 틀린 토큰 / 만료된 토큰 | 401 (코드는 [../api-contract.md §8.5](../api-contract.md)의 경계대로) |
| 저장 루트 없음 / 빈 값 / 없는 경로 / 파일인 경로 | 기동 실패 |
| 비밀키 없음 / 빈 값 / 31바이트 | 기동 실패. 32바이트면 기동 |
| 비밀키가 다중 바이트 문자 | UTF-8 바이트로 센다(예: 한글 11자는 33바이트라 기동한다) |

> **「쓸 수 없는 디렉터리」 는 테스트로 만들 수 있으면 넣는다.** 만드는 법이 플랫폼마다 다르므로, 만들지 못했으면 그 사실과 이유를 보고에 적는다.

---

### B-17 댓글 삭제를 `post` 먼저·조건부 전환으로 고친다 [결함 수정]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | 없음 — 1차 `CommentService.delete`(B-08·B-10 산출물)를 고친다 |
| 병렬 | §1.2 |
| 공유 파일 | `Comment` — B-14 도 고친다. `PostRepository` — B-14·B-21 도 고친다. `CommentService`, `CommentRepository`, `CommentServiceTest` — B-22 가 이어서 고친다 |
| 마이그레이션 | 없음 |
| 참조 | [../domain-model.md §6](../domain-model.md)·§6.2·§5, [../requirements/board.md §12](../requirements/board.md), [../api-contract.md §4.4](../api-contract.md), [../process/review-policy.md §4.1](../process/review-policy.md) |

**무엇이 틀렸나.** [../domain-model.md §6](../domain-model.md)의 표가 「집계의 증감은 근거 행의 전환이 이 트랜잭션에서 실제로 일어났을 때만 남긴다」 를 요구한다. 1차의 댓글 삭제는 그것을 지키지 않는다고 2026-11-11 `D-18` 이 코드 읽기로 적었다 — **측정하지 않았다**(같은 절의 블록인용). 2026-11-12 코드 읽기로 본 모양은 이렇다: `delete` 가 활성 댓글을 락 없이 읽고(`findByIdAndDeletedFalse`), `Comment.softDelete()` 로 엔티티를 바꾼 뒤 `PostRepository.decreaseCommentCount` 를 부른다. 그 문장의 `flushAutomatically` 가 댓글 UPDATE 를 먼저 내보내므로 순서는 **댓글 행 → `post`** 이고, 댓글 UPDATE 에는 `deleted = false` 조건이 없다. 같은 댓글의 동시 삭제가 둘 다 활성으로 읽으면 둘 다 줄일 것으로 본다.

**고치는 모양** — [../domain-model.md §6.2](../domain-model.md)의 첨부 삭제와 같다.

```
DELETE /comments/{id}  한 트랜잭션 (404 CM001 -> 403 CM002 판정 뒤 — 1차 그대로)
  1) PostRepository.decreaseCommentCount   (where comment_count > 0 — 1차 문장 그대로)
  2) UPDATE comment SET deleted = true WHERE id = ? AND deleted = false
       0행이면 이미 지워진 것 -> 트랜잭션을 되돌린다(1)의 감소도 되돌아간다) 404 CM001
```

**순서가 `post` 먼저인 이유**는 그 블록인용이 적는다 — 지금 순서는 답글 작성(`post` → 부모 행의 FK 공유 락)과 반대라 교착할 것으로 본다. 1차 작성 경로는 `increaseCommentCount` 를 INSERT 보다 먼저 부른다(2026-11-12 코드 읽기). 1)이 0행인 경우(활성 댓글이 있는데 집계가 이미 0)는 1차처럼 2)를 그대로 하고 집계를 0 에 둔다 — **그 상태를 WARN 으로 드러낼지는 정본이 댓글 경로에 정하지 않았다**([../domain-model.md §6.2](../domain-model.md)의 WARN 문장은 좋아요·첨부의 두 경로를 말한다). 이 항목은 바꾸지 않는다. 바꾸려면 정본 개정이 먼저다.

**`Comment.softDelete()` 를 지우지 않는다.** B-03 이 도메인 메서드 표와 완료 기준으로 그 존재를 요구한다. 삭제 경로가 그 메서드를 더 쓰지 않게 되면 B-10 처럼 주석으로 막는다 — 「댓글 삭제 경로는 이 메서드를 쓰지 않는다 / 전환은 `CommentRepository` 의 조건부 UPDATE 가 한다 / 이 메서드로 되돌리면 결함이 돌아온다」.

**산출물**
- `comment/repository/CommentRepository` — 조건부 전환(영향 행 수를 돌려준다)
- `comment/service/CommentService` — `delete` 의 순서와 0행 처리, javadoc
- `comment/entity/Comment` — `softDelete()` 의 주석(위 문단)
- `post/repository/PostRepository` — `increaseCommentCount` javadoc 의 `flushAutomatically` 근거를 새 순서로 고친다

**완료 기준**
- [ ] **고치기 전에 아래 검증표 첫 줄이 1차 코드에서 빨개지는 것을 보았다** — 코드 읽기의 추정이 측정이 된다. 결과를 보고에 적는다
- [ ] 같은 댓글의 동시 삭제가 `comment_count` 를 한 번만 줄인다 — 활성 댓글 수와 같다
- [ ] 순서가 `post` 감소 → 댓글의 조건부 전환이다
- [ ] 전환이 0행이면 트랜잭션이 되돌아가고 404 `CM001` 이다 — 그 요청의 감소가 남지 않는다
- [ ] 댓글 행의 전환이 조건부 문장 하나다 — 엔티티 더티 체킹의 UPDATE 가 아니다
- [ ] 404 `CM001` → 403 `CM002` 의 선후, `MemberClient` 호출 0회, 한 로컬 트랜잭션이 1차 그대로다(B-08·B-10)
- [ ] `comment_count` 가 음수가 되지 않는다
- [ ] `delete` 의 javadoc 이 동시 삭제에 대해 거짓을 말하지 않는다 — 지금의 「그래서 같은 댓글을 두 번 지워도 집계가 두 번 깎이지 않는다」 는 순차에서만 참일 것으로 본다 — 첫 완료 기준이 잰다
- [ ] 기존 테스트가 깨지지 않는다

**검증** — `CommentServiceTest` 확장

| 케이스 | 기대 결과 |
| --- | --- |
| **같은 댓글의 동시 삭제 N건 — 두 읽기가 어느 쓰기보다 먼저 일어나게 강제한다** | 성공 1건, 나머지 404 `CM001`, `comment_count` 가 1 만 준다. **1차 코드(조건 없는 전환)로 되돌리면 깨진다** |
| 발행된 문장의 순서 | `update post` 가 `update comment` 보다 먼저다 |
| 전환이 0행인 경로 | 그 요청의 감소가 되돌아간다 — 커밋된 `comment_count` 불변 |
| 집계가 이미 0 인 활성 댓글 삭제 | 204, `comment_count` 0, 음수 아님 |
| 같은 댓글 순차 2회 삭제 | 두 번째는 404 `CM001`, 감소는 한 번 (1차 그대로) |

> **이 이중 감소는 애플리케이션에서 일어나므로 H2 에서도 재현될 것으로 본다** — 1차 B-10 의 소실 갱신이 그랬다([phase1.md](phase1.md) B-10 의 블록인용). 끼워넣기는 강제한다(예: B-10·B-11 의 `StatementInspector` + `CyclicBarrier`). 실 MySQL 에서의 측정은 통합의 몫이다(§4.1).

---

### B-18 글 수정·삭제가 집계 컬럼을 싣지 않게 한다 [결함 수정]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-14 — 새 집계 컬럼이 엔티티에 있어야 1차 집계와 함께 막는다 |
| 병렬 | §1.2 |
| 공유 파일 | `Post`(B-14 산출물), `PostServiceTest` — B-19·B-21·B-24 가 이어서 고친다 |
| 마이그레이션 | 없음 |
| 참조 | [../domain-model.md §6](../domain-model.md), [../requirements/board.md §5](../requirements/board.md), [phase1.md §2.6](phase1.md) |

**무엇이 틀렸나.** [../domain-model.md §6](../domain-model.md)의 표가 「엔티티 갱신이 집계 컬럼을 싣지 않는다」 를 요구한다. 같은 절의 첫 블록인용이 2026-11-11 코드 읽기로 적었다 — 글 수정(P-06)·삭제(P-07)가 `post` 를 엔티티로 저장하고 갱신 컬럼을 좁히는 설정이 없어, 그 UPDATE 가 트랜잭션이 읽은 낡은 집계를 다시 써서 그 사이에 커밋된 증감을 지울 것으로 본다(그 경로의 문장은 측정하지 않았다). 2차에서는 **`attachment_count` 의 상한 판정까지 무너뜨릴 수 있다.** 2026-11-12 코드 읽기에서도 `Post` 의 1차 집계 필드는 `@Column(nullable = false)` 만 갖고 `@DynamicUpdate` 가 없었다.

**수단은 구현이 고른다**([../domain-model.md §6](../domain-model.md) — 예: 매핑에서 집계 컬럼을 갱신 대상에서 빼거나, 바뀐 컬럼만 싣는 설정). **단 B-03 의 완료 기준을 깨는 수단이면 멈춘다**([phase1.md §2.6](phase1.md)의 2번). 예: 집계 필드를 갱신 대상에서 빼면 B-03 이 요구한 엔티티 메서드(`increaseViewCount()` 등)의 변경이 저장되지 않는다. 2026-11-12 코드 읽기로 `PostRepositoryTest` 의 `조회수_증가`·`댓글수_증감` 은 그 메서드를 부르고 flush·clear 뒤에 다시 읽는다 — 그 수단은 B-03 검증표의 두 줄(`increaseViewCount()` 2회, `increaseCommentCount()` 3회 후 `decrease` 1회)을 깰 것으로 본다(코드 읽기). `PostServiceTest` 의 `삭제_시_하위_댓글도_deleted_가_된다` 도 엔티티 메서드와 `saveAndFlush` 로 `comment_count` 를 준비한다. 바뀐 컬럼만 싣는 설정은 그 메서드의 변경을 그대로 싣는다.

**산출물**
- `post/entity/Post` — 고른 수단(매핑)과 그 이유의 주석
- `PostServiceTest` — 끼워넣기 테스트

**완료 기준**
- [ ] **고치기 전에 아래 검증표 첫 줄이 빨개지는 것을 보았다** — 블록인용의 추정(코드 읽기)이 측정이 된다. 결과를 보고에 적는다
- [ ] 글 수정·삭제가 발행하는 `update post` 에 집계 컬럼(`view_count`·`comment_count`·`like_count`·`attachment_count`)이 없다
- [ ] 수정·삭제와 집계 증감을 끼워넣어도 증감이 남는다 — 집계마다
- [ ] 수단이 B-03 의 완료 기준을 깨지 않는다
- [ ] 수정·삭제의 응답과 동작이 1차 그대로다(B-07)
- [ ] 기존 테스트가 깨지지 않는다

**검증** — `PostServiceTest` 확장

| 케이스 | 기대 결과 |
| --- | --- |
| **글 수정이 `post` 를 읽은 뒤, 수정이 flush 되기 전에 댓글 작성(좁은 UPDATE)이 커밋된다** | `comment_count` 가 그 증가를 유지한다. **수단을 빼면 깨진다** |
| 같은 끼워넣기를 `view_count`·`like_count`·`attachment_count` 의 좁은 UPDATE 로 | 같음 — 문장은 `PostRepository` 의 것을 직접 부른다(`view_count` 는 B-11, 나머지는 B-14) |
| 글 삭제와 집계 증가의 끼워넣기 | 같음 |
| 수정·삭제가 발행한 `update post` | 집계 컬럼이 없다 (B-10 의 `StatementInspector` 관측) |

---

### B-19 카테고리 — P-11 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-14, B-15, B-18 |
| 병렬 | §1.2 |
| 공유 파일 | `PostService`, `PostController`, `post/dto/*`, `PostServiceTest` — B-21·B-24 가 이어서 고친다 |
| 마이그레이션 | 없음 (`V3` 는 B-14) |
| 참조 | [../requirements/board.md §8](../requirements/board.md)·§4·§5, [../api-contract.md §4.1](../api-contract.md)·§4.3·§4.4·§9.3, [../security.md §5.2](../security.md), [../conventions.md §6.1](../conventions.md) |

**산출물**
- `post/dto/PostCreateRequest`·`PostUpdateRequest` — 선택 필드 `category`
- `post/dto/PostSearchCondition`, `post/repository/PostQueryRepository` — 목록의 `category` 필터
- `post/service/PostService`, `post/controller/PostController` — 작성·수정의 `P003`, 목록 파라미터
- `post/dto/PostResponse`·`PostDetailResponse` — `category`·`likeCount`

**목록 항목에 `category` 와 `likeCount` 를 함께 더한다.** 목록 항목의 키 집합은 [../api-contract.md §4.3](../api-contract.md)의 한 줄이고 1차 테스트가 그것을 리터럴 집합으로 단언한다(2026-11-12 코드 읽기. 예: `PostControllerTest` 의 `LIST_ITEM_KEYS`, `PostServiceTest` 의 `목록_항목_키_집합`) — 한 키만 더하면 그 단언을 지금의 계약과 맞출 수 없다. `likeCount` 는 컬럼을 그대로 싣는 것이라 좋아요 기능(B-20)을 기다리지 않는다.

**완료 기준**
- [ ] 작성에서 `category` 를 생략하면 `FREE`, 수정에서 생략하면 지금 값을 유지한다
- [ ] `NOTICE` 작성은 ADMIN 만이다 — 아니면 403 `P003`. **`P003` 을 member 호출보다 먼저 판정한다** — 프로필이 없는 USER 가 공지로 쓰면 `S002` 가 아니라 `P003` 이고 `MemberClient` 호출이 0회다([../requirements/board.md §8](../requirements/board.md)의 판정 순서)
- [ ] 수정은 404 `P001` → 403 `P002` → `P003` 순서다. 카테고리가 `NOTICE` 로 바뀌거나 `NOTICE` 에서 바뀔 때만 ADMIN 을 요구하고, 바뀌지 않는 수정(생략·같은 값)은 그 판정을 거치지 않는다
- [ ] ADMIN 도 남의 글의 카테고리를 바꾸지 못한다 — 403 `P002`
- [ ] 본문의 잘못된 `category` 는 400 `C001`, 쿼리의 잘못된 `category` 는 400 `C002` 다([../requirements/board.md §4](../requirements/board.md))
- [ ] 목록의 `category` 가 검색·정렬과 AND 로 걸리고, 생략하면 공지를 포함한 모든 카테고리다. `GET /posts/me` 에는 이 필터를 두지 않는다
- [ ] **목록 항목(`GET /posts`·`GET /posts/me`)의 키 집합이 [../api-contract.md §4.3](../api-contract.md)의 목록 줄과 정확히 같다**
- [ ] 상세 모양(작성·수정·상세 응답)에 `category`·`likeCount` 가 더해진다 — 나머지 키는 B-21·B-24 가 더한다
- [ ] 목록·상세 키를 리터럴 집합으로 단언하는 1차 테스트(예: `PostControllerTest` 의 두 상수, `PostServiceTest` 의 모양 테스트)를 고친다 — 목록 키는 [../api-contract.md §4.3](../api-contract.md)의 목록 줄로 고치고, 상세 키에는 이 항목이 더한 `category`·`likeCount` 만 더한다. 정본의 상세 줄과 같아지는 것은 B-24 다(이 문서 머리의 둘째 문단)
- [ ] 기존 테스트가 깨지지 않는다 — 위에서 고친 단언 밖에서

**검증** — `PostServiceTest`, `PostControllerTest`, `PostQueryRepositoryTest` 확장

| 케이스 | 기대 결과 |
| --- | --- |
| `category` 없이 작성 | 201, `category: FREE` |
| USER 가 `QNA` 로 작성 | 201, `category: QNA` |
| USER 가 `NOTICE` 로 작성 | 403 `P003`, 글 0개 |
| **프로필 없는 USER 가 `NOTICE` 로 작성** | **403 `P003`** (`S002` 아님), `MemberClient` 호출 0회 |
| ADMIN 이 `NOTICE` 로 작성 | 201 |
| USER 가 자기 `FREE` 글을 `NOTICE` 로 | 403 `P003`, 카테고리 불변 |
| USER 의 `NOTICE` 글(테스트 데이터)을 그 USER 가 `FREE` 로 | 403 `P003` |
| USER 의 `NOTICE` 글을 그 USER 가 `category` 생략·같은 값으로 수정 | 200, `category` 가 `NOTICE` 그대로 — 판정을 거치지 않는다 |
| USER 가 자기 `QNA` 글을 `category` 생략으로 수정 | 200, `category: QNA` |
| USER 가 남의 글을 `NOTICE` 로 | 403 `P002` (`P003` 아님) |
| USER 가 지운 자기 글을 `NOTICE` 로 | 404 `P001` (`P003` 아님) |
| ADMIN 이 남의 글을 `NOTICE` 로 | 403 `P002` |
| ADMIN 이 자기 글을 `NOTICE` 로, 다시 `FREE` 로 | 200 `category: NOTICE`, 200 `category: FREE` |
| 본문 `category: "BOGUS"` | 400 `C001` |
| 쿼리 `category=BOGUS` | 400 `C002` |
| `category=NOTICE` + 검색 + 정렬 | 세 조건이 AND 로 걸린다 |
| `category` 없는 목록 | 공지가 들어 있다 |
| 목록 항목의 키 집합 | [../api-contract.md §4.3](../api-contract.md)의 목록 줄과 정확히 같다 — 리터럴 집합으로 대조한다 |

---

### B-20 좋아요 — P-09 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-14, B-16 |
| 병렬 | §1.2 |
| 마이그레이션 | 없음 (`V5` 는 B-14) |
| 참조 | [../requirements/board.md §10](../requirements/board.md), [../domain-model.md §6.1](../domain-model.md)·§4.4, [../api-contract.md §4.6](../api-contract.md)·§4.2·§9.8, [../security.md §5.2](../security.md), [../tech-stack.md §2.1](../tech-stack.md) |

**산출물**
- `like/controller/*`, `like/service/*`, `like/dto/*`
- `like/repository/PostLikeRepository` — 취소의 삭제 문장(영향 행 수를 돌려준다)

**순서는 [../domain-model.md §6.1](../domain-model.md)이다** — `post` 의 좁은 UPDATE 로 배타 락을 먼저 잡고 `post_like` 쓰기를 나중에 한다. 근거 행이 새로 생기거나 지워지지 않으면 트랜잭션을 되돌린다. 1)을 잠금 읽기로 잡고 증가를 근거 행이 생긴 뒤에 하는 모양도 요건을 지킨다(같은 절).

**완료 기준**
- [ ] `PUT` 이 누르고 `DELETE` 가 취소한다. 둘 다 멱등이고 200 `{liked, likeCount}` 다 — `PUT` 은 언제나 `liked: true`, `DELETE` 는 언제나 `false`
- [ ] 위 순서다 — `post` 의 배타 락이 먼저이고, 증감은 근거 행이 이 트랜잭션에서 새로 생기거나 지워졌을 때만 남는다
- [ ] **INSERT 의 UNIQUE 충돌이 500 이 아니다** — `liked: true` 로 답하고 그 요청의 증가가 남지 않는다. 제약 위반이 트랜잭션을 rollback-only 로 만드는 문제를 수단이 다룬다
- [ ] 응답의 `likeCount` 는 쓴 뒤(되돌렸으면 되돌린 뒤) 읽은 값이다
- [ ] 없는·삭제된 글은 누르기·취소 모두 404 `P001` 이다
- [ ] 어긋난 상태(행은 있는데 집계가 0)의 취소는 집계를 0 에 두고 WARN 을 남긴다
- [ ] **프로필이 필요 없다** — `MemberClient` 호출 0회, `S002` 가 나지 않는다
- [ ] 두 핸들러가 `@CurrentMember` 를 받고 `JwtAuthenticationTest` 의 인증 경로 목록에 들어 있다([../tech-stack.md §2.1](../tech-stack.md))
- [ ] 글을 지워도 `post_like` 행이 남는다. 자기 글에도 된다
- [ ] 기존 테스트가 깨지지 않는다

**검증** — 서비스·컨트롤러 테스트

| 케이스 | 기대 결과 |
| --- | --- |
| 누르기 | 200 `liked: true`, `likeCount` 1, 행 1 |
| 다시 누르기 | 200 `liked: true`, `likeCount` 1 — 증가가 남지 않는다 |
| 누르지 않은 글 취소 | 200 `liked: false`, 집계 불변 |
| 누르고 취소 | 200 `liked: false`, `likeCount` 0, 행 0 |
| **UNIQUE 충돌 경로** — 확인을 지난 뒤 INSERT 가 충돌하게 만든다(수단은 구현이 고른다. 예: 확인을 대역으로 바꿔 행이 없다고 답하게 한다) | 200 `liked: true`, 커밋된 `like_count` 불변, 500 아님 |
| 같은 계정의 동시 누르기 N건 | `likeCount` 1, 행 1, 응답 전부 200 `liked: true` |
| 누른 뒤 같은 계정의 동시 취소 N건 | `likeCount` 는 한 번만 준다, 행 0, 응답 전부 200 `liked: false` |
| 서로 다른 계정의 동시 누르기 N건 | `likeCount` = 행 수 = N |
| 발행 순서 | `post` 행의 배타 락을 잡는 문장(좁은 UPDATE, 또는 같은 절이 허용한 잠금 읽기)이 `post_like` 쓰기보다 먼저다 |
| 없는·삭제된 글에 누르기·취소 | 404 `P001` |
| 자기 글에 누르고 그 글을 지운다 | 누르기 200 `liked: true`, 지운 뒤에도 `post_like` 행이 남는다 |
| 프로필 없는 계정 | 200, `MemberClient` 호출 0회 |
| 행은 있는데 집계가 0 인 글을 취소 | 200 `liked: false`, 집계 0, WARN |
| 응답의 `likeCount` | 커밋된 `like_count` 와 같다 — 좁은 UPDATE 뒤의 낡은 사본이 아니다 |
| claim 이 계약 밖인 토큰 | 401 `A002` (컨트롤러 테스트 — 1차 `PostControllerTest` 의 `role = BOGUS` 테스트와 같은 방식. 인증 경로 목록은 무토큰 `A001` 만 본다) |

---

### B-21 상세 조회의 선택적 인증과 조회수 판정 — P-05 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-14, B-16, B-19 |
| 병렬 | §1.2 |
| 공유 파일 | `PostService`, `PostController`, `PostDetailResponse`, `PostServiceTest` — B-19 다음, B-24 앞. `PostRepository` — B-14 다음, B-17 도 고친다 |
| 마이그레이션 | 없음 (`V6` 은 B-14) |
| 참조 | [../requirements/board.md §9](../requirements/board.md)(§9.1~§9.3), [../api-contract.md §4.8](../api-contract.md)·§4.3·§4.4·§9.6, [../domain-model.md §4.5](../domain-model.md)·§6, [../security.md §9](../security.md), [../tech-stack.md §4.5](../tech-stack.md), [../nfr.md §4](../nfr.md), [../adr/0014](../adr/0014-view-count-dedup.md) |

**산출물**
- `post/support/` — 판정 키 만들기(HMAC), 판정(상세 조회와 다른 트랜잭션), 오래된 판정 행의 정리 작업
- `post/repository/PostViewRepository` — 조건부 UPDATE, 존재 확인, 정리 삭제
- `post/repository/PostRepository` — `increaseViewCount` 의 javadoc(부르는 쪽, `clearAutomatically` 의 근거)을 새 경로로 고친다. 2026-11-13 코드 읽기로 그 javadoc 은 `PostService.getDetail` 이 그 문장을 부른 뒤 같은 영속성 컨텍스트에서 글을 다시 읽는 것을 근거로 든다 — +1 이 판정 트랜잭션으로 옮겨 가면 맞지 않는다
- `PostService`·`PostController` — 상세 조회의 선택적 리졸버, 판정 뒤의 읽기, `liked`
- `PostDetailResponse` — `liked`. 작성 응답은 `false`, 수정 응답은 요청한 계정의 실제 상태다([../api-contract.md §4.4](../api-contract.md))
- `PostServiceTest` — B-11 블록의 javadoc. `comment_count`·`totalElements` 의 등식을 인용한 문장을 지금의 계약으로 고친다(B-22 의 완료 기준이 나눈 몫이다)

**완료 기준**
- [ ] 판정 키가 [../requirements/board.md §9.1](../requirements/board.md)의 모양이다 — 유효한 토큰이면 `a:` + accountId, 토큰이 없으면 `i:` + `HMAC-SHA256(비밀키, remoteAddr)` 의 소문자 hex. 원 IP 를 저장하지도 로그에 남기지도 않는다([../security.md §9](../security.md))
- [ ] `X-Forwarded-For` 같은 헤더를 읽지 않는다 — `remoteAddr` 만 쓴다
- [ ] 없는·삭제된 글은 404 `P001` 이고 판정 행이 생기지 않는다 — 판정은 404 판정 뒤다([../domain-model.md §4.5](../domain-model.md))
- [ ] 판정이 [../requirements/board.md §9.3](../requirements/board.md)의 순서다 — 조건부 UPDATE 먼저, 0행이면 존재 확인, 없을 때만 INSERT. `INSERT IGNORE`·`ON DUPLICATE KEY UPDATE` 를 쓰지 않는다
- [ ] 집계될 때만 `view_count` 를 좁은 UPDATE 로 +1 하고 그 +1 이 판정 트랜잭션 안이다
- [ ] **판정 INSERT 의 UNIQUE 충돌이 상세 조회를 500 으로 만들지 않는다** — 판정이 상세 조회와 다른 트랜잭션이다
- [ ] **응답의 `viewCount` 는 판정 커밋 뒤에 시작된 읽기의 값이다** — 판정 전에 연 트랜잭션에서 읽지 않는다
- [ ] 24시간 안의 조회는 창을 밀지 않는다(`viewed_at` 불변). 지난 조회는 +1 이고 그 시각이 새 기준이다. 시각은 앱 시계이고 DB 의 `NOW()` 를 쓰지 않는다
- [ ] 작성자 자신의 조회도 센다
- [ ] 정리 작업이 기준 시각이 24시간을 넘은 행만 B-16 의 주기로 지운다
- [ ] 정리 작업이 실패하면 로그로 드러난다 — 예외를 삼키지 않는다([../nfr.md §4](../nfr.md)의 `post_view` 줄)
- [ ] `liked` 는 토큰이 없으면 `null`, 있으면 그 계정이 눌렀는지다. 키는 언제나 있다([../api-contract.md §4.3](../api-contract.md))
- [ ] 상세 조회가 B-16 의 선택적 리졸버를 쓴다 — claim 이 계약 밖인 토큰은 401 `A002` 다
- [ ] **H2 테스트 연결의 격리 수준을 재서 보고에 적는다.** MySQL 의 반복 읽기와 다르면 위 `viewCount` 기준을 H2 테스트가 잡지 못한다는 것도 적는다([../requirements/board.md §9.3](../requirements/board.md)이 「확인 필요」 로 남겼다). **검증표에 넣지 않는다** — 측정이다
- [ ] 1차의 조회수 단언(상세 조회마다 +1, 같은 글의 동시 조회 N건 → N)을 지금의 계약으로 고친다 — 같은 조회자는 한 번, 서로 다른 조회자는 각각이다. **B-11 의 「조회 하나가 `comment_count` 를 덮어쓰지 않는다」 와 좁은 UPDATE 의 모양 단언은 그대로 둔다**
- [ ] 상세 키를 리터럴 집합으로 단언하는 테스트에 `liked` 를 더한다(B-19 와 같은 이유)
- [ ] 기존 테스트가 깨지지 않는다 — 위에서 고친 단언 밖에서

**검증** — `PostServiceTest`, `PostControllerTest` 확장, 판정·정리의 테스트

| 케이스 | 기대 결과 |
| --- | --- |
| 비로그인 첫 조회 | 200, `viewCount` +1, 판정 행의 키가 `i:` + 소문자 hex 64자 |
| 비로그인 판정 키의 값 | `i:` 뒤가 테스트 비밀키로 계산한 `HMAC-SHA256(비밀키, remoteAddr)` 의 소문자 hex 와 같다 — 키 없는 SHA-256·설정 밖의 키로 바꾸면 깨진다([../security.md §9](../security.md)) |
| 같은 주소의 재조회 (24시간 안) | `viewCount` 불변, `viewed_at` 불변 |
| 로그인 조회 | 키가 `a:{accountId}` |
| 작성자가 자기 글을 처음 조회 | `viewCount` +1 |
| 같은 사람의 로그인 전·후 조회 | 두 조회자 — 각각 +1 |
| 다른 `remoteAddr` | 다른 키 |
| 같은 `remoteAddr` 에 `X-Forwarded-For` 만 다르게 | 같은 키 |
| 판정 행의 `viewed_at` 을 24시간보다 이전으로 옮긴 뒤 조회 | +1, `viewed_at` 이 새 시각 |
| **같은 키의 동시 첫 조회 N건** | `view_count` +1, 응답 전부 200 |
| **판정 INSERT 가 UNIQUE 충돌** (끼워넣기를 강제한다) | 200 — 500 이 아니다, 집계 불변 |
| 서로 다른 조회자의 동시 조회 N건 | `view_count` = N (B-11 의 소실 방지가 그대로) |
| 응답의 `viewCount` | 판정이 반영된 값 — 집계된 조회면 증가 뒤의 값 |
| 없는·삭제된 글 | 404 `P001`, 판정 행 0 |
| `liked` — 토큰 없음 / 누른 계정 / 누르지 않은 계정 | `null` / `true` / `false` |
| 작성 응답의 `liked` / 수정 응답의 `liked` | `false` / 요청한 계정의 실제 상태 |
| claim 이 계약 밖인 토큰으로 상세 조회 | 401 `A002` |
| 정리 작업 | 기준 시각이 24시간을 넘은 행만 지운다 |
| 정리의 삭제가 예외를 던진다 (대역으로 만든다) | 그 예외를 삼키지 않는다 |
| 판정 행 | `viewer_key` 에 주소 문자열이 들어 있지 않다 |

---

### B-22 답글 — C-05 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-14, B-15, B-17 |
| 병렬 | §1.2 |
| 공유 파일 | `CommentService`, `CommentRepository`, `CommentServiceTest`, `CommentController`, `comment/dto/*` — B-17 다음 |
| 마이그레이션 | 없음 (`V4` 는 B-14) |
| 참조 | [../requirements/board.md §12](../requirements/board.md)·§5, [../domain-model.md §5](../domain-model.md)·§4.2·§6, [../api-contract.md §4.5](../api-contract.md)·§9.7, [../process/review-policy.md §4.1](../process/review-policy.md) |

**산출물**
- `comment/dto/*` — 작성 본문의 `parentId`, 댓글 모양의 `parentId`·`deleted`, 목록 최상위의 `replies`
- `comment/service/CommentService`, `comment/controller/CommentController`
- `comment/repository/CommentRepository` — 최상위 페이징과 그 페이지의 답글을 한 번에 읽는 조회

**완료 기준**
- [ ] `parentId` 가 없거나 `null` 이면 최상위 댓글이다
- [ ] 판정 순서가 [../requirements/board.md §12](../requirements/board.md)와 같다 — 없는·삭제된 글 404 `P001` → 부모의 존재·같은 글·활성 404 `CM001` → 부모가 최상위인가 400 `CM003`. 프로필 판정(`S001`·`S002`)은 1차처럼 그보다 앞의 트랜잭션 밖이다
- [ ] 답글 작성도 `comment_count` +1 이고 **`post` 의 좁은 UPDATE 를 INSERT 보다 먼저 한다** — 1차 작성 경로의 순서이고, B-17 이 고친 삭제와 같은 쪽이다([../domain-model.md §6](../domain-model.md)의 블록인용)
- [ ] 목록이 최상위를 페이징하고(기본 20) 답글을 각 최상위 아래에 전부 등록순으로 싣는다. 페이징 단위와 `totalElements` 가 최상위 항목이다([../api-contract.md §4.5](../api-contract.md))
- [ ] 활성 답글이 있는 삭제된 최상위만 자리로 남고, 그 자리는 `deleted: true` 이며 `writerId`·`writerNickname`·`content` 가 `null` 이다. 활성 답글이 없어지면 자리도 사라진다. 지운 답글은 싣지 않는다
- [ ] 댓글 모양(작성·수정 응답과 답글)이 §4.5 의 키 집합과 정확히 같고, 최상위 항목은 거기에 `replies` 를 더한 것이다
- [ ] 답글이 달린 댓글을 지워도 답글은 남고, 지운 그 하나만 `comment_count` −1 이다(B-17 의 경로)
- [ ] **목록의 쿼리 수가 최상위 항목 수·답글 수와 무관하다** — 행 수만 바꾼 두 측정이 같은지 본다([phase1.md](phase1.md) B-09 의 블록인용과 같은 방식)
- [ ] 1차 테스트의 댓글 키 단언과, `comment_count`·`totalElements` 의 등식을 인용한 1차 javadoc 을 지금의 계약으로 고친다(이 문서 머리의 둘째 문단). 그 javadoc 은 `CommentServiceTest` 의 것이 이 항목, `PostServiceTest`(B-11 블록)의 것이 B-21 의 몫이다
- [ ] **부모 확인과 커밋 사이의 창은 닫지 않는다.** [../requirements/board.md §12](../requirements/board.md)가 「삭제된 댓글에 답글 불가」 를 보장이 아니라 통상 동작으로 두었고, B-17 뒤에 「그때 다시 본다」 고 적었다 — 닫기로 하면 정본 개정이 먼저다
- [ ] 기존 테스트가 깨지지 않는다 — 위에서 고친 단언 밖에서

**검증** — `CommentServiceTest`, `CommentControllerTest`, `CommentRepositoryTest` 확장

| 케이스 | 기대 결과 |
| --- | --- |
| 최상위 작성 | 201, `parentId: null`, `deleted: false`, 키 집합이 §4.5 의 댓글 모양 |
| 답글 작성 | 201, `parentId` 가 부모, `comment_count` +1 |
| 답글에 답글 | 400 `CM003` |
| 없는 부모 / 다른 글의 댓글 / 삭제된 부모 | 404 `CM001` |
| 다른 글의 **답글**을 부모로 | 404 `CM001` (`CM003` 아님 — 순서) |
| 삭제된 글에 답글 | 404 `P001` |
| 프로필 없는 계정의 답글 | 403 `S002`, 행 0, 집계 불변 |
| 발행 순서 | `update post` 가 `insert into comment` 보다 먼저다 |
| 최상위 25개와 각 답글 | 첫 페이지 최상위 20, `totalElements` 25, 답글 전부 |
| 목록 최상위 항목의 키 집합 | §4.5 의 댓글 모양 + `replies` — 리터럴 집합으로 대조한다 |
| 목록 답글 원소의 키 집합 | §4.5 의 댓글 모양 — `replies` 가 없다 |
| 답글 없는 최상위 | `replies: []` |
| 답글 있는 부모 삭제 | 부모 자리 `deleted: true`, 세 필드 `null`, 답글 그대로, `comment_count` −1 |
| 활성 최상위 2·활성 답글이 있는 삭제된 최상위 1·답글 없는 삭제된 최상위 1, `size=2` 의 첫 페이지 | `totalElements` 3 — 페이지가 꽉 차 건수 쿼리를 본다(review-policy §4.1 의 `PageImpl` 블록인용) |
| 위에서 그 삭제된 최상위의 답글까지 삭제, 같은 `size` | 자리가 사라지고 `totalElements` 2 |
| 답글 없는 최상위 삭제 | 목록에서 사라진다 |
| 지운 답글 | 싣지 않는다 |
| 글 삭제 | 답글도 논리 삭제된다 (1차 연쇄 그대로) |
| 같은 `created_at` 의 최상위·답글 | `id` 로 순서가 정해진다 |
| 목록 쿼리 수 | 최상위·답글 수를 바꾼 두 측정이 같다 |
| 목록 `size=0` / `page=-1` | 400 `C001`, `fieldErrors` 1건 (1차 그대로) |

---

### B-23 첨부 올리기와 저장소 — P-10 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-14, B-15, B-16 |
| 병렬 | §1.2 |
| 공유 파일 | `attachment/*` — B-24 가 이어서 고친다 |
| 마이그레이션 | 없음 (`V7` 은 B-14) |
| 참조 | [../requirements/board.md §11](../requirements/board.md), [../domain-model.md §6.2](../domain-model.md)·§4.6, [../api-contract.md §4.7](../api-contract.md)·§4.3·§9.9, [../security.md §8](../security.md), [../tech-stack.md §4.5](../tech-stack.md), [../adr/0013](../adr/0013-attachment-storage.md) |

**산출물**
- `attachment/storage/` — 저장소 인터페이스(저장·열기·지우기)와 로컬 디스크 구현([../adr/0013](../adr/0013-attachment-storage.md)). 저장 루트는 B-16 의 설정이다
- `attachment/controller/*`, `attachment/service/*`, `attachment/dto/*` — 올리기와 첨부 하나의 모양
- 형식 판정(매직 바이트)·파일명 정리 — 자리는 구현이 고른다. 의존성을 더하지 않는다([../tech-stack.md §4.5](../tech-stack.md))

**흐름은 [../domain-model.md §6.2](../domain-model.md)다** — 판정을 모두 지난 뒤 트랜잭션 밖에서 파일을 쓰고, 한 트랜잭션에서 `attachment_count` 의 조건부 UPDATE → INSERT 를 한다. 실패하면 쓴 파일을 지운다(best effort).

**완료 기준**
- [ ] 판정 순서가 [../requirements/board.md §11](../requirements/board.md)과 같다 — 401 → multipart·크기(`C001`·`C008`) → 0바이트 400 `C001` → 404 `P001` → 403 `P002` → 형식 400 `AT002`·파일명 400 `C001` → 개수 409 `AT003`. **형식·파일명까지의 판정에서 거부될 요청은 파일을 쓰지 않는다** — 개수 409 는 쓴 파일을 지운다([../domain-model.md §6.2](../domain-model.md))
- [ ] `multipart/form-data` 가 아니면 415 `C006` 이다 — 매핑이 `consumes` 로 선언한다([../api-contract.md §4.7](../api-contract.md))
- [ ] 형식은 매직 바이트로만 판정한다 — 요청의 `Content-Type`·확장자를 쓰지 않는다. 판정한 형식이 저장되고 응답의 `contentType` 이 된다. SVG 는 받지 않는다
- [ ] 파일명은 경로 구분자 앞부분과 제어 문자를 버린 뒤 1~255자여야 하고 메타데이터로만 쓴다
- [ ] 저장 이름이 서버가 만든 UUID 이고 파일이 저장 루트 바로 아래 그 이름 하나다 — 요청의 어떤 값도 경로가 되지 않는다
- [ ] **개수 상한은 `attachment_count` 의 조건부 UPDATE 하나가 판정한다.** 0행이면 글이 없거나 지워졌을 때 404 `P001`, 아니면 409 `AT003` 이다. 미리 세어 보는 것은 형식·파일명 판정 뒤에만 둘 수 있고 판정이 아니다
- [ ] DB 가 실패하면 쓴 파일을 지운다
- [ ] 글 작성자만 올린다 — ADMIN 도 남의 글에는 403 `P002` 다. 프로필이 필요 없다(`MemberClient` 호출 0회)
- [ ] 201 응답의 키 집합이 [../api-contract.md §4.7](../api-contract.md)의 첨부 하나의 모양과 같고 저장 이름이 나가지 않는다. `createdAt` 이 저장값과 같다([../api-contract.md §4.3](../api-contract.md)의 쓰기 응답 문단)
- [ ] 핸들러가 `@CurrentMember` 를 받고 `JwtAuthenticationTest` 의 인증 경로 목록에 들어 있다
- [ ] 기존 테스트가 깨지지 않는다

**검증** — 서비스·컨트롤러·저장소 테스트. 저장 루트는 테스트마다 비운 임시 디렉터리다([../tech-stack.md §4.5](../tech-stack.md))

| 케이스 | 기대 결과 |
| --- | --- |
| 네 형식의 머리를 가진 파일 | 201, `contentType` 이 판정한 값 |
| PNG 머리 + 요청 `Content-Type: image/jpeg` + 확장자 `.jpg` | 201, `contentType: image/png` |
| SVG / 텍스트 / 머리보다 짧은 파일 | 400 `AT002`, 파일 없음 |
| 0바이트 | 400 `C001`, 파일 없음 |
| 삭제된 글에 0바이트 | 400 `C001` (`P001` 아님 — 순서), 파일 없음 |
| `file` 파트 없음 | 400 `C001` |
| multipart 가 아닌 요청 | 415 `C006` |
| 파일명 `../../x.png`·`C:\a\b.png` | 201, 원본 파일명은 앞부분을 버린 값, 저장 경로와 무관 |
| 정리 뒤 빈 파일명 / 256자 | 400 `C001`, 파일 없음 |
| 정리 뒤 1자 / 255자 파일명 | 201, 저장된 원본 파일명이 그 값 |
| 제어 문자가 든 파일명 | 제어 문자를 버린 값 |
| 남의 글 (USER·ADMIN) | 403 `P002`, 파일 없음 |
| 남의 글에 SVG | 403 `P002` (`AT002` 아님 — 순서), 파일 없음 |
| 없는·삭제된 글 | 404 `P001`, 파일 없음 |
| 남의 삭제된 글 | 404 `P001` (`P002` 아님 — 순서), 파일 없음 |
| 활성 첨부가 상한인 글 | 409 `AT003`, 파일이 남지 않는다 |
| 활성 첨부가 상한인 글에 SVG | 400 `AT002` (`AT003` 아님 — 순서), 파일 없음 |
| **상한 하나 아래에서 동시 올리기 N건** | 성공 1, 나머지 409 `AT003`, `attachment_count` 와 활성 행이 상한, 남은 파일 수 = 행 수 |
| INSERT 가 실패하는 경로 | 쓴 파일이 지워진다 |
| 응답 키 집합 | §4.7 의 첨부 하나의 모양과 정확히 같다 |
| 응답의 `createdAt` | 다시 읽은 저장값과 같다 |
| 저장된 파일 | 저장 루트 바로 아래 UUID 이름 |
| 프로필 없는 계정 | 201, `MemberClient` 호출 0회 |
| claim 이 계약 밖인 토큰 | 401 `A002` (컨트롤러 테스트 — 1차 `PostControllerTest` 의 `role = BOGUS` 테스트와 같은 방식. 인증 경로 목록은 무토큰 `A001` 만 본다) |

> **크기 한도(413 `C008`)는 이 항목의 검증표에 없다.** 매핑은 B-15 가 예외를 직접 던져 보고, 컨테이너를 거친 응답은 통합이 잰다(§4.1).

---

### B-24 첨부 내려받기·지우기와 상세의 첨부 목록 — P-10 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-21, B-23 |
| 병렬 | §1.2 |
| 공유 파일 | `PostService`·`PostDetailResponse`·`PostServiceTest`(B-21 다음), `attachment/*`(B-23 다음) |
| 마이그레이션 | 없음 |
| 참조 | [../requirements/board.md §11](../requirements/board.md), [../api-contract.md §4.7](../api-contract.md)·§4.3·§4.4·§9.6, [../security.md §8](../security.md), [../domain-model.md §6.2](../domain-model.md)·§4.6 |

**산출물**
- `attachment/controller`·`attachment/service` — 내려받기(스트리밍)와 지우기
- `attachment/repository/AttachmentRepository` — 조건부 전환(활성일 때만), 글의 활성 첨부 조회
- `PostService`·`PostDetailResponse` — `attachments`

**완료 기준**
- [ ] 내려받기가 비로그인에 열려 있고, 성공 응답은 봉투가 아니라 파일의 바이트다. 헤더가 [../security.md §8](../security.md)의 서빙 응답 헤더 표와 같다
- [ ] 없는·삭제된 첨부, 지워진 글의 첨부, 저장소에 파일이 없는 첨부는 모두 404 `AT001`(봉투)이다. 파일이 없을 때는 WARN 을 남긴다
- [ ] `Content-Disposition` 의 파일명은 `filename*=UTF-8''` 퍼센트 인코딩으로만 싣는다 — 따옴표·줄바꿈이 헤더로 새지 않는다
- [ ] 지우기의 판정 순서가 없는·이미 지운 첨부 404 `AT001`(그 글이 지워졌어도 같다) → 403 `P002` 다. ADMIN 도 남의 글의 첨부는 403 `P002` 다
- [ ] 지우기가 [../domain-model.md §6.2](../domain-model.md)의 모양이다 — `attachment_count` 감소가 먼저이고, 첨부의 조건부 전환이 최종 판정이며 0행이면 되돌린다(404 `AT001`). 집계가 이미 0 이면 0 에 두고 WARN
- [ ] 파일은 어느 경우에도 지우지 않는다
- [ ] 상세·수정 응답의 `attachments` 가 활성 첨부를 올린 순서(`id` 오름차순)로 싣고 원소가 §4.7 의 모양이다. 작성 응답은 빈 배열이다
- [ ] **상세 모양의 키 집합이 [../api-contract.md §4.3](../api-contract.md)의 상세 줄과 정확히 같다** — 상세 키를 리터럴 집합으로 단언하는 테스트를 그 줄로 고쳐 B-19·B-21 이 더한 키와 함께 여기서 대조한다
- [ ] 지우기 핸들러가 `@CurrentMember` 를 받고 `JwtAuthenticationTest` 의 인증 경로 목록에 들어 있다
- [ ] 기존 테스트가 깨지지 않는다 — 위에서 고친 단언 밖에서

**검증** — `PostServiceTest`·`PostControllerTest` 확장, B-23 이 만든 첨부의 서비스·컨트롤러 테스트 확장. 지우기 경로의 무토큰 401 은 B-16 이 `JwtAuthenticationTest` 에 넣는다 — 이 항목은 그 목록에 경로가 있는지 확인만 한다

| 케이스 | 기대 결과 |
| --- | --- |
| 내려받기 | 200, 본문이 올린 바이트, 헤더가 [../security.md §8](../security.md)의 표와 같다 |
| 비로그인 내려받기 | 200 |
| 삭제된 첨부 / 지워진 글의 첨부 / 없는 id | 404 `AT001` 봉투 |
| 행은 있는데 파일이 없다 | 404 `AT001`, WARN |
| 따옴표·줄바꿈·한글이 든 원본 파일명 | `filename*=UTF-8''…` 로만 실리고 헤더가 깨지지 않는다 |
| 지우기 | 204, `attachment_count` −1, 파일이 남는다, 내려받기 404 `AT001` |
| **같은 첨부의 동시 지우기 N건 — 판정 읽기가 어느 쓰기보다 먼저 일어나게 강제한다** | 성공 1, 나머지 404 `AT001`, `attachment_count` 가 1 만 준다 |
| 상한이던 글에서 하나를 지운 뒤 올리기 | 201 |
| 집계가 0 인데 활성 첨부를 지우기 | 204, 집계 0, WARN |
| 남의 글의 첨부 (USER·ADMIN) | 403 `P002` |
| 이미 지운 첨부를 지우기, 그 글도 지워졌다 | 404 `AT001` (`P001` 아님) |
| 남의 글의 이미 지운 첨부를 지우기 | 404 `AT001` (`P002` 아님 — 순서) |
| 프로필 없는 계정이 자기 글의 첨부를 지우기 | 204, `MemberClient` 호출 0회 |
| claim 이 계약 밖인 토큰으로 지우기 | 401 `A002` |
| 상세의 `attachments` | 활성만, `id` 오름차순, 원소의 키가 §4.7 의 모양 |
| 수정 응답의 `attachments` | 상세와 같다 — 활성만, `id` 오름차순 |
| 작성 응답의 `attachments` | 빈 배열 |
| 상세 모양의 키 집합 (작성·수정·상세) | [../api-contract.md §4.3](../api-contract.md)의 상세 줄과 정확히 같다 — 리터럴 집합으로 대조한다 |

## 4. 넘기는 것

### 4.1 통합 계획이 I 항목으로 세울 측정 대상

[phase2.md §5.4](phase2.md)가 실 MySQL·실서버에서 재라고 한 것 중 board 의 것이다 — §5.4 밖에서 온 줄은 줄 머리에 그렇게 적는다. **이 계획은 항목으로 세우지 않는다** — 통합 계획([phase2-frontend-integration.md](phase2-frontend-integration.md))이 I 항목으로 세운다. 「뒤」 는 그 측정이 뜻을 갖는 B 항목이다.

| 측정 대상 | 근거 | 뒤 |
| --- | --- | --- |
| 같은 댓글의 동시 삭제가 `comment_count` 를 한 번만 줄이는가 | [phase2.md §5.4](phase2.md), [../domain-model.md §6](../domain-model.md)의 블록인용 | B-17 |
| 같은 글의 동시 좋아요·취소에서 `like_count` 가 `post_like` 행 수와 같은가, 순서(`post` 먼저)가 교착을 막는가 | [../domain-model.md §6.1](../domain-model.md) | B-20 |
| 같은 글의 동시 첫 조회 — 서로 다른 조회자(조건부 UPDATE 의 간격 락과 INSERT 의 교착)·같은 조회자(+1 한 번). 측정이 뒤집으면 판정 순서를 바꾼다 | [../requirements/board.md §9.3](../requirements/board.md)의 블록인용 | B-21 |
| 상세 응답의 `viewCount` 가 판정의 커밋을 보는가 — MySQL 의 반복 읽기에서 | [../requirements/board.md §9.3](../requirements/board.md) | B-21 (H2 의 격리 수준은 B-21 이 잰다) |
| 경합의 UNIQUE 충돌(판정 행·좋아요)이 남기는 로그 수준 — ERROR 면 [../conventions.md §6.1](../conventions.md)과 어긋난다 | [../requirements/board.md §9.3](../requirements/board.md)의 블록인용, [../domain-model.md §6.1](../domain-model.md) | B-20, B-21 |
| 동시 답글, 같은 부모에 대한 답글 작성과 부모 삭제 — 교착과 집계 | [phase2.md §5.4](phase2.md), [../domain-model.md §6](../domain-model.md)의 블록인용 | B-17, B-22 |
| 동시 업로드가 개수 상한을 넘지 않는가 | [../domain-model.md §6.2](../domain-model.md) | B-23 |
| 같은 첨부의 동시 삭제가 `attachment_count` 를 한 번만 줄이는가 | [../domain-model.md §6.2](../domain-model.md) | B-24 |
| **한도를 넘는 업로드가 실서버에서 계약대로 응답하는가** — `max-file-size`·`max-request-size` 를 넘으면 413 `C008` 인가, `max-swallow-size` 를 넘는 본문에서 연결이 끊기는가와 그때 클라이언트가 보는 것, 토큰 없이 한도를 넘으면 401 이 먼저인가([../requirements/board.md §11](../requirements/board.md)의 판정 순서) | [../tech-stack.md §4.5](../tech-stack.md), [../conventions.md §6.1](../conventions.md) | B-15, B-23 |
| **§5.4 의 board 목록 밖이다** — 근거 열의 정본이 세 서비스에 같은 매핑을 요구하고, 세 서비스의 비교는 1차 [integration.md](integration.md) I-04 의 방식이다. 세 서비스의 multipart 매핑이 같은 본문·로그 수준을 내는가 | [../conventions.md §6.1](../conventions.md), [../api-contract.md §8.1](../api-contract.md), [integration.md](integration.md) I-04 | B-15 와 auth·member 계획의 multipart 예외 매핑 항목 |
| **제안 — §5.4 의 board 목록에는 없다.** 기동한 board 에 `X-Forwarded-For` 를 바꿔 보내도 비로그인 판정 키가 같은가(`forward-headers-strategy: none` 의 효과는 컨테이너에서만 보인다) | [../tech-stack.md §4.5](../tech-stack.md), [../security.md §9](../security.md) | B-16, B-21 |

### 4.2 화면(F)이 필요로 하는 것

[phase2.md §5.3](phase2.md)이 적은 화면 요구를 board 의 엔드포인트·에러 코드 단위로 B 항목에 잇는다. **화면 항목은 이 계획이 세우지 않는다** — [phase2-frontend-integration.md](phase2-frontend-integration.md)가 세운다. 화면의 설계는 §5.3 과 `sp-frontend` 의 `CLAUDE.md` 가 갖는다. 「뒤」 는 서버 쪽이 준비되는 B 항목이다.

| 화면이 쓰는 것 | 화면에 필요한 것 | 뒤 |
| --- | --- | --- |
| `GET /api/v1/posts?category=` | 카테고리 탭, 전체 목록 첫 페이지 위의 공지 고정(예: `category=NOTICE&page=0&size=3`). 서버는 전체 목록에서 공지를 빼지 않는다 | B-19 |
| `POST /api/v1/posts`·`PUT /api/v1/posts/{id}` 의 `category` | 선택 필드. 공지는 ADMIN 일 때만 고를 수 있게 그리고 최종 판정은 서버의 `P003` | B-19 |
| 목록·상세의 `category`·`likeCount` | 공지 배지, 좋아요 수 | B-19 |
| `PUT`·`DELETE /api/v1/posts/{id}/like` | 응답 `{liked, likeCount}` 로 버튼 상태를 바꾼다. 비로그인이면 로그인 안내 | B-20 |
| 상세의 `liked` | `null` 은 「누구인지 모른다」 이고 `false` 와 다르다([../api-contract.md §4.3](../api-contract.md)) | B-21 |
| 상세의 `viewCount` | 같은 조회자의 재조회(예: 댓글을 쓴 뒤 상세를 다시 받기)에서 오르지 않는다 — 그것을 기대한 화면 테스트·e2e 를 고친다 | B-21 |
| `POST /api/v1/posts/{postId}/comments` 의 `parentId` | 최상위 댓글에만 답글 쓰기 | B-22 |
| `GET /api/v1/posts/{postId}/comments` 의 모양 | 최상위 페이징과 `replies`, `deleted: true` 자리(세 필드 `null`)의 「삭제된 댓글입니다」, `totalElements` 가 최상위 항목의 수라 `commentCount` 와 다르다 | B-22 |
| `POST /api/v1/posts/{postId}/attachments` | `multipart/form-data`, 파트 `file`. 브라우저가 경계를 붙인 `Content-Type` 을 보내야 한다 — 지금 API 클라이언트의 기본 JSON 헤더가 그것을 깨뜨릴 것으로 추정하고 측정 대상이다(§5.3). 글을 만든 뒤 파일마다 보내므로 일부만 실패한 상태를 다룬다. 업로드 전에 위치 정보(EXIF)가 공개된다는 것을 알리는 것이 바람직하다([../security.md §8](../security.md)) | B-23 |
| 상세의 `attachments` 와 `GET /api/v1/attachments/{id}` | 글 하단 갤러리. 응답에 URL 키가 없으므로 원소의 `id` 로 board 기준 주소에 붙여 만든다([../api-contract.md §4.7](../api-contract.md)). 직접 호출 모드의 CSP `img-src` 에 board 오리진, 미리보기를 `blob:` 로 그리면 그것도(§5.3) | B-24 |
| `DELETE /api/v1/attachments/{id}` | 작성자에게만 보이는 업로더의 지우기 | B-24 |
| 경로 접두어 `/api/v1/attachments` | `sp-frontend` `CLAUDE.md` 의 「서비스 주소와 CORS」 에 board 로 배정한다(§5.3) | B-24 |
| 새 에러 코드의 문장 — [../api-contract.md §8.1](../api-contract.md)·§8.3 에서 `D-18` 이 더한 코드 | 업로드 화면의 `C008` 은 파일 크기 한도로 안내한다. **옮긴 목록과 코드 사전을 함께 고친다** — 코드 사전 테스트(`F-03`)는 정본의 변경을 스스로 잡지 못한다(§5.3) | B-15 |
| 실제 서비스 e2e 의 board 기동 | B-16 뒤로 board 는 `ATTACHMENT_STORAGE_ROOT`·`VIEW_COUNT_HMAC_SECRET` 이 없으면 뜨지 않는다. e2e 는 서비스를 띄우지 않고 `local` 로 먼저 뜬 서비스를 쓰므로(`sp-frontend` `CLAUDE.md` 의 「실제 서비스와의 e2e」) 두 값은 board 의 로컬 설정(`application-local.yml`, 템플릿은 `application-local.yml.example`)에 있어야 한다([../tech-stack.md §4.5](../tech-stack.md)) | B-16 |

### 4.3 정본 개정으로 넘기는 것

이 계획을 쓰며 본 정본의 공백과 결함이다. **이 계획은 정본을 고치지 않는다** — 아래 항목은 지금의 정본대로 하고, 정하거나 고치는 것은 정본 개정이다.

- **댓글 삭제의 어긋난 상태(활성 댓글이 있는데 `comment_count` 가 0)를 WARN 으로 드러낼지.** [../domain-model.md §6.2](../domain-model.md)의 WARN 문장은 좋아요·첨부의 두 경로만 말한다. B-17 은 WARN 을 더하지 않는다
- **답글의 부모 확인과 커밋 사이의 창.** [../requirements/board.md §12](../requirements/board.md)가 댓글 삭제를 `post` 먼저로 고친 뒤(B-17) 「그때 다시 본다」 고 적었다. B-22 는 닫지 않는다
- **지워진 글의 활성 첨부를 지울 때의 결과.** 404 `AT001` 로 정한 것은 없는·이미 지운 첨부뿐이고([../api-contract.md §4.7](../api-contract.md), [../requirements/board.md §11](../requirements/board.md)), [../domain-model.md §6.2](../domain-model.md)의 삭제 흐름은 글이 지워졌는지 보지 않는다. B-24 의 검증표는 이 경우를 단언하지 않는다
- **[../tech-stack.md §2.1](../tech-stack.md)의 블록인용이 `B-12` 를 `todo` 로 적는다**(「아직 맞지 않았다(두 항목이 `todo` 다)」). 같은 절의 `D-18` 블록인용은 「열거 검사는 B-12 가 더했다」 고 적고, sp-board `docs/checklist.md` 의 `B-12` 는 `done` 이다(2026-11-12 읽기)
- **[../tech-stack.md §4.5](../tech-stack.md)의 업로드 한도 값이 정본 값인지 예시인지 갈리지 않는다.** 표는 `max-request-size`·`max-swallow-size` 를 정본 값으로 분류하지만 값은 「예」 로 소개한 YAML 블록에만 있다. B-15 는 그 블록의 값을 쓴다
