"""Tests for the Binance crypto klines adapter.

All payloads are SYNTHETIC, hand-crafted to match the live Binance
``GET /api/v3/klines`` shape (a JSON array-of-arrays with string scalars).
No real provider rows are committed.

Binance kline array index map (verified live, see docs/sources/crypto-binance.md):
    [0] openTime (epoch ms)
    [1] open     (string)
    [2] high     (string)
    [3] low      (string)
    [4] close    (string)
    [5] volume   (base asset, string)
    [6] closeTime (epoch ms)
    [7] quoteAssetVolume (string)
    [8] numberOfTrades (int)
    [9] takerBuyBaseVolume (string)
    [10] takerBuyQuoteVolume (string)
    [11] ignore
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.crypto import BinanceCryptoSource, CryptoBar, CryptoHistory
from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable, UnsupportedInterval
from vnfin.models import Interval

UTC = timezone.utc

# (openTime_ms, open, high, low, close, volume) — strings, USD via USDT
_ROWS = [
    (1781481600000, "65711.11", "67248.13", "65315.84", "66289.50", "20000.10000000"),
    (1781568000000, "66328.74", "66992.00", "65360.92", "65675.01", "14302.05801000"),
    (1781654400000, "65675.02", "66445.93", "64565.00", "65429.99", "13867.92621000"),
]


def _kline(row):
    open_ms, o, h, l, c, v = row
    close_ms = open_ms + 86_400_000 - 1
    return [open_ms, o, h, l, c, v, close_ms, "0", 100, "0", "0", "0"]


def _payload(rows=None):
    rows = _ROWS if rows is None else rows
    return json.dumps([_kline(r) for r in rows])


def src_with(text):
    return BinanceCryptoSource(http_get=lambda url, params, headers: text)


def _raising(exc):
    def _g(url, params, headers):
        raise exc

    return _g


# wide bounding range covering all synthetic rows
WIDE = (date(2026, 6, 1), date(2026, 6, 30))


# --- normal parse -----------------------------------------------------------


def test_parses_klines():
    h = src_with(_payload()).get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert isinstance(h, CryptoHistory)
    assert len(h) == 3
    assert all(isinstance(b, CryptoBar) for b in h.bars)
    assert h.symbol == "BTCUSDT"
    assert h.interval is Interval.D1
    assert h.source == "binance"
    assert h.currency == "USD"


def test_ohlcv_values_and_types():
    h = src_with(_payload()).get_klines("BTCUSDT", Interval.D1, *WIDE)
    b = h.bars[0]
    # strings parsed to float, no scaling (USDT ~ USD, 1:1)
    assert b.open == pytest.approx(65711.11)
    assert b.high == pytest.approx(67248.13)
    assert b.low == pytest.approx(65315.84)
    assert b.close == pytest.approx(66289.50)
    # base-asset volume is fractional -> kept as float, not int
    assert isinstance(b.volume, float)
    assert b.volume == pytest.approx(20000.10)


def test_time_is_tz_aware_utc():
    h = src_with(_payload()).get_klines("BTCUSDT", Interval.D1, *WIDE)
    b = h.bars[0]
    assert b.time.tzinfo is not None
    assert b.time.utcoffset() == timedelta(0)  # UTC
    assert b.time == datetime(2026, 6, 15, tzinfo=UTC)  # openTime 1781481600000


def test_attribution_and_fetched_at():
    h = src_with(_payload()).get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert h.source == "binance"
    assert h.provider_symbol == "BTCUSDT"
    assert h.fetched_at_utc is not None
    assert h.fetched_at_utc.tzinfo is not None


def test_symbol_normalized_uppercase():
    h = src_with(_payload()).get_klines("btcusdt", Interval.D1, *WIDE)
    assert h.symbol == "BTCUSDT"
    assert h.provider_symbol == "BTCUSDT"


def test_bars_sorted_and_range_filtered():
    # request only the middle day (synthetic rows are 2026-06-15/16/17)
    h = src_with(_payload()).get_klines(
        "BTCUSDT", Interval.D1, date(2026, 6, 16), date(2026, 6, 16)
    )
    assert len(h) == 1
    assert h.bars[0].time.date() == date(2026, 6, 16)


def test_to_dataframe_roundtrip():
    h = src_with(_payload()).get_klines("BTCUSDT", Interval.D1, *WIDE)
    df = h.to_dataframe()
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert len(df) == 3
    assert df.attrs["currency"] == "USD"
    assert df.attrs["source"] == "binance"


# --- interval mapping -------------------------------------------------------


def test_supports_intervals():
    s = BinanceCryptoSource()
    for iv in (Interval.M1, Interval.M5, Interval.M15, Interval.M30,
               Interval.H1, Interval.D1, Interval.W1, Interval.MN1):
        assert s.supports(iv)


def test_interval_token_mapping():
    captured = {}

    def cap(url, params, headers):
        captured.update(params)
        return _payload()

    BinanceCryptoSource(http_get=cap).get_klines("BTCUSDT", Interval.H1, *WIDE)
    assert captured["interval"] == "1h"

    BinanceCryptoSource(http_get=cap).get_klines("BTCUSDT", Interval.MN1, *WIDE)
    assert captured["interval"] == "1M"

    BinanceCryptoSource(http_get=cap).get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert captured["interval"] == "1d"


def test_unsupported_interval_raises():
    # M5 is supported; craft an interval not in the map by monkeypatching support off
    s = BinanceCryptoSource()
    # Use a genuinely unmapped interval: temporarily ensure W1/MN1 mapped; pick one removed
    # Instead assert that an interval absent from RESOLUTION_MAP raises.
    # All Interval members are mapped, so emulate by clearing one on a subclass.
    class Narrow(BinanceCryptoSource):
        SUPPORTED = frozenset({Interval.D1})
        RESOLUTION_MAP = {Interval.D1: "1d"}

    with pytest.raises(UnsupportedInterval):
        Narrow(http_get=lambda u, p, h: _payload()).get_klines("BTCUSDT", Interval.H1, *WIDE)


# --- empty / no-data --------------------------------------------------------


def test_empty_array_raises_empty():
    with pytest.raises(EmptyData):
        src_with("[]").get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_no_bars_in_range_raises_empty():
    # rows exist but fall entirely outside the requested window
    with pytest.raises(EmptyData):
        src_with(_payload()).get_klines(
            "BTCUSDT", Interval.D1, date(2020, 1, 1), date(2020, 1, 2)
        )


# --- error objects / invalid data -------------------------------------------


def test_binance_error_object_raises_empty_or_invalid():
    # Binance returns {"code":-1121,"msg":"Invalid symbol."} (object, not array)
    payload = json.dumps({"code": -1121, "msg": "Invalid symbol."})
    with pytest.raises(EmptyData):
        src_with(payload).get_klines("NOPENOPE", Interval.D1, *WIDE)


def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        src_with("<html>504 gateway</html>").get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_malformed_scalar_close_raises_invalid():
    bad = _kline((1781481600000, "65711.11", "67248.13", "65315.84", "65711.11", "1.0"))
    bad[4] = "not-a-number"  # close
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_null_scalar_raises_invalid():
    bad = _kline((1781481600000, "65711.11", "67248.13", "65315.84", "65711.11", "1.0"))
    bad[2] = None  # high
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_garbage_timestamp_raises_invalid():
    bad = _kline((1781481600000, "65711.11", "67248.13", "65315.84", "65711.11", "1.0"))
    bad[0] = "xx"  # openTime
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_nan_price_raises_invalid():
    # bare NaN parsed by json.loads -> non-finite guard
    payload = (
        '[[1781481600000,"65711.11",NaN,"65315.84","65711.11","1.0",'
        '1781567999999,"0",100,"0","0","0"]]'
    )
    with pytest.raises(InvalidData):
        src_with(payload).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_negative_volume_raises_invalid():
    bad = _kline((1781481600000, "65711.11", "67248.13", "65315.84", "65711.11", "-5.0"))
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_ohlc_invariant_violation_raises_invalid():
    # low (99000) > high (67248) -> invalid
    bad = _kline((1781481600000, "65711.11", "67248.13", "99000.00", "65711.11", "1.0"))
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_short_row_raises_invalid():
    # a kline row with too few fields
    payload = json.dumps([[1781481600000, "65711.11", "67248.13"]])
    with pytest.raises(InvalidData):
        src_with(payload).get_klines("BTCUSDT", Interval.D1, *WIDE)


# --- transport --------------------------------------------------------------


def test_transport_error_wrapped():
    s = BinanceCryptoSource(http_get=_raising(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        s.get_klines("BTCUSDT", Interval.D1, *WIDE)


# --- request construction ---------------------------------------------------


def test_request_params_and_limit():
    captured = {}

    def cap(url, params, headers):
        captured["url"] = url
        captured["params"] = dict(params)
        return _payload()

    BinanceCryptoSource(http_get=cap).get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert captured["url"].endswith("/api/v3/klines")
    p = captured["params"]
    assert p["symbol"] == "BTCUSDT"
    assert p["interval"] == "1d"
    assert p["limit"] == 1000
    # start/end carried as epoch ms
    assert isinstance(p["startTime"], int)
    assert isinstance(p["endTime"], int)
    assert p["startTime"] < p["endTime"]


def test_datetime_inputs_accepted():
    h = src_with(_payload()).get_klines(
        "BTCUSDT", Interval.D1, datetime(2026, 6, 1, tzinfo=UTC), datetime(2026, 6, 30, tzinfo=UTC)
    )
    assert len(h) == 3
