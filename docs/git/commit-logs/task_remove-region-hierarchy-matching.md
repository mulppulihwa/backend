# 정책 매칭 — region 계층 기반 매칭 제거

**날짜**: 2026-06-14
**커밋 로그**: [1f3f1d9](https://github.com/mulppulihwa/backend/commit/1f3f1d9)

## 작업 배경

v2.0.0 현장 피드백(`docs/plan/v2.0.0-field-feedback-revisions.md` §1) — 향후
크롤링 소스를 그린대로/옥천군청 두 곳으로 한정하기로 결정. 이 두 소스에서
가져오는 정책은 이미 옥천 대상임이 보장되므로, region 계층 비교(상위
행정구역까지 포함한 집합 ∩ 정책의 `region_codes`) 매칭이 더 이상 필요 없음.

운영 DB 조사 결과(§9): 복지로 정책 1,400건 중 1,399건이 `region_codes=[]`(전국)
이고, `region_codes=[]`는 기존 로직에서도 region 필터를 무조건 통과했음 →
이번 변경으로 기존 정책 노출 범위가 바뀌지 않음.

§9 작업 순서의 3번째 단계(정책 매칭로직 설계).

## AS-IS

```python
# lib/matching/policy_matcher.py
from .region_hierarchy import get_ancestor_codes

def match_policies(user_profile):
    region_code = user_profile.get('region_code', '')
    try:
        ancestor_codes = get_ancestor_codes(region_code)  # regions 테이블 recursive CTE
    except Exception:
        ancestor_codes = [region_code] if region_code else []
    matched = _run_matching(age, occ_tags, income, ancestor_codes, user_profile)

def _run_matching(..., ancestor_codes, user_profile):
    if ancestor_codes:
        qs = qs.filter(region_codes__exact=[]) | qs.filter(region_codes__overlap=ancestor_codes)
    ...
```

`_build_profile_dict()`는 `region_code`를 매칭 엔진에 전달했고,
`_build_match_reason()`은 `region_code`와 `policy.region_codes`가 둘 다
비어있지 않으면 "지역 조건 충족"을 매칭 이유로 표시했음.

## TO-BE

- `policy_matcher.py`에서 `get_ancestor_codes` 호출과 region 필터 블록 제거,
  `_run_matching()` 시그니처에서 `ancestor_codes` 제거.
- `lib/matching/region_hierarchy.py` 삭제 — 다른 곳에서 참조 없음(dead code).
- `_build_profile_dict()`에서 `region_code` 키 제거 — 매칭에서 더 이상 사용 안 함.
- `_build_match_reason()`의 "지역 조건 충족" 문구 제거 — 매칭 로직과 무관해져서
  더 이상 정확하지 않은 표시였음.
- `lib/exceptions.py`의 `MatchingError` docstring 예시("region_code 누락 등")
  정리.

`Policy.region_codes`(필드+GIN 인덱스), `Region` 모델, `UserProfile.region_code`
필드 자체는 **삭제하지 않고 메타데이터로 유지** — 추후 데이터 분석/표시용으로
남겨둠.

## 주요 변경

- `lib/matching/policy_matcher.py` — region 계층 매칭 로직 제거
- `lib/matching/region_hierarchy.py` — 파일 삭제
- `apps/policies/views.py` — `_build_profile_dict()`/`_build_match_reason()` 정리
- `lib/exceptions.py` — `MatchingError` docstring 정리
- `tests/test_policy_matcher.py` — `get_ancestor_codes` mock 의존 테스트 정리
  (`test_ancestor_codes_failure_uses_empty` 제거, 나머지는 데코레이터만 정리)
- `docs/plan/v2.0.0-field-feedback-revisions.md` §3 — stale `get_ancestor_codes`
  캐싱 제안 제거

## 검증

`pytest tests/` — 35 passed, 1 failed (기존부터 실패하던 무관 테스트,
`test_policy_parser.py::test_pydantic_validation_error`).

## 참고 — 남은 작업 (§9)

4번(정책 크롤링 source 수정 — 그린대로/옥천군청 어댑터) 이어서 진행.
