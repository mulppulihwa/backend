# 2030년 이후 마감일 placeholder null 처리

**날짜**: 2026-06-16
**커밋 로그**: [fef4c54](https://github.com/mulppulihwa/backend/commit/fef4c54)

## 작업 배경

[[task_policy-deadline-null-rule]]에서 마감일 미명시 시 `null` 처리 규칙을
세웠는데, 운영 DB를 확인해보니 귀농센터 정책 1건(`맞춤형농지지원...`)의
`apply_end_date`가 `2099-12-31`로 들어가 있었음. AI가 "상시" 류 표현을
먼 미래 날짜로 잘못 변환한 것으로 추정 — 이런 값은 실제 마감일이 아니므로
같은 규칙으로 `null` 처리해야 함.

## AS-IS

- `ParsedPolicy.validate_apply_end_date`는 `YYYY-MM-DD` 형식만 검사 —
  형식만 맞으면 `2099-12-31` 같은 값도 그대로 통과.
- 운영 DB에 `apply_end_date >= 2030-01-01`인 정책 1건 존재.

## TO-BE

- `apply_end_date`의 연도가 `MAX_VALID_END_YEAR`(2030) 이상이면 `null`로
  정규화.
- 마이그레이션 `0008_clear_far_future_deadlines`로 운영 DB의 기존
  `apply_end_date >= 2030-01-01` 레코드를 일괄 `null` 처리(역방향은
  no-op — placeholder 값이라 복원 의미 없음).

## 주요 변경

- `lib/parsing/policy_parser.py`: `MAX_VALID_END_YEAR = 2030` 상수 추가,
  `validate_apply_end_date`에 연도 검사 추가.
- `apps/policies/migrations/0008_clear_far_future_deadlines.py`(신규).
- `tests/test_policy_parser.py`: `2099-12-31` → `null` 검증 테스트 추가.
- `docs/policy-data-rules.md`: "먼 미래 placeholder 방지" 섹션 추가.
- `railway run manage.py migrate`로 운영 DB 적용, `apply_end_date >= 2030`
  레코드 0건 확인.
