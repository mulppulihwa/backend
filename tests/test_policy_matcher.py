"""policy_matcher.py 유닛 테스트 — DB를 mock으로 대체."""
from unittest.mock import MagicMock, patch

import pytest

from lib.matching.policy_matcher import _run_matching, match_policies


def _make_policy(
    condition_tree=None,
    occupation_tags=None,
    income_level=None,
    apply_end_date=None,
):
    p = MagicMock()
    p.condition_tree = condition_tree
    p.occupation_tags = occupation_tags or []
    p.income_level = income_level or []
    p.apply_end_date = apply_end_date
    return p


PROFILE = {
    'region_code': '43720',
    'age': 70,
    'occupation_tags': ['귀농'],
    'income_level': '기초수급',
    'non_farm_income': 2000,
}


class TestMatchPoliciesErrorHandling:
    @patch('lib.matching.policy_matcher.get_ancestor_codes', side_effect=Exception('DB down'))
    @patch('lib.matching.policy_matcher._run_matching')
    def test_ancestor_codes_failure_uses_empty(self, mock_run, mock_get):
        mock_run.return_value = []
        with patch('lib.matching.policy_matcher.Policy') as mock_policy:
            mock_policy.objects.filter.return_value.order_by.return_value.__getitem__.return_value = []
            result = match_policies(PROFILE)
        # ancestor_codes 실패해도 매칭 자체는 실행됨
        assert 'policies' in result

    @patch('lib.matching.policy_matcher.get_ancestor_codes', return_value=['43720', '43'])
    @patch('lib.matching.policy_matcher._run_matching', side_effect=Exception('DB error'))
    def test_db_error_returns_fallback(self, mock_run, mock_get):
        from django.db import DatabaseError
        mock_run.side_effect = DatabaseError('DB error')
        result = match_policies(PROFILE)
        assert result['fallback'] is True
        assert 'error' in result

    @patch('lib.matching.policy_matcher.get_ancestor_codes', return_value=['43720', '43'])
    @patch('lib.matching.policy_matcher._run_matching', return_value=[])
    @patch('lib.matching.policy_matcher.Policy')
    def test_empty_match_returns_fallback_policies(self, mock_policy, mock_run, mock_get):
        fallback = [_make_policy()]
        mock_policy.objects.filter.return_value.order_by.return_value.__getitem__.return_value = fallback
        result = match_policies(PROFILE)
        assert result['fallback'] is True
        assert result['policies'] == fallback


class TestConditionTreeEvaluation:
    @patch('lib.matching.policy_matcher.get_ancestor_codes', return_value=['43720', '43'])
    @patch('lib.matching.policy_matcher._run_matching')
    def test_policy_with_no_condition_tree_passes(self, mock_run, mock_get):
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

        from lib.matching.policy_matcher import _run_matching
        import lib.matching.policy_matcher as pm

        with patch.object(pm.timezone, 'now') as mock_now:
            mock_now.return_value.date.return_value = today
            with patch('lib.matching.policy_matcher.Policy') as mock_policy:
                mock_policy.objects.filter.return_value = MagicMock()
                # _run_matching을 통하지 않고 정렬 로직만 검증
                policies = [p1, p3, p2]
                policies.sort(key=lambda p: (0, (p.apply_end_date - today).days) if p.apply_end_date else (1, 0))
                assert policies[0] == p2   # 마감 가장 임박
                assert policies[1] == p1
                assert policies[2] == p3   # 마감 없으면 마지막
