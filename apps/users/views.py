import logging

import httpx
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User

logger = logging.getLogger(__name__)

KAKAO_TOKEN_URL = 'https://kauth.kakao.com/oauth/token'
KAKAO_USER_URL  = 'https://kapi.kakao.com/v2/user/me'
KAKAO_TIMEOUT   = 10  # seconds


class KakaoAuthView(APIView):
    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response(
                {'error': 'code 파라미터가 필요합니다.', 'code': 'missing_code'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 카카오 토큰 교환
        try:
            token_res = httpx.post(
                KAKAO_TOKEN_URL,
                data={
                    'grant_type':    'authorization_code',
                    'client_id':     settings.KAKAO_CLIENT_ID,
                    'client_secret': settings.KAKAO_CLIENT_SECRET,
                    'redirect_uri':  settings.KAKAO_REDIRECT_URI,
                    'code':          code,
                },
                timeout=KAKAO_TIMEOUT,
            )
            token_res.raise_for_status()
        except httpx.TimeoutException:
            logger.warning('Kakao token exchange timed out')
            return Response(
                {'error': '카카오 서버 응답이 느립니다. 잠시 후 다시 시도해 주세요.', 'code': 'kakao_timeout'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except httpx.HTTPStatusError as e:
            logger.warning('Kakao token exchange failed: %s', e.response.text)
            return Response(
                {'error': '카카오 인증에 실패했습니다. 다시 로그인해 주세요.', 'code': 'kakao_auth_failed'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except httpx.RequestError as e:
            logger.error('Kakao token exchange network error: %s', e)
            return Response(
                {'error': '카카오 서버에 연결할 수 없습니다.', 'code': 'kakao_unreachable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        kakao_token_data = token_res.json()
        kakao_access_token = kakao_token_data.get('access_token')
        if not kakao_access_token:
            logger.error('Kakao response missing access_token: %s', kakao_token_data)
            return Response(
                {'error': '카카오 토큰을 받지 못했습니다.', 'code': 'kakao_no_token'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 카카오 사용자 정보 조회
        try:
            user_res = httpx.get(
                KAKAO_USER_URL,
                headers={'Authorization': f'Bearer {kakao_access_token}'},
                timeout=KAKAO_TIMEOUT,
            )
            user_res.raise_for_status()
        except httpx.TimeoutException:
            logger.warning('Kakao user info fetch timed out')
            return Response(
                {'error': '카카오 서버 응답이 느립니다.', 'code': 'kakao_timeout'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except httpx.HTTPStatusError as e:
            logger.warning('Kakao user info fetch failed: %s', e.response.text)
            return Response(
                {'error': '사용자 정보 조회에 실패했습니다.', 'code': 'kakao_user_fetch_failed'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except httpx.RequestError as e:
            logger.error('Kakao user info network error: %s', e)
            return Response(
                {'error': '카카오 서버에 연결할 수 없습니다.', 'code': 'kakao_unreachable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        kakao_user = user_res.json()

        try:
            kakao_id = str(kakao_user['id'])
            nickname = (
                kakao_user
                .get('kakao_account', {})
                .get('profile', {})
                .get('nickname', '')
            )
        except (KeyError, TypeError) as e:
            logger.error('Unexpected Kakao user response structure: %s | %s', kakao_user, e)
            return Response(
                {'error': '카카오 사용자 정보 형식이 올바르지 않습니다.', 'code': 'kakao_bad_response'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        user, _ = User.objects.get_or_create(
            kakao_id=kakao_id,
            defaults={'nickname': nickname},
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access':            str(refresh.access_token),
            'refresh':           str(refresh),
            'profile_completed': user.profile_completed,
        })
