"""vnfin.macro — cross-country macroeconomic indicator data.

Public API:
- ``IndicatorSeries`` — frozen typed result (country, indicator, points, source).
- ``WorldBankMacroSource`` — primary no-key cross-country source (World Bank API v2).
- ``FREDMacroSource`` — stub; TODO(requires FRED_API_KEY env), not yet implemented.

World Bank is the recommended backbone: no auth, deep annual history (1960+),
all countries (US/CHN/JPN/DEU/VNM and ~217 others), one consistent JSON schema.
"""
from __future__ import annotations

from .fred import FREDMacroSource
from .models import IndicatorSeries
from .worldbank import WorldBankMacroSource

__all__ = [
    "IndicatorSeries",
    "WorldBankMacroSource",
    "FREDMacroSource",
]
