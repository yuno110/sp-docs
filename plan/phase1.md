---
title: 1차 작업 계획
type: plan
status: living
version: v1
updated: 2026-09-11
read_when: "작업 항목의 범위·의존·완료 기준을 확인하거나 다음 할 일을 고를 때. 상태는 담당 저장소의 checklist.md를 본다"
related: [README.md, integration.md, ../process/dev-workflow.md, ../requirements/member.md, ../requirements/board.md]
---
# 1차 작업 계획

작업 항목 20개(M 11 + B 9)와 통합 검증 4개로 구성한다. 통합 검증은 [integration.md](integration.md)에 있다.

절차는 [../process/dev-workflow.md](../process/dev-workflow.md)를 따른다. **상태는 이 문서에 적지 않는다.**

## 1. 병렬 구간

```
member 저장소                    board 저장소
─────────────                    ────────────
M-01 스캐폴딩                     B-01 스캐폴딩
M-02 공통 기반                    B-02 공통 기반          <- 여기부터 완전 병렬
M-03 Member 엔티티                B-03 JWT 검증
M-04 회원가입                     B-04 Post 엔티티
M-05 JWT 발급                     B-05 게시글 작성·상세
M-06 로그인                       B-06 목록·검색
M-07 토큰 재발급·로그아웃          B-07 수정·삭제
M-08 내 정보                      B-08 댓글
M-09 비밀번호·탈퇴                 B-09 마무리
M-10 프로필·내부 API
M-11 마무리
        \                              /
         \____ I-01 ~ I-04 통합 검증 __/   <- 순차
```

**두 서비스는 서로를 기다리지 않는다.** B-03(JWT 검증)이 M-05(JWT 발급)를 기다릴 것 같지만 그렇지 않다. 계약이 [../api-contract.md §5](../api-contract.md)에 문서로 확정되어 있으므로, board는 그 스펙대로 **테스트용 키 페어를 만들어 자체 검증**하면 된다. 실제 키 교환은 통합 단계(I-01)에서 한다.

## 2. member-service 작업 항목

### M-01 프로젝트 스캐폴딩

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | 없음 |
| 참조 | [../tech-stack.md §1 §3](../tech-stack.md), [../conventions.md §1.1](../conventions.md) |

**산출물**
- `build.gradle`, `settings.gradle`, Gradle Wrapper
- `src/main/java/com/example/member/MemberApplication.java`
- `src/main/resources/application.yml`, `application-local.yml`
- `.gitignore` (`private.pem`, `*.env`, `build/`, `.gradle/`, QueryDSL 생성 경로 포함)

**완료 기준**
- [ ] `./gradlew build`가 성공한다
- [ ] `./gradlew bootRun`으로 8081 포트에 기동된다
- [ ] `application-local.yml`의 DB 접속 정보가 환경변수로 외부화되어 있다 ([../tech-stack.md §4.3](../tech-stack.md))
- [ ] `.gitignore`에 `private.pem`, `*.env`가 있다
- [ ] 시간대가 `Asia/Seoul`로 명시 설정되어 있다

**검증** — `MemberApplicationTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 컨텍스트 로딩 | 예외 없이 기동 |
| `TimeZone.getDefault()` | `Asia/Seoul` |

---

### M-02 공통 기반

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-01 |
| 참조 | [../api-contract.md §6 §7.1 §7.2](../api-contract.md), [../domain-model.md §1.1](../domain-model.md), [../conventions.md §6 §7](../conventions.md) |

**산출물**
- `global/common/ApiResponse.java`, `ErrorResponse.java`, `PageResponse.java`
- `global/common/BaseTimeEntity.java`
- `global/error/ErrorCode.java` (C001~C005, A001~A004, M001~M005)
- `global/error/BusinessException.java`
- `global/error/GlobalExceptionHandler.java`
- `global/config/JpaConfig.java` (`@EnableJpaAuditing`)
- `global/config/SwaggerConfig.java`

복제 대상 파일 상단에 정본 주석을 남긴다([../conventions.md §7.1](../conventions.md)).

**완료 기준**
- [ ] `ErrorCode`의 코드·HTTP 상태·메시지가 [../api-contract.md §7](../api-contract.md)과 정확히 일치한다
- [ ] `BusinessException`을 던지면 해당 코드의 HTTP 상태와 응답 본문이 나온다
- [ ] `@Valid` 검증 실패가 `C001`로 변환되고 `fieldErrors`에 필드별 메시지가 담긴다
- [ ] 응답 본문에 스택트레이스·SQL이 포함되지 않는다
- [ ] `/swagger-ui.html`이 열린다

**검증** — `GlobalExceptionHandlerTest` (`@WebMvcTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| `BusinessException(M002)` 발생 | 409, `error.code = "M002"` |
| `BusinessException(A004)` 발생 | 403, `error.code = "A004"` |
| `@Valid` 실패 | 400, `C001`, `fieldErrors` 비어있지 않음 |
| 성공 응답 | `success = true`, `error = null` |
| 예상치 못한 `RuntimeException` | 500, `C005`, 본문에 스택트레이스 없음 |

---

### M-03 Member 엔티티와 스키마

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-02 |
| 참조 | [../domain-model.md §1 §2.1 §2.3](../domain-model.md), [../conventions.md §2](../conventions.md) |

**산출물**
- `member/entity/Member.java`, `member/entity/Role.java`
- `member/repository/MemberRepository.java`
- `src/main/resources/db/migration/V1__create_member.sql`

**완료 기준**
- [ ] 기동 시 Flyway가 `member` 테이블을 생성한다
- [ ] 컬럼 타입·길이·NULL 여부가 [../domain-model.md §2.1](../domain-model.md)과 일치한다
- [ ] `email`, `nickname`에 UNIQUE 제약이 있다
- [ ] `created_at`, `updated_at`이 `DATETIME`이고 자동 기록된다
- [ ] `role`이 문자열(`USER`/`ADMIN`)로 저장된다
- [ ] Entity에 `@Setter`·`@Data`가 없다

**검증** — `MemberRepositoryTest` (`@DataJpaTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| 저장 후 조회 | 모든 필드 일치 |
| 중복 email 저장 | `DataIntegrityViolationException` |
| 중복 nickname 저장 | `DataIntegrityViolationException` |
| 저장 시 | `createdAt`, `updatedAt`이 null이 아님 |
| `role` 미지정 저장 | `USER`로 저장됨 |
| `deleted` 미지정 저장 | `false`로 저장됨 |

---

### M-04 회원가입과 중복 확인

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-03 |
| 참조 | [../requirements/member.md §1 §2 §3](../requirements/member.md) (M-01~M-03), [../api-contract.md §2.2 §8.1](../api-contract.md), [../security.md §1](../security.md) |

**산출물**
- `member/dto/SignUpRequest.java`, `MemberResponse.java`, `CheckResponse.java`
- `member/service/MemberService.java`
- `member/controller/MemberController.java`
- `global/config/SecurityConfig.java` (`PasswordEncoder` 빈, 가입·중복확인 경로 `permitAll`)
- `V2__seed_admin.sql` (기본 관리자 1개, BCrypt 해시)

**완료 기준**
- [ ] `POST /api/v1/members`가 201과 `{id, email, nickname}`을 반환한다
- [ ] 응답에 `password`가 포함되지 않는다
- [ ] 비밀번호가 BCrypt로 해싱되어 저장된다 (평문 저장 아님)
- [ ] 중복 이메일은 409 `M002`, 중복 닉네임은 409 `M003`
- [ ] 검증 규칙이 [../requirements/member.md §2](../requirements/member.md)와 일치한다
- [ ] `GET /api/v1/members/check-email`, `check-nickname`이 동작한다
- [ ] seed 관리자 계정이 생성되고 비밀번호가 BCrypt 해시로 저장되어 있다

**검증** — `MemberServiceTest`(단위), `MemberControllerTest`(`@SpringBootTest` + MockMvc)

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 가입 | 201, DB에 저장됨 |
| 저장된 비밀번호 | 평문과 다르고 `BCrypt.matches`로 검증됨 |
| 응답 본문 | `password` 키 없음 |
| 중복 이메일 | 409, `M002` |
| 중복 닉네임 | 409, `M003` |
| 이메일 형식 오류 | 400, `C001` |
| 비밀번호 7자 | 400, `C001` |
| 비밀번호 특수문자 없음 | 400, `C001` |
| 닉네임 1자 / 11자 | 400, `C001` |
| 미사용 이메일 중복 확인 | 사용 가능 응답 |

---

### M-05 RSA 키와 JWT 발급

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-04 |
| 참조 | [../security.md §2 §3 §4](../security.md), [../api-contract.md §5](../api-contract.md), [../tech-stack.md §2.2](../tech-stack.md) |

**산출물**
- `global/security/JwtTokenProvider.java` (`NimbusJwtEncoder` 사용)
- `global/config/JwtConfig.java` (개인키 로딩, `kid` 설정)
- `auth/dto/TokenResponse.java`
- `application.yml`에 만료 시간 설정

**완료 기준**
- [ ] 발급된 토큰의 Claim이 [../api-contract.md §5](../api-contract.md)와 정확히 일치한다 (`sub`, `nickname`, `role`, `iss`, `iat`, `exp`)
- [ ] 서명 알고리즘이 RS256이고 header에 `kid`가 있다
- [ ] Access Token 만료가 30분, Refresh Token이 14일이다
- [ ] 개인키가 환경변수로 주입되며 **기본값이 없다** (없으면 기동 실패)
- [ ] 개인키 파일이 커밋되지 않았다
- [ ] jjwt 의존성을 사용하지 않는다

**검증** — `JwtTokenProviderTest`

| 케이스 | 기대 결과 |
| --- | --- |
| Access Token 발급 후 디코딩 | `sub`, `nickname`, `role`, `iss` 값 일치 |
| 토큰 header | `alg = RS256`, `kid` 존재 |
| Access Token `exp - iat` | 1800초 |
| Refresh Token `exp - iat` | 1209600초 |
| 공개키로 서명 검증 | 통과 |
| payload 변조 후 검증 | 실패 |
| 개인키 환경변수 없이 기동 | 기동 실패 |

---

### M-06 로그인과 Security 설정

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-05 |
| 참조 | [../requirements/member.md §1](../requirements/member.md) (M-04), [../api-contract.md §2.1 §8.2](../api-contract.md), [../security.md §1 §4 §5.1](../security.md) |

**산출물**
- `auth/dto/LoginRequest.java`
- `auth/service/AuthService.java`
- `auth/controller/AuthController.java`
- `global/security/LoginMember.java`, `@LoginMember` ArgumentResolver
- `SecurityConfig` 갱신 (STATELESS, CSRF 비활성, CORS 화이트리스트, 경로별 인가)

**완료 기준**
- [ ] `POST /api/v1/auth/login`이 200과 `TokenResponse`를 반환한다
- [ ] 비밀번호 불일치·없는 이메일 모두 401 `M004` (어느 쪽이 틀렸는지 노출하지 않는다)
- [ ] 탈퇴 회원(`deleted = true`)은 로그인할 수 없다
- [ ] 세션이 생성되지 않는다 (`SessionCreationPolicy.STATELESS`)
- [ ] 인증 없이 보호 경로 접근 시 401 `A001`
- [ ] CORS 설정에 `*`가 없다

**검증** — `AuthServiceTest`, `AuthControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 로그인 | 200, accessToken·refreshToken 존재 |
| 비밀번호 불일치 | 401, `M004` |
| 없는 이메일 | 401, `M004` (메시지가 위와 동일) |
| 탈퇴 회원 로그인 | 401 |
| 토큰 없이 `/members/me` | 401, `A001` |
| 유효 토큰으로 `/members/me` | 200 |
| 로그인 응답 헤더 | `Set-Cookie` 세션 쿠키 없음 |

---

### M-07 토큰 재발급과 로그아웃

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-06 |
| 참조 | [../requirements/member.md §1](../requirements/member.md) (M-05, M-06), [../domain-model.md §2.2](../domain-model.md), [../security.md §4](../security.md) |

**산출물**
- `auth/entity/RefreshToken.java`
- `auth/repository/RefreshTokenRepository.java`
- `V3__create_refresh_token.sql`
- `AuthService` 확장 (`reissue`, `logout`), `AuthController` 확장

**완료 기준**
- [ ] 로그인 시 Refresh Token이 DB에 저장된다 (회원당 1행, 재로그인 시 갱신)
- [ ] `POST /api/v1/auth/reissue`가 새 Access·Refresh Token을 반환한다 (Rotation)
- [ ] **재발급 후 이전 Refresh Token은 사용할 수 없다**
- [ ] DB에 없는 Refresh Token으로 재발급 시 401 `A002`
- [ ] 만료된 Refresh Token으로 재발급 시 401 `A003`
- [ ] `POST /api/v1/auth/logout`이 DB의 Refresh Token을 삭제한다
- [ ] 로그아웃 후 그 Refresh Token으로 재발급할 수 없다

**검증** — `RefreshTokenRepositoryTest`, `AuthServiceTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 로그인 2회 | `refresh_token` 행이 1개 (갱신됨) |
| 정상 재발급 | 200, 새 토큰 반환 |
| 재발급 후 이전 토큰 재사용 | 401, `A002` |
| DB에 없는 토큰으로 재발급 | 401, `A002` |
| 만료 토큰으로 재발급 | 401, `A003` |
| 로그아웃 후 재발급 | 401, `A002` |

---

### M-08 내 정보 조회·수정

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-07 |
| 참조 | [../requirements/member.md §1 §4](../requirements/member.md) (M-07, M-08), [../api-contract.md §2.2](../api-contract.md), [../architecture.md §4.2](../architecture.md) |

**산출물**
- `member/dto/MemberUpdateRequest.java`, `MemberUpdateResponse.java` (회원 정보 + 새 accessToken)
- `MemberService` 확장, `MemberController` 확장

**완료 기준**
- [ ] `GET /api/v1/members/me`가 본인 정보를 반환한다 (`password` 제외)
- [ ] `PATCH /api/v1/members/me`가 닉네임을 변경한다
- [ ] **닉네임 변경 응답에 새 Access Token이 포함된다**
- [ ] 새 토큰의 `nickname` Claim이 변경된 닉네임이다
- [ ] 중복 닉네임으로 변경 시 409 `M003`
- [ ] 자기 현재 닉네임으로 변경 시 중복 오류가 나지 않는다

**검증** — `MemberServiceTest`, `MemberControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 내 정보 조회 | 200, `password` 키 없음 |
| 닉네임 변경 | 200, DB 반영됨 |
| 변경 응답의 새 토큰 Claim | `nickname`이 새 값 |
| 타인 닉네임으로 변경 | 409, `M003` |
| 자기 현재 닉네임으로 변경 | 200 (중복 오류 아님) |
| 닉네임 1자 | 400, `C001` |

---

### M-09 비밀번호 변경과 탈퇴

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-08 |
| 참조 | [../requirements/member.md §1 §3](../requirements/member.md) (M-09, M-10), [../security.md §7](../security.md) |

**산출물**
- `member/dto/PasswordChangeRequest.java`, `WithdrawRequest.java`
- `MemberService` 확장, `MemberController` 확장

**완료 기준**
- [ ] `PATCH /api/v1/members/me/password`가 204를 반환한다
- [ ] 현재 비밀번호 불일치 시 400 `M005`
- [ ] 새 비밀번호가 BCrypt로 해싱되어 저장된다
- [ ] **비밀번호 변경 시 Refresh Token이 삭제된다**
- [ ] `DELETE /api/v1/members/me`가 `deleted = true`로 변경한다 (행 삭제 아님)
- [ ] 탈퇴 시 Refresh Token이 삭제된다
- [ ] 탈퇴 회원의 이메일로 재가입할 수 없다 (409 `M002`)

**검증** — `MemberServiceTest`, `MemberControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 비밀번호 변경 | 204, 새 비밀번호로 로그인 가능 |
| 현재 비밀번호 불일치 | 400, `M005` |
| 변경 후 `refresh_token` 행 | 삭제됨 |
| 새 비밀번호 형식 오류 | 400, `C001` |
| 정상 탈퇴 | 204, `deleted = true`, 행 존재 |
| 탈퇴 후 로그인 | 401 |
| 탈퇴 회원 이메일로 재가입 | 409, `M002` |
| 탈퇴 시 `refresh_token` 행 | 삭제됨 |

---

### M-10 회원 프로필 조회와 내부 API

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-09 |
| 참조 | [../requirements/member.md §1 §5](../requirements/member.md) (M-11, M-12), [../api-contract.md §4](../api-contract.md), [../security.md §6](../security.md) |

**산출물**
- `member/dto/MemberProfileResponse.java`
- `internal/dto/MemberBulkRequest.java`, `MemberSummaryResponse.java`
- `internal/controller/InternalMemberController.java`
- `global/security/InternalApiKeyFilter.java`
- `SecurityConfig` 갱신 (`/internal/**` 경로)

**완료 기준**
- [ ] `GET /api/v1/members/{id}`가 공개 정보(닉네임, 가입일)만 반환한다. 이메일 미포함
- [ ] `POST /internal/v1/members/bulk`가 [../api-contract.md §4](../api-contract.md) 형식으로 응답한다
- [ ] 탈퇴 회원은 `deleted: true`, 닉네임 `"탈퇴한 회원"`으로 반환한다
- [ ] 내부 API 응답에 이메일·비밀번호가 없다
- [ ] `X-Internal-Api-Key` 없이 호출하면 거부된다
- [ ] 내부 API 키가 환경변수로 주입된다

**검증** — `InternalMemberControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 벌크 조회 (3건) | 200, 3건 반환 |
| 존재하지 않는 id 포함 | 해당 id는 결과에서 제외 |
| 탈퇴 회원 포함 | `deleted: true`, 닉네임 `"탈퇴한 회원"` |
| 응답 본문 | `email`, `password` 키 없음 |
| API 키 없이 호출 | 401 또는 403 |
| 잘못된 API 키 | 401 또는 403 |
| 회원 프로필 조회 | 200, `email` 키 없음 |

---

### M-11 마무리

| | |
| --- | --- |
| 저장소 | `yuno110/member` |
| 의존 | M-10 |
| 참조 | [../nfr.md](../nfr.md), [../tech-stack.md §5](../tech-stack.md) |

**산출물**
- `README.md` 갱신 (실행 방법, 환경변수 목록)
- Actuator 설정 (`/actuator/health`만 노출)
- 운영 프로파일에서 Swagger 비활성화 설정
- `application-prod.yml`

**완료 기준**
- [ ] `README.md`에 로컬 실행 절차와 필요한 환경변수가 모두 적혀 있다
- [ ] `/actuator/health`가 동작하고 그 외 actuator 엔드포인트는 노출되지 않는다
- [ ] `prod` 프로파일에서 Swagger UI가 비활성화된다
- [ ] `prod` 프로파일에서 SQL 로그가 꺼진다
- [ ] 전체 테스트가 통과한다 (`./gradlew test`)
- [ ] 커밋된 파일에 비밀 값이 없다

**검증**

| 케이스 | 기대 결과 |
| --- | --- |
| `/actuator/health` | 200, `{"status":"UP"}` |
| `/actuator/env` | 404 또는 403 |
| `prod` 프로파일로 `/swagger-ui.html` | 404 |
| `git log -p` 에서 키·비밀번호 검색 | 없음 |

## 3. board-service 작업 항목

### B-01 프로젝트 스캐폴딩

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | 없음 |
| 병렬 | M-01과 동시 진행 가능 |
| 참조 | [../tech-stack.md §1 §3](../tech-stack.md), [../conventions.md §1.2](../conventions.md) |

**산출물**
- `build.gradle`, `settings.gradle`, Gradle Wrapper
- `src/main/java/com/example/board/BoardApplication.java`
- `application.yml`, `application-local.yml`
- `global/config/QuerydslConfig.java` (`JPAQueryFactory` 빈)
- `.gitignore`

**완료 기준**
- [ ] `./gradlew build`가 성공한다
- [ ] 8082 포트에 기동된다
- [ ] QueryDSL Q타입이 생성되고 `.gitignore`에 생성 경로가 있다
- [ ] DB 접속 정보가 환경변수로 외부화되어 있다
- [ ] 시간대가 `Asia/Seoul`로 명시 설정되어 있다

**검증** — `BoardApplicationTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 컨텍스트 로딩 | 예외 없이 기동 |
| `JPAQueryFactory` 빈 | 주입됨 |
| `TimeZone.getDefault()` | `Asia/Seoul` |

---

### B-02 공통 기반

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-01 |
| 참조 | [../api-contract.md §6 §7.1 §7.3](../api-contract.md), [../domain-model.md §1.1](../domain-model.md), [../conventions.md §6 §7](../conventions.md) |

**산출물**
- `global/common/ApiResponse.java`, `ErrorResponse.java`, `PageResponse.java`
- `global/common/BaseTimeEntity.java`
- `global/error/ErrorCode.java` (C001~C005, A001~A004, **P001, P002, CM001, CM002, S001**)
- `global/error/BusinessException.java`, `GlobalExceptionHandler.java`
- `global/config/JpaConfig.java`, `SwaggerConfig.java`

**M-02와 같은 파일을 만들되 `ErrorCode`는 board 전용 코드를 쓴다.** `ApiResponse` 등 복제 대상은 정본 주석을 남긴다.

**완료 기준**
- [ ] `ApiResponse`, `ErrorResponse`, `PageResponse`, `BaseTimeEntity`가 member-service와 **구조가 동일**하다
- [ ] `ErrorCode`에 member 전용 코드(`M0xx`)가 **없다**
- [ ] `ErrorCode`의 코드·HTTP·메시지가 [../api-contract.md §7.1 §7.3](../api-contract.md)과 일치한다
- [ ] 복제 파일 상단에 정본 주석이 있다
- [ ] `/swagger-ui.html`이 열린다

**검증** — `GlobalExceptionHandlerTest` (`@WebMvcTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| `BusinessException(P001)` | 404, `error.code = "P001"` |
| `BusinessException(P002)` | 403, `P002` |
| `@Valid` 실패 | 400, `C001`, `fieldErrors` 존재 |
| 성공 응답 | `success = true`, `error = null` |
| 예상치 못한 예외 | 500, `C005`, 스택트레이스 없음 |

---

### B-03 JWT 검증과 인증 컨텍스트

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-02 |
| 병렬 | **M-05를 기다리지 않는다.** 계약이 문서에 확정되어 있다 |
| 참조 | [../api-contract.md §5](../api-contract.md), [../tech-stack.md §2.1](../tech-stack.md), [../security.md §2 §5](../security.md) |

**산출물**
- `global/security/LoginMember.java` (record: `memberId`, `nickname`, `role`)
- `global/security/RoleClaimConverter.java`
- `global/security/CurrentMemberArgumentResolver.java`, `@CurrentMember`
- `global/config/SecurityConfig.java`
- `src/main/resources/jwt-public.pem` (**테스트용 키 페어의 공개키**)
- `src/test/java/.../TestTokenFactory.java` (테스트용 토큰 생성기)

**Spring Security `oauth2-resource-server`를 사용한다. JWT 필터를 직접 만들지 않는다.**

테스트용 키 페어를 만들어 자체 검증한다. 실제 member-service의 공개키로 교체하는 것은 I-01에서 한다.

**완료 기준**
- [ ] [../api-contract.md §5](../api-contract.md) 스펙의 토큰에서 `memberId`, `nickname`, `role`을 추출한다
- [ ] 서명이 잘못된 토큰은 401 `A002`
- [ ] 만료된 토큰은 401 `A003`
- [ ] 토큰 없이 보호 경로 접근 시 401 `A001`
- [ ] `role` claim이 `GrantedAuthority`로 변환된다
- [ ] JWT 검증 필터를 직접 구현하지 않았다 (Spring 표준 사용)
- [ ] 세션이 생성되지 않는다

**검증** — `JwtAuthenticationTest` (`@SpringBootTest` + MockMvc)

| 케이스 | 기대 결과 |
| --- | --- |
| 유효 토큰으로 보호 경로 | 200, `LoginMember`에 Claim 값 주입 |
| 토큰 없이 보호 경로 | 401, `A001` |
| 서명 변조 토큰 | 401, `A002` |
| 만료 토큰 | 401, `A003` |
| `role = ADMIN` 토큰 | `ROLE_ADMIN` 권한 보유 |
| 비로그인 허용 경로 | 토큰 없이 200 |

---

### B-04 Post 엔티티와 스키마

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-02 |
| 참조 | [../domain-model.md §3.1 §3.3](../domain-model.md), [../requirements/board.md §3](../requirements/board.md) |

**산출물**
- `post/entity/Post.java`
- `post/repository/PostRepository.java`
- `db/migration/V1__create_post.sql`

**완료 기준**
- [ ] 기동 시 Flyway가 `post` 테이블을 생성한다
- [ ] 컬럼이 [../domain-model.md §3.1](../domain-model.md)과 일치한다 (`writer_id`, `writer_nickname` 포함)
- [ ] **`writer_id`에 FK 제약이 없다**
- [ ] `content`가 `TEXT` 타입이다
- [ ] `idx_post_created_at`, `idx_post_writer_id`, `idx_post_title` 인덱스가 있다
- [ ] `view_count`, `comment_count` 기본값이 0이다
- [ ] Entity에 `@Setter`·`@Data`가 없다

**검증** — `PostRepositoryTest` (`@DataJpaTest`)

| 케이스 | 기대 결과 |
| --- | --- |
| 저장 후 조회 | 모든 필드 일치 |
| 존재하지 않는 `writer_id`로 저장 | **성공** (FK 제약 없음) |
| 저장 시 | `viewCount = 0`, `commentCount = 0`, `deleted = false` |
| 10,000자 content 저장 | 성공 |
| 저장 시 | `createdAt`, `updatedAt` null 아님 |

`writer_id` FK 제약이 없다는 것을 테스트로 고정한다. 나중에 누군가 FK를 추가하면 이 테스트가 깨진다.

---

### B-05 게시글 작성·상세 조회

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-03, B-04 |
| 참조 | [../requirements/board.md §1 §3 §4](../requirements/board.md) (P-01, P-04, P-05), [../api-contract.md §3 §8.3](../api-contract.md) |

**산출물**
- `post/dto/PostCreateRequest.java`, `PostResponse.java`, `PostDetailResponse.java`
- `post/service/PostService.java`
- `post/controller/PostController.java`

**완료 기준**
- [ ] `POST /api/v1/posts`가 201을 반환한다
- [ ] **`writer_id`, `writer_nickname`을 JWT Claim에서 가져온다.** 요청 본문의 값을 쓰지 않는다
- [ ] 요청 본문에 `writerId`를 넣어도 무시된다
- [ ] `GET /api/v1/posts/{id}`가 상세를 반환한다 (비로그인 허용)
- [ ] 상세 조회 시 `view_count`가 1 증가한다
- [ ] 삭제된 게시글 조회 시 404 `P001`
- [ ] 없는 id 조회 시 404 `P001`
- [ ] 제목 201자·내용 10,001자는 400 `C001`

**검증** — `PostServiceTest`, `PostControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 정상 작성 | 201, DB 저장됨 |
| 저장된 `writer_id`/`writer_nickname` | JWT Claim 값과 일치 |
| 요청 본문에 `writerId: 999` 전달 | 저장된 값은 Claim의 `sub` |
| 토큰 없이 작성 | 401, `A001` |
| 상세 조회 (비로그인) | 200 |
| 상세 조회 2회 | `viewCount`가 2 |
| 없는 id | 404, `P001` |
| 삭제된 게시글 | 404, `P001` |
| 제목 201자 | 400, `C001` |
| 제목 공백만 | 400, `C001` |

---

### B-06 게시글 목록과 QueryDSL 검색

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-05 |
| 참조 | [../requirements/board.md §1 §6](../requirements/board.md) (P-02, P-03), [../api-contract.md §3.1 §6.1](../api-contract.md), [../nfr.md §1](../nfr.md) |

**산출물**
- `post/dto/PostSearchCondition.java`, `SearchType.java`, `PostSortType.java`
- `post/repository/PostQueryRepository.java` (QueryDSL)
- `PostService`·`PostController` 확장

**완료 기준**
- [ ] `GET /api/v1/posts`가 페이징 응답을 반환한다 ([../api-contract.md §6.1](../api-contract.md) 형식)
- [ ] 기본 `size`가 10이고, 51을 요청하면 50으로 절삭된다
- [ ] `sort=latest`(최신순), `sort=views`(조회순)가 동작한다
- [ ] 삭제된 게시글이 목록에서 제외된다
- [ ] 4가지 `searchType`이 모두 동작한다
- [ ] `keyword`가 없으면 전체 목록을 반환한다
- [ ] `searchType`만 있고 `keyword`가 없으면 400 `C001`
- [ ] **목록 조회 시 member-service를 호출하지 않는다**
- [ ] 정렬 파라미터로 임의 컬럼명을 넣을 수 없다 (Enum 화이트리스트)

**검증** — `PostQueryRepositoryTest` (`@DataJpaTest`), `PostControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 15건 저장 후 목록 조회 | 10건 반환, `totalElements = 15` |
| `size=51` | 50건 이하 반환 |
| `sort=latest` | `createdAt` 내림차순 |
| `sort=views` | `viewCount` 내림차순 |
| 삭제 게시글 포함 상태 | 삭제분 제외됨 |
| `searchType=TITLE&keyword=공지` | 제목에 "공지" 포함분만 |
| `searchType=CONTENT` | 내용 기준 |
| `searchType=TITLE_CONTENT` | 제목 OR 내용 |
| `searchType=WRITER&keyword=홍길동` | `writer_nickname` 기준 |
| `keyword` 없이 조회 | 전체 반환 |
| `searchType=TITLE` 만 전달 | 400, `C001` |
| `sort=password` | 400 |

---

### B-07 게시글 수정·삭제와 권한

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-06 |
| 참조 | [../requirements/board.md §1 §5 §7](../requirements/board.md) (P-06, P-07), [../security.md §5](../security.md) |

**산출물**
- `post/dto/PostUpdateRequest.java`
- `PostService` 확장 (`update`, `delete`, `validateOwner`)
- `PostController` 확장

**완료 기준**
- [ ] `PUT /api/v1/posts/{id}`를 작성자 본인만 수정할 수 있다
- [ ] 타인이 수정 시 403 `P002`
- [ ] **ADMIN도 수정할 수 없다** (403 `P002`)
- [ ] `DELETE /api/v1/posts/{id}`를 작성자 본인과 ADMIN이 삭제할 수 있다
- [ ] 삭제는 Soft Delete다 (행이 남고 `deleted = true`)
- [ ] 소유자 검증이 Service 계층에 있다
- [ ] 수정 시 `writer_id`, `writer_nickname`이 바뀌지 않는다

**검증** — `PostServiceTest`, `PostControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 본인 글 수정 | 200, 반영됨 |
| 타인 글 수정 | 403, `P002` |
| **ADMIN이 타인 글 수정** | **403, `P002`** |
| 수정 후 `writer_id` | 변경 없음 |
| 본인 글 삭제 | 204, `deleted = true`, 행 존재 |
| ADMIN이 타인 글 삭제 | 204 |
| 타인(일반) 글 삭제 | 403, `P002` |
| 없는 글 수정 | 404, `P001` |
| 토큰 없이 수정 | 401, `A001` |

---

### B-08 댓글

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-07 |
| 참조 | [../requirements/board.md §2 §5](../requirements/board.md) (C-01~C-04), [../domain-model.md §3.2 §3.3 §4](../domain-model.md) |

**산출물**
- `comment/entity/Comment.java`
- `comment/repository/CommentRepository.java`
- `comment/dto/*`, `comment/service/CommentService.java`, `comment/controller/CommentController.java`
- `db/migration/V2__create_comment.sql`

**완료 기준**
- [ ] `comment` 테이블이 [../domain-model.md §3.2](../domain-model.md)와 일치하고 `idx_comment_post_id`가 있다
- [ ] 댓글 작성 시 `post.comment_count`가 1 증가한다
- [ ] 댓글 삭제 시 `comment_count`가 1 감소한다
- [ ] **`comment_count`가 음수가 되지 않는다**
- [ ] 작성자 본인만 수정, 본인·ADMIN이 삭제할 수 있다
- [ ] 삭제는 Soft Delete다
- [ ] **게시글 삭제 시 하위 댓글도 `deleted = true`가 된다**
- [ ] 작성자 정보를 JWT Claim에서 가져온다
- [ ] 없는 게시글에 댓글 작성 시 404 `P001`

**검증** — `CommentServiceTest`, `CommentControllerTest`

| 케이스 | 기대 결과 |
| --- | --- |
| 댓글 작성 | 201, `comment_count = 1` |
| 댓글 3개 작성 | `comment_count = 3` |
| 댓글 1개 삭제 | `comment_count = 2` |
| 같은 댓글 2회 삭제 시도 | `comment_count`가 음수 안 됨 |
| 목록 조회 | 등록순, 기본 20건 |
| 본인 댓글 수정 | 200 |
| 타인 댓글 수정 | 403, `CM002` |
| ADMIN이 타인 댓글 수정 | 403, `CM002` |
| ADMIN이 타인 댓글 삭제 | 204 |
| **게시글 삭제** | **하위 댓글 전부 `deleted = true`** |
| 없는 게시글에 댓글 | 404, `P001` |
| 501자 댓글 | 400, `C001` |

---

### B-09 내가 쓴 글과 마무리

| | |
| --- | --- |
| 저장소 | `yuno110/board` |
| 의존 | B-08 |
| 참조 | [../requirements/board.md §1](../requirements/board.md) (P-08), [../nfr.md](../nfr.md) |

**산출물**
- `PostService`·`PostController` 확장 (내가 쓴 글)
- `README.md` 갱신
- Actuator·운영 프로파일 설정

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
| 토큰 없이 호출 | 401, `A001` |
| 목록 조회 쿼리 수 | 게시글 수와 무관하게 일정 (N+1 없음) |
| `/actuator/env` | 404 또는 403 |

## 4. 다음 단계

M-11과 B-09가 모두 `done`이 되면 [integration.md](integration.md)로 넘어간다.
