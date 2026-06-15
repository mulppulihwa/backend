"""geocoding.py 유닛 테스트 — 카카오 로컬 API를 mock으로 대체."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import httpx

from lib.services.geocoding import geocode_address


class TestGeocodeAddress:
    def test_empty_address_returns_none(self):
        assert geocode_address('') is None

    @patch('lib.services.geocoding.settings')
    def test_missing_api_key_returns_none(self, mock_settings):
        mock_settings.KAKAO_LOCAL_API_KEY = ''
        assert geocode_address('충북 옥천군 옥천읍') is None

    @patch('lib.services.geocoding.httpx.get')
    @patch('lib.services.geocoding.settings')
    def test_success_returns_lat_lng(self, mock_settings, mock_get):
        mock_settings.KAKAO_LOCAL_API_KEY = 'test-key'
        response = MagicMock()
        response.json.return_value = {
            'documents': [{'y': '36.3061', 'x': '127.5717'}],
        }
        mock_get.return_value = response

        result = geocode_address('충북 옥천군 옥천읍')

        assert result == (Decimal('36.3061'), Decimal('127.5717'))

    @patch('lib.services.geocoding.httpx.get')
    @patch('lib.services.geocoding.settings')
    def test_no_results_returns_none(self, mock_settings, mock_get):
        mock_settings.KAKAO_LOCAL_API_KEY = 'test-key'
        response = MagicMock()
        response.json.return_value = {'documents': []}
        mock_get.return_value = response

        assert geocode_address('존재하지 않는 주소') is None

    @patch('lib.services.geocoding.httpx.get')
    @patch('lib.services.geocoding.settings')
    def test_http_error_returns_none(self, mock_settings, mock_get):
        mock_settings.KAKAO_LOCAL_API_KEY = 'test-key'
        mock_get.side_effect = httpx.ConnectError('connection failed')

        assert geocode_address('충북 옥천군 옥천읍') is None
