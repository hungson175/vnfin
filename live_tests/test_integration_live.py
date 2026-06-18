"""LIVE integration tests against real broker endpoints.

Live-only: this directory is outside the default test collection and requires
``VNFIN_LIVE=1`` (enforced by ``live_tests/conftest.py``, which fails clearly rather
than skipping). Real network, never mocked; asserts only structural invariants (never
exact prices), commits no broker data.
Run with: ``VNFIN_LIVE=1 ./.venv/bin/python -m pytest live_tests/``.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

import vnfin
from vnfin.models import Interval

pytestmark = pytest.mark.integration


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


def test_each_default_source_returns_daily_live():
    # Verify each default source independently returns a sane daily series.
    from vnfin.sources.registry import default_sources

    end = date.today()
    start = end - timedelta(days=25)
    for src in default_sources():
        h = src.get_history("FPT", Interval.D1, start, end)
        assert len(h) > 0, f"{src.name} returned no bars"
        assert h.currency == "VND"
