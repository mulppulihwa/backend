"""
프로젝트 공통 예외 클래스.
모든 커스텀 예외는 여기서 정의하고 각 모듈에서 import해 사용.
"""

from rest_framework import status
from rest_framework.exceptions import APIException


# ── 도메인 예외 (비-HTTP, lib/에서 raise) ──────────────────────────────────

class PolicyParseError(Exception):
    """공고문 파싱 실패 — 호출자가 사용자에게 안내할 수 있도록 구체적인 메시지 포함."""


class MatchingError(Exception):
    """정책 매칭 파이프라인 오류."""


# ── DRF API 예외 (views에서 raise → DRF가 자동으로 Response 변환) ──────────

class KakaoAuthError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = 'kakao_auth_failed'
    default_detail = '카카오 인증에 실패했습니다. 다시 로그인해 주세요.'


class KakaoUnavailableError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = 'kakao_unreachable'
    default_detail = '카카오 서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.'


class ProfileIncompleteError(APIException):
    """진단 미완료 사용자가 매칭 API 호출 시."""
    status_code = status.HTTP_403_FORBIDDEN
    default_code = 'profile_incomplete'
    default_detail = '진단을 먼저 완료해 주세요.'


class PolicyNotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'policy_not_found'
    default_detail = '해당 정책을 찾을 수 없습니다.'
