---
title: 비기능 요구사항
type: spec
status: living
version: v1
updated: 2026-09-11
read_when: "성능·장애 격리 기준을 확인하거나, 완료 기준의 검증 수단을 정할 때"
related: [architecture.md, process/dev-workflow.md]
---
# 비기능 요구사항

## 1. 성능

| 항목 | 기준 |
| --- | --- |
| 게시글 목록 조회 | p95 < 300ms (1만 건 기준) |
| 목록 조회의 원격 호출 | **0회** (스냅샷 설계로 보장) |
| N+1 쿼리 | 발생 시 `fetch join` 또는 `@BatchSize`로 해결 |

`commentCount`를 `post`에 비정규화해 둔 것은 목록 조회에서 댓글 수 집계 쿼리를 없애기 위해서다([domain-model.md §3.1](domain-model.md)).

## 2. 장애 격리

| 시나리오 | 기대 동작 |
| --- | --- |
| member-service 다운 | 게시글 **조회**는 정상. 로그인·작성만 불가 |
| 내부 API 호출 실패 | 스냅샷 값으로 폴백. 게시판 조회를 실패시키지 않음 |

이 기준은 통합 검증 단계에서 실제로 member-service를 내리고 확인한다([plan/integration.md](plan/integration.md)).

## 3. 회복탄력성

| 항목 | 기준 |
| --- | --- |
| 서비스 간 호출 타임아웃 | connect 1초 / read 3초 |
| 타임아웃 미지정 | 금지. 기본값(무제한)으로 두지 않는다 |
| 서킷 브레이커 | 2차 범위 |

## 4. 확장성·가용성

- Stateless 설계로 서비스별 독립 수평 확장이 가능하다
- 각 서비스가 `/actuator/health`를 제공한다

## 5. 로깅·추적

| 항목 | 기준 |
| --- | --- |
| 요청 추적 | `X-Request-Id` 헤더를 서비스 간 전파하고 MDC에 실어 로그 상관관계를 만든다 |
| SQL 로그 | 로컬 프로파일만 ON. 운영 OFF |
| 민감정보 | 비밀번호·토큰·키를 로그에 남기지 않는다 |

## 6. 테스트

| 항목 | 기준 |
| --- | --- |
| Service 계층 | 단위 테스트 필수 |
| 주요 API | 통합 테스트(`@SpringBootTest` + MockMvc) |
| 커버리지 목표 | 70% |
| 커버리지 채우기용 테스트 | **작성하지 않는다.** 동작을 검증하지 않는 테스트는 없는 것만 못하다 |
| 서비스 간 연동 | 계약 테스트 또는 Mock 서버로 검증 |

작성 시점과 검증 절차는 [process/dev-workflow.md](process/dev-workflow.md)가 정한다.

## 7. 데이터 정합성

- 모든 쓰기는 트랜잭션 내에서 수행한다
- 논리 삭제(`deleted = true`) 데이터는 조회 시 일괄 제외한다
- 서비스 간은 최종 일관성을 허용한다([architecture.md §4.2](architecture.md))

## 8. 문서화

- 서비스별 Swagger UI (`/swagger-ui.html`)
- 운영 프로파일에서는 비활성화한다

## 9. 시간대

전 구성요소 KST(`Asia/Seoul`) 통일. 설정 항목과 검증 방법은 [tech-stack.md §5](tech-stack.md)를 본다.
