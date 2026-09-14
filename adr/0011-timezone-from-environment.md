---
title: JVM 시간대는 실행 환경이 정한다
type: adr
status: accepted
version: v1
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

**데이터 안전은 다른 계층이 보장한다.** JDBC URL의 `serverTimezone`과 `hibernate.jdbc.time_zone`이 DB 경계를 고정하므로, JVM이 UTC여도 저장되는 값은 KST 기준으로 유지된다. JVM 시간대가 실제로 영향을 주는 것은 로그 타임스탬프와 `LocalDateTime.now()`이고, 둘 다 배포 환경을 KST로 맞추면 해결된다.

**검증이 불가능했다.** 검증 표의 `TimeZone.getDefault()` 케이스는 KST 개발 머신에서 설정이 없어도 통과한다. 이 사실 때문에 "설정이 동작했는지"와 "OS가 원래 KST인지"를 구분하려고 리뷰어·수정 워커·오케스트레이터가 각자 다른 측정을 했고, 세 번 모두 서로 다른 잘못된 결론을 냈다.

## 결과

- 두 서비스의 `static` 블록과 Gradle `jvmArgs`를 제거했다
- `TimeZone.getDefault()`를 단언하는 테스트를 제거했다. 개발 머신에서 항상 통과해 아무것도 검증하지 못했다
- JDBC·Hibernate·Jackson의 시간대 설정은 유지한다. 이들은 환경 설정이 아니라 **데이터 경계의 계약**이다
- 배포 시 시간대 지정이 필요해졌다. 2차 컨테이너화에서 `ENV TZ=Asia/Seoul`로 처리한다

## 되돌릴 조건

배포 환경의 시간대를 통제할 수 없는 상황이 생기면 재검토한다. 그때도 코드가 아니라 실행 명령(`-Duser.timezone`)이 먼저다.
