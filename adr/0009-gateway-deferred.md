---
title: API Gateway 2차 이연
type: adr
status: accepted
version: v1
updated: 2026-09-11
read_when: "1차에 게이트웨이를 두지 않는 이유가 궁금할 때"
related: [README.md, ../architecture.md, ../plan/phase2.md]
---
# 0009. API Gateway 2차 이연

## 상태
accepted

## 맥락

MSA의 표준 구성에는 API Gateway가 들어간다. 단일 진입점, 라우팅, CORS 일괄 처리, 1차 JWT 검증을 담당한다. 1차부터 둘지 정해야 했다.

## 결정

**1차에서는 게이트웨이를 두지 않는다.** 클라이언트가 `:8081`(member), `:8082`(board)를 직접 호출한다.

## 근거

- 서비스가 2개뿐이라 프론트엔드가 주소 2개를 아는 것으로 충분하다
- 게이트웨이는 Spring Cloud Gateway를 쓰게 되는데, **Spring Cloud 릴리스 트레인은 Boot 버전과 강하게 결합**되어 업그레이드 부담을 만든다. 1차에 도입을 미루면 그 결합을 피할 수 있다
- 게이트웨이가 없어도 각 서비스가 JWT를 독립 검증하므로 보안이 약해지지 않는다. 오히려 Zero Trust 원칙상 **게이트웨이가 있어도 각 서비스는 재검증해야** 한다

## 결과

- `gateway/` 디렉터리를 만들지 않는다
- **CORS를 각 서비스가 개별 설정한다.** 게이트웨이 도입 시 이 설정을 게이트웨이로 옮긴다
- Spring Cloud 의존성을 1차에 도입하지 않는다
- [../api-contract.md §1](../api-contract.md)의 경로 표는 2차 전환 시 게이트웨이 라우팅 규칙의 명세가 된다

## 도입 시점

2차. 도입 시 `/internal/**`을 라우팅에서 제외해 내부 API의 외부 노출을 차단한다.
