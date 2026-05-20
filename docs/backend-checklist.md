# 백엔드 구현 체크리스트

> 참고: `docs/plan/backend-plan.md`  
> 현재 상태: 핵심 로직 구현 완료 / 앱 골격 + 미구현 모듈 남음

---

## 0. 프로젝트 세팅

- [ ] `manage.py` 생성
- [ ] `requirements.txt` 작성 (backend-plan.md §12 참고)
- [ ] `config/settings.py` — DB, CORS, JWT, 앱 등록, `AUTH_USER_MODEL = 'users.User'`
- [ ] `config/urls.py` — 루트 URL 라우팅 (auth / policies / places / regions / admin / api/docs)
- [ ] `config/wsgi.py`
- [ ] `.env` 파일 구조 확인 (backend-plan.md §4)
- [ ] `Procfile` + `railway.json` 생성 (backend-plan.md §15)

---

## 1. users 앱

- [x] `apps/users/models.py` — User + UserProfile 모델
- [x] `apps/users/signals.py` — UserProfile post_save 자동 생성
- [x] `apps/users/views.py` — KakaoAuthView (카카오 OAuth + JWT 발급)
- [ ] `apps/users/serializers.py` — UserProfileSerializer (PATCH용)
- [ ] `apps/users/urls.py` — `/api/auth/kakao/`, `/api/auth/token/refresh/`, `/api/profile/`
- [ ] `apps/users/apps.py` — signals 연결 (`ready()`)
- [ ] **마이그레이션** — `python manage.py makemigrations users`

---

## 2. policies 앱

- [x] `apps/policies/models.py` — Policy 모델 + GIN 인덱스
- [x] `apps/policies/views.py` — Preview / Match / Detail / Parse 뷰
- [ ] `apps/policies/serializers.py` — PolicyCardSerializer + PolicyDetailSerializer ← **서버 시작 시 ImportError 발생하므로 최우선**
- [ ] `apps/policies/admin.py` — PolicyAdmin + AI 파싱 커스텀 액션
- [ ] `apps/policies/urls.py` — `/api/policies/` 라우팅
- [ ] **마이그레이션** — `python manage.py makemigrations policies`

---

## 3. places 앱 (미생성)

- [ ] `apps/places/models.py` — LocalPlace 모델
- [ ] `apps/places/serializers.py`
- [ ] `apps/places/views.py` — 목록 / 상세
- [ ] `apps/places/admin.py` — LocalPlaceAdmin
- [ ] `apps/places/urls.py`
- [ ] **마이그레이션** — `python manage.py makemigrations places`

---

## 4. regions 앱 (미생성)

- [ ] `apps/regions/models.py` — Region 모델 (code PK, parent_code)
- [ ] `apps/regions/views.py` — 드롭다운용 시도·시군구 목록
- [ ] `apps/regions/urls.py`
- [ ] **마이그레이션** — `python manage.py makemigrations regions`

---

## 5. 핵심 로직 (lib/)

- [x] `lib/condition_tree.py` — AND/OR/NOT/LEAF 평가기 (logging + 에러 핸들링 포함)
- [x] `lib/region_hierarchy.py` — recursive CTE ancestor_codes 조회
- [x] `lib/policy_matcher.py` — SQL 1차 필터 + condition_tree 2차 평가
- [x] `lib/policy_parser.py` — Claude API 파싱 + Pydantic 검증
- [ ] `lib/bokjiro_sync.py` — 복지로 API 동기화 (backend-plan.md §10 코드 참고)
  - 페이지네이션 루프 (while True → for item in data → page += 1)
  - Claude 호출 후 0.5s delay
  - confidence >= 0.7 → is_active=True, < 0.7 → False
  - max_items 파라미터로 비용 제한

---

## 6. 시드 데이터

- [ ] `data/seed/regions.json` — 시도 17개 + 옥천군(43720) + 충청북도(43) 포함
- [ ] `data/seed/policies.json` — 귀농귀촌 정책 20~30개
- [ ] `data/seed/local_places.json` — 옥천군 장소 30~50곳
- [ ] management command: `python manage.py seed_data`
- [ ] management command: `python manage.py sync_bokjiro`

---

## 7. 테스트

- [x] `tests/test_condition_tree.py` (160줄)
- [x] `tests/test_policy_matcher.py` (91줄)
- [x] `tests/test_policy_parser.py` (91줄)
- [ ] `tests/test_policy_views.py` — API 엔드포인트 테스트 (backend-plan.md §9 테스트 명세)
- [ ] `tests/test_auth_views.py` — KakaoAuthView 에러 케이스
- [ ] `tests/test_bokjiro_sync.py` — 페이지루프, confidence 필터, 중복 스킵

---

## 8. 배포

- [ ] Railway 프로젝트 생성 + GitHub 연동
- [ ] Railway 환경변수 등록 (backend-plan.md §4 목록)
- [ ] Supabase DB 연결 확인 (`DATABASE_URL`)
- [ ] `python manage.py migrate`
- [ ] `python manage.py createsuperuser`
- [ ] `https://your-api.railway.app/api/docs/` 접속 확인
- [ ] CORS_ALLOWED_ORIGINS에 Vercel 도메인 추가
- [ ] 카카오 개발자 콘솔 Redirect URI: `{Railway도메인}/api/auth/kakao/`

---

## 구현 순서 권장

```
1순위: policies/serializers.py  ← 없으면 서버 자체가 안 켜짐
2순위: 앱 urls.py + config/urls.py (라우팅)
3순위: config/settings.py + manage.py (프로젝트 실행)
4순위: places + regions 앱 골격
5순위: bokjiro_sync.py
6순위: 시드 데이터 + management commands
7순위: 테스트 추가 3개
8순위: Railway 배포
```
