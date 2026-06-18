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
    "client",
    "source",
]


def source(http_get=None, timeout: float = 25.0) -> WorldBankMacroSource:
    """Primary macro entry: the default :class:`WorldBankMacroSource` (World Bank, no-key).

    Standard ``<domain>.source(...)`` factory. Use ``.get_indicator(...)`` on the
    returned object. ``FREDMacroSource`` is an advanced/opt-in alternative and is not
    the default (it is currently a stub requiring ``FRED_API_KEY``).
    """
    return WorldBankMacroSource(http_get=http_get, timeout=timeout)


# Default macro backbone is World Bank; ``client`` aliases ``source`` for consistency.
client = source
