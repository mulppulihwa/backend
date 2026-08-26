# 옥천군 상담센터/옥천신문 추천 마크 수기 반영

**날짜**: 2026-08-26
**커밋 로그**: [4e70c96](https://github.com/mulppulihwa/backend/commit/4e70c96)

## 작업 배경

사용자가 특정 사용처 6곳에 옥천군 상담센터/옥천신문 추천 마크를 붙여 달라고
요청. `okcheon_news_recommended`/`counseling_center_recommended` 필드는 이미
2026-08-20 신뢰도 마크 스펙(`docs/superpowers/specs/2026-08-20-trust-badges-design.md`
"판단 사항 3")에서 "관리자가 백엔드에서 수기로 반영"하는 것으로 설계돼 있었음 —
새 기능이 아니라 기존 설계대로 데이터만 채우는 작업.

6곳 중 4곳(아세아농기계 옥천대리점, 옥천군주민정보화교육장, 배바우손두부,
옥천체육센터)은 이미 DB에 있었고, 2곳(부소담악, 맥우직매장)은 없어서 신규
등록이 필요했음. 사용자에게 주소를 확인한 결과 맥우직매장 주소만 받음
(부소담악은 주소 미확정으로 보류).

옥천체육센터(id=98)는 앞선 카테고리 재편 작업에서 `동호회`→`명소`로
재분류되어 있었는데, 사용자가 이번 요청에서 다시 "동호회"로 지칭해 재확인—
카테고리는 그대로 `명소` 유지하기로 확정.

## AS-IS

- 6곳 중 4곳 존재, `okcheon_news_recommended`/`counseling_center_recommended`
  모두 `False`
- 맥우직매장 미등록

## TO-BE

- `apps/places/management/commands/seed_trust_badges.py` 신규 — `--dry-run`
  지원, 이름으로 사용처를 찾아 마크 필드를 켜고, 없는 곳은 `NEW_PLACES`에
  등록해서 자동 생성. 이미 마크가 켜져 있거나 이미 존재하는 곳은 스킵해
  재실행해도 안전(idempotent)
- 프로덕션 DB에 실행 완료:
  - `counseling_center_recommended=True`: 아세아농기계 옥천대리점(id=169),
    옥천군주민정보화교육장(id=171), 맥우직매장(id=173, 신규)
  - `okcheon_news_recommended=True`: 배바우손두부(id=95), 옥천체육센터(id=98)
- 맥우직매장(id=173)은 "충청북도 옥천군 군서면 성왕로 975" 주소로 신규 등록.
  단, 로컬 `.env`에 `KAKAO_LOCAL_API_KEY`가 설정돼 있지 않아 `geocode_address()`가
  바로 `None`을 반환 — `lat`/`lng`가 `null`로 저장됨. 프로덕션 Railway 환경에
  이 키가 설정돼 있다면 문제 없지만, 없다면 지도에 핀이 안 뜸 — 별도 확인 필요

## API/프론트 연동

- 새 엔드포인트 없음. 기존 `GET /api/places/`, `GET /api/places/<id>/`가
  이미 두 뱃지 필드를 응답에 포함하고 있어(2b40f96에서 노출) 프론트는 추가
  API 호출 없이 응답의 `okcheon_news_recommended`/`counseling_center_recommended`
  boolean만 보고 뱃지 아이콘을 조건부 렌더링하면 됨

## 남은 작업 (별도 확인 필요)

- ~~부소담악(명소): 정확한 도로명주소를 받아야 등록 가능~~ → 주소 확인 후
  [9a268fc](https://github.com/mulppulihwa/backend/commit/9a268fc)에서 등록 완료
  (`task_regeocode-missing-coordinates.md`, `task_busodam-ak-registration.md` 참고)
- ~~맥우직매장(id=173) 좌표 미설정~~ → `regeocode_places` 커맨드로 해결
  (`task_regeocode-missing-coordinates.md` 참고)
