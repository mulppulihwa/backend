# 정책 진단 매칭 결과를 최대 5개로 제한

**날짜**: 2026-06-15
**커밋 로그**: (현재 커밋)

## 작업 배경

프론트(`Results.jsx`)는 `/api/policies/match/` 응답의 `policies` 배열을
순회하며 각 정책을 `savePolicy()`로 `UserPolicy`에 자동 저장한다. §9 6번
(정책 DB 정리)으로 매칭 가능한 정책 풀이 늘어나면서, 매칭된 정책이 모두
반환·저장되는 문제가 있어 진단 1회당 저장 개수를 5개로 제한 요청.

## AS-IS

```python
# lib/matching/policy_matcher.py
FALLBACK_LIMIT = 10

def match_policies(user_profile: dict) -> dict:
    ...
    fallback = len(matched) == 0
    if fallback:
        matched = list(
            Policy.objects.filter(is_active=True).order_by('-created_at')[:FALLBACK_LIMIT]
        )
    return {'policies': matched, 'fallback': fallback}
```

매칭된(`fallback=False`) 경우 개수 제한이 없어, 조건을 만족하는 정책이
모두 반환되고 프론트에서 전부 `UserPolicy`로 저장됨.

## TO-BE

```python
MATCH_LIMIT = 5

def match_policies(user_profile: dict) -> dict:
    ...
    fallback = len(matched) == 0
    if fallback:
        matched = list(
            Policy.objects.filter(is_active=True).order_by('-created_at')[:MATCH_LIMIT]
        )
    else:
        matched = matched[:MATCH_LIMIT]
    return {'policies': matched, 'fallback': fallback}
```

- 마감 임박 순 정렬(`sort_key`) 이후 상위 5개만 반환 — fallback/매칭 결과
  모두 동일하게 최대 5개로 제한.

## 주요 변경

- `lib/matching/policy_matcher.py` — `FALLBACK_LIMIT = 10` → `MATCH_LIMIT = 5`,
  매칭(non-fallback) 경로에도 동일 제한 적용

## 검증

- `pytest tests/` — 36 passed, 1 failed (기존부터 실패하던 무관 테스트,
  `test_policy_parser.py::test_pydantic_validation_error`).
