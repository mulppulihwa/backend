# 정책 상세 — 게시일(published_at) 필드 추가

**날짜**: 2026-06-14
**커밋 로그**: [9515324](https://github.com/mulppulihwa/backend/commit/9515324)

## 작업 배경

v2.0.0 현장 피드백(`docs/plan/v2.0.0-field-feedback-revisions.md` §4): "정책
상세정보 더 추가 - 정보 출처로 가는 하이퍼링크(or 경로), 언제 업로드 되었는지".
`source_url`은 이미 모델/시리얼라이저에 존재했으나, "원문 공고가 실제 게시된
날짜"를 나타내는 필드는 없었음.

§9 작업 순서의 2번째 단계(정책 필드 수정) — additive 변경이라 기존 정책
데이터(1,420건)에는 영향 없음.

## AS-IS

- `Policy`에 게시일 관련 필드 없음 (`created_at`/`updated_at`은 우리 DB 저장
  시점일 뿐, 원문 공고 게시일과 다름)
- `PolicyDetailSerializer`에 `updated_at` 미포함

## TO-BE

```python
class Policy(models.Model):
    ...
    published_at = models.DateField(null=True, blank=True)  # 원문 공고 게시일
```

## 주요 변경

- `apps/policies/models.py` — `Policy.published_at` (DateField, null/blank) 추가
- `apps/policies/migrations/0004_policy_published_at.py` — 필드 추가 마이그레이션
- `apps/policies/serializers.py` — `PolicyDetailSerializer.fields`에
  `published_at`, `updated_at` 추가
- `apps/policies/admin.py` — "신청 정보" fieldset에 `published_at` 추가
  (Django Admin에서 수동 입력 가능)

## 검증

`pytest tests/` — 36 passed, 1 failed(`test_policy_parser.py::test_pydantic_validation_error`,
이번 변경과 무관한 기존 실패 — 변경 전 커밋에서도 동일하게 실패함을 확인).
운영 DB(Supabase)에 마이그레이션 적용 완료.

## 참고 — 남은 작업

- 기존 정책 데이터의 `published_at`/`source_url` 값 보강(노가다)은 §2 축소
  작업과 함께 진행 예정.
- `lib/parsing/policy_parser.py`에 `published_at` 자동 추출 추가는 보류
  (§4 "검토" 항목, 후속 결정).
- §9 3번(정책 매칭로직 설계 — region 계층 매칭 제거) 이어서 진행.
