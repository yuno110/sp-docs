---
title: 작성자 정보 스냅샷 복제
type: adr
status: accepted
version: v1
updated: 2026-09-11
read_when: "게시글에 작성자 닉네임을 복제 저장하는 이유가 궁금할 때"
related: [README.md, ../architecture.md, 0010-kafka-for-nickname-sync.md]
---
# 0003. 작성자 정보 스냅샷 복제

## 상태
accepted

## 맥락

게시글 목록에는 작성자 닉네임이 필요하다. 모놀리식이라면 조인 한 번이다.

```sql
SELECT p.id, p.title, m.nickname
FROM post p JOIN member m ON p.member_id = m.id
```

그러나 `post`는 `board_db`에, `member`는 `member_db`에 있다([0001](0001-msa-adoption.md)). 로컬에서 두 스키마가 같은 MySQL 인스턴스에 있어 기술적으로는 조인이 가능하지만, 운영에서 DB를 물리 분리하는 순간 깨지고 게시판이 회원 테이블 스키마에 묶인다.

## 결정

**작성 시점의 닉네임을 `post.writer_nickname`에 복제 저장한다(스냅샷).**

착안점은 게시글을 작성하는 순간 작성자가 누구인지 이미 알고 있다는 것이다. 작성자 본인이 로그인 상태로 요청을 보냈고 JWT Claim에 닉네임이 들어 있다.

## 대안 비교

| | 스냅샷 (채택) | 동기 조회 |
| --- | --- | --- |
| 목록 조회 | `board_db` 단일 쿼리 | 목록 1건당 네트워크 왕복 |
| member 장애 시 | 게시글 조회 정상 | 게시판 조회 불가 |
| 닉네임 변경 | 과거 글 미반영 | 항상 최신 |
| 결합도 | 낮음 | 높음 |

게시판의 지배적 부하는 목록 조회다. 그 경로가 네트워크에 의존하지 않는 쪽을 택했다. 장애 격리 원칙([../architecture.md §2](../architecture.md))에도 부합한다.

## 결과

**얻은 것**
- 목록 조회에서 원격 호출 0회
- member-service가 죽어도 게시글 조회가 동작한다
- 작성자 닉네임 검색을 로컬 `LIKE`로 처리할 수 있다(부수 효과)

**잃은 것**
- 닉네임을 바꿔도 과거 글에는 반영되지 않는다. `writer_id`는 변하지 않으므로 "누가 썼는가"는 정확하고, 어긋나는 것은 표시용 이름뿐이다
- 2차에 Kafka 이벤트로 해소한다 → [0010](0010-kafka-for-nickname-sync.md)

**파생 규칙**
- JWT Claim에도 닉네임이 있으므로, 닉네임 변경 시 새 토큰을 발급해야 한다. 그러지 않으면 옛 토큰으로 쓴 **새 글**에도 옛 닉네임이 박제된다([../requirements/member.md](../requirements/member.md) M-08)
- `writer_id`에 FK 제약을 걸지 않는다

## 정규화 위반이 아닌가

모놀리식 DB 설계에서 데이터 중복은 정규화 위반으로 배격된다. MSA에서는 각 서비스가 자기 일에 필요한 데이터를 자기 DB에 갖는 것(Data Locality)이 원칙이며, 중복은 서비스 자율성과 장애 격리를 얻기 위해 의도적으로 지불하는 비용이다. 정규화는 서비스 경계 안쪽의 규칙이지 경계를 가로지르는 지점의 규칙이 아니다.
