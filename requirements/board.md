---
title: 게시판 기능 요구사항
type: requirements
status: frozen
version: v2
updated: 2026-09-15
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

엔드포인트와 파라미터는 [../api-contract.md §4](../api-contract.md)가 정본이다.

## 3. 작성자 정보 처리 — 핵심 규칙

작성자 닉네임은 member-service 소유 데이터이므로 **DB 조인이 불가능하다.** 작성 시점의 값을 복제 저장한다.

**`writer_id`는 JWT Claim에서, `writer_nickname`은 member의 내부 API에서 얻는다.** JWT Claim에 `nickname`이 없기 때문이다([../adr/0012](../adr/0012-auth-as-separate-service.md) §3).

```
POST /api/v1/posts
  JWT Claim { sub: "3", role: "USER" }
    1) POST /internal/v1/members/bulk  { accountIds: [3] }     <- 트랜잭션 밖
       -> 200 { members: [{ accountId: 3, nickname: "홍길동", deleted: false }] }
    2) BEGIN
       INSERT INTO post (writer_id, writer_nickname, ...) VALUES (3, '홍길동', ...)
       COMMIT
```

| 규칙 | 내용 |
| --- | --- |
| 1 | `writer_id`는 **검증된 JWT의 `sub`에서만** 가져온다. 요청 본문에서 받지 않는다 |
| 2 | `writer_nickname`은 **내부 API 응답에서만** 가져온다. 요청 본문의 닉네임을 신뢰하지 않는다 |
| 3 | **조회 키도 JWT의 `sub`다.** 본문의 `writerId`로 조회하지 않는다 |
| 4 | `writer_id`에 FK 제약을 걸지 않는다 |
| 5 | `sp_member`·`sp_auth`를 조회하지 않는다. 같은 MySQL 인스턴스에 있어도 크로스 스키마 조인 금지 |
| 6 | 닉네임 변경이 과거 글에 반영되지 않는 것은 **의도된 동작**이다. 1차에서 해결하지 않는다 |
| 7 | **수정 시 스냅샷을 갱신하지 않는다.** 작성 당시 표시를 보존한다. 그래서 수정 경로는 member를 호출하지 않는다 |
| 8 | 원격 호출은 **DB 트랜잭션 밖에서 먼저** 한다([../architecture.md §5](../architecture.md)) |

배경과 대안 비교는 [../adr/0003-writer-snapshot.md](../adr/0003-writer-snapshot.md)에 있다. 취득 경로가 바뀐 이유는 [../adr/0012](../adr/0012-auth-as-separate-service.md) §6이다. 2차 해소 방안은 [../adr/0010-kafka-for-nickname-sync.md](../adr/0010-kafka-for-nickname-sync.md)를 본다.

### 3.0 프로필이 없으면 쓸 수 없다

**활성 프로필이 있어야 글·댓글을 생성할 수 있다.** 계정만 만들고 프로필을 등록하지 않은 사용자는 `S002`(403)로 거부된다.

실패 판정은 **응답 본문으로만** 한다. HTTP 404를 "프로필 없음"으로 해석하지 않는다 — 경로 오설정이나 내부 API 키 거부가 업무 오류로 위장되어 전 사용자의 쓰기가 조용히 멈춘다. 전체 표는 [../api-contract.md §5.1](../api-contract.md)에 있다.

**member 장애 시 새 글·댓글 작성이 중단된다.** 이것은 [../adr/0012](../adr/0012-auth-as-separate-service.md)가 비용으로 수용한 것이다. 조회·수정·삭제는 영향받지 않는다.

**확인과 커밋 사이에 창이 있다.** 프로필 확인 뒤 커밋 전에 탈퇴가 커밋되면 탈퇴한 프로필의 글이 생성될 수 있다. 원격 호출을 트랜잭션 안에 넣을 수 없으므로(규칙 8) 이 창은 닫을 수 없다. **"탈퇴 후 작성 불가"는 보장이 아니라 통상 동작이다.**

### 3.1 부수 효과 — 작성자 검색이 가능하다

`writer_nickname`이 `sp_board`에 있으므로 작성자 닉네임 검색(P-03의 `searchType=WRITER`)을 로컬 `LIKE`로 처리한다. member-service 호출이 필요 없다.

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
| 8 | 게시글·댓글 **생성**에는 활성 프로필이 필요하다(§3.0). 수정·삭제에는 필요하지 않다 |

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

[../security.md §5.2](../security.md)의 권한 매트릭스를 따른다. **권한 판정은 JWT Claim의 `sub`·`role`만으로 한다.** 권한을 다른 서비스에 되묻지 않는다.

**작성자 스냅샷 취득(§3)은 권한 판정이 아니다.** 생성 경로에서 member를 호출하는 것은 닉네임을 얻기 위해서이며, 그 부수 효과로 활성 프로필이 확인된다. 수정·삭제·관리자 기능은 Claim만으로 판정하므로 member를 호출하지 않는다.

**검증은 오프라인이다.** 탈퇴나 권한 박탈이 기존 Access Token에 즉시 반영되지 않는다. 최대 노출은 토큰 만료까지이며, 잔여 권한은 그 `role`이 가진 모든 변경 권한이다 — **ADMIN이면 타인 글·댓글 삭제를 포함한다**([../adr/0012](../adr/0012-auth-as-separate-service.md) 포기 목록 1).
