"""The refresh validator can be checked without contacting the Observatory."""

import json
from datetime import date, timedelta

import pytest

from week04.refresh_data import ROOT, TARGETS, validate


def payload():
    days = [date(2026, 1, 1) + timedelta(days=offset) for offset in range(365)]
    return {
        "fields": ["MM", "DD", *(f"{hour:02}" for hour in range(1, 25))],
        "data": [
            [f"{day.month:02}", f"{day.day:02}", *("1.25" for _ in range(24))]
            for day in days
        ],
    }


def test_validate_accepts_a_full_year():
    result = validate(json.dumps(payload()).encode())

    assert len(result["data"]) == 365


def test_validate_rejects_a_short_file():
    raw = payload()
    raw["data"].pop()

    with pytest.raises(ValueError, match="expected 365 daily rows"):
        validate(json.dumps(raw).encode())


def test_validate_rejects_a_malformed_row():
    raw = payload()
    raw["data"][0].pop()

    with pytest.raises(ValueError, match="every daily row"):
        validate(json.dumps(raw).encode())


def test_validate_rejects_a_duplicate_date():
    raw = payload()
    raw["data"][1][:2] = raw["data"][0][:2]

    with pytest.raises(ValueError, match="one row for every day"):
        validate(json.dumps(raw).encode())


def test_worker_snapshot_matches_the_week03_source():
    source, worker = TARGETS

    assert source == ROOT / "week03" / "data" / "tides-QUB-2026.json"
    assert source.read_bytes() == worker.read_bytes()


def test_validate_rejects_shuffled_hour_labels():
    raw = payload()
    raw["fields"][2:4] = ["02", "01"]
    with pytest.raises(ValueError, match="fields in order"):
        validate(json.dumps(raw).encode())


@pytest.mark.parametrize("height", ["NaN", "Infinity", "-Infinity"])
def test_validate_rejects_non_finite_heights(height):
    raw = payload()
    raw["data"][0][2] = height
    with pytest.raises(ValueError, match="finite number"):
        validate(json.dumps(raw).encode())


def test_saved_snapshot_passes_validation():
    validate(TARGETS[0].read_bytes())


def test_failed_replacement_preserves_the_old_file(tmp_path, monkeypatch):
    from week04 import refresh_data

    target = tmp_path / "snapshot.json"
    target.write_bytes(b"old snapshot")

    def refuse_replace(*args):
        raise OSError("replacement failed")

    monkeypatch.setattr(refresh_data.os, "replace", refuse_replace)
    with pytest.raises(OSError, match="replacement failed"):
        refresh_data.save_atomically(target, b"new snapshot")
    assert target.read_bytes() == b"old snapshot"
    assert list(tmp_path.iterdir()) == [target]
