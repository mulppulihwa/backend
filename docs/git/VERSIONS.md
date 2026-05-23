# 버전 계획

브랜치 전략: `feature/vX.Y.Z/기능명` → `release/vX.Y.Z` → `develop` → `main`
**1버전 = 1기능**

---

## v1.x — 핵심 유저 플로우 완성

| 버전 | 브랜치 | 기능 | 설명 |
|------|--------|------|------|
| v1.1.0 | `feature/v1.1.0/profile-api` | 프로필 API | `GET /api/profile/` 조회, `PATCH /api/profile/` 수정, `profile_completed` 자동 업데이트 |
| v1.2.0 | `feature/v1.2.0/user-policy-api` | 유저 정책 API | `POST /api/policies/{id}/save/`, `PATCH /api/policies/{id}/status/`, `GET /api/users/me/policies/` |
| v1.3.0 | `feature/v1.3.0/diagnosis-service` | 온보딩 Facade | `lib/diagnosis_service.py` — 온보딩 완료 처리, profile_completed 업데이트 로직 통합 |
| v1.4.0 | `feature/v1.4.0/policy-data` | 실 정책 데이터 입력 | parse API + Admin으로 귀농귀촌 실제 정책 최소 10개 등록 |

---

## v2.x — 자동화 + 운영 인프라

| 버전 | 브랜치 | 기능 | 설명 |
|------|--------|------|------|
| v2.0.0 | `feature/v2.0.0/welfare-sync` | 복지로 API 연동 | `lib/sync/adapters/` 구현. 복지로 API 정책 자동 동기화 |
| v2.1.0 | `feature/v2.1.0/greendaero-crawler` | 귀농귀촌종합센터 크롤러 | `lib/sync/crawlers/` 구현. greendaero.go.kr 크롤링 |
| v2.2.0 | `feature/v2.2.0/d7-notification` | D-7 마감 알림 | `UserPolicy.d7_alerted_at` 활용. 마감 7일 전 알림 발송 |
| v2.3.0 | `feature/v2.3.0/admin-cms` | Admin CMS API | 정책·장소 등록·수정·비활성화 API (관리자 전용) |

---

## 브랜치 흐름

```
develop
├── release/v1.1.0
│   └── feature/v1.1.0/profile-api
├── release/v1.2.0
│   └── feature/v1.2.0/user-policy-api
├── release/v1.3.0
│   └── feature/v1.3.0/diagnosis-service
├── release/v1.4.0
│   └── feature/v1.4.0/policy-data
├── release/v2.0.0
│   └── feature/v2.0.0/welfare-sync
├── release/v2.1.0
│   └── feature/v2.1.0/greendaero-crawler
├── release/v2.2.0
│   └── feature/v2.2.0/d7-notification
└── release/v2.3.0
    └── feature/v2.3.0/admin-cms
```
