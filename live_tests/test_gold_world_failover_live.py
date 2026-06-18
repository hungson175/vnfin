"""Live cross-source agreement for world-gold (XAU/USD) daily history.

Real-network only (outside the default ``tests/`` collection; requires ``VNFIN_LIVE=1``,
enforced by ``live_tests/conftest.py``). NEVER mocked, NEVER committing fixtures.

Asserts that the primary (currency-api) and the stooq backup agree on a recent EOD
XAU/USD price within a wide tolerance — the point is to catch order-of-magnitude
unit/scale mistakes (USD/oz vs total, x10, etc.), not to track market micro-moves.
The stooq leg may be unreachable from a datacenter IP (anti-bot JS challenge -> it
surfaces as SourceUnavailable); that case is reported, not silently passed.

Run:  ``VNFIN_LIVE=1 ./.venv/bin/python -m pytest live_tests/test_gold_world_failover_live.py -q``
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.integration


def _last_price(hist):
    bars = sorted(hist.bars, key=lambda b: b.date)
    return bars[-1].price


def test_world_gold_failover_returns_usd_oz_series():
    from vnfin.gold import default_world_gold_client

    end = date.today()
    start = end - timedelta(days=14)
    client = default_world_gold_client()
    hist = client.get_history(start, end)
    assert hist.unit == "USD/oz"
    assert len(hist) >= 1
    # sanity magnitude band for XAU/USD spot (broad on purpose)
    assert 500.0 < _last_price(hist) < 50_000.0


def test_primary_and_stooq_agree_when_both_reachable():
    from vnfin.exceptions import SourceError
    from vnfin.gold import CurrencyApiGoldSource, StooqGoldSource

    end = date.today()
    start = end - timedelta(days=14)

    primary = CurrencyApiGoldSource()
    backup = StooqGoldSource()

    p_hist = primary.get_history(start, end)
    p_price = _last_price(p_hist)
    assert p_hist.unit == "USD/oz"

    try:
        b_hist = backup.get_history(start, end)
    except SourceError as exc:
        pytest.skip(f"stooq backup unreachable from this host: {exc}")

    b_price = _last_price(b_hist)
    assert b_hist.unit == "USD/oz"
    # wide tolerance: same scale/unit, not identical EOD timestamp
    rel = abs(p_price - b_price) / p_price
    assert rel < 0.10, f"world-gold sources disagree: currency-api={p_price} stooq={b_price}"
