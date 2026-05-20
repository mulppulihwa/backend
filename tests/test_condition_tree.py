"""condition_tree.py 유닛 테스트 — Django 의존 없음."""
import pytest
from lib.matching.condition_tree import evaluate_tree


PROFILE = {
    'age': 70,
    'income_level': '기초수급',
    'occupation_tags': ['귀농'],
    'region_code': '43720',
}


class TestNoneNode:
    def test_none_returns_true(self):
        assert evaluate_tree(None, PROFILE) is True


class TestLeaf:
    def test_eq_match(self):
        node = {'type': 'LEAF', 'field': 'income_level', 'op': 'eq', 'value': '기초수급'}
        assert evaluate_tree(node, PROFILE) is True

    def test_eq_no_match(self):
        node = {'type': 'LEAF', 'field': 'income_level', 'op': 'eq', 'value': '일반'}
        assert evaluate_tree(node, PROFILE) is False

    def test_gte(self):
        node = {'type': 'LEAF', 'field': 'age', 'op': 'gte', 'value': 65}
        assert evaluate_tree(node, PROFILE) is True

    def test_gte_fail(self):
        node = {'type': 'LEAF', 'field': 'age', 'op': 'gte', 'value': 80}
        assert evaluate_tree(node, PROFILE) is False

    def test_lte(self):
        node = {'type': 'LEAF', 'field': 'age', 'op': 'lte', 'value': 75}
        assert evaluate_tree(node, PROFILE) is True

    def test_between(self):
        node = {'type': 'LEAF', 'field': 'age', 'op': 'between', 'value': [60, 80]}
        assert evaluate_tree(node, PROFILE) is True

    def test_between_out_of_range(self):
        node = {'type': 'LEAF', 'field': 'age', 'op': 'between', 'value': [18, 64]}
        assert evaluate_tree(node, PROFILE) is False

    def test_in_match(self):
        node = {'type': 'LEAF', 'field': 'income_level', 'op': 'in', 'value': ['기초수급', '차상위']}
        assert evaluate_tree(node, PROFILE) is True

    def test_in_no_match(self):
        node = {'type': 'LEAF', 'field': 'income_level', 'op': 'in', 'value': ['일반']}
        assert evaluate_tree(node, PROFILE) is False

    def test_missing_field_returns_false(self):
        node = {'type': 'LEAF', 'field': 'nonexistent', 'op': 'eq', 'value': 'x'}
        assert evaluate_tree(node, PROFILE) is False

    def test_unsupported_op_returns_false(self):
        node = {'type': 'LEAF', 'field': 'age', 'op': 'contains', 'value': 70}
        assert evaluate_tree(node, PROFILE) is False

    def test_type_error_returns_false(self):
        # age(int)를 문자열과 비교 — TypeError가 아닌 False 반환
        node = {'type': 'LEAF', 'field': 'age', 'op': 'gte', 'value': 'not_a_number'}
        assert evaluate_tree(node, PROFILE) is False


class TestAnd:
    def test_all_true(self):
        node = {
            'type': 'AND',
            'children': [
                {'type': 'LEAF', 'field': 'age', 'op': 'gte', 'value': 65},
                {'type': 'LEAF', 'field': 'income_level', 'op': 'eq', 'value': '기초수급'},
            ],
        }
        assert evaluate_tree(node, PROFILE) is True

    def test_one_false(self):
        node = {
            'type': 'AND',
            'children': [
                {'type': 'LEAF', 'field': 'age', 'op': 'gte', 'value': 65},
                {'type': 'LEAF', 'field': 'income_level', 'op': 'eq', 'value': '일반'},
            ],
        }
        assert evaluate_tree(node, PROFILE) is False

    def test_empty_children_returns_true(self):
        node = {'type': 'AND', 'children': []}
        assert evaluate_tree(node, PROFILE) is True


class TestOr:
    def test_one_true(self):
        node = {
            'type': 'OR',
            'children': [
                {'type': 'LEAF', 'field': 'age', 'op': 'gte', 'value': 65},
                {'type': 'LEAF', 'field': 'income_level', 'op': 'eq', 'value': '일반'},
            ],
        }
        assert evaluate_tree(node, PROFILE) is True

    def test_all_false(self):
        node = {
            'type': 'OR',
            'children': [
                {'type': 'LEAF', 'field': 'age', 'op': 'lte', 'value': 50},
                {'type': 'LEAF', 'field': 'income_level', 'op': 'eq', 'value': '일반'},
            ],
        }
        assert evaluate_tree(node, PROFILE) is False

    def test_empty_children_returns_false(self):
        node = {'type': 'OR', 'children': []}
        assert evaluate_tree(node, PROFILE) is False


class TestNot:
    def test_not_true(self):
        node = {
            'type': 'NOT',
            'child': {'type': 'LEAF', 'field': 'income_level', 'op': 'eq', 'value': '일반'},
        }
        assert evaluate_tree(node, PROFILE) is True

    def test_not_false(self):
        node = {
            'type': 'NOT',
            'child': {'type': 'LEAF', 'field': 'income_level', 'op': 'eq', 'value': '기초수급'},
        }
        assert evaluate_tree(node, PROFILE) is False


class TestUnknownType:
    def test_unknown_type_returns_false(self):
        node = {'type': 'INVALID_TYPE', 'children': []}
        assert evaluate_tree(node, PROFILE) is False


class TestNestedTree:
    def test_complex_or_and(self):
        # (age >= 65 OR income == 기초수급) AND occupation_tags 귀농
        node = {
            'type': 'AND',
            'children': [
                {
                    'type': 'OR',
                    'children': [
                        {'type': 'LEAF', 'field': 'age', 'op': 'gte', 'value': 65},
                        {'type': 'LEAF', 'field': 'income_level', 'op': 'eq', 'value': '기초수급'},
                    ],
                },
                {'type': 'LEAF', 'field': 'occupation_tags', 'op': 'in', 'value': ['귀농', '귀촌']},
            ],
        }
        assert evaluate_tree(node, PROFILE) is True
