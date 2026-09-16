# Python, as far as we have got

Everything here has been on a slide or in a tutorial, in the order it was taught,
with where to find it again. Nothing else has. A line that is not on this page is
not wrong — it is further ahead than the course, and you cannot sign off what you
cannot read. The last section is the list to be suspicious of. Run anything here
with `uv run`; week 2's drills also run in the browser, nothing to install:
<https://sd5913.github.io/teaching/week02/>.

## Six types, and the quotes

`print(...)` puts a value on screen. `=` gives a value a name: name on the left,
value on the right. Everything you will be handed is one of six types.

| Value | Type | What it is |
|---|---|---|
| `3` | `int` | a whole number |
| `2.19` | `float` | a number with a decimal point |
| `"2.19"` | `str` | text. The quotes are what make it text |
| `True` | `bool` | yes or no |
| `[2.19, 2.09]` | `list` | several things, in order |
| `{"station": "QUB"}` | `dict` | values you look up by name |

`type(x)` asks which one it is — use it on anything an assistant gave you. `+`
adds numbers and joins text, and Python picks by type, not by what you meant: a
number out of a file is text until `int()` or `float()`. An `f` before the quotes
drops a value into the text at the `{ }`.
*Week 1 slide 34; week 2 slides 24–27 and 29; week 3 slides 22 and 23.*

```python
a = "6"
print(type(a), a + a)               # <class 'str'> 66  — joined, not added
print(int(a) + int(a))              # 12
print(f"{1:2} {float('2.19')} m")   #  1 2.19 m
```

## Square brackets

A list answers to a position, a dict to a name, both asked the same way. Positions
count from `0`, `-1` is the last. `len` counts, `min` and `max` pick, `.append(x)`
adds one on the end. `b = a` does not copy a list — it is a second name for it.
*Week 2 slides 28 and 45; week 3 slides 12 and 21.*

```python
heights = [2.19, 2.09, 1.90, 1.63, 1.36, 1.14, 1.05]
print(heights[0], heights[-1], len(heights), max(heights))   # 2.19 1.05 7 2.19
d = {"data": [["09", "17", "2.19"]]}
print(d["data"][0][2])                                       # 2.19 — still a str
```

## if, for, and the four spaces

`if` runs the indented lines only when the test is true: `>` `<` `>=` `<=` `==`
`!=`, joined by `and`, `or`, `not`. A `for` loop does them once for each item;
`enumerate` hands you the position too, and `start=1` makes the first hour 1, not
0. `range(1, 25)` is 1 to 24 — the second number is where it stops. The four
spaces say which lines are inside the loop, and in Python that is the logic. Two
traps: never `==` on numbers with a decimal point (`0.1 + 0.1 + 0.1 == 0.3` is
`False`), and an empty list, empty text, `0` and `None` all count as no.
*Week 1 slide 34; week 2 slides 33 and 42–44; week 3 slides 13, 14 and 35.*

```python
heights = [2.19, 2.09, 1.90]
for hour, height in enumerate(heights, start=1):
    if height > 2:
        print(hour, height)    # 1 2.19   then   2 2.09
```

## def, return, None

`def` gives a rule a name: something goes in, something comes out — but only if
you write `return`. Without it the function hands back `None`, silently, which is
the mistake generated code makes more than any other. `round(x)` gives a whole
number, `round(x, 2)` two decimals; ties go to the even side, so `round(0.5)` is
`0` and `round(2.5)` is `2`.
*Week 2 slide 46; week 3 slides 15 and 17.*

```python
def bar(height):
    return "#" * round(height * 10)
print(bar(2.19))          # ###################### — 22 of them
```

## import, tuples, and a loop on one line

`import` fetches a library; `from math import cos, sin` takes two names out of
one. A tuple is a list you do not change, in round brackets — use it for a
coordinate, where the order is the meaning. A list comprehension is a loop written
on one line and nothing more. `row[2:]` is "from position 2 on", `hours[:i]` is
"the first i".
*Week 2 slide 35 (`import random`); week 3 slides 27, 28, 29, 32, 35 and 41.*

```python
import math
def to_xy(hour, height):                      # (hour, height) in, (x, y) out
    a = hour / 24 * 2 * math.pi
    return (round(height * math.cos(a), 2), round(height * math.sin(a), 2))
print([to_xy(h, 1.14) for h in [6, 12]])      # [(0.0, 1.14), (-1.14, 0.0)]
```

## Where the file is, and what it needs

Build every address from the folder the script is in and it runs from anywhere,
including GitHub's machine — paths and the dot names are [`files.md`](files.md).
The block at the top says what the script needs, so `uv run` fetches it on
anyone's machine — see [`uv.md`](uv.md).
*Week 2 slide 48; week 3 slide 9; week 3 tutorial step 5.*

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "requests"]
# ///
from pathlib import Path
HERE = Path(__file__).parent          # the folder this script is in
DATA = HERE / "data" / "tides.json"   # / joins; .name is "tides.json"
```

## json, and the picture

`json.load` turns a saved `.json` file into the dicts and lists it describes. The
library runs the loop; you still choose which number goes on which axis, and an
axis with no label costs marks. `plt.bar(x, y)` draws bars instead of a line;
`fig, ax = plt.subplots()` keeps hold of the picture, and then it is `ax.plot(...)`.
*Week 3 slides 35, 38 and 41.*

```python
import json
import matplotlib.pyplot as plt
d = json.load(open("data/tides-QUB-2026.json"))
heights = [float(v) for v in d["data"][259][2:]]   # 17 Sept, text into numbers
plt.plot(range(1, 25), heights)
plt.xlabel("hour")
plt.ylabel("metres above chart datum")
plt.savefig("out/tide-day.png", dpi=150)
plt.show()
```

## Things that look like Python but are not yet in this course

A model writes these without being asked. None is wrong; none has been taught. Ask
what one does until you can say it in a sentence, or ask for the version without it.

| Not yet | What you have instead |
|---|---|
| `class`, `self` | a `def` |
| `while` | `for` over a list |
| `try` / `except` | let it crash and read the message — it names the line |
| `lambda` | a `def` with a name |
| `import numpy` | a list, and a loop |
| `import pandas` | `json.load`, and a list |
| `with open(...) as f` | real, but never explained — the template's `plot.py` has one |
| `%`, `//`, `continue` | seen on a slide, never explained. Ask before you keep one |
| `{k: v for ...}`, `set()` | a dict, and a list you build with `.append()` |
| type hints, `->`, decorators | nothing. They change what a reader knows, not what runs |

Keeping a line you cannot explain is allowed. Saying so in your `PROCESS.md` is
what the mark is for.
