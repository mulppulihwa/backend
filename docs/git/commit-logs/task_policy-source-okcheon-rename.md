# 정책 출처 '수동입력' → '옥천군청' 변경

**날짜**: 2026-06-15
**커밋 로그**: [b4b564e](https://github.com/mulppulihwa/backend/commit/b4b564e)

## 작업 배경

수동입력(`source='수동입력'`)으로 등록된 정책 20건은 실제로 옥천군청
홈페이지에 게시된 정책임이 확인됨. API 응답의 `source` 값이 출처를
오해하게 만들지 않도록 '옥천군청'으로 표기를 변경.

## AS-IS

- `SOURCES`: `복지로`, `수동입력`, `귀농센터`
- 정책 20건의 `source = '수동입력'`
- `SOURCE_PRIORITY = {'수동입력': 0, '귀농센터': 1, '복지로': 2}`

## TO-BE

- `SOURCES`에 `옥천군청` 추가 (기존 `수동입력`은 향후 임시 입력용 기본값으로 유지)
- 마이그레이션 `0006_manual_source_to_okcheon`(`RunPython`)으로 기존
  `source='수동입력'` 20건을 `'옥천군청'`으로 일괄 변경 (역방향 마이그레이션 포함)
- `SOURCE_PRIORITY = {'옥천군청': 0, '수동입력': 0, '귀농센터': 1, '복지로': 2}`
  — 옥천 큐레이션이 매칭 결과 정렬에서 항상 최우선 노출되도록 유지

## 주요 변경

- `apps/policies/models.py`: `SOURCES`에 `('옥천군청', '옥천군청')` 추가.
- `apps/policies/migrations/0005_alter_policy_source.py`: `source` 필드
  choices 변경(`AlterField`).
- `apps/policies/migrations/0006_manual_source_to_okcheon.py`: 기존
  `수동입력` 정책 20건의 `source`를 `옥천군청`으로 변경하는 데이터 마이그레이션.
- `lib/matching/policy_matcher.py`: `SOURCE_PRIORITY`에 `옥천군청: 0` 추가,
  관련 주석 갱신.
- `tests/test_policy_matcher.py`: 로컬 `SOURCE_PRIORITY` 갱신,
  `test_sort_by_source_priority`를 `옥천군청` 기준으로 수정.
- `railway run manage.py migrate`로 운영 DB에 적용, `source='옥천군청'` 20건
  확인 완료 (`복지로: 1400, 옥천군청: 20, 귀농센터: 6`).
