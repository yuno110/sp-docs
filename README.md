---
title: simple 프로젝트 문서
type: index
status: rule
version: v1
updated: 2026-09-11
read_when: "이 프로젝트에서 어떤 작업이든 시작하기 전. 어떤 문서를 읽어야 하는지 정할 때"
related: [plan/README.md, process/dev-workflow.md]
---
# simple 프로젝트 문서

게시판·회원 백엔드 시스템(MSA)의 정본 문서다. 사람과 AI 워커가 같은 문서를 읽는다는 전제로 쓴다.

이 저장소는 **문서만** 둔다. 코드는 `yuno110/sp-member`, `yuno110/sp-board` 두 저장소에 있다.

## 저장소 구성

| 저장소 | 내용 | 쓰기 주체 |
| --- | --- | --- |
| `yuno110/sp-docs` | 이 저장소. 정본 문서, 작업 계획 | 정본 개정 시에만 |
| `yuno110/sp-member` | member-service 코드 + `docs/checklist.md` | member 담당 워커 |
| `yuno110/sp-board` | board-service 코드 + `docs/checklist.md` | board 담당 워커 |

**작업 항목의 상태는 각 서비스 저장소의 `docs/checklist.md`에 있다.** 이 저장소에는 상태를 적지 않는다. 이유는 [plan/README.md](plan/README.md) §상태의 위치를 본다.

## 읽기 규칙

1. 작업을 시작하면 아래 "작업별 읽을 문서" 표에서 **필요한 문서만** 고른다. 전부 읽지 않는다.
2. 각 문서 front matter의 `read_when`으로 지금 읽을 문서가 맞는지 확인하고, `related`로 다음 문서를 찾는다.
3. **값**(엔드포인트, 컬럼명, 에러 코드, 토큰 만료 시간, 버전)은 `api-contract.md`·`domain-model.md`·`tech-stack.md`에서만 가져온다. `architecture.md`나 ADR의 설명 문장을 값의 근거로 쓰지 않는다.
4. 문서와 코드가 충돌하면 코드를 고치거나 문서를 개정한다. 코드에 맞춰 문서를 암묵적으로 재해석하지 않는다.
5. 문서를 인용할 때는 경로와 절 번호를 함께 적는다. 예: `domain-model.md §2.2`.
6. 결정의 **이유**가 필요하면 `adr/`를 본다. 본문 문서는 "무엇을·어떻게"만 적고 "왜"는 ADR에 있다.
7. **ID 접두어는 문서 갈래마다 다르다.** 아래 표를 보고 어느 네임스페이스인지 먼저 확인한다. 본문 문서는 "무엇을·어떻게"만 적고 "왜"는 ADR에 있다.

## ID 네임스페이스

같은 숫자라도 접두어가 다르면 **다른 것**이다. 섞어 읽지 않는다.

| 접두어 | 무엇 | 어디에 |
| --- | --- | --- |
| `MR-xx` | 회원 **기능 요구사항** | [requirements/member.md](requirements/member.md) |
| `P-xx` / `C-xx` | 게시글 / 댓글 **기능 요구사항** | [requirements/board.md](requirements/board.md) |
| `M-xx` / `B-xx` | member / board **작업 항목** | [plan/phase1.md](plan/phase1.md) |
| `I-xx` | **통합 검증** 항목 | [plan/integration.md](plan/integration.md) |
| `C001`·`M002`·`P001` 등 | **에러 코드** | [api-contract.md §7](api-contract.md) |

`M-05`(작업 항목: 회원가입)와 `MR-05`(요구사항: 토큰 재발급)처럼 숫자가 겹칠 수 있다. 계획서의 "참조" 필드에 적힌 괄호 안 ID는 **요구사항 쪽**이다.

새 접두어를 만들 때는 기존 것과 겹치지 않는지 이 표에서 확인한다.

## 작업별 읽을 문서

| 작업 | 읽을 문서 |
| --- | --- |
| 지금 할 일 고르기·상태 갱신 | 담당 저장소의 `docs/checklist.md`, [plan/README.md](plan/README.md) |
| 작업 항목의 범위·의존·완료 기준 | [plan/phase1.md](plan/phase1.md) |
| 구현·테스트·커밋 절차 | [process/dev-workflow.md](process/dev-workflow.md) |
| 프로젝트 범위·용어 확인 | [overview.md](overview.md) |
| 서비스 경계·통신·데이터 일관성 | [architecture.md](architecture.md) |
| 버전·의존성·로컬 환경 구성 | [tech-stack.md](tech-stack.md) |
| 엔티티·컬럼·인덱스 | [domain-model.md](domain-model.md) |
| 엔드포인트·요청/응답·에러 코드·토큰 Claim | [api-contract.md](api-contract.md) |
| 코드 스타일·패키지 구조·공통 코드 정책 | [conventions.md](conventions.md) |
| 인증·인가·키 관리 | [security.md](security.md) |
| 회원 기능 요구사항 | [requirements/member.md](requirements/member.md) |
| 게시판 기능 요구사항 | [requirements/board.md](requirements/board.md) |
| 성능·장애 격리·테스트 기준 | [nfr.md](nfr.md) |
| 결정의 이유 확인 | [adr/README.md](adr/README.md) |
| 리뷰·판정 | [process/review-policy.md](process/review-policy.md) |
| 워커 분배·병렬 구간 | [process/orchestration.md](process/orchestration.md) |
| 2차 범위 확인 | [plan/phase2.md](plan/phase2.md) |

## 문서 갈래

| 성격 | 문서 | 독자의 질문 |
| --- | --- | --- |
| 값 | `api-contract.md`, `domain-model.md`, `tech-stack.md` | 정확히 무엇인가 |
| 설명 | `overview.md`, `architecture.md`, `security.md`, `nfr.md` | 어떻게 동작하는가 |
| 이유 | `adr/` | 왜 그렇게 정했는가 |
| 절차 | `process/` | 어떻게 하는가 |
| 요구사항 | `requirements/` | 무엇을 만드는가 |
| 계획 | `plan/` | 어떤 순서로 만드는가 |

값과 이유가 한 문서에 섞이면 값을 값 문서로 뗀다.

## front matter

모든 문서의 첫머리에 둔다.

```yaml
---
title: 문서 제목
type: index | spec | explanation | adr | process | requirements | plan
status: rule | living | frozen | draft
version: v1
updated: 2026-09-11
read_when: "이 문서를 읽어야 하는 상황 한 문장"
related: [상대 경로 목록]
---
```

## 문서 규칙

- 파일명은 kebab-case의 `.md`다.
- 한 문서는 한 가지 목적만 갖는다.
- 절 번호는 안정적인 앵커다. 절을 옮기거나 지울 때 번호를 재사용하지 않는다.
- 표는 5열 이하로 두고 좌우 스크롤이 생기면 표를 쓰지 않는다.
- 비밀 값(키, 비밀번호, 토큰)을 적지 않는다.
- 진행 상태는 각 서비스 저장소의 `docs/checklist.md`에만 적는다. 이 저장소의 어떤 문서에도 상태를 적지 않는다.
