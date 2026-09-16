# Files, folders and the dot

Every script in this course reads a file and writes one. A repository is a folder.
GitHub runs your check only if a file sits at one exact address. When the address
is wrong, nothing happens and nothing says why. This page is ten minutes and it is
the ten minutes most people skip.

## A folder is a list of names

Your computer is a tree: folders hold files and other folders. Finder and Explorer
draw it as a picture; the terminal shows it as text. It is the same tree.

| Command | What it does |
|---|---|
| `pwd` | *print working directory* — where am I? |
| `ls` | what is here? (`ls -a` shows the hidden names too; Windows PowerShell: `ls -Force`) |
| `cd name` | go into the folder called `name` |
| `cd ..` | go up, into the folder this one is in |
| `cd` | go home |
| `mkdir name` | make a folder. `mkdir -p .github/workflows` makes both levels at once |
| `cat name` | print a text file |

Press **Tab** after typing the first letters of a name and the terminal finishes it.
Press **↑** to get the last command back. Those two keys are half of using a terminal.

```
$ pwd
/Users/mia/Documents
$ ls
pfad        tidal-clock
$ cd tidal-clock
$ ls
PROCESS.md  README.md  data  fetch.py  out  plot.py
$ cd ..
$ pwd
/Users/mia/Documents
```

*Working directory* is the terminal's word for "here". Every command runs from
there, and every relative address is counted from there.

## A path is an address

`tidal-clock/data/tides.json` is a path: the names of the folders you pass
through, then the file, separated by `/`. Windows writes `\` instead, and Python
accepts either.

- A path that starts with `/` (or `C:\`) is **absolute** — the address from the
  root of the disk, the same wherever you are.
- Anything else is **relative** — counted from the working directory. `data/tides.json`
  means a different file depending on where you are standing.
- `.` is here. `..` is the folder above. `../faults` is the folder next door.
  `~` is your home folder.

The trap this sets: run `uv run tides.py` from inside `week03/` and it finds
`data/`; run `uv run week03/tides.py` from `pfad/` and the same script looks for
`pfad/data/`, which does not exist. That is why every script in this course
starts like this:

```python
HERE = Path(__file__).parent          # the folder this script is in, wherever you ran it from
DATA = HERE / "data" / "tides.json"   # / between two paths joins them
OUT = HERE / "out"
```

`__file__` is the script's own address. `.parent` is `..` in code. `.name` is the
last piece (`tides.json`). Build addresses from `HERE` and the script works from
any working directory, on any machine, including GitHub's.

## The names that start with a dot

A name beginning with `.` is hidden — by Finder, by Explorer, and by plain `ls`.
Not by git, and not by VS Code's file list. It is an old convention for "machinery,
not work", and every repository you make has three of them:

| Name | What it is |
|---|---|
| `.git/` | The repository itself: every commit, every branch. `git clone` creates it. Never edit anything inside it. Delete it and the folder is just files again. |
| `.github/workflows/check.yml` | What GitHub runs on every push. The address is exact: `.github/workflow/` or `github/workflows/` and the Actions tab stays empty. |
| `.gitignore` | A plain text list of names git will never commit, one per line; a trailing `/` means a folder. `cat .gitignore` to read it. |

Two more appear on their own and belong in `.gitignore`:

- `.venv/` — a private Python installation that `uv` makes next to your script.
  Hundreds of megabytes, rebuilt in seconds, never committed.
- `.DS_Store` and `Thumbs.db` — notes Finder and Explorer keep for themselves.
  Junk; the check flags them.

To see hidden names in Finder press **⌘ Shift .**; in Explorer, *View → Show →
Hidden items*. Or use `ls -a`.

## When a file "is not there"

1. `pwd` — are you where you think you are?
2. `ls -a` — is it spelled that way, dot included, same capitals? macOS forgives
   `process.md` for `PROCESS.md`. GitHub does not.
3. `git ls-files` — did git get it? An ignored or never-added file is not in the
   repository, however hard you push.
