"""Tests for the SSI iBoard adapter (`vnfin.sources.ssi.SSIiBoardSource`).

All payloads are HAND-CRAFTED SYNTHETIC JSON shaped like the SSI envelope:
``{"code":"SUCCESS","data":{t,o,h,l,c,v,s,nextTime},"status":"ok"}`` with the
UDF status field ``s`` living *inside* ``data``. No real broker rows are used.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable, UnsupportedInterval
from vnfin.models import AdjustmentPolicy, Interval
from vnfin.sources.ssi import SSIiBoardSource

WIDE = (date(2024, 1, 1), date(2024, 1, 31))

# (date, open, high, low, close, volume) — prices in THOUSANDS of VND (feed convention)
_ROWS = [
    ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1_000_000),
    ("2024-01-03", 72.3, 73.0, 72.1, 72.8, 1_200_000),
    ("2024-01-04", 72.8, 73.2, 72.5, 73.0, 900_000),
]


def _ts(d: str) -> int:
    return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _envelope(rows=None, status="ok", outer_code="SUCCESS", outer_status="ok") -> str:
    """Synthetic SSI envelope. Status `s` lives inside `data`."""
    rows = _ROWS if rows is None else rows
    data = {
        "t": [_ts(r[0]) for r in rows],
        "o": [r[1] for r in rows],
        "h": [r[2] for r in rows],
        "l": [r[3] for r in rows],
        "c": [r[4] for r in rows],
        "v": [r[5] for r in rows],
        "s": status,
        "nextTime": None,
    }
    return json.dumps(
        {"code": outer_code, "message": "ok", "data": data, "status": outer_status}
    )


def _src(text: str) -> SSIiBoardSource:
    return SSIiBoardSource(http_get=lambda url, params, headers: text)


def test_parses_ssi_envelope():
    s = _src(_envelope())
    h = s.get_history("fpt", Interval.D1, *WIDE)
    assert len(h) == 3
    assert h.source == "ssi"
    assert h.provider_symbol == "FPT"  # normalized uppercase
    assert h.currency == "VND"
    assert h.adjustment_policy is AdjustmentPolicy.PROVIDER_ADJUSTED


def test_price_scaling_to_vnd():
    h = _src(_envelope()).get_history("FPT", Interval.D1, *WIDE)
    # feed close 72.3 (thousands) -> 72,300 VND ; open 72.0 -> 72,000 VND
    assert h.bars[0].close == pytest.approx(72_300.0)
    assert h.bars[0].open == pytest.approx(72_000.0)


def test_timezone_is_vietnam():
    h = _src(_envelope()).get_history("FPT", Interval.D1, *WIDE)
    bar = h.bars[0]
    assert bar.time.utcoffset() == timedelta(hours=7)
    assert bar.time.date() == date(2024, 1, 2)


def test_range_filter():
    h = _src(_envelope()).get_history("FPT", Interval.D1, date(2024, 1, 3), date(2024, 1, 3))
    assert len(h) == 1
    assert h.bars[0].time.date() == date(2024, 1, 3)


def test_status_no_data_raises_empty():
    with pytest.raises(EmptyData):
        _src(_envelope(status="no_data")).get_history("FPT", Interval.D1, *WIDE)


def test_outer_code_failure_raises_unavailable():
    # Issue #40: outer envelope `code` must be SUCCESS before unwrapping `data`.
    with pytest.raises(SourceUnavailable):
        _src(_envelope(outer_code="FAIL")).get_history("FPT", Interval.D1, *WIDE)


def test_outer_status_not_ok_raises_source_unavailable():
    # Issue #40: outer envelope `status` must be "ok" before unwrapping `data`.
    # The provider uses status="error" for explicit failures, so it should be a
    # failover-triggering SourceUnavailable rather than silent success.
    with pytest.raises(SourceUnavailable):
        _src(_envelope(outer_status="error")).get_history("FPT", Interval.D1, *WIDE)


def test_outer_status_missing_raises_invalid():
    with pytest.raises(InvalidData):
        _src(_envelope(outer_status=None)).get_history("FPT", Interval.D1, *WIDE)


def test_outer_code_missing_raises_invalid():
    with pytest.raises(InvalidData):
        _src(_envelope(outer_code=None)).get_history("FPT", Interval.D1, *WIDE)


def test_envelope_top_level_not_dict_raises_invalid():
    with pytest.raises(InvalidData):
        _src("[1, 2, 3]").get_history("FPT", Interval.D1, *WIDE)


def test_empty_arrays_raise_empty():
    # SSI returns s="ok" with empty arrays for unknown symbols.
    with pytest.raises(EmptyData):
        _src(_envelope(rows=[])).get_history("FPT", Interval.D1, *WIDE)


def test_intraday_h1_supported():
    assert SSIiBoardSource().supports(Interval.H1)
    h = _src(_envelope()).get_history("FPT", Interval.H1, *WIDE)
    assert len(h) == 3


def test_unsupported_interval_raises():
    # W1 is intentionally NOT in SUPPORTED for the MVP.
    assert not SSIiBoardSource().supports(Interval.W1)
    with pytest.raises(UnsupportedInterval):
        _src(_envelope()).get_history("FPT", Interval.W1, *WIDE)


def test_resolution_tokens():
    s = SSIiBoardSource()
    assert s.RESOLUTION_MAP[Interval.D1] == "1D"
    assert s.RESOLUTION_MAP[Interval.H1] == "60"
    assert s.RESOLUTION_MAP[Interval.M30] == "30"
    assert s.RESOLUTION_MAP[Interval.M15] == "15"
    assert s.RESOLUTION_MAP[Interval.M5] == "5"
    assert s.RESOLUTION_MAP[Interval.M1] == "1"


def test_build_params_keys():
    s = SSIiBoardSource()
    params = s._build_params("FPT", "1D", 100, 200)
    assert params == {"resolution": "1D", "symbol": "FPT", "from": 100, "to": 200}


def test_bool_ohlc_quarantined_not_served_as_price():
    # Issue #87: JSON booleans must NEVER become scaled VND prices via float(True).
    # Under #186 a bool scalar fails parse → the row is quarantined (dropped), so the
    # bool is never served; the clean bar alongside it is kept and a warning is emitted.
    rows = [
        ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1_000_000),
        ("2024-01-03", True, True, True, True, True),
    ]
    h = _src(_envelope(rows=rows)).get_history("FPT", Interval.D1, *WIDE)
    assert [b.time.date() for b in h] == [date(2024, 1, 2)]  # bool row dropped, not served
    assert any("quarantined_invalid_bars" in w for w in h.warnings)


def test_bool_ohlc_all_bad_yields_emptydata():
    # A lone bool-only row leaves zero clean bars → EmptyData (a SourceError → failover),
    # so the bool is still never served as a price.
    rows = [("2024-01-02", True, True, True, True, True)]
    with pytest.raises(EmptyData):
        _src(_envelope(rows=rows)).get_history("FPT", Interval.D1, *WIDE)


def test_bool_timestamp_quarantined_not_served():
    rows = [
        ("2024-01-02", 72.0, 72.5, 71.8, 72.3, 1_000_000),
        ("2024-01-03", 72.3, 73.0, 72.1, 72.8, 1_200_000),
    ]
    payload = json.loads(_envelope(rows=rows))
    payload["data"]["t"][1] = True  # corrupt the 2nd row's timestamp to a JSON bool
    h = _src(json.dumps(payload)).get_history("FPT", Interval.D1, *WIDE)
    assert [b.time.date() for b in h] == [date(2024, 1, 2)]  # bool-ts row dropped
    assert any("quarantined_invalid_bars" in w for w in h.warnings)
