import re
from typing import Any


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def build_poi_key(poi_name: str, city: str) -> str:
    return f"{slugify(poi_name)}__{slugify(city)}"


def merge_dicts(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    merged = {**secondary, **primary}
    for key, value in secondary.items():
        if isinstance(value, dict) and isinstance(primary.get(key), dict):
            merged[key] = merge_dicts(primary[key], value)
    return merged
