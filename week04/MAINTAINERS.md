# Week 4 — Maintainer checks

Run commands from the repository root. The normal student sequence is in
[README.md](README.md).

## Data and app checks

```bash
uv run --with pytest --with streamlit --with pandas python -m pytest week04/tests
uv run pywrangler deploy --dry-run
```

The tests check the data transformations, validate the saved year, and exercise
the Streamlit selectors, including changing from a 31-day month to February.
They do not need a running API. The dry run validates the Worker bundle without
deploying it. The [Week 4 workflow](../.github/workflows/week04-tests.yml) runs
both checks.

For the completed service, start `uv run pywrangler dev`, then run:

```bash
uv run --with pytest python -m pytest week04/tdd/test_api.py
```

Expect a pass. For the student exercise, stop that Worker and start
`uv run pywrangler dev week04/tdd_api.py`: expect 404 until the student adds the
route described in the README. The intentionally incomplete starter is excluded
from the default test path so that routine `pytest` runs do not require a server.

For the browser demo, serve the repository on port 8000 as described in the
README. Check September 17, a month change, and a failed network request. The
frontend must hide old chart data while loading or after failure. Changing a day
should not fetch again; a late response for a previous month must not replace the
latest selection. `events/` provides the blocking, polling and callback demos.

## Worker details

FastAPI supplies the route and `/docs`. `workers.asgi.entrypoint(app)` adapts that
app to Cloudflare's Python Worker runtime. Python runs through Pyodide; Node.js
runs the local development tooling. [`../wrangler.jsonc`](../wrangler.jsonc)
specifies the main module, runtime compatibility and bundled JSON file.

CORS permits `https://sd5913.github.io`, `http://localhost:8000`, and
`http://127.0.0.1:8000`. The `/teaching/` path is not part of an origin. CORS is a
browser reading rule, not authentication. Check a valid month (200), missing or
invalid month (422), `/docs`, and `/openapi.json` before class.

Deployment is a separate maintainer action:

```bash
uv run pywrangler deploy
```

Deploy only the completed `week04/api.py` configured in `wrangler.jsonc`, never
the exercise starter. See [Cloudflare's FastAPI adapter documentation](https://developers.cloudflare.com/workers/languages/python/packages/fastapi/).

## Snapshot refresh

The app and API read committed files, without fetching from the Observatory
on each request. `week03/data/tides-QUB-2026.json` and
`week04/tides-QUB-2026.json` must stay identical.

Only when deliberately refreshing the snapshot:

```bash
uv run week04/refresh_data.py
```

This fetches one response, validates its field names, all 365 dates and finite
numeric heights, then replaces each snapshot using an atomic file write.
Review both changes and run the checks before committing. Replacing the two
files is not one transaction; if the second write fails, rerun the refresh and
confirm the files match before committing.

The manual [refresh workflow](../.github/workflows/refresh-tides.yml) performs the
same checks before committing both files. A data refresh does not redeploy the
Worker; deploy separately when the served snapshot should change.
