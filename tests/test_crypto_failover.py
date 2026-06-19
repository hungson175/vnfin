"""Tests for the crypto failover client (Binance primary -> Coinbase backup).

Wires ``default_crypto_sources()`` + ``default_crypto_client()`` over the generic
``vnfin.failover.FailoverClient``, mirroring ``vnfin/client.py``. All payloads are
SYNTHETIC (fabricated round numbers); both adapters emit unit "USD" so the
unit-homogeneity guard accepts the chain.

Binance rows are array-of-arrays of STRINGS, order OHLC, time in ms.
Coinbase rows are array-of-arrays of NUMBERS, order low/high/open/close, time in sec,
newest-first. The two fixtures below match each provider's real shape exactly.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.crypto import (
    BinanceCryptoSource,
    CoinbaseCryptoSource,
    CryptoHistory,
    FailoverCryptoClient,
    default_crypto_client,
    default_crypto_sources,
)
from vnfin.crypto.models import CryptoBar
from vnfin.exceptions import (
    AllSourcesFailed,
    InvalidData,
    SourceUnavailable,
    UnitMismatchError,
    UnsupportedInterval,
)
from vnfin.models import Interval

UTC = timezone.utc
DAY_MS = 86_400_000


def _ms(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp() * 1000)


def _sec(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp())


# Binance-shaped synthetic page (strings, OHLC order, ms).
def _binance_payload():
    rows = []
    for d, o, h, l, c, v in [
        (date(2026, 6, 15), "100.00", "110.00", "90.00", "105.00", "1.0"),
        (date(2026, 6, 16), "105.00", "120.00", "100.00", "115.00", "2.0"),
    ]:
        ot = _ms(d)
        rows.append([ot, o, h, l, c, v, ot + DAY_MS - 1, "0", 100, "0", "0", "0"])
    return json.dumps(rows)


# Coinbase-shaped synthetic page (numbers, low/high/open/close order, sec, newest-first).
def _coinbase_payload():
    rows = []
    for d, low, high, op, cl, v in [
        (date(2026, 6, 15), 90.0, 110.0, 100.0, 105.0, 1.0),
        (date(2026, 6, 16), 100.0, 120.0, 105.0, 115.0, 2.0),
    ]:
        rows.append([_sec(d), low, high, op, cl, v])
    rows.sort(key=lambda r: r[0], reverse=True)
    return json.dumps(rows)


WIDE = (date(2026, 6, 1), date(2026, 6, 30))


# --- default factory --------------------------------------------------------


def test_default_sources_order_and_types():
    srcs = default_crypto_sources()
    assert len(srcs) == 2
    assert isinstance(srcs[0], BinanceCryptoSource)  # primary
    assert isinstance(srcs[1], CoinbaseCryptoSource)  # backup
    # both declare USD so the unit guard keeps both
    assert all(s.unit == "USD" for s in srcs)


def test_default_client_unit_is_usd():
    client = default_crypto_client()
    assert client.unit == "USD"


# --- primary success (no failover) ------------------------------------------


def test_primary_used_when_healthy():
    binance = BinanceCryptoSource(http_get=lambda u, p, h: _binance_payload())
    # Coinbase would raise if ever called -> proves it was NOT called.
    coinbase = CoinbaseCryptoSource(
        http_get=lambda u, p, h: (_ for _ in ()).throw(AssertionError("backup hit"))
    )
    client = default_crypto_client(sources=[binance, coinbase])
    h = client.get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert isinstance(h, CryptoHistory)
    assert h.source == "binance"
    assert len(h) == 2


# --- failover to backup -----------------------------------------------------


def test_failover_to_coinbase_on_primary_transport_error():
    def boom(url, params, headers):
        raise ConnectionError("binance down")

    binance = BinanceCryptoSource(http_get=boom)
    coinbase = CoinbaseCryptoSource(http_get=lambda u, p, h: _coinbase_payload())
    client = default_crypto_client(sources=[binance, coinbase])
    h = client.get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert h.source == "coinbase"  # failed over to backup
    assert h.currency == "USD"
    assert len(h) == 2


def test_failover_on_primary_empty():
    binance = BinanceCryptoSource(http_get=lambda u, p, h: "[]")  # EmptyData
    coinbase = CoinbaseCryptoSource(http_get=lambda u, p, h: _coinbase_payload())
    client = default_crypto_client(sources=[binance, coinbase])
    h = client.get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert h.source == "coinbase"


def test_failover_on_primary_invalid():
    binance = BinanceCryptoSource(http_get=lambda u, p, h: "<html>oops</html>")
    coinbase = CoinbaseCryptoSource(http_get=lambda u, p, h: _coinbase_payload())
    client = default_crypto_client(sources=[binance, coinbase])
    h = client.get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert h.source == "coinbase"


def test_all_sources_fail_raises_all_sources_failed():
    binance = BinanceCryptoSource(
        http_get=lambda u, p, h: (_ for _ in ()).throw(ConnectionError("x"))
    )
    coinbase = CoinbaseCryptoSource(
        http_get=lambda u, p, h: (_ for _ in ()).throw(ConnectionError("y"))
    )
    client = default_crypto_client(sources=[binance, coinbase])
    with pytest.raises(AllSourcesFailed):
        client.get_klines("BTCUSDT", Interval.D1, *WIDE)


def test_never_leaks_raw_exception():
    binance = BinanceCryptoSource(
        http_get=lambda u, p, h: (_ for _ in ()).throw(TimeoutError("raw"))
    )
    coinbase = CoinbaseCryptoSource(
        http_get=lambda u, p, h: (_ for _ in ()).throw(TimeoutError("raw"))
    )
    client = default_crypto_client(sources=[binance, coinbase])
    with pytest.raises(AllSourcesFailed):
        client.get_klines("BTCUSDT", Interval.D1, *WIDE)


# --- capability skip (Coinbase lacks weekly/monthly) ------------------------


def test_unsupported_interval_skips_incapable_backup_and_uses_primary():
    """W1 is supported by Binance but NOT Coinbase. Coinbase must be skipped (no call),
    not failed over to, and the primary serves the request."""
    binance = BinanceCryptoSource(http_get=lambda u, p, h: _binance_payload())
    coinbase = CoinbaseCryptoSource(
        http_get=lambda u, p, h: (_ for _ in ()).throw(AssertionError("backup hit on W1"))
    )
    client = default_crypto_client(sources=[binance, coinbase])
    h = client.get_klines("BTCUSDT", Interval.W1, *WIDE)
    assert h.source == "binance"


def test_no_capable_source_raises_unsupported_interval():
    """If the only configured source cannot serve the interval, surface a clean
    UnsupportedInterval (a capability signal), not AllSourcesFailed."""
    coinbase = CoinbaseCryptoSource(http_get=lambda u, p, h: _coinbase_payload())
    client = default_crypto_client(sources=[coinbase])  # Coinbase only, no weekly
    with pytest.raises(UnsupportedInterval):
        client.get_klines("BTCUSDT", Interval.W1, *WIDE)


# --- unit-homogeneity guard -------------------------------------------------


def test_unit_guard_rejects_mismatched_unit_source():
    class PointsSource(CoinbaseCryptoSource):
        unit = "points"

    binance = BinanceCryptoSource()
    bad = PointsSource()
    with pytest.raises(UnitMismatchError):
        default_crypto_client(sources=[binance, bad])


def test_unit_guard_accepts_homogeneous_usd_chain():
    # default chain is all USD -> constructs without raising
    client = default_crypto_client()
    assert client.unit == "USD"
    assert len(client.sources) == 2


# --- B9: result-level USD guard (non-USD pair must NOT be served as USD) -----


def _binance_btc_quoted_payload():
    """Synthetic ETHBTC-shaped page: prices in BTC (fabricated tiny round numbers)."""
    rows = []
    for d, o, h, l, c, v in [
        (date(2026, 6, 15), "0.05000", "0.06000", "0.04000", "0.05500", "10.0"),
        (date(2026, 6, 16), "0.05500", "0.07000", "0.05000", "0.06500", "20.0"),
    ]:
        ot = _ms(d)
        rows.append([ot, o, h, l, c, v, ot + DAY_MS - 1, "0", 100, "0", "0", "0"])
    return json.dumps(rows)


def test_ethbtc_btc_quoted_result_is_rejected_in_usd_chain():
    """A USD chain must NOT silently serve a BTC-quoted ETHBTC series as USD.

    Binance returns ETHBTC with currency/value_unit "BTC". Coinbase has no native
    ETH-BTC USD product and raises, so the only result available is BTC-denominated.
    The result-level unit guard must reject it -> AllSourcesFailed, never a BTC series
    mislabeled USD.
    """
    binance = BinanceCryptoSource(http_get=lambda u, p, h: _binance_btc_quoted_payload())
    coinbase = CoinbaseCryptoSource(
        http_get=lambda u, p, h: (_ for _ in ()).throw(ConnectionError("no eth-btc usd"))
    )
    client = default_crypto_client(sources=[binance, coinbase])
    assert client.unit == "USD"
    with pytest.raises(AllSourcesFailed):
        client.get_klines("ETHBTC", Interval.D1, *WIDE)


def test_ethbtc_never_returned_with_usd_value_unit():
    """Even from the primary alone, a BTC-quoted ETHBTC result is not served by a
    USD-declared chain. The guard checks the actual currency/value_unit, not the
    static source.unit."""
    binance = BinanceCryptoSource(http_get=lambda u, p, h: _binance_btc_quoted_payload())
    coinbase = CoinbaseCryptoSource(
        http_get=lambda u, p, h: (_ for _ in ()).throw(ConnectionError("x"))
    )
    client = default_crypto_client(sources=[binance, coinbase])
    with pytest.raises(AllSourcesFailed) as ei:
        client.get_klines("ETHBTC", Interval.D1, *WIDE)
    # the recorded attempt explains the rejection was a unit mismatch, not transport
    reasons = "; ".join(a.reason for a in ei.value.attempts)
    assert "unit mismatch" in reasons
    assert "BTC" in reasons


def test_usd_pair_still_served_normally():
    """The result guard must not block a legitimate USD result."""
    binance = BinanceCryptoSource(http_get=lambda u, p, h: _binance_payload())
    coinbase = CoinbaseCryptoSource(
        http_get=lambda u, p, h: (_ for _ in ()).throw(AssertionError("backup hit"))
    )
    client = default_crypto_client(sources=[binance, coinbase])
    h = client.get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert h.source == "binance"
    assert h.currency == "USD"
    assert h.value_unit == "USD"


# --- symbol normalization carries across the chain --------------------------


def test_backup_normalizes_binance_symbol_to_coinbase_product():
    captured = {}

    def boom(url, params, headers):
        raise ConnectionError("binance down")

    def cap(url, params, headers):
        captured["url"] = url
        return _coinbase_payload()

    binance = BinanceCryptoSource(http_get=boom)
    coinbase = CoinbaseCryptoSource(http_get=cap)
    client = default_crypto_client(sources=[binance, coinbase])
    h = client.get_klines("BTCUSDT", Interval.D1, *WIDE)
    assert h.source == "coinbase"
    # Coinbase product path uses the hyphenated BASE-QUOTE form even though the
    # caller passed the Binance concatenated symbol.
    assert "BTC-USD" in captured["url"]


def test_failover_crypto_client_materializes_iterator_sources():
    # Issue #95: iterator/generator sources must not drop the primary entry.
    class FakeCrypto:
        unit = "USD"

        def __init__(self, name):
            self.name = name

        def supports(self, interval):
            return True

        def get_klines(self, symbol, interval, start, end):
            return CryptoHistory(
                symbol=symbol,
                interval=interval,
                source=self.name,
                currency="USD",
                value_unit="USD",
                bars=(
                    CryptoBar(
                        datetime(2026, 1, 1, tzinfo=UTC),
                        1.0,
                        1.0,
                        1.0,
                        1.0,
                        1.0,
                    ),
                ),
            )

    client = FailoverCryptoClient(iter([FakeCrypto("primary"), FakeCrypto("backup")]))
    assert [s.name for s in client.sources] == ["primary", "backup"]
    assert client.get_klines("BTCUSDT", Interval.D1).source == "primary"

    single = FailoverCryptoClient(iter([FakeCrypto("only")]))
    assert [s.name for s in single.sources] == ["only"]
    assert single.get_klines("BTCUSDT", Interval.D1).source == "only"


def test_rejects_history_entirely_outside_requested_range():
    # Issue #84: crypto failover must reject out-of-window histories.
    class OutOfRangeCrypto:
        unit = "USD"

        def __init__(self, name):
            self.name = name

        def supports(self, interval):
            return True

        def get_klines(self, symbol, interval, start, end):
            return CryptoHistory(
                symbol=symbol,
                interval=interval,
                source=self.name,
                currency="USD",
                value_unit="USD",
                bars=(
                    CryptoBar(
                        datetime(2030, 1, 1, tzinfo=UTC),
                        1.0,
                        1.0,
                        1.0,
                        1.0,
                        1.0,
                    ),
                ),
            )

    class GoodCrypto(OutOfRangeCrypto):
        def get_klines(self, symbol, interval, start, end):
            return CryptoHistory(
                symbol=symbol,
                interval=interval,
                source=self.name,
                currency="USD",
                value_unit="USD",
                bars=(
                    CryptoBar(
                        datetime(2025, 1, 2, tzinfo=UTC),
                        1.0,
                        1.0,
                        1.0,
                        1.0,
                        1.0,
                    ),
                ),
            )

    client = FailoverCryptoClient([OutOfRangeCrypto("oor"), GoodCrypto("good")])
    h = client.get_klines("BTCUSDT", Interval.D1, date(2025, 1, 1), date(2025, 1, 3))
    assert h.source == "good"

    with pytest.raises(AllSourcesFailed):
        FailoverCryptoClient([OutOfRangeCrypto("oor")]).get_klines(
            "BTCUSDT", Interval.D1, date(2025, 1, 1), date(2025, 1, 3)
        )


def test_rejects_history_before_one_sided_start():
    # Review B3: one-sided start bound must reject bars entirely before start.

    class EarlyCrypto:
        unit = "USD"
        name = "early"

        def supports(self, interval):
            return True

        def get_klines(self, symbol, interval, start, end):
            return CryptoHistory(
                symbol=symbol,
                interval=interval,
                source=self.name,
                currency="USD",
                value_unit="USD",
                bars=(
                    CryptoBar(
                        datetime(2020, 1, 1, tzinfo=UTC),
                        1.0,
                        1.0,
                        1.0,
                        1.0,
                        1.0,
                    ),
                ),
            )

    with pytest.raises(AllSourcesFailed):
        FailoverCryptoClient([EarlyCrypto()]).get_klines(
            "BTCUSDT", Interval.D1, start=date(2025, 1, 1), end=None
        )


# --- Batch-1 result guards --------------------------------------------------


class _RawCryptoSource:
    """Test double that returns a CryptoHistory exactly as configured.

    ``name`` defaults to ``"raw"`` (matching ``_crypto_history``'s default
    ``source="raw"``) so the provenance guard (#126) accepts it; pass ``name`` to
    match a custom stamped ``source``.
    """

    unit = "USD"

    def __init__(self, history, name="raw"):
        self._history = history
        self.name = name

    def supports(self, interval):
        return True

    def get_klines(self, symbol, interval, start, end):
        return self._history


def _crypto_history(bars, **kwargs):
    defaults = dict(
        symbol="BTCUSDT",
        interval=Interval.D1,
        source="raw",
        currency="USD",
        value_unit="USD",
        base_asset="BTC",
        quote_asset="USDT",
        price_unit="USD per BTC",
        volume_unit="BTC",
    )
    defaults.update(kwargs)
    return CryptoHistory(bars=bars, **defaults)


def test_rejects_invalid_interval_before_source_call():
    src = _RawCryptoSource(_crypto_history(bars=()))
    client = FailoverCryptoClient([src])
    with pytest.raises(InvalidData):
        client.get_klines("BTCUSDT", "D1", date(2024, 1, 1), date(2024, 1, 2))
    assert src._history is not None  # no call made


def test_rejects_inverted_date_range_before_source_call():
    src = _RawCryptoSource(_crypto_history(bars=()))
    client = FailoverCryptoClient([src])
    with pytest.raises(InvalidData):
        client.get_klines(
            "BTCUSDT", Interval.D1, date(2024, 1, 3), date(2024, 1, 1)
        )


def test_rejects_empty_symbol_before_source_call():
    src = _RawCryptoSource(_crypto_history(bars=()))
    client = FailoverCryptoClient([src])
    with pytest.raises(InvalidData):
        client.get_klines("", Interval.D1, date(2024, 1, 1), date(2024, 1, 2))


def _assert_rejected_reason(history, expected_substring):
    client = FailoverCryptoClient([_RawCryptoSource(history)])
    with pytest.raises(AllSourcesFailed) as ei:
        client.get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 1, 3))
    assert expected_substring in ei.value.attempts[0].reason


def test_rejects_returned_interval_mismatch():
    bad = _crypto_history(
        bars=(CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),),
        interval=Interval.W1,
    )
    _assert_rejected_reason(bad, "interval mismatch")


def test_rejects_returned_currency_mismatch():
    bad = _crypto_history(
        bars=(CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),),
        currency="BTC",
        value_unit="BTC",
    )
    _assert_rejected_reason(bad, "unit mismatch")


@pytest.mark.parametrize(
    "currency,value_unit,expected_substring",
    [
        (None, "USD", "currency"),
        ("USD", None, "value_unit"),
        (None, None, "currency"),
        ("", "USD", "currency"),
        ("USD", "", "value_unit"),
        (True, "USD", "currency"),
        ("USD", [], "value_unit"),
        ("USD", 123, "value_unit"),
    ],
)
def test_rejects_missing_or_malformed_unit_metadata(currency, value_unit, expected_substring):
    """A USD chain must reject CryptoHistory results with missing/empty/malformed
    currency or value_unit; the unit guard must not accept absent metadata."""
    bad = _crypto_history(
        bars=(CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),),
        currency=currency,
        value_unit=value_unit,
    )
    _assert_rejected_reason(bad, expected_substring)


def test_rejects_returned_symbol_mismatch_and_failsover():
    # Regression: a result for a different base asset must be rejected and the
    # failover client must move on to the next source.
    bad = _crypto_history(
        bars=(CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),),
        symbol="ETHUSDT",
        base_asset="ETH",
        quote_asset="USDT",
    )
    good = _crypto_history(
        bars=(CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),),
        symbol="BTCUSDT",
        source="good",
        base_asset="BTC",
        quote_asset="USDT",
    )

    class NamedRaw(_RawCryptoSource):
        def __init__(self, history, name):
            super().__init__(history)
            self.name = name

    client = FailoverCryptoClient([NamedRaw(bad, "bad"), NamedRaw(good, "good")])
    h = client.get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 1, 3))
    assert h.symbol == "BTCUSDT"
    assert h.source == "good"


def test_rejects_unsorted_bars():
    bars = (
        CryptoBar(datetime(2024, 1, 3, tzinfo=UTC), 3, 3, 3, 3, 3),
        CryptoBar(datetime(2024, 1, 1, tzinfo=UTC), 1, 1, 1, 1, 1),
    )
    bad = _crypto_history(bars=bars)
    _assert_rejected_reason(bad, "not strictly ascending")


@pytest.mark.parametrize(
    "bar_factory,expected_substring",
    [
        (
            lambda t: CryptoBar(t, 100, 90, 110, 95, 1.0),
            "open 100 not in [low 110, high 90]",
        ),
        (
            lambda t: CryptoBar(t, 100, 110, 90, 95, -1.0),
            "volume must be non-negative",
        ),
        (
            lambda t: CryptoBar(t, -1, 1, -2, 0, 1.0),
            "open must be positive",
        ),
    ],
)
def test_rejects_economically_impossible_bars(bar_factory, expected_substring):
    t = datetime(2024, 1, 2, tzinfo=UTC)
    bad = _crypto_history(bars=(bar_factory(t),))
    _assert_rejected_reason(bad, expected_substring)


# --------------------------------------------------------------------------- #
# Issue #125 — malformed (non-typed) crypto result container -> rejected attempt
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "bad",
    [{}, None, [], 42, "history", object()],
    ids=["dict", "none", "list", "int", "str", "object"],
)
def test_rejects_malformed_crypto_result_container(bad):
    _assert_rejected_reason(bad, "unexpected result type")


def test_malformed_crypto_container_failsover_to_backup():
    good = _crypto_history(bars=(CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),), source="good")
    client = FailoverCryptoClient([_RawCryptoSource({}), _RawCryptoSource(good, name="good")])
    out = client.get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 1, 3))
    # The malformed primary must be rejected (not raise raw) and the backup used.
    assert out.source == "good"


# --------------------------------------------------------------------------- #
# Issue #124 — CryptoBar.time must be a timezone-AWARE datetime (tz-aware UTC).
# Naive datetimes / non-datetime keys are rejected before sort/window logic.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "bad_time",
    [
        datetime(2024, 1, 2),  # naive
        date(2024, 1, 2),      # date, not datetime
        "2024-01-02",          # string
        None,
        1704153600,            # epoch int
    ],
    ids=["naive_datetime", "date", "str", "none", "int"],
)
def test_rejects_malformed_crypto_bar_time(bad_time):
    bad = _crypto_history(bars=(CryptoBar(bad_time, 1, 1, 1, 1, 1),))
    _assert_rejected_reason(bad, "malformed bar time")


def test_malformed_crypto_bar_time_failsover_to_backup():
    bad = _crypto_history(bars=(CryptoBar(datetime(2024, 1, 2), 1, 1, 1, 1, 1),))
    good = _crypto_history(
        bars=(CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),), source="good"
    )
    client = FailoverCryptoClient([_RawCryptoSource(bad), _RawCryptoSource(good, name="good")])
    out = client.get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 1, 3))
    assert out.source == "good"


# --------------------------------------------------------------------------- #
# Issue #126 — provenance: a CryptoHistory stamped with a source that is not the
# producing source's name is rejected; failover continues.
# --------------------------------------------------------------------------- #
def test_rejects_crypto_provenance_mismatch_and_failsover():
    bad = _crypto_history(
        bars=(CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),), source="claimed_backup"
    )
    good = _crypto_history(
        bars=(CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),), source="good"
    )
    client = FailoverCryptoClient(
        [_RawCryptoSource(bad, name="real"), _RawCryptoSource(good, name="good")]
    )
    out = client.get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 1, 3))
    assert out.source == "good"


def test_crypto_provenance_match_is_accepted():
    good = _crypto_history(
        bars=(CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),), source="real"
    )
    client = FailoverCryptoClient([_RawCryptoSource(good, name="real")])
    out = client.get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 1, 3))
    assert out.source == "real"


# Issue #125 (reopen) — malformed inner crypto bar object.
@pytest.mark.parametrize("bad_row", [object(), None, {}, "bar", 42], ids=["object", "none", "dict", "str", "int"])
def test_rejects_malformed_crypto_bar_object(bad_row):
    _assert_rejected_reason(_crypto_history(bars=(bad_row,)), "malformed bar object")


def test_malformed_crypto_bar_object_failsover_to_backup():
    good = _crypto_history(bars=(CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),), source="good")
    client = FailoverCryptoClient([_RawCryptoSource(_crypto_history(bars=(object(),))), _RawCryptoSource(good, name="good")])
    out = client.get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 1, 3))
    assert out.source == "good"


# Issue #127 — present-malformed crypto fetched_at_utc rejected (None allowed).
@pytest.mark.parametrize(
    "bad_ts",
    [datetime(2026, 6, 19, 3), datetime(2026, 6, 19, 10, tzinfo=timezone(timedelta(hours=7))), "2026-06-19T03:00:00Z", 1718766000],
    ids=["naive", "non_utc", "str", "int"],
)
def test_rejects_malformed_crypto_fetched_at_utc(bad_ts):
    bars = (CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),)
    _assert_rejected_reason(_crypto_history(bars=bars, fetched_at_utc=bad_ts), "fetched_at_utc")


def test_accepts_none_crypto_fetched_at_utc():
    bars = (CryptoBar(datetime(2024, 1, 2, tzinfo=UTC), 1, 1, 1, 1, 1),)
    client = FailoverCryptoClient([_RawCryptoSource(_crypto_history(bars=bars, fetched_at_utc=None))])
    assert client.get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 1, 3)).source == "raw"
