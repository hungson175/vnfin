"""Macro no-key live checks — RELIABLE-from-this-host subset (no skips, no flake).

The no-key macro chain is World-Bank-first. World Bank's official API answers
reliably from this server, so these are real pass/fail checks with **no conditional
``pytest.skip``**: once invoked with ``VNFIN_LIVE=1`` they must genuinely pass here.

IMF DataMapper probes were intentionally MOVED OUT of this suite: IMF's host
(``www.imf.org/external/datamapper``) returns HTTP 403 to this datacenter IP, which is
host-infra flakiness, not a library bug. Keeping those as hard live checks would make
``VNFIN_LIVE=1 pytest live_tests`` fail/skipped from this host. They now live as a
manually-invoked diagnostics script that is NOT collected by pytest:

    ./.venv/bin/python scripts/diagnostics_live.py            # runs the IMF probes too

Live-only: outside the default test collection; requires ``VNFIN_LIVE=1``
(enforced by ``live_tests/conftest.py``). Run with
``VNFIN_LIVE=1 ./.venv/bin/python -m pytest live_tests/test_macro_failover_live.py``.

Clean-room: World Bank / IMF DataMapper / DBnomics official APIs only; no vnstock.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def _latest_value(series):
    pt = series.latest()
    return pt[1] if pt else None


def test_failover_chain_serves_percent_indicator_for_vietnam():
    """The default no-key chain must return a plausible inflation % for Vietnam."""
    from vnfin.macro import MacroIndicator, get_indicator

    series = get_indicator("VNM", MacroIndicator.INFLATION)
    assert series.unit == "%"
    val = _latest_value(series)
    assert val is not None
    # Inflation % sanity band — catches an index-level leak (would be ~100+).
    assert -20.0 < val < 60.0, f"VN inflation {val} outside plausible % band (unit bug?)"


def test_default_gdp_chain_returns_usd_level_live():
    """Default GDP chain must return a USD level (World Bank) without UnitMismatch."""
    from vnfin.macro import MacroIndicator, get_indicator

    series = get_indicator("USA", MacroIndicator.GDP)
    assert series.unit == "current US$"
    assert series.currency == "USD"
    latest = series.latest()
    assert latest is not None and latest[1] > 0
