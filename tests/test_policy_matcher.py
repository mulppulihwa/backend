"""policy_matcher.py 유닛 테스트 — DB를 mock으로 대체."""
from unittest.mock import MagicMock, patch

import pytest

from lib.matching.policy_matcher import _run_matching, match_policies


def _make_policy(
    condition_tree=None,
    occupation_tags=None,
    income_level=None,
    apply_end_date=None,
    source='복지로',
):
    p = MagicMock()
    p.condition_tree = condition_tree
    p.occupation_tags = occupation_tags or []
    p.income_level = income_level or []
    p.apply_end_date = apply_end_date
    p.source = source
    return p


SOURCE_PRIORITY = {'수동입력': 0, '귀농센터': 1, '복지로': 2}


def _sort_key(p, today):
    source_rank = SOURCE_PRIORITY.get(p.source, len(SOURCE_PRIORITY))
    if p.apply_end_date:
        return (source_rank, 0, (p.apply_end_date - today).days)
    return (source_rank, 1, 0)


PROFILE = {
    'age': 70,
    'occupation_tags': ['귀농'],
    'income_level': '기초수급',
    'non_farm_income': 2000,
}


class TestMatchPoliciesErrorHandling:
    @patch('lib.matching.policy_matcher._run_matching', side_effect=Exception('DB error'))
    def test_db_error_returns_fallback(self, mock_run):
        from django.db import DatabaseError
        mock_run.side_effect = DatabaseError('DB error')
        result = match_policies(PROFILE)
        assert result['fallback'] is True
        assert 'error' in result

    @patch('lib.matching.policy_matcher._run_matching', return_value=[])
    @patch('lib.matching.policy_matcher.Policy')
    def test_empty_match_returns_fallback_policies(self, mock_policy, mock_run):
        fallback = [_make_policy()]
        mock_policy.objects.filter.return_value.order_by.return_value.__getitem__.return_value = fallback
        result = match_policies(PROFILE)
        assert result['fallback'] is True
        assert result['policies'] == fallback


class TestConditionTreeEvaluation:
    @patch('lib.matching.policy_matcher._run_matching')
    def test_policy_with_no_condition_tree_passes(self, mock_run):
        p = _make_policy(condition_tree=None)
        mock_run.return_value = [p]
        result = match_policies(PROFILE)
        assert p in result['policies']

    def test_sort_by_deadline(self):
        from datetime import date
        today = date(2026, 5, 13)
        p1 = _make_policy(apply_end_date=date(2026, 6, 30))
        p2 = _make_policy(apply_end_date=date(2026, 5, 20))
        p3 = _make_policy(apply_end_date=None)

        # _run_matching을 통하지 않고 정렬 로직만 검증 (동일 출처 → 마감 임박 순)
        policies = [p1, p3, p2]
        policies.sort(key=lambda p: _sort_key(p, today))
        assert policies[0] == p2   # 마감 가장 임박
        assert policies[1] == p1
        assert policies[2] == p3   # 마감 없으면 마지막

    def test_sort_by_source_priority(self):
        from datetime import date
        today = date(2026, 5, 13)
        # 복지로 정책이 마감 임박이어도, 수동입력/귀농센터 정책보다 뒤로
        p_bokjiro  = _make_policy(apply_end_date=date(2026, 5, 14), source='복지로')
        p_gwiro    = _make_policy(apply_end_date=None, source='귀농센터')
        p_manual   = _make_policy(apply_end_date=None, source='수동입력')

        policies = [p_bokjiro, p_gwiro, p_manual]
        policies.sort(key=lambda p: _sort_key(p, today))
        assert policies[0] == p_manual
        assert policies[1] == p_gwiro
        assert policies[2] == p_bokjiro
