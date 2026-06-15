import logging

logger = logging.getLogger(__name__)

SUPPORTED_OPS = {'eq', 'in', 'gte', 'lte', 'between'}


def evaluate_tree(node: dict | None, profile: dict) -> bool:
    """condition_tree를 재귀적으로 평가한다. 오류 시 False 반환 (안전한 기본값)."""
    if node is None:
        return True

    try:
        return _evaluate(node, profile)
    except Exception as e:
        logger.error('condition_tree evaluation error: %s | node=%s', e, node)
        return False


def _evaluate(node: dict, profile: dict) -> bool:
    node_type = node.get('type')

    match node_type:
        case 'AND':
            children = node.get('children')
            if not isinstance(children, list) or not children:
                logger.warning('AND node has no children: %s', node)
                return True
            return all(_evaluate(c, profile) for c in children)

        case 'OR':
            children = node.get('children')
            if not isinstance(children, list) or not children:
                logger.warning('OR node has no children: %s', node)
                return False
            return any(_evaluate(c, profile) for c in children)

        case 'NOT':
            child = node.get('child')
            if child is None:
                logger.warning('NOT node has no child: %s', node)
                return True
            return not _evaluate(child, profile)

        case 'LEAF':
            return _evaluate_leaf(node, profile)

        case _:
            # AI가 생성한 condition_tree가 기대 스키마(type/children)를 따르지 않는 경우,
            # 정책을 매칭에서 제외하지 않도록 통과(True) 처리한다.
            logger.warning('Unknown node type: %s — 조건 평가 불가, 통과 처리', node_type)
            return True


def _evaluate_leaf(node: dict, profile: dict) -> bool:
    field = node.get('field')
    op    = node.get('op')
    value = node.get('value')

    if not field or not op:
        logger.warning('LEAF node missing field or op: %s', node)
        return False

    if op not in SUPPORTED_OPS:
        logger.warning('Unsupported op "%s" in node: %s', op, node)
        return False

    val = profile.get(field)
    if val is None:
        return False

    try:
        match op:
            case 'eq':
                return val == value
            case 'in':
                if not isinstance(value, list):
                    logger.warning('op=in requires list value, got: %s', value)
                    return False
                # val이 list(e.g. occupation_tags)면 하나라도 포함되면 True
                if isinstance(val, list):
                    return any(item in value for item in val)
                return val in value
            case 'gte':
                return val >= value
            case 'lte':
                return val <= value
            case 'between':
                if not isinstance(value, list) or len(value) != 2:
                    logger.warning('op=between requires [min, max] list, got: %s', value)
                    return False
                return value[0] <= val <= value[1]
    except TypeError as e:
        logger.warning('Type error evaluating leaf %s: %s', node, e)
        return False

    return False
