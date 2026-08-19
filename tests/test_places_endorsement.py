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
