import logging

import anthropic
from pydantic import BaseModel, ValidationError

from lib.exceptions import PolicyParseError

logger = logging.getLogger(__name__)

client = anthropic.Anthropic()

MAX_TEXT_LENGTH = 20_000


class ChecklistItemParsed(BaseModel):
    order: int
    label: str


class ParsedChecklist(BaseModel):
    items: list[ChecklistItemParsed] = []


CHECKLIST_TOOL = {
    'name': 'extract_checklist_items',
    'description': '정책 공고문에서 신청 시 필요한 준비물(서류, 자격 등) 목록을 추출합니다',
    'input_schema': {
        'type': 'object',
        'properties': {
            'items': {
                'type': 'array',
                'description': '준비물 항목 목록. 순서대로 번호를 매긴다.',
                'items': {
                    'type': 'object',
                    'properties': {
                        'order': {'type': 'integer', 'description': '순서 (0부터 시작)'},
                        'label': {'type': 'string', 'description': '준비물 항목명 (예: 농업경영체 등록증)'},
                    },
                    'required': ['order', 'label'],
                },
            },
        },
        'required': ['items'],
    },
}


def parse_checklist(title: str, raw_text: str) -> list[dict]:
    """raw_text에서 준비물 목록을 추출해 [{order, label}] 반환."""
    if not raw_text or not raw_text.strip():
        raise PolicyParseError('공고문 텍스트가 비어 있습니다.')

    text = raw_text.strip()
    if len(text) > MAX_TEXT_LENGTH:
        logger.warning('Checklist parse: text truncated from %d to %d chars', len(text), MAX_TEXT_LENGTH)
        text = text[:MAX_TEXT_LENGTH]

    prompt = (
        f'정책명: {title}\n\n'
        f'공고문:\n{text}\n\n'
        '위 공고문에서 신청자가 준비해야 할 서류, 자격증, 확인서 등 준비물 목록을 추출해줘. '
        '공고문에 준비물 정보가 없으면 items를 빈 배열로 반환해.'
    )

    try:
        response = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=512,
            tools=[CHECKLIST_TOOL],
            tool_choice={'type': 'tool', 'name': 'extract_checklist_items'},
            messages=[{'role': 'user', 'content': prompt}],
        )
    except anthropic.RateLimitError:
        raise PolicyParseError('AI 서버 요청 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.')
    except anthropic.APITimeoutError:
        raise PolicyParseError('AI 서버 응답 시간이 초과됐습니다. 잠시 후 다시 시도해 주세요.')
    except anthropic.APIStatusError as e:
        logger.error('Anthropic API error %s: %s', e.status_code, e.message)
        raise PolicyParseError(f'AI 서버 오류가 발생했습니다 (HTTP {e.status_code}).')
    except anthropic.APIConnectionError as e:
        logger.error('Anthropic connection error: %s', e)
        raise PolicyParseError('AI 서버에 연결할 수 없습니다.')

    tool_use = next((b for b in response.content if b.type == 'tool_use'), None)
    if not tool_use:
        raise PolicyParseError('AI가 준비물 추출을 거부했습니다.')

    try:
        parsed = ParsedChecklist(**tool_use.input)
    except ValidationError as e:
        logger.error('Checklist parse validation error: %s | input: %s', e, tool_use.input)
        raise PolicyParseError('AI 응답 형식이 올바르지 않습니다.')

    return [item.model_dump() for item in parsed.items]
