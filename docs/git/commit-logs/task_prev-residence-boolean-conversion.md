# 이전 거주지(동/읍면) 속성을 boolean으로 전환

**날짜**: 2026-06-14
**커밋 로그**: [9a96857](https://github.com/mulppulihwa/backend/commit/9a96857)

## 작업 배경

v2.0.0 현장 피드백 반영(`docs/plan/v2.0.0-field-feedback-revisions.md` §1)에서
진단 질문을 "이전 거주지 도시/농촌" 2지선다로 축소하기로 결정. 기존
`prev_residence_type`(choices `'동'`/`'읍면'`)은 카카오 우편번호 검색 + 법정동명
자동분류로 채워졌으나, 새 질문은 사용자가 직접 라디오로 답하는 단순 2지선다라
choice 문자열보다 boolean이 더 적합하다고 판단.

§9에서 정리한 "정책 진단·매칭 로직 수정" 작업 순서의 1번째 단계.

## AS-IS

```python
PREV_RESIDENCE_CHOICES = [('동', '동'), ('읍면', '읍/면')]

class UserProfile(models.Model):
    prev_residence_type = models.CharField(max_length=10, choices=PREV_RESIDENCE_CHOICES, blank=True)
```

`policy_matcher.py`에서 `prev_residence_type == '읍면'`이면 귀농 정책 제외.

## TO-BE

```python
class UserProfile(models.Model):
    prev_residence_is_rural = models.BooleanField(null=True)  # 이전 거주지가 농촌(읍/면)이었는지 여부
```

`policy_matcher.py`에서 `prev_residence_is_rural is True`이면 귀농 정책 제외
(로직 동일, 비교 조건만 변경 — `None`/미답변은 기존 빈 문자열과 동일하게 필터링 안 함).

## 주요 변경

- `apps/users/models.py` — `PREV_RESIDENCE_CHOICES` 제거, `prev_residence_type` →
  `prev_residence_is_rural`(BooleanField, null=True)
- `apps/users/migrations/0006_remove_userprofile_prev_residence_type_and_more.py` —
  RemoveField + AddField (기존 13개 UserProfile의 값은 보존하지 않음 —
  §9의 최종 단계(계정 초기화)에서 재가입 예정이라 마이그레이션 불필요로 판단)
- `apps/policies/views.py` — `_build_profile_dict()` 키 변경
- `lib/matching/policy_matcher.py` — `_run_matching()`의 비교 조건 변경

## 검증

`pytest tests/test_policy_matcher.py tests/test_condition_tree.py` — 28개 통과.
운영 DB(Supabase)에 마이그레이션 적용 완료, `prev_residence_is_rural` 컬럼 생성 확인.

## 프론트엔드 후속 작업 (별도 레포, 미착수)

- `Step1.jsx` 진단 폼: 주소 검색 팝업 + bname1 자동분류 제거 →
  "예전에 사시던 곳은 도시였나요 농촌이었나요?" 2지선다(라디오) 질문으로 대체
- `PATCH /api/profile/` 요청 바디의 `prev_residence_type` → `prev_residence_is_rural`(boolean)
- `BasicInfo.jsx`의 "이전 거주지" 표시 항목 갱신 필요

## 참고 — 남은 작업 (§9)

2~7번(정책 필드 수정, region 계층 매칭 제거, 크롤링 소스 변경, 샘플 테스트,
정책 DB 정리, 계정 초기화)은 아직 미착수.
