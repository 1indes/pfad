"""Tests for the pure data rules. No network and no plotting library."""

import pytest

from week04.transform import parse_rows, select_day, select_month


def row(month, day, height="1.25"):
    return [f"{month:02}", f"{day:02}", *([height] * 24)]


def test_parse_rows_turns_hko_text_into_numbers():
    result = parse_rows([row(9, 17, "2.19")])

    assert result == [{"month": 9, "day": 17, "heights": [2.19] * 24}]


def test_select_month_keeps_only_the_requested_month():
    records = parse_rows([row(9, 17), row(10, 1)])

    assert select_month(records, 9) == [records[0]]


def test_select_month_can_return_no_rows():
    records = parse_rows([row(9, 17)])

    assert select_month(records, 10) == []


def test_select_day_returns_the_matching_record():
    records = parse_rows([row(9, 17), row(9, 18)])

    assert select_day(records, 17) == records[0]


def test_select_day_returns_none_when_absent():
    records = parse_rows([row(9, 17)])

    assert select_day(records, 18) is None


@pytest.mark.parametrize("month", [0, 13])
def test_select_month_rejects_an_invalid_month(month):
    with pytest.raises(ValueError, match="month must be from 1 to 12"):
        select_month([], month)


def test_parse_rows_rejects_a_row_with_the_wrong_shape():
    with pytest.raises(ValueError, match="expected 26 fields"):
        parse_rows([["09", "17", "2.19"]])
