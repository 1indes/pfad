"""Exercise real Streamlit reruns and compare plotted values with the snapshot."""

import json
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def app(monkeypatch):
    # streamlit run adds the script's directory to sys.path; reproduce that here.
    monkeypatch.syspath_prepend(str(ROOT))
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()


def test_selecting_a_day_uses_its_24_heights(monkeypatch):
    plotted = []
    original = st.line_chart

    def capture(data, *args, **kwargs):
        plotted.append(data.copy())
        return original(data, *args, **kwargs)

    monkeypatch.setattr(st, "line_chart", capture)
    screen = app(monkeypatch)
    assert not screen.exception
    screen.selectbox[0].set_value(9).run()
    screen.selectbox[1].set_value(17).run()
    assert not screen.exception
    assert screen.caption[0].value.endswith("2026-09-17")
    raw = json.loads((ROOT / "tides-QUB-2026.json").read_text())
    expected = next(row for row in raw["data"] if row[:2] == ["09", "17"])
    assert plotted[-1]["Height (m)"].tolist() == [float(value) for value in expected[2:]]
    assert plotted[-1].index.tolist() == list(range(1, 25))


def test_changing_month_never_keeps_an_invalid_day(monkeypatch):
    screen = app(monkeypatch)
    screen.selectbox[1].set_value(31).run()
    screen.selectbox[0].set_value(2).run()
    assert not screen.exception
    assert len(screen.selectbox[1].options) == 28
    assert 1 <= screen.selectbox[1].value <= 28
    assert screen.caption[0].value.endswith(f"2026-02-{screen.selectbox[1].value:02}")
