# 신뢰도 기반 안심 검증 마크 설계

- 작성일: 2026-08-20
- 관련 레포: `mulppulihwa/backend` (본 레포)
- 범위: 옥천신문/옥천군 상담센터 추천 뱃지 + 사용자 추천(좋아요) 기능. 야간 무인 작업으로 진행되어 브레인스토밍 인터랙션 없이 기존 요구사항(최초 사용자 메시지의 usecase 2)을 근거로 작성. 애매한 지점은 판단 근거를 명시하고 "판단 사항" 섹션에 모아둠 — 아침에 검토 요망.

## 배경 / 목적

지도 상 사용처(`apps.places.LocalPlace`) 카드에 신뢰도 신호를 노출한다: 옥천신문/옥천군 상담센터가 추천한 곳인지, 주민들이 얼마나 추천했는지. 두 기관 추천 여부는 관리자가 큐레이션하는 정적 플래그이고, 사용자 추천("추천해요" 버튼)은 로그인 사용자가 실시간으로 누적하는 카운터다.

## 데이터 모델

### `LocalPlace`에 필드 2개 추가 (`apps/places/models.py`)
| 필드 | 타입 | 비고 |
|---|---|---|
| okcheon_news_recommended | BooleanField(default=False) | 옥천신문 추천 여부 |
| counseling_center_recommended | BooleanField(default=False) | 옥천군 상담센터 추천 여부 |

두 필드 모두 **관리자 전용** — `LocalPlaceWriteSerializer`(사용자가 사용처 등록/수정 시 쓰는 시리얼라이저)에는 포함하지 않는다. 기존 레포 컨벤션과 동일: `subsidy_tags`, `receipt_claimable`, `is_active` 등도 이미 `LocalPlaceWriteSerializer.fields`에서 빠져있고 관리자(Admin) 또는 시스템이 채운다. Django Admin의 `LocalPlaceAdmin.list_display`/`list_editable`에 추가해 관리자가 체크박스로 바로 토글하게 한다.

### `PlaceEndorsement` (신규 모델, `apps/places/models.py`)
| 필드 | 타입 | 비고 |
|---|---|---|
| place | FK LocalPlace, related_name='endorsements' | |
| user | FK users.User, related_name='place_endorsements' | |
| created_at | DateTimeField(auto_now_add=True) | |
| unique_together | (place, user) | 중복 추천 방지 — `apps.board.JobApplication`과 동일 패턴 |

카운터를 `LocalPlace`에 별도 정수 필드로 비정규화하지 않고, `endorsements.count()`로 그때그때 계산한다. 이 레포에 페이지네이션 컨벤션이 없어 목록이 크지 않다고 가정하는 것과 같은 이유로, 지금 규모(옥천군 사용처)에서 매번 `count()` 하는 비용은 무시할 만하고, 비정규화 카운터는 동시성 버그(레이스로 카운트 drift)를 낳을 여지가 있어 피한다.

## API

기존 `apps/places` 컨벤션(APIView, 읽기/쓰기 시리얼라이저 분리, `{'error','code'}` 에러, soft delete 무관)을 따른다.

- `LocalPlaceSerializer`(읽기)에 필드 추가: `okcheon_news_recommended`, `counseling_center_recommended`, `endorsement_count`(`SerializerMethodField`, `obj.endorsements.count()`), `is_endorsed`(`SerializerMethodField`, 로그인 사용자가 이미 추천했는지)
- `POST /api/places/<int:pk>/endorse/` — 신규 엔드포인트. `IsAuthenticated`. `PlaceEndorsement.objects.get_or_create(place=place, user=request.user)`로 **멱등** 처리 — 이미 추천한 상태에서 다시 눌러도 에러 없이 현재 상태(`endorsement_count`, `is_endorsed: true`)를 그대로 반환한다. "좋아요" 버튼과 동일한 UX이므로 `JobApplication`의 "중복 지원 시 400"과 다르게, 중복 호출을 사용자 실수가 아니라 정상적인 재클릭으로 본다.
  - 응답: `{'endorsement_count': <int>, 'is_endorsed': true}`
  - 존재하지 않는/비활성 사용처면 404 `{'error': '사용처를 찾을 수 없습니다.', 'code': 'place_not_found'}` (기존 `PlaceDetailView`와 동일 메시지 재사용)
- 추천 취소(unlike) 엔드포인트는 **만들지 않는다** — usecase에 취소 동작이 없고, 지금 없어도 되는 기능을 미리 만들지 않는다(YAGNI).

## 판단 사항 (아침에 확인 요망)

1. **추천 재호출을 멱등 처리(에러 없이 현재 상태 반환)한 것**: usecase 원문 "사용자가 이미 추천한 가맹점인 경우 추천 상태를 활성화하여 중복 추천을 방지한다"를 "버튼이 눌린 상태로 유지되고 카운트는 더 안 올라간다"로 해석했다. "중복 추천 시도 시 에러 메시지를 보여줘야 한다"는 의도였다면 `JobApplication`처럼 400 `already_endorsed`로 바꿔야 한다.
2. **추천 취소(언추천) 기능 없음**: 요구사항에 명시되지 않아 안 만들었다. 필요하면 `DELETE /api/places/<pk>/endorse/` 추가는 간단하다(이미 있는 `PlaceEndorsement` unique_together 구조 그대로 재사용 가능).
3. **뱃지 필드는 관리자 전용**으로 결정 — 사용처 등록 폼(프론트)에서 사용자가 "우리 가게가 옥천신문에 추천됐어요" 같은 자기 신고를 못 하게 막았다. 두 기관의 실제 추천 여부는 운영진이 Django Admin에서 수기로 반영하는 걸 전제로 한다. 이 운영 프로세스(누가, 어떻게 실제 추천 여부를 확인해서 반영하는지)는 이 스펙 범위 밖 — 아침에 확인 필요.
4. **카운터 비정규화 안 함**(매번 `count()`) — 사용처 개수가 많아지면(수백~수천) 목록 API에서 N+1 걱정이 있다. `LocalPlaceListView`에서 `annotate(endorsement_count_anno=Count('endorsements'))`로 쿼리 1번에 처리하는 걸 구현 단계에서 우선 시도하고, 여의치 않으면 `SerializerMethodField` + `prefetch_related('endorsements')`로 폴백한다.

## 테스트

`tests/test_places_endorsement.py` 신규 파일. 최소 커버리지: 추천 시 카운트 1 증가, 같은 사용자가 두 번 추천해도 카운트 그대로(멱등), 비로그인 추천 시 401, 존재하지 않는 사용처 추천 시 404, `LocalPlaceSerializer`가 뱃지 필드/카운트/`is_endorsed`를 정확히 반환.

## 범위 밖

- 프론트엔드 UI(뱃지 표시, 추천 버튼) — 이 레포는 백엔드 전용
- 옥천신문/상담센터 추천 여부를 자동으로 가져오는 파이프라인(크롤링 등) — 지금은 수동(Admin) 입력
