---
title: JVM 시간대는 실행 환경이 정한다
type: adr
status: accepted
version: v4
updated: 2026-09-14
read_when: "시간대 설정을 어디에 둘지 판단할 때"
related: [README.md, ../tech-stack.md]
---
# 0011. JVM 시간대는 실행 환경이 정한다

## 상태
accepted (0010 이후 추가)

## 맥락

`tech-stack.md`가 "전 구성요소 KST 통일"을 정하면서, 그 근거로 "배포 서버·CI 러너는 대개 UTC"를 들었다. 그 결과 **코드가 어떤 환경에서도 KST가 되도록 강제하는** 방향으로 구현됐다.

M-01·B-01에서 나온 형태는 이랬다.

```java
static {
    TimeZone.setDefault(TimeZone.getTimeZone("Asia/Seoul"));
}
```

```groovy
tasks.withType(JavaExec).configureEach { jvmArgs '-Duser.timezone=Asia/Seoul' }
tasks.withType(Test).configureEach     { jvmArgs '-Duser.timezone=Asia/Seoul' }
```

## 결정

**JVM 시간대를 코드·빌드에서 설정하지 않는다.** 실행 환경(OS·컨테이너·CI)이 정한다.

## 근거

**표준이 아니다.** 일반적인 Java·Spring 프로젝트는 JVM 시간대를 배포 환경에서 맞춘다. `TimeZone.setDefault()`를 애플리케이션 코드에 넣는 것은 환경 설정을 코드가 침범하는 것이다.

**실행 방식마다 동작이 갈린다.** `static` 블록은 그 클래스를 로딩할 때만 돌고, Gradle `jvmArgs`는 Gradle을 거치는 실행에만 붙는다. 어느 쪽도 모든 경로를 덮지 못해 결국 둘 다 넣게 되고, 그래도 IDE 직접 실행과 `java -jar`는 각각 한쪽만 덮인다. 덮이지 않는 조합을 추적하는 비용이 이득을 넘었다.

**데이터 안전은 다른 계층이 보장한다.** JVM이 UTC여도 **저장되는 값은 KST 기준으로 유지된다** — I-03에서 세 서비스를 `-Duser.timezone=UTC`로 함께 띄워 측정했다(바인드 `01:19:5x` → 저장 `10:19:5x`). 왕복에 손실이 없다.

> **영향 범위가 이 절이 적었던 것보다 넓다. I-03 실측이다.** JVM 시간대가 영향을 주는 것은 로그와 `LocalDateTime.now()`만이 아니다 — **조회 응답도 영향을 받는다.** 읽기 경로가 DB의 KST 값을 JVM 존으로 되돌리므로 UTC JVM에서 `GET /posts/{id}`가 `2026-10-17T01:19:56`을 돌려줬다(저장값은 `10:19:56`). **오프셋 표기가 없으므로 클라이언트는 그것을 KST로 읽는다** — 9시간 틀린 시각이 조용히 나간다. 그래서 배포 시 `ENV TZ=Asia/Seoul`을 거는 근거는 로그 편의가 아니라 **응답의 정확성**이다([../plan/phase2.md](../plan/phase2.md)).
>
> **`hibernate.jdbc.time_zone` 이 이 경로의 변환을 정한다. I-03 리뷰 실측이다.** 값을 `UTC` 로 바꾸면 저장값이 `02:31:39` 로 **UTC 가 된다** — 관측되므로 무효한 설정이 아니다. 그리고 그 설정이 **JDBC URL 의 `serverTimezone` 을 이긴다**: URL 에 `connectionTimeZone=UTC` 를 넣어도 이 설정이 `Asia/Seoul` 이면 저장값은 KST 로 맞았고, 거꾸로 URL 에서 `serverTimezone` 을 **빼도** 저장값이 그대로 KST 였다. **`serverTimezone` 은 어느 조합에서도 결과를 바꾸지 않았다.**
>
> **앞선 측정이 교란됐던 자리다.** "설정을 가진 auth 와 가지지 않은 board 가 똑같이 변환됐다" 로 "무효하다" 를 결론했는데, 설정을 빼면 Connector/J 가 **서버 존으로 폴백**하고 이 환경의 MySQL `time_zone` 이 `+09:00` 이라 `Asia/Seoul` 과 같은 오프셋이다. **"있음 vs 없음" 은 설계상 같은 결과를 내므로 "무효" 와 "폴백이 우연히 일치" 를 가르지 못한다.** 가르려면 **값을 바꿔야** 한다.
>
> **그래서 이 설정을 지우면 안 된다.** MySQL 서버 존이 `+09:00` 이 아닌 환경 — 이 ADR 이 전제로 든 바로 그 환경 — 에서 저장값이 조용히 어긋난다.

JVM 시간대는 배포 환경을 KST로 맞추면 해결된다.

**검증이 불가능했다.** 검증 표의 `TimeZone.getDefault()` 케이스는 KST 개발 머신에서 설정이 없어도 통과한다. 이 사실 때문에 "설정이 동작했는지"와 "OS가 원래 KST인지"를 구분하려고 리뷰어·수정 워커·오케스트레이터가 각자 다른 측정을 했고, 세 번 모두 서로 다른 잘못된 결론을 냈다.

## 결과

- 두 서비스의 `static` 블록과 Gradle `jvmArgs`를 제거했다
- `TimeZone.getDefault()`를 단언하는 테스트를 제거했다. 개발 머신에서 항상 통과해 아무것도 검증하지 못했다
- JDBC·Hibernate·Jackson의 시간대 설정은 유지한다. 이들은 환경 설정이 아니라 **데이터 경계의 계약**이다 — **다만 셋의 무게가 다르다**(아래)

> **셋을 같은 무게로 적은 것이 과했다. 무게는 I-03 리뷰가 측정했다.** 1차의 타입 조합(`LocalDateTime` + `DATETIME`)에서 변환을 정하는 것은 **`hibernate.jdbc.time_zone` 하나다.** `serverTimezone` 은 **어느 조합에서도 결과를 바꾸지 않았고**, `spring.jackson.time-zone` 은 [../tech-stack.md §6](../tech-stack.md)이 적은 대로 **`LocalDateTime` 직렬화에 영향이 없다**(존이 없어 변환할 것이 없다). **무게가 `hibernate.jdbc.time_zone` ≫ `serverTimezone` ≈ `spring.jackson.time-zone` 이다.**
>
> **그래서 board에 없는 두 줄을 다르게 처리했다.** `hibernate.jdbc.time_zone`은 [../plan/integration.md](../plan/integration.md) I-03의 완료 기준이 "세 서비스에 있다"를 요구하므로 **더했다** — **요구로 골랐는데 그것이 마침 실제로 일하는 설정이었다.** 효과로 골랐다면 당시의 (교란된) 측정 때문에 "무효하니 안 더한다"로 틀렸을 것이다. `spring.jackson.time-zone`은 §6의 표가 API 응답을 "Jackson **기본값**"으로 적고 같은 절이 무효임을 명시하므로 **더하지 않았다** — auth·member가 그것을 가진 쪽이 잉여다. **효과로 고르지 않고 정본이 요구하는지로 골랐다.**
- 배포 시 시간대 지정이 필요해졌다. 2차 컨테이너화에서 `ENV TZ=Asia/Seoul`로 처리한다

## 되돌릴 조건

배포 환경의 시간대를 통제할 수 없는 상황이 생기면 재검토한다. 그때도 코드가 아니라 실행 명령(`-Duser.timezone`)이 먼저다.
