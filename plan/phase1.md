---
title: 1차 작업 계획
type: plan
status: living
version: v4
updated: 2026-09-15
read_when: "작업 항목의 범위·의존·완료 기준을 확인하거나 다음 할 일을 고를 때. 상태는 담당 저장소의 checklist.md를 본다"
related: [README.md, integration.md, ../process/dev-workflow.md, ../requirements/member.md, ../requirements/board.md]
---
# 1차 작업 계획

작업 항목 31개(AU 11 + M 11 + B 9)와 통합 검증 5개로 구성한다. 통합 검증은 [integration.md](integration.md)에 있다.

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
| **기반** | AU-01~AU-04, M-01R~M-04, B-01~B-04 | 순차. 뒤의 모든 항목이 의존한다 |
| **기능** | AU-05~AU-11, M-05·M-08~M-11, B-05~B-09 | 기반 산출물을 **읽기만** 하고 자기 파일을 만든다 |

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

D-01은 구현 항목이 아니므로 리뷰 게이트의 대상은 같지만 테스트 대신 **참조 정합성 검증**으로 완료를 판정한다.

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
| **auth** | `V1__create_account.sql`, `V2__create_refresh_token.sql` (AU-03) | `V3__seed_admin_account.sql` (AU-05) |
| **member** | `V1__create_member.sql` (M-03) | `V2__seed_admin_profile.sql` (M-05) |
| board | `V1__create_post.sql`, `V2__create_comment.sql` (B-03) | 없음 |

> **member의 번호 의미가 바뀌었다.** v3에서 `V2`는 `create_refresh_token`이었으나, 그 테이블이 auth로 옮겨가면서 `V2`가 seed가 됐다. **코드가 아직 없으므로 무해하지만, v3 기준으로 기억한 번호를 쓰지 않는다.**

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
- [ ] `/swagger-ui.html`이 열린다

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
- [ ] **테스트가 `application-test.yml`의 URL(`MODE=MySQL`)로 돈다**
- [ ] **`ddl-auto: validate`가 실제로 적용된다**

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
| 테스트 실행 중 DataSource URL | `MODE=MySQL` 포함 |
| 엔티티에만 있는 컬럼 추가 후 실행 | **실패** — `SchemaManagementException` |

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
- `db/migration/V3__seed_admin_account.sql` (**`id` 명시 고정**, BCrypt 해시)

**완료 기준**
- [ ] `POST /api/v1/accounts`가 201과 `{accountId, email}`을 반환한다
- [ ] **응답에 `password`가 포함되지 않는다**
- [ ] 비밀번호가 BCrypt로 해싱되어 저장된다
- [ ] 중복 이메일 409 `AU002`
- [ ] 검증 규칙이 [../requirements/member.md §2](../requirements/member.md)와 일치한다
- [ ] `GET /api/v1/accounts/check-email`이 동작한다
- [ ] **탈퇴 계정의 이메일로 재가입할 수 없다** (409 `AU002`)
- [ ] **seed의 `account.id`가 SQL에 명시되어 있다.** AUTO_INCREMENT에 맡기지 않는다
- [ ] seed 비밀번호가 BCrypt 해시로 저장되어 있다 (평문 아님)
- [ ] **닉네임을 받지도 저장하지도 않는다**

**검증** — `AccountServiceTest`, `AccountControllerTest`

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
| seed 적용 후 `SELECT id FROM account WHERE role='ADMIN'` | SQL에 적힌 값과 일치 |

---

### AU-06 로그인 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-05 |
| 참조 | [../requirements/member.md §1](../requirements/member.md) (MR-04), [../security.md §4](../security.md), [../api-contract.md §9.2](../api-contract.md) |

**산출물**
- `auth/dto/LoginRequest.java`
- `auth/service/AuthService.java` (생성)
- `auth/controller/AuthController.java` (생성)

**완료 기준**
- [ ] `POST /api/v1/auth/login`이 200과 `TokenResponse`를 반환한다
- [ ] 비밀번호 불일치·없는 이메일 **모두** 401 `AU003` (어느 쪽이 틀렸는지 노출하지 않는다)
- [ ] **탈퇴 계정(`deleted = true`)은 로그인할 수 없다**
- [ ] 발급된 토큰의 `sub`·`role` Claim이 계정 정보와 일치한다
- [ ] **토큰에 `nickname` Claim이 없다**
- [ ] **프로필이 없어도 로그인이 된다.** auth는 프로필 존재를 모른다

**검증** — `AuthServiceTest`, `AuthControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 로그인 | 200, accessToken·refreshToken 존재 |
| 비밀번호 불일치 | 401 `AU003` |
| 없는 이메일 | 401 `AU003` (메시지가 위와 동일) |
| **탈퇴 계정 로그인** | **401** |
| 발급 토큰의 Claim | 계정의 `id`·`role`과 일치, `nickname` 없음 |
| 유효 토큰으로 `/accounts/me` 접근 | 401이 아님 |

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

**경합 방지가 이 항목의 핵심이다.** 재발급은 RefreshToken 조회와 `account.deleted` 확인을 **같은 트랜잭션**에서 하고, 회전은 AU-03의 조건부 UPDATE로 처리한다. 그렇지 않으면 탈퇴와 겹칠 때 삭제한 행이 되살아나 탈퇴 계정이 14일간 갱신할 수 있다([../requirements/member.md §6](../requirements/member.md)).

**완료 기준**
- [ ] `POST /api/v1/auth/reissue`가 새 Access/Refresh를 반환한다
- [ ] Rotation이 적용된다 (이전 Refresh Token은 무효)
- [ ] 저장값과 다른 Refresh Token은 거부된다
- [ ] 만료·변조된 Refresh Token은 거부된다
- [ ] **탈퇴 계정은 재발급받을 수 없다**
- [ ] **조회와 `deleted` 확인이 같은 트랜잭션이다**
- [ ] **회전이 조건부 UPDATE이고 0행이면 실패한다**
- [ ] `POST /api/v1/auth/logout`이 204를 반환하고 저장된 Refresh Token을 삭제한다
- [ ] 로그아웃 후 같은 Refresh Token으로 재발급이 실패한다

**검증** — `AuthServiceTest`, `AuthControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 재발급 | 200, 새 토큰 2개 |
| 이전 Refresh Token 재사용 | 실패 |
| 저장값과 다른 토큰 | 실패 |
| 만료된 Refresh Token | 실패 |
| **탈퇴 계정의 유효 Refresh Token** | **실패** |
| **탈퇴 커밋 후 재발급 시도** | **실패. `refresh_token` 행이 되살아나지 않음** |
| 정상 로그아웃 | 204, `refresh_token` 행 삭제됨 |
| 로그아웃 후 재발급 | 실패 |

---

### AU-08 비밀번호 변경 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-07 |
| 공유 파일 | `AccountService`, `AccountController` (AU-05 생성) |
| 참조 | [../requirements/member.md §1 §3](../requirements/member.md) (MR-09), [../security.md §7](../security.md) |

**산출물**
- `account/dto/PasswordChangeRequest.java`
- `AccountService`·`AccountController` 확장

**완료 기준**
- [ ] `PATCH /api/v1/accounts/me/password`가 204를 반환한다
- [ ] 현재 비밀번호 불일치 시 400 `AU004`
- [ ] 새 비밀번호가 BCrypt로 해싱되어 저장된다 (`Account.changePassword()` 사용)
- [ ] **비밀번호 변경 시 Refresh Token이 삭제된다**
- [ ] **두 연산이 한 로컬 트랜잭션이다**

**검증** — `AccountServiceTest`, `AccountControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 변경 | 204, 새 비밀번호로 로그인 가능 |
| 현재 비밀번호 불일치 | 400 `AU004` |
| 변경 후 `refresh_token` 행 | 삭제됨 |
| 새 비밀번호 형식 오류 | 400 `C001` |
| 변경 중 예외 발생 | 비밀번호와 토큰 **둘 다** 롤백 |

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
- [ ] `Account.withdraw()`로 `deleted = true`가 된다 (행 삭제 아님)
- [ ] **해당 계정의 Refresh Token이 전부 삭제된다**
- [ ] **두 연산이 한 로컬 트랜잭션이다**
- [ ] **멱등이다.** 이미 탈퇴한 계정에 다시 호출해도 204
- [ ] 탈퇴 후 로그인·재발급이 실패한다
- [ ] **member를 호출하지 않는다.** 프로필 삭제는 클라이언트가 2단계로 호출한다

**검증** — `AccountServiceTest`, `AccountControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 탈퇴 | 204, `deleted = true`, 행 존재 |
| **비밀번호 없이 요청** | **400 `C001`** |
| **비밀번호 불일치** | **400 `AU004`. `deleted`가 그대로 false** |
| 탈퇴 시 `refresh_token` 행 | 삭제됨 |
| 탈퇴 후 로그인 | 401 |
| 탈퇴 후 재발급 | 실패 |
| **이미 탈퇴한 계정에 재호출** | **204** (멱등) |
| 탈퇴 중 예외 발생 | `deleted`와 토큰 **둘 다** 롤백 |
| 탈퇴 직후 발신 호출 | **없음.** member를 호출하지 않는다 |

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

---

### AU-11 마무리 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-10 |
| 참조 | [../nfr.md](../nfr.md), [../tech-stack.md §6](../tech-stack.md) |

**산출물**
- `README.md` 갱신 (실행 절차, 환경변수 목록, **키 배치 절차**)
- Actuator 설정 (`/actuator/health`만 노출)
- `application-prod.yml` (Swagger·SQL 로그 비활성화)

**완료 기준**
- [ ] `README.md`에 로컬 실행 절차와 필요한 환경변수가 모두 적혀 있다
- [ ] `README.md`에 **개인키 배치 절차**가 적혀 있다
- [ ] `/actuator/health`가 동작하고 그 외 엔드포인트는 노출되지 않는다
- [ ] `prod` 프로파일에서 Swagger UI가 비활성화된다
- [ ] `prod` 프로파일에서 SQL 로그가 꺼진다
- [ ] 전체 테스트가 통과한다 (`./gradlew test`)
- [ ] **커밋된 파일에 개인키·비밀 값이 없다**

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| `/actuator/health` | 200, `{"status":"UP"}` |
| `/actuator/env` | 404 또는 403 |
| `prod` 프로파일로 `/swagger-ui.html` | 404 |
| `git log -p`에서 `BEGIN PRIVATE KEY` 검색 | **없음** |
| `git log -p`에서 비밀번호 검색 | 없음 |

## 5. member-service 작업 항목

**M-01은 `done`이지만 완료 기준이 깨졌다.** auth 분리로 [../tech-stack.md §3.2](../tech-stack.md)의 의존성 배정이 바뀌었기 때문이다. §2.6 #2에 해당하므로 항목을 수정하지 않고 **`M-01R`을 신설해** 처리한다.

**M-06·M-07은 없다.** 로그인·재발급·로그아웃이 auth로 옮겨가 `AU-06`·`AU-07`이 됐다. 번호는 재사용하지 않는다.

### M-01 프로젝트 스캐폴딩 [기반 · done]

원래 완료 기준은 그대로 둔다. 바뀐 부분은 `M-01R`이 처리한다.

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
- [ ] **`spring-security-oauth2-jose`가 없다.** member는 서명하지 않는다([../security.md §2](../security.md))
- [ ] `spring-boot-starter-oauth2-resource-server`가 있다
- [ ] 그 외 [../tech-stack.md §3.1](../tech-stack.md)의 의존성이 전부 선언되어 있다
- [ ] `INTERNAL_API_KEY`가 기본값 없이 외부화되어 있다
- [ ] `./gradlew build`가 성공하고 8081 포트에 기동된다
- [ ] M-01의 나머지 완료 기준이 여전히 충족된다

**검증** — `MemberApplicationTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 컨텍스트 로딩 | 예외 없이 기동 |
| 의존성 트리에서 `oauth2-jose` 검색 | **없음** |
| `INTERNAL_API_KEY` 없이 기동 | 기동 실패 |

---

### M-02 공통 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-01R |
| 참조 | [../api-contract.md §7 §8.1 §8.2](../api-contract.md), [../domain-model.md §1.1](../domain-model.md), [../conventions.md §6 §7](../conventions.md) |

**산출물**
- `global/common/ApiResponse.java`, `ErrorResponse.java`, `PageResponse.java`
- `global/common/BaseTimeEntity.java`
- `global/error/ErrorCode.java` (C001~C005, A001~A004, **M001·M003·M006·M007**)
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
- [ ] `/swagger-ui.html`이 열린다

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

---

### M-03 도메인 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-02 |
| 참조 | [../domain-model.md §1 §3](../domain-model.md), [../conventions.md §2](../conventions.md), [../requirements/member.md §3](../requirements/member.md) |

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
- [ ] **테스트가 `application-test.yml`의 URL(`MODE=MySQL`)로 돈다**
- [ ] **`ddl-auto: validate`가 실제로 적용된다**

**검증** — `MemberRepositoryTest` (`@DataJpaTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| 저장 후 조회 | 모든 필드 일치 |
| 중복 `account_id` 저장 | `DataIntegrityViolationException` |
| 중복 nickname 저장 | `DataIntegrityViolationException` |
| 저장 시 | `createdAt`, `updatedAt` null 아님 |
| `deleted` 미지정 저장 | `false` |
| `updateNickname()` 호출 | 닉네임만 변경, `createdAt` 불변 |
| `withdraw()` 호출 | `deleted = true`, **`nickname = null`**, 행 존재 |
| **두 회원을 연달아 `withdraw()`** | **둘 다 성공.** UNIQUE 위반 없음 |
| `MemberReader`로 없는 `accountId` 조회 | `BusinessException(M001)` |
| 테이블 메타데이터 | `email`·`password`·`role` 컬럼 없음 |
| 테스트 실행 중 DataSource URL | `MODE=MySQL` 포함 |
| 엔티티에만 있는 컬럼 추가 후 실행 | **실패** — `SchemaManagementException` |

> **탈퇴 2건 연속 테스트를 반드시 넣는다.** 첫 탈퇴는 항상 성공하므로 1건만 보면 UNIQUE 결함을 놓친다.

---

### M-04 보안 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-03 |
| 참조 | [../security.md](../security.md) 전체, [../api-contract.md §3 §6](../api-contract.md), [../conventions.md §1.2](../conventions.md) |

**member는 검증만 한다.** 개인키·`JwtTokenProvider`·`TokenResponse`는 auth(`AU-04`)로 옮겨갔다.

**산출물**
- `global/config/SecurityConfig.java` — **[../api-contract.md §3](../api-contract.md)의 전체 경로 인가**, 공개키 검증기, CORS, STATELESS
- `global/security/RoleClaimConverter.java` (`role` claim → `GrantedAuthority`)
- `global/security/LoginMember.java` (record), `@CurrentMember` ArgumentResolver
- `src/main/resources/jwt-public.pem` (**공개키. 커밋 가능**)

**⚠ `LoginMember`는 `(accountId, role)`이다.** `nickname`이 없다 — Claim에 없기 때문이다([../api-contract.md §6](../api-contract.md)).

**⚠ 개인키를 두지 않는다.** member는 토큰을 발급하지 않는다. `oauth2-jose` 의존성도 없다(M-01R).

**⚠ 경로 선언 순서** — `GET /api/v1/members/{accountId}`는 `permitAll`, `/api/v1/members/me`는 `authenticated`다. `requestMatchers`는 **먼저 선언된 규칙이 이기므로** `/members/me`를 반드시 먼저 선언한다. 뒤에 두면 **내 정보가 인증 없이 열린다.**

**실제 공개키가 이미 배치되어 있다.** AU-04를 기다리지 않는다. I-01에서 두 사본의 일치와 실제 발급 토큰 수용을 확인한다.

**완료 기준**
- [ ] 공개키로 서명 검증이 동작한다
- [ ] **개인키를 로딩하지 않는다.** 서명 기능이 없다
- [ ] `LoginMember`가 `(accountId, role)`이고 **`nickname` 필드가 없다**
- [ ] `role` claim이 `GrantedAuthority`로 변환된다
- [ ] [../api-contract.md §3](../api-contract.md)의 **모든 경로**에 인가 규칙이 선언되어 있다
- [ ] **`/members/me`가 `/members/{accountId}`보다 먼저 선언되어 있다**
- [ ] `/internal/**`이 외부 인증 체인에서 분리되어 있다
- [ ] 세션이 생성되지 않는다
- [ ] CORS 설정에 `*`가 없다
- [ ] 공개키가 없으면 **기동이 실패한다**

**검증** — `SecurityConfigTest` (`@SpringBootTest` + MockMvc)

| 케이스 | 기대 결과 |
| --- | --- |
| 유효 토큰으로 인증 | 통과, `LoginMember.accountId()`가 `sub`와 일치 |
| `LoginMember` 필드 목록 | `nickname` 없음 |
| payload 변조된 토큰 | 401 |
| 만료된 토큰 | 401 `A003` |
| **토큰 없이 `GET /api/v1/members/me`** | **401 `A001`** |
| **토큰 없이 `GET /api/v1/members/1`** | **401이 아님** |
| 공개키 없이 기동 | 기동 실패 |
| 응답 헤더 | `Set-Cookie` 세션 쿠키 없음 |

> `/members/me`와 `/members/{accountId}` 두 케이스를 **반드시 함께** 검증한다. 하나만 보면 순서 결함을 놓친다.

---

### M-05 프로필 등록과 닉네임 중복 확인 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-04 |
| 참조 | [../requirements/member.md §1 §2 §3 §4 §10](../requirements/member.md) (MR-01 3단계, MR-03), [../api-contract.md §3 §9.1](../api-contract.md) |

**가입 3단계다.** 계정 생성(AU-05)과 로그인(AU-06)이 먼저다.

**산출물**
- `member/dto/ProfileCreateRequest.java`, `MemberResponse.java`, `CheckResponse.java`
- `member/service/MemberService.java` (생성)
- `member/controller/MemberController.java` (생성)
- `db/migration/V2__seed_admin_profile.sql` (**`account_id`는 AU-05가 고정한 값**)

**⚠ `POST /api/v1/members`는 인증이 필요하다.** `account_id`는 **검증된 JWT의 `sub`에서만** 가져온다. 요청 본문의 식별자를 신뢰하지 않는다.

**⚠ 이메일·비밀번호를 받지 않는다.** 계정은 auth 소유다.

**완료 기준**
- [ ] `POST /api/v1/members`가 **인증을 요구한다.** 토큰 없으면 401 `A001`
- [ ] 201과 `{accountId, nickname}`을 반환한다
- [ ] **`account_id`가 JWT `sub`에서 온다.** 본문에 다른 값을 넣어도 무시된다
- [ ] **멱등이다** — 상태별 응답이 [../api-contract.md §3](../api-contract.md) 표와 일치한다
- [ ] 중복 닉네임 409 `M003`
- [ ] 검증 규칙이 [../requirements/member.md §2](../requirements/member.md)와 일치한다
- [ ] `GET /api/v1/members/check-nickname`이 동작한다
- [ ] **이메일·비밀번호를 받지도 저장하지도 않는다**
- [ ] seed 프로필의 `account_id`가 `AU-05`의 seed와 같은 값이다

**검증** — `MemberServiceTest`, `MemberControllerTest`

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
| 참조 | [../requirements/member.md §1 §5 §7](../requirements/member.md) (MR-07의 프로필 절반, MR-08) |

**MR-07이 두 서비스로 갈라진 절반이다.** 이메일·가입일은 `AU-10`이 담당한다.

**산출물**
- `member/dto/NicknameUpdateRequest.java`, `MemberResponse.java` 재사용
- `MemberService`·`MemberController` 확장

**⚠ 새 Access Token을 반환하지 않는다.** 이전 v3의 요구는 **폐기됐다.** Claim에 `nickname`이 없으므로 토큰이 낡을 이유가 없고, member는 개인키가 없어 발급할 수도 없다([../requirements/member.md §7](../requirements/member.md)).

**완료 기준**
- [ ] `GET /api/v1/members/me`가 내 프로필(닉네임)을 반환한다
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
| 응답 본문 | **`email` 키 없음, `accessToken` 키 없음** |
| **프로필 없는 계정으로 조회** | **404 `M001`** |
| 닉네임 변경 | 200, DB 반영됨 |
| 변경 응답 본문 | **토큰 키 없음** |
| 타인 닉네임으로 변경 | 409 `M003` |
| 자기 현재 닉네임으로 변경 | 200 |
| 닉네임 1자 | 400 `C001` |
| 탈퇴한 프로필로 조회 | 404 `M001` |
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
- [ ] **auth를 호출하지 않는다**
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
| 탈퇴 중 발신 호출 | **없음** |

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
- [ ] `GET /api/v1/members/{accountId}`가 공개 정보(닉네임, 가입일)만 반환한다. **이메일 미포함**
- [ ] **경로 변수가 `accountId`다.** `member.id`를 외부에 노출하지 않는다
- [ ] **`GET /members/me`가 `GET /members/{accountId}`보다 먼저 매칭된다**
- [ ] `POST /internal/v1/members/bulk`가 [../api-contract.md §5](../api-contract.md) 형식으로 응답한다
- [ ] 요청 키가 `accountIds`, 응답 키가 `accountId`다
- [ ] **존재하지 않는 id는 결과에서 제외된다.** 404가 아니다
- [ ] 탈퇴 프로필은 `deleted: true`, 닉네임 `"탈퇴한 회원"` (**DB에는 NULL**)
- [ ] 내부 API 응답에 이메일·비밀번호가 없다 (애초에 갖고 있지 않다)
- [ ] `X-Internal-Api-Key` 없이 호출하면 401 또는 403이다
- [ ] 내부 API 키가 **기본값 없이** 주입된다
- [ ] **단건 전용 엔드포인트가 없다**

**검증** — `MemberControllerTest`, `InternalMemberControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 프로필 조회 | 200, `email` 키 없음 |
| **`GET /members/me` (유효 토큰)** | **내 정보 반환** (`me`를 accountId로 해석하지 않음) |
| 정상 벌크 조회 (3건) | 200, 3건 반환 |
| **벌크 1건 요청** | **200, 1건 반환** |
| **존재하지 않는 id 포함** | **200. 해당 id는 결과에서 제외. 404 아님** |
| **전부 존재하지 않는 id** | **200, 빈 배열. 404 아님** |
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

**완료 기준**
- [ ] `README.md`에 로컬 실행 절차와 필요한 환경변수가 모두 적혀 있다
- [ ] `README.md`에 **공개키 배치 절차**와 `INTERNAL_API_KEY`가 적혀 있다
- [ ] `/actuator/health`가 동작하고 그 외 엔드포인트는 노출되지 않는다
- [ ] `prod` 프로파일에서 Swagger UI가 비활성화된다
- [ ] `prod` 프로파일에서 SQL 로그가 꺼진다
- [ ] 전체 테스트가 통과한다 (`./gradlew test`)
- [ ] 커밋된 파일에 비밀 값이 없다
- [ ] **개인키가 저장소에 없다**

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| `/actuator/health` | 200, `{"status":"UP"}` |
| `/actuator/env` | 404 또는 403 |
| `prod` 프로파일로 `/swagger-ui.html` | 404 |
| `git log -p`에서 `BEGIN PRIVATE KEY` 검색 | **없음** |
| `git log -p`에서 키·비밀번호 검색 | 없음 |

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
| 참조 | [../api-contract.md §7 §8.1 §8.3](../api-contract.md), [../domain-model.md §1.1](../domain-model.md), [../conventions.md §6 §7](../conventions.md) |

**산출물**
- `global/common/ApiResponse.java`, `ErrorResponse.java`, `PageResponse.java`
- `global/common/BaseTimeEntity.java`
- `global/error/ErrorCode.java` (C001~C005, A001~A004, **P001, P002, CM001, CM002, S001, S002**)
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
- [ ] `/swagger-ui.html`이 열린다

**검증** — `GlobalExceptionHandlerTest` (`@WebMvcTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| `BusinessException(P001)` | 404 `P001` |
| `BusinessException(P002)` | 403 `P002` |
| `@Valid` 실패 | 400 `C001`, `fieldErrors` 존재 |
| 성공 응답 | `success = true`, `error = null` |
| 예상치 못한 예외 | 500 `C005`, 스택트레이스 없음 |

---

### B-03 도메인 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-02 |
| 참조 | [../domain-model.md §3 §4](../domain-model.md), [../conventions.md §2](../conventions.md), [../requirements/board.md §3 §5](../requirements/board.md) |

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
- [ ] 컬럼이 [../domain-model.md §3](../domain-model.md)과 일치한다
- [ ] **`post.writer_id`, `comment.writer_id`에 FK 제약이 없다**
- [ ] `post.content`가 `TEXT` 타입이다
- [ ] `idx_post_created_at`, `idx_post_writer_id`, `idx_post_title`, `idx_comment_post_id`가 있다
- [ ] `view_count`, `comment_count` 기본값이 0이다
- [ ] 위 표의 도메인 메서드 6개가 모두 구현되어 있다
- [ ] `decreaseCommentCount()`가 0에서 호출돼도 음수가 되지 않는다
- [ ] `CommentRepository.softDeleteByPostId()`가 동작한다
- [ ] Entity에 `@Setter`·`@Data`가 없다
- [ ] **`@DataJpaTest` 클래스에 `@AutoConfigureTestDatabase(replace = NONE)`이 붙어 있다** ([../tech-stack.md §5.2](../tech-stack.md))
- [ ] **테스트가 `application-test.yml`의 URL(`MODE=MySQL`)로 돈다.** `jdbc:h2:mem:<uuid>`가 아니다
- [ ] **`ddl-auto: validate`가 실제로 적용된다.** 엔티티에만 있고 마이그레이션에 없는 컬럼을 넣으면 테스트가 실패해야 한다

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
| 테스트 실행 중 DataSource URL | `MODE=MySQL` 포함 (`jdbc:h2:mem:<uuid>` 아님) |
| 엔티티에만 있는 컬럼 추가 후 실행 | **실패** — `SchemaManagementException`. 초록이면 `validate`가 안 걸린 것 |

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
- [ ] [../api-contract.md §3](../api-contract.md)의 **모든 경로**에 인가 규칙이 선언되어 있다
- [ ] 비로그인 허용 경로(`GET /posts`, `GET /posts/{id}`, 댓글 목록)가 토큰 없이 통과한다
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

**`MemberClientTest`** — 스텁 서버로 응답을 흉내 낸다

| 스텁 응답 | 기대 결과 |
| --- | --- |
| 200 + `[{accountId:3, nickname:"홍길동", deleted:false}]` | 닉네임 `"홍길동"` 반환 |
| 200 + `{members: []}` (결과에서 제외됨) | `BusinessException(S002)` |
| 200 + `[{accountId:3, deleted:true}]` | `BusinessException(S002)` |
| **404 (경로 오설정)** | **`BusinessException(S001)`. `S002` 아님** |
| **401 (API 키 거부)** | **`BusinessException(S001)`** |
| 500 | `BusinessException(S001)` |
| 응답 없음 (타임아웃) | `BusinessException(S001)` |
| 본문 파싱 실패 | `BusinessException(S001)` |
| 요청 헤더 | `X-Internal-Api-Key` 존재 |

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
- [ ] `GET /api/v1/posts/{id}`가 상세를 반환한다 (비로그인 허용)
- [ ] 상세 조회 시 `view_count`가 1 증가한다 (`Post.increaseViewCount()` 사용)
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
| 제목 201자 / 공백만 | 400 `C001` |

---

### B-06 게시글 목록과 QueryDSL 검색 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-board` |
| 의존 | B-05 |
| 공유 파일 | `PostService`, `PostController` (B-05 생성) |
| 참조 | [../requirements/board.md §1 §6](../requirements/board.md) (P-02, P-03), [../api-contract.md §4.1 §7.1](../api-contract.md), [../nfr.md §1](../nfr.md) |

**산출물**
- `post/dto/PostSearchCondition.java`, `SearchType.java`, `PostSortType.java`
- `post/repository/PostQueryRepository.java` (QueryDSL)
- `PostService`·`PostController` 확장

**완료 기준**
- [ ] `GET /api/v1/posts`가 페이징 응답을 반환한다 ([../api-contract.md §7.1](../api-contract.md) 형식)
- [ ] 기본 `size` 10, 51 요청 시 50으로 절삭
- [ ] `sort=latest`, `sort=views`가 동작한다
- [ ] 삭제된 게시글이 목록에서 제외된다
- [ ] 4가지 `searchType`이 모두 동작한다
- [ ] `keyword`가 없으면 전체 목록
- [ ] `searchType`만 있고 `keyword`가 없으면 400 `C001`
- [ ] **목록 조회 시 member-service를 호출하지 않는다**
- [ ] 정렬 파라미터로 임의 컬럼명을 넣을 수 없다 (Enum 화이트리스트)

**검증** — `PostQueryRepositoryTest` (`@DataJpaTest`), `PostControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 15건 저장 후 목록 조회 | 10건, `totalElements = 15` |
| `size=51` | 50건 이하 |
| `sort=latest` / `sort=views` | 각각 내림차순 |
| 삭제 게시글 포함 상태 | 삭제분 제외 |
| `searchType=TITLE&keyword=공지` | 제목 포함분만 |
| `searchType=CONTENT` / `TITLE_CONTENT` | 각 기준 |
| `searchType=WRITER&keyword=홍길동` | `writer_nickname` 기준 |
| `keyword` 없이 조회 | 전체 |
| `searchType=TITLE`만 전달 | 400 `C001` |
| `sort=password` | 400 |

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
- [ ] 소유자 검증이 Service 계층에 있다
- [ ] 수정 시 `writer_id`, `writer_nickname`이 바뀌지 않는다

**검증** — `PostServiceTest`, `PostControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 본인 글 수정 | 200, 반영됨 |
| 타인 글 수정 | 403 `P002` |
| **ADMIN이 타인 글 수정** | **403 `P002`** |
| 수정 후 `writer_id` | 변경 없음 |
| 본인 글 삭제 | 204, `deleted = true`, 행 존재 |
| ADMIN이 타인 글 삭제 | 204 |
| 타인(일반)이 삭제 | 403 `P002` |
| **게시글 삭제 후 하위 댓글** | **전부 `deleted = true`** |
| 없는 글 수정 | 404 `P001` |
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
- [ ] 댓글 작성 시 `post.comment_count`가 1 증가한다 (`Post.increaseCommentCount()` 사용)
- [ ] 댓글 삭제 시 1 감소한다
- [ ] **`comment_count`가 음수가 되지 않는다**
- [ ] 작성자 본인만 수정, 본인·ADMIN이 삭제할 수 있다
- [ ] 삭제는 Soft Delete다
- [ ] **`writer_id`는 JWT `sub`, `writer_nickname`은 `MemberClient` 응답에서 가져온다**
- [ ] **프로필이 없거나 탈퇴했으면 403 `S002`이고 댓글이 저장되지 않는다**
- [ ] **member 호출 실패 시 503 `S001`이고 댓글이 저장되지 않는다**
- [ ] **원격 호출이 DB 트랜잭션 밖에서 일어난다.** `comment_count`도 증가하지 않는다
- [ ] 댓글 수정·삭제는 `MemberClient`를 호출하지 않는다
- [ ] 없는 게시글에 댓글 작성 시 404 `P001`
- [ ] 댓글 목록이 등록순 페이징(기본 20)으로 반환된다

**검증** — `CommentServiceTest`, `CommentControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 댓글 작성 | 201, `comment_count = 1` |
| 저장된 `writer_nickname` | `MemberClient` 응답값과 일치 |
| **프로필 미등록 계정으로 작성** | **403 `S002`. 댓글 0개, `comment_count` 불변** |
| **member 타임아웃** | **503 `S001`. 댓글 0개, `comment_count` 불변** |
| **member가 404 반환** | **503 `S001`** |
| 댓글 수정·삭제 시 `MemberClient` | **호출 0회** |
| 댓글 목록 조회 시 `MemberClient` | **호출 0회** |
| 댓글 3개 작성 후 1개 삭제 | `comment_count = 2` |
| 같은 댓글 2회 삭제 시도 | `comment_count` 음수 안 됨 |
| 목록 조회 | 등록순, 기본 20건 |
| 본인 댓글 수정 | 200 |
| 타인 댓글 수정 | 403 `CM002` |
| ADMIN이 타인 댓글 수정 | 403 `CM002` |
| ADMIN이 타인 댓글 삭제 | 204 |
| 없는 게시글에 댓글 | 404 `P001` |
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
- [ ] 내가 쓴 글 목록이 `writer_id` 기준으로 페이징 조회된다
- [ ] 삭제된 글은 제외된다
- [ ] `README.md`에 실행 절차와 환경변수가 적혀 있다
- [ ] `/actuator/health`만 노출된다
- [ ] `prod` 프로파일에서 Swagger·SQL 로그가 꺼진다
- [ ] 전체 테스트가 통과한다
- [ ] 목록 조회 쿼리에 N+1이 없다

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| 내 글 5건 + 타인 글 3건 | 5건만 반환 |
| 내 글 중 삭제분 포함 | 삭제분 제외 |
| 토큰 없이 호출 | 401 `A001` |
| 목록 조회 쿼리 수 | 게시글 수와 무관하게 일정 |
| `/actuator/env` | 404 또는 403 |

## 7. 다음 단계

**AU-11·M-11·B-09가 모두 `done`이 되면** [integration.md](integration.md)로 넘어간다.

세 서비스가 모두 기동된 상태를 전제하므로 통합 검증은 순차로 진행한다.
