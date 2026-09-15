---
title: 2차 작업 계획 (개요)
type: plan
status: draft
version: v1
updated: 2026-09-15
read_when: "2차 범위를 확인할 때. 1차 진행 중에는 참고용이며 작업 지시로 쓰지 않는다"
related: [phase1.md, integration.md, ../adr/0010-kafka-for-nickname-sync.md, ../adr/0005-no-docker-in-mvp.md]
---
# 2차 작업 계획 (개요)

**이 문서는 개요 수준이다.** 작업 항목으로 쪼개는 것은 1차 완료 후에 한다.

지금 상세화하지 않는 이유는 1차 결과에 따라 내용이 바뀌기 때문이다. 예를 들어 Outbox 테이블 설계는 1차의 트랜잭션 경계가 실제로 어떻게 잡혔는지 보고 정해야 한다. 지금 쓰면 다시 써야 한다.

## 1. 우선순위

| 순서 | 범위 | 선행 조건 | 근거 |
| --- | --- | --- | --- |
| 1 | 컨테이너화 (Docker) | 1차 완료 | [../adr/0005](../adr/0005-no-docker-in-mvp.md) |
| 2 | Kafka + 닉네임 동기화 | 컨테이너화 | [../adr/0010](../adr/0010-kafka-for-nickname-sync.md) |
| 3 | API Gateway | 1차 완료 | [../adr/0009](../adr/0009-gateway-deferred.md) |
| 4 | 기능 확장 (좋아요·첨부·카테고리·대댓글) | 1차 완료 | [../requirements/](../requirements/) |
| 5 | 운영 강화 (Resilience4j, 분산 추적) | 3 이후 | [../nfr.md §3](../nfr.md) |

1과 2를 묶어서 진행한다. Kafka가 컨테이너를 필요로 하는 지점이기 때문이다.

## 2. 컨테이너화

**전제**: 1차에서 환경 의존 값이 설정으로 외부화되어 있어야 한다([../tech-stack.md §4.3](../tech-stack.md)). 되어 있지 않으면 이 작업 전에 먼저 처리한다.

| 산출물 | 위치 |
| --- | --- |
| `Dockerfile` | 각 서비스 저장소 |
| `docker-compose.yml` | 문서 저장소 또는 별도 인프라 저장소 (도입 시 결정) |

**바뀌는 것은 DB 접속 주소뿐이다.** `localhost:3306` → `mysql:3306`. 애플리케이션 코드는 그대로다.

부수 효과로 서비스 디스커버리가 DNS 기반이 된다([../architecture.md §6](../architecture.md)). `http://localhost:8081`을 `http://member-service:8081`로 바꾸면 된다. **이 설정을 갖는 것은 board 하나뿐이다.**

**주의**: 컨테이너의 기본 시간대는 UTC다. **`ENV TZ=Asia/Seoul`을 반드시 넣는다.** JVM 시간대를 코드·빌드가 아니라 실행 환경이 정하기로 했으므로([../adr/0011](../adr/0011-timezone-from-environment.md)), 이 한 줄이 빠지면 로그와 `LocalDateTime.now()`가 UTC가 된다. 컨테이너에서 `TimeZone.getDefault()`가 `Asia/Seoul`인지 확인하는 것이 이 단계의 검증 항목이다.

## 3. Kafka와 닉네임 동기화

목표는 [../adr/0003](../adr/0003-writer-snapshot.md)에서 포기했던 정합성을 되찾는 것이다.

```
member-service                              board-service
  [닉네임 변경 커밋]
  MemberNicknameChangedEvent --> Kafka --> 구독
       { accountId, nickname }              UPDATE post SET writer_nickname=?
                                            WHERE writer_id=?
```

**이벤트 키는 `accountId`다.** 전역 식별자가 `account.id`이기 때문이다([../adr/0012](../adr/0012-auth-as-separate-service.md) §1).

**필수 설계 요건** — 이것을 빼면 안 된다.

| 요건 | 이유 |
| --- | --- |
| Transactional Outbox | DB 커밋과 이벤트 발행의 원자성. 커밋 후 발행 실패하면 영원히 어긋난다 |
| 소비자 멱등성 | Kafka는 최소 1회 전달이다. 같은 이벤트를 두 번 받아도 결과가 같아야 한다 |
| `idx_post_writer_id` | 1차에서 이미 만들어 둠. 일괄 갱신 쿼리를 뒷받침한다 |

**이벤트 종류**

| 이벤트 | 발행 시점 | 소비 동작 |
| --- | --- | --- |
| `MemberNicknameChangedEvent` | member의 닉네임 변경 | `post`·`comment`의 `writer_nickname` 갱신 |
| `MemberWithdrawnEvent` | member의 프로필 탈퇴 | `writer_nickname`을 "탈퇴한 회원"으로 갱신 |
| `AccountWithdrawnEvent` | **auth의 계정 탈퇴** | member가 구독해 프로필을 soft delete. 탈퇴 2단계를 서버가 책임진다 |

세 이벤트 모두 페이로드의 식별자는 `accountId`다.

**1차 코드에 발행 훅을 미리 넣지 않는다.** YAGNI. Outbox 테이블과 함께 추가한다.

### 3.1 탈퇴 2단계를 서버로 옮긴다

1차의 탈퇴는 클라이언트가 2단계를 호출하고, 서버는 완주를 강제하지도 관측하지도 못한다([../architecture.md §4.4](../architecture.md)). `AccountWithdrawnEvent`가 이것을 해소한다.

```
auth: [계정 삭제 + RefreshToken 삭제 + outbox INSERT]  <- 한 로컬 트랜잭션
        --> Kafka --> member 구독 --> 프로필 soft delete (멱등)
```

**추가 요건**

| 요건 | 이유 |
| --- | --- |
| 삭제 이벤트가 프로필 생성보다 먼저 도착하는 경우 | member에 삭제 표식을 남겨야 한다. "삭제할 프로필 없음"으로 끝내면 뒤늦은 생성 요청이 통과한다 |
| 탈퇴 완료의 의미 | auth에서 계정이 막힌 시점인지, member 삭제까지 반영된 시점인지 API가 구분해야 한다. 비동기 정리 중인데 "완료"라고 응답하면 계약이 거짓이 된다 |
| 장기 실패 탐지 | outbox에 쌓인 채 전달되지 않는 이벤트를 관측할 수 있어야 한다 |

## 4. API Gateway

Spring Cloud Gateway를 도입한다. Boot 버전과 호환되는 릴리스 트레인을 확인해 고정한다.

| 담당 | 내용 |
| --- | --- |
| 라우팅 | [../api-contract.md §1](../api-contract.md)의 경로 표가 그대로 명세가 된다 |
| CORS | 각 서비스의 개별 설정을 게이트웨이로 이관 |
| `/internal/**` | **라우팅에서 제외**해 외부 노출을 차단 |
| 1차 JWT 검증 | 게이트웨이에서 한 번, 각 서비스에서 한 번 더 (Zero Trust) |

각 서비스의 독립 검증을 제거하지 않는다. 게이트웨이 우회 호출 가능성을 배제하지 않는다.

## 5. 기능 확장

| ID | 기능 | 비고 |
| --- | --- | --- |
| P-09 | 좋아요 | `post_like` 테이블. 회원당 게시글 1회 |
| P-10 | 파일 첨부 | 저장소(로컬/S3)를 이 시점에 결정 |
| P-11 | 카테고리 | 공지/자유/질문 |
| C-05 | 대댓글 | 1단계 depth만 |
| M-13 | 회원 목록 (ADMIN) | QueryDSL 페이징 |
| - | 조회수 어뷰징 방지 | 동일 사용자 24h 1회 |
| - | 로그인 실패 5회 잠금 | |
| - | 이메일 인증·비밀번호 재설정 | |

## 6. 운영 강화

| 항목 | 내용 |
| --- | --- |
| Resilience4j | `board -> member` 호출에 서킷 브레이커. 1차의 타임아웃 위에 얹는다. **쓰기 경로가 member에 의존하므로 1차보다 값어치가 크다** |
| 토큰 블랙리스트 / introspection | 탈퇴·권한 박탈의 즉시 차단. 1차는 최대 30분 노출을 감수한다([../security.md §5.3](../security.md)) |
| 분산 추적 | Micrometer Tracing + Zipkin. `X-Request-Id` 전파를 대체 |
| JWKS | **auth-service**가 `/.well-known/jwks.json` 제공, member·board가 공개키 자동 획득. **배포 지점 2곳이 사라진다** |

## 7. 상세화 시점

1차의 I-04가 `done`이 되면 이 문서를 [phase1.md](phase1.md)와 같은 형식(산출물·참조·의존·완료 기준·검증)으로 상세화한다.
