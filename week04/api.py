"""A small read-only API over week 3's committed HKO tide data.

Run it as a local Python Worker:

    uv run pywrangler dev
"""

import json
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from workers import asgi

try:
    from .transform import parse_rows, select_month
except ImportError:  # The Worker loads api.py as a top-level module.
    from transform import parse_rows, select_month

DATA = Path(__file__).resolve().parent / "tides-QUB-2026.json"
app = FastAPI(title="Quarry Bay tides")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sd5913.github.io",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_methods=["GET"],
    allow_headers=[],
)


def load_rows():
    """Read the committed source file; never fetch from inside a request."""
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    return parse_rows(raw["data"])


@app.get("/tides")
def tides(month: int = Query(ge=1, le=12)):
    """Return one month's daily records as JSON."""
    return select_month(load_rows(), month)


# Cloudflare's Python ASGI adapter turns the FastAPI app into a Worker entrypoint.
Default = asgi.entrypoint(app)
