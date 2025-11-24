from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TIMEZONE = os.getenv("TIMEZONE", "Europe/Brussels")
OUT_DIR = Path(os.getenv("OUT_DIR", "out"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

PG_CONN = os.getenv("PG_CONN")
if not PG_CONN:
    host = os.getenv("PGHOST")
    port = os.getenv("PGPORT", "5432")
    db = os.getenv("PGDATABASE", "postgres")
    user = os.getenv("PGUSER", "postgres")
    pwd = os.getenv("PGPASSWORD", "")
    sslmode = os.getenv("PGSSLMODE", "require")
    PG_CONN = f"host={host} dbname={db} user={user} password={pwd} port={port} sslmode={sslmode}"
