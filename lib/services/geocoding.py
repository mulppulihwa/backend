"""주소 → 좌표 변환 (카카오 로컬 API, 주소 검색)."""

import logging
from decimal import Decimal

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

KAKAO_GEOCODE_URL = 'https://dapi.kakao.com/v2/local/search/address.json'
GEOCODE_TIMEOUT = 5  # seconds


def geocode_address(address: str) -> tuple[Decimal, Decimal] | None:
    """주소 문자열을 (lat, lng)로 변환. 변환 실패 시 None."""
    if not settings.KAKAO_LOCAL_API_KEY or not address:
        return None

    try:
        res = httpx.get(
            KAKAO_GEOCODE_URL,
            params={'query': address},
            headers={'Authorization': f'KakaoAK {settings.KAKAO_LOCAL_API_KEY}'},
            timeout=GEOCODE_TIMEOUT,
        )
        res.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning('Kakao geocoding failed for %r: %s', address, e)
        return None

    documents = res.json().get('documents', [])
    if not documents:
        logger.info('Kakao geocoding returned no results for %r', address)
        return None

    doc = documents[0]
    return Decimal(doc['y']), Decimal(doc['x'])
