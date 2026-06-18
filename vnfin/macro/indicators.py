"""Canonical macro-indicator registry: one logical indicator -> per-provider spec.

A failover chain must be able to serve the **same logical indicator** across
different providers. Each provider, though, names indicators differently
(World Bank uses WDI codes like ``NY.GDP.MKTP.KD.ZG``; IMF DataMapper uses WEO
codes like ``NGDP_RPCH``; DBnomics/IMF-IFS uses series like ``A.{CC}.NGDP_XDC``)
and — importantly — may emit a **different unit** for what looks like the "same"
quantity (IMF GDP level is USD bn, DBnomics IFS GDP is *national currency*).

This module is the single source of truth that maps a :class:`MacroIndicator`
to a :class:`MacroIndicatorSpec` per provider: the provider's series code, the
unit it actually emits, the observation frequency, and whether it can carry
future projections (IMF WEO does). The macro failover client uses this registry
to:

1. **Pre-filter sources by unit** (B6/B7): before building the generic
   :class:`vnfin.failover.FailoverClient`, the macro client keeps only sources
   whose declared unit for the indicator equals the canonical unit. A source
   that would emit a noncanonical unit (e.g. IMF GDP in ``USD bn`` while the
   canonical GDP unit is ``current US$``) is dropped up front, so the default
   GDP/CPI/percent chains never trip the unit-homogeneity guard and a value is
   never relabelled into a unit it was not measured in.
2. **Carry frequency + projection semantics** (B8) onto each result.

Clean-room: indicator codes were taken only from each provider's own public API
docs/responses (World Bank Indicators API, IMF DataMapper WEO, IMF IFS via
DBnomics), never from any third-party library.
"""
from __future__ import annotations

from dataclasses import dataclass
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


class Frequency(str, Enum):
    """Observation frequency of an indicator series."""

    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    DAILY = "daily"


@dataclass(frozen=True)
class MacroIndicatorSpec:
    """How one provider serves one canonical :class:`MacroIndicator`.

    - ``provider_code`` — the provider's own series/indicator code.
    - ``unit`` — the unit the provider actually emits for this indicator. The
      macro client compares this against :func:`canonical_unit`; only an exact
      match is eligible for the indicator's failover chain (no relabelling).
    - ``frequency`` — observation frequency stamped onto the result.
    - ``carries_projections`` — True when the provider mixes future projections
      with historical actuals (IMF WEO). The adapter must then flag/filter
      projections so ``latest()`` never returns a future forecast as an actual.
    - ``currency`` — money unit when (and only when) it is meaningful. ``None``
      for percent/index indicators so we never stamp a misleading currency.
    """

    provider_code: str
    unit: str
    frequency: Frequency
    carries_projections: bool = False
    currency: Optional[str] = None


# Canonical (provider-independent) unit per indicator. This is the unit the
# failover chain promises to a caller; only providers that can emit this exact
# unit are eligible for that indicator's chain.
#
# Percent indicators (growth / inflation / unemployment) are unit-homogeneous
# across every no-key provider, so all three providers can serve them. Level
# indicators (GDP nominal, CPI index) diverge by provider unit/scale, so the
# canonical unit deliberately pins one unit and the macro client drops any
# provider that would emit a different one BEFORE the failover guard runs.
CANONICAL_UNIT: dict[MacroIndicator, str] = {
    MacroIndicator.GDP: "current US$",        # USD-level (WB current US$; IMF USD bn excluded by unit)
    MacroIndicator.GDP_GROWTH: "%",
    MacroIndicator.CPI: "index",              # CPI index level (2010=100 class)
    MacroIndicator.INFLATION: "%",
    MacroIndicator.UNEMPLOYMENT: "%",
}


# Canonical currency per indicator. Only money-denominated level indicators carry
# a currency; percent/index indicators carry ``None`` so a result is never
# stamped with a misleading currency (B7).
CANONICAL_CURRENCY: dict[MacroIndicator, Optional[str]] = {
    MacroIndicator.GDP: "USD",          # canonical GDP level is current US$
    MacroIndicator.GDP_GROWTH: None,
    MacroIndicator.CPI: None,           # index level, no currency
    MacroIndicator.INFLATION: None,
    MacroIndicator.UNEMPLOYMENT: None,
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


def canonical_currency(indicator) -> Optional[str]:
    """Canonical currency for a logical indicator, or ``None`` when not money-denominated."""
    return CANONICAL_CURRENCY[normalize_indicator(indicator)]


def _source_unit_for(source, indicator) -> Optional[str]:
    """Best-effort: the unit a source declares for ``indicator`` (``None`` if it can't).

    A source is eligible only when it both *supports* the indicator and declares
    a unit for it. Anything that raises or has no capability probe is treated as
    "declares no unit", so it is filtered out of a unit-pinned chain rather than
    silently anchoring it.
    """
    supports = getattr(source, "supports", None)
    if callable(supports):
        try:
            if not supports(indicator):
                return None
        except Exception:
            return None
    unit_for = getattr(source, "unit_for", None)
    if not callable(unit_for):
        return None
    try:
        return unit_for(indicator)
    except Exception:
        return None


def eligible_sources(sources, indicator) -> list:
    """Filter ``sources`` to those whose declared unit == the canonical unit.

    This is the B6/B7 fix: it runs BEFORE the generic
    :class:`vnfin.failover.FailoverClient` is built. Only sources that emit the
    exact canonical unit for ``indicator`` survive, so:

    - the default GDP/CPI/percent chains never raise ``UnitMismatchError`` (the
      surviving sources all share one unit), and
    - a source that would emit a noncanonical unit is rejected up front rather
      than having its values relabelled into a unit it was not measured in.

    Sources that don't expose ``supports``/``unit_for`` at all are treated as
    unit-undeclared and kept (so non-macro fakes still work), but any source that
    declares a *different* unit is dropped.
    """
    want = canonical_unit(indicator)
    kept = []
    for src in sources:
        # A source with neither probe is unit-undeclared -> keep (compatible-with-anything).
        if not hasattr(src, "supports") and not hasattr(src, "unit_for"):
            kept.append(src)
            continue
        unit = _source_unit_for(src, indicator)
        if unit is None:
            # Does not support the indicator (or can't declare a unit) -> drop;
            # the failover layer treats it as "no capable source" if none remain.
            continue
        if unit == want:
            kept.append(src)
        # unit != want -> noncanonical: drop (never relabel).
    return kept
