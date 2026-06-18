# 마감 지난 정책 하드 삭제 커맨드 추가

**날짜**: 2026-06-16

## 작업 배경

`apply_end_date`가 오늘보다 이전인 정책은 더 이상 추천에 의미가 없으므로 DB에서
완전히 제거하기로 결정. `UserPolicy`(저장 내역)와 `ChecklistItem`은 Policy와
`on_delete=CASCADE` 관계이므로 함께 삭제된다.

## 주요 변경

- `apps/policies/management/commands/prune_expired_policies.py`(신규):
  `apply_end_date__lt=today` 정책 일괄 삭제 management command.
  - `apply_end_date=null`(상시 모집) 정책은 건드리지 않음.
  - `--dry-run` 옵션으로 삭제 대상 미리 확인 가능.

## 실행 방법

```bash
# 삭제 대상 확인
railway run python manage.py prune_expired_policies --dry-run

# 실제 삭제
railway run python manage.py prune_expired_policies
```
