# '구하기' 게시판 (apps.board) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** '사람 구해요'(구인구직 + 지원)와 '집 구해요'(부동산 매물 + 사진) 두 게시판을 새 Django 앱 `apps.board`에 구현하고, DRF API로 노출한다.

**Architecture:** 기존 레포 컨벤션(`apps.places`)을 그대로 따르는 Django REST 앱. `APIView` + 읽기/쓰기 시리얼라이저 분리, `get_permissions()`로 메서드별 권한, `is_active` soft delete, `{'error', 'code'}` 에러 포맷. `JobPost`/`JobApplication`/`HousingPost`/`HousingPhoto` 네 모델을 한 앱에 나란히 둔다(공통 베이스 테이블 없음). 사진은 Cloudflare R2(S3 호환)에 저장.

**Tech Stack:** Django 6.1, Django REST Framework, `django-storages[s3]`(R2), Pillow, pytest + pytest-django.

**설계 스펙 원본:** `docs/superpowers/specs/2026-08-19-gu-hagi-board-design.md` (읽어볼 필요는 없음 — 이 플랜에 필요한 내용은 전부 아래에 포함됨)

## Global Constraints

- URL prefix: `/api/board/` (jobs/housing 하위 경로로 분리)
- 지역 필드는 `regions.Region` FK를 쓰지 않는다 — 옥천군 8개 읍/면을 고정 `choices`로 하드코딩 (아래 `OKCHEON_REGIONS` 참고)
- 목록 API는 페이지네이션 없음 (레포 전체에 페이지네이션 컨벤션 자체가 없음, `REST_FRAMEWORK`에 `DEFAULT_PAGINATION_CLASS` 미설정)
- 에러 응답은 항상 `{'error': '한국어 메시지', 'code': 'snake_case_code'}` + 적절한 HTTP status
- 삭제는 항상 soft delete (`is_active = False`), 하드 삭제 금지
- 이미지 저장은 Cloudflare R2. R2 자격증명은 이미 루트 `.env`에 설정되어 있음(`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL`)
- 지원자 이름/전화번호는 `User.phone` + 신규 `UserProfile.applicant_name` 필드에 저장해 다음 지원부터 자동완성

---

### Task 1: pytest + Django 테스트 DB 배선

이 레포는 API 레벨 테스트가 없고 `pytest.ini`도 없다. `DATABASE_URL`은 Supabase의 **pgbouncer transaction-pooling** 연결(포트 6543)인데, `CREATE DATABASE`(pytest-django가 테스트 실행마다 시도) 같은 세션 단위 명령은 이 풀링 모드에서 실패한다. `.env`의 `DIRECT_URL`(포트 5432, 논-풀링)로 테스트 시에만 전환해야 한다. 이후 모든 태스크의 DB 연동 테스트가 이 설정에 의존하므로 가장 먼저 처리한다.

**Files:**
- Create: `pytest.ini`
- Modify: `config/settings.py:83` (DB URL 선택 로직)
- Test: `tests/test_board_smoke.py`

**Interfaces:**
- Produces: pytest 실행 시 `DIRECT_URL`을 쓰는 DB 연결 (후속 모든 태스크의 `@pytest.mark.django_db` 테스트가 이걸 전제로 함)

- [ ] **Step 1: pytest.ini 작성**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = test_*.py
```

- [ ] **Step 2: config/settings.py의 DB URL 선택 로직 수정**

`config/settings.py:83` 현재 코드:
```python
_db_url = os.environ['DATABASE_URL'].split('?')[0]  # psycopg2는 ?pgbouncer=true 등 미지원 파라미터 거부
```

아래로 교체:
```python
# pytest 실행 중에는 DIRECT_URL(논-풀링) 사용 — pgbouncer transaction pooling은
# 테스트 DB 생성(CREATE DATABASE) 같은 세션 단위 명령을 지원하지 않음
_running_pytest = 'PYTEST_CURRENT_TEST' in os.environ
_db_url = os.environ.get('DIRECT_URL', os.environ['DATABASE_URL']) if _running_pytest else os.environ['DATABASE_URL']
_db_url = _db_url.split('?')[0]  # psycopg2는 ?pgbouncer=true 등 미지원 파라미터 거부
```

- [ ] **Step 3: 실패하는 스모크 테스트 작성**

`tests/test_board_smoke.py`:
```python
"""apps.board 작업 전, pytest-django DB 배선이 실제로 동작하는지 확인하는 스모크 테스트."""
import pytest

from apps.regions.models import Region


@pytest.mark.django_db
def test_can_create_and_query_region():
    Region.objects.create(code='11', name='서울특별시')
    assert Region.objects.filter(code='11').exists()
```

- [ ] **Step 4: 테스트 실행**

Run: `pytest tests/test_board_smoke.py -v`
Expected: PASS (테스트 DB가 처음 생성되면서 마이그레이션이 자동 적용됨 — 몇 초 걸릴 수 있음). `django.db.utils.OperationalError`가 나면 `.env`의 `DIRECT_URL` 값을 다시 확인할 것.

- [ ] **Step 5: 커밋**

```bash
git add pytest.ini config/settings.py tests/test_board_smoke.py
git commit -m "test: pytest-django DB 연동 배선 (DIRECT_URL로 pgbouncer 풀링 우회)"
```

---

### Task 2: apps.board 스캐폴딩 + JobPost 모델

**Files:**
- Create: `apps/board/__init__.py`
- Create: `apps/board/apps.py`
- Create: `apps/board/models.py`
- Create: `apps/board/admin.py`
- Create: `apps/board/migrations/__init__.py`
- Modify: `config/settings.py` (`INSTALLED_APPS`)
- Test: `tests/test_board_jobs.py`

**Interfaces:**
- Produces: `apps.board.models.OKCHEON_REGIONS` (choices 튜플, Task 6에서 `HousingPost.region`도 재사용), `apps.board.models.JobPost`

- [ ] **Step 1: 앱 스캐폴딩 생성**

`apps/board/__init__.py`: 빈 파일

`apps/board/apps.py`:
```python
from django.apps import AppConfig


class BoardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.board'
```

`apps/board/migrations/__init__.py`: 빈 파일

- [ ] **Step 2: JobPost 모델 작성**

`apps/board/models.py`:
```python
from django.db import models

OKCHEON_REGIONS = [
    ('옥천읍', '옥천읍'), ('동이면', '동이면'), ('안남면', '안남면'), ('청성면', '청성면'),
    ('청산면', '청산면'), ('이원면', '이원면'), ('군서면', '군서면'), ('군북면', '군북면'),
]

JOB_CATEGORIES = [
    ('농촌일손', '농촌일손'), ('주택수리', '주택수리'), ('돌봄', '돌봄'), ('동아리', '동아리'), ('기타', '기타'),
]


class JobPost(models.Model):
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=JOB_CATEGORIES)
    region = models.CharField(max_length=10, choices=OKCHEON_REGIONS, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    recruit_count = models.IntegerField(null=True, blank=True)
    conditions = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='job_posts',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'job_posts'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['region']),
        ]
```

- [ ] **Step 3: admin.py 작성**

`apps/board/admin.py`:
```python
from django.contrib import admin

from .models import JobPost


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'region', 'created_by', 'is_active']
    list_filter = ['category', 'region', 'is_active']
    search_fields = ['title', 'description']
```

- [ ] **Step 4: INSTALLED_APPS에 등록**

`config/settings.py`의 `INSTALLED_APPS` 리스트 마지막(`'apps.regions',` 다음 줄)에 추가:
```python
    'apps.board',
```

- [ ] **Step 5: 마이그레이션 생성 및 적용**

Run: `python manage.py makemigrations board`
Expected: `apps/board/migrations/0001_initial.py` 생성됨

Run: `python manage.py migrate`
Expected: `Applying board.0001_initial... OK`

- [ ] **Step 6: 실패하는 모델 테스트 작성**

`tests/test_board_jobs.py`:
```python
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
```

- [ ] **Step 7: 테스트 실행**

Run: `pytest tests/test_board_jobs.py -v`
Expected: PASS

- [ ] **Step 8: 커밋**

```bash
git add apps/board config/settings.py tests/test_board_jobs.py
git commit -m "feat: apps.board 앱 생성 + JobPost 모델"
```

---

### Task 3: JobApplication 모델 + UserProfile.applicant_name

**Files:**
- Modify: `apps/board/models.py`
- Modify: `apps/users/models.py`
- Modify: `apps/board/admin.py`
- Test: `tests/test_board_jobs.py`

**Interfaces:**
- Consumes: `apps.board.models.JobPost` (Task 2)
- Produces: `apps.board.models.JobApplication`, `UserProfile.applicant_name` 필드 (Task 4/5에서 지원 로직이 이 필드를 읽고 씀)

- [ ] **Step 1: JobApplication 모델 추가**

`apps/board/models.py` 끝에 추가:
```python


class JobApplication(models.Model):
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='job_applications')
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    message = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_applications'
        unique_together = [['job_post', 'applicant']]
```

- [ ] **Step 2: UserProfile에 applicant_name 필드 추가**

`apps/users/models.py`의 `UserProfile` 클래스 안, `is_disabled` 필드(`# 복지로 API 매칭용` 섹션) 다음 줄에 추가:
```python

    # 구하기 게시판 지원자 정보
    applicant_name = models.TextField(blank=True)
```

`UserProfileSerializer`(`apps/users/serializers.py`)는 `exclude = ['user']`라 이 필드는 코드 변경 없이 자동으로 API에 노출된다.

- [ ] **Step 3: admin.py에 JobApplication 인라인 추가**

`apps/board/admin.py`를 아래로 교체:
```python
from django.contrib import admin

from .models import JobApplication, JobPost


class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    fields = ['applicant', 'name', 'phone', 'applied_at']
    readonly_fields = ['applied_at']


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    inlines = [JobApplicationInline]
    list_display = ['title', 'category', 'region', 'created_by', 'is_active']
    list_filter = ['category', 'region', 'is_active']
    search_fields = ['title', 'description']
```

- [ ] **Step 4: 마이그레이션 생성 및 적용**

Run: `python manage.py makemigrations board users`
Expected: `apps/board/migrations/0002_jobapplication.py`, `apps/users/migrations/000X_userprofile_applicant_name.py` 생성됨

Run: `python manage.py migrate`
Expected: 두 마이그레이션 모두 `OK`

- [ ] **Step 5: 실패하는 테스트 작성 (중복 지원 방지)**

`tests/test_board_jobs.py`에 추가:
```python
from django.db import IntegrityError

from apps.board.models import JobApplication


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
```

- [ ] **Step 6: 테스트 실행**

Run: `pytest tests/test_board_jobs.py -v`
Expected: PASS (2 tests)

- [ ] **Step 7: 커밋**

```bash
git add apps/board apps/users tests/test_board_jobs.py
git commit -m "feat: JobApplication 모델 + UserProfile.applicant_name 추가"
```

---

### Task 4: JobPost API (목록/생성/상세/수정/삭제)

**Files:**
- Create: `apps/board/serializers.py`
- Create: `apps/board/views.py`
- Create: `apps/board/urls.py`
- Modify: `config/urls.py`
- Test: `tests/test_board_jobs.py`

**Interfaces:**
- Consumes: `apps.board.models.JobPost` (Task 2)
- Produces: `apps.board.serializers.JobPostSerializer`, `JobPostWriteSerializer`; `apps.board.views.JobPostListView`, `JobPostDetailView`; URL `/api/board/jobs/`, `/api/board/jobs/<int:pk>/`

- [ ] **Step 1: 시리얼라이저 작성**

`apps/board/serializers.py`:
```python
from rest_framework import serializers

from .models import JobPost


class JobPostSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    created_by_nickname = serializers.CharField(source='created_by.nickname', read_only=True)

    class Meta:
        model = JobPost
        fields = [
            'id', 'title', 'category', 'region', 'description', 'location',
            'start_date', 'end_date', 'recruit_count', 'conditions',
            'created_by', 'created_by_nickname', 'is_owner', 'created_at',
        ]

    def get_is_owner(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.created_by_id == user.id


class JobPostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = [
            'title', 'category', 'region', 'description', 'location',
            'start_date', 'end_date', 'recruit_count', 'conditions',
        ]
        extra_kwargs = {
            'region': {'required': False},
            'location': {'required': False},
            'start_date': {'required': False},
            'end_date': {'required': False},
            'recruit_count': {'required': False},
            'conditions': {'required': False},
        }
```

- [ ] **Step 2: 뷰 작성**

`apps/board/views.py`:
```python
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobPost
from .serializers import JobPostSerializer, JobPostWriteSerializer


class JobPostListView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        posts = JobPost.objects.filter(is_active=True).order_by('-created_at')
        category = request.query_params.get('category')
        if category:
            posts = posts.filter(category=category)
        region = request.query_params.get('region')
        if region:
            posts = posts.filter(region=region)
        return Response(JobPostSerializer(posts, many=True, context={'request': request}).data)

    def post(self, request):
        serializer = JobPostWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(created_by=request.user)
        return Response(
            JobPostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class JobPostDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def _get_object(self, pk):
        try:
            return JobPost.objects.get(pk=pk, is_active=True)
        except JobPost.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '모집글을 찾을 수 없습니다.', 'code': 'job_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(JobPostSerializer(post, context={'request': request}).data)

    def patch(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '모집글을 찾을 수 없습니다.', 'code': 'job_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if post.created_by_id != request.user.id:
            return Response(
                {'error': '작성자만 수정할 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = JobPostWriteSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(JobPostSerializer(post, context={'request': request}).data)

    def delete(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '모집글을 찾을 수 없습니다.', 'code': 'job_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if post.created_by_id != request.user.id:
            return Response(
                {'error': '작성자만 삭제할 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )
        post.is_active = False
        post.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 3: urls.py 작성 및 config/urls.py에 연결**

`apps/board/urls.py`:
```python
from django.urls import path

from .views import JobPostDetailView, JobPostListView

urlpatterns = [
    path('jobs/', JobPostListView.as_view()),
    path('jobs/<int:pk>/', JobPostDetailView.as_view()),
]
```

`config/urls.py`의 `path('api/regions/', include('apps.regions.urls')),` 다음 줄에 추가:
```python
    path('api/board/', include('apps.board.urls')),
```

- [ ] **Step 4: 실패하는 API 테스트 작성**

`tests/test_board_jobs.py` 상단 import에 추가:
```python
from rest_framework.test import APIClient
```

파일 끝에 추가:
```python
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
```

이 클래스 전체에 DB 접근이 필요하므로, 파일 상단 import 아래에 pytest 마크를 클래스에 붙인다 — `TestJobPostAPI` 클래스 선언 줄을:
```python
@pytest.mark.django_db
class TestJobPostAPI:
```
로 바꾼다 (Step 4의 `class TestJobPostAPI:` 앞에 데코레이터 추가).

- [ ] **Step 5: 테스트 실행**

Run: `pytest tests/test_board_jobs.py -v`
Expected: PASS (8 tests: 기존 2개 + 이번에 추가한 6개)

- [ ] **Step 6: 커밋**

```bash
git add apps/board config/urls.py tests/test_board_jobs.py
git commit -m "feat: JobPost 목록/생성/상세/수정/삭제 API"
```

---

### Task 5: 지원하기 + 지원자 목록 API

**Files:**
- Modify: `apps/board/serializers.py`
- Modify: `apps/board/views.py`
- Modify: `apps/board/urls.py`
- Test: `tests/test_board_jobs.py`

**Interfaces:**
- Consumes: `apps.board.models.JobApplication` (Task 3), `JobPost` (Task 2)
- Produces: URL `/api/board/jobs/<int:pk>/apply/` (POST), `/api/board/jobs/<int:pk>/applications/` (GET)

- [ ] **Step 1: JobApplicationSerializer 추가**

`apps/board/serializers.py` 최상단 import 줄을 아래로 교체:
```python
from rest_framework import serializers

from .models import JobApplication, JobPost
```

파일 끝에 추가:
```python


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['id', 'name', 'phone', 'message', 'applied_at']
```

- [ ] **Step 2: JobApplyView, JobApplicationListView 작성**

`apps/board/views.py` 상단 import를 아래로 교체:
```python
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobApplication, JobPost
from .serializers import JobApplicationSerializer, JobPostSerializer, JobPostWriteSerializer
```

파일 끝에 추가:
```python


class JobApplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            job_post = JobPost.objects.get(pk=pk, is_active=True)
        except JobPost.DoesNotExist:
            return Response(
                {'error': '모집글을 찾을 수 없습니다.', 'code': 'job_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if JobApplication.objects.filter(job_post=job_post, applicant=request.user).exists():
            return Response(
                {'error': '이미 지원한 모집글입니다.', 'code': 'already_applied'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = request.data.get('name') or request.user.profile.applicant_name
        phone = request.data.get('phone') or request.user.phone
        if not name or not phone:
            return Response(
                {'error': '이름과 전화번호를 입력해주세요.', 'code': 'missing_applicant_info'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application = JobApplication.objects.create(
            job_post=job_post, applicant=request.user,
            name=name, phone=phone, message=request.data.get('message', ''),
        )

        profile = request.user.profile
        if profile.applicant_name != name:
            profile.applicant_name = name
            profile.save(update_fields=['applicant_name'])
        if request.user.phone != phone:
            request.user.phone = phone
            request.user.save(update_fields=['phone'])

        return Response(JobApplicationSerializer(application).data, status=status.HTTP_201_CREATED)


class JobApplicationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            job_post = JobPost.objects.get(pk=pk, is_active=True)
        except JobPost.DoesNotExist:
            return Response(
                {'error': '모집글을 찾을 수 없습니다.', 'code': 'job_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if job_post.created_by_id != request.user.id:
            return Response(
                {'error': '작성자만 지원자 목록을 볼 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )

        applications = job_post.applications.order_by('-applied_at')
        return Response(JobApplicationSerializer(applications, many=True).data)
```

- [ ] **Step 3: urls.py 갱신**

`apps/board/urls.py`를 아래로 교체:
```python
from django.urls import path

from .views import (
    JobApplicationListView, JobApplyView, JobPostDetailView, JobPostListView,
)

urlpatterns = [
    path('jobs/', JobPostListView.as_view()),
    path('jobs/<int:pk>/', JobPostDetailView.as_view()),
    path('jobs/<int:pk>/apply/', JobApplyView.as_view()),
    path('jobs/<int:pk>/applications/', JobApplicationListView.as_view()),
]
```

- [ ] **Step 4: 실패하는 테스트 작성**

`tests/test_board_jobs.py` 끝에 추가:
```python


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
```

`JobApplication`을 이미 import했는지 확인 — `tests/test_board_jobs.py` 상단 import가 `from apps.board.models import JobApplication, JobPost`인지 확인(Task 3에서 이미 추가됨).

- [ ] **Step 5: 테스트 실행**

Run: `pytest tests/test_board_jobs.py -v`
Expected: PASS (13 tests)

- [ ] **Step 6: 커밋**

```bash
git add apps/board tests/test_board_jobs.py
git commit -m "feat: 사람 구해요 지원하기 + 지원자 목록 API"
```

---

### Task 6: Cloudflare R2 스토리지 설정 + HousingPost/HousingPhoto 모델

**Files:**
- Modify: `requirements.txt`
- Modify: `config/settings.py`
- Modify: `apps/board/models.py`
- Modify: `apps/board/admin.py`
- Test: `tests/test_board_housing.py`

**Interfaces:**
- Consumes: `apps.board.models.OKCHEON_REGIONS` (Task 2)
- Produces: `apps.board.models.HousingPost`, `HousingPhoto`

- [ ] **Step 1: 의존성 추가**

`requirements.txt` 끝에 추가:
```
django-storages[s3]>=1.14
Pillow>=10.0
```

Run: `pip install -r requirements.txt`

- [ ] **Step 2: R2 스토리지 설정 추가**

`config/settings.py`의 `STATIC_ROOT = BASE_DIR / 'staticfiles'` 다음 줄에 추가:
```python

# ── Cloudflare R2 (이미지 저장) ─────────────────────────────────────────────

_r2_account_id = os.environ.get('R2_ACCOUNT_ID', '')
STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        'OPTIONS': {
            'access_key': os.environ.get('R2_ACCESS_KEY_ID', ''),
            'secret_key': os.environ.get('R2_SECRET_ACCESS_KEY', ''),
            'bucket_name': os.environ.get('R2_BUCKET_NAME', ''),
            'endpoint_url': f'https://{_r2_account_id}.r2.cloudflarestorage.com' if _r2_account_id else '',
            'addressing_style': 'virtual',
            'default_acl': None,
            'querystring_auth': False,
            'custom_domain': os.environ.get('R2_PUBLIC_URL', '').replace('https://', '').replace('http://', ''),
        },
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}
```

`'apps.board'`도 `django-storages`를 쓰려면 별도 `INSTALLED_APPS` 등록이 필요 없다(`storages` 앱 자체는 `INSTALLED_APPS` 등록 불필요, `STORAGES` 설정만으로 동작).

- [ ] **Step 3: HousingPost, HousingPhoto 모델 추가**

`apps/board/models.py` 최상단 import를 아래로 교체:
```python
from django.contrib.postgres.fields import ArrayField
from django.db import models
```

파일 끝에 추가:
```python


ROOM_TYPES = [
    ('원룸', '원룸'), ('투룸이상', '투룸이상'), ('오피스텔', '오피스텔'), ('주택', '주택'), ('기타', '기타'),
]
DEAL_TYPES = [('전세', '전세'), ('월세', '월세')]


class HousingPost(models.Model):
    title = models.CharField(max_length=100)
    region = models.CharField(max_length=10, choices=OKCHEON_REGIONS, blank=True)
    detail_address = models.TextField()
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    room_layout = models.CharField(max_length=100, blank=True)
    size_pyeong = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    deal_type = models.CharField(max_length=10, choices=DEAL_TYPES)
    deposit = models.IntegerField(null=True, blank=True)
    monthly_rent = models.IntegerField(null=True, blank=True)
    maintenance_fee = models.IntegerField(null=True, blank=True)
    options = ArrayField(models.TextField(), default=list, blank=True)
    description = models.TextField(blank=True)
    contact_name = models.CharField(max_length=50)
    contact_phone = models.CharField(max_length=20)
    lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    created_by = models.ForeignKey(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='housing_posts',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'housing_posts'
        indexes = [
            models.Index(fields=['room_type']),
            models.Index(fields=['region']),
        ]


class HousingPhoto(models.Model):
    housing_post = models.ForeignKey(HousingPost, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='housing_photos/')
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'housing_photos'
        ordering = ['order', 'id']
```

- [ ] **Step 4: admin.py 갱신**

`apps/board/admin.py`를 아래로 교체:
```python
from django.contrib import admin

from .models import HousingPhoto, HousingPost, JobApplication, JobPost


class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    fields = ['applicant', 'name', 'phone', 'applied_at']
    readonly_fields = ['applied_at']


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    inlines = [JobApplicationInline]
    list_display = ['title', 'category', 'region', 'created_by', 'is_active']
    list_filter = ['category', 'region', 'is_active']
    search_fields = ['title', 'description']


class HousingPhotoInline(admin.TabularInline):
    model = HousingPhoto
    extra = 0
    fields = ['image', 'order']


@admin.register(HousingPost)
class HousingPostAdmin(admin.ModelAdmin):
    inlines = [HousingPhotoInline]
    list_display = ['title', 'room_type', 'region', 'deal_type', 'created_by', 'is_active']
    list_filter = ['room_type', 'region', 'deal_type', 'is_active']
    search_fields = ['title', 'detail_address']
```

- [ ] **Step 5: 마이그레이션 생성 및 적용**

Run: `python manage.py makemigrations board`
Expected: `apps/board/migrations/0003_housingpost_housingphoto.py` 생성됨

Run: `python manage.py migrate`
Expected: `OK`

- [ ] **Step 6: 실패하는 모델 테스트 작성**

`tests/test_board_housing.py`:
```python
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
```

- [ ] **Step 7: 테스트 실행**

Run: `pytest tests/test_board_housing.py -v`
Expected: PASS

- [ ] **Step 8: 커밋**

```bash
git add requirements.txt config/settings.py apps/board tests/test_board_housing.py
git commit -m "feat: Cloudflare R2 스토리지 설정 + HousingPost/HousingPhoto 모델"
```

---

### Task 7: HousingPost API (목록/생성(multipart)/상세/수정/삭제)

**Files:**
- Modify: `apps/board/serializers.py`
- Modify: `apps/board/views.py`
- Modify: `apps/board/urls.py`
- Test: `tests/test_board_housing.py`

**Interfaces:**
- Consumes: `apps.board.models.HousingPost`, `HousingPhoto` (Task 6), `lib.services.geocoding.geocode_address(address: str) -> tuple[Decimal, Decimal] | None`
- Produces: URL `/api/board/housing/`, `/api/board/housing/<int:pk>/`

- [ ] **Step 1: 시리얼라이저 추가**

`apps/board/serializers.py` 상단 import를 아래로 교체:
```python
from rest_framework import serializers

from .models import HousingPhoto, HousingPost, JobApplication, JobPost
```

파일 끝에 추가:
```python


class HousingPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingPhoto
        fields = ['id', 'image', 'order']


class HousingPostSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    photos = HousingPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = HousingPost
        fields = [
            'id', 'title', 'region', 'detail_address', 'room_type', 'room_layout',
            'size_pyeong', 'deal_type', 'deposit', 'monthly_rent', 'maintenance_fee',
            'options', 'description', 'contact_name', 'contact_phone', 'lat', 'lng',
            'photos', 'is_owner', 'created_at',
        ]

    def get_is_owner(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.created_by_id == user.id


class HousingPostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingPost
        fields = [
            'title', 'region', 'detail_address', 'room_type', 'room_layout',
            'size_pyeong', 'deal_type', 'deposit', 'monthly_rent', 'maintenance_fee',
            'options', 'description', 'contact_name', 'contact_phone',
        ]
        extra_kwargs = {
            'region': {'required': False},
            'room_layout': {'required': False},
            'size_pyeong': {'required': False},
            'deposit': {'required': False},
            'monthly_rent': {'required': False},
            'maintenance_fee': {'required': False},
            'options': {'required': False},
            'description': {'required': False},
        }
```

- [ ] **Step 2: 뷰 작성**

`apps/board/views.py` 상단 import를 아래로 교체:
```python
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lib.services.geocoding import geocode_address

from .models import HousingPhoto, HousingPost, JobApplication, JobPost
from .serializers import (
    HousingPostSerializer, HousingPostWriteSerializer,
    JobApplicationSerializer, JobPostSerializer, JobPostWriteSerializer,
)
```

파일 끝에 추가:
```python


class HousingPostListView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        posts = HousingPost.objects.filter(is_active=True).order_by('-created_at')
        room_type = request.query_params.get('room_type')
        if room_type:
            posts = posts.filter(room_type=room_type)
        region = request.query_params.get('region')
        if region:
            posts = posts.filter(region=region)
        return Response(HousingPostSerializer(posts, many=True, context={'request': request}).data)

    def post(self, request):
        serializer = HousingPostWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        coords = geocode_address(serializer.validated_data['detail_address'])
        lat, lng = coords if coords else (None, None)

        post = serializer.save(created_by=request.user, lat=lat, lng=lng)

        images = request.FILES.getlist('images')
        HousingPhoto.objects.bulk_create([
            HousingPhoto(housing_post=post, image=img, order=i)
            for i, img in enumerate(images)
        ])

        return Response(
            HousingPostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class HousingPostDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def _get_object(self, pk):
        try:
            return HousingPost.objects.get(pk=pk, is_active=True)
        except HousingPost.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '매물을 찾을 수 없습니다.', 'code': 'housing_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(HousingPostSerializer(post, context={'request': request}).data)

    def patch(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '매물을 찾을 수 없습니다.', 'code': 'housing_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if post.created_by_id != request.user.id:
            return Response(
                {'error': '작성자만 수정할 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = HousingPostWriteSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_address = serializer.validated_data.get('detail_address')
        if new_address and new_address != post.detail_address:
            coords = geocode_address(new_address)
            post.lat, post.lng = coords if coords else (None, None)

        serializer.save()
        return Response(HousingPostSerializer(post, context={'request': request}).data)

    def delete(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '매물을 찾을 수 없습니다.', 'code': 'housing_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if post.created_by_id != request.user.id:
            return Response(
                {'error': '작성자만 삭제할 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )
        post.is_active = False
        post.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 3: urls.py 갱신**

`apps/board/urls.py`를 아래로 교체:
```python
from django.urls import path

from .views import (
    HousingPostDetailView, HousingPostListView,
    JobApplicationListView, JobApplyView, JobPostDetailView, JobPostListView,
)

urlpatterns = [
    path('jobs/', JobPostListView.as_view()),
    path('jobs/<int:pk>/', JobPostDetailView.as_view()),
    path('jobs/<int:pk>/apply/', JobApplyView.as_view()),
    path('jobs/<int:pk>/applications/', JobApplicationListView.as_view()),
    path('housing/', HousingPostListView.as_view()),
    path('housing/<int:pk>/', HousingPostDetailView.as_view()),
]
```

- [ ] **Step 4: 실패하는 API 테스트 작성**

`tests/test_board_housing.py` 끝에 추가:
```python


from unittest.mock import patch

from rest_framework.test import APIClient


@override_settings(STORAGES=TEST_STORAGES)
@pytest.mark.django_db
class TestHousingPostAPI:
    def test_list_filters_by_room_type(self, tmp_path, settings):
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
```

- [ ] **Step 5: 테스트 실행**

Run: `pytest tests/test_board_housing.py -v`
Expected: PASS (4 tests)

Run: `pytest tests/test_board_jobs.py tests/test_board_housing.py tests/test_board_smoke.py -v`
Expected: 전체 PASS (약 18개 테스트)

- [ ] **Step 6: 전체 회귀 테스트**

Run: `pytest -v`
Expected: 기존 테스트(`test_policy_matcher.py` 등)와 이번에 추가한 테스트 모두 PASS

- [ ] **Step 7: 커밋**

```bash
git add apps/board tests/test_board_housing.py
git commit -m "feat: HousingPost 목록/생성(멀티파트)/상세/수정/삭제 API"
```

---

## 구현 후 체크리스트 (코드 외 작업)

- [ ] Railway 프로덕션 환경변수에 `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL` 등록 (`railway variables --set KEY=VALUE`)
- [ ] `docs/git/commit-logs/`에 Task 형식 커밋 로그 문서 작성 (레포 컨벤션, 별도 커밋으로 추가)
- [ ] 배포 후 `POST /api/board/jobs/`, `POST /api/board/housing/`(이미지 포함)을 실제로 호출해 R2에 파일이 올라가는지, `image` URL이 `R2_PUBLIC_URL` 기준으로 정상 응답되는지 수동 확인
