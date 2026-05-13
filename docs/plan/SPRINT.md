# 스프린트 계획

총 예상 기간: **2~3주** (1인 기준)  
병렬 가능한 구간: Sprint 2 + Sprint 3는 동시 진행 가능  
각 태스크는 30분~2시간 단위

---

## Sprint 0 — 프로젝트 세팅 (0.5일)

| # | 태스크 | 예상 |
|---|---|---|
| S0-1 | `npx create-next-app` (TypeScript + Tailwind + App Router) | 15분 |
| S0-2 | Supabase 프로젝트 생성 + `.env.local` 연결 (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`) | 20분 |
| S0-3 | Vercel 프로젝트 생성 + GitHub 연동 + 환경변수 등록 | 20분 |
| S0-4 | 카카오 개발자 콘솔 앱 등록 (로그인 + 지도) — [TODOS 체크리스트 참고](../../../TODOS.md) | 30분 |
| S0-5 | `npm install` 패키지 설치: `next-auth @supabase/supabase-js` | 5분 |
| S0-6 | 폴더 구조 생성: `app/`, `components/`, `lib/`, `data/seed/` | 5분 |

---

## Sprint 1 — 인증 + 프로필 폼 (1~1.5일) `Lane A`

### DB
| # | 태스크 | 예상 |
|---|---|---|
| S1-1 | `supabase/migrations/001_users.sql` 작성 (User 테이블 + profile_completed) | 20분 |
| S1-2 | Supabase에 마이그레이션 실행 | 5분 |

### 인증
| # | 태스크 | 예상 |
|---|---|---|
| S1-3 | `app/api/auth/[...nextauth]/route.ts` — Kakao provider 설정 | 30분 |
| S1-4 | NextAuth `callbacks.jwt` + `callbacks.session`에 `profile_completed` 포함 | 20분 |
| S1-5 | `lib/auth.ts` — `getServerSession` helper | 10분 |
| S1-6 | 로컬에서 카카오 로그인 동작 확인 | 15분 |

### 프로필 폼
| # | 태스크 | 예상 |
|---|---|---|
| S1-7 | `app/profile/setup/page.tsx` — 5개 질문 폼 레이아웃 (노인 접근성 스펙: 폰트 18px+, 버튼 52px+) | 60분 |
| S1-8 | `POST /api/profile` — 프로필 저장 + `profile_completed=true` 업데이트 | 20분 |
| S1-9 | 홈 컴포넌트에 `useSession` 체크 → `profile_completed=false`면 `/profile/setup` 리다이렉트 | 15분 |
| S1-10 | `app/(tabs)/layout.tsx` — 하단 탭바 (홈 / 마을 지도 / 전체 정책 / 내 정보) | 30분 |

---

## Sprint 2 — 정책 매칭 엔진 (1.5~2일) `Lane B`

### DB
| # | 태스크 | 예상 |
|---|---|---|
| S2-1 | `002_regions.sql` — Regions 테이블 (code, name, parent_code, level) | 15분 |
| S2-2 | `003_policies.sql` — Policies 테이블 + GIN 인덱스 5개 | 20분 |
| S2-3 | `data/seed/regions.json` — 옥천군 계층 데이터 (전국 → 충북 → 옥천군) | 30분 |
| S2-4 | `scripts/seedRegions.ts` + 실행 | 20분 |

### 매칭 로직
| # | 태스크 | 예상 |
|---|---|---|
| S2-5 | `lib/regionHierarchy.ts` — recursive CTE로 ancestor_codes 조회 | 30분 |
| S2-6 | `lib/conditionTree.ts` — AND/OR/NOT/LEAF 평가기 (핵심 로직) | 60분 |
| S2-7 | `lib/policyMatcher.ts` — SQL 1차 필터 + condition_tree 평가 통합 | 30분 |
| S2-8 | `GET /api/policies/match` — 로그인 사용자 맞춤 매칭 API | 20분 |
| S2-9 | `GET /api/policies/preview` — 비로그인 최신 3개 API (UNION ALL 쿼리) | 20분 |

### 정책 카드 컴포넌트
| # | 태스크 | 예상 |
|---|---|---|
| S2-10 | `components/PolicyCard.tsx` — 카드 UI (정책명, 금액, 해당 이유, 마감일) | 30분 |
| S2-11 | D-7 마감 뱃지 — `apply_end_date`와 `today` 비교 → "마감 D-N" 빨간 뱃지 | 15분 |

---

## Sprint 3 — 홈 + 정책 페이지 (1일) `Lane D` (Sprint 1+2 완료 후)

| # | 태스크 | 예상 |
|---|---|---|
| S3-1 | `app/page.tsx` — 비로그인 상태: 미리보기 3개 + 로그인 CTA | 30분 |
| S3-2 | `app/page.tsx` — 로그인 상태: 맞춤 정책 리스트 (정렬: 마감 임박 순) | 30분 |
| S3-3 | `app/page.tsx` — 빈 상태: 매칭 0개 시 전체 정책 마감순 fallback | 20분 |
| S3-4 | `app/policy/[id]/page.tsx` — 정책 상세 (신청 안내, 담당기관 링크) | 40분 |
| S3-5 | `app/policies/page.tsx` — 전체 정책 목록 (지역/나이/종류/마감순 필터) | 40분 |
| S3-6 | `app/(tabs)/내정보/page.tsx` — 비로그인: 로그인 유도 / 로그인: 프로필 수정 링크 | 20분 |

---

## Sprint 4 — 로컬 백과사전 (1.5~2일) `Lane C`

### DB
| # | 태스크 | 예상 |
|---|---|---|
| S4-1 | `004_local_places.sql` — LocalPlace 테이블 (lat, lng, category, subsidy_tags 등) | 15분 |

### 지도 컴포넌트
| # | 태스크 | 예상 |
|---|---|---|
| S4-2 | `components/KakaoMap.tsx` — 카카오맵 JavaScript API 로드 + 마커 렌더링 | 60분 |
| S4-3 | 카테고리 탭 필터 → 지도 마커 + 하단 리스트 동시 필터링 | 30분 |
| S4-4 | 장소 카드 팝업 (이름, 거리, 전화하기, 길찾기) | 20분 |

### 페이지
| # | 태스크 | 예상 |
|---|---|---|
| S4-5 | `app/local/page.tsx` — 지도 뷰 메인 | 30분 |
| S4-6 | `app/local/[id]/page.tsx` — 장소 상세 (지원금 태그, 주민 메모, 가격 정보) | 30분 |
| S4-7 | `app/policy/[id]/page.tsx` — [받았다 ✓] 버튼 → 지원금 유형 판별 → 로컬 백과사전 연결 | 30분 |

---

## Sprint 5 — 관리자 CMS (1일)

| # | 태스크 | 예상 |
|---|---|---|
| S5-1 | `middleware.ts` — `/admin/**` 경로에 `ADMIN_EMAIL`/`ADMIN_PASSWORD` credentials guard | 20분 |
| S5-2 | `app/admin/policies/page.tsx` — 정책 목록 테이블 | 30분 |
| S5-3 | `app/admin/policies/[id]/page.tsx` — 정책 등록/수정 폼 (`region_codes` 필수 입력 표시) | 60분 |
| S5-4 | `app/admin/places/page.tsx` — 장소 목록 테이블 | 20분 |
| S5-5 | `app/admin/places/[id]/page.tsx` — 장소 등록/수정 폼 + [좌표 자동 입력] 버튼 (카카오 로컬 API) | 45분 |

---

## Sprint 6 — 데이터 입력 (1~2일)

| # | 태스크 | 예상 |
|---|---|---|
| S6-1 | `data/seed/policies.json` — 귀농귀촌 정책 20~30개 수집·정리 (옥천군 → 충북 → 중앙부처 순) | 3~4시간 |
| S6-2 | `data/seed/local_places.json` — 장소 30~50곳 수집 (농약사, 농기계, 행정기관 등) | 3~4시간 |
| S6-3 | `scripts/seedPolicies.ts` — Supabase upsert | 20분 |
| S6-4 | `scripts/seedPlaces.ts` — 주소 → 카카오 로컬 API 좌표 변환 + upsert | 30분 |
| S6-5 | 시드 실행 + 관리자 페이지에서 데이터 확인 | 15분 |

---

## Sprint 7 — 수동 검증 + 배포 (0.5~1일)

### 검증 체크리스트 (SPRINT.md 아닌 platform-plan.md §8 참고)
| # | 태스크 | 예상 |
|---|---|---|
| S7-1 | condition_tree AND/OR/NOT 각 케이스 수동 검증 (정책 직접 입력 후 결과 확인) | 30분 |
| S7-2 | 비로그인 홈 → 카카오 로그인 → 프로필 입력 → 맞춤 정책 전체 플로우 | 20분 |
| S7-3 | 재방문 시 폼 없이 맞춤 정책 즉시 표시 확인 | 10분 |
| S7-4 | 옥천군 사용자 → 충청북도 광역 정책 매칭 확인 | 10분 |
| S7-5 | /admin 비인증 접근 → 차단 확인 | 5분 |
| S7-6 | 카테고리 탭 → 지도 마커 + 리스트 동시 필터링 확인 | 10분 |

### 배포
| # | 태스크 | 예상 |
|---|---|---|
| S7-7 | Vercel 프로덕션 배포 | 10분 |
| S7-8 | 카카오 개발자 콘솔 — 배포 도메인 허용 도메인에 추가 | 10분 |
| S7-9 | 프로덕션에서 카카오 로그인 최종 확인 | 10분 |

---

## 병렬 실행 권장 순서

```
Week 1
  Day 1: S0 (세팅) + S1 시작 (인증)
  Day 2: S1 완료 (프로필 폼) || S2 시작 (DB + 매칭 엔진)
  Day 3: S2 계속 (conditionTree, policyMatcher)

Week 2
  Day 4: S2 완료 + S3 시작 (홈 + 정책 페이지) || S4 시작 (로컬 백과)
  Day 5: S3 + S4 병렬 진행
  Day 6: S4 완료 + S5 (관리자)

Week 3
  Day 7-8: S6 (데이터 수집 + 입력) — 가장 오래 걸림, 미리 시작 권장
  Day 9: S7 (검증 + 배포)
```

> **데이터 수집 (S6)은 최대한 빨리 시작하세요.**  
> 코딩과 병렬로 진행할 수 있고, 정책 정보 수집에 실제로 가장 많은 시간이 걸립니다.

---

## 핵심 위험 태스크

| 태스크 | 이유 | 대비 |
|---|---|---|
| S2-6 conditionTree 평가기 | 핵심 로직, 버그 시 정책 누락/오표시 | S7-1에서 반드시 수동 검증 |
| S4-2 KakaoMap 컴포넌트 | Next.js App Router + 카카오맵 SSR 이슈 가능 | `"use client"` 처리, dynamic import |
| S6-1~2 데이터 수집 | 양이 많고 품질 중요 | region_codes 반드시 입력, 마감일 정확히 |
| S0-4 카카오 앱 등록 | 배포 도메인 없으면 OAuth 안 됨 | localhost 먼저 세팅, 배포 도메인 나오면 추가 |
