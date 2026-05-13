# Eng Review 2차 — 누락 항목 4건 수정

**날짜**: 2026-05-13
**커밋 로그**: [ef6aaee](https://github.com/mulppulihwa/backend/commit/ef6aaee)

## 작업 배경

backend-plan.md에 대해 2차 /plan-eng-review 진행.
1차에서 놓친 4건의 블로킹/일관성 이슈 발견 및 수정.

## AS-IS

- `serializers.py` 미정의 → 서버 시작 시 ImportError
- `BOKJIRO_API_KEY` §4 env vars 목록 누락
- Policy SOURCES에 제외된 '보조금24' 잔존
- `sync_bokjiro` 1페이지만 수집 후 종료

## TO-BE

- PolicyCardSerializer, PolicyDetailSerializer §7-2에 정의
- BOKJIRO_API_KEY §4에 추가
- SOURCES = ['복지로', '수동입력', '귀농센터'] 3개로 정리
- sync_bokjiro totalCount 기준 전체 페이지 루프

## 주요 변경

- backend-plan.md §7-2 신설 (Serializers)
- backend-plan.md §4 BOKJIRO_API_KEY 추가
- backend-plan.md + apps/policies/models.py SOURCES 수정
- backend-plan.md §10 sync_bokjiro 페이지네이션 루프 추가
