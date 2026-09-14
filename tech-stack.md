---
title: 기술 스택과 로컬 환경
type: spec
status: frozen
version: v1
updated: 2026-09-11
read_when: "의존성 버전을 정하거나, 프로젝트를 스캐폴딩하거나, 로컬 환경을 구성할 때"
related: [conventions.md, adr/0005-no-docker-in-mvp.md, adr/0007-shared-code-policy.md]
---
# 기술 스택과 로컬 환경

버전의 정본은 이 문서다. 다른 문서의 서술을 버전의 근거로 쓰지 않는다.

## 1. 공통 스택

두 서비스가 동일하다.

| 구분 | 기술 | 버전 |
| --- | --- | --- |
| Language | Java | 21 (LTS) |
| Framework | Spring Boot | **3.5.16** (고정) |
| Build | Gradle (Groovy DSL) + Wrapper | 9.7.1 |
| ORM | Spring Data JPA (Hibernate 6.x) | Boot BOM |
| 보일러플레이트 | Lombok | Boot BOM |
| 동적 쿼리 | QueryDSL (jakarta) | 5.1.0 |
| 보안 | Spring Security | 6.x (Boot BOM) |
| JWT | Spring Security OAuth2 Resource Server / Jose | Boot BOM |
| 검증 | Jakarta Bean Validation | Boot BOM |
| API 문서 | springdoc-openapi (webmvc-ui) | 2.8.x |
| DB | MySQL | 8.0 |
| DB (테스트) | H2 (MySQL 호환 모드) | Boot BOM |
| 마이그레이션 | Flyway | Boot BOM |
| 테스트 | JUnit 5, Spring Boot Test, AssertJ | Boot BOM |
| 모니터링 | Spring Boot Actuator | Boot BOM |

**버전 확정**: Boot 버전은 **3.5.16으로 고정**한다. Boot BOM이 관리하지 않는 서드파티(QueryDSL, springdoc)도 `build.gradle`에 버전을 명시 고정한다.

### 1.1 프로젝트 생성 — Initializr는 3.x를 주지 않는다

**start.spring.io는 Boot 4.0.0 이상만 제공한다.** `bootVersion=3.5.16`으로 요청하면 거부된다.

```
400 Bad Request — Invalid Spring Boot version '3.5.16',
                  Spring Boot compatibility range is >=4.0.0
```

3.5.16 자체는 Maven Central에 있으므로 사용에는 문제가 없다. **4.x로 골격을 받은 뒤 버전을 내린다.**

1. Initializr에서 `bootVersion=4.0.8`, `type=gradle-project`, `javaVersion=21`로 생성한다
2. `build.gradle`의 `id 'org.springframework.boot' version` 을 `3.5.16`으로 바꾼다
3. **의존성을 3.x 이름으로 다시 쓴다.** Boot 4는 스타터 이름이 다르다

| Boot 4 (생성 결과) | Boot 3.5 (써야 할 것) |
| --- | --- |
| `spring-boot-starter-webmvc` | `spring-boot-starter-web` |
| `spring-boot-starter-webmvc-test` | `spring-boot-starter-test` |

**Gradle Wrapper는 그대로 둔다.** Initializr가 생성하는 9.7.1이 Boot 3.5.16과 정상 동작한다 (§3.1 전체 의존성으로 `./gradlew build` 성공 확인).

> Boot 4 전환은 1차 완료 후 2차에서 다룬다. 지금 올리면 Spring Security 7, Jakarta EE 11, springdoc 3.x까지 연쇄 변경이 필요하고 QueryDSL 5.1.0 호환성도 미검증이다.

**Spring Cloud를 도입하지 않는다.** 서비스 간 호출은 Boot 내장 `RestClient`로 충분하며, Cloud 릴리스 트레인은 Boot 버전과 강하게 결합되어 업그레이드 부담을 만든다.

## 2. JWT 처리 — 직접 구현하지 않는다

RS256을 쓰기로 했으므로([adr/0004](adr/0004-rs256-over-hs256.md)) Spring Security 표준 기능을 사용한다. JWT 필터·Provider·검증 로직을 손으로 만들지 않는다. 근거는 [adr/0007](adr/0007-shared-code-policy.md)에 있다.

### 2.1 board-service (검증)

```groovy
implementation 'org.springframework.boot:spring-boot-starter-oauth2-resource-server'
```

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          public-key-location: classpath:jwt-public.pem
```

이것으로 서명 검증·만료 확인·`SecurityContext` 주입이 끝난다. 직접 작성할 것은 `role` claim을 `GrantedAuthority`로 바꾸는 컨버터뿐이다.

> 의존성 이름에 `oauth2`가 붙지만 OAuth2 인가 서버가 필요한 것이 아니다. 표준 JWT(RFC 7519) 검증기 부분만 사용한다.

### 2.2 member-service (발급)

```groovy
implementation 'org.springframework.security:spring-security-oauth2-jose'
```

`NimbusJwtEncoder`로 서명한다. jjwt 라이브러리는 사용하지 않는다.

## 3. Gradle 의존성

### 3.1 두 서비스 공통

아래 전체 조합으로 Boot 3.5.16 + Gradle 9.7.1에서 `./gradlew build` 성공을 확인했다.

```groovy
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-validation'
    implementation 'org.springframework.boot:spring-boot-starter-security'
    implementation 'org.springframework.boot:spring-boot-starter-actuator'

    // Lombok (annotationProcessor 선언은 QueryDSL보다 먼저)
    compileOnly 'org.projectlombok:lombok'
    annotationProcessor 'org.projectlombok:lombok'
    testCompileOnly 'org.projectlombok:lombok'
    testAnnotationProcessor 'org.projectlombok:lombok'

    // QueryDSL
    implementation 'com.querydsl:querydsl-jpa:5.1.0:jakarta'
    annotationProcessor 'com.querydsl:querydsl-apt:5.1.0:jakarta'
    annotationProcessor 'jakarta.annotation:jakarta.annotation-api'
    annotationProcessor 'jakarta.persistence:jakarta.persistence-api'

    // API Docs
    implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:2.8.5'

    // DB / Migration
    runtimeOnly 'com.mysql:mysql-connector-j'
    runtimeOnly 'com.h2database:h2'
    implementation 'org.flywaydb:flyway-core'
    implementation 'org.flywaydb:flyway-mysql'

    // Test
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.security:spring-security-test'
}
```

### 3.2 서비스별 추가

| 서비스 | 추가 |
| --- | --- |
| member | `org.springframework.security:spring-security-oauth2-jose` (서명) |
| board | `org.springframework.boot:spring-boot-starter-oauth2-resource-server` (검증) |

QueryDSL Q타입 생성 경로(`build/generated/sources/annotationProcessor`)를 `.gitignore`에 넣는다.

## 4. 로컬 환경

**1차는 Docker를 사용하지 않는다**([adr/0005](adr/0005-no-docker-in-mvp.md)). MySQL은 로컬에 직접 설치하고 서비스는 IDE 또는 `gradlew bootRun`으로 실행한다.

### 4.1 MySQL 설치 후 1회

```sql
CREATE DATABASE sp_member DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE DATABASE sp_board  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

SET PERSIST time_zone = '+09:00';
```

**시간대는 `SET PERSIST`로 설정한다.** `my.ini`에 `default-time-zone`을 적는 것과 효과가 같으면서 제약이 없다.

| | `my.ini` 수정 | `SET PERSIST` |
| --- | --- | --- |
| 관리자 권한 | 필요 | 불필요 |
| 서비스 재시작 | 필요 | 불필요 (즉시 적용) |
| 재시작 후 유지 | 유지 | 유지 |

MySQL 8.0이 데이터 디렉터리의 `mysqld-auto.cnf`에 기록하고, 이 파일은 `my.ini`보다 나중에 읽혀 우선한다.

**확인**

```sql
SELECT @@global.time_zone, NOW();
SELECT variable_name, variable_value FROM performance_schema.persisted_variables;
```

`@@global.time_zone`이 `+09:00`이고 `persisted_variables`에 `time_zone` 행이 있어야 한다. 후자가 비어 있으면 현재 세션에만 적용된 것이라 서버 재시작 시 풀린다.

> 데이터 디렉터리(`Data/`)는 ACL로 보호되어 관리자가 아니면 읽을 수 없다. 설정 확인은 파일이 아니라 위 쿼리로 한다.

### 4.2 RSA 키 페어 생성 (1회)

```bash
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out private.pem
openssl rsa -in private.pem -pubout -out public.pem
```

배포 방식과 보관 규칙은 [security.md §3](security.md)를 본다.

### 4.3 설정 외부화 (필수)

환경 의존 값은 기본값과 함께 환경변수로 외부화한다. 2차 컨테이너 전환을 코드 변경 없이 하기 위해서이며, 보안 요구와도 일치한다.

```yaml
spring:
  datasource:
    url: ${DB_URL:jdbc:mysql://localhost:3306/sp_member?serverTimezone=Asia/Seoul&characterEncoding=UTF-8}
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD}
member-service:
  url: ${MEMBER_SERVICE_URL:http://localhost:8081}
```

**비밀 값(JWT 개인키, DB 비밀번호)은 기본값을 두지 않는다.** `${DB_PASSWORD}`처럼 기본값 없이 쓴다. 없으면 기동이 실패해야 한다.

> Spring은 해석되지 않은 placeholder를 리터럴 문자열로 남긴다. 그래서 `DB_PASSWORD` 미설정 시 오류 메시지가 `Access denied for user 'root'@'localhost' (using password: YES)`로 나온다. **비밀번호가 틀린 게 아니라 환경변수가 없는 것**이니 먼저 §4.3.1을 확인한다.

#### 4.3.1 로컬 환경변수 설정 (1회)

애플리케이션은 `DB_PASSWORD` 없이 기동하지 않는다. 개발 머신에 **사용자 수준 환경변수**로 한 번 등록한다.

```powershell
[Environment]::SetEnvironmentVariable('DB_PASSWORD', '<MySQL root 비밀번호>', 'User')
```

등록 후 **새로 여는 터미널·IDE부터** 적용된다. 이미 열려 있는 프로세스는 갱신되지 않으므로 다시 열어야 한다.

확인:

```powershell
[Environment]::GetEnvironmentVariable('DB_PASSWORD','User')
```

`JWT_PRIVATE_KEY`도 같은 방식으로 등록한다(M-04부터 필요). 값 생성은 §4.2를 본다.

### 4.4 실행

| 서비스 | 명령 | 주소 |
| --- | --- | --- |
| member | `./gradlew bootRun --args='--spring.profiles.active=local'` | `:8081` |
| board | 동일 | `:8082` |

- Swagger UI: `/swagger-ui.html` (운영 프로파일에서는 비활성화)
- 헬스체크: `/actuator/health`

## 5. 시간대 — KST 통일

전 구성요소를 `Asia/Seoul`로 맞춘다. 한쪽만 UTC면 작성 시각이 9시간 어긋난다.

| 계층 | 설정 |
| --- | --- |
| JVM | `-Duser.timezone=Asia/Seoul` |
| MySQL 서버 | `default-time-zone = '+09:00'` |
| JDBC URL | `serverTimezone=Asia/Seoul&characterEncoding=UTF-8` |
| 컬럼 타입 | `DATETIME` (`TIMESTAMP` 아님 — 자동 UTC 변환 회피) |
| Java 타입 | `LocalDateTime` |
| API 응답 | `yyyy-MM-dd'T'HH:mm:ss` (오프셋 미표기) |

로컬 Windows는 OS 시간대가 이미 KST지만 **명시적으로 지정한다.** 배포 서버·CI 러너는 대개 UTC이므로 명시하지 않으면 그 시점에 문제가 드러난다. 시각 검증 테스트를 통합 테스트에 포함한다.

### 5.1 구현 방식 — 두 지점 모두 건다

JVM 플래그와 코드 초기화를 **함께** 쓴다. 각자 상대가 못 막는 경우를 막는다.

**1) `build.gradle` — 개발·CI 실행**

```groovy
tasks.withType(JavaExec).configureEach { jvmArgs '-Duser.timezone=Asia/Seoul' }
tasks.withType(Test).configureEach     { jvmArgs '-Duser.timezone=Asia/Seoul' }
```

**왜 이 형태인가**

- `bootRun`은 `JavaExec` 하위 타입이라 첫 줄에 걸리고, `bootTestRun` 같은 태스크가 생겨도 따라온다
- 두 타입을 한 가지 문장으로 덮어 두 저장소에서 같은 형태가 된다

**`systemProperty`와의 관계** — `Test` 태스크에서는 두 형태가 **등가다.** Gradle의 `DefaultJavaForkOptions`가 `jvmArgs`의 `-D` 인자를 `systemProperties`로 정규화하므로, 결국 같은 `-Duser.timezone`이 워커 커맨드라인에 실린다. `systemProperty 'user.timezone', 'Asia/Seoul'`로 써도 동작한다.

`jvmArgs`로 통일하는 것은 **의도를 명시하고 `JavaExec`까지 한 문장으로 덮기 위해서이지, `systemProperty`가 동작하지 않아서가 아니다.**

> 측정할 때 주의할 점이 있다. `jvmArgs`로 건 `-D` 인자는 `jvmArgs` getter에서 사라지고 `systemProperties`에 들어간다. `Test` 태스크의 실제 워커 인자는 `allJvmArgs`에서 봐야 한다. 이 정규화를 모르고 측정하면 어느 쪽으로든 틀린 결론이 나온다.

**`gradle.properties`의 `systemProp.user.timezone`은 오답이다.** Gradle **데몬** JVM에만 적용되고 포크된 test·bootRun 워커에 상속되지 않는다.

**2) 애플리케이션 클래스 — 패키징된 jar 실행**

`main()`의 `SpringApplication.run(...)` **이전** 또는 static 초기화 블록에서 건다.

```java
static {
	TimeZone.setDefault(TimeZone.getTimeZone("Asia/Seoul"));
}
```

**`@PostConstruct`로 걸지 않는다. 이미 그렇게 되어 있다면 삭제한다** — 남겨두면 같은 일을 두 번 하면서 늦은 쪽이 의도를 흐린다. 그 훅은 `dataSource`·`flywayInitializer`·`entityManagerFactory`가 모두 초기화된 **뒤에** 실행되며, Logback은 그 전에 기본 시간대를 캐싱해 교정되지 않는다. 더 중요하게는 **Spring 컨텍스트를 띄우지 않는 단위 테스트에 적용되지 않는다** — Mockito 기반 Service 테스트가 CI 러너의 UTC를 그대로 쓰게 된다.

**두 지점의 역할이 다르다.** JVM 플래그는 *테스트 JVM과 로컬 실행*의 하한선을 보장하고, static 블록은 *배포된 애플리케이션*이 실행 방식과 무관하게 KST임을 보장한다. 겹치는 게 아니라 서로의 사각지대를 덮는다.

| 경로 | JVM 플래그 | static 블록 |
| --- | --- | --- |
| `gradlew test` (Spring 컨텍스트 있음) | O | O |
| `gradlew test` (Mockito 단위 테스트) | O | **X** — `*Application`을 로딩하지 않아 static 블록이 실행되지 않는다 |
| `gradlew bootRun` | O | O |
| IDE의 Spring Boot 실행 구성 | **X** — Gradle을 거치지 않는다 | O |
| `java -jar` (2차 컨테이너) | **X** | O |

static 블록만 두면 **실행 순서에 따라 결과가 달라진다.** Gradle은 기본적으로 한 저장소의 테스트 전부를 워커 JVM 하나에서 돌리므로, `@SpringBootTest`가 먼저 돌면 이미 KST로 바뀐 상태를 뒤따르는 Mockito 테스트가 보고, 반대 순서면 UTC를 본다. 클래스 이름·필터·병렬 설정이 바뀌면 간헐적으로 깨지며 원인 추적이 어렵다. JVM 플래그가 이 순서 의존을 구조적으로 없앤다.

> 검증 표의 `TimeZone.getDefault()` 케이스는 **KST 개발 머신에서는 설정이 없어도 통과한다.** 그래서 이 절을 지켰는지는 테스트 통과가 아니라 위 두 지점의 존재로 확인한다.
