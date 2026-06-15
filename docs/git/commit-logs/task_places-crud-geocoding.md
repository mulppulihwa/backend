# 사용처(LocalPlace) 등록/수정/삭제 API 및 주소→좌표 변환 추가

**날짜**: 2026-06-15
**커밋 로그**: [1c0176d](https://github.com/mulppulihwa/backend/commit/1c0176d)

## 작업 배경

v2.0.0 현장 피드백 §7(사용처 CRUD) — 사용처 보기 페이지에서 "추가하기" 클릭 →
주소찾기 팝업(다음 Postcode) → 사용처 등록 팝업(이름/주소 자동입력 + 전화번호/
운영시간/메모 직접입력) → 등록 직후 카카오맵에 마커 표시, 그리고 본인이 등록한
사용처에 한해 목록 카드에서 수정/삭제가 가능해야 하는 시나리오 구현.

## AS-IS

- `apps/places/views.py`에 `PlaceListView`(GET 목록)만 존재 — 등록/수정/삭제/상세
  API 없음.
- `LocalPlace` 모델에 운영시간(`business_hours`), 등록자(`created_by`) 필드 없음.
- 사용자가 등록한 장소의 좌표(`lat`/`lng`)를 채울 방법이 없음 — 지도에 바로
  표시되지 않음.

## TO-BE

- `GET/POST /api/places/`, `GET/PATCH/DELETE /api/places/<id>/` 전체 CRUD 구현.
- 등록/수정 시 본인 소유 여부(`created_by`)로 권한 판별, 응답에 `is_owner` 포함.
- 등록·수정 시 `lat`/`lng`을 프론트(Kakao Maps Geocoder)가 보내면 그대로 저장,
  안 보내면 백엔드가 카카오 주소 검색 API로 변환(`geocode_address`) — 등록 즉시
  지도에 마커 표시 가능.

## 주요 변경

- `apps/places/models.py`: `LocalPlace`에 `business_hours`(CharField, blank),
  `created_by`(FK → User, `SET_NULL`, `related_name='registered_places'`) 추가.
  마이그레이션 `0003_localplace_business_hours_localplace_created_by`.
- `apps/places/serializers.py`:
  - `LocalPlaceSerializer`(읽기) — `business_hours`, `local_memo`, `is_owner`
    (`request.user`가 `created_by`와 같은지) 추가.
  - `LocalPlaceWriteSerializer`(쓰기, 신규) — `name`/`address`/`category` 필수,
    `phone`/`business_hours`/`local_memo`/`lat`/`lng` 선택.
- `apps/places/views.py`:
  - `PlaceListView.post` — `IsAuthenticated`, `created_by=request.user`로 등록.
    `lat`/`lng` 미제공 시 `geocode_address(address)` 폴백.
  - `PlaceDetailView`(신규) — `GET`(공개, `is_owner` 포함), `PATCH`/`DELETE`
    (`IsAuthenticated` + 소유자 검증, 아니면 403). `PATCH`에서 주소가 바뀌고
    `lat`/`lng`을 안 보낸 경우에만 재geocoding. `DELETE`는 `is_active=False`
    soft delete.
- `apps/places/urls.py`: `path('<int:pk>/', PlaceDetailView.as_view())` 추가.
- `apps/places/admin.py`: list_display에 `created_by` 추가.
- `lib/services/geocoding.py`(신규): 카카오 로컬 "주소 검색" API로 주소→좌표
  변환. `KAKAO_LOCAL_API_KEY` 미설정/요청 실패/결과 없음이면 `None` 반환(no-op).
- `tests/test_geocoding.py`(신규): geocoding 함수 단위 테스트 5건
  (빈 주소, 키 없음, 성공, 결과 없음, HTTP 에러).
