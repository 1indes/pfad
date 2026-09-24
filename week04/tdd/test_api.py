"""One first API check: the route responds with the expected JSON shape."""

from json import load
from urllib.request import urlopen

API = "http://127.0.0.1:8787/tides?month=9"


def test_september_tides_returns_daily_records():
    with urlopen(API, timeout=10) as response:
        assert response.status == 200
        rows = load(response)

    assert rows[0]["month"] == 9
    assert rows[0]["day"] == 1
    assert len(rows[0]["heights"]) == 24
    assert all(isinstance(height, (int, float)) for height in rows[0]["heights"])
