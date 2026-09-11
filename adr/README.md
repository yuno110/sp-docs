---
title: 결정 기록 (ADR)
type: index
status: rule
version: v1
updated: 2026-09-11
read_when: "어떤 결정이 왜 내려졌는지 확인하거나, 새 결정을 기록할 때"
related: [../README.md, ../overview.md]
---
# 결정 기록 (ADR)

본문 문서는 "무엇을·어떻게"만 적는다. "왜 그렇게 정했는가"는 여기 둔다.

## 목록

| 번호 | 제목 | 상태 |
| --- | --- | --- |
| [0001](0001-msa-adoption.md) | MSA 채택과 서비스 경계 | accepted |
| [0002](0002-separate-repositories.md) | 저장소 분리와 문서 전용 저장소 | accepted |
| [0003](0003-writer-snapshot.md) | 작성자 정보 스냅샷 복제 | accepted |
| [0004](0004-rs256-over-hs256.md) | JWT 서명 알고리즘 RS256 | accepted |
| [0005](0005-no-docker-in-mvp.md) | 1차에서 Docker 미사용 | accepted |
| [0006](0006-auth-inside-member-service.md) | auth를 member-service 내 패키지로 | accepted |
| [0007](0007-shared-code-policy.md) | 공통 코드 — 라이브러리 대신 표준 활용 + 최소 복제 | accepted |
| [0008](0008-api-versioning.md) | API 경로 버저닝 | accepted |
| [0009](0009-gateway-deferred.md) | API Gateway 2차 이연 | accepted |
| [0010](0010-kafka-for-nickname-sync.md) | 2차 Kafka로 닉네임 동기화 | accepted |

## 형식

- 파일명 `NNNN-<slug>.md`. 번호는 4자리 순번이며 재사용하지 않는다
- 절 구성: 상태 / 맥락 / 결정 / 결과 / 재검토 조건
- 결정이 뒤집히면 새 ADR을 만들고 이전 것의 상태를 `superseded`로 바꾼다. 삭제하지 않는다
- 이 README의 목록을 함께 갱신한다
