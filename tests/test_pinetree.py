"""Tests for the Pinetree UDF adapter.

All payloads here are HAND-CRAFTED SYNTHETIC JSON — no real broker rows. Pinetree
serves a BARE UDF object (top-level t/o/h/l/c/v/s, no envelope) in RAW VND
(PRICE_SCALE = 1.0), so the synthetic closes are written in whole VND and the
adapter must pass them through unscaled.
"""
import json
from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.exceptions import EmptyData, UnsupportedInterval
from vnfin.models import AdjustmentPolicy, Interval
from vnfin.sources.pinetree import PinetreeSource

WIDE = (date(2024, 1, 1), date(2024, 1, 31))

# (date, open, high, low, close, volume) — RAW VND (Pinetree convention)
_ROWS = [
    ("2024-01-02", 72_000.0, 72_500.0, 71_800.0, 72_300.0, 5_000_000),
    ("2024-01-03", 72_300.0, 73_000.0, 72_100.0, 72_800.0, 6_000_000),
    ("2024-01-04", 72_800.0, 73_200.0, 72_500.0, 73_000.0, 4_500_000),
]


def _ts(d: str) -> int:
    return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def bare(rows=None, status="ok") -> str:
    """Synthetic BARE UDF payload matching Pinetree's observed shape."""
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
            "nextTime": -1,
        }
    )


def src_with(text):
    return PinetreeSource(http_get=lambda url, params, headers: text)


def test_parses_bare_udf():
    h = src_with(bare()).get_history("fpt", Interval.D1, *WIDE)
    assert len(h) == 3
    assert h.source == "pinetree"
    assert h.provider_symbol == "FPT"  # normalized uppercase
    assert h.currency == "VND"
    assert h.adjustment_policy is AdjustmentPolicy.PROVIDER_ADJUSTED


def test_price_scale_is_raw_vnd():
    # PRICE_SCALE = 1.0 -> raw VND passes through unchanged
    h = src_with(bare()).get_history("FPT", Interval.D1, *WIDE)
    assert h.bars[0].close == pytest.approx(72_300.0)
    assert h.bars[0].open == pytest.approx(72_000.0)
    assert h.bars[0].high == pytest.approx(72_500.0)


def test_timezone_is_vietnam():
    bar = src_with(bare()).get_history("FPT", Interval.D1, *WIDE).bars[0]
    assert bar.time.utcoffset() == timedelta(hours=7)
    assert bar.time.date() == date(2024, 1, 2)


def test_range_filter():
    h = src_with(bare()).get_history("FPT", Interval.D1, date(2024, 1, 3), date(2024, 1, 3))
    assert len(h) == 1
    assert h.bars[0].time.date() == date(2024, 1, 3)


def test_build_params_keys_and_resolution():
    captured = {}

    def grab(url, params, headers):
        captured["url"] = url
        captured["params"] = params
        return bare()

    PinetreeSource(http_get=grab).get_history("FPT", Interval.D1, *WIDE)
    assert captured["url"] == "https://charts.pinetree.vn/tv/history"
    assert set(captured["params"]) == {"symbol", "resolution", "from", "to"}
    assert captured["params"]["symbol"] == "FPT"
    assert captured["params"]["resolution"] == "1D"
    assert isinstance(captured["params"]["from"], int)
    assert isinstance(captured["params"]["to"], int)


def test_intraday_h1_token():
    captured = {}

    def grab(url, params, headers):
        captured["params"] = params
        return bare()

    PinetreeSource(http_get=grab).get_history("FPT", Interval.H1, *WIDE)
    assert captured["params"]["resolution"] == "60"


def test_status_no_data_raises_empty():
    with pytest.raises(EmptyData):
        src_with(bare(status="no_data")).get_history("FPT", Interval.D1, *WIDE)


def test_unsupported_interval_weekly_raises():
    # W1 is intentionally NOT mapped for Pinetree.
    with pytest.raises(UnsupportedInterval):
        src_with(bare()).get_history("FPT", Interval.W1, *WIDE)


def test_supported_set():
    s = PinetreeSource()
    for iv in (Interval.D1, Interval.M1, Interval.M5, Interval.M15, Interval.M30, Interval.H1):
        assert s.supports(iv)
    assert not s.supports(Interval.W1)
    assert not s.supports(Interval.MN1)
