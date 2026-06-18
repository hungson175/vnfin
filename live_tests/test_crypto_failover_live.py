"""Live cross-source agreement check for the crypto failover chain.

Binance (primary) and Coinbase (backup) must AGREE on recent BTC daily closes in USD —
this catches silent unit/scale mismatches (USDT vs USD, sec vs ms, low/high/open/close
order bugs) that synthetic fixtures cannot. The failover client must also succeed and
return a USD series.

Live-only: outside the default test collection; requires ``VNFIN_LIVE=1`` (enforced by
``live_tests/conftest.py``). Run with:
    VNFIN_LIVE=1 ./.venv/bin/python -m pytest live_tests/test_crypto_failover_live.py

NO fixtures are committed — every value is fetched live at run time.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.integration


def _rel_spread(values):
    lo, hi = min(values), max(values)
    return (hi - lo) / lo if lo else float("inf")


def test_binance_and_coinbase_agree_on_btc_daily_close():
    """Both crypto sources must report the same recent BTC daily close in USD."""
    from vnfin.crypto import BinanceCryptoSource, CoinbaseCryptoSource
    from vnfin.models import Interval

    end = date.today()
    start = end - timedelta(days=10)
    closes = {}
    for src, sym in (
        (BinanceCryptoSource(), "BTCUSDT"),
        (CoinbaseCryptoSource(), "BTC-USD"),
    ):
        try:
            h = src.get_klines(sym, Interval.D1, start, end)
            assert h.currency == "USD", f"{src.name} not USD"
            closes[src.name] = h.bars[-1].close
        except Exception:  # a single dead source must not fail the differential check
            pass
    assert len(closes) >= 2, f"need >=2 live crypto sources, got {closes}"
    for name, c in closes.items():
        assert 1_000 < c < 10_000_000, f"{name} BTC close {c} outside plausible USD band (unit bug?)"
    # Independent exchanges; allow a loose band for genuine venue spread / timing.
    assert _rel_spread(list(closes.values())) < 0.05, f"crypto sources disagree on BTC: {closes}"


def test_failover_client_returns_usd_series():
    from vnfin.crypto import default_crypto_client
    from vnfin.models import Interval

    end = date.today()
    start = end - timedelta(days=10)
    client = default_crypto_client()
    assert client.unit == "USD"
    h = client.get_klines("BTCUSDT", Interval.D1, start, end)
    assert h.currency == "USD"
    assert len(h) > 0
    assert 1_000 < h.bars[-1].close < 10_000_000


def test_failover_client_never_serves_btc_quoted_pair_as_usd():
    """B9 live: a real non-USD pair (ETHBTC) must NOT be served as USD by the USD chain.

    Binance trades ETHBTC (currency BTC, prices << 1); the USD chain's result-level unit
    guard must reject it -> AllSourcesFailed, never a BTC series mislabeled USD.
    """
    from vnfin.crypto import default_crypto_client
    from vnfin.exceptions import AllSourcesFailed
    from vnfin.models import Interval

    end = date.today()
    start = end - timedelta(days=10)
    client = default_crypto_client()
    with pytest.raises(AllSourcesFailed):
        client.get_klines("ETHBTC", Interval.D1, start, end)
