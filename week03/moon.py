# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "requests"]
# ///

"""
Does the moon move the sea? One month of tidal range against the age of the moon.

Run it:

    uv run moon.py

Writes out/tide-moon.png and opens a window.

The **range** of a day is one number made out of twenty-four: the highest water
minus the lowest. The **age** of the moon is one number made out of a date, by
five lines of arithmetic and no data at all — the Observatory publishes no phase
endpoint, so we compute it.

Then the two get put on the same page, and you look. The textbook says the tides
are biggest at new and full moon. The sea, here, agrees — roughly, and a day or
two late. The roughness is the interesting part. Do not smooth it away.
"""

import datetime as dt
from pathlib import Path

import matplotlib.pyplot as plt

from tides import load_year

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

MONTH = None               # None = this month. Or a number: 9 is September.
NEW_MOON = dt.date(2000, 1, 6)     # a new moon somebody wrote down
SYNODIC = 29.53            # days from one new moon to the next, on average

PAPER = "#faf8f4"
INK = "#1d1d1b"
WATER = "#2a6f7f"
MOON = "#d6591d"
FIGSIZE = (11, 5)

HERE = Path(__file__).parent
OUT = HERE / "out"

# ---------------------------------------------------------------------------
# The moon, in five lines and no data.
# ---------------------------------------------------------------------------


def moon_age(day):
    """Days since the last new moon. 0 is new, about 14.8 is full."""
    return (day - NEW_MOON).days % SYNODIC


def phase_name(age):
    """The four names people use, from one number."""
    quarter = int((age / SYNODIC * 4 + 0.5) % 4)
    return ["new moon", "first quarter", "full moon", "last quarter"][quarter]


# ---------------------------------------------------------------------------
# The drawing.
# ---------------------------------------------------------------------------


def main():
    month = MONTH or dt.date.today().month
    days = [(when, heights) for when, heights in load_year() if when.month == month]
    if not days:
        raise SystemExit(f"no month {month} in the file")

    # One number per day, made by a function, by a loop. The rest is drawing.
    dates = [when for when, _ in days]
    ranges = [max(heights) - min(heights) for _, heights in days]
    ages = [moon_age(when) for when in dates]

    figure, axes = plt.subplots(figsize=FIGSIZE, facecolor=PAPER)
    axes.set_facecolor(PAPER)

    axes.bar([when.day for when in dates], ranges, color=WATER, alpha=0.75, width=0.7)
    axes.set_ylabel("the day's range: highest minus lowest, in metres", color=INK)
    axes.set_xlabel(f"day of {dates[0]:%B %Y}", color=INK)
    axes.tick_params(colors=INK)
    axes.set_xticks([1, 5, 10, 15, 20, 25, dates[-1].day])
    axes.grid(axis="y", color=INK, alpha=0.1)
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)

    moon_axis = axes.twinx()          # a second scale on the right-hand side
    moon_axis.plot([when.day for when in dates], ages, color=MOON,
                   linewidth=1.6, linestyle="--")
    moon_axis.set_ylabel("age of the moon, in days", color=MOON)
    moon_axis.tick_params(colors=MOON)
    moon_axis.set_ylim(0, SYNODIC)
    moon_axis.spines["top"].set_visible(False)

    # Where is new moon, where is full? Straight out of the ages, no lookup table.
    marks = []
    for i in range(1, len(dates)):
        if ages[i] < ages[i - 1]:                                   # the age wrapped
            marks.append((dates[i], "new moon"))
        if ages[i - 1] < SYNODIC / 2 <= ages[i]:
            marks.append((dates[i], "full moon"))
    for when, label in marks:
        axes.axvline(when.day, color=MOON, alpha=0.5, linewidth=1.2)
        axes.annotate(f"{label}\n{when:%d %b}", (when.day, max(ranges)),
                      textcoords="offset points", xytext=(4, -4),
                      color=MOON, fontsize=9, va="top")

    biggest = dates[ranges.index(max(ranges))]
    smallest = dates[ranges.index(min(ranges))]
    axes.set_title(
        f"Quarry Bay, {dates[0]:%B %Y} — biggest tides {biggest:%d %b}, "
        f"smallest {smallest:%d %b}", color=INK, fontsize=13)

    OUT.mkdir(exist_ok=True)
    target = OUT / "tide-moon.png"
    figure.tight_layout()
    figure.savefig(target, dpi=150, facecolor=PAPER)
    print(f"wrote {target.relative_to(HERE)}")

    print(f"\nbiggest range {max(ranges):.2f} m on {biggest:%d %b}, "
          f"moon age {moon_age(biggest):.1f} days ({phase_name(moon_age(biggest))})")
    print(f"smallest range {min(ranges):.2f} m on {smallest:%d %b}, "
          f"moon age {moon_age(smallest):.1f} days ({phase_name(moon_age(smallest))})")
    for when, label in marks:
        print(f"the model puts {label} on {when:%d %b}")
    print("\nCheck it against the Observatory's own moon times, and against the sky.")

    plt.show()


if __name__ == "__main__":
    main()
