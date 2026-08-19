# LocalPlace 신뢰도 뱃지 필드 + PlaceEndorsement 모델 추가

**날짜**: 2026-08-20
**커밋 로그**: [a86c954](https://github.com/mulppulihwa/backend/commit/a86c954)

## 작업 배경

신뢰도 기반 안심 검증 마크(뱃지 + 추천) 기능 구현 플랜의 Task 1. 사용처
목록에서 "옥천군소식 추천"/"상담센터 추천" 뱃지와 사용자 "추천해요" 수를
보여주기 위한 데이터 모델부터 마련한다.

## AS-IS

- `LocalPlace`에 관리자 큐레이션 뱃지 필드가 없어 신뢰도 표시를 할 방법이
  없었음.
- 사용자가 사용처를 추천했다는 기록을 남길 모델이 없음.

## TO-BE

- `LocalPlace`에 `okcheon_news_recommended`, `counseling_center_recommended`
  (둘 다 `BooleanField(default=False)`) 추가 — 관리자가 Django Admin에서
  직접 체크.
- `PlaceEndorsement`(신규 모델) — `place`(FK → `LocalPlace`,
  `related_name='endorsements'`, `CASCADE`), `user`(FK → `User`,
  `related_name='place_endorsements'`, `CASCADE`), `created_at`.
  `unique_together = [['place', 'user']]`로 같은 사용자의 중복 추천을
  DB 레벨에서 차단(추후 Task 3의 `get_or_create` 멱등 처리와 함께 동작).

## 주요 변경

- `apps/places/models.py`: `LocalPlace`에 뱃지 필드 2개 추가, `PlaceEndorsement`
  모델 신규 추가(`db_table='place_endorsements'`).
- `apps/places/migrations/0004_localplace_counseling_center_recommended_and_more.py`
  (신규): 뱃지 필드 2개 `AddField` + `category` 필드 재정렬로 인한
  `AlterField`(필드 순서 변경에 따른 Django 자동 생성분, 실질 변경 없음) +
  `PlaceEndorsement` `CreateModel`.
- `apps/places/admin.py`: `LocalPlaceAdmin`에 뱃지 필드 2개를 `list_display`/
  `list_filter`/`list_editable`에 추가(목록에서 바로 체크 가능). `PlaceEndorsement`용
  `PlaceEndorsementAdmin`(신규) 등록 — `list_display = ['place', 'user', 'created_at']`.
- `tests/test_places_endorsement.py`(신규): 모델 레벨 테스트 2건 —
  `test_local_place_badge_fields_default_false`(뱃지 기본값 확인),
  `test_duplicate_endorsement_blocked_at_db_level`(`unique_together` 위반 시
  `IntegrityError` 확인).
