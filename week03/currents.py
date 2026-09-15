# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pillow", "requests"]
# ///

"""
The tidal streams of Hong Kong, on a map, moving.

Run it:

    uv run currents.py            # out/currents.png and out/currents.webp — arrows, one frame per hour
    uv run currents.py --still    # only the PNG: the quick way to try the knobs
    uv run currents.py --drift    # out/currents-drift.webp — particles carried by the water

`fetch.py` asks the Hydrographic Office for five days of its tidal-stream forecast,
hour by hour: a current arrow at about 1,150 points in Hong Kong waters — where it
is (longitude, latitude), how fast the water runs (knots) and which way (a compass
bearing). Week 2 had one afternoon of this and drew it as rings, positions thrown
away. This script keeps the positions and puts each arrow back where it was
measured, on a map, and plays the five days back — ten tidal cycles in ten seconds.

Three transformations do all the work, and each is a function you can read:

  * `to_xy(knot, deg)`     — a compass bearing into an (east, north) vector
  * `to_pixel(lng, lat)`   — the round Earth onto a flat map (Web Mercator, the
                             projection every online map uses, so our arrows land
                             on somebody else's tiles)
  * `frame(i)`             — one hour into one picture; the loop over i is the
                             animation

The map under the arrows is stitched from Esri's light-grey tiles, the same 256 px
squares every web map is made of. They are fetched once and saved to data/ as a
single PNG, so this runs without the internet. Attribution: Esri, HERE, Garmin,
© OpenStreetMap contributors.

This is what an assignment 2 repo can look like: one published file of numbers,
one picture that could not have been drawn by hand, and every step written down.
"""

import csv
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.collections import LineCollection
from PIL import Image

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

ZOOM = 11                  # map tiles: 10 is coarse and quick, 12 is sharp and 4x the pixels
ARROW_STYLE = "weight"     # "weight": every arrow the same length, speed as thickness and colour
                           # "length": speed as length too — the classic vector plot, busier
ARROW = 26.0               # "length": pixels of arrow per knot. "weight": pixels of every arrow
WEIGHT = 2.4               # "weight": extra line width per knot
STILL = 8                  # which hour of the data out/currents.png shows (0 is the first)
THIN = 1                   # draw every THIN-th arrow (2 halves the clutter)
FPS = 12                   # frames per second: 120 hours in ten seconds

PARTICLES = 2500           # --drift: how many specks of water to follow
SPEEDUP = 1.5              # --drift: real distance per slot, times this
SUBSTEPS = 4               # --drift: moves per frame. Water an hour on is not where one straight
                           # jump puts it: ask the nearest arrow again every quarter of the way
STEPS = 1                  # --drift: frames per slot (120 frames for 120 hours)
TRAIL = 5                  # --drift: how many past positions each particle leaves behind
SEED = 5913

TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
CREDIT = "map: Esri, HERE, Garmin, © OpenStreetMap contributors · currents: Hydrographic Office, Hong Kong"

PAPER = "#faf8f4"
INK = "#1d1d1b"
WATER = "#2a6f7f"
FAST = "#d6591d"
RAMP = [WATER, "#8fb3a3", "#e9a23b", FAST]   # slow to fast. Straight teal-to-orange goes through mud
FIGSIZE = (10, 7.2)
DPI = 72                   # of the films. They are animated WebP, not GIF: the same 120 frames
                           # were 10 MB as a GIF and are under 3 MB as WebP, and GitHub plays both

HERE = Path(__file__).parent
DATA = HERE / "data" / "tidal-streams-2026-09-14-to-18.csv"   # written by fetch.py: five days, every hour
OUT = HERE / "out"

# ---------------------------------------------------------------------------
# The numbers. One list of arrows per slot.
# ---------------------------------------------------------------------------


def load_slots(path):
    """tides.csv -> [(time, [(lng, lat, knot, deg), ...]), ...], oldest first."""
    by_time = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            by_time[row["time"]].append((float(row["lng"]), float(row["lat"]),
                                         float(row["knot"]), float(row["deg"])))
    return [(when, by_time[when]) for when in sorted(by_time)]


# ---------------------------------------------------------------------------
# Three transformations.
# ---------------------------------------------------------------------------


def slot_hours(slots):
    """How far apart the slots are, in hours, read off the first two timestamps."""
    if len(slots) < 2:
        return 0.25
    (a, _), (b, _) = slots[0], slots[1]
    h0, m0 = int(a[11:13]), int(a[14:16])
    h1, m1 = int(b[11:13]), int(b[14:16])
    return ((h1 * 60 + m1) - (h0 * 60 + m0)) % (24 * 60) / 60


def to_xy(knot, deg):
    """A speed and a compass bearing into an (east, north) vector, in knots.
    Bearings turn clockwise from north, so sin gives east and cos gives north."""
    phi = math.radians(deg)
    return (knot * math.sin(phi), knot * math.cos(phi))


def to_pixel(lng, lat, zoom=ZOOM):
    """Web Mercator: where (lng, lat) lands on the world's tile grid, in pixels.
    Every online map uses this, which is why our arrows land on somebody else's tiles."""
    n = 256 * 2 ** zoom
    x = (lng + 180) / 360 * n
    phi = math.radians(lat)
    y = (1 - math.log(math.tan(phi) + 1 / math.cos(phi)) / math.pi) / 2 * n
    return (x, y)


def to_lnglat(x, y, zoom=ZOOM):
    """The way back — --drift needs it to move a particle by a distance in degrees."""
    n = 256 * 2 ** zoom
    lng = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return (lng, lat)


# ---------------------------------------------------------------------------
# The map. Fetched once, stitched, saved as one PNG in data/.
# ---------------------------------------------------------------------------


def basemap(arrows, zoom=ZOOM, pad=0.03):
    """A PIL image covering every arrow, and the pixel coordinates of its top-left."""
    lngs = [a[0] for a in arrows]
    lats = [a[1] for a in arrows]
    west, east = min(lngs) - pad, max(lngs) + pad
    south, north = min(lats) - pad, max(lats) + pad
    x0, y0 = to_pixel(west, north, zoom)
    x1, y1 = to_pixel(east, south, zoom)
    tx0, ty0, tx1, ty1 = int(x0 // 256), int(y0 // 256), int(x1 // 256), int(y1 // 256)

    cached = HERE / "data" / f"basemap-z{zoom}-{tx0}-{ty0}-{tx1}-{ty1}.png"
    if not cached.is_file():
        import requests                                     # only when the file is missing

        print(f"data/{cached.name} is not here — fetching {(tx1 - tx0 + 1) * (ty1 - ty0 + 1)} tiles, once.")
        sheet = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), PAPER)
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                reply = requests.get(TILES.format(z=zoom, x=tx, y=ty), timeout=30,
                                     headers={"User-Agent": "SD5913 PolyU teaching example"})
                reply.raise_for_status()
                tile = Image.open(__import__("io").BytesIO(reply.content)).convert("RGB")
                sheet.paste(tile, ((tx - tx0) * 256, (ty - ty0) * 256))
        cached.parent.mkdir(exist_ok=True)
        sheet.save(cached)
        print(f"saved data/{cached.name} — it will not be fetched again.")

    return Image.open(cached), (tx0 * 256, ty0 * 256)


# ---------------------------------------------------------------------------
# Picture 1 — arrows, one hour per frame.
# ---------------------------------------------------------------------------


def arrows_figure(slots):
    sheet, (ox, oy) = basemap(slots[0][1])
    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.patch.set_facecolor(PAPER)
    ax.imshow(sheet, extent=(ox, ox + sheet.width, oy + sheet.height, oy), alpha=0.85)
    ax.set_xlim(ox, ox + sheet.width)
    ax.set_ylim(oy + sheet.height, oy)                     # pixel y grows downwards
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)

    quiver = None
    label = ax.text(0.015, 0.975, "", transform=ax.transAxes, va="top", ha="left",
                    fontsize=14, family="monospace", color=INK,
                    bbox=dict(boxstyle="round,pad=0.3", fc=PAPER, ec="none", alpha=0.9))
    ax.text(0.99, 0.01, CREDIT, transform=ax.transAxes, va="bottom", ha="right",
            fontsize=7, color="#666", family="monospace")

    def frame(i):
        nonlocal quiver
        when, arrows = slots[i]
        xs, ys, us, vs, speed = [], [], [], [], []
        for lng, lat, knot, deg in arrows[::THIN]:
            if knot == 0:
                continue                                      # slack water has no direction
            x, y = to_pixel(lng, lat)
            u, v = to_xy(knot, deg)
            if ARROW_STYLE == "weight":                       # same length for all: divide the speed out
                u, v = u / knot, v / knot
            xs.append(x)
            ys.append(y)
            us.append(u * ARROW)
            vs.append(-v * ARROW)                             # north is up, pixel y is down
            speed.append(knot)
        if quiver is not None:
            quiver.remove()
        widths = [0.2 + WEIGHT * k for k in speed] if ARROW_STYLE == "weight" else 0
        quiver = ax.quiver(xs, ys, us, vs, speed, angles="xy", scale_units="xy", scale=1,
                           cmap=matplotlib.colors.LinearSegmentedColormap.from_list("sea", RAMP),
                           clim=(0, 2.5), width=0.0022, headwidth=3.2, headlength=4.5,
                           alpha=1.0 if ARROW_STYLE == "weight" else 0.9,
                           linewidths=widths, edgecolor="face")
        mean = sum(speed) / len(speed)
        label.set_text(f"{when}   surface current, {len(arrows)} points, mean {mean:.2f} kn")
        return quiver, label

    return fig, frame


# ---------------------------------------------------------------------------
# Picture 2 — drift. Specks of water carried by whichever arrow is nearest.
# ---------------------------------------------------------------------------

CELL = 0.012                                                # degrees; a little more than the arrow spacing


def field(arrows):
    """The arrows binned into cells, so 'nearest arrow' is a dict lookup, not 1,150 distances."""
    cells = defaultdict(list)
    for lng, lat, knot, deg in arrows:
        cells[(int(lng / CELL), int(lat / CELL))].append((lng, lat, knot, deg))
    return cells


def nearest(cells, lng, lat):
    """The closest arrow in this cell or the eight around it — or None: that is land."""
    cx, cy = int(lng / CELL), int(lat / CELL)
    best, best_d = None, CELL * CELL * 2
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for a in cells.get((cx + dx, cy + dy), ()):
                d = (a[0] - lng) ** 2 + (a[1] - lat) ** 2
                if d < best_d:
                    best, best_d = a, d
    return best


def drift_figure(slots):
    rng = random.Random(SEED)
    sheet, (ox, oy) = basemap(slots[0][1])
    fields = [field(arrows) for _, arrows in slots]
    starts = slots[0][1]

    def spawn():
        lng, lat, _, _ = rng.choice(starts)
        return [lng + rng.uniform(-CELL, CELL), lat + rng.uniform(-CELL, CELL)]

    particles = [spawn() for _ in range(PARTICLES)]
    trails = [[to_pixel(*p)] for p in particles]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.patch.set_facecolor(PAPER)
    ax.imshow(sheet, extent=(ox, ox + sheet.width, oy + sheet.height, oy), alpha=0.85)
    ax.set_xlim(ox, ox + sheet.width)
    ax.set_ylim(oy + sheet.height, oy)
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)
    lines = LineCollection([], linewidths=1.1, colors=WATER, alpha=0.75)
    ax.add_collection(lines)
    heads = ax.scatter([], [], s=3, c=FAST, alpha=0.9, linewidths=0)
    label = ax.text(0.015, 0.975, "", transform=ax.transAxes, va="top", ha="left",
                    fontsize=14, family="monospace", color=INK,
                    bbox=dict(boxstyle="round,pad=0.3", fc=PAPER, ec="none", alpha=0.9))
    ax.text(0.99, 0.01, CREDIT, transform=ax.transAxes, va="bottom", ha="right",
            fontsize=7, color="#666", family="monospace")

    # A knot is one nautical mile an hour: 1852 m. One slot of the data at one knot is
    # that times the slot length, and one degree of latitude is about 111 km. So, per
    # frame, per knot:
    per_knot = 1852 * slot_hours(slots) / 111_000 * SPEEDUP / STEPS / SUBSTEPS
    cos_lat = math.cos(math.radians(22.3))                    # a degree of longitude is shorter here

    def frame(i):
        slot = i // STEPS
        when, _ = slots[slot]
        cells = fields[slot]
        for n, p in enumerate(particles):
            for _ in range(SUBSTEPS):
                arrow = nearest(cells, p[0], p[1])
                if arrow is None:                             # ran aground, or out of the data
                    break
                east, north = to_xy(arrow[2], arrow[3])
                p[0] += east * per_knot / cos_lat
                p[1] += north * per_knot
            if arrow is None:
                particles[n] = spawn()
                trails[n] = [to_pixel(*particles[n])]
                continue
            trails[n].append(to_pixel(p[0], p[1]))
            del trails[n][:-TRAIL]
        lines.set_segments([t for t in trails if len(t) > 1])
        heads.set_offsets([t[-1] for t in trails])
        label.set_text(f"{when}   {PARTICLES} specks of water, {SPEEDUP}x real drift")
        return lines, heads, label

    return fig, frame, len(slots) * STEPS


# ---------------------------------------------------------------------------


def main():
    if not DATA.is_file():
        print(f"{DATA.name} is missing — run:  uv run fetch.py")
        return
    slots = load_slots(DATA)
    print(f"{DATA.name}: {len(slots)} slots of {slot_hours(slots) * 60:.0f} minutes, {len(slots[0][1])} arrows each")
    OUT.mkdir(exist_ok=True)

    if "--drift" in sys.argv:
        fig, frame, n = drift_figure(slots)
        anim = FuncAnimation(fig, frame, frames=n, interval=1000 / (FPS * 2), blit=False)
        path = OUT / "currents-drift.webp"
        anim.save(path, writer=PillowWriter(fps=FPS * 2), dpi=DPI)
        print(f"wrote {path.relative_to(HERE)} — {n} frames, {path.stat().st_size // 1024} KB")
        return

    fig, frame = arrows_figure(slots)
    frame(STILL)
    still = OUT / "currents.png"
    fig.savefig(still, dpi=110, facecolor=PAPER)
    print(f"wrote {still.relative_to(HERE)}")
    if "--still" in sys.argv:                          # just the PNG, for trying knobs quickly
        return
    anim = FuncAnimation(fig, frame, frames=len(slots), interval=1000 / FPS, blit=False)
    path = OUT / "currents.webp"
    anim.save(path, writer=PillowWriter(fps=FPS), dpi=DPI)
    print(f"wrote {path.relative_to(HERE)} — {len(slots)} frames, {path.stat().st_size // 1024} KB")
    plt.show()


if __name__ == "__main__":
    main()
