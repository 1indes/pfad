# When it goes wrong

Every error message in this course is a sentence somebody wrote to help you. A
Python one names your file and the line number; a git one usually tells you the
command to run next. **Read the last line first, then work upwards.**

This is the dictionary: the exact text you see, what it means, what to do. Grouped
by where it happens. If yours is not here, paste the last line into a search box —
you will not be the first.

---

## In the terminal

**`git: command not found` · `'git' is not recognized`**
The shell looked through every folder on your `PATH` and did not find it. Almost
always: the terminal opened *before* the installer ran, and a window that is
already open never notices a `PATH` change. Close it, open a new one. Still
failing? The install did not finish — go back to [`week01`](../week01/README.md), step 3.

**`uv: command not found`**
Same cause, same fix: new terminal first. If it still says that, uv is not
installed — the `setup.bat` link in [`uv.md`](uv.md) on Windows, `brew install uv`
on macOS. `uv --version` is how you check.

**`Python was not found; run without arguments to install from the Microsoft Store`**
You typed `python` on Windows. That name is a stub Microsoft ships whose only job
is to open the Store; it is not Python. Do not install from there. Type
`uv run script.py` instead — this is the exact trap uv exists to sidestep.

**"Windows protected your PC"** (blue SmartScreen box)
Windows does not recognise `setup.bat` because almost nobody has run it yet.
*More info* → *Run anyway*. Safe to run again if you are unsure.

**`cd: … No such file or directory`**
The folder is not where you are standing, or is spelled differently. `pwd` says
where you are, `ls` says what is here, **Tab** completes a name you got right.
Paths and how they are counted: [`files.md`](files.md).

---

## From `uv run`

**`error: An opening tag (# /// script) was found without a closing tag (# ///)`**
The dependency block at the top of the file is broken — usually a missing `# ///`
on the last line, or a line inside the block that does not start with `#`. Every
line of that block is a comment, including the blank-looking ones.

**`× No solution found when resolving script dependencies … was not found in the package registry`**
A name in `dependencies = [...]` does not exist on PyPI. It is a typo, or you
wrote the import name where the install name goes — `pygame-ce` installs,
`pygame` imports. Check the library's own page.

**`ModuleNotFoundError: No module named 'matplotlib'`** (with a `# /// script` block)
The script imports something the block does not list. Add it to the list and run
again. **Do not `pip install` it** — that installs into a different Python and the
error will not even change. See [`uv.md`](uv.md).

**`ModuleNotFoundError: No module named 'tides'`**
Different problem: that is not a library, it is a file in the folder. You are
running from the wrong place, or you copied the script somewhere without its
neighbour. `cd` into the folder that has both and try again.

**`Downloading cpython-3.12… (29.4MiB)`** · **`Installed 5 packages in 4ms`**
Not errors. uv is fetching the interpreter and the libraries the first time, and
saying so. You will not see either line again for that script.

---

## From git

**`fatal: not a git repository (or any parent up to mount point /)`**
You are not standing in a repository. `cd` into your project folder — the one with
`.git/` in it — and try again. In VS Code, *File → Open Folder* on the project,
then *Terminal → New Terminal*, and the terminal starts in the right place.

**`nothing to commit, working tree clean`**
Git sees no change. Either you did not save the file (`Ctrl+S` / `Cmd+S`), or you
edited a file in a different folder from the one you are committing in. `git status`
before and after saving will show you which.

**`! [rejected] main -> main (fetch first)`** · **`(non-fast-forward)`**
GitHub has a commit you do not have — usually a past you, editing on the website.
`git pull`, then `git push`. In VS Code, **Sync Changes** does both in that order,
which is why it is one button.

**`hint: You have divergent branches and need to specify how to reconcile them`**
Both you and GitHub have commits the other lacks, and git will not guess. Run
`git config pull.rebase false` once, then `git pull` again. That tells git to
merge, which is what you want for an essay or a plot.

**`CONFLICT (content): Merge conflict in README.md`**
You and GitHub changed the same lines. Open the file: the two versions are marked
with `<<<<<<<`, `=======` and `>>>>>>>`. Delete the markers, keep the text you
want, save, `git add`, `git commit`.

**`fatal: refusing to merge unrelated histories`**
You are trying to join two repositories that were started separately — usually
because a repo was made on GitHub *and* made again with `git init` on the laptop.
Do not force it. Keep the one with your work, clone it fresh, copy your files in.

**`Support for password authentication was removed`**
Git asked for your GitHub password; that stopped working in 2021. Let VS Code
sign you in (it opens a browser the first time you push), or install the
[GitHub CLI](https://cli.github.com/) and run `gh auth login`.

**`Permission denied (publickey)`**
The remote is an SSH address (`git@github.com:…`) and this machine has no key
registered. The simplest fix is to use the HTTPS address instead:
`git remote set-url origin https://github.com/YOUR-USERNAME/YOUR-REPO`.

**`remote: Repository not found`**
The URL is wrong, the repo is private and you are not signed in, or the name has a
typo. Copy the address off the repo's own page rather than typing it.

**A push to `sd5913/pfad` is rejected**
Expected. You have read access to the course repo, not write. Open an issue, or
fork it and send a pull request — [`git.md`](git.md).

**Your commits show a grey avatar and are not on your contribution graph**
`git config user.email` does not match an email on your GitHub account. Fix the
config; past commits stay grey. This is why week 1 sets it before your first commit.

---

## On GitHub

**The Actions tab is empty**
GitHub looks at one address and nowhere else. The file must be at exactly
`.github/workflows/check.yml` — not `workflow/`, not `github/`, not `Check.yml`.
`git ls-files .github` shows what git actually has; if the file is not in that
list, it was never committed.

**A red cross next to your commit**
The check ran and something failed. Click it → *check* → the *Check* step, and you
get the same list `uv run …/check.py` prints. A red cross is information, not a
grade. Read the log from the bottom up.

**`FAIL  README.md is a placeholder (12 words)` · `is N words; the essay is 500–1000`**
The essay goes in `README.md` itself, at the top level, and it is measured without
the bibliography. The second one is the writing, not the repo shape — it clears on
Sunday, not today.

**`FAIL  README.md has no References heading`**
Add `## References` at the bottom and cite what you drew on, in APA. Check every
reference actually exists before you trust it.

**`FAIL  PROCESS.md is missing` · `is empty`**
Make `PROCESS.md` at the top level, spelled exactly that. Tools you used, one
thing you kept, one thing you rejected, and why. "I did not use any" is valid if
it is true.

**`note  process.md should be spelled PROCESS.md exactly — git mv it`**
Windows and macOS do not care about capitals; GitHub does. `git mv process.md PROCESS.md`.

**`FAIL  3 commits, all on one day`**
Commit again tomorrow, from home. It cannot be cleared on the day and it is not
meant to be — [`git.md`](git.md) says why.

**`FAIL  files that do not belong in a repo: .DS_Store, notes.docx`**
Delete them, commit the deletion, and add the names to `.gitignore` so they do not
come back. What belongs where: [`files.md`](files.md).

**`FAIL  no dependency block: plot.py needs matplotlib`**
The script imports a library and does not say so. Add the `# /// script` block —
[`uv.md`](uv.md).

**`FAIL  no data/ folder with a file in it`** (assignment 2)
The raw file you fetched has to be committed, so the repo runs with the wifi off.
`git add data`, commit, push.

**`FAIL  the repository is private`**
GitHub → your repo → *Settings* → *Danger Zone* → *Change visibility* → Public. A
private repo cannot be marked.

**A README image is broken** (grey box, or the alt text)
The path in `![…](out/plot.png)` is counted from the repo root and is
case-sensitive on GitHub. And the picture has to be committed — `git ls-files out`
will tell you whether it is.

---

## From Python

The last line is the error. The lines above it are the route the program took to
get there, newest at the bottom; the second-to-last block names your file and the
line number.

**`NameError: name 'color' is not defined. Did you mean: 'colour'?`**
You used a name that does not exist yet — a typo, or a variable defined further
down the file than the line using it. Python often guesses the name you meant,
and the guess is usually right.

**`TypeError: can only concatenate str (not "int") to str`**
`"total: " + 5`. Text and numbers are different things and `+` will not bridge
them. Either `"total: " + str(5)`, or an f-string: `f"total: {5}"`. Going the
other way — a number out of a file that is still text — is `float("2.19")`.

**`ValueError: could not convert string to float: '2.19 m'`**
`float()` was handed text that is not only a number. Strip the unit first. This is
the everyday state of data somebody else published.

**`IndentationError: expected an indented block after function definition on line 1`**
The body of a `def`, `for` or `if` must be indented under it — four spaces, and
the same four every time. Do not mix tabs and spaces; VS Code will do it for you.

**`SyntaxError: expected ':'`**
A missing colon at the end of a `def`, `for`, `if` or `while` line. The `^` points
at where it should have been.

**`SyntaxError: '(' was never closed`**
An unclosed bracket or quote. The line it names is where the bracket *opened*,
which is often a line or two above the one that looks wrong.

**`IndexError: list index out of range`**
You asked for item `n` of a list with fewer than `n+1` items. Counting starts at
`0`, so a list of three has `0`, `1`, `2`, and `[3]` is one too far. `len(things)`
tells you how many there are.

**`KeyError: 'Height'`**
A dictionary has no such key. Capitals and spaces count: `"Height"` is not
`"height"`. `print(d.keys())` shows you what is actually in there.

**`FileNotFoundError: [Errno 2] No such file or directory: 'data/tides.json'`**
The address is relative, and it is counted from wherever you ran the command, not
from where the script lives. That is why every script here builds its paths from
`HERE = Path(__file__).parent` — [`files.md`](files.md).

**`AttributeError: 'NoneType' object has no attribute 'upper'`**
Something you expected to be a value is `None`. Usually a function that forgot to
`return`, or a lookup that found nothing. Print it just before the failing line.

**`requests.exceptions.ConnectionError`**
A script tried to fetch something and there was no connection. If the file should
have been in `data/`, you deleted it — `git status` will say which, and
`git checkout data` brings it back. Fetch once, keep the file, parse the file.

**A window opens and closes at once**
Read the terminal, not the window. The traceback is sitting there and it names the
line. That is not a failure of the tutorial; that is the tutorial.

**`pygame` cannot open a display**
No screen — a remote machine or a headless lab image. Every window script here
takes `--save out.png`, which draws one frame to a file instead.

**The window will not close and the terminal is stuck**
The script is waiting on `plt.show()`. Close the plot window. `Ctrl+C` in the
terminal also works.

---

## It ran, and it is wrong

The worst ones do not print anything at all. Four that this course puts in front
of you on purpose:

- **`"6" + "6"` is `"66"`.** Nothing is broken and nothing errors; the code
  quietly did the other job. Anything read out of a file or typed on a keyboard is
  text until you convert it.
- **A function with no `return` returns `None`** — and printing it twenty-four
  times is what that looks like.
- **`b = a` on a list does not copy it.** Both names point at the same list, so
  changing one changes the other. Numbers and strings do not behave this way, which
  is what makes it hard to see.
- **A path built the wrong way is still a perfectly real-looking path** to a file
  that does not exist.

When the output is wrong and there is no message, you are back to the three
questions: what did I predict, what did it do, and which line is the difference.
