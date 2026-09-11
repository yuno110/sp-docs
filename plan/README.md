---
title: 작업 계획
type: index
status: rule
version: v1
updated: 2026-09-11
read_when: "작업 계획의 구조를 이해하거나, 상태를 어디에 적는지 확인할 때"
related: [phase1.md, phase2.md, integration.md, ../process/dev-workflow.md]
---
# 작업 계획

| 문서 | 역할 | 갱신 시점 |
| --- | --- | --- |
| [phase1.md](phase1.md) | 1차 작업 항목. 산출물·참조·의존·완료 기준·검증 | 범위·순서가 바뀔 때만 |
| [integration.md](integration.md) | 두 서비스에 걸친 통합 검증 | 같음 |
| [phase2.md](phase2.md) | 2차 범위 개요 | 1차 완료 후 상세화 |

**이 문서들은 상태를 적지 않는다.**

## 상태의 위치

저장소가 분리되어 있으므로([../adr/0002-separate-repositories.md](../adr/0002-separate-repositories.md)) 상태 파일을 한 곳에 둘 수 없다. **항목별로 원본을 하나씩 둔다.**

| 항목 ID | 상태 원본 |
| --- | --- |
| `M-xx` | `yuno110/member` 의 `docs/checklist.md` |
| `B-xx` | `yuno110/board` 의 `docs/checklist.md` |
| `I-xx` | `yuno110/board` 의 `docs/checklist.md` (통합 단계는 순차 진행) |

M-xx의 상태 원본은 member 저장소 하나뿐이고 B-xx는 board 저장소 하나뿐이므로 "상태의 단일 원본" 원칙은 유지된다. 두 워커가 서로 다른 파일에 쓰므로 충돌하지 않는다.

## 항목 ID 규칙

| 접두어 | 의미 | 담당 |
| --- | --- | --- |
| `M` | member-service 작업 | member 워커 |
| `B` | board-service 작업 | board 워커 |
| `I` | 통합 검증 | 순차 (두 서비스 기동 필요) |

- 번호는 재사용하지 않는다. 항목을 삭제해도 번호를 비워 둔다
- 항목을 추가·분할하려면 **계획을 먼저 개정**하고 양쪽 체크리스트에 반영한다

## 작업 항목 형식

각 항목은 다섯 요소를 갖는다.

| 요소 | 내용 |
| --- | --- |
| 저장소 / 의존 / 병렬 | 어디서, 무엇 다음에, 무엇과 동시에 |
| 참조 | 읽어야 할 문서와 절 번호. **이것만 읽는다** |
| 산출물 | 만들 파일 목록. 범위를 한정한다 |
| 완료 기준 | 체크박스. 전부 충족해야 완료 |
| 검증 | 테스트 케이스 표. 전부 테스트 코드로 만든다 |

## 체크리스트 줄 형식

```
- [ ] <ID> <이름> · 상태 <todo|doing|review|blocked|done> · 커밋 <해시 또는 ->
```

`blocked`는 줄 끝에 `· 사유: ...`를 붙인다. 사유는 다음 작업자가 이어받을 수 있을 만큼 구체적으로 적는다([../process/dev-workflow.md §4](../process/dev-workflow.md)).

## 작업 시작 규칙

1. 담당 저장소의 `docs/checklist.md`에서 `doing` 항목을 먼저 찾는다
2. 없으면 순서상 다음 `todo`를 고른다. **의존 항목이 모두 `done`이어야 한다**
3. 절차는 [../process/dev-workflow.md](../process/dev-workflow.md)를 따른다
