# 최종 리뷰 Important 3건 대응 — 사진 업로드 검증, 지원하기 시리얼라이저화, 중복지원 레이스 방어

**날짜**: 2026-08-20
**커밋 로그**: [2e33319](https://github.com/mulppulihwa/backend/commit/2e33319edafdea6d1ab5f7f8b24be810c504b7ab)

## 작업 배경

`apps.board`(구하기 게시판) 기능이 완성된 뒤 브랜치 전체를 대상으로 진행한 최종 코드
리뷰에서 Important 등급 findings 3건이 나왔다. 세 건 모두 `apps/board/views.py`에
집중돼 있어 한 번의 디스패치로 함께 처리했다.

## AS-IS

- `HousingPostListView.post`: `request.FILES.getlist('images')`를 검증 없이
  `HousingPhoto.objects.bulk_create()`로 바로 저장. `bulk_create`는 `full_clean()`을
  건너뛰므로 `ImageField`의 Pillow 기반 이미지 검증이 전혀 실행되지 않아, 임의의 바이트를
  아무 파일명으로나 올리면 공개 R2 버킷에 그대로 저장됨. 파일 개수/용량 제한도 없음.
- `JobApplyView.post`: `name`/`phone`/`message`를 `request.data`에서 직접 꺼내
  `JobApplication.objects.create()`에 바로 전달. `full_clean()`을 거치지 않아
  Postgres의 `varchar(50)`/`varchar(20)` 컬럼 제약만 남고, 위반 시 처리되지 않은
  `DataError` → 500으로 노출됨.
- `JobApplyView.post`: 중복 지원 방지가 `.filter(...).exists()` 사전 체크 하나뿐이라
  체크와 `.create()` 사이의 레이스 윈도우에서 동시 요청 두 개가 모두 체크를 통과하면
  두 번째 `.create()`가 `unique_together` 위반으로 처리되지 않은 `IntegrityError` → 500.

## TO-BE

- `apps/board/views.py`: `MAX_HOUSING_IMAGES`(10장), `MAX_IMAGE_SIZE_BYTES`(10MB) 상수 추가.
  `HousingPostListView.post`에서 `HousingPost` 저장 전에 이미지 개수/용량/유효성(Pillow)을
  먼저 검증하고, 저장 실패 시 photoless `HousingPost` row가 남지 않도록 `HousingPost` 생성 +
  `HousingPhoto.bulk_create`를 `transaction.atomic()`으로 묶음.
- `apps/board/serializers.py`: `JobApplicationWriteSerializer`(plain `Serializer`) 추가 —
  `name`(max_length=50)/`phone`(max_length=20)/`message`를 검증.
- `apps/board/views.py`: `JobApplyView.post`가 `request.data`를 직접 쓰지 않고
  `JobApplicationWriteSerializer`로 먼저 검증한 뒤, 검증된 데이터로 autofill/생성 로직 수행.
- `apps/board/views.py`: `JobApplication.objects.create()`를 `try/except IntegrityError`로
  감싸 레이스로 제약 위반이 나도 400(`already_applied`)을 반환하도록 방어 추가. 기존
  `.exists()` 사전 체크는 그대로 유지(빠른 경로).

## 주요 변경

- `apps/board/views.py`
  - `HousingPostListView.post`: 이미지 개수(`too_many_images`)/용량(`image_too_large`)/
    유효성(`invalid_image`) 검증을 `HousingPost` 필드 검증 직후, geocoding/저장 이전으로 이동.
    `drf_serializers.ImageField().run_validation()`으로 검증하되, DRF가 내부적으로 Django
    `ImageField.clean()`을 직접 호출해 `django.core.exceptions.ValidationError`를 그대로
    던지는 케이스가 있어 `(drf_serializers.ValidationError, DjangoValidationError)` 둘 다 캐치.
  - `JobApplyView.post`: `JobApplicationWriteSerializer(data=request.data)`로 먼저 검증
    (`raise_exception=True`) → 이후 autofill/`missing_applicant_info` 체크/`create`는
    `validated_data` 기준으로 수행. `create()` 호출을 `try/except IntegrityError`로 감싸
    500 대신 400(`already_applied`) 반환.
- `apps/board/serializers.py`: `JobApplicationWriteSerializer` 추가.
- `tests/test_board_housing.py`: Pillow 검증이 실제로 동작하므로 기존
  `test_create_with_multipart_images`가 가짜 바이트 대신 실제 JPEG를 생성해서 사용하도록
  수정(`make_real_image` 헬퍼 추가). `test_create_with_invalid_image_returns_400`,
  `test_create_with_too_many_images_returns_400` 2개 테스트 추가.
- `tests/test_board_jobs.py`: `test_apply_with_overlong_name_returns_400_not_500` 추가
  (이름 60자 → 500이 아닌 400 확인). 기존 `test_duplicate_apply_returns_400`은 수정 없이
  그대로 통과함(사전 `.exists()` 체크로 여전히 충족).
- 동시 지원 레이스 자체는 동기 테스트로 재현 불가능하므로 별도 테스트 없음 — `IntegrityError`
  캐치는 방어적 코드.

## Result

`pytest tests/test_board_jobs.py tests/test_board_housing.py tests/test_board_smoke.py -v`
21 passed (공유 원격 Postgres 테스트 DB의 무해한 teardown 레이스로 1회 재시도 후 통과).
