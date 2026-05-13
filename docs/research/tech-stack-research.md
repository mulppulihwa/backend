# 귀농인 정책 매칭 웹앱 — 기술 스택 리서치

> 웹 기반 / 한국 시장 / 시니어 사용자 / 공공 API 연동 기준

---

## 1. 프론트엔드 프레임워크

### 추천: Next.js 14 (App Router)

**선택 근거:**
- **SEO**: 정책 정보는 공개 자료이므로 검색 노출 중요. SSR/Static Generation으로 "귀농 지원금" 검색 상위 노출 가능
- **API 통합**: 보조금24, 복지로 API 호출을 Next.js 서버 사이드에서 처리 → CORS 문제 없음
- **배포**: Vercel 완벽 통합 (GitHub push → 자동 배포)
- **한국 커뮤니티**: Vue/Nuxt 대비 압도적으로 풍부

**기술 상세:**
```
Frontend: Next.js 14 (App Router)
UI: React 19
Styling: Tailwind CSS v4
상태관리: TanStack Query (서버) + Zustand (클라이언트)
폼: React Hook Form + Zod
```

**시니어 친화적 UI:**
- 폰트: 기본 `text-lg` 이상 (16px+), Pretendard 또는 Noto Sans KR
- 색상 대비: WCAG AAA 준수 (배경-텍스트 명도차 ≥ 7:1)
- 터치 타겟: 최소 48×48px
- 애니메이션: `prefers-reduced-motion` 존중

---

## 2. 백엔드 프레임워크

> **⚠️ 2026-05-08 업데이트:** v1 스코프 확정 후 FastAPI → **Next.js API Routes**로 변경.  
> FastAPI는 v1.5+ (Celery 배치 작업, 크롤링 파이프라인) 시점에 별도 마이크로서비스로 추가.  
> 아래 비교표는 참고용으로 유지.

### 최종 결정: Next.js API Routes (v1)

**이유:**
- v1 스코프에 백그라운드 작업 없음 (알림·크롤링 모두 v1.5+ 보류)
- Vercel 단일 배포로 Railway + Redis 인프라 불필요 (월 $0~20 절감)
- TypeScript 코드베이스 일원화 — 프론트엔드와 타입 공유 가능
- NextAuth.js Kakao provider가 Next.js에서 최적으로 동작
- 정책 매칭 로직은 SQL + 서버사이드 TS로 충분 (AI/LLM 불필요)

**FastAPI 재검토 시점:** 카카오 알림톡 배치 발송 또는 공공 API 자동 동기화 구현 시

---

### (참고) FastAPI vs Next.js API Routes 비교

### 참고: FastAPI (Python 3.11+)

| 기준 | FastAPI | Django | Express |
|------|---------|--------|---------|
| 규칙 기반 필터링 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 내장 Admin | ✗ (SQLAdmin으로 보완) | ⭐⭐⭐⭐⭐ | ✗ |
| 비동기 지원 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 크롤링/데이터 처리 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 자동 API 문서(Swagger) | ✅ | ✗ | ✗ |

**FastAPI 선택 이유:**
- Python 생태계 → 크롤링(BeautifulSoup, Playwright)·데이터 처리에 최적
- 비동기 네이티브 → 카카오 알림톡 + 공공 API 호출 동시 처리
- SQLAdmin으로 관리자 패널 구축 가능 (Django Admin과 유사)

**기술 상세:**
```
Framework: FastAPI (Python 3.11+)
ORM: SQLAlchemy 2.0 + Alembic (마이그레이션)
DB: PostgreSQL 15+ (Supabase)
검증: Pydantic v2
Admin: SQLAdmin
비동기 태스크: Celery + Redis
HTTP 클라이언트: httpx (비동기)
```

---

## 3. 한국 특화 기술

### 3-1. 카카오 알림톡 API

```
1단계: 카카오 비즈니스 계정 개설 → 알림톡 채널 신청
        - 심사: 7~10일 (공익 목적 신속처리 요청 가능)
        - 발송료: 건당 약 10~30원

2단계: 알림톡 템플릿 등록 (심사 필요)
        예시 템플릿:
        ---
        #{userName}님, 
        정책 신청 마감이 #{daysLeft}일 남았습니다!
        [#{policyName}]
        신청: #{applyLink}
        ---

3단계: FastAPI에서 httpx로 직접 API 호출
        (Python 공식 SDK 없음 → requests/httpx 직접 구현)
```

**FastAPI 통합 예제:**
```python
import httpx

class KakaoNotificationService:
    async def send_deadline_alert(
        self, user_phone: str, policy_name: str, days_left: int, apply_url: str
    ):
        payload = {
            "plus_friend_id": self.sender_id,
            "template_id": "POLICY_DEADLINE_ALERT",
            "recipient_number": user_phone,
            "message_data": {
                "policyName": policy_name,
                "daysLeft": days_left,
                "applyLink": apply_url
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://kapi.kakao.com/v2/notification/send",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload
            )
        return response.json()
```

---

### 3-2. 공공데이터 API

| API | 출처 | 활용도 | 비고 |
|-----|------|--------|------|
| **보조금24** | 행정안전부 | 🟢 필수 | 중앙 + 지자체 혜택 통합 |
| **복지로** | 한국사회보장정보원 | 🟢 필수 | 노인 복지 상세 정보 |
| **농사로** | 농촌진흥청 | 🟡 보조 | 농업 기술 정보 |
| **워크넷** | 고용노동부 | 🟡 보조 | 귀농인 교육 프로그램 |

**발급 절차:** data.go.kr 회원가입 → 각 API 신청 → 담당 기관 승인 (1~3일)

**⚠️ 상업 이용 여부 사전 확인 필수** (행정안전부 문의: subsidy24@mois.go.kr)

---

## 4. 데이터 파이프라인

### 정책 데이터 흐름

```
1. 공공 API (보조금24, 복지로) → 자동 동기화 (주 1회 Celery)
2. 귀농귀촌종합센터 (returnfarm.com) → 크롤링 (월 1회)
3. 지자체 홈페이지 → 선택적 크롤링
4. 정규화 + PostgreSQL 저장 + 중복 제거
```

### 크롤링 도구 선택

| 도구 | 용도 | 단계 |
|------|------|------|
| **requests + BeautifulSoup4** | 정적 HTML | MVP (즉시) |
| **Playwright** | JS 렌더링 필요 사이트 | v1.5+ |
| Scrapy | 대규모 크롤링 | 불필요 (과함) |

**MVP 구현:**
```python
import httpx
from bs4 import BeautifulSoup

class ReturnFarmCrawler:
    async def crawl_policies(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.returnfarm.com/bbs/board.php?bo_table=policy"
            )
        soup = BeautifulSoup(response.text, "html.parser")
        policies = []
        for item in soup.select("table.list tr"):
            cells = item.find_all("td")
            if len(cells) < 4:
                continue
            policies.append({
                "title": cells[0].get_text(strip=True),
                "apply_end_date": cells[2].get_text(strip=True),
                "source": "returnfarm"
            })
        return policies
```

**데이터 정규화 (출처별 필드명 통일):**
```python
def normalize_policy(raw: dict) -> dict:
    return {
        "title": raw.get("제목") or raw.get("name"),
        "description": raw.get("내용") or raw.get("description"),
        "amount": parse_amount(raw.get("지원금액")),
        "apply_end_date": parse_date(raw.get("신청마감")),
        "region_codes": extract_region_codes(raw.get("지역")),
        "source": raw.get("출처")
    }
```

---

## 5. 규칙 기반 정책 매칭 엔진

### 방식 비교

| 방식 | 추천 단계 | 이유 |
|------|-----------|------|
| **SQL WHERE 필터** | ✅ MVP | 간단, 빠름, 디버깅 쉬움 |
| **전용 Rules Engine** | △ 규칙 50개 초과 시 | 오버헤드 높음 |
| **LLM (Claude API)** | ✅ 사용자 대화용 | 자연어 해석, 유연함 |
| **하이브리드 (LLM + SQL)** | ✅ 최종 추천 | 정확도 + 유연성 동시 확보 |

### 추천: 하이브리드 아키텍처

```
사용자 자연어 입력 ("60세, 올해 귀농")
    ↓
Claude API — Function Calling으로 정보 추출
    { age: 60, is_new_farmer: true, region: "옥천군" }
    ↓
규칙 기반 SQL 쿼리 → 정책 매칭
    ↓
Claude API — 결과를 자연어로 친절하게 설명
    ↓
사용자에게 표시
```

**구현 (Claude API + FastAPI):**
```python
from anthropic import Anthropic

client = Anthropic()

def extract_user_profile(user_message: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=[{
            "name": "extract_profile",
            "description": "사용자 프로필 정보 추출",
            "input_schema": {
                "type": "object",
                "properties": {
                    "age": {"type": "integer"},
                    "region": {"type": "string"},
                    "is_new_farmer": {"type": "boolean"},
                    "income_level": {
                        "type": "string",
                        "enum": ["기초수급", "차상위", "일반"]
                    }
                },
                "required": ["age", "region"]
            }
        }],
        messages=[{"role": "user", "content": user_message}]
    )
    for block in response.content:
        if hasattr(block, "input"):
            return block.input
    return {}

async def match_policies(profile: dict):
    query = db.query(Policy).filter(
        and_(
            Policy.min_age <= profile["age"],
            Policy.max_age >= profile["age"],
            Policy.region_codes.contains(profile["region"])
        )
    )
    if profile.get("is_new_farmer"):
        query = query.filter(Policy.occupation_tags.contains("귀농"))
    return query.all()
```

---

## 6. 알림 스케줄링 아키텍처

```
아키텍처:
FastAPI ←→ Celery Beat (스케줄러) → Celery Worker → Kakao 알림톡
                                        ↕
                                   PostgreSQL
```

**Celery 설정:**
```python
from celery.schedules import crontab

app.conf.timezone = "Asia/Seoul"  # 한국 시간대 필수

app.conf.beat_schedule = {
    "send-deadline-alerts": {
        "task": "tasks.send_deadline_alerts",
        "schedule": crontab(hour=22, minute=0),  # 매일 밤 10시
    },
    "sync-subsidy-policies": {
        "task": "tasks.sync_subsidy_policies",
        "schedule": crontab(hour=2, minute=0, day_of_week=4),  # 매주 목 오전 2시
    }
}
```

**D-7 / D-1 알림 로직:**
```python
@celery_app.task
def send_deadline_alerts():
    today = datetime.now().date()
    for days_left in [7, 1]:
        policies = db.query(Policy).filter(
            Policy.apply_end_date == today + timedelta(days=days_left)
        ).all()
        for policy in policies:
            for user in get_interested_users(policy.id):
                kakao_service.send_deadline_alert(
                    phone=user.phone,
                    policy_name=policy.title,
                    days_left=days_left,
                    apply_url=policy.apply_url
                )
```

---

## 7. 접근성 — 시니어 TTS (음성 읽기)

### 추천: Web Speech API + Server-side TTS 폴백

| 방식 | 장점 | 단점 | 단계 |
|------|------|------|------|
| **Web Speech API** | 무료, 지연 없음 | 브라우저 의존, 음질 불안정 | MVP |
| **NAVER Clova TTS** | 자연스러운 한국어, 월 200만자 무료 | 인터넷 필요 | v1.5 |
| **Google Cloud TTS** | 고음질, 감정 표현 | 유료 ($20/100만자) | v2 |

**Next.js 구현 (Web Speech API):**
```typescript
const handleSpeak = (text: string) => {
  const synth = window.speechSynthesis;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'ko-KR';
  utterance.rate = 0.85;  // 천천히 (시니어 배려)
  synth.speak(utterance);
};

// 버튼 (최소 48px 높이)
<button
  onClick={() => handleSpeak(`${policy.title}. ${policy.description}`)}
  className="w-full py-4 text-xl font-bold bg-blue-600 text-white rounded-lg"
>
  🔊 읽어주기
</button>
```

---

## 8. 배포

### 추천: Vercel + Railway + Supabase

```
사용자
  ↓
Vercel (Next.js / CDN)
  ↓
Railway (FastAPI + Celery)
  ↓
Supabase (PostgreSQL)
```

| 플랫폼 | 역할 | 월 비용 |
|--------|------|---------|
| **Vercel** | 프론트엔드 | $0~20 |
| **Railway** | 백엔드 API + Celery | $0~20 |
| **Supabase** | PostgreSQL | $0~25 |
| **Upstash** | Redis (Celery 브로커) | $0 무료 티어 |

**월 총 비용: $30~50 + 카카오 알림톡 비용 (건당 10~30원)**

**⚠️ Vercel, Railway 결제: 해외 신용카드 필요 (국내 체크카드 불가)**

### 대안: AWS 서울 리전 (사용자 10,000명+ 시 권장)
- ECS (Fargate) + RDS + CloudFront
- 월 비용: $50~150
- 장점: 서울 리전 → 최저 지연, 법인 크레딧 활용 가능

---

## 8-B. Next.js 백엔드 추가 리서치 (2026-05-08)

### Supabase JS Client — 서버사이드 패턴

Next.js App Router에서는 클라이언트/서버 두 가지 Supabase 인스턴스가 필요하다.

```
패키지: @supabase/supabase-js @supabase/ssr

lib/supabase/server.ts   ← API Routes, Server Components에서 사용 (service role key)
lib/supabase/client.ts   ← Client Components에서 사용 (anon key)
```

**서버사이드 (API Route):**
```ts
import { createClient } from '@supabase/supabase-js'

export function createServerClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!  // 절대 클라이언트에 노출 금지
  )
}
```

**RLS(Row Level Security) 전략:**
- 학교 프로젝트 규모에서는 서비스 롤 키를 API Routes에서만 사용하고
  RLS는 off로 두는 것이 구현 속도 빠름
- 프로덕션 확장 시 RLS 정책 추가:
  ```sql
  ALTER TABLE users ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "users can read own profile"
    ON users FOR SELECT USING (auth.uid()::text = id);
  ```

---

### Next.js App Router API Route 패턴

```
app/
  api/
    auth/[...nextauth]/route.ts    ← NextAuth handler
    policies/
      route.ts                    ← GET /api/policies (목록)
      match/route.ts              ← GET /api/policies/match (맞춤 매칭)
      preview/route.ts            ← GET /api/policies/preview (비로그인 3개)
      [id]/route.ts               ← GET /api/policies/[id] (상세)
    profile/route.ts              ← GET/POST /api/profile
    places/
      route.ts                    ← GET /api/places
      [id]/route.ts               ← GET /api/places/[id]
      geocode/route.ts            ← POST /api/places/geocode (좌표 변환)
    regions/route.ts              ← GET /api/regions (드롭다운용)
    admin/
      policies/
        route.ts                  ← GET/POST
        [id]/route.ts             ← PUT/DELETE
      places/
        route.ts                  ← GET/POST
        [id]/route.ts             ← PUT/DELETE
```

**Route Handler 기본 패턴:**
```ts
// app/api/policies/match/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { matchPolicies } from '@/lib/policyMatcher'

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const policies = await matchPolicies(session.user.profile)
  return NextResponse.json({ policies })
}
```

---

### Vercel Cron (알림 기능 v1.5 준비)

알림 기능이 v1.5로 확정되면 Celery 없이 Vercel Cron으로 대체 가능.

```json
// vercel.json
{
  "crons": [
    {
      "path": "/api/cron/policy-alerts",
      "schedule": "0 13 * * *"   // 매일 22시 KST (UTC+9 = UTC 13시)
    }
  ]
}
```

제약: Vercel Cron은 Hobby 플랜에서 1개, Pro에서 무제한.  
실행 시간 제한: 최대 60초 (Hobby) / 900초 (Pro).  
학교 프로젝트는 Hobby로 충분. 사용자 10,000명 이상이면 Railway + Celery 전환 검토.

---

### PostgreSQL 타입 안전성 — DB 타입 자동 생성

Supabase CLI로 DB 타입을 TypeScript 타입으로 자동 생성:
```bash
npx supabase gen types typescript --project-id <프로젝트ID> > lib/database.types.ts
```

생성된 타입을 Supabase 클라이언트에 주입:
```ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/lib/database.types'

export const supabase = createClient<Database>(url, key)
// 이후 supabase.from('policies').select()에 자동 타입 추론 적용
```

---

## 9. 종합 기술 스택 (최종)

```yaml
Frontend:
  - Next.js 14 (App Router)
  - React 19 + Tailwind CSS v4
  - TanStack Query + Zustand
  - React Hook Form + Zod
  - Web Speech API (TTS)

Backend:
  - FastAPI (Python 3.11+)
  - SQLAlchemy 2.0 + Alembic
  - Pydantic v2
  - Celery + Redis (스케줄링)
  - httpx (비동기 HTTP)
  - BeautifulSoup4 / Playwright (크롤링)

AI/LLM:
  - Claude API (claude-sonnet-4-6)
  - Function Calling (사용자 정보 추출)
  - 프롬프트 캐싱 적용 (비용 절감)

Database:
  - PostgreSQL 15+ (Supabase)

External APIs:
  - 보조금24 (행정안전부)
  - 복지로 (한국사회보장정보원)
  - 카카오 알림톡
  - NAVER Clova TTS (v1.5)

Infra:
  - Vercel (프론트)
  - Railway (백엔드)
  - Supabase (DB)
  - Upstash Redis (Celery 브로커)

DevOps:
  - GitHub + GitHub Actions (CI/CD)
  - Docker (컨테이너화)
  - Sentry (에러 모니터링)
```

---

## 10. 기술적 디벨롭 포인트 (발전 가능 영역)

### 단기 (MVP → v1.5)
| 영역 | 현재 | 발전 방향 |
|------|------|-----------|
| 매칭 | SQL 필터링 | Claude Function Calling 하이브리드 |
| 알림 | D-7/D-1 고정 | 사용자별 관심 정책 맞춤 알림 |
| 크롤링 | BeautifulSoup 정적 | Playwright 동적 크롤링 |
| TTS | 브라우저 Web Speech API | NAVER Clova TTS 고음질 |
| 관리자 | SQLAdmin 기본 | 정책 승인 워크플로우 + 크롤링 모니터링 |

### 중기 (v2.0+)
| 영역 | 발전 방향 |
|------|-----------|
| AI 매칭 | 사용자 이용 이력 기반 추천 (협업 필터링) |
| 정책 데이터 | 자동 변경 감지 + 알림 (정책 개정 추적) |
| 대화 인터페이스 | 음성 입력 (Web Speech API STT) |
| 신청 지원 | 서류 체크리스트 자동 생성, 신청 대행 링크 |
| 모바일 | PWA 전환 (홈화면 추가, 오프라인 캐싱) |

---

## 11. 법적 고려사항

### 개인정보보호법 (PIPA)
- 나이·지역·연락처 수집 시 개인정보 처리방침 공개 필수
- 알림톡 발송: 사용자 동의 후 발송 (수신 거부 기능 필수)

### 면책 조항
```
"본 서비스는 공공 정책 정보 제공만 목적이며, 실제 신청 자격은
담당 기관이 최종 판단합니다. 부정확한 정보로 인한 손해는
책임지지 않습니다."
```

### 공공 API 이용 약관
- 상업적 이용 여부 사전 확인 (보조금24: 행정안전부 문의)
- 출처 명시 의무

---

## 12. 마이그레이션 경로

```
v1.0 (3개월, MVP)
└─ AI 챗봇 + SQL 정책 매칭 + 보조금24/복지로 API

v1.5 (6개월)
└─ 카카오 알림톡 + NAVER Clova TTS + Playwright 크롤링

v2.0 (9개월)
└─ 회원가입 + 즐겨찾기 + PWA + 음성 입력(STT)

v3.0+ (12개월+)
└─ 지자체 파트너십 + 신청 대행 + 모바일 앱 (React Native)
```
