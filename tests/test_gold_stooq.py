"""Tests for Stooq world-gold CSV backup — synthetic fixtures only.

No real provider rows; CSV bodies are hand-crafted to match the Stooq
``xauusd`` daily shape but use obviously-fabricated prices/dates.
"""
from __future__ import annotations

from datetime import date

import pytest

from vnfin.exceptions import InvalidData
from vnfin.gold import GoldBar, GoldHistory, StooqGoldSource


def _csv(*rows: tuple[str, str, str, str, str, str]) -> str:
    lines = ["Date,Open,High,Low,Close,Volume"]
    for r in rows:
        lines.append(",".join(r))
    return "\n".join(lines) + "\n"


def _src(csv_text: str) -> StooqGoldSource:
    return StooqGoldSource(http_get=lambda url, params=None, headers=None: csv_text)


def _valid_row(d: str = "2026-06-15") -> tuple[str, str, str, str, str, str]:
    return (d, "3200", "3500", "3000", "3300", "0")


# --------------------------------------------------------------------------- #
# Normal parse
# --------------------------------------------------------------------------- #

def test_parses_valid_csv_into_gold_history():
    csv = _csv(_valid_row())
    hist = _src(csv).get_history(date(2026, 6, 15), date(2026, 6, 15))
    assert isinstance(hist, GoldHistory)
    assert len(hist.bars) == 1
    assert hist.bars[0] == GoldBar(date=date(2026, 6, 15), price=pytest.approx(3300.0))


# --------------------------------------------------------------------------- #
# Issue #53: malformed OHLC rows must be rejected
# --------------------------------------------------------------------------- #

def test_close_above_high_raises_invalid():
    csv = _csv(("2026-06-15", "3200", "3500", "3000", "4100", "0"))
    with pytest.raises(InvalidData):
        _src(csv).get_history(date(2026, 6, 15), date(2026, 6, 15))


def test_close_below_low_raises_invalid():
    csv = _csv(("2026-06-15", "3200", "3500", "3000", "2500", "0"))
    with pytest.raises(InvalidData):
        _src(csv).get_history(date(2026, 6, 15), date(2026, 6, 15))


def test_non_numeric_high_raises_invalid():
    csv = _csv(("2026-06-15", "3200", "not-a-number", "3000", "3300", "0"))
    with pytest.raises(InvalidData):
        _src(csv).get_history(date(2026, 6, 15), date(2026, 6, 15))


def test_negative_low_raises_invalid():
    csv = _csv(("2026-06-15", "3200", "3500", "-1", "3300", "0"))
    with pytest.raises(InvalidData):
        _src(csv).get_history(date(2026, 6, 15), date(2026, 6, 15))


def test_open_above_high_raises_invalid():
    csv = _csv(("2026-06-15", "3600", "3500", "3000", "3300", "0"))
    with pytest.raises(InvalidData):
        _src(csv).get_history(date(2026, 6, 15), date(2026, 6, 15))


def test_high_below_low_raises_invalid():
    csv = _csv(("2026-06-15", "3200", "2900", "3000", "2950", "0"))
    with pytest.raises(InvalidData):
        _src(csv).get_history(date(2026, 6, 15), date(2026, 6, 15))
