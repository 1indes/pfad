# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "requests"]
# ///

"""
Every earthquake on Earth of the last month, as a dot on a map.

Run it:

    uv run earthquakes.py           # out/quakes-month.png, the whole month at once
    uv run earthquakes.py --day     # out/quakes-month.gif, the month played back

A point on a map with a size and a colour is **four numbers at once**: longitude
and latitude decide where, magnitude decides how big, depth decides the colour.
That is what "dimensions" means, and the shape that appears is not drawn by
anyone — nobody added a coastline. The dots *are* the plate boundaries.

The map is equirectangular: longitude straight across, latitude straight up, and
nothing else. Greenland comes out enormous. That is a decision, not a bug — every
flat map of a round planet is wrong somewhere, and choosing where is your job.

The numbers are the USGS public feed:

    https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson

`data/earthquakes-2.5-month.geojson` is that reply, saved on 15 September 2026, and
committed. The live feed is a moving window — delete the file and the next run
fetches a different month, which is worth doing once so you see it happen.
"""

import datetime as dt
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

MIN_MAG = 2.5              # the feed starts at 2.5. Try 4.5 and watch the map empty.
DOT = 2.6                  # how big a dot is: DOT ** magnitude, so 6 dwarfs 3
COLOURS = "magma_r"        # depth, in colour. Try "viridis", "cividis", "Blues"
MAX_DEPTH = 300            # km. Deeper than this is drawn as this.
FPS = 4                    # frames per second in the --day animation
PAPER = "#faf8f4"
INK = "#1d1d1b"
SEA = "#eceae4"            # the empty map behind the dots

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out"
CACHE = DATA / "earthquakes-2.5-month.geojson"
URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson"

# ---------------------------------------------------------------------------
# Getting the numbers. Fetch once, keep the file, parse the file.
# ---------------------------------------------------------------------------


def fetch():
    """Ask the USGS for the last month, save the raw reply, return the path."""
    import requests

    DATA.mkdir(exist_ok=True)
    print(f"data/{CACHE.name} is not here — asking the USGS for it, once.")
    reply = requests.get(URL, timeout=60,
                         headers={"User-Agent": "SD5913 PolyU teaching example"})
    reply.raise_for_status()
    CACHE.write_text(reply.text, encoding="utf-8")
    print(f"saved data/{CACHE.name} ({CACHE.stat().st_size // 1024} KB).")
    return CACHE


def load_quakes():
    """The feed, trimmed to the five numbers this picture needs.

    GeoJSON is a dict of lists of dicts. Square brackets read all of it, and the
    only hard part is knowing what is inside — which is why you print it first.
    """
    if not CACHE.is_file():
        fetch()

    raw = json.loads(CACHE.read_text(encoding="utf-8"))

    quakes = []
    for feature in raw["features"]:
        info = feature["properties"]
        lng, lat, depth = feature["geometry"]["coordinates"]
        if info["mag"] is None or info["mag"] < MIN_MAG:
            continue
        quakes.append({
            "mag": float(info["mag"]),
            "lng": float(lng),
            "lat": float(lat),
            "depth": float(depth or 0),
            "when": dt.datetime.fromtimestamp(info["time"] / 1000, dt.timezone.utc),
            "place": info["place"] or "",
        })
    quakes.sort(key=lambda q: q["when"])
    return quakes


def save_csv(quakes):
    """1.5 MB of feed down to five columns. Trimming is part of the work."""
    OUT.mkdir(exist_ok=True)
    target = OUT / "quakes.csv"
    with target.open("w", encoding="utf-8") as handle:
        handle.write("mag,lng,lat,depth,when\n")
        for q in quakes:
            handle.write(f"{q['mag']},{q['lng']},{q['lat']},{q['depth']},"
                         f"{q['when']:%Y-%m-%dT%H:%M:%SZ}\n")
    return target


# ---------------------------------------------------------------------------
# The drawing.
# ---------------------------------------------------------------------------


def blank_map(axes, title):
    """The empty page every frame starts from."""
    axes.set_facecolor(SEA)
    axes.set_aspect("equal")      # one degree across is one degree up. Nothing else.
    axes.set_xlim(-180, 180)
    axes.set_ylim(-90, 90)
    axes.set_xticks([-180, -90, 0, 90, 180])
    axes.set_yticks([-60, -30, 0, 30, 60])
    axes.tick_params(colors=INK, labelsize=8)
    axes.grid(color=INK, alpha=0.12, linewidth=0.6)
    axes.set_title(title, color=INK, fontsize=12)


def dots(axes, quakes, alpha=0.75):
    """One scatter call: four numbers per earthquake."""
    return axes.scatter(
        [q["lng"] for q in quakes],
        [q["lat"] for q in quakes],
        s=[DOT ** q["mag"] for q in quakes],
        c=[min(q["depth"], MAX_DEPTH) for q in quakes],
        cmap=COLOURS, vmin=0, vmax=MAX_DEPTH,
        alpha=alpha, linewidths=0,
    )


def still(quakes):
    figure, axes = plt.subplots(figsize=(12, 6), facecolor=PAPER)
    first, last = quakes[0]["when"], quakes[-1]["when"]
    blank_map(axes, f"{len(quakes)} earthquakes of magnitude {MIN_MAG}+, "
                    f"{first:%d %b} to {last:%d %b %Y}")
    painted = dots(axes, quakes)
    bar = figure.colorbar(painted, ax=axes, shrink=0.72)
    bar.set_label("depth below the surface, km", color=INK)
    bar.ax.tick_params(colors=INK)
    axes.set_xlabel("longitude — equirectangular, so the poles are stretched", color=INK)
    axes.set_ylabel("latitude", color=INK)

    biggest = max(quakes, key=lambda q: q["mag"])
    axes.annotate(f"M{biggest['mag']} · {biggest['place']}",
                  (biggest["lng"], biggest["lat"]), textcoords="offset points",
                  xytext=(8, 8), color=INK, fontsize=9)

    OUT.mkdir(exist_ok=True)
    target = OUT / "quakes-month.png"
    figure.tight_layout()
    figure.savefig(target, dpi=150, facecolor=PAPER)
    print(f"wrote {target.relative_to(HERE)}")
    print(f"biggest: M{biggest['mag']} {biggest['place']}, {biggest['when']:%d %b %H:%M} UTC")
    plt.show()


def playback(quakes):
    """One frame per day. A frame is a function of time."""
    days = sorted({q["when"].date() for q in quakes})

    figure, axes = plt.subplots(figsize=(8, 4), facecolor=PAPER)

    def frame(i):
        today = days[i]
        axes.clear()
        blank_map(axes, f"{today:%d %B %Y}")
        before = [q for q in quakes if q["when"].date() < today]
        now = [q for q in quakes if q["when"].date() == today]
        if before:
            axes.scatter([q["lng"] for q in before], [q["lat"] for q in before],
                         s=[DOT ** q["mag"] for q in before],
                         color=INK, alpha=0.10, linewidths=0)
        if now:
            dots(axes, now, alpha=0.9)
        axes.text(-175, -80, f"{len(now)} today · {len(before) + len(now)} so far",
                  color=INK, fontsize=9)

    movie = FuncAnimation(figure, frame, frames=len(days), interval=1000 // FPS)

    OUT.mkdir(exist_ok=True)
    target = OUT / "quakes-month.gif"
    movie.save(target, writer=PillowWriter(fps=FPS), dpi=70)
    print(f"wrote {target.relative_to(HERE)} — {len(days)} frames, "
          f"{target.stat().st_size // 1024} KB")
    plt.show()


def main():
    quakes = load_quakes()
    csv = save_csv(quakes)
    print(f"{len(quakes)} earthquakes of magnitude {MIN_MAG}+ — "
          f"trimmed to {csv.relative_to(HERE)}")
    if "--day" in sys.argv:
        playback(quakes)
    else:
        still(quakes)


if __name__ == "__main__":
    main()
