# 로직·아키텍처 점검 체크리스트

> 구현 전/중에 직접 코드 읽으며 확인할 항목.  
> `[x]` = 확인 완료, `[ ]` = 미확인

---

## A. 정책 매칭 파이프라인 (`lib/policy_matcher.py`)

- [x] `region_codes__exact=[]` — 전국 정책 포함 (수정 완료 2026-05-17)
- [x] `occupation_tags__exact=[]` — 직업 제한 없는 정책 포함 (수정 완료)
- [x] `income_level__exact=[]` — 소득 제한 없는 정책 포함 (수정 완료)
- [ ] `is_disabled=None` → 장애 필터 스킵 정상 동작하는지 확인
- [ ] 옥천군(43720) 사용자 → 충청북도(43) 정책 매칭되는지 확인 (ancestor_codes CTE 검증)
- [ ] 옥천군(43720) 사용자 → 전국(region_codes=[]) 정책 매칭되는지 확인
- [ ] fallback 동작: 매칭 0건 → 최신 10개 반환이 실제로 트리거되는지
- [ ] `age=None`(birth_date 미입력) → age 0으로 처리 → min_age=0 정책만 매칭 (의도된 동작인지 확인)

---

## B. condition_tree 평가기 (`lib/condition_tree.py`)

- [x] AND/OR/NOT/LEAF 기본 동작 테스트됨
- [x] unknown node type → False + 경고 로그
- [ ] **`op='in'` + 리스트 필드 버그 미해결** — `occupation_tags`(profile 값이 list)로 `val in value` 하면 `['귀농'] in ['귀농', '귀촌']` = False. condition_tree LEAF에서 리스트 필드를 쓸 경우 항상 False 반환됨. → `any(x in value for x in val)` 로 수정 필요
- [ ] `op='in'`이 리스트 값인지 스칼라 값인지 Claude 출력 기준 확인 (정책 파싱 시 어떻게 생성되는지)
- [ ] `field='years_since_move'`, `op='lte'` — float 비교 정상 동작하는지
- [ ] `field='farm_registered_date'` — date 문자열 비교가 의도대로 동작하는지

---

## C. 카카오 OAuth + JWT (`apps/users/views.py`)

- [x] code 없을 때 400
- [x] 카카오 타임아웃 → 503
- [x] 잘못된 code → 401
- [x] 신규 유저 생성 / 기존 유저 조회
- [ ] **JWT access token 만료 시간 설정** — SimpleJWT 기본값 5분. 60세+ 사용자가 온보딩 폼(5개 질문) 작성 중 만료될 수 있음. `SIMPLE_JWT` 설정에서 `ACCESS_TOKEN_LIFETIME` 확인 필요 (최소 30분 권장)
- [ ] refresh token 만료 후 재로그인 흐름 프론트와 협의됐는지
- [ ] `profile_completed=False` 유저가 `/api/policies/match/` 호출 시 404 응답 정상 동작

---

## D. 정책 파싱 (`lib/policy_parser.py`)

- [x] 빈 텍스트 → PolicyParseError
- [x] Claude RateLimitError → PolicyParseError
- [x] Claude APITimeoutError → PolicyParseError
- [x] Pydantic ValidationError → PolicyParseError
- [ ] `confidence < 0.7` 결과: `min_age=0, max_age=130, region_codes=[]` 기본값으로 저장됨 → 관리자가 `is_active=True`로 수동 활성화 시 모든 사용자에게 노출될 위험. Admin 화면에서 경고 필요한지 검토
- [ ] `tool_choice='auto'` → Claude가 tool 안 쓰고 텍스트 응답 시 PolicyParseError 발생하는지 확인
- [ ] 파싱 결과의 `region_codes` — `['43720']`(옥천군), `['43']`(충북), `[]`(전국) 세 케이스가 실제 파싱 출력에서 정확히 나오는지 프롬프트로 테스트

---

## E. 복지로 동기화 (`lib/bokjiro_sync.py` — 미구현)

- [ ] **구현 전 플랜 §10 코드 예시 반드시 확인** — for 루프 while 안에 있는지 체크 (2026-05-17 수정됨)
- [ ] `httpx.get` 호출에 try/except 추가 필요 — 네트워크 오류 시 전체 sync 중단, 부분 저장된 항목은 살아있음
- [ ] `per_page=20`, `CLAUDE_CALL_DELAY=0.5` 설정 적용됐는지
- [ ] 같은 `external_id` 두 번 실행 → upsert (중복 없음) 검증
- [ ] 타 소스(수동입력) 동일 제목 스킵 → 원래 의도는 중복 방지인데, 더 풍부한 복지로 데이터가 버려지는 문제 인지하고 있는지

---

## F. 지역 계층 (`lib/region_hierarchy.py`)

- [ ] `regions` 테이블 비어있을 때 → fallback `[region_code]` 반환 동작 확인
- [ ] 옥천군(43720) → `[43720, 43]` 반환 되는지 CTE 직접 실행해서 확인
- [ ] 배포 체크리스트에 `regions` 시드 데이터 로드 포함됐는지 (§15 체크리스트 확인 필요)

---

## G. 아키텍처 전반

- [x] §2 다이어그램 — 카카오 로컬 API 제거됨 (2026-05-17 수정)
- [ ] `CORS_ALLOWED_ORIGINS` — Vercel 도메인만 허용 설정됐는지
- [ ] Django Admin(`/admin/`) — Railway 배포 환경에서 static files 서빙 (whitenoise 또는 S3 필요한지)
- [ ] `SECRET_KEY` — 50자 이상 랜덤값, `.env`에만 있는지
- [ ] `DEBUG=False` — 배포 환경에서 반드시 False 확인
- [ ] `IsAdminUser` 권한 체크 — Django admin 계정(superuser)으로만 파싱 API 호출 가능한지

---

## 미해결 (Outside Voice 지적, 아직 결정 안 됨)

- [ ] **condition_tree `op='in'` + 리스트 필드** — 위 B 섹션 참고. 수정 여부 결정 필요
- [ ] **JWT access token 만료시간** — 위 C 섹션 참고. 30분으로 늘릴지 결정 필요
- [ ] **sync_bokjiro HTTP 오류 시 재시도 없음** — 위 E 섹션 참고. v1 허용 범위인지 결정 필요
