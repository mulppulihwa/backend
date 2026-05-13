# 브랜치 전략 섹션 추가 및 섹션 번호 정리

**날짜**: 2026-05-13
**커밋 로그**: [6f703aa](https://github.com/mulppulihwa/backend/commit/6f703aa)

## 작업 배경

backend-plan.md에 브랜치 전략이 문서화되어 있지 않았음.
백엔드 1인 개발 구조에 맞는 깃플로우 간소화 버전 설계 후 플랜에 반영.

## AS-IS

- 브랜치 전략 문서 없음
- §11~13 섹션 번호 중복 (브랜치 섹션 삽입으로 발생)

## TO-BE

- §11 브랜치 전략 신설
- §12~17 번호 순서 정리 완료

## 주요 변경

- `main` / `develop` / `feature/xxx` 3단계 브랜치 구조 확정
- `main`은 Railway 배포 트리거, 직접 push 금지
- 브랜치 명명 규칙 및 커밋 메시지 prefix 규칙 추가
