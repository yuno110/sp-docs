---
title: 코드 컨벤션
type: spec
status: rule
version: v1
updated: 2026-09-11
read_when: "코드를 작성하거나 리뷰할 때. 패키지를 새로 만들 때"
related: [tech-stack.md, adr/0007-shared-code-policy.md, process/dev-workflow.md]
---
# 코드 컨벤션

## 1. 패키지 구조

도메인형으로 나눈다. 계층형(controller/service/repository를 최상위로)으로 두지 않는다.

### 1.1 member-service

```
com.example.member
├── MemberApplication.java
├── global
│   ├── config          # SecurityConfig, JpaConfig, SwaggerConfig, WebConfig(CORS)
│   ├── common          # BaseTimeEntity, ApiResponse, PageResponse
│   ├── error           # ErrorCode, BusinessException, GlobalExceptionHandler
│   └── security        # JwtTokenProvider(서명), @LoginMember
├── auth
│   ├── controller / service / repository / entity / dto
├── member
│   ├── controller / service / repository / entity / dto
└── internal
    └── controller      # InternalMemberController (/internal/v1/**)
```

`auth`와 `member`의 책임 구분과 의존 방향은 [adr/0006](adr/0006-auth-inside-member-service.md)을 본다. **의존 방향은 `auth → member` 단방향이다.** `member` 패키지는 `auth`를 참조하지 않는다.

**예외 하나**: `member`는 비밀번호 변경·탈퇴 시의 토큰 무효화에 한해 `auth.repository.RefreshTokenRepository`를 참조할 수 있다. 범위와 근거는 [adr/0006 §예외](adr/0006-auth-inside-member-service.md)에 있다. 그 외의 `auth` 참조는 금지한다.

### 1.2 board-service

```
com.example.board
├── BoardApplication.java
├── global
│   ├── config          # SecurityConfig, JpaConfig, QuerydslConfig, SwaggerConfig, WebConfig
│   ├── common          # BaseTimeEntity, ApiResponse, PageResponse
│   ├── error           # ErrorCode, BusinessException, GlobalExceptionHandler
│   └── security        # RoleClaimConverter, LoginMember(record), @CurrentMember
├── post
│   ├── controller / service / repository / entity / dto
├── comment
│   ├── controller / service / repository / entity / dto
└── client
    └── MemberClient    # 내부 API 호출 (2차)
```

## 2. Entity

- 기본 생성자는 `@NoArgsConstructor(access = AccessLevel.PROTECTED)`
- 생성은 `@Builder`
- **`@Data`, `@Setter`, 연관관계를 포함한 `@ToString` 금지.** 무한 루프와 의도치 않은 변경을 막기 위해서다
- `equals`/`hashCode`는 `id` 기준으로 직접 구현한다
- 도메인 로직은 Entity 메서드로 둔다 (`post.update(...)`, `member.changePassword(...)`)
- Enum은 `@Enumerated(EnumType.STRING)`

## 3. DTO

- `record`를 우선 사용한다
- **Entity를 Controller 밖으로 노출하지 않는다.** 반드시 DTO로 변환한다
- 원격 호출 결과 DTO는 소비 서비스가 자체 정의한다. 제공 서비스의 DTO 클래스를 공유하지 않는다

## 4. 의존성 주입

생성자 주입만 사용한다.

```java
@Service
@RequiredArgsConstructor
public class PostService {
    private final PostRepository postRepository;
}
```

필드 주입(`@Autowired` 필드), 세터 주입 금지.

## 5. 트랜잭션

- 경계는 Service에 둔다. Controller·Repository에 `@Transactional`을 붙이지 않는다
- 조회는 `@Transactional(readOnly = true)`
- **트랜잭션 안에서 다른 서비스를 호출하지 않는다**([architecture.md §5](architecture.md))

## 6. 예외 처리

- `BusinessException(ErrorCode)`를 던진다
- `@RestControllerAdvice`의 `GlobalExceptionHandler`에서 일괄 변환한다
- 에러 코드는 [api-contract.md §7](api-contract.md)이 정본이다. 코드를 추가하려면 그 문서를 먼저 개정한다
- 응답에 스택트레이스·SQL·내부 호스트명을 넣지 않는다

## 7. 공통 코드 정책

두 서비스가 같은 코드를 갖는 것은 **복제**로 처리한다. 공용 라이브러리 모듈을 만들지 않는다. 근거와 재검토 조건은 [adr/0007](adr/0007-shared-code-policy.md)에 있다.

### 7.1 복제 대상 (약 75줄)

| 항목 | 정본 |
| --- | --- |
| `ApiResponse`, `ErrorResponse` | [api-contract.md §6](api-contract.md) |
| `PageResponse` | [api-contract.md §6.1](api-contract.md) |
| `BaseTimeEntity` | [domain-model.md §1.1](domain-model.md) |
| `BusinessException` | 이 문서 §6 |

복제본 파일 상단에 정본 위치를 주석으로 남긴다.

```java
// 정본: simple-docs/api-contract.md §6
// 변경 시 두 서비스를 함께 고친다.
public record ApiResponse<T>(boolean success, T data, ErrorResponse error) { }
```

### 7.2 복제하지 않는 것

- `ErrorCode` enum — 서비스마다 코드가 다르다. 공유하면 board 코드가 member에 들어간다
- `GlobalExceptionHandler` — 서비스별 `ErrorCode`에 의존한다
- **JWT 검증·발급 코드** — 직접 만들지 않고 Spring 표준을 쓴다([tech-stack.md §2](tech-stack.md))

## 8. 로깅

- 비밀번호·토큰·개인키를 로그에 남기지 않는다
- 로컬 프로파일만 SQL 로그를 켠다. 운영은 끈다

## 9. 테스트

- 테스트 클래스명은 `<대상>Test`
- 메서드명은 한글 또는 `should_...` 형식으로 무엇을 검증하는지 드러낸다
- 작성 시점과 검증 절차는 [process/dev-workflow.md](process/dev-workflow.md)를 따른다

## 10. 커밋

```
<type>(<scope>): <요약>
```

- `type`: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`
- `scope`: `member`, `auth`, `post`, `comment`, `global`, `docs`
- 본문에는 무엇을 왜 바꿨는지 적는다. 비밀 값·개인정보를 넣지 않는다

예: `feat(post): 게시글 목록 QueryDSL 동적 검색 추가`
