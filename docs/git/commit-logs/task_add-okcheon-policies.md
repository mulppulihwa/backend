---
commit: 7d2254c
branch: feature/v2.0.0/welfare-sync
date: 2026-06-16
---

# Task: 옥천군청 정책 4개 추가

## 목적

옥천군청 공고문 4건을 DB에 추가한다. 출처 `옥천군청`.

## 변경 파일

| 파일 | 내용 |
|------|------|
| `apps/policies/management/commands/add_okcheon_policies.py` | 정책 데이터 하드코딩 커맨드 (신규) |

## 추가된 정책 목록

| # | 제목 | is_active | 체크리스트 |
|---|------|-----------|-----------|
| 1 | 2026년 충북행복결혼공제 모집 | True | - |
| 2 | 옥천군 농어촌 기본소득 | True | 6개 |
| 3 | 2026년 청년 부동산 중개보수 및 이사비 지원 | True | - |
| 4 | 2026년 청년농업인 영농정착지원사업 2차 | True | 3개 |

## 주요 매핑

| 정책 | min_age | max_age | occupation_tags | benefit_type |
|------|---------|---------|-----------------|--------------|
| 충북행복결혼공제 | 19 | 39 | [] | 현금지원 |
| 농어촌 기본소득 | 0 | 130 | [] | 현금지원 |
| 청년 부동산 지원 | 19 | 39 | [] | 현금지원 |
| 청년농업인 영농정착 | 18 | 39 | ['귀농'] | 현금지원 |

- 영농정착지원사업 `apply_url`: `https://uni.nongupez.go.kr`
- 나머지 `apply_url`: `https://www.oc.go.kr`

## 실행 방법

```bash
railway run backend/.venv/bin/python manage.py add_okcheon_policies --dry-run
railway run backend/.venv/bin/python manage.py add_okcheon_policies
```
