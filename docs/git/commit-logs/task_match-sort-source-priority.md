# 매칭 정책 정렬 기준을 출처 우선순위로 변경

**날짜**: 2026-06-15
**커밋 로그**: (현재 커밋)

## 작업 배경

[[task_match-limit-5]]에서 매칭 결과를 상위 5개로 제한했는데, 기존
"마감 임박 순" 정렬은 옥천 큐레이션(수동입력) 정책보다 마감일이 빠른
복지로 일반 정책이 먼저 노출/저장될 수 있는 문제가 있음. 옥천 맞춤
서비스 취지에 맞게 **출처 우선순위(수동입력 > 귀농센터 > 복지로)** 를
1차 정렬 기준으로 변경.

## AS-IS

```python
# 정렬: 마감 임박 순 (마감일 없으면 뒤로)
def sort_key(p: Policy):
    if p.apply_end_date:
        days_left = (p.apply_end_date - today).days
        return (0, days_left)
    return (1, 0)
```

## TO-BE

```python
SOURCE_PRIORITY = {'수동입력': 0, '귀농센터': 1, '복지로': 2}

# 정렬: 출처 우선순위(수동입력 > 귀농센터 > 복지로) → 그 안에서 마감 임박 순
def sort_key(p: Policy):
    source_rank = SOURCE_PRIORITY.get(p.source, len(SOURCE_PRIORITY))
    if p.apply_end_date:
        days_left = (p.apply_end_date - today).days
        return (source_rank, 0, days_left)
    return (source_rank, 1, 0)
```

## 주요 변경

- `lib/matching/policy_matcher.py` — `SOURCE_PRIORITY` 상수 추가, `sort_key`에
  출처 우선순위를 1차 기준으로 추가 (마감 임박 순은 2차 기준으로 유지)
- `tests/test_policy_matcher.py`
  - `_make_policy`에 `source` 파라미터 추가
  - `_sort_key` 헬퍼 추가, `test_sort_by_deadline` 갱신
  - `test_sort_by_source_priority` 추가 (수동입력 > 귀농센터 > 복지로 검증)

## 검증

- `pytest tests/test_policy_matcher.py` — 5 passed.
- 운영 DB 샘플 프로필(35세, 귀농)로 `match_policies()` 실행 — 반환 5건 모두
  `source='수동입력'`(옥천/충북 정책)으로 노출 순서 확인.
