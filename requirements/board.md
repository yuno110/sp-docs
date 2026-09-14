---
title: 게시판 기능 요구사항
type: requirements
status: frozen
version: v1
updated: 2026-09-11
read_when: "board-service의 기능을 구현하거나 완료 기준을 확인할 때"
related: [../api-contract.md, ../domain-model.md, ../security.md, ../adr/0003-writer-snapshot.md]
---
# 게시판 기능 요구사항

담당 서비스: board-service (`yuno110/sp-board`)

## 1. 게시글

| ID | 기능 | 상세 | 차수 |
| --- | --- | --- | --- |
| P-01 | 게시글 작성 | 로그인 필요. 제목 1~200자, 내용 1~10,000자. JWT Claim에서 작성자 스냅샷 저장 | 1차 |
| P-02 | 목록 조회 | 비로그인 허용. 페이징, 정렬(최신순/조회순), 삭제글 제외 | 1차 |
| P-03 | 검색 | QueryDSL 동적 쿼리. 제목/내용/제목+내용/작성자 기준. 목록 API에 통합 | 1차 |
| P-04 | 상세 조회 | 비로그인 허용. 작성자 정보·댓글 수 포함 | 1차 |
| P-05 | 조회수 증가 | 상세 조회 시 +1 | 1차 |
| P-06 | 게시글 수정 | 작성자 본인만 | 1차 |
| P-07 | 게시글 삭제 | 작성자 본인 또는 ADMIN. Soft Delete, 하위 댓글도 논리 삭제 | 1차 |
| P-08 | 내가 쓴 글 목록 | `writer_id` 기준 페이징 | 1차 |
| P-09 | 좋아요 | 회원당 게시글 1회. `post_like` 테이블 추가 | 2차 |
| P-10 | 파일 첨부 | 이미지 다중 업로드, 개당 최대 5MB | 2차 |
| P-11 | 카테고리 | 공지/자유/질문 분류 | 2차 |

## 2. 댓글

| ID | 기능 | 상세 | 차수 |
| --- | --- | --- | --- |
| C-01 | 댓글 작성 | 로그인 필요. 1~500자. `commentCount` 증가 | 1차 |
| C-02 | 댓글 목록 | 게시글별 등록순 페이징(기본 20) | 1차 |
| C-03 | 댓글 수정 | 작성자 본인만 | 1차 |
| C-04 | 댓글 삭제 | 작성자 본인 또는 ADMIN. Soft Delete, `commentCount` 감소 | 1차 |
| C-05 | 대댓글 | 1단계 depth만 | 2차 |

엔드포인트와 파라미터는 [../api-contract.md §3](../api-contract.md)이 정본이다.

## 3. 작성자 정보 처리 — 핵심 규칙

작성자 닉네임은 member-service 소유 데이터이므로 **DB 조인이 불가능하다.** 작성 시점의 값을 복제 저장한다.

```
POST /api/v1/posts
  JWT Claim { sub: "3", nickname: "홍길동" }
    -> INSERT INTO post (writer_id, writer_nickname, ...) VALUES (3, '홍길동', ...)
    -> member-service 호출 없음
```

| 규칙 | 내용 |
| --- | --- |
| 1 | `writer_id`, `writer_nickname`은 **JWT Claim에서만** 가져온다. 요청 본문에서 받지 않는다 |
| 2 | `writer_id`에 FK 제약을 걸지 않는다 |
| 3 | `member_db`를 조회하지 않는다. 같은 MySQL 인스턴스에 있어도 크로스 스키마 조인 금지 |
| 4 | 닉네임 변경이 과거 글에 반영되지 않는 것은 **의도된 동작**이다. 1차에서 해결하지 않는다 |

배경과 대안 비교는 [../adr/0003-writer-snapshot.md](../adr/0003-writer-snapshot.md)에 있다. 2차 해소 방안은 [../adr/0010-kafka-for-nickname-sync.md](../adr/0010-kafka-for-nickname-sync.md)를 본다.

### 3.1 부수 효과 — 작성자 검색이 가능하다

`writer_nickname`이 `board_db`에 있으므로 작성자 닉네임 검색(P-03의 `searchType=WRITER`)을 로컬 `LIKE`로 처리한다. member-service 호출이 필요 없다.

## 4. 입력 검증

| 항목 | 규칙 |
| --- | --- |
| title | 1~200자, 공백만으로 채울 수 없음 |
| content (게시글) | 1~10,000자 |
| content (댓글) | 1~500자 |
| page | 0 이상 |
| size | 1~50. 초과 시 50으로 절삭 |

## 5. 비즈니스 규칙

| # | 규칙 |
| --- | --- |
| 1 | 삭제된 게시글·댓글(`deleted = true`)은 목록·상세에서 제외한다 |
| 2 | 삭제된 댓글은 "삭제된 댓글입니다"로 표시할 수 있도록 행을 남긴다 |
| 3 | 게시글 삭제 시 하위 댓글을 함께 논리 삭제한다 |
| 4 | `comment_count`는 음수가 될 수 없다 |
| 5 | 소유자 검증은 Service 계층에서 한다([../security.md §5.1](../security.md)) |
| 6 | ADMIN은 삭제만 가능하고 수정은 불가하다 |
| 7 | 조회수 어뷰징 방지(동일 사용자 24h 1회)는 2차 범위다 |

## 6. P-03 상세 — 검색

QueryDSL `BooleanExpression`으로 동적 조건을 조합한다.

| searchType | 대상 컬럼 |
| --- | --- |
| `TITLE` | `title` |
| `CONTENT` | `content` |
| `TITLE_CONTENT` | `title` OR `content` |
| `WRITER` | `writer_nickname` |

- `keyword`가 없으면 조건을 적용하지 않는다(전체 목록)
- `searchType`만 있고 `keyword`가 없으면 검증 오류(`C001`)
- 정렬은 `sort` 화이트리스트 Enum으로만 받는다. 컬럼명 직접 입력 금지

## 7. 권한

[../security.md §5.2](../security.md)의 권한 매트릭스를 따른다. board-service는 JWT Claim의 `sub`·`role`만으로 판정하며 member-service에 되묻지 않는다.
