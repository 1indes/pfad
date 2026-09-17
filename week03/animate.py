# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pillow", "requests"]
# ///

"""
The tide clock, moving: twenty-four frames, one hour each, written to a GIF.

Run it:

    uv run animate.py

Writes out/tide-clock.gif and opens a window. It takes a few seconds.

**A frame is a function of time.** `frame(i)` draws the first `i` hours of the day
and puts the hand at hour `i`; `FuncAnimation` calls it once per frame and hands
the result to a writer. Nothing new is being calculated — `to_xy` is the same
function `tide_clock.py` uses, imported from it, because it is written down once.
"""

import datetime as dt
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from tide_clock import BASELINE, HOURS, to_xy      # written once, used twice
from tides import CLASS_DAY, day, has

# ---------------------------------------------------------------------------
# The knobs.
# ---------------------------------------------------------------------------

WHEN = None                # None = today. Or pin one: dt.date(2026, 9, 17)
FPS = 6                    # frames per second in the GIF. 24 frames, so 4 seconds.
SIZE = 4.5                 # inches square
DPI = 72                   # 4.5 x 72 = 324 pixels. Raise it and the file grows fast.
TRAIL = True               # keep the hours already drawn?

PAPER = "#faf8f4"
INK = "#1d1d1b"
WATER = "#2a6f7f"
MARK = "#d6591d"

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
    points = [to_xy(hour, height - BASELINE) for hour, height in enumerate(heights, start=1)]
    reach = max(max(abs(x), abs(y)) for x, y in points) * 1.10

    figure, axes = plt.subplots(figsize=(SIZE, SIZE), facecolor=PAPER)
    figure.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02)
    axes.set_facecolor(PAPER)
    axes.set_aspect("equal")
    axes.axis("off")
    axes.set_xlim(-reach, reach)
    axes.set_ylim(-reach, reach)
    axes.set_title(f"{when:%d %B %Y} — Quarry Bay", color=INK, fontsize=11)

    # The things that change. Empty now; frame() fills them in.
    trace, = axes.plot([], [], color=WATER, linewidth=2.4)
    hand, = axes.plot([], [], color=MARK, linewidth=1.6)
    head, = axes.plot([], [], "o", color=MARK, markersize=8)
    clock = axes.text(0, -reach * 0.95, "", color=INK, fontsize=10, ha="center")

    # The faint full ring, so you can see where the hand is going.
    ghost = points + [points[0]]
    axes.plot([p[0] for p in ghost], [p[1] for p in ghost],
              color=INK, alpha=0.14, linewidth=1.0)

    def frame(i):
        """Everything you can see at hour i. This is the whole animation."""
        so_far = points[: i + 1] if TRAIL else points[i : i + 1]
        trace.set_data([p[0] for p in so_far], [p[1] for p in so_far])
        hand.set_data([0, points[i][0]], [0, points[i][1]])
        head.set_data([points[i][0]], [points[i][1]])
        clock.set_text(f"{i + 1:02}:00   {heights[i]:.2f} m")
        return trace, hand, head, clock

    movie = FuncAnimation(figure, frame, frames=HOURS, interval=1000 // FPS, blit=True)

    OUT.mkdir(exist_ok=True)
    target = OUT / "tide-clock.gif"
    movie.save(target, writer=PillowWriter(fps=FPS), dpi=DPI)
    print(f"wrote {target.relative_to(HERE)} — {HOURS} frames, "
          f"{target.stat().st_size // 1024} KB")
    plt.show()


if __name__ == "__main__":
    main()
