"""Macro cross-source agreement — LIVE differential test (no committed fixtures).

The no-key macro providers (World Bank, IMF DataMapper, DBnomics) must agree on
the SAME logical indicator for the SAME country, within a sensible tolerance. This
catches the worst class of macro bug: a silent unit/scale mismatch sneaking past
the per-indicator unit-homogeneity guard (e.g. percent-change vs index level, or
USD-level vs national-currency GDP).

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


def test_percent_indicator_agrees_across_no_key_providers():
    """WB and IMF must agree on a recent GDP-growth % for a real country (USA)."""
    from vnfin.macro import (
        IMFDataMapperSource,
        MacroIndicator,
        WorldBankMacroSource,
    )

    country = "USA"
    ind = MacroIndicator.GDP_GROWTH

    wb = WorldBankMacroSource().get_canonical_indicator(country, ind)
    imf = IMFDataMapperSource().get_indicator(country, ind)

    assert wb.unit == "%" and imf.unit == "%", f"unit mismatch: WB={wb.unit} IMF={imf.unit}"

    # Compare the most recent COMMON year (IMF carries projections WB may not have).
    wb_by_year = {d.year: v for (d, v) in wb.points}
    imf_by_year = {d.year: v for (d, v) in imf.points}
    common = sorted(set(wb_by_year) & set(imf_by_year))
    assert common, "no overlapping years between WB and IMF GDP-growth"
    year = common[-1]
    a, b = wb_by_year[year], imf_by_year[year]
    # Growth rates are small numbers; require absolute agreement within 1.0 pp.
    assert abs(a - b) < 1.0, f"GDP-growth % disagree for {country} {year}: WB={a} IMF={b}"


def test_failover_chain_serves_percent_indicator_for_vietnam():
    """The default no-key chain must return a plausible inflation % for Vietnam."""
    from vnfin.macro import MacroIndicator, get_indicator

    series = get_indicator("VNM", MacroIndicator.INFLATION)
    assert series.unit == "%"
    val = _latest_value(series)
    assert val is not None
    # Inflation % sanity band — catches an index-level leak (would be ~100+).
    assert -20.0 < val < 60.0, f"VN inflation {val} outside plausible % band (unit bug?)"


def test_failover_falls_through_to_imf_when_worldbank_blocked():
    """If World Bank is forced to fail, the chain must still answer via IMF."""
    from vnfin.exceptions import SourceUnavailable
    from vnfin.macro import (
        DBnomicsSource,
        IMFDataMapperSource,
        MacroIndicator,
        WorldBankMacroSource,
        default_macro_client,
    )

    def _dead(url, params=None, headers=None):
        raise SourceUnavailable("forced-down World Bank")

    wb = WorldBankMacroSource(http_get=_dead)
    chain = default_macro_client(sources=[wb, IMFDataMapperSource(), DBnomicsSource()])
    series = chain.get_indicator("USA", MacroIndicator.GDP_GROWTH)
    assert series.source == "imf_datamapper"
    assert series.unit == "%"
