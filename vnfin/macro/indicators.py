"""Canonical macro-indicator map: one logical indicator -> per-provider code + unit.

A failover chain must be able to serve the **same logical indicator** across
different providers. Each provider, though, names indicators differently
(World Bank uses WDI codes like ``NY.GDP.MKTP.KD.ZG``; IMF DataMapper uses WEO
codes like ``NGDP_RPCH``; DBnomics/IMF-IFS uses series like ``A.{CC}.NGDP_XDC``)
and — importantly — may emit a **different unit** for what looks like the "same"
quantity (IMF GDP level is USD bn, DBnomics IFS GDP is *national currency*).

This module is the single source of truth that maps a :class:`MacroIndicator`
to ``(provider code, provider unit)`` per provider. The macro failover client
uses the *unit* recorded here as the per-indicator unit-homogeneity key, so the
generic :class:`vnfin.failover.FailoverClient` guard structurally refuses to
silently fail over between providers that emit different units for the same
logical indicator (e.g. a percent-change series vs an index-level series).

Clean-room: indicator codes were taken only from each provider's own public API
docs/responses (World Bank Indicators API, IMF DataMapper WEO, IMF IFS via
DBnomics), never from any third-party library.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional


class MacroIndicator(str, Enum):
    """Logical, provider-independent macro indicators.

    String-valued so it round-trips cleanly through configs/JSON and so callers
    may pass either the enum or its string value.
    """

    GDP = "gdp"                    # nominal GDP level
    GDP_GROWTH = "gdp_growth"      # real GDP growth, % YoY
    CPI = "cpi"                    # consumer price index (level)
    INFLATION = "inflation"       # CPI inflation, % YoY
    UNEMPLOYMENT = "unemployment"  # unemployment rate, % of labor force


# Canonical (provider-independent) unit per indicator. This is the unit the
# failover chain promises to a caller; only providers that can emit this exact
# unit are eligible for that indicator's chain.
#
# Percent indicators (growth / inflation / unemployment) are unit-homogeneous
# across every no-key provider, so all three providers can serve them. Level
# indicators (GDP nominal, CPI index) diverge by provider unit/scale, so the
# canonical unit deliberately pins one unit and the homogeneity guard drops any
# provider that would emit a different one.
CANONICAL_UNIT: dict[MacroIndicator, str] = {
    MacroIndicator.GDP: "current US$",        # USD-level (WB current US$ / IMF USD bn excluded by unit)
    MacroIndicator.GDP_GROWTH: "%",
    MacroIndicator.CPI: "index",              # CPI index level (2010=100 class)
    MacroIndicator.INFLATION: "%",
    MacroIndicator.UNEMPLOYMENT: "%",
}


def normalize_indicator(indicator) -> MacroIndicator:
    """Coerce ``MacroIndicator`` | name | value to a :class:`MacroIndicator`.

    Accepts the enum itself, its ``.value`` (``"gdp_growth"``), or its member name
    (``"GDP_GROWTH"``), case-insensitively. Raises ``ValueError`` on anything else
    so callers get a clear, catchable error rather than a malformed request.
    """
    if isinstance(indicator, MacroIndicator):
        return indicator
    if isinstance(indicator, str):
        key = indicator.strip()
        # by value (e.g. "gdp_growth")
        for m in MacroIndicator:
            if key.lower() == m.value:
                return m
        # by member name (e.g. "GDP_GROWTH")
        try:
            return MacroIndicator[key.upper()]
        except KeyError:
            pass
    valid = ", ".join(m.value for m in MacroIndicator)
    raise ValueError(f"unknown macro indicator {indicator!r}; expected one of: {valid}")


def canonical_unit(indicator) -> str:
    """Canonical unit string for a logical indicator (the chain's promised unit)."""
    return CANONICAL_UNIT[normalize_indicator(indicator)]
