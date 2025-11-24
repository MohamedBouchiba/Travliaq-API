from __future__ import annotations
import logging
from typing import Any, Dict
import psycopg
from psycopg.rows import dict_row
from .config import PG_CONN, TIMEZONE

log = logging.getLogger(__name__)
SQL_FETCH = "SELECT * FROM public.questionnaire_responses WHERE id = %s"

def fetch_row_by_id(response_id: str) -> Dict[str, Any]:
    log.info("SQL: %s ; params: (%s,)", SQL_FETCH, response_id)
    with psycopg.connect(PG_CONN) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"SET TIME ZONE '{TIMEZONE}'")
            cur.execute(SQL_FETCH, (response_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"No row found for id={response_id}")
            log.debug("DB row (python types): %r", row)
            return dict(row)
