# 복지로 정책 DB 정리 + 그린대로 전체 크롤링 (운영 DB 적용)

**날짜**: 2026-06-15
**커밋 로그**: [aa789ce](https://github.com/mulppulihwa/backend/commit/aa789ce)

## 작업 배경

§9 6번 단계 — "정책 DB 정리(복지로 비옥천 정책 prune) + 그린대로/옥천군청
전체 크롤링". 옥천군청 어댑터는 4번 단계에서 이미 보류 결정(별도 게시판
형식 조사 필요)되어 이번 단계에서는 제외, 그린대로만 전체 크롤링.

운영 DB 확인 결과 `is_active=True` 복지로 정책 94건이 모두 `region_codes=[]`
(전국)이라 §2 plan의 "region_codes가 충북/옥천/전국이 아니거나" 조건은
현재 데이터에선 영향이 없고, 사실상 "occupation_tags에 귀농/귀촌 태그가
없으면 비활성화" 조건만 동작함. 이 기준을 수동입력/귀농센터에도 그대로
적용하면 옥천 지역 한정 정책(청년 전세/월세 지원, 농어촌 기본소득 등 —
`occupation_tags=[]`이지만 `region_codes=['43720']`)까지 비활성화되는
문제가 있어, **prune 대상을 `source='복지로'`로 한정**하기로 결정.

## AS-IS

- 복지로: 전체 1400건, `is_active=True` 94건
  - 귀농/귀촌 태그 보유 11건(어업·북한이탈주민 정착 관련)
  - 귀농/귀촌 태그 없는 83건(아동수당, 장애인법률구조, 치매치료비 등
    보편적 국가복지) — 옥천 귀농귀촌 이주자 대상 서비스 취지와 거리가 멈
- 귀농센터: 0건 (그린대로 어댑터는 4번 단계에서 트랜잭션 롤백 테스트만 진행)
- 수동입력: 20건, 전부 `is_active=True`

## TO-BE

```python
# apps/policies/management/commands/prune_policy_scope.py
def _in_scope(policy: Policy) -> bool:
    """충북/옥천 지역 또는 전국(region_codes 없음) 대상이면서,
    귀농·귀촌 태그가 있으면 유지 대상."""
    region_in_scope = (
        not policy.region_codes
        or any(code.startswith('43') for code in policy.region_codes)
    )
    has_gwiro_tag = any(tag in ('귀농', '귀촌') for tag in policy.occupation_tags)
    return region_in_scope and has_gwiro_tag
```

- `source='복지로'`, `is_active=True` 중 `_in_scope()`가 False인 정책을
  `is_active=False`로 일괄 업데이트. `--dry-run`으로 대상 목록 사전 확인 가능.
- `sync_greendaero` 전체 크롤링(`--max-items` 없이) 실행.

## 주요 변경

- `apps/policies/management/commands/prune_policy_scope.py` 신규 추가
  (커밋 `aa789ce`)
- 운영 DB 직접 실행 (코드 변경 아님):
  - `python manage.py prune_policy_scope` → 복지로 정책 83건 `is_active=False`
  - `python manage.py sync_greendaero` → 귀농센터 정책 6건 신규 저장
    (saved=6, skipped=2, low_confidence=0)

## 검증

- `--dry-run` 결과(83건)와 실제 실행 결과(83건 비활성화) 일치 확인.
- 실행 후 최종 active 현황:
  - 복지로: 94 → 11 (귀농/귀촌 관련만 유지)
  - 귀농센터: 0 → 6 (청년농업인영농정착지원금, 영농창업특성화대학,
    농업계대학지원, 맞춤형농지지원, 임대형 스마트팜, 스마트팜 청년창업
    보육센터)
  - 수동입력: 20 (변경 없음)
  - 전체 active: 114 → 37
- `pytest tests/` — 36 passed, 1 failed (기존부터 실패하던 무관 테스트,
  `test_policy_parser.py::test_pydantic_validation_error`).

## 참고 — 남은 작업 (§9)

6번(정책 DB 정리 + 그린대로 전체 크롤링) 완료. 옥천군청 어댑터는 계속
보류. 7번(계정 초기화, 최종)만 남음 — 배포/검증 완료 후 진행.
