# 백엔드 플랜

> 백엔드: Django + DRF (Python) / 프론트엔드: Next.js (React) — 분리 구조  
> 프론트엔드 관련 내용(UI, 페이지 구조)은 platform-plan.md 참고.
>
> **정책 매칭 파이프라인: Pipeline A 채택 (확정)**  
> SQL 1차 필터 + Python condition_tree 평가. LLM은 저장 단계(공고문 파싱)에서만 사용.  
> 매칭 단계 LLM 호출 없음 → 비용 0, 응답 일관성 보장.  
> 근거: `docs/research/policy-matching-methods.md §10` 참고.

---

## 1. 기술 스택

| 레이어 | 기술 | 선택 이유 |
|---|---|---|
| 백엔드 프레임워크 | Django 5.x + DRF | 팀 경험 충분, Django Admin 자동 생성 |
| 언어 | Python 3.12 | 팀 익숙, anthropic SDK 풍부 |
| DB | PostgreSQL (Supabase) | GIN 인덱스, JSONB, ArrayField 지원 |
| ORM | Django ORM + psycopg2 | 모델 → 마이그레이션 자동화 |
| 인증 | JWT (simplejwt) + Kakao OAuth | 프론트-백 분리 구조에 적합 |
| LLM 파싱 | Claude API (anthropic Python SDK) | 공고문 → 정책 조건 자동 추출 |
| 검증 | Pydantic v2 | Claude 출력 구조화 검증 |
| 지도 | 카카오 로컬 API (Django 뷰에서 프록시) | API 키 노출 방지 |
| 프론트 배포 | Vercel | Next.js 최적화 |
| 백엔드 배포 | Railway | Django + Python 배포 간단 |
| 플랫폼 | 웹 (모바일 반응형) | 앱스토어 심사 없음 |

---

## 2. 아키텍처

```
브라우저 (Next.js React)
  │  HTTPS
  ▼
Vercel
  └── /app/**  — React 컴포넌트 (프론트엔드)
        │  API 요청 (JSON)
        ▼
Railway (Django + DRF)
  ├── /api/policies/**
  ├── /api/places/**
  ├── /api/auth/**
  ├── /admin/          ← Django Admin (자동 생성)
  └── CORS 허용: Vercel 도메인만
        │
        ▼
  Supabase PostgreSQL
  ├── policies
  ├── users
  ├── regions
  └── local_places

  외부 API (Django 서버에서 직접 호출)
  ├── 카카오 OAuth  ← /api/auth/kakao/
  ├── 카카오 로컬  ← /api/places/geocode/
  └── Claude API   ← /api/admin/policies/parse/
```

---

## 3. 디렉토리 구조

```
backend/
├── config/
│   ├── settings.py          (환경변수, 앱 등록, DB 설정)
│   ├── urls.py              (루트 URL 라우팅)
│   └── wsgi.py
│
├── apps/
│   ├── users/
│   │   ├── models.py        (User 모델)
│   │   ├── serializers.py
│   │   ├── views.py         (카카오 OAuth 콜백, 프로필 API)
│   │   ├── signals.py       (UserProfile post_save 자동 생성)
│   │   ├── apps.py          (시그널 연결)
│   │   └── urls.py
│   ├── policies/
│   │   ├── models.py        (Policy 모델)
│   │   ├── serializers.py
│   │   ├── views.py         (매칭, 목록, 상세, 파싱)
│   │   ├── admin.py         (Django Admin 커스터마이징)
│   │   └── urls.py
│   ├── places/
│   │   ├── models.py        (LocalPlace 모델)
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── admin.py
│   │   └── urls.py
│   └── regions/
│       ├── models.py        (Region 모델)
│       ├── views.py         (드롭다운용)
│       └── urls.py
│
├── lib/
│   ├── policy_matcher.py    (매칭 파이프라인)
│   ├── condition_tree.py    (AND/OR/NOT 평가기)
│   ├── region_hierarchy.py  (recursive CTE)
│   ├── policy_parser.py     (Claude API 파싱)
│   └── bokjiro_sync.py      (복지로 API 동기화)
│
├── tests/
│   ├── test_condition_tree.py
│   ├── test_policy_matcher.py
│   └── test_policy_parser.py
│
├── requirements.txt
└── manage.py
```

---

## 4. 환경변수

```bash
# .env (절대 커밋 금지)

# Django
SECRET_KEY=랜덤_50자_이상
DEBUG=False
ALLOWED_HOSTS=railway.app도메인,localhost

# DB (Supabase)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# 카카오
KAKAO_CLIENT_ID=abc123
KAKAO_CLIENT_SECRET=xyz789
KAKAO_REDIRECT_URI=https://your-api.railway.app/api/auth/kakao/  # 로컬: http://localhost:8000/api/auth/kakao/

# 카카오 로컬 API
KAKAO_LOCAL_API_KEY=local_key

# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# 복지로 API (data.go.kr)
BOKJIRO_API_KEY=119f505d...  # data.go.kr 일반 인증키

# CORS (프론트 Vercel 도메인)
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

---

## 5. Django 모델

### users/models.py

User는 인증 관련 필드만, 정책 매칭 기준은 UserProfile로 분리.
`profile_completed`는 온보딩 흐름과 연결되므로 User에 유지.

```python
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

GENDER_CHOICES   = [('남', '남'), ('여', '여')]
MARITAL_CHOICES  = [('미혼', '미혼'), ('기혼', '기혼')]
HOUSEHOLD_CHOICES = [('독거', '독거'), ('부부', '부부'), ('기타', '기타')]
INCOME_CHOICES    = [('기초수급', '기초수급'), ('차상위', '차상위'), ('일반', '일반')]

class User(AbstractUser):
    username = None                         # 카카오 로그인만 사용
    kakao_id = models.TextField(unique=True)
    nickname = models.TextField(blank=True)
    phone    = models.TextField(blank=True) # 알림톡 v1.5

    profile_completed = models.BooleanField(default=False)

    USERNAME_FIELD  = 'kakao_id'            # JWT 식별자
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # 기본 정보
    region_code = models.TextField(blank=True)
    birth_date  = models.DateField(null=True, blank=True)   # age 대신 생년월일 저장
    gender      = models.CharField(max_length=5, choices=GENDER_CHOICES, blank=True)

    # 귀농/귀촌 상태
    occupation_tags = ArrayField(models.TextField(), default=list, blank=True)
    move_in_date    = models.DateField(null=True, blank=True)   # 전입일 (farming_start 대체)

    # 경제 상태
    household_type  = models.CharField(max_length=10, choices=HOUSEHOLD_CHOICES, blank=True)
    income_level    = models.CharField(max_length=10, choices=INCOME_CHOICES, blank=True)
    non_farm_income = models.IntegerField(null=True, blank=True)  # 농업외 소득 (만원 단위)
    marital_status  = models.CharField(max_length=5, choices=MARITAL_CHOICES, blank=True)

    # 농업 자격
    is_farm_registered   = models.BooleanField(null=True)          # 농업경영체 등록 여부
    farm_registered_date = models.DateField(null=True, blank=True)  # 등록일 (1년 이상 조건)
    education_hours      = models.SmallIntegerField(default=0)      # 귀농교육 이수 시간

    # 복지로 API 매칭용
    is_disabled          = models.BooleanField(null=True)           # 장애 여부 (노인 장애 복지 정책 매칭)

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = timezone.now().date()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def years_since_move(self):
        if not self.move_in_date:
            return None
        return (timezone.now().date() - self.move_in_date).days / 365

    class Meta:
        db_table = 'user_profiles'
```

`config/settings.py`에 추가 필수:
```python
AUTH_USER_MODEL = 'users.User'  # 반드시 첫 마이그레이션 전에 설정
```

**설계 근거:**
- `birth_date`: 매년 수동 업데이트 없이 `age` property로 실시간 계산
- `move_in_date`: "전입 후 3/5/6년 이내" 조건을 `years_since_move` property 하나로 커버. 기존 `farming_start` 범주형으로는 정확한 필터 불가
- `gender`: 여성농업인 행복바우처 등 성별 조건 정책 대응
- `marital_status`: 충북행복 결혼공제 미혼 조건 대응
- `is_farm_registered` + `farm_registered_date`: 농업인 공익수당 (1년 이상 등록) 대응
- `education_hours`: 귀농 농업창업·주택구입 지원 교육이수 조건 (8시간/100시간) 대응
- `non_farm_income`: 농업인 공익수당 농업외 소득 3,700만원 미만 조건 대응

### policies/models.py

```python
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex

BENEFIT_TYPES = [
    ('현금지원','현금지원'), ('교육','교육'), ('컨설팅','컨설팅'),
    ('시설','시설'), ('세금감면','세금감면'), ('현물','현물'), ('기타','기타'),
]
SOURCES = [
    ('복지로','복지로'), ('수동입력','수동입력'), ('귀농센터','귀농센터'),
]

class Policy(models.Model):
    title          = models.CharField(max_length=200)
    summary        = models.TextField()
    description    = models.TextField(blank=True)
    benefit_type   = models.CharField(max_length=20, choices=BENEFIT_TYPES, blank=True)
    amount         = models.IntegerField(null=True, blank=True)
    amount_text    = models.CharField(max_length=100, blank=True)
    source         = models.CharField(max_length=20, choices=SOURCES, default='수동입력')

    # 1차 SQL 필터 조건
    min_age        = models.SmallIntegerField(default=0)
    max_age        = models.SmallIntegerField(default=130)
    gender         = models.CharField(max_length=10, default='all')
    region_codes   = ArrayField(models.TextField(), default=list)
    occupation_tags = ArrayField(models.TextField(), default=list)
    household_type = ArrayField(models.TextField(), default=list)
    move_status    = ArrayField(models.TextField(), default=list)
    income_level   = ArrayField(models.TextField(), default=list)
    disability_required = models.BooleanField(null=True)            # None=무관, True=장애인만

    # 복합 조건 트리 (단순 태그로 표현 불가한 경우에만)
    condition_tree = models.JSONField(null=True, blank=True)

    # 신청 정보
    apply_start_date = models.DateField(null=True, blank=True)
    apply_end_date   = models.DateField(null=True, blank=True)
    apply_url        = models.URLField(blank=True)
    managing_org     = models.CharField(max_length=100, blank=True)
    source_url       = models.URLField(blank=True)
    external_id      = models.CharField(max_length=100, blank=True)
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'policies'
        indexes = [
            models.Index(fields=['min_age', 'max_age']),
            models.Index(fields=['apply_end_date']),
            GinIndex(fields=['region_codes'],    name='idx_policies_region_codes'),
            GinIndex(fields=['occupation_tags'], name='idx_policies_occupation_tags'),
            GinIndex(fields=['income_level'],    name='idx_policies_income_level'),
        ]
```

### places/models.py

```python
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex

class LocalPlace(models.Model):
    CATEGORIES = [
        ('지원금사용처','지원금사용처'), ('농자재','농자재'), ('농기계','농기계'),
        ('농협','농협'), ('행정','행정'), ('생활','생활'),
    ]
    name              = models.CharField(max_length=100)
    category          = models.CharField(max_length=20, choices=CATEGORIES)
    address           = models.TextField()
    phone             = models.CharField(max_length=20, blank=True)
    lat               = models.DecimalField(max_digits=10, decimal_places=7, null=True)
    lng               = models.DecimalField(max_digits=10, decimal_places=7, null=True)
    subsidy_tags      = ArrayField(models.TextField(), default=list)
    receipt_claimable = models.BooleanField(default=False)
    local_memo        = models.TextField(blank=True)
    price_notes       = models.TextField(blank=True)
    last_verified     = models.DateField(null=True, blank=True)
    is_active         = models.BooleanField(default=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'local_places'
        indexes = [
            models.Index(fields=['category']),
            GinIndex(fields=['subsidy_tags'], name='idx_places_subsidy_tags'),
        ]
```

### regions/models.py

```python
from django.db import models

class Region(models.Model):
    code        = models.CharField(max_length=10, primary_key=True)  # 예: '43720'
    name        = models.CharField(max_length=50)                     # 예: '옥천군'
    parent_code = models.CharField(max_length=10, null=True, blank=True)  # 예: '43'

    class Meta:
        db_table = 'regions'
```

**초기 데이터:** `data/seed/regions.json` — 시도 17개 + 서비스 대상 시군구 목록  
`python manage.py loaddata regions` 또는 management command로 로드.

---

## 6. Django Admin (자동 생성)

장고 어드민의 핵심 장점 — 모델 등록만 하면 CRUD 패널이 자동으로 생겨.

```python
# policies/admin.py
from django.contrib import admin
from .models import Policy
from lib.policy_parser import parse_policy

@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display  = ['title', 'managing_org', 'apply_end_date', 'is_active']
    list_filter   = ['is_active', 'benefit_type', 'source']
    search_fields = ['title', 'summary', 'managing_org']
    list_editable = ['is_active']
    actions       = ['parse_from_text']   # 커스텀 액션 추가

    # 공고문 파싱 액션 — lib/policy_parser.parse_policy()를 직접 호출
    def parse_from_text(self, request, queryset):
        from lib.policy_parser import parse_policy, PolicyParseError
        for policy in queryset:
            if not hasattr(policy, '_raw_text'):
                self.message_user(request, f'{policy.title}: 공고문 텍스트가 없습니다.', level='warning')
                continue
            try:
                result = parse_policy(policy._raw_text)
                for field, val in result['parsed'].items():
                    if hasattr(policy, field):
                        setattr(policy, field, val)
                policy.save()
                self.message_user(request, f'{policy.title}: 파싱 완료 (confidence={result["confidence"]:.2f})')
            except PolicyParseError as e:
                self.message_user(request, f'{policy.title}: {e}', level='error')
    parse_from_text.short_description = 'AI로 공고문 자동 파싱'

    # 실제 사용: Admin Policy 수정 화면에 raw_text TextField 추가하고
    # 위 액션 호출 시 해당 필드를 읽도록 개선 필요 (v1.5)
```

```python
# places/admin.py
from django.contrib import admin
from .models import LocalPlace

@admin.register(LocalPlace)
class LocalPlaceAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'address', 'is_active']
    list_filter   = ['category', 'is_active', 'receipt_claimable']
    search_fields = ['name', 'address']
```

`/admin/` 접속하면 정책·장소 CRUD가 이미 다 동작함. 직접 만들 필요 없음.

---

## 7. 인증 구조 (Kakao OAuth + JWT)

프론트-백 분리 구조에서 Kakao OAuth 흐름:

```
① 프론트: [카카오 로그인] 버튼 클릭
② 프론트: 카카오 OAuth 페이지로 리다이렉트
③ 카카오: 인증 후 code 발급 → 프론트로 콜백
④ 프론트: code를 Django에 전송
    POST /api/auth/kakao/  { "code": "..." }
⑤ Django: code로 카카오 토큰 교환 → 사용자 정보 조회
⑥ Django: User 생성 또는 조회 → JWT 발급
    { "access": "jwt...", "refresh": "jwt..." }
⑦ 프론트: JWT를 localStorage에 저장
⑧ 이후 모든 요청: Authorization: Bearer <jwt>
```

```python
# users/views.py
import httpx
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

class KakaoAuthView(APIView):
    def post(self, request):
        code = request.data.get('code')

        # 카카오 토큰 교환
        token_res = httpx.post('https://kauth.kakao.com/oauth/token', data={
            'grant_type':   'authorization_code',
            'client_id':    settings.KAKAO_CLIENT_ID,
            'client_secret': settings.KAKAO_CLIENT_SECRET,
            'redirect_uri': settings.KAKAO_REDIRECT_URI,
            'code':         code,
        })
        kakao_token = token_res.json()['access_token']

        # 사용자 정보 조회
        user_res = httpx.get('https://kapi.kakao.com/v2/user/me',
            headers={'Authorization': f'Bearer {kakao_token}'}
        )
        kakao_user = user_res.json()
        kakao_id   = str(kakao_user['id'])
        nickname   = kakao_user['kakao_account']['profile']['nickname']

        # User 생성 또는 조회
        user, created = User.objects.get_or_create(
            kakao_id=kakao_id,
            defaults={'nickname': nickname}
        )

        # JWT 발급
        refresh = RefreshToken.for_user(user)
        return Response({
            'access':            str(refresh.access_token),
            'refresh':           str(refresh),
            'profile_completed': user.profile_completed,
        })
```

---

## 7-2. Serializers

서버 시작 시 `policies/views.py`가 import하므로 반드시 먼저 정의 필요.

```python
# apps/policies/serializers.py
from rest_framework import serializers
from .models import Policy

class PolicyCardSerializer(serializers.ModelSerializer):
    """홈 화면 카드용 — 목록에서 쓰는 최소 필드."""
    class Meta:
        model = Policy
        fields = [
            'id', 'title', 'summary', 'amount_text',
            'benefit_type', 'apply_end_date', 'managing_org',
        ]

class PolicyDetailSerializer(serializers.ModelSerializer):
    """정책 상세 페이지용 — 전체 필드."""
    class Meta:
        model = Policy
        fields = [
            'id', 'title', 'summary', 'description',
            'benefit_type', 'amount', 'amount_text',
            'apply_start_date', 'apply_end_date', 'apply_url',
            'managing_org', 'source_url', 'source',
        ]
```

---

## 8. API 엔드포인트 명세

### URL 구조

```python
# config/urls.py
urlpatterns = [
    path('admin/',         admin.site.urls),
    path('api/auth/',      include('apps.users.urls')),
    path('api/policies/',  include('apps.policies.urls')),
    path('api/places/',    include('apps.places.urls')),
    path('api/regions/',   include('apps.regions.urls')),
]
```

---

#### `GET /api/policies/preview/`
비로그인 홈용 최신·마감임박 정책 3개.

```python
class PolicyPreviewView(APIView):
    def get(self, request):
        from django.db.models import F, ExpressionWrapper, DateField
        from django.utils import timezone
        today = timezone.now().date()
        deadline_soon = Policy.objects.filter(
            is_active=True,
            apply_end_date__range=(today, today + timedelta(days=7))
        ).order_by('apply_end_date')[:3]

        rest = Policy.objects.filter(
            is_active=True
        ).exclude(
            apply_end_date__range=(today, today + timedelta(days=7))
        ).order_by('-created_at')

        policies = list(deadline_soon) + list(rest)
        policies = policies[:3]
        return Response(PolicyCardSerializer(policies, many=True).data)
```

---

#### `GET /api/policies/match/` 🔒 JWT 필요
로그인 사용자 맞춤 정책 매칭.

**응답**
```json
{
  "policies": [
    {
      "id": 1,
      "title": "귀농 창업 지원금",
      "summary": "귀농 초기 창업 비용 지원",
      "amount_text": "최대 300만원",
      "apply_end_date": "2026-06-30",
      "days_left": 53,
      "match_reason": "귀농 1년 이내, 옥천군 거주, 65세 이상"
    }
  ],
  "total": 5,
  "fallback": false
}
```

---

#### `GET /api/policies/` — 전체 목록 (필터)
#### `GET /api/policies/<id>/` — 상세
#### `GET /api/profile/` 🔒 / `PATCH /api/profile/` 🔒
UserProfile 조회 및 수정. User와 1:1 분리되어 있으므로 `request.user.profile`로 접근.
#### `GET /api/places/` — 장소 목록
#### `GET /api/places/<id>/` — 장소 상세
#### `POST /api/places/geocode/` — 주소→좌표
#### `GET /api/regions/` — 시도·시군구 드롭다운
#### `POST /api/auth/kakao/` — 카카오 로그인
#### `POST /api/auth/token/refresh/` — JWT 갱신

---

#### `POST /api/policies/parse/` 🔒 Admin only
공고문 → 정책 조건 자동 파싱.

**요청**
```json
{ "text": "신청 자격: 만 65세 이상 또는 기초생활수급자로서..." }
```

**응답**
```json
{
  "parsed": {
    "title": "귀농 창업 지원금",
    "min_age": 18,
    "region_codes": ["43720"],
    "occupation_tags": ["귀농"],
    "income_level": ["기초수급", "차상위"],
    "apply_end_date": "2026-06-30",
    "condition_tree": { "type": "OR", "children": [...] }
  },
  "confidence": 0.85,
  "flags": ["income_level: 중위소득 150% → 차상위로 해석, 확인 필요"]
}
```

---

## 9. 핵심 로직 상세

### lib/policy_parser.py — Claude API 파싱

```python
import anthropic
from pydantic import BaseModel, field_validator
from typing import Optional

client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 자동 읽음

class ParsedPolicy(BaseModel):
    title:           str
    summary:         str
    min_age:         int = 0
    max_age:         int = 130
    region_codes:    list[str] = []
    occupation_tags: list[str] = []
    household_type:  list[str] = []
    income_level:    list[str] = []
    move_status:     list[str] = []
    amount_text:     Optional[str] = None
    apply_end_date:  Optional[str] = None   # YYYY-MM-DD
    managing_org:    Optional[str] = None
    condition_tree:  Optional[dict] = None
    confidence:      float
    flags:           list[str] = []

    @field_validator('income_level')
    def validate_income(cls, v):
        allowed = {'기초수급', '차상위', '일반'}
        return [x for x in v if x in allowed]

PARSE_TOOL = {
    'name': 'extract_policy_conditions',
    'description': '정책 공고문에서 신청 자격 조건을 추출합니다',
    'input_schema': {
        'type': 'object',
        'properties': {
            'title':           {'type': 'string', 'description': '정책명'},
            'summary':         {'type': 'string', 'description': '한 줄 요약 (쉬운 말)'},
            'min_age':         {'type': 'integer', 'description': '최소 나이 (없으면 0)'},
            'max_age':         {'type': 'integer', 'description': '최대 나이 (없으면 130)'},
            'region_codes':    {'type': 'array', 'items': {'type': 'string'},
                                'description': '지역 코드. 옥천군=43720, 충청북도=43, 전국=[]'},
            'occupation_tags': {'type': 'array', 'items': {'type': 'string'},
                                'description': '가능한 값: 귀농, 귀촌, 노인, 여성농업인'},
            'income_level':    {'type': 'array', 'items': {'type': 'string'},
                                'description': '가능한 값: 기초수급, 차상위, 일반'},
            'amount_text':     {'type': 'string', 'description': '지원 금액 (예: 최대 300만원)'},
            'apply_end_date':  {'type': 'string', 'description': '신청 마감일 YYYY-MM-DD'},
            'managing_org':    {'type': 'string', 'description': '담당 기관명'},
            'condition_tree':  {'type': 'object',
                                'description': '단순 태그로 표현 불가한 복합 조건만. 예: OR(age≥65, income=기초수급)'},
            'confidence':      {'type': 'number',
                                'description': '파싱 신뢰도 0~1. 명확하면 0.9+, 모호하면 0.5 이하'},
            'flags':           {'type': 'array', 'items': {'type': 'string'},
                                'description': '불확실하게 해석한 필드. 예: ["income_level: 중위소득 150% → 차상위 해석, 확인 필요"]'},
        },
        'required': ['title', 'summary', 'confidence', 'flags'],
    },
}

def parse_policy(text: str) -> dict:
    response = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=1024,
        tools=[PARSE_TOOL],
        tool_choice={'type': 'auto'},
        messages=[{
            'role': 'user',
            'content': f'다음 정책 공고문에서 신청 자격 조건을 추출해줘.\n\n{text}',
        }],
    )

    tool_use = next(
        (b for b in response.content if b.type == 'tool_use'), None
    )
    if not tool_use:
        raise ValueError('Claude가 tool을 호출하지 않았습니다')

    # Pydantic으로 검증 — LLM이 잘못된 타입 반환 시 여기서 잡힘
    parsed = ParsedPolicy(**tool_use.input)

    return {
        'parsed':      parsed.model_dump(),
        'confidence':  parsed.confidence,
        'flags':       parsed.flags,
    }
```

**신뢰도 기준:**

| confidence | 어드민 표시 |
|---|---|
| 0.9 이상 | 결과 바로 표시, 빠른 확인 후 저장 |
| 0.7~0.9 | 결과 표시 + flags 하이라이트 |
| 0.7 미만 | "직접 입력을 권장합니다" 경고 |

---

### lib/condition_tree.py — AND/OR/NOT 평가기

```python
from typing import Any

def evaluate_tree(node: dict | None, profile: dict) -> bool:
    if node is None:
        return True   # condition_tree 없으면 통과

    match node['type']:
        case 'AND': return all(evaluate_tree(c, profile) for c in node['children'])
        case 'OR':  return any(evaluate_tree(c, profile) for c in node['children'])
        case 'NOT': return not evaluate_tree(node['child'], profile)
        case 'LEAF': return _evaluate_leaf(node, profile)
    return False

def _evaluate_leaf(node: dict, profile: dict) -> bool:
    field = node['field']
    op    = node['op']
    value = node['value']
    val   = profile.get(field)

    if val is None:
        return False

    match op:
        case 'eq':      return val == value
        case 'in':      return val in value
        case 'gte':     return val >= value
        case 'lte':     return val <= value
        case 'between': return value[0] <= val <= value[1]
    return False
```

---

### lib/region_hierarchy.py — 지역 계층 조회

```python
from django.db import connection

def get_ancestor_codes(region_code: str) -> list[str]:
    with connection.cursor() as cursor:
        cursor.execute("""
            WITH RECURSIVE ancestors AS (
                SELECT code, parent_code
                FROM regions
                WHERE code = %s
                UNION ALL
                SELECT r.code, r.parent_code
                FROM regions r
                JOIN ancestors a ON r.code = a.parent_code
                WHERE a.parent_code IS NOT NULL
            )
            SELECT ARRAY_AGG(code) FROM ancestors
        """, [region_code])
        row = cursor.fetchone()
    return row[0] if row and row[0] else [region_code]
```

---

### lib/policy_matcher.py — 매칭 파이프라인

```python
from django.utils import timezone
from .region_hierarchy import get_ancestor_codes
from .condition_tree import evaluate_tree
from apps.policies.models import Policy

def match_policies(user_profile: dict) -> dict:
    # user_profile은 UserProfile 인스턴스를 dict로 변환한 것
    # age, years_since_move는 property로 계산됨
    ancestor_codes = get_ancestor_codes(user_profile.get('region_code', ''))
    age            = user_profile.get('age', 0)       # UserProfile.age property
    occ_tags       = user_profile.get('occupation_tags', [])
    income         = user_profile.get('income_level', '')

    # 1차 SQL 필터
    qs = Policy.objects.filter(
        is_active=True,
        min_age__lte=age,
        max_age__gte=age,
    )
    # 지역: region_codes 배열과 ancestor_codes 중 겹치는 것
    qs = qs.filter(region_codes__overlap=ancestor_codes)

    # occupation_tags 없는 정책(전체 대상)도 포함
    if occ_tags:
        qs = qs.filter(occupation_tags__len=0) | qs.filter(occupation_tags__overlap=occ_tags)

    # income_level 없는 정책(전체 소득 대상)도 포함
    if income:
        qs = qs.filter(income_level__len=0) | qs.filter(income_level__contains=[income])

    # disability_required=None(무관) 정책은 항상 포함
    is_disabled = user_profile.get('is_disabled')
    if is_disabled is not None:
        qs = qs.filter(disability_required__isnull=True) | qs.filter(
            disability_required=is_disabled
        )

    # 2차: condition_tree 평가
    matched = [p for p in qs if evaluate_tree(p.condition_tree, user_profile)]

    # 정렬: 마감 임박 순
    today = timezone.now().date()
    def sort_key(p):
        if p.apply_end_date:
            return (0, (p.apply_end_date - today).days)
        return (1, 0)
    matched.sort(key=sort_key)

    fallback = len(matched) == 0
    if fallback:
        matched = list(Policy.objects.filter(is_active=True).order_by('-created_at')[:10])

    return {'policies': matched, 'fallback': fallback}
```

---

## 10. 복지로 API 연동

> **확정 (2026-05-13):** 복지로 API를 v1에 포함. 정책 텍스트를 Claude로 파싱해 DB에 저장하는 파이프라인.

### 기본 정보

```
Base URL:  https://api.odcloud.kr/api/gov24/v3/serviceList
인증 방식: Query parameter — serviceKey={BOKJIRO_API_KEY}
```

환경변수 추가 (§4):
```bash
BOKJIRO_API_KEY=119f505d...  # data.go.kr 일반 인증키
```

### 응답 → Policy 필드 매핑

| 복지로 필드 | Policy 필드 | 비고 |
|---|---|---|
| `서비스명` | `title` | |
| `서비스목적요약` | `summary` | |
| `지원내용` | `description` | |
| `지원유형` | `benefit_type` | 현금(감면) → 세금감면 등 변환 필요 |
| `소관기관명` | `managing_org` | |
| `신청기한` | `apply_end_date` | 날짜 파싱 필요 |
| `상세조회URL` | `apply_url` | |
| `서비스ID` | `external_id` | 중복 방지 키 |
| `지원대상` + `선정기준` | `condition_tree` | Claude 파싱으로 추출 |

`source = '복지로'` 로 고정 저장.

### 동기화 파이프라인

```
복지로 API GET /serviceList (페이지네이션)
    ↓
지원대상 + 선정기준 텍스트 추출
    ↓
parse_policy(text) — Claude API로 condition_tree 생성
    ↓
confidence ≥ 0.7  → Policy.objects.update_or_create(external_id=..., source='복지로')
confidence < 0.7  → is_active=False 저장 → 관리자 검토 대기
```

### lib/bokjiro_sync.py

```python
import httpx
from django.conf import settings
from apps.policies.models import Policy
from lib.policy_parser import parse_policy, PolicyParseError

BOKJIRO_URL = 'https://api.odcloud.kr/api/gov24/v3/serviceList'
CONFIDENCE_THRESHOLD = 0.7


def sync_bokjiro(per_page: int = 100) -> int:
    """전체 페이지를 순환하며 복지로 정책을 동기화한다."""
    total_saved = 0
    page = 1

    while True:
        res = httpx.get(BOKJIRO_URL, params={
            'page': page,
            'perPage': per_page,
            'serviceKey': settings.BOKJIRO_API_KEY,
        }, timeout=30)
        res.raise_for_status()
        body = res.json()
        data = body.get('data', [])
        if not data:
            break

        total_count = body.get('totalCount', 0)

    for item in data:
        title = item.get('서비스명', '')
        text = f"{item.get('지원대상', '')} {item.get('선정기준', '')}".strip()
        external_id = item.get('서비스ID', '')

        # 타 소스(귀농센터 등)에서 같은 제목으로 이미 저장된 경우 스킵
        if Policy.objects.filter(title=title).exclude(source='복지로').exists():
            continue

        try:
            result = parse_policy(text) if text else None
        except PolicyParseError:
            result = None

        is_active = result and result['confidence'] >= CONFIDENCE_THRESHOLD
        defaults = {
            'title':        title,
            'summary':      item.get('서비스목적요약', ''),
            'description':  item.get('지원내용', ''),
            'managing_org': item.get('소관기관명', ''),
            'apply_url':    item.get('상세조회URL', ''),
            'source':       '복지로',
            'is_active':    bool(is_active),
        }
        if result:
            defaults['condition_tree'] = result['parsed'].get('condition_tree')

        Policy.objects.update_or_create(
            external_id=external_id, source='복지로',
            defaults=defaults,
        )
        total_saved += 1

        if page * per_page >= total_count:
            break
        page += 1

    return total_saved
```

management command (`python manage.py sync_bokjiro`) 로 실행.

---

## 11. 브랜치 전략

> 백엔드 1인 개발 기준. 깃플로우 간소화 버전.

### 브랜치 구조

```
main ──────────────────────────────────── 배포 브랜치 (Railway 자동 배포)
  └── develop ────────────────────────── 통합 브랜치
        ├── feature/kakao-auth
        ├── feature/policy-match
        ├── feature/bokjiro-sync
        └── feature/...
```

### 규칙

| 브랜치 | 역할 | 직접 push |
|---|---|---|
| `main` | Railway 배포 트리거. 항상 동작하는 코드만 | ❌ (develop에서 merge만) |
| `develop` | 개발 통합. 기능 완성되면 여기서 확인 | ✅ (feature merge 후) |
| `feature/xxx` | 기능 단위 개발 | ✅ |

### 작업 흐름

```
feature/xxx 에서 개발
    ↓
develop 에 merge (로컬)
    ↓
동작 확인 후 main 에 merge
    ↓
Railway 자동 배포
```

### 브랜치 명명 규칙

```
feature/kakao-auth          # 카카오 로그인
feature/policy-match        # 정책 매칭 API
feature/bokjiro-sync        # 복지로 API 연동
feature/region-model        # 지역 모델/시드
fix/occupation-filter-bug   # 버그 수정
```

### 커밋 메시지 규칙

```
feat: 새 기능
fix:  버그 수정
docs: 문서 (커밋 로그 포함)
refactor: 리팩토링
test: 테스트
chore: 설정, 의존성
```

---

## 12. requirements.txt

```
django>=5.0
djangorestframework>=3.15
djangorestframework-simplejwt>=5.3
django-cors-headers>=4.3
drf-spectacular>=0.27          # API 자동 문서 (Swagger UI)
psycopg2-binary>=2.9
python-decouple>=3.8           # 환경변수 관리
httpx>=0.27                    # 카카오 API 호출
anthropic>=0.25                # Claude API
pydantic>=2.6                  # LLM 출력 검증
gunicorn>=22.0                 # Railway 배포용 WSGI 서버
```

---

## 13. API 문서 (drf-spectacular)

팀원이 프론트 개발할 때 별도 문서 없이 브라우저에서 바로 API 확인·테스트 가능.

**설정:**

```python
# config/settings.py
INSTALLED_APPS = [
    ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

```python
# config/urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    ...
    path('api/schema/', SpectacularAPIView.as_view()),
    path('api/docs/',   SpectacularSwaggerView.as_view()),  # Swagger UI
]
```

**접속:**
- 로컬: `http://localhost:8000/api/docs/`
- 배포: `https://your-api.railway.app/api/docs/`

코드가 바뀌면 문서도 자동으로 갱신됨. 팀원한테 URL만 알려주면 돼.

---

## 14. 배포 구조

```
GitHub
  ├── backend 레포 → Railway (Django 자동 배포)
  └── frontend 레포 → Vercel (Next.js 자동 배포)

push하면 자동으로 빌드 + 배포됨
환경변수는 각 플랫폼 대시보드에서 관리
```

---

## 15. Railway 배포 전략 — 빈 껍데기 먼저

프론트 팀원이 기다리지 않도록 **기능이 없어도 Day 1에 배포부터 먼저**.  
API가 만들어지는 순서대로 팀원이 바로바로 연결.

```
Day 1: Django 프로젝트 생성 → Railway 배포
       → https://your-api.railway.app/api/docs/ 팀원 공유
       → 아직 API 없어도 서버는 떠 있음

Day 3: /api/policies/preview/ 완성
       → 팀원이 /api/docs/에서 바로 확인 + 프론트 연결

Day 5: /api/policies/match/ 완성
       → 팀원이 홈 화면에 연결

...이후 만들어지는 순서대로 점진적 통합
```

---

### Railway 배포 설정

**`Procfile` (레포 루트에 생성):**
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

**`railway.json` (레포 루트에 생성):**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

---

### 배포 순서 체크리스트

```
[ ] 1. GitHub backend 레포 생성
[ ] 2. Railway 가입 + 프로젝트 생성 (GitHub 연동)
[ ] 3. Railway 환경변수 등록 (§4 목록 전체)
[ ] 4. Supabase DB 연결 확인 (DATABASE_URL)
[ ] 5. python manage.py migrate
[ ] 6. python manage.py createsuperuser (Admin 계정)
[ ] 7. https://your-api.railway.app/api/docs/ 접속 확인
[ ] 8. 팀원한테 URL 공유
[ ] 9. CORS_ALLOWED_ORIGINS에 Vercel 도메인 추가 (프론트 배포 후)
[ ] 10. 카카오 개발자 콘솔 Redirect URI: {Railway도메인}/api/auth/kakao/
```

---

### 비용 관리

```
Railway 무료 티어: 매달 $5 크레딧
Django 서버 1개:  약 15일치

→ 개발할 때만 켜두거나
→ GitHub Student Pack으로 추가 크레딧 신청 (학교 이메일 필요)
```

---

## 16. v1.5 이후 확장 경로

```
v1.5 — 알림 기능 (카카오 알림톡)
  Django management command + Railway Cron
  → python manage.py send_deadline_alerts
  → Railway에서 매일 오전 9시 KST 실행 설정
```

---

## 17. v2 — 정책 자동 수집 파이프라인

### 수집 대상

| 출처 | 방식 | 주기 |
|---|---|---|
| 복지로 (data.go.kr) | 공공 API | 주 1회 (v1 포함) |
| 귀농귀촌종합센터 (greendaero.go.kr) | 크롤링 (정적/동적) | 주 1회 |
| 옥천군청 홈페이지 | 크롤링 (정적/동적) | 주 1회 |
| 충청북도청 홈페이지 | 크롤링 (정적/동적) | 월 1회 |

---

### 크롤링 방식 선택 기준

```
사이트 접속 → HTML 소스 확인 (크롬 개발자도구)

정책 목록이 소스에 바로 보임  → BeautifulSoup (정적)
목록이 소스에 없고 JS로 로드  → Playwright (동적)
```

**BeautifulSoup — 정적 HTML:**
```python
# lib/crawlers/greendaero.py
# 귀농귀촌종합센터: https://www.greendaero.go.kr/svc/rfph/cpif/front/home.do
import httpx
from bs4 import BeautifulSoup
from apps.policies.models import Policy

GREENDAERO_URL = 'https://www.greendaero.go.kr/svc/rfph/cpif/front/home.do'

def crawl_greendaero():
    res = httpx.get(GREENDAERO_URL)
    soup = BeautifulSoup(res.text, 'html.parser')

    for row in soup.select('table.list tr'):
        cells = row.find_all('td')
        if len(cells) < 3:
            continue

        title    = cells[0].get_text(strip=True)
        end_date = cells[2].get_text(strip=True)  # 마감일
        link     = cells[0].find('a')['href']

        # 타 소스(복지로 등)에서 같은 제목으로 이미 저장된 경우 스킵
        if Policy.objects.filter(title=title).exclude(source='귀농센터').exists():
            continue

        Policy.objects.update_or_create(
            external_id=link,
            source='귀농센터',
            defaults={
                'title':         title,
                'apply_end_date': parse_date(end_date),
                'source_url':    f'{GREENDAERO_URL}{link}',
                'is_active':     True,
            }
        )
```

**Playwright — JS 렌더링 동적 페이지:**
```python
# lib/crawlers/okcheon.py
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def crawl_okcheon_dynamic():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.okcheon.go.kr/policy')

        # JS 로딩 대기
        page.wait_for_selector('table.policy-list')

        # 더보기 버튼이 있으면 클릭
        while page.locator('#btn-more').is_visible():
            page.click('#btn-more')
            page.wait_for_timeout(1000)

        # 다 로드된 후 HTML 파싱
        soup = BeautifulSoup(page.content(), 'html.parser')
        browser.close()

    for row in soup.select('table.policy-list tr'):
        # BeautifulSoup으로 동일하게 파싱
        ...
```

---

### 수집 후 처리 파이프라인

크롤링으로 가져온 데이터는 원문 텍스트 상태야. 이걸 DB에 저장 가능한 구조로 바꿔야 해.

```
크롤러 실행 (BeautifulSoup / Playwright)
    ↓
원문 텍스트 수집 (제목, 본문, 마감일 등)
    ↓
Claude API로 자동 파싱          ← v1에서 만든 parse_policy() 재사용
  (자격조건 추출 → condition_tree 생성)
    ↓
신뢰도 체크
  confidence ≥ 0.7  → DB 자동 저장 (is_active=True)
  confidence < 0.7  → is_active=False 로 저장 → 관리자 검토 대기
    ↓
Django Admin에서 검토 대기 목록 확인 후 활성화
```

**management command로 실행:**
```python
# apps/policies/management/commands/sync_policies.py
from django.core.management.base import BaseCommand
from lib.crawlers.greendaero import crawl_greendaero
from lib.crawlers.okcheon import crawl_okcheon_dynamic

class Command(BaseCommand):
    help = '정책 데이터 자동 수집 및 파싱'

    def handle(self, *args, **options):
        self.stdout.write('귀농귀촌종합센터 크롤링...')
        crawl_greendaero()

        self.stdout.write('옥천군청 크롤링...')
        crawl_okcheon_dynamic()

        self.stdout.write('완료')
```

Railway Cron에서 주 1회 실행:
```
python manage.py sync_policies
```

---

### v2 추가 패키지

```
# requirements.txt 추가
beautifulsoup4>=4.12
playwright>=1.44          # pip install playwright 후 playwright install chromium
celery>=5.3               # 비동기 태스크 (트래픽 많아지면)
redis>=5.0                # Celery 브로커
```

---

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 1 | CLEAR | 3 proposals, 1 accepted, 2 deferred |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 6 | CLEAR | 4 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

**2026-05-13 1차 Eng Review 결정:**
- `is_disabled` (UserProfile) + `disability_required` (Policy) 추가
- 복지로 API v1 연동 확정 (§10), `occupation_tags` 필터 버그 수정
- UserProfile `post_save` signal 신설, 유닛 테스트 25개 작성

**2026-05-13 2차 Eng Review 결정:**
- `serializers.py` (PolicyCardSerializer, PolicyDetailSerializer) §7-2에 정의 추가
- `BOKJIRO_API_KEY` §4 env vars에 추가
- Policy SOURCES에서 '보조금24' 제거
- `sync_bokjiro` 전체 페이지 루프 추가 (pagination 완성)

- **UNRESOLVED:** 0
- **VERDICT:** CEO + ENG CLEARED — Django 초기 세팅 후 구현 시작 가능.
