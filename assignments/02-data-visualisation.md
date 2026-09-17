# Assignment 2 — Data visualisation

**Weight:** 10% · **Due:** Sunday 4 October 2026, 23:59

Numbers about a natural phenomenon, obtained from a file somebody publishes, turned
into a picture. Published as a GitHub repository.

---

## The brief

Pick a **natural phenomenon**. The tide, the weather, the moon, earthquakes,
rainfall, air quality, sunrise times, bird sightings, typhoons, solar radiation,
river levels, the length of the day. Something that happens whether or not anyone
is measuring it — and that somebody is measuring anyway.

Then do three things.

**Obtain the numbers.** Somebody already did the measuring and published the
result: JSON, CSV, or a table on a web page. Find that file, fetch it **once**, and
commit the raw reply, unchanged, to `data/` in your repository. Your scripts read
the committed file. They do not fetch every time they run, and they work with the
wifi off.

**Make a picture from them.** Informative, artistic, or animated — the three are
equally welcome and they are marked the same way. Any library you like; the script
says what it needs.

**Say what it is.** A `README.md` with the phenomenon, where the numbers come from
with a link, the picture itself, and how to run the thing. Plus a `PROCESS.md`, as
in assignment 1.

## Two paths, both fine

**The designer's path.** The chart type follows from the dimensionality of the
data: one number over time is a line, two numbers is a scatter, three might be
position and size, a cycle might be a circle. Label the axes. Say the units. One
message per picture, and the picture makes it. If somebody has to read a paragraph
to understand what they are looking at, the picture has not done its job.

**The artist's path.** The numbers are material. A tidal range can be the width of
a stroke, an earthquake can be a scratch in a plate, a month of rainfall can be
thirty rings on a page. The picture does not have to explain itself and does not
have to be legible as a chart. It does still have to be **made from the actual
numbers**, and you still have to say where they came from — an artwork built on
invented data is not this assignment.

Read week 2's `tides.py` if you want an example of the second path and week 3's
`plot_day.py` for the first. Both are in this repository.

What is not acceptable on either path: a chart of numbers you typed in by hand, a
screenshot of somebody else's chart, or a tide chart of Quarry Bay — that one has
been done, in front of you, in week 3.

## What to hand in

A **public GitHub repository** on your own account, named after the phenomenon
(`tidal-clock`, `quakes-this-month`, `kowloon-rainfall`), not `assignment2`.

Start from the template: open [`sd5913/assignment-2-template`](https://github.com/sd5913/assignment-2-template),
press **Use this template → Create a new repository**, and you have this tree, the
check workflow, and a `fetch.py` and `plot.py` that already run — on the Observatory's
daily temperature, which is an example and not your phenomenon. Then replace every
line of it.

```
your-repo/
├── README.md          the phenomenon, the source (a link), the picture, how to run it
├── PROCESS.md         how you used AI: one thing kept, one thing rejected, and why
├── fetch.py           gets the file once and saves it to data/   (or part of another script)
├── plot.py            reads data/, makes the picture, saves it to out/
├── data/
│   └── <the raw file you fetched, exactly as it arrived>
└── out/
    └── <your picture: .png, .svg, .gif or .mp4>
```

The file names are yours. The shape is not.

### `README.md`

At least 150 words, and it must show the picture. Cover:

- **The phenomenon.** What goes up and down, and why you looked at it.
- **The source.** A link to the page or endpoint the file came from, and one line
  on what is in the file — how many rows, what a row means, what the units are.
- **The picture**, embedded: `![what it is](out/your-picture.png)`. If it is an
  animation, embed a still as well; GIFs render on GitHub, MP4s do not.
- **What the picture shows**, in two or three sentences. Including what it hides —
  every transformation throws something away, and naming what yours threw away is
  the single easiest way to sound like you know what you did.
- **How to run it**: the `uv run` line, and nothing else.

### `PROCESS.md`

Same as assignment 1, same weight, same honesty. Which tools you used and for
what; one thing you **kept** and why it was good; one thing you **rejected** and
why it was wrong. "I did not use any" is fine if it is true.

If a model wrote most of the plotting code — likely, and allowed — the interesting
part of `PROCESS.md` is what you had to correct. Did it invent a column name? Use
pandas where a list would do? Silently drop the rows it could not parse?

### The code

One or more `.py` files, each carrying its own dependency block so `uv run` needs
nothing else:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "requests"]
# ///
```

Somewhere in it there must be **a loop over the numbers and a function you wrote**
— not because loops and functions are the point, but because they are what makes a
program yours rather than a recipe you ran. A marker will read them.

### A history that shows you worked

A handful of commits across more than one day: fetching the file, printing it,
the first ugly plot, the one that works. The ugly one is worth committing. Commit
messages in plain language.

## Publish it as a web page — optional

If your picture is a web page — a [`folium`](https://python-visualization.github.io/folium/)
map, a [Plotly](https://plotly.com/python/) chart, anything your script writes as
`site/index.html` — copy [`pages.yml`](pages.yml) into your repo as
`.github/workflows/pages.yml`, change the one line it tells you to, and turn on
Pages (Settings → Pages → Source: GitHub Actions). Every push then rebuilds the
page on GitHub's machine from the numbers in `data/` and publishes it at
`https://YOUR-USERNAME.github.io/YOUR-REPO/`. Put that link in your README.

[`sd5913/tidal-streams`](https://github.com/sd5913/tidal-streams) is a complete
worked example of this assignment, with the page live at
<https://sd5913.github.io/tidal-streams/>: the same numbers as the animated GIF,
as a map you can pan, zoom and play. Its `README.md` and `PROCESS.md` are the
shape yours should have. Do not commit `site/` — it is output.
A page that builds itself is not extra credit, but it is the thing the group
project will demand of you in November, and it is easier to learn on a map of
the sea than on a deadline.

## Submit

Post the **repository URL** on Canvas: `https://github.com/YOUR-USERNAME/YOUR-REPO`

Public, on your own account, `README.md` at the top level so it renders on the
front page. Nothing is uploaded and there is no PDF.

## Check it before you submit

```bash
uv run https://raw.githubusercontent.com/sd5913/pfad/2026/assignments/check.py --assignment 2
```

`--assignment 2` is not optional — without it you get assignment 1's spec and a
confusing list about bibliographies.

The template already carries the workflow, so GitHub has run it on every push since
your first. If you built the repo by hand, copy [`02-check.yml`](02-check.yml) into it
as `.github/workflows/check.yml` and push. The **Actions** tab then shows a green tick
or a red cross with the same checklist.

It checks shape, not quality: the files exist, the README is long enough and shows
an image, every script says what it needs, `data/` has something in it, a picture
exists, the history spans more than one sitting, nothing junk is committed. A tick
means the repo has the right shape. Whether the picture says anything is a person's
call.

## How it is marked

| | |
|---|---|
| **Data** (25%) | A real phenomenon, from a real published source, fetched once and cached in `data/`, documented with a link. The repo runs with the internet off. |
| **Picture** (35%) | It says something, or it means something. The transformation fits the dimensions of the data. Informative and artistic are marked equally; undecided is marked badly. |
| **Code** (20%) | It runs with `uv run`, with no arguments and nothing preinstalled. There is a loop and a function a person can read. The dependency block is there and is complete. |
| **Process** (20%) | An honest `PROCESS.md`, and a commit history showing the work happening rather than arriving. |

## Where to find numbers

| Source | What |
|---|---|
| [HKO Open Data](https://data.weather.gov.hk/weatherAPI/doc/HKO_Open_Data_API_Documentation.pdf) | Hong Kong: tides, temperature, rainfall, sunrise and moonrise times, lightning, typhoon tracks. JSON and CSV, no key. |
| [USGS earthquakes](https://earthquake.usgs.gov/earthquakes/feed/) | Every earthquake on Earth, GeoJSON, feeds from the last hour to the last month. |
| [AQHI Hong Kong](https://www.aqhi.gov.hk/en/download/past-24-hours-pollutant-concentration.html) | Hourly pollutant concentrations, CSV. |
| [Open-Meteo](https://open-meteo.com/) | Weather and historical weather anywhere, JSON, no key. |
| [NASA POWER](https://power.larc.nasa.gov/) | Solar radiation and climate for any point on Earth, CSV. |
| [GBIF](https://www.gbif.org/) · [eBird](https://ebird.org/data/download) | Species and bird observations. |
| [NOAA tides & currents](https://tidesandcurrents.noaa.gov/) | If you would rather have somebody else's sea. |
| Wikipedia | A table of almost anything, if you are willing to parse HTML. |

If it needs a login, an API key, or money, pick another one. There is enough free
data about the sky and the sea to last a lifetime.

## Before you start

Work through [`week03/README.md`](../week03/README.md) if you have not. It is the
same job, done twice, with the code in front of you — and every script in it is a
legitimate starting point for yours.

Two things worth your time:

- Edward Tufte, *The Visual Display of Quantitative Information* (1983) — on the
  ratio between the ink on the page and the information in it.
- [Nadieh Bremer's *Data Sketches*](https://www.datasketch.es/) — twelve months of
  two people making a chart a month, with every decision written down. The best
  argument that the designer's path and the artist's path are the same path.
