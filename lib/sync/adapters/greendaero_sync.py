import logging
from datetime import datetime

import httpx

from apps.policies.models import Policy
from lib.exceptions import PolicyParseError
from lib.parsing.policy_parser import parse_policy

logger = logging.getLogger(__name__)

GREENDAERO_URL = 'https://www.greendaero.go.kr/svc/cmns/search/wise/searchTotalInfo.do'
GREENDAERO_DETAIL_URL = 'https://www.greendaero.go.kr/svc/rfph/cpif/front/policyDetail.do'
CONFIDENCE_THRESHOLD = 0.7


def _build_text(item: dict) -> str:
    parts = [
        item.get('TITLE', ''),
        item.get('IEM_CN1', ''),
        item.get('IEM_CN2', ''),
        item.get('IEM_CN3', ''),
        item.get('IEM_CN4', ''),
        item.get('IEM_CN5', ''),
    ]
    return '\n'.join(p for p in parts if p)


def _parse_date(value: str | None, fmt: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, fmt).date()
    except ValueError:
        return None


def sync_greendaero(max_items: int | None = None) -> dict:
    """그린대로(greendaero.go.kr) 농림축산식품사업 카탈로그를 동기화한다.

    `topic=A` 통합검색 결과 중 `CMNS_CD_NM`이 "농림축산식품사업"인 항목만 대상으로 한다
    (전국 단위 귀농·농업 지원사업으로, 시군구 코드 필터 없이도 범위가 정해져 있음).
    """
    try:
        res = httpx.get(
            GREENDAERO_URL,
            params={
                'query': '', 'ctpv_cd1': '', 'sgg_cd1': '',
                'ctpv_cd2': '', 'sgg_cd2': '', 'ctpv_cd3': '', 'sgg_cd3': '',
                'purpose': '', 'family': '', 'age': '',
                'topic': 'A', 'gnrlzInfoSbjtClsfcd': '', 'gnrlzInfoInstcd': '',
                'pageNum': 1, 'sort': 'DATE',
            },
            timeout=30,
        )
        res.raise_for_status()
    except httpx.HTTPError as e:
        logger.error('그린대로 API 요청 실패: %s', e)
        return {'saved': 0, 'skipped': 0, 'low_confidence': 0}

    items = [
        item for item in res.json().get('resultList', [])
        if '농림축산식품사업' in item.get('CMNS_CD_NM', '')
    ]

    saved = 0
    skipped = 0
    low_confidence = 0

    for item in items:
        if max_items is not None and saved + skipped + low_confidence >= max_items:
            break

        title = item.get('TITLE', '').strip()
        external_id = item.get('BBSCTT_SN', '').strip()

        if not title or not external_id:
            continue

        if Policy.objects.filter(title=title).exclude(source='귀농센터').exists():
            skipped += 1
            continue

        text = _build_text(item)

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
            'summary':      item.get('IEM_CN1', ''),
            'raw_text':     text,
            'source_url':   f'{GREENDAERO_DETAIL_URL}?bbscttSn={external_id}',
            'published_at': _parse_date(item.get('DATE'), '%Y.%m.%d'),
            'source':       '귀농센터',
            'is_active':    is_active,
        }
        if result:
            parsed = result['parsed']
            for field in ('min_age', 'max_age', 'region_codes', 'occupation_tags',
                          'income_level', 'amount_text', 'condition_tree', 'managing_org'):
                if parsed.get(field) is not None:
                    defaults[field] = parsed[field]
            if parsed.get('apply_end_date'):
                defaults['apply_end_date'] = _parse_date(parsed['apply_end_date'], '%Y-%m-%d')

        Policy.objects.update_or_create(
            external_id=external_id,
            source='귀농센터',
            defaults=defaults,
        )

        saved += 1

    logger.info('그린대로 동기화 완료 — saved=%d skipped=%d low_confidence=%d',
                saved, skipped, low_confidence)
    return {'saved': saved, 'skipped': skipped, 'low_confidence': low_confidence}
