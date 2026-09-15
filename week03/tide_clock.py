# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "requests"]
# ///

"""
The same day, bent into a circle: the hour becomes an angle, the height a radius.

Run it:

    uv run tide_clock.py

Writes out/tide-clock.png and opens a window.

Nothing about the numbers changed. `plot_day.py` and this file draw the same
twenty-four heights; what differs is one function, `to_xy`, applied to every one
of them by a loop. **A chart type is a transformation.**

`move`, `scale` and `rotate` are the other three transformations from the
lecture. Each is one line of arithmetic on a point, and each is applied to the
whole shape by a loop — which is all a graphics library ever does.
"""

import datetime as dt
import math
from pathlib import Path

import matplotlib.pyplot as plt

from tides import CLASS_DAY, day, has

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

WHEN = None                # None = today. Or pin one: dt.date(2026, 9, 17)
HOURS = 24                 # a full turn is one day
TURN = 360                 # degrees in a full turn. Try 180: half a day per turn.
ROTATE = 0                 # turn the whole clock, in degrees. Try 90.
BASELINE = 0.8             # where the centre of the clock sits, in metres. Raise it
                           # towards the low water and the shape exaggerates. This is
                           # why a radial chart can flatter or flatten the same numbers.
ZOOM = 1.0                 # scale the whole clock
CENTRE = (0.0, 0.0)        # move the whole clock

PAPER = "#faf8f4"
INK = "#1d1d1b"
WATER = "#2a6f7f"
MARK = "#d6591d"
LINE_WIDTH = 2.4
DOTS = True                # a dot on every hour?

HERE = Path(__file__).parent
OUT = HERE / "out"

# ---------------------------------------------------------------------------
# Four transformations. A point is a tuple: (x, y).
# ---------------------------------------------------------------------------


def to_xy(hour, height):
    """Polar to cartesian. Hour 0 at the top, going clockwise like a clock."""
    angle = math.radians(90 - hour / HOURS * TURN)
    return (height * math.cos(angle), height * math.sin(angle))


def move(p, dx, dy):
    """Slide a point across the page."""
    return (p[0] + dx, p[1] + dy)


def scale(p, k):
    """Push a point k times further from the origin."""
    return (p[0] * k, p[1] * k)


def rotate(p, deg):
    """Turn a point about the origin, anticlockwise, by deg degrees."""
    a = math.radians(deg)
    return (p[0] * math.cos(a) - p[1] * math.sin(a),
            p[0] * math.sin(a) + p[1] * math.cos(a))


def place(p):
    """The three whole-shape transformations, in the order that matters."""
    return move(scale(rotate(p, ROTATE), ZOOM), CENTRE[0], CENTRE[1])


# ---------------------------------------------------------------------------
# The drawing.
# ---------------------------------------------------------------------------


def main():
    when = WHEN or dt.date.today()
    if not has(when):
        when = CLASS_DAY

    heights = day(when)

    # One loop, one function per number. That is the whole chart.
    points = [place(to_xy(hour, height - BASELINE))
              for hour, height in enumerate(heights, start=1)]
    points.append(points[0])                       # close the ring back onto 24:00

    figure, axes = plt.subplots(figsize=(6.5, 6.5), facecolor=PAPER)
    axes.set_facecolor(PAPER)
    axes.set_aspect("equal")
    axes.axis("off")

    # The hour spokes and the mean-water circle: to_xy again, with fixed radii.
    lo = min(heights) - BASELINE
    hi = max(heights) - BASELINE
    mean = sum(heights) / len(heights) - BASELINE
    for hour in range(1, HOURS + 1):
        inner, outer = place(to_xy(hour, lo * 0.55)), place(to_xy(hour, hi * 1.06))
        axes.plot([inner[0], outer[0]], [inner[1], outer[1]], color=INK,
                  alpha=0.35 if hour % 6 == 0 else 0.12, linewidth=0.9)
        if hour % 6 == 0:
            label = place(to_xy(hour, hi * 1.22))
            axes.text(label[0], label[1], f"{hour:02}:00", color=INK, alpha=0.7,
                      fontsize=9, ha="center", va="center")

    ring = [place(scale(to_xy(hour, 1.0), mean)) for hour in range(0, HOURS + 1)]
    axes.plot([p[0] for p in ring], [p[1] for p in ring], color=INK, alpha=0.25,
              linewidth=0.9, linestyle="--")

    axes.fill([p[0] for p in points], [p[1] for p in points], color=WATER, alpha=0.15)
    axes.plot([p[0] for p in points], [p[1] for p in points],
              color=WATER, linewidth=LINE_WIDTH)
    if DOTS:
        axes.plot([p[0] for p in points], [p[1] for p in points], "o",
                  color=WATER, markersize=4)

    high = heights.index(max(heights)) + 1
    top = place(to_xy(high, max(heights) - BASELINE))
    axes.plot(top[0], top[1], "o", color=MARK, markersize=9)

    axes.margins(0.14)
    axes.set_title(f"Tide at Quarry Bay — {when:%d %B %Y}\nhour as angle, metres as radius",
                   color=INK, fontsize=12, pad=20)

    OUT.mkdir(exist_ok=True)
    target = OUT / "tide-clock.png"
    figure.tight_layout()
    figure.savefig(target, dpi=150, facecolor=PAPER)
    print(f"wrote {target.relative_to(HERE)}")
    print(f"hour 6 lands at {tuple(round(v, 2) for v in to_xy(6, heights[5]))}")
    print(f"hour 12 lands at {tuple(round(v, 2) for v in to_xy(12, heights[11]))}")
    plt.show()


if __name__ == "__main__":
    main()
