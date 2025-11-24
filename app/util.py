from __future__ import annotations
import json, uuid
from datetime import date, datetime
from typing import Any

class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, uuid.UUID):
            return str(o)
        return super().default(o)

def to_json(data: Any, **kwargs) -> str:
    kwargs.setdefault("ensure_ascii", False)
    kwargs.setdefault("indent", 2)
    return json.dumps(data, cls=ExtendedJSONEncoder, **kwargs)
