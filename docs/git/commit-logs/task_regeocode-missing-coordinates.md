# 좌표 없는 사용처 일괄 지오코딩

**날짜**: 2026-08-26
**커밋 로그**: [1085ab4](https://github.com/mulppulihwa/backend/commit/1085ab4)

## 작업 배경

`seed_trust_badges`로 맥우직매장(id=173)을 신규 등록하면서 `geocode_address()`
가 `None`을 반환해 좌표가 비어 있었음. 원인을 확인해보니 로컬 `.env`에는
`DATABASE_URL`(프로덕션 Supabase)만 있고 `KAKAO_LOCAL_API_KEY`는 없었음 — 즉
DB는 프로덕션에 붙어 있었지만 카카오 지오코딩 키만 로컬 환경변수에서 빠져 있어
조용히 실패한 것. 사용자가 Railway 환경변수에는 이 키가 정상적으로 설정돼
있다고 확인해줌.

## AS-IS

- 맥우직매장(id=173) `lat`/`lng` = `null`
- 확인 과정에서 기존에도 좌표가 비어 있던 곳 9곳(군북면/안남면/청성면/청산면/
  이원면/군서면/동이면 행정복지센터, 옥천군의회, 옥천군 농업기술센터)을 추가로
  발견 — 이번 작업과 무관하게 이전부터 비어 있던 데이터

## TO-BE

- `apps/places/management/commands/regeocode_places.py` 신규 — `lat__isnull=True`
  이고 주소가 있는 사용처를 찾아 `geocode_address()`로 재시도, 성공하면 저장
- 로컬 `.env`를 수정하는 대신 `railway run python manage.py regeocode_places`로
  Railway의 실제 프로덕션 환경변수(`KAKAO_LOCAL_API_KEY` 포함)를 그대로 써서
  실행 — 키 값을 로컬에 복사하거나 채팅에 노출할 필요 없음
- 결과: 10곳 전부 좌표 변환 성공, 실패 0건

## 주요 변경

- `apps/places/management/commands/regeocode_places.py`: 신규
