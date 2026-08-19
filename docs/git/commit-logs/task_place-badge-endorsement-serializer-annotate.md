# LocalPlace API에 신뢰도 뱃지/추천수/추천여부 노출 (N+1 방지 annotate)

**날짜**: 2026-08-20
**커밋 로그**: [2b40f96](https://github.com/mulppulihwa/backend/commit/2b40f96)

## 작업 배경

신뢰도 기반 안심 검증 마크(뱃지 + 추천) 기능 구현 플랜의 Task 2. Task 1에서
추가한 뱃지 필드와 `PlaceEndorsement` 모델을 실제로 `GET /api/places/`
응답에 노출한다. 사용처 개수가 늘어나도 목록 조회가 느려지지 않도록
N+1 쿼리를 처음부터 피하는 것이 핵심.

## AS-IS

- `LocalPlaceSerializer`에 뱃지 필드, 추천수, 추천여부가 노출되지 않음.
- `PlaceListView.get`이 `LocalPlace.objects.filter(is_active=True)`를
  그대로 직렬화 — 만약 여기서 사용처마다 `place.endorsements.count()`를
  단순 호출하면 목록 개수만큼 쿼리가 추가로 나가는 N+1 문제가 생김.

## TO-BE

- `LocalPlaceSerializer`에 `endorsement_count`, `is_endorsed`
  (`SerializerMethodField`) 및 기존 뱃지 필드(`okcheon_news_recommended`,
  `counseling_center_recommended`) 노출 추가.
  - `get_endorsement_count`/`get_is_endorsed`는 뷰가 미리 annotate해준
    `endorsement_count_anno`/`is_endorsed_anno`가 있으면 그 값을 그대로
    쓰고(annotate 경로, N+1 없음), 없으면 `obj.endorsements.count()` /
    `obj.endorsements.filter(user=user).exists()`로 직접 쿼리하는
    fallback 경로로 동작 — 단건 조회(`PlaceDetailView`)나 생성/수정
    직후 응답처럼 annotate가 없는 곳에서도 항상 올바른 값을 반환.
- `PlaceListView.get`에서 `Count('endorsements')`로 `endorsement_count_anno`를
  annotate. 로그인 사용자에 한해 `Exists(PlaceEndorsement.objects.filter(
  place=OuterRef('pk'), user=request.user))`로 `is_endorsed_anno`도 함께
  annotate — 목록 조회는 몇 개의 사용처를 반환하든 추가 쿼리 없이 1~2개의
  쿼리로 끝남.

## 주요 변경

- `apps/places/serializers.py`: `LocalPlaceSerializer`에
  `endorsement_count`/`is_endorsed` `SerializerMethodField` 및
  `get_endorsement_count`/`get_is_endorsed` 추가(annotate 우선, 없으면
  fallback 쿼리). `Meta.fields`에 뱃지 2개 + 신규 필드 2개 추가.
- `apps/places/views.py`: `PlaceListView.get`에 `Count`/`Exists`/`OuterRef`
  annotate 추가(비로그인 시 `is_endorsed_anno`는 annotate하지 않고
  serializer의 `user.is_authenticated` 분기에 맡김).
- `tests/test_places_endorsement.py`: 목록 API 레벨 테스트 2건 추가 —
  `test_serializer_exposes_badges_and_counts`(뱃지 True + 본인 추천 시
  count/`is_endorsed` 확인), `test_serializer_is_endorsed_false_for_other_user`
  (다른 사용자가 추천한 사용처를 조회하면 `is_endorsed`는 `False`, `count`는
  그대로 반영되는지 확인).

## 후속 노트

이 커밋 시점에는 `PlaceDetailView.get`/`PlaceListView.post`/
`PlaceDetailView.patch`가 annotate 없이 `LocalPlaceSerializer`를 그대로
쓰기 때문에 fallback 경로를 타는데, 이 세 엔드포인트에 대한 테스트는
아직 없었다(최종 리뷰에서 지적되어 이후 커밋에서 보강).
