---
title: 리뷰 정책
type: process
status: rule
version: v1
updated: 2026-09-11
read_when: "구현 결과를 리뷰하거나 정본 문서를 개정할 때"
related: [dev-workflow.md, orchestration.md]
---
# 리뷰 정책

## 1. 원칙

**작성자와 리뷰어는 달라야 한다.** 사람이든 AI 세션이든 마찬가지다. 자기가 쓴 코드를 자기가 승인하지 않는다.

| 산출물 | 리뷰 대상 | 통과 조건 |
| --- | --- | --- |
| 구현 | 정본 문서와의 정합, 테스트, 완료 기준 충족 | APPROVED + 테스트 통과 |
| 정본 문서 개정 | 결정·범위·계약과의 정합 | APPROVED |

## 2. 판정

- 결과는 `APPROVED` 또는 `CHANGES_REQUESTED` 둘 중 하나다. 중간 값을 두지 않는다
- finding은 **심각도 · 파일·라인 · 문제 · 수정 제안**을 갖는다
- 심각도는 `blocker`, `major`, `minor` 셋이다
- **blocker 또는 major가 하나라도 있으면 `CHANGES_REQUESTED`다**
- minor만 남으면 `APPROVED`로 판정하고 minor는 후속 정리로 기록한다
- `CHANGES_REQUESTED`는 작성자가 반영한 뒤 다시 판정한다. **부분 반영이나 무응답을 승인으로 해석하지 않는다**

## 3. 심각도 기준

| 심각도 | 기준 |
| --- | --- |
| blocker | 정본 문서와 어긋남, 보안 결함, 데이터 손상 가능성, [dev-workflow.md §3](dev-workflow.md)의 금지 사항 위반 |
| major | 완료 기준 미충족, 테스트 누락, 아키텍처 원칙 위반(크로스 스키마 조인, 트랜잭션 내 원격 호출 등) |
| minor | 네이밍, 주석, 사소한 중복 |

## 4. 리뷰 체크 항목

구현 리뷰에서 확인한다.

- [ ] 완료 기준을 **모두** 충족했는가
- [ ] 검증 표의 케이스가 **모두** 테스트 코드로 있는가
- [ ] 테스트가 실제로 통과하는가 (`@Disabled`·약화된 단언이 없는가)
- [ ] 값이 정본 문서와 일치하는가 (에러 코드, 컬럼명, 엔드포인트)
- [ ] 산출물 목록 밖의 파일을 건드리지 않았는가
- [ ] [../conventions.md](../conventions.md) 위반이 없는가 (Entity `@Setter`, 필드 주입 등)
- [ ] [../architecture.md §5](../architecture.md) 금지 사항 위반이 없는가
- [ ] 비밀 값이 커밋되지 않았는가

## 5. 기록

- 리뷰 보고서 파일을 저장소에 남기지 않는다
- 구현 리뷰 결과는 PR 코멘트 또는 작업 보고에 남긴다
- 문서 리뷰 결과는 **개정 자체로** 반영한다. 경위·라운드 수를 문서에 적지 않는다
- 코드 사실을 인용할 때는 파일·라인을 함께 적는다

## 6. 정본 개정

`api-contract.md`, `domain-model.md`, `tech-stack.md`, `requirements/`의 변경은 개정이다.

- front matter의 `version`과 `updated`를 올린다
- **`api-contract.md §5`(JWT Claim)는 두 서비스가 공유하는 계약이다.** 개정 시 양쪽 담당이 모두 확인한다
- 구현이 정본과 어긋나면 **코드를 고치거나 정본을 개정한다.** 코드에 맞춰 문서를 암묵적으로 재해석하지 않는다
