# 정책 신청 마감일 — 미명시 시 placeholder 대신 null 처리

**날짜**: 2026-06-16
**커밋 로그**: [47c1f36](https://github.com/mulppulihwa/backend/commit/47c1f36)

## 작업 배경

옥천군청(수동입력) 정책 20건이 실제 원문에 마감일이 명시되지 않았는데도
`apply_end_date`에 "2026-12-31"(또는 17번은 "2027-12-31") placeholder가
일괄 입력돼 있었음. 이 값은 매칭 결과의 "마감 임박" 정렬과 홈 화면 마감임박
배지 로직을 왜곡시킬 수 있음. 마감일이 원문에 명시된 경우에만 값을 채우고,
없으면 `null`로 두어 프론트가 "신청기간 확인"으로 표시할 수 있게 규칙을 정리.

## AS-IS

- 옥천군청 20건 전부 `apply_end_date = 2026-12-31`(17번만 2027-12-31)로
  하드코딩 — 원문에 해당 날짜에 대한 근거 없음.
- `ParsedPolicy.apply_end_date`는 AI가 "예산소진시까지" 같은 비날짜 문자열을
  반환해도 그대로 통과.
- `bokjiro_sync`는 AI 파싱 결과의 `apply_end_date`를 전혀 정책에 반영하지
  않음(필드 복사 목록에 없음) — 복지로 정책은 항상 `null`.

## TO-BE

- `ParsedPolicy.validate_apply_end_date`: `YYYY-MM-DD` 형식이 아니면(예: '상시',
  '예산소진시까지') `null`로 정규화.
- `bokjiro_sync`: AI가 유효한 `apply_end_date`를 추출하면 정책에 반영.
- 옥천군청 20건의 `apply_end_date`를 모두 `null`로 정리(마이그레이션
  `0007_clear_okcheon_placeholder_deadlines`, 역방향 포함) + seed 데이터
  동기화. seed 데이터의 `source`도 `수동입력` → `옥천군청`으로 함께 정리.
- `docs/policy-data-rules.md`: 신청 기간(`apply_start_date`/`apply_end_date`)과
  `source` 표기에 대한 관리 규칙 문서화.

## 주요 변경

- `lib/parsing/policy_parser.py`: `DATE_RE` + `validate_apply_end_date` 필드
  검증기 추가.
- `lib/sync/adapters/bokjiro_sync.py`: `apply_end_date` 필드를 파싱 결과에서
  반영하도록 추가 (`date.fromisoformat`).
- `apps/policies/migrations/0007_clear_okcheon_placeholder_deadlines.py`(신규):
  `source='옥천군청'` 정책의 `apply_end_date`를 `null`로 변경(데이터 마이그레이션,
  역방향 포함).
- `data/seed/policies.json`: pk 1~20의 `apply_end_date`를 `null`로,
  `source`를 `옥천군청`으로 갱신.
- `tests/test_policy_parser.py`: `apply_end_date` 형식 검증 테스트 2건 추가.
- `railway run manage.py migrate`로 운영 DB에 적용, 옥천군청 20건 전부
  `apply_end_date = null` 확인 완료.
