"""apps.places 신뢰도 기반 안심 검증 마크(뱃지 + 추천) 모델/API 테스트."""
import pytest
from django.db import IntegrityError
from rest_framework.test import APIClient

from apps.places.models import LocalPlace, PlaceEndorsement
from apps.users.models import User


@pytest.mark.django_db
def test_local_place_badge_fields_default_false():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    assert place.okcheon_news_recommended is False
    assert place.counseling_center_recommended is False


@pytest.mark.django_db
def test_duplicate_endorsement_blocked_at_db_level():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    user = User.objects.create_user(kakao_id='endorser1')
    PlaceEndorsement.objects.create(place=place, user=user)

    with pytest.raises(IntegrityError):
        PlaceEndorsement.objects.create(place=place, user=user)


@pytest.mark.django_db
def test_serializer_exposes_badges_and_counts():
    place = LocalPlace.objects.create(
        name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가',
        okcheon_news_recommended=True,
    )
    user = User.objects.create_user(kakao_id='endorser2')
    PlaceEndorsement.objects.create(place=place, user=user)

    client = APIClient()
    client.force_authenticate(user=user)
    res = client.get('/api/places/')
    assert res.status_code == 200
    data = next(p for p in res.data if p['id'] == place.id)
    assert data['okcheon_news_recommended'] is True
    assert data['counseling_center_recommended'] is False
    assert data['endorsement_count'] == 1
    assert data['is_endorsed'] is True


@pytest.mark.django_db
def test_serializer_is_endorsed_false_for_other_user():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    endorser = User.objects.create_user(kakao_id='endorser3')
    other = User.objects.create_user(kakao_id='viewer1')
    PlaceEndorsement.objects.create(place=place, user=endorser)

    client = APIClient()
    client.force_authenticate(user=other)
    res = client.get('/api/places/')
    data = next(p for p in res.data if p['id'] == place.id)
    assert data['endorsement_count'] == 1
    assert data['is_endorsed'] is False


@pytest.mark.django_db
def test_endorse_requires_auth():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    res = APIClient().post(f'/api/places/{place.id}/endorse/')
    assert res.status_code == 401


@pytest.mark.django_db
def test_endorse_increments_count():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    user = User.objects.create_user(kakao_id='endorser4')

    client = APIClient()
    client.force_authenticate(user=user)
    res = client.post(f'/api/places/{place.id}/endorse/')
    assert res.status_code == 200
    assert res.data['endorsement_count'] == 1
    assert res.data['is_endorsed'] is True


@pytest.mark.django_db
def test_endorse_twice_is_idempotent():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    user = User.objects.create_user(kakao_id='endorser5')

    client = APIClient()
    client.force_authenticate(user=user)
    client.post(f'/api/places/{place.id}/endorse/')
    res = client.post(f'/api/places/{place.id}/endorse/')
    assert res.status_code == 200
    assert res.data['endorsement_count'] == 1
    assert PlaceEndorsement.objects.filter(place=place, user=user).count() == 1


@pytest.mark.django_db
def test_endorse_nonexistent_place_404():
    user = User.objects.create_user(kakao_id='endorser6')
    client = APIClient()
    client.force_authenticate(user=user)
    res = client.post('/api/places/99999/endorse/')
    assert res.status_code == 404
    assert res.data['code'] == 'place_not_found'


@pytest.mark.django_db
def test_detail_view_exposes_endorsement_fields_via_fallback():
    """PlaceDetailView.get은 annotate 없이 조회하므로 serializer의 fallback(.count()/.filter().exists()) 경로를 탄다."""
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    user = User.objects.create_user(kakao_id='endorser7')
    PlaceEndorsement.objects.create(place=place, user=user)

    client = APIClient()
    client.force_authenticate(user=user)
    res = client.get(f'/api/places/{place.id}/')
    assert res.status_code == 200
    assert res.data['endorsement_count'] == 1
    assert res.data['is_endorsed'] is True


@pytest.mark.django_db
def test_create_view_exposes_endorsement_fields_via_fallback():
    """PlaceListView.post도 annotate 없이 새로 저장한 인스턴스를 직렬화하므로 fallback 경로를 탄다."""
    user = User.objects.create_user(kakao_id='creator1')
    client = APIClient()
    client.force_authenticate(user=user)
    res = client.post('/api/places/', {
        'name': '옥천 마트',
        'category': '생활',
        'address': '옥천군 옥천읍 어딘가',
    })
    assert res.status_code == 201
    assert res.data['endorsement_count'] == 0
    assert res.data['is_endorsed'] is False


@pytest.mark.django_db
def test_my_endorsed_filter_returns_only_endorsed_places():
    liked = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    not_liked = LocalPlace.objects.create(name='옥천 카페', category='생활', address='옥천군 옥천읍 어딘가')
    user = User.objects.create_user(kakao_id='endorser8')
    other = User.objects.create_user(kakao_id='endorser9')
    PlaceEndorsement.objects.create(place=liked, user=user)
    PlaceEndorsement.objects.create(place=liked, user=other)
    PlaceEndorsement.objects.create(place=not_liked, user=other)

    client = APIClient()
    client.force_authenticate(user=user)
    res = client.get('/api/places/?my_endorsed=true')
    assert res.status_code == 200
    assert [p['id'] for p in res.data] == [liked.id]
    # 다른 유저의 추천도 함께 집계돼야 함 (본인 추천만 세는 조인 버그 방지)
    assert res.data[0]['endorsement_count'] == 2


@pytest.mark.django_db
def test_my_endorsed_filter_requires_auth():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    user = User.objects.create_user(kakao_id='endorser10')
    PlaceEndorsement.objects.create(place=place, user=user)

    res = APIClient().get('/api/places/?my_endorsed=true')
    assert res.status_code == 200
    assert res.data == []
