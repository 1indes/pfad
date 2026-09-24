# Week 04 — One control, one clear response

Two hours: **try the demos for one hour, adapt an idea for half an hour, then
work on Assignment 2 for half an hour.**

[The slides](https://sd5913.github.io/teaching/week04/) and this folder share one promise:

> When I choose a day, the chart shows that day's 24 hourly tide heights.

| Example | Where the data comes from | Where the picture is made |
|---|---|---|
| [Streamlit app](app.py) | A committed JSON file, read by Python | Streamlit builds the chart for the browser |
| [Browser frontend](browser/index.html) | An HTTP request to the FastAPI backend | JavaScript draws the chart in the browser |
| [FastAPI backend](api.py) | The same committed JSON snapshot | It returns records; the client draws them |

Streamlit still has a browser and a server, even when both run on your laptop.
Its Python script reads a local file; it does not call our separate `/tides` API.

## Before starting

Open a terminal in your clone's **repository root**, the folder containing
`week01`, `week02`, `week03`, and `week04`. If you are still in `week03`, run
`cd ..` first. All commands below run from the root.

```bash
git switch 2026
git pull
```

Use `uv --version` and `node --version` to check the tools. `uv` manages Python
and the libraries; **Node.js 22.12 or newer** is also needed for the local Worker.
The [lab setup](https://github.com/ait4x/v915-setup) installs both. The first run
needs internet to download dependencies. The Streamlit app then uses the saved
snapshot; the browser demo needs a running API.

## 0:00–0:15 — Run the complete interaction

```bash
uv run --with streamlit --with pandas streamlit run week04/app.py
```

Open <http://localhost:8501>. Choose **September**, then **day 17**. Change the
day; the chart and date caption should change together. Every day has 24 heights.
Try January 31, then February: the day selector should offer only February's days.

| Part | In this app |
|---|---|
| Input | The month and day selectors |
| State | The currently selected month and day |
| Response | The chart and its date caption |

Read [`app.py`](app.py) from the file load to `st.line_chart`:

1. Read the snapshot beside the script.
2. `parse_rows` turns strings into numbers.
3. `select_month` keeps the chosen month's records.
4. `select_day` chooses one record.
5. Draw its 24 heights, indexed by hour 1 to 24.

A widget change reruns the script with the new value. Stop Streamlit with
**Ctrl+C** when you have finished this demo.

## 0:15–0:30 — Follow a browser request

Start a static file server:

```bash
uv run python -m http.server 8000 --bind 127.0.0.1
```

Open <http://127.0.0.1:8000/week04/browser/>. This is a working frontend using
plain JavaScript and SVG; it needs no React installation or build step.

Choose a month and then a day. **Open the JSON request** shows what crossed the
network: daily records, not a finished chart. Read [`browser/app.js`](browser/app.js):
`fetch` asks for a month; `showDay` selects a record; `drawChart` draws its heights.
Changing the day reuses the downloaded month without another request.

Open your browser's developer tools → Network. Change the month and find the
`/tides?month=...` request. Identify its method, status and JSON response.

**FastAPI** connects URLs to Python functions. In the
[live API docs](https://sd5913-week04-tides.venetanji.workers.dev/docs), open
`GET /tides`, press **Try it out**, enter `9`, and execute. Expect 30 records,
starting with September 1; each contains 24 heights. Try `13` and inspect the
validation error. The route is in [`api.py`](api.py).

Leave the static server running for the next demo. To use the API locally later,
change `API` in `browser/app.js` to `http://127.0.0.1:8787` and start the completed
Worker with `uv run pywrangler dev` in a second terminal. The API already permits
browser requests from this local port-8000 page and the teaching site.

## 0:30–0:40 — Waiting, polling and callbacks

In a second terminal at the repository root:

```bash
uv run week04/events/blocking.py
```

Wait before typing your name. Which printed line cannot appear until you answer?
That execution path is blocked at `input()`.

Now open <http://127.0.0.1:8000/week04/events/>. Move both sliders:

- The polling example checks the value once per second.
- The event callback updates the result when you move its slider.

Read the script in [`events/index.html`](events/index.html). Change the polling
interval from `1000` to `100` and reload. What feels different? What extra work
happens even when nobody touches the control? Both examples let the browser
keep working between responses; neither uses a blocking loop in JavaScript.

## 0:40–1:00 — One test, red then green

Use the **unfinished starter**, [`tdd_api.py`](tdd_api.py). It creates a FastAPI
app and imports the data helpers, but deliberately has no `/tides` route.
The complete `api.py` and deployed service already work, so testing those first
would start green.

Stop any Worker already using port 8787 with **Ctrl+C**. In one terminal:

```bash
uv run pywrangler dev week04/tdd_api.py
```

Wait for `Ready on http://localhost:8787` (or `127.0.0.1:8787`), then open
<http://127.0.0.1:8787/docs>. It should show **Week 4 · test first**, with no tide
route. Local development needs no Cloudflare account or deployment.

In a second terminal, read [`tdd/test_api.py`](tdd/test_api.py), then run it:

```bash
uv run --with pytest python -m pytest week04/tdd/test_api.py
```

**Red:** expect `HTTP Error 404: Not Found`. The server is running, but the route
is missing. A connection-refused error means the server did not start; fix that
before treating the test as evidence.

Add this route to `tdd_api.py`, above `Default = ...`:

```python
@app.get("/tides")
def tides(month: int):
    return select_month(load_rows(), month)
```

Wrangler reloads when you save. Wait for it to be ready, then run the **same test**.
**Green:** expect `1 passed`. Explain one assertion to your partner. The completed
[`api.py`](api.py) also validates that the month is from 1 to 12.

Stop the Worker and static file server with **Ctrl+C** when finished. Keep your
exercise edit; there is no need to deploy it or push it to the course repository.

## 1:00–1:30 — Adapt an idea

Choose one idea for your own project: a meaningful selector, a response to an
event, a data request, or a small test. Write the promise first:

> When I ___, the interface ___.

Use your own data and keep the scope to one action and one visible response.
Ask a partner to try it and explain what they expected to happen.

The image-generation example in the slides is another request/response pattern:
a prompt goes to an API and image data comes back. It is an instructor example,
not a required account or purchase. Its illustration is not measured tide data.

## 1:30–2:00 — Assignment 2 clinic

[Assignment 2](../assignments/02-data-visualisation.md) is due **Sunday 4 October,
23:59**. No class on 1 October. Use this time to ask a tutor about your question,
source, picture, README, or PROCESS.md.

Start from [the assignment template](https://github.com/sd5913/assignment-2-template).
In **your assignment repository**, run:

```bash
uv run https://raw.githubusercontent.com/sd5913/pfad/2026/assignments/check.py --assignment 2
```

Read a failing item, fix it, then push to rerun the check on GitHub. A green check
confirms the listed conditions; a person still assesses what the picture reveals.
A web interface is optional for Assignment 2. Your own committed raw data and
picture remain required; do not submit the Quarry Bay teaching example.

## Troubleshooting

| What happened | What to check |
|---|---|
| The browser shows code or refuses a request | Use the `http://127.0.0.1:8000/...` link, not a `file://` URL. |
| `Address already in use` | Stop the earlier server in its terminal before starting another on the same port. |
| `node` or `uv` is not found | Reopen the terminal after installing the lab tools; see [the uv reference](../reference/uv.md). |
| The API test passes before you add anything | Stop the completed Worker and start `week04/tdd_api.py`. Check the title at `/docs`. |
| The browser cannot fetch JSON | Open the JSON link. Check the connection, API URL and page origin. The local page must use port 8000. |
| A Python file cannot be found | Run commands from `pfad`, not from `week04`. |

## Maintainer checks and deployment

The student path ends above. [`MAINTAINERS.md`](MAINTAINERS.md) records the
additional checks, the Worker adapter, and deliberate snapshot refresh.
