"""policy_parser.py 유닛 테스트 — anthropic 클라이언트를 mock으로 대체."""
from unittest.mock import MagicMock, patch

import pytest

from lib.parsing.policy_parser import PolicyParseError, parse_policy


def _make_tool_use_response(data: dict):
    tool_block = MagicMock()
    tool_block.type = 'tool_use'
    tool_block.input = data
    response = MagicMock()
    response.content = [tool_block]
    return response


MINIMAL_VALID = {
    'title': '테스트 정책',
    'summary': '한 줄 요약',
    'confidence': 0.9,
    'flags': [],
}


class TestInputValidation:
    def test_empty_text_raises(self):
        with pytest.raises(PolicyParseError, match='비어 있습니다'):
            parse_policy('')

    def test_whitespace_only_raises(self):
        with pytest.raises(PolicyParseError, match='비어 있습니다'):
            parse_policy('   ')

    def test_too_short_raises(self):
        with pytest.raises(PolicyParseError, match='짧습니다'):
            parse_policy('짧음')


class TestSuccessPath:
    @patch('lib.parsing.policy_parser.client')
    def test_normal_parse(self, mock_client):
        mock_client.messages.create.return_value = _make_tool_use_response(MINIMAL_VALID)
        result = parse_policy('귀농인 대상 지원금 정책입니다. 만 65세 이상 옥천군 거주자.')
        assert result['confidence'] == 0.9
        assert result['parsed']['title'] == '테스트 정책'
        assert result['flags'] == []

    @patch('lib.parsing.policy_parser.client')
    def test_income_level_validation(self, mock_client):
        data = {**MINIMAL_VALID, 'income_level': ['기초수급', '중위150%', '일반']}
        mock_client.messages.create.return_value = _make_tool_use_response(data)
        result = parse_policy('귀농인 대상 지원금 정책입니다. 만 65세 이상 옥천군 거주자.')
        assert '중위150%' not in result['parsed']['income_level']
        assert '기초수급' in result['parsed']['income_level']

    @patch('lib.parsing.policy_parser.client')
    def test_confidence_clamped(self, mock_client):
        data = {**MINIMAL_VALID, 'confidence': 1.5}
        mock_client.messages.create.return_value = _make_tool_use_response(data)
        result = parse_policy('귀농인 대상 지원금 정책입니다. 만 65세 이상 옥천군 거주자.')
        assert result['confidence'] <= 1.0

    @patch('lib.parsing.policy_parser.client')
    def test_apply_end_date_valid_format_kept(self, mock_client):
        data = {**MINIMAL_VALID, 'apply_end_date': '2026-09-30'}
        mock_client.messages.create.return_value = _make_tool_use_response(data)
        result = parse_policy('귀농인 대상 지원금 정책입니다. 만 65세 이상 옥천군 거주자.')
        assert result['parsed']['apply_end_date'] == '2026-09-30'

    @patch('lib.parsing.policy_parser.client')
    def test_apply_end_date_non_date_text_nulled(self, mock_client):
        # '상시', '예산소진시까지' 등 비확정 표현은 null로 정규화
        data = {**MINIMAL_VALID, 'apply_end_date': '예산소진시까지'}
        mock_client.messages.create.return_value = _make_tool_use_response(data)
        result = parse_policy('귀농인 대상 지원금 정책입니다. 만 65세 이상 옥천군 거주자.')
        assert result['parsed']['apply_end_date'] is None

    @patch('lib.parsing.policy_parser.client')
    def test_apply_end_date_far_future_nulled(self, mock_client):
        # '9999-12-31', '2099-12-31' 같은 먼 미래 placeholder도 null로 정규화
        data = {**MINIMAL_VALID, 'apply_end_date': '2099-12-31'}
        mock_client.messages.create.return_value = _make_tool_use_response(data)
        result = parse_policy('귀농인 대상 지원금 정책입니다. 만 65세 이상 옥천군 거주자.')
        assert result['parsed']['apply_end_date'] is None


class TestApiErrors:
    @patch('lib.parsing.policy_parser.client')
    def test_rate_limit_error(self, mock_client):
        import anthropic
        mock_client.messages.create.side_effect = anthropic.RateLimitError(
            message='rate limit', response=MagicMock(), body={}
        )
        with pytest.raises(PolicyParseError, match='요청 한도'):
            parse_policy('귀농인 대상 지원금 정책입니다. 만 65세 이상 옥천군 거주자.')

    @patch('lib.parsing.policy_parser.client')
    def test_no_tool_use_block(self, mock_client):
        response = MagicMock()
        response.content = []  # tool_use 블록 없음
        response.stop_reason = 'end_turn'
        mock_client.messages.create.return_value = response
        with pytest.raises(PolicyParseError, match='거부'):
            parse_policy('귀농인 대상 지원금 정책입니다. 만 65세 이상 옥천군 거주자.')

    @patch('lib.parsing.policy_parser.client')
    def test_pydantic_validation_error(self, mock_client):
        # confidence 누락 → ValidationError → PolicyParseError
        mock_client.messages.create.return_value = _make_tool_use_response(
            {'title': '정책', 'summary': '요약'}  # confidence 없음
        )
        with pytest.raises(PolicyParseError, match='형식'):
            parse_policy('귀농인 대상 지원금 정책입니다. 만 65세 이상 옥천군 거주자.')
