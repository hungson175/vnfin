"""Tests for the Binance crypto klines adapter.

All payloads are SYNTHETIC, hand-crafted to match the live Binance
``GET /api/v3/klines`` shape (a JSON array-of-arrays with string scalars).
Every number below is FABRICATED (obviously-fake round prices like 100/110/90/105
and made-up volumes/timestamps) — NO real provider rows or live-proof values are
committed here. Real proof snippets live only in docs/sources/crypto-binance.md.

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
DAY_MS = 86_400_000


def _ms(d: date) -> int:
    """Epoch-ms at UTC midnight for a date (fabricated synthetic timestamps)."""
    return int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp() * 1000)


# FABRICATED synthetic OHLCV — obviously-fake round numbers, NOT real provider data.
# (openTime_ms, open, high, low, close, volume) as Binance string scalars.
_ROWS = [
    (_ms(date(2026, 6, 15)), "100.00", "110.00", "90.00", "105.00", "12.345"),
    (_ms(date(2026, 6, 16)), "105.00", "120.00", "100.00", "115.00", "23.456"),
    (_ms(date(2026, 6, 17)), "115.00", "118.00", "108.00", "112.00", "34.567"),
]


def _kline(row):
    open_ms, o, h, l, c, v = row
    close_ms = open_ms + DAY_MS - 1
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
    assert b.open == pytest.approx(100.00)
    assert b.high == pytest.approx(110.00)
    assert b.low == pytest.approx(90.00)
    assert b.close == pytest.approx(105.00)
    # base-asset volume is fractional -> kept as float, not int
    assert isinstance(b.volume, float)
    assert b.volume == pytest.approx(12.345)


def test_time_is_tz_aware_utc():
    h = src_with(_payload()).get_klines("BTCUSDT", Interval.D1, *WIDE)
    b = h.bars[0]
    assert b.time.tzinfo is not None
    assert b.time.utcoffset() == timedelta(0)  # UTC
    assert b.time == datetime(2026, 6, 15, tzinfo=UTC)  # fabricated openTime


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
    # Binance returns {"code":-1121,"msg":"Invalid symbol."} (object, not array).
    # Use a parseable fake pair so the provider-error path (not symbol parsing) is hit.
    payload = json.dumps({"code": -1121, "msg": "Invalid symbol."})
    with pytest.raises(EmptyData):
        src_with(payload).get_klines("ZZZUSDT", Interval.D1, *WIDE)


def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        src_with("<html>504 gateway</html>").get_klines("BTCUSDT", Interval.D1, *WIDE)


_GOOD = (_ms(date(2026, 6, 15)), "100.00", "110.00", "90.00", "105.00", "1.0")


def test_malformed_scalar_close_raises_invalid():
    bad = _kline(_GOOD)
    bad[4] = "not-a-number"  # close
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_null_scalar_raises_invalid():
    bad = _kline(_GOOD)
    bad[2] = None  # high
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_garbage_timestamp_raises_invalid():
    bad = _kline(_GOOD)
    bad[0] = "xx"  # openTime
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_nan_price_raises_invalid():
    # bare NaN parsed by json.loads -> non-finite guard
    open_ms = _ms(date(2026, 6, 15))
    payload = (
        f'[[{open_ms},"100.00",NaN,"90.00","105.00","1.0",'
        f'{open_ms + DAY_MS - 1},"0",100,"0","0","0"]]'
    )
    with pytest.raises(InvalidData):
        src_with(payload).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_negative_volume_raises_invalid():
    bad = _kline((_ms(date(2026, 6, 15)), "100.00", "110.00", "90.00", "105.00", "-5.0"))
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_negative_low_price_raises_invalid():
    # crypto prices cannot be negative even if low <= open/close <= high holds
    bad = _kline((_ms(date(2026, 6, 15)), "100.00", "110.00", "-0.50", "105.00", "1.0"))
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_negative_open_price_raises_invalid():
    # negative open with low below it; invariants pass but price must be rejected
    bad = _kline((_ms(date(2026, 6, 15)), "-5.00", "110.00", "-10.00", "105.00", "1.0"))
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_zero_prices_rejected_as_invalid():
    # Issue #59: an all-zero candle is not a valid market observation.
    bad = _kline((_ms(date(2026, 6, 15)), "0.00", "0.00", "0.00", "0.00", "0.0"))
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_ohlc_invariant_violation_raises_invalid():
    # low (200) > high (110) -> invalid
    bad = _kline((_ms(date(2026, 6, 15)), "100.00", "110.00", "200.00", "105.00", "1.0"))
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_short_row_raises_invalid():
    # a kline row with too few fields
    payload = json.dumps([[_ms(date(2026, 6, 15)), "100.00", "110.00"]])
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


# --- quote asset / currency metadata (B3) -----------------------------------


def test_usdt_pair_currency_is_usd():
    h = src_with(_payload()).get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert h.currency == "USD"
    assert h.base_asset == "BTC"
    assert h.quote_asset == "USDT"
    assert h.volume_unit == "BTC"
    assert h.price_unit == "USDT per BTC"


def test_other_usd_stablecoin_quotes_map_to_usd():
    for sym, base, quote in (
        ("ETHUSDC", "ETH", "USDC"),
        ("SOLBUSD", "SOL", "BUSD"),
        ("BNBFDUSD", "BNB", "FDUSD"),
        ("XRPTUSD", "XRP", "TUSD"),
    ):
        h = src_with(_payload()).get_klines(sym, Interval.D1, *WIDE)
        assert h.currency == "USD", sym
        assert h.base_asset == base
        assert h.quote_asset == quote


def test_btc_quoted_pair_currency_is_btc_not_usd():
    # ETHBTC prices are BTC per ETH; currency must NOT be hard-coded USD.
    h = src_with(_payload()).get_klines("ETHBTC", Interval.D1, *WIDE)
    assert h.currency == "BTC"
    assert h.base_asset == "ETH"
    assert h.quote_asset == "BTC"
    assert h.volume_unit == "ETH"
    assert h.price_unit == "BTC per ETH"
    assert h.to_dataframe().attrs["currency"] == "BTC"


def test_eth_and_fiat_quoted_pairs_keep_quote_currency():
    h1 = src_with(_payload()).get_klines("BNBETH", Interval.D1, *WIDE)
    assert h1.currency == "ETH" and h1.base_asset == "BNB"
    h2 = src_with(_payload()).get_klines("BTCEUR", Interval.D1, *WIDE)
    assert h2.currency == "EUR" and h2.base_asset == "BTC"


def test_unknown_quote_asset_raises_invalid():
    # an unrecognized quote suffix must fail loudly, not silently mislabel as USD
    with pytest.raises(InvalidData):
        src_with(_payload()).get_klines("FAKE1ZZZ", Interval.D1, *WIDE)


def test_empty_symbol_raises_invalid():
    with pytest.raises(InvalidData):
        src_with(_payload()).get_klines("   ", Interval.D1, *WIDE)


def test_dataframe_attrs_carry_quote_volume_metadata():
    df = src_with(_payload()).get_klines("BTCUSDT", Interval.D1, *WIDE).to_dataframe()
    assert df.attrs["base_asset"] == "BTC"
    assert df.attrs["quote_asset"] == "USDT"
    assert df.attrs["volume_unit"] == "BTC"
    assert df.attrs["price_unit"] == "USDT per BTC"


# --- pagination (B2) --------------------------------------------------------


def _seq_rows(start_day: date, n: int):
    """n consecutive synthetic daily rows (fabricated flat OHLC, increasing volume)."""
    rows = []
    for i in range(n):
        d = start_day + timedelta(days=i)
        rows.append((_ms(d), "100.00", "110.00", "90.00", "105.00", f"{1.0 + i:.3f}"))
    return rows


def test_pagination_covers_multi_page_range():
    """A range wider than one 1000-row page must trigger multiple HTTP calls and
    return ALL bars (no silent 1000-row truncation), ordered and de-duplicated."""
    start = date(2024, 1, 1)
    total = 2300  # > 2 full pages
    all_rows = _seq_rows(start, total)
    calls = {"n": 0, "starts": []}

    def paging_http(url, params, headers):
        calls["n"] += 1
        calls["starts"].append(params["startTime"])
        st = params["startTime"]
        et = params["endTime"]
        window = [r for r in all_rows if st <= r[0] <= et]
        page = window[:1000]  # provider caps at 1000 rows/call
        return json.dumps([_kline(r) for r in page])

    end = start + timedelta(days=total - 1)
    h = BinanceCryptoSource(http_get=paging_http).get_klines("BTCUSDT", Interval.D1, start, end)

    # all rows returned, not just the first 1000
    assert len(h) == total
    # multiple paginated calls were made
    assert calls["n"] >= 3
    # strictly increasing, de-duplicated open times
    times = [b.time for b in h.bars]
    assert times == sorted(times)
    assert len(set(times)) == total
    # cursor advanced (each call started later than the previous)
    assert calls["starts"] == sorted(calls["starts"])
    assert len(set(calls["starts"])) == calls["n"]


def test_pagination_stops_on_short_page():
    """A single short page (< limit) must not trigger extra calls."""
    calls = {"n": 0}

    def http(url, params, headers):
        calls["n"] += 1
        return _payload()  # 3 rows, far below the 1000 cap

    BinanceCryptoSource(http_get=http).get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert calls["n"] == 1


def test_pagination_deduplicates_overlapping_pages():
    """If pages overlap on the boundary bar, the result must not double-count it."""
    start = date(2024, 1, 1)
    rows = _seq_rows(start, 1500)

    def paging_http(url, params, headers):
        st = params["startTime"]
        et = params["endTime"]
        window = [r for r in rows if st <= r[0] <= et]
        page = window[:1000]
        return json.dumps([_kline(r) for r in page])

    end = start + timedelta(days=1499)
    h = BinanceCryptoSource(http_get=paging_http).get_klines("BTCUSDT", Interval.D1, start, end)
    times = [b.time for b in h.bars]
    assert len(times) == len(set(times)) == 1500
