---
title: MSA 채택과 서비스 경계
type: adr
status: accepted
version: v1
updated: 2026-09-11
read_when: "MSA로 나눈 이유나 서비스 경계 기준이 궁금할 때"
related: [README.md, ../architecture.md]
---
# 0001. MSA 채택과 서비스 경계

## 상태
accepted

## 맥락

회원 기능과 게시판 기능을 제공하는 백엔드가 필요하다. 모놀리식 단일 서버로 만들 수도 있었다.

## 결정

**member-service와 board-service 두 개로 나눈다.**

경계는 **데이터 소유권**으로 긋는다. member는 회원·인증 데이터를, board는 게시글·댓글 데이터를 소유한다.

## 근거

- 두 컨텍스트는 변경 주기와 확장 요구가 다르다. 게시판은 트래픽 급증 시 독립 확장이 필요하고, 회원은 보안 요구가 높아 변경이 보수적이다
- 두 컨텍스트 사이의 결합이 **작성자 식별자(memberId) 하나**로 최소화된다. 경계가 자연스럽게 얇다
- 학습 목적으로 MSA의 핵심 문제(데이터 분리, 서비스 간 통신, 최종 일관성)를 실제로 다뤄볼 수 있다

## 결과

- `board_db`에서 `member` 테이블을 조인할 수 없다. 작성자 닉네임 처리 방법이 필요해졌다 → [0003](0003-writer-snapshot.md)
- 인증 정보를 서비스 간에 전달할 방법이 필요해졌다 → JWT Claim 전파([../api-contract.md §5](../api-contract.md))
- 회원 탈퇴가 두 서비스에 걸친 작업이 되었다. 2PC 대신 최종 일관성을 택했다([../architecture.md §4.4](../architecture.md))
- 배포·모니터링 대상이 2배가 되었다

## 재검토 조건

서비스를 더 쪼개야 할 이유가 생기면 같은 기준(데이터 소유권)으로 판단한다. 데이터를 나눠 가질 수 없는 관심사는 서비스로 분리하지 않는다 → [0006](0006-auth-inside-member-service.md)
