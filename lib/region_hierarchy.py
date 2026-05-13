import logging

from django.db import DatabaseError, connection, OperationalError

logger = logging.getLogger(__name__)


def get_ancestor_codes(region_code: str) -> list[str]:
    """지역 코드의 상위 계층 코드를 모두 반환한다.

    DB 오류 시 원래 코드만 담은 리스트를 반환해 매칭이 완전히 깨지지 않도록 한다.
    """
    if not region_code or not isinstance(region_code, str):
        return []

    region_code = region_code.strip()
    if not region_code:
        return []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH RECURSIVE ancestors AS (
                    SELECT code, parent_code
                    FROM regions
                    WHERE code = %s
                    UNION ALL
                    SELECT r.code, r.parent_code
                    FROM regions r
                    JOIN ancestors a ON r.code = a.parent_code
                    WHERE a.parent_code IS NOT NULL
                )
                SELECT ARRAY_AGG(code) FROM ancestors
                """,
                [region_code],
            )
            row = cursor.fetchone()
    except OperationalError as e:
        logger.error('DB connection error in get_ancestor_codes(%s): %s', region_code, e)
        return [region_code]
    except DatabaseError as e:
        logger.error('DB error in get_ancestor_codes(%s): %s', region_code, e)
        return [region_code]

    if not row or not row[0]:
        # regions 테이블에 해당 코드가 없을 때 — 자기 자신만 반환
        logger.warning('region_code not found in DB: %s', region_code)
        return [region_code]

    return row[0]
