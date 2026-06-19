"""Phase 3 contract primitives — time-series row/key rules (#refactor)."""
from __future__ import annotations

from datetime import date, datetime

from vnfin._contracts import row_object_and_plain_date_reason, strictly_ascending_reason


class _Bar:
    def __init__(self, d):
        self.date = d


def _key(b):
    return b.date


def test_row_object_and_plain_date_accepts_clean():
    rows = [_Bar(date(2025, 1, 1)), _Bar(date(2025, 1, 2))]
    assert row_object_and_plain_date_reason(rows, _Bar, key=_key, noun="bar") is None


def test_row_object_reason_first():
    rows = ["not a bar"]
    assert row_object_and_plain_date_reason(rows, _Bar, key=_key, noun="bar") == (
        "malformed bar object str"
    )


def test_plain_date_reason_rejects_datetime_and_nondate():
    # datetime subclasses date but is rejected explicitly.
    rows = [_Bar(datetime(2025, 1, 1, 12, 0))]
    msg = row_object_and_plain_date_reason(rows, _Bar, key=_key, noun="bar")
    assert msg.startswith("malformed bar date") and "plain datetime.date" in msg
    rows2 = [_Bar("2025-01-01")]
    assert "malformed bar date" in row_object_and_plain_date_reason(rows2, _Bar, key=_key, noun="bar")


def test_ordering_preserved_object_before_date_per_row():
    # First row has a bad DATE; second row is a bad OBJECT. Per-row order means the
    # bad-date of row 0 wins (NOT row 1's bad object) — proves single-pass ordering.
    rows = [_Bar(datetime(2025, 1, 1)), "bad object"]
    assert "malformed bar date" in row_object_and_plain_date_reason(rows, _Bar, key=_key, noun="bar")


def test_strictly_ascending_reason():
    asc = [_Bar(date(2025, 1, 1)), _Bar(date(2025, 1, 2))]
    assert strictly_ascending_reason(asc, key=_key, msg="not ascending") is None
    dup = [_Bar(date(2025, 1, 1)), _Bar(date(2025, 1, 1))]
    assert strictly_ascending_reason(dup, key=_key, msg="not ascending") == "not ascending"
    desc = [_Bar(date(2025, 1, 2)), _Bar(date(2025, 1, 1))]
    assert strictly_ascending_reason(desc, key=_key, msg="not ascending") == "not ascending"
