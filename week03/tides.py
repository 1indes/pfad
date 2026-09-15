# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""
The tide at Quarry Bay, hour by hour, for every day of 2026 — and one day of it
printed as a chart made of `#`.

This file is two things at once, which is the point of it:

  * a **script**. `uv run tides.py` prints today's twenty-four numbers.
  * a **module**. Every other script in this folder starts with
    `from tides import load_year, day, bar`, so the reading of the file is
    written once and the drawing is written seven times.

Run it:

    uv run tides.py

The numbers come from the Hong Kong Observatory, which publishes the predicted
height of the water at Quarry Bay for every hour of the year, in metres above
chart datum:

    https://data.weather.gov.hk/weatherAPI/opendata/opendata.php?dataType=HHOT&station=QUB&year=2026&rformat=json

`data/tides-QUB-2026.json` is that reply, saved. It is committed to this repo, so
nothing here needs the internet. If you delete it, the next run fetches it again —
once — and saves it again. **Fetch once, keep the file, parse the file.**
"""

import datetime as dt
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

STATION = "QUB"              # QUB Quarry Bay · CCH Cheung Chau · TBT Tsim Bei Tsui
YEAR = 2026                  # the Observatory publishes a file per station per year
DAY = None                   # None = today. Or pin one: dt.date(2026, 9, 17)
BAR_SCALE = 10               # how many "#" per metre of water

CLASS_DAY = dt.date(2026, 9, 17)   # the day of the week 3 class, used if today is not in the file

HERE = Path(__file__).parent       # this folder, wherever you ran the command from
DATA = HERE / "data"

URL = "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"

_loaded = {}                 # a year, once parsed, is kept here instead of parsed again

# ---------------------------------------------------------------------------
# Getting the numbers.
# ---------------------------------------------------------------------------


def fetch_year(station, year):
    """Ask the Observatory for one year, save the raw reply, return the path."""
    import requests                     # only needed when the file is missing

    DATA.mkdir(exist_ok=True)
    path = DATA / f"tides-{station}-{year}.json"
    print(f"data/{path.name} is not here — asking the Observatory for it, once.")
    reply = requests.get(
        URL,
        params={"dataType": "HHOT", "station": station, "year": year, "rformat": "json"},
        timeout=30,
        headers={"User-Agent": "SD5913 PolyU teaching example"},
    )
    reply.raise_for_status()
    path.write_text(reply.text, encoding="utf-8")
    print(f"saved data/{path.name} ({path.stat().st_size // 1024} KB) — it will not be fetched again.")
    return path


def load_year(station=STATION, year=YEAR):
    """One year at one station, as a list of (date, [24 heights in metres]).

    The file holds text — `"2.19"`, not `2.19` — because JSON came out of a web
    page and everything in a web page is text until somebody says `float()`.
    """
    if (station, year) in _loaded:
        return _loaded[(station, year)]

    path = DATA / f"tides-{station}-{year}.json"
    if not path.is_file():
        path = fetch_year(station, year)

    raw = json.loads(path.read_text(encoding="utf-8"))

    days = []
    for row in raw["data"]:                       # a row is ["09", "17", "2.19", …]
        when = dt.date(year, int(row[0]), int(row[1]))
        heights = [float(height) for height in row[2:]]
        days.append((when, heights))

    _loaded[(station, year)] = days
    return days


def day(when=None, station=STATION, year=YEAR):
    """The twenty-four heights for one date. No date given: today."""
    when = when or DAY or dt.date.today()
    for date, heights in load_year(station, year):
        if date == when:
            return heights
    raise LookupError(
        f"{when} is not in data/tides-{station}-{year}.json, which covers {year}. "
        f"Set YEAR at the top of tides.py, or pass a date in {year}."
    )


def has(when, station=STATION, year=YEAR):
    """True if that date is in the file. Used to decide what to show you."""
    return any(date == when for date, _ in load_year(station, year))


# ---------------------------------------------------------------------------
# Making one number into something you can see. No library involved.
# ---------------------------------------------------------------------------


def bar(height):
    """One number as a row of `#`. That is the whole idea of a bar chart."""
    return "#" * round(height * BAR_SCALE)


def main():
    when = DAY or dt.date.today()
    if not has(when):
        print(f"({when} is not in the {YEAR} file — showing {CLASS_DAY} instead.)\n")
        when = CLASS_DAY

    heights = day(when)

    print(f"{when:%A %d %B %Y} — {STATION}, tide height in metres above chart datum")
    print(f"one # is {1 / BAR_SCALE:.2f} m\n")

    # A loop: once for each number, with the hour counted alongside it.
    for hour, height in enumerate(heights, start=1):
        print(f"{hour:2}:00  {height:4.2f}  {bar(height)}")

    # Another loop, keeping the best so far. No max(), so you can see it happen.
    high_hour, low_hour = 1, 1
    for hour, height in enumerate(heights, start=1):
        if height > heights[high_hour - 1]:
            high_hour = hour
        if height < heights[low_hour - 1]:
            low_hour = hour

    span = max(heights) - min(heights)
    print()
    print(f"high water {high_hour:2}:00 at {heights[high_hour - 1]:.2f} m")
    print(f"low water  {low_hour:2}:00 at {heights[low_hour - 1]:.2f} m")
    print(f"the day's range is {span:.2f} m")
    print("\nNow: uv run plot_day.py")


if __name__ == "__main__":
    main()
