"""PolicyChecklistView — Redis 장애 시에도 준비물 조회가 죽지 않는지 검증."""
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.policies.models import ChecklistItem, Policy


def _make_policy(**kwargs):
    defaults = dict(title='귀농 정착 지원금', summary='요약', raw_text='')
    defaults.update(kwargs)
    return Policy.objects.create(**defaults)


@pytest.mark.django_db
def test_checklist_returns_items_normally():
    policy = _make_policy()
    ChecklistItem.objects.create(policy=policy, order=0, label='주민등록등본')

    res = APIClient().get(f'/api/policies/{policy.id}/checklist/')
    assert res.status_code == 200
    assert res.data['items'][0]['label'] == '주민등록등본'


@pytest.mark.django_db
def test_checklist_nonexistent_policy_404():
    res = APIClient().get('/api/policies/99999/checklist/')
    assert res.status_code == 404
    assert res.data['code'] == 'policy_not_found'


@pytest.mark.django_db
def test_checklist_survives_redis_outage_on_read():
    """cache.get이 Redis ConnectionError를 던져도 500이 아니라 DB에서 바로 응답해야 한다."""
    policy = _make_policy()
    ChecklistItem.objects.create(policy=policy, order=0, label='주민등록등본')

    with patch('apps.policies.views.cache.get', side_effect=ConnectionError('redis down')):
        res = APIClient().get(f'/api/policies/{policy.id}/checklist/')

    assert res.status_code == 200
    assert res.data['items'][0]['label'] == '주민등록등본'


@pytest.mark.django_db
def test_checklist_survives_redis_outage_on_write():
    """캐시 저장(cache.set)이 실패해도 응답 자체는 정상적으로 나가야 한다."""
    policy = _make_policy()
    ChecklistItem.objects.create(policy=policy, order=0, label='주민등록등본')

    with patch('apps.policies.views.cache.set', side_effect=ConnectionError('redis down')):
        res = APIClient().get(f'/api/policies/{policy.id}/checklist/')

    assert res.status_code == 200
    assert res.data['items'][0]['label'] == '주민등록등본'


@pytest.mark.django_db
def test_checklist_no_items_no_raw_text_survives_redis_outage():
    policy = _make_policy(raw_text='')

    with patch('apps.policies.views.cache.get', side_effect=ConnectionError('redis down')), \
         patch('apps.policies.views.cache.set', side_effect=ConnectionError('redis down')):
        res = APIClient().get(f'/api/policies/{policy.id}/checklist/')

    assert res.status_code == 200
    assert res.data == {'items': [], 'parsing': False}
