"""Tests for the KIS Vietnam price source (``KISVietnamSource``).

Synthetic payloads only — no real broker rows. The KIS feed is a BARE TradingView-UDF
object (top-level t/o/h/l/c/v/s) in RAW VND (PRICE_SCALE = 1.0).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.exceptions import EmptyData, UnsupportedInterval
from vnfin.models import AdjustmentPolicy, Interval
from vnfin.sources.kis import KISVietnamSource

WIDE = (date(2024, 1, 1), date(2024, 1, 31))


def _ts(d: str) -> int:
    return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


# Raw-VND rows (date, open, high, low, close, volume) — mirrors KIS's clean-integer recent feed.
_RAW_ROWS = [
    ("2024-01-02", 72_000.0, 72_500.0, 71_800.0, 72_300.0, 1_000_000),
    ("2024-01-03", 72_300.0, 73_000.0, 72_100.0, 72_800.0, 1_200_000),
    ("2024-01-04", 72_800.0, 73_200.0, 72_500.0, 73_000.0, 900_000),
]


def kis_bare(rows=None, status="ok") -> str:
    """Hand-crafted BARE UDF payload matching the KIS response shape."""
    rows = _RAW_ROWS if rows is None else rows
    return json.dumps(
        {
            "t": [_ts(r[0]) for r in rows],
            "o": [r[1] for r in rows],
            "h": [r[2] for r in rows],
            "l": [r[3] for r in rows],
            "c": [r[4] for r in rows],
            "v": [r[5] for r in rows],
            "s": status,
            "nextTime": None,
        }
    )


def src_with(text):
    return KISVietnamSource(http_get=lambda url, params, headers: text)


# --- configuration / contract ---


def test_name_and_adjustment_policy():
    s = KISVietnamSource()
    assert s.name == "kis"
    # KIS mixes adjusted history with raw recent bars -> conservatively MIXED.
    assert s.ADJUSTMENT_POLICY is AdjustmentPolicy.MIXED


def test_daily_supported_and_resolution_token():
    s = KISVietnamSource()
    assert s.supports(Interval.D1)
    assert s.RESOLUTION_MAP[Interval.D1] == "1D"


def test_intraday_resolutions_supported_and_tokens():
    s = KISVietnamSource()
    expected = {
        Interval.H1: "60",
        Interval.M30: "30",
        Interval.M15: "15",
        Interval.M5: "5",
        Interval.M1: "1",
    }
    for interval, token in expected.items():
        assert s.supports(interval), interval
        assert s.RESOLUTION_MAP[interval] == token


def test_build_params_uses_live_param_names():
    s = KISVietnamSource()
    params = s._build_params("FPT", "1D", 1_700_000_000, 1_701_000_000)
    assert params == {
        "symbol": "FPT",
        "resolution": "1D",
        "from": 1_700_000_000,
        "to": 1_701_000_000,
    }


# --- parse / scale / tz / range ---


def test_parses_bare_udf():
    h = src_with(kis_bare()).get_history("fpt", Interval.D1, *WIDE)
    assert len(h) == 3
    assert h.source == "kis"
    assert h.currency == "VND"
    assert h.provider_symbol == "FPT"  # normalized uppercase
    assert h.adjustment_policy is AdjustmentPolicy.MIXED


def test_price_is_raw_vnd_no_scaling():
    # PRICE_SCALE = 1.0 — feed is already raw VND, value must pass through unchanged.
    h = src_with(kis_bare()).get_history("FPT", Interval.D1, *WIDE)
    assert h.bars[0].close == pytest.approx(72_300.0)
    assert h.bars[0].open == pytest.approx(72_000.0)
    assert h.bars[0].volume == 1_000_000


def test_timezone_is_vietnam():
    h = src_with(kis_bare()).get_history("FPT", Interval.D1, *WIDE)
    bar = h.bars[0]
    assert bar.time.utcoffset() == timedelta(hours=7)
    assert bar.time.date() == date(2024, 1, 2)


def test_range_filter_and_sort():
    h = src_with(kis_bare()).get_history("FPT", Interval.D1, date(2024, 1, 3), date(2024, 1, 3))
    assert len(h) == 1
    assert h.bars[0].time.date() == date(2024, 1, 3)


# --- empty / status ---


def test_status_no_data_raises_empty():
    with pytest.raises(EmptyData):
        src_with(kis_bare(status="no_data")).get_history("FPT", Interval.D1, *WIDE)


def test_empty_arrays_raise_empty():
    # KIS returns s:"ok" with empty arrays for an unknown symbol.
    with pytest.raises(EmptyData):
        src_with(kis_bare(rows=[])).get_history("FPT", Interval.D1, *WIDE)


# --- capability gating ---


def test_unsupported_interval_weekly_raises():
    # W1 (weekly) was NOT included in SUPPORTED.
    with pytest.raises(UnsupportedInterval):
        src_with(kis_bare()).get_history("FPT", Interval.W1, *WIDE)
