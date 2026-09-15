# 작업 체크리스트 — sp-docs

`D-xx`(정본 개정) 항목의 **상태 원본은 이 파일 하나뿐이다.** 다른 곳에 상태를 적지 않는다([../plan/README.md](../plan/README.md) §상태의 위치).

항목의 산출물·완료 기준·검증은 [../plan/phase1.md](../plan/phase1.md) §3에 있다.

## 상태 값

`todo` → `doing` → `review` → `done` / `blocked`

## 항목

- [ ] D-01 정본 개정 · 상태 doing · 사유: 정본 21편과 ADR 7편 개정 완료, 참조 정합성 검증 통과. **`sp-auth`의 `README.md`·`docs/checklist.md`와 세 저장소 체크리스트 재구성이 남음**

## 선행 조건

없다. D-01은 모든 구현 항목의 선행 조건이다([../plan/phase1.md](../plan/phase1.md) §1.5).

**D-01이 `done`이 되기 전에는 `AU-xx`·`M-xx`·`B-xx` 어느 것도 시작하지 않는다.** 정본에 없는 값을 정해야 하는 상황이 반드시 생기고, 그것은 §2.6 #1의 BLOCKED 사유다.
