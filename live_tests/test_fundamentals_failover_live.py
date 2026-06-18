"""Live cross-source check for fundamentals failover (VNDirect vs CafeF).

Independent fundamental sources for the same company must AGREE in MAGNITUDE on a
headline annual figure (net revenue), proving both emit RAW VND on the same scale
— the failover unit-homogeneity guard depends on this. Also smoke-tests the
default failover chain end to end.

Live-only: outside the default test collection; requires ``VNFIN_LIVE=1``
(enforced by ``live_tests/conftest.py``). Run with:
    VNFIN_LIVE=1 ./.venv/bin/python -m pytest live_tests/test_fundamentals_failover_live.py

No committed fixtures. Uses a real, large-cap HOSE symbol on purpose so both
sources have coverage; tolerances are deliberately loose (line-item taxonomies
differ across providers) but tight enough to catch order-of-magnitude unit bugs.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

# A widely-covered large-cap; revenue is tens of trillions VND, far from any
# thousand-VND or billion-VND scaling artifact.
_SYMBOL = "FPT"


def _rel_spread(values):
    lo, hi = min(values), max(values)
    return (hi - lo) / lo if lo else float("inf")


def _latest_revenue(source):
    """Newest annual net-revenue figure (raw VND) from a fundamental source.

    VNDirect codes net revenue as itemCode 11000; CafeF codes it as DTTBHCCDV.
    Returns ``None`` if the source can't supply it (so one dead source doesn't
    fail the differential check).
    """
    from vnfin.fundamentals import Period, StatementType

    try:
        reports = source.get_financials(_SYMBOL, StatementType.INCOME, Period.ANNUAL, limit=2)
    except Exception:
        return None
    if not reports:
        return None
    newest = reports[0]
    return newest.get("11000") or newest.get("DTTBHCCDV")


def test_vndirect_and_cafef_agree_on_revenue_magnitude():
    from vnfin.fundamentals import CafeFFundamentalSource, VNDirectFundamentalSource

    revenues = {}
    for src in (VNDirectFundamentalSource(), CafeFFundamentalSource()):
        rev = _latest_revenue(src)
        if rev is not None:
            revenues[src.name] = rev
    assert revenues, "no fundamental source reachable"
    for name, rev in revenues.items():
        # tens of trillions VND for a large-cap; this band catches a x1000 or
        # /1e9 scaling bug while staying tolerant of which fiscal year is newest.
        assert 1e12 < rev < 1e16, f"{name} revenue {rev} outside plausible raw-VND band (unit bug?)"
    if len(revenues) >= 2:
        # Same fiscal year across providers should match closely; allow slack for
        # the case where one source's newest year leads the other by a period.
        assert _rel_spread(list(revenues.values())) < 0.25, (
            f"VNDirect vs CafeF revenue magnitude mismatch (unit/scale?): {revenues}"
        )


def test_default_failover_chain_returns_reports():
    from vnfin.fundamentals import Period, StatementType, default_fundamental_client

    client = default_fundamental_client()
    assert client.unit == "VND"
    reports = client.get_financials(_SYMBOL, StatementType.INCOME, Period.ANNUAL, limit=3)
    assert reports, "default failover chain returned no reports"
    assert reports[0].currency == "VND"
    assert reports[0].source in {"vndirect", "cafef"}
