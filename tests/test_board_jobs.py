"""apps.board JobPost/JobApplication 모델 + API 테스트."""
import pytest
from django.db import IntegrityError
from rest_framework.test import APIClient

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


@pytest.mark.django_db
class TestJobPostAPI:
    def test_list_returns_active_posts(self):
        writer = User.objects.create_user(kakao_id='writer3')
        JobPost.objects.create(title='공고1', category='돌봄', description='설명', created_by=writer)
        JobPost.objects.create(title='공고2', category='동아리', description='설명', created_by=writer, is_active=False)

        res = APIClient().get('/api/board/jobs/')
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]['title'] == '공고1'

    def test_list_filters_by_category(self):
        writer = User.objects.create_user(kakao_id='writer4')
        JobPost.objects.create(title='농사일', category='농촌일손', description='설명', created_by=writer)
        JobPost.objects.create(title='돌봄일', category='돌봄', description='설명', created_by=writer)

        res = APIClient().get('/api/board/jobs/', {'category': '돌봄'})
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]['title'] == '돌봄일'

    def test_create_requires_auth(self):
        res = APIClient().post('/api/board/jobs/', {
            'title': '공고', 'category': '돌봄', 'description': '설명',
        })
        assert res.status_code == 401

    def test_create_and_retrieve(self):
        user = User.objects.create_user(kakao_id='writer5')
        client = APIClient()
        client.force_authenticate(user=user)

        res = client.post('/api/board/jobs/', {
            'title': '새 공고', 'category': '주택수리', 'description': '지붕 수리 도와주실 분',
        })
        assert res.status_code == 201
        assert res.data['is_owner'] is True

    def test_non_owner_cannot_edit_or_delete(self):
        owner = User.objects.create_user(kakao_id='owner1')
        other = User.objects.create_user(kakao_id='other1')
        post = JobPost.objects.create(title='공고', category='돌봄', description='설명', created_by=owner)

        client = APIClient()
        client.force_authenticate(user=other)

        res = client.patch(f'/api/board/jobs/{post.id}/', {'title': '수정시도'})
        assert res.status_code == 403

        res = client.delete(f'/api/board/jobs/{post.id}/')
        assert res.status_code == 403

    def test_owner_delete_soft_deletes(self):
        owner = User.objects.create_user(kakao_id='owner2')
        post = JobPost.objects.create(title='공고', category='돌봄', description='설명', created_by=owner)

        client = APIClient()
        client.force_authenticate(user=owner)
        res = client.delete(f'/api/board/jobs/{post.id}/')
        assert res.status_code == 204

        post.refresh_from_db()
        assert post.is_active is False


@pytest.mark.django_db
class TestJobApplyAPI:
    def test_apply_requires_auth(self):
        writer = User.objects.create_user(kakao_id='writer6')
        post = JobPost.objects.create(title='공고', category='돌봄', description='설명', created_by=writer)

        res = APIClient().post(f'/api/board/jobs/{post.id}/apply/', {'name': '홍길동', 'phone': '010-0000-0000'})
        assert res.status_code == 401

    def test_apply_saves_name_and_phone_for_autofill(self):
        writer = User.objects.create_user(kakao_id='writer7')
        applicant = User.objects.create_user(kakao_id='applicant2')
        post = JobPost.objects.create(title='공고', category='돌봄', description='설명', created_by=writer)

        client = APIClient()
        client.force_authenticate(user=applicant)
        res = client.post(f'/api/board/jobs/{post.id}/apply/', {'name': '김철수', 'phone': '010-1234-5678'})
        assert res.status_code == 201

        applicant.refresh_from_db()
        assert applicant.phone == '010-1234-5678'
        assert applicant.profile.applicant_name == '김철수'

    def test_apply_autofills_from_saved_profile(self):
        writer = User.objects.create_user(kakao_id='writer8')
        applicant = User.objects.create_user(kakao_id='applicant3', phone='010-9999-8888')
        applicant.profile.applicant_name = '박영희'
        applicant.profile.save(update_fields=['applicant_name'])
        post = JobPost.objects.create(title='공고', category='돌봄', description='설명', created_by=writer)

        client = APIClient()
        client.force_authenticate(user=applicant)
        res = client.post(f'/api/board/jobs/{post.id}/apply/', {})
        assert res.status_code == 201
        assert res.data['name'] == '박영희'
        assert res.data['phone'] == '010-9999-8888'

    def test_duplicate_apply_returns_400(self):
        writer = User.objects.create_user(kakao_id='writer9')
        applicant = User.objects.create_user(kakao_id='applicant4')
        post = JobPost.objects.create(title='공고', category='돌봄', description='설명', created_by=writer)

        client = APIClient()
        client.force_authenticate(user=applicant)
        client.post(f'/api/board/jobs/{post.id}/apply/', {'name': '지원자', 'phone': '010-1111-1111'})
        res = client.post(f'/api/board/jobs/{post.id}/apply/', {'name': '지원자', 'phone': '010-1111-1111'})
        assert res.status_code == 400
        assert res.data['code'] == 'already_applied'

    def test_apply_with_overlong_name_returns_400_not_500(self):
        writer = User.objects.create_user(kakao_id='writer11')
        applicant = User.objects.create_user(kakao_id='applicant6')
        post = JobPost.objects.create(title='공고', category='돌봄', description='설명', created_by=writer)

        client = APIClient()
        client.force_authenticate(user=applicant)
        res = client.post(f'/api/board/jobs/{post.id}/apply/', {
            'name': '가' * 60, 'phone': '010-1234-5678',
        })
        assert res.status_code == 400
        assert JobApplication.objects.filter(job_post=post, applicant=applicant).exists() is False

    def test_applications_list_owner_only(self):
        writer = User.objects.create_user(kakao_id='writer10')
        applicant = User.objects.create_user(kakao_id='applicant5')
        other = User.objects.create_user(kakao_id='other2')
        post = JobPost.objects.create(title='공고', category='돌봄', description='설명', created_by=writer)
        JobApplication.objects.create(job_post=post, applicant=applicant, name='지원자', phone='010-2222-2222')

        client = APIClient()
        client.force_authenticate(user=other)
        res = client.get(f'/api/board/jobs/{post.id}/applications/')
        assert res.status_code == 403

        client.force_authenticate(user=writer)
        res = client.get(f'/api/board/jobs/{post.id}/applications/')
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]['name'] == '지원자'
