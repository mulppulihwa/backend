# 크로스 소스 정책 중복 처리 추가

**날짜**: 2026-05-13
**커밋 로그**: [389d34d](https://github.com/mulppulihwa/backend/commit/389d34d)

## 작업 배경

복지로 API와 귀농귀촌종합센터 크롤링이 같은 정책을 각각 저장하면
source가 달라 중복 레코드가 생기는 문제 발견.

## AS-IS

`update_or_create(external_id, source)` 기준이라 같은 정책도 소스가 다르면 2개로 저장됨.

## TO-BE

저장 전 타 소스에 같은 제목이 있으면 스킵. 먼저 저장된 소스의 레코드를 유지.

## 주요 변경

- `bokjiro_sync`: `filter(title=title).exclude(source='복지로').exists()` 체크 추가
- `crawl_greendaero`: `filter(title=title).exclude(source='귀농센터').exists()` 체크 추가
- greendaero source_url 하드코딩 제거 (`GREENDAERO_URL` 상수 활용)
