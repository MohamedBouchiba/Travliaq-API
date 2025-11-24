from __future__ import annotations
import logging
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from .config import OUT_DIR, LOG_LEVEL
from .db import fetch_row_by_id, SQL_FETCH
from .schema_loader import load_schema
from .enrich import build_enriched
from .util import to_json
from fastapi.encoders import jsonable_encoder

logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
log = logging.getLogger("travliaq.api")

app = FastAPI(title="Travliaq API - Normalize & Enrich")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/responses/{response_id}")
def get_response(response_id: str, write: bool = Query(False, description="Write flat_raw.json and enrich.json")):
    try:
        row = fetch_row_by_id(response_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    flat_raw = row
    schema = load_schema()
    enriched = build_enriched(row, schema)

    out_paths: Dict[str, str] = {}
    if write:
        outdir = OUT_DIR / response_id
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "flat_raw.json").write_text(to_json(flat_raw), encoding="utf-8")
        (outdir / "enrich.json").write_text(to_json(enriched), encoding="utf-8")
        out_paths = {
            "flat_raw_path": str(outdir / "flat_raw.json"),
            "enrich_path": str(outdir / "enrich.json"),
        }

    payload: Dict[str, Any] = {
        "sql": {"query": SQL_FETCH, "params": [response_id]},
        "flat_raw": flat_raw,
        "enriched": enriched,
        **({"written": out_paths} if write else {})
    }
    content = jsonable_encoder(enriched if not write else payload)
    return JSONResponse(content=content)
