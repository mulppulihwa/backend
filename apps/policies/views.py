import logging
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lib.matching.policy_matcher import match_policies
from lib.parsing.policy_parser import PolicyParseError, parse_policy
from .models import Policy
from .serializers import PolicyCardSerializer, PolicyDetailSerializer

logger = logging.getLogger(__name__)


class PolicyPreviewView(APIView):
    """비로그인 홈용 최신·마감임박 정책 3개."""

    def get(self, request):
        try:
            today = timezone.now().date()
            deadline_soon = list(
                Policy.objects.filter(
                    is_active=True,
                    apply_end_date__range=(today, today + timedelta(days=7)),
                ).order_by('apply_end_date')[:3]
            )
            rest = list(
                Policy.objects.filter(is_active=True)
                .exclude(apply_end_date__range=(today, today + timedelta(days=7)))
                .order_by('-created_at')[: max(0, 3 - len(deadline_soon))]
            )
            policies = (deadline_soon + rest)[:3]
        except DatabaseError as e:
            logger.error('DB error in PolicyPreviewView: %s', e)
            return Response(
                {'error': '정책 목록을 불러오는 중 오류가 발생했습니다.', 'code': 'db_error'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(PolicyCardSerializer(policies, many=True).data)


class PolicyMatchView(APIView):
    """로그인 사용자 맞춤 정책 매칭."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except ObjectDoesNotExist:
            return Response(
                {'error': '프로필이 아직 작성되지 않았습니다. 온보딩을 완료해 주세요.', 'code': 'profile_missing'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not request.user.profile_completed:
            return Response(
                {'error': '프로필 작성을 완료해야 맞춤 정책을 확인할 수 있습니다.', 'code': 'profile_incomplete'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile_dict = _build_profile_dict(profile)
        result = match_policies(profile_dict)

        if 'error' in result:
            return Response(
                {'error': result['error'], 'code': 'match_error'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        today = timezone.now().date()
        policies_data = PolicyCardSerializer(result['policies'], many=True).data

        # days_left, match_reason 주입
        for item, policy in zip(policies_data, result['policies']):
            if policy.apply_end_date:
                item['days_left'] = (policy.apply_end_date - today).days
            else:
                item['days_left'] = None
            item['match_reason'] = _build_match_reason(policy, profile_dict)

        return Response({
            'policies': policies_data,
            'total':    len(policies_data),
            'fallback': result['fallback'],
        })


class PolicyParseView(APIView):
    """공고문 → 정책 조건 자동 파싱 (Admin 전용)."""

    permission_classes = [IsAdminUser]

    def post(self, request):
        text = request.data.get('text', '')
        if not text:
            return Response(
                {'error': 'text 필드가 필요합니다.', 'code': 'missing_text'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = parse_policy(text)
        except PolicyParseError as e:
            return Response(
                {'error': str(e), 'code': 'parse_error'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response(result)


# ── helpers ──────────────────────────────────────────────────────────────────

def _build_profile_dict(profile) -> dict:
    return {
        'region_code':         profile.region_code,
        'age':                 profile.age,
        'gender':              profile.gender,
        'occupation_tags':     profile.occupation_tags,
        'household_type':      profile.household_type,
        'income_level':        profile.income_level,
        'marital_status':      profile.marital_status,
        'is_farm_registered':  profile.is_farm_registered,
        'farm_registered_date': str(profile.farm_registered_date) if profile.farm_registered_date else None,
        'education_hours':     profile.education_hours,
        'non_farm_income':     profile.non_farm_income,
        'years_since_move':    profile.years_since_move,
        'move_in_date':        str(profile.move_in_date) if profile.move_in_date else None,
        'is_disabled':         profile.is_disabled,
    }


def _build_match_reason(policy: Policy, profile: dict) -> str:
    parts = []
    if profile.get('occupation_tags'):
        overlap = set(policy.occupation_tags) & set(profile['occupation_tags'])
        if overlap:
            parts.append(', '.join(overlap))
    if profile.get('region_code') and policy.region_codes:
        parts.append('지역 조건 충족')
    if policy.min_age > 0 or policy.max_age < 130:
        age = profile.get('age')
        if age is not None:
            parts.append(f'{age}세')
    return ', '.join(parts) if parts else '기본 매칭'
