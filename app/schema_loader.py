from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schemas" / "questionnaire-response.schema.json"

@lru_cache(maxsize=1)
def load_schema() -> dict:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
