"""Tests for the VNDirect UDF adapter.

SYNTHETIC PAYLOADS ONLY — no real broker price rows are committed. Fixtures are
hand-crafted bare-UDF JSON matching the live response shape verified at
docs/sources/vndirect.md (bare {t,o,h,l,c,v,s}, prices in thousands of VND).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.exceptions import EmptyData, UnsupportedInterval
from vnfin.models import AdjustmentPolicy, Interval
from vnfin.sources.vndirect import VNDirectSource

WIDE = (date(2024, 1, 1), date(2024, 1, 31))

# (date, open, high, low, close, volume) — prices in THOUSANDS of VND (feed convention).
_ROWS = [
    ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1_714_500),
    ("2024-01-03", 72.3, 73.0, 72.1, 72.8, 1_436_900),
    ("2024-01-04", 72.8, 73.2, 72.5, 73.0, 2_973_900),
]


def _ts(d: str) -> int:
    return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _bare(rows=None, status="ok") -> str:
    """Hand-crafted bare UDF payload matching the live VNDirect shape."""
    rows = _ROWS if rows is None else rows
    return json.dumps(
        {
            "t": [_ts(r[0]) for r in rows],
            "o": [r[1] for r in rows],
            "h": [r[2] for r in rows],
            "l": [r[3] for r in rows],
            "c": [r[4] for r in rows],
            "v": [r[5] for r in rows],
            "s": status,
        }
    )


def _src(text):
    return VNDirectSource(http_get=lambda url, params, headers: text)


# --- configuration / identity ---

def test_source_identity_and_config():
    s = VNDirectSource()
    assert s.name == "vndirect"
    assert s.BASE_URL == "https://dchart-api.vndirect.com.vn"
    assert s.HISTORY_PATH == "/dchart/history"
    assert s.PRICE_SCALE == 1000.0
    assert s.ADJUSTMENT_POLICY is AdjustmentPolicy.PROVIDER_ADJUSTED


def test_build_params_keys_and_resolution():
    s = VNDirectSource()
    params = s._build_params("FPT", "D", 1704128400, 1705338000)
    assert params == {
        "symbol": "FPT",
        "resolution": "D",
        "from": 1704128400,
        "to": 1705338000,
    }
    # daily token is "D"
    assert s.RESOLUTION_MAP[Interval.D1] == "D"


# --- parse (bare UDF) ---

def test_parses_bare_udf():
    h = _src(_bare()).get_history("fpt", Interval.D1, *WIDE)
    assert len(h) == 3
    assert h.source == "vndirect"
    assert h.provider_symbol == "FPT"  # normalized uppercase
    assert h.currency == "VND"
    assert h.adjustment_policy is AdjustmentPolicy.PROVIDER_ADJUSTED


# --- price scaling to VND ---

def test_price_scaling_to_vnd():
    h = _src(_bare()).get_history("FPT", Interval.D1, *WIDE)
    # feed close 72.3 (thousands) -> 72,300 VND; open 72.0 -> 72,000 VND
    assert h.bars[0].close == pytest.approx(72_300.0)
    assert h.bars[0].open == pytest.approx(72_000.0)
    assert h.bars[0].high == pytest.approx(72_500.0)
    assert h.bars[0].low == pytest.approx(71_800.0)


# --- Vietnam timezone ---

def test_timezone_is_vietnam():
    h = _src(_bare()).get_history("FPT", Interval.D1, *WIDE)
    bar = h.bars[0]
    assert bar.time.utcoffset() == timedelta(hours=7)
    assert bar.time.date() == date(2024, 1, 2)


# --- range filter ---

def test_range_filter_narrows_to_single_day():
    h = _src(_bare()).get_history("FPT", Interval.D1, date(2024, 1, 3), date(2024, 1, 3))
    assert len(h) == 1
    assert h.bars[0].time.date() == date(2024, 1, 3)


# --- status no_data -> EmptyData ---

def test_status_no_data_raises_empty():
    with pytest.raises(EmptyData):
        _src(_bare(status="no_data")).get_history("FPT", Interval.D1, *WIDE)


# --- intraday capability ---

def test_intraday_resolutions_supported_and_mapped():
    s = VNDirectSource()
    expected = {
        Interval.M1: "1",
        Interval.M5: "5",
        Interval.M15: "15",
        Interval.M30: "30",
        Interval.H1: "60",
        Interval.D1: "D",
    }
    for interval, token in expected.items():
        assert s.supports(interval), f"{interval} should be supported"
        assert s.RESOLUTION_MAP[interval] == token


def test_intraday_hourly_parses():
    # Intraday hourly bars carry DISTINCT timestamps (07:00 then 08:00); a synthetic
    # same-timestamp fixture would now be rejected as a duplicate key (#66).
    base = int(datetime(2024, 1, 2, 0, 0, tzinfo=timezone.utc).timestamp())
    payload = json.dumps(
        {
            "t": [base, base + 3600],
            "o": [72.0, 72.3], "h": [72.5, 73.0], "l": [71.8, 72.1],
            "c": [72.3, 72.8], "v": [778_600, 841_200], "s": "ok",
        }
    )
    s = VNDirectSource(http_get=lambda url, params, headers: payload)
    h = s.get_history("FPT", Interval.H1, *WIDE)
    assert len(h) == 2
    assert h.interval is Interval.H1
    assert h.bars[0].close == pytest.approx(72_300.0)


# --- unsupported interval (not included) ---

def test_weekly_unsupported_raises():
    # W1 is intentionally NOT in SUPPORTED for this MVP.
    with pytest.raises(UnsupportedInterval):
        _src(_bare()).get_history("FPT", Interval.W1, *WIDE)


def test_monthly_unsupported_raises():
    with pytest.raises(UnsupportedInterval):
        _src(_bare()).get_history("FPT", Interval.MN1, *WIDE)
