"""Tests for #183 client-side D1 resampling (`vnfin._resample`) and the two
daily-native accessors that use it (`vnfin.prices.history` + `vnfin.indices.index_history`).

All fixtures are SYNTHETIC: most tests build a D1 :class:`PriceHistory` directly and call
the resample helpers; the two end-to-end tests inject a fake ``http_get`` returning a
synthetic UDF/SSI daily envelope (no real broker rows, no network).

Design contract: docs/design/prices-index-resample.md (LOCKED decisions). Key trap:
``M1`` is one MINUTE; monthly is ``MN1``. The pandas alias ``'M'`` MUST map to ``MN1``.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

import vnfin
from vnfin._resample import (
    PARTIAL_PERIOD_TOKEN,
    RESAMPLED_FROM_D1,
    apply_interval,
    resample_history,
    resolve_interval,
)
from vnfin.exceptions import InvalidData, UnsupportedInterval
from vnfin.models import AdjustmentPolicy, Interval, PriceBar, PriceHistory

_VN_TZ = timezone(timedelta(hours=7))


# --------------------------------------------------------------------------- #
# synthetic fixtures
# --------------------------------------------------------------------------- #
def _bar(d: str, o, h, l, c, v) -> PriceBar:
    t = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=_VN_TZ)
    return PriceBar(time=t, open=float(o), high=float(h), low=float(l), close=float(c), volume=int(v))


def _daily(bars, *, symbol="FAKECORP", value_unit="VND", currency="VND",
           source="ssi", warnings=()) -> PriceHistory:
    return PriceHistory(
        symbol=symbol,
        interval=Interval.D1,
        adjustment_policy=AdjustmentPolicy.PROVIDER_ADJUSTED,
        source=source,
        bars=tuple(bars),
        currency=currency,
        value_unit=value_unit,
        warnings=tuple(warnings),
    )


# A clean multi-month, multi-quarter, multi-year D1 series with known O/H/L/C/V so we
# can assert open=first, high=max, low=min, close=last, volume=sum per calendar period.
_MULTI = _daily([
    # Jan 2024
    _bar("2024-01-02", 10, 12, 9, 11, 100),
    _bar("2024-01-15", 11, 15, 10, 13, 200),
    _bar("2024-01-31", 13, 14, 8, 9, 300),   # Jan close=9, high(max)=15, low(min)=8, last day
    # Feb 2024
    _bar("2024-02-01", 9, 20, 9, 18, 400),
    _bar("2024-02-29", 18, 19, 16, 17, 500),  # Feb close=17, last day
    # Mar 2024
    _bar("2024-03-01", 17, 25, 15, 22, 600),
    _bar("2024-03-29", 22, 23, 21, 21, 700),  # Mar close=21 -> ends Q1
    # Apr 2024 (Q2)
    _bar("2024-04-01", 21, 30, 20, 28, 800),
    _bar("2024-04-30", 28, 31, 27, 30, 900),  # Apr close=30
    # Jan 2025 (next year)
    _bar("2025-01-02", 30, 40, 29, 35, 1000),
    _bar("2025-01-31", 35, 41, 34, 38, 1100),  # 2025 close=38
])


# --------------------------------------------------------------------------- #
# 1. OHLC aggregation correctness — MN1 / Q1 / Y1
# --------------------------------------------------------------------------- #
def test_mn1_ohlc_aggregation_and_last_trading_day():
    h = resample_history(_MULTI, Interval.MN1, date(2024, 1, 1), date(2025, 1, 31))
    assert h.interval is Interval.MN1
    # 5 calendar months present: 2024-01, 02, 03, 04 + 2025-01
    assert len(h.bars) == 5
    jan = h.bars[0]
    assert (jan.open, jan.high, jan.low, jan.close, jan.volume) == (10, 15, 8, 9, 600)
    assert jan.time.date() == date(2024, 1, 31)  # last ACTUAL trading day in Jan
    feb = h.bars[1]
    assert (feb.open, feb.high, feb.low, feb.close, feb.volume) == (9, 20, 9, 17, 900)
    assert feb.time.date() == date(2024, 2, 29)
    last = h.bars[-1]  # 2025-01
    assert (last.open, last.close) == (30, 38)
    assert last.time.date() == date(2025, 1, 31)


def test_q1_ohlc_aggregation():
    h = resample_history(_MULTI, Interval.Q1, date(2024, 1, 1), date(2025, 12, 31))
    assert h.interval is Interval.Q1
    # Q1-2024 (Jan-Mar), Q2-2024 (Apr), Q1-2025 (Jan) -> 3 groups
    assert len(h.bars) == 3
    q1 = h.bars[0]
    # Q1-2024: open=first(Jan-02)=10, high=max over Jan-Mar=25, low=min=8, close=last(Mar-29)=21
    assert (q1.open, q1.high, q1.low, q1.close) == (10, 25, 8, 21)
    assert q1.volume == 100 + 200 + 300 + 400 + 500 + 600 + 700
    assert q1.time.date() == date(2024, 3, 29)  # last trading day of Q1
    q2 = h.bars[1]
    assert (q2.open, q2.high, q2.low, q2.close) == (21, 31, 20, 30)
    assert q2.time.date() == date(2024, 4, 30)


def test_y1_ohlc_aggregation():
    h = resample_history(_MULTI, Interval.Y1, date(2024, 1, 1), date(2025, 12, 31))
    assert h.interval is Interval.Y1
    assert len(h.bars) == 2  # 2024 and 2025
    y2024 = h.bars[0]
    # open=first=10, high=max over all 2024=31, low=min=8, close=last 2024 bar (Apr-30)=30
    assert (y2024.open, y2024.high, y2024.low, y2024.close) == (10, 31, 8, 30)
    assert y2024.time.date() == date(2024, 4, 30)
    y2025 = h.bars[1]
    assert (y2025.open, y2025.close) == (30, 38)
    assert y2025.time.date() == date(2025, 1, 31)


# --------------------------------------------------------------------------- #
# 2. W1 grouping by ISO week across a boundary
# --------------------------------------------------------------------------- #
def test_w1_groups_by_iso_week():
    # 2024-01-05 = Fri (ISO week 1), 2024-01-08 = Mon (ISO week 2), 2024-01-12 = Fri (week 2)
    daily = _daily([
        _bar("2024-01-04", 10, 11, 9, 10, 100),  # Thu week 1
        _bar("2024-01-05", 10, 13, 10, 12, 100),  # Fri week 1
        _bar("2024-01-08", 12, 14, 11, 13, 100),  # Mon week 2
        _bar("2024-01-12", 13, 15, 12, 14, 100),  # Fri week 2
    ])
    h = resample_history(daily, Interval.W1, date(2024, 1, 1), date(2024, 1, 31))
    assert h.interval is Interval.W1
    assert len(h.bars) == 2
    wk1 = h.bars[0]
    assert (wk1.open, wk1.high, wk1.low, wk1.close) == (10, 13, 9, 12)
    assert wk1.time.date() == date(2024, 1, 5)
    wk2 = h.bars[1]
    assert (wk2.open, wk2.high, wk2.low, wk2.close) == (12, 15, 11, 14)
    assert wk2.time.date() == date(2024, 1, 12)


# --------------------------------------------------------------------------- #
# 3. pandas alias resolution — the 'M' -> MN1 (MONTH, not minute) trap
# --------------------------------------------------------------------------- #
def test_alias_M_maps_to_month_not_minute():
    assert resolve_interval("M") is Interval.MN1
    assert resolve_interval("M") is not Interval.M1  # explicit anti-minute guard


def test_alias_all_and_case_insensitive():
    assert resolve_interval("D") is Interval.D1
    assert resolve_interval("W") is Interval.W1
    assert resolve_interval("M") is Interval.MN1
    assert resolve_interval("Q") is Interval.Q1
    assert resolve_interval("Y") is Interval.Y1
    # case-insensitive + whitespace-stripped
    assert resolve_interval("m") is Interval.MN1
    assert resolve_interval("Y ") is Interval.Y1
    assert resolve_interval(" d ") is Interval.D1


def test_resolve_interval_passes_through_members():
    for iv in (Interval.D1, Interval.W1, Interval.MN1, Interval.Q1, Interval.Y1, Interval.M1):
        assert resolve_interval(iv) is iv


def test_resolve_interval_unknown_alias_raises():
    with pytest.raises(InvalidData):
        resolve_interval("X")
    with pytest.raises(InvalidData):
        resolve_interval("1d")  # raw provider token is NOT an accepted alias
    with pytest.raises(InvalidData):
        resolve_interval("")


# --------------------------------------------------------------------------- #
# 4. Index OHLC-for-both — units preserved, .close == period-end value
# --------------------------------------------------------------------------- #
def test_index_resample_preserves_points_and_close_is_period_end():
    idx = _daily([
        _bar("2024-01-02", 1000, 1010, 995, 1005, 0),
        _bar("2024-01-31", 1005, 1100, 1000, 1080, 0),  # period-end close=1080
        _bar("2024-02-29", 1080, 1090, 1050, 1060, 0),
    ], symbol="VNINDEX", value_unit="points", currency="points", source="vps_index")
    h = resample_history(idx, Interval.MN1, date(2024, 1, 1), date(2024, 2, 29))
    assert h.value_unit == "points"
    assert h.currency == "points"
    assert h.symbol == "VNINDEX"
    jan = h.bars[0]
    # full OHLC retained
    assert (jan.open, jan.high, jan.low, jan.close) == (1000, 1100, 995, 1080)
    # lossless: .close IS exactly the period-end (last-day) value a caller plots
    assert jan.close == 1080


# --------------------------------------------------------------------------- #
# 5. Intraday rejected on the daily-native path
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("iv", [Interval.M1, Interval.M5, Interval.M15, Interval.M30, Interval.H1])
def test_apply_interval_rejects_intraday(iv):
    def _should_not_fetch():
        raise AssertionError("fetch_d1 must NOT be called for an intraday request")

    with pytest.raises(UnsupportedInterval):
        apply_interval(iv, date(2024, 1, 1), date(2024, 6, 30), _should_not_fetch)


def test_prices_history_rejects_intraday():
    with pytest.raises(UnsupportedInterval):
        vnfin.prices.history("FAKECORP", Interval.M5, date(2024, 1, 1), date(2024, 6, 30))


def test_index_history_rejects_intraday():
    with pytest.raises(UnsupportedInterval):
        vnfin.indices.index_history("VNINDEX", date(2024, 1, 1), date(2024, 6, 30),
                                    interval=Interval.H1)


# --------------------------------------------------------------------------- #
# 6. D1 back-compat passthrough — unchanged, NO resampled_from_d1 warning
# --------------------------------------------------------------------------- #
def test_d1_passthrough_unchanged():
    daily = _daily([_bar("2024-01-02", 10, 12, 9, 11, 100)], warnings=("preexisting",))
    out = apply_interval(Interval.D1, date(2024, 1, 1), date(2024, 1, 31), lambda: daily)
    assert out is daily  # passthrough is the exact object the thunk returned
    assert RESAMPLED_FROM_D1 not in out.warnings
    assert out.interval is Interval.D1


def test_default_interval_is_daily_passthrough():
    # the default Interval.D1 path is the passthrough — resolve_interval(D1) -> D1
    assert resolve_interval(Interval.D1) is Interval.D1


# --------------------------------------------------------------------------- #
# 7. resampled_from_d1 present + interval == requested on every resampled result
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("iv", [Interval.W1, Interval.MN1, Interval.Q1, Interval.Y1])
def test_resampled_results_self_disclose(iv):
    h = resample_history(_MULTI, iv, date(2024, 1, 1), date(2025, 12, 31))
    assert h.interval is iv
    assert RESAMPLED_FROM_D1 in h.warnings


def test_apply_interval_resamples_for_coarse():
    h = apply_interval(Interval.MN1, date(2024, 1, 1), date(2025, 1, 31), lambda: _MULTI)
    assert h.interval is Interval.MN1
    assert RESAMPLED_FROM_D1 in h.warnings


# --------------------------------------------------------------------------- #
# 8. Partial-period warning — mid-period edge -> exactly one token, bars kept;
#    calendar-aligned window -> NO partial warning
# --------------------------------------------------------------------------- #
def test_partial_period_warning_on_mid_period_edges():
    # window starts mid-Jan and ends mid-2025 (mid-Jan) -> both edges partial
    h = resample_history(_MULTI, Interval.MN1, date(2024, 1, 10), date(2025, 1, 15))
    partials = [w for w in h.warnings if w.startswith(PARTIAL_PERIOD_TOKEN)]
    assert len(partials) == 1  # exactly ONE partial warning
    assert RESAMPLED_FROM_D1 in h.warnings
    # bars are KEPT, not dropped
    assert len(h.bars) == 5


def test_no_partial_warning_when_calendar_aligned():
    # window spans full calendar months exactly: Jan-1 .. last day present
    h = resample_history(_MULTI, Interval.Y1, date(2024, 1, 1), date(2025, 12, 31))
    partials = [w for w in h.warnings if w.startswith(PARTIAL_PERIOD_TOKEN)]
    assert partials == []
    assert RESAMPLED_FROM_D1 in h.warnings


# --------------------------------------------------------------------------- #
# 9. Both accessors end-to-end with injected synthetic daily rows
# --------------------------------------------------------------------------- #
def _ts(d: str) -> int:
    return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


_E2E_ROWS = [
    ("2024-01-02", 10.0, 12.0, 9.0, 11.0, 100),
    ("2024-01-31", 11.0, 15.0, 8.0, 9.0, 300),
    ("2024-02-29", 9.0, 20.0, 9.0, 17.0, 500),
    ("2024-03-29", 17.0, 25.0, 15.0, 21.0, 700),
]


def _ssi_envelope(rows):
    """Synthetic SSI iBoard envelope (status `s` inside `data`)."""
    data = {
        "t": [_ts(r[0]) for r in rows],
        "o": [r[1] for r in rows],
        "h": [r[2] for r in rows],
        "l": [r[3] for r in rows],
        "c": [r[4] for r in rows],
        "v": [r[5] for r in rows],
        "s": "ok",
        "nextTime": None,
    }
    return json.dumps({"code": "SUCCESS", "message": "ok", "data": data, "status": "ok"})


def _bare_udf(rows, symbol="VNINDEX"):
    """Synthetic bare-UDF envelope shaped like the VPS index feed."""
    return json.dumps({
        "symbol": symbol,
        "s": "ok",
        "t": [_ts(r[0]) for r in rows],
        "o": [r[1] for r in rows],
        "h": [r[2] for r in rows],
        "l": [r[3] for r in rows],
        "c": [r[4] for r in rows],
        "v": [r[5] for r in rows],
    })


def test_prices_history_end_to_end_resample_mn1():
    env = _ssi_envelope(_E2E_ROWS)
    fake = lambda url, params, headers: env  # noqa: E731
    h = vnfin.prices.history("FAKECORP", Interval.MN1, date(2024, 1, 1), date(2024, 3, 31),
                             http_get=fake)
    assert h.interval is Interval.MN1
    assert RESAMPLED_FROM_D1 in h.warnings
    assert len(h.bars) == 3  # Jan, Feb, Mar
    # SSI scales thousands-of-VND -> VND; just assert aggregation shape, last close present
    assert h.bars[0].time.date() == date(2024, 1, 31)


def test_index_history_end_to_end_resample_quarter_alias():
    env = _bare_udf(_E2E_ROWS, symbol="VNINDEX")
    fake = lambda url, params, headers: env  # noqa: E731
    h = vnfin.indices.index_history("VNINDEX", date(2024, 1, 1), date(2024, 3, 31),
                                    interval="Q", http_get=fake)
    assert h.interval is Interval.Q1
    assert h.value_unit == "points"
    assert RESAMPLED_FROM_D1 in h.warnings
    assert len(h.bars) == 1  # all rows fall in Q1-2024
    assert h.bars[0].time.date() == date(2024, 3, 29)


# --------------------------------------------------------------------------- #
# 10. Empty series -> no crash, interval set, resampled_from_d1, no partial
# --------------------------------------------------------------------------- #
def test_empty_series_resample_no_crash():
    empty = _daily([], warnings=("upstream",))
    h = resample_history(empty, Interval.MN1, date(2024, 1, 1), date(2024, 6, 30))
    assert h.bars == ()
    assert h.interval is Interval.MN1
    assert RESAMPLED_FROM_D1 in h.warnings
    assert "upstream" in h.warnings
    assert not any(w.startswith(PARTIAL_PERIOD_TOKEN) for w in h.warnings)


# --------------------------------------------------------------------------- #
# 11. Crypto/world untouched — Q1/Y1 cleanly unsupported, no KeyError
# --------------------------------------------------------------------------- #
def test_crypto_rejects_new_members_cleanly():
    from vnfin.crypto.binance import BinanceCryptoSource

    src = BinanceCryptoSource()
    assert src.supports(Interval.Q1) is False
    assert src.supports(Interval.Y1) is False
    with pytest.raises(UnsupportedInterval):
        src.get_klines("BTCUSDT", Interval.Q1, date(2024, 1, 1), date(2024, 6, 30))


def test_new_enum_members_exist_and_not_intraday():
    assert Interval.Q1.value == "1Q"
    assert Interval.Y1.value == "1Y"
    assert Interval.Q1.is_intraday is False
    assert Interval.Y1.is_intraday is False
    # the minute/month invariant
    assert Interval.M1.value == "1m"
    assert Interval.MN1.value == "1M"
