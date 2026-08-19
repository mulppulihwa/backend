"""apps.board HousingPost/HousingPhoto 모델 + API 테스트."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.board.models import HousingPhoto, HousingPost
from apps.users.models import User

# 테스트에서는 실제 R2에 업로드하지 않고 로컬 파일시스템에 저장한다.
TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


@override_settings(STORAGES=TEST_STORAGES)
@pytest.mark.django_db
def test_create_housing_post_with_photo(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    user = User.objects.create_user(kakao_id='landlord1')
    post = HousingPost.objects.create(
        title='옥천읍 분리형 원룸', region='옥천읍', detail_address='옥천군 옥천읍 어딘가',
        room_type='원룸', deal_type='월세', deposit=500, monthly_rent=30,
        contact_name='집주인', contact_phone='010-1234-0000', created_by=user,
    )
    image = SimpleUploadedFile('room.jpg', b'fake-image-bytes', content_type='image/jpeg')
    photo = HousingPhoto.objects.create(housing_post=post, image=image, order=0)

    assert post.photos.count() == 1
    assert photo.housing_post_id == post.id


from unittest.mock import patch

from rest_framework.test import APIClient


@pytest.mark.django_db
class TestHousingPostAPI:
    def test_list_filters_by_room_type(self, tmp_path, settings):
        settings.STORAGES = TEST_STORAGES
        settings.MEDIA_ROOT = tmp_path
        user = User.objects.create_user(kakao_id='landlord2')
        HousingPost.objects.create(
            title='원룸 매물', region='옥천읍', detail_address='주소1', room_type='원룸',
            deal_type='월세', contact_name='집주인', contact_phone='010-0000-0001', created_by=user,
        )
        HousingPost.objects.create(
            title='투룸 매물', region='옥천읍', detail_address='주소2', room_type='투룸이상',
            deal_type='전세', contact_name='집주인', contact_phone='010-0000-0002', created_by=user,
        )

        res = APIClient().get('/api/board/housing/', {'room_type': '원룸'})
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]['title'] == '원룸 매물'

    @patch('apps.board.views.geocode_address', return_value=None)
    def test_create_with_multipart_images(self, mock_geocode, tmp_path, settings):
        settings.STORAGES = TEST_STORAGES
        settings.MEDIA_ROOT = tmp_path
        user = User.objects.create_user(kakao_id='landlord3')
        client = APIClient()
        client.force_authenticate(user=user)

        image1 = SimpleUploadedFile('room1.jpg', b'fake-bytes-1', content_type='image/jpeg')
        image2 = SimpleUploadedFile('room2.jpg', b'fake-bytes-2', content_type='image/jpeg')

        res = client.post('/api/board/housing/', {
            'title': '옥천읍 분리형 원룸', 'region': '옥천읍', 'detail_address': '옥천군 옥천읍 어딘가',
            'room_type': '원룸', 'deal_type': '월세', 'deposit': 500, 'monthly_rent': 30,
            'contact_name': '집주인', 'contact_phone': '010-1234-5678',
            'options': ['에어컨', '냉장고'],  # 멀티파트에서 반복 key로 전송되면 DRF ListField가 자동으로 리스트로 파싱
            'images': [image1, image2],
        }, format='multipart')

        assert res.status_code == 201
        assert len(res.data['photos']) == 2
        assert res.data['options'] == ['에어컨', '냉장고']
        mock_geocode.assert_called_once_with('옥천군 옥천읍 어딘가')

    def test_non_owner_cannot_edit_or_delete(self, tmp_path, settings):
        settings.STORAGES = TEST_STORAGES
        settings.MEDIA_ROOT = tmp_path
        owner = User.objects.create_user(kakao_id='landlord4')
        other = User.objects.create_user(kakao_id='other3')
        post = HousingPost.objects.create(
            title='매물', region='옥천읍', detail_address='주소', room_type='원룸',
            deal_type='월세', contact_name='집주인', contact_phone='010-0000-0003', created_by=owner,
        )

        client = APIClient()
        client.force_authenticate(user=other)

        res = client.patch(f'/api/board/housing/{post.id}/', {'title': '수정시도'})
        assert res.status_code == 403

        res = client.delete(f'/api/board/housing/{post.id}/')
        assert res.status_code == 403
