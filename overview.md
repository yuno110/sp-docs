---
title: 프로젝트 개요
type: explanation
status: living
version: v2
updated: 2026-09-15
read_when: "프로젝트의 목표·범위·용어를 확인할 때. 처음 합류했을 때 가장 먼저"
related: [architecture.md, plan/phase1.md, plan/phase2.md]
---
# 프로젝트 개요

## 1. 목표

회원 인증/인가와 게시판(게시글·댓글)을 제공하는 **REST API 백엔드 시스템**을 MSA로 구축한다. 프론트엔드와 완전히 분리된 서버로 JSON API만 제공한다.

## 2. 서비스 구성

| 서비스 | 저장소 | 책임 | 포트 | 스키마 |
| --- | --- | --- | --- | --- |
| auth-service | `yuno110/sp-auth` | 계정(이메일·비밀번호·권한), 인증, **JWT 발급** | 8083 | `sp_auth` |
| member-service | `yuno110/sp-member` | 프로필(닉네임), 내부 API 제공 | 8081 | `sp_member` |
| board-service | `yuno110/sp-board` | 게시글, 댓글 | 8082 | `sp_board` |

**계정과 프로필이 갈라져 있다.** 그래서 가입과 탈퇴가 각각 2단계다([adr/0012](adr/0012-auth-as-separate-service.md)).

서비스 경계와 통신 방식은 [architecture.md](architecture.md)를 본다.

## 3. 범위

### 3.1 1차 (MVP)

- 회원가입, 로그인·로그아웃·토큰 재발급
- 내 정보 조회·수정, 비밀번호 변경, 회원 탈퇴
- 게시글 CRUD, 목록(페이징·검색·정렬), 조회수
- 댓글 CRUD
- 권한 제어(작성자 본인 / 관리자)
- 공통 응답·예외 처리, API 문서(Swagger UI)

상세 항목은 [requirements/member.md](requirements/member.md), [requirements/board.md](requirements/board.md)에 있다.

### 3.2 2차

Kafka 도입(닉네임 즉시 반영), Docker 컨테이너화, API Gateway, 좋아요·파일 첨부·카테고리·대댓글 등. [plan/phase2.md](plan/phase2.md)를 본다.

### 3.3 범위 제외

- 프론트엔드 화면
- 실시간 알림(WebSocket), 채팅
- 소셜 로그인(OAuth2)
- 결제, 정산

## 4. 용어

| 용어 | 설명 |
| --- | --- |
| Account | 인증 주체. 이메일·비밀번호·권한. **auth-service가 소유** |
| Member (프로필) | 표시 정보. 닉네임. **member-service가 소유** |
| accountId | **전역 식별자.** auth가 발급하고 세 서비스가 공유한다. JWT의 `sub` |
| Post / Comment | 게시글 / 댓글. board-service가 소유 |
| Access Token | API 호출용 단기 인증 토큰 (JWT) |
| Refresh Token | Access Token 재발급용 장기 토큰 |
| Soft Delete | 실제 삭제 대신 `deleted` 플래그로 처리하는 논리 삭제 |
| 2단계 가입 | 계정 생성(auth) → 로그인 → 프로필 등록(member). 원자적이지 않다 |
| 2단계 탈퇴 | 계정 탈퇴(auth, 비밀번호 재확인) → 프로필 탈퇴(member). **순서를 바꾸지 않는다** |
| 스냅샷 | 타 서비스 소유 데이터를 기록 시점 값으로 복제 저장하는 것 |
| 내부 API | 서비스 간 호출 전용 API. 외부에 노출하지 않음 (`/internal/**`) |

## 5. 확정된 주요 결정

이유는 각 ADR을 본다.

| 항목 | 결정 | 근거 |
| --- | --- | --- |
| 아키텍처 | MSA (auth / member / board 3개 서비스) | [adr/0001-msa-adoption.md](adr/0001-msa-adoption.md) |
| 저장소 | 서비스별 분리 + 문서 전용 저장소 | [adr/0002-separate-repositories.md](adr/0002-separate-repositories.md) |
| 작성자 정보 | 스냅샷 복제 | [adr/0003-writer-snapshot.md](adr/0003-writer-snapshot.md) |
| JWT 서명 | RS256 (비대칭키) | [adr/0004-rs256-over-hs256.md](adr/0004-rs256-over-hs256.md) |
| 컨테이너 | 1차 미사용, 2차 도입 | [adr/0005-no-docker-in-mvp.md](adr/0005-no-docker-in-mvp.md) |
| auth 도메인 | **별도 서비스로 분리** | [adr/0012-auth-as-separate-service.md](adr/0012-auth-as-separate-service.md) (0006을 대체) |
| 공통 코드 | Spring 표준 활용 + 최소 복제 | [adr/0007-shared-code-policy.md](adr/0007-shared-code-policy.md) |
| API 버전 | `/api/v1` 경로 버저닝 | [adr/0008-api-versioning.md](adr/0008-api-versioning.md) |
| Gateway | 2차 이연 | [adr/0009-gateway-deferred.md](adr/0009-gateway-deferred.md) |
| 닉네임 동기화 | 2차 Kafka 이벤트 | [adr/0010-kafka-for-nickname-sync.md](adr/0010-kafka-for-nickname-sync.md) |
| 시간대 | JVM 시간대는 실행 환경이 정한다 | [adr/0011-timezone-from-environment.md](adr/0011-timezone-from-environment.md) |

그 외 확정 사항: 운영 DB는 MySQL 8.0, 시간대는 KST(`Asia/Seoul`) 통일, 동적 검색은 QueryDSL, 빌드는 Gradle, 탈퇴 계정 이메일 재사용 불가.

### 1차에서 의도적으로 포기한 것

"해결됨"이 아니라 "감수함"이다. 전체 목록과 근거는 [adr/0012](adr/0012-auth-as-separate-service.md)에 있다.

| 포기한 것 | 결과 |
| --- | --- |
| 원자적 가입 | "계정만 있는 상태"가 정상 상태가 된다 |
| 원자적 탈퇴 | 2단계. 중간 실패를 순서와 멱등으로 다룬다 |
| 탈퇴 후 토큰 즉시 차단 | 최대 30분 노출. ADMIN이면 타인 글 삭제 포함 |
| 미완료 가입 계정 정리 | 이메일이 선점된 채 남는다 |
| 쓰기 경로의 member 독립성 | member 장애 시 새 글·댓글 작성이 중단된다 |
