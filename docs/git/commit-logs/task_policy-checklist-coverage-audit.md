# 정책 체크리스트 커버리지 점검 + 수기 보완 (id 1444, 1446)

**날짜**: 2026-08-26
**커밋 로그**: [c30c300](https://github.com/mulppulihwa/backend/commit/c30c300)

## 작업 배경

사용자가 "현재 등록된 정책들에 한해 체크리스트가 있는지 확인해 달라"고 요청.
프로덕션 DB(Supabase)를 직접 조회해 현황을 파악하고, 자동으로 채울 수 있는
건 채우기로 합의.

## AS-IS (조회 시점)

- 활성 정책(`is_active=True`) 89건 중 체크리스트 없는 정책 25건
- 자동 채우기 수단 보유 여부:
  - 복지로(`external_id` 있음) → `backfill_checklists` 커맨드로 이미 전부
    커버됨 (0건 누락)
  - AI 파싱 가능(`raw_text` 있음) → 1건(id 1432, 귀농센터)
  - 나머지 24건(옥천군청 20 + 옥천군농업기술센터 4)은 `external_id`도
    `raw_text`도 없어 자동 채우기 수단이 전혀 없음

같은 세션에서 먼저 마감 지난 정책 12건을 삭제했는데(별도 커밋 참고), 그중
5건(id 1432, 1436, 1437, 1438, 1440)이 체크리스트 없는 25건과 겹쳐 있어
삭제 후 남은 미보유 건수는 20건으로 줄었음.

## TO-BE

- 20건 중 `qualification_text`/`how_to_apply`에 실제 원문이 있는 2건
  (id 1444 "2026년 충북행복결혼공제 모집", id 1446 "2026년 청년 부동산
  중개보수 및 이사비 지원")만, 그 원문을 근거로 체크리스트 초안을 작성해
  `seed_manual_checklists` 커맨드로 저장
- 나머지 18건(id 2~20 범위, 옥천군청 초기 수기입력분)은
  `qualification_text`/`how_to_apply`/`apply_institution`/`raw_text`가 전부
  빈 값이라, 추측으로 채우면 실제 신청자에게 잘못된 서류 안내가 나갈 위험이
  있어 이번 작업 범위에서 제외

## 주요 변경

- `apps/policies/management/commands/seed_manual_checklists.py`: 신규.
  `backfill_checklists`/`prune_expired_policies`와 동일하게 `--dry-run` 지원
- 프로덕션 DB에 `seed_manual_checklists` 실행 — id 1444(6개), id 1446(8개)
  체크리스트 저장

## 남은 작업 (별도 확인 필요)

- 체크리스트 없는 정책 18건(id 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15,
  16, 17, 18, 19, 20)은 원본 공고문/신청요건 텍스트를 옥천군청에서 다시
  확보하지 않는 한 자동/추론 방식으로는 채울 수 없음. 실제 공고문을 구해
  `raw_text`에 채워 넣으면 `parse_checklists` AI 파싱으로 처리 가능
