# `uv run`, and nothing else

```bash
uv run script.py
```

That is the only Python command in this course. Not `python`, not `pip`, not
`python3`, not `source .venv/bin/activate`. One line, on Windows and on macOS, in
the lab and on your laptop and on GitHub's machine.

This page is what that line actually does, so that when it misbehaves you know
which half to look at.

## What happens when you type it

Four things, in order:

1. **It finds a Python.** If a suitable one is installed it uses that. If there is
   none, it downloads one — about 30 MB, once, and it says so:
   `Downloading cpython-3.11.16 (29.4MiB)`. You do not install Python before this
   course; `uv` does it when it is needed.
2. **It reads the `# /// script` block** at the top of your file to find out what
   the script needs.
3. **It builds a private environment** with exactly those libraries in it. The
   first time you see `Installed 5 packages in 4ms`; after that, nothing, because
   it is cached.
4. **It runs the script** in that environment.

```
$ uv run tides.py
Installed 5 packages in 4ms
 1:00  2.19  ######################
 ...
```

The `Installed …` line appears once per new set of requirements and then never
again. It is not a warning. It is uv telling you it did the part you would
otherwise have had to do by hand.

## Why the course never says `python` or `pip`

**`python` is not one program.** On a fresh Windows machine typing `python` opens
the **Microsoft Store**, because Windows ships a stub at that name whose only job
is to sell you an install. It looks like a command; it is an advertisement. On a
Mac `python` may be a Python from 2019 that half your libraries have dropped
support for, or it may not exist at all and you get `python3` instead. `py` works
on Windows and nowhere else. Four machines, four answers.

**`pip install` installs into whichever of those Pythons you happened to hit**,
system-wide, permanently, for every project at once. Two scripts that want
different versions of the same library cannot both work, and a library you
installed in September is a library your marker does not have in October.

Last year every week of this course shipped a `requirements.txt`, and **every one
of them was missing something** — a library somebody had installed months ago and
forgotten was not standard. The fix is not a better `requirements.txt`. It is
putting the requirements inside the script, where they cannot drift away from it.

`uv run` collapses all of that into one line that behaves the same everywhere.

## The block at the top of every script

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "requests"]
# ///
```

Line by line:

| Line | What it is |
|---|---|
| `# /// script` | The opening tag. uv looks for exactly this, at the top of the file. |
| `# requires-python = ">=3.10"` | Which Pythons this script will run on. `">=3.10,<3.14"` means 3.10 up to but not including 3.14 — used when a library has not caught up yet. |
| `# dependencies = [...]` | The libraries to install, by their name on PyPI, in a comma-separated list. `[]` if the script needs none. |
| `# ///` | The closing tag. Forgetting it is an error, and uv says so plainly. |

Three things about it that are not obvious:

- **Every line is a comment.** The block is invisible to Python; it is a standard
  (PEP 723) that says a comment in this shape is metadata. A script with the block
  is still an ordinary Python file.
- **The name in `dependencies` is the install name, not the import name.** You
  write `dependencies = ["pygame-ce"]` and then `import pygame`. They are often the
  same and sometimes not; the library's own page tells you.
- **Only what comes from outside goes in the list.** `math`, `random`, `json`,
  `csv`, `pathlib` and `datetime` ship with Python — they are not dependencies.
  Neither is a `.py` file of your own sitting next to the script.

Read the block as: *this program is not finished until it says what it needs.*
Every script you hand in from now on carries one if it imports anything, and the
check fails a repo where one does not:

```
  FAIL  no dependency block: plot.py needs matplotlib — add the # /// script block so uv run installs it
```

## Running a script straight off the internet

```bash
uv run https://raw.githubusercontent.com/sd5913/pfad/2026/assignments/check.py
```

`uv run` takes a URL as happily as a filename. It downloads the script, reads its
block, builds the environment and runs it — in **your** current folder, which is
the whole point for the check: it looks at the repository you are standing in.

This is also why the check has nothing to install. Read the top of
`assignments/check.py` and you will see it uses only what ships with Python.

## When a library is missing

You will see this:

```
ModuleNotFoundError: No module named 'matplotlib'
```

It means the script imported something that is not in its environment. **Do not
run `pip install`.** It would install into a Python that `uv run` is not using,
and the error would not even change. Put the library in the block instead:

```python
# dependencies = ["matplotlib"]
```

Run again. uv installs it and the import works. If you would rather uv edited the
block for you:

```bash
uv add --script plot.py matplotlib
```

which rewrites the block in place, pinning a minimum version:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "matplotlib>=3.10.9",
# ]
# ///
```

Either form is fine. What matters is that the requirement lives in the file, so
that the same file works on the lab machine, on your laptop, and on GitHub's
machine during the Actions run — none of which have anything preinstalled.

If the name is wrong you get told, at some length, that no such package exists:

```
  × No solution found when resolving script dependencies:
  ╰─▶ Because matplotlibb was not found in the package registry …
```

Check the spelling on the library's page before you believe anything else.

## Where the environment goes, and why you never see it

A script with a `# /// script` block gets a **cached** environment, kept out of the
way under uv's own cache folder. Nothing appears next to your script. Run
`uv run hello.py` in an empty folder and afterwards the folder still contains
exactly one file.

You will meet `.venv/` anyway, because a folder with a `pyproject.toml` in it is a
*project* rather than a script, and there uv makes the environment locally:

```
Using CPython 3.12.14
Creating virtual environment at: .venv
```

That folder is a whole private copy of Python and its libraries — hundreds of
megabytes, rebuilt in seconds, different on every machine. It is output, not work.
**It is never committed**, which is why `.venv/` is in every `.gitignore` in this
course and why the check flags a repo that contains one. Same reasoning as
`__pycache__/`: see [`files.md`](files.md).

You do not need to make a `pyproject.toml` for anything in this course. One script,
one block, `uv run`.

## If uv itself is not there

```
uv: command not found
'uv' is not recognized as the name of a cmdlet
```

Usually the terminal is older than the install — installers change your `PATH` and
a window that was already open never notices. **Close it, open a new one.**

Still nothing? Install it:

- **Windows** — download and double-click
  <https://github.com/ait4x/v915-setup/releases/latest/download/setup.bat>, which
  sets up the whole toolchain for this course, then open a new terminal.
- **macOS** — `brew install uv`.

`uv --version` tells you it is there.

There is one command you might want beyond `uv run`, and only if you are curious
or offline: `uv python install 3.12` fetches an interpreter up front instead of
waiting for the first script to need one. `uv python list` shows what is already
on the machine. Neither is required.

## When it goes wrong

The errors `uv run` produces, and the Python errors that come out the other side
of it, are in [`errors.md`](errors.md).
