---
title: 통합 검증
type: plan
status: living
version: v1
updated: 2026-09-11
read_when: "1차 개별 작업이 끝나고 두 서비스를 함께 검증할 때"
related: [phase1.md, ../nfr.md, ../architecture.md]
---
# 통합 검증

M-11과 B-09가 모두 `done`이 된 뒤에 진행한다.

**이 단계는 순차로 진행한다.** 두 서비스가 모두 기동된 상태를 전제하므로 병렬 작업이 불가능하다. 상태는 `yuno110/sp-board`의 `docs/checklist.md`에 기록한다([README.md](README.md) §상태의 위치).

여기서 확인하는 것은 **개별 서비스 테스트로는 잡을 수 없는 것들**이다. 두 서비스 사이의 계약, 실제 키 교환, 장애 격리, 시간대 정합.

---

## I-01 실제 키 교환과 E2E

| | |
| --- | --- |
| 의존 | M-11, B-09 |
| 참조 | [../security.md §2 §3](../security.md), [../api-contract.md §5](../api-contract.md) |

B-03에서 board-service는 **테스트용 키 페어**로 자체 검증만 했다. 여기서 member-service가 실제로 발급한 토큰을 받아 검증한다.

**작업**
1. member-service의 `public.pem`을 board-service의 `src/main/resources/jwt-public.pem`으로 교체
2. 두 서비스를 함께 기동 (`:8081`, `:8082`)
3. 아래 시나리오를 수행

**E2E 시나리오**
```
1. POST :8081/api/v1/members           회원가입
2. POST :8081/api/v1/auth/login        로그인 -> accessToken 획득
3. POST :8082/api/v1/posts             그 토큰으로 게시글 작성
4. GET  :8082/api/v1/posts             목록에서 작성자 닉네임 확인
5. POST :8082/api/v1/posts/{id}/comments   댓글 작성
6. GET  :8082/api/v1/posts/{id}        commentCount 확인
```

**완료 기준**
- [ ] member-service가 발급한 토큰을 board-service가 검증한다
- [ ] 게시글의 `writer_id`가 회원 id와 일치한다
- [ ] 게시글의 `writer_nickname`이 가입 시 닉네임과 일치한다
- [ ] 위 6단계가 오류 없이 완료된다
- [ ] board-service의 `jwt-public.pem`이 테스트용이 아닌 실제 공개키다
- [ ] **member-service의 개인키가 board 저장소에 없다**

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| E2E 6단계 수행 | 전 단계 성공 |
| 게시글의 `writerId` | 회원 id와 일치 |
| 게시글의 `writerNickname` | 가입 닉네임과 일치 |
| board 저장소에서 `private` 검색 | 개인키 없음 |
| 다른 키로 서명한 토큰 | board가 401 거부 |

---

## I-02 장애 격리

| | |
| --- | --- |
| 의존 | I-01 |
| 참조 | [../nfr.md §2](../nfr.md), [../adr/0003-writer-snapshot.md](../adr/0003-writer-snapshot.md) |

**스냅샷 설계를 채택한 핵심 근거를 실제로 확인한다.**

**작업**
1. I-01에서 게시글·댓글을 몇 건 만들어 둔다
2. **member-service를 중지한다**
3. board-service의 조회 기능을 호출한다

**완료 기준**
- [ ] member-service 중지 상태에서 `GET /api/v1/posts`(목록)가 정상 동작한다
- [ ] 작성자 닉네임이 정상 표시된다
- [ ] `GET /api/v1/posts/{id}`(상세)가 정상 동작한다
- [ ] 댓글 목록이 정상 동작한다
- [ ] 기존 토큰이 유효한 동안에는 **게시글 작성도 가능하다** (검증은 공개키로 하므로)
- [ ] member-service 재기동 후 로그인이 정상 동작한다

**검증**

| 케이스 (member 중지 상태) | 기대 결과 |
| --- | --- |
| 게시글 목록 조회 | 200, 작성자 닉네임 표시됨 |
| 게시글 상세 조회 | 200 |
| 댓글 목록 조회 | 200 |
| 유효 토큰으로 게시글 작성 | 201 |
| 로그인 시도 | 실패 (member 필요 — 정상) |
| member 재기동 후 로그인 | 200 |

이 결과가 [../adr/0003](../adr/0003-writer-snapshot.md)에서 스냅샷을 택한 이유를 증명한다.

---

## I-03 시간대 정합

| | |
| --- | --- |
| 의존 | I-01 |
| 참조 | [../tech-stack.md §5](../tech-stack.md) |

**한 서비스만 UTC면 9시간이 어긋난다.** 두 서비스와 DB가 모두 KST인지 확인한다.

**완료 기준**
- [ ] member-service의 `createdAt`과 board-service의 `createdAt`이 같은 기준 시각이다
- [ ] DB에 저장된 값이 KST다
- [ ] API 응답의 시각 형식이 `yyyy-MM-dd'T'HH:mm:ss`이고 오프셋이 없다
- [ ] 두 서비스 JVM의 기본 시간대가 `Asia/Seoul`이다

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| 회원가입·게시글 작성을 1분 내 수행 | 두 `createdAt` 차이가 1분 이내 |
| DB에서 직접 조회한 `created_at` | 현재 KST 시각과 일치 |
| API 응답의 시각 문자열 | `Z`·`+09:00` 등 오프셋 없음 |
| 두 서비스의 `TimeZone.getDefault()` | 모두 `Asia/Seoul` |

> 로컬 Windows는 OS가 KST라 이 테스트가 쉽게 통과한다. **그래서 설정을 명시했는지 함께 확인한다.** 명시하지 않으면 UTC 서버에 배포할 때 드러난다.

---

## I-04 응답 형식 계약 일치

| | |
| --- | --- |
| 의존 | I-01 |
| 참조 | [../api-contract.md §6 §7.1](../api-contract.md), [../adr/0007-shared-code-policy.md](../adr/0007-shared-code-policy.md) |

`ApiResponse` 등을 두 서비스에 복제했으므로([../adr/0007](../adr/0007-shared-code-policy.md)) **실제로 같은 형식인지 확인**한다. 이것이 복제 방식의 위험을 막는 장치다.

**완료 기준**
- [ ] 두 서비스의 성공 응답 구조가 동일하다 (`success`, `data`, `error` 키)
- [ ] 두 서비스의 에러 응답 구조가 동일하다 (`error.code`, `error.message`, `error.fieldErrors`)
- [ ] 공통 에러 코드(`C001`, `A001`~`A004`)의 HTTP 상태와 메시지가 두 서비스에서 같다
- [ ] 두 서비스의 페이징 응답 구조가 동일하다
- [ ] 어느 쪽 응답에도 스택트레이스·SQL·내부 호스트명이 없다

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| 양쪽 성공 응답의 최상위 키 | 동일 집합 |
| 양쪽 `C001` 응답 | HTTP 400, 같은 메시지, `fieldErrors` 존재 |
| 양쪽 `A001` 응답 | HTTP 401, 같은 메시지 |
| 양쪽 `A002`·`A003`·`A004` | 상태·메시지 일치 |
| 양쪽 페이징 응답 키 | `content`, `page`, `size`, `totalElements`, `totalPages`, `first`, `last` |
| 500 응답 본문 | 양쪽 모두 스택트레이스 없음 |

불일치가 발견되면 [../api-contract.md](../api-contract.md)를 정본으로 삼아 양쪽을 맞춘다.

---

## 완료 후

I-01~I-04가 모두 `done`이면 1차가 완료된다. [phase2.md](phase2.md)의 상세화를 시작한다.
