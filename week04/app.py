# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "streamlit"]
# ///

"""A Streamlit app that reads its bundled tide data file.

    uv run --with streamlit --with pandas streamlit run week04/app.py
"""

import calendar
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from transform import parse_rows, select_day, select_month

DATA_FILE = Path(__file__).resolve().with_name("tides-QUB-2026.json")
DATA = json.loads(DATA_FILE.read_text(encoding="utf-8"))
ALL_ROWS = parse_rows(DATA["data"])

st.title("Quarry Bay, one day at a time")
month = st.selectbox("Month", range(1, 13), format_func=lambda n: calendar.month_name[n])

rows = select_month(ALL_ROWS, month)
if not rows:
    st.info("There are no rows for that month.")
    st.stop()

day = st.selectbox("Day", [row["day"] for row in rows])
record = select_day(rows, day)
chart = pd.DataFrame({"Height (m)": record["heights"]}, index=range(1, 25))
chart.index.name = "Hour"
st.line_chart(chart)
st.caption(f"Hong Kong Observatory · Quarry Bay · 2026-{month:02}-{day:02}")
