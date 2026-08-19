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
