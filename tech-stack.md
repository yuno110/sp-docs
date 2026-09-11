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
| Framework | Spring Boot | 3.5.x 최신 패치 |
| Build | Gradle (Groovy DSL) + Wrapper | 8.x |
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

**버전 확정**: 프로젝트 생성 시 [start.spring.io](https://start.spring.io)에서 3.5.x 최신 패치를 선택한다. Boot BOM이 관리하지 않는 서드파티(QueryDSL, springdoc)는 `build.gradle`에 버전을 명시 고정한다.

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
CREATE DATABASE member_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE DATABASE board_db  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

```ini
; my.ini
[mysqld]
default-time-zone = '+09:00'
```

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
    url: ${DB_URL:jdbc:mysql://localhost:3306/member_db?serverTimezone=Asia/Seoul&characterEncoding=UTF-8}
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:}
member-service:
  url: ${MEMBER_SERVICE_URL:http://localhost:8081}
```

비밀 값(JWT 개인키, DB 비밀번호)은 기본값을 두지 않는다. 없으면 기동이 실패해야 한다.

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
