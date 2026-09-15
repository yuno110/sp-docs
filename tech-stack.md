---
title: 기술 스택과 로컬 환경
type: spec
status: frozen
version: v3
updated: 2026-09-15
read_when: "의존성 버전을 정하거나, 프로젝트를 스캐폴딩하거나, 로컬 환경을 구성할 때"
related: [conventions.md, adr/0005-no-docker-in-mvp.md, adr/0007-shared-code-policy.md]
---
# 기술 스택과 로컬 환경

버전의 정본은 이 문서다. 다른 문서의 서술을 버전의 근거로 쓰지 않는다.

## 1. 공통 스택

세 서비스가 동일하다.

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

### 3.1 세 서비스 공통

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
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}
```

**이 목록은 정본이다.** 여기 있는 것은 전부 선언해야 하고, 여기 없는 의존성을 임의로 추가하지 않는다. 필요하면 이 문서를 먼저 개정한다([process/review-policy.md §8](process/review-policy.md)).

예외는 **Initializr가 생성한 골격의 일부**다. `junit-platform-launcher`(Gradle 9의 테스트 런타임에 필요)와 `.gitattributes`가 여기 해당하며, 전자는 위 목록에 포함시켰다.

### 3.2 서비스별 추가

| 서비스 | 추가 | 왜 |
| --- | --- | --- |
| auth | `org.springframework.security:spring-security-oauth2-jose`<br>`org.springframework.boot:spring-boot-starter-oauth2-resource-server` | **서명**(`NimbusJwtEncoder`) + 자기 발급 토큰 검증 |
| member | `org.springframework.boot:spring-boot-starter-oauth2-resource-server` | 검증만 |
| board | `org.springframework.boot:spring-boot-starter-oauth2-resource-server` | 검증만 |

**서명 의존성을 갖는 것은 auth 하나뿐이다.** member·board에 `oauth2-jose`를 넣지 않는다 — 넣으면 개인키만 있으면 토큰을 만들 수 있게 되어 [security.md §2](security.md)의 경계가 흐려진다.

QueryDSL Q타입 생성 경로(`build/generated/sources/annotationProcessor`)를 `.gitignore`에 넣는다.

## 4. 로컬 환경

**1차는 Docker를 사용하지 않는다**([adr/0005](adr/0005-no-docker-in-mvp.md)). MySQL은 로컬에 직접 설치하고 서비스는 IDE 또는 `gradlew bootRun`으로 실행한다.

### 4.1 MySQL 설치 후 1회

```sql
CREATE DATABASE sp_auth   DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
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

**개인키는 auth-service 하나만 갖는다.** 공개키는 member와 board **두 곳**에 배포한다. 배포 방식과 보관 규칙은 [security.md §3](security.md)를 본다.

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
  internal-api-key: ${INTERNAL_API_KEY}
```

`MEMBER_SERVICE_URL`은 board만 쓴다. **auth는 다른 서비스의 주소를 알지 않는다.**

**비밀 값(JWT 개인키, DB 비밀번호)은 기본값을 두지 않는다.** `${DB_PASSWORD}`처럼 기본값 없이 쓴다. 없으면 기동이 실패해야 한다.

> Spring은 해석되지 않은 placeholder를 리터럴 문자열로 남긴다. 그래서 `DB_PASSWORD` 미설정 시 오류 메시지가 `Access denied for user 'root'@'localhost' (using password: YES)`로 나온다. **비밀번호가 틀린 게 아니라 환경변수가 없는 것**이니 먼저 §4.3.1을 확인한다.

#### 4.3.1 로컬 비밀번호 — `application-local.yml`

애플리케이션은 `DB_PASSWORD` 없이 기동하지 않는다. **로컬에서는 환경변수 대신 파일로 준다.**

```
application.yml          커밋됨.  password: ${DB_PASSWORD}      ← 배포용
application-local.yml    .gitignore.  password: 실제값          ← 내 PC에만
```

프로파일 설정(`application-local.yml`)이 기본 설정(`application.yml`)을 **덮어쓴다.** 따라서 로컬에서는 환경변수가 없어도 파일의 값이 쓰이고, 배포 환경에서는 파일이 없으므로 환경변수가 쓰인다. 실측으로 확인했다.

**최초 1회**

```bash
cp src/main/resources/application-local.yml.example src/main/resources/application-local.yml
# 파일을 열어 password 에 MySQL root 비밀번호를 적는다
```

`application-local.yml`은 `.gitignore`에 있어 **평문으로 적어도 커밋되지 않는다.** 템플릿(`.example`)만 저장소에 남는다.

**실행할 때는 local 프로파일을 켠다.**

```bash
./gradlew bootRun --args='--spring.profiles.active=local'
```

**왜 환경변수가 아니라 파일인가** — 둘 다 비밀 값을 저장소 밖에 두므로 안전 측면은 같다. 파일 쪽이 설정·확인·수정이 눈에 보이고 IDE 재시작이 필요 없다. 배포 시에는 파일을 두지 않고 환경변수로 주입한다(§4.3).

> `DB_PASSWORD`가 어디에도 없으면 `Access denied for user 'root'@'localhost' (using password: YES)`로 기동이 실패한다. **비밀번호가 틀린 게 아니라 값이 없는 것이다.** Spring이 해석되지 않은 placeholder를 리터럴로 남기기 때문이다.

`JWT_PRIVATE_KEY`(auth만)와 `INTERNAL_API_KEY`(member·board)도 같은 방식으로 `application-local.yml`에 넣는다.

### 4.4 실행

| 서비스 | 명령 | 주소 |
| --- | --- | --- |
| auth | `./gradlew bootRun --args='--spring.profiles.active=local'` | `:8083` |
| member | 동일 | `:8081` |
| board | 동일 | `:8082` |

- Swagger UI: `/swagger-ui.html` (운영 프로파일에서는 비활성화)
- 헬스체크: `/actuator/health`

## 5. 테스트 환경

테스트는 H2(MySQL 호환 모드)를 쓴다(§1). 그런데 **두 가지가 조용히 어긋난다.** 둘 다 실측으로 확인했다.

### 5.1 테스트 프로파일을 기본으로 만든다

테스트 설정은 `src/test/resources/application-test.yml`에 둔다. 파일명을 `application.yml`로 두면 테스트 클래스패스에서 main 설정을 **병합이 아니라 교체**해버려 `spring.application.name`·`server.port`·`public-key-location` 같은 main 값이 전부 사라진다.

그런데 프로파일 설정은 `@ActiveProfiles("test")`를 붙인 테스트에만 적용된다. 붙이지 않은 테스트는 그 파일을 아예 읽지 않는다.

```groovy
tasks.named('test') {
	useJUnitPlatform()
	systemProperty 'spring.profiles.active', 'test'
}
```

**이 한 줄로 opt-in을 없앤다.** 없으면 `@ActiveProfiles`를 빠뜨린 테스트가 조용히 다른 설정으로 돈다.

| `@DataJpaTest` | `spring.jpa.hibernate.ddl-auto` | 결과 |
| --- | --- | --- |
| 프로파일 없음 | `null` → 임베디드 기본값 `create-drop` | **엔티티로부터 스키마 생성. 마이그레이션이 깨져도 초록** |
| 프로파일 있음 | `validate` | 마이그레이션과 엔티티가 어긋나면 실패 |

`application-test.yml`에 `spring.jpa.hibernate.ddl-auto: validate`를 명시한다. 스키마 출처를 Flyway 하나로 고정하기 위해서다.

### 5.2 `@DataJpaTest`는 DataSource URL을 덮는다

`@DataJpaTest`의 기본 `@AutoConfigureTestDatabase(replace = ANY)`가 `application-test.yml`의 URL을 무시하고 `jdbc:h2:mem:<uuid>`로 바꾼다. **`MODE=MySQL`이 사라진다.**

그러면 마이그레이션 SQL이 MySQL 문법(`TEXT`, `AUTO_INCREMENT`, 인덱스 선언)을 쓸 때 호환 모드가 아닌 H2에서 실행된다.

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class MemberRepositoryTest { ... }
```

**모든 `@DataJpaTest` 클래스에 이 애노테이션을 붙인다.** `ddl-auto`는 프로파일에서 오고 URL은 덮이는, 절반만 적용되는 상태를 막는다.

## 6. 시간대 — KST 통일

| 계층 | 설정 | 누가 |
| --- | --- | --- |
| **JVM** | OS·컨테이너의 시간대를 따른다 | **배포 환경** |
| MySQL 서버 | `SET PERSIST time_zone='+09:00'` (§4.1) | 로컬 1회 / 운영 DBA |
| JDBC URL | `serverTimezone=Asia/Seoul` | `application.yml` |
| Hibernate | `spring.jpa.properties.hibernate.jdbc.time_zone: Asia/Seoul` | `application.yml` |
| 컬럼 타입 | `DATETIME` (`TIMESTAMP` 아님 — 자동 UTC 변환 회피) | 마이그레이션 |
| Java 타입 | `LocalDateTime` | 엔티티 |
| API 응답 | `yyyy-MM-dd'T'HH:mm:ss` (오프셋 미표기) | `spring.jackson.time-zone` |

### 6.1 JVM 시간대는 코드에서 건드리지 않는다

**`TimeZone.setDefault()`를 애플리케이션 코드에 넣지 않는다.** `build.gradle`에 `-Duser.timezone`을 박지도 않는다. JVM 시간대는 **실행 환경이 정하는 것**이고, 코드가 환경 설정을 침범하면 실행 방식마다 동작이 갈린다.

환경별로 이렇게 맞춘다.

| 환경 | 방법 |
| --- | --- |
| 로컬 개발 | OS 시간대가 KST면 그대로 (Windows 한국 설정은 이미 KST) |
| Docker (2차) | `ENV TZ=Asia/Seoul` |
| 리눅스 서버 | `timedatectl set-timezone Asia/Seoul` |
| CI | 러너 설정 또는 `TZ` 환경변수 |
| 필요 시 직접 지정 | `java -Duser.timezone=Asia/Seoul -jar app.jar` |

### 6.2 JVM이 KST가 아니어도 데이터는 안전하다

위 표의 **JDBC·Hibernate 설정이 DB 경계를 고정**하기 때문이다. JVM이 UTC인 환경에 배포되어도 DB에 저장되는 값은 KST 기준으로 유지된다.

JVM 시간대가 어긋날 때 영향받는 것은 **로그 타임스탬프와 `LocalDateTime.now()`** 다. 전자는 운영 편의의 문제이고, 후자는 배포 환경을 KST로 맞추면 해결된다.

> 이전 버전은 `static` 초기화 블록과 Gradle `jvmArgs`로 JVM 시간대를 강제했다. 표준에서 벗어난 방식이라 제거했다. 판단 근거는 [adr/0011-timezone-from-environment.md](adr/0011-timezone-from-environment.md)에 있다.
