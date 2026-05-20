import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from lib.exceptions import PolicyParseError, MatchingError

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    # 도메인 예외 → HTTP 응답으로 변환
    if isinstance(exc, PolicyParseError):
        return Response(
            {'error': str(exc), 'code': 'parse_error'},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if isinstance(exc, MatchingError):
        return Response(
            {'error': str(exc), 'code': 'matching_error'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    response = exception_handler(exc, context)

    if response is not None:
        # DRF가 이미 처리한 예외 — 포맷 통일
        response.data = {
            'error': _flatten_errors(response.data),
            'code': getattr(exc, 'default_code', 'error'),
        }
        return response

    # DRF가 처리하지 못한 예외 (DB 오류, 외부 API 오류 등)
    logger.exception('Unhandled exception in view', exc_info=exc)
    return Response(
        {'error': '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.', 'code': 'server_error'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _flatten_errors(data):
    if isinstance(data, list):
        return ' '.join(str(e) for e in data)
    if isinstance(data, dict):
        parts = []
        for key, val in data.items():
            msg = _flatten_errors(val)
            parts.append(f'{key}: {msg}' if key != 'detail' else msg)
        return ' '.join(parts)
    return str(data)
