# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""Fetch, validate and atomically replace the HKO tide snapshot.

Run only when you intend to refresh the committed 2026 file:

    uv run week04/refresh_data.py
"""

import json
import math
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

URL = ("https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
       "?dataType=HHOT&station=QUB&year=2026&rformat=json")
ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    ROOT / "week03" / "data" / "tides-QUB-2026.json",
    ROOT / "week04" / "tides-QUB-2026.json",
]


def validate(payload):
    """Raise ValueError unless this looks like the expected full HKO year."""
    data = json.loads(payload)
    fields, rows = data.get("fields"), data.get("data")
    if fields != ["MM", "DD", *(f"{hour:02}" for hour in range(1, 25))]:
        raise ValueError("expected 26 HKO fields in order: MM, DD, 01 through 24")
    if not isinstance(rows, list) or len(rows) != 365:
        raise ValueError("expected 365 daily rows")
    if any(not isinstance(row, list) or len(row) != 26 for row in rows):
        raise ValueError("every daily row must have 26 values")
    dates = []
    for row in rows:
        month, day = int(row[0]), int(row[1])
        dates.append(date(2026, month, day))
        for value in row[2:]:
            if not math.isfinite(float(value)):
                raise ValueError("every height must be a finite number")
    expected = [date(2026, 1, 1) + timedelta(days=offset) for offset in range(365)]
    if dates != expected:
        raise ValueError("expected one row for every day of 2026 in date order")
    return data


def fetch(url=URL):
    import requests

    response = requests.get(url, timeout=60,
                            headers={"User-Agent": "SD5913 PolyU teaching example"})
    response.raise_for_status()
    validate(response.content)
    return response.content


def save_atomically(path, content):
    """Keep the old file if writing the new validated response fails."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(handle, "wb") as output:
            output.write(content)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def main():
    content = fetch()
    for target in TARGETS:
        save_atomically(target, content)
        print(f"validated and refreshed {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
