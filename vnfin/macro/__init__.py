"""vnfin.macro — cross-country macroeconomic indicator data (no-key-first + BYOK).

Public API:
- ``IndicatorSeries`` — frozen typed result (country, indicator, points, source,
  unit, value_unit, indicator-specific ``currency`` (None for non-money series),
  ``frequency``, ``projection_from_year``). ``latest()`` excludes future
  projections; ``actual_points`` / ``latest_including_projections()`` expose them.
- ``MacroIndicator`` — canonical, provider-independent indicator enum (GDP,
  GDP_GROWTH, CPI, INFLATION, UNEMPLOYMENT).
- ``Frequency`` — annual/quarterly/monthly/daily observation cadence.
- ``MacroIndicatorSpec`` / ``canonical_unit`` / ``canonical_currency`` /
  ``eligible_sources`` — the canonical registry + the unit pre-filter that keeps
  only canonical-unit sources before failover (so default GDP/CPI/percent never
  raise ``UnitMismatchError``).
- No-key sources (default chain): ``WorldBankMacroSource`` (primary) ->
  ``IMFDataMapperSource`` -> ``DBnomicsSource``.
- ``FREDMacroSource`` — optional bring-your-own-key (``FRED_API_KEY``), official
  API only, excluded from the no-key default chain; keyless -> not capable, skipped
  without a network call.
- ``default_macro_sources()`` / ``default_macro_client()`` / ``get_indicator()`` —
  the failover chain that serves the SAME canonical indicator across providers,
  unit-pre-filtered then guarded.

World Bank is the recommended backbone: no auth, deep annual history (1960+),
all countries (US/CHN/JPN/DEU/VNM and ~217 others), one consistent JSON schema.
IMF DataMapper and DBnomics add no-key redundancy; FRED is an optional keyed
upgrade keyed to the *user's own* free key (never bundled, never scraped).
"""
from __future__ import annotations

from .client import (
    MacroClient,
    default_macro_client,
    default_macro_sources,
    get_indicator,
)
from .dbnomics import DBnomicsSource
from .fred import FREDMacroSource
from .imf import IMFDataMapperSource
from .indicators import (
    Frequency,
    MacroIndicator,
    MacroIndicatorSpec,
    canonical_currency,
    canonical_unit,
    eligible_sources,
    normalize_indicator,
)
from .models import IndicatorSeries
from .worldbank import WorldBankMacroSource

__all__ = [
    "IndicatorSeries",
    "MacroIndicator",
    "MacroIndicatorSpec",
    "Frequency",
    "canonical_unit",
    "canonical_currency",
    "eligible_sources",
    "normalize_indicator",
    "WorldBankMacroSource",
    "IMFDataMapperSource",
    "DBnomicsSource",
    "FREDMacroSource",
    "MacroClient",
    "default_macro_sources",
    "default_macro_client",
    "get_indicator",
    "client",
    "source",
]


def source(http_get=None, timeout: float = 25.0) -> WorldBankMacroSource:
    """Primary single-source macro entry: the default :class:`WorldBankMacroSource`.

    Standard ``<domain>.source(...)`` factory returning the World Bank backbone.
    For automatic multi-source failover over the same canonical indicator, use
    :func:`default_macro_client` / :func:`get_indicator` instead.
    """
    return WorldBankMacroSource(http_get=http_get, timeout=timeout)


def client(http_get=None, timeout: float = 25.0) -> MacroClient:
    """Standard ``<domain>.client(...)`` — World Bank->IMF->DBnomics no-key failover.

    Consistent with the other domains, ``client()`` returns the multi-source failover
    client; use :func:`source` for the bare primary (:class:`WorldBankMacroSource`).
    """
    return default_macro_client(http_get=http_get, timeout=timeout)
