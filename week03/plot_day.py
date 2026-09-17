# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "requests"]
# ///

"""
One day of tide as a line: hour along the bottom, metres up the side.

Run it:

    uv run plot_day.py

Writes out/tide-day.png and opens a window. This is `tides.py`'s text chart with
a library doing the drawing — the loop is still there, matplotlib is just running
it for you. You still choose what goes on which axis.
"""

import datetime as dt
from pathlib import Path

import matplotlib.pyplot as plt

from tides import CLASS_DAY, day, has          # your own file is a library too

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

WHEN = None                # None = today. Or pin one: dt.date(2026, 9, 17)
PAPER = "#faf8f4"          # background
INK = "#1d1d1b"            # text and axes
WATER = "#2a6f7f"          # the line
MARK = "#d6591d"           # the high and low water dots
LINE_WIDTH = 2.4
FILL = True                # colour in the water under the line?
FIGSIZE = (9, 4.5)         # inches, wide and short like a tide table

HERE = Path(__file__).parent
OUT = HERE / "out"

# ---------------------------------------------------------------------------
# The drawing.
# ---------------------------------------------------------------------------


def main():
    when = WHEN or dt.date.today()
    if not has(when):
        when = CLASS_DAY

    heights = day(when)
    hours = list(range(1, 25))             # the file's 24 columns are 01:00 to 24:00

    figure, axes = plt.subplots(figsize=FIGSIZE, facecolor=PAPER)
    axes.set_facecolor(PAPER)

    axes.plot(hours, heights, color=WATER, linewidth=LINE_WIDTH)
    if FILL:
        axes.fill_between(hours, heights, min(heights) - 0.1, color=WATER, alpha=0.15)

    # The two moments worth naming, found with a loop over the same numbers.
    high, low = 0, 0
    for i, height in enumerate(heights):
        if height > heights[high]:
            high = i
        if height < heights[low]:
            low = i
    for i in (high, low):
        hour = hours[i]
        side = "left" if hour < 5 else "right" if hour > 20 else "center"
        axes.plot(hour, heights[i], "o", color=MARK, markersize=8)
        axes.annotate(f"{heights[i]:.2f} m at {hour:02}:00",
                      (hour, heights[i]), textcoords="offset points",
                      xytext=(0, 12), ha=side, color=MARK, fontsize=9)

    axes.set_title(f"Tide at Quarry Bay — {when:%A %d %B %Y}", color=INK, fontsize=13)
    axes.set_xlabel("hour of the day", color=INK)
    axes.set_ylabel("metres above chart datum", color=INK)
    axes.set_xticks([1, 4, 8, 12, 16, 20, 24])
    axes.tick_params(colors=INK)
    axes.grid(color=INK, alpha=0.12)
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)

    OUT.mkdir(exist_ok=True)
    target = OUT / "tide-day.png"
    figure.tight_layout()
    figure.savefig(target, dpi=150, facecolor=PAPER)
    print(f"wrote {target.relative_to(HERE)}")
    plt.show()


if __name__ == "__main__":
    main()
