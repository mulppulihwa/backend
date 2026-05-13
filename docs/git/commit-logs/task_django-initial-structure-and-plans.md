# Django 백엔드 초기 구조 및 플랜 문서 추가

**날짜**: 2026-05-13
**커밋 로그**: [e51f234](https://github.com/mulppulihwa/backend/commit/e51f234)

## 작업 배경

백엔드 레포(mulppulihwa/backend)에 README.md만 있는 빈 상태였음.
엔지니어링 리뷰(plan-eng-review) 결과를 반영해 초기 Django 프로젝트 구조와 핵심 로직을 먼저 구성함.

## AS-IS

- 레포에 README.md만 존재
- 백엔드 코드 없음
- 플랜 문서가 socialventure/ 루트에 분산

## TO-BE

- Django 앱 구조 (apps/users, apps/policies), 핵심 lib, 테스트, 플랜 문서 일괄 추가
- docs/를 backend/ 내부로 이동해 레포에서 직접 관리

## 주요 변경

- **apps/users**: User/UserProfile 모델, 카카오 OAuth 뷰, post_save 시그널 (UserProfile 자동 생성)
- **apps/policies**: Policy 모델 (`disability_required` 포함), 매칭/파싱 뷰
- **lib**: policy_matcher (income_level·disability SQL 필터 포함), condition_tree, policy_parser, region_hierarchy — 전체 에러처리 포함
- **tests**: condition_tree·policy_parser·policy_matcher 유닛테스트 25개
- **docs/plan**: backend-plan (복지로 API 섹션 포함), platform-plan 최신화
- **.gitignore**: .claude, .venv, .env 제외
