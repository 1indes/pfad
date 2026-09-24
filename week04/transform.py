"""Small, deterministic transformations for the week 4 interface example."""


def parse_rows(rows):
    """Convert HKO rows [MM, DD, 01, ..., 24] into typed records."""
    records = []
    for row in rows:
        if len(row) != 26:
            raise ValueError(f"expected 26 fields, got {len(row)}")
        month, day = int(row[0]), int(row[1])
        heights = [float(value) for value in row[2:]]
        records.append({"month": month, "day": day, "heights": heights})
    return records


def select_month(rows, month):
    """Keep records for one month, preserving their original order."""
    if not 1 <= month <= 12:
        raise ValueError("month must be from 1 to 12")
    return [row for row in rows if row["month"] == month]


def select_day(rows, day):
    """Return one daily record, or None when that day is absent."""
    return next((row for row in rows if row["day"] == day), None)
