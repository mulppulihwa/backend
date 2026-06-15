# 정책 상세 조회 API 추가

**날짜**: 2026-06-15
**커밋 로그**: (현재 커밋)

## 작업 배경

프론트 `Detail.jsx`는 별도 API 없이 목록(`/match/`, `/preview/`)에서 받은
카드 데이터(`PolicyCardSerializer`)와 하드코딩된 placeholder 텍스트로
상세 화면을 구성하고 있었음. `PolicyDetailSerializer`(§4에서 추가한
`published_at`/`source_url` 포함)는 정의돼 있었지만 어떤 API에서도
사용되지 않는 상태였음.

## AS-IS

- `apps/policies/urls.py`: `preview/`, `match/`, `parse/`,
  `<int:policy_id>/checklist/`만 존재 — 단건 상세 조회 라우트 없음
- `PolicyDetailSerializer` 미사용

## TO-BE

```python
# apps/policies/views.py
class PolicyDetailView(APIView):
    """정책 상세 조회."""

    def get(self, request, policy_id):
        try:
            policy = Policy.objects.get(pk=policy_id, is_active=True)
        except Policy.DoesNotExist:
            return Response(
                {'error': '정책을 찾을 수 없습니다.', 'code': 'policy_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(PolicyDetailSerializer(policy).data)
```

```python
# apps/policies/urls.py
path('<int:policy_id>/', PolicyDetailView.as_view()),
```

- `GET /api/policies/<id>/` — `is_active=True`인 정책만 조회 가능(없으면 404),
  `PolicyChecklistView`/`UserPolicySaveView`와 동일한 관습.
- 반환 필드(`PolicyDetailSerializer`, 변경 없음): `id`, `title`, `summary`,
  `description`(신청 자격/상세 설명 — 31/37건에 데이터 존재), `benefit_type`,
  `amount`, `amount_text`, `apply_start_date`, `apply_end_date`, `apply_url`,
  `managing_org`, `source_url`, `source`, `published_at`, `updated_at`.
- "신청 서류"(`Detail.jsx`의 하드코딩 섹션)는 이 API 범위 밖 — 이미
  `/api/policies/<id>/checklist/`(준비물 API)가 별도로 커버.

## 주요 변경

- `apps/policies/views.py` — `PolicyDetailView` 추가
- `apps/policies/urls.py` — `<int:policy_id>/` 라우트 추가

## 검증

- `pytest tests/` — 37 passed, 1 failed (기존부터 실패하던 무관 테스트).
- Django test client로 운영 DB against 확인:
  - `GET /api/policies/1/` → 200, `description`/`amount`/`apply_end_date`/
    `managing_org` 등 정상 반환
  - `GET /api/policies/999999/` → 404 `policy_not_found`
  - `GET /api/policies/1/checklist/` → 200 (기존 라우트와 충돌 없음)

## 참고

- 프론트 `Detail.jsx`를 이 API로 연동하는 작업은 별도 — 프론트 레포는
  사용자 명시 요청 전까지 수정하지 않음.
