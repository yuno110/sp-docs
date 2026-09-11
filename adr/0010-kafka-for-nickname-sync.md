---
title: 2차 Kafka로 닉네임 동기화
type: adr
status: accepted
version: v1
updated: 2026-09-11
read_when: "스냅샷의 정합성 문제를 어떻게 해소하는지 확인할 때"
related: [README.md, 0003-writer-snapshot.md, ../plan/phase2.md]
---
# 0010. 2차 Kafka로 닉네임 동기화

## 상태
accepted

## 맥락

스냅샷 방식([0003](0003-writer-snapshot.md))은 목록 조회 성능과 장애 격리를 얻는 대신 정합성을 포기했다. 회원이 닉네임을 바꿔도 과거 게시글에는 반영되지 않는다.

1차에서는 이를 "작성 당시 표기"로 정의하고 수용했다. 그러나 **즉시 반영이 요구사항으로 확정**되었다.

## 결정

**2차에 Kafka를 도입해 이벤트 기반 최종 일관성으로 해소한다.**

```
member-service                              board-service
     |                                           |
  [닉네임 변경 커밋]                              |
     |                                           |
  MemberNicknameChangedEvent --> Kafka -->    구독
  { memberId: 3, nickname: "고길동" }             |
                              UPDATE post SET writer_nickname='고길동'
                              WHERE writer_id = 3
```

동일 구조를 `MemberWithdrawnEvent`(탈퇴 시 "탈퇴한 회원" 표기)에도 적용한다.

## 설계 요건

| 요건 | 내용 |
| --- | --- |
| 발행 신뢰성 | **Transactional Outbox 패턴.** DB 커밋과 이벤트 발행의 원자성을 확보한다 |
| 소비자 멱등성 | 같은 이벤트를 다시 받아도 결과가 같아야 한다 |
| 인덱스 | `idx_post_writer_id`가 일괄 갱신 쿼리를 뒷받침한다([../domain-model.md §3.3](../domain-model.md)) |
| 컨테이너 | Kafka는 로컬 설치가 번거롭다. 이 시점에 Docker를 함께 도입한다([0005](0005-no-docker-in-mvp.md)) |

## 결과

- **1차에서 `idx_post_writer_id`를 미리 만들어 둔다.** 2차 갱신 쿼리를 위한 것이며 "내가 쓴 글" 조회에도 쓰인다
- 2차 범위에 Kafka + Docker 도입이 확정되었다([../plan/phase2.md](../plan/phase2.md))
- 1차 코드에 이벤트 발행 훅을 미리 넣지 않는다. YAGNI. 2차에 Outbox 테이블과 함께 추가한다

## "즉시"의 의미

이벤트 처리에는 수백 밀리초~수 초의 지연이 있다. 사용자가 닉네임을 바꾼 직후 새로고침하면 아직 옛 닉네임이 보일 수 있으며, 이는 **최종 일관성의 정상 동작**이다. UI 수준의 즉시성이 필요하면 화면에서 낙관적 업데이트를 적용한다.

동기 호출로 바꾸는 것은 해법이 아니다. 그러면 [0003](0003-writer-snapshot.md)에서 버린 장애 격리와 조회 성능을 다시 잃는다.
