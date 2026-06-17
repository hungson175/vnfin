"""Opt-in LIVE integration tests against real broker endpoints.

Skipped unless ``VNFIN_LIVE=1`` is set, so CI never live-fetches. Asserts only
structural invariants (never exact prices), and commits no broker data.
Run with: ``VNFIN_LIVE=1 ./.venv/bin/python -m pytest -m integration``.
"""
from __future__ import annotations

import os
from datetime import date, timedelta

import pytest

import vnfin
from vnfin.models import Interval

pytestmark = pytest.mark.integration

_LIVE = os.getenv("VNFIN_LIVE") == "1"
_skip = pytest.mark.skipif(not _LIVE, reason="set VNFIN_LIVE=1 to run live network tests")


@_skip
def test_default_client_fetches_daily_live():
    client = vnfin.default_client()
    end = date.today()
    start = end - timedelta(days=25)
    h = client.get_daily("FPT", start, end)
    assert len(h) > 0
    assert h.currency == "VND"
    assert h.adjustment_policy.value == "provider_adjusted"
    assert h.source in {"ssi", "vndirect", "vps", "pinetree"}
    bar = h.bars[-1]
    assert bar.low <= bar.open <= bar.high
    assert bar.low <= bar.close <= bar.high
    assert bar.volume >= 0
    assert bar.time.utcoffset() == timedelta(hours=7)


@_skip
def test_each_default_source_returns_daily_live():
    # Verify each default source independently returns a sane daily series.
    from vnfin.sources.registry import default_sources

    end = date.today()
    start = end - timedelta(days=25)
    for src in default_sources():
        h = src.get_history("FPT", Interval.D1, start, end)
        assert len(h) > 0, f"{src.name} returned no bars"
        assert h.currency == "VND"
