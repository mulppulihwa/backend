# JobPost 목록/생성/상세/수정/삭제 API 추가

**날짜**: 2026-08-20
**커밋 로그**: [89682d6](https://github.com/mulppulihwa/backend/commit/89682d6)

## 작업 배경

구하기 게시판(`apps.board`) 기능 구현 계획의 Task 4. Task 2~3에서 만든
`JobPost` 모델(모집글)을 REST API로 노출한다. `apps.places`에 이미 자리잡은
패턴(APIView 클래스, `get_permissions()` 메서드별 오버라이드, 수동
`try/except Model.DoesNotExist` 조회, `{'error', 'code'}` 에러 응답 형식)을
그대로 따른다.

## AS-IS

- `apps.board`에 `JobPost`, `JobApplication` 모델만 존재 (Task 2~3)
- `apps/board/serializers.py`, `views.py`, `urls.py` 없음
- `config/urls.py`에 board 라우트 연결 없음

## TO-BE

- `apps/board/serializers.py`: `JobPostSerializer`(읽기, `is_owner`/`created_by_nickname` 포함), `JobPostWriteSerializer`(쓰기)
- `apps/board/views.py`: `JobPostListView`(GET 목록+category/region 필터, POST 생성), `JobPostDetailView`(GET 상세, PATCH/DELETE는 작성자 본인만)
- `apps/board/urls.py`: `/jobs/`, `/jobs/<int:pk>/`
- `config/urls.py`: `path('api/board/', include('apps.board.urls'))` 추가 (`api/regions/` 다음 줄)
- DELETE는 하드 삭제 대신 `is_active = False` 소프트 삭제

## 주요 변경

- 목록 조회는 `is_active=True`인 글만 반환, `category`/`region` 쿼리 파라미터로 필터링
- 생성은 인증 필요(`IsAuthenticated`), 목록/상세 조회는 `AllowAny`
- 수정/삭제는 `created_by_id != request.user.id`일 때 403 (`not_owner`) 반환
- `tests/test_board_jobs.py`에 `TestJobPostAPI` 클래스 추가 (목록/필터/인증 필요/생성-조회/소유자 아님/소프트 삭제 6개 테스트) — 총 8개 테스트 통과
