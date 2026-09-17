# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""
Fetch the Hong Kong tidal-stream forecast and write it out as a CSV.

The Hydrographic Office publishes, for any quarter of an hour, a current arrow at
about 1,150 points in Hong Kong waters: a speed in knots and a direction in degrees.
That is the material tides.py draws.

Run it:

    uv run fetch.py            # the slots in the knobs below
    uv run fetch.py --now      # start from the current quarter hour instead

Every request is saved to cache/ before anything is parsed, and a slot already in
cache/ is never fetched again. So the second run is instant, and a run with no
internet still works if you have run it once. `tides.csv` is committed to this repo,
so the tutorial survives dead lab wifi entirely — you can skip this script.
"""

import csv
import datetime as dt
import json
import sys
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

DATE = "2026-09-14"   # YYYY-MM-DD. It is a forecast, so future dates work too.
TIME = "00:00"        # HH:MM, on a quarter hour
SLOTS = 120           # how many slots to fetch, starting at TIME: 5 days of hours
STEP_MINUTES = 60     # the office publishes every 15 minutes; every 60 keeps the file at 7 MB
MODE = "S"            # "S" surface current, "A" depth-averaged

HERE = Path(__file__).parent          # this folder, wherever you ran the command from
CACHE = HERE / "data" / "cache"          # the raw replies, one per quarter hour
OUTPUT = HERE / "data" / "tidal-streams-2026-09-14-to-18.csv"

# The endpoint the government's own map calls. Watch this line rot:
#   until ~2023 it was a POST to https://current.hydro.gov.hk/php/tidalgetdata.php
#   that answered in XML. That URL now redirects to the home page, and the map has
#   moved to this one, which answers GeoJSON. See NOTES.md.
URL = "https://current.hydro.gov.hk/data/static_geojson.php"

# ---------------------------------------------------------------------------
# Getting the data. Fetch once, keep the file, parse the file.
# ---------------------------------------------------------------------------


def slot_times():
    """The list of moments to ask about."""
    start = dt.datetime.strptime(f"{DATE} {TIME}", "%Y-%m-%d %H:%M")
    if "--now" in sys.argv:
        now = dt.datetime.now()
        start = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0)
    return [start + dt.timedelta(minutes=STEP_MINUTES * i) for i in range(SLOTS)]


def fetch(moment):
    """One time slot, as raw text. Returns None if it is not cached and not reachable."""
    stamp = moment.strftime("%Y%m%d%H%M%S")
    cached = CACHE / f"tidal-{stamp}-{MODE}.json"

    if cached.exists():
        return cached.read_text(encoding="utf-8")

    try:
        reply = requests.get(URL, params={"time": stamp, "mode": MODE}, timeout=30)
        reply.raise_for_status()
    except requests.RequestException as problem:
        print(f"  {moment:%H:%M}  could not fetch ({problem})")
        return None

    CACHE.mkdir(parents=True, exist_ok=True)
    cached.write_text(reply.text, encoding="utf-8")
    time.sleep(0.5)                        # 120 requests: give their server a breath between them
    return reply.text


def markers(text, moment):
    """Pull the (speed, direction, position) of every arrow out of one reply."""
    rows = []
    for feature in json.loads(text)["features"]:
        info = feature["properties"]
        lng, lat = feature["geometry"]["coordinates"]
        rows.append({
            "time": moment.strftime("%Y-%m-%d %H:%M"),
            "point_id": info["point_id"],
            "knot": float(info["knot"]),      # speed of the current
            "deg": float(info["deg"]),        # the direction it flows towards
            "lng": round(lng, 5),
            "lat": round(lat, 5),
        })
    return rows


def main():
    all_rows = []
    for moment in slot_times():
        text = fetch(moment)
        if text is None:
            continue
        rows = markers(text, moment)
        print(f"  {moment:%Y-%m-%d %H:%M}  {len(rows)} arrows")
        all_rows.extend(rows)

    if not all_rows:
        print("nothing fetched and nothing cached — tides.csv left as it is")
        return

    all_rows.sort(key=lambda r: (r["time"], r["point_id"]))
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)

    slots = len({r["time"] for r in all_rows})
    print(f"wrote {OUTPUT.name} — {len(all_rows)} rows, {slots} time slots")
    print("now run:  uv run currents.py")


if __name__ == "__main__":
    main()
