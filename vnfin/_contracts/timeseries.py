"""Composable time-series row/key validators (#refactor Phase 3).

Behavior-preserving extractions for the per-row and ordering checks shared by the
domain result validators. Like :mod:`vnfin._contracts.results`, reason strings are
parameterized (entity ``noun``, ``key`` accessor, ``msg``) to stay byte-exact.

**Ordering contract:** ``row_object_and_plain_date_reason`` checks the row-object
and date conditions for the *same row in one pass* — preserving the original
first-failing-condition order. Do NOT decompose it into two separate all-rows
passes: that would change which reason wins for a multi-malformed input.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Callable, Optional, Sequence


def row_object_and_plain_date_reason(
    rows: Sequence,
    expected_type,
    *,
    key: Callable,
    noun: str,
) -> Optional[str]:
    """Per row, reject a non-``expected_type`` object then a non-plain-``date`` key.

    Plain ``datetime.date`` only — ``datetime`` is rejected explicitly (it
    subclasses ``date`` but carries intraday/tz meaning). Single pass so the
    first-failing condition (object before date, row by row) is preserved.

    Reasons: ``f"malformed {noun} object {type(row).__name__}"`` and
    ``f"malformed {noun} date {d!r}: expected a plain datetime.date"``.
    """
    for row in rows:
        if not isinstance(row, expected_type):
            return f"malformed {noun} object {type(row).__name__}"
        d = key(row)
        if not isinstance(d, date) or isinstance(d, datetime):
            return f"malformed {noun} date {d!r}: expected a plain datetime.date"
    return None


def row_object_and_aware_datetime_reason(
    rows: Sequence,
    expected_type,
    *,
    key: Callable,
    noun: str,
    key_name: str = "time",
) -> Optional[str]:
    """Per row, reject a non-``expected_type`` object then a non-tz-aware key.

    The key must be a timezone-AWARE ``datetime`` (``utcoffset() is not None``) —
    the documented intraday-bar ``.time`` contract; a naive datetime or non-datetime
    key is rejected. Single pass so object-before-key, row-by-row order is preserved.

    Reasons: ``f"malformed {noun} object {type(row).__name__}"`` and
    ``f"malformed {noun} {key_name} {t!r}: expected a timezone-aware datetime"``.
    """
    for row in rows:
        if not isinstance(row, expected_type):
            return f"malformed {noun} object {type(row).__name__}"
        t = key(row)
        if not isinstance(t, datetime) or t.utcoffset() is None:
            return f"malformed {noun} {key_name} {t!r}: expected a timezone-aware datetime"
    return None


def strictly_ascending_reason(
    rows: Sequence, *, key: Callable, msg: str
) -> Optional[str]:
    """Reject rows not strictly ascending by ``key`` with the caller's ``msg``."""
    for i in range(len(rows) - 1):
        if not (key(rows[i]) < key(rows[i + 1])):
            return msg
    return None
