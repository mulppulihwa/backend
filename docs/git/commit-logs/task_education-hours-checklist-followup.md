# 농업교육 체크리스트 후속 조치 — condition_tree 매칭 버그 수정 및 100시간 항목 추가

**날짜**: 2026-06-07
**커밋 로그**: [342271d](https://github.com/mulppulihwa/backend/commit/342271d)

## 작업 배경

[[task_education-hours-to-checklist]]에서 `UserProfile.education_hours`를 제거하고
`condition_tree`를 `null`로 정리했다고 기록했으나, 운영 DB에는 그 fixture 변경이
실제로 반영되지 않은 상태였음 (옥천군 region_code 건과 동일한 fixture/DB 불일치 패턴).
그 결과 정책 1·10이 `_build_profile_dict()`에 더 이상 존재하지 않는
`education_hours` 필드를 조건으로 평가하다 항상 `False`를 반환 — **두 정책이
출시 이후 단 한 명에게도 매칭되지 않고 있었음**.

추가로, 사용자 요청으로 "100시간 교육 이수 확인" 체크리스트 항목을 만들면서
DB를 조사한 결과 정책 10의 `description`에 "교육 8시간 이상 이수(100시간 미만 시
D등급)"이라는 실제 등급 기준이 있음을 확인 — 100시간은 자격要件이 아니라 등급
산정 기준이므로, 전체 정책에 일괄 추가하는 대신 농업교육이 실제로 의미 있는
정책 2건에만 한정해서 추가하기로 결정.

## AS-IS

- 정책 1(귀농주택 구입 자금 지원), 10(귀농 농업창업 지원)의 `condition_tree`가
  `{"op": "AND", "children": [{"op": "gte", "field": "education_hours", "value": 8}]}`로
  남아 있음 — `evaluate_tree`가 `profile.get('education_hours')` → `None` →
  무조건 `False` 반환
- 두 정책 모두 기존에 "농업 관련 교육 8시간 이상 이수 확인서" 체크리스트 항목만 보유

## TO-BE

- 정책 1·10의 `condition_tree`를 `null`로 정리 (운영 DB 직접 수정 + `data/seed/policies.json` 동기화)
- 두 정책에 "농업 관련 교육 100시간 이상 이수 확인 (미만 시 등급 불리)" 체크리스트 항목 추가
  - 정책 1: order=8 (기존 7개 항목 뒤)
  - 정책 10: order=2 (기존 "8시간" 항목 뒤)
- `match_policies()` 재실행으로 두 정책이 정상적으로 매칭 후보에 포함됨을 확인

## 주요 변경

- `data/seed/policies.json` — `policies.checklistitem` 픽스처 2건 추가 (pk=90003, 90004; 기존 90001/90002와의 충돌 방지 컨벤션 유지)
- 운영 DB 직접 수정 (마이그레이션 아님): `policies` 테이블 `condition_tree` 컬럼 (id=1, 10 → `null`), `checklist_items` 테이블에 신규 행 2건

## 참고

- 매칭 테스트 중 별개로, 다른 정책 ~25건(id=86, 87, 95, 97, 100, 103, 109, 117, 129,
  131, 133, 137, 138, 141, 143, 145, 148, 152, 160, 164 등)의 `condition_tree`가
  `evaluate_tree`가 기대하는 `type`/`LEAF` 스키마가 아닌 `operator`/`conditions` 등
  다른 스키마로 저장되어 있어 `Unknown node type: None` 경고와 함께 항상 `False`로
  평가되고 있음을 발견. 오늘 작업과는 무관한 더 큰 범위의 사전 존재 이슈로, 별도
  triage가 필요해 보임 (손대지 않음).
