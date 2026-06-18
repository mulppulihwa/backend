# 시스템 아키텍처

```mermaid
graph LR
    subgraph FE["프론트엔드"]
        FE1["React + Vite<br/>TypeScript"]
    end

    subgraph BE["백엔드"]
        BE1["Python · Django<br/>Django REST Framework"]
        BE2["JWT 로그인"]
    end

    subgraph DBG["데이터베이스"]
        DB1["PostgreSQL<br/>(Supabase)"]
        DB2["Redis<br/>(캐시)"]
    end

    subgraph EXTAPI["외부 API"]
        E1["카카오<br/>로그인 · 지도 · 주소 검색"]
        E2["복지로 · 그린대로<br/>정책 정보"]
        E3["Anthropic Claude<br/>AI 정책 분석"]
    end

    subgraph DEPLOY["배포"]
        D1["Netlify<br/>(프론트엔드)"]
        D2["Railway<br/>(백엔드 · Gunicorn)"]
    end

    FE <-->|화면에 필요한 정보를 요청하고 응답받음| BE
    FE <-->|카카오 로그인 · 지도 · 주소 검색을 화면에서 직접 이용| EXTAPI
    BE <-->|회원 · 정책 · 사용처 정보를 저장하고 불러옴| DBG
    BE <-->|정책 정보를 가져오고 AI에게 분석을 요청함| EXTAPI
    D1 -. 여기서 실행됨 .- FE
    D2 -. 여기서 실행됨 .- BE

    style FE fill:#EDE7FF,stroke:#9B8AFB,stroke-width:2px
    style BE fill:#DCEEFF,stroke:#6FA8DC,stroke-width:2px
    style DBG fill:#DFF5E1,stroke:#6FCF7E,stroke-width:2px
    style EXTAPI fill:#FFEFD5,stroke:#F2A65A,stroke-width:2px
    style DEPLOY fill:#F0F0F0,stroke:#AAAAAA,stroke-width:2px
```

- **프론트엔드**: React + Vite(TypeScript), React Router — Netlify에 배포
- **백엔드**: Python + Django(Django REST Framework), JWT 로그인 — Railway에 배포(Gunicorn)
- **데이터베이스**: PostgreSQL(Supabase), Redis(캐시)
- **외부 API**: 카카오(로그인·지도·주소 검색), 복지로·그린대로(정책 정보), Anthropic Claude(AI 정책 분석)

## 기능 흐름: 정책 수집

정책 추천에 쓰이는 정책 데이터는 사용자가 요청하는 시점이 아니라, **그 전에
미리 준비**된다. 정기적으로(또는 관리자가 실행할 때) 아래 과정을 거쳐
데이터베이스에 정책이 쌓인다.

```mermaid
sequenceDiagram
    participant 외부 as 외부 정책 사이트<br/>(복지로 · 그린대로)
    participant 서버 as 서버 (백엔드)
    participant AI as AI (Claude)
    participant DB as 데이터베이스
    actor 관리자

    서버->>외부: 최신 정책 공고 목록 요청
    외부-->>서버: 정책 공고문 응답
    서버->>AI: 공고문 내용 분석 요청<br/>(누가 신청 가능한지 · 마감일 · 지원금액)
    AI-->>서버: 분석 결과 + 확신도 응답
    alt 분석 결과를 충분히 신뢰할 수 있음
        서버->>DB: 정책 저장 → 바로 추천 대상에 포함
    else 확신도가 낮음
        서버->>DB: 정책 저장 → 추천 대상에서 제외(검토 대기)
        관리자->>DB: 내용 확인 후 노출 여부 결정
    end
```

- 옥천군청 정책처럼 **지자체 홈페이지에 올라온 정책은 관리자가 공고문 원문을
  직접 입력**한다. 복지로·그린대로는 API 응답이 이미 JSON이라 서버가 바로 AI에게
  분석을 요청하지만, 옥천군청·수동입력 공고문은 줄글 형태이므로 관리자가 입력한
  뒤 같은 AI 분석 단계를 거쳐 구조화된 정보로 변환된다. 이렇게 만들어진 정책은
  "옥천 지역 큐레이션"으로 분류돼 추천 시 가장 먼저 보여준다.
- "확신도가 낮음"으로 분류된 정책은 화면에 노출되지 않고, 관리자가 검토해서
  내용이 맞으면 노출하도록 바꿀 수 있다.

## 기능 흐름: 정책 추천

```mermaid
sequenceDiagram
    actor 사용자
    participant 화면 as 화면 (프론트엔드)
    participant 서버 as 서버 (백엔드)
    participant DB as 데이터베이스

    사용자->>화면: '내 맞춤 정책' 메뉴 클릭
    화면->>서버: 로그인 정보와 함께 맞춤 정책 요청
    서버->>DB: 내 프로필(나이 · 직업 · 소득 · 거주 이력 등) 조회
    DB-->>서버: 프로필 정보 응답
    서버->>DB: 프로필 조건에 맞는 정책 후보 조회
    DB-->>서버: 정책 후보 목록 응답
    서버->>서버: 세부 조건 한 번 더 확인 + 마감임박/지역 우선순위로 정렬
    alt 맞는 정책이 하나도 없음
        서버->>DB: 최신 정책으로 대체 조회
        DB-->>서버: 최신 정책 목록 응답
    end
    서버-->>화면: 맞춤 정책 목록(최대 5개) + 마감일 · 추천 이유
    화면-->>사용자: 정책 카드로 화면에 표시
```

- 이 흐름에서 **AI는 직접 호출되지 않는다.** 정책 데이터(자격 조건, 마감일 등)는
  복지로·그린대로에서 정기적으로 가져올 때 AI가 미리 분석해 데이터베이스에
  저장해 두고, 추천 시에는 이미 정리된 데이터에서 조건만 비교한다.
- "세부 조건 확인"은 단순 나이/지역/소득 조건으로 못 거르는 복합 조건(예: "귀농
  3년 이내이면서 농지 보유")을 정책별로 한 번 더 검사하는 단계다.

### 1차/2차 필터링 개념도

```mermaid
flowchart TD
    A["전체 정책"] --> B["1차 필터링<br/>기본 조건<br/>(나이 · 소득 · 지역 · 장애여부)"]
    B --> C["후보 정책"]
    C --> D["2차 필터링<br/>정책별 세부 조건<br/>(AI가 분석한 자격 조건)"]
    D --> E["최종 추천<br/>최대 5개, 마감임박/우선순위 정렬"]
```

**왜 2단계가 필요한가 — 예시**

사용자 프로필: *32세 · 귀농 준비 중 · 농지 미보유 · 옥천 거주 1년차*

| 단계 | "청년 귀농 정착 지원금" 정책 | 결과 |
|---|---|---|
| 1차 필터 (만 18~40세 대상) | 32세 → 조건 만족 | ✅ 통과 |
| 2차 필터 (농지 보유자만 신청 가능) | 농지 미보유 | ❌ 제외 |

나이만 보면 추천될 정책이지만, 실제로는 신청 자격이 없는 "그림의 떡" 정책이다. 2차
필터링이 이런 정책을 걸러내서 진짜 신청 가능한 정책만 추천 목록에 남긴다.

### 매칭 로직 코드 (`lib/matching/policy_matcher.py`)

**1차 필터링** — DB 쿼리로 나이 · 직업 · 소득 · 장애 여부 등 단순 조건을 먼저 좁힌다.

```python
qs = Policy.objects.filter(
    is_active=True,
    min_age__lte=age,
    max_age__gte=age,
)

if occ_tags:
    # occupation_tags 없는 정책(전체 대상)도 포함
    qs = qs.filter(occupation_tags__exact=[]) | qs.filter(
        occupation_tags__overlap=occ_tags
    )

if income:
    # income_level 없는 정책(전체 소득 대상)도 포함
    qs = qs.filter(income_level__exact=[]) | qs.filter(
        income_level__contains=[income]
    )
```

**2차 필터링** — 1차로 못 거르는 복합 조건은 정책별 `condition_tree`(AND/OR/NOT/LEAF로
구성된 JSON, AI 분석 단계에서 함께 생성됨)를 사용자 프로필에 대해 재귀적으로 평가한다.
평가 중 오류가 나면 정책을 제외하지 않고 통과시킨다(안전한 기본값).

```python
matched = [p for p in qs if evaluate_tree(p.condition_tree, user_profile)]
```

**정렬** — 옥천 큐레이션(옥천군청 · 수동입력) > 귀농센터 > 복지로 순으로 먼저 묶고,
같은 출처 안에서는 마감일이 빠른 정책을 앞에 둔다. 마감일이 없는 정책은 가장 뒤로 보낸다.

```python
SOURCE_PRIORITY = {'옥천군청': 0, '수동입력': 0, '귀농센터': 1, '복지로': 2}

def sort_key(p: Policy):
    source_rank = SOURCE_PRIORITY.get(p.source, len(SOURCE_PRIORITY))
    if p.apply_end_date:
        days_left = (p.apply_end_date - today).days
        return (source_rank, 0, days_left)
    return (source_rank, 1, 0)

matched.sort(key=sort_key)
```

**대체(fallback)** — 위 과정을 거쳐 매칭된 정책이 0건이면, 가장 최근에 등록된 활성
정책으로 대체한다(`fallback: true`로 응답에 표시되어 프론트에서 "맞춤 정책은 없지만
최신 정책을 보여드려요" 처럼 안내할 수 있다).

```python
if not matched:
    matched = Policy.objects.filter(is_active=True).order_by('-created_at')[:MATCH_LIMIT]
```

## 상세 구성 (개발자용)

- **프론트엔드**: 로그인(카카오 OAuth), 지도(카카오맵 SDK)·주소검색(다음 Postcode)은
  프론트에서 직접 외부 SDK를 호출하고, 그 외 데이터는 백엔드 REST API를 통해 가져온다.
- **백엔드 (Django/DRF, Railway 배포)**
  - `apps/users`: 카카오 로그인 콜백 처리, 프로필, 내가 진단받은 정책 관리
  - `apps/policies`: 사용자 프로필 기반 정책 매칭(`lib/matching/policy_matcher`),
    정책 목록/상세 조회
  - `apps/places`: 사용처(LocalPlace) CRUD, 등록 시 주소→좌표 변환
    (`lib/services/geocoding`, 카카오 로컬 API 폴백)
  - `apps/regions`: 지역 정보
  - `lib/sync/adapters`: 복지로·그린대로(귀농센터) 정책 수집 어댑터 —
    management command(`sync_bokjiro`, `sync_greendaero`)로 주기 실행
  - `lib/parsing`: Anthropic Claude API를 이용해 정책/준비물 텍스트를 구조화 데이터로 파싱
- **DB**: Supabase(Postgres) — 정책, 체크리스트, 사용처, 사용자, 지역 등 저장
- **정책 출처(source)**: `복지로` / `귀농센터`(그린대로) / `옥천군청`(수동 큐레이션) /
  `수동입력` — 매칭 결과 정렬 시 옥천 큐레이션(`옥천군청`/`수동입력`)이 최우선 노출됨
  (`SOURCE_PRIORITY`, `lib/matching/policy_matcher.py`)
