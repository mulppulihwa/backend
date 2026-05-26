import logging

logger = logging.getLogger(__name__)

# 온보딩 완료 판단 기준 필드
REQUIRED_FIELDS = ('region_code', 'birth_date', 'occupation_tags')


def is_profile_complete(profile) -> bool:
    return all(getattr(profile, f, None) for f in REQUIRED_FIELDS)


def sync_profile_completed(user) -> bool:
    """profile_completed를 프로필 상태에 맞게 갱신한다. 변경됐으면 True 반환."""
    complete = is_profile_complete(user.profile)
    if complete == user.profile_completed:
        return False
    user.profile_completed = complete
    user.save(update_fields=['profile_completed'])
    logger.info('profile_completed updated to %s for user %s', complete, user.pk)
    return True
