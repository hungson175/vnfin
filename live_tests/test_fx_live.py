"""Live FX checks — cross-source USD/VND parity (differential/oracle testing).

The two no-key FX sources (open.er-api market rate, Vietcombank commercial transfer quote)
must AGREE on USD/VND within a tolerance that accepts the normal commercial-vs-market spread
(per Boss's "accept small difference" guidance). A large divergence flags a unit/inversion bug
or a broken source.

Live-only: outside the default collection; requires ``VNFIN_LIVE=1`` (enforced by
``live_tests/conftest.py``). Run: ``VNFIN_LIVE=1 ./.venv/bin/python -m pytest live_tests/test_fx_live.py``.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_usd_vnd_in_plausible_band_each_source():
    from vnfin.fx import OpenErApiFXSource, VietcombankFXSource

    for src in (OpenErApiFXSource(), VietcombankFXSource()):
        r = src.get_rate("USD")
        assert r.quote == "VND" and r.unit == "VND per 1 USD"
        assert 15_000 < r.rate < 40_000, f"{src.name} USD/VND {r.rate} outside band (unit bug?)"


def test_usd_vnd_cross_source_parity():
    from vnfin.fx import OpenErApiFXSource, VietcombankFXSource

    rates = {}
    errors = {}
    for src in (OpenErApiFXSource(), VietcombankFXSource()):
        try:
            rates[src.name] = src.get_rate("USD").rate
        except Exception as exc:  # capture per-source reason for fast diagnosis (no skip/fake)
            errors[src.name] = f"{type(exc).__name__}: {exc}"
    assert len(rates) >= 2, f"need both FX sources reachable; got rates={rates} errors={errors}"
    lo, hi = min(rates.values()), max(rates.values())
    spread = (hi - lo) / lo
    # market vs commercial-bank transfer quote: allow a modest spread, catch inversion/unit bugs
    assert spread < 0.05, f"USD/VND mismatch across FX sources (unit/inversion bug?): {rates}"


def test_failover_client_usd_vnd_live():
    from vnfin.fx import client

    r = client().get_rate("USD")
    assert r.quote == "VND" and 15_000 < r.rate < 40_000
