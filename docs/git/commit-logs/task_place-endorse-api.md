# 사용처 추천하기(추천해요) API 추가

**날짜**: 2026-08-20
**커밋 로그**: [e80b914](https://github.com/mulppulihwa/backend/commit/e80b914)

## 작업 배경

신뢰도 기반 안심 검증 마크(뱃지 + 추천) 기능 구현 플랜의 Task 3. Task 1에서
`PlaceEndorsement` 모델과 뱃지 필드를, Task 2에서 `LocalPlaceSerializer`의
`endorsement_count`/`is_endorsed` 노출(N+1 방지 annotate)을 추가했고, 이번
Task 3에서 실제로 사용자가 "추천해요" 버튼을 눌러 추천을 남기는 POST 엔드포인트를
구현했다.

## AS-IS

- `PlaceEndorsement` 레코드를 만들 수 있는 API가 없어 Django Admin에서 수동으로
  넣거나 테스트 코드에서 직접 `objects.create()`하는 방법뿐이었음.
- `apps/places/urls.py`에는 목록(`''`)과 상세(`'<int:pk>/'`) 라우트만 존재.

## TO-BE

- `POST /api/places/<int:pk>/endorse/` — 로그인 사용자가 사용처를 추천.
  - `IsAuthenticated` 필수, 미인증 시 401.
  - 존재하지 않거나 비활성(`is_active=False`) 사용처는 404,
    `{'error': '사용처를 찾을 수 없습니다.', 'code': 'place_not_found'}`
    (`PlaceDetailView`와 동일한 에러 메시지/코드 재사용).
  - `PlaceEndorsement.objects.get_or_create(place=place, user=request.user)`로
    처리 — 같은 사용자가 두 번 눌러도 `IntegrityError` 없이 멱등하게 동작
    (Task 1에서 건 `unique_together` 제약을 신뢰).
  - 응답: `{'endorsement_count': <int>, 'is_endorsed': True}`.

## 주요 변경

- `apps/places/views.py`: 파일 끝에 `PlaceEndorseView(APIView)` 추가.
- `apps/places/urls.py`: `path('<int:pk>/endorse/', PlaceEndorseView.as_view())`
  추가 (3번째 라우트).
- `tests/test_places_endorsement.py`: API 레벨 테스트 4건 추가 —
  `test_endorse_requires_auth`(401),
  `test_endorse_increments_count`(200 + 카운트/플래그 확인),
  `test_endorse_twice_is_idempotent`(중복 클릭해도 레코드 1개·200 유지),
  `test_endorse_nonexistent_place_404`(404 + `place_not_found` 코드).
- 전체 테스트 스위트(`pytest tests/`) 75건 전부 통과 확인.
