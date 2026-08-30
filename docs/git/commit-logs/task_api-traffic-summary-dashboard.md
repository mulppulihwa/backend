# API 트래픽 요약 대시보드 (/admin/)

**날짜**: 2026-08-30
**커밋 로그**: [3dd0c43](https://github.com/mulppulihwa/backend/commit/3dd0c43)

## 작업 배경

[task_api-traffic-logging-middleware.md](task_api-traffic-logging-middleware.md)로
`RequestLog`를 쌓기 시작했지만, 사용자가 "API 요청 수 기반으로 유저가 얼마나,
어디에 반응하는지 통계적으로 확인하고 싶다"고 요청 — 목록 화면만으로는 집계가
안 돼서 별도 요약 페이지가 필요했음.

두 방향(1. 커스텀 Admin 요약 페이지, 2. Google Analytics 등 프론트 스크립트)을
제시했고, 사용자가 프론트를 안 건드리는 1번(API 호출 수 기준 집계)을 선택.

## AS-IS

- `/admin/analytics/requestlog/`에서 낱개 요청 행만 필터링해서 볼 수 있었고,
  집계(총 몇 건, 어떤 경로가 인기있는지, 유저 몇 명이 쓰는지)는 직접 세는
  방법밖에 없었음

## TO-BE

- `RequestLogAdmin.get_urls()`에 `summary/` 커스텀 뷰 추가
  (`/admin/analytics/requestlog/summary/`), 목록 화면 우측 상단에
  "📊 요약 보기" 링크로 진입(`change_list.html` 오버라이드,
  `object-tools-items` 블록에 링크 추가)
- 요약 페이지가 보여주는 것:
  - 전체 누적 / 오늘 / 최근 7일 요청 수
  - 누적 / 최근 7일 로그인 유저 수(`user`가 채워진 로그의 distinct 개수)
  - **최근 7일 Top 10 엔드포인트**: 경로의 숫자 id 세그먼트를 `{id}`로
    정규화해 집계 — 예: `/api/places/169/endorse/`, `/api/places/171/endorse/`
    둘 다 `/api/places/{id}/endorse/`로 묶여서 "추천하기 버튼이 얼마나
    눌리는지" 같은 액션 단위 집계가 됨. Postgres `regexp_replace`를
    `django.db.models.Func()`로 호출(정적 패턴만 사용, 사용자 입력이 SQL에
    안 들어가 인젝션 여지 없음)
  - **최근 7일 Top 10 구체적인 경로**: 정규화 안 한 원본 경로 그대로 집계 —
    "어떤 특정 사용처/정책이 제일 많이 조회되는지" 확인용
  - 최근 14일 일별 요청 수 추이
- `tests/test_analytics_summary.py` 신규 2건: 비로그인 접근 시 302/403,
  집계 로직(총 개수/유니크 유저/id 정규화 그룹핑) 검증

## 주요 변경

- `apps/analytics/admin.py`: `get_urls()`, `summary_view()` 추가
- `apps/analytics/templates/admin/analytics/requestlog/change_list.html`: 신규
  (요약 보기 링크)
- `apps/analytics/templates/admin/analytics/requestlog/summary.html`: 신규
  (집계 결과 렌더링)
- `tests/test_analytics_summary.py`: 신규 2건

## 범위에서 제외한 것

- 세션/퍼널 분석(한 유저가 어떤 순서로 화면을 이동했는지) — "API 호출 수"
  기준으로는 못 잡음, 사용자에게 이 한계를 미리 설명하고 동의받음
- 차트/그래프 시각화 — 지금은 표 형태. 필요해지면 후속 작업으로
