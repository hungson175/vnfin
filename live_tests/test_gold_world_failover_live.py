"""Live world-gold (XAU/USD) daily-history checks against real provider infra.

Real-network only (outside the default ``tests/`` collection; requires ``VNFIN_LIVE=1``,
enforced by ``live_tests/conftest.py``). NEVER mocked, NEVER committing fixtures.

These tests have **no conditional ``pytest.skip``** (B12): once explicitly invoked with
``VNFIN_LIVE=1`` they are real pass/fail checks. The default world-gold chain now
contains only the reliable no-key source (currency-api); Stooq is an opt-in backup that
commonly answers a JS anti-bot challenge from datacenter IPs, so we assert its
*contract* (USD/oz data **or** a clean ``SourceUnavailable``) rather than skipping.

Run:  ``VNFIN_LIVE=1 ./.venv/bin/python -m pytest live_tests/test_gold_world_failover_live.py -q``
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.integration


def _last_price(hist):
    bars = sorted(hist.bars, key=lambda b: b.date)
    return bars[-1].price


def test_default_world_gold_chain_is_currency_api_only():
    """The default chain is the single reliable no-key source — Stooq is not in it."""
    from vnfin.gold import CurrencyApiGoldSource, StooqGoldSource, default_world_gold_sources

    sources = default_world_gold_sources()
    assert [type(s) for s in sources] == [CurrencyApiGoldSource]
    assert not any(isinstance(s, StooqGoldSource) for s in sources)


def test_world_gold_failover_returns_usd_oz_series():
    from vnfin.gold import default_world_gold_client

    end = date.today()
    start = end - timedelta(days=14)
    client = default_world_gold_client()
    hist = client.get_history(start, end)
    assert hist.unit == "USD/oz"
    assert hist.value_unit == "USD/oz"
    assert len(hist) >= 1
    # sanity magnitude band for XAU/USD spot (broad on purpose)
    assert 500.0 < _last_price(hist) < 50_000.0


def test_opt_in_stooq_backup_honors_its_contract():
    """Opt Stooq in as a backup: it must either serve USD/oz data or fail cleanly.

    No skip — both real-world outcomes are asserted as a valid contract:
    * reachable: returns a USD/oz series that agrees with currency-api within a wide
      band (catches order-of-magnitude unit/scale mistakes); or
    * unreachable from this host (the documented JS anti-bot challenge): raises a
      ``SourceUnavailable`` rather than leaking a raw exception.
    """
    from vnfin.exceptions import SourceUnavailable
    from vnfin.gold import CurrencyApiGoldSource, StooqGoldSource

    end = date.today()
    start = end - timedelta(days=14)

    primary = CurrencyApiGoldSource()
    p_hist = primary.get_history(start, end)
    p_price = _last_price(p_hist)
    assert p_hist.unit == "USD/oz"

    backup = StooqGoldSource()
    try:
        b_hist = backup.get_history(start, end)
    except SourceUnavailable:
        # Documented anti-bot outcome from datacenter IPs — failover-safe, not a skip.
        return

    b_price = _last_price(b_hist)
    assert b_hist.unit == "USD/oz"
    # wide tolerance: same scale/unit, not identical EOD timestamp
    rel = abs(p_price - b_price) / p_price
    assert rel < 0.10, f"world-gold sources disagree: currency-api={p_price} stooq={b_price}"
