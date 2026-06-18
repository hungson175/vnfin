"""Tests for the Coinbase Exchange crypto candles adapter (backup source).

All payloads are SYNTHETIC, hand-crafted to match the live Coinbase
``GET /products/{PRODUCT}/candles`` shape (a JSON array-of-arrays, newest-first,
with JSON NUMBER scalars — NOT strings, unlike Binance). Every number below is
FABRICATED (obviously-fake round prices like 100/110/90/105 and made-up
volumes/timestamps) — NO real provider rows or live-proof values are committed.
Real proof snippets live only in docs/research/2026-06-18-crypto.md.

Coinbase candle array index map (verified live, see research doc):
    [0] time   (epoch SECONDS)        <- NOTE: seconds, not ms
    [1] low
    [2] high
    [3] open                          <- NOTE: order is low,high,open,close
    [4] close
    [5] volume (base asset)

Coinbase product symbols are BASE-QUOTE with a hyphen (e.g. BTC-USD), so the
adapter must accept BOTH a Binance-style concatenated symbol (BTCUSDT) and a
hyphenated product symbol (BTC-USD) and normalize internally. Coinbase quotes
in native fiat USD (and USDC), so BTC-USD -> currency "USD".
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.crypto import CoinbaseCryptoSource, CryptoBar, CryptoHistory
from vnfin.exceptions import (
    EmptyData,
    InvalidData,
    SourceUnavailable,
    UnsupportedInterval,
)
from vnfin.models import Interval

UTC = timezone.utc


def _sec(d: date) -> int:
    """Epoch-SECONDS at UTC midnight for a date (fabricated synthetic timestamps)."""
    return int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp())


# FABRICATED synthetic OHLCV — obviously-fake round numbers, NOT real provider data.
# Coinbase order is [time, low, high, open, close, volume] and NEWEST-FIRST.
# (date, low, high, open, close, volume)
_LOGICAL = [
    (date(2026, 6, 15), 90.0, 110.0, 100.0, 105.0, 12.345),
    (date(2026, 6, 16), 100.0, 120.0, 105.0, 115.0, 23.456),
    (date(2026, 6, 17), 108.0, 118.0, 115.0, 112.0, 34.567),
]


def _candle(rec):
    d, low, high, open_, close, vol = rec
    return [_sec(d), low, high, open_, close, vol]


def _payload(recs=None):
    recs = _LOGICAL if recs is None else recs
    # Coinbase returns NEWEST-FIRST.
    rows = [_candle(r) for r in recs]
    rows.sort(key=lambda row: row[0], reverse=True)
    return json.dumps(rows)


def src_with(text):
    return CoinbaseCryptoSource(http_get=lambda url, params, headers: text)


def _raising(exc):
    def _g(url, params, headers):
        raise exc

    return _g


# wide bounding range covering all synthetic rows
WIDE = (date(2026, 6, 1), date(2026, 6, 30))


# --- normal parse -----------------------------------------------------------


def test_parses_candles():
    h = src_with(_payload()).get_klines("BTC-USD", Interval.D1, *WIDE)
    assert isinstance(h, CryptoHistory)
    assert len(h) == 3
    assert all(isinstance(b, CryptoBar) for b in h.bars)
    assert h.interval is Interval.D1
    assert h.source == "coinbase"
    assert h.currency == "USD"


def test_ohlcv_values_and_order_mapping():
    """Coinbase order is [time, low, high, open, close, volume] — verify we map it
    correctly (NOT the Binance OHLC order)."""
    h = src_with(_payload()).get_klines("BTC-USD", Interval.D1, *WIDE)
    b = h.bars[0]  # earliest after our internal sort (2026-06-15)
    assert b.low == pytest.approx(90.0)
    assert b.high == pytest.approx(110.0)
    assert b.open == pytest.approx(100.0)
    assert b.close == pytest.approx(105.0)
    assert isinstance(b.volume, float)
    assert b.volume == pytest.approx(12.345)


def test_time_is_tz_aware_utc_from_seconds():
    h = src_with(_payload()).get_klines("BTC-USD", Interval.D1, *WIDE)
    b = h.bars[0]
    assert b.time.tzinfo is not None
    assert b.time.utcoffset() == timedelta(0)
    assert b.time == datetime(2026, 6, 15, tzinfo=UTC)  # fabricated openTime (seconds)


def test_bars_sorted_ascending_even_though_coinbase_newest_first():
    h = src_with(_payload()).get_klines("BTC-USD", Interval.D1, *WIDE)
    times = [b.time for b in h.bars]
    assert times == sorted(times)
    assert times[0] == datetime(2026, 6, 15, tzinfo=UTC)
    assert times[-1] == datetime(2026, 6, 17, tzinfo=UTC)


def test_attribution_and_fetched_at():
    h = src_with(_payload()).get_klines("BTC-USD", Interval.D1, *WIDE)
    assert h.source == "coinbase"
    assert h.fetched_at_utc is not None
    assert h.fetched_at_utc.tzinfo is not None


def test_to_dataframe_roundtrip():
    h = src_with(_payload()).get_klines("BTC-USD", Interval.D1, *WIDE)
    df = h.to_dataframe()
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert len(df) == 3
    assert df.attrs["currency"] == "USD"
    assert df.attrs["source"] == "coinbase"


def test_range_filtered():
    h = src_with(_payload()).get_klines(
        "BTC-USD", Interval.D1, date(2026, 6, 16), date(2026, 6, 16)
    )
    assert len(h) == 1
    assert h.bars[0].time.date() == date(2026, 6, 16)


# --- symbol normalization (hyphen vs concatenated) --------------------------


def test_accepts_hyphenated_product_symbol():
    h = src_with(_payload()).get_klines("BTC-USD", Interval.D1, *WIDE)
    assert h.base_asset == "BTC"
    assert h.quote_asset == "USD"
    assert h.currency == "USD"


def test_accepts_binance_style_concatenated_symbol():
    """BTCUSDT (Binance form) must be normalized to a Coinbase BTC-USD product and
    map a USD-stablecoin quote to currency USD so the failover chain is unit-homogeneous."""
    captured = {}

    def cap(url, params, headers):
        captured["url"] = url
        return _payload()

    h = CoinbaseCryptoSource(http_get=cap).get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert h.base_asset == "BTC"
    assert h.quote_asset == "USD"
    assert h.currency == "USD"
    # the Coinbase product path uses the hyphenated BASE-QUOTE form
    assert "BTC-USD" in captured["url"]


def test_symbol_lowercase_normalized_uppercase():
    h = src_with(_payload()).get_klines("btc-usd", Interval.D1, *WIDE)
    assert h.base_asset == "BTC"
    assert h.quote_asset == "USD"


def test_usdc_quote_maps_to_usd():
    h = src_with(_payload()).get_klines("ETH-USDC", Interval.D1, *WIDE)
    assert h.currency == "USD"
    assert h.base_asset == "ETH"
    assert h.quote_asset == "USDC"


def test_concatenated_usdc_quote():
    h = src_with(_payload()).get_klines("ETHUSDC", Interval.D1, *WIDE)
    assert h.currency == "USD"
    assert h.base_asset == "ETH"


def test_price_and_volume_units():
    h = src_with(_payload()).get_klines("BTC-USD", Interval.D1, *WIDE)
    assert h.volume_unit == "BTC"
    assert h.price_unit == "USD per BTC"
    assert h.value_unit == "USD"


def test_empty_symbol_raises_invalid():
    with pytest.raises(InvalidData):
        src_with(_payload()).get_klines("   ", Interval.D1, *WIDE)


def test_unknown_quote_asset_raises_invalid():
    with pytest.raises(InvalidData):
        src_with(_payload()).get_klines("FAKE1ZZZ", Interval.D1, *WIDE)


# --- interval / granularity mapping -----------------------------------------


def test_supports_only_coinbase_granularities():
    s = CoinbaseCryptoSource()
    # Coinbase supports 60/300/900/3600/21600/86400 -> M1/M5/M15/H1/(6h)/D1.
    for iv in (Interval.M1, Interval.M5, Interval.M15, Interval.H1, Interval.D1):
        assert s.supports(iv), iv
    # Coinbase does NOT have 30m, 1w, or 1M granularities.
    for iv in (Interval.M30, Interval.W1, Interval.MN1):
        assert not s.supports(iv), iv


def test_granularity_param_mapping():
    captured = {}

    def cap(url, params, headers):
        captured.update(params)
        return _payload()

    CoinbaseCryptoSource(http_get=cap).get_klines("BTC-USD", Interval.H1, *WIDE)
    assert captured["granularity"] == 3600

    CoinbaseCryptoSource(http_get=cap).get_klines("BTC-USD", Interval.D1, *WIDE)
    assert captured["granularity"] == 86400

    CoinbaseCryptoSource(http_get=cap).get_klines("BTC-USD", Interval.M1, *WIDE)
    assert captured["granularity"] == 60


def test_unsupported_interval_raises():
    with pytest.raises(UnsupportedInterval):
        src_with(_payload()).get_klines("BTC-USD", Interval.MN1, *WIDE)


# --- empty / no-data --------------------------------------------------------


def test_empty_array_raises_empty():
    with pytest.raises(EmptyData):
        src_with("[]").get_klines("BTC-USD", Interval.D1, *WIDE)


def test_no_bars_in_range_raises_empty():
    with pytest.raises(EmptyData):
        src_with(_payload()).get_klines(
            "BTC-USD", Interval.D1, date(2020, 1, 1), date(2020, 1, 2)
        )


# --- error objects / invalid data -------------------------------------------


def test_coinbase_error_object_raises_empty():
    # Coinbase returns {"message":"NotFound"} (object, not array) for a bad product.
    payload = json.dumps({"message": "NotFound"})
    with pytest.raises(EmptyData):
        src_with(payload).get_klines("BTC-USD", Interval.D1, *WIDE)


def test_unsupported_granularity_error_object_raises_empty():
    payload = json.dumps({"message": "Unsupported granularity"})
    with pytest.raises(EmptyData):
        src_with(payload).get_klines("BTC-USD", Interval.D1, *WIDE)


def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        src_with("<html>504 gateway</html>").get_klines("BTC-USD", Interval.D1, *WIDE)


_GOOD = (date(2026, 6, 15), 90.0, 110.0, 100.0, 105.0, 1.0)


def test_malformed_scalar_close_raises_invalid():
    bad = _candle(_GOOD)
    bad[4] = "not-a-number"  # close
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTC-USD", Interval.D1, *WIDE)


def test_null_scalar_raises_invalid():
    bad = _candle(_GOOD)
    bad[2] = None  # high
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTC-USD", Interval.D1, *WIDE)


def test_garbage_timestamp_raises_invalid():
    bad = _candle(_GOOD)
    bad[0] = "xx"  # time
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTC-USD", Interval.D1, *WIDE)


def test_nan_price_raises_invalid():
    open_sec = _sec(date(2026, 6, 15))
    payload = f'[[{open_sec},90.0,NaN,100.0,105.0,1.0]]'  # high = NaN
    with pytest.raises(InvalidData):
        src_with(payload).get_klines("BTC-USD", Interval.D1, *WIDE)


def test_negative_volume_raises_invalid():
    bad = _candle((date(2026, 6, 15), 90.0, 110.0, 100.0, 105.0, -5.0))
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTC-USD", Interval.D1, *WIDE)


def test_negative_price_raises_invalid():
    bad = _candle((date(2026, 6, 15), -0.5, 110.0, 100.0, 105.0, 1.0))  # low < 0
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTC-USD", Interval.D1, *WIDE)


def test_zero_prices_allowed_if_invariants_hold():
    ok = _candle((date(2026, 6, 15), 0.0, 0.0, 0.0, 0.0, 0.0))
    h = src_with(json.dumps([ok])).get_klines("BTC-USD", Interval.D1, *WIDE)
    assert h.bars[0].low == 0.0


def test_ohlc_invariant_violation_raises_invalid():
    # low (200) > high (110) -> invalid
    bad = _candle((date(2026, 6, 15), 200.0, 110.0, 100.0, 105.0, 1.0))
    with pytest.raises(InvalidData):
        src_with(json.dumps([bad])).get_klines("BTC-USD", Interval.D1, *WIDE)


def test_short_row_raises_invalid():
    payload = json.dumps([[_sec(date(2026, 6, 15)), 90.0, 110.0]])
    with pytest.raises(InvalidData):
        src_with(payload).get_klines("BTC-USD", Interval.D1, *WIDE)


def test_non_list_payload_raises_invalid():
    # a JSON scalar / unexpected shape
    with pytest.raises(InvalidData):
        src_with('"surprise"').get_klines("BTC-USD", Interval.D1, *WIDE)


# --- transport --------------------------------------------------------------


def test_transport_error_wrapped():
    s = CoinbaseCryptoSource(http_get=_raising(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        s.get_klines("BTC-USD", Interval.D1, *WIDE)


# --- request construction ---------------------------------------------------


def test_request_url_and_params():
    captured = {}

    def cap(url, params, headers):
        captured["url"] = url
        captured["params"] = dict(params)
        return _payload()

    CoinbaseCryptoSource(http_get=cap).get_klines("BTC-USD", Interval.D1, *WIDE)
    assert "/products/BTC-USD/candles" in captured["url"]
    p = captured["params"]
    assert p["granularity"] == 86400
    # start/end carried as ISO8601 strings
    assert isinstance(p["start"], str)
    assert isinstance(p["end"], str)
    assert p["start"] < p["end"]


def test_datetime_inputs_accepted():
    h = src_with(_payload()).get_klines(
        "BTC-USD",
        Interval.D1,
        datetime(2026, 6, 1, tzinfo=UTC),
        datetime(2026, 6, 30, tzinfo=UTC),
    )
    assert len(h) == 3


# --- B10: backward pagination must not drop boundary candles ----------------

_DAY_SEC = 86_400


def _provider_window(all_secs, start_sec, end_sec, cap=300):
    """Simulate Coinbase: inclusive [start, end], NEWEST-FIRST, capped at ``cap`` rows.

    The real provider caps each call at ~300 candles; when asked for an inclusive
    window that contains more than 300 candle slots it returns only the 300 NEWEST,
    silently dropping the oldest boundary candles. The B10 bug was that an off-by-one
    page span requested 301 slots, so one boundary candle per page was dropped and the
    backward step then skipped it. This faithful simulator reproduces that.
    """
    win = sorted((s for s in all_secs if start_sec <= s <= end_sec), reverse=True)
    return win[:cap]


def test_pagination_multi_page_covers_exact_bar_count_no_boundary_drop():
    """A 750-daily-candle range (> 2 Coinbase pages) must return EXACTLY 750 bars.

    Regression for B10: the old ``page_span = step * 300`` requested 301 inclusive
    candle slots per page; the provider's 300-row cap dropped one boundary candle per
    page and the backward step skipped it (observed 748 of 750). The fix windows each
    page to exactly 300 candle slots and overlaps slabs (de-duplicated), so no boundary
    candle is ever lost.
    """
    n = 750
    base = _sec(date(2024, 1, 1))
    all_secs = [base + i * _DAY_SEC for i in range(n)]
    expected_secs = set(all_secs)

    calls = {"n": 0}

    def paging_http(url, params, headers):
        calls["n"] += 1
        # adapter sends ISO8601 start/end; convert back to epoch seconds
        st = int(datetime.strptime(params["start"], "%Y-%m-%dT%H:%M:%S")
                 .replace(tzinfo=UTC).timestamp())
        et = int(datetime.strptime(params["end"], "%Y-%m-%dT%H:%M:%S")
                 .replace(tzinfo=UTC).timestamp())
        secs = _provider_window(all_secs, st, et, cap=300)
        # build NEWEST-FIRST candle rows (Coinbase order: time,low,high,open,close,vol)
        rows = [[s, 90.0, 110.0, 100.0, 105.0, 1.0] for s in secs]
        return json.dumps(rows)

    start = date(2024, 1, 1)
    end = start + timedelta(days=n - 1)
    h = CoinbaseCryptoSource(http_get=paging_http).get_klines(
        "BTC-USD", Interval.D1, start, end
    )

    # exactly 750 bars, no boundary candle dropped, none duplicated
    assert len(h) == n
    got_secs = {int(b.time.timestamp()) for b in h.bars}
    assert got_secs == expected_secs
    # multiple paginated calls were actually made (range > one 300-candle page)
    assert calls["n"] >= 3
    # ascending, de-duplicated
    times = [b.time for b in h.bars]
    assert times == sorted(times)
    assert len(set(times)) == n


def test_pagination_deduplicates_overlapping_slabs():
    """Overlapping backward slabs (boundary candle fetched by two pages) must not
    double-count: B10 fix relies on overlap+dedupe, so the bar count stays exact."""
    n = 605  # spans 3 pages with overlap
    base = _sec(date(2024, 1, 1))
    all_secs = [base + i * _DAY_SEC for i in range(n)]

    def paging_http(url, params, headers):
        st = int(datetime.strptime(params["start"], "%Y-%m-%dT%H:%M:%S")
                 .replace(tzinfo=UTC).timestamp())
        et = int(datetime.strptime(params["end"], "%Y-%m-%dT%H:%M:%S")
                 .replace(tzinfo=UTC).timestamp())
        secs = _provider_window(all_secs, st, et, cap=300)
        rows = [[s, 90.0, 110.0, 100.0, 105.0, 1.0] for s in secs]
        return json.dumps(rows)

    start = date(2024, 1, 1)
    end = start + timedelta(days=n - 1)
    h = CoinbaseCryptoSource(http_get=paging_http).get_klines(
        "BTC-USD", Interval.D1, start, end
    )
    times = [b.time for b in h.bars]
    assert len(times) == len(set(times)) == n


# --- unit attribute for the failover guard ----------------------------------


def test_unit_attr_is_usd():
    assert CoinbaseCryptoSource().unit == "USD"
