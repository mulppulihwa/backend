# 정책 상세 필드 추가 (지원 자격 · 신청 방법 · 신청 기관)

**날짜**: 2026-06-16

## 작업 배경

정책 상세 화면의 "지원 자격 / 신청 방법 / 신청 기관" 항목이 비어 있었다.
Policy 모델에 해당 필드 자체가 없었고, AI 파싱 도구(`PARSE_TOOL`)에도 항목이
빠져 있었기 때문.

## AS-IS

- `Policy` 모델에 `qualification_text`, `how_to_apply`, `apply_institution` 필드 없음.
- `PARSE_TOOL` / `ParsedPolicy` 에 해당 항목 없음 → AI가 공고문에서 추출 불가.
- 복지로 `serviceDetail` API의 `신청방법`, `접수기관명` 필드를 사용하지 않음.
- `PolicyDetailSerializer`에 미포함 → API 응답에 미노출.

## TO-BE

- `Policy` 모델에 세 TextField/CharField 추가 (마이그레이션 `0009`).
- `ParsedPolicy` + `PARSE_TOOL`에 세 항목 추가 → 그린대로·수동입력 공고문에서 AI 자동 추출.
- 복지로 `_fetch_checklist_labels` → `_fetch_detail`로 확장:
  `신청방법`, `접수기관명`도 함께 가져와 저장.
- 복지로 `지원대상` + `선정기준` → `qualification_text`에 직접 매핑.
- `PolicyDetailSerializer`에 세 필드 추가.

## 주요 변경

- `apps/policies/models.py`: `qualification_text`, `how_to_apply`, `apply_institution` 추가.
- `apps/policies/migrations/0009_add_policy_detail_fields.py`(신규).
- `lib/parsing/policy_parser.py`: `ParsedPolicy` + `PARSE_TOOL` 업데이트.
- `lib/sync/adapters/bokjiro_sync.py`: `_fetch_checklist_labels` → `_fetch_detail` 리팩터.
- `lib/sync/adapters/greendaero_sync.py`: parsed 필드 매핑에 세 항목 추가.
- `apps/policies/serializers.py`: `PolicyDetailSerializer` 업데이트.
- `tests/test_policy_parser.py`: 기존 ValidationError 테스트 입력값 수정.
