# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "requests"]
# ///

"""
A whole month of tide, twice: thirty days drawn on top of each other, and the same
thirty days as a grid of colour, one square per hour.

Run it:

    uv run tide_month.py

Writes out/tide-month.png and opens a window.

Same numbers, two transformations. On the left, height is a position — you read a
shape. On the right, height is a colour — you read a pattern, and the fortnightly
swing between big tides and small ones appears, which the left panel hides in a
thicket of lines. Neither picture is more true than the other. They answer
different questions.
"""

import datetime as dt
from pathlib import Path

import matplotlib.pyplot as plt

from tides import CLASS_DAY, load_year

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

MONTH = None               # None = this month. Or a number: 1 is January, 9 September.
COLOURS = "viridis"        # try "Blues", "magma", "coolwarm", "cividis"
PAPER = "#faf8f4"
INK = "#1d1d1b"
WATER = "#2a6f7f"
TODAY_MARK = "#d6591d"     # the colour of the one day drawn thick
LINE_ALPHA = 0.28          # how faint each of the thirty days is
FIGSIZE = (13, 5)

HERE = Path(__file__).parent
OUT = HERE / "out"

# ---------------------------------------------------------------------------
# The drawing.
# ---------------------------------------------------------------------------


def main():
    today = dt.date.today()
    month = MONTH or today.month
    year = load_year()

    # A loop that picks: every day of the month, as (date, [24 heights]).
    days = [(when, heights) for when, heights in year if when.month == month]
    if not days:
        raise SystemExit(f"no month {month} in the file")

    pick = today if any(when == today for when, _ in days) else CLASS_DAY
    hours = list(range(1, 25))

    figure, (left, right) = plt.subplots(1, 2, figsize=FIGSIZE, facecolor=PAPER)

    # -- left: thirty lines, one per day ------------------------------------
    left.set_facecolor(PAPER)
    for when, heights in days:
        left.plot(hours, heights, color=WATER, alpha=LINE_ALPHA, linewidth=1.0)
    for when, heights in days:
        if when == pick:
            left.plot(hours, heights, color=TODAY_MARK, linewidth=2.6,
                      label=f"{when:%d %b}")
    left.set_title(f"{days[0][0]:%B %Y} — every day, drawn over the last",
                   color=INK, fontsize=12)
    left.set_xlabel("hour of the day", color=INK)
    left.set_ylabel("metres above chart datum", color=INK)
    left.set_xticks([1, 6, 12, 18, 24])
    left.tick_params(colors=INK)
    left.grid(color=INK, alpha=0.1)
    left.legend(frameon=False, labelcolor=INK)
    for side in ("top", "right"):
        left.spines[side].set_visible(False)

    # -- right: the same numbers as a grid of colour ------------------------
    # A list of lists is a grid: one row per day, one column per hour.
    grid = [heights for when, heights in days]
    picture = right.imshow(grid, aspect="auto", cmap=COLOURS, origin="upper",
                           extent=(0.5, 24.5, len(days) + 0.5, 0.5))
    right.set_title("the same numbers as colour — one square per hour",
                    color=INK, fontsize=12)
    right.set_xlabel("hour of the day", color=INK)
    right.set_ylabel("day of the month", color=INK)
    right.set_xticks([1, 6, 12, 18, 24])
    right.set_yticks([1, 5, 10, 15, 20, 25, len(days)])
    right.tick_params(colors=INK)
    bar = figure.colorbar(picture, ax=right)
    bar.set_label("metres above chart datum", color=INK)
    bar.ax.tick_params(colors=INK)

    OUT.mkdir(exist_ok=True)
    target = OUT / "tide-month.png"
    figure.tight_layout()
    figure.savefig(target, dpi=150, facecolor=PAPER)
    print(f"wrote {target.relative_to(HERE)} — {len(days)} days, {len(days) * 24} numbers")
    plt.show()


if __name__ == "__main__":
    main()
