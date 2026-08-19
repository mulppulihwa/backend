"""apps.board JobPost/JobApplication 모델 + API 테스트."""
import pytest
from django.db import IntegrityError

from apps.board.models import JobApplication, JobPost
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


@pytest.mark.django_db
def test_duplicate_application_blocked():
    writer = User.objects.create_user(kakao_id='writer2')
    applicant = User.objects.create_user(kakao_id='applicant1')
    post = JobPost.objects.create(
        title='돌봄 봉사자 모집', category='돌봄', description='어르신 돌봄 봉사', created_by=writer,
    )
    JobApplication.objects.create(job_post=post, applicant=applicant, name='지원자', phone='010-1111-2222')

    with pytest.raises(IntegrityError):
        JobApplication.objects.create(job_post=post, applicant=applicant, name='지원자', phone='010-1111-2222')
