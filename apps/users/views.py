import logging
import threading

import httpx
from django.core.cache import cache
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.policies.models import ChecklistItem, Policy
from lib.diagnosis_service import sync_profile_completed
from lib.parsing.checklist_parser import parse_checklist
from lib.exceptions import PolicyParseError
from .models import User, UserPolicy
from .serializers import UserPolicySerializer, UserProfileSerializer

logger = logging.getLogger(__name__)

def _parse_checklist_bg(policy):
    try:
        items = parse_checklist(policy.title, policy.raw_text)
        if items:
            ChecklistItem.objects.bulk_create([
                ChecklistItem(policy=policy, order=item['order'], label=item['label'])
                for item in items
            ])
            cache.delete(f'checklist:{policy.pk}')
    except PolicyParseError as e:
        logger.warning('Background checklist parse failed for policy %s: %s', policy.pk, e)
    except Exception as e:
        logger.error('Unexpected error in background checklist parse for policy %s: %s', policy.pk, e)


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



class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user.profile)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user.profile,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors, 'code': 'invalid_profile'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile = serializer.save()
        sync_profile_completed(request.user)
        return Response(serializer.data)


class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        nickname = request.data.get('nickname')
        if not nickname or not str(nickname).strip():
            return Response(
                {'error': 'nickname 필드가 필요합니다.', 'code': 'missing_nickname'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.nickname = str(nickname).strip()
        request.user.save(update_fields=['nickname'])
        return Response({'nickname': request.user.nickname})


class UserPolicyListView(APIView):
    """저장된 정책 목록 조회."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            UserPolicy.objects
            .filter(profile=request.user.profile)
            .select_related('policy')
            .order_by('-created_at')
        )
        return Response(UserPolicySerializer(qs, many=True).data)


class UserPolicySaveView(APIView):
    """정책 저장 (UserPolicy 생성)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, policy_id):
        try:
            policy = Policy.objects.get(pk=policy_id, is_active=True)
        except Policy.DoesNotExist:
            return Response(
                {'error': '정책을 찾을 수 없습니다.', 'code': 'policy_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        user_policy, created = UserPolicy.objects.get_or_create(
            profile=request.user.profile,
            policy=policy,
        )

        if created and not ChecklistItem.objects.filter(policy=policy).exists():
            threading.Thread(
                target=_parse_checklist_bg,
                args=(policy,),
                daemon=True,
            ).start()

        return Response(
            UserPolicySerializer(user_policy).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class UserPolicyStatusView(APIView):
    """저장된 정책 상태 변경."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, policy_id):
        try:
            user_policy = UserPolicy.objects.get(
                profile=request.user.profile,
                policy_id=policy_id,
            )
        except UserPolicy.DoesNotExist:
            return Response(
                {'error': '저장된 정책을 찾을 수 없습니다.', 'code': 'user_policy_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get('status')
        if new_status not in UserPolicy.Status.values:
            return Response(
                {'error': f'유효하지 않은 상태입니다. 가능한 값: {UserPolicy.Status.values}', 'code': 'invalid_status'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_policy.status = new_status
        user_policy.save(update_fields=['status'])
        return Response(UserPolicySerializer(user_policy).data)


class UserPolicyChecklistView(APIView):
    """저장된 정책의 준비물 체크 상태 업데이트."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, policy_id):
        try:
            user_policy = UserPolicy.objects.get(
                profile=request.user.profile,
                policy_id=policy_id,
            )
        except UserPolicy.DoesNotExist:
            return Response(
                {'error': '저장된 정책을 찾을 수 없습니다.', 'code': 'user_policy_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        checked_items = request.data.get('checked_items')
        if not isinstance(checked_items, list) or not all(isinstance(i, int) for i in checked_items):
            return Response(
                {'error': 'checked_items는 정수 배열이어야 합니다.', 'code': 'invalid_checked_items'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_ids = set(
            ChecklistItem.objects.filter(policy_id=policy_id)
            .values_list('id', flat=True)
        )
        invalid = [i for i in checked_items if i not in valid_ids]
        if invalid:
            return Response(
                {'error': f'존재하지 않는 항목 id: {invalid}', 'code': 'invalid_item_ids'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_policy.checked_items = list(set(checked_items))
        user_policy.save(update_fields=['checked_items'])
        return Response(UserPolicySerializer(user_policy).data)
