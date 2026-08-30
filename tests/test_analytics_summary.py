"""apps.analytics — /admin/ 요약 대시보드 뷰 테스트."""
import pytest
from django.test import Client
from django.urls import reverse

from apps.analytics.models import RequestLog
from apps.users.models import User


@pytest.mark.django_db
def test_summary_requires_staff_login():
    res = Client().get(reverse('admin:analytics_requestlog_summary'))
    assert res.status_code in (302, 403)


@pytest.mark.django_db
def test_summary_shows_aggregated_counts():
    admin = User.objects.create_superuser(kakao_id='admin-tester', password='testpass123')
    viewer = User.objects.create_user(kakao_id='viewer1')

    RequestLog.objects.create(path='/api/places/169/endorse/', method='POST', status_code=200, user=viewer)
    RequestLog.objects.create(path='/api/places/171/endorse/', method='POST', status_code=200, user=viewer)
    RequestLog.objects.create(path='/api/places/', method='GET', status_code=200, user=None)

    client = Client()
    client.force_login(admin)
    res = client.get(reverse('admin:analytics_requestlog_summary'))

    assert res.status_code == 200
    assert res.context['total'] == 3
    assert res.context['unique_users_total'] == 1

    actions = {row['action']: row['count'] for row in res.context['top_actions']}
    assert actions['/api/places/{id}/endorse/'] == 2

    paths = {row['path']: row['count'] for row in res.context['top_paths']}
    assert paths['/api/places/169/endorse/'] == 1
    assert paths['/api/places/171/endorse/'] == 1
