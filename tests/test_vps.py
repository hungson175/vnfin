"""Tests for the VPS UDF adapter.

Synthetic payloads only — no real broker rows. The fixtures mirror the live
*shape* of the bare-UDF feed (top-level `symbol` + `s`/`t`/`o`/`h`/`l`/`c`/`v`
arrays) and a deliberately scaled-down price magnitude (thousands of VND).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.exceptions import EmptyData, UnsupportedInterval
from vnfin.models import AdjustmentPolicy, Interval
from vnfin.sources.vps import VPSSource

WIDE = (date(2024, 1, 1), date(2024, 1, 31))

# (date, open, high, low, close, volume) — prices in THOUSANDS of VND, matching the feed.
_ROWS = [
    ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1_000_000),
    ("2024-01-03", 72.3, 73.0, 72.1, 72.8, 1_200_000),
    ("2024-01-04", 72.8, 73.2, 72.5, 73.0, 900_000),
]


def _ts(d: str) -> int:
    return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _bare(rows=None, status="ok") -> str:
    """Synthetic bare-UDF payload shaped like the live VPS response."""
    rows = _ROWS if rows is None else rows
    return json.dumps(
        {
            "symbol": "FPT",
            "s": status,
            "t": [_ts(r[0]) for r in rows],
            "o": [r[1] for r in rows],
            "h": [r[2] for r in rows],
            "l": [r[3] for r in rows],
            "c": [r[4] for r in rows],
            "v": [r[5] for r in rows],
        }
    )


def _src(text):
    return VPSSource(http_get=lambda url, params, headers: text)


# --- configuration / wiring -------------------------------------------------

def test_identity_and_config():
    s = VPSSource()
    assert s.name == "vps"
    assert s.NAME == "vps"
    assert s.BASE_URL == "https://histdatafeed.vps.com.vn"
    assert s.HISTORY_PATH == "/tradingview/history"
    assert s.PRICE_SCALE == 1000.0
    assert s.ADJUSTMENT_POLICY is AdjustmentPolicy.PROVIDER_ADJUSTED
    assert s.EXCHANGE is None
    assert s.supports(Interval.D1)


def test_build_params_shape():
    s = VPSSource()
    params = s._build_params("FPT", "D", 100, 200)
    assert params == {"symbol": "FPT", "resolution": "D", "from": 100, "to": 200}


def test_daily_resolution_token():
    assert VPSSource.RESOLUTION_MAP[Interval.D1] == "D"


def test_intraday_resolution_tokens():
    # Intraday tokens verified live: 1/5/15/30/60.
    assert VPSSource.RESOLUTION_MAP[Interval.M1] == "1"
    assert VPSSource.RESOLUTION_MAP[Interval.M5] == "5"
    assert VPSSource.RESOLUTION_MAP[Interval.M15] == "15"
    assert VPSSource.RESOLUTION_MAP[Interval.M30] == "30"
    assert VPSSource.RESOLUTION_MAP[Interval.H1] == "60"


# --- parsing / scaling / tz -------------------------------------------------

def test_parses_bare_udf():
    h = _src(_bare()).get_history("fpt", Interval.D1, *WIDE)
    assert len(h) == 3
    assert h.source == "vps"
    assert h.provider_symbol == "FPT"  # normalized uppercase
    assert h.exchange is None
    assert h.currency == "VND"
    assert h.adjustment_policy is AdjustmentPolicy.PROVIDER_ADJUSTED


def test_price_scaling_to_vnd():
    h = _src(_bare()).get_history("FPT", Interval.D1, *WIDE)
    # feed close 72.3 (thousands) -> 72,300 VND
    assert h.bars[0].close == pytest.approx(72_300.0)
    assert h.bars[0].open == pytest.approx(72_000.0)
    assert h.bars[0].high == pytest.approx(72_500.0)
    assert h.bars[0].low == pytest.approx(71_800.0)


def test_timezone_is_vietnam():
    bar = _src(_bare()).get_history("FPT", Interval.D1, *WIDE).bars[0]
    assert bar.time.utcoffset() == timedelta(hours=7)
    assert bar.time.date() == date(2024, 1, 2)


# --- range filtering --------------------------------------------------------

def test_range_filtered_and_sorted():
    h = _src(_bare()).get_history("FPT", Interval.D1, date(2024, 1, 3), date(2024, 1, 3))
    assert len(h) == 1
    assert h.bars[0].time.date() == date(2024, 1, 3)


# --- empty / no_data --------------------------------------------------------

def test_status_no_data_raises_empty():
    with pytest.raises(EmptyData):
        _src(_bare(status="no_data")).get_history("FPT", Interval.D1, *WIDE)


def test_empty_arrays_raise_empty():
    with pytest.raises(EmptyData):
        _src(_bare(rows=[])).get_history("FPT", Interval.D1, *WIDE)


# --- unsupported interval ---------------------------------------------------

def test_unsupported_interval_raises():
    # W1 (weekly) is NOT in SUPPORTED for this adapter.
    assert not VPSSource().supports(Interval.W1)
    with pytest.raises(UnsupportedInterval):
        _src(_bare()).get_history("FPT", Interval.W1, *WIDE)
