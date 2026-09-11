---
title: 워커 오케스트레이션
type: process
status: draft
version: v1
updated: 2026-09-11
read_when: "워커를 배치하거나 병렬 작업 범위를 정할 때"
related: [dev-workflow.md, ../plan/README.md, ../plan/phase1.md]
---
# 워커 오케스트레이션

> **상태: draft.** 실행 환경의 두 가지 전제(§1)가 확정되면 `rule`로 올린다. 전제가 다르면 이 문서만 고치면 되며 다른 문서는 영향받지 않는다.

## 1. 전제

현재 다음을 가정한다.

| # | 전제 | 대안이면 바뀌는 것 |
| --- | --- | --- |
| 1 | 워커마다 **별도 작업 공간**을 갖는다 (각자 클론 또는 워크트리) | 한 폴더를 공유하면 §3의 병렬 배치가 불가능하고 파일 잠금 규칙이 필요하다 |
| 2 | 워커가 **체크리스트를 직접 읽고** 할 일을 고른다 | 오케스트레이터가 프롬프트로 지시한다면 §4의 작업 지시 형식을 사용한다 |

전제 1이 중요한 이유는 두 워커가 같은 디렉터리에서 일하면 서로의 파일을 덮어써 병렬의 이점이 사라지기 때문이다.

## 2. 워커 역할

| 역할 | 담당 저장소 | 담당 항목 |
| --- | --- | --- |
| member 워커 | `yuno110/member` | M-01 ~ M-11 |
| board 워커 | `yuno110/board` | B-01 ~ B-09 |
| 통합 워커 | 두 저장소 + 실행 환경 | I-01 ~ I-04 |
| 리뷰 워커 | 대상 저장소 (읽기) | 구현 결과 리뷰 |

**리뷰 워커는 구현 워커와 달라야 한다**([review-policy.md §1](review-policy.md)).

## 3. 병렬 배치

```
      member 워커                board 워커
      ───────────                ──────────
      M-01 ~ M-11                B-01 ~ B-09
           │                          │
           └────────┬─────────────────┘
                    │  두 워커 모두 done
              통합 워커
              I-01 ~ I-04   (순차)
```

**member 워커와 board 워커는 서로를 기다리지 않는다.** 두 저장소가 분리되어 있고 계약이 문서에 확정되어 있기 때문이다.

특히 B-03(JWT 검증)이 M-05(JWT 발급)를 기다릴 필요가 없다. [../api-contract.md §5](../api-contract.md)에 Claim 스펙이 있으므로 board 워커는 테스트용 키 페어로 자체 검증하면 된다. 실제 키 교환은 I-01에서 한다.

**통합 단계는 병렬화하지 않는다.** 두 서비스가 기동된 상태를 전제하며 I-01의 키 교체가 나머지의 선행 조건이다.

## 4. 워커에게 주는 것

### 4.1 워커가 체크리스트를 직접 읽는 경우 (전제 2 기본값)

워커 기동 시 다음만 알려주면 된다.

```
저장소: yuno110/member
지시: CLAUDE.md를 읽고 그 절차를 따라라.
```

나머지는 워커가 스스로 한다.

```
CLAUDE.md 읽음
  → AGENTS.md (행동 원칙)
  → docs/checklist.md 에서 doing 또는 다음 todo 선택
  → simple-docs/plan/phase1.md 에서 그 항목의 상세 확인
  → 항목의 "참조" 문서만 읽음
  → simple-docs/process/dev-workflow.md 절차대로 구현·테스트·커밋
  → docs/checklist.md 상태 갱신
```

### 4.2 오케스트레이터가 지시하는 경우

작업 항목 본문을 그대로 전달하고 아래를 덧붙인다.

```
저장소: <저장소>
작업 항목: <ID>
절차: simple-docs/process/dev-workflow.md 를 따른다
완료 후: <저장소>/docs/checklist.md 의 <ID> 줄을 done으로 갱신한다
```

작업 항목 본문은 [../plan/phase1.md](../plan/phase1.md)에서 해당 절을 잘라 쓴다. 항목마다 산출물·완료 기준·검증이 자족적으로 적혀 있어 그대로 전달 가능하다.

## 5. 문서 저장소 접근

| 작업 | 권한 |
| --- | --- |
| 정본 문서 읽기 | 모든 워커 |
| 정본 문서 수정 | **구현 워커는 하지 않는다** |

구현 중 문서가 틀렸다고 판단되면 고치지 말고 BLOCKED로 보고한다([dev-workflow.md §4](dev-workflow.md)). 문서 개정은 별도 절차다([review-policy.md §6](review-policy.md)).

이유는 문서가 두 워커의 공유 지점이기 때문이다. 한 워커가 임의로 고치면 다른 워커가 이미 그 값으로 구현한 것과 어긋난다.

## 6. 충돌 회피

| 지점 | 규칙 |
| --- | --- |
| 같은 저장소 | 한 번에 한 워커만 쓴다 |
| `docs/checklist.md` | 담당 저장소의 것만 수정한다 |
| 문서 저장소 | 구현 워커는 읽기만 |
| 산출물 목록 밖 파일 | 수정하지 않는다 ([dev-workflow.md §3](dev-workflow.md) 금지 7) |

## 7. 진행 확인

전체 진행 상황은 두 체크리스트를 함께 봐야 한다.

```bash
# member
gh api repos/yuno110/member/contents/docs/checklist.md --jq '.content' | base64 -d
# board
gh api repos/yuno110/board/contents/docs/checklist.md --jq '.content' | base64 -d
```

`blocked` 항목이 있으면 사유를 읽고 막힘을 푼다. 사유는 다음 작업자가 이어받을 수 있을 만큼 구체적이어야 한다([dev-workflow.md §4](dev-workflow.md)).
