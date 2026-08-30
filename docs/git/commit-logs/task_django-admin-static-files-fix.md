# Django Admin CSS/JS 미적용 문제 — whitenoise로 정적 파일 서빙 추가

**날짜**: 2026-08-30
**커밋 로그**: [c29be60](https://github.com/mulppulihwa/backend/commit/c29be60)

## 작업 배경

`/admin/analytics/requestlog/` 화면을 스크린샷으로 확인해보니 표/버튼 스타일이
하나도 안 먹은 순수 HTML로 떠 있었음. 사용자가 "예쁘게 만들어" 요청.

## AS-IS

- `Procfile`/`railway.json` 배포 커맨드 어디에도 `collectstatic`이 없었음
- `MIDDLEWARE`에 정적 파일을 서빙하는 미들웨어가 없어, `DEBUG=False`인
  프로덕션에서는 gunicorn이 `/static/...` 요청을 처리할 방법이 아예 없었음
  (Django 개발 서버는 `DEBUG=True`일 때만 자동으로 정적 파일을 서빙함)
- 결과: `/admin/`의 모든 CSS/JS가 404, 순수 비-스타일 HTML로만 렌더링

## TO-BE

- `requirements.txt`에 `whitenoise` 추가
- `MIDDLEWARE`에 `whitenoise.middleware.WhiteNoiseMiddleware`를
  `SecurityMiddleware` 바로 뒤(whitenoise 공식 권장 위치)에 추가
- `STORAGES['staticfiles']`를
  `whitenoise.storage.CompressedStaticFilesStorage`로 변경(기존
  `django.contrib.staticfiles.storage.StaticFilesStorage`에서 교체) — gzip
  사전 압축 지원
  - 처음엔 해시 기반 캐시버스팅이 되는 `CompressedManifestStaticFilesStorage`를
    썼다가, `collectstatic`을 실행하지 않은 환경(로컬 테스트, 로컬 개발)에서
    `{% static %}` 태그가 `ValueError: Missing staticfiles manifest entry`를
    던져 `test_admin_and_docs_paths_are_excluded` 테스트가 깨지는 걸 발견 —
    이 프로젝트 규모에서는 해시 캐시버스팅의 이점보다 "collectstatic 안 돌려도
    안 깨짐"이 더 중요하다고 판단해 non-manifest 버전으로 변경
- `Procfile`/`railway.json` 배포 커맨드 맨 앞에
  `python manage.py collectstatic --noinput &&` 추가
- `.gitignore`에 `staticfiles/` 추가 (로컬에서 `collectstatic` 테스트하며 생긴
  디렉터리가 실수로 커밋되는 것 방지)

## 주요 변경

- `requirements.txt`: `whitenoise>=6.7` 추가
- `config/settings.py`: `MIDDLEWARE`, `STORAGES['staticfiles']` 변경
- `Procfile`, `railway.json`: 배포 커맨드에 `collectstatic --noinput` 추가
- `.gitignore`: `staticfiles/` 추가

## 검증

- 로컬 `python manage.py collectstatic --noinput` 정상 동작(157개 파일,
  148개 후처리) 확인
- 전체 테스트 스위트 재실행, `test_admin_and_docs_paths_are_excluded` 포함
  전부 통과 확인
- 배포 후 실제로 `/admin/analytics/requestlog/`가 정상 스타일로 렌더링되는지는
  사용자가 브라우저로 재확인 예정
