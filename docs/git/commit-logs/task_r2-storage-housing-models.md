# Cloudflare R2 스토리지 설정 + HousingPost/HousingPhoto 모델

**날짜**: 2026-08-20
**커밋 로그**: [156b717](https://github.com/mulppulihwa/backend/commit/156b717)

## 작업 배경

구하기 게시판(`apps.board`) 기능 구현 계획의 Task 6. Task 1~5에서 완성한
`JobPost`/`JobApplication` 기능에 이어, 두 가지 독립적인 작업을 함께 진행한다.
(1) 이미지 파일을 Cloudflare R2에 저장하도록 Django 파일 스토리지 백엔드를
설정하고, (2) 살 곳 게시판에 쓸 `HousingPost`/`HousingPhoto` 모델을 추가한다.

## AS-IS

- `requirements.txt`에 파일 스토리지/이미지 관련 패키지 없음 (`django-storages`, `Pillow` 미설치)
- `config/settings.py`에 `STORAGES` 설정 없음 (기본 로컬 파일시스템 스토리지 사용)
- `apps/board/models.py`에 `JobPost`, `JobApplication`만 존재
- `apps/board/admin.py`에 `JobPostAdmin`만 등록

## TO-BE

- `requirements.txt`: `django-storages[s3]>=1.14`, `Pillow>=10.0` 추가
- `config/settings.py`: `STATIC_ROOT` 다음에 `STORAGES` 딕셔너리 추가 —
  `default`는 `storages.backends.s3boto3.S3Boto3Storage`(R2 엔드포인트,
  `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY`/`R2_BUCKET_NAME`/`R2_PUBLIC_URL`
  환경변수 사용), `staticfiles`는 기존 `StaticFilesStorage` 유지
- `apps/board/models.py`: `ArrayField` import 추가, 파일 끝에 `HousingPost`,
  `HousingPhoto` 모델과 `ROOM_TYPES`, `DEAL_TYPES` 선택지 추가
- `apps/board/admin.py`: `HousingPhotoInline`, `HousingPostAdmin` 추가 (기존
  `JobPostAdmin`은 그대로 유지)
- `apps/board/migrations/0003_housingpost_housingphoto_and_more.py` 생성
- `tests/test_board_housing.py` 신규 작성

## 주요 변경

- `STORAGES['default']['OPTIONS']`의 키는 Django 설정 이름이 아니라
  `django-storages`의 `S3Boto3Storage` 생성자 kwargs이므로 전부 소문자
  스네이크케이스(`access_key`, `secret_key`, `bucket_name`, `endpoint_url`,
  `addressing_style`, `default_acl`, `querystring_auth`, `custom_domain`) 사용
- `endpoint_url`은 `R2_ACCOUNT_ID` 환경변수로 `https://{account_id}.r2.cloudflarestorage.com`
  형태로 조립, `custom_domain`은 `R2_PUBLIC_URL`에서 스킴(`https://`/`http://`)을
  제거한 값 사용 (django-storages가 URL 생성 시 스킴을 다시 붙임)
- `django.contrib.postgres.fields.ArrayField`를 사용해 `HousingPost.options`를
  텍스트 배열로 저장 (편의시설 목록 등)
- `HousingPhoto.image`는 `ImageField(upload_to='housing_photos/')`로 R2에
  저장되며, `order` 필드로 정렬 순서 관리
- `tests/test_board_housing.py`는 `@override_settings(STORAGES=TEST_STORAGES)`로
  테스트 중 `FileSystemStorage`를 사용해 실제 R2에 업로드하지 않도록 격리 —
  `pytest tests/test_board_housing.py -v` 단독 실행 시 1개 테스트 통과 확인
- 전체 테스트(`pytest tests/`) 실행 시 이번 변경과 무관하게 원격 Supabase
  테스트 DB(`test_postgres`)에 대한 동시 세션 충돌로 일부 테스트가
  `SystemExit: 2`로 에러났으나, 개별 실행 시에는 모두 통과함(환경 이슈로 판단)
