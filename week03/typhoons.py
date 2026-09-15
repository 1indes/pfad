# /// script
# requires-python = ">=3.10"
# dependencies = ["beautifulsoup4", "matplotlib", "requests"]
# ///

"""
This year's Pacific typhoons, out of a Wikipedia table: wind speed against pressure.

Run it:

    uv run typhoons.py

Writes out/typhoons.png and opens a window.

Same idea as the tide and the earthquakes, messier. Nobody publishes this as JSON;
it is a table on a web page, written by people, for people. A page is a **tree**,
BeautifulSoup walks it, and `select("table.wikitable.sortable tr")` gets the rows.
Every cell is text: `"215 km/h (130 mph)"` has a number in it somewhere and you
have to go and get it.

Then look at what comes out. The points fall on a curve, because wind speed and
central pressure are two measurements of one thing — the storm. A scatter plot
that shows a physical law is not decoration.

    https://en.wikipedia.org/wiki/2026_Pacific_typhoon_season

`data/2026_Pacific_typhoon_season.html` is that page, saved on 15 September 2026,
and committed. Fetch it yourself and you will get a longer table — the season is
still running.
"""

import re
from pathlib import Path

import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

LABEL_ABOVE = 150          # name every storm whose peak wind is at least this, km/h
DOT_SIZE = 90
PAPER = "#faf8f4"
INK = "#1d1d1b"
STORM = "#d6591d"
FIGSIZE = (9, 6)

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out"
CACHE = DATA / "2026_Pacific_typhoon_season.html"
URL = "https://en.wikipedia.org/wiki/2026_Pacific_typhoon_season"

# Be polite: say who you are and what this is for. Never fetch in a loop.
AGENT = "SD5913-PolyU-teaching/1.0 (course example; one request)"

# ---------------------------------------------------------------------------
# Getting the numbers. Fetch once, keep the file, parse the file.
# ---------------------------------------------------------------------------


def fetch():
    """One request, saved. The page is 1.5 MB; you need it once."""
    import requests

    DATA.mkdir(exist_ok=True)
    print(f"data/{CACHE.name} is not here — asking Wikipedia for it, once.")
    reply = requests.get(URL, timeout=30, headers={"User-Agent": AGENT})
    reply.raise_for_status()
    CACHE.write_text(reply.text, encoding="utf-8")
    print(f"saved data/{CACHE.name} ({CACHE.stat().st_size // 1024} KB).")
    return CACHE


def number(text, unit):
    """The number in front of a unit, or None. `"996 hPa (29.41 inHg)"` -> 996.0"""
    found = re.search(rf"([\d,]+(?:\.\d+)?)\s*{unit}", text)
    return float(found.group(1).replace(",", "")) if found else None


def load_storms():
    """The season-effects table, as a list of dicts. Rows that are not data are skipped."""
    if not CACHE.is_file():
        fetch()

    page = BeautifulSoup(CACHE.read_text(encoding="utf-8"), "html.parser")
    table = page.select_one("table.wikitable.sortable")

    storms, skipped = [], []
    for row in table.select("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.select("th, td")]

        # The table has a footer. Stop when you reach it, or the totals row
        # arrives dressed as a storm called "35 systems".
        if cells and "Season aggregates" in cells[0]:
            break
        if not row.select("td") or len(cells) < 6:
            continue                              # the two header rows are all <th>

        name, dates, category, wind, pressure = cells[0], cells[1], cells[2], cells[3], cells[4]
        speed = number(wind, "km/h")
        hpa = number(pressure, "hPa")
        if speed is None or hpa is None:
            skipped.append(f"{name} ({dates}) — wind reads {wind!r}")
            continue

        storms.append({"name": name, "dates": dates, "category": category,
                       "wind": speed, "pressure": hpa})

    return storms, skipped


# ---------------------------------------------------------------------------
# The drawing.
# ---------------------------------------------------------------------------


def main():
    storms, skipped = load_storms()
    print(f"{len(storms)} storms with both numbers, {len(skipped)} rows skipped")
    for line in skipped:
        print(f"  skipped: {line}")

    figure, axes = plt.subplots(figsize=FIGSIZE, facecolor=PAPER)
    axes.set_facecolor(PAPER)

    axes.scatter([s["wind"] for s in storms], [s["pressure"] for s in storms],
                 s=DOT_SIZE, color=STORM, alpha=0.75, linewidths=0)

    # Two storms can land on exactly the same point. Nudge the second label down
    # rather than let the names sit on top of each other.
    stacked = {}
    for storm in storms:
        if storm["wind"] < LABEL_ABOVE:
            continue
        spot = (storm["wind"], storm["pressure"])
        stacked[spot] = stacked.get(spot, 0) + 1
        axes.annotate(storm["name"].split("(")[0].strip(), spot,
                      textcoords="offset points",
                      xytext=(7, 4 - 12 * (stacked[spot] - 1)),
                      color=INK, fontsize=9)

    axes.invert_yaxis()            # low pressure is a strong storm, so put it at the top
    axes.set_xlabel("peak wind speed, km/h", color=INK)
    axes.set_ylabel("central pressure, hPa  (low is strong)", color=INK)
    axes.set_title(f"2026 Pacific typhoon season — {len(storms)} named systems\n"
                   "two measurements of one thing", color=INK, fontsize=13)
    axes.tick_params(colors=INK)
    axes.grid(color=INK, alpha=0.12)
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)

    strongest = max(storms, key=lambda s: s["wind"])
    print(f"\nstrongest: {strongest['name']} — {strongest['wind']:.0f} km/h, "
          f"{strongest['pressure']:.0f} hPa, {strongest['category']}, {strongest['dates']}")

    OUT.mkdir(exist_ok=True)
    target = OUT / "typhoons.png"
    figure.tight_layout()
    figure.savefig(target, dpi=150, facecolor=PAPER)
    print(f"wrote {target.relative_to(HERE)}")
    plt.show()


if __name__ == "__main__":
    main()
