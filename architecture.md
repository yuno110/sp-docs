---
title: 아키텍처
type: explanation
status: living
version: v2
updated: 2026-09-15
read_when: "서비스 경계, 서비스 간 통신, 데이터 일관성 설계를 확인할 때"
related: [domain-model.md, api-contract.md, adr/0001-msa-adoption.md, adr/0003-writer-snapshot.md, adr/0012-auth-as-separate-service.md]
---
# 아키텍처

## 1. 전체 구성

```
                         Client (Web/App)
                                |
         +----------------------+----------------------+
         |                      |                      |
  :8083 auth-service    :8081 member-service    :8082 board-service
  - 계정 CRUD           - 프로필 CRUD           - 게시글 CRUD/검색
  - 로그인/재발급       - 내부 API 제공         - 댓글 CRUD
  - JWT 발급 (개인키)   - JWT 검증 (공개키)     - JWT 검증 (공개키)
         |                      |    ^                 |
     sp_auth               sp_member  \                sp_board
  account,                  member     \------------- post, comment
  refresh_token                   내부 API (쓰기 경로에서만)
```

**호출 방향은 `board -> member` 하나뿐이다.** auth는 다른 서비스를 호출하지 않고, 다른 서비스도 auth를 런타임에 호출하지 않는다. 토큰 검증은 공개키로 오프라인 수행한다.

1차에서는 API Gateway를 두지 않고 클라이언트가 세 서비스를 직접 호출한다([adr/0009](adr/0009-gateway-deferred.md)).

**계정과 프로필이 갈라져 있으므로 가입과 탈퇴가 2단계다.** 클라이언트가 순서대로 호출한다([adr/0012](adr/0012-auth-as-separate-service.md) §4·§5).

DB는 로컬에서 MySQL 1 인스턴스에 스키마 3개로 두고, 운영에서는 인스턴스를 분리한다. 스키마가 같은 인스턴스에 있어도 §5의 금지 사항은 그대로 적용한다.

## 2. 설계 원칙

| # | 원칙 | 적용 |
| --- | --- | --- |
| 1 | Database per Service | 서비스는 자기 DB만 접근한다. 타 서비스 테이블 직접 조회·조인·FK 제약 전면 금지 |
| 2 | API를 통한 통신 | 데이터가 필요하면 소유 서비스의 API를 호출하거나 스냅샷으로 복제한다 |
| 3 | 독립 배포 | 각 서비스는 자체 저장소·빌드를 가지며 단독 배포된다 |
| 4 | 장애 격리 | member 장애 시에도 게시글 **조회·수정·삭제**는 정상 동작해야 한다. **생성은 중단된다**(§4.3) |
| 5 | Stateless | 세션 미사용. 모든 인스턴스가 동등하며 수평 확장 가능 |
| 6 | 최종 일관성 | 서비스에 걸친 작업은 2PC 대신 순서와 멱등으로 다룬다. 중간 실패가 안전한 쪽으로 떨어지게 순서를 정한다(§4.4) |

## 3. 서비스 내부 계층 (공통)

```
Controller   요청·응답 DTO, 입력 검증, HTTP 관심사만
    |
Service      비즈니스 로직, 트랜잭션 경계(@Transactional)
    |
Repository   Spring Data JPA / QueryDSL
    |
Database     자기 서비스 전용 스키마
```

- Entity는 Controller 밖으로 노출하지 않는다. 반드시 DTO로 변환한다
- 트랜잭션 경계는 Service에 둔다. 조회는 `@Transactional(readOnly = true)`
- 도메인 로직은 Entity 메서드로 구현한다 (`post.update(...)`, `account.changePassword(...)`)
- **트랜잭션 안에서 다른 서비스를 호출하지 않는다.** 네트워크 지연이 DB 커넥션을 점유한다

## 4. 서비스 간 통신

### 4.1 신원 전파

Access Token(JWT)의 Claim에 신원 정보를 담아 member·board가 네트워크 호출 없이 요청자를 식별한다. Claim 스펙의 정본은 [api-contract.md §6](api-contract.md)다.

**발급은 auth-service 하나다.** member·board는 서명을 검증한 뒤 Claim에서 `sub`(accountId)와 `role`을 꺼내 `LoginMember` 객체로 만든다.

**`nickname` claim은 없다.** auth는 닉네임을 소유하지 않으므로 넣을 수 없다. 그 결과 작성자 스냅샷을 Claim에서 얻을 수 없고, 쓰기 경로에서 member를 호출해야 한다(§4.2·§4.3). 이것이 auth 분리의 실질 비용이다([adr/0012](adr/0012-auth-as-separate-service.md) §3).

**검증은 오프라인이다.** 탈퇴·권한 박탈이 기존 토큰에 즉시 반영되지 않는다. 잔여 노출은 Access Token 만료까지이며, 그 `role`이 가진 모든 변경 권한을 포함한다.

JWT payload는 암호화되지 않으므로 이메일 등 불필요한 개인정보를 넣지 않는다.

### 4.2 작성자 정보 — 스냅샷

게시글 목록에는 작성자 닉네임이 필요하지만 닉네임은 member-service 소유 데이터이고 `sp_board`에서 조인할 수 없다. **작성 시점의 닉네임을 `post.writer_nickname`에 복제 저장**한다.

```
[작성]  POST /api/v1/posts
        Authorization: Bearer <JWT>  -> Claim { sub:"3", role:"USER" }

        1) POST /internal/v1/members/bulk  { accountIds: [3] }    <- 트랜잭션 밖
           -> 200 { members: [{ accountId:3, nickname:"홍길동", deleted:false }] }

        2) BEGIN
           INSERT INTO post (writer_id, writer_nickname, ...) VALUES (3, '홍길동', ...)
           COMMIT

        => member-service 호출 1회 (생성 경로에서만)

[조회]  SELECT id, title, writer_id, writer_nickname, ... FROM post
        => sp_board 단일 쿼리. member-service가 죽어도 동작
```

`writer_id`는 `accountId`를 논리 참조하지만 **FK 제약을 걸지 않는다**.

**0003이 지키려던 것과 잃은 것을 구분한다.** 조회 경로 원격 호출 0회는 그대로다 — 이것이 스냅샷의 목적이었다. 잃은 것은 **쓰기 경로의 독립성**이다. 취득 경로가 Claim에서 내부 API로 바뀐 이유는 [adr/0012](adr/0012-auth-as-separate-service.md) §6에 있다.

**트레이드오프**: 닉네임 변경 시 과거 글에 반영되지 않는다. 2차에 Kafka 이벤트로 해소한다([adr/0010](adr/0010-kafka-for-nickname-sync.md)). 선택 근거와 대안 비교는 [adr/0003](adr/0003-writer-snapshot.md)에 있다.

**연관 규칙**: **수정 시 스냅샷을 갱신하지 않는다.** 작성 당시 표시를 보존하기 위해서다. 그 결과 수정·삭제 경로는 member를 호출하지 않는다. 닉네임 변경 API가 토큰을 반환하던 규칙은 폐기됐다 — Claim에 닉네임이 없으므로 토큰이 낡을 이유가 사라졌다([requirements/member.md §7](requirements/member.md)).

### 4.3 내부 API

member-service가 서비스 간 호출 전용으로 제공한다. 엔드포인트와 실패 판정의 정본은 [api-contract.md §5](api-contract.md)다.

- **벌크 하나만 둔다.** 목록 N건에 N번 호출하는 구현 금지. 1건만 필요한 쓰기 경로도 벌크에 1건을 담는다
- 타임아웃: connect 1초 / read 3초. 기본값(무제한) 금지
- 보호: `X-Internal-Api-Key` 헤더 검증 + 외부 라우팅 제외
- 원격 호출은 **DB 트랜잭션 밖에서 먼저** 한다(§3·§5)

**1차부터 board가 글·댓글 생성 시 호출한다.** Claim에 닉네임이 없으므로 다른 취득 경로가 없다.

### 4.3.1 실패 처리 — 조회와 쓰기가 다르다

| 경로 | 1차 동작 |
| --- | --- |
| **조회** | 내부 API를 호출하지 않는다. 스냅샷만 읽는다. member 장애와 무관하다 |
| **쓰기** | 호출이 실패하면 **저장하지 않고 503을 반환한다.** 폴백할 스냅샷이 아직 없다 |

**쓰기 경로에는 폴백이 없다.** 저장할 닉네임을 만들어낼 수 없으므로 실패를 드러낸다.

**HTTP 404를 업무 의미로 쓰지 않는다.** 프로필 유무는 200 응답의 본문으로만 판정한다. 404를 "프로필 없음"으로 해석하면 경로 오설정·내부 API 키 거부가 업무 오류로 위장되어, 경보도 서킷도 없이 전 사용자의 쓰기가 조용히 멈춘다. 전체 표는 [api-contract.md §5.1](api-contract.md)에 있다.

**확인–커밋 사이의 창은 닫을 수 없다.** 원격 호출이 트랜잭션 밖이므로, 확인 뒤 커밋 전에 탈퇴가 커밋되면 탈퇴한 프로필의 글이 생성될 수 있다. "탈퇴 후 작성 불가"는 보장이 아니라 통상 동작이다.

### 4.4 회원 탈퇴 시 데이터 처리

세 서비스에 걸친 작업이지만 **2PC를 사용하지 않는다.** 대신 **중간 실패가 안전한 쪽으로 떨어지도록 순서를 정한다.**

1차 처리:

```
1. DELETE /api/v1/accounts/me  (auth)   비밀번호 재확인
                                        -> account.deleted = true
                                        +  RefreshToken 삭제      [한 로컬 트랜잭션]
2. DELETE /api/v1/members/me   (member) 프로필 deleted = true, nickname = NULL
3. board                                별도 처리 없음. 스냅샷 닉네임을 그대로 노출
```

**계정이 먼저다.** 이유는 둘이다.

- member는 비밀번호를 갖지 않는다. 프로필을 먼저 지우면 [requirements/member.md](requirements/member.md) MR-10의 **비밀번호 재확인이 구조적으로 불가능해진다**
- 중간 실패 시 계정 먼저는 아무것도 비가역으로 파괴하지 않고 30분 안에 스스로 잠긴다. 프로필 먼저는 프로필을 영구히 파괴한 채 계정을 영구히 살려 둔다

전체 비교는 [adr/0012](adr/0012-auth-as-separate-service.md) §5에 있다.

**중간 실패를 서버가 관측·복구하지 못한다.** 2단계는 클라이언트가 호출하고, auth는 프로필 존재를 모른다. 2단계가 수행되지 않으면 프로필 행이 남아 닉네임이 선점된다. 1차의 알려진 제약이며, 2차에 이벤트로 옮긴다([adr/0010](adr/0010-kafka-for-nickname-sync.md)).

탈퇴 회원 표기 갱신도 2차 이벤트 동기화 범위다.

## 5. 금지 사항

| 금지 | 사유 |
| --- | --- |
| `sp_board`·`sp_member`에서 다른 스키마 조인 | Database per Service 위반. 같은 인스턴스여도 금지 |
| `post.writer_id`·`member.account_id`에 FK 제약 설정 | 서비스 간 배포·삭제 순서를 강결합시킴 |
| `@Transactional` 안에서 원격 호출 | DB 커넥션이 네트워크 지연만큼 점유됨 |
| **조회 경로**에 board → member 동기 호출 배치 | 스냅샷의 목적이 사라진다([adr/0003](adr/0003-writer-snapshot.md)) |
| member → board 호출, auth → 다른 서비스 호출 | 호출 방향은 `board -> member` 단방향 하나뿐 |
| member·board가 개인키를 갖는 것 | 발급 주체는 auth 하나다([security.md §2](security.md)) |
| auth가 닉네임을 다루는 것 | 닉네임은 member 소유다 |
| 요청 본문의 `writerId`·`nickname`을 신뢰하는 것 | 검증된 JWT의 `sub`와 내부 API 응답에서만 가져온다 |
| HTTP 404를 "프로필 없음"으로 해석하는 것 | 인프라 오류가 업무 오류로 위장된다(§4.3.1) |

**해제된 금지** — 이전 v1의 "board → member 동기 호출을 **쓰기 경로**에 배치"는 해제됐다. 사유란의 "member 장애가 게시글 작성 실패로 전파"는 여전히 참이며, §4.3.1이 그것을 비용으로 수용한다. 이 금지는 닉네임이 JWT Claim에 있던 시절, 즉 **서비스가 둘일 때만 지킬 수 있던 규칙**이다. 근거는 [adr/0012](adr/0012-auth-as-separate-service.md)의 "정면으로 개정되는 규칙"에 있다. **조회 경로의 금지는 그대로 유지된다.**

## 6. 서비스 주소 관리

호출 주소를 코드에 하드코딩하지 않고 설정으로 외부화한다.

```yaml
member-service:
  url: ${MEMBER_SERVICE_URL:http://localhost:8081}
  internal-api-key: ${INTERNAL_API_KEY}
```

**이 설정을 갖는 것은 board 하나다.** member는 아무도 호출하지 않고, auth는 다른 서비스의 존재를 모른다.

> `MEMBER_SERVICE_URL`이 잘못 설정되면 member는 Spring 기본 404를 돌려준다. 그 404를 "프로필 없음"으로 해석하지 않는 것이 §4.3.1의 핵심이다.

1차는 정적 설정으로 충분하다. 서비스 디스커버리(Eureka 등 레지스트리 서버)는 도입하지 않는다. 2차에 컨테이너를 도입하면 주소를 `http://member-service:8081`로 바꾸는 것만으로 DNS 기반 디스커버리가 된다.
