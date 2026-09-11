---
title: 아키텍처
type: explanation
status: living
version: v1
updated: 2026-09-11
read_when: "서비스 경계, 서비스 간 통신, 데이터 일관성 설계를 확인할 때"
related: [domain-model.md, api-contract.md, adr/0001-msa-adoption.md, adr/0003-writer-snapshot.md]
---
# 아키텍처

## 1. 전체 구성

```
                    Client (Web/App)
                           |
              +------------+------------+
              |                         |
     :8081 member-service      :8082 board-service
     - 회원 CRUD               - 게시글 CRUD/검색
     - JWT 발급 (개인키 서명)  - 댓글 CRUD
     - 내부 API 제공           - JWT 검증 (공개키)
              |                         |
         member_db                  board_db
     member, refresh_token        post, comment
```

1차에서는 API Gateway를 두지 않고 클라이언트가 두 서비스를 직접 호출한다([adr/0009](adr/0009-gateway-deferred.md)).

DB는 로컬에서 MySQL 1 인스턴스에 스키마 2개로 두고, 운영에서는 인스턴스를 분리한다. 스키마가 같은 인스턴스에 있어도 §5의 금지 사항은 그대로 적용한다.

## 2. 설계 원칙

| # | 원칙 | 적용 |
| --- | --- | --- |
| 1 | Database per Service | 서비스는 자기 DB만 접근한다. 타 서비스 테이블 직접 조회·조인·FK 제약 전면 금지 |
| 2 | API를 통한 통신 | 데이터가 필요하면 소유 서비스의 API를 호출하거나 스냅샷으로 복제한다 |
| 3 | 독립 배포 | 각 서비스는 자체 저장소·빌드를 가지며 단독 배포된다 |
| 4 | 장애 격리 | member-service 장애 시에도 게시글 조회는 정상 동작해야 한다 |
| 5 | Stateless | 세션 미사용. 모든 인스턴스가 동등하며 수평 확장 가능 |

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
- 도메인 로직은 Entity 메서드로 구현한다 (`post.update(...)`, `member.changePassword(...)`)
- **트랜잭션 안에서 다른 서비스를 호출하지 않는다.** 네트워크 지연이 DB 커넥션을 점유한다

## 4. 서비스 간 통신

### 4.1 신원 전파

Access Token(JWT)의 Claim에 신원 정보를 담아 board-service가 네트워크 호출 없이 작성자를 식별한다. Claim 스펙의 정본은 [api-contract.md §5](api-contract.md)다.

board-service는 서명을 검증한 뒤 Claim에서 `sub`(memberId), `nickname`, `role`을 꺼내 `LoginMember` 객체로 만든다.

`nickname`을 Claim에 넣는 이유는 게시글·댓글 작성 시 작성자 닉네임 스냅샷을 저장하기 위해서다. 이것이 없으면 쓰기마다 member-service를 동기 호출해야 한다.

JWT payload는 암호화되지 않으므로 이메일 등 불필요한 개인정보를 넣지 않는다.

### 4.2 작성자 정보 — 스냅샷

게시글 목록에는 작성자 닉네임이 필요하지만 닉네임은 member-service 소유 데이터이고 `board_db`에서 조인할 수 없다. **작성 시점의 닉네임을 `post.writer_nickname`에 복제 저장**한다.

```
[작성]  POST /api/v1/posts
        Authorization: Bearer <JWT>  -> Claim { sub:"3", nickname:"홍길동" }

        INSERT INTO post (writer_id, writer_nickname, title, content, ...)
        VALUES (3, '홍길동', ...)

        => member-service 호출 0회

[조회]  SELECT id, title, writer_id, writer_nickname, ... FROM post
        => board_db 단일 쿼리. member-service가 죽어도 동작
```

`writer_id`는 `member.id`를 논리 참조하지만 **FK 제약을 걸지 않는다**.

**트레이드오프**: 닉네임 변경 시 과거 글에 반영되지 않는다. 2차에 Kafka 이벤트로 해소한다([adr/0010](adr/0010-kafka-for-nickname-sync.md)). 선택 근거와 대안 비교는 [adr/0003](adr/0003-writer-snapshot.md)에 있다.

**연관 규칙**: JWT Claim에도 닉네임이 있으므로, 닉네임을 바꾸면 기존 토큰은 옛 닉네임 상태다. 그 토큰으로 새 글을 쓰면 새 글에도 옛 닉네임이 박제된다. 따라서 닉네임 변경 API는 새 Access Token을 함께 반환한다([requirements/member.md](requirements/member.md) M-08).

### 4.3 내부 API

member-service가 서비스 간 호출 전용으로 제공한다. 엔드포인트 정본은 [api-contract.md §4](api-contract.md)다.

- 조회는 반드시 **벌크 API**로 한다. 목록 N건에 N번 호출하는 구현 금지
- 타임아웃: connect 1초 / read 3초. 기본값(무제한) 금지
- 실패 시 **폴백**: 스냅샷 값을 사용하고 경고 로그만 남긴다. 예외를 전파해 게시판 조회를 실패시키지 않는다
- 보호: `X-Internal-Api-Key` 헤더 검증 + 외부 라우팅 제외

1차에서 board-service가 이 API를 호출하는 경로는 없다. 스냅샷으로 충분하기 때문이다. 내부 API는 2차 대비로 member-service 쪽에만 만든다.

### 4.4 회원 탈퇴 시 데이터 처리

두 서비스에 걸친 작업이지만 **2PC를 사용하지 않는다.**

1차 처리:
1. member-service가 `member.deleted = true`, Refresh Token 삭제 → 트랜잭션 종료
2. board-service는 별도 처리 없음. 스냅샷 닉네임을 그대로 노출

탈퇴 회원 표기 갱신은 2차 이벤트 동기화 범위다.

## 5. 금지 사항

| 금지 | 사유 |
| --- | --- |
| `board_db`에서 `member` 테이블 조인 | Database per Service 위반. 같은 인스턴스여도 금지 |
| `post.writer_id`에 FK 제약 설정 | 서비스 간 배포·삭제 순서를 강결합시킴 |
| `@Transactional` 안에서 원격 호출 | DB 커넥션이 네트워크 지연만큼 점유됨 |
| board → member 동기 호출을 쓰기 경로에 배치 | member 장애가 게시글 작성 실패로 전파 |
| member → board 호출 | 호출 방향은 board → member 단방향 |

## 6. 서비스 주소 관리

호출 주소를 코드에 하드코딩하지 않고 설정으로 외부화한다.

```yaml
member-service:
  url: ${MEMBER_SERVICE_URL:http://localhost:8081}
```

1차는 정적 설정으로 충분하다. 서비스 디스커버리(Eureka 등 레지스트리 서버)는 도입하지 않는다. 2차에 컨테이너를 도입하면 주소를 `http://member-service:8081`로 바꾸는 것만으로 DNS 기반 디스커버리가 된다.
