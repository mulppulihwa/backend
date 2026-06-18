import logging

from django.db import DatabaseError
from django.utils import timezone

from apps.policies.models import Policy
from .condition_tree import evaluate_tree

logger = logging.getLogger(__name__)

MATCH_LIMIT = 5

# 옥천 큐레이션(옥천군청/수동입력) > 귀농센터 > 복지로 순으로 노출
SOURCE_PRIORITY = {'옥천군청': 0, '옥천군 농업기술센터': 0, '수동입력': 0, '귀농센터': 1, '복지로': 2}

# 매칭 결과에 노출할 출처 — 옥천군 직접 큐레이션 정책만 대상
LOCAL_SOURCES = [k for k, v in SOURCE_PRIORITY.items() if v == 0]


def match_policies(user_profile: dict) -> dict:
    """사용자 프로필로 맞춤 정책을 매칭한다.

    DB 오류 등 예외 발생 시 빈 결과 대신 fallback 정책을 반환한다.
    """
    age      = user_profile.get('age') or 0
    occ_tags = user_profile.get('occupation_tags') or []
    income   = user_profile.get('income_level', '')

    try:
        matched = _run_matching(age, occ_tags, income, user_profile)
    except DatabaseError as e:
        logger.error('DB error during policy matching: %s', e)
        return {'policies': [], 'fallback': True, 'error': 'DB 오류로 매칭에 실패했습니다.'}
    except Exception as e:
        logger.error('Unexpected error during policy matching: %s', e)
        return {'policies': [], 'fallback': True, 'error': '매칭 중 오류가 발생했습니다.'}

    fallback = len(matched) == 0
    if fallback:
        try:
            matched = list(
                Policy.objects.filter(is_active=True, source__in=LOCAL_SOURCES)
                .order_by('-created_at')[:MATCH_LIMIT]
            )
        except DatabaseError as e:
            logger.error('DB error fetching fallback policies: %s', e)
            matched = []
    else:
        matched = matched[:MATCH_LIMIT]

    return {'policies': matched, 'fallback': fallback}


def _run_matching(
    age: int,
    occ_tags: list[str],
    income: str,
    user_profile: dict,
) -> list[Policy]:
    qs = Policy.objects.filter(
        is_active=True,
        source__in=LOCAL_SOURCES,
        min_age__lte=age,
        max_age__gte=age,
    )

    if occ_tags:
        # occupation_tags 없는 정책(전체 대상)도 포함
        qs = qs.filter(occupation_tags__exact=[]) | qs.filter(
            occupation_tags__overlap=occ_tags
        )

    if income:
        # income_level 없는 정책(전체 소득 대상)도 포함
        qs = qs.filter(income_level__exact=[]) | qs.filter(
            income_level__contains=[income]
        )

    is_disabled = user_profile.get('is_disabled')
    if is_disabled is not None:
        # disability_required=None(무관) 정책은 항상 포함
        # disability_required=True 정책은 장애인 사용자에게만, False는 비장애인에게만
        qs = qs.filter(disability_required__isnull=True) | qs.filter(
            disability_required=is_disabled
        )

    # 이전 거주지가 농촌(읍/면)이었던 사용자는 도시→농촌 이주를 전제로 하는 귀농 정책 대상이 아님.
    # 도시 출신/미답변은 귀농 여부가 불확실하므로 필터링하지 않고 노출 후 사용자가 직접 확인하게 둔다.
    if user_profile.get('prev_residence_is_rural') is True:
        qs = qs.exclude(occupation_tags__contains=['귀농'])

    # condition_tree 2차 평가 — evaluate_tree는 내부적으로 예외를 잡아 False 반환
    matched = [p for p in qs if evaluate_tree(p.condition_tree, user_profile)]

    # 정렬: 출처 우선순위(옥천군청/수동입력 > 귀농센터 > 복지로) → 그 안에서 마감 임박 순
    today = timezone.now().date()

    def sort_key(p: Policy):
        source_rank = SOURCE_PRIORITY.get(p.source, len(SOURCE_PRIORITY))
        if p.apply_end_date:
            days_left = (p.apply_end_date - today).days
            return (source_rank, 0, days_left)
        return (source_rank, 1, 0)

    matched.sort(key=sort_key)
    return matched
