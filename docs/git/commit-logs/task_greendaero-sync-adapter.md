# 그린대로 귀농·농업 지원사업 동기화 어댑터 추가

**날짜**: 2026-06-15
**커밋 로그**: [76fd82a](https://github.com/mulppulihwa/backend/commit/76fd82a)

## 작업 배경

§9 작업 순서의 4번째 단계(정책 크롤링 source 수정). 향후 정책 크롤링
소스를 그린대로/옥천군청 두 곳으로 한정하기로 했고, 그 중 그린대로
어댑터를 먼저 구현.

`backend-plan.md`에 있던 `crawl_greendaero()` 스케치(`table.list tr`
셀렉터, BeautifulSoup)는 실제 페이지 구조를 확인하지 않은 placeholder였음.
실제로 greendaero.go.kr의 정책정보 메뉴는 SPA로 렌더링되며, 브라우저
개발자도구로 확인한 결과 화면은 `/svc/cmns/search/wise/searchTotalInfo.do`
JSON API(통합검색)를 호출해 데이터를 채움.

`topic=A`(지원정책) 통합검색은 두 종류가 섞여 있음:
- `CMNS_CD_NM: "농림축산식품사업(2026년)"` — 전국 단위 귀농·농업 지원사업
  (1페이지에 고정 8건, IEM_CN1~5에 목적/대상/요건/제출서류/지원내용 텍스트 포함)
- `CMNS_CD_NM: "기초자치단체정책"` — 시군구별 일반 복지정책 (10,508건,
  `ctpv_cd1`/`sgg_cd1`로 옥천군 필터링 시도했으나 그린대로 자체 지역코드
  체계를 알아내지 못해 0건 반환 — 역공학 비용이 큼)

후자는 보류하고, 전자(전국 귀농·농업 지원사업)만 가져오기로 함 —
옥천 한정은 아니지만 귀농·농업 정책으로 범위를 넓혀도 된다는 결정에
부합하고, region 코드 문제도 없음.

## AS-IS

그린대로 소스로 정책을 가져오는 어댑터 없음 (`Policy.SOURCES`에
`'귀농센터'` 선택지만 미리 정의되어 있었음).

## TO-BE

- `lib/sync/adapters/greendaero_sync.py` 신설
  - `searchTotalInfo.do?topic=A&sort=DATE&pageNum=1` 호출
  - `resultList`에서 `CMNS_CD_NM`에 "농림축산식품사업" 포함된 항목만 필터
  - `bokjiro_sync.py`와 동일한 패턴:
    - `Policy.objects.filter(title=title).exclude(source='귀농센터').exists()`
      cross-source dedup
    - `parse_policy()`로 IEM_CN1~5 텍스트 파싱, confidence ≥0.7이면
      `is_active=True`
    - `external_id=BBSCTT_SN`, `source='귀농센터'`
    - `source_url`은 `policyDetail.do?bbscttSn=...`
    - `published_at`은 API의 `DATE`(`YYYY.MM.DD`) 필드를 직접 파싱해 채움
      (LLM 불필요)
    - `apply_end_date`는 parse_policy 결과(`YYYY-MM-DD`)가 있을 때만 채움
- `apps/policies/management/commands/sync_greendaero.py` 신설 —
  `sync_bokjiro` 명령어와 동일한 형태, `--max-items` 옵션

## 주요 변경

- `lib/sync/adapters/greendaero_sync.py` — 신규
- `apps/policies/management/commands/sync_greendaero.py` — 신규
- `Policy.SOURCES`/모델 변경 없음 (`'귀농센터'` 선택지 기존 그대로 사용)

## 검증

`pytest tests/` — 35 passed, 1 failed (기존부터 실패하던 무관 테스트,
`test_policy_parser.py::test_pydantic_validation_error`).

management command `sync_greendaero --help` 정상 등록 확인.
실제 API 호출/DB 반영은 §9 5번 단계(샘플 데이터 테스트)에서 진행.

## 참고 — 남은 작업 (§9)

- 옥천군청 어댑터는 보류 — 특정 게시판 형식이 아니라 별도 조사 필요,
  추후 별도 작업으로 진행.
- 4번 단계의 그린대로 부분 완료. 5번(샘플 데이터 테스트), 6번(정책 DB
  정리 + 전체 크롤링), 7번(계정 초기화, 최종) 이어서 진행.
