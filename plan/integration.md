---
title: 통합 검증
type: plan
status: living
version: v21
updated: 2026-10-18
read_when: "1차 개별 작업이 끝나고 세 서비스를 함께 검증할 때"
related: [phase1.md, ../nfr.md, ../architecture.md]
---
# 통합 검증

**AU-11·M-11·B-09가 모두 `done`이 된 뒤에** 진행한다. 통합 검증이 찾은 결함을 고치는 항목(현재 [B-10](phase1.md))은 **통합과 병행하되 1차 완료 전에 `done`이어야 한다**([phase1.md §7](phase1.md)).

**이 단계는 순차로 진행한다.** 세 서비스가 모두 기동된 상태를 전제하므로 병렬 작업이 불가능하다. 상태는 `yuno110/sp-board`의 `docs/checklist.md`에 기록한다([README.md](README.md) §상태의 위치).

여기서 확인하는 것은 **개별 서비스 테스트로는 잡을 수 없는 것들**이다. 서비스 사이의 계약, 실제 키 교환, 장애 격리, 시간대 정합, 그리고 **두 DB에 걸친 seed와 탈퇴의 부분 실패**.

---

## I-01 실제 키 교환과 E2E

> **한글을 본문에 실어 보낼 때 셸이 바이트를 깨뜨린다 — I-01 실측.** 검증 워커가 보낸 닉네임이 **member 에 닿기 전에** 한 바이트 바뀌어 "통합검증"(U+AC80)이 "통합곀증"(U+ACC0)으로 저장됐다(`B2`→`B3`). 서비스 결함이 **아니다** — 요청을 만든 셸·콘솔 코드페이지의 문제다.
>
> **그래서 눈으로 보지 말고 바이트로 본다.** 보낼 값의 바이트를 먼저 확정하고(`od` 등) `HEX(CONVERT(col USING utf8mb4))` 로 저장값과 대조한다. 그 방식이 이 깨짐을 잡아냈다 — 깨진 채로도 "member 에 등록된 값 = board 스냅샷" 은 성립했으므로 **문자열을 눈으로 비교하면 통과했을 것이다.**
>
> **한글이 꼭 필요하지 않은 검증에는 ASCII 를 쓴다.** 닉네임 바이트 보존 자체가 대상인 경우에만 한글을 쓰고, 그때는 위 방식으로 통제한다.
>
> **`curl -w` 출력을 응답 본문과 섞지 마라.** 섞인 것에서 토큰을 뽑으면 `Authorization` 헤더에 개행이 들어가 **Tomcat이 400 HTML**을 돌려준다 — 서비스 결함처럼 보이지만 아니다. 본문은 `-o <파일>`로 따로 받고, 토큰은 그 파일에서만 뽑아 `tr -d '
'`을 거친다.
>
> **`java -jar` 로 검증할 때 jar 가 소스를 담았는지 먼저 확인하라.** I-03 리뷰 실측: `build/libs` 의 jar 가 **직전 설정 변경을 담지 않은 채** 남아 있었다(`bootJar` 가 다시 돌지 않았다). 그 상태로 재현하면 **설정 없는 서비스를 재면서 설정 있는 서비스를 쟀다고 기록한다.** 변이를 넣은 뒤에도 다시 빌드해야 한다 — 안 하면 변이가 무효다.
>
> **Refresh Token은 1회용이고 로그인도 그것을 교체한다.** 그래서 대조군으로 **로그인을 먼저 치면 바로 뒤에 시험할 refresh token이 이미 죽는다** — I-02 리뷰어가 그걸로 재발급에서 401 `A002`를 받았고 순서를 바로잡자 200이었다. **I-05가 특히 걸린다**: "1단계 후 재발급 → 실패"를 로그인 뒤에 치면 **틀린 이유로 실패**하고 거짓 통과가 기록된다.

| | |
| --- | --- |
| 의존 | AU-11, M-11, B-09 |
| 참조 | [../security.md §2 §3](../security.md), [../api-contract.md §5 §6](../api-contract.md), [../requirements/member.md §10](../requirements/member.md) |

M-04·B-04에서 member·board는 **배치된 공개키**로 자체 검증만 했다. 여기서 auth-service가 실제로 발급한 토큰을 받아 검증한다.

**공개키 배포 지점이 두 곳이다.** member와 board가 각각 사본을 갖는다.

**작업**
1. member와 board 두 곳의 `src/main/resources/jwt-public.pem`이 auth의 개인키와 짝인지 확인한다 (교체가 필요하면 교체)
2. board에 내부 API 키를 member와 같은 값으로 설정. **`application-local.yml`을 쓰면 이미 충족이다**(I-01 실측: member·board의 그 파일이 sha256까지 동일). **환경변수로 줄 때 이름이 갈린다** — 운영은 `INTERNAL_API_KEY`, 로컬에서 `application-local.yml`의 리터럴을 덮으려면 `MEMBER_SERVICE_INTERNAL_API_KEY`다([../tech-stack.md §4.3](../tech-stack.md))
3. 세 서비스를 함께 기동 (`:8083`, `:8081`, `:8082`)
4. 아래 시나리오를 수행

**E2E 시나리오** — 가입이 3단계다

```
1. POST :8083/api/v1/accounts              계정 생성 -> accountId
2. POST :8083/api/v1/auth/login            로그인 -> accessToken
3. POST :8081/api/v1/members               그 토큰으로 프로필 등록 (닉네임)
4. POST :8082/api/v1/posts                 게시글 작성
                                           (board -> member 내부 API 호출이 실제로 일어난다)
5. GET  :8082/api/v1/posts                 목록에서 작성자 닉네임 확인
6. POST :8082/api/v1/posts/{id}/comments   댓글 작성
7. GET  :8082/api/v1/posts/{id}            commentCount 확인
```

**3단계를 건너뛴 경로도 확인한다.** 계정만 만들고 프로필 없이 글을 쓰면 403 `S002`여야 한다.

**완료 기준**
- [ ] auth-service가 발급한 토큰을 member와 board가 **모두** 검증한다
- [ ] **두 `jwt-public.pem`이 같은 키다**
- [ ] 게시글의 `writer_id`가 `accountId`와 일치한다
- [ ] 게시글의 `writer_nickname`이 프로필 등록 시 닉네임과 일치한다
- [ ] **board → member 내부 API 호출이 실제로 성공한다** (스텁이 아니다)
- [ ] 위 7단계가 오류 없이 완료된다
- [ ] 두 `jwt-public.pem`이 auth의 개인키와 짝이다
- [ ] **auth의 개인키가 member·board 저장소에 없다**
- [ ] **ADMIN seed의 `accountId`가 두 DB에서 일치한다**

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| E2E 7단계 수행 | 전 단계 성공 |
| 게시글의 `writerId` | `accountId`와 일치 |
| 게시글의 `writerNickname` | 프로필 닉네임과 일치 |
| **프로필 없이 글 작성** | **403 `S002`** |
| **`sp_auth.account`와 `sp_member.member`의 ADMIN** | **`id`와 `account_id`가 같은 값** |
| member·board의 `jwt-public.pem` | 바이트 단위로 동일 |
| member·board 저장소에서 `PRIVATE KEY` 검색 | 없음 |
| 다른 키로 서명한 토큰 | member·board **둘 다** 401 거부 |
| board에 잘못된 내부 API 키를 주고 작성 | **503 `S001`.** `S002` 아님. 같은 상태에서 **조회는 200**이다(§4.2). **환경변수로 줄 때는 `MEMBER_SERVICE_INTERNAL_API_KEY`다** — `INTERNAL_API_KEY`로는 덮이지 않아 **작성이 201로 성공한다**(I-01 실측 두 번, [../tech-stack.md §4.3](../tech-stack.md)) |

---

## I-02 장애 격리

| | |
| --- | --- |
| 의존 | I-01 |
| 참조 | [../nfr.md §2](../nfr.md), [../adr/0003-writer-snapshot.md](../adr/0003-writer-snapshot.md), [../adr/0012](../adr/0012-auth-as-separate-service.md) |

**스냅샷 설계의 이득과 auth 분리의 비용을 함께 확인한다.**

> **v1에서 바뀐 항목이다.** 이전에는 "member 중지 중에도 게시글 작성 → 201"이 완료 기준이었다. **이제는 503이다.** 닉네임이 JWT Claim에서 빠져 쓰기 경로가 member에 의존하기 때문이다([../adr/0012](../adr/0012-auth-as-separate-service.md)). 이것은 계획된 변경이지 결함이 아니다.

**작업**
1. I-01에서 게시글·댓글을 몇 건 만들어 둔다
2. **member-service를 중지한다** → 조회·수정·삭제를 호출한다
3. member를 되살리고 **auth-service를 중지한다** → 조회·작성을 호출한다

**완료 기준 — member 중지**
- [ ] `GET /api/v1/posts`(목록)가 정상 동작하고 작성자 닉네임이 표시된다
- [ ] `GET /api/v1/posts/{id}`(상세)와 댓글 목록이 정상 동작한다
- [ ] **기존 글·댓글의 수정·삭제가 정상 동작한다** (스냅샷을 갱신하지 않으므로 — [../requirements/board.md §3](../requirements/board.md) 규칙 7)
- [ ] **새 게시글·댓글 작성은 503 `S001`이고 저장되지 않는다**
- [ ] **로그인은 정상 동작한다** (auth가 살아 있으므로)
- [ ] member 재기동 후 작성이 정상 동작한다

**완료 기준 — auth 중지**
- [ ] 로그인·재발급이 실패한다
- [ ] **기존 토큰으로 조회·작성·수정·삭제가 모두 정상 동작한다** (오프라인 검증)
- [ ] auth 재기동 후 로그인이 정상 동작한다

**검증**

| 케이스 (member 중지) | 기대 결과 |
| --- | --- |
| 게시글 목록 조회 | 200, 작성자 닉네임 표시됨 |
| 게시글 상세 조회 | 200 |
| 댓글 목록 조회 | 200 |
| **유효 토큰으로 게시글 작성** | **503 `S001`. `post` 행 증가 없음** |
| **유효 토큰으로 댓글 작성** | **503 `S001`. `comment_count` 불변** |
| **기존 게시글 수정** | **200** |
| **기존 게시글 삭제** | **204** |
| **기존 댓글 수정** | **200** |
| **기존 댓글 삭제** | **204.** `comment_count` 감소 |
| 로그인 시도 | **200** (auth가 담당) |
| member 재기동 후 작성 | 201 |

| 케이스 (auth 중지) | 기대 결과 |
| --- | --- |
| 로그인 시도 | 실패 (auth 필요 — 정상) |
| 재발급 시도 | 실패 |
| **기존 토큰으로 게시글 작성** | **201** |
| 게시글 조회·수정·삭제 | 정상 |
| 프로필 조회 | 정상 |
| auth 재기동 후 로그인 | 200 |

조회 결과가 [../adr/0003](../adr/0003-writer-snapshot.md)에서 스냅샷을 택한 이유를 증명하고, 작성 결과가 [../adr/0012](../adr/0012-auth-as-separate-service.md)가 수용한 비용을 드러낸다.

> **이 항목은 타임아웃 예산을 쓰지 않는다.** 프로세스를 내리면 TCP가 **즉시 거부**를 돌려주므로 503이 10ms 안쪽에 떨어지고 `connect-timeout: 1s`는 발동할 기회가 없다(I-02 실측: 503이 8.6~12.8ms, connect 0.37~0.47ms). **그래서 "I-02가 타임아웃을 확인했다"고 말할 수 없다.** 그 값은 B-04의 `MemberClientTest`가 맡는다([phase1.md](phase1.md)의 "connect 1초 / read 3초 타임아웃이 설정되어 있다" 완료 기준).

---

## I-03 시간대 정합

| | |
| --- | --- |
| 의존 | I-01 |
| 참조 | [../tech-stack.md §6](../tech-stack.md) |

JVM 시간대는 실행 환경이 정한다([../adr/0011](../adr/0011-timezone-from-environment.md)). 여기서 확인하는 것은 **세 서비스와 세 스키마가 같은 기준으로 시각을 다루는가**다.

**완료 기준**
- [ ] auth·member·board의 `createdAt`이 같은 기준 시각이다
- [ ] 세 DB에 저장된 값이 KST다
- [ ] API 응답의 시각에 **오프셋이 없다.** 고정 패턴을 단언하지 않는다 — 소수부는 컬럼 타입이 정하고 코드가 보장하지 않는다([../tech-stack.md §6](../tech-stack.md))
- [ ] **세 서비스**의 JDBC URL에 `serverTimezone=Asia/Seoul`이 있다
- [ ] **세 서비스**에 `hibernate.jdbc.time_zone: Asia/Seoul`이 있다
- [ ] **MySQL `DATETIME`에 소수부가 남지 않고 가까운 시각이 한 값으로 합쳐지는 것을 확인한다**(`DATETIME`은 **반올림**한다 — `…09.5` 이상은 다음 초다). [../api-contract.md §7.1](../api-contract.md)의 동률 정렬 규칙이 **그 합쳐짐**에 걸려 있다

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| 계정 생성·프로필 등록·게시글 작성을 1분 내 수행 | 세 `createdAt` 차이가 1분 이내 |
| DB에서 직접 조회한 `created_at` | 현재 KST 시각과 일치 |
| API 응답의 시각 문자열 | `Z`·`+09:00` 등 오프셋 없음 |
| **가까운 시각에 게시글·댓글 여러 건 작성** | DB의 `created_at`이 **한 값으로 합쳐진다**(소수부가 없다 — `DATETIME`은 **반올림**한다, [../api-contract.md §7.1](../api-contract.md)). H2는 `DATETIME_PRECISION`이 6이라 **단위 테스트로는 재현되지 않는다** |
| **그 동률 상태에서 목록 1·2페이지** | 중복·누락 **없음**([../api-contract.md §7.1](../api-contract.md)의 `id` 마지막 정렬 키). **이 조건을 실제로 만들 수 있는 곳은 여기뿐이다** |

> **JVM 기본 시간대는 검증 대상이 아니다.** 개발 머신이 KST라 항상 통과하므로 아무것도 증명하지 못한다. 배포 시 `TZ=Asia/Seoul`을 거는 것은 2차 컨테이너화의 확인 항목이다([../plan/phase2.md](../plan/phase2.md)).

---

## I-04 응답 형식 계약 일치

| | |
| --- | --- |
| 의존 | I-01 |
| 참조 | [../api-contract.md §7 §8.1](../api-contract.md), [../adr/0007-shared-code-policy.md](../adr/0007-shared-code-policy.md) |

`ApiResponse` 등을 **세 서비스에** 복제했으므로([../adr/0007](../adr/0007-shared-code-policy.md)) **실제로 같은 형식인지 확인**한다. 이것이 복제 방식의 위험을 막는 장치다.

**복제본이 2벌에서 3벌로 늘었다.** 0007의 재검토 조건("서비스가 3개째")이 발동했고 재검토 결과 복제를 유지하기로 했으므로, **이 검증의 중요도가 올라간다.** 비교는 2자가 아니라 3자다.

**완료 기준**
- [ ] **세 서비스**의 성공 응답 구조가 동일하다 (`success`, `data`, `error` 키)
- [ ] **세 서비스**의 에러 응답 구조가 동일하다 (`error.code`, `error.message`, `error.fieldErrors`)
- [ ] **`fieldErrors` 의 요청 수준·바인딩 수준 구분이 세 서비스에서 같다** ([../api-contract.md §2.3](../api-contract.md)) — 누락은 빈 배열, 바인딩된 필드의 오류는 1건. **board 의 빈 배열은 본문 파싱 실패로 본다** — 아래 블록인용
- [ ] 공통 에러 코드(`C001`, `A001`~`A004`)의 HTTP 상태와 메시지가 **세 서비스에서** 같다
- [ ] **세 서비스**의 페이징 응답 **클래스**가 동일하다 — **응답 3자 비교는 할 수 없다**(auth·member 에 목록 엔드포인트가 없다, I-04 실측). **패키지명을 정규화하면 `PageResponse` 가 주석까지 3벌 동일한 것**과 board 의 세 경로가 §7.1 의 키를 내는 것으로 본다 (원본은 바이트 동일이 **아니다** — 패키지 선언이 다르다. 정규화 강도를 적는 이유는 [../process/review-policy.md §4.1](../process/review-policy.md)에 있다). **복제 대상은 넷이다** — `ApiResponse`·`ErrorResponse`·`PageResponse`·`BusinessException` 이고 넷 다 같은 정규화에서 3벌 동일이다
- [ ] 어느 응답에도 스택트레이스·SQL·내부 호스트명이 없다
- [ ] **서비스별 에러 코드가 서로 섞이지 않았다** — auth에 `M0xx`, member에 `AU0xx`, board에 둘 다 없다

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| 세 서비스 성공 응답의 최상위 키 | 동일 집합 |
| 세 서비스 `C001` 응답 | HTTP 400, 같은 메시지, `fieldErrors` 존재 |
| **세 서비스 `C002`~`C007`** | **상태·메시지 일치.** [../conventions.md §6.1](../conventions.md) 의 예외 11종이 같은 코드로 변환된다. **11종 중 9종은 세 서비스 전부에서 실행으로, 둘은 도달 불가라 소스로 본다** — 아래 블록인용 |
| 세 서비스 `A001`~`A004` | 상태·메시지 일치 |
| **Claim 계약 위반 토큰** | `role` 누락·`sub` 누락 토큰(서명은 유효)에 **셋 다 401 `A002`** ([../tech-stack.md §2.1](../tech-stack.md)). 집행 층이 서비스마다 다르므로 **응답으로만 비교한다** |
| 세 서비스 `fieldErrors` 빈 배열 케이스 | 필수 파라미터 누락·본문 파싱 실패에서 **셋 다 빈 배열** ([../api-contract.md §2.3](../api-contract.md)). **board 에는 필수 파라미터 누락 경로가 없다** — 아래 블록인용 |
| **세 서비스 `fieldErrors` 1건 케이스** | **바인딩 수준** 오류에서 **셋 다 1건**이고 `field` 가 파라미터명이다 ([../api-contract.md §2.3 §4.1](../api-contract.md)). 경로는 auth `check-email` 의 형식 오류, member `check-nickname` 의 형식·길이, board 의 목록 `size=0`·`page=-1` 이다 — 셋 다 `HandlerMethodValidationException` 을 지난다 |
| 각 서비스의 `ErrorCode` 열거 | 타 서비스 전용 접두어 없음 |
| 세 서비스 페이징 응답 키 | `content`, `page`, `size`, `totalElements`, `totalPages`, `first`, `last`. **board 에서만 관측된다** — 아래 블록인용 |
| **세 서비스의 작성 응답 대 조회 응답 시각 모양** | **소수부가 갈린다** — 작성은 flush 전 엔티티라 소수부가 있고 조회는 `DATETIME` 이라 없다([../tech-stack.md §6](../tech-stack.md) I-01 실측). **그 갈림은 board 에서만 관측된다** — auth·member 의 작성 응답에는 시각 필드가 없다(아래 블록인용). 조회 경로끼리는 셋 다 소수부 없음으로 비교한다. 고정 패턴을 단언하지 않는다 |
| 500 응답 본문 | **세 서비스 모두** 스택트레이스 없음. **500 은 유도해야 한다** — 아래 블록인용에 수단이 있다 |
| **세 서비스의 로그 수준** | 클라이언트 오류는 `ERROR`가 **아니고** 마지막 그물은 `ERROR`다 ([../conventions.md §6.1](../conventions.md)). **`GlobalExceptionHandler` 가 남긴 줄로 센다** — 전체 로그로 세면 틀린다(Hibernate 의 `SqlExceptionHelper` 가 `ERROR` 를 따로 낸다. I-04 리뷰 실측). **절대 수치는 요청 집합에 따라 달라지므로 재현 대상이 아니다** — 두 극이 핸들러 단위로 성립하는지만 본다. **auth 는 이 단언을 자기 테스트에 갖지 않으므로 여기가 유일한 게이트다** |

> **"세 서비스" 를 요구하는 네 줄 중 셋은 경로가 두 서비스에 없다. I-04 실측이고 구현 차이가 아니다.** 완료 기준을 다시 쓸 때 **먼저 그 경로가 존재하는지 본다** — 없는 경로를 요구하면 측정이 불가능하거나, 소스 비교를 "충족" 으로 적는 공허한 충족이 된다.
>
> - **페이징 응답**: auth·member 에 목록 엔드포인트가 **없다.** 매핑 전수(auth 8개·member 7개)에 목록 핸들러가 없고, **`PageResponse` 가 두 저장소에서 자기 파일 밖 사용처가 0건**이다(board 는 6곳). **"지금 없다" 까지만 확인됐다** — 목록이 생기는 것을 막는 테스트나 빌드 규칙은 **없다**(auth 테스트 21개·member 15개에 가드가 없고, member 의 라우팅 단언은 `/internal` 아래만 못박는다)
> - **`C002`(타입 불일치)**: auth 의 두 컨트롤러에 `@PathVariable` 이 **0개**이고 `@RequestParam` 하나가 `String` 이다. `@RequestHeader`·`@CookieValue`·`@RequestPart`·`@ModelAttribute`·`@MatrixVariable`·`@RequestAttribute`·`@SessionAttribute` 가 **전부 0개**이고 커스텀 `Converter`·`Formatter`·`@InitBinder` 도 없다 — **변환 지점이 하나도 없다.** `GET /accounts/abc` 는 매핑이 없어 **404 `C004`** 다. 노린 요청 10가지가 하나도 닿지 않았고 **member·board 에서는 쉽게 닿는다**(대조군). **"지금 없다" 까지만 확인됐다**
> - **필수 파라미터 누락**: board 의 `@RequestParam` **10개가 전부 `required = false`** 다(`@RequestPart`·`@ModelAttribute`·`@RequestHeader` 도 0개라 우회로가 없다). board 의 빈 배열은 본문 파싱 실패로만 확인한다. **"지금 없다" 까지만 확인됐다**
> - **작성 응답의 시각**: auth·member 의 작성 응답 DTO 에 시각 필드가 **없다**(`MemberResponse` 는 `(accountId, nickname)` 이다). `createdAt` 을 싣는 DTO 는 두 서비스에 하나씩이고 **둘 다 조회 경로**다. member 의 `PATCH /members/me` 도 `MemberResponse` 를 돌려주므로 변경 경로에도 없다. **`grep` 으로는 속는다** — 그 파일들의 `createdAt` 문자열은 javadoc 이다. record 선언을 읽는다
>
> **500 은 평범한 호출로 유도되지 않는다. 먼저 그것을 재고, 그다음 유도한다.** 비정형 요청 15가지(깨진 charset·2000단 중첩 JSON·5000자리 숫자·`%2F` 경로·`TRACE`·`page=2147483648` 등)가 **하나도 `C005` 에 닿지 않았다** — §6.1 의 10종이 모두 4xx 로 받는다. 유도는 **코드·설정·스키마·seed·MySQL 변수를 바꾸지 않고** 자기가 만든 행 하나만 건드리는 쪽으로 한다(I-04 실측, 전부 원복했다).
>
> - **board** — 자기 글의 `view_count` 를 `9223372036854775807` 로 두고 상세 조회. 좁은 UPDATE 가 SQL 쪽에서 더하므로 `Data truncation: BIGINT value is out of range` → `DataIntegrityViolationException`
> - **auth** — 자기 계정의 `role` 을 `'BOGUS'` 로 두고 `GET /accounts/me`. **JWT 인증은 통과하고 서비스의 DB 읽기에서 터진다**(`No enum constant …Role.BOGUS`)
> - **member** — 별도 MySQL 세션에서 **자기 행 하나만** `FOR UPDATE` 로 잡고 `PATCH /members/me`. `innodb_lock_wait_timeout`(50초)을 넘겨 `PessimisticLockingFailureException`. **닉네임을 현재 값과 다르게** 줘야 한다(같으면 더티 체크가 UPDATE 를 발행하지 않는다). 락은 세션으로 들고 있어야 하므로 락 프로세스와 요청을 분리한다
> - **안 되는 수단 둘**: 내부 벌크에 70,000건(Hibernate 가 쪼갠다 — `in` 절 `?` 가 1개였다), `nickname` 을 NULL 로 두기(던지는 자리가 없어 200 `"nickname":null`)
>
> **Claim 계약 위반 토큰은 셋 다 401 `A002` 이고 본문이 바이트 동일이다(각 119바이트). 갈리는 것은 `Content-Type` 하나다** — member 만 `application/json;charset=UTF-8` 이고 auth·board 는 `application/json` 이다. 집행 층이 달라서다(member 는 디코더 → `SecurityErrorResponder`, auth·board 는 리졸버 → `GlobalExceptionHandler`. 로그가 그것을 보여 준다 — member 만 `business exception: A002` 를 남기지 않는다). 쓰레기 토큰은 **셋 다** `charset=UTF-8` 이다. 검증표가 응답으로만 비교하라고 했고 상태·본문이 같으므로 결함이 아니다. **대조군 토큰을 먼저 쳐서 서명 체계가 유효함을 고정한다** — 그러지 않으면 뒤의 401 이 서명 문제인지 claim 문제인지 가를 수 없다.
>
> **`role` 이 "있지만 열거 밖인 값" 이면 갈린다 — I-04 리뷰 실측이다.** auth 401 `A002` · member 200 · board 200. 소스가 갈림을 설명한다(auth 만 `Role.valueOf`, member·board 는 `hasText`). 검증표가 요구하는 것은 **누락** 두 경우이고 그 둘은 일치했으므로 이 항목의 미충족은 아니지만, **계약 밖 토큰이 두 서비스를 통과하는 것은 발견이다.** 권한 상승은 아니다 — 자세한 것은 [../tech-stack.md §2.1](../tech-stack.md)이 갖는다. **값 검증을 어디에 둘지는 별 항목이 결정한다.**
>
> **`ApiResponse` 모양이 아닌 에러 응답이 세 서비스에 공통으로 둘 있다. I-04 리뷰 실측이고 결함이 아니다 — 셋이 대칭이다.** 하나는 `/error`(Spring Boot 기본 모양, `status:999`), 다른 하나는 **쿼리에 `[` 를 넣는 등 Spring 에 닿기 전에 컨테이너가 자르는 요청**으로 **435바이트 HTML**(`text/html;charset=utf-8`, 상태 줄만)이다. 둘 다 누출이 없다(스택트레이스·SQL·호스트명 0건). **이 경계를 적어 두는 이유는 "세 서비스의 에러 응답 구조가 동일하다" 를 `ApiResponse` 로만 읽으면 그 밖이 보이지 않기 때문이다.**

불일치가 발견되면 [../api-contract.md](../api-contract.md)를 정본으로 삼아 세 서비스를 맞춘다.

---

## I-05 탈퇴 부분 실패

| | |
| --- | --- |
| 의존 | I-01 |
| 참조 | [../architecture.md §4.4](../architecture.md), [../requirements/member.md §8](../requirements/member.md), [../adr/0012](../adr/0012-auth-as-separate-service.md) §5 |

**탈퇴가 2단계이고 서버가 완주를 강제하지 못하므로, 중간 상태가 실제로 안전한지 확인한다.** 이것은 단위 테스트로 잡을 수 없다 — 두 서비스와 두 DB에 걸쳐 있다.

**작업**
1. 계정과 프로필을 만들고 게시글을 몇 건 쓴다
2. **1단계만 수행한다** (`DELETE :8083/api/v1/accounts/me`)
3. 2단계를 수행하지 않은 채로 아래를 확인한다
4. 그 다음 2단계를 수행하고 최종 상태를 확인한다

**완료 기준 — 1단계만 수행한 상태**
- [ ] **로그인이 즉시 막힌다** (401)
- [ ] **재발급이 즉시 막힌다**
- [ ] 기존 Access Token으로는 토큰 만료까지 접근이 가능하다 (알려진 잔여 노출). **세 성분을 갈라 적는다** — ① 1단계 뒤에도 접근이 **된다** ② 그 접근이 **만료로 끝난다** ③ 끊기는 지점이 **`exp`+60초**다. skew 값 자체의 소유는 [../security.md §5.3](../security.md)이다 (I-05 실측: 같은 경로가 만료 전 200, `exp`**+7초·+35초 200**, `exp`**+70초·+130초 401 `A003`**. 무토큰 대조가 여섯 발화 모두 200 이라 "서비스가 내려갔다" 가 배제된다. 만료 뒤 쓰기도 board·member 둘 다 401 `A003` 이고, **같은 board 쓰기가 만료 전에는 403 `S002`** 였다 — 만료가 프로필 상태보다 앞서 끊었다)
- [ ] 프로필 행이 아직 `deleted = false`다
- [ ] **기존 토큰으로 2단계를 재시도할 수 있다** (복구 경로가 살아 있다)
- [ ] 과거 게시글·**댓글**의 `writer_nickname`이 그대로 남아 있다

**완료 기준 — 2단계까지 수행**
- [ ] 프로필이 `deleted = true`, `nickname = null`이다
- [ ] 같은 계정으로 프로필을 재생성할 수 없다 (409 `M007`)
- [ ] 같은 이메일로 계정을 재생성할 수 없다 (409 `AU002`)
- [ ] 과거 게시글이 남아 있고 닉네임도 그대로다
- [ ] **해방된 닉네임을 다른 사람이 쓸 수 있다**

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| 1단계 후 로그인 | 401 |
| 1단계 후 재발급 | **401 `A002`** (I-05 실측. [../api-contract.md §2.1](../api-contract.md) — 재발급 거부는 만료만 `A003` 이고 나머지는 전부 `A002` 다) |
| 1단계 후 기존 토큰으로 프로필 조회 | 200 (아직 살아 있음) |
| **1단계 후 기존 토큰으로 2단계 재시도** | **204. 복구된다** |
| 1단계를 **비밀번호 없이** 시도 | 400. 아무것도 삭제되지 않음 |
| 2단계 후 프로필 재생성 | 409 `M007` |
| 2단계 후 같은 이메일로 계정 생성 | 409 `AU002` |
| 2단계 후 해방된 닉네임으로 타인 등록 | 201 |
| 2단계 후 과거 게시글 조회 | 200, 닉네임 그대로 |
| **2단계 후 과거 댓글 목록 조회** | **200, 닉네임 그대로.** 댓글도 스냅샷이다([../domain-model.md §4.2](../domain-model.md)) |
| 1·2단계 중 서비스 간 호출 | **0회.** 클라이언트가 순서대로 호출한다 |

> **쓰기 차단은 1단계가 아니라 2단계가 만든다. I-05 실측이고 2차의 입력이다.** 1단계만 끝난 계정은 프로필이 활성이라 내부 API 가 `deleted:false` 를 돌려주고 **새 글·댓글이 생성된다**(201). auth 만 `/accounts/me*` 를 닫고(404 `AU001`) member·board 는 **전부 열려 있다** — 닉네임 변경 200, 글·댓글 작성·수정·삭제 201·200·204. 2단계 뒤에는 같은 토큰이 **403 `S002`** 다. 즉 **클라이언트가 1단계 뒤 이탈하면 AT 만료까지 board 에서 완전히 기능하는 "탈퇴한" 사용자가 남는다.** [../architecture.md §4.3.1](../architecture.md)의 "탈퇴 후 작성 불가는 보장이 아니라 통상 동작" 이 그 모습이다.
>
> **이미 탈퇴한 계정에서는 1단계가 멱등이고 틀린 비밀번호에도 204 다**(실측). 이미 삭제된 계정에 `DELETE /accounts/me` 를 틀린 비밀번호로 쳐도 204 이고 `updated_at` 이 바뀌지 않는다 — [../api-contract.md §2.2](../api-contract.md)의 "아무것도 바꾸지 않는다" 와 같다. **미삭제 계정에서는 갈린다** — 비밀번호 누락은 400 `C001`, 틀린 비밀번호는 400 `AU004` 다.
>
> **2단계를 수행하지 않으면 프로필이 남고 닉네임이 선점된다.** 1차에는 **고아 프로필을 찾아내는(목록·수거) 수단이 없다.** 알려진 제약이며 2차 이벤트 범위다([../adr/0010](../adr/0010-kafka-for-nickname-sync.md)).
>
> **"관측할 수단이 없다" 로 읽지 마라 — I-05 실측.** `accountId` 를 **이미 알고 있으면** `GET /api/v1/members/{accountId}` 가 `deleted:false` 를 돌려주므로 **한 건은 관측된다.** 없는 것은 **찾아내는** 경로다 — 세 서비스에 `@Scheduled`·`@EnableScheduling` 이 0건이고 member 의 엔드포인트에 관리자 경로가 없다(실측).

---

## 완료 후

I-01~I-05가 모두 `done`이면 1차가 완료된다. [phase2.md](phase2.md)의 상세화를 시작한다.
