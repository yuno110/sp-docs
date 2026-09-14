---
title: 1차에서 Docker 미사용
type: adr
status: accepted
version: v1
updated: 2026-09-11
read_when: "Docker를 왜 1차에 쓰지 않는지, 나중에 어떻게 도입하는지 확인할 때"
related: [README.md, ../tech-stack.md, ../plan/phase2.md]
---
# 0005. 1차에서 Docker 미사용

## 상태
accepted

## 맥락

초기 계획에는 Docker Compose로 MySQL과 두 서비스를 띄우는 구성이 들어 있었다. MSA 프로젝트의 관례를 따른 기본값이었다. 실제로 1차에서 값어치가 있는지 따져볼 필요가 있었다.

## 결정

**1차에서 Docker를 사용하지 않는다.** MySQL은 로컬에 직접 설치하고 서비스는 IDE 또는 `gradlew bootRun`으로 실행한다.

## 근거

Docker를 넣으려던 이유를 1차 기준으로 평가하면 다음과 같다.

| 이유 | 1차에서의 필요성 |
| --- | --- |
| MySQL을 설치 없이 띄우고 지우기 | 로컬 설치도 1회로 끝난다 — 낮음 |
| 프로세스 여럿을 일괄 기동 | 3개는 IDE에서 실행 가능 — 낮음 |
| 팀원·새 PC 환경 재현 | 1인 개발 — 낮음 |
| 환경변수 일괄 통제 | Windows 로컬은 이미 KST — 낮음 |
| 운영 배포의 표준 | 높음. 단 2차 |
| Kafka 등 설치가 번거로운 미들웨어 | 높음. 단 2차 |

앞의 넷은 이득이 크지 않고, 뒤의 둘은 2차에 가서야 필요해진다. Spring Boot·JPA·MSA·JWT를 동시에 다루는 단계에서 학습 대상을 하나 줄이는 편이 낫다고 판단했다.

## 결과

- 1차 작업 계획에서 `docker-compose.yml`과 `Dockerfile`이 빠졌다. 대신 MySQL 로컬 설치와 스키마 생성이 들어간다([../tech-stack.md §4](../tech-stack.md))
- **전제 조건이 하나 생겼다.** 나중에 전환할 때 코드를 고치지 않으려면 환경 의존 값을 설정으로 외부화해야 한다. 이는 보안 요구와도 일치한다

```yaml
spring:
  datasource:
    url: ${DB_URL:jdbc:mysql://localhost:3306/sp_member}
```

- 전환 시 바뀌는 것은 DB 접속 주소가 `localhost:3306`에서 `mysql:3306`이 되는 것뿐이다. 추가되는 파일은 서비스별 `Dockerfile`(10줄 내외)과 `docker-compose.yml` 하나다

## 도입 시점

**2차에 Kafka를 도입할 때 함께 컨테이너화한다.** Kafka는 로컬 직접 설치가 번거로워 컨테이너의 이득이 명확해지는 지점이며, 이때 MySQL·서비스까지 옮기면 DNS 기반 서비스 디스커버리도 자연히 확보된다.
