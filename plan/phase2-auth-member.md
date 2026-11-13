---
title: 2차 작업 계획 — auth·member 기능 확장
type: plan
status: living
version: v1
updated: 2026-11-12
read_when: "2차 기능 확장의 auth·member 작업 항목(AU-12 부터·M-14 부터)의 범위·의존·마이그레이션 번호·완료 기준을 확인하거나 다음 할 일을 고를 때. 상태는 담당 저장소의 checklist.md 를 본다"
related: [phase2.md, phase1.md, integration.md, ../requirements/member.md, ../domain-model.md, ../api-contract.md, ../security.md, ../conventions.md, ../tech-stack.md]
---
# 2차 작업 계획 — auth·member 기능 확장

**2026-11-12 `D-20` 이 썼다.** [phase2.md §5](phase2.md)의 기능 확장 중 auth·member 쪽을 작업 항목(산출물·참조·의존·마이그레이션·완료 기준·검증)으로 쪼갠다. **설계의 정본은 [phase2.md §5.2](phase2.md)의 둘째 표(auth·member)가 가리키는 곳이고, 이 문서는 작업 항목만 갖는다** — 완료 기준에 보이는 값은 확인할 자리를 짚으려는 것이고, 정본과 어긋나면 정본이 이긴다(그때 이 문서를 고친다). board 쪽 항목은 이 문서에 없다. 항목 ID 는 auth 가 `AU-12`, member 가 `M-14` 부터 잇고 번호를 재사용하지 않는다([README.md](README.md) §항목 ID 규칙). 절차는 [../process/dev-workflow.md](../process/dev-workflow.md)를, 다른 항목의 산출물을 고칠 때와 멈출 때는 [phase1.md §2.5](phase1.md)·§2.6 을 따른다. **상태는 이 문서에 적지 않는다** — 담당 저장소의 `docs/checklist.md` 가 갖는다.

## 1. 단계와 병렬 가능성

### 1.1 단계

| 단계 | 항목 | 성격 |
| --- | --- | --- |
| **기반** — auth | AU-12~AU-15 | 순차가 기본이다. 테이블·엔티티·에러 코드·예외 매핑·경로 선언·메일 발송·링크 토큰 발급을 여기서 끝낸다 — `C009` 매핑은 제한기와 함께 AU-19 가 둔다. 기능 항목 여럿이 쓰는 문장(토큰 사용 처리와 해시로 읽기, 잠금 해제, 잠금 키 변환)도 여기 둔다 |
| **기반** — member | M-14 | 에러 코드·예외 매핑·경로 선언 — `C009` 매핑은 제한기와 함께 M-15 가 둔다. member 는 마이그레이션이 없다(§2) |
| **기능** — auth | AU-16~AU-21 | 기반 산출물을 읽고 자기 파일을 만든다. 같은 Service·Controller 를 고치는 항목이 있어 저장소 안에서는 §1.2 의 순서를 따른다 |
| **기능** — member | M-15, M-16 | M-14 뒤 |

[phase1.md §1.1](phase1.md)과 같은 이유로 **순서 의존과 공유 상태를 기반에 몰았다.** 에러 코드와 `SecurityConfig` 의 경로·CORS 를 기반이 끝내므로 기능 항목은 그 파일들을 고치지 않는다.

```
                        D-19 설계 (sp-docs)
                               |
            +------------------+-------------------+
            |                                      |
      auth 저장소                             member 저장소
      ───────────                             ─────────────
      AU-12 마이그레이션·엔티티 [기반]         M-14 에러 코드·경로    [기반]
      AU-13 에러 코드·경로      [기반]         ─────────────────────
      AU-14 메일 발송 기반      [기반]         M-15 요청 수 제한      [기능]
      AU-15 링크 토큰 발급      [기반]         M-16 프로필 일괄 조회  [기능]
      ─────────────────────
      AU-16 이메일 인증·AU006   [기능]  <- 화면의 가입 흐름(F-08)과 한 번에 커밋 (§1.3)
      AU-17 비밀번호 재설정     [기능]
      AU-18 로그인 잠금         [기능]
      AU-19 요청 수 제한        [기능]
      AU-20 계정 목록           [기능]  <- M-16 과 함께 화면의 회원 목록
      AU-21 정리 작업           [기능]
            \                                      /
             +---- 통합 측정 (§5.1) · 화면 항목 (§5.2) ----+
```

### 1.2 의존과 병렬

| 항목 | 의존 | 겹치는 파일 (같은 저장소의 다른 항목) | 저장소 밖 |
| --- | --- | --- | --- |
| AU-12 | 없음 | `LoginAttemptRepository`·그 테스트 (AU-18·AU-21), `AccountTokenRepository`·그 테스트 (AU-21) — AU-13·AU-14 와는 없어 함께 돌 수 있다 | — |
| AU-13 | 없음 | `GlobalExceptionHandler`·그 테스트 (AU-19) | 화면: 무인증 경로의 401 (§5.2) |
| AU-14 | 없음 | `application.yml` (AU-19·AU-21), `application-local.yml.example`·`application-test.yml`·`README.md` (AU-19) | 로컬 `local` 기동이 메일 설정을 요구하게 된다 (§1.3) |
| AU-15 | AU-12, AU-14 | — | — |
| AU-16 | AU-13, AU-15 | `AccountController`·`AccountService` (AU-17·AU-19·AU-20), `AuthService` (AU-18) | 화면의 가입 흐름 (§1.3) |
| AU-17 | AU-16 | `AccountController`·`AccountService` | 화면의 비밀번호 찾기·재설정 |
| AU-18 | AU-12, AU-13, AU-16 | `AuthService` (AU-16), `LoginAttemptRepository`·그 테스트 (AU-12·AU-21), `AuthControllerTest` (AU-19) | 화면의 로그인 안내 |
| AU-19 | AU-13, AU-16, AU-17 | `AccountController` (AU-16·AU-17·AU-20), `GlobalExceptionHandler`·그 테스트 (AU-13), `application.yml` (AU-14·AU-21), `application-local.yml.example`·`application-test.yml`·`README.md` (AU-14), `AuthControllerTest` (AU-18) | 화면의 429 안내, 로컬 템플릿 (§1.3) |
| AU-20 | AU-12, AU-13 | `AccountController`·`AccountService` | 화면의 관리자 회원 목록 (M-16 과 함께) |
| AU-21 | AU-12, AU-16, AU-18 | `application.yml` (AU-14·AU-19), `LoginAttemptRepository`·그 테스트 (AU-12·AU-18), `AccountTokenRepository`·그 테스트 (AU-12) | — |
| M-14 | 없음 | `GlobalExceptionHandler`·그 테스트 (M-15) | 화면: 무인증 경로의 401 |
| M-15 | M-14 | `GlobalExceptionHandler`·그 테스트 (M-14), `MemberControllerTest` (M-16) | 화면의 429 안내, 로컬 템플릿 |
| M-16 | M-14 | `MemberControllerTest` (M-15) | 화면의 관리자 회원 목록 (AU-20 과 함께) |

**저장소마다 구현 워커가 하나면**(두 저장소의 `CLAUDE.md` 가 그렇게 적는다 — 2026-11-12 읽기) auth 는 AU-12 → AU-13 → … → AU-21 의 번호 순서로 하나씩 한다. **AU-20 은 의존이 적어 앞당길 수 있다**(예: 화면의 회원 목록을 먼저 할 때). 저장소 안의 병렬은 「겹치는 파일」 이 없는 항목끼리만 한다. auth 와 member 는 서로의 파일을 고치지 않으므로 두 저장소는 처음부터 함께 돈다.

### 1.3 저장소 밖과 맞물리는 때

- **AU-16 이 병합되면 [phase2.md §5.3](phase2.md) 「가입 흐름」 이 적는 `F-04` 가 만든 화면 흐름(계정 → 바로 로그인 → 프로필)이 로그인에서 403 `AU006` 을 받는다.** 화면의 가입 흐름 항목(§5.2)은 AU-16 을 기다리고, **AU-16 은 리뷰 APPROVED 뒤 커밋하지 않고 그 항목(`F-08`)의 APPROVED 를 기다린다 — 오케스트레이터가 둘을 한 번에 커밋한다**([phase2-frontend-integration.md §1.4](phase2-frontend-integration.md), [../process/dev-workflow.md §3.1](../process/dev-workflow.md)). 그동안 auth 의 다른 항목은 멈춘다. AU-16 의 코드가 auth 작업 트리에 있는 동안(구현부터 두 항목의 커밋까지) 그 auth 로 돈 화면의 실제 서비스 e2e 도 가입에서 같은 응답을 받으므로, 오케스트레이터는 F-07 이 `done` 이고 진행 중인 F 항목이 없을 때 AU-16 을 배정하고 그 사이 F 는 F-08 만 한다([phase2-frontend-integration.md §1.4](phase2-frontend-integration.md))
- **AU-14 뒤에는 auth 의 `local` 기동에 메일 설정이 있어야 한다** — 정책값에 기본값이 없고 가드가 기동을 막는다([../tech-stack.md §4.7](../tech-stack.md)). AU-19·M-15 뒤에는 한도를 덮는 줄이 있어야 e2e 가 429 를 맞지 않는다(§4.6). **둘 다 템플릿(`application-local.yml.example`)과 `README.md` 에만 들어간다** — 이미 만든 각자의 `application-local.yml` 에는 옮겨야 한다. 그 항목들(AU-14·AU-19·M-15)의 완료 보고가 옮길 줄을 적는다
- **AU-20 과 M-16 은 둘 다 있어야** 화면이 회원 목록을 합친다([../requirements/member.md §13](../requirements/member.md))
- **board 와** — 이 문서의 항목은 board 저장소의 파일을 고치지 않고 board 의 항목을 기다리지 않는다. multipart 예외 매핑은 `D-18` 이 세 서비스에 같은 매핑을 요구하므로([../conventions.md §6.1](../conventions.md), [../api-contract.md §8.1](../api-contract.md)의 `C008` 문단) auth·member 몫을 AU-13·M-14 가 갖고, 세 서비스의 비교는 통합 측정(§5.1)이 한다

## 2. 마이그레이션 번호

[phase1.md §2.4](phase1.md)의 순번을 잇는다. **워커가 스스로 정하지 않는다.** 할 것은 [../domain-model.md §7](../domain-model.md)의 auth 줄이고, 이름과 폭은 같은 문서 §2.1·§2.3~§2.5 의 표가 정본이다.

| 서비스 | 파일 | 항목 | 담는 것 |
| --- | --- | --- | --- |
| auth | `V6__add_account_email_verified_at.sql` | AU-12 | `account.email_verified_at` 을 더하고, **같은 파일에서** 그때의 행 전부를 `created_at` 으로 채운다 — ADMIN seed(`V3`)의 행도 포함된다 |
| auth | `V7__create_account_token.sql` | AU-12 | `account_token` 과 그 제약·인덱스(§2.3 의 `account_token` 줄) |
| auth | `V8__create_login_attempt.sql` | AU-12 | `login_attempt` 와 그 제약·인덱스. **FK 가 없다.** 테이블 선언은 `V1` 의 `account` 와 같은 문자셋 선언을 쓴다 |
| member | 없음 | — | **member 는 마이그레이션이 없다**([../domain-model.md §7](../domain-model.md)). 일괄 조회의 키 `account_id` 에는 `uk_member_account_id` 가 이미 있다(같은 절) |

**한 파일에 한 테이블이다** — 1차의 `V1`·`V2` 와 같은 묶음이다. `V6` 이 컬럼 추가와 채움을 한 파일에 두는 것은 정본의 요구다(「같은 마이그레이션에서 채운다」). 세 파일은 한 항목(AU-12)이 함께 만들므로 번호 사이에 다른 항목의 마이그레이션이 끼지 않는다.

- **적용된 마이그레이션을 고치지 않는다**([phase1.md §2.4](phase1.md)) — 2026-11-12 폴더 읽기로 auth 는 `V5`, member 는 `V2` 까지 있다
- **H2 와 MySQL 양쪽에서 되는 구문이어야 한다.** 테스트가 같은 파일을 H2(MySQL 모드)로 돌린다([../tech-stack.md §5.3](../tech-stack.md)). 예: 컬럼 단위 `CHARACTER SET` 절은 H2 가 거부한다(auth `V5` 의 주석)
- 배정되지 않은 마이그레이션이 더 필요하면 번호를 붙이지 말고 BLOCKED 로 보고한다([phase1.md §2.6](phase1.md) #3)

## 3. auth-service 작업 항목

### AU-12 2차 마이그레이션과 엔티티 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | 없음 |
| 마이그레이션 | `V6`·`V7`·`V8` (§2) |
| 참조 | [../domain-model.md §2.1](../domain-model.md)·§2.3~§2.5·§7, [../requirements/member.md §11.1](../requirements/member.md)·§12.1·§12.2, [../conventions.md §1.1](../conventions.md)·§9.2 |

**산출물**
- `src/main/resources/db/migration/V6__add_account_email_verified_at.sql`, `V7__create_account_token.sql`, `V8__create_login_attempt.sql`
- `account/entity/Account.java` 확장 — `emailVerifiedAt` 과 인증을 채우는 도메인 메서드
- `account/entity/AccountToken.java`, `account/entity/TokenPurpose.java`
- `account/repository/AccountTokenRepository.java` — 사용 처리(조건부 UPDATE), 해시로 행 읽기(사용 처리가 1행이면 확인이 그 행의 계정 id 를 얻는다 — 판정은 사용 처리가 한다), 같은 계정·목적의 행 지우기
- `auth/entity/LoginAttempt.java`, `auth/repository/LoginAttemptRepository.java` — 키로 읽기, 카운터를 0 으로 하고 잠금을 푸는 문장
- 잠금 키 변환(ASCII 대문자만 소문자로) — 한 곳에 둔다. AU-17·AU-18·AU-20 이 같은 것을 쓴다
- 테스트: `AccountTokenRepositoryTest`, `LoginAttemptRepositoryTest` 신설, `AdminSeedTest`·`AccountRepositoryTest` 확장

**완료 기준**
- [ ] 세 마이그레이션이 [domain-model.md §7](../domain-model.md)의 auth 줄을 한다. 컬럼·타입·제약·인덱스 이름이 §2.1·§2.3~§2.5 의 표와 같다
- [ ] `V6` 이 컬럼 추가와 채움(`UPDATE account SET email_verified_at = created_at`)을 한 파일에 갖는다
- [ ] `V8` 의 `login_attempt` 에 FK 가 없고 테이블 선언이 `V1` 과 같은 문자셋 선언을 쓴다(파일 비교로 확인). **두 컬럼의 실제 콜레이션은 실 MySQL 의 `information_schema` 로만 보이므로 §5.1 로 넘긴다**
- [ ] **세 파일이 H2(MySQL 모드)와 MySQL 양쪽에서 되는 구문이다.** H2 는 `./gradlew test` 가, MySQL 은 로컬 `sp_auth` 에 `local` 기동으로 `V8` 까지 적용한 것이 확인한다. 둘이 다르게 받을 수 있는 구문(예: 한 `ALTER TABLE` 에 여러 절, 컬럼 단위 `CHARACTER SET`)은 쓰면 H2 에서 확인한다(domain-model §7)
- [ ] 적용된 마이그레이션(`V1`~`V5`)을 고치지 않는다
- [ ] 세 테이블의 시각을 쓰는 코드가 앱 시계(`Clock`)의 값을 **초로 잘라** 넣는다(domain-model §1.1·§2.1·§2.4·§2.5)
- [ ] `Account` 의 인증 표시는 이미 채워져 있으면 덮지 않는다. 인증을 되돌리는 메서드를 두지 않는다(§2.1)
- [ ] `AccountToken` 은 `BaseTimeEntity` 를 상속하지 않고 `updated_at` 이 없다(§2.4). `purpose` 는 enum 의 이름으로 저장한다
- [ ] 사용 처리는 domain-model §2.4 의 조건부 UPDATE 하나이고 영향 행 수를 돌려준다 — 읽고 확인한 뒤 쓰는 메서드를 두지 않는다
- [ ] 잠금 키 변환이 ASCII 대문자만 바꾸고 `Locale` 에 따른 변환을 쓰지 않는다(member.md §12.1)
- [ ] 이 항목은 행을 만들고 읽는 바탕만 둔다 — 로그인·메일·엔드포인트의 동작이 바뀌지 않는다(기존 테스트가 그대로 초록이다)

**검증** — 위 테스트 클래스, `./gradlew test`. MySQL 적용은 보고에 기동 로그의 Flyway 줄로 적는다

| 케이스 | 기대 결과 |
| --- | --- |
| 마이그레이션 뒤 ADMIN seed 의 행 | `email_verified_at` 이 그 행의 `created_at` 과 같다 |
| 마이그레이션 뒤에 만든 계정 | `email_verified_at` 이 NULL 이다 |
| 사용 처리 — 쓰이지 않았고 만료 전 | 1행. `used_at` 이 채워진다 |
| 사용 처리 — 이미 씀·만료(시계를 움직인다)·목적 다름·없는 해시 | 각각 0행. **사유마다 따로 단언한다** |
| 같은 계정·목적의 행 지우기 | 그 계정·목적의 행만 지워진다 — 다른 목적·다른 계정의 행이 남는다 |
| `token_hash` 64자·`email_key` 100자·`purpose` 의 가장 긴 열거 값 | 저장된다([../conventions.md §9.2](../conventions.md)) |
| `email_key` 가 같은 둘째 INSERT | 제약 위반이다 |
| 잠금 해제 문장 | 그 키의 `failed_count` 가 0, `locked_until` 이 NULL 이 된다 |
| 키 변환 | ASCII 대문자는 소문자가 되고 비ASCII 는 그대로다(예: U+0130 `İ`) |
| 인증 표시를 두 번 | 처음 시각이 남는다 |
| 소수부가 있는 시계로 쓴 시각 | 저장값의 소수부가 없다 |

---

### AU-13 에러 코드·예외 매핑·경로 선언 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | 없음 |
| 마이그레이션 | 없음 |
| 참조 | [../api-contract.md §2.4](../api-contract.md)·§2.5·§8.1·§8.4·§8.5, [../conventions.md §6.1](../conventions.md), [../security.md §1.1](../security.md)·§5.1, [../requirements/board.md §9.1](../requirements/board.md) |

**산출물**
- `global/error/ErrorCode.java` — `C008`·`C009`·`AU005`·`AU006`·`AU007`
- `global/error/GlobalExceptionHandler.java` — multipart 의 줄([../conventions.md §6.1](../conventions.md))
- `global/config/SecurityConfig.java` — api-contract §2.4 의 무인증 경로, CORS 가 노출하는 `Retry-After`
- 테스트: `ErrorCodeTest`, `GlobalExceptionHandlerTest`, `SecurityConfigTest` 확장

**완료 기준**
- [ ] 새 코드의 HTTP 상태·메시지가 api-contract §8.1·§8.4 와 같다
- [ ] multipart 예외가 conventions §6.1 의 표대로 매핑된다 — `MaxUploadSizeExceededException` 은 413 `C008`, 그 밖의 multipart 줄은 400 `C001`, 모두 `fieldErrors` 빈 배열·`warn`. 상위 타입만 두어 크기 위반이 `C001` 이 되는 일이 없다. **auth 는 multipart 를 받지 않지만 같은 핸들러를 갖는다**(api-contract §8.1 의 `C008` 문단)
- [ ] **핸들러를 넣기 전의 응답을 실제 서버에서 재서 보고에 적는다** — conventions §6.1 의 블록인용이 「핸들러를 넣기 전에 실제 서버에서 한 번 재서」 확인하라고 한다. board 의 측정으로 대신하면 그 근거를 적는다
- [ ] `C009` 의 매핑은 이 항목에 없다 — 제한기의 예외와 함께 AU-19 가 둔다(conventions §6.1 의 `C009` 문단)
- [ ] api-contract §2.4 의 무인증 경로를 **메서드와 함께 하나씩** `permitAll` 로 선언한다. `/api/v1/accounts/**` 같은 넓은 무인증 규칙이 없고 `/api/v1/accounts/me` 의 규칙이 그대로 앞에 있다
- [ ] `GET /api/v1/accounts` 가 인증 경로로 남는다 — `POST /api/v1/accounts` 의 `permitAll` 은 메서드를 붙인 그대로다(§2.4 의 마지막 문단)
- [ ] CORS 가 `Retry-After` 를 노출한다([../security.md §1.1](../security.md)). 429 는 AU-19 가 만들지만 CORS 설정은 이 항목이 끝낸다 — 기능 항목이 `SecurityConfig` 를 고치지 않게 한다
- [ ] **무인증 경로에 잘못된 토큰을 실은 요청의 응답을 테스트로 묶는다.** 이 계획이 정한 테스트다. 정본은 board 상세 조회에 대해서만 이것을 테스트 대상으로 적었다(2026-11-12 `D-20` 이 B-16 에 세웠다)([../requirements/board.md §9.1](../requirements/board.md) — board 몫은 [phase2-board.md](phase2-board.md)). auth·member 에 두는 이유는 화면이 무인증 요청에 저장된 토큰을 실을 때의 응답을 고정하려는 것이다(§5.2). 코드의 경계는 경로를 가리지 않는 [../api-contract.md §8.5](../api-contract.md)의 표다
  - 케이스는 **필터가 끊는 것**으로 한다(예: `b64token` 문법 위반, 문법은 맞지만 JWT 가 아닌 값, 서명 불일치, 만료). 기대는 같은 `Authorization` 을 인증 경로에 실었을 때와 같은 401 코드다 — 프레임워크 동작의 코드 읽기에서 온 기대이고, 이 테스트가 확인한다
  - **claim 계약 위반(예: 열거 밖 `role`)은 단언하지 않는다.** auth 는 그 검증을 `@CurrentAccount` 의 인자 해석에서 하므로(§8.5 의 블록인용) 그것을 쓰지 않는 무인증 경로에서의 결과를 정본이 정하지 않았다. 관측한 값을 보고에 적는다
  - **결과가 기대와 다르면 코드를 고치지 말고 보고한다** — auth·member 의 무인증 경로에 대해 정한 정본 문장이 없다
- [ ] 이 항목은 엔드포인트를 만들지 않는다

**검증** — `SecurityConfigTest`, `GlobalExceptionHandlerTest`, `ErrorCodeTest`, `./gradlew test`. 2026-11-12 코드 읽기로 auth·member 에 `JwtAuthenticationTest` 라는 클래스는 없다 — auth 의 무인증 경로 매개변수 테스트는 `SecurityConfigTest` 에 있고 그 곁에 더한다

| 케이스 | 기대 결과 |
| --- | --- |
| §2.4 의 무인증 경로, 토큰 없음 | 401 이 아니다 (기존 무인증 경로 매개변수 테스트에 더한다) |
| 같은 경로를 다른 메서드로(예: `GET /api/v1/accounts/password-reset`), 토큰 없음 | 401 `A001` — 무인증으로 열리지 않는다 |
| `GET /api/v1/accounts`, 토큰 없음 | 401 `A001` |
| `GET /api/v1/accounts/me`, 토큰 없음 | 401 `A001` — 새 규칙이 내 계정 경로를 열지 않는다 |
| 무인증 경로(예: `GET /api/v1/accounts/check-email`, `POST /api/v1/auth/login`)에 `Bearer not!a!token` | 401 `A001` |
| 같은 경로에 문법은 맞지만 JWT 가 아닌 값 | 401 `A002` |
| 같은 경로에 만료된 토큰 | 401 `A003` |
| `MaxUploadSizeExceededException` | 413 `C008`, `fieldErrors` 빈 배열, ERROR 로그가 아니다 |
| conventions §6.1 의 그 밖의 multipart 예외 | 400 `C001`, `fieldErrors` 빈 배열, ERROR 로그가 아니다 |
| 처리하지 않은 예외 | 500 `C005`, ERROR 로그 — 위 줄과 함께 양쪽을 단언한다(conventions §6.1) |
| CORS 설정값 | 노출 헤더에 `Retry-After` 가 있다 |

---

### AU-14 메일 발송 기반 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | 없음 |
| 마이그레이션 | 없음 |
| 참조 | [../tech-stack.md §3.2](../tech-stack.md)·§4.3·§4.7·§4.7.1, [../requirements/member.md §11.5](../requirements/member.md), [../security.md §12](../security.md), [../nfr.md §2](../nfr.md)·§3, [../conventions.md §1.1](../conventions.md), [../adr/0016](../adr/0016-mail-and-verification-gate.md) |

**산출물**
- `build.gradle` — `spring-boot-starter-mail`([../tech-stack.md §3.2](../tech-stack.md)). 그 밖의 의존성을 더하지 않는다
- `mail/` — 발송 인터페이스, SMTP 구현, 메일 설정 클래스와 기동 가드, 커밋 뒤 발송을 거는 장치
- `global/config/` — 발송 실행기(대기열 상한)
- `src/main/resources/application.yml`·`application-prod.yml`·`application-local.yml.example`, `src/test/resources/application-test.yml` — `application.yml` 은 메일 헬스 지표도 끈다(완료 기준)
- `README.md` — 「환경변수」 표에 tech-stack §4.3 이 auth 에 더한 메일 값, 「로컬 실행」 의 준비에 Mailpit([../tech-stack.md §4.7.1](../tech-stack.md))
- `src/test/java/com/example/auth/support/` — 메일을 메모리에 모으는 시험용 발송기
- 테스트: 가드·실행기·발송 실패 로그·운영 프로파일(`ProdProfileTest` 확장 포함)

**완료 기준**
- [ ] **기동 가드** — 아래 자리마다 기동이 실패하고, 실패마다 테스트가 있다. 근거는 자리마다 적는다
  - `spring.mail.host`·`port` 가 비었거나 미해석 `${…}` 리터럴이다 — [../tech-stack.md §4.7](../tech-stack.md)의 표
  - `spring.mail.username`·`password` 중 하나만 있다, 어느 프로파일이든 — 같은 표
  - 운영 프로파일에서 `username`·`password` 가 비었거나 미해석 리터럴이다 — 같은 표
  - `mail.from` 이 비었거나 미해석 리터럴이다 — 표 아래 문단(「정책값마다 기동 시점의 검사를 두고」)
  - `mail.frontend-base-url` 이 비었거나 미해석 리터럴이거나 `http`·`https` 의 절대 URL 이 아니다 — 같은 표
  - 시험용 발송기가 선택된 채 운영 프로파일로 뜬다 — 표 아래 문단과 [../security.md §12](../security.md)
- [ ] 가드는 값을 읽는 쪽의 동작에 기대지 않는다 — `@ConfigurationProperties` 는 미해석 리터럴을 통과시키고 빈 환경변수는 빈 문자열로 해석된다([../tech-stack.md §4.3](../tech-stack.md)의 측정)
- [ ] `application.yml` 에 정책값·비밀값의 기본값이 없다(§4.3)
- [ ] SMTP 타임아웃이 §4.7 의 값이다. 운영 프로파일이 암호화 연결을 요구한다(같은 표의 「암호화 연결」 줄)
- [ ] 발송은 요청 스레드 밖의 실행기에서 돈다. 대기열이 차면 그 작업을 버리고 WARN 을 남긴다(`mail.executor.queue-capacity`)
- [ ] 발송이 실패하면 다시 보내지 않고 **WARN 이상**으로 남긴다([../nfr.md §2](../nfr.md)). 로그에 토큰·링크·SMTP 비밀번호가 없다 — 계정 id·목적·예외의 종류만([../security.md §12](../security.md))
- [ ] `mail` 패키지가 `account` 를 부르지 않는다([../conventions.md §1.1](../conventions.md))
- [ ] 시험용 발송기는 `src/test` 에만 있다. 테스트 프로파일은 SMTP 에 접속하지 않는다
- [ ] **`/actuator/health` 가 SMTP 에 묶이지 않는다** — `management.health.mail.enabled: false`(이 계획의 결정, [../nfr.md §2](../nfr.md)의 SMTP 줄 「이미 인증된 계정의 로그인과 다른 모든 기능은 영향이 없다」). 스타터가 들어오고 가드 때문에 모든 프로파일이 `spring.mail.host` 를 채우면 Boot 의 메일 헬스 지표(`MailHealthContributorAutoConfiguration`)가 켜져 health 가 SMTP 접속을 따르고, SMTP 가 없는 테스트에서는 health 가 `UP` 이 아닐 것으로 본다(코드 읽기 추정 — AU-14 가 확인한다). 기존 `SecurityConfigTest` 의 health 200 `UP` 이 그대로 초록이다
- [ ] `application-local.yml.example` 이 Mailpit 의 값을 담는다(§4.7.1 — SMTP `localhost:1025`, 인증이 없어 `username`·`password` 빈 값). **Mailpit 의 버전을 고정해 같은 파일의 주석에 적는다**(§4.7.1 「버전은 작업 항목이 고정한다」 — 적는 자리는 이 계획이 정했다)
- [ ] `README.md`·`application-local.yml.example` 에 메일 설정이 있다 — `README.md` 는 「환경변수」 표의 메일 값과 Mailpit 의 준비다
- [ ] 완료 보고가 각자의 `application-local.yml` 에 옮길 줄을 적는다 — 이 항목 뒤 그 줄이 없으면 `local` 기동이 가드에 걸린다(§1.3)

**검증** — 가드 테스트(예: 속성을 바꿔 가며 컨텍스트를 띄운다), 실행기·발송 테스트, `ProdProfileTest`, `./gradlew test`

| 케이스 | 기대 결과 |
| --- | --- |
| 가드의 각 자리 | 기동 실패. 실패 메시지가 어느 키인지 말한다 — 이 계획의 선택이다. 다른 원인의 기동 실패와 가르려는 것이다 |
| `username`·`password` 가 둘 다 빈 값이고 운영 프로파일이 아니다 | 기동한다 (로컬 Mailpit 의 모양) |
| 대기열이 찬 상태의 발송 | 버려지고 WARN 한 줄 |
| SMTP 구현이 예외를 던진다 | 다시 보내지 않고 WARN 이상 한 줄. 그 줄에 토큰·링크가 없다 |
| 트랜잭션 안에서 건 발송이 되돌려진다 | 보내지 않는다 |
| 운영 프로파일의 메일 속성 | 암호화 연결 요구가 켜져 있다 |
| 메일 속성의 타임아웃 | §4.7 의 값이다 |

---

### AU-15 링크 토큰 발급 작업 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-12, AU-14 |
| 마이그레이션 | 없음 |
| 참조 | [../requirements/member.md §11.1](../requirements/member.md)·§11.2·§11.3·§11.5, [../domain-model.md §2.4](../domain-model.md), [../security.md §10.1](../security.md)·§12, [../api-contract.md §2.4](../api-contract.md), [../tech-stack.md §3.2](../tech-stack.md) |

**산출물**
- `account/` 아래 발급 작업(예: `account/service/AccountTokenIssuer.java`) — 자기 트랜잭션, 커밋 뒤 발송
- 계정 id·목적마다의 발송 상한(인스턴스 메모리, 주입한 `Clock`)
- 토큰 생성·해시, 메일 본문과 링크
- 테스트: 발급 작업·발송 상한

**완료 기준**
- [ ] 토큰은 `SecureRandom` 32바이트를 base64url(패딩 없음)로 쓴 문자열이고, 저장은 그 문자열(UTF-8)의 SHA-256 소문자 hex 뿐이다(member.md §11.1, domain-model §2.4)
- [ ] 수명은 목적마다 member.md §11.1 의 값이고 앱 시계로 정한다
- [ ] **발급 작업은 요청 스레드가 아니라 AU-14 의 실행기에서 돈다** — 재발송·재설정 요청의 스레드는 DB 일을 하지 않고 조회·발급·발송을 뒤의 작업에 넘긴다(member.md §11.3, security.md §12)
- [ ] 작업 안의 순서는 member.md §11.5 마지막 문단에 §11.2·§11.3 의 보낼 조건을 계정 찾기 뒤에 끼운 순서다 — 그 자리는 이 계획이 정했다. 자기 트랜잭션에서 계정 찾기 → 그 목적의 보낼 조건 → 계정 id·목적의 발송 상한 → 같은 계정·목적의 앞 토큰 지우기 → 새 토큰 넣기 → **그 트랜잭션이 커밋된 뒤** 발송
- [ ] 보낼 조건이 member.md §11.2(재발송)·§11.3(재설정)의 표와 같다 — 조건이 안 되면 토큰도 메일도 없다
- [ ] 이메일로 시작한 발급은 **계정에 저장된 주소로** 보낸다 — 요청의 표기로 보내지 않는다(§11.3)
- [ ] 발송 상한(값은 member.md §11.5)을 넘으면 발급·발송하지 않고 WARN 을 남긴다. 상한은 앞 토큰을 지우기 전에 본다
- [ ] 링크가 `{mail.frontend-base-url}/verify-email#token=…`·`/reset-password#token=…` 이다(§11.5). 기준 주소는 설정에서만 오고 요청의 `Host`·`Origin` 을 읽지 않는다(security.md §12). 요청 진입점은 AU-16·AU-17 이 만들므로 그 테스트가 확인한다
- [ ] 인증 메일이 「가입하지 않았다면 이 메일을 무시하세요」 를 적는다(member.md §11.2). 본문의 형식은 구현이 정하되 [../tech-stack.md §3.2](../tech-stack.md) 밖의 의존성(예: 템플릿 엔진)을 더하지 않는다
- [ ] 작업이 실패하면 WARN 이상으로 남긴다 — 실행기 안의 예외가 조용히 사라지지 않는다([../AGENTS.md](../AGENTS.md) 불변식 9). 로그 규칙은 AU-14 와 같다
- [ ] 가입이 넘기는 발급(AU-16 이 잇는다)도 같은 작업을 지난다

**검증** — 발급 작업 테스트(시험용 발송기, 시계를 움직인다), `./gradlew test`

| 케이스 | 기대 결과 |
| --- | --- |
| 재발송 — 활성·미인증 | 토큰 1행, 메일 1통. 링크의 토큰을 해시하면 저장값이다 |
| 재발송 — 없음·탈퇴·이미 인증 | 행도 메일도 없다 |
| 재설정 — 활성(인증·미인증 모두) | 메일이 간다 |
| 재설정 — 없음·탈퇴 | 행도 메일도 없다 |
| 요청 문자열과 저장된 주소가 다른 경우(예: 대소문자) | 받는 주소가 저장된 주소다. H2 는 대소문자를 구분해 비교하므로(member.md §12.2) 그 경우는 계정 조회를 대역으로 만든다 |
| 같은 계정·목적의 둘째 발급 | 앞 토큰이 지워지고 새 토큰만 남는다. 다른 목적의 토큰은 남는다 |
| 발송 상한을 넘는 요청 | 새 행·메일이 없고 WARN. 상한 안에서 마지막으로 보낸 링크의 토큰 행이 남아 있다(그 링크의 토큰을 해시해 읽힌다). 시계를 그 시간 너머로 움직이면 다시 보낸다. 목적마다 따로 센다 |
| 발급 트랜잭션이 되돌려진다 | 메일이 없다 |

---

### AU-16 이메일 인증과 미인증 로그인 차단 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-13, AU-15 |
| 공유 파일 | `AccountController`·`AccountService` (AU-17·AU-19·AU-20 도 고친다), `AuthService` (AU-18 도 고친다) |
| 마이그레이션 | 없음 |
| 참조 | [../requirements/member.md §4](../requirements/member.md)·§11.2·§12.1·§3 규칙 11, [../api-contract.md §2.1](../api-contract.md)·§2.2·§2.4·§9.10, [../security.md §12](../security.md), [../adr/0016](../adr/0016-mail-and-verification-gate.md), [../process/review-policy.md §4.1](../process/review-policy.md) |

**산출물**
- `account/dto/EmailRequest.java` — 재발송·재설정 요청의 `{email}`(AU-17 이 같이 쓴다)
- `account/dto/TokenConfirmRequest.java` — `{token}`
- `AccountController`·`AccountService` 확장 — 가입 뒤 발급, 재발송, 확인
- `auth/service/AuthService.java` — 미인증의 맞는 비밀번호에 403 `AU006`
- 테스트: `AccountControllerTest`, `AccountServiceTest`, `AuthServiceTest`, `AuthControllerTest` 확장

**완료 기준**
- [ ] 가입(`POST /api/v1/accounts`)의 요청·응답은 그대로다(201, 중복이면 409 `AU002`). 계정 INSERT 가 **커밋된 뒤** 인증 메일 발급을 넘긴다 — 가입이 되돌려지면 메일이 없다(member.md §11.2)
- [ ] 재발송의 `email` 은 가입과 같은 규칙이다(위반은 400 `C001`, `fieldErrors` 에 `email`). 그 밖에는 **언제나 202** 와 api-contract §2.4 의 본문이다. 요청 스레드는 DB 일을 하지 않는다(security.md §12)
- [ ] 확인은 **한 트랜잭션**이다 — member.md §11.2 의 순서(사용 처리, 0행이면 400 `AU007` → 탈퇴 계정이면 되돌리고 400 `AU007` → 미인증이면 지금 시각으로 채우고 이미 인증됐으면 그대로) → 204, 본문 없음
- [ ] **트랜잭션 경계를 관측한다** — 한 번의 확인에 커밋이 한 번이다([../process/review-policy.md §4.1](../process/review-policy.md))
- [ ] `token` 에 `@NotBlank` 만 건다 — 형식 검증을 걸지 않는다(api-contract §2.4)
- [ ] 확인은 토큰(Access·Refresh)을 주지 않는다
- [ ] 로그인 — 비밀번호가 맞고 미인증이면 403 `AU006`. **비밀번호가 틀리면 미인증이어도 401 `AU003` 이다** — `AU006` 은 비밀번호가 맞은 뒤에만 나온다(member.md §12.1 의 5). 잠금과 카운터는 AU-18 이 더한다
- [ ] `V6` 이 채운 계정(1차에 만든 계정·ADMIN seed)은 그대로 로그인한다
- [ ] 완료 보고가 화면의 가입 흐름과 병합 시점을 맞춰야 한다는 것을 적는다(§1.3)

**검증** — 위 테스트 클래스(시험용 발송기, 시계를 움직인다), `./gradlew test`

| 케이스 | 기대 결과 |
| --- | --- |
| 가입 | 201, 인증 메일 1통 |
| 가입을 바깥 트랜잭션 안에서 한다 | 트랜잭션이 열린 동안 실행기(대역)가 받은 발급 작업 0건. 되돌리면 끝까지 0건, 커밋하면 그때 1건 |
| 재발송 — 없음·탈퇴·인증됨·미인증 | 어느 경우든 202·같은 본문. 메일은 미인증일 때만 |
| 가입·재발송 — 요청에 다른 `Host` | 메일 링크의 기준 주소가 그대로 설정값이다 |
| 재발송 — 형식 위반 | 400 `C001`, `fieldErrors` 에 `email` |
| 확인 — 정상 | 204, `email_verified_at` 이 채워진다 |
| 확인 — 같은 토큰 두 번 | 둘째가 400 `AU007` |
| 확인 — 수명 너머(시계) | 400 `AU007` |
| 확인 — 재설정 목적의 토큰 | 400 `AU007` |
| 확인 — 탈퇴한 계정 | 400 `AU007`. `email_verified_at` 그대로, 토큰의 `used_at` 도 되돌려진다 |
| 확인 — 이미 인증된 계정 | 204, 처음 시각이 남는다 |
| 확인 — `token` 누락·빈 값 | 400 `C001`, `fieldErrors` 에 `token` |
| 확인 — 길이·문자가 틀린 `token` | 400 `AU007` — `C001` 이 아니다 |
| 한 번의 확인 | 커밋이 정확히 한 번(`isNewTransaction` 인 `commit` 만 센다) |
| 미인증 계정 — 맞는 비밀번호로 로그인 | 403 `AU006`, 토큰 없음 |
| 미인증 계정 — 틀린 비밀번호로 로그인 | 401 `AU003` |
| 인증한 뒤 로그인 | 200 |
| ADMIN seed 로 로그인 | 200 |

---

### AU-17 비밀번호 재설정 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-16 (요청 DTO 와 컨트롤러를 잇는다. AU-13·AU-15 는 그 안에 있다) |
| 공유 파일 | `AccountController`·`AccountService` |
| 마이그레이션 | 없음 |
| 참조 | [../requirements/member.md §11.3](../requirements/member.md)·§11.4·§12.2, [../api-contract.md §2.4](../api-contract.md)·§9.11, [../security.md §5.3](../security.md)·§12, [../domain-model.md §2.5](../domain-model.md), [../process/review-policy.md §4.1](../process/review-policy.md) |

**산출물**
- `account/dto/PasswordResetConfirmRequest.java` — `{token, newPassword}`
- `AccountController`·`AccountService` 확장 — 재설정 요청·확인
- 테스트: `AccountControllerTest`, `AccountServiceTest` 확장

**완료 기준**
- [ ] 재설정 요청은 재발송과 같은 모양이다 — 형식 위반만 400 `C001` 이고 그 밖에는 언제나 202. 요청 스레드는 DB 일을 하지 않는다(member.md §11.3, security.md §12)
- [ ] 요청만으로는 세션·잠금·비밀번호가 바뀌지 않는다
- [ ] 확인의 `newPassword` 는 비밀번호 규칙이고 위반은 400 `C001`(`fieldErrors` 에 `newPassword`) — **토큰을 쓰기 전에** 거른다
- [ ] `token` 은 AU-16 과 같이 `@NotBlank` 만 건다 — 형식 검증을 걸지 않는다(api-contract §2.4)
- [ ] 확인은 **한 로컬 트랜잭션**이고 member.md §11.4 의 순서다(사용 처리 → 탈퇴 검사 → 비밀번호 → 그 계정의 `refresh_token` 삭제 → 그 계정 이메일의 잠금 해제 → 미인증이면 인증) → 204
- [ ] 잠금 해제는 AU-12 의 키 변환과 해제 문장을 쓴다. 키는 계정에 저장된 이메일에서 만든다
- [ ] 확인은 토큰을 주지 않는다. 이미 발급된 Access Token 은 만료까지 통과한다 — 막는 코드를 두지 않는다(security.md §5.3)
- [ ] **트랜잭션 경계를 관측한다** — 한 번의 확인에 커밋이 한 번이고, 중간 실패가 §11.4 의 변경을 모두 되돌린다. 변경마다 반증 가능한 단언이다([../process/review-policy.md §4.1](../process/review-policy.md))

**검증** — 위 테스트 클래스(시험용 발송기, 시계를 움직인다), `./gradlew test`

| 케이스 | 기대 결과 |
| --- | --- |
| 요청 — 없음·탈퇴·미인증·인증 | 어느 경우든 202·같은 본문. 메일은 활성 계정일 때만 |
| 요청 — 요청에 다른 `Host` | 메일 링크의 기준 주소가 그대로 설정값이다 |
| 확인 — 정상 | 204. 새 비밀번호로 로그인 200, 옛 비밀번호는 401 `AU003` |
| 확인 뒤 옛 Refresh Token 으로 재발급 | 401 `A002` — 세션 없음([../api-contract.md §2.1](../api-contract.md)) |
| 확인 뒤 옛 Access Token 으로 보호 경로 | 통과한다(만료 전) |
| 잠긴 행(`locked_until` 이 미래)을 심고 확인 | 그 행의 `failed_count` 가 0, `locked_until` 이 NULL |
| 미인증 계정에서 확인 | `email_verified_at` 이 채워진다 |
| `newPassword` 규칙 위반 | 400 `C001`. 같은 토큰으로 다시 확인하면 204 다 — 소모되지 않았다 |
| 수명 너머(시계)·이미 씀·인증 목적의 토큰 | 400 `AU007` |
| `token` 누락·빈 값 | 400 `C001`, `fieldErrors` 에 `token` |
| 길이·문자가 틀린 `token` | 400 `AU007` — `C001` 이 아니다 |
| 탈퇴한 계정 | 400 `AU007`, 비밀번호 그대로 |
| 중간 실패 | 비밀번호·토큰 사용·Refresh Token·잠금·인증이 모두 그대로다 |
| 한 번의 확인 | 커밋이 정확히 한 번 |

---

### AU-18 로그인 잠금 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-12, AU-13, AU-16 (`AuthService` 의 로그인을 AU-16 다음에 고친다) |
| 공유 파일 | `AuthService`, `LoginAttemptRepository`, `AuthControllerTest` (AU-19 도 고친다) |
| 마이그레이션 | 없음 |
| 참조 | [../requirements/member.md §12](../requirements/member.md), [../domain-model.md §2.5](../domain-model.md), [../api-contract.md §2.1](../api-contract.md)·§8.4, [../security.md §4.1](../security.md)·§11, [../conventions.md §1.1](../conventions.md) |

**산출물**
- 카운터 빈 — 로그인 서비스와 **다른 빈**(예: `auth/service/LoginAttemptService.java`), `REQUIRES_NEW`
- `LoginAttemptRepository` 확장 — 증가·잠금 문장
- `auth/service/AuthService.java` — member.md §12.1 의 판정 순서
- 테스트: `AuthServiceTest`, `AuthControllerTest`, `LoginAttemptRepositoryTest` 확장, 카운터 빈의 테스트

**완료 기준**
- [ ] 로그인의 판정이 member.md §12.1 의 순서다 — 빈 값·100자 초과는 계정 조회 없이 `AU003`·세지 않는다 → 계정 조회 + BCrypt 정확히 한 번(없거나 탈퇴면 더미 해시) → 잠겨 있으면 `AU005`(비밀번호와 무관, 세지 않는다) → 실패를 세고, 그 실패로 잠기거나 그 사이 잠겼으면 `AU005` 아니면 `AU003` → 미인증의 맞는 비밀번호는 카운터를 0 으로 하고 `AU006` → 성공은 카운터를 0 으로
- [ ] 키는 AU-12 의 변환이다(ASCII 대문자만)
- [ ] 증가가 domain-model §2.5 의 순서와 원자성을 지킨다 — 조건부 UPDATE(없으면 INSERT), 증가가 잡은 행 락 아래·같은 트랜잭션의 5회 판정, 읽고 비교한 뒤 쓰지 않는다. `INSERT IGNORE`·`ON DUPLICATE KEY UPDATE` 로 판정하지 않는다
- [ ] 다시 하는 자리(UNIQUE 충돌, 0행인데 잠기지 않은 행)는 **새 트랜잭션**에서 한 번 더 하고, 그래도 실패하면 응답은 `AU003` 그대로·**세지 못한 실패를 WARN 으로** 남긴다
- [ ] 카운트와 0 으로 되돌리기는 로그인 트랜잭션과 다른 트랜잭션에서 커밋된다 — 실패 응답·`AU006` 이 로그인 트랜잭션을 되돌려도 남는다. `REQUIRES_NEW` 는 로그인 서비스와 다른 빈에 있다(conventions §1.1)
- [ ] 잠금 판정은 최신 커밋 값을 읽는다 — 로그인 트랜잭션이 먼저 연 스냅샷으로 읽지 않는다(member.md §12.2)
- [ ] 판정 시각은 주입한 `Clock` 이다. 마지막 실패에서 24시간이 지난 실패는 1부터 다시 센다. 잠금은 member.md §12 의 시간 뒤 풀리고, 잠긴 동안의 시도는 잠금을 늘리지 않는다
- [ ] `PATCH /me/password`·`DELETE /me` 의 `AU004` 는 세지 않는다
- [ ] 잠긴 경로의 응답이 비밀번호와 무관하게 같다(상태·본문)

**검증** — 위 테스트 클래스(`support/MutableClock`), `./gradlew test`

| 케이스 | 기대 결과 |
| --- | --- |
| 같은 이메일로 틀린 비밀번호를 연속으로 | 넷째까지는 `AU003`, 다섯째가 `AU005`(횟수는 member.md §12) |
| 잠긴 동안 맞는 비밀번호 | 401 `AU005` — 틀린 비밀번호의 응답과 상태·본문이 같다 |
| 잠긴 동안의 시도 | 카운터·`locked_until` 이 그대로다 |
| 잠금 시각 너머(시계) | 맞는 비밀번호로 200 |
| 없는 이메일로 연속 실패 | 다섯째가 `AU005` |
| ASCII 대소문자만 다른 이메일로 번갈아 실패 | 한 키로 센다. 그 밖의 표기는 §5.1 |
| 마지막 실패 + 24시간 뒤의 실패 | 1부터 다시 센다 |
| 실패를 쌓아 둔 뒤 성공 | 카운터 0 이 커밋되어 있다 |
| 실패를 쌓아 둔 뒤 미인증의 맞는 비밀번호 | 403 `AU006`, 카운터 0 이 커밋되어 있다 |
| 실패 응답 뒤의 `login_attempt` | 행이 커밋되어 있다 — 같은 트랜잭션으로 셌다면 빨개지는 단언이다 |
| 이메일 100자 초과 | 401 `AU003`, 행이 생기지 않는다 |
| 이메일 또는 비밀번호가 빈 값(있는 이메일 + 빈 비밀번호 포함) | 401 `AU003`, `login_attempt` 행이 생기지 않는다 |
| 잠긴 경로의 BCrypt 호출 | 정확히 한 번 |
| 비밀번호 변경의 `AU004` | 카운터가 그대로 |
| 판정(member.md §12.1 의 3)과 증가 사이에 잠금이 커밋된다(대역) | 401 `AU005`, 카운터·`locked_until` 그대로 |
| 증가 UPDATE 가 0행이고 잠기지 않은 행이 있다(대역 — domain-model §2.5 의 갱신 문장) | 새 트랜잭션에서 한 번 더 센다 |
| 다시 하기 — UNIQUE 충돌을 만든다(예: 대역) | 한 번 더 한다. 또 실패하면 `AU003` 과 WARN 한 줄 |

---

### AU-19 요청 수 제한 — auth [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-13, AU-16, AU-17 (이메일 키를 그 둘의 컨트롤러 안에서 센다) |
| 공유 파일 | `AccountController`, `GlobalExceptionHandler`, `application.yml`·`application-local.yml.example`·`application-test.yml`·`README.md`, `AuthControllerTest` (AU-18 도 고친다) |
| 마이그레이션 | 없음 |
| 참조 | [../security.md §10](../security.md)·§10.1·§1.1, [../tech-stack.md §4.6](../tech-stack.md)·§3.2, [../conventions.md §1.1](../conventions.md)·§6.1·§7.2, [../api-contract.md §8.1](../api-contract.md)·§9.13, [../adr/0015](../adr/0015-rate-limit-without-gateway.md) |

**산출물**
- `global/ratelimit/` — 제한기(고정 창·버킷 카운터·버킷을 고르는 HMAC), 규칙 설정, IP 키를 세는 인터셉터, 제한 초과 예외
- `global/config/WebConfig.java` — 인터셉터 등록
- `global/error/GlobalExceptionHandler.java` — `C009` 매핑(`Retry-After`)
- `AccountController` — 재설정 요청·재발송의 이메일 키
- `application.yml` — `server.forward-headers-strategy: none`, 규칙의 한도·창, 규칙마다의 버킷 수
- `application-local.yml.example` — 한도를 크게 덮는다
- `README.md` — 로컬 템플릿이 한도를 덮는다는 것과 옮길 줄
- `src/test/resources/application-test.yml` — 테스트 프로파일의 한도. 2026-11-12 코드 읽기로 `AccountControllerTest`·`AuthControllerTest` 는 `@SpringBootTest`·MockMvc 라 캐시된 컨텍스트가 제한기 하나를 나눠 쓰고 요청 주소가 하나다
- 테스트: 제한기 단위 테스트, 인터셉터 테스트, 컨트롤러 테스트(`AccountControllerTest`·`AuthControllerTest` 확장 — 로그인·재발급은 `AuthController` 의 경로다), `GlobalExceptionHandlerTest` 확장

**완료 기준**
- [ ] 대상·키·한도가 security.md §10 의 표에서 auth 의 줄이다. 두 확인(`…/confirm`)과 재발급은 제한하지 않는다
- [ ] 방식이 security.md §10 의 「항목 / 정한 것」 표다 — 시계 경계에 맞춘 고정 창, 주입한 `Clock`, 규칙마다 고정 크기 카운터 배열, **기동마다 새로 만든 비밀**의 HMAC-SHA256 으로 버킷 선택(비밀은 설정·로그에 없다), 창 경계에서 비우기, 저장하지 않는다
- [ ] IP 키는 `request.getRemoteAddr()` 만이다 — IPv4 는 그대로, IPv6 는 /64, IPv4 사상 주소는 IPv4. `X-Forwarded-For`·`X-Real-IP` 를 읽지 않는다. `server.forward-headers-strategy: none`
- [ ] IP 키는 CORS 처리 뒤·핸들러 앞에서 세고 preflight(`OPTIONS`)를 세지 않는다. 그 경로에 닿은 요청은 성공·실패를 가르지 않고 센다
- [ ] 이메일 키는 본문 검증 뒤 컨트롤러 안에서 센다 — `Locale.ROOT` 소문자다. **AU-12 의 잠금 키(ASCII 만)와 다른 변환이다 — 섞어 쓰지 않는다.** 검증에 실패한 요청은 이메일 키로 세지 않는다(IP 키로는 센다). 이메일 키를 넘으면 발급 작업을 넘기지 않는다
- [ ] 넘으면 429 `C009` + `Retry-After`(창이 끝날 때까지 남은 초, 올림, 최소 1), `fieldErrors` 빈 배열, 로그 `warn`
- [ ] 429 응답에 CORS 헤더가 실리고 `Retry-After` 가 노출된다(AU-13 의 노출 설정)
- [ ] 의존성을 더하지 않는다(tech-stack §3.2)
- [ ] **기동 가드** — 규칙의 설정이 빠졌거나 한도·창·버킷 수가 양수가 아니면 기동이 실패한다. 제한이 조용히 꺼지지 않게 한다([../AGENTS.md](../AGENTS.md) 불변식 9). tech-stack §4.6 은 이 값들을 정본 값으로 분류하므로 정책값처럼 「기본값 없음」 을 요구하지 않는다 — 이 가드는 빠짐과 잘못된 값만 막는다
- [ ] `application-local.yml.example` 이 한도를 크게 덮는다 — 값은 템플릿이 정하고 기준은 「운영 한도보다 e2e 의 요청 수가 넉넉히 들어가게」 다(tech-stack §4.6). 완료 보고와 `README.md` 가 각자의 `application-local.yml` 에 옮길 줄을 적는다(§1.3)
- [ ] 기존 테스트가 그대로 초록이다 — 테스트 프로파일의 한도는 위 `application-test.yml` 이 갖는다

**검증** — 위 테스트(`support/MutableClock`), `./gradlew test`. MockMvc 는 Tomcat 의 주소 처리를 거치지 않는다 — 실서버의 동작은 §5.1

| 케이스 | 기대 결과 |
| --- | --- |
| `check-email` 을 한도까지, 한 번 더 | 한도까지 통과, 다음이 429 `C009` + `Retry-After` |
| 시계를 창 경계 너머로 | 다시 통과 |
| `Retry-After` 의 값 | 창 끝까지 남은 초의 올림, 최소 1 |
| 버킷 수 1 의 제한기 — 다른 키 둘 | 한 키가 한도를 채우면 다른 키도 429 다 |
| 요청마다 다른 `X-Forwarded-For` | 같은 키로 센다 |
| 같은 IPv6 /64 의 두 주소 | 한 키 |
| `::ffff:a.b.c.d` | IPv4 `a.b.c.d` 와 같은 키 |
| preflight | 세지 않는다 |
| 재설정 요청 — 같은 이메일, 다른 IP | 이메일 키의 한도에서 429 |
| 재설정 요청·재발송 — 비ASCII 대문자를 포함한 대소문자 변형(예: 로컬 파트의 `Ä`/`ä` — 비ASCII 로컬은 검증을 지난다, [../requirements/member.md §2.0](../requirements/member.md)), 다른 IP | 한 이메일 키로 센다(`Locale.ROOT`, [../security.md §10](../security.md)) |
| 재설정 요청 — 형식 위반 | 400 `C001`, 이메일 키로 세지 않는다 |
| 이메일 키 초과 | 발급 작업이 넘어가지 않는다 |
| 두 확인·재발급 | 몇 번이든 429 가 아니다 |
| 제한하지 않는 요청(예: `GET /api/v1/accounts/me`, AU-20 의 `GET /api/v1/accounts`) | 몇 번이든 429 가 아니다 — 규칙은 메서드와 경로로 고른다. `GET /api/v1/accounts` 는 AU-20 이 만든다 — 그 전이면 메서드로 고르는 것을 제한기 단위 테스트로 본다 |
| 허용 오리진에서 온 요청의 429 | `Access-Control-Allow-Origin` 이 있고 `Retry-After` 가 노출된다 |
| 규칙 설정이 빠졌다 | 기동 실패 |

---

### AU-20 계정 목록 (ADMIN) [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-12, AU-13 |
| 공유 파일 | `AccountController`·`AccountService` |
| 마이그레이션 | 없음 |
| 참조 | [../requirements/member.md §13](../requirements/member.md), [../api-contract.md §2.5](../api-contract.md)·§7.1·§9.12, [../security.md §5.1](../security.md)·§5.2, [../conventions.md §1.1](../conventions.md), [../domain-model.md §2.5](../domain-model.md) |

**산출물**
- `global/config/QuerydslConfig.java` — auth 의 첫 QueryDSL 사용이다(api-contract §2.5). 의존성은 `build.gradle` 에 이미 있다(2026-11-12 코드 읽기)
- `account/repository/` — 조건·정렬·페이징을 조합하는 조회(QueryDSL)
- `account/dto/` — 목록 원소와 조건
- `AccountController`·`AccountService` 확장
- 테스트: 컨트롤러·서비스·저장소 테스트

**완료 기준**
- [ ] 파라미터·기본값·정렬·필터가 api-contract §2.5 의 표다 — `size` 초과는 최대값으로 절삭, `email` 이 공백만이면 없음, 부분 일치
- [ ] 응답이 §7.1 의 페이징 모양이고 원소의 키가 §2.5 의 표다. 비밀번호·인증 시각·잠금 시각을 싣지 않는다
- [ ] `locked` 는 그 계정 이메일의 잠금이 지금 걸려 있을 때 `true` 다 — 키는 AU-12 의 변환, 시각은 주입한 `Clock`
- [ ] ADMIN 판정은 Service 계층에서 `LoginAccount.role` 이 `ADMIN` 과 **같을 때만 허용**하는 모양이다. 아니면 403 `A004`. `GrantedAuthority`·`hasRole` 로 판정하지 않는다(security.md §5.1)
- [ ] 검증 실패가 §2.5 의 표대로다 — `page` 음수·`size` 1 미만·`email` 100자 초과는 400 `C001`(`fieldErrors` 1건), `sort`·`role`·`deleted` 의 틀린 값은 400 `C002`
- [ ] 정렬 키의 끝에 `id` 가 있다

**검증** — 위 테스트, `./gradlew test`

| 케이스 | 기대 결과 |
| --- | --- |
| ADMIN 토큰, 파라미터 없음 | 200, §2.5 의 기본 `size`·`latest`(같은 `created_at` 은 `id DESC`) |
| `sort=email` | `email ASC, id ASC` |
| `email=exam` | 그 문자열을 포함하는 계정만 |
| `role=ADMIN`·`deleted=true` | 그 조건의 계정만 |
| 최대보다 큰 `size` | 응답의 `size` 가 최대값이다 |
| `page=-1`·`size=0`·`email` 101자 | 400 `C001`, `fieldErrors` 1건 |
| `sort=bogus`·`role=bogus`·`deleted=maybe` | 400 `C002` |
| USER 토큰 | 403 `A004` |
| 토큰 없음 | 401 `A001` |
| 잠긴 이메일의 계정 | `locked: true`. 시계를 잠금 너머로 → `false` |
| 미인증 계정 | `emailVerified: false` |
| 원소의 키 | §2.5 의 표 밖의 키가 없다(예: `password`) |

---

### AU-21 만료 토큰·오래된 잠금 행 정리 [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-auth` |
| 의존 | AU-12, AU-16, AU-18 (완료 기준의 같은 결과 비교가 확인의 `AU007` 과 실패의 재계수를 쓴다) |
| 공유 파일 | `application.yml`, `LoginAttemptRepository` |
| 마이그레이션 | 없음 |
| 참조 | [../domain-model.md §2.4](../domain-model.md)·§2.5, [../tech-stack.md §4.7](../tech-stack.md), [../conventions.md §1.1](../conventions.md), [../nfr.md §4](../nfr.md) |

**산출물**
- `global/config/` — 스케줄링 활성화(auth 의 첫 스케줄러다 — tech-stack §4.7)
- 정리 작업 — 두 저장소의 삭제 문장을 부른다
- `AccountTokenRepository`·`LoginAttemptRepository` — 삭제 문장
- `application.yml` — `account-cleanup.interval`
- 테스트: 정리 작업·삭제 문장

**완료 기준**
- [ ] 만료된 `account_token` 과 오래된 `login_attempt` 를 domain-model §2.4·§2.5 의 기준으로 지운다
- [ ] 판정 시각은 주입한 `Clock` 이다
- [ ] 주기는 `account-cleanup.interval`(편의값, tech-stack §4.7)이다
- [ ] 지운 행과 남은 행의 판정 결과가 같다 — 지운 토큰과 만료된 토큰의 확인이 둘 다 `AU007`, 지운 잠금 행과 24시간 지난 행의 다음 실패가 둘 다 1부터다(§2.4·§2.5)
- [ ] 여러 인스턴스가 각자 돌아도 결과가 같다 — 실행 위치를 고르는 장치를 두지 않는다(tech-stack §4.7)

**검증** — 위 테스트(`support/MutableClock`), `./gradlew test`

| 케이스 | 기대 결과 |
| --- | --- |
| 만료 전·만료 뒤의 토큰 | 뒤만 지워진다 |
| 24시간 안·밖의 잠금 행 | 밖만 지워진다 |
| 지금 잠겨 있는 행 | 남는다 |
| 지운 토큰으로 확인 | 400 `AU007`(만료 토큰과 같다) |
| 지운 잠금 행의 이메일로 실패 | 카운터 1(24시간 지난 행과 같다) |

## 4. member-service 작업 항목

### M-14 에러 코드·예외 매핑·경로 선언 [기반]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | 없음 |
| 마이그레이션 | 없음 — member 는 마이그레이션이 없다(§2) |
| 참조 | [../api-contract.md §3.2](../api-contract.md)·§8.1·§8.5, [../conventions.md §6.1](../conventions.md), [../security.md §1.1](../security.md), [../requirements/board.md §9.1](../requirements/board.md) |

**산출물**
- `global/error/ErrorCode.java` — `C008`·`C009`
- `global/error/GlobalExceptionHandler.java` — multipart 의 줄(conventions §6.1)
- `global/config/SecurityConfig.java` — `GET /api/v1/members` 의 인증 경로 선언, CORS 가 노출하는 `Retry-After`
- 테스트: `ErrorCodeTest`, `GlobalExceptionHandlerTest`, `SecurityConfigTest` 확장

**완료 기준**
- [ ] 새 코드가 api-contract §8.1 과 같다. member 접두어(`M0xx`)에 새 코드가 없다
- [ ] multipart 예외의 매핑이 AU-13 의 같은 줄과 같다 — member 도 multipart 를 받지 않지만 같은 핸들러를 갖는다(api-contract §8.1). 핸들러를 넣기 전의 응답을 재서 보고에 적는 것도 AU-13 과 같다(board 의 측정으로 대신하면 그 근거를 적는다)
- [ ] `C009` 의 매핑은 M-15 가 둔다
- [ ] `GET /api/v1/members` 를 인증 경로로 **선언한다**(api-contract §3.2). `GET /api/v1/members/{accountId}` 의 `permitAll` 은 그대로이고 이 경로를 열지 않는다
- [ ] CORS 가 `Retry-After` 를 노출한다(security.md §1.1)
- [ ] **무인증 경로에 잘못된 토큰을 실은 요청의 응답을 테스트로 묶는다** — AU-13 처럼 이 계획이 정한 테스트이고(정본은 board 상세 조회에 대해서만 이것을 테스트 대상으로 적었다), 이유·케이스·다를 때의 처리는 AU-13 의 같은 기준과 같다. member 의 `SecurityConfigTest` 에는 토큰 변형마다의 401 테스트가 있다(2026-11-12 코드 읽기, 표시 이름) — 그 변형 중 필터가 끊는 것을 무인증 경로(예: `GET /api/v1/members/{accountId}`, `GET /api/v1/members/check-nickname`)에 싣는다. member 는 claim 계약을 디코더에서 집행하므로(api-contract §8.5 의 블록인용) 계약 위반 토큰의 결과가 auth 와 다를 수 있다 — 관측한 값을 보고에 적고 단언하지 않는다

**검증** — 위 테스트, `./gradlew test`

| 케이스 | 기대 결과 |
| --- | --- |
| `GET /api/v1/members`, 토큰 없음 | 401 `A001` |
| `GET /api/v1/members/{accountId}`, 토큰 없음 | 401 이 아니다 |
| 무인증 경로에 `b64token` 문법 위반·JWT 가 아닌 값·만료 토큰 | 인증 경로와 같은 401 코드(`A001`·`A002`·`A003`) |
| `MaxUploadSizeExceededException` | 413 `C008`, `fieldErrors` 빈 배열, ERROR 로그가 아니다(기존 로그 수준 테스트에 더한다 — 2026-11-12 코드 읽기) |
| conventions §6.1 의 그 밖의 multipart 예외 | 400 `C001`, `fieldErrors` 빈 배열, ERROR 로그가 아니다 |
| CORS 설정값 | 노출 헤더에 `Retry-After` 가 있다 |

---

### M-15 요청 수 제한 — member [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-14 |
| 공유 파일 | `GlobalExceptionHandler` (M-14), `application.yml`·`application-local.yml.example`, `MemberControllerTest` (M-16) |
| 마이그레이션 | 없음 |
| 참조 | [../security.md §10](../security.md)·§10.1, [../tech-stack.md §4.6](../tech-stack.md), [../conventions.md §1.2](../conventions.md)·§6.1·§7.2, [../api-contract.md §8.1](../api-contract.md)·§9.13, [../adr/0015](../adr/0015-rate-limit-without-gateway.md) |

**산출물**
- `global/config/ClockConfig.java` — member 의 첫 `Clock` 빈이다(conventions §1.2. 2026-11-12 코드 읽기로 member 에 `Clock` 이 없다)
- `global/ratelimit/` — 제한기·규칙 설정·인터셉터·예외. auth 와 같은 동작을 member 가 따로 쓴다(conventions §7.2)
- `global/config/WebConfig.java`, `global/error/GlobalExceptionHandler.java` — 인터셉터 등록, `C009` 매핑
- `application.yml` — `server.forward-headers-strategy: none`, `check-nickname` 규칙, 버킷 수
- `application-local.yml.example` — 한도를 크게 덮는다
- `README.md` — 로컬 템플릿이 한도를 덮는다는 것과 옮길 줄
- `src/test/resources/application-test.yml` — 테스트 프로파일의 한도. 2026-11-12 코드 읽기로 `MemberControllerTest` 도 `@SpringBootTest`·MockMvc 라 AU-19 와 같은 이유다
- `src/test/java/com/example/member/support/` — 움직일 수 있는 시계(auth 의 `MutableClock` 과 같은 쓰임)
- 테스트: 제한기 단위 테스트, 인터셉터 테스트, 컨트롤러 테스트(`MemberControllerTest` 확장 — `check-nickname` 의 테스트가 그 파일에 있다), `GlobalExceptionHandlerTest` 확장

**완료 기준**
- [ ] 대상은 security.md §10 의 member 줄이다
- [ ] 방식·IP 키·세는 자리·응답·`Retry-After`·버킷 카운터가 AU-19 의 완료 기준과 같다 — 같아야 하는 것은 동작이고 정본은 security.md §10 이다(conventions §7.2). 코드를 auth 에서 옮겨 오더라도 공유 모듈을 만들지 않는다
- [ ] 기동 가드가 AU-19 의 것과 같다 — 근거는 AU-19 와 같은 [../AGENTS.md](../AGENTS.md) 불변식 9 다
- [ ] `application-local.yml.example` 이 한도를 크게 덮는다 — 기준은 tech-stack §4.6 이다(AU-19 와 같다)
- [ ] 코드 주석이 이 제한을 개인정보 보호로 적지 않는다 — `check-nickname` 의 제한은 부하 방어다(security.md §10.1)
- [ ] 완료 보고와 `README.md` 가 각자의 `application-local.yml` 에 옮길 줄을 적는다(§1.3)
- [ ] 기존 테스트가 그대로 초록이다 — 테스트 프로파일의 한도는 위 `application-test.yml` 이 갖는다

**검증** — 위 테스트(움직이는 시계), `./gradlew test`

| 케이스 | 기대 결과 |
| --- | --- |
| `check-nickname` 을 한도까지, 한 번 더 | 다음이 429 `C009` + `Retry-After` |
| 시계를 창 경계 너머로 | 다시 통과 |
| 요청마다 다른 `X-Forwarded-For` | 같은 키로 센다 |
| 같은 IPv6 /64·IPv4 사상 주소 | AU-19 와 같다 |
| 버킷 수 1 | AU-19 와 같다 |
| preflight | 세지 않는다 |
| 허용 오리진에서 온 요청의 429 | CORS 헤더가 있고 `Retry-After` 가 노출된다 |
| 제한하지 않는 경로(예: `GET /api/v1/members/{accountId}`) | 몇 번이든 429 가 아니다 |
| 규칙 설정이 빠졌다 | 기동 실패 |

---

### M-16 프로필 일괄 조회 (ADMIN) [기능]

| | |
| --- | --- |
| 저장소 | `yuno110/sp-member` |
| 의존 | M-14 |
| 공유 파일 | `MemberController`·`MemberService`, `MemberControllerTest` (M-15) |
| 마이그레이션 | 없음 |
| 참조 | [../requirements/member.md §13](../requirements/member.md), [../api-contract.md §3.1](../api-contract.md)·§3.2·§9.12, [../security.md §5.1](../security.md)·§5.2, [../conventions.md §1.2](../conventions.md) |

**산출물**
- `member/dto/` — `{ "members": [...] }` 응답. 원소는 `GET /api/v1/members/{accountId}` 의 응답 DTO 를 그대로 쓴다
- `MemberController`·`MemberService` 확장
- `MemberRepository` — `account_id` 목록으로 읽기
- 테스트: `MemberControllerTest`, `MemberServiceTest`, `MemberRepositoryTest` 확장

**완료 기준**
- [ ] `accountIds` 가 쉼표 목록과 같은 이름의 반복을 둘 다 받는다(api-contract §3.2)
- [ ] 원소가 §3.1 의 공개 조회와 같은 모양이다 — 탈퇴는 `"탈퇴한 회원"`·`deleted: true`, 마스킹 규칙은 한 곳이다
- [ ] 없는 id 는 빼고(404 가 아니다), 같은 id 는 한 번, `accountId` 오름차순
- [ ] 개수가 §3.2 의 범위 밖이면 400 `C001`(`fieldErrors` 에 `accountIds`) — **절삭하지 않는다.** 누락은 400 `C001`(`fieldErrors` 빈 배열), 숫자가 아닌 값은 400 `C002`
- [ ] ADMIN 판정은 Service 계층에서 `LoginMember.role()` 이 `"ADMIN"` 과 **같을 때만 허용**하는 모양이다. 아니면 403 `A004`(security.md §5.1)
- [ ] 내부 API(`/internal/**`)를 쓰지 않고, member 가 auth 를 부르지 않는다(§3.2, member.md §13)

**검증** — 위 테스트, `./gradlew test`

| 케이스 | 기대 결과 |
| --- | --- |
| ADMIN, `accountIds=3,1` | 200, `accountId` 1·3 의 순서 |
| `accountIds=1&accountIds=2` | 둘 다 |
| 없는 id 가 섞였다 | 빠진다 |
| 같은 id 두 번 | 한 번 |
| 탈퇴한 프로필 | `"탈퇴한 회원"`, `deleted: true` |
| 최대보다 많은 id | 400 `C001`, `fieldErrors` 에 `accountIds` |
| `accountIds` 누락 | 400 `C001`, `fieldErrors` 빈 배열 |
| `accountIds=abc` | 400 `C002` |
| USER 토큰 | 403 `A004` |
| 토큰 없음 | 401 `A001` |
| `GET /api/v1/members/{accountId}` | 그대로 무인증으로 응답한다 |

## 5. 넘기는 것

### 5.1 통합 계획이 I 항목으로 세울 측정 대상

**목록의 정본은 [phase2.md §5.4](phase2.md)의 「auth·member 쪽의 측정 대상」 단락이다** — 그 단락이 예로 든 것을 아래에 이 계획의 항목과 이어 적는다. 그 단락이 바뀌면 그쪽을 따른다. 이 계획은 이것들을 작업 항목으로 세우지 않는다 — 항목의 테스트는 H2·MockMvc 위에서 돌아 MySQL 의 락·콜레이션과 Tomcat 의 주소 처리를 재현하지 않는다.

| 측정 대상 (phase2 §5.4 의 예) | 재는 대상을 만드는 항목 |
| --- | --- |
| 같은 이메일의 동시 로그인 실패에서 카운터·잠금이 시도 수와 맞는가(첫 실패의 동시 INSERT 충돌 포함) | AU-18 |
| 같은 토큰의 동시 확인 중 정확히 하나만 성공하는가 | AU-16, AU-17 |
| `login_attempt.email_key` 와 `account.email` 의 콜레이션이 같고(`information_schema`) 계정 조회와 같은 기준으로 키가 합쳐지는가 | AU-12, AU-18 |
| `X-Forwarded-For` 를 바꿔 보내도 제한이 같은 키로 세는가 | AU-19, M-15 |
| `account.email` 의 콜레이션이 대소문자 말고 무엇을 같다고 보는가(예: 악센트 변형) | AU-12, AU-19 |
| 비ASCII 표기가 계정 조회와 같은 키로 합쳐지는가(예: U+0130 `İ`) | AU-18 |
| 재설정 요청·재발송의 응답 시간이 계정 유무로 갈리지 않는가 | AU-15, AU-16, AU-17 |
| 100자를 넘는 이메일 입력이 계정에 닿지 않는가(예: 끝 공백) | AU-18 |
| 429 응답에 CORS 헤더와 `Retry-After` 가 실리고 브라우저가 읽는가 | AU-19, M-15 |
| SMTP 가 응답하지 않을 때 API 응답이 늦어지지 않는가 | AU-14, AU-15 |

**§5.4 밖이지만 정본이 비교를 요구하는 것** — 같은 통합 항목에 넣을 수 있다.

| 대상 | 근거 | 항목 |
| --- | --- | --- |
| `C009` 의 본문·헤더를 auth·member 가 같게 내는가 — 둘의 비교다 | [../api-contract.md §8.1](../api-contract.md)의 `C009` 문단, [../conventions.md §6.1](../conventions.md) | AU-19, M-15 |
| multipart 매핑이 세 서비스에서 같고, 한도를 넘는 multipart 가 실서버에서 413 `C008` 인가 — MockMvc 는 서블릿 컨테이너의 한도를 거치지 않는다 | [../conventions.md §6.1](../conventions.md)의 블록인용 | AU-13, M-14 (board 의 같은 매핑과 함께) |

### 5.2 화면 항목이 필요로 하는 것

화면 고유의 결정은 `sp-frontend` 의 `CLAUDE.md` 가 갖는다([phase2.md §7](phase2.md)). 설계 수준의 요구는 [phase2.md §5.3](phase2.md)의 둘째 목록(2026-11-11 `D-19`)이 정본이다 — 아래는 그것을 이 계획의 항목과 이어 화면 항목을 세울 단위로 적은 것이다. **이 계획은 화면 코드를 읽지 않았다.**

**에러 코드**

| 코드 | 화면 | 생기는 항목 |
| --- | --- | --- |
| `AU006` | 로그인 — 미인증. 재발송 링크와 함께 | AU-16 |
| `AU007` | 인증·재설정의 결과 — 이미 쓴 인증 링크면 「이미 인증했다면 로그인하라」 를 함께([../requirements/member.md §11.2](../requirements/member.md)) | AU-16, AU-17 |
| `AU005` | 로그인 — 잠김. 비밀번호 재설정 링크와 함께 | AU-18 |
| `C009` + `Retry-After` | 중복 확인·가입·재설정·재발송·로그인 — 헤더의 초를 읽어 안내한다 | AU-19, M-15 |

- **코드 사전** — 이 계획의 코드에 문장이 있어야 한다. 코드 사전 테스트는 정본의 변경을 스스로 잡지 못하므로 옮긴 목록과 사전을 함께 고친다([phase2.md §5.3](phase2.md) 「에러 문장」)
- **무인증 경로의 토큰** — 무인증 경로에 만료·잘못된 토큰을 실으면 401 일 것으로 본다(프레임워크 동작의 코드 읽기). AU-13·M-14 의 테스트가 확인한다. 그대로라면 화면이 인증·재설정·재발송·로그인 요청에 저장된 Access Token 을 실을 때 만료된 토큰을 가진 사용자가 그 요청에서 401 을 받는다 — 싣는지 화면 항목이 확인한다

**엔드포인트**

| 엔드포인트 | 화면 | 생기는 항목 |
| --- | --- | --- |
| `POST /api/v1/accounts/email-verification` (202) | 재발송 요청. 202 면 계정 유무와 무관한 같은 문장 | AU-16 |
| `POST /api/v1/accounts/email-verification/confirm` (204) | `/verify-email` — fragment 의 토큰을 읽고 **사용자가 확인을 눌러야** 보낸다([../security.md §12](../security.md)). 읽은 뒤 주소창에서 fragment 를 지운다 | AU-16 |
| `POST /api/v1/accounts/password-reset` (202) | 비밀번호 찾기. 202 면 같은 문장 | AU-17 |
| `POST /api/v1/accounts/password-reset/confirm` (204) | `/reset-password` — 새 비밀번호 입력. `C001`(`newPassword`)·`AU007` 안내. fragment 를 지운다 | AU-17 |
| `GET /api/v1/accounts` + `GET /api/v1/members?accountIds=` | 관리자 회원 목록 — 한 페이지의 id 로 일괄 조회해 합치고 프로필이 없는 계정을 그린다 | AU-20 + M-16 |

**메일 흐름**

- **가입** — 계정을 만든 뒤 자동 로그인하지 않는다. 「메일을 확인하세요」 와 재발송 안내를 보이고, 프로필 등록은 인증한 뒤 처음 로그인할 때 잇는다([../requirements/member.md §4](../requirements/member.md)). **AU-16 과 한 번에 커밋한다**(§1.3)
- **링크의 모양** — `{FRONTEND_BASE_URL}/verify-email#token=…`, `{FRONTEND_BASE_URL}/reset-password#token=…`([../requirements/member.md §11.5](../requirements/member.md)). 화면의 경로가 이것과 맞아야 메일의 링크가 열린다
- **실제 서비스 e2e** — 가입한 계정이 로그인하려면 인증이 필요하다. e2e 는 Mailpit 의 API(`localhost:8025`, [../tech-stack.md §4.7.1](../tech-stack.md))로 받은 메일을 읽어 링크의 토큰을 꺼낸다. Mailpit 의 버전은 AU-14 가 고정한 것을 쓴다. e2e 는 요청 수 제한을 검증하지 않는다 — 로컬 템플릿이 한도를 덮는다([../tech-stack.md §4.6](../tech-stack.md))
- **로컬 설정** — AU-14 뒤에는 메일 설정이, AU-19·M-15 뒤에는 한도를 덮는 줄이 각 서비스의 `application-local.yml` 에 있어야 한다 — 메일 설정이 없으면 auth 가 `local` 로 뜨지 않고, 한도를 덮지 않으면 e2e 가 429 를 맞는다(§1.3). 실제 서비스 e2e 는 서비스를 띄우지 않는다 — `local` 로 먼저 띄워 둔 서비스를 친다(`sp-frontend` 의 `CLAUDE.md` — 2026-11-12 읽기)
- **중복 확인의 호출 시점** — 입력마다 부르면 한도([../security.md §10](../security.md))에 닿기 쉽다. 부르는 시점은 화면이 정한다

### 5.3 정본 개정으로 넘기는 것

이 계획을 쓰며 본 정본의 공백과 결함이다. **이 계획은 정본을 고치지 않는다** — 아래 항목은 지금의 정본대로 하고, 정하거나 고치는 것은 정본 개정이다.

- **auth·member 의 무인증 경로에 잘못된 토큰이 올 때의 응답.** 정본은 board 상세 조회에 대해서만 적는다([../requirements/board.md §9.1](../requirements/board.md)). AU-13·M-14 는 관측한 응답을 테스트로 묶을 뿐 정하지 않는다. claim 계약 위반 토큰(예: 열거 밖 `role`)이 무인증 경로로 올 때도 같다
- **요청 수 제한 설정의 기동 가드.** [../tech-stack.md §4.6](../tech-stack.md)은 그 값들을 정본 값으로 분류해 가드를 요구하지 않는다. AU-19·M-15 의 가드는 AGENTS.md 불변식 9 를 근거로 이 계획이 정했다
- **메일 헬스 지표.** 정본이 정하지 않았다. AU-14 의 끄기는 [../nfr.md §2](../nfr.md)를 근거로 이 계획이 정했다
