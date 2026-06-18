---
commit: c763f35
branch: feature/v2.0.0/welfare-sync
date: 2026-06-16
---

# Task: 옥천군 농업기술센터 정책 9개 추가

## 목적

옥천군 농업기술센터 공고문 9건을 DB에 추가한다.
출처를 `옥천군 농업기술센터`로 표시하고 기존 정책 상세 필드(지원 자격·신청 방법·신청 기관 등)에 최대한 채운 뒤, 넘치는 정보는 `description`에 기록한다.

## 변경 파일

| 파일 | 내용 |
|------|------|
| `apps/policies/models.py` | SOURCES에 `'옥천군 농업기술센터'` 추가 |
| `lib/matching/policy_matcher.py` | SOURCE_PRIORITY에 `'옥천군 농업기술센터': 0` 추가 |
| `apps/policies/management/commands/add_agri_policies.py` | 정책 데이터 하드코딩 커맨드 (신규) |

## 추가된 정책 목록

| # | 제목 | is_active | 체크리스트 |
|---|------|-----------|-----------|
| 1 | 2026년 하반기 귀농 농업창업 및 주택구입 지원사업 | True | 7개 |
| 2 | 귀농인의 집 11호 입주자 모집 | True | - |
| 3 | 2026년 하반기 로컬푸드 생산자 신규 교육 | True | - |
| 4 | 리턴팜·러스틱하우스 입주자 모집 | True | - |
| 5 | 2026년 과수 무병묘 모수포 조성 지원 | True | 3개 |
| 6 | 2027년 유기질비료 지원사업 | True | - |
| 7 | 2026년 치유농업시설 운영자 기초과정 교육 | False | - |
| 8 | 2026년 옥천로컬푸드 잡초관리 피복재 지원사업 | False | - |
| 9 | 2026년 6월 로컬푸드 요리교실 | False | - |

## 주요 처리 사항

- `source_url` / `apply_url`: URLField(max_length=200) 제한으로 쿼리 파라미터를 제거한 URL 사용
  - `https://www.oc.go.kr/agri/selectBbsNttList.do?key=1641&bbsNo=139`
- 마감된 정책(7~9번)은 `is_active=False`로 저장
- `occupation_tags`: 귀농/귀촌 관련 정책에 `['귀농', '귀촌']` 태그 부여
- `benefit_type`: 현금지원 / 시설 / 교육 구분
- `--dry-run` 옵션으로 사전 확인 후 실제 실행

## 실행 방법

```bash
# 사전 확인
railway run backend/.venv/bin/python manage.py add_agri_policies --dry-run

# 실제 추가
railway run backend/.venv/bin/python manage.py add_agri_policies
```
