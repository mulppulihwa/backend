# 신뢰도 기반 안심 검증 마크 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `apps.places.LocalPlace`에 옥천신문/옥천군 상담센터 추천 뱃지(관리자 큐레이션)와 사용자 추천 카운터(`PlaceEndorsement`, "추천해요" 버튼)를 추가하고 API로 노출한다.

**Architecture:** 기존 `apps.places` 컨벤션(APIView, 읽기/쓰기 시리얼라이저 분리, `{'error','code'}` 에러)을 그대로 따르는 최소 확장. 새 모델은 `PlaceEndorsement` 하나뿐이고, 나머지는 `LocalPlace`에 필드 2개 추가.

**Tech Stack:** Django 6.1, Django REST Framework, pytest + pytest-django (기존 `apps.board` 작업에서 이미 배선 완료된 DIRECT_URL 테스트 DB 설정 그대로 재사용).

**설계 스펙 원본:** `docs/superpowers/specs/2026-08-20-trust-badges-design.md` — 특히 "판단 사항" 섹션은 야간 무인 작업 중 내린 결정이라 사용자 검토가 필요함(이 플랜에는 그 결정을 이미 반영한 코드만 담겨 있음).

## Global Constraints

- 뱃지 필드(`okcheon_news_recommended`, `counseling_center_recommended`)는 관리자 전용 — `LocalPlaceWriteSerializer`에 포함하지 않는다
- 추천(`PlaceEndorsement`) 중복 호출은 에러 없이 멱등 처리 (스펙의 "판단 사항 1" 참고 — 아침에 뒤집힐 수 있는 결정)
- 추천 취소(언추천) 엔드포인트는 만들지 않는다
- 목록 API(`GET /api/places/`)에서 추천 수/추천 여부 계산이 N+1을 일으키지 않도록 쿼리셋 단계에서 annotate
- 에러 응답은 항상 `{'error': '한국어 메시지', 'code': 'snake_case_code'}` + 적절한 HTTP status (기존 `PlaceDetailView`와 동일 메시지 재사용)

---

### Task 1: 모델 확장 — LocalPlace 뱃지 필드 + PlaceEndorsement

**Files:**
- Modify: `apps/places/models.py`
- Modify: `apps/places/admin.py`
- Test: `tests/test_places_endorsement.py`

**Interfaces:**
- Produces: `LocalPlace.okcheon_news_recommended`, `LocalPlace.counseling_center_recommended`, `apps.places.models.PlaceEndorsement` (Task 2/3이 이 모델의 `place`/`user`/`related_name='endorsements'`를 그대로 씀)

- [ ] **Step 1: LocalPlace에 뱃지 필드 2개 추가**

`apps/places/models.py`의 `LocalPlace` 클래스 안, `is_active = models.BooleanField(default=True)` 다음 줄에 추가:
```python

    # 신뢰도 기반 안심 검증 마크 — 관리자 큐레이션
    okcheon_news_recommended = models.BooleanField(default=False)
    counseling_center_recommended = models.BooleanField(default=False)
```

- [ ] **Step 2: PlaceEndorsement 모델 추가**

`apps/places/models.py` 파일 끝에 추가:
```python


class PlaceEndorsement(models.Model):
    place = models.ForeignKey(LocalPlace, on_delete=models.CASCADE, related_name='endorsements')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='place_endorsements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'place_endorsements'
        unique_together = [['place', 'user']]
```

- [ ] **Step 3: admin.py 갱신**

`apps/places/admin.py`를 아래로 교체:
```python
from django.contrib import admin

from .models import LocalPlace, PlaceEndorsement


@admin.register(LocalPlace)
class LocalPlaceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'address', 'created_by', 'is_active',
        'okcheon_news_recommended', 'counseling_center_recommended',
    ]
    list_filter = ['category', 'is_active', 'receipt_claimable', 'okcheon_news_recommended', 'counseling_center_recommended']
    list_editable = ['okcheon_news_recommended', 'counseling_center_recommended']
    search_fields = ['name', 'address']


@admin.register(PlaceEndorsement)
class PlaceEndorsementAdmin(admin.ModelAdmin):
    list_display = ['place', 'user', 'created_at']
    list_filter = ['place']
```

(`list_editable`을 쓰려면 해당 필드가 `list_display`에도 있어야 하고, `ModelAdmin`에 `list_display_links`가 명시적으로 없으면 Django가 첫 번째 컬럼을 자동으로 링크 컬럼으로 잡아 `list_editable`과 충돌하지 않는다 — 지금처럼 `name`이 링크 컬럼, 뱃지 두 개가 editable인 구성은 문제없다.)

- [ ] **Step 4: 마이그레이션 생성 및 적용**

Run: `python manage.py makemigrations places`
Expected: `apps/places/migrations/000X_localplace_okcheon_news_recommended_and_more.py` (또는 유사한 자동 생성 이름) 생성됨 — `LocalPlace`에 필드 2개 추가 + `PlaceEndorsement` 모델 생성이 한 마이그레이션에 묶여 나올 수 있음, 정상.

Run: `python manage.py migrate`
Expected: `OK`

- [ ] **Step 5: 실패하는 모델 테스트 작성**

`tests/test_places_endorsement.py`:
```python
"""apps.places 신뢰도 기반 안심 검증 마크(뱃지 + 추천) 모델/API 테스트."""
import pytest
from django.db import IntegrityError

from apps.places.models import LocalPlace, PlaceEndorsement
from apps.users.models import User


@pytest.mark.django_db
def test_local_place_badge_fields_default_false():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    assert place.okcheon_news_recommended is False
    assert place.counseling_center_recommended is False


@pytest.mark.django_db
def test_duplicate_endorsement_blocked_at_db_level():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    user = User.objects.create_user(kakao_id='endorser1')
    PlaceEndorsement.objects.create(place=place, user=user)

    with pytest.raises(IntegrityError):
        PlaceEndorsement.objects.create(place=place, user=user)
```

- [ ] **Step 6: 테스트 실행**

Run: `pytest tests/test_places_endorsement.py -v`
Expected: PASS (2 tests)

- [ ] **Step 7: 커밋**

```bash
git add apps/places tests/test_places_endorsement.py
git commit -m "feat: LocalPlace 신뢰도 뱃지 필드 + PlaceEndorsement 모델 추가"
```

---

### Task 2: 시리얼라이저 확장 — 뱃지/추천수/추천여부 노출 (N+1 방지)

**Files:**
- Modify: `apps/places/serializers.py`
- Modify: `apps/places/views.py`
- Test: `tests/test_places_endorsement.py`

**Interfaces:**
- Consumes: `apps.places.models.PlaceEndorsement` (Task 1)
- Produces: `LocalPlaceSerializer`가 응답에 `okcheon_news_recommended`, `counseling_center_recommended`, `endorsement_count`, `is_endorsed` 필드를 포함 (Task 3의 endorse 응답이 이 값들과 형식을 맞춰 씀)

- [ ] **Step 1: LocalPlaceSerializer 갱신**

`apps/places/serializers.py`를 아래로 교체:
```python
from rest_framework import serializers

from .models import LocalPlace


class LocalPlaceSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    endorsement_count = serializers.SerializerMethodField()
    is_endorsed = serializers.SerializerMethodField()

    class Meta:
        model = LocalPlace
        fields = [
            'id', 'name', 'category', 'address', 'phone', 'business_hours',
            'local_memo', 'lat', 'lng', 'subsidy_tags', 'receipt_claimable',
            'is_owner', 'okcheon_news_recommended', 'counseling_center_recommended',
            'endorsement_count', 'is_endorsed',
        ]

    def get_is_owner(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.created_by_id == user.id

    def get_endorsement_count(self, obj):
        count = getattr(obj, 'endorsement_count_anno', None)
        return count if count is not None else obj.endorsements.count()

    def get_is_endorsed(self, obj):
        anno = getattr(obj, 'is_endorsed_anno', None)
        if anno is not None:
            return anno
        user = self.context['request'].user
        return user.is_authenticated and obj.endorsements.filter(user=user).exists()


class LocalPlaceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalPlace
        fields = ['name', 'category', 'address', 'phone', 'business_hours', 'local_memo', 'lat', 'lng']
        extra_kwargs = {
            'phone': {'required': False},
            'business_hours': {'required': False},
            'local_memo': {'required': False},
            'lat': {'required': False},
            'lng': {'required': False},
        }
```

`get_endorsement_count`/`get_is_endorsed`는 쿼리셋에 `endorsement_count_anno`/`is_endorsed_anno` annotation이 있으면 그 값을 쓰고(목록 API, Step 2), 없으면(상세 API처럼 단건 조회라 annotate 안 해도 쿼리 1번뿐인 경우) `obj.endorsements.count()`/`.filter().exists()`로 즉석 계산한다.

- [ ] **Step 2: PlaceListView에 annotate 추가 (N+1 방지)**

`apps/places/views.py` 상단 import 블록을 아래로 교체 (기존 `from .models import LocalPlace` 줄과 `from rest_framework...` 줄들을 포함한 전체 import 블록):
```python
from django.db.models import Count, Exists, OuterRef
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lib.services.geocoding import geocode_address

from .models import LocalPlace, PlaceEndorsement
from .serializers import LocalPlaceSerializer, LocalPlaceWriteSerializer
```

`PlaceListView.get` 메서드를 아래로 교체:
```python
    def get(self, request):
        places = LocalPlace.objects.filter(is_active=True).annotate(
            endorsement_count_anno=Count('endorsements'),
        )
        if request.user.is_authenticated:
            places = places.annotate(
                is_endorsed_anno=Exists(
                    PlaceEndorsement.objects.filter(place=OuterRef('pk'), user=request.user)
                ),
            )
        places = places.order_by('name')
        return Response(
            LocalPlaceSerializer(places, many=True, context={'request': request}).data
        )
```

- [ ] **Step 3: 실패하는 API 테스트 작성**

`tests/test_places_endorsement.py`에 추가 (상단 import에 `from rest_framework.test import APIClient` 추가):
```python
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_serializer_exposes_badges_and_counts():
    place = LocalPlace.objects.create(
        name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가',
        okcheon_news_recommended=True,
    )
    user = User.objects.create_user(kakao_id='endorser2')
    PlaceEndorsement.objects.create(place=place, user=user)

    client = APIClient()
    client.force_authenticate(user=user)
    res = client.get('/api/places/')
    assert res.status_code == 200
    data = next(p for p in res.data if p['id'] == place.id)
    assert data['okcheon_news_recommended'] is True
    assert data['counseling_center_recommended'] is False
    assert data['endorsement_count'] == 1
    assert data['is_endorsed'] is True


@pytest.mark.django_db
def test_serializer_is_endorsed_false_for_other_user():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    endorser = User.objects.create_user(kakao_id='endorser3')
    other = User.objects.create_user(kakao_id='viewer1')
    PlaceEndorsement.objects.create(place=place, user=endorser)

    client = APIClient()
    client.force_authenticate(user=other)
    res = client.get('/api/places/')
    data = next(p for p in res.data if p['id'] == place.id)
    assert data['endorsement_count'] == 1
    assert data['is_endorsed'] is False
```

- [ ] **Step 4: 테스트 실행**

Run: `pytest tests/test_places_endorsement.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: 커밋**

```bash
git add apps/places tests/test_places_endorsement.py
git commit -m "feat: LocalPlace API에 신뢰도 뱃지/추천수/추천여부 노출 (N+1 방지 annotate)"
```

---

### Task 3: 추천하기 API

**Files:**
- Modify: `apps/places/views.py`
- Modify: `apps/places/urls.py`
- Test: `tests/test_places_endorsement.py`

**Interfaces:**
- Consumes: `apps.places.models.PlaceEndorsement` (Task 1), `LocalPlaceSerializer`의 `endorsement_count`/`is_endorsed` (Task 2)
- Produces: URL `/api/places/<int:pk>/endorse/` (POST)

- [ ] **Step 1: PlaceEndorseView 작성**

`apps/places/views.py` 파일 끝에 추가:
```python


class PlaceEndorseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            place = LocalPlace.objects.get(pk=pk, is_active=True)
        except LocalPlace.DoesNotExist:
            return Response(
                {'error': '사용처를 찾을 수 없습니다.', 'code': 'place_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        PlaceEndorsement.objects.get_or_create(place=place, user=request.user)

        return Response({
            'endorsement_count': place.endorsements.count(),
            'is_endorsed': True,
        })
```

`apps/places/views.py` 상단 import는 Task 2의 Step 2에서 이미 `from .models import LocalPlace, PlaceEndorsement`로 정리되어 있으므로 추가 변경 불필요.

- [ ] **Step 2: urls.py 갱신**

`apps/places/urls.py`를 아래로 교체:
```python
from django.urls import path

from .views import PlaceDetailView, PlaceEndorseView, PlaceListView

urlpatterns = [
    path('', PlaceListView.as_view()),
    path('<int:pk>/', PlaceDetailView.as_view()),
    path('<int:pk>/endorse/', PlaceEndorseView.as_view()),
]
```

- [ ] **Step 3: 실패하는 API 테스트 작성**

`tests/test_places_endorsement.py` 끝에 추가:
```python


@pytest.mark.django_db
def test_endorse_requires_auth():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    res = APIClient().post(f'/api/places/{place.id}/endorse/')
    assert res.status_code == 401


@pytest.mark.django_db
def test_endorse_increments_count():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    user = User.objects.create_user(kakao_id='endorser4')

    client = APIClient()
    client.force_authenticate(user=user)
    res = client.post(f'/api/places/{place.id}/endorse/')
    assert res.status_code == 200
    assert res.data['endorsement_count'] == 1
    assert res.data['is_endorsed'] is True


@pytest.mark.django_db
def test_endorse_twice_is_idempotent():
    place = LocalPlace.objects.create(name='옥천 식당', category='음식점', address='옥천군 옥천읍 어딘가')
    user = User.objects.create_user(kakao_id='endorser5')

    client = APIClient()
    client.force_authenticate(user=user)
    client.post(f'/api/places/{place.id}/endorse/')
    res = client.post(f'/api/places/{place.id}/endorse/')
    assert res.status_code == 200
    assert res.data['endorsement_count'] == 1
    assert PlaceEndorsement.objects.filter(place=place, user=user).count() == 1


@pytest.mark.django_db
def test_endorse_nonexistent_place_404():
    user = User.objects.create_user(kakao_id='endorser6')
    client = APIClient()
    client.force_authenticate(user=user)
    res = client.post('/api/places/99999/endorse/')
    assert res.status_code == 404
    assert res.data['code'] == 'place_not_found'
```

- [ ] **Step 4: 테스트 실행**

Run: `pytest tests/test_places_endorsement.py -v`
Expected: PASS (8 tests)

Run: `pytest tests/ -v`
Expected: 기존 테스트 전부 + 이번에 추가한 8개 전부 PASS

- [ ] **Step 5: 커밋**

```bash
git add apps/places tests/test_places_endorsement.py
git commit -m "feat: 사용처 추천하기(추천해요) API 추가"
```

---

## 구현 후 체크리스트 (코드 외 작업, 아침에 확인 요망)

- [ ] 스펙 문서의 "판단 사항" 4가지 검토 — 특히 추천 재클릭을 멱등 처리한 것과 언추천 미구현
- [ ] 옥천신문/상담센터 추천 여부를 실제로 누가/어떻게 Django Admin에 반영할지 운영 프로세스 논의
- [ ] 프론트엔드와 뱃지 UI/추천 버튼 연동
