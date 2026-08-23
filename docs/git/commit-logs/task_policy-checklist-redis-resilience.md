# 준비물 체크리스트 조회 시 Redis 장애에도 500 대신 DB 폴백

**날짜**: 2026-08-23
**커밋 로그**: [7751d16](https://github.com/mulppulihwa/backend/commit/7751d16)

## 작업 배경

"준비물 확인이 안 된다"는 사용자 제보로 Railway 프로덕션 로그를 확인.
`/api/policies/<id>/checklist/` 요청마다 다음 에러가 반복되고 있었음:

```
redis.exceptions.ConnectionError: Error -2 connecting to redis.railway.internal:6379.
Name or service not known.
```

`railway status`로 확인해보니 Redis 데이터베이스 서비스 자체가 `Failed` 상태였고,
내부 DNS(`redis.railway.internal`)가 해석되지 않아 캐시 접근이 전부 실패하고 있었음.

## AS-IS

- `PolicyChecklistView.get()`이 `cache.get(key)`를 예외 처리 없이 바로 호출.
- Redis 연결 실패가 그대로 `ConnectionError`로 view까지 전파되어 500 Internal
  Server Error 응답.
- 코드베이스 내 캐시 접근 지점 중 `lib/sync/adapters/bokjiro_sync.py`의
  `cache.delete`에는 이미 동일한 문제로 try/except 가드가 붙어있었지만
  (`89cdda2`), 정작 사용자가 직접 호출하는 조회 경로(`apps/policies/views.py`)에는
  적용되어 있지 않았음.

## TO-BE

- `apps/policies/views.py`에 `_cache_get`/`_cache_set`/`_cache_delete` 헬퍼 추가.
  캐시 백엔드 예외를 흡수하고 `logger.warning`만 남긴 뒤, `get`은 `None`을
  반환하고 `set`/`delete`는 조용히 무시.
- `PolicyChecklistView.get()`과 백그라운드 파싱 헬퍼 `_parse_checklist_bg()`의
  모든 `cache.*` 호출을 이 헬퍼로 교체.
- 결과: Redis가 죽어있어도 캐시 없이 DB(`ChecklistItem`)에서 바로 조회해
  200 응답. 캐시가 살아있을 때의 정상 동작(캐시 히트/저장)은 그대로 유지.

## 주요 변경

- `apps/policies/views.py`: `_cache_get`/`_cache_set`/`_cache_delete` 헬퍼 추가,
  기존 `cache.get`/`cache.set`/`cache.delete` 호출 7곳을 헬퍼 호출로 교체.
- `tests/test_policy_checklist.py`: 신규 테스트 5건 —
  `test_checklist_returns_items_normally`(정상 조회),
  `test_checklist_nonexistent_policy_404`,
  `test_checklist_survives_redis_outage_on_read`(`cache.get`이
  `ConnectionError`를 던져도 200 + DB 값 응답),
  `test_checklist_survives_redis_outage_on_write`(`cache.set` 실패해도 200),
  `test_checklist_no_items_no_raw_text_survives_redis_outage`.
- 전체 테스트 스위트(`pytest tests/`) 80건 전부 통과 확인.

## 범위에서 제외한 것

- `apps/policies/admin.py`, `apps/policies/management/commands/backfill_checklists.py`
  의 미가드 `cache.delete` 호출은 이번 사용자 제보(조회 500 에러)와 직접 관련이
  없어 손대지 않음. 같은 클래스의 문제이긴 하나 admin 액션/수동 커맨드라 사용자
  트래픽에 영향이 없고, 필요하면 별도 작업으로 처리.
- Redis 서비스 자체를 다시 살리는 작업(A)은 별도 진행.
