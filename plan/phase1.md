---
title: 1차 작업 계획
type: plan
status: living
version: v60
updated: 2026-10-18
read_when: "작업 항목의 범위·의존·완료 기준을 확인하거나 다음 할 일을 고를 때. 상태는 담당 저장소의 checklist.md를 본다"
related: [README.md, integration.md, ../process/dev-workflow.md, ../requirements/member.md, ../requirements/board.md]
---
# 1차 작업 계획

작업 항목 33개(AU 11 + M 11 + B 11)와 통합 검증 5개로 구성한다. **그 38개가 1차의 범위이고 전부 `done` 이다** — `[1차 후]` 로 표시된 항목(`M-12`·`B-12`)은 통합 검증이 찾은 것이고 **1차 완료 선언을 되돌리지 않는다**(§7). 통합 검증은 [integration.md](integration.md)에 있다.

절차는 [../process/dev-workflow.md](../process/dev-workflow.md)를 따른다. **상태는 이 문서에 적지 않는다.**

> **v4 변경 — auth 분리**: auth가 별도 서비스가 되면서([../adr/0012](../adr/0012-auth-as-separate-service.md)) `AU-01`~`AU-11`이 신설되고 **M-03·M-04·M-05·M-06·M-07·M-09의 내용이 대폭 옮겨갔다.**
>
> - **M-06·M-07은 통째로 auth로 갔다.** member 저장소에 M-06·M-07은 더 이상 없다
> - **M-01은 재개방된다.** 의존성 배정이 바뀌었다(M-01R)
> - **v3 기준으로 기억하고 있는 내용을 쓰지 말고 이 문서를 다시 읽는다**
>
> ID는 재사용하지 않는다. 비어 있는 번호(M-06·M-07)는 비워 둔다.

## 1. 단계와 워커 구성

### 1.1 두 단계

| 단계 | 항목 | 성격 |
| --- | --- | --- |
| **정본 개정** | **D-01** | 나머지 전부의 선행 조건. §3 |
| **기반** | AU-01~AU-04, **AU-03R**, M-01R~M-04, B-01~B-04 | 순차. 뒤의 모든 항목이 의존한다 |
| **기능** | AU-05~AU-11, M-05·M-08~M-11, B-05~B-09 | 기반 산출물을 **읽기만** 하고 자기 파일을 만든다 |
| **결함 수정** | **B-10**, **B-11** | **통합 검증이 찾은 결함을 고친다.** 앞의 두 단계와 달리 **완료된 항목의 산출물을 고치므로** 그 항목의 완료 기준과 충돌하지 않는지 먼저 본다(B-10이 B-08 완료 기준 1을 대체한 것이 그 예다) |

기반 단계에 **순서 의존과 공유 상태를 몰아서 제거한다.** 엔티티 도메인 메서드, 전체 경로 인가 설정, 마이그레이션, 공통 빈이 모두 여기서 끝난다.

이 구조의 값어치는 병렬화가 아니다. **작업이 앞 항목의 미완성에 걸려 멈추는 일이 없어지는 것**이다. 워커가 하나여도 이득이 있다.

```
                      D-01 정본 개정  (sp-docs)
                             |
      +----------------------+----------------------+
      |                      |                      |
auth 저장소            member 저장소           board 저장소
───────────            ─────────────           ────────────
AU-01 스캐폴딩  [기반]  M-01R 의존성 정정 [기반] B-01 스캐폴딩  [기반] (done)
AU-02 공통 기반 [기반]  M-02 공통 기반    [기반] B-02 공통 기반 [기반]
AU-03 도메인    [기반]  M-03 도메인 기반  [기반] B-03 도메인    [기반]
AU-04 보안      [기반]  M-04 보안 기반    [기반] B-04 보안      [기반]
──────────────────     ──────────────────      ──────────────────
AU-05 계정 생성 [기능]  M-05 프로필 등록  [기능] B-05 글 작성·상세 [기능]
AU-06 로그인    [기능]  M-08 내 프로필    [기능] B-06 목록·검색    [기능]
AU-07 재발급·로그아웃   M-09 프로필 탈퇴  [기능] B-07 수정·삭제    [기능]
AU-08 비밀번호 변경     M-10 프로필·내부API      B-08 댓글         [기능]
AU-09 계정 탈퇴         M-11 마무리       [기능] B-09 내가 쓴 글·마무리
AU-10 계정 조회
AU-11 마무리
      \                      |                      /
       \_________ I-01 ~ I-05 통합 검증 __________/
                              |
                   B-10 comment_count 소실 [결함 수정]
                   (I-03 이 찾았다. 1차 완료 전에 done)
                   B-11 조회수가 집계를 덮어쓴다 [결함 수정]
                   (B-10 이 찾았다)
```

**M-06·M-07은 없다.** 로그인·재발급·로그아웃이 auth로 옮겨가 `AU-06`·`AU-07`이 됐다. 번호는 재사용하지 않는다.

### 1.2 워커 구성 — 저장소별 1개로 시작

**D-01이 끝난 뒤 구현 워커 3개로 진행한다.** 저장소마다 하나다.

세 저장소는 완전히 병렬이다. 소스가 겹칠 수 없고, 계약이 [../api-contract.md](../api-contract.md) §5(내부 API)·§6(JWT Claim)에 확정되어 있어 서로를 기다리지 않는다.

- **AU-04(JWT 발급)를 M-04·B-04(JWT 검증)가 기다리지 않는다.** 검증 측은 테스트용 키 페어로 자체 검증하고 실제 키 교환은 I-01에서 한다
- **B-05(글 작성)가 M-10(내부 API)을 기다리지 않는다.** board는 스텁으로 `MemberClient`를 테스트하고 실제 연동은 I-01에서 확인한다. 기다리면 board 전체가 member의 임계 경로에 묶인다

**저장소 안에서 워커를 더 늘리지 않는다.** auth 분리로 member 트랙과 auth 트랙이 **저장소 단위로 갈라졌으므로**, 한 저장소를 다시 쪼갤 이유가 사라졌다.

**확대는 측정 후에 정한다.** 한 사이클을 돌려 병합·전체 테스트·리뷰에 실제 몇 분이 드는지 재고, 그 비용이 절약분보다 크면 그대로 둔다.

**확대는 측정 후에 정한다.** 한 사이클을 돌려 병합·전체 테스트·리뷰에 실제 몇 분이 드는지 재고, 그 비용이 절약분보다 크면 그대로 둔다.

### 1.3 워크트리의 주된 쓰임 — 구현 ∥ 리뷰

구현 워커가 2개뿐이어도 워크트리는 값어치가 있다. **리뷰 워커를 동시에 돌리는 것**이다.

```
구현 워커:  M-05 ──> M-06 ──> M-07 ──> ...
리뷰 워커:        M-05 리뷰 ──> M-06 리뷰 ──> ...
```

리뷰 워커는 읽기만 하므로 충돌이 구조적으로 불가능하고, [../process/review-policy.md §1](../process/review-policy.md)의 작성자≠리뷰어 요구를 자동으로 만족한다. 구현 워커를 늘리는 것보다 위험 대비 효용이 크다.

### 1.4 병합 순서

같은 저장소에서 두 워커를 돌릴 경우에만 해당한다. **현재 구성(저장소당 1개)에서는 해당 없다.**

돌리게 된다면 먼저 병합할 트랙을 미리 정한다. 순서를 정하지 않으면 양쪽이 서로를 기다린다.

병합 후에는 반드시 전체 테스트를 다시 돌린다. 각자의 워크트리에서 통과했어도 합친 뒤 깨질 수 있다.

### 1.5 선행 조건 — D-01 정본 개정

**D-01이 끝나기 전에는 어떤 구현 항목도 시작하지 않는다.**

auth 분리가 정본 21편에 걸쳐 있고, §2.6 #1이 "정본에 없는 값을 정해야 하면 BLOCKED"이기 때문이다. 개정 없이 M-02를 집으면 완료 기준 1번("`ErrorCode`가 [../api-contract.md §8](../api-contract.md)과 정확히 일치")에서 즉시 멈춘다 — auth 접두어가 §8에 없다.

| 항목 | 내용 | 저장소 |
| --- | --- | --- |
| **D-01** | 정본 21편 + ADR 7편 개정, `sp-auth` 저장소 문서 생성 | `sp-docs`, `sp-auth` |

D-01은 구현 항목이 아니므로 리뷰 게이트의 대상은 같지만 테스트 대신 **참조 정합성 검증**으로 완료를 판정한다 — `python tools/check_refs.py`다([../process/review-policy.md §8](../process/review-policy.md)).

## 2. 경로 소유

이 표는 **어느 항목이 무엇을 만드는지**를 적은 지도다. 두 가지 용도가 있고, 강제 수준이 다르다.

| 용도 | 언제 | 강제 |
| --- | --- | --- |
| 문서 — 어디를 봐야 하는지 | 항상 | 없음 |
| 충돌 방지 — 남의 파일을 건드리지 않기 | **여러 워커를 동시에 돌릴 때만** | 강함 |

**저장소당 워커가 하나면(현재 구성) 경로를 넘는 것 자체는 문제가 아니다.** 순차로 진행하므로 충돌할 상대가 없다. 다만 §2.6의 세 가지는 워커 수와 무관하게 지킨다.

### 2.1 기반이 만들고 기능이 읽는 것

아래는 기반 단계에서 완성된다. **기능 단계는 읽기만 하고 수정하지 않는다.**

| 경로 | 소유 | 기능 단계의 접근 |
| --- | --- | --- |
| `build.gradle`, `settings.gradle`, `.gitignore` | AU-01 / M-01R / B-01 | 읽기 전용 |
| `global/common/`, `global/error/` | AU-02 / M-02 / B-02 | 읽기 전용 |
| `global/config/` 전부 (`SecurityConfig` 포함) | AU-04 / M-04 / B-04 | 읽기 전용 |
| `global/security/` 전부 | AU-04 / M-04 / B-04 | 읽기 전용 |
| `*/entity/`, `*/repository/`, `*/support/` | AU-03 / M-03 / B-03 | 읽기 전용 |
| `db/migration/V1`, `V2` | AU-03 / M-03 / B-03 | 읽기 전용 (member는 V1만, §2.4) |
| `client/MemberClient` | B-04 | B-05·B-08이 호출만 한다 |

기능 단계는 이 경로를 **읽기만 하는 것이 기본**이다. 고쳐야 한다면 자기 항목의 범위가 맞는지 먼저 확인하고, 맞으면 고친 뒤 보고에 적는다. 판단이 서지 않으면 §2.6을 본다.

### 2.2 기능 단계의 경로 소유

| 경로 | 저장소 | 소유 항목 |
| --- | --- | --- |
| `account/dto/`, `account/service/`, `account/controller/` | auth | AU-05, AU-08, AU-09, AU-10 (§2.3) |
| `auth/dto/`, `auth/service/`, `auth/controller/` | auth | AU-06, AU-07 |
| `db/migration/V3__seed_admin_account.sql` | auth | AU-05 |
| `member/dto/`, `member/service/`, `member/controller/` | member | M-05, M-08, M-09, M-10 (§2.3) |
| `db/migration/V2__seed_admin_profile.sql` | member | M-05 |
| `internal/` | member | M-10 |
| `post/dto/`, `post/service/`, `post/controller/` | board | B-05, B-06, B-07, B-09 (§2.3) |
| `post/repository/PostQueryRepository` | board | B-06 |
| `comment/dto/`, `comment/service/`, `comment/controller/` | board | B-08 |

### 2.3 공유 지점

기반 확대 후 남은 것은 아래 셋뿐이다.

| 파일 | 생성 | 확장 | 규칙 |
| --- | --- | --- | --- |
| `account/service/AccountService`, `account/controller/AccountController` | AU-05 | AU-08, AU-09, AU-10 | auth는 단일 워커이므로 순차 |
| `auth/service/AuthService`, `auth/controller/AuthController` | AU-06 | AU-07 | 같음 |
| `member/service/MemberService`, `member/controller/MemberController` | M-05 | M-08, M-09, M-10 | member는 단일 워커이므로 순차 |
| `post/service/PostService`, `post/controller/PostController` | B-05 | B-06, B-07, B-09 | board는 단일 워커이므로 순차 |
| `docs/checklist.md` | - | 모든 항목 | 자기 줄만 ([../process/orchestration.md §6](../process/orchestration.md)) |

**v1에서 이 표에 있던 `SecurityConfig`·`build.gradle`·`db/migration`은 기반 단계로 옮겨져 사라졌다.** 근거는 각각 M-04(전체 경로 인가 선반영), M-01(의존성 확정), M-03(V1·V2 통합)이다.

**`RefreshTokenRepository`는 더 이상 공유 지점이 아니다.** auth 저장소 안에서 `auth`와 `account`가 같이 쓰며, 단방향 제약을 두지 않는다([../conventions.md §1.1](../conventions.md)).

`member/dto/`와 `post/dto/`는 여러 항목이 쓰지만 **각자 새 파일만 추가**하므로 공유 지점이 아니다. 기존 DTO 파일을 수정해야 한다면 자기 항목의 범위가 맞는지 확인하고 진행한다.

> **이 표가 완전하다고 보증하지 않는다.** 여러 워커를 동시에 돌릴 때 목록 밖의 파일에서 충돌이 났다면 (a) 누군가 경계를 넘었거나 (b) 이 표가 빠뜨린 것이다. **워커의 잘못으로 단정하지 않는다.**

### 2.4 마이그레이션 번호

Flyway 버전은 서비스마다 하나의 순번이다. 번호는 계획이 배정한다. **워커가 스스로 정하지 않는다.**

| 서비스 | 기반 | 기능 |
| --- | --- | --- |
| **auth** | `V1__create_account.sql`, `V2__create_refresh_token.sql` (AU-03) | `V3__seed_admin_account.sql` (AU-05)<br>`V4__widen_refresh_token.sql` (**AU-03R**) |
| **member** | `V1__create_member.sql` (M-03) | `V2__seed_admin_profile.sql` (M-05) |
| board | `V1__create_post.sql`, `V2__create_comment.sql` (B-03) | 없음 |

> **member의 번호 의미가 바뀌었다.** v3에서 `V2`는 `create_refresh_token`이었으나, 그 테이블이 auth로 옮겨가면서 `V2`가 seed가 됐다. **코드가 아직 없으므로 무해하지만, v3 기준으로 기억한 번호를 쓰지 않는다.**

**적용된 마이그레이션을 고치지 않는다.** Flyway가 체크섬을 보관하므로 이미 적용된 파일을 수정하면 다음 기동이 실패한다. `V2`의 컬럼 폭을 바꿔야 할 때도 `V2`를 고치지 않고 `V4`를 새로 쓴다(AU-03R).

**ADMIN seed는 두 스키마에 걸친다.** `AU-05`의 `account.id`를 명시적으로 고정하고, `M-05`의 `V2__seed_admin_profile.sql`이 그 값을 `account_id`로 쓴다. AUTO_INCREMENT에 맡기면 두 값이 어긋난다([../requirements/member.md §10](../requirements/member.md)). 일치 여부는 I-01에서 확인한다.

배정되지 않은 마이그레이션이 필요하면 임의로 번호를 붙이지 말고 BLOCKED로 보고한다(§2.6).

### 2.5 다른 항목의 산출물을 고쳐야 할 때

**저장소당 워커가 하나면 고쳐도 된다.** 자기 작업 항목을 끝내는 데 필요한 변경이면 진행하고, 무엇을 왜 고쳤는지 보고에 적는다. 리뷰어가 범위가 타당한지 판단한다.

다만 **완료된 항목의 완료 기준을 깨뜨리는 변경은 하지 않는다.** 예를 들어 M-01의 완료 기준에 "`.gitignore`에 `private.pem`이 있다"가 있으므로 그 줄을 지우면 안 된다. 그런 변경이 필요하다면 계획 자체가 틀린 것이므로 §2.6으로 간다.

**여러 워커를 동시에 돌릴 때**는 이야기가 다르다. 다른 워커가 쓰고 있는 파일을 고치면 병합에서 충돌한다. 그때는 진행하지 말고 오케스트레이터에게 보고한다.

**미리 정해둔 것 둘** — 판단할 필요 없다.

| 상황 | 처리 |
| --- | --- |
| AU-08·AU-09가 `RefreshTokenRepository`를 참조해야 함 | 같은 저장소 안이므로 허용한다. 단방향 제약을 두지 않는다([../conventions.md §1.1](../conventions.md)) |
| B-07(게시글 삭제)이 댓글을 연쇄 삭제해야 함 | B-03이 `CommentRepository.softDeleteByPostId()`를 미리 만든다. B-08을 기다리지 않는다 |
| B-05·B-08이 `MemberClient`를 써야 함 | B-04가 미리 만든다. M-10(제공 측)을 기다리지 않고 스텁으로 테스트한다 |
| AU-03 / M-03 / B-03이 `build.gradle`·`application-test.yml`을 고쳐야 함 | 산출물 목록에 이미 적혀 있다 |

### 2.6 그래도 멈춰야 하는 세 가지

워커 수와 무관하게, 아래는 추측으로 진행하지 말고 BLOCKED로 보고한다([../process/dev-workflow.md §5](../process/dev-workflow.md)).

| # | 상황 | 왜 |
| --- | --- | --- |
| 1 | **정본에 없는 값을 정해야 함** | 엔드포인트·에러 코드·컬럼·만료 시간 등. 임의로 정하면 정본과 어긋난 구현이 된다 |
| 2 | **완료된 항목의 완료 기준을 깨야 함** | 계획이 틀렸다는 뜻이다. 코드가 아니라 계획을 고쳐야 한다 |
| 3 | **마이그레이션 번호가 배정되지 않음** | §2.4. 임의로 붙이면 병렬 작업에서 겹친다 |

**이 셋이 아니면 멈추지 않는다.** 경계를 넘는 것 자체는 보고 사유이지 중단 사유가 아니다.

> **#2의 선례** — M-01이 `done`인 상태에서 auth 분리로 의존성 배정(`tech-stack.md` §3.2)이 바뀌었다. 이것이 정확히 #2에 해당하며, 계획은 M-01을 수정하는 대신 **`M-01R`을 신설해** 처리했다(§4). 같은 상황이면 같은 방식으로 보고한다.

## 3. D-01 정본 개정 [선행]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-docs`, `yuno110/sp-auth` |
| 의존 | 없음 |
| 참조 | [../adr/0012](../adr/0012-auth-as-separate-service.md) |

**모든 구현 항목의 선행 조건이다.** §1.5를 본다.

**산출물**

| 대상 | 내용 |
| --- | --- |
| 정본 21편 | auth 분리 반영. `frozen` 5편(`api-contract`, `domain-model`, `tech-stack`, `requirements/member`, `requirements/board`) 포함 |
| ADR | 0012 신규, 0006 `superseded`, 0001·0002·0003·0007·0010 개정, `adr/README.md` 목록 갱신 |
| `sp-auth` | `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/checklist.md` |
| `sp-member`·`sp-board` | `docs/checklist.md` 재구성 (선행 조건 절, 항목 목록) |

**완료 기준**
- [ ] `adr/0006`의 `status`가 `superseded`이고 `adr/README.md` 목록에 반영되어 있다
- [ ] `api-contract.md` §8에 auth 에러 코드(`AU0xx`)와 board `S002`가 등록되어 있다
- [ ] `domain-model.md`에 `account` 테이블과 `member.account_id`가 있다
- [ ] `tech-stack.md` §3.2의 의존성 배정이 세 서비스로 되어 있고, §4.1이 `sp_auth`를 생성한다
- [ ] `README.md` ID 네임스페이스에 `AU-xx`가 있고 `A-xx` 금지가 명시되어 있다
- [ ] 문서 간 `§N.N` 참조가 전부 실재하는 절을 가리킨다
- [ ] `nickname` claim을 전제한 서술이 남아 있지 않다
- [ ] 폐기된 MR-08의 "새 토큰 반환"이 네 문서 전부에서 정리되어 있다

**검증** — 테스트 대신 참조 정합성으로 판정한다

| 케이스 | 기대 결과 |
| --- | --- |
| 전 문서 `§N.N` 상호 참조 검사 | 깨진 참조 0건 |
| `adr/0006` 링크 검사 | 현행 결정으로 인용하는 곳 0건 |
| `nickname` claim 전수 검색 | "없다"는 서술 외 0건 |
| `M002`·`M004`·`M005` 전수 검색 | member 코드표에 없고, 이동 기록만 남음 |

---

## 4. auth-service 작업 항목

**신규 저장소다.** M-03·M-04·M-06·M-07·M-09의 내용 상당 부분이 여기로 옮겨왔다.

### AU-01 프로젝트 스캐폴딩 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | D-01 |
| 참조 | [../tech-stack.md §1 §3](../tech-stack.md), [../conventions.md §1.1](../conventions.md) |

**산출물**
- `build.gradle`, `settings.gradle`, Gradle Wrapper
- `src/main/java/com/example/auth/AuthApplication.java`
- `src/main/resources/application.yml`, `application-local.yml.example`
- `.gitignore` (`private.pem`, `application-local.yml`, `*.env`, `build/`, `.gradle/`, QueryDSL 생성 경로)

**프로젝트 생성은 [../tech-stack.md §1.1](../tech-stack.md) 절차를 따른다.** start.spring.io는 Boot 3.x를 주지 않으므로 4.0.8로 생성한 뒤 3.5.16으로 내리고 의존성 이름을 3.x용으로 다시 쓴다.

**의존성을 여기서 전부 확정한다.** auth는 [../tech-stack.md §3.2](../tech-stack.md)에 따라 **서명(`oauth2-jose`)과 검증(`oauth2-resource-server`) 둘 다** 필요하다.

**완료 기준**
- [ ] `./gradlew build`가 성공한다
- [ ] Boot 플러그인 버전이 `3.5.16`이다
- [ ] `spring-boot-starter-webmvc` 등 Boot 4 스타터 이름이 남아 있지 않다
- [ ] `./gradlew bootRun`으로 **8083** 포트에 기동된다
- [ ] [../tech-stack.md §3.1 §3.2](../tech-stack.md)의 의존성이 전부 선언되어 있다 (**`oauth2-jose` 포함**)
- [ ] DB 접속 정보가 환경변수로 외부화되어 있고 스키마가 `sp_auth`다
- [ ] `.gitignore`에 **`private.pem`**, `application-local.yml`, `*.env`가 있다
- [ ] `gradlew`에 실행 권한이 있다

**검증** — `AuthApplicationTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 컨텍스트 로딩 | 예외 없이 기동 |
| `git check-ignore private.pem` | 무시됨 |

---

### AU-02 공통 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-01 |
| 참조 | [../api-contract.md §7 §8.1 §8.4](../api-contract.md), [../domain-model.md §1.1](../domain-model.md), [../conventions.md §6 §7](../conventions.md) |

**산출물**
- `global/common/ApiResponse.java`, `ErrorResponse.java`, `PageResponse.java`
- `global/common/BaseTimeEntity.java`
- `global/error/ErrorCode.java` (C001~C005, A001~A004, **AU001~AU004**)
- `global/error/BusinessException.java`, `GlobalExceptionHandler.java`
- `global/config/JpaConfig.java` (`@EnableJpaAuditing`), `SwaggerConfig.java`

복제 대상 파일 상단에 정본 주석을 남긴다([../conventions.md §7.1](../conventions.md)). **복제본이 3벌이 되므로** 형식 일치는 I-04에서 3자 비교한다.

**완료 기준**
- [ ] `ErrorCode`의 코드·HTTP 상태·메시지가 [../api-contract.md §8](../api-contract.md)과 정확히 일치한다
- [ ] **`M002`·`M004`·`M005`를 쓰지 않는다.** `AU002`·`AU003`·`AU004`다
- [ ] `BusinessException`을 던지면 해당 코드의 HTTP 상태와 응답 본문이 나온다
- [ ] `@Valid` 검증 실패가 `C001`로 변환되고 `fieldErrors`에 필드별 메시지가 담긴다
- [ ] 응답 본문에 스택트레이스·SQL이 포함되지 않는다
- [ ] **springdoc이 OpenAPI 문서를 생성한다.** `/v3/api-docs`가 문서를 돌려주고 `SwaggerConfig`가 등록된다
- [ ] `/swagger-ui.html`이 **인증 없이** 열리는 것은 이 항목의 기준이 아니다. `SecurityConfig`가 없으면 Boot 기본 필터가 전 경로를 401로 막는다([../security.md §5.1.1](../security.md)). 보안 기반 항목에서 확인한다

**검증** — `GlobalExceptionHandlerTest` (`@WebMvcTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| `BusinessException(AU002)` | 409, `error.code = "AU002"` |
| `BusinessException(A004)` | 403, `A004` |
| `@Valid` 실패 | 400, `C001`, `fieldErrors` 비어있지 않음 |
| 성공 응답 | `success = true`, `error = null` |
| 예상치 못한 `RuntimeException` | 500, `C005`, 스택트레이스 없음 |

---

### AU-03 도메인 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-02 |
| 참조 | [../domain-model.md §1 §2](../domain-model.md), [../conventions.md §2](../conventions.md), [../requirements/member.md §3 §6](../requirements/member.md) |

**두 엔티티와 도메인 메서드를 여기서 전부 만든다.**

**산출물**
- `account/entity/Account.java`, `Role.java`
- `account/repository/AccountRepository.java`
- `account/support/AccountReader.java` (find or throw — `AU001`)
- `auth/entity/RefreshToken.java`
- `auth/repository/RefreshTokenRepository.java`
- `db/migration/V1__create_account.sql`, `V2__create_refresh_token.sql`
- `build.gradle` 수정 — test 태스크에 `systemProperty 'spring.profiles.active', 'test'` ([../tech-stack.md §5.1](../tech-stack.md))
- `src/test/resources/application-test.yml` — `spring.jpa.hibernate.ddl-auto: validate` 명시

**`Account`의 도메인 메서드** — 전부 이 항목에서 구현한다.

| 메서드 | 동작 |
| --- | --- |
| `changePassword(String encoded)` | 해시된 비밀번호로 교체 |
| `withdraw()` | `deleted = true` |
| `isActive()` | `!deleted` |

**`RefreshTokenRepository`의 회전 연산** — 경합을 막는 지점이다([../requirements/member.md §6](../requirements/member.md)).

| 메서드 | 요구 |
| --- | --- |
| `rotate(...)` 또는 동등한 연산 | **조건부 UPDATE로 affected rows를 확인한다.** 0행이면 실패로 처리 |
| `deleteByAccountId(Long)` | 로그아웃·비밀번호 변경·탈퇴가 쓴다 |

**완료 기준**
- [ ] 기동 시 Flyway가 `account`, `refresh_token` 테이블을 생성한다
- [ ] 컬럼 타입·길이·NULL 여부가 [../domain-model.md §2](../domain-model.md)와 일치한다
- [ ] `account.email`, `refresh_token.account_id`, `refresh_token.token`에 UNIQUE 제약이 있다
- [ ] `created_at`, `updated_at`이 `DATETIME`이고 자동 기록된다
- [ ] `role`이 문자열(`USER`/`ADMIN`)로 저장된다
- [ ] 위 표의 도메인 메서드 3개가 모두 구현되어 있다
- [ ] `AccountReader`가 없는 id 조회 시 `BusinessException(AU001)`을 던진다
- [ ] **회전 연산이 조건부 UPDATE이고 affected rows를 확인한다**
- [ ] Entity에 `@Setter`·`@Data`가 없다
- [ ] **`@DataJpaTest` 클래스에 `@AutoConfigureTestDatabase(replace = NONE)`이 붙어 있다** ([../tech-stack.md §5.2](../tech-stack.md))
- [ ] **테스트 DataSource URL이 [../tech-stack.md §5.3](../tech-stack.md)의 정본과 일치한다** — `DATABASE_TO_LOWER`·`CASE_INSENSITIVE_IDENTIFIERS`·`DB_CLOSE_DELAY=-1` 포함
- [ ] **테스트가 그 URL로 돈다.** `jdbc:h2:mem:<uuid>`가 아니다
- [ ] **`ddl-auto: validate`가 실제로 적용된다.** 엔티티에만 있는 컬럼을 넣는 변이에서 `SchemaManagementException`으로 기동이 실패하는 것으로 확인한다 — **검증표에 넣지 않는다**(테스트가 자기 엔티티를 바꿀 수 없다, [../process/review-policy.md §5.3](../process/review-policy.md))

**검증** — `AccountRepositoryTest`, `RefreshTokenRepositoryTest` (`@DataJpaTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| 저장 후 조회 | 모든 필드 일치 |
| 중복 email 저장 | `DataIntegrityViolationException` |
| 저장 시 | `createdAt`, `updatedAt` null 아님 |
| `role` / `deleted` 미지정 저장 | `USER` / `false` |
| `changePassword()` 호출 | 비밀번호만 변경 |
| `withdraw()` 호출 | `deleted = true`, 행 존재 |
| 같은 `account_id`로 refresh token 2개 저장 | `DataIntegrityViolationException` |
| **이미 삭제된 행에 회전 시도** | **0행 갱신 → 실패로 처리** |
| `AccountReader`로 없는 id 조회 | `BusinessException(AU001)` |
| 테스트 실행 중 DataSource URL | [../tech-stack.md §5.3](../tech-stack.md)의 정본과 문자열 일치 |
| 저장된 테이블명 | **소문자** `account`·`refresh_token`. `DATABASE_TO_LOWER` 효과 |

---

### AU-03R 토큰 컬럼 폭 정정 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-03 |
| 참조 | [../domain-model.md §2.2](../domain-model.md), [../conventions.md §9.2](../conventions.md) |

**AU-03의 완료 기준이 깨졌다.** `refresh_token.token`이 `VARCHAR(512)`인데 **이 서비스가 발급하는 토큰은 541~557자**다. AU-06에서 로그인이 `Value too long for column`으로 끊겨 드러났다.

§2.6 #2(완료된 항목의 완료 기준을 깨야 할 때)에 해당하므로 AU-03을 수정하지 않고 후속 항목으로 처리한다. `M-01R`과 같은 방식이다.

**`V2`를 고치지 않는다.** 이미 적용되어 Flyway가 체크섬을 보관하므로 수정하면 다음 기동이 실패한다. 새 마이그레이션을 쓴다(§2.4가 `V4`를 배정했다).

**산출물**
- `db/migration/V4__widen_refresh_token.sql` — 테이블을 ascii 로 바꾼 **뒤** `token`을 `VARCHAR(1024)`로. **순서가 뒤집히면 `ERROR 1071`이다.** 컬럼 단위 `CHARACTER SET` 구문은 H2가 거부한다 ([../domain-model.md §2.2](../domain-model.md))
- `auth/entity/RefreshToken.java` — `@Column(length = ...)` 갱신
- `auth/repository/RefreshTokenRepositoryTest` — 픽스처를 실제 길이로

**완료 기준**
- [ ] `token`이 `VARCHAR(1024)`이고 테이블 문자셋이 `ascii`다 ([../domain-model.md §2.2](../domain-model.md))
- [ ] **마이그레이션이 MySQL 과 H2 양쪽에서 돈다.** 테스트가 같은 스크립트를 쓴다
- [ ] `uk_refresh_token` UNIQUE 제약이 유지된다
- [ ] **`V2`를 수정하지 않았다.** 기존 `flyway_schema_history`와 체크섬이 맞는다
- [ ] 엔티티의 `length`가 마이그레이션과 일치한다 (`ddl-auto: validate`가 통과한다)
- [ ] **리포지토리 테스트가 실제 발급 토큰 길이의 값으로 저장을 확인한다** ([../conventions.md §9.2](../conventions.md))
- [ ] AU-03의 나머지 완료 기준이 여전히 충족된다

**검증** — `RefreshTokenRepositoryTest`

| 케이스 | 기대 결과 |
| --- | --- |
| **557자 토큰 저장** | 성공. 조회값이 입력과 같다 |
| **898자 토큰 저장** | 성공 — 4096비트 키로 회전해도 들어간다 |
| 1025자 토큰 저장 | 실패 (길이 제약이 실재한다) |
| 같은 토큰 2건 저장 | `DataIntegrityViolationException` (`uk_refresh_token` 유지) |
| 기동 시 Flyway | `V1`~`V4` 적용, 체크섬 오류 없음 |
| `ddl-auto: validate` | 통과 (엔티티와 스키마 일치) |

---

### AU-04 보안 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-03 |
| 참조 | [../security.md](../security.md) 전체, [../api-contract.md §2 §6](../api-contract.md), [../tech-stack.md §3.2 §4.2](../tech-stack.md) |

**이 서비스만 개인키를 갖는다.** 토큰 발급의 유일한 주체다.

**산출물**
- `global/config/JwtConfig.java` (개인키 로딩, `kid`)
- `global/security/JwtTokenProvider.java` (`NimbusJwtEncoder`)
- `global/config/SecurityConfig.java` — **[../api-contract.md §2](../api-contract.md)의 전체 경로 인가**, `PasswordEncoder` 빈, CORS, STATELESS
- `global/security/LoginAccount.java`, `@CurrentAccount` ArgumentResolver
- `auth/dto/TokenResponse.java`
- `application.yml`에 토큰 만료 시간

**⚠ Claim에 `nickname`을 넣지 않는다.** auth는 닉네임을 소유하지 않는다([../api-contract.md §6](../api-contract.md)). 넣으면 소유하지 않은 값을 서명하는 것이 된다.

**⚠ 경로 선언 순서** — `/api/v1/accounts/me`(인증)와 `/api/v1/accounts`(무인증, POST)가 접두어를 공유한다. `requestMatchers`는 **먼저 선언된 규칙이 이기므로** `/accounts/me`를 먼저 선언한다.

**의존성 빈 선제 준비** — `AccountService`·`AuthService`가 쓸 빈(`AccountRepository`, `AccountReader`, `PasswordEncoder`, `JwtTokenProvider`, `RefreshTokenRepository`)이 이 항목 완료 시점에 전부 존재해야 한다.

**완료 기준**
- [ ] 발급된 토큰의 Claim이 [../api-contract.md §6](../api-contract.md)과 정확히 일치한다
- [ ] **`nickname` claim이 없다**
- [ ] `sub`가 `account.id`의 문자열이고 `iss`가 `auth-service`다
- [ ] 서명 알고리즘이 RS256이고 header에 `kid`가 있다
- [ ] Access Token 만료 30분, Refresh Token 14일
- [ ] 개인키가 외부에서 주입되며 **기본값이 없다** (없으면 기동 실패)
- [ ] **개인키 파일이 커밋되지 않았다**
- [ ] jjwt 의존성을 사용하지 않는다
- [ ] [../api-contract.md §2](../api-contract.md)의 **모든 경로**에 인가 규칙이 선언되어 있다
- [ ] **`/accounts/me`가 `/accounts`보다 먼저 선언되어 있다**
- [ ] **`/swagger-ui/**`·`/v3/api-docs/**`가 `permitAll`이고 인증 없이 열린다** ([../security.md §5.1.1](../security.md))
- [ ] `/actuator/health` 외의 actuator 경로가 노출되지 않는다
- [ ] 세션이 생성되지 않는다
- [ ] CORS 설정에 `*`가 없다

**검증** — `JwtTokenProviderTest`, `SecurityConfigTest` (`@SpringBootTest` + MockMvc)

| 케이스 | 기대 결과 |
| --- | --- |
| Access Token 발급 후 디코딩 | `sub`, `role`, `iss` 일치 |
| **디코딩한 Claim 집합** | **`nickname` 키 없음** |
| 토큰 header | `alg = RS256`, `kid` 존재 |
| Access Token `exp - iat` | 1800초 |
| Refresh Token `exp - iat` | 1209600초 |
| 공개키로 서명 검증 | 통과 |
| payload 변조 후 검증 | 실패 |
| 개인키 없이 기동 | 기동 실패 |
| **토큰 없이 `GET /api/v1/accounts/me`** | **401 `A001`** |
| 토큰 없이 `POST /api/v1/accounts` | 401이 아님 |
| 토큰 없이 `POST /api/v1/auth/login` | 401이 아님 |
| **토큰 없이 `/swagger-ui.html`** | **302 → `/swagger-ui/index.html`.** `/login` 으로 가면 실패 |
| **토큰 없이 `/swagger-ui/index.html`** | **200** |
| **토큰 없이 `/v3/api-docs`** | **200, OpenAPI 문서** |
| 응답 헤더 | `Set-Cookie` 세션 쿠키 없음 |

---

### AU-05 계정 생성과 이메일 중복 확인 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-04 |
| 참조 | [../requirements/member.md §1 §2 §4 §10](../requirements/member.md) (MR-01 1단계, MR-02), [../api-contract.md §2.2 §9.1](../api-contract.md) |

**산출물**
- `account/dto/AccountCreateRequest.java`, `AccountResponse.java`, `CheckResponse.java`
- `account/service/AccountService.java` (생성)
- `account/controller/AccountController.java` (생성)
- `db/migration/V3__seed_admin_account.sql` — 값은 [../requirements/member.md §10.1](../requirements/member.md)이 정본. **해시는 Flyway placeholder로 주입하고 커밋하지 않는다**(§10.2)
- `application.yml`에 `spring.flyway.placeholders.adminPasswordHash: ${ADMIN_PASSWORD_HASH}` (기본값 없음)
- `build.gradle`에 `bcrypt` 태스크 ([../tech-stack.md §4.2.1](../tech-stack.md))
- `global/config/FlywayConfig.java` — `adminPasswordHash` 가드. **`global/config/`는 AU-04 소유지만 이 항목이 새 빈을 추가한다**(§2.5). YAML만으로는 기동이 실패하지 않으므로 필요하다([../requirements/member.md §10.2](../requirements/member.md))

**완료 기준**
- [ ] `POST /api/v1/accounts`가 201과 `{accountId, email}`을 반환한다
- [ ] **응답에 `password`가 포함되지 않는다**
- [ ] 비밀번호가 BCrypt로 해싱되어 저장된다
- [ ] 중복 이메일 409 `AU002`
- [ ] 검증 규칙이 [../requirements/member.md §2](../requirements/member.md)와 일치한다
- [ ] `GET /api/v1/accounts/check-email`이 동작한다
- [ ] **탈퇴 계정의 이메일로 재가입할 수 없다** (409 `AU002`)
- [ ] `GET /api/v1/accounts/check-email`의 응답이 `{ "available": boolean }`이다 ([../api-contract.md §2.3](../api-contract.md))
- [ ] **탈퇴 계정의 이메일은 `available: false`다**
- [ ] **seed의 `account.id`가 `1`로 명시되어 있다.** AUTO_INCREMENT에 맡기지 않는다 ([../requirements/member.md §10.1](../requirements/member.md))
- [ ] **seed에 평문도 해시도 커밋되지 않았다.** `${adminPasswordHash}` placeholder다 (§10.2)
- [ ] **커밋되는 어떤 파일에도 BCrypt 모양 문자열이 없다** (§10.2). 검색 패턴은 문자 클래스로 조립해 자기 파일이 걸리지 않게 한다
- [ ] **커밋된 픽스처의 모양을 되읽는 단언이 없다** (§10.2). 런타임 생성값에 형식을 단언하는 것은 해당 없다
- [ ] **애플리케이션 `PasswordEncoder` 빈의 해시가 `$2[aby]$10$`로 시작하는지 단언한다** — `security.md` §1의 strength 10을 고정한다
- [ ] **`ADMIN_PASSWORD_HASH` 없이 기동하면 실패한다.** YAML만으로는 리터럴이 통과하므로 가드가 필요하다 ([../requirements/member.md §10.2](../requirements/member.md))
- [ ] `./gradlew bcrypt -Ppassword=...`가 해시 한 줄을 출력하고 평문을 출력하지 않는다. 인자가 없으면 실패한다 (**관측으로 충족**)
- [ ] **닉네임을 받지도 저장하지도 않는다**
- [ ] 비밀번호 특수문자 집합이 [../requirements/member.md §2.1](../requirements/member.md)과 일치한다

**검증** — `AccountServiceTest`, `AccountControllerTest`, **`AdminSeedTest`**(seed 관련 전부)

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 생성 | 201, DB 저장됨 |
| 저장된 비밀번호 | 평문과 다르고 `BCrypt.matches`로 검증됨 |
| 응답 본문 | `password` 키 없음, **`nickname` 키 없음** |
| 중복 이메일 | 409 `AU002` |
| 탈퇴 계정(`deleted=true`) 이메일로 생성 | 409 `AU002` |
| 이메일 형식 오류 | 400 `C001` |
| 비밀번호 7자 / 특수문자 없음 | 400 `C001` |
| 요청에 `nickname` 포함 | 무시되거나 400. **저장되지 않음** |
| seed 적용 후 `SELECT id FROM account WHERE role='ADMIN'` | **`1`** |
| seed 적용 후 ADMIN 이메일 | `admin@example.com` |
| **`ADMIN_PASSWORD_HASH` 미주입으로 기동** | **기동 실패.** 가드가 던지고 **테이블이 생성되지 않는다** |
| **가드 없이 미주입으로 기동** | 마이그레이션 성공, `password = "${ADMIN_PASSWORD_HASH}"`. **이것이 가드가 필요한 이유다** |
| 미사용 이메일 중복 확인 | `{ "available": true }` |
| 사용 중 이메일 중복 확인 | `{ "available": false }` |
| **탈퇴 계정 이메일 중복 확인** | **`{ "available": false }`** |
| 한글만으로 특수문자 조건 충족 시도 (`비밀번호1234`) | 400 `C001` |
| `V3` SQL 전문 검색 | `$2a$`·`$2b$` 로 시작하는 문자열 없음 |
| **저장소 전문 검색** | **`$2[aby]$` 0건.** `git ls-files -co --exclude-standard` 전체 |
| **스캔 자기 점검** | 수집 파일 수가 0이 아니고, 패턴이 알려진 양성 샘플(`$2a$10$...`)을 잡는다. **스캔이 0개 파일을 보면 `isEmpty()`는 공허하게 통과한다** |
| **애플리케이션 `PasswordEncoder` 빈이 만든 해시** | **`$2[aby]$10$` 로 시작** — `security.md` §1의 strength 10을 고정한다. 패턴은 문자 클래스로 조립 |

---

### AU-06 로그인 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-05, **AU-03R** |
| 참조 | [../requirements/member.md §1](../requirements/member.md) (MR-04), [../security.md §4](../security.md), [../api-contract.md §9.2](../api-contract.md) |

> **AU-03R이 선행 조건이다.** 그것 없이는 발급한 Refresh Token 을 저장할 수 없다.

**산출물**
- `auth/dto/LoginRequest.java`
- `auth/service/AuthService.java` (생성)
- `auth/controller/AuthController.java` (생성)

`RefreshToken` 엔티티·리포지토리와 `TokenResponse`는 AU-03·AU-04 산출물이다. **이 항목에서 만들지 않고 쓴다.**

**완료 기준**
- [ ] `POST /api/v1/auth/login`이 200과 `TokenResponse`를 반환한다
- [ ] **발급한 Refresh Token을 `sp_auth`에 upsert한다** ([../security.md §4](../security.md), [../domain-model.md §2.2](../domain-model.md))
- [ ] **계정당 1행이다.** 재로그인하면 행이 늘지 않고 값이 교체된다
- [ ] **기존 행을 갱신한다. 삭제하고 다시 넣지 않는다.** `refresh_token.id`가 재로그인 후에도 같아야 한다 — 삭제·재삽입은 로그인마다 `id`를 증가시키고 인덱스를 흔든다
- [ ] 비밀번호 불일치·없는 이메일 **모두** 401 `AU003` (어느 쪽이 틀렸는지 노출하지 않는다)
- [ ] **응답 시간으로도 구별되지 않는다.** 계정이 없거나 탈퇴했을 때도 더미 해시로 `matches`를 한 번 수행한다 ([../security.md §4.1](../security.md))
- [ ] 더미 해시를 **상수로 커밋하지 않는다** — 기동 시 인코딩해 메모리에만 둔다
- [ ] **탈퇴 계정(`deleted = true`)은 로그인할 수 없다**
- [ ] 발급된 토큰의 `sub`·`role` Claim이 계정 정보와 일치한다
- [ ] **토큰에 `nickname` Claim이 없다**
- [ ] **프로필이 없어도 로그인이 된다.** auth는 프로필 존재를 모른다

**검증** — `AuthServiceTest`, `AuthControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 로그인 | 200, accessToken·refreshToken 존재 |
| 정상 로그인 후 `refresh_token` | **1행. 응답의 refreshToken과 저장값이 같다** |
| **같은 계정으로 재로그인** | **여전히 1행. 토큰 값이 새것으로 교체됨** |
| 로그인 실패(비밀번호 불일치) 후 `refresh_token` | **행이 생기지 않는다** |
| **재로그인 후 `refresh_token.id`** | **첫 로그인의 `id`와 같다** — 갱신이지 재삽입이 아니다 |
| **세 실패 경로의 `matches` 호출 횟수** | **각 1회.** 기계 속도와 무관하게 결정적이다 — **이쪽이 본질이다** |
| 세 실패 경로의 응답 시간 | 같은 자리수. **같은 실행에서 측정한 BCrypt 1회 비용을 기준으로** 비교한다. 단정적 임계(`< 100ms` 등)를 쓰지 않는다 — 기계 속도·GC에 흔들린다 |
| 비밀번호 불일치 | 401 `AU003` |
| 없는 이메일 | 401 `AU003` (메시지가 위와 동일) |
| **탈퇴 계정 로그인** | **401** |
| 발급 토큰의 Claim | 계정의 `id`·`role`과 일치, `nickname` 없음 |
| 유효 토큰으로 `/accounts/me` 접근 | **401이 아님** — `GET /accounts/me`는 AU-10이 만들므로 지금은 404여도 된다. 보는 것은 **토큰이 인증을 통과하는가**다 |

---

### AU-07 토큰 재발급과 로그아웃 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-06 |
| 공유 파일 | `AuthService`, `AuthController` (AU-06 생성) |
| 참조 | [../requirements/member.md §1 §6](../requirements/member.md) (MR-05, MR-06), [../security.md §4](../security.md) |

**산출물**
- `auth/dto/ReissueRequest.java`
- `AuthService`·`AuthController` 확장
- `global/security/SecurityErrorResponder` 확장 — `A002`·`A003` 구분

**`global/security/`는 AU-04 소유지만 이 항목이 확장한다.** AU-04는 필터 단계의 모든 인증 실패를 `A001`로 냈고, `A002`·`A003`의 구분은 여기 배정되어 있다(§2.5). 판단할 필요 없이 진행하고 보고에 적는다.

**경합 방지가 이 항목의 핵심이다.** 재발급은 RefreshToken 조회와 `account.deleted` 확인을 **같은 트랜잭션**에서 하고, 회전은 AU-03의 조건부 UPDATE로 처리한다. 그렇지 않으면 탈퇴와 겹칠 때 삭제한 행이 되살아나 탈퇴 계정이 14일간 갱신할 수 있다([../requirements/member.md §6](../requirements/member.md)).

**`RefreshToken.renew()`를 쓰지 않는다.** AU-06이 로그인용으로 추가한 엔티티 메서드다. 회전에 쓰면 탈퇴와 겹칠 때 지운 행이 되살아난다 — 그것이 조건부 UPDATE를 쓰는 이유다. 엔티티 javadoc에도 경고가 있다.

**`useAffectedRows=true`를 JDBC URL에 넣지 않는다.** "0행이면 실패" 판정이 found rows에 의존한다([../requirements/member.md §6.1](../requirements/member.md)).

**AU-06이 남긴 경합이 여기서 닫힌다.** 로그인은 `authenticate()` 후 탈퇴가 커밋되면 탈퇴 계정 행을 INSERT할 수 있다. **재발급이 `account.deleted`를 같은 트랜잭션에서 검사하는 한 무해하다** — 그 검사가 이 항목의 완료 기준이다.

**완료 기준**
- [ ] `POST /api/v1/auth/reissue`가 새 Access/Refresh를 반환한다
- [ ] Rotation이 적용된다 (이전 Refresh Token은 무효). **같은 초에 발급한 두 토큰이 같은 것은 1차의 알려진 한계다** ([../requirements/member.md §6.2](../requirements/member.md))
- [ ] 저장값과 다른 Refresh Token은 거부된다
- [ ] 만료·변조된 Refresh Token은 거부된다
- [ ] **탈퇴 계정은 재발급받을 수 없다**
- [ ] **조회와 `deleted` 확인이 같은 트랜잭션이다**
- [ ] **회전이 조건부 UPDATE이고 0행이면 실패한다**
- [ ] **`RefreshToken.renew()`를 쓰지 않는다**
- [ ] JDBC URL에 `useAffectedRows=true`가 없다
- [ ] `POST /api/v1/auth/logout`이 204를 반환하고 저장된 Refresh Token을 삭제한다
- [ ] 로그아웃 후 같은 Refresh Token으로 재발급이 실패한다
- [ ] **서명이 잘못된 토큰은 401 `A002`, 만료된 토큰은 401 `A003`이다** — Access Token과 Refresh Token 양쪽. AU-04는 필터 단계의 모든 인증 실패를 `A001`로 냈으므로 여기서 구분한다
- [ ] 세 코드가 [../api-contract.md §8.1](../api-contract.md)의 상태·메시지와 일치한다

**검증** — `AuthServiceTest`, `AuthControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 재발급 | 200, 새 토큰 2개 |
| 이전 Refresh Token 재사용 | 실패 |
| 저장값과 다른 토큰 | 실패 |
| 만료된 Refresh Token | 실패 |
| **탈퇴 계정의 유효 Refresh Token** | **실패** |
| **탈퇴 커밋 후 재발급 시도** | **실패. `refresh_token` 행이 되살아나지 않음** |
| **값이 같은 토큰으로 회전** | **성공.** 0행으로 떨어지면 `useAffectedRows` 설정을 확인한다 ([../requirements/member.md §6.1](../requirements/member.md)) |
| 정상 로그아웃 | 204, `refresh_token` 행 삭제됨 |
| 로그아웃 후 재발급 | 실패 |
| **서명 변조된 Access Token으로 보호 경로 접근** | **401 `A002`** |
| **만료된 Access Token으로 보호 경로 접근** | **401 `A003`** |
| 토큰 없이 보호 경로 접근 | 401 `A001` |

---

### AU-08 비밀번호 변경 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-07 |
| 공유 파일 | `AccountService`, `AccountController` (AU-05 생성) |
| 참조 | [../requirements/member.md §1 §3](../requirements/member.md) (MR-09), [../api-contract.md §2.2](../api-contract.md), [../security.md §4.1 §5.3 §7](../security.md) |

**산출물**
- `account/dto/PasswordChangeRequest.java`
- `AccountService`·`AccountController` 확장

**완료 기준**
- [ ] `PATCH /api/v1/accounts/me/password`가 204를 반환한다
- [ ] 요청 본문이 `{currentPassword, newPassword}`다 ([../api-contract.md §2.2](../api-contract.md))
- [ ] 현재 비밀번호 불일치 시 **400** `AU004` (401이 아니다 — 요청자는 이미 인증되어 있다)
- [ ] **`currentPassword`에 형식 검증을 걸지 않는다.** 틀린 형식과 틀린 비밀번호가 응답에서 갈리면 안 된다
- [ ] **새 비밀번호가 현재와 같아도 거부하지 않는다** ([../api-contract.md §2.2](../api-contract.md))
- [ ] **`currentPassword`에 `@NotBlank`는 붙인다.** 금지되는 것은 `@Pattern`이다 ([../api-contract.md §2.2](../api-contract.md))
- [ ] **탈퇴한 계정은 404 `AU001`로 거부한다.** 검사를 `AccountReader`에 두지 않는다 ([../api-contract.md §2.2](../api-contract.md))
- [ ] **더미 해시 비교를 넣지 않는다.** 이미 인증된 요청이므로 숨길 것이 없다 ([../security.md §4.1](../security.md))
- [ ] 새 비밀번호가 BCrypt로 해싱되어 저장된다 (`Account.changePassword()` 사용)
- [ ] **비밀번호 변경 시 Refresh Token이 삭제된다**
- [ ] **두 연산이 한 로컬 트랜잭션이다**

**검증** — `AccountServiceTest`, `AccountControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 변경 | 204, 새 비밀번호로 로그인 가능 |
| 현재 비밀번호 불일치 | 400 `AU004` |
| 변경 후 `refresh_token` 행 | 삭제됨 |
| 새 비밀번호 형식 오류 | 400 `C001`, `fieldErrors`에 `newPassword` |
| **`currentPassword`가 형식 위반이고 값도 틀림** | **400 `AU004`** — `C001`이 아니다. 형식으로 가르지 않는다 |
| **`currentPassword` 누락 · `null` · 빈 문자열** | **400 `C001`**, `fieldErrors`에 `currentPassword`. AU-09와 같다 |
| **새 비밀번호 형식 오류 + 현재 비밀번호 불일치 동시** | **400 `C001`** — Bean Validation이 먼저 돈다 |
| **탈퇴한 계정의 토큰으로 변경 시도** | **404 `AU001`.** `password`와 `updated_at`이 **둘 다 그대로** |
| **새 비밀번호가 현재와 같음** | **204** — 거부하지 않는다 |
| **변경 후 기존 Access Token으로 보호 경로** | **통과한다** — 만료까지 유효하다 ([../security.md §5.3](../security.md)) |
| 변경 후 기존 Refresh Token으로 재발급 | 실패 (저장값 삭제됨) |
| 변경 중 예외 발생 | 비밀번호와 토큰 **둘 다** 롤백. **두 단언이 각각 반증 가능해야 한다** ([../process/review-policy.md §4.1](../process/review-policy.md)) |
| **한 번의 호출에 커밋이 정확히 한 번** | 트랜잭션 경계를 직접 관측한다. 행위 단언으로 대체할 수 없다 |

---

### AU-09 계정 탈퇴 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-08 |
| 공유 파일 | `AccountService`, `AccountController` — **AU-08 완료 후 시작** |
| 참조 | [../requirements/member.md §1 §8](../requirements/member.md) (MR-10 **1단계**), [../architecture.md §4.4](../architecture.md) |

**탈퇴 2단계 중 1단계다.** 2단계(프로필 삭제)는 member의 M-09다. **순서를 바꾸지 않는다** — 비밀번호 재확인이 여기에만 있기 때문이다.

**산출물**
- `account/dto/WithdrawRequest.java` (현재 비밀번호)
- `AccountService`·`AccountController` 확장

**완료 기준**
- [ ] `DELETE /api/v1/accounts/me`가 204를 반환한다
- [ ] **본문의 현재 비밀번호를 재확인한다.** 불일치 시 400 `AU004`
- [ ] 본문이 `{password}`다. **`currentPassword`가 아니다** ([../api-contract.md §2.2](../api-contract.md))
- [ ] **`@NotBlank`만 붙이고 `@Pattern`은 걸지 않는다.** 누락·빈 값은 400 `C001`
- [ ] **`deleted` 검사가 비밀번호 비교보다 먼저다.** 이미 탈퇴한 계정은 비밀번호를 검증하지 않는다
- [ ] `Account.withdraw()`로 `deleted = true`가 된다 (행 삭제 아님)
- [ ] **해당 계정의 Refresh Token이 전부 삭제된다**
- [ ] **두 연산이 한 로컬 트랜잭션이다**
- [ ] **멱등이다.** 이미 탈퇴한 계정에 다시 호출해도 204
- [ ] 탈퇴 후 로그인·재발급이 실패한다
- [ ] **member를 호출하지 않는다.** 프로필 삭제는 클라이언트가 2단계로 호출한다 — 저장소에 HTTP 클라이언트가 **없다**는 관측으로 충족한다([../process/review-policy.md §5.3](../process/review-policy.md))

**검증** — `AccountServiceTest`, `AccountControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 탈퇴 | 204, `deleted = true`, 행 존재 |
| **비밀번호 없이 요청** | **400 `C001`** |
| **비밀번호 불일치** | **400 `AU004`. `deleted`가 그대로 false** |
| 탈퇴 시 `refresh_token` 행 | 삭제됨 |
| 탈퇴 후 로그인 | 401 |
| 탈퇴 후 재발급 | 실패 |
| **이미 탈퇴한 계정에 재호출 (비밀번호 맞음)** | **204** (멱등). `updated_at`이 그대로 |
| **이미 탈퇴한 계정에 재호출 (비밀번호 틀림)** | **204.** 검사가 비교보다 먼저다 ([../api-contract.md §2.2](../api-contract.md)) |
| **`sub`가 가리키는 행 부재** | **404 `AU001`.** 멱등의 대상이 아니다 |
| 탈퇴 중 예외 발생 | `deleted`와 토큰 **둘 다** 롤백. **두 단언이 각각 반증 가능해야 한다** |
| **한 번의 호출에 커밋이 정확히 한 번** | 변이 **셋**(A·B·C)을 돌린다. **C는 행위 단언으로 잡히지 않는다** ([../process/review-policy.md §4.1](../process/review-policy.md)) |

---

### AU-10 내 계정 조회 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-09 |
| 공유 파일 | `AccountService`, `AccountController` — **AU-09 완료 후 시작** |
| 참조 | [../requirements/member.md §5](../requirements/member.md) (MR-07의 계정 절반), [../api-contract.md §2.2](../api-contract.md) |

**MR-07이 두 서비스로 갈라진 절반이다.** 나머지 절반(닉네임)은 member의 M-08이다.

**산출물**
- `account/dto/AccountMeResponse.java` (이메일, 가입일)
- `AccountService`·`AccountController` 확장

**완료 기준**
- [ ] `GET /api/v1/accounts/me`가 200과 이메일·가입일을 반환한다
- [ ] 응답 필드가 `email`·`createdAt` **둘뿐이다.** `accountId`를 넣지 않는다 ([../api-contract.md §2.2](../api-contract.md))
- [ ] **읽기 전용이다.** `@Transactional(readOnly = true)`
- [ ] **응답에 `password`가 없다**
- [ ] **응답에 `nickname`이 없다.** auth는 닉네임을 모른다
- [ ] 토큰 없이 접근하면 401 `A001`
- [ ] 계정 식별은 **검증된 JWT의 `sub`**로만 한다

**검증** — `AccountControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 내 계정 조회 | 200, `email`·가입일 존재 |
| 응답 본문 | `password` 키 없음, `nickname` 키 없음 |
| 토큰 없이 접근 | 401 `A001` |
| 타인의 accountId를 본문·파라미터로 전달 | 무시됨. 자기 정보만 반환 |
| **탈퇴한 계정의 토큰으로 조회** | **404 `AU001`** ([../api-contract.md §2.2](../api-contract.md)) |
| **`sub`가 가리키는 행 부재** | **404 `AU001`.** 탈퇴와 같은 코드다 |
| **응답 키 집합** | `email`·`createdAt` **정확히 둘.** `accountId`도 없다 |
| `createdAt` 형식 | **오프셋 표기 없음.** 소수부는 선택으로 둔다 — H2 는 마이크로초를 남긴다 ([../tech-stack.md §6](../tech-stack.md)) |

---

### AU-11 마무리 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-10 |
| 참조 | [../nfr.md](../nfr.md), [../tech-stack.md §6](../tech-stack.md) |

**산출물**
- `README.md` 갱신 (실행 절차, 환경변수 목록, **키 배치 절차**)
- `JwtConfig`의 claim 검증기 집합을 고정하는 테스트 — AU-07에서 넘어온 것
- `GlobalExceptionHandler`에 **미디어 타입 예외 둘** (`C006` 415 · `C007` 406), `ErrorCode` 확장
- Actuator 설정 — **AU-01의 `management.endpoints.web.exposure.include: health`와 AU-04의 `denyAll`이 이미 한다.** 확인만 하고 중복을 만들지 않는다
- `application-prod.yml` (Swagger·SQL 로그 비활성화)

**완료 기준**
- [ ] `README.md`에 로컬 실행 절차와 필요한 환경변수가 모두 적혀 있다
- [ ] `README.md`에 **개인키 배치 절차**가 적혀 있다
- [ ] `/actuator/health`가 200 `{"status":"UP"}`이고 **그 외 엔드포인트는 노출되지 않는다.** 무토큰은 401 `A001`, 유효 토큰은 403 `A004`다 (실측) — 404가 아니다. **AU-01·AU-04가 만든 동작이고 `SecurityConfigTest`가 그 기준("노출되지 않는다")을 덮는다.** 여기서는 관측으로 확인한다
- [ ] `prod` 프로파일에서 Swagger UI가 비활성화된다
- [ ] **`springdoc.api-docs.enabled`도 끈다.** UI만 끄면 `/v3/api-docs`가 전체 엔드포인트 목록을 그대로 낸다
- [ ] `prod` 프로파일에서 SQL 로그가 꺼진다 — **`show-sql`과 `logging.level` 둘 다**. 후자가 보안 쪽이다: **바인드 파라미터 로그에는 비밀번호가 평문으로 실린다**([../nfr.md §5](../nfr.md), [../conventions.md §8](../conventions.md))
- [ ] **그 `logging.level` 블록을 지우면 테스트가 깨진다.** 루트 수준 기본이 `INFO`라 **설정이 없어도 로거는 이미 조용하다** — 효과를 보는 단언은 블록 삭제를 잡지 못한다. **속성값을 단언한다**
- [ ] 전체 테스트가 통과한다 (`./gradlew test`)
- [ ] **커밋된 파일에 개인키·비밀 값이 없다.** 아래 셋을 실행해 확인한다

| 검사 | 기대 |
| --- | --- |
| `git grep`으로 **현재 트리**의 비밀번호·BCrypt 모양 | **없음** |
| `git log -p`의 `BEGIN PRIVATE KEY` | **1건.** `TestRsaKeys`의 **PEM 헤더 문자열 리터럴**이다(`157741a`, AU-04) — 실행 시점에 만든 키를 임시 파일로 쓸 때 붙이는 것이고 **키 자료가 아니다** |
| `git log -p`의 BCrypt 모양 | **3줄.** 아래 "이력에 남은 BCrypt 모양"을 본다 |
- [ ] **미디어 타입 예외 둘을 다룬다.** `Content-Type` 누락이 500이 아니라 **415 `C006`**, `Accept` 불일치가 **406 `C007`**이다 ([../api-contract.md §8.1](../api-contract.md))
- [ ] **그 둘이 `log.error`를 남기지 않는다.** 클라이언트 실수가 ERROR 경보를 만들면 안 된다
- [ ] **`JwtConfig`가 쓰는 claim 검증기 집합이 테스트로 고정되어 있다.** AU-07의 `failureCode`가 예외 타입만 보고 `A002`·`A003`을 가르는데, 그 판정은 `JwtValidators.createDefault()`가 `JwtTimestampValidator`와 `X509CertificateThumbprintValidator` 둘뿐이라는 데 걸려 있다. 둘 중 실제로 실패할 수 있는 것은 **만료 하나**이므로 `JwtValidationException`을 만료로 읽을 수 있다. **검증기를 하나 더 붙이면 그 검증기의 실패도 `JwtValidationException`이 되어 만료가 아닌 사유가 조용히 `A003`(만료)으로 나간다.** `JwtTokenProvider`의 javadoc이 그 전제를 적어 두었다

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| `prod` 프로파일로 `/swagger-ui.html`·`/v3/api-docs` | **404.** 같은 경로가 `test` 프로파일에서는 열린다 — 그 대조가 404의 출처를 가린다 |
| `prod` 프로파일의 SQL 로그 | `show-sql`과 `logging.level.*` **속성값**이 꺼짐으로 설정되어 있다 |
| **미디어 타입 둘의 로그** | **`log.error`가 아니다** (실제는 `WARN`). 해당 완료 기준이 "ERROR를 남기지 않는다"이므로 **수준을 못박지 않는다** — 기준보다 좁은 주장을 하지 않는다([../process/review-policy.md §5.3](../process/review-policy.md)) |
| **`JwtConfig`의 검증기 집합** | **`JwtTimestampValidator`·`X509CertificateThumbprintValidator` 둘뿐.** 늘면 테스트가 깨져 `failureCode`를 함께 보게 한다 |
| **본문이 있는데 `Content-Type` 없음** | **415 `C006`.** 500이 아니다 |
| `Content-Type: text/plain` + JSON 본문 | 415 `C006` |
| **`Accept: application/xml`** | **406 `C007`** |

#### 이력에 남은 BCrypt 모양 — 감수한다

**현재 트리는 0건이지만 이력에는 3줄이 있다.** `0043308`(AU-03)가 넣고 `a678606`(AU-05)가 뺐다. 값은 `$2a$10$abcdefghijklmnop…`처럼 순차 문자열로 조립한 것이라 **실제 자격증명이 아니다.**

[../requirements/member.md §10.2](../requirements/member.md)의 근거 둘 중 하나는 이력에도 적용된다 — **이력을 훑는 시크릿 스캐너는 이 3줄을 집어낸다.** 다른 하나(읽는 사람이 진짜와 구분할 수 없다)는 현재 트리가 깨끗하므로 해당되지 않는다.

**BCrypt 3줄을 지우기 위한 이력 재작성은 하지 않는다.** 실제 자격증명이 아니므로 비용이 이득을 넘는다. **필요해지면 명시적 결정으로 한다.**

> **이 문단이 들던 비용 근거 하나는 이미 지불됐다.** 2026-10-14에 네 저장소의 이력 전체를 재작성했다 — 사유는 BCrypt가 아니라 **커밋 author 이메일**이었다([../process/dev-workflow.md §3.10](../process/dev-workflow.md)). 그래서 **모든 커밋 해시가 이미 바뀌었다.** 커밋 메시지가 인용한 해시 17개는 전부 끊겼다(측정값 — 현재 `main`에서 도달 불가). 문서 본문의 해시 참조 넷은 새 해시로 고쳤으나 **커밋 메시지는 고칠 수 없다.** 그러므로 그 비용을 BCrypt 재작성의 억지력으로 다시 인용하지 않는다.
>
> 한편 그 재작성은 author·committer 신원만 바꿨다. **트리가 동일하므로 BCrypt 3줄은 이력에 그대로 있다** — 위 결론은 유효하다. 다시 재작성하면 해시가 또 바뀐다는 비용은 남아 있다.

#### 하지 않기로 한 것 둘

리뷰에서 후속으로 올라왔으나 AU-11에서 하지 않는다. **근거를 적어 두는 것이 결론이다** — 적지 않으면 다음 사람이 같은 것을 다시 검토한다.

| | 왜 하지 않나 |
| --- | --- |
| `AccountControllerTest`·`AccountServiceTest` 분리 | 불변식 6은 줄 수가 아니라 **책임 단위**로 나누라고 한다. 두 파일은 **컨트롤러 하나·서비스 하나**의 계약이고 `@Nested`가 이미 구조를 준다. 1차에서 더 늘지 않는다(auth의 마지막 항목이다). 반면 1100줄 규모의 이동은 **diff가 전부 삭제·추가로 보여 단언 유실을 리뷰로 잡기 어렵다** — 기능 이득이 0인데 위험만 지는 교환이다 |
| 재발급의 RSA 검증을 트랜잭션 밖으로 | `reissue`가 `@Transactional`이므로 서명 검증이 트랜잭션 안에서 돈다. **비용을 측정하지 않았고**, 밖으로 빼려면 빈을 하나 더 두거나 프록시를 우회해야 한다. "조회·확인·회전이 한 트랜잭션"은 어느 쪽이든 성립한다 |

## 5. member-service 작업 항목

**M-01은 `done`이지만 완료 기준이 깨졌다.** auth 분리로 [../tech-stack.md §3.2](../tech-stack.md)의 의존성 배정이 바뀌었기 때문이다. §2.6 #2에 해당하므로 항목을 수정하지 않고 **`M-01R`을 신설해** 처리한다.

**M-06·M-07은 없다.** 로그인·재발급·로그아웃이 auth로 옮겨가 `AU-06`·`AU-07`이 됐다. 번호는 재사용하지 않는다.

### M-01 프로젝트 스캐폴딩 [기반 · done]

**원래 완료 기준을 여기 남겨 둔다.** `M-01R`이 "M-01의 나머지 완료 기준이 여전히 충족된다"를 요구하므로, 그 목록이 정본에 있어야 한다 — 이전 판은 "원래 완료 기준은 그대로 둔다"고만 적고 목록을 지워서, 확인하려면 git 이력을 뒤져야 했다.

- [x] `./gradlew build`가 성공한다
- [x] Boot 플러그인 버전이 `3.5.16`이다
- [x] `spring-boot-starter-webmvc` 등 Boot 4 스타터 이름이 남아 있지 않다
- [x] `./gradlew bootRun`으로 8081 포트에 기동된다
- [x] [../tech-stack.md §3.1 §3.2](../tech-stack.md)의 의존성이 전부 선언되어 있다
- [x] DB 접속 정보가 환경변수로 외부화되어 있다 ([../tech-stack.md §4.3](../tech-stack.md))
- [x] `.gitignore`에 `private.pem`, `*.env`가 있다

**이 중 다섯째가 auth 분리로 틀려졌다.** `M-01`은 당시 [../tech-stack.md §2.2](../tech-stack.md)("member-service (발급)")를 따라 서명 의존성을 넣었고, 그 절이 분리 전 구조였다. `M-01R`이 의존성을 정정하고 §2.2도 함께 고쳤다.

---

### M-01R 의존성·설정 정정 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | D-01 |
| 참조 | [../tech-stack.md §3.2 §4.3](../tech-stack.md), [../conventions.md §1.2](../conventions.md) |

**M-01의 완료 기준 중 auth 분리로 틀려진 것만 고친다.** 새 스캐폴딩이 아니다.

**산출물**
- `build.gradle` 수정 — 서명 의존성 제거, 검증 의존성 추가
- `application.yml` 수정 — 내부 API 키 설정 추가

**완료 기준**
- [ ] **`spring-security-oauth2-jose`를 직접 선언하지 않는다.** member는 서명하지 않는다([../security.md §2](../security.md)) — `build.gradle`을 읽어 확인한다. **의존성 트리에서 0건인지 보지 않는다**: 검증 의존성이 그것을 추이로 끌고 오므로 불가능하다([../tech-stack.md §2.2](../tech-stack.md)의 측정값)
- [ ] `spring-boot-starter-oauth2-resource-server`가 있다
- [ ] 그 외 [../tech-stack.md §3.1](../tech-stack.md)의 의존성이 전부 선언되어 있다
- [ ] `INTERNAL_API_KEY`가 **기본값 없이** 선언되어 있다 — `application.yml`을 읽어 확인한다. **"없으면 기동이 실패한다"는 이 항목에서 성립하지 않는다**: 그 속성을 읽는 코드가 없으므로 placeholder가 해석되지 않고 기동이 성공한다. 그 보장은 키를 실제로 읽는 M-10이 진다
- [ ] `./gradlew build`가 성공하고 8081 포트에 기동된다
- [ ] M-01의 나머지 완료 기준이 여전히 충족된다

**검증** — `MemberApplicationTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 컨텍스트 로딩 | 예외 없이 기동 |

---

### M-02 공통 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-01R |
| 참조 | [../api-contract.md §7 §8.1 §8.2](../api-contract.md), [../domain-model.md §1.1](../domain-model.md), [../conventions.md §6 §6.1 §7 §9](../conventions.md) |

**산출물**
- `global/common/ApiResponse.java`, `ErrorResponse.java`, `PageResponse.java`
- `global/common/BaseTimeEntity.java`
- `global/error/ErrorCode.java` (C001~**C007**, A001~A004, **M001·M003·M006·M007**)
- `global/error/BusinessException.java`, `GlobalExceptionHandler.java`
- `global/config/JpaConfig.java` (`@EnableJpaAuditing`), `SwaggerConfig.java`

복제 대상 파일 상단에 정본 주석을 남긴다([../conventions.md §7.1](../conventions.md)).

**완료 기준**
- [ ] `ErrorCode`의 코드·HTTP 상태·메시지가 [../api-contract.md §8](../api-contract.md)과 정확히 일치한다
- [ ] **`M002`·`M004`·`M005`가 없다.** auth로 이동했다(`AU002`·`AU003`·`AU004`). **번호를 재사용하지 않는다**
- [ ] `M001`의 메시지가 "프로필을 찾을 수 없습니다."다
- [ ] `BusinessException`을 던지면 해당 코드의 HTTP 상태와 응답 본문이 나온다
- [ ] `@Valid` 검증 실패가 `C001`로 변환되고 `fieldErrors`에 필드별 메시지가 담긴다
- [ ] 응답 본문에 스택트레이스·SQL이 포함되지 않는다
- [ ] **springdoc이 OpenAPI 문서를 생성한다.** `/v3/api-docs`가 문서를 돌려주고 `SwaggerConfig`가 등록된다
- [ ] `/swagger-ui.html`이 **인증 없이** 열리는 것은 이 항목의 기준이 아니다. `SecurityConfig`가 없으면 Boot 기본 필터가 전 경로를 401로 막는다([../security.md §5.1.1](../security.md)). 보안 기반 항목에서 확인한다

**검증** — `GlobalExceptionHandlerTest` (`@WebMvcTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| `BusinessException(M003)` | 409, `error.code = "M003"` |
| `BusinessException(M006)` | 409, `M006` |
| `BusinessException(A004)` | 403, `A004` |
| `ErrorCode` 열거 전체 | `M002`·`M004`·`M005` 없음 |
| `@Valid` 실패 | 400, `C001`, `fieldErrors` 비어있지 않음 |
| 성공 응답 | `success = true`, `error = null` |
| 예상치 못한 `RuntimeException` | 500, `C005`, 스택트레이스 없음 |
| **타입 불일치 파라미터** | 400 `C002` |
| **없는 HTTP 메서드** | 405 `C003` |
| **매핑 없는 경로** | 404 `C004` |
| **필수 파라미터 누락** | 400 `C001`, `fieldErrors` **빈 배열** |
| **본문이 있는데 `Content-Type` 없음** | **415 `C006`.** 500 이 아니고 `log.error` 를 남기지 않는다 |
| **`Accept: application/xml`** | **406 `C007`** |
| **마지막 그물의 로그 수준** | **`ERROR`.** `warn` 으로 낮추면 500 이 ERROR 경보를 전혀 만들지 않는다 ([../conventions.md §6.1](../conventions.md)) |

---

### M-03 도메인 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-02 |
| 참조 | [../domain-model.md §1 §3](../domain-model.md), [../conventions.md §2 §9](../conventions.md), [../requirements/member.md §3](../requirements/member.md) |

**엔티티가 하나로 줄었다.** `RefreshToken`은 auth(`AU-03`)로 옮겨갔고, `Member`에서 `email`·`password`·`role`이 빠졌다.

**산출물**
- `member/entity/Member.java`
- `member/repository/MemberRepository.java`
- `member/support/MemberReader.java` (find or throw — `M001`)
- `db/migration/V1__create_member.sql` (**V2는 seed다. §2.4**)
- `build.gradle` 수정 — test 태스크에 `systemProperty 'spring.profiles.active', 'test'` ([../tech-stack.md §5.1](../tech-stack.md))
- `src/test/resources/application-test.yml` — `spring.jpa.hibernate.ddl-auto: validate` 명시

**`Role` enum을 만들지 않는다.** 권한은 auth 소유이며 JWT Claim으로 전달된다.

**`Member`의 도메인 메서드** — 전부 이 항목에서 구현한다.

| 메서드 | 동작 |
| --- | --- |
| `updateNickname(String)` | 닉네임 변경 |
| `withdraw()` | `deleted = true`, **`nickname = null`** |
| `isActive()` | `!deleted` |

**`withdraw()`가 닉네임을 비우는 것이 핵심이다.** `uk_member_nickname`이 UNIQUE이므로, 값을 남겨두면 그 닉네임이 영구 소각되고 `"탈퇴한 회원"`으로 마스킹해 **저장**하면 두 번째 탈퇴가 UNIQUE 위반으로 500이 난다([../domain-model.md §3.1](../domain-model.md)).

**완료 기준**
- [ ] 기동 시 Flyway가 `member` 테이블을 생성한다
- [ ] 컬럼 타입·길이·NULL 여부가 [../domain-model.md §3.1](../domain-model.md)과 일치한다
- [ ] **`email`·`password`·`role` 컬럼이 없다**
- [ ] `member.account_id`, `member.nickname`에 UNIQUE 제약이 있다
- [ ] **`nickname`이 NULL을 허용한다**
- [ ] `account_id`에 **FK 제약이 없다** (서비스 경계를 넘는다)
- [ ] `created_at`, `updated_at`이 `DATETIME`이고 자동 기록된다
- [ ] 위 표의 도메인 메서드 3개가 모두 구현되어 있다
- [ ] **`withdraw()`가 `nickname`을 NULL로 만든다**
- [ ] `MemberReader`가 없는 `accountId` 조회 시 `BusinessException(M001)`을 던진다
- [ ] Entity에 `@Setter`·`@Data`가 없다
- [ ] **`@DataJpaTest` 클래스에 `@AutoConfigureTestDatabase(replace = NONE)`이 붙어 있다** ([../tech-stack.md §5.2](../tech-stack.md))
- [ ] **테스트 DataSource URL이 [../tech-stack.md §5.3](../tech-stack.md)의 정본과 일치한다** — `DATABASE_TO_LOWER`·`CASE_INSENSITIVE_IDENTIFIERS`·`DB_CLOSE_DELAY=-1` 포함
- [ ] **테스트가 그 URL로 돈다.** `jdbc:h2:mem:<uuid>`가 아니다
- [ ] **`ddl-auto: validate`가 실제로 적용된다.** 엔티티에만 있는 컬럼을 넣는 변이에서 `SchemaManagementException`으로 기동이 실패하는 것으로 확인한다 — **검증표에 넣지 않는다**(테스트가 자기 엔티티를 바꿀 수 없다, [../process/review-policy.md §5.3](../process/review-policy.md))

**검증** — `MemberRepositoryTest` (`@DataJpaTest`), 그리고 **테스트 환경 클래스**(이름은 구현이 정한다)

> **환경 클래스에는 `@ActiveProfiles` 를 붙이지 않는다.** 전부 붙어 있으면 `build.gradle` 의 `systemProperty` 한 줄을 지워도 스위트가 초록이어서, [../tech-stack.md §5.1](../tech-stack.md)의 opt-in 제거가 일하는지 확인할 길이 없다. 실행 중 DataSource URL·테이블명·**스키마 출처**가 그 클래스의 몫이다 ([../tech-stack.md §5.2](../tech-stack.md)).

| 케이스 | 기대 결과 |
| --- | --- |
| 저장 후 조회 | 모든 필드 일치 |
| 중복 `account_id` 저장 | `DataIntegrityViolationException` |
| 중복 nickname 저장 | `DataIntegrityViolationException` |
| 저장 시 | `createdAt`, `updatedAt` null 아님 |
| `deleted` 미지정 저장 | `false`. **엔티티 생성자를 증명한다** — JPA 는 INSERT 에 컬럼을 항상 보내므로 `V1` 의 `DEFAULT FALSE` 는 이 경로에서 발동하지 않는다. 그쪽이 일하는 자리는 M-05 의 seed 같은 순수 SQL 경로다 |
| `updateNickname()` 호출 | 닉네임만 변경, `createdAt` 불변 |
| `withdraw()` 호출 | `deleted = true`, **`nickname = null`**, 행 존재 |
| **두 회원을 연달아 `withdraw()`** | **둘 다 성공.** UNIQUE 위반 없음 |
| `MemberReader`로 없는 `accountId` 조회 | `BusinessException(M001)` |
| 테이블 메타데이터 | `email`·`password`·`role` 컬럼 없음 |
| **`information_schema` 의 `nickname` 폭** | **30.** 엔티티의 `@Column(length)` 와 일치한다 — **`validate` 는 길이를 보지 않는다.** 다만 이 비교는 **Flyway 가 스키마를 소유할 때만 뜻이 있다**([../tech-stack.md §5.2](../tech-stack.md)) |
| **`information_schema` 의 FK 제약** | **`member` 에 `FOREIGN KEY` 0건.** `V1` 을 한 번 읽는 것으로는 **나중 마이그레이션이 FK 를 추가하는 것**을 막지 못한다 |
| 테스트 실행 중 DataSource URL | [../tech-stack.md §5.3](../tech-stack.md)의 정본과 문자열 일치 |
| 저장된 테이블명 | **소문자** `member`. `DATABASE_TO_LOWER` 효과 |

> **탈퇴 2건 연속 테스트를 반드시 넣는다.** 첫 탈퇴는 항상 성공하므로 1건만 보면 UNIQUE 결함을 놓친다.

---

### M-04 보안 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-03 |
| 참조 | [../security.md](../security.md) 전체, [../api-contract.md §3 §6 **§8.5**](../api-contract.md), [../conventions.md §1.2 §9](../conventions.md) |

**member는 검증만 한다.** 개인키·`JwtTokenProvider`·`TokenResponse`는 auth(`AU-04`)로 옮겨갔다.

**산출물**
- `global/config/SecurityConfig.java` — **[../api-contract.md §3](../api-contract.md)의 전체 경로 인가**, 공개키 검증기, CORS, STATELESS
- `global/security/RoleClaimConverter.java` (`role` claim → `GrantedAuthority`)
- `global/security/LoginMember.java` (record), `@CurrentMember` ArgumentResolver
- `src/main/resources/jwt-public.pem` (**공개키. 커밋 가능**)
- `application.yml` 수정 — 공개키 설정 키를 **정본 키로 교체**하고 `cors.allowed-origins: ${CORS_ALLOWED_ORIGINS}` 를 **기본값 없이** 추가한다 ([../security.md §1.1](../security.md), [../tech-stack.md §4.3](../tech-stack.md))

**⚠ `LoginMember`는 `(accountId, role)`이다.** `nickname`이 없다 — Claim에 없기 때문이다([../api-contract.md §6](../api-contract.md)).

**⚠ 개인키를 두지 않는다.** member는 토큰을 발급하지 않는다. `oauth2-jose` 의존성도 없다(M-01R).

**⚠ 경로 선언 순서** — `GET /api/v1/members/{accountId}`는 `permitAll`, `/api/v1/members/me`는 `authenticated`다. `requestMatchers`는 **먼저 선언된 규칙이 이기므로** `/members/me`를 반드시 먼저 선언한다. 뒤에 두면 **내 정보가 인증 없이 열린다.**

**실제 공개키가 이미 배치되어 있다.** AU-04를 기다리지 않는다. I-01에서 두 사본의 일치와 실제 발급 토큰 수용을 확인한다.

**완료 기준**
- [ ] 공개키로 서명 검증이 동작한다
- [ ] **개인키를 로딩하지 않는다.** 서명 기능이 없다
- [ ] `LoginMember`가 `(accountId, role)`이고 **`nickname` 필드가 없다**
- [ ] `role` claim이 `GrantedAuthority`로 변환된다
- [ ] **`A001`·`A002`·`A003`의 경계가 [../api-contract.md §8.5](../api-contract.md)와 일치한다.** 세 서비스가 공유하는 계약이다 — auth(AU-04)가 이미 이 경계로 구현했고 I-04가 3자 비교한다. **예외 타입만 보고 가른다. 메시지 문자열을 파싱하지 않는다**
- [ ] [../api-contract.md §3](../api-contract.md)의 **모든 경로**에 인가 규칙이 선언되어 있다
- [ ] **`/members/me`가 `/members/{accountId}`보다 먼저 선언되어 있다**
- [ ] **`/swagger-ui/**`·`/v3/api-docs/**`가 `permitAll`이고 인증 없이 열린다** ([../security.md §5.1.1](../security.md))
- [ ] `/actuator/health` 외의 actuator 경로가 노출되지 않는다
- [ ] `/internal/**`이 외부 인증 체인에서 분리되어 있다
- [ ] 세션이 생성되지 않는다
- [ ] **CORS 허용 오리진이 비었거나 `*`가 섞이면 기동이 실패한다** ([../security.md §1.1](../security.md)). "설정에 `*`가 없다" 는 그 절반이다 — **값이 환경에서 오므로 금지를 지키는 지점은 `SecurityConfig` 안의 가드뿐이다.** AU-04 가 같은 가드를 갖는다
- [ ] 허용 메서드·헤더·`allowCredentials` 가 §1.1 의 정본 값과 일치한다. **CORS 는 `SecurityConfig` 에 둔다** — MVC 쪽에만 두면 preflight 가 401 로 막힌다
- [ ] **공개키 설정 키가 `spring.security.oauth2.resourceserver.jwt.public-key-location`이다** ([../tech-stack.md §2.1](../tech-stack.md)). 현재 `application.yml`에 들어 있는 `jwt.public-key-location`은 **정본 키가 아니고 읽는 코드도 없다** — 내 설정 커밋(`8b3a4f8`)이 넣은 것이고 이 항목에서 교체한다. 표준 키를 쓰면 스타터가 `JwtDecoder`를 자동구성하므로 컨버터 외에 직접 만들 것이 없다
- [ ] 공개키가 없으면 **기동이 실패한다.** **측정해서 확인한다** — 자동구성이 기동 시점에 키 파일을 읽는지가 전제다. `INTERNAL_API_KEY`가 그 전제 없이 적혀 있다가 M-10으로 옮겨졌다(M-01R 참조). **추측하지 말고 파일을 치우고 띄워 본다.** **검증표에 넣지 않는다** — 컨텍스트 기동 실패를 테스트로 만드는 것은 무겁고, 실패시키는 주체가 우리 코드가 아니라 스타터다([../process/review-policy.md §5.3](../process/review-policy.md), [../AGENTS.md](../AGENTS.md) 불변식 11)

**검증** — `SecurityConfigTest` (`@SpringBootTest` + MockMvc)

| 케이스 | 기대 결과 |
| --- | --- |
| 유효 토큰으로 인증 | 통과, `LoginMember.accountId()`가 `sub`와 일치 |
| `LoginMember` 필드 목록 | `nickname` 없음 |
| **헤더 없음** | **401 `A001`** |
| **`Bearer not!a!token`** (`b64token` 문법 위반) | **401 `A001`** — 애초에 bearer 자격증명이 아니다 |
| **`Bearer <문법은 맞지만 JWT가 아님>`** | **401 `A002`** |
| payload 변조된 토큰 | **401 `A002`** |
| 만료된 토큰 | 401 `A003` |
| **`iss` 불일치** | **401 `A002`** — 사유를 가르지 않는다 |
| **토큰 없이 `GET /api/v1/members/me`** | **401 `A001`** |
| **토큰 없이 `GET /api/v1/members/1`** | **401이 아님** |
| **허용 오리진에 `*` 가 섞임** | **기동 실패**(`IllegalStateException`). 메서드를 직접 호출해 단언한다 |
| **허용 오리진이 빈 목록** | **기동 실패.** 둘을 함께 본다 — 하나만 보면 다른 쪽이 열린다 |
| **토큰 없이 `/swagger-ui.html`** | **302 → `/swagger-ui/index.html`.** `/login` 으로 가면 실패 |
| **토큰 없이 `/swagger-ui/index.html`** | **200** |
| **토큰 없이 `/v3/api-docs`** | **200, OpenAPI 문서** |
| 응답 헤더 | `Set-Cookie` 세션 쿠키 없음 |

> `/members/me`와 `/members/{accountId}` 두 케이스를 **반드시 함께** 검증한다. 하나만 보면 순서 결함을 놓친다.

---

### M-05 프로필 등록과 닉네임 중복 확인 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-04 |
| 참조 | [../requirements/member.md §1 §2 §3 §4 §10](../requirements/member.md) (MR-01 3단계, MR-03), [../api-contract.md §3 §3.1 §9.1](../api-contract.md), [../conventions.md §9](../conventions.md) |

**가입 3단계다.** 계정 생성(AU-05)과 로그인(AU-06)이 먼저다.

**산출물**
- `member/dto/ProfileCreateRequest.java`, `MemberResponse.java`, `CheckResponse.java`
- `member/service/MemberService.java` (생성)
- `member/controller/MemberController.java` (생성)
- `db/migration/V2__seed_admin_profile.sql` — `account_id = 1`, `nickname = 관리자`. 값은 [../requirements/member.md §10.1](../requirements/member.md)이 정본. **비밀번호가 없으므로 placeholder가 필요 없다**

> **이 seed 가 기존 테스트 픽스처와 충돌할 수 있다.** `(1, '관리자')` 가 들어가는 순간 같은 `account_id` 나 닉네임을 쓰는 픽스처가 UNIQUE 위반으로 깨진다. auth 가 `admin@example.com` 에서 같은 것을 겪었다. M-03 의 픽스처는 `accountId` 101~ 과 `관리자` 아닌 닉네임을 쓰도록 미리 피해 뒀다 — **그 회피를 깨뜨리지 말고, 새 픽스처도 같은 규칙을 따른다.**

**⚠ `POST /api/v1/members`는 인증이 필요하다.** `account_id`는 **검증된 JWT의 `sub`에서만** 가져온다. 요청 본문의 식별자를 신뢰하지 않는다.

**⚠ 이메일·비밀번호를 받지 않는다.** 계정은 auth 소유다.

**완료 기준**
- [ ] `POST /api/v1/members`가 **인증을 요구한다.** 토큰 없으면 401 `A001`
- [ ] 201과 `{accountId, nickname}`을 반환한다
- [ ] **`account_id`가 JWT `sub`에서 온다.** 본문에 다른 값을 넣어도 무시된다
- [ ] **멱등이다** — 상태별 응답이 [../api-contract.md §3](../api-contract.md) 표와 일치한다
- [ ] 중복 닉네임 409 `M003`
- [ ] 검증 규칙이 [../requirements/member.md §2](../requirements/member.md)와 일치한다
- [ ] `GET /api/v1/members/check-nickname`의 응답이 `{ "available": boolean }`이다 ([../api-contract.md §2.3](../api-contract.md))
- [ ] **탈퇴로 해방된 닉네임은 `available: true`다** — 이메일과 달리 닉네임은 재사용할 수 있다
- [ ] **이메일·비밀번호를 받지도 저장하지도 않는다**
- [ ] seed 프로필의 `account_id`가 `AU-05`의 seed와 같은 값이다

**검증** — `MemberServiceTest`, `MemberControllerTest`, **`AdminProfileSeedTest`**(seed 관련)

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 등록 | 201, DB 저장됨 |
| 토큰 없이 등록 | 401 `A001` |
| **본문에 다른 `accountId` 전달** | **JWT `sub` 값으로 저장됨** |
| **같은 계정·같은 닉네임으로 재호출** | **200, 기존 반환** (멱등) |
| **같은 계정·다른 닉네임으로 재호출** | **409 `M006`** |
| **탈퇴한 프로필의 계정으로 재호출** | **409 `M007`** |
| 타인이 쓰는 닉네임 | 409 `M003` |
| 닉네임 1자 / 11자 | 400 `C001` |
| 요청에 `email`·`password` 포함 | 무시됨. 저장되지 않음 |
| 미사용 닉네임 중복 확인 | 사용 가능 응답 |

---

### M-08 내 프로필 조회·수정 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-05 |
| 공유 파일 | `MemberService`, `MemberController` (M-05 생성) |
| 참조 | [../requirements/member.md §1 §5 §7](../requirements/member.md) (MR-07의 프로필 절반, MR-08), [../api-contract.md §3.1](../api-contract.md), [../conventions.md §9](../conventions.md) |

**MR-07이 두 서비스로 갈라진 절반이다.** 이메일·가입일은 `AU-10`이 담당한다.

**산출물**
- `member/dto/NicknameUpdateRequest.java`, `MemberResponse.java` 재사용
- `MemberService`·`MemberController` 확장

**⚠ 새 Access Token을 반환하지 않는다.** 이전 v3의 요구는 **폐기됐다.** Claim에 `nickname`이 없으므로 토큰이 낡을 이유가 없고, member는 개인키가 없어 발급할 수도 없다([../requirements/member.md §7](../requirements/member.md)).

**완료 기준**
- [ ] `GET /api/v1/members/me`가 **`accountId`·`nickname` 둘만** 반환한다 ([../api-contract.md §3.1](../api-contract.md)). `createdAt`을 넣지 않는다 — MR-07이 member에 배정한 것은 닉네임뿐이다
- [ ] **응답에 `email`이 없다.** member는 이메일을 모른다
- [ ] **프로필이 없으면 404 `M001`이다.** 가입 3단계 미완료를 뜻한다
- [ ] `PATCH /api/v1/members/me`가 닉네임을 변경한다 (`Member.updateNickname()` 사용)
- [ ] **응답에 토큰이 포함되지 않는다**
- [ ] 중복 닉네임으로 변경 시 409 `M003`
- [ ] **자기 현재 닉네임으로 변경 시 중복 오류가 나지 않는다**
- [ ] 탈퇴한 프로필은 조회·수정할 수 없다

**검증** — `MemberServiceTest`, `MemberControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 내 프로필 조회 | 200, 닉네임 존재 |
| **응답 키 집합** | **`accountId`·`nickname` 정확히 둘.** `email`·`accessToken`·`createdAt` 없음 |
| **프로필 없는 계정으로 조회** | **404 `M001`** |
| 닉네임 변경 | 200, DB 반영됨 |
| 변경 응답 본문 | **토큰 키 없음** |
| 타인 닉네임으로 변경 | 409 `M003` |
| 자기 현재 닉네임으로 변경 | 200 |
| 닉네임 1자 | 400 `C001` |
| 탈퇴한 프로필로 조회 | 404 `M001` |
| **탈퇴한 프로필로 수정** | **404 `M001`** |
| 토큰 없이 `/me` 접근 | 401 `A001` |

---

### M-09 프로필 탈퇴 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-08 |
| 공유 파일 | `MemberService`, `MemberController` — **M-08 완료 후 시작** |
| 참조 | [../requirements/member.md §1 §8](../requirements/member.md) (MR-10 **2단계**), [../architecture.md §4.4](../architecture.md) |

**탈퇴 2단계 중 2단계다.** 1단계(계정 탈퇴 + 비밀번호 재확인)는 auth의 `AU-09`다.

**비밀번호 변경은 이 항목에 없다.** 전부 auth(`AU-08`)로 옮겨갔다. `RefreshTokenRepository`도 member에 없다.

**산출물**
- `MemberService`·`MemberController` 확장

**⚠ 비밀번호를 받지 않는다.** member는 비밀번호를 갖지 않는다. 재확인은 1단계(`AU-09`)에서 이미 끝났다.

**⚠ 계정 상태를 확인하지 않는다.** member는 `sp_auth`를 조회할 수 없다. 토큰 서명이 유효하면 진행한다.

**완료 기준**
- [ ] `DELETE /api/v1/members/me`가 204를 반환한다
- [ ] `Member.withdraw()`로 `deleted = true`, **`nickname = null`**이 된다 (행 삭제 아님)
- [ ] **멱등이다.** 이미 탈퇴한 프로필에 다시 호출해도 204
- [ ] 탈퇴 후 프로필 조회가 404 `M001`이다
- [ ] 탈퇴 후 같은 계정으로 프로필을 재생성할 수 없다 (409 `M007`)
- [ ] **auth를 호출하지 않는다** — 저장소에 HTTP 클라이언트가 **없다**는 관측으로 충족한다. **검증표에 넣지 않는다**(없는 호출을 관측하는 테스트는 아무것도 잡지 못한다, [../process/review-policy.md §5.3](../process/review-policy.md))
- [ ] **비밀번호를 받지 않는다**

**검증** — `MemberServiceTest`, `MemberControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 탈퇴 | 204, `deleted = true`, `nickname = null`, 행 존재 |
| **이미 탈퇴한 프로필에 재호출** | **204** (멱등) |
| **두 회원을 연달아 탈퇴** | **둘 다 204.** UNIQUE 위반 없음 |
| 탈퇴 후 `GET /members/me` | 404 `M001` |
| 탈퇴 후 `POST /members` 재시도 | 409 `M007` |
| 탈퇴 후 해방된 닉네임으로 타인이 등록 | 201 |

---

### M-10 프로필 조회와 내부 API [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-09 |
| 공유 파일 | `MemberController` — **M-09 완료 후 시작** |
| 참조 | [../requirements/member.md §1 §9](../requirements/member.md) (MR-11, MR-12), [../api-contract.md §5](../api-contract.md), [../security.md §6](../security.md) |

**1차부터 board가 호출한다.** 더 이상 "2차 대비"가 아니다. 이 API가 없으면 board는 글을 저장할 수 없다.

**산출물**
- `member/dto/MemberProfileResponse.java`
- `internal/dto/MemberBulkRequest.java`, `MemberSummaryResponse.java`
- `internal/controller/InternalMemberController.java`
- `internal/service/InternalMemberService.java`
- `global/security/InternalApiKeyFilter.java`

**⚠ 벌크 하나만 만든다.** 단건 전용 API를 두지 않는다. board가 1건만 필요해도 벌크에 1건을 담는다. 실패 의미론을 하나로 유지하기 위해서다.

**⚠ 존재하지 않는 `accountId`는 결과에서 제외한다. 404를 반환하지 않는다.** board가 404를 "프로필 없음"으로 해석하면 경로 오설정이 업무 오류로 위장된다([../api-contract.md §5.1](../api-contract.md)).

**⚠ `"탈퇴한 회원"`은 응답 시 변환이다.** DB에는 NULL이 저장되어 있다.

`/internal/**` 경로의 인가 설정은 M-04 산출물이다. 필터 등록만 이 항목에서 한다.

**완료 기준**
- [ ] `GET /api/v1/members/{accountId}`가 **`accountId`·`nickname`·`createdAt`·`deleted`** 를 반환한다 ([../api-contract.md §3.1](../api-contract.md)). **이메일 미포함**
- [ ] **그 `createdAt`은 `member.created_at`(프로필 등록 시각)이다.** MR-07의 가입일(`account.created_at`)과 **다른 값이고**, 타인의 계정 생성 시각은 읽을 수 없다
- [ ] **탈퇴한 프로필도 200이다.** `nickname`은 `"탈퇴한 회원"`, `deleted: true` — 글이 남아 있으므로 표시할 것이 있다
- [ ] **그 `accountId`의 프로필이 아예 없으면 404 `M001`이다.** 공개 조회는 클라이언트를 상대하므로 404가 맞다 — §5.1이 금지한 것은 **내부 API**의 404다. **두 경로를 같게 맞추지 않는다**
- [ ] **경로 변수가 `accountId`다.** `member.id`를 외부에 노출하지 않는다
- [ ] **`GET /members/me`가 `GET /members/{accountId}`보다 먼저 매칭된다**
- [ ] `POST /internal/v1/members/bulk`가 [../api-contract.md §5](../api-contract.md) 형식으로 응답한다
- [ ] 요청 키가 `accountIds`, 응답 키가 `accountId`다
- [ ] **존재하지 않는 id는 결과에서 제외된다.** 404가 아니다
- [ ] 탈퇴 프로필은 `deleted: true`, 닉네임 `"탈퇴한 회원"` (**DB에는 NULL**)
- [ ] 내부 API 응답에 이메일·비밀번호가 없다 (애초에 갖고 있지 않다)
- [ ] `X-Internal-Api-Key` 없이 호출하면 401 또는 403이다
- [ ] 내부 API 키가 **기본값 없이** 주입되고, **키가 없으면 기동이 실패한다.** 리터럴 `${INTERNAL_API_KEY}`가 유효한 키로 쓰이면 **커밋된 `application.yml`의 문자열이 내부 API의 키가 된다** — board도 같은 리터럴을 쓰면 통과한다
- [ ] **그 실패를 측정해 확인한다.** `@Value` 주입이 미해결 placeholder에 예외를 던지는지는 읽는 방식에 달려 있다 — auth에서는 `@ConfigurationProperties` **맵** 값이 리터럴을 통과시켜 별도 가드가 필요했다([../requirements/member.md §10.2](../requirements/member.md)). **추측하지 말고 키 없이 기동해 본다.** 통과하면 가드를 넣는다
- [ ] **단건 전용 엔드포인트가 없다**

**검증** — `MemberControllerTest`, `InternalMemberControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 프로필 조회 | 200, 키가 `accountId`·`nickname`·`createdAt`·`deleted`. `email` 없음 |
| **탈퇴한 프로필 공개 조회** | **200**, `nickname = "탈퇴한 회원"`, `deleted: true` |
| **프로필이 없는 `accountId`** | **404 `M001`** |
| **`GET /members/me` (유효 토큰)** | **내 정보 반환** (`me`를 accountId로 해석하지 않음) |
| 정상 벌크 조회 (3건) | 200, 3건 반환 |
| **벌크 1건 요청** | **200, 1건 반환** |
| **존재하지 않는 id 포함** | **200. 해당 id는 결과에서 제외. 404 아님** |
| **전부 존재하지 않는 id** | **200, 빈 배열. 404 아님** |
| **`accountIds` 누락 · `null`** | **400 `C001`** |
| **`accountIds` 빈 배열** | **200, 빈 배열.** 400 이 아니다 — [../api-contract.md §5](../api-contract.md) |
| 탈퇴 프로필 포함 | `deleted: true`, 닉네임 `"탈퇴한 회원"` |
| 탈퇴 프로필의 DB 값 | `nickname IS NULL` |
| 응답 본문 | `email`, `password` 키 없음 |
| API 키 없이 / 잘못된 키 | 401 또는 403 |
| 라우팅 테이블에 `GET /internal/v1/members/{id}` | **없음** |

---

### M-11 마무리 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-10 |
| 참조 | [../nfr.md](../nfr.md), [../tech-stack.md §6](../tech-stack.md) |

**산출물**
- `README.md` 갱신 (실행 절차, 환경변수 목록, **공개키 배치 절차**)
- Actuator 설정 (`/actuator/health`만 노출)
- `application-prod.yml` (Swagger·SQL 로그 비활성화)
- **claim 검증기 집합을 고정하는 테스트** — M-04 에서 넘어온 것

**완료 기준**
- [ ] `README.md`에 로컬 실행 절차와 필요한 환경변수가 모두 적혀 있다
- [ ] `README.md`에 **공개키 배치 절차**와 `INTERNAL_API_KEY`가 적혀 있다
- [ ] `/actuator/health`가 200 `{"status":"UP"}`이고 **그 외 엔드포인트는 노출되지 않는다.** auth 실측은 무토큰 401 `A001`·유효 토큰 403 `A004`이고 **404가 아니다** — member도 확인한다. **M-04가 만든 동작이므로 관측으로 충족한다**
- [ ] `prod` 프로파일에서 Swagger UI가 비활성화된다
- [ ] **`springdoc.api-docs.enabled`도 끈다.** UI만 끄면 `/v3/api-docs`가 전체 엔드포인트 목록을 그대로 낸다
- [ ] `prod` 프로파일에서 SQL 로그가 꺼진다 — **`show-sql`과 `logging.level` 둘 다**. 후자가 보안 쪽이다: **바인드 파라미터 로그에는 비밀번호가 평문으로 실린다**. member는 비밀번호를 갖지 않지만 `logging.level`을 같은 모양으로 둔다(세 서비스가 같은 운영 설정을 쓴다)
- [ ] **그 `logging.level` 블록을 지우면 테스트가 깨진다.** 루트 기본이 `INFO`라 설정이 없어도 로거는 이미 조용하다 — **효과가 아니라 속성값을 단언한다**
- [ ] **`JwtValidators.createDefault()` 가 거는 검증기 집합이 테스트로 고정되어 있다.** M-04 의 `A002`·`A003` 판정이 그 집합에 걸려 있다 — Claim 계약 위반은 **검증기 결과가 아니라** `ClaimContractValidator` 가 던지는 `BadJwtException` 으로 오므로 `A002` 가 되고, 그래서 남은 `JwtValidationException` 을 **만료**라고 읽을 수 있다. 기본 둘 중 실제로 실패할 수 있는 것이 만료 하나이기 때문이다. **검증기가 하나 더 붙으면 그 검증기의 실패도 `JwtValidationException` 이 되어 만료가 아닌 사유가 조용히 `A003`(만료)으로 나간다.** `SecurityErrorResponder` 의 javadoc 이 그 전제를 적어 두었다. AU-11 이 auth 에서 같은 것을 못박았다 — 같은 모양으로 한다

> **M-04 의 `A002`·`A003` 테스트는 검증기 추가를 잡지 못한다. 측정값이다.** M-11 에서 `JwtIssuerValidator` 를 더해 둔 채 `SecurityConfigTest` 전체를 돌려도 통과한다 — 이 집합 단언이 그 변화를 드러내는 **유일한 기계장치**다.
>
> **`iss` 불일치는 이 위험에 해당하지 않는다.** member 는 `ClaimContractValidator` 가 `BadJwtException` 을 직접 던지므로 검증기가 늘어도 `A002` 로 남고, auth 는 `iss` 검증기를 아예 붙이지 않았다(`JwtTokenProvider` javadoc). **두 완료 기준이 한때 `iss` 를 예로 들었는데 그 인과가 한 단계 넓었다** — M-11 구현 워커가 측정으로 바로잡았다.
- [ ] 전체 테스트가 통과한다 (`./gradlew test`)
- [ ] 커밋된 파일에 비밀 값이 없다. `git grep`으로 **현재 트리**를 확인한다
- [ ] **개인키가 저장소에 없다.** `git log -p`의 `BEGIN PRIVATE KEY`를 확인한다 — **검증표에 넣지 않는다**(이력 조회는 테스트가 아니다, [../process/review-policy.md §5.3](../process/review-policy.md))

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| `prod` 프로파일로 `/swagger-ui.html`·`/v3/api-docs` | **404.** 같은 경로가 `test` 프로파일에서는 열린다 — 그 대조가 404의 출처를 가린다 |
| **claim 검증기 집합** | **`JwtTimestampValidator`·`X509CertificateThumbprintValidator` 둘뿐.** 늘면 테스트가 깨져 `A002`·`A003` 판정을 함께 보게 한다 |
| `prod` 프로파일의 SQL 로그 | `show-sql`과 `logging.level.*` **속성값**이 꺼짐으로 설정되어 있다 |

## 6. board-service 작업 항목

### B-01 프로젝트 스캐폴딩 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | 없음 |
| 병렬 | M-01과 동시 진행 (다른 저장소) |
| 참조 | [../tech-stack.md §1 §3](../tech-stack.md), [../conventions.md §1.2](../conventions.md) |

**산출물**
- `build.gradle`, `settings.gradle`, Gradle Wrapper
- `src/main/java/com/example/board/BoardApplication.java`
- `application.yml`, `application-local.yml`
- `global/config/QuerydslConfig.java` (`JPAQueryFactory` 빈)
- `.gitignore`

**프로젝트 생성은 [../tech-stack.md §1.1](../tech-stack.md) 절차를 따른다** (M-01과 동일). 의존성도 여기서 전부 확정한다.

**완료 기준**
- [ ] `./gradlew build`가 성공한다
- [ ] Boot 플러그인 버전이 `3.5.16`이다
- [ ] Boot 4 스타터 이름이 남아 있지 않다
- [ ] 8082 포트에 기동된다
- [ ] QueryDSL Q타입이 생성되고 `.gitignore`에 생성 경로가 있다
- [ ] [../tech-stack.md §3.1 §3.2](../tech-stack.md)의 의존성이 전부 선언되어 있다
- [ ] DB 접속 정보가 환경변수로 외부화되어 있다

**검증** — `BoardApplicationTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 컨텍스트 로딩 | 예외 없이 기동 |
| `JPAQueryFactory` 빈 | 주입됨 |

---

### B-02 공통 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-01 |
| 참조 | [../api-contract.md §7 §8.1 §8.3](../api-contract.md), [../domain-model.md §1.1](../domain-model.md), [../conventions.md §6 §6.1 §7 §9](../conventions.md) |

**산출물**
- `global/common/ApiResponse.java`, `ErrorResponse.java`, `PageResponse.java`
- `global/common/BaseTimeEntity.java`
- `global/error/ErrorCode.java` (C001~**C007**, A001~A004, **P001, P002, CM001, CM002, S001, S002**)
- `global/error/BusinessException.java`, `GlobalExceptionHandler.java`
- `global/config/JpaConfig.java`, `SwaggerConfig.java`

AU-02·M-02와 같은 파일을 만들되 `ErrorCode`는 board 전용 코드를 쓴다. **복제본이 3벌이 되므로** 형식 일치는 I-04에서 3자 비교한다.

**`S002`(403, "프로필 등록이 필요합니다.")가 새로 필요하다.** 글·댓글 생성 시 활성 프로필이 없을 때 쓴다([../api-contract.md §5.1](../api-contract.md)). `S001`(503)은 내부 API 호출 실패에 쓴다.

**완료 기준**
- [ ] `ApiResponse`, `ErrorResponse`, `PageResponse`, `BaseTimeEntity`가 auth·member-service와 **구조가 동일**하다
- [ ] `ErrorCode`에 member 전용 코드(`M0xx`)·auth 전용 코드(`AU0xx`)가 **없다**
- [ ] `S002`가 403이고 메시지가 [../api-contract.md §8.3](../api-contract.md)과 일치한다
- [ ] 코드·HTTP·메시지가 [../api-contract.md §8.1 §8.3](../api-contract.md)과 일치한다
- [ ] 복제 파일 상단에 정본 주석이 있다
- [ ] **springdoc이 OpenAPI 문서를 생성한다.** `/v3/api-docs`가 문서를 돌려주고 `SwaggerConfig`가 등록된다
- [ ] `/swagger-ui.html`이 **인증 없이** 열리는 것은 이 항목의 기준이 아니다. `SecurityConfig`가 없으면 Boot 기본 필터가 전 경로를 401로 막는다([../security.md §5.1.1](../security.md)). 보안 기반 항목에서 확인한다

**검증** — `GlobalExceptionHandlerTest` (`@WebMvcTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| `BusinessException(P001)` | 404 `P001` |
| `BusinessException(P002)` | 403 `P002` |
| `@Valid` 실패 | 400 `C001`, `fieldErrors` 존재 |
| 성공 응답 | `success = true`, `error = null` |
| 예상치 못한 예외 | 500 `C005`, 스택트레이스 없음 |
| **타입 불일치 파라미터** | 400 `C002` |
| **없는 HTTP 메서드** | 405 `C003` |
| **매핑 없는 경로** | 404 `C004` |
| **필수 파라미터 누락** | 400 `C001`, `fieldErrors` **빈 배열** |
| **본문이 있는데 `Content-Type` 없음** | **415 `C006`.** 500 이 아니고 `log.error` 를 남기지 않는다 |
| **`Accept: application/xml`** | **406 `C007`** |
| **마지막 그물의 로그 수준** | **`ERROR`.** `warn` 으로 낮추면 500 이 ERROR 경보를 전혀 만들지 않는다 ([../conventions.md §6.1](../conventions.md)) |

---

### B-03 도메인 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-02 |
| 참조 | [../domain-model.md §4 §5](../domain-model.md), [../conventions.md §2](../conventions.md), [../requirements/board.md §3 §4 §5](../requirements/board.md) |

**두 엔티티와 도메인 메서드를 여기서 전부 만든다.** 기능 단계에 남겨두면 여러 항목이 같은 엔티티 파일을 고치게 된다.

**산출물**
- `post/entity/Post.java`, `post/repository/PostRepository.java`
- `post/support/PostReader.java` (find or throw — `P001`)
- `comment/entity/Comment.java`, `comment/repository/CommentRepository.java`
- `db/migration/V1__create_post.sql`, `V2__create_comment.sql`
- `build.gradle` 수정 — test 태스크에 `systemProperty 'spring.profiles.active', 'test'` ([../tech-stack.md §5.1](../tech-stack.md))

`build.gradle`은 B-01 산출물이지만 **이 항목에서 고치는 것이 허용된다**(§2.5). 해당 한 줄에 한정한다. `application-test.yml`의 `ddl-auto: validate`는 B-01이 이미 넣었다.

**도메인 메서드** — 전부 이 항목에서 구현한다.

| 메서드 | 동작 |
| --- | --- |
| `Post.update(title, content)` | 제목·내용 변경. `writerId`·`writerNickname` 불변 |
| `Post.softDelete()` | `deleted = true` |
| `Post.increaseViewCount()` | 조회수 +1 |
| `Post.increaseCommentCount()` / `decreaseCommentCount()` | 댓글 수 증감. **음수가 되지 않는다** |
| `Comment.update(content)` | 내용 변경 |
| `Comment.softDelete()` | `deleted = true` |

**`CommentRepository.softDeleteByPostId(Long postId)`를 여기서 만든다.** B-07(게시글 삭제)이 댓글을 연쇄 삭제할 때 쓴다. 이것이 없으면 B-07이 B-08의 산출물을 기다리게 된다.

**완료 기준**
- [ ] Flyway가 `post`, `comment` 테이블을 생성한다
- [ ] 컬럼이 [../domain-model.md §4](../domain-model.md)과 일치한다
- [ ] **`post.writer_id`, `comment.writer_id`에 FK 제약이 없다**
- [ ] `post.content`가 `TEXT` 타입이다
- [ ] `idx_post_created_at`, `idx_post_writer_id`, `idx_post_title`, `idx_comment_post_id`가 있다
- [ ] `view_count`, `comment_count` 기본값이 0이다
- [ ] 위 표의 도메인 메서드 6개가 모두 구현되어 있다
- [ ] `decreaseCommentCount()`가 0에서 호출돼도 음수가 되지 않는다 — **이 가드는 B-10 이후 운영 경로를 지키지 않는다.** 집계 갱신이 좁은 UPDATE 로 바뀌어 엔티티를 지나지 않으므로 **운영의 음수 방지는 그 문장의 `where` 절**에 있다(B-10). 이 기준은 메서드가 그 자리에 남아 있는 한 그대로 유효하다
- [ ] `CommentRepository.softDeleteByPostId()`가 동작한다
- [ ] Entity에 `@Setter`·`@Data`가 없다
- [ ] **`@DataJpaTest` 클래스에 `@AutoConfigureTestDatabase(replace = NONE)`이 붙어 있다** ([../tech-stack.md §5.2](../tech-stack.md))
- [ ] **테스트 DataSource URL이 [../tech-stack.md §5.3](../tech-stack.md)의 정본과 일치한다** — `DATABASE_TO_LOWER`·`CASE_INSENSITIVE_IDENTIFIERS`·`DB_CLOSE_DELAY=-1` 포함
- [ ] **테스트가 그 URL로 돈다.** `jdbc:h2:mem:<uuid>`가 아니다
- [ ] **`ddl-auto: validate`가 실제로 적용된다.** 엔티티에만 있는 컬럼을 넣는 변이에서 `SchemaManagementException`으로 기동이 실패하는 것으로 확인한다 — **검증표에 넣지 않는다**(테스트가 자기 엔티티를 바꿀 수 없다, [../process/review-policy.md §5.3](../process/review-policy.md))
- [ ] **엔티티와 마이그레이션의 컬럼 폭이 일치한다.** `information_schema` 의 실제 폭을 읽어 비교하는 테스트로 고정한다 — **`ddl-auto: validate` 는 폭을 보지 않는다**([../domain-model.md §4](../domain-model.md)의 주의, [../tech-stack.md §5.2](../tech-stack.md)). board 는 입력 규칙과 컬럼 폭이 같아 여유가 없다

**검증** — `PostRepositoryTest`, `CommentRepositoryTest` (`@DataJpaTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| 저장 후 조회 | 모든 필드 일치 |
| **존재하지 않는 `writer_id`로 저장** | **성공** (FK 제약 없음) |
| 저장 시 | `viewCount=0`, `commentCount=0`, `deleted=false` |
| 10,000자 content 저장 | 성공 |
| `update()` 호출 | 제목·내용만 변경, `writerId` 불변 |
| `increaseViewCount()` 2회 | `viewCount = 2` |
| `increaseCommentCount()` 3회 후 `decrease` 1회 | `commentCount = 2` |
| **`decreaseCommentCount()` (count=0)** | **0 유지, 음수 아님** |
| `softDeleteByPostId()` | 해당 게시글의 댓글 전부 `deleted = true` |
| `PostReader`로 없는 id 조회 | `BusinessException(P001)` |
| 테스트 실행 중 DataSource URL | [../tech-stack.md §5.3](../tech-stack.md)의 정본과 문자열 일치 |
| 저장된 테이블명 | **소문자** `post`·`comment`. `DATABASE_TO_LOWER` 효과 |
| **`information_schema` 의 실제 폭** | `post.title` **200**, `comment.content` **500**, 양쪽 `writer_nickname` **30**. 엔티티 선언과 일치 |

---

### B-04 보안 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-02 |
| 병렬 | B-03과 동시 진행 가능 (`global/*` vs `post/*`·`comment/*`) |
| 참조 | [../api-contract.md §4 §5 §6](../api-contract.md), [../tech-stack.md §3.2](../tech-stack.md), [../security.md §2 §5 §6](../security.md), [../conventions.md §1.3](../conventions.md) |

**산출물**
- `global/security/LoginMember.java` (record: **`accountId`, `role`**)
- `global/security/RoleClaimConverter.java`
- `global/security/CurrentMemberArgumentResolver.java`, `@CurrentMember`
- `global/config/SecurityConfig.java` — **[../api-contract.md §4](../api-contract.md)의 전체 경로 인가**, CORS, STATELESS
- `src/main/resources/jwt-public.pem` (**실제 공개키. 이미 배치되어 있다**)
- `src/test/java/.../TestTokenFactory.java`
- **`client/MemberClient.java`** — 내부 API 호출 + 실패 판정
- **`client/dto/MemberBulkRequest.java`, `MemberSummaryResponse.java`** (board가 자체 정의, [../conventions.md §3](../conventions.md))

**Spring Security `oauth2-resource-server`를 사용한다. JWT 필터를 직접 만들지 않는다.**

**⚠ `LoginMember`에 `nickname`이 없다.** JWT Claim에서 빠졌기 때문이다([../api-contract.md §6](../api-contract.md)). 작성자 닉네임은 `MemberClient`로 얻는다.

**`MemberClient`를 여기서 만든다.** B-05·B-08이 호출만 하도록 기반 단계에 둔다. **M-10(제공 측)을 기다리지 않는다** — 스텁으로 테스트하고 실제 연동은 I-01에서 확인한다. 기다리면 board 전체가 member의 임계 경로에 묶인다.

**`MemberClient`의 실패 판정** — [../api-contract.md §5.1](../api-contract.md)이 정본이다. **HTTP 404를 업무 의미로 쓰지 않는다.**

| member 응답 | 처리 |
| --- | --- |
| 200, 결과에 `deleted = false` | 닉네임 반환 |
| 200, 결과에서 제외됨 / `deleted = true` | `BusinessException(S002)` — 403 |
| 그 밖의 모든 응답 (4xx, 5xx, 타임아웃, 파싱 실패) | `BusinessException(S001)` — 503. **경보 대상** |

타임아웃은 **connect 1초 / read 3초**다([../nfr.md §3](../nfr.md)). 재시도·서킷브레이커는 1차 범위 밖이다.

**공개키는 이미 배치되어 있다.** AU-04를 기다리지 않는다. I-01에서 두 사본의 일치와 실제 발급 토큰 수용을 확인한다.

**완료 기준**
- [ ] [../api-contract.md §6](../api-contract.md) 스펙의 토큰에서 `accountId`, `role`을 추출한다
- [ ] **`LoginMember`에 `nickname` 필드가 없다**
- [ ] `MemberClient`가 **벌크 엔드포인트 하나만** 호출한다
- [ ] `X-Internal-Api-Key` 헤더를 싣는다. 키는 **기본값 없이** 주입된다
- [ ] connect 1초 / read 3초 타임아웃이 설정되어 있다. **기본값(무제한)이 아니다**
- [ ] **위 표의 세 분기가 전부 구현되어 있다**
- [ ] **404가 `S002`가 아니라 `S001`로 간다**
- [ ] 서명이 잘못된 토큰 → 401 `A002`
- [ ] 만료된 토큰 → 401 `A003`
- [ ] 토큰 없이 보호 경로 → 401 `A001`
- [ ] `role` claim이 `GrantedAuthority`로 변환된다
- [ ] JWT 검증 필터를 직접 구현하지 않았다
- [ ] [../api-contract.md §4](../api-contract.md)의 **모든 경로**에 인가 규칙이 선언되어 있다
- [ ] 비로그인 허용 경로(`GET /posts`, `GET /posts/{id}`, 댓글 목록)가 토큰 없이 통과한다
- [ ] **`/swagger-ui/**`·`/v3/api-docs/**`가 `permitAll`이고 인증 없이 열린다** ([../security.md §5.1.1](../security.md))
- [ ] `/actuator/health` 외의 actuator 경로가 노출되지 않는다
- [ ] 세션이 생성되지 않는다

**검증** — `JwtAuthenticationTest` (`@SpringBootTest` + MockMvc)

| 케이스 | 기대 결과 |
| --- | --- |
| 유효 토큰으로 `POST /posts` | 401이 아님 |
| 토큰 없이 `POST /posts` | 401 `A001` |
| 서명 변조 토큰 | 401 `A002` |
| 만료 토큰 | 401 `A003` |
| `role = ADMIN` 토큰 | `ROLE_ADMIN` 권한 보유 |
| 토큰 없이 `GET /posts` | 401이 아님 |
| `LoginMember` 필드 목록 | **`nickname` 없음** |
| **토큰 없이 `/swagger-ui.html`** | **302 → `/swagger-ui/index.html`.** `/login` 으로 가면 실패 |
| **토큰 없이 `/swagger-ui/index.html`** | **200** |
| **토큰 없이 `/v3/api-docs`** | **200, OpenAPI 문서** |
| `/actuator/env` | **무토큰 401 `A001`, 유효 토큰 403 `A004`.** 404 가 아니다 |

**`MemberClientTest`** — 스텁 서버로 응답을 흉내 낸다

| 스텁 응답 | 기대 결과 |
| --- | --- |
| 200 + `data.members` 에 `{accountId:3, nickname:"홍길동", deleted:false}` | 닉네임 `"홍길동"` 반환 |
| 200 + `data.members` 가 빈 배열 (결과에서 제외됨) | `BusinessException(S002)` |
| 200 + `data.members` 에 `{accountId:3, deleted:true}` | `BusinessException(S002)` |
| **404 (경로 오설정)** | **`BusinessException(S001)`. `S002` 아님** |
| **401 (API 키 거부)** | **`BusinessException(S001)`** |
| 500 | `BusinessException(S001)` |
| 응답 없음 (타임아웃) | `BusinessException(S001)` |
| 본문 파싱 실패 | `BusinessException(S001)` |
| 요청 헤더 | `X-Internal-Api-Key` 존재 |

> **스텁 응답은 [../api-contract.md §5](../api-contract.md)의 봉투를 그대로 쓴다.** `{"success": true, "data": {"members": [...]}, "error": null}` 이고 **배열이 최상위가 아니다.** 봉투를 빼고 스텁을 쓰면 `MemberClientTest` 는 통과하지만 M-10 이 실제로 돌려주는 모양과 달라 I-01 에서 깨진다 — 그 어긋남은 §5.1 이 "본문 파싱 실패 → `S001`" 로 분류하므로 **board 가 전 사용자의 쓰기를 멈춘 뒤에야 드러난다.**

> **404 케이스를 반드시 넣는다.** 이것을 `S002`로 처리하면 경로 오설정이 "프로필 없음"으로 위장되어, 경보 없이 전 사용자의 쓰기가 멈춘다.

---

### B-05 게시글 작성·상세 조회 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-03, B-04 |
| 참조 | [../requirements/board.md §1 §3 §3.0 §4](../requirements/board.md) (P-01, P-04, P-05), [../api-contract.md §4 §5.1](../api-contract.md) |

**산출물**
- `post/dto/PostCreateRequest.java`, `PostResponse.java`, `PostDetailResponse.java`
- `post/service/PostService.java` (생성)
- `post/controller/PostController.java` (생성)

`MemberClient`는 B-04 산출물이다. **이 항목에서 만들지 않고 호출만 한다.**

**⚠ 닉네임 취득 경로가 바뀌었다.** `writer_id`는 JWT Claim에서, **`writer_nickname`은 `MemberClient`에서** 가져온다. Claim에 `nickname`이 없기 때문이다.

**⚠ 원격 호출은 `@Transactional` 밖에서 먼저 한다.** [../architecture.md §5](../architecture.md)가 트랜잭션 안의 원격 호출을 금지한다. 순서는 `조회 -> 성공 확인 -> BEGIN -> INSERT -> COMMIT`이다.

**완료 기준**
- [ ] `POST /api/v1/posts`가 201을 반환한다
- [ ] **`writer_id`를 검증된 JWT의 `sub`에서 가져온다**
- [ ] **`writer_nickname`을 `MemberClient` 응답에서 가져온다**
- [ ] **조회 키가 JWT의 `sub`다.** 요청 본문의 `writerId`로 조회하지 않는다
- [ ] 요청 본문에 `writerId`·`nickname`을 넣어도 무시된다
- [ ] **프로필이 없거나 탈퇴했으면 403 `S002`이고 글이 저장되지 않는다**
- [ ] **member 호출이 실패하면 503 `S001`이고 글이 저장되지 않는다**
- [ ] **원격 호출이 DB 트랜잭션 밖에서 일어난다**
- [ ] 수정 경로는 `MemberClient`를 호출하지 않는다 (B-07)
- [ ] `GET /api/v1/posts/{id}`가 [../api-contract.md §4.3](../api-contract.md)의 상세 모양을 반환한다 (비로그인 허용)
- [ ] 상세 조회 시 `view_count`가 1 증가한다 (`Post.increaseViewCount()` 사용 — **갱신 수단은 B-11이 좁은 UPDATE로 대체한다.** 그쪽 완료 기준이 이 괄호를 이긴다)
- [ ] 삭제된 게시글·없는 id 조회 시 404 `P001`
- [ ] 제목 201자·내용 10,001자는 400 `C001`

**검증** — `PostServiceTest`, `PostControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 작성 | 201, DB 저장됨 |
| 저장된 `writer_id` | JWT `sub`와 일치 |
| 저장된 `writer_nickname` | **`MemberClient` 응답값과 일치** |
| 요청 본문에 `writerId: 999` 전달 | 저장된 값은 Claim의 `sub`. **999로 조회하지도 않음** |
| 요청 본문에 `nickname: "가짜"` 전달 | 저장된 값은 `MemberClient` 응답값 |
| **프로필 미등록 계정으로 작성** | **403 `S002`. `post` 행 0개** |
| **탈퇴한 프로필로 작성** | **403 `S002`. `post` 행 0개** |
| **member 타임아웃** | **503 `S001`. `post` 행 0개** |
| **member가 404 반환 (경로 오설정)** | **503 `S001`.** `S002` 아님 |
| 원격 호출 시점 | **트랜잭션 시작 전** |
| 토큰 없이 작성 | 401 `A001` |
| 상세 조회 (비로그인) | 200. **`MemberClient` 호출 0회** |
| 상세 조회 2회 | `viewCount = 2` |
| 없는 id / 삭제된 게시글 | 404 `P001` |
| **상세 응답 키 집합** | `id`·`title`·`content`·`writerId`·`writerNickname`·`viewCount`·`commentCount`·`createdAt` **정확히 여덟.** `deleted`·`updatedAt` 없음 |
| 제목 201자 / 공백만 | 400 `C001` |

---

### B-06 게시글 목록과 QueryDSL 검색 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-05 |
| 공유 파일 | `PostService`, `PostController` (B-05 생성) |
| 참조 | [../requirements/board.md §1 §4 §6](../requirements/board.md) (P-02, P-03), [../api-contract.md §4.1 §7.1](../api-contract.md), [../nfr.md §1](../nfr.md) |

**산출물**
- `post/dto/PostSearchCondition.java`, `SearchType.java`, `PostSortType.java`
- `post/repository/PostQueryRepository.java` (QueryDSL)
- `PostService`·`PostController` 확장

**완료 기준**
- [ ] `GET /api/v1/posts`가 페이징 응답을 반환한다 ([../api-contract.md §7.1](../api-contract.md) 형식)
- [ ] 기본 `size` 10, 51 요청 시 50으로 절삭. **기본 `sort`는 `latest`다** ([../api-contract.md §4.1](../api-contract.md))
- [ ] `sort=latest`, `sort=views`가 동작한다
- [ ] 삭제된 게시글이 목록에서 제외된다
- [ ] 4가지 `searchType`이 모두 동작한다
- [ ] `keyword`가 없으면 전체 목록
- [ ] `searchType`만 있고 `keyword`가 없으면 400 `C001`
- [ ] **목록 조회 시 member-service를 호출하지 않는다**
- [ ] 정렬 파라미터로 임의 컬럼명을 넣을 수 없다 (Enum 화이트리스트)
- [ ] **동률이 있어도 페이지 경계가 안정적이다.** `id`가 마지막 정렬 키다 ([../api-contract.md §4.1 §7.1](../api-contract.md))
- [ ] **`keyword`만 있고 `searchType`이 없으면 400 `C001`이다.** 조용히 무시하지 않는다 ([../api-contract.md §4.1](../api-contract.md))
- [ ] **`page`·`size` 하한 위반이 400 `C001`이고 `fieldErrors`에 파라미터명이 담긴다** ([../requirements/board.md §4](../requirements/board.md), [../api-contract.md §4.1 §2.3](../api-contract.md)). **500이 아니다**

**검증** — `PostQueryRepositoryTest` (`@DataJpaTest`), `PostControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 15건 저장 후 목록 조회 | 10건, `totalElements = 15` |
| `size=51` | 50건 이하 |
| `sort=latest` / `sort=views` | 각각 내림차순 |
| `sort` 미전달 | `latest`와 같은 순서. 기본값을 `views`로 바꾸면 깨진다 |
| 삭제 게시글 포함 상태 | 삭제분 제외 |
| `searchType=TITLE&keyword=공지` | 제목 포함분만 |
| `searchType=CONTENT` / `TITLE_CONTENT` | 각 기준 |
| `searchType=WRITER&keyword=홍길동` | `writer_nickname` 기준 |
| `keyword` 없이 조회 | 전체 |
| `searchType=TITLE`만 전달 | 400 `C001`, `fieldErrors` **빈 배열**(요청 수준) |
| `sort=password` | 400 |
| `created_at`이 **같은** 글 다수를 1·2페이지로 조회 | 중복·누락 **없음**. 시각을 직접 박아 동률을 만든다 |
| `view_count`가 **전부 0**인 목록을 1·2페이지로 조회 | 중복·누락 **없음** |
| `keyword=공지`만 전달 | **400 `C001`**, `fieldErrors` **빈 배열**(요청 수준) |
| `searchType=TITLE&keyword=`(공백만) | **400 `C001`** |
| `size=0` / `page=-1` | **400 `C001`**, `fieldErrors` **1건**(파라미터명). 500 `C005`가 아니다 |

---

### B-07 게시글 수정·삭제와 권한 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-06 |
| 공유 파일 | `PostService`, `PostController` — B-06 완료 후 시작 |
| 참조 | [../requirements/board.md §1 §5 §7](../requirements/board.md) (P-06, P-07), [../security.md §5](../security.md) |

**산출물**
- `post/dto/PostUpdateRequest.java`
- `PostService`·`PostController` 확장

**게시글 삭제 시 댓글 연쇄 삭제**는 B-03이 만든 `CommentRepository.softDeleteByPostId()`를 호출한다. **B-08을 기다리지 않는다.**

**완료 기준**
- [ ] `PUT /api/v1/posts/{id}`를 작성자 본인만 수정할 수 있다 (`Post.update()` 사용)
- [ ] 타인이 수정 시 403 `P002`
- [ ] **ADMIN도 수정할 수 없다** (403 `P002`)
- [ ] `DELETE /api/v1/posts/{id}`를 작성자 본인과 ADMIN이 삭제할 수 있다
- [ ] 삭제는 Soft Delete다 (`Post.softDelete()`)
- [ ] **게시글 삭제 시 하위 댓글도 `deleted = true`가 된다**
- [ ] **그 두 효과가 한 로컬 트랜잭션이다** ([../domain-model.md §5](../domain-model.md))
- [ ] 소유자 검증이 Service 계층에 있다
- [ ] 수정 시 `writer_id`, `writer_nickname`이 바뀌지 않는다

**검증** — `PostServiceTest`, `PostControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 본인 글 수정 | 200, 반영됨 |
| 타인 글 수정 | 403 `P002` |
| **ADMIN이 타인 글 수정** | **403 `P002`** |
| 수정 후 `writer_id` | 변경 없음 |
| 수정 후 `writer_nickname` | 변경 없음 |
| 본인 글 삭제 | 204, `deleted = true`, 행 존재 |
| ADMIN이 타인 글 삭제 | 204 |
| 타인(일반)이 삭제 | 403 `P002` |
| **게시글 삭제 후 하위 댓글** | **전부 `deleted = true`** |
| 삭제 중 예외 발생 | `post.deleted`와 댓글 `deleted` **둘 다** 롤백. **두 단언이 각각 반증 가능해야 한다** |
| **한 번의 삭제에 커밋이 정확히 한 번** | 변이 **셋**(A·B·C)을 돌린다. **C는 행위 단언으로 잡히지 않는다** ([../process/review-policy.md §4.1](../process/review-policy.md)) |
| 없는 글 수정 | 404 `P001` |
| **타인의 삭제된 글** 수정 | **404 `P001`.** 403 `P002`가 아니다 ([../api-contract.md §4.4](../api-contract.md)). **행이 없는 id로는 선후가 관측되지 않는다** |
| **타인의 삭제된 글** 삭제 (**호출자는 일반 `USER`**) | **404 `P001`.** §4.4는 수정과 **삭제**를 함께 못박는다. **한 행이 변이 둘을 잡는다** — 권한 판정을 앞으로 옮기면 403이 되고, 조용히 204를 돌려주면 204가 된다. **ADMIN으로 쓰면 앞의 변이가 숨는다** — 삭제가 ADMIN에게 열려 있어 순서를 뒤집어도 권한 판정을 통과한다 |
| 토큰 없이 수정 | 401 `A001` |

---

### B-08 댓글 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-05 |
| 참조 | [../requirements/board.md §2 §3 §3.0 §5](../requirements/board.md) (C-01~C-04), [../domain-model.md §4.2 §5](../domain-model.md), [../api-contract.md §5.1](../api-contract.md) |

**산출물**
- `comment/dto/*`
- `comment/service/CommentService.java`
- `comment/controller/CommentController.java`

`Comment` 엔티티·리포지토리는 B-03 산출물이다. **이 항목에서 만들지 않는다.** `comment/*`만 쓰므로 `PostService`를 건드리지 않는다.

**댓글 작성도 `MemberClient`를 호출한다.** 게시글과 같은 규칙이다 — `writer_id`는 Claim, `writer_nickname`은 내부 API, 호출은 트랜잭션 밖. **수정·삭제는 호출하지 않는다.**

**완료 기준**
- [ ] 댓글 작성 시 `post.comment_count`가 1 증가한다 (`Post.increaseCommentCount()` 사용 — **갱신 수단은 B-10이 좁은 UPDATE로 대체한다.** 그쪽 완료 기준이 이 괄호를 이긴다)
- [ ] **댓글 INSERT 와 `comment_count` 갱신이 한 로컬 트랜잭션이다** ([../domain-model.md §5](../domain-model.md))
- [ ] 댓글 삭제 시 1 감소한다
- [ ] **`comment_count`가 음수가 되지 않는다**
- [ ] 작성자 본인만 수정, 본인·ADMIN이 삭제할 수 있다
- [ ] 삭제는 Soft Delete다
- [ ] **`writer_id`는 JWT `sub`, `writer_nickname`은 `MemberClient` 응답에서 가져온다**
- [ ] **프로필이 없거나 탈퇴했으면 403 `S002`이고 댓글이 저장되지 않는다**
- [ ] **member 호출 실패 시 503 `S001`이고 댓글이 저장되지 않는다**
- [ ] **원격 호출이 DB 트랜잭션 밖에서 일어난다.** `comment_count`도 증가하지 않는다
- [ ] 댓글 수정·삭제는 `MemberClient`를 호출하지 않는다
- [ ] 없는 게시글에 댓글 작성 시 404 `P001`. **목록 조회도 404 `P001`이다** ([../api-contract.md §4.5](../api-contract.md))
- [ ] 댓글 목록이 등록순 페이징(기본 20)으로 반환된다. **`created_at ASC, id ASC`다** ([../api-contract.md §7.1](../api-contract.md))
- [ ] **삭제된 댓글이 목록에서 제외된다** ([../requirements/board.md §5](../requirements/board.md) 규칙 1)
- [ ] **응답이 §4.5 의 다섯 키다** ([../api-contract.md §4.5](../api-contract.md)). `deleted`·`postId`·`updatedAt`을 넣지 않는다

**검증** — `CommentServiceTest`, `CommentControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 댓글 작성 | 201, `comment_count = 1` |
| 저장된 `writer_nickname` | `MemberClient` 응답값과 일치 |
| **프로필 미등록 계정으로 작성** | **403 `S002`. 댓글 0개, `comment_count` 불변** |
| **member 타임아웃** | **503 `S001`. 댓글 0개, `comment_count` 불변** |
| **member가 404 반환** | **503 `S001`** |
| 댓글 저장 중 예외 발생 | 댓글과 `comment_count` **둘 다** 롤백. **두 단언이 각각 반증 가능해야 한다** |
| **한 번의 작성에 커밋이 정확히 한 번** | 변이 **셋**(A·B·C)을 돌린다. **C는 행위 단언으로 잡히지 않는다** ([../process/review-policy.md §4.1](../process/review-policy.md)) |
| 댓글 수정·삭제 시 `MemberClient` | **호출 0회** |
| 댓글 목록 조회 시 `MemberClient` | **호출 0회** |
| 댓글 3개 작성 후 1개 삭제 | `comment_count = 2` |
| 같은 댓글 2회 삭제 시도 | `comment_count` 음수 안 됨 |
| 목록 조회 | 등록순, 기본 20건 |
| 삭제된 댓글 포함 상태 | **목록에서 제외**([../requirements/board.md §5](../requirements/board.md) 규칙 1). 건수 쿼리도 제외한다 |
| 댓글 응답 키 집합 | **다섯 키 정확히**([../api-contract.md §4.5](../api-contract.md)). 리터럴 집합으로 대조한다 |
| 없는·삭제된 게시글의 댓글 목록 | **404 `P001`.** 빈 페이지 200이 아니다 ([../api-contract.md §4.5](../api-contract.md)) |
| 목록 `size=0` / `page=-1` | **400 `C001`**, `fieldErrors` **1건**(파라미터명). 500 `C005`가 아니다 ([../api-contract.md §4.5 §4.1](../api-contract.md)) |
| `created_at`이 **같은** 댓글 다수 | 등록순이 `id`로 결정된다. 중복·누락 없음 |
| 본인 댓글 수정 | 200 |
| 타인 댓글 수정 | 403 `CM002` |
| ADMIN이 타인 댓글 수정 | 403 `CM002` |
| ADMIN이 타인 댓글 삭제 | 204 |
| 없는 게시글에 댓글 | 404 `P001` |
| **타인의 삭제된 댓글** 수정 | **404 `CM001`.** 403 `CM002`가 아니다 ([../api-contract.md §4.4](../api-contract.md)). **행이 없는 id로는 선후가 관측되지 않는다** |
| **타인의 삭제된 댓글** 삭제 (**호출자는 일반 `USER`**) | **404 `CM001`.** 수정 경로의 테스트가 삭제 경로를 덮지 않는다 — B-07에서 변이 둘이 그 공백을 통과했다. **ADMIN으로 쓰면 순서 변이가 숨는다** |
| 501자 댓글 | 400 `C001` |

---

### B-09 내가 쓴 글과 마무리 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-07, B-08 |
| 공유 파일 | `PostService`, `PostController` |
| 참조 | [../requirements/board.md §1](../requirements/board.md) (P-08), [../nfr.md](../nfr.md) |

**산출물**
- `PostService`·`PostController` 확장 (내가 쓴 글)
- `README.md` 갱신, Actuator·`application-prod.yml`

**완료 기준**
- [ ] 내가 쓴 글 목록이 `writer_id` 기준으로 페이징 조회된다. **마지막 정렬 키가 `id`다** ([../api-contract.md §7.1](../api-contract.md))
- [ ] **`page`·`size` 하한 위반이 400 `C001`이고 `fieldErrors`에 파라미터명이 담긴다** ([../api-contract.md §4.1](../api-contract.md), [../requirements/board.md §4](../requirements/board.md)). **500 `C005`가 아니다** — B-06은 하한을 `PostController.getList`의 `@Min` **한 자리**에서 집행한다. `PostSearchCondition.of`를 쓰면서 그 제약을 빠뜨리면 `size=0`이 `PageRequest.of`를 거쳐 500이 된다
- [ ] 삭제된 글은 제외된다
- [ ] `README.md`에 실행 절차와 환경변수가 적혀 있다
- [ ] `/actuator/health`만 노출된다
- [ ] `prod` 프로파일에서 Swagger·SQL 로그가 꺼진다
- [ ] 전체 테스트가 통과한다
- [ ] 목록 조회 쿼리에 N+1이 없다. **관측 수단을 갖춘다** — 아래 블록인용의 형태다
- [ ] **`JwtValidators.createDefault()` 가 거는 검증기 집합이 테스트로 고정되어 있다.** B-04 의 `A002`·`A003` 판정이 그 집합에 걸려 있다 — 기본 둘 중 실제로 실패할 수 있는 것이 만료 하나라서 `JwtValidationException` 을 만료로 읽을 수 있다. **검증기가 하나 더 붙으면 그 검증기의 실패도 `JwtValidationException` 이 되어 만료가 아닌 사유가 조용히 `A003`(만료)으로 나간다.** `SecurityErrorResponder` 의 javadoc 이 그 전제를 적어 두었다. AU-11·M-11 이 같은 것을 못박았다 — 같은 모양으로 한다

> **쿼리 수를 예측값으로 쓰지 않는다.** "2회" 같은 상수를 단언하면 페이징 구현이 바뀔 때마다 숫자가 낡고, 그 숫자가 맞는지는 아무것도 증명하지 않는다([../process/review-policy.md §4.1](../process/review-policy.md)의 같은 금지다). **같은 조건에서 행 수만 바꾼 두 측정이 같은지** 본다 — 예를 들어 3건과 30건으로 각각 세어 두 값이 **같음**을 단언한다. N+1 이 생기면 행 수에 비례해 갈라진다.
>
> **관측 수단이 저장소에 없다.** Hibernate `Statistics`(`hibernate.generate_statistics` 를 **테스트 프로파일에만** 켜고 `getPrepareStatementCount()` 를 읽는 것)가 한 방법이다. 수단을 고르는 것은 구현의 몫이고, **고른 수단이 실제로 N+1 을 잡는지 측정해서 보고한다** — 일부러 지연 로딩 반복을 넣어 두 값이 갈라지는 것을 본다.
>
> **`Post` 에는 컬렉션이 없다.** `comment_count` 가 비정규화되어 있어([../domain-model.md §4.1](../domain-model.md)) 지금은 N+1 이 날 자리가 없다. 그래서 이 항목은 **회귀 가드**다 — 나중에 연관관계를 더하는 사람이 목록을 깨뜨리는 것을 잡는다.

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| 내 글 5건 + 타인 글 3건 | 5건만 반환 |
| 내 글 중 삭제분 포함 | 삭제분 제외 |
| 토큰 없이 호출 | 401 `A001` |
| 내 글 목록에 `size=0` / `page=-1` | **400 `C001`**, `fieldErrors` **1건**(파라미터명). 500이 아니다 |
| 목록 조회 쿼리 수 | **게시글 수와 무관하게 일정.** 아래 방식으로 관측한다 |
| `/actuator/env` | **무토큰 401 `A001`, 유효 토큰 403 `A004`.** 404 가 아니다 |

### B-10 comment_count 소실 갱신 [결함 수정]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-08 (I-03 리뷰가 발견했다) |
| 공유 파일 | `Post`, `CommentService` — B-03·B-08 산출물 |
| 참조 | [../requirements/board.md §2 §5](../requirements/board.md) (C-01, C-04), [../api-contract.md §4.5](../api-contract.md), [../domain-model.md §5](../domain-model.md), [../nfr.md §1](../nfr.md) |

**I-03 리뷰 실측.** 같은 게시글에 댓글을 동시에 쓰면 **성공한 커밋들 사이에서 `comment_count` 증가가 소실된다** — 동시 커밋 2건 이상인 **6개 게시글에서 6/6** 어긋났고(201 4건에 증가 2, 201 11건에 증가 10), 외부에서 관측된다(`commentCount: 10` vs 댓글 목록 `totalElements: 11`). 순차·단건은 어긋나지 않는다.

**한계가 아니라 결함이다.** C-01("댓글 작성 시 `commentCount` 증가")과 §4.5("`comment_count`와 목록의 `totalElements`가 같다")를 깨므로 **동시 쓰기 기준의 부재로 면제되지 않는다.** 교착(500)과 달리 **아무 오류 없이 틀린 수를 남긴다**([../AGENTS.md](../AGENTS.md) 불변식 9).

**원인은 read-modify-write다.** 엔티티를 읽어 메모리에서 증가시키고 더티 체킹이 **변경되지 않은 컬럼까지 전부** 싣는 UPDATE로 낡은 스냅샷째 덮어쓴다(실패 statement가 `update post set comment_count=?,content=?,deleted=?,title=?,...` 였다).

**이 항목이 B-08 완료 기준 1의 `Post.increaseCommentCount()` 요구를 대체한다.** 엔티티 메서드를 쓰면 flush 때 더티 체킹이 전체 컬럼 UPDATE를 발행하므로 둘을 함께 만족시킬 수 없다 — **B-10의 요구가 이긴다.**

**산출물**
- `post/repository/PostRepository` — `comment_count` 갱신을 **좁은 UPDATE**로 바꾼다 (`comment_count = comment_count + 1` / `- 1`)
- `comment/service/CommentService` · `post/entity/Post` — 호출 지점과 엔티티 메서드 **역할 재서술**

> **`Post.increaseCommentCount()`·`decreaseCommentCount()` 를 지우지 않는다.** B-03 이 네 군데서 그 존재를 요구한다 — 도메인 메서드 표, 완료 기준 "표의 도메인 메서드 **6개**가 모두 구현되어 있다", 완료 기준 "`decreaseCommentCount()`가 0에서 호출돼도 음수가 되지 않는다", 검증표 두 행. **§1.1 의 결함 수정 면제는 경로 소유에 대한 것이고 완료 기준에 대한 것이 아니다**(B-10 이 대체한다고 적은 것도 B-08 완료 기준 1 의 **갱신 수단**이다).
>
> **대신 주석으로 막는다** — 두 메서드와 `commentCount` 필드에 "댓글 작성·삭제 경로는 이 메서드를 쓰지 않는다. 집계 동기화는 `PostRepository` 의 좁은 UPDATE 가 하고 음수 방지는 그 문장의 `where` 절에 있다. **집계를 이 메서드로 바꾸면 결함이 돌아온다**" 를 적는다.
>
> **지우려면 D 항목이 먼저다.** 커버리지가 막는 것은 아니다 — 두 테스트의 주제(집계가 컬럼에 남는다 / 음수 가드)가 모두 `CommentServiceTest` 로 옮겨 가 측정됐다(B-10 실측). 막는 것은 **B-03 의 문구**이므로, 지우는 쪽으로 가려면 B-03 의 표·완료 기준 둘·검증표 두 행을 먼저 고치고 그 다음 코드 세 지점(엔티티 메서드 둘, `PostRepositoryTest` 두 테스트, `PostServiceTest` 의 픽스처)을 손본다. **1차에서는 하지 않는다.**

**기반 소유 경로를 고치는 것이 이 항목의 범위다.** §2.1이 `*/entity/`·`*/repository/`를 B-03 소유로 두고 기능 단계에 읽기 전용으로 배정했지만, **결함 수정 단계는 그 제약을 받지 않는다**(§1.1). 고친 뒤 B-03의 완료 기준이 깨지지 않는지 확인한다.

**완료 기준**
- [ ] **동시 커밋에서 `comment_count`가 소실되지 않는다.** 활성 댓글 수와 같다
- [ ] 갱신이 **좁은 UPDATE**다 — 엔티티 더티 체킹의 전체 컬럼 UPDATE가 아니다
- [ ] 삭제도 같은 모양이고 **`comment_count`가 음수가 되지 않는다**(C-04, §5)
- [ ] **B-08의 트랜잭션 경계가 유지된다** — 댓글 INSERT와 집계 갱신이 한 로컬 트랜잭션이고 커밋이 정확히 한 번이다
- [ ] **기존 테스트가 깨지지 않는다**

**검증** — `CommentServiceTest` 확장

| 케이스 | 기대 결과 |
| --- | --- |
| **같은 게시글에 동시 작성 N건** | `comment_count` = 활성 댓글 수. **엔티티 증가로 되돌리면 깨진다** |
| **같은 게시글에 동시 삭제 N건** | 같음 |
| 같은 댓글 2회 삭제 | `comment_count` 음수 안 됨 |
| 발행된 UPDATE의 모양 | **`comment_count`만 싣는다.** `title`·`content`가 실리지 않는다 |
| 한 번의 작성에 커밋 | **정확히 한 번**(B-08의 경계 관측을 그대로 쓴다) |

> **소실 갱신은 DB가 아니라 애플리케이션에서 일어난다.** 두 트랜잭션이 각각 엔티티를 읽어 메모리에서 증가시키면 마지막 쓰기가 이긴다 — **H2에서도 재현된다.** 그래서 이 검증은 실제 MySQL이 필요하지 않다. 다만 **두 읽기가 두 쓰기보다 먼저 일어나도록** 끼워넣기를 강제해야 한다(래치 등). **강제는 결정성의 보장이다 — 강제가 없으면 반드시 공허해진다는 뜻이 아니다.** B-10 리뷰가 집결지를 무력화하고 엔티티 증가 변이와 조합해 **7회 반복 / 14개 관측**을 모았는데 전부 같은 값으로 빨개졌다(0회도 중간값도 없었다). 창이 넓어서다 — 첫 스레드가 SELECT→UPDATE→INSERT→COMMIT 을 끝내는 동안 나머지는 SELECT 만 들어가면 되고, H2 의 행 락이 뒤의 UPDATE 를 첫 커밋까지 잡는다. **그것은 이 기계의 스케줄 관측이고 보장이 아니므로** 강제는 그대로 요구한다.
>
> **교착은 이 항목의 대상이 아니다.** 좁은 UPDATE가 교착을 줄일 **수 있지만 측정되지 않았고**, 동시 쓰기 기준 자체가 1차에 없다([../nfr.md §1](../nfr.md)). **교착률을 이 항목의 완료 기준으로 삼지 않는다** — 재고 싶으면 보고에만 적는다.

---

### B-11 조회수 증가가 comment_count 를 덮어쓴다 [결함 수정]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-10 (B-10 구현 워커가 찾았다) |
| 공유 파일 | `PostService`·`PostRepository`·`Post` — B-05·B-10 산출물 |
| 참조 | [../requirements/board.md §1 §5](../requirements/board.md) (P-05), [../api-contract.md §4.3 §4.5](../api-contract.md), [../domain-model.md §4.1 §5](../domain-model.md), [../nfr.md §1](../nfr.md) |

**B-10 이 댓글 쓰기 경로를 고쳤지만 같은 불변식을 깨는 경로가 하나 더 남았다.** `PostService.getDetail`(상세 조회의 조회수 증가, P-05)이 관리 엔티티를 바꾸므로 **같은 전체 컬럼 UPDATE** 를 발행한다(측정값: `update post set comment_count=?,content=?,deleted=?,title=?,updated_at=?,view_count=?,writer_id=?,writer_nickname=? where id=?`). 그 트랜잭션이 읽은 `comment_count` 를 그대로 다시 쓰므로 **SELECT 와 flush 사이에 커밋된 댓글 작성의 증가가 조회 하나로 소실될 수 있다.**

**`view_count` 자체도 같은 성질이다** — 동시 조회 둘이 같은 값을 읽어 하나가 소실된다.

**산출물**
- `post/repository/PostRepository` — 조회수 증가를 **좁은 UPDATE** 로 (`view_count = view_count + 1`)
- `post/service/PostService` — `getDetail` 의 호출 지점

**완료 기준**
- [ ] **조회 하나가 `comment_count` 를 덮어쓰지 않는다**
- [ ] 조회수 증가가 **좁은 UPDATE** 다 — `view_count` 만 싣는다
- [ ] **동시 조회에서 `view_count` 가 소실되지 않는다**
- [ ] P-05 의 조회수 증가 동작과 §4.3 의 응답 키가 그대로다 (B-05 의 **동작·응답** 완료 기준을 깨지 않는다 — 갱신 **수단**을 적은 괄호는 이 항목이 이긴다)
- [ ] 기존 테스트가 깨지지 않는다

**검증** — `PostServiceTest` 확장

| 케이스 | 기대 결과 |
| --- | --- |
| **댓글 작성과 상세 조회를 끼워넣기** | `comment_count` 가 덮어써지지 않는다. **조회수 증가를 엔티티 변경으로 되돌리면 깨진다** |
| **같은 글을 동시 조회 N건** | `view_count` = N. 소실 없음 |
| 발행된 UPDATE 의 모양 | **`view_count` 만 싣는다.** `comment_count`·`title`·`content` 가 실리지 않는다 |
| 상세 조회 1회 | `view_count` 가 1 증가하고 응답이 §4.3 의 여덟 키다 |

> **끼워넣기를 강제한다.** B-10 이 `StatementInspector` + `CyclicBarrier` 로 `update post` 발행 직전에 세우는 방식을 썼다 — 같은 수단을 쓸 수 있다. **강제는 보장이지, 없을 때 반드시 공허해진다는 뜻이 아니다** — B-10 절의 측정이 그것이다.
>
> **`Post.increaseViewCount()` 를 지우지 않는다.** B-03 이 세 군데서 그 존재를 요구한다 — 도메인 메서드 표, 완료 기준 "위 표의 도메인 메서드 6개가 모두 구현되어 있다", 검증표 "`increaseViewCount()` 2회 → `viewCount = 2`". **대신 주석으로 막는다** — 그 메서드와 `viewCount` 필드에 "상세 조회 경로는 이 메서드를 쓰지 않는다 / 증가는 `PostRepository.increaseViewCount` 의 좁은 UPDATE 가 한다 / **이 메서드로 바꾸면 결함이 돌아온다**" 를 적는다. B-10 이 집계 메서드 둘에 같은 처리를 했다.
>
> **`clearAutomatically` 를 켜는지는 B-11 이 재서 정했고, 켜는 쪽이다.** B-10 은 껐지만 **그 선택을 관측하는 단언이 B-10 에 없었다** — 리뷰가 두 `@Modifying` 에 켜 보았고 **272/272, 종료 코드 0** 으로 아무것도 깨지지 않았다. B-10 의 두 경로가 `post` 를 다시 읽지 않기 때문이다. **B-11 은 달랐다** — `getDetail` 은 `PostDetailResponse.from(...)` 로 엔티티를 다시 읽고, 좁은 UPDATE 는 영속성 컨텍스트를 지나지 않으므로 **비우지 않으면 식별자 맵의 낡은 사본이 돌아온다.** 끈 상태에서 **3개가 빨개졌다**(B-11 실측): `PostControllerTest` 의 `$.data.viewCount expected:<1> but was:<0>` 와 서비스 쪽 둘이고, 셋 다 **DB 는 1 인데 응답이 0** 이라는 같은 사실이다.
>
> **가른 것은 응답의 키가 아니라 값이다.** 이 문서의 앞 판이 "§4.3 의 여덟 키를 그대로 내는 쪽을 택한다" 고 적었는데 **그것으로는 갈리지 않는다** — `PostDetailResponse` 가 레코드이므로 키 집합은 켜든 끄든 여덟이다. 관측 지점은 **`viewCount` 가 증가 후 값인가**이고, 커밋된 `view_count` 를 보는 단언은 끈 쪽에서도 녹색이었다. **저장이 아니라 응답이 깨진다.**
>
> 단, **이 관측은 "다시 읽어 응답을 만든다" 는 설계를 전제로 한다.** 응답의 `viewCount` 를 그 자리에서 `post.getViewCount() + 1` 로 계산하는 구현은 이 설정이 필요 없고 **스위트 전체를 통과한다**(B-11 리뷰 실측 276/276, 종료 코드 0). 그 구현이 틀린 이유는 **동시 조회에서 응답이 거짓이 되는 것**인데(둘이 각각 `n+1` 을 돌려주지만 DB 는 `n+2` 다), 완료 기준 3번이 **저장된 값**에 대한 것이라 그 자리를 요구하지 않는다. **스위트가 이 설정을 고정하지는 않는다.**
>
> 확실한 것은 따로 있다 — **엔티티가 더티로 남으면 전체 컬럼 UPDATE 가 좁은 UPDATE 를 덮어쓴다.** 그것은 `update post` 가 **정확히 하나**인지로 관측된다 — B-10 리뷰 실측: 좁은 UPDATE 를 두고 `post.increaseCommentCount()` 를 함께 호출하는 변이에서 `Expected size: 1 but was: 2` 로 빨개진다. **그 단언이 막는 것은 `clear` 설정이 아니라 더티 엔티티다.**

---

### D-02 `role` 값 검증의 소유를 정한다 [정본 개정]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-docs` (결정에 따라 `sp-member`·`sp-board` 가 뒤따른다) |
| 의존 | 없다. **1차 완료를 막지 않는다** — §7 의 완료 조건은 `AU-xx`·`M-xx`·`B-xx`·`I-xx` 다 |
| 참조 | [../api-contract.md §6](../api-contract.md), [../tech-stack.md §2.1](../tech-stack.md), [../security.md §5.2](../security.md), [integration.md](integration.md) I-04 |

**I-04 리뷰가 찾았다.** [../api-contract.md §6](../api-contract.md)이 `role` 을 `USER | ADMIN` 으로 못박는데 **member·board 는 값을 검사하지 않는다** — `hasText` 만 본다. `{"role":"BOGUS"}` 로 서명한 토큰에 **auth 401 `A002` · member 200 · board 200** 이다(실측). auth 만 `Role.valueOf` 로 걸린다.

**권한 상승은 아니다(실측).** board 의 역할 판정 두 자리가 문자열 동등 비교라 열거 밖 값은 "ADMIN 아님" 으로 떨어진다 — 타인 글·댓글 삭제가 `role=USER` 와 **바이트 동일한 403** 이었다. 역할 기반 인가 규칙이 세 저장소에 0건이라 `ROLE_BOGUS` 는 **만들어지고 아무도 읽지 않는다.** 그래서 1차를 막지 않는다.

**정해야 하는 것 하나** — **계약 밖 `role` 값을 받은 서비스는 거부하는가, 통과시키는가.** 그에 따라 세 가지가 따라온다.

| 결정 | 따라오는 것 |
| --- | --- |
| **거부한다** | member 의 `ClaimContractValidator` 와 board 의 `CurrentMemberArgumentResolver` 에 열거 검사를 더한다. board 의 `LoginMember.role` 을 `String` 에서 열거로 바꿀지도 함께 본다(auth 의 `LoginAccount` 는 이미 `Role` 이다) |
| **통과시킨다** | [../api-contract.md §6](../api-contract.md)에 **"소비자는 값을 검사하지 않는다"** 를 명시하고, `ROLE_` 권한이 소비되지 않는다는 전제를 [../tech-stack.md §2.1](../tech-stack.md)에 못박는다. **역할 기반 인가 규칙이 생기는 순간 그 전제가 깨진다**는 조건을 함께 적는다 |

**비용은 측정됐다. 거부하는 쪽을 택해도 깨지는 테스트가 0건이다** — **계약 밖 값을 넘기는 호출 지점이 없어서다**(팩토리가 `role` 을 자유 문자열로 받으므로 호출 지점만 늘리면 된다 — 타입으로 막히는 것은 auth 뿐이다. member 에는 공백 role 헬퍼가 없고 board 에는 `tokenWithBlankRole` 이 있다). **같은 사실의 뒷면이 지금의 fail-open 을 고정하는 테스트도 없다는 것이다** — 어느 쪽으로 정하든 **그 결정을 관측하는 테스트가 새로 필요하다.**

**결정: 거부한다.** 사용자가 2026-10-18 에 그렇게 정했다. 근거 넷.

1. [../api-contract.md §6](../api-contract.md)이 값을 못박았으므로 열거 밖 토큰은 **계약 위반 입력**이고, 그것을 조용히 통과시키는 것이 `AGENTS.md` 불변식 9(실패 은폐 금지 — 암묵적 fallback·silent degradation 으로 실패를 숨기지 않는다)가 금지하는 모양이다. 열거 밖 값이 `ROLE_BOGUS` 로 조립되고 서비스가 "ADMIN 아님" 으로 **묵시적으로 강등 처리**하는 것이 그 모양이다 (그 파일은 세 구현 저장소에 있고 `sp-docs` 에는 없다 — 링크로 적지 않는다, [../process/review-policy.md §8](../process/review-policy.md))
2. **auth 는 이미 거부한다.** 세 서비스가 갈라져 있고, 복제를 유지한 대가로 둔 3자 비교(I-04)가 잡는 것이 바로 그 갈림이다([../adr/0007](../adr/0007-shared-code-policy.md))
3. **비용이 0 이다** — **계약 밖 값을 넘기는 호출 지점이 없어서** 깨지는 테스트가 없다(팩토리는 `role` 을 자유 문자열로 받으므로 새 메서드 없이 `"BOGUS"` 를 넘기면 된다 — 타입으로 막히는 것은 auth 뿐이다). **그 0 은 지정된 집행 지점에서만 0 이다** — 두 항목이 고르는 자리를 벗어나면 깨진다(M-12·B-12 의 산출물이 그것을 고정한다)
4. **지금의 닫힘이 설계가 아니다.** board 의 인가 표현 둘이 "ADMIN 과 **같을 때만** 통과" 라서 모르는 값은 더 좁은 분기로 떨어진다 — 안전이 **비교의 모양**에 딸려 온다. **모르는 값이 허용 분기로 가는 표현이 하나라도 생기면 닫히지 않는다**: 역할이 늘어 "USER 만 제약한다" 로 **역전된 검사**가 적히는 경우, 부정형 권한 표현(`!hasRole('USER')`·기본 분기가 허용인 `switch`·`getOrDefault(role, ALL)`), 그리고 `RoleClaimConverter` 가 **검사 없이 claim 값을 권한 이름으로 올리는 것**. **`hasRole("ADMIN")` 도입과 열거 전환은 반례가 아니다** — 둘 다 안전하게 닫힌다(이 절의 앞 판이 그 둘을 계기로 적었는데 **틀렸고 D-02 리뷰가 잡았다**). 자세한 것은 [../tech-stack.md §2.1](../tech-stack.md)이 갖는다

**따라오는 구현 항목 둘을 세웠다** — `M-12`·`B-12`(둘 다 **[1차 후]**). **`LoginMember.role` 의 타입 변경은 두 항목 어디에도 넣지 않았다** — 그것은 board 의 ADMIN 판정 두 자리와 `RoleClaimConverter` 를 함께 봐야 하는 별 항목이다.

**완료 기준**
- [ ] 위 둘 중 하나로 정본이 정해져 있다 — [../api-contract.md §6](../api-contract.md)과 [../tech-stack.md §2.1](../tech-stack.md)이 같은 말을 한다
- [ ] 거부하는 쪽이면 **구현 항목이 세워져 있다**(저장소별로 하나씩). 통과시키는 쪽이면 **전제가 깨지는 조건**이 적혀 있다
- [ ] `python tools/check_refs.py` 가 통과한다 ([../process/review-policy.md §8](../process/review-policy.md))

---
### M-12 열거 밖 `role` 을 거부한다 [1차 후]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | **D-02** (그 항목이 이 요구를 만들었다) |
| 참조 | [../api-contract.md §6](../api-contract.md), [../tech-stack.md §2.1](../tech-stack.md), [../security.md §5](../security.md) |

**D-02 가 "거부한다" 로 정했다.** `ClaimContractValidator` 가 `role` 의 **존재**만 보고 **값**을 보지 않는다 — `{"role":"BOGUS"}` 로 서명한 토큰이 **200** 으로 통과했다(I-04 리뷰 실측).

**산출물**
- `global/security/ClaimContractValidator` — `role` 이 `USER`·`ADMIN` 중 하나인지 검사한다. 아니면 지금 누락에서 내는 것과 **같은 예외**를 던진다(`BadJwtException` → 401 `A002`). **그 클래스 안을 고친다 — 새 검증기 빈을 만들면 `JwtDecoderValidatorsTest` 의 "검증기가 기본 둘과 `ClaimContractValidator` 뿐이다" 단언이 빨개진다**
- `global/security/LoginMember` — javadoc 두 문장이 **member 에서 거짓이거나 절반만 참이다**(M-12 구현 워커가 측정해 올렸다). ① "권한 판정은 `RoleClaimConverter` 가 만든 `GrantedAuthority` 로 한다" — member `src/main` 에 `hasRole`·`@PreAuthorize`·`hasAuthority` 가 **0건**이고 `LoginMember.role()` 호출처도 **0건**이다. member 에는 그 판정 자체가 없다. ② "값이 `USER`·`ADMIN` 중 하나인지는 **발급 측 계약**이며" — **이 항목이 그것을 절반 거짓으로 만든다.** 이제 member 도 집행한다. **그 문장을 믿고 열거 검사를 지우면** [../conventions.md §9.5](../conventions.md)가 경고하는 모양이 된다

**완료 기준**
- [ ] `role` 이 열거 밖인 토큰에 **401 `A002`** 다. 누락·공백과 **응답이 같다** — 거부 사유를 응답으로 구별하지 않는다 ([../api-contract.md §8.5](../api-contract.md)의 "그 밖의 claim 검증 실패" 행을 구체화한 것이다)
- [ ] `role = "USER"`·`"ADMIN"` 토큰은 그대로 통과한다
- [ ] **열거 값의 출처를 하나 만들고 그 하나만 쓴다** — member 에는 **지금 출처가 없다**(`src/main` 에 `"USER"`·`"ADMIN"` 리터럴 0건, D-02 리뷰 실측). 그래서 "새로 박지 않는다" 로는 판정할 수 없다
- [ ] **`LoginMember` javadoc 이 member 의 실제 경로를 적는다** — 권한 판정이 member 에 없다는 것과, 값 검증을 **이 항목 이후 member 도 한다**는 것. B-12 가 board 쪽에 같은 기준을 갖는다(거기서는 판정이 **있고** 문장이 그 수단을 틀리게 적는다 — **두 저장소의 거짓이 다르다**)
- [ ] 기존 테스트가 깨지지 않는다 (182개)

**검증** — `SecurityConfigTest`·`JwtDecoderValidatorsTest` 확장 (**`ClaimContractValidatorTest` 는 없다.** 누락 role 의 401 `A002` 단언이 `SecurityConfigTest` 에 산다 — D-02 리뷰 실측)

| 케이스 | 기대 결과 |
| --- | --- |
| `role = "BOGUS"` (서명 유효) | **401 `A002`**, 본문이 누락 케이스와 **바이트 동일** |
| `role = "user"` (소문자) | **401 `A002`** — 대소문자를 관용하지 않는다 |
| `role = "USER"` · `"ADMIN"` | 통과 (200/201) |
| 열거 검사를 지우는 변이 | **첫 두 케이스가 빨개진다** |

> **지금의 fail-open 을 고정하는 테스트가 없다는 것이 D-02 의 측정값이다.** **계약 밖 값을 넘기는 호출 지점이 없어서 깨지는 테스트가 0건**이고(팩토리는 `role` 을 자유 문자열로 받는다), 같은 이유로 **이 변경을 관측하는 테스트도 없다.** 그래서 위 검증표의 첫 두 행이 이 항목의 산출물 중 가장 중요한 부분이다 — 코드 한 줄보다 그 두 행이 오래 남는다.

> **스위트는 열거 값을 고정하고 "그 상수를 쓰는 것" 은 고정하지 않는다. M-12 리뷰 실측.** `CONTRACT_ROLES` 를 쓰지 않는 구현 셋(리터럴 비교·정규식·`switch` 식)을 넣었더니 **셋 다 190/190 녹색**이었고, 그 상태에서 그 상수의 참조는 **javadoc 둘뿐**이었다. 즉 `role_허용값_출처` 는 **상수가 §6 의 값을 갖는다**를 못박고 **검증기가 그것을 쓴다**는 못박지 않는다. 기준 3 은 결과가 아니라 **수단**을 요구하므로 **기계로 고정되지 않는다** — `src/main` 의 리터럴이 상수 선언 줄 하나뿐임을 **`grep` 으로 확인하는 것**이 그 기준의 실제 판정 수단이고, **양성 대조를 세워** 확인한다. **테스트를 더하지 않는다**([../AGENTS.md](../AGENTS.md) 불변식 11 — 같은 결함을 두 번 보는 테스트를 넣지 않는다).

---

### M-13 member javadoc 의 수량 주장과 거짓 인용 [1차 후]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | **M-12** (그 항목의 구현 워커가 찾았다) |
| 참조 | [../security.md §5.1](../security.md), [../tech-stack.md §2.1](../tech-stack.md), [../conventions.md §9.5](../conventions.md) |

**M-12 구현 워커가 읽고 문장별로 판정해 올렸다.** 고치지 않고 보고한 것이 맞다 — M-12 산출물이 그 파일을 담지 않았다.

| 문장 | 판정 |
| --- | --- |
| `role` claim 을 `GrantedAuthority` 로 바꾼다 | **참** |
| "직접 작성할 것으로 남겨 둔 것이 **이 컨버터뿐이다**" | **거짓은 아니지만 유일성 주장**이다 — [../tech-stack.md §2.1](../tech-stack.md)의 문장을 인용했는데 **같은 절이 바로 뒤에서 "Claim 계약 검증은 이 목록에 없다" 로 한정한다.** 실제로 member `global/security` 에 손으로 쓴 클래스가 넷 더 있다(`ClaimContractValidator`·`SecurityErrorResponder`·`InternalApiKeyFilter`·`CurrentMemberArgumentResolver`). 단독으로 읽으면 "보안 코드는 이것 하나" 로 읽힌다 — [../conventions.md §9.5](../conventions.md)가 금지한 모양이다 |
| `ROLE_` 은 `hasRole` 이 보는 이름이고 B-04 검증표가 그것을 요구한다 | **참이고 주소도 맞다**(§6 의 B-04 절. 워커가 확인했다). **프레임워크 사실을 적을 뿐 member 가 `hasRole` 로 판정한다고 말하지 않는다** |
| "— **세 서비스가 같은 이름을 쓴다**" | **거짓이다.** `sp-auth/src/main` 에 `ROLE_` **0건**, `GrantedAuthority` 를 쓰는 파일 **0건**이다(양성 대조: board 는 적중). auth 는 그 이름을 **아예 만들지 않는다** — [../security.md §5.1](../security.md)이 그렇게 정했다. 쓰는 것은 **둘**이다 |
| `role` claim 존재는 `ClaimContractValidator` 가 보장하므로 여기서 다시 보지 않는다 | **참이고 M-12 가 더 강하게 만들었다** — 이제 **값까지** 보장하므로 이 컨버터가 `ROLE_BOGUS` 를 조립할 경로가 member 에서 닫혔다. **javadoc 이 아직 그것을 적지 않는다** |

**산출물**
- `global/security/RoleClaimConverter` — javadoc 만. 유일성 주장을 걷고, "세 서비스" 를 **둘**로 고치고, M-12 이후 **값까지 보장된다**는 것을 적는다
- `global/security/LoginMember` — **`:6` 의 인용이 너무 넓다**(M-12 수정 워커가 찾았다). "요청 본문·**경로 변수**의 식별자를 신뢰하지 않는다 ([../security.md §4](../security.md))" 인데 **§4 는 본문만 말한다**("`account_id = Claim.sub` ← 본문의 식별자를 신뢰하지 않는다"). 그리고 **member 는 경로 변수 식별자를 실제로 읽는다** — `GET /api/v1/members/{accountId}` 가 `permitAll` 이고 그 값이 공개 조회의 **조회 키**다. **주체의 식별자**에 한정해 적거나 인용을 §4 가 뒷받침하는 범위로 좁힌다

**완료 기준**
- [ ] 유일성 주장("…뿐이다")이 없다 — 그 자리에 **무엇이 더 있는지** 적거나 주장을 걷는다
- [ ] "세 서비스가 같은 이름을 쓴다" 가 **둘**로 고쳐져 있다(auth 는 `ROLE_` 을 만들지 않는다)
- [ ] M-12 이후 **값까지** 보장된다는 것이 적혀 있다 — `ROLE_BOGUS` 조립 경로가 닫혔다
- [ ] **`LoginMember:6` 의 인용이 §4 가 뒷받침하는 범위 안이다** — 경로 변수를 §4 의 말로 적지 않는다. `GET /{accountId}` 가 그 값을 조회 키로 쓰는 것과 어긋나지 않는다
- [ ] 기존 테스트가 깨지지 않는다 (**190개**. javadoc 만 고치므로 수가 변하지 않는다)

> **`B-12` 가 board 쪽 같은 문장을 고친다.** 네 번째 문장은 **두 저장소에 바이트 동일**이다(M-12 워커 실측) — 복제 문장이므로 한쪽만 고치면 다른 쪽에 거짓이 남는다. **다섯째 문장은 board 에서는 `B-12` 가 끝난 뒤에야 참이 된다** — 그 순서가 맞다.
>
> **`RoleClaimConverter.java` 는 CRLF 다. M-12 리뷰 실측.** `sp-member` 의 java 가 전부 LF 가 아니다 — `src/**/*.java` 중 **16파일이 CRLF** 이고 이 항목이 손대는 파일이 그중 하나다. **`sed`·`awk`·`grep` 으로 고치면 CR 을 먹는다**(Git Bash 측정값). 파이썬 바이트 치환을 쓰고 **고치기 전에 줄끝을 세고 고친 뒤 다시 센다**.
>
> **테스트로 고정되지 않는다.** javadoc 이므로 변이로 잡을 수 없고, 완료 기준은 **읽어서** 판정한다. 측정으로 받칠 수 있는 것은 수량 주장 쪽이다 — `sp-auth/src/main` 의 `ROLE_` 0건에 **양성 대조를 세워** 보고한다.

---
### B-12 열거 밖 `role` 을 거부한다 [1차 후]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | **D-02** |
| 참조 | [../api-contract.md §6](../api-contract.md), [../tech-stack.md §2.1](../tech-stack.md), [../security.md §5.2](../security.md) |

**같은 요구의 board 쪽이다.** 집행 지점이 다르다 — board 는 디코더가 아니라 **`@CurrentMember` 리졸버**에서 집행한다([../tech-stack.md §2.1](../tech-stack.md)).

**산출물**
- `global/security/CurrentMemberArgumentResolver` — `role` 이 열거 안인지 검사한다. 아니면 지금 `hasText` 가드가 내는 것과 **같은 예외**를 던진다(→ 401 `A002`). **디코더에 검증기 빈을 더하지 않는다** — `JwtDecoderValidatorsTest` 가 "기동된 디코더의 claim 검증기가 **기본 둘뿐이다**" 를 단언한다(그 선택이 테스트로 강제돼 있다)
- `global/security/LoginMember` — javadoc 의 **"권한 판정은 `RoleClaimConverter` 가 만든 `GrantedAuthority` 로 한다" 가 이미 거짓이다**(실제 판정은 `loginMember.role()` 문자열 비교이고 `hasRole`·`@PreAuthorize` 사용처가 0건이다, D-02 리뷰 실측). **이 항목이 그 파일의 이웃을 건드리므로 함께 고친다**
- `global/security/RoleClaimConverter` — javadoc 의 **"세 서비스가 같은 이름을 쓴다" 가 거짓이다**(`sp-auth/src/main` 에 `ROLE_` 0건, M-12 워커 실측). **둘**로 고친다. 그 문장은 **member 쪽과 바이트 동일한 복제**이고 `M-13` 이 member 쪽을 맡는다 — 한쪽만 고치면 다른 쪽에 거짓이 남는다

**완료 기준**
- [ ] `role` 이 열거 밖인 토큰에 **401 `A002`** 다. 누락·공백과 응답이 같다
- [ ] `role = "USER"`·`"ADMIN"` 토큰은 그대로 통과한다
- [ ] **`"ADMIN".equals(...)` 로 ADMIN 을 판정하는 두 자리가 그대로 동작한다** — `PostService`·`CommentService` 의 삭제 권한([../security.md §5.2](../security.md)의 매트릭스)
- [ ] **`LoginMember.role` 의 타입을 바꾸지 않는다** — 열거로 바꾸는 것은 이 항목의 범위가 아니다(바꾸면 그 두 자리와 `RoleClaimConverter` 를 함께 봐야 한다). 바꾸고 싶으면 별 항목이다
- [ ] **열거 값의 출처를 하나 만들고 세 자리가 그것을 쓴다** — 리졸버의 열거 검사 + `PostService`·`CommentService` 의 ADMIN 판정. board 에는 지금 `"ADMIN"` 이 **두 벌** 박혀 있다(`PostService`·`CommentService` 의 `ROLE_ADMIN` 상수 — **이름에는 `ROLE_` 접두어가 있는데 값에는 없다**). 기준이 없으면 리졸버에 세 번째 `"ADMIN"` 과 첫 `"USER"` 가 생긴다. **타입 변경과 다른 일이고**, 상수를 모으면 나중에 타입을 바꿀 때 고칠 자리가 하나다
- [ ] **`LoginMember` javadoc 이 실제 판정 경로를 적는다** — 지금 "권한 판정은 `RoleClaimConverter` 가 만든 `GrantedAuthority` 로 한다" 로 적혀 있는데 실제 판정은 서비스의 문자열 비교다(D-02 리뷰 실측)
- [ ] 기존 테스트가 깨지지 않는다 (276개)

**검증** — `JwtAuthenticationTest`·`PostControllerTest` 확장

| 케이스 | 기대 결과 |
| --- | --- |
| `role = "BOGUS"` 로 `GET /posts/me` | **401 `A002`** (전에는 200 이었다 — I-04 리뷰 실측) |
| `role = "BOGUS"` 로 `POST /posts` | **401 `A002`** (전에는 201 로 글이 생성됐다) |
| `role = "ADMIN"` 으로 타인 글 삭제 | **204** — 기존 동작이 그대로다 |
| `role = "USER"` 로 타인 글 삭제 | **403 `P002`** |
| 열거 검사를 지우는 변이 | **첫 두 케이스가 빨개진다** |

> **출처를 "쓴다" 는 것도 테스트로 관측되지 않는다. B-12 실측이고 M-12 와 같다.** `ContractRole` 과 그 값을 그대로 두고 **읽지 않게만** 바꾼 변이 네 갈래(리졸버만 리터럴·정규식·`switch`, 두 서비스만 리터럴, 세 자리 전부)가 **전부 0 red**(282/0/0/0, 종료 코드 0)였다. **출처를 읽는 자리가 셋이어도 다르지 않았다** — 잡히는 것은 **값이 틀릴 때**이고 — **집계는 그것을 낸 변이와 함께 적는다**(B-12 리뷰가 "3 red" 를 재현하지 못해 올렸다): ADMIN **판정값만** 어긋내고 **허용집합을 리터럴로 고정하면 3 red**(삭제 둘이 `204→403`, 서비스 하나가 `P002`. **수정 셋은 녹색**), **상수 한 줄만** 어긋내면 **7 red**(`VALUES = Set.of(USER, ADMIN)` 이 그 상수에서 파생되므로 **ADMIN 토큰 자체가 거부된다** — 삭제 둘 `204→401`·수정 둘 `403→401`·유효 토큰 통과 둘), 허용집합을 **소문자로** 바꾸면 **54 red**, 집합에서 **`USER` 를 빼면 48 red** **값이 같은 채 수단만 다르면 동작이 바이트까지 같다.** 빌드에도 신호가 없다 — 세 자리를 모두 비껴간 상태에서 두 서비스의 `ContractRole` import 가 쓰이지 않는데 javac 이 경고하지 않았다.
>
> **그래서 이 기준의 판정 수단은 `grep` 이다.** `src/main` 의 `"USER"`·`"ADMIN"` 리터럴이 **출처 선언 두 줄뿐**인지 보고, **양성 대조를 세워** 확인한다(변이 상태에서 그 수가 3·4·5 줄로 늘었다 — 즉 `grep` 은 가른다). **테스트를 더하지 않는다**([../AGENTS.md](../AGENTS.md) 불변식 11).
>
> **`@CurrentMember` 를 받지 않는 핸들러에는 이 집행이 닿지 않는다.** [../tech-stack.md §2.1](../tech-stack.md)이 적어 둔 전제가 그대로 적용된다 — 보호는 그 애노테이션을 받는 핸들러에서만 성립하고, `.authenticated()` 만 걸린 핸들러가 생기면 그 자리는 비어 있다. **이 항목이 그 전제를 없애지 않는다.**

---
### D-06 "직접 작성할 것은 컨버터뿐이다" 를 좁힌다 [정본 개정]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-docs` (결정에 따라 세 저장소의 주석이 뒤따른다) |
| 의존 | 없다. **1차 완료를 막지 않는다** |
| 참조 | [../tech-stack.md §2.1](../tech-stack.md), [../conventions.md §9.5](../conventions.md), [../security.md §5.1](../security.md) |

**M-12 리뷰가 올렸다.** [../tech-stack.md §2.1](../tech-stack.md)이 "직접 작성할 것은 `role` claim 을 `GrantedAuthority` 로 바꾸는 **컨버터뿐이다**" 를 적는데, **같은 절이 뒤에서 "Claim 계약 검증은 이 목록에 없다" 로 한정한다.** 플랫하게 거짓은 아니지만 **유일성 주장**이고([../conventions.md §9.5](../conventions.md)), **단독으로 인용되면 "보안 코드는 컨버터 하나" 로 읽힌다.**

**실제로 그렇게 인용됐다.** 세 저장소의 `RoleClaimConverter` javadoc 이 그 문장을 옮겨 적었다 — member 에는 손으로 쓴 보안 클래스가 넷 더 있다(`ClaimContractValidator`·`SecurityErrorResponder`·`InternalApiKeyFilter`·`CurrentMemberArgumentResolver`). **정본의 유일성 주장이 코드 주석 셋으로 번진 사례**다.

> **같은 가족이 하나 더 있다. B-12 구현이 찾았다.** [../conventions.md §1.3](../conventions.md)의 board 패키지 트리가 `global/security` 를 `# RoleClaimConverter, LoginMember(record), @CurrentMember` 로 적는데 **그 디렉터리의 파일은 B-12 전에 이미 다섯이었다**(`CurrentMemberArgumentResolver`·`SecurityErrorResponder` 가 빠져 있다). 빠진 둘 중 하나는 [../tech-stack.md §2.1](../tech-stack.md)이 **board 의 집행 지점으로 지명한 클래스**다 — **한 절이 지명하는 클래스가 다른 절의 목록에 없다.** B-12 가 `ContractRole` 을 더해 지금은 여섯이다. **목록을 늘리지 말고 성질로 적는 쪽을 권한다**(예: `# 보안 — JWT claim 변환·계약 검증·인증 실패 응답`) — 늘리면 다음 항목이 또 거짓으로 만든다. member 의 §1.2 가 같은 모양인지는 **재지 않았다**(B-12 구현이 확인 못 함으로 남겼다).

**결정: M-12 리뷰의 제안대로 좁혔다(2026-10-18).** [../tech-stack.md §2.1](../tech-stack.md)이 이제 **스타터의 몫**(서명 검증·만료 확인·`SecurityContext` 주입)과 **서비스의 몫**(`GrantedAuthority` 변환·Claim 계약 검증·인증 실패 응답·인자 해석)을 갈라 적고 **"컨버터뿐" 이 아니다**를 명시한다. 세 저장소의 javadoc 인용은 `M-13`·`B-12` 가 걷었다 — **auth 에는 `RoleClaimConverter` 가 없다**(M-12 리뷰 실측).

**정해야 하는 것** — 그 문장을 **무엇으로 좁히는가.** M-12 리뷰의 제안: "스타터가 하는 것은 **서명 검증·만료 확인·`SecurityContext` 주입**이고, **`GrantedAuthority` 변환과 Claim 계약 검증은 서비스가 작성한다**". 그러면 §2.1 의 집행 지점 표(member 는 디코더, board 는 리졸버, auth 는 리졸버)와 어긋나지 않는다.

**완료 기준**
- [ ] §2.1 에 **유일성 주장이 없다** — 스타터의 몫과 서비스의 몫이 갈려 적혀 있다
- [ ] 세 저장소의 `RoleClaimConverter` javadoc 이 그 문장을 **더는 인용하지 않거나 좁혀진 쪽을 인용한다**. `M-13`(member)·`B-12`(board)가 그 자리를 이미 맡는다 — **auth 에는 `RoleClaimConverter` 가 없다**(M-12 리뷰 실측: `global/security` 에 다섯 클래스가 있고 그 컨버터는 없다)
- [ ] `python tools/check_refs.py` 를 **커밋 직전에** 돌려 통과했고 그 출력을 커밋 메시지에 남겼다

> **코드 주석 셋이 정본 한 문장에 매달려 있다.** 그래서 순서가 **정본 먼저**다 — 주석을 먼저 고치면 무엇을 인용할지 정해지지 않는다. `M-13`·`B-12` 가 그 주석을 고칠 때 이 항목이 아직 `todo` 면, **인용을 걷어내는 쪽**(문장을 가리키지 않고 자기 저장소의 사실만 적는 쪽)으로 한다.

---
### D-07 `.gitattributes` 에 텍스트 파일 줄끝을 고정한다 [정본 개정]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth`·`yuno110/sp-member`·`yuno110/sp-board` (세 저장소에 같은 줄) |
| 의존 | 없다. **1차 완료를 막지 않는다** |
| 참조 | [../process/review-policy.md §4.1](../process/review-policy.md), [../adr/0002-separate-repositories.md](../adr/0002-separate-repositories.md) |

**이 세션이 줄끝으로 치른 모든 대가의 뿌리다. B-12 구현이 찾았고 내가 세 저장소에서 확인했다.**

| 측정 | 값 |
| --- | --- |
| `core.autocrlf` 의 출처 | **시스템 gitconfig** (`file:C:/Program Files/Git/etc/gitconfig true`) — 저장소·전역 설정에는 **없다**. Git for Windows 설치 기본값이다 |
| 세 저장소의 `.gitattributes` | **똑같이 세 줄**(`/gradlew text eol=lf` · `*.bat text eol=crlf` · `*.jar binary`). **`text=auto` 도 다른 확장자 규칙도 없다** |
| `src/**/*.java` 중 CRLF | auth **4** / 59 · member **16** / 50 · board **17** / 64 |
| 추적되는 `*.yml`·`*.md` 중 CRLF | auth **4**(`AGENTS.md`·`README.md`·`application.yml`·`application-prod.yml`) · member **4**(`AGENTS.md`·`CLAUDE.md`·`docs/checklist.md`·`application-test.yml`) · board **4**(`AGENTS.md`·`CLAUDE.md`·`README.md`·`application.yml`) |

**규칙이 아니라 체크아웃 이력이 상태를 정한다.** 인덱스는 LF 인데 작업 트리는 체크아웃마다 CRLF 가 되므로, **같은 파일이 작업자에 따라 LF 이거나 CRLF 다.** 그래서 이 세션의 워커들이 매번 줄끝을 세어야 했고, `git add` 때마다 `LF will be replaced by CRLF` 경고가 찍혔다.

**`*.java` 만 고정하면 사고가 난 파일 종류가 남는다.** 이 절의 앞 판은 산출물과 완료 기준을 `*.java` 한 줄로 적었는데, **[../process/review-policy.md §4.1](../process/review-policy.md) 이 기록한 실제 사고는 `.yml` 에서 났다** — I-03 리뷰가 57줄 CRLF 파일의 줄끝을 `sed … | od -c` 로 확인해 **LF 로 오진한 일**이고, 그 파일은 `src/main/resources` 의 yml 이다. `*.java` 규칙은 그 조건을 **`.java` 에서만** 없앤다. 위 표의 둘째 행이 그 잔여를 센 것이고, 그래서 범위를 **텍스트 파일 전체**로 넓힌다.

**고치면 사고의 조건 자체가 사라진다.** `* text=auto eol=lf` 가 작업 트리를 고정하고, **Git Bash 의 `sed`·`awk`·`grep` 이 CR 을 먹어 바이트 복원을 깨뜨리는 사고**([../process/review-policy.md §4.1](../process/review-policy.md))가 일어날 수 없다. `text=auto` 라 이진 파일은 git 의 탐지에 맡기고, `*.bat`(CRLF 가 필요하다)·`*.jar`(binary)는 **뒤에 오는 명시 규칙이 이긴다.**

**산출물**
- 세 저장소의 `.gitattributes` — `* text=auto eol=lf` 를 **먼저** 두고 기존 세 줄을 그 뒤에 남긴다(뒤가 이긴다). **세 저장소에 같은 내용으로 둔다**(`AGENTS.md` 가 그렇게 요구한다)

**완료 기준**
- [ ] 세 `.gitattributes` 가 **바이트 동일**하고 `*.bat` 는 여전히 `eol=crlf` 로 해석된다(`git check-attr` 로 확인한다 — 규칙 순서를 틀리면 조용히 뒤집힌다)
- [ ] `git check-attr text eol -- <아무 .java>`·`<아무 .yml>`·`<아무 .md>` 가 세 저장소에서 **`unspecified` 가 아니다**(앞 판에서는 전부 `unspecified` 였다 — B-12 실측)
- [ ] **재정규화의 영향을 측정해서 적는다** — `git add --renormalize` 가 무엇을 바꾸는지. B-12 구현은 "인덱스가 이미 LF 라서 필요 없다" 고 **추론했고 재지 않았다**. 그 추론을 그대로 믿지 말고 **재서** 적는다
- [ ] **작업 트리에 CRLF 가 남지 않는다** — 속성 추가만으로는 바뀌지 않는다는 것이 측정값이다(아래 블록)
- [ ] 세 저장소의 테스트가 그대로 통과한다 (auth 224 · member 190 · board 282)

> **`.gitattributes` 를 바꾸는 것은 저장소 설정 변경이고 과거 커밋의 내용을 바꾸지 않는다** — 다만 그것도 위의 측정 대상이다. 체크아웃된 작업 트리의 줄끝은 바뀔 수 있으므로 **각 저장소에서 테스트를 한 번 돌려 확인한다.**

> **속성을 추가해도 작업 트리는 그대로다. 측정값이다**(2026-10-18, auth·board). `git add --renormalize .` 가 바꾼 `.java` blob 은 **0개**였다 — 인덱스가 이미 LF 라는 추론은 맞았다. 그런데 **그 뒤에도 작업 트리의 CRLF 개수는 줄지 않았다**(board 17 → 17). 속성은 **다음 체크아웃**에 적용되므로, 해당 파일을 `rm` 후 `git checkout --` 로 다시 받아야 0 이 된다. **"규칙을 넣었으니 상태가 바뀌었다" 는 추론이 여기서 틀린다.**

---

### B-13 board javadoc 의 인용 범위 [1차 후]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | **B-12** (그 항목의 구현 워커가 찾았다) |
| 참조 | [../security.md §4](../security.md), [../api-contract.md §6](../api-contract.md) |

**`M-13` 의 board 쪽이다.** `global/security/CurrentMember` 의 javadoc 이 "요청 본문·**경로 변수**의 식별자를 신뢰하지 않는다 ([../security.md §4](../security.md))" 를 적는데 **§4 는 본문만 말한다**(`account_id = Claim.sub` ← 본문의 식별자를 신뢰하지 않는다).

**board 는 member 와 사정이 다르다.** member 에서는 그 문장이 **실제와도 어긋난다** — `GET /api/v1/members/{accountId}` 가 `permitAll` 이고 그 경로 변수를 조회 키로 읽는다. **board 는 인증 경로가 모두 `sub` 를 쓰므로 실제와는 어긋나지 않고 인용 범위만 넓다**(B-12 구현 실측). 그래서 **고칠 것은 인용이지 사실이 아니다.**

**산출물**
- `global/security/CurrentMember` — javadoc 의 인용을 §4 가 뒷받침하는 범위로 좁힌다. board 의 `LoginMember` javadoc 은 같은 문장을 갖지만 **§4 를 인용하지 않으므로**(꼬리가 `adr/0003`·`adr/0012` §6 이다) 그 자리는 손대지 않는다 — **확인하고 손대지 마라**

**완료 기준**
- [ ] `CurrentMember` 의 인용이 §4 가 뒷받침하는 범위 안이다
- [ ] `LoginMember` 의 같은 문장은 **그대로**다(인용이 다르다 — 확인했다는 것을 보고에 적는다)
- [ ] 기존 테스트가 깨지지 않는다 (**282개**. javadoc 만 고치므로 수가 변하지 않는다)

> **`src/**/*.java` 중 17파일이 CRLF 다**(B-12 실측). 고치기 전에 그 파일의 줄끝을 세고 고친 뒤 다시 세라. `sed`·`awk`·`grep` 으로 고치면 CR 을 먹는다. `D-07` 이 그 조건을 없애지만 그 전까지는 세어야 한다.

---
### D-03 로컬 바인드 로그가 비밀번호 해시를 남긴다 [정본 개정]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-docs` (결정에 따라 `sp-auth` 가 뒤따른다) |
| 의존 | 없다. **1차 완료를 막지 않는다** — §7 의 완료 조건은 `AU-xx`·`M-xx`·`B-xx`·`I-xx` 다 |
| 참조 | [../security.md §1](../security.md) 민감정보 로깅 행, [../nfr.md §5](../nfr.md), [../conventions.md §8](../conventions.md) |

**I-05 가 찾았다.** 세 저장소의 커밋된 템플릿 `application-local.yml.example` 이 `org.hibernate.orm.jdbc.bind: trace` 를 켠다. 그래서 **`account` 에 쓰기가 일어날 때마다 저장된 BCrypt 해시가 로컬 로그에 찍힌다**(auth 만 해당한다 — member·board 에는 비밀 컬럼이 없다). `application-prod.yml` 은 세 저장소 모두 `org.hibernate.SQL: warn` 과 `org.hibernate.orm.jdbc.bind: warn` 이라 **운영은 영향이 없다**(실측).

**정본 통제와 어긋난다.** [../security.md §1](../security.md)의 "민감정보 로깅 — 비밀번호·토큰·키를 로그에 남기지 않음" 과 [../nfr.md §5](../nfr.md)의 같은 행이 **프로파일을 가리지 않는다.** 그리고 이 프로젝트는 BCrypt 해시를 비밀로 취급해 왔다 — 커밋되는 파일에 `$2[aby]$` 모양 문자열을 넣지 않는 규칙이 그것이다. **평문 비밀번호는 로그에 남지 않는다** — 바인드 파라미터에 실리는 것은 이미 인코딩된 해시다.

**결정: 운영만이다.** 사용자가 2026-10-18 에 "문서에 결함이 있으면 안 된다" 로 마무리를 지시했고 내가 그렇게 정했다. [../security.md §1.2](../security.md)를 새로 두어 **로컬의 예외와 그 조건**(로그를 공유·업로드·커밋하지 않는다 · 인용할 때 BCrypt 모양을 지우고 **패턴의 양성 대조를 먼저 세운다** · 커밋되는 파일에는 어떤 프로파일에서도 넣지 않는다)을 적었고, [../security.md §1](../security.md)과 [../nfr.md §5](../nfr.md)의 행에 **프로파일 범위**를 달았다. **로컬을 끄지 않은 이유는 그 로거가 [../conventions.md §8](../conventions.md)이 켜라고 적은 학습 수단이기 때문이다.**

**정해야 하는 것 하나** — **통제가 운영만을 말하는가, 모든 프로파일을 말하는가.**

| 결정 | 따라오는 것 |
| --- | --- |
| **운영만** | [../security.md §1](../security.md)과 [../nfr.md §5](../nfr.md)의 그 행에 **프로파일 범위**를 적고, 로컬 로그에 해시가 남는다는 것을 **알려진 제약**으로 적는다. 로컬 로그를 공유·업로드하지 않는다는 조건을 함께 적는다 |
| **모든 프로파일** | `sp-auth` 의 템플릿에서 바인드 로거를 내린다. **대가가 있다** — 로컬에서 SQL 파라미터를 못 본다. 그 로거는 이 프로젝트의 학습 수단이고 [../conventions.md §8](../conventions.md)이 켜라고 적는다. auth 만 내릴지, 세 저장소를 맞출지도 함께 정한다 |

**어느 쪽으로 정하든 그 결정을 관측하는 수단이 지금 없다.** 템플릿의 로거 수준을 되돌리는 변이를 잡는 테스트가 세 저장소에 없다 — `.example` 은 실행되지 않는 파일이고 `application-local.yml` 은 gitignore 되어 있다. **그 비대칭을 적어 두는 것이 이 항목의 산출물 중 하나다.**

> **I-05 워커는 자기 scratchpad 로그에서 그 네 자리를 지우고 독립 `grep` 으로 0건을 확인했다.** 저장소 파일은 고치지 않았다 — 고치는 것이 이 항목이다.

---
### D-04 `AGENTS.md` 링크 여덟 개를 참으로 만든다 [정본 개정]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-docs` |
| 의존 | 없다. **1차 완료를 막지 않는다** |
| 참조 | [../process/review-policy.md §8](../process/review-policy.md), [../adr/0002-separate-repositories.md](../adr/0002-separate-repositories.md) |

**`../AGENTS.md` 를 가리키는 링크 여덟 개가 존재하지 않는 경로다.** `AGENTS.md` 는 세 구현 저장소에 있고 **`sp-docs` 에는 없다**. [../process/review-policy.md §8](../process/review-policy.md)이 그것을 부채로 적고 **"1차에서 건드리지 않는다"** 로 유보했는데, **1차가 2026-10-18 에 닫혔으므로 그 줄 자신의 조건에 따라 지금이 처리 시점이다.**

**`check_refs.py` 가 잡아 주지 않는다.** `main()` 의 `secs = SEC.findall(label); if not secs: continue` 가 **라벨에 `§` 가 없는 링크를 건너뛴다**(§8 이 I-03 2라운드 실측으로 적었다). D-02 리뷰가 양성 대조로 재확인했다 — `§` 있는 깨진 링크는 exit 1, **없는 것은 exit 0** 이다. 그래서 **도구가 통과해도 깨져 있고**, D-02 가 아홉 번째를 더하다가 리뷰에 잡혔다.

**정해야 하는 것 하나** — **링크를 없애는가, 대상을 만드는가.**

| 결정 | 따라오는 것 |
| --- | --- |
| **(i) 여덟 곳을 평문 참조로 바꾼다** | **다섯 파일 여덟 곳이고 그중 둘이 개정 대상**이다 — `api-contract.md` 3건 · `conventions.md` 1건(각각 `version`·`updated` 를 올려야 한다. `api-contract.md` 는 세 서비스 공유 계약이다). **나머지 넷은 개정 대상이 아니다** — `plan/phase1.md` 2건 · `nfr.md` 1건 · `process/review-policy.md` 1건(`nfr.md` 는 `version` 을 갖지만 [../process/review-policy.md §8](../process/review-policy.md)의 개정 대상 목록에 없다). 마지막 1건은 **§4(체크 항목) 끝에 있고, 완료 기준 2가 지우는 §8 의 부채 줄과는 다른 자리다** — 기준 2를 만족해도 그 링크는 남으므로 따로 고친다(D-02 3라운드 실측: 링크는 §4, 부채 줄은 §8 이고 부채 줄에는 마크다운 링크가 없다) |
| **(ii) `sp-docs/AGENTS.md` 를 만든다** | **파일 하나 추가로 여덟 링크가 한 번에 참이 된다.** 개정 대상을 건드리지 않는다. 세 사본이 **바이트 동일**이므로(md5 동일, 5584B, D-02 리뷰 실측) 넷째 사본의 유지 비용은 [../adr/0002](../adr/0002-separate-repositories.md)가 이미 "거의 바뀌지 않아 낮다" 로 받은 성질이다 |

> **결정: (ii) 를 택했고, 그것만으로는 모자랐다. 2026-10-18 실측.** `sp-docs/AGENTS.md` 를 세 사본과 **바이트 동일**로 만들었지만(md5 `453823f9d80131612ad2debb78d68a55`) **여덟 중 셋만 참이 됐다** — `plan/`·`process/` 안의 셋이다. **루트 문서 다섯의 `../AGENTS.md` 는 `sp-docs` 바깥을 가리킨다**(그 문서가 저장소 루트에 있으므로). 그 다섯을 `AGENTS.md` 로 고쳤다(`api-contract.md` 3 · `conventions.md` 1 · `nfr.md` 1). **M-12 리뷰의 "파일 하나로 여덟이 한 번에 참이 된다" 는 절반이 틀렸고 내가 그것을 이 절에 옮겼다** — 경로가 문서의 위치에 달려 있다는 것을 세지 않았다.
>
> **지금 대상 없는 `.md` 링크는 셋이고 전부 [../process/review-policy.md §8](../process/review-policy.md)의 예시다**(`other.md`·`tech-stack.md`·`phase1.md` — 도구가 무엇을 검사하는가를 보이는 샘플이라 대상이 없는 것이 정상이다). 그 절의 부채 줄은 **지웠고** 그 자리에 이 구분을 적었다. **네 사본을 바이트 동일로 유지하는 규칙은 [../adr/0002-separate-repositories.md](../adr/0002-separate-repositories.md)에 적었다.**
>
> **부채의 진짜 모양은 링크가 아닐 수 있다.** 지금 `sp-docs` 에는 `AGENTS.md` 도 `CLAUDE.md` 도 **없다** — `D-xx` 를 하는 워커만 불변식 문서 없이 일하고, 정작 그 불변식을 **인용하는** 문서가 `sp-docs` 에 모여 있다. D-02 리뷰가 **(ii) 를 먼저 재라**고 권고했다. 판정은 이 항목의 리뷰어가 한다.
>
> **D-02 가 이 절을 쓰면서 같은 맹점에 세 번 빠졌다. D-02 3라운드가 전수로 잡았다.** 이 절의 세 링크가 `../adr/0002-shared-nothing-repos.md`(없는 파일)를 가리켰고 — 실제는 `adr/0002-separate-repositories.md` 다 — **라벨에 `§` 가 없어 `check_refs.py` 가 통과시켰다.** 그중 하나는 **완료 기준**이어서, 따랐다면 워커가 없는 파일을 새로 만들어 **ADR 0002 가 두 벌로 쪼개졌을 것이다.** 경로는 고쳤다(`380b398` 다음 커밋). **완료 기준 1을 `AGENTS.md` 가 아니라 "대상 없는 `.md` 링크 0건" 으로 둔 이유가 이것이다** — 설명만 있는 맹점은 다시 밟힌다.
>
> **전수로 세면 11건이 나오는데 셋은 고칠 대상이 아니다.** `process/review-policy.md` §8 의 표·블록인용이 "도구가 무엇을 검사하는가" 를 보이는 **예시**(`other.md`·`tech-stack.md`·`phase1.md`)여서 대상이 없는 것이 정상이다. **이 항목이 0으로 만들 것은 나머지 여덟이다.**

**완료 기준**
- [ ] `sp-docs` 안에 **대상 없는 `.md` 링크가 0건**이다 — `../AGENTS.md` 여덟 개가 그 대부분이고, **`sp-docs/AGENTS.md` 를 만들면 그 여덟은 한 번에 참이 된다**. 기준을 `AGENTS.md` 로 좁히지 않는 이유는 **`§` 없는 링크를 건너뛰는 맹점을 완료 기준 쪽에서 닫는 것**이다(아래 블록인용).
      **검색 패턴을 이 문서에 적지 마라** — 적으면 그 `grep` 이 **자기 자신을 센다**. 이 기준의 앞 판이 패턴을 적어서 8건을 9건으로 세게 만들었다(백틱 안이라 링크는 아니지만 검색은 걸린다)
- [ ] **[../process/review-policy.md §8](../process/review-policy.md)의 부채 줄을 지운다** — 부채를 닫는 항목이 부채 기록을 남겨 두면 다음 사람이 또 센다
- [ ] (ii) 를 택하면 **네 사본을 맞추는 규칙**이 [../adr/0002](../adr/0002-separate-repositories.md)에 적혀 있다
- [ ] `python tools/check_refs.py` 가 통과한다. **그 통과가 이 항목을 판정하지 않는다** — 위 **기준 1**이 판정한다

---

### D-05 만료와 claim 계약 위반이 겹칠 때의 코드를 정한다 [정본 개정]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-docs` |
| 의존 | **`M-12`·`B-12` 가 `done` 인 뒤가 값싸다** (그때 세 서비스를 한 번에 잰다) |
| 참조 | [../api-contract.md §6 §8.5](../api-contract.md), [../security.md §4.1 §5.3](../security.md) |

**[../api-contract.md §8.5](../api-contract.md)가 `exp` 경과를 `A003`, 그 밖의 claim 검증 실패를 `A002` 로 정하는데 둘이 겹치는 경우를 정하지 않는다.** 만료됐고 동시에 claim 계약을 깬 토큰이다.

**D-02 리뷰가 소스로 추론했다 — 측정값이 아니다.** member 의 `ClaimContractValidator` 는 결과를 돌려주지 않고 **던지므로**(그 클래스 javadoc 이 이유를 적는다: 결과로 실패하면 `JwtValidationException` 이 되어 §8.5 가 `A002` 로 정한 것이 **만료로 읽힌다**) 그 토큰이 `A003` 이 아니라 `A002` 가 될 것으로 본다. **누락 role + 만료에서 이미 그렇고 `M-12`·`B-12` 가 그 표면을 넓힌다.**

> **이 항목의 산출물은 실측이다.** 세 서비스에 **만료 + 계약 위반** 토큰을 쳐서 나오는 코드를 재고 그것을 §8.5 에 적는다. **미측정 추론을 계약에 적지 않는다** — 그것이 이 세션에서 반복된 실패의 모양이고, D-02 가 그래서 리뷰에서 `CHANGES_REQUESTED` 를 받았다.

**완료 기준**
- [ ] 세 서비스에서 **만료 + 계약 위반** 토큰의 응답을 **실측**했다(상태와 `error.code`)
- [ ] [../api-contract.md §8.5](../api-contract.md)에 그 선후가 적혀 있다 — 셋이 다르면 **그 차이도** 적는다
- [ ] **노출을 측정에 묶어 본다** — 셋 중 어느 코드가 나가든 **본문과 상태가 단일 사유 케이스와 바이트 동일**한지 함께 재고, 다르면 그 차이가 노출인지 [../security.md §4.1](../security.md)("어느 쪽이 틀렸는지 노출하지 않는다")로 판정해 적는다
- [ ] `M-12`·`B-12` 를 막지 않는다. 두 항목의 검증표는 **서명 유효** 토큰만 쓰고 만료와 겹치는 케이스를 요구하지 않는다

---
## 7. 다음 단계

**AU-11·M-11·B-09가 모두 `done`이 되면** [integration.md](integration.md)로 넘어간다.

세 서비스가 모두 기동된 상태를 전제하므로 통합 검증은 순차로 진행한다.

**통합 검증이 결함을 찾으면 그것을 고치는 항목이 생긴다.** B-10이 그렇게 생겼다(I-03이 찾았다). **그 항목은 통합 검증과 병행하되 1차 완료 전에 `done`이어야 한다** — 통합 항목의 선행 조건에 끼워 넣지 않는 이유는 발견 시점이 그보다 뒤이기 때문이다. **1차가 끝났다고 말할 수 있는 조건은 `AU-xx`·`M-xx`·`B-xx`·`I-xx`가 모두 `done`인 것이다.**

> **1차는 2026-10-18 에 완료됐다.** `AU-01`~`AU-11`(+`AU-03R`) · `M-01`~`M-11`(+`M-01R`, `M-06`·`M-07`은 auth로 옮겨가 없다) · `B-01`~`B-11` · `I-01`~`I-05` 가 모두 `done` 이다(`sp-auth` `e5fe6a8` · `sp-member` `98f11be` · `sp-board` `2ea6a17`). **`AU-12` 는 존재하지 않는다** — 이 줄의 앞 판이 그렇게 적었고 D-02 리뷰가 잡았다. 번호는 재사용하지 않으므로([README.md](README.md) §항목 ID 규칙) 없는 번호를 완료 명부에 두면 다음 auth 항목이 그것을 집을 때 충돌한다.
>
> **바로 위 「통합 검증이 결함을 찾으면 그것을 고치는 항목이 생긴다」 규칙은 선언 당시 정본을 깨는 결함에 적용된다.** B-10 이 그 경우다 — `api-contract.md` §4.5 가 **1차 동안** "`comment_count` 와 `totalElements` 가 같다" 를 요구했고 구현이 그것을 깼다. 그래서 1차 안에서 고쳐야 했다.
>
> **`M-12`·`B-12` 가 고치는 것은 2026-10-18 에 새로 생긴 요구다.** 1차가 끝날 때까지 [../api-contract.md §6](../api-contract.md)은 `role` 의 **값**만 못박았고 **소비자가 검증해야 한다**고는 말하지 않았다. 그때 열려 있던 것은 "결함인가" 가 아니라 **"결함인지를 정해야 한다"**(= D-02)였고, `D-xx` 는 그 규칙의 완료 조건에 애초에 들어 있지 않다. **1차가 요구받은 적 없는 것을 구현하는 항목이므로 `[1차 후]` 다** — 그 요구의 발효 날짜가 §6 에 적혀 있다.
>
> **이 구분을 적어 두는 이유는 그 구분이 없으면 규칙을 피할 수 있기 때문이다.** `D-xx` 를 열어 두고 구현 항목을 선언 뒤에 세우는 순서로 언제든 그 규칙을 비껴갈 수 있다 — **D-02 의 순서가 실제로 그 모양이었다**(D-02 등록 02:26 → 1차 선언 09:56 → `M-12`·`B-12` 등록 10:30). 그것이 아니었다는 근거는 **면제가 선언보다 7시간 반 앞섰다**는 것과 위의 발효 날짜뿐이고, **그 근거가 문서에 없으면 읽는 사람은 편의로 읽는다.** 다음에 `[1차 후]` 를 붙일 때는 **요구가 언제 생겼는지를 먼저 적는다.**
>
> **`D-xx` 는 애초에 그 조건에 들어 있지 않다.** 상태는 [../docs/checklist.md](../docs/checklist.md)가 갖는다.
