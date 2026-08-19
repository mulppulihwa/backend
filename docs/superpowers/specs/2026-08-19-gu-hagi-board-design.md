# '구하기' 게시판 (apps.board) 설계

- 작성일: 2026-08-19
- 관련 레포: `mulppulihwa/backend` (본 레포)
- 범위: 신뢰도 기반 안심 검증 마크는 별도 스펙으로 분리 (이번 스펙 범위 아님)

## 배경 / 목적

기존 백엔드에는 옥천군 정책 매칭(`apps.policies`)과 사용처 지도(`apps.places`)만 있고, 주민 간 구인구직/부동산 정보를 교환할 채널이 없다. 홈 화면 하단 세 번째 탭('구하기')에서 사람(농촌일손·주택수리·돌봄·동아리 등)과 집(임대 매물)을 구하고 올릴 수 있게 한다. 사람 구하기 정보는 옥천신문 장터 게시판을 참고 소스로 삼는다.

향후 '사람'/'집' 외에 다른 구하기 카테고리(예: 물건 구해요)가 추가될 수 있으므로, 새 카테고리 추가가 앱 하나 통째로 늘리는 일 없이 기존 앱에 모델 하나 더하는 정도로 끝나도록 설계한다.

## 결정된 아키텍처

**하나의 새 Django 앱 `apps.board`**에 카테고리별 모델을 나란히 둔다. `apps.users`가 `User`/`UserProfile`/`UserPolicy`를 한 앱에 묶어둔 것과 같은 패턴이다. Post/Detail 공통 베이스 테이블이나 JSON blob 같은 다형성 구조는 채택하지 않는다 — 이 레포 어디에도 그런 패턴이 없고, 지금 필요한 범위(사람/집 두 카테고리)에 비해 과설계이기 때문. 새 카테고리가 실제로 필요해지면 그때 이 앱에 모델+뷰 한 쌍을 추가한다.

URL prefix: `/api/board/` (기존 `path('api/<name>/', include('apps.<name>.urls'))` 패턴을 따르되, jobs/housing을 하위 경로로 나눈다).

## 데이터 모델

### JobPost (사람 구해요)
| 필드 | 타입 | 비고 |
|---|---|---|
| title | CharField | 게시글 제목 |
| category | CharField(choices) | 농촌일손·주택수리·돌봄·동아리·기타 — 상단 필터 대상 |
| region | CharField(choices), blank=True | 옥천군 읍/면 (아래 "지역 필드" 참고) |
| description | TextField | 모집 내용 |
| location | CharField | 장소(자유 텍스트) |
| start_date, end_date | DateField, null=True | 모집 기간 |
| recruit_count | IntegerField, null=True | 모집 인원 |
| conditions | TextField, blank=True | 지원 조건 |
| created_by | FK `users.User` | |
| is_active | BooleanField(default=True) | soft delete (기존 `places` 패턴) |
| created_at, updated_at | DateTimeField | |

### JobApplication (지원)
| 필드 | 타입 | 비고 |
|---|---|---|
| job_post | FK JobPost | |
| applicant | FK `users.User` | |
| name, phone | CharField | 지원 시점 스냅샷. 최초 지원 시 `User.phone`이 비어있으면 채워 넣고, `UserProfile.applicant_name`에 이름을 저장해 다음 지원부터 자동완성되게 한다 |
| message | TextField, blank=True | 선택 입력 |
| applied_at | DateTimeField(auto_now_add) | |
| unique_together | (job_post, applicant) | 중복 지원 방지 |

`apps.users.UserProfile`에 `applicant_name = TextField(blank=True)` 필드 추가 필요. `UserProfileSerializer`는 이미 `exclude=['user']`라 필드 추가만으로 API에 자동 노출된다.

### HousingPost (집 구해요)
| 필드 | 타입 | 비고 |
|---|---|---|
| title | CharField | |
| region | CharField(choices), blank=True | 옥천군 읍/면 (아래 "지역 필드" 참고) |
| detail_address | TextField | 자세한 주소 |
| room_type | CharField(choices) | 원룸·투룸이상·오피스텔·주택·기타 — 상단 필터 대상 |
| room_layout | CharField, blank=True | 자유 텍스트, 예: "분리형 원룸" (목록에 표시) |
| size_pyeong | DecimalField, null=True | 평수 |
| deal_type | CharField(choices) | 전세·월세 |
| deposit | IntegerField, null=True | 보증금, 만원 단위 (`UserProfile.non_farm_income` 관례 따름) |
| monthly_rent | IntegerField, null=True | 월세, 전세면 null |
| maintenance_fee | IntegerField, null=True | 관리비, 만원 단위 |
| options | ArrayField(TextField), default=list | 옵션 태그 (`LocalPlace.subsidy_tags` 패턴) |
| description | TextField, blank=True | 상세 설명(서술형) |
| contact_name, contact_phone | CharField | 작성자 정보 — 로그인 계정과 별개로 입력받음(집주인 번호 등일 수 있음) |
| lat, lng | DecimalField, null=True | `lib/services/geocoding.geocode_address` 재사용해 `detail_address`로부터 자동 채움 (기존 `PlaceListView.post` 패턴) |
| created_by | FK `users.User` | |
| is_active | BooleanField(default=True) | |
| created_at, updated_at | DateTimeField | |

### HousingPhoto
| 필드 | 타입 | 비고 |
|---|---|---|
| housing_post | FK HousingPost, related_name='photos' | |
| image | ImageField | Cloudflare R2 저장 (아래 인프라 섹션) |
| order | IntegerField(default=0) | 표시 순서 |
| created_at | DateTimeField(auto_now_add) | |

### 지역 필드

`regions.Region`은 시/도~시/군 단위(전국 28개 행)까지만 시드되어 있고 옥천군(43720) 밑의 읍/면 단위 데이터가 없다. 이 앱은 옥천군 하나만 다루는 로컬 서비스라 전국 행정구역 계층을 새로 채워 넣을 필요는 없다고 판단, `region`은 `regions.Region` FK 대신 **레포 컨벤션(`LocalPlace.CATEGORIES`처럼 고정 `choices`)을 따르는 `CharField`**로 둔다. 선택지는 `apps/places/management/commands/add_okcheon_places.py`에서 이미 쓰인 8개 읍/면과 동일하게 맞춘다: 옥천읍·동이면·안남면·청성면·청산면·이원면·군서면·군북면.

## API 엔드포인트

모두 기존 컨벤션(APIView, 읽기/쓰기 시리얼라이저 분리, `get_permissions()`로 메서드별 권한, 페이지네이션 없음, 에러는 `{'error': ..., 'code': ...}`)을 따른다.

- `GET /api/board/jobs/` — 목록. `?category=`, `?region=` 쿼리 파라미터로 필터. `AllowAny`
- `POST /api/board/jobs/` — 글쓰기. `IsAuthenticated`
- `GET /api/board/jobs/<id>/` — 상세. `AllowAny`
- `PATCH/DELETE /api/board/jobs/<id>/` — 작성자만 (places의 `created_by_id != request.user.id` 403 패턴). DELETE는 `is_active=False`
- `POST /api/board/jobs/<id>/apply/` — 지원하기. `IsAuthenticated`. body에 name/phone 없으면 저장된 값으로 자동 채움, 있으면 갱신 후 프로필에 반영
- `GET /api/board/jobs/<id>/applications/` — 지원자 목록. 작성자만 (아니면 403)
- `GET /api/board/housing/` — 목록. `?room_type=`, `?region=` 필터. `AllowAny`
- `POST /api/board/housing/` — 글쓰기(multipart, 사진 여러 장). `IsAuthenticated`
- `GET /api/board/housing/<id>/` — 상세(사진 목록 + 연락처 포함). `AllowAny`
- `PATCH/DELETE /api/board/housing/<id>/` — 작성자만

'문의하기 → 바로 전화걸기'는 프론트엔드 전용 UI 흐름이다 — 상세 API가 이미 `contact_phone`을 반환하므로 백엔드에 추가 엔드포인트는 필요 없다.

## 이미지 업로드 인프라 (신규 구축)

현재 레포에는 파일 업로드 관련 설정이 전혀 없다(MEDIA 설정, ImageField, 스토리지 백엔드 전무). 이번에 처음 구축한다.

- **스토리지**: Cloudflare R2 (S3 호환 API). Railway는 재배포 시 파일시스템이 초기화되므로 로컬 저장은 쓰지 않는다.
- 추가 패키지: `django-storages[s3]`, `boto3`, `Pillow`(ImageField 필수 의존성) → `requirements.txt`에 추가
- 설정(`config/settings.py`에 추가): `DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'`, `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`(R2 API 토큰), `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`(R2 엔드포인트), `AWS_S3_ADDRESSING_STYLE='virtual'`, `AWS_DEFAULT_ACL=None`(R2는 ACL 미지원)
- R2 버킷 생성 + Account API Token(Object Read & Write, 버킷 범위 지정) 발급 완료, 루트 `.env`에 `R2_ACCOUNT_ID`/`R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY`/`R2_BUCKET_NAME`/`R2_PUBLIC_URL` 값 설정 완료 — 구현 시 이 키 이름 그대로 읽어서 settings에 연결. Railway 프로덕션 환경변수에도 동일 값 등록 필요(배포 단계에서 처리)
- 업로드 뷰는 `MultiPartParser`를 명시적으로 사용

## 재사용하는 기존 컴포넌트

- `regions.Region` — 위 "지역 필드"에서 결정한 대로 FK로 쓰지 않음(옥천군 읍/면 데이터 없음, 고정 choices로 대체)
- `lib/services/geocoding.geocode_address` — 주소→좌표. Railway 프로덕션 환경변수에는 `KAKAO_LOCAL_API_KEY`가 설정되어 있음을 확인(로컬 `.env`에는 없었음 — 로컬 개발 시엔 no-op으로 lat/lng만 비게 됨, 배포 환경에서는 정상 동작)
- `apps.users` 인증/프로필 — JWT(`rest_framework_simplejwt`), `UserProfile`은 `User` 생성 시 signal로 자동 생성됨. 지원자 이름/전화번호 자동완성은 `User.phone` + 신규 `UserProfile.applicant_name` 필드로 처리

## 테스트

이 레포에는 API 레벨 테스트가 아직 없다(순수 로직 유닛테스트만 존재, `tests/` 루트, pytest+pytest-django 설치됨). 이번 작업이 첫 `APIClient` 기반 테스트가 된다. `tests/` 루트에 `test_board_jobs.py`, `test_board_housing.py`로 추가하고, 기존 스타일(`TestXxx` 클래스, `test_snake_case` 메서드)을 따른다. 최소 커버리지: 목록/필터, 글쓰기 권한(비로그인 403), 작성자 아닌 사용자의 수정/삭제 거부, 중복 지원 방지, 지원자 목록 조회 권한.

## 관리자 페이지

`apps/places/admin.py` 패턴(`list_display`, `list_filter`, `search_fields`)을 따라 `JobPost`, `HousingPost`에 대해 등록. `JobApplication`은 `JobPost` 어드민에 `TabularInline`으로 노출 (policies 앱의 `ChecklistItemInline` 패턴 참고).

## 범위 밖 (다음 스펙)

- 신뢰도 기반 안심 검증 마크(옥천신문/상담센터 추천 뱃지, 추천 수 카운터) — 별도 스펙에서 다룸
- 새로운 '구하기' 카테고리(예: 물건 구해요) — 필요해지면 `apps.board`에 모델 하나 추가하는 정도로 확장
