import logging
from typing import Optional

import anthropic
from pydantic import BaseModel, ValidationError, field_validator

logger = logging.getLogger(__name__)

client = anthropic.Anthropic()

MAX_TEXT_LENGTH = 20_000  # Claude context 낭비 방지


class ParsedPolicy(BaseModel):
    title:           str
    summary:         str
    min_age:         int = 0
    max_age:         int = 130
    region_codes:    list[str] = []
    occupation_tags: list[str] = []
    household_type:  list[str] = []
    income_level:    list[str] = []
    move_status:     list[str] = []
    amount_text:     Optional[str] = None
    apply_end_date:  Optional[str] = None
    managing_org:    Optional[str] = None
    condition_tree:  Optional[dict] = None
    confidence:      float
    flags:           list[str] = []

    @field_validator('income_level')
    def validate_income(cls, v):
        allowed = {'기초수급', '차상위', '일반'}
        return [x for x in v if x in allowed]

    @field_validator('confidence')
    def validate_confidence(cls, v):
        return max(0.0, min(1.0, float(v)))


PARSE_TOOL = {
    'name': 'extract_policy_conditions',
    'description': '정책 공고문에서 신청 자격 조건을 추출합니다',
    'input_schema': {
        'type': 'object',
        'properties': {
            'title':           {'type': 'string', 'description': '정책명'},
            'summary':         {'type': 'string', 'description': '한 줄 요약 (쉬운 말)'},
            'min_age':         {'type': 'integer', 'description': '최소 나이 (없으면 0)'},
            'max_age':         {'type': 'integer', 'description': '최대 나이 (없으면 130)'},
            'region_codes':    {'type': 'array', 'items': {'type': 'string'},
                                'description': '지역 코드. 옥천군=43720, 충청북도=43, 전국=[]'},
            'occupation_tags': {'type': 'array', 'items': {'type': 'string'},
                                'description': '가능한 값: 귀농, 귀촌, 노인, 여성농업인'},
            'income_level':    {'type': 'array', 'items': {'type': 'string'},
                                'description': '가능한 값: 기초수급, 차상위, 일반'},
            'amount_text':     {'type': 'string', 'description': '지원 금액 (예: 최대 300만원)'},
            'apply_end_date':  {'type': 'string', 'description': '신청 마감일 YYYY-MM-DD'},
            'managing_org':    {'type': 'string', 'description': '담당 기관명'},
            'condition_tree':  {'type': 'object',
                                'description': '단순 태그로 표현 불가한 복합 조건만'},
            'confidence':      {'type': 'number',
                                'description': '파싱 신뢰도 0~1'},
            'flags':           {'type': 'array', 'items': {'type': 'string'},
                                'description': '불확실하게 해석한 필드 목록'},
        },
        'required': ['title', 'summary', 'confidence', 'flags'],
    },
}


class PolicyParseError(Exception):
    """파싱 실패 — 호출자가 사용자에게 안내할 수 있도록 구체적인 메시지 포함."""


def parse_policy(text: str) -> dict:
    if not text or not text.strip():
        raise PolicyParseError('공고문 텍스트가 비어 있습니다.')

    text = text.strip()
    if len(text) < 30:
        raise PolicyParseError('공고문이 너무 짧습니다. 최소 30자 이상 입력해 주세요.')

    if len(text) > MAX_TEXT_LENGTH:
        logger.warning('Policy text truncated from %d to %d chars', len(text), MAX_TEXT_LENGTH)
        text = text[:MAX_TEXT_LENGTH]

    try:
        response = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=1024,
            tools=[PARSE_TOOL],
            tool_choice={'type': 'auto'},
            messages=[{
                'role': 'user',
                'content': f'다음 정책 공고문에서 신청 자격 조건을 추출해줘.\n\n{text}',
            }],
        )
    except anthropic.RateLimitError:
        logger.warning('Anthropic rate limit reached')
        raise PolicyParseError('AI 서버 요청 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.')
    except anthropic.APITimeoutError:
        logger.warning('Anthropic API timeout')
        raise PolicyParseError('AI 서버 응답 시간이 초과됐습니다. 잠시 후 다시 시도해 주세요.')
    except anthropic.APIStatusError as e:
        logger.error('Anthropic API error %s: %s', e.status_code, e.message)
        raise PolicyParseError(f'AI 서버 오류가 발생했습니다 (HTTP {e.status_code}).')
    except anthropic.APIConnectionError as e:
        logger.error('Anthropic connection error: %s', e)
        raise PolicyParseError('AI 서버에 연결할 수 없습니다.')

    tool_use = next(
        (b for b in response.content if b.type == 'tool_use'), None
    )
    if not tool_use:
        logger.error('Claude did not call the tool. Stop reason: %s', response.stop_reason)
        raise PolicyParseError('AI가 조건 추출을 거부했습니다. 공고문 내용을 확인해 주세요.')

    try:
        parsed = ParsedPolicy(**tool_use.input)
    except ValidationError as e:
        logger.error('Claude output failed Pydantic validation: %s | input: %s', e, tool_use.input)
        raise PolicyParseError('AI 응답 형식이 올바르지 않습니다. 다시 시도해 주세요.')

    return {
        'parsed':     parsed.model_dump(),
        'confidence': parsed.confidence,
        'flags':      parsed.flags,
    }
