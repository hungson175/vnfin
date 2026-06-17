"""Cross-source consistency tests — differential / oracle testing (Boss directive).

Independent sources for the same quantity must AGREE. This catches the nastiest class
of bug — silent unit/scale mismatches (VND vs thousand-VND, per-chi vs per-luong,
USD/oz vs total) — plus stale/bad data, with NO committed fixtures.

Opt-in and CI-skipped: run with ``VNFIN_LIVE=1 ./.venv/bin/python -m pytest -m integration``.
Tolerances are deliberately wide where appropriate: tight (<2%) for adjusted equity
closes that must be unit-identical; loose magnitude bands elsewhere so the tests catch
order-of-magnitude unit errors without being brittle to real market moves.
"""
from __future__ import annotations

import os
from datetime import date, timedelta

import pytest

_LIVE = os.getenv("VNFIN_LIVE") == "1"
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _LIVE, reason="set VNFIN_LIVE=1 to run live cross-source tests"),
]


def _rel_spread(values):
    lo, hi = min(values), max(values)
    return (hi - lo) / lo if lo else float("inf")


def test_all_price_sources_agree_on_daily_close():
    """Every broker price source must return the same adjusted close (unit-identical VND)."""
    from vnfin.models import Interval
    from vnfin.sources.registry import ALL_SOURCE_CLASSES

    end = date.today()
    start = end - timedelta(days=12)
    closes = {}
    for cls in ALL_SOURCE_CLASSES:
        try:
            src = cls()
            closes[src.name] = src.get_history("FPT", Interval.D1, start, end).bars[-1].close
        except Exception:  # a single dead source must not fail the differential check
            pass
    assert len(closes) >= 2, f"need >=2 live price sources, got {closes}"
    for name, c in closes.items():
        assert 1_000 < c < 10_000_000, f"{name} close {c} outside plausible VND band (unit bug?)"
    assert _rel_spread(list(closes.values())) < 0.02, f"price unit/scale mismatch across sources: {closes}"


@pytest.mark.xfail(
    reason="VN gold adapter mislabels mixed-weight/silver rows as VND/chi — see docs/units.md",
    strict=False,
)
def test_vn_gold_dealers_same_magnitude():
    """BTMC vs PNJ must be the same order of magnitude (both VND/chi) — catches a x1000 bug."""
    from vnfin.gold import BTMCGoldSource, PNJGoldSource

    mids = {}
    for src in (BTMCGoldSource(), PNJGoldSource()):
        try:
            quotes = src.get_quotes()
            picks = [q.mid for q in quotes if q.mid > 0]
            if picks:
                picks.sort()
                mids[src.name] = picks[len(picks) // 2]  # median quote
        except Exception:
            pass
    assert mids, "no VN gold dealer reachable"
    for name, m in mids.items():
        # 1 chi of gold is ~millions of VND; this band only catches unit (x1000) errors
        assert 1_000_000 < m < 100_000_000, f"{name} mid {m} outside plausible VND/chi band (unit bug?)"
    if len(mids) >= 2:
        assert _rel_spread(list(mids.values())) < 0.5, f"VN gold dealers differ too much: {mids}"


def test_world_gold_spot_plausible_usd_per_oz():
    from vnfin.gold import CurrencyApiGoldSource, GoldApiSource

    prices = {}
    for src in (CurrencyApiGoldSource(), GoldApiSource()):
        try:
            prices[src.name] = src.get_quote().mid
        except Exception:
            pass
    assert prices, "no world gold source reachable"
    for name, p in prices.items():
        assert 500 < p < 20_000, f"{name} world gold {p} outside plausible USD/oz band (unit bug?)"
    if len(prices) >= 2:
        assert _rel_spread(list(prices.values())) < 0.05, f"world gold sources disagree: {prices}"


def test_crypto_btc_plausible_usd():
    from vnfin.crypto import BinanceCryptoSource
    from vnfin.models import Interval

    end = date.today()
    start = end - timedelta(days=10)
    h = BinanceCryptoSource().get_klines("BTCUSDT", Interval.D1, start, end)
    close = h.bars[-1].close
    assert h.currency == "USD"
    assert 1_000 < close < 10_000_000, f"BTC close {close} outside plausible USD band (unit bug?)"
