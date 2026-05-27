# 정책 매칭 방식 비교 연구

> **최종 결정: Pipeline A 채택 (2026-05-08)**  
> SQL 1차 필터 + Python condition_tree 평가. LLM은 저장 단계(공고문 파싱)에서만 사용.  
> 결정 근거: §10 파이프라인 비교 참고.

---

## 1. SQL WHERE 필터 (이진 매칭)

조건을 모두 충족해야만 결과에 나오는 방식.

```sql
SELECT * FROM policies
WHERE min_age <= 60 AND max_age >= 60
  AND region_codes @> '["충북 옥천군"]'
  AND occupation_tags && '["귀농"]'
```

**장점:** 빠름, 예측 가능, 디버깅 쉬움  
**단점:** 조건 하나라도 안 맞으면 결과에서 완전히 탈락 → "아무 결과 없음" 상황 발생 가능

---

## 2. 스코어링 / 부분 매칭

조건마다 점수를 매겨 순위 기반 추천. 완전히 안 맞아도 "거의 해당됨"으로 표시 가능.

```
정책 A:
  나이 조건 충족    → +30점
  지역 조건 충족    → +30점
  소득 조건 모름    → +0점 (not null이 아니라 skip)
  직종 조건 충족    → +40점
  총점: 100/100 → "해당됨"

정책 B:
  나이 조건 충족    → +30점
  지역: 전국 대상   → +30점
  직종 조건 미충족  → +0점
  총점: 60/100 → "확인 필요" 표시
```

**장점:** 결과가 풍부해짐, "아무것도 없음" 방지  
**단점:** 점수 가중치 설계가 어려움

---

## 3. 단계적 좁히기 (Wizard / Funnel)

질문을 순서대로 하면서 결과를 점점 좁혀가는 방식. 정책 포털에서 흔히 씀.

```
Q1. 지역 선택 → 전국 정책 300개 → 충북 정책 40개
Q2. 나이 입력  → 40개 → 25개
Q3. 귀농 여부  → 25개 → 12개
Q4. 소득 구간  → 12개 → 7개
```

**장점:** 사용자가 "좁혀지는 과정"을 직접 느낌, 결과가 직관적  
**단점:** 순서에 따라 결과가 달라질 수 있음

---

## 4. 태그 겹침 수 (Overlap Count)

사용자 프로필 태그와 정책 태그가 얼마나 겹치는지만 계산. 설계가 단순함.

```
사용자 태그: [60대, 귀농, 충북, 독거, 기초수급]

정책 A 태그: [60대, 귀농, 충북]   → 겹침 3개 ✅
정책 B 태그: [귀농, 전국]         → 겹침 1개 △
정책 C 태그: [20대, 창업]         → 겹침 0개 ❌
```

**장점:** 구현 초간단, 정책 DB 설계가 쉬움  
**단점:** 태그 정교함에 전적으로 의존

---

## 5. 벡터 유사도 검색 (Semantic Search)

정책 설명문을 임베딩 벡터로 변환해 저장. 사용자 상황 텍스트와 유사한 정책을 검색.

```
사용자: "65세 남성, 올해 충북 옥천으로 귀농, 소 10마리 키움"
    ↓ 임베딩
[0.23, -0.81, 0.44, ...] (1536차원 벡터)
    ↓ cosine similarity
정책 DB에서 가장 가까운 벡터의 정책들 반환
```

**장점:** 조건이 딱 안 맞아도 "의미적으로 비슷한" 정책 발견  
**단점:** OpenAI Embeddings 등 외부 API 필요, 설명이 잘 작성되어 있어야 함

---

## 6. LLM 직접 판단

정책 조건 전문을 LLM에 넘기고 "이 사람에게 해당되나요?" 판단 위임.

```
prompt: "다음 사람에게 이 정책이 해당되는지 판단해줘.
사람: 65세, 충북 옥천, 귀농 1년차, 기초수급자
정책: [정책 조건 전문]
→ 해당 여부: YES/NO + 이유"
```

**장점:** 복잡하고 모호한 조건도 해석 가능 ("농업에 준하는 활동" 같은 문구)  
**단점:** 느림, 비용 발생, 정책 수 많으면 API 호출 폭증

---

## 방식 선택 가이드

| 방식 | 구현 난이도 | 결과 품질 | 적합한 상황 |
|---|---|---|---|
| SQL WHERE | ★☆☆ | 보통 (조건 딱 맞을 때만) | MVP, 조건이 명확한 정책 |
| 스코어링 | ★★☆ | 좋음 | 결과가 너무 없거나 너무 많을 때 |
| Wizard | ★☆☆ | 좋음 | 입력 단계가 자연스러워야 할 때 |
| 태그 겹침 | ★☆☆ | 보통 | DB 설계 단순하게 가고 싶을 때 |
| 벡터 검색 | ★★★ | 매우 좋음 | 정책 설명이 자연어 중심일 때 |
| LLM 판단 | ★★☆ | 매우 좋음 | 조건이 모호하거나 예외가 많을 때 |

---

## MVP 추천 조합

**SQL WHERE (필수 조건 하드 필터) + 스코어링 (선택 조건 순위)**

- 나이·지역처럼 명확한 조건은 SQL WHERE로 하드 필터
- 소득·가구 유형 등 선택 입력 조건은 점수로 환산해 정렬
- 결과를 "해당됨" / "확인 필요" 두 그룹으로 나눠 표시
- 벡터 검색·LLM 판단은 정책 수가 늘고 조건이 복잡해질 때 도입 검토

---

## 7. 정책 DB 저장 방식 — JSONB + 배열 필드

### JSON vs JSONB

PostgreSQL에는 JSON과 JSONB 두 가지 타입이 있다.

| | JSON | JSONB |
|---|---|---|
| 저장 방식 | 텍스트 그대로 | 바이너리 파싱해서 저장 |
| 인덱스 | 불가 | GIN 인덱스 가능 |
| 검색 속도 | 느림 (매번 파싱) | 빠름 |
| 쓰기 속도 | 빠름 | 약간 느림 (파싱 비용) |
| 사용 권장 | 로그 보관 등 단순 저장 | 검색·필터가 필요한 경우 |

**→ 우리 서비스는 condition_tree를 검색에 쓰지 않고 서버에서 읽어서 평가하므로 JSONB와 JSON 둘 다 가능. 단, 향후 DB 레벨 조회 가능성을 위해 JSONB 권장.**

---

### 정책 필드 설계 — 구조화 필드 + JSONB 혼합

단순 조건은 구조화 필드(배열)로, 복합 조건은 JSONB로 분리.

```
policies 테이블

── 구조화 필드 (1차 SQL 필터용) ─────────────────
  min_age        INTEGER          나이 하한
  max_age        INTEGER          나이 상한
  region_codes   TEXT[]           적용 지역 코드 배열
  occupation_tags TEXT[]          직종 태그 배열
  income_level   TEXT[]           소득 기준 배열
  household_type TEXT[]           가구 유형 배열
  move_status    TEXT[]           이주 상태 배열

── JSONB 필드 (2차 서버 평가용) ──────────────────
  condition_tree JSONB NULL       복합 조건 트리
                                  NULL이면 구조화 필드만으로 판단
```

**왜 둘을 나눴나?**

```
구조화 필드  → SQL 인덱스 탐색 가능, 빠름
             → 단순 AND 조건만 표현 가능

JSONB       → OR, NOT 등 복합 조건 표현 가능
             → 인덱스 타기 어려워서 후처리(서버)에서 평가
```

즉, SQL로 후보를 빠르게 좁히고, JSONB로 정밀하게 걸러내는 2단계 구조.

---

### 배열 필드와 GIN 인덱스

PostgreSQL 배열 필드에 `&&` (겹침) 연산자를 쓸 때 GIN 인덱스 없이는 전체 테이블 스캔이 발생한다.

```sql
-- GIN 인덱스 없이
SELECT * FROM policies WHERE region_codes && ARRAY['43720', '43'];
-- → 정책 10만 개면 10만 행 전부 스캔

-- GIN 인덱스 있으면
-- → 인덱스로 바로 해당 행만 탐색
```

**GIN 인덱스 생성:**
```sql
CREATE INDEX idx_policies_region_codes
  ON policies USING GIN (region_codes);

CREATE INDEX idx_policies_occupation_tags
  ON policies USING GIN (occupation_tags);

CREATE INDEX idx_policies_income_level
  ON policies USING GIN (income_level);
```

**Django에서:**
```python
from django.contrib.postgres.indexes import GinIndex

class Policy(models.Model):
    class Meta:
        indexes = [
            GinIndex(fields=['region_codes'],    name='idx_policies_region_codes'),
            GinIndex(fields=['occupation_tags'], name='idx_policies_occupation_tags'),
            GinIndex(fields=['income_level'],    name='idx_policies_income_level'),
        ]
```

---

### condition_tree JSONB 스키마

단순 태그 배열로 표현할 수 없는 복합 조건을 AND/OR/NOT 트리로 저장.

**노드 타입:**

```
AND  → children 모두 true여야 통과
OR   → children 중 하나라도 true면 통과
NOT  → child가 false여야 통과
LEAF → 실제 조건값 비교
```

**LEAF 연산자:**

| op | 의미 | 예시 |
|---|---|---|
| `eq` | 같음 | income_level = "기초수급" |
| `in` | 포함 | farming_start in ["1년이내","1~3년"] |
| `gte` | 이상 | age >= 65 |
| `lte` | 이하 | age <= 75 |
| `between` | 범위 | age between [60, 75] |

**예시 — "65세 이상이거나 기초수급자이면서 귀농 3년 이내":**

```json
{
  "type": "AND",
  "children": [
    {
      "type": "OR",
      "children": [
        { "type": "LEAF", "field": "age", "op": "gte", "value": 65 },
        { "type": "LEAF", "field": "income_level", "op": "eq", "value": "기초수급" }
      ]
    },
    {
      "type": "LEAF",
      "field": "farming_start",
      "op": "in",
      "value": ["1년이내", "1~3년"]
    }
  ]
}
```

**조건이 단순할 때는 condition_tree 없이 구조화 필드만 써도 됨 (NULL로 두면 통과).**

---

## 8. 매칭 파이프라인 상세 — 1차 SQL + 2차 서버 평가

### 전체 흐름

```
사용자 프로필
  { age: 65, region_code: "43720",
    occupation_tags: ["귀농"],
    income_level: "기초수급",
    farming_start: "1년이내" }

          ↓

① 지역 계층 조회 (recursive CTE)
   "43720" → ["43720", "43"]   옥천군 + 충청북도

          ↓

② 1차 SQL 필터 (구조화 필드 인덱스 탐색)
   WHERE min_age <= 65 AND max_age >= 65
     AND region_codes && ["43720","43"]
     AND (occupation_tags = '{}' OR occupation_tags && ["귀농"])
     AND (income_level = '{}' OR income_level && ["기초수급"])
   → 후보 정책 N개 반환

          ↓

③ 2차 condition_tree 평가 (Python 서버)
   후보 N개 중 condition_tree가 있는 정책만 추가 검증
   evaluate_tree(policy.condition_tree, user_profile)
   → 최종 매칭 정책 M개

          ↓

④ 정렬
   마감 임박 순 → 최신 등록 순

          ↓

⑤ match_reason 생성
   매칭된 필드 기반 한국어 설명
   "귀농 1년 이내, 옥천군 거주, 65세 이상"
```

---

### 왜 2단계로 나누나

```
DB에서 전부 처리하면?
  → JSONB 조건을 SQL로 표현하면 복잡한 재귀 쿼리 필요
  → 인덱스 못 타고 느림
  → 조건 변경 시 SQL 수정 복잡

서버에서 전부 처리하면?
  → 정책 전체를 DB에서 불러와서 Python으로 필터
  → 정책 10만 개면 10만 개 전부 메모리에 올려야 함
  → 매우 느림

2단계 구조 (현재 채택):
  → SQL로 후보를 빠르게 좁힘 (인덱스 활용)
  → 후보만 Python으로 정밀 평가 (소수의 행만 처리)
  → 속도 + 유연성 동시 확보
```

---

### 지역 계층 조회 — recursive CTE

사용자가 "옥천군"을 입력하면 "충청북도" 대상 정책도 함께 매칭해야 한다.

```sql
WITH RECURSIVE ancestors AS (
  -- 시작: 사용자 입력 지역
  SELECT code, parent_code FROM regions WHERE code = '43720'

  UNION ALL

  -- 재귀: 상위 지역 타고 올라감
  SELECT r.code, r.parent_code
  FROM regions r
  JOIN ancestors a ON r.code = a.parent_code
  WHERE a.parent_code IS NOT NULL
)
SELECT ARRAY_AGG(code) FROM ancestors;
-- 결과: ["43720", "43"]
```

이 배열을 `region_codes &&` 연산에 사용하면 옥천군 정책 + 충청북도 전체 정책이 모두 매칭된다.

---

### condition_tree Python 평가기

```python
def evaluate_tree(node: dict | None, profile: dict) -> bool:
    if node is None:
        return True  # condition_tree 없으면 무조건 통과

    match node['type']:
        case 'AND':
            return all(evaluate_tree(c, profile) for c in node['children'])
        case 'OR':
            return any(evaluate_tree(c, profile) for c in node['children'])
        case 'NOT':
            return not evaluate_tree(node['child'], profile)
        case 'LEAF':
            return _evaluate_leaf(node, profile)
    return False

def _evaluate_leaf(node: dict, profile: dict) -> bool:
    val = profile.get(node['field'])
    if val is None:
        return False

    match node['op']:
        case 'eq':      return val == node['value']
        case 'in':      return val in node['value']
        case 'gte':     return val >= node['value']
        case 'lte':     return val <= node['value']
        case 'between': return node['value'][0] <= val <= node['value'][1]
    return False
```

---

### match_reason 생성

사용자에게 "나에게 해당되는 이유"를 보여주는 문자열 생성.

```python
def build_match_reason(policy: Policy, profile: dict) -> str:
    reasons = []

    if policy.min_age > 0 or policy.max_age < 130:
        reasons.append(f"{profile['age']}세 해당")

    if policy.region_codes:
        reasons.append(f"{profile['region_name']} 거주")

    if '귀농' in policy.occupation_tags:
        reasons.append(f"귀농 {profile['farming_start']} 해당")

    if policy.income_level:
        reasons.append(f"{profile['income_level']} 해당")

    return ', '.join(reasons)
    # 예: "65세 해당, 옥천군 거주, 귀농 1년이내 해당"
```

---

## 9. 우리 서비스 최종 채택 방식

```
v1:  SQL 1차 필터 + condition_tree 2차 평가
     LLM은 공고문 파싱(입력 단계)에만 사용
     → 매칭 자체에 LLM 호출 없음 (속도 보장)

v2:  공공 API JSON → 필드 매핑 직접
     자연어 조건 필드 있을 때만 LLM 파싱 추가
     크롤링 HTML → LLM 파싱 → DB 저장
```

---

## 10. 파이프라인 설계 비교

저장부터 매칭까지 두 가지 구조를 비교한다.

---

### Pipeline A — 규칙 기반 (채택)

**저장 단계:**
```
공고문 텍스트
    ↓ Claude API (입력 단계 1회)
구조화 필드 추출
    ↓
DB 저장
  min_age=18, max_age=130
  region_codes=["43720"]
  occupation_tags=["귀농"]
  income_level=["기초수급","차상위"]
  condition_tree={
    "type": "OR",
    "children": [
      {"type":"LEAF","field":"age","op":"gte","value":65},
      {"type":"LEAF","field":"income_level","op":"eq","value":"기초수급"}
    ]
  }
```

**매칭 단계:**
```
사용자 프로필
    ↓
① SQL 1차 필터 (GIN 인덱스 탐색, 빠름)
   WHERE min_age<=65 AND max_age>=65
     AND region_codes && ["43720","43"]
   → 후보 8개

    ↓
② Python condition_tree 평가
   evaluate_tree(policy.condition_tree, profile)
   → 최종 5개

    ↓
③ 정렬 + match_reason 생성
```

---

### Pipeline B — LLM 재판단 (하이브리드)

**저장 단계:**
```
공고문 텍스트
    ↓ 구조화 필드만 추출 (나이, 지역 등 명확한 것만)
DB 저장
  min_age=18
  region_codes=["43720"]
  occupation_tags=["귀농"]
  raw_condition="만 65세 이상 또는 기초생활수급자로서
                 귀농한 지 3년 이내인 자"  ← 원문 그대로 보관
  condition_tree=NULL
```

**매칭 단계:**
```
사용자 프로필
    ↓
① SQL 1차 필터 (인덱스 탐색, 빠름)
   → 후보 8개

    ↓
② LLM 판단 (후보마다 Claude 호출)
   prompt:
     "사람: 65세, 기초수급자, 귀농 1년차
      정책 조건: {raw_condition}
      이 사람에게 해당되나요? YES/NO + 이유"
   → 최종 5개

    ↓
③ 정렬 + LLM이 생성한 이유 그대로 표시
```

---

### 비교표

| | Pipeline A (규칙 기반) | Pipeline B (LLM 재판단) |
|---|---|---|
| **저장 복잡도** | 높음 (condition_tree 생성) | 낮음 (원문 텍스트만 저장) |
| **매칭 속도** | 빠름 (SQL + Python) | 느림 (LLM 후보 수만큼 호출) |
| **매칭 비용** | 0원 | 후보 8개 × $0.01 = 매 요청마다 발생 |
| **OR 조건 처리** | 가능 (condition_tree) | 가능 (LLM이 해석) |
| **모호한 문구 처리** | 불가능 | 가능 ("농업에 준하는 활동" 등) |
| **결과 일관성** | 항상 동일 | LLM마다 다를 수 있음 |
| **구현 난이도** | 중간 (트리 평가기) | 낮음 (프롬프트만 설계) |
| **match_reason** | 직접 생성 | LLM 설명 그대로 사용 |

---

### 선택 기준

```
Pipeline A 선택 조건:
  → 매칭이 자주 일어남 (사용자 홈 접속마다)
  → 비용 0으로 유지해야 함
  → 결과가 예측 가능해야 함

Pipeline B 선택 조건:
  → 공고문 조건이 모호한 경우가 많음
  → 매칭 정확도가 속도·비용보다 중요
  → 구현 시간이 촉박함
```

**→ 우리 서비스는 Pipeline A 채택.**  
홈 접속마다 LLM 호출하면 동시접속자 100명 시 100번 호출 + 응답 지연 발생.  
Pipeline B는 조건이 극도로 복잡해졌을 때 검토.

---

## 11. 매칭 강화 방안

> Pipeline A(SQL 1차 + condition_tree 2차) 구조를 유지하면서 결과 품질을 높이는 방법들.  
> v1 구현 이후 단계적으로 적용 검토.

---

### 11-1. 다중 가중치 스코어링 (Multi-factor Weighted Scoring)

현재 매칭은 조건 충족 여부만 판단(이진). 충족한 조건의 종류와 수에 따라 점수를 매겨 순위를 개선할 수 있다.

**설계 예시:**

```python
FIELD_WEIGHTS = {
    'region':           30,  # 지역 조건 일치는 가장 중요
    'age':              25,
    'occupation_tags':  20,
    'income_level':     15,
    'household_type':   5,
    'move_status':      5,
}

def score_policy(policy: Policy, profile: dict) -> int:
    score = 0

    if profile.get('age') is not None:
        if policy.min_age <= profile['age'] <= policy.max_age:
            score += FIELD_WEIGHTS['age']

    ancestor_codes = get_ancestor_codes(profile.get('region_code', ''))
    if not policy.region_codes or set(policy.region_codes) & set(ancestor_codes):
        score += FIELD_WEIGHTS['region']

    if not policy.occupation_tags or set(policy.occupation_tags) & set(profile.get('occupation_tags', [])):
        score += FIELD_WEIGHTS['occupation_tags']

    if not policy.income_level or profile.get('income_level') in policy.income_level:
        score += FIELD_WEIGHTS['income_level']

    return score
```

**활용:**
- 최소 점수 이상만 "해당됨" 그룹, 그 아래는 "확인 필요" 그룹으로 분리
- 동점 시 마감 임박 순으로 타이브레이크

**장점:** 프로필이 부분적으로만 입력됐을 때 "0개 결과" 방지  
**비용:** 코드 변경만, DB 스키마 무관

---

### 11-2. 프로필 누락 필드 폴백 (Progressive Relaxation)

사용자가 프로필을 완전히 입력하지 않은 경우, 엄격한 조건 매칭은 결과가 0개가 되기 쉽다.  
입력된 필드만으로 매칭하고, 누락 필드는 "조건 없음(전체 대상)"으로 간주하는 전략.

**현재 코드 문제점:**

```python
# 현재: income 미입력 시 income_level 필터 자체를 건너뜀
if income:
    qs = qs.filter(income_level__len=0) | qs.filter(income_level__contains=[income])
# → income 미입력이면 소득 조건이 있는 정책도 모두 포함되어 과매칭 발생 가능
```

**개선 방향 — 3단계 폴백:**

```
1단계: 모든 입력 필드 사용 → 결과 >= 3개면 반환
         ↓ 결과 < 3개
2단계: 선택 필드(household_type, marital_status) 제거 → 결과 >= 3개면 반환
         ↓ 결과 < 3개
3단계: 필수 필드(나이, 지역)만 사용 + 전체 대상 정책 포함 → 반환
```

```python
def match_with_fallback(profile: dict) -> dict:
    for relaxation_level in range(3):
        result = match_policies(profile, relaxation_level=relaxation_level)
        if len(result['policies']) >= 3:
            return {**result, 'relaxation_level': relaxation_level}
    return {**result, 'relaxation_level': 2}
```

**응답에 `relaxation_level` 포함** → 프론트에서 "프로필을 더 입력하면 더 정확한 결과를 볼 수 있어요" 안내 가능

---

### 11-3. 피드백 루프 (UserPolicy 상태 반영)

`user_policies` 테이블의 `status` 필드를 매칭 순위에 반영해 재노출을 방지하고 개인화를 강화한다.

**현재 상태 → 활용 방안:**

| status | 현재 | 강화 후 |
|---|---|---|
| `신청예정` | 상태 저장만 | 목록에서 상단 고정 + "D-N 마감" 배지 |
| `신청완료` | 상태 저장만 | 매칭 결과에서 제외 (이미 신청한 정책 재노출 방지) |
| `관심없음` | 상태 저장만 | 같은 `benefit_type` + `managing_org` 조합 정책 순위 하락 |

**구현 예시:**

```python
def filter_already_applied(policies, profile_id):
    applied_ids = set(
        UserPolicy.objects.filter(
            profile_id=profile_id,
            status=UserPolicy.Status.APPLIED,
        ).values_list('policy_id', flat=True)
    )
    return [p for p in policies if p.id not in applied_ids]

def deprioritize_not_interested(policies, profile_id):
    disliked = UserPolicy.objects.filter(
        profile_id=profile_id,
        status=UserPolicy.Status.NOT_INTERESTED,
    ).values_list('policy__benefit_type', 'policy__managing_org')
    disliked_combos = set(disliked)

    def sort_key(p):
        is_disliked = (p.benefit_type, p.managing_org) in disliked_combos
        return (1 if is_disliked else 0,)  # 비선호 하단으로

    return sorted(policies, key=sort_key)
```

**비용:** 쿼리 2회 추가 (이미 캐싱 레이어 있으면 무시 가능 수준)

---

### 11-4. 마감 임박 부스팅 (Deadline Proximity Boost)

현재 매칭 후 마감 임박 순 정렬이 있지만, 마감이 없는 상시 정책과의 순위 분리가 명확하지 않다.

**개선 — 마감 구간별 가중치:**

```python
from datetime import date

def deadline_boost(policy: Policy, today: date) -> int:
    if not policy.apply_end_date:
        return 0   # 상시 정책 → 부스트 없음

    days_left = (policy.apply_end_date - today).days

    if days_left < 0:
        return -9999   # 마감 지남 → 최하단
    elif days_left <= 7:
        return 50      # D-7 이내 → 최상단 부스트
    elif days_left <= 30:
        return 20
    elif days_left <= 90:
        return 5
    else:
        return 0
```

**정렬 키 통합:**

```python
def final_sort_key(policy, score, today):
    return -(score + deadline_boost(policy, today))
    # 음수로 뒤집어 내림차순 정렬

matched.sort(key=lambda p: final_sort_key(p, score_map[p.id], today))
```

**D-7 알림과 연계:** `user_policies.d7_alerted_at` 필드와 함께 쓰면 알림 발송 + 앱 내 부스팅 일관성 확보 (v2.2.0)

---

### 11-5. 벡터 검색 통합 방안 (v3 검토)

Pipeline A의 SQL 필터로 잡을 수 없는 케이스 — "농업에 준하는 활동", "저소득 가구" 같은 모호한 조건 — 를  
벡터 유사도로 보완하는 하이브리드 구조.

**구조:**

```
① SQL 1차 필터 (현재 Pipeline A 유지)
   → 후보 N개

② 벡터 유사도 Re-rank (추가 레이어)
   후보 N개를 임베딩 유사도로 재순위
   → 상위 K개만 반환

③ condition_tree 2차 평가 (현재 유지)
```

**임베딩 대상:**

```python
# 정책 저장 시 (1회성)
policy_text = f"{policy.title} {policy.summary} {policy.description}"
policy.embedding = embed(policy_text)   # 1536차원 벡터
policy.save()

# 매칭 시 (요청마다)
profile_text = f"귀농 {profile.years_since_move:.0f}년차 {profile.age}세 {profile.region_name} 거주"
query_embedding = embed(profile_text)
```

**PostgreSQL pgvector 사용:**

```sql
-- 유사도 순 정렬
SELECT id, title, embedding <=> $1 AS distance
FROM policies
WHERE id = ANY($2)   -- SQL 1차 필터 후보 ID 배열
ORDER BY distance
LIMIT 10;
```

**도입 조건:**
- 정책 수가 500개 이상으로 늘어날 때
- SQL 필터 결과가 "너무 많음" (30개+) 문제 생길 때
- Supabase pgvector 확장 활성화 필요 (`CREATE EXTENSION vector`)

**비용:** 정책 저장 시 임베딩 API 호출 1회 (OpenAI `text-embedding-3-small` 기준 정책 1000개 ≈ $0.02)

---

### 강화 방안 우선순위 요약

| 방안 | 효과 | 구현 비용 | 권장 시점 |
|---|---|---|---|
| 11-3. 피드백 루프 | 중 | 낮음 (쿼리 2개) | v1.5 — UserPolicy 쌓이면 바로 |
| 11-4. 마감 임박 부스팅 | 중 | 낮음 (정렬 키 수정) | v1.5 — D-7 알림과 묶어서 |
| 11-1. 다중 가중치 스코어링 | 높음 | 중간 (점수 설계 필요) | v2 — 정책 20개+ 쌓인 후 |
| 11-2. 프로필 폴백 | 중 | 중간 (폴백 로직) | v2 — 프로필 완성도 낮은 사용자 늘면 |
| 11-5. 벡터 검색 | 높음 | 높음 (인프라 변경) | v3 — 정책 500개+ |
