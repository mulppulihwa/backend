import logging

import httpx
from django.conf import settings

from apps.policies.models import Policy
from lib.exceptions import PolicyParseError
from lib.parsing.policy_parser import parse_policy

logger = logging.getLogger(__name__)

BOKJIRO_URL = 'https://api.odcloud.kr/api/gov24/v3/serviceList'
CONFIDENCE_THRESHOLD = 0.7

BENEFIT_TYPE_MAP = {
    '현금': '현금지원',
    '현물': '현물',
    '서비스': '기타',
    '이용권': '현금지원',
    '감면': '세금감면',
    '교육': '교육',
    '컨설팅': '컨설팅',
    '시설': '시설',
}


def _map_benefit_type(raw: str) -> str:
    for key, val in BENEFIT_TYPE_MAP.items():
        if key in raw:
            return val
    return '기타'


def sync_bokjiro(per_page: int = 100, max_items: int | None = None) -> dict:
    """복지로 API 전체 페이지를 순환하며 정책을 동기화한다."""
    api_key = getattr(settings, 'BOKJIRO_API_KEY', '')
    if not api_key:
        raise RuntimeError('BOKJIRO_API_KEY 환경변수가 설정되지 않았습니다.')

    saved = 0
    skipped = 0
    low_confidence = 0
    processed = 0
    page = 1

    while True:
        try:
            res = httpx.get(
                BOKJIRO_URL,
                params={'page': page, 'perPage': per_page, 'serviceKey': api_key},
                timeout=30,
            )
            res.raise_for_status()
        except httpx.HTTPError as e:
            logger.error('복지로 API 요청 실패 (page=%d): %s', page, e)
            break

        body = res.json()
        data = body.get('data', [])
        if not data:
            break

        total_count = body.get('totalCount', 0)

        for item in data:
            if max_items is not None and processed >= max_items:
                break

            title = item.get('서비스명', '').strip()
            external_id = item.get('서비스ID', '').strip()

            if not title or not external_id:
                continue

            # 수동입력·귀농센터 소스와 제목 충돌 시 스킵
            if Policy.objects.filter(title=title).exclude(source='복지로').exists():
                skipped += 1
                continue

            text = f"{item.get('지원대상', '')} {item.get('선정기준', '')}".strip()

            try:
                result = parse_policy(text) if len(text) >= 30 else None
            except PolicyParseError as e:
                logger.warning('파싱 실패 (%s): %s', title, e)
                result = None

            is_active = bool(result and result['confidence'] >= CONFIDENCE_THRESHOLD)
            if result and not is_active:
                low_confidence += 1

            defaults = {
                'title':        title,
                'summary':      item.get('서비스목적요약', ''),
                'description':  item.get('지원내용', ''),
                'raw_text':     '\n'.join(filter(None, [
                                    item.get('지원대상', ''),
                                    item.get('선정기준', ''),
                                    item.get('지원내용', ''),
                                ])),
                'managing_org': item.get('소관기관명', ''),
                'apply_url':    item.get('상세조회URL', ''),
                'benefit_type': _map_benefit_type(item.get('지원유형', '')),
                'source':       '복지로',
                'is_active':    is_active,
            }
            if result:
                parsed = result['parsed']
                for field in ('min_age', 'max_age', 'region_codes', 'occupation_tags',
                              'income_level', 'amount_text', 'condition_tree'):
                    if parsed.get(field) is not None:
                        defaults[field] = parsed[field]

            Policy.objects.update_or_create(
                external_id=external_id,
                source='복지로',
                defaults=defaults,
            )
            saved += 1
            processed += 1

        if max_items is not None and processed >= max_items:
            break
        if page * per_page >= total_count:
            break
        page += 1

    logger.info('복지로 동기화 완료 — saved=%d skipped=%d low_confidence=%d',
                saved, skipped, low_confidence)
    return {'saved': saved, 'skipped': skipped, 'low_confidence': low_confidence}
