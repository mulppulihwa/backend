# 농업교육 이수 요건을 프로필 필드에서 정책 체크리스트로 이동

**날짜**: 2026-06-07
**커밋 로그**: [c24ac49](https://github.com/mulppulihwa/backend/commit/c24ac49)

## 작업 배경

`UserProfile.education_hours`로 "농업교육 OO시간 이수" 자격을 표현하고 있었으나,
정책마다 요구 시간(8시간/100시간 등)이 달라 단일 숫자 필드 + 매칭 조건으로는
일관되게 표현하기 어려웠음. 팀 논의 결과 프로필 속성에서 빼고 다른 준비물(구비서류)과
동일하게 정책 체크리스트 항목으로 노출해 사용자가 직접 체크하도록 하기로 결정.

## AS-IS

- `UserProfile.education_hours = SmallIntegerField(default=0)` — 사용자가 입력하는 숫자 필드
- `_build_profile_dict()`(`apps/policies/views.py`)가 이 값을 매칭 엔진에 전달
- 정책의 `condition_tree`에 `{"field": "education_hours", "op": "gte", "value": 8}` 형태로 자격 조건 박혀 있음 (`data/seed/policies.json` pk=1, pk=10)

## TO-BE

- `UserProfile.education_hours` 필드 제거 (마이그레이션 `0004_remove_userprofile_education_hours`)
- `_build_profile_dict()`에서 `education_hours` 항목 제거 — 매칭 조건에서 더 이상 사용하지 않음
- 해당 두 정책의 `condition_tree`에서 `education_hours` 조건 삭제 (`condition_tree: null`)
- 같은 두 정책에 `policies.checklistitem` 픽스처로 "농업 관련 교육 8시간 이상 이수 확인서" 항목 추가 — 기존 준비물과 동일하게 `order` + `label`만으로 표현, 사용자는 `checked_items`로 체크

## 주요 변경

- `apps/users/models.py` — `education_hours` 필드 삭제
- `apps/users/migrations/0004_remove_userprofile_education_hours.py` — 필드 제거 마이그레이션
- `apps/policies/views.py` — `_build_profile_dict()`에서 `education_hours` 키 삭제
- `data/seed/policies.json` — pk=1, pk=10의 `condition_tree`를 `null`로 정리, `ChecklistItem` 픽스처 2건(pk=1, pk=2) 추가

## 참고

복지로 API에서 동기화되는 정책의 경우, 농업교육 시간 요건이 `구비서류`/`선정기준` 텍스트에
포함돼 있으면 기존 `_fetch_checklist_labels` 동기화 로직이 자동으로 체크리스트 항목으로
끌어올 가능성이 높음 — 별도 파싱 로직 추가 불필요해 보이나 실제 텍스트 형태 확인 필요.
