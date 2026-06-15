# 시스템 아키텍처

```mermaid
graph TB
    subgraph Client["클라이언트"]
        FE["프론트엔드 (Next.js/React)<br/>socialventure-frontend"]
    end

    subgraph External["외부 서비스"]
        KakaoLogin["카카오 로그인 (OAuth)"]
        KakaoMap["카카오 지도 SDK<br/>(JS, 클라이언트 Geocoder)"]
        DaumPostcode["다음 우편번호(Postcode)<br/>주소 검색"]
        KakaoLocal["카카오 로컬 API<br/>(주소 검색 / 서버 Geocoding)"]
        Bokjiro["복지로 Open API"]
        Greendaero["그린대로(귀농센터)<br/>크롤링 대상"]
        Anthropic["Anthropic Claude API<br/>(정책/준비물 파싱)"]
    end

    subgraph Backend["백엔드 (Django/DRF, Railway)"]
        direction TB

        subgraph Apps["apps/"]
            UsersApp["users<br/>인증·프로필·내 정책"]
            PoliciesApp["policies<br/>정책 매칭·조회"]
            PlacesApp["places<br/>사용처 CRUD"]
            RegionsApp["regions<br/>지역 정보"]
        end

        subgraph Lib["lib/"]
            Matcher["matching/policy_matcher<br/>조건 매칭·정렬"]
            Parser["parsing/<br/>policy_parser, checklist_parser"]
            SyncAdapters["sync/adapters<br/>bokjiro_sync, greendaero_sync"]
            Geocoding["services/geocoding<br/>주소→좌표 변환"]
        end

        subgraph Commands["management commands"]
            SyncCmd["sync_bokjiro / sync_greendaero<br/>prune_policy_scope<br/>parse_checklists / backfill_checklists"]
        end
    end

    subgraph DB["DB (Supabase Postgres)"]
        Tables["users, policies, checklist_items,<br/>local_places, regions ..."]
    end

    %% 클라이언트 <-> 외부 서비스 (프론트 직접 연동)
    FE -- "로그인 redirect" --> KakaoLogin
    FE -- "지도 표시 / 클라이언트 geocoding" --> KakaoMap
    FE -- "주소 검색 팝업" --> DaumPostcode

    %% 클라이언트 <-> 백엔드
    FE -- "REST API<br/>(/api/auth, /api/profile,<br/>/api/policies, /api/places, /api/regions)" --> Apps
    KakaoLogin -. "인가 코드" .-> UsersApp

    %% 백엔드 내부
    PoliciesApp --> Matcher
    PlacesApp --> Geocoding
    Commands --> SyncAdapters
    Commands --> Parser

    %% 백엔드 <-> DB
    Apps --> Tables
    Lib --> Tables

    %% 백엔드 <-> 외부 서비스
    Geocoding -- "서버 geocoding (폴백)" --> KakaoLocal
    SyncAdapters -- "정책 수집" --> Bokjiro
    SyncAdapters -- "정책 수집" --> Greendaero
    Parser -- "구조화 파싱" --> Anthropic
```

## 구성 요약

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
