"""Exercise starter: the server works, but GET /tides is not implemented yet.

    uv run pywrangler dev week04/tdd_api.py

Add the route below, using the existing data loader and selection rule.
"""

from fastapi import FastAPI
from workers import asgi

from api import load_rows
from transform import select_month

app = FastAPI(title="Week 4 · test first")

# TODO: implement GET /tides with a required integer month query parameter.
# Return that month's records from load_rows().

Default = asgi.entrypoint(app)
