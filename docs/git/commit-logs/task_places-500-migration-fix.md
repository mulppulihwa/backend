# /api/places/ 500 에러 — 운영 DB 마이그레이션 미적용 + 배포 설정 수정

**날짜**: 2026-06-15
**커밋 로그**: [1ad0af9](https://github.com/mulppulihwa/backend/commit/1ad0af9)

## 작업 배경

§7(사용처 CRUD) 배포 직후 운영 환경에서 `GET/POST /api/places/`가 모두 500을
반환. Railway 로그 확인 결과 두 요청 모두 `httpStatus: 500`.

## 원인

1. `LocalPlace`에 추가한 `business_hours`/`created_by` 컬럼에 대한 마이그레이션
   `0003_localplace_business_hours_localplace_created_by`가 운영 DB에 미적용
   (`showmigrations` 확인 결과 `[ ] 0003...`). ORM이 존재하지 않는 컬럼을
   SELECT/INSERT하면서 500 발생.
2. 근본 원인: `Procfile`은 `python manage.py migrate && gunicorn ...`이지만
   `railway.json`의 `deploy.startCommand`가 `migrate` 없이 gunicorn만 실행하도록
   덮어쓰고 있어, Railway가 `railway.json`을 우선 적용하는 한 **배포 시 자동
   마이그레이션이 동작하지 않는 상태**였음.

## AS-IS

```json
// railway.json
"startCommand": "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"
```

## TO-BE

```json
// railway.json
"startCommand": "python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"
```

## 주요 변경

- `railway run python manage.py migrate places`로 운영 DB에 0003 마이그레이션
  즉시 적용 (additive `AddField`만 있어 데이터 손실 없음).
- `railway.json`의 `startCommand`에 `migrate &&` 추가 — Procfile과 동일하게
  맞춰 앞으로 배포 시 마이그레이션이 자동 적용되도록 수정.
- 적용 후 `GET /api/places/` 200 확인.
