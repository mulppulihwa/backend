# 부소담악(명소) 신규 등록 + 상담센터 추천 마크

**날짜**: 2026-08-26
**커밋 로그**: [9a268fc](https://github.com/mulppulihwa/backend/commit/9a268fc)

## 작업 배경

[task_trust-badge-manual-curation.md](task_trust-badge-manual-curation.md)에서
요청받은 6곳 중 유일하게 주소 미확정으로 보류했던 부소담악(명소)을, 사용자가
도로명주소("충청북도 옥천군 군북면 추소리 234-2")를 확인해줘서 마저 등록.

## TO-BE

- `seed_trust_badges.py`의 `NEW_PLACES`/`BADGES`에 부소담악 추가 (기존 커맨드가
  이미 존재 여부/마크 여부를 체크해 스킵하는 구조라, 재실행해도 이미 반영된
  5곳은 건드리지 않고 부소담악만 새로 처리됨 — dry-run으로 먼저 확인)
- `railway run python manage.py seed_trust_badges`로 프로덕션 환경변수
  (`KAKAO_LOCAL_API_KEY` 포함) 그대로 실행 → 부소담악(id=174) 등록,
  좌표(36.3486887413374, 127.567149472674) 정상 변환,
  `counseling_center_recommended=True` 반영

## 주요 변경

- `apps/places/management/commands/seed_trust_badges.py`: `NEW_PLACES`/`BADGES`
  목록에 부소담악 1건 추가

이걸로 요청받은 신뢰도 마크 6곳(농기계/생활/명소/음식점 2곳/동호회) 전부 반영
완료.
