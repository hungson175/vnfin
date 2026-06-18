"""Cross-source consistency tests — differential / oracle testing (Boss directive).

Independent sources for the same quantity must AGREE. This catches the nastiest class
of bug — silent unit/scale mismatches (VND vs thousand-VND, per-chi vs per-luong,
USD/oz vs total) — plus stale/bad data, with NO committed fixtures.

Live-only: outside the default test collection; requires ``VNFIN_LIVE=1`` (enforced by
``live_tests/conftest.py``). Run with ``VNFIN_LIVE=1 ./.venv/bin/python -m pytest live_tests/``.
Tolerances are deliberately wide where appropriate: tight (<2%) for adjusted equity
closes that must be unit-identical; loose magnitude bands elsewhere so the tests catch
order-of-magnitude unit errors without being brittle to real market moves.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.integration


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


def test_vn_gold_dealers_same_magnitude():
    """BTMC vs PNJ must agree on the canonical VN gold quote (both VND/lượng).

    Catches the class of unit bugs this fix resolved: mixed gold/silver rows, total
    price for a stated weight vs per-chỉ, and thousand-VND vs VND scaling. Both
    dealers must land in the per-lượng band and within a loose relative spread.
    """
    from vnfin.gold import BTMCGoldSource, PNJGoldSource

    mids = {}
    for src in (BTMCGoldSource(), PNJGoldSource()):
        try:
            quotes = src.get_quotes()
            assert all(q.unit == "VND/luong" for q in quotes), f"{src.name} not VND/luong"
            picks = [q.mid for q in quotes if q.mid > 0]
            if picks:
                picks.sort()
                mids[src.name] = picks[len(picks) // 2]  # median quote
        except Exception:
            pass
    assert mids, "no VN gold dealer reachable"
    for name, m in mids.items():
        # 1 lượng of gold is ~hundreds of millions of VND; this band catches unit errors
        # (per-chỉ ~15M, thousand-VND-scale ~150k, or silver contamination).
        assert 10_000_000 < m < 1_000_000_000, f"{name} mid {m} outside plausible VND/luong band (unit bug?)"
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
