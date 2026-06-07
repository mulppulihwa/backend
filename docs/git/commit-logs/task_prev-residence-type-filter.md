# 이전 거주지(동/읍면) 속성 추가 및 귀농 정책 매칭 보정

**날짜**: 2026-06-07
**커밋 로그**: [d3a5211](https://github.com/mulppulihwa/backend/commit/d3a5211)

## 작업 배경

진단 단계에서 사용자의 이전 거주지가 도시(동)인지 농촌(읍/면)인지가
귀농 정책 매칭 정확도에 중요해짐. 정책 자격요건 문서 자체가 "도시지역(동 지역)"을
공식 정의로 사용하므로, 동/읍면 이분법을 매칭에 반영하기로 함.

다만 "보수적으로 많은 정책을 노출"하고 싶다는 요구에 따라 비대칭 필터로 설계:
- **읍/면 출신**: 이미 농촌에 거주 중 → 도시→농촌 이주를 전제로 한 귀농 정책 자격이 없는 게 확실 → 매칭에서 제외
- **동 출신**: 귀농 여부가 불확실 (모든 동 거주자가 귀농 예정자는 아님) → 필터링하지 않고 그대로 노출, 정책 상세/체크리스트로 사용자가 직접 자격 확인

값 입력 방식은 주소 API 연동(다음 우편번호 서비스)으로 받은 법정동명의
끝 글자(읍/면/동)를 프론트에서 분류해 전달하는 방향으로 결정 — 별도
행정구역 데이터셋 구축이나 자체 드롭다운보다 비용이 훨씬 낮음.

## AS-IS

- `UserProfile`에 이전 거주지 관련 속성 없음
- 귀농(`occupation_tags=['귀농']`) 정책 매칭이 사용자의 실제 이전 거주지와 무관하게 동작

## TO-BE

- `UserProfile.prev_residence_type` 필드 추가 (choices: `'동'` / `'읍면'`)
- `_build_profile_dict()`가 이 값을 매칭 엔진에 전달
- `_run_matching()`에서 `prev_residence_type == '읍면'`이면 `occupation_tags__contains=['귀농']` 정책을 쿼리에서 제외

## 주요 변경

- `apps/users/models.py` — `PREV_RESIDENCE_CHOICES`, `UserProfile.prev_residence_type` 추가
- `apps/users/migrations/0005_userprofile_prev_residence_type.py` — 필드 추가 마이그레이션
- `apps/policies/views.py` — `_build_profile_dict()`에 `prev_residence_type` 키 추가
- `lib/matching/policy_matcher.py` — `_run_matching()`에 단방향 exclude 필터 추가

## 검증

트랜잭션 롤백 환경에서 `match_policies()` 호출해 확인 (`occupation_tags=['귀농']` 프로필 기준):

| prev_residence_type | 매칭 정책 수 | 그중 귀농 태그 정책 수 |
|---|---|---|
| 읍면 | 9 | 0 |
| 동 | 11 | 2 |
| (미입력) | 11 | 2 |

## 프론트엔드 후속 작업 (별도 레포)

- 진단 폼에 "이전 거주지" 질문 단계 추가
- 다음(Daum) 우편번호 검색 위젯 연동 → 응답의 법정동명(`bname` 등) 끝 글자로 `'동'`/`'읍면'` 분류
- `PATCH /api/profile/` 요청에 `prev_residence_type` 포함
