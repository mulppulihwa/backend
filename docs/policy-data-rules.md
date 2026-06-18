# 정책 DB 관리 규칙

## 신청 기간 (`apply_start_date` / `apply_end_date`)

**원칙: 원문(공고문/출처 페이지)에 구체적인 날짜가 명시된 경우에만 값을 채운다.
명시되지 않았거나 "상시", "수시", "예산 소진 시까지" 등 비확정 표현이면 `null`로 둔다.**

- `null`을 임의의 날짜(예: "일단 연말로")로 채우지 않는다. placeholder 날짜는
  매칭 정렬(`apply_end_date` 기준 마감임박순)과 홈 화면 "마감임박" 노출 로직을
  왜곡시킨다.
- 프론트엔드는 `apply_end_date: null`을 "상시 모집" 또는 "신청기간 확인 필요"로
  표시하고, D-day/마감임박 배지는 값이 있을 때만 노출한다.

### 출처별 적용

- **복지로 / 귀농센터(그린대로)** — `lib/parsing/policy_parser.py`의 AI 파싱 결과
  `apply_end_date`를 사용한다. `ParsedPolicy.validate_apply_end_date`가
  `YYYY-MM-DD` 형식이 아닌 값(예: "예산소진시까지")은 자동으로 `null`로
  정규화하므로, sync 어댑터(`bokjiro_sync`, `greendaero_sync`)는 검증된 값만
  받는다.

### 먼 미래 placeholder 방지

`apply_end_date`의 연도가 `MAX_VALID_END_YEAR`(2030) 이상이면 — AI가 "상시"를
"9999-12-31"/"2099-12-31" 등으로 잘못 변환한 경우 — `null`로 정규화한다
(`lib/parsing/policy_parser.py`의 `validate_apply_end_date`). 2026-06-16:
귀농센터 정책 1건(`2099-12-31`)을 마이그레이션
`0008_clear_far_future_deadlines`로 정리.
- **옥천군청(수동입력)** — 등록·수정 시 옥천군청 등 원출처 페이지에 명시된
  마감일이 있을 때만 입력한다. 명시된 마감일이 없으면 `apply_end_date`를
  비워(`null`) 둔다. (2026-06-16: 기존 20건에 일괄 입력돼 있던 "2026-12-31"
  placeholder를 모두 `null`로 정리 — `0007_clear_okcheon_placeholder_deadlines`)

## 출처(`source`) 표기

- `복지로`: 복지로 Open API 동기화
- `귀농센터`: 그린대로(greendaero.go.kr) 동기화
- `옥천군청`: 옥천군청 등 지자체 홈페이지 게시 정책의 수동 큐레이션
  (2026-06-15부터 `수동입력`을 대체)
- `수동입력`: 위 세 출처에 속하지 않는 임시/기타 수동 입력 (기본값 유지)
- 매칭 정렬 우선순위(`SOURCE_PRIORITY`, `lib/matching/policy_matcher.py`)는
  `옥천군청`/`수동입력` > `귀농센터` > `복지로` 순서를 유지한다.
