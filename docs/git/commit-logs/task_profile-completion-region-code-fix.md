# 진단 완료해도 프로필 완료 안 됨 — region_code 필수 조건 제거

**날짜**: 2026-06-08
**커밋 로그**: [2c6829b](https://github.com/mulppulihwa/backend/commit/2c6829b)

## 작업 배경

신규 가입자(인은선, id=17)가 진단 폼을 끝까지 작성·제출했는데도 "프로필 작성을
완료해야 맞춤 정책을 확인할 수 있습니다" 에러가 계속 떠서 맞춤 정책을 못 본다는
신고 발생. 실제 DB를 확인해보니 `birth_date`/`occupation_tags`/`gender`/
`move_in_date`/`prev_residence_type`/`household_type` 등 나머지 필드는 전부
정상 저장돼 있었고, **`region_code`만 빈 문자열(`''`)** 이었음.

원인을 추적해보니 프론트(`socialventure-frontend/src/pages/Step1.jsx`)의
`buildProfilePayload`에서
```js
const regionName = location === '옥천' ? '옥천군' : region
```
의 `region` state가 어떤 입력 요소에도 연결되지 않은 채 항상 `''`로 남아있어,
사용자가 "현재 어디 사세요?"에서 "옥천 외"를 선택하면 `region_code`가 항상
빈 값으로 전송되는 구조적 문제가 있었음 (프론트는 `region` 참조를 빈 문자열로
교체하는 방식으로 별도 수정).

이 서비스는 옥천 거주민만을 대상으로 하므로, "옥천 외"를 선택한 사용자에게
특정 시군구 `region_code`를 요구하는 것 자체가 의미가 없음 — 백엔드의 프로필
완료 판정에서 `region_code`를 필수 조건에서 제외하는 것이 맞다고 판단.

## AS-IS

`lib/diagnosis_service.py`
```python
REQUIRED_FIELDS = ('region_code', 'birth_date', 'occupation_tags')
```
`region_code`가 빈 값이면 (옥천 외 선택자는 항상 그러함) `is_profile_complete`가
`False`를 반환 → `profile_completed`가 영원히 `True`로 전환되지 않아 맞춤 정책
화면이 항상 "프로필 작성을 완료해야..." 에러를 표시.

## TO-BE

```python
REQUIRED_FIELDS = ('birth_date', 'occupation_tags')
```
`region_code`는 더 이상 완료 조건에 포함되지 않음. 매칭 로직(`policy_matcher.py`,
`region_hierarchy.get_ancestor_codes`)은 이미 빈 `region_code`를 안전하게
처리하도록 되어 있어 (지역 필터 없이 전국 정책 위주로 매칭) 부작용 없음.

## 주요 변경

- `lib/diagnosis_service.py` — `REQUIRED_FIELDS`에서 `region_code` 제거
- (별도 레포) `socialventure-frontend/src/pages/Step1.jsx` — `regionName` 계산에서
  미연결 `region` state 참조를 빈 문자열로 교체

## 참고

- 기존에 `profile_completed=False`로 저장된 사용자(인은선 포함)는 다음
  `PATCH /api/profile/` 호출(예: 진단 폼 재제출) 시 `sync_profile_completed`가
  새 기준으로 재평가하면서 자동으로 `True`로 전환됨 — 별도 데이터 수정 불필요.
