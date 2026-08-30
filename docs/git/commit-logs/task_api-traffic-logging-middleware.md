# API 호출 트래픽 로깅 미들웨어 추가 (apps.analytics)

**날짜**: 2026-08-30
**커밋 로그**: [3d001bb](https://github.com/mulppulihwa/backend/commit/3d001bb)

## 작업 배경

사용자가 "접속자수 지표를 확인하고 싶은데, 나는 백엔드만 건드리고 프론트는
안 건드리면서 다른 팀원들도 지표를 볼 수 있게 하고 싶다"고 요청. 확인해보니
백엔드에 방문자/트래픽을 기록하는 코드가 전혀 없었음(미들웨어, 관련 테이블,
GA 등 외부 툴 전부 없음).

두 가지 선택지를 제시:
1. 프론트에 스크립트 한 줄(GA/Plausible) — 정확한 방문자 지표(체류시간·이탈률)
   가능하지만 프론트 코드를 조금이라도 건드려야 함
2. 백엔드 미들웨어로 API 호출 수 기록 + Django Admin으로 열람 — 프론트 코드
   전혀 안 건드리고, 팀원은 계정만 있으면 `/admin/`에서 확인 가능하지만
   "API 호출 수" 기준이라 진짜 방문자 지표(세션 등)는 아님

사용자가 2번(API 호출 수 기준)을 선택.

## AS-IS

- 방문/트래픽을 기록하는 코드 없음 — 지금 당장 확인 가능한 지표 자체가 없었음

## TO-BE

- 신규 앱 `apps/analytics/` — `RequestLog` 모델(`path`, `method`, `status_code`,
  `user`(nullable FK), `created_at`)
- `RequestLogMiddleware`(`MIDDLEWARE` 맨 끝, `AuthenticationMiddleware` 이후에
  배치해 `request.user`가 채워진 뒤 기록됨): 모든 요청의 응답을 받은 뒤
  `RequestLog`에 저장. `/admin/`, `/static/`, `/api/docs/`, `/api/schema/`는
  자기 자신을 기록하는 노이즈를 피하려 제외
- DB 기록 실패는 `logger.warning`만 남기고 무시 — 기존 캐시 폴백 패턴
  (`apps/policies/views.py`의 `_cache_get`/`_cache_set`)과 동일하게, 로깅
  실패가 실제 API 응답을 절대 깨지 않게 함
- Django Admin에 등록(`RequestLogAdmin`) — `date_hierarchy='created_at'`로
  연/월/일 드릴다운, `method`/`status_code` 필터, `path` 검색 지원.
  add/change 권한은 막아 로그 데이터를 실수로 편집 못 하게 함
- `tests/test_analytics_middleware.py` 신규 4건: 일반 요청 로깅, 인증된
  유저 기록, 제외 경로(admin/docs/schema) 미기록, 404 응답도 상태코드
  그대로 기록되는지

## 주요 변경

- `apps/analytics/`: 신규 앱 (`models.py`, `middleware.py`, `admin.py`,
  `apps.py`, `migrations/0001_initial.py`)
- `config/settings.py`: `INSTALLED_APPS`에 `apps.analytics` 추가,
  `MIDDLEWARE` 맨 끝에 `RequestLogMiddleware` 추가
- `tests/test_analytics_middleware.py`: 신규 4건
- 프로덕션 DB에 `analytics.0001_initial` 마이그레이션 적용 완료
  (`railway run python manage.py migrate analytics`)

## 팀원이 확인하는 방법

- `https://web-production-24d4f.up.railway.app/admin/analytics/requestlog/`
  접속 (is_staff 계정 필요 — 슈퍼유저가 아니어도 `is_staff=True` + 해당 모델
  view 권한만 있으면 됨)
- 상단 날짜 드릴다운으로 일자별 요청 수, 필터로 메서드/상태코드별 확인 가능

## 범위에서 제외한 것

- 브라우저 단 방문자 지표(세션, 체류시간, 이탈률, 유니크 방문자) — 프론트에
  스크립트를 넣지 않는 한 API 호출 수로는 알 수 없음. 필요해지면 별도로
  GA/Plausible 도입 논의
- 집계 차트/대시보드 화면 — Django Admin 기본 목록/필터로 대체. 더 보기 좋은
  요약 화면이 필요하면 커스텀 admin 뷰 추가는 이후 별도 작업
