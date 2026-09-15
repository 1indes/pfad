# /// script
# requires-python = ">=3.10"
# dependencies = ["folium"]
# ///

"""
The same tidal streams as currents.py, but as a web page you can pan, zoom and play.

Run it:

    uv run currents_web.py        # writes site/index.html — open it in a browser

No window opens and no picture is drawn. Python writes one HTML file, and the
browser does the drawing: `folium` is a Python library that generates the
JavaScript for Leaflet, the map library behind most of the maps on the web. The
file it writes is self-contained apart from the tiles, so double-clicking it on
your machine is a complete test — and a GitHub Actions workflow can run this
script on every push and publish the result as a web page. See `pages.yml` in
`assignments/` and the README for how.

Same three transformations as currents.py — only the last one changed:

  * `to_xy(knot, deg)`   — a compass bearing into an (east, north) vector
  * `to_lnglat(...)`     — that vector into a second point on the Earth, so an
                           arrow is a line between two (lng, lat) pairs
  * `feature(...)`       — one arrow into one GeoJSON feature with a timestamp;
                           the loop over the slots is the animation, and the
                           browser's time slider is the frame counter

Web maps do not need to_pixel: Leaflet does the Web Mercator projection for you,
which is exactly what currents.py wrote by hand.
"""

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import folium
from folium.plugins import TimestampedGeoJson

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

THIN = 2                   # keep every THIN-th arrow: 1 is all 1,158 per frame, 2 is half
MIN_KNOT = 0.4             # skip arrows slower than this: half the open sea barely moves, and
                           # 120 hours of it would make a 25 MB page
ARROW_MINUTES = 40         # an arrow's length is how far the water goes in this many minutes
PLAY_MS = 150              # milliseconds per hour when playing: five days in eighteen seconds
CENTRE = (22.30, 114.15)   # where the map opens (lat, lng — Leaflet's order, not ours)
ZOOM = 11

TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
CREDIT = "map: Esri, HERE, Garmin, © OpenStreetMap contributors · currents: Hydrographic Office, Hong Kong"

SLOW, FAST = "#2a6f7f", "#d6591d"

HERE = Path(__file__).parent
DATA = HERE / "data" / "tidal-streams-2026-09-14-to-18.csv"   # written by fetch.py
SITE = HERE / "site"

# ---------------------------------------------------------------------------
# The numbers, and two transformations. Same as currents.py.
# ---------------------------------------------------------------------------


def load_slots(path):
    by_time = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            by_time[row["time"]].append((float(row["lng"]), float(row["lat"]),
                                         float(row["knot"]), float(row["deg"])))
    return [(when, by_time[when]) for when in sorted(by_time)]


def to_xy(knot, deg):
    """A speed and a compass bearing into (east, north), in knots."""
    phi = math.radians(deg)
    return (knot * math.sin(phi), knot * math.cos(phi))


def to_lnglat(lng, lat, east, north, minutes):
    """Where the water will be in `minutes`, starting at (lng, lat) and moving at
    (east, north) knots. A knot is 1852 m an hour; a degree of latitude is ~111 km;
    a degree of longitude is that times the cosine of the latitude."""
    metres = 1852 / 60 * minutes
    dlat = north * metres / 111_000
    dlng = east * metres / (111_000 * math.cos(math.radians(lat)))
    return (lng + dlng, lat + dlat)


def colour(knot):
    """SLOW to FAST, mixed by speed. Three knots is as fast as this water gets."""
    t = min(knot / 3, 1)
    a = tuple(int(SLOW[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(FAST[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------------------
# The third transformation: an arrow into a GeoJSON feature with a time on it.
# ---------------------------------------------------------------------------


def feature(when, lng, lat, knot, deg):
    east, north = to_xy(knot, deg)
    tip = to_lnglat(lng, lat, east, north, ARROW_MINUTES)
    return {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": [[lng, lat], list(tip)]},
        "properties": {
            "times": [when.replace(" ", "T") + ":00+08:00"] * 2,
            "style": {"color": colour(knot), "weight": 1 + knot, "opacity": 0.85},
            "popup": f"{when} · {knot:.2f} kn · {deg:.0f}°",
        },
    }


def main():
    slots = load_slots(DATA)
    print(f"{DATA.name}: {len(slots)} slots, {len(slots[0][1])} arrows each")

    features = []
    for when, arrows in slots:                       # the loop over the slots is the film
        for lng, lat, knot, deg in arrows[::THIN]:
            if knot >= MIN_KNOT:
                features.append(feature(when, lng, lat, knot, deg))

    m = folium.Map(location=CENTRE, zoom_start=ZOOM, tiles=None, control_scale=True)
    folium.TileLayer(tiles=TILES, attr=CREDIT, name="Esri light grey").add_to(m)
    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="PT1H", duration="PT59M",              # each arrow shows for its own hour
        transition_time=PLAY_MS, auto_play=True, loop=True,
        add_last_point=False, date_options="YYYY-MM-DD HH:mm",
    ).add_to(m)
    folium.LayerControl().add_to(m)

    SITE.mkdir(exist_ok=True)
    out = SITE / "index.html"
    m.save(out)
    print(f"wrote {out.relative_to(HERE)} — {len(features)} arrows over {len(slots)} slots, "
          f"{out.stat().st_size // 1024} KB. Open it in a browser.")


if __name__ == "__main__":
    main()
