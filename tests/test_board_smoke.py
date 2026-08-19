"""apps.board 작업 전, pytest-django DB 배선이 실제로 동작하는지 확인하는 스모크 테스트."""
import pytest

from apps.regions.models import Region


@pytest.mark.django_db
def test_can_create_and_query_region():
    Region.objects.create(code='11', name='서울특별시')
    assert Region.objects.filter(code='11').exists()
