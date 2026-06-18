# condition_tree 미지원 스키마를 통과(true)로 처리

**날짜**: 2026-06-15
**커밋 로그**: [bc6744e](https://github.com/mulppulihwa/backend/commit/bc6744e)

## 작업 배경

§9 5번 단계(샘플 데이터 테스트) — 그린대로 어댑터로 수집한 정책 2건을
`transaction.atomic()` + rollback으로 DB에 임시 저장한 뒤 `match_policies()`
전체 플로우를 검증.

크롤링/AI 파싱/저장은 정상이었지만, SQL 1차 필터(나이/직업태그)를 통과한
두 정책이 최종 매칭 결과에서 빠짐. 원인은 `lib/matching/condition_tree.py`의
`evaluate_tree()`가 `{'type': 'AND'|'OR'|'NOT'|'LEAF', 'children': [...]}`
스키마만 인식하는데, `lib/parsing/policy_parser.py`의 `PARSE_TOOL`은
`condition_tree`를 `{'type': 'object'}`(자유 형식)로만 정의해 Claude가
`{'AND': [...]}`, `{'선정방식': {...}, ...}` 등 다른 형태를 생성함.
`evaluate_tree`는 인식 못하는 최상위 구조를 만나면 `_evaluate()`의
default case(`Unknown node type: None`)에서 **`False`를 반환** → SQL
필터를 통과한 정책이 조건 평가 단계에서 탈락.

로그 확인 결과 기존 복지로 정책 다수에서도 동일한 경고
(`AND node has no children`, `Unknown node type: None`)가 발생 —
그린대로 한정 문제가 아니라 전체 DB에 영향을 주는 기존 이슈.

## AS-IS

```python
# lib/matching/condition_tree.py
def _evaluate(node, profile):
    node_type = node.get('type')
    match node_type:
        case 'AND': ...
        case 'OR': ...
        case 'NOT': ...
        case 'LEAF': ...
        case _:
            logger.warning('Unknown node type: %s', node_type)
            return False
```

AI가 기대 스키마와 다른 `condition_tree`를 생성하면, SQL 필터(나이·직업·
소득 등)를 모두 만족하는 정책도 매칭 결과에서 제외됨.

## TO-BE

인식 불가능한 condition_tree 구조는 "조건 없음"과 동일하게 **통과(true)**
처리 — `node is None`일 때와 동일한 취지(조건을 평가할 수 없으면 SQL
필터 결과를 신뢰).

```python
        case _:
            logger.warning('Unknown node type: %s — 조건 평가 불가, 통과 처리', node_type)
            return True
```

## 주요 변경

- `lib/matching/condition_tree.py` — `_evaluate()` default case `False` → `True`
- `tests/test_condition_tree.py`
  - `test_unknown_type_returns_false` → `test_unknown_type_returns_true`로 변경
  - `test_missing_type_returns_true` 추가 (`{'AND': [...]}` 형태 검증)

## 검증

`pytest tests/` — 36 passed, 1 failed (기존부터 실패하던 무관 테스트,
`test_policy_parser.py::test_pydantic_validation_error`).

그린대로 샘플 데이터로 재검증: 수정 전 19건 → 수정 후 85건으로 매칭 결과
증가, 새로 수집한 2건("청년농업인영농정착지원금", "영농창업특성화대학")도
정상 매칭됨 확인 (트랜잭션 롤백으로 운영 DB 변경 없음).

## 참고 — 남은 작업 (§9)

5번(샘플 데이터 테스트) 완료. 6번(정책 DB 정리 + 전체 크롤링),
7번(계정 초기화, 최종) 이어서 진행.
