"""apps.analytics — API 호출 트래픽 로깅 미들웨어 테스트."""
import pytest
from rest_framework.test import APIClient

from apps.analytics.models import RequestLog
from apps.users.models import User


@pytest.mark.django_db
def test_api_request_is_logged():
    APIClient().get('/api/places/')
    log = RequestLog.objects.get(path='/api/places/')
    assert log.method == 'GET'
    assert log.status_code == 200
    assert log.user is None


@pytest.mark.django_db
def test_authenticated_request_records_user():
    user = User.objects.create_user(kakao_id='analytics-tester')
    client = APIClient()
    client.force_authenticate(user=user)
    client.get('/api/places/')
    log = RequestLog.objects.get(path='/api/places/')
    assert log.user_id == user.id


@pytest.mark.django_db
def test_admin_and_docs_paths_are_excluded():
    APIClient().get('/admin/login/')
    APIClient().get('/api/docs/')
    APIClient().get('/api/schema/')
    assert not RequestLog.objects.filter(path__startswith='/admin/').exists()
    assert not RequestLog.objects.filter(path__startswith='/api/docs/').exists()
    assert not RequestLog.objects.filter(path__startswith='/api/schema/').exists()


@pytest.mark.django_db
def test_404_is_logged_with_its_status_code():
    APIClient().get('/api/places/999999/')
    log = RequestLog.objects.get(path='/api/places/999999/')
    assert log.status_code == 404
