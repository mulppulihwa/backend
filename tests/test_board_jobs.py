"""apps.board JobPost/JobApplication 모델 + API 테스트."""
import pytest

from apps.board.models import JobPost
from apps.users.models import User


@pytest.mark.django_db
def test_create_job_post():
    user = User.objects.create_user(kakao_id='writer1')
    post = JobPost.objects.create(
        title='감자 수확 도와주실 분', category='농촌일손', region='동이면',
        description='감자밭 수확 인력 모집', created_by=user,
    )
    assert post.is_active is True
    assert post.category == '농촌일손'
