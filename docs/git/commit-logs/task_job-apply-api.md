# 지원하기 + 지원자 목록 API 추가

**날짜**: 2026-08-20
**커밋 로그**: [ca0e079](https://github.com/mulppulihwa/backend/commit/ca0e079)

## 작업 배경

구하기 게시판(`apps.board`) 기능 구현 계획의 Task 5. Task 4에서 만든
`JobPost` 목록/생성/상세/수정/삭제 API에 이어, 지원자가 모집글에 "지원하기"를
할 수 있는 엔드포인트와 작성자가 지원자 목록을 확인하는 엔드포인트를 추가한다.
기존 뷰들과 동일한 패턴(APIView, 수동 `try/except Model.DoesNotExist` 조회,
`{'error', 'code'}` 에러 응답 형식)을 그대로 따른다.

## AS-IS

- `apps/board/serializers.py`에 `JobPostSerializer`, `JobPostWriteSerializer`만 존재
- `apps/board/views.py`에 `JobPostListView`, `JobPostDetailView`만 존재
- `apps/board/urls.py`에 `jobs/`, `jobs/<int:pk>/` 두 라우트만 존재
- `JobApplication` 모델(Task 3)은 있지만 API로 노출되지 않음

## TO-BE

- `apps/board/serializers.py`: `JobApplicationSerializer` 추가 (`id`, `name`, `phone`, `message`, `applied_at`)
- `apps/board/views.py`: `JobApplyView`(POST, 인증 필요), `JobApplicationListView`(GET, 인증 필요) 추가
- `apps/board/urls.py`: `jobs/<int:pk>/apply/`, `jobs/<int:pk>/applications/` 라우트 추가

## 주요 변경

- `JobApplyView.post`: 대상 모집글이 없으면 404(`job_post_not_found`), 이미 지원한 이력이 있으면
  `get_or_create` 대신 사전 존재 체크로 400(`already_applied`)을 반환해 원시 `IntegrityError`가
  API 응답으로 새지 않도록 함
- 지원 시 요청 본문에 `name`/`phone`이 없으면 `request.user.profile.applicant_name` /
  `request.user.phone`으로 자동 채움 — `UserProfile`은 시그널로 항상 존재하므로 null 체크 불필요
- 지원 완료 후 이름/전화번호가 프로필/유저에 저장된 값과 다르면 다시 저장해, 다음 지원부터
  자동으로 채워지도록 함(`update_fields`로 부분 저장)
- `JobApplicationListView.get`: 작성자 본인이 아니면 403(`not_owner`), 본인이면 지원자 목록을
  `-applied_at` 순으로 반환
- `tests/test_board_jobs.py`에 `TestJobApplyAPI` 클래스 추가 (인증 필요/이름·전화 자동저장/
  프로필 자동채움/중복 지원 차단/지원자 목록 소유자 제한 5개 테스트) — 총 13개 테스트 통과
