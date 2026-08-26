# 사용처 카테고리 8종 재편 + 내 추천목록(my_endorsed) 필터 추가

**날짜**: 2026-08-26
**커밋 로그**: [29e7b9b](https://github.com/mulppulihwa/backend/commit/29e7b9b)

## 작업 배경

사용자가 사용처 카테고리를 `농자재, 농기계, 행정, 생활, 명소, 음식점, 동호회,
부동산, 내가 추천한 가게(좋아요 누른 가게)` 9종으로 정리해 달라고 요청.

프로덕션 DB(Supabase)를 직접 조회해보니 기존 14개 카테고리 중 실제로 쓰이는 건
8개뿐이었고, 그마저도 테스트/더미 데이터가 많이 섞여 있었음:

- `건축자재` 카테고리의 실제 내용물이 전부 **부동산 중개사무소**
  (옥천향수공인중개사사무소, 열매공인중개사사무소) — 실제 업종과 기존 카테고리가
  전혀 안 맞았음
- `약국` 카테고리는 실제 약국이 0곳이고 전부 테스트용 더미 데이터
  (금강전기공사, 쌍둥이네집수리 등 — 심지어 `생활`에도 동일 이름으로 중복 등록)
- `동호회` 중 옥천향수시네마/옥천체육센터/옥천문화예술관은 클럽이 아니라 장소성
  콘텐츠라 신규 `명소` 카테고리가 더 적합

또한 "내가 추천한 가게"를 요청받았을 때, 이건 유저마다 값이 다른(같은 가게라도
A에게는 해당·B에게는 비해당) 속성이라 `category` 컬럼(장소 하나에 값 하나, 모든
유저에게 동일하게 보임) 자체에는 저장할 수 없다는 점을 사용자에게 설명하고,
목록 API의 쿼리 필터로 구현하기로 합의.

## AS-IS

- `LocalPlace.CATEGORIES` 14종: 지원금사용처/농자재/농기계/농협/행정/생활/
  음식점/약국/건축자재/의류/식품/전자제품/가구/동호회 — 실사용 8종 + 미사용 6종
- `GET /api/places/`에 카테고리/추천 여부로 필터링할 방법이 없어 "내가 추천한
  가게만 보기"를 구현할 방법이 없었음

## TO-BE

- `LocalPlace.CATEGORIES`를 8종(농자재/농기계/행정/생활/명소/음식점/동호회/
  부동산)으로 축소
- 마이그레이션 `0005_update_category_choices`에 `RunPython` 데이터 재매핑 포함
  (스키마 변경과 한 마이그레이션에서 함께 처리, `noop`으로 역방향 지원):
  ```python
  REMAP = {
      '건축자재': '부동산', '약국': '생활', '지원금사용처': '생활',
      '농협': '생활', '의류': '생활', '식품': '생활',
      '전자제품': '생활', '가구': '생활',
  }
  RECLASSIFY_TO_LANDMARK = [97, 98, 99]  # 옥천향수시네마/체육센터/문화예술관
  ```
  적용 결과(총 47곳): 생활 17 / 행정 11 / 음식점 5 / 농기계 4 / 동호회 4 /
  부동산 3 / 명소 3
- `GET /api/places/?my_endorsed=true` 필터 추가. 비로그인 요청은 빈 배열 반환.
  `pk__in=PlaceEndorsement.objects.filter(user=...).values('place_id')`로
  서브쿼리 필터링 — `annotate(Count('endorsements'))` 뒤에
  `.filter(endorsements__user=...)`를 그대로 쓰면 같은 관계의 JOIN이 재사용돼
  `endorsement_count`가 본인 추천 1건으로 줄어드는 Django 함정이 있어 이를 피함

## 주요 변경

- `apps/places/models.py`: `CATEGORIES` 14종 → 8종
- `apps/places/migrations/0005_update_category_choices.py`: 신규 —
  choices 변경 + 데이터 재매핑 RunPython
- `apps/places/views.py`: `PlaceListView.get()`에 `my_endorsed` 쿼리 파라미터
  처리 추가
- `tests/test_places_endorsement.py`: 기존 테스트의 카테고리 값을 `식품`→`생활`로
  수정(제거된 카테고리라 400 발생하던 것 수정), 신규 테스트 2건 —
  `test_my_endorsed_filter_returns_only_endorsed_places`(필터링 + 타인 추천
  포함 count 검증), `test_my_endorsed_filter_requires_auth`
- 전체 테스트 스위트 84건 중 83건 통과 확인 (나머지 1건은 백그라운드 테스트를
  겹쳐 돌리다 생긴 테스트 DB 커넥션 충돌로, 단독 재실행 시 정상 통과 — 이번
  변경과 무관)

## 함께 진행한 운영 작업 (코드 변경 아님)

- `python manage.py prune_expired_policies` 실행 — 마감일이 지난 정책 12건을
  프로덕션 DB에서 삭제 (기존 마감정책 삭제 명령어를 그대로 사용, 자동화 인프라
  없이 수동 실행)

## 범위에서 제외한 것

- 프론트엔드(`socialventure-frontend`)는 사용자 요청 전까지 손대지 않는다는
  기존 방침에 따라, 카테고리 아이콘/탭 UI는 이번 작업에서 다루지 않음
