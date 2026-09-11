---
title: 공통 코드 — 라이브러리 대신 표준 활용 + 최소 복제
type: adr
status: accepted
version: v1
updated: 2026-09-11
read_when: "공통 코드를 왜 라이브러리로 묶지 않는지 확인할 때"
related: [README.md, ../conventions.md, ../tech-stack.md]
---
# 0007. 공통 코드 — 라이브러리 대신 표준 활용 + 최소 복제

## 상태
accepted

## 맥락

두 서비스가 같은 코드를 갖게 된다. `ApiResponse`, `ErrorCode`, `GlobalExceptionHandler`, `BaseTimeEntity`, JWT 검증 등이다. 이것을 `common` 또는 `core` 라이브러리로 분리해 제공하자는 제안이 있었다. 특히 **JWT 검증 코드 중복은 실질적 위험**이다. 보안 코드라 한쪽만 고치면 구멍이 난다.

## 결정

**공유 방식을 정하기 전에 공유 대상을 줄인다.** Spring 표준으로 대체할 수 있는 것은 대체하고, 남는 것(약 75줄)만 복제한다. 공용 라이브러리 모듈을 만들지 않는다.

## 근거

### 1단계 — 공유 대상 분해

"복제"라고 뭉뚱그린 것을 펼치면 이렇다.

| 항목 | 규모 | 판단 |
| --- | --- | --- |
| JWT 검증 필터·Provider·Resolver | ~190줄 | **Spring이 제공** — 직접 만들지 않음 |
| `GlobalExceptionHandler` | ~80줄 | 서비스별 `ErrorCode`에 의존 → 공유 대상 아님 |
| `ErrorCode` enum | 서비스별 상이 | **공유하면 안 됨** (board 코드가 member에 들어감) |
| `PageResponse` | ~30줄 | Spring Data `Page` 직렬화로 대체 가능 |
| `ApiResponse` / `ErrorResponse` | ~40줄 | 직접 필요 |
| `BaseTimeEntity` | ~20줄 | 직접 필요 |
| `BusinessException` | ~15줄 | 직접 필요 |

실제로 두 벌 유지할 것은 **약 75줄**이다.

### 2단계 — JWT 코드가 사라지는 이유

RS256을 택한 덕분에([0004](0004-rs256-over-hs256.md)) Spring Security 표준을 쓸 수 있다.

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          public-key-location: classpath:jwt-public.pem
```

이것으로 서명 검증·만료 확인·`SecurityContext` 주입이 끝난다. 직접 작성할 것은 role claim 컨버터 ~15줄뿐이다. member-service의 서명도 `NimbusJwtEncoder`로 처리해 jjwt 의존성 자체를 뺀다.

결과적으로 양쪽이 같은 Spring 추상화를 쓰게 되어 "두 벌의 손수 만든 보안 코드"라는 위험이 사라진다.

### 3단계 — 75줄에 라이브러리는 과하다

| 라이브러리 방식의 비용 | |
| --- | --- |
| 3번째 저장소 + GitHub Packages 퍼블리싱 + 인증 설정 | 초기 반나절~하루 |
| 버전 불일치 | common 1.0.2인데 board만 1.0.1 쓰는 상황 |
| **독립 배포 원칙과 충돌** | common 고치면 두 서비스 재빌드·재배포 |
| 공유 범위 확대 경향 | ApiResponse → 유틸 → DTO → "분산 모놀리스" |
| **워커 병렬 작업에 직렬 지점 생성** | 워커A가 common 수정→퍼블리시→워커B 대기 |

마지막 항목이 특히 중요하다. 복제 방식이면 member 워커와 board 워커가 서로를 기다리지 않는다.

### DRY에 대하여

DRY는 "**지식**의 중복을 피하라"는 원칙이지 "코드의 유사성을 없애라"가 아니다. `ApiResponse`가 두 곳에 있는 것이 문제가 되는 지점은 **응답 형식이라는 계약**이 공유 지식이기 때문인데, 그 계약을 강제하는 수단은 라이브러리 말고도 있다.

## 결과

**복제 위험을 낮추는 장치**

- 정본을 문서에 둔다. `ApiResponse`는 [../api-contract.md §6](../api-contract.md), `BaseTimeEntity`는 [../domain-model.md §1.1](../domain-model.md)
- 복제본 파일 상단에 정본 위치를 주석으로 남긴다
- 두 서비스의 응답 형식 일치를 확인하는 계약 테스트를 통합 검증 단계에 둔다

**문서 저장소는 왜 만들었는가**([0002](0002-separate-repositories.md))

문서 저장소는 빌드·배포 파이프라인이 없다. 라이브러리 저장소를 반대한 이유(퍼블리싱 파이프라인, 버전 결합)가 문서에는 적용되지 않는다.

## 재검토 조건

다음 중 하나면 라이브러리 추출을 재검토한다.

- 서비스가 3개째가 될 때
- 복제 코드가 300줄을 넘을 때

복제 → 라이브러리 추출은 쉽지만, 라이브러리 → 분리는 이미 생긴 결합을 걷어내야 해서 더 어렵다. 되돌리기 쉬운 쪽을 먼저 택한다.
