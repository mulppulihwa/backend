# 보조금24 제거, 귀농귀촌종합센터 크롤링으로 교체

**날짜**: 2026-05-13
**커밋 로그**: [50a8418](https://github.com/mulppulihwa/backend/commit/50a8418)

## 작업 배경

v2 자동 수집 파이프라인에서 보조금24 API를 제거하고,
귀농귀촌종합센터(greendaero.go.kr)를 크롤링 대상으로 확정.

## AS-IS

- v2 수집 대상에 보조금24(data.go.kr) 공공 API 포함
- 크롤러 파일명 `crawlers/returnfarm.py` (returnfarm.com 기준)

## TO-BE

- 보조금24 제거 (귀농귀촌 특화 플랫폼 범위 밖)
- 크롤러 대상: `https://www.greendaero.go.kr/svc/rfph/cpif/front/home.do`
- 파일명 `crawlers/greendaero.py`로 변경

## 주요 변경

- backend-plan §17 수집 대상 테이블 업데이트
- management command import 경로 수정
- platform-plan source 필드, 기술 스택, MVP 제외 항목 업데이트
