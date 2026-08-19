"""apps.places 신뢰도 기반 안심 검증 마크(뱃지 + 추천) 모델/API 테스트."""
import pytest
from django.db import IntegrityError

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
