"""Macro failover client + default no-key chain.

Wraps the generic :class:`vnfin.failover.FailoverClient` for the macro domain,
mirroring how :class:`vnfin.client.FailoverPriceClient` wraps it for prices. The
chain serves the SAME logical :class:`~vnfin.macro.indicators.MacroIndicator`
across providers via the canonical indicator map, with a **per-indicator
unit-homogeneity guard**: a fresh engine is built per ``get_indicator`` call whose
``unit_of`` returns each source's unit *for that indicator*, so the guard refuses
to fail over between providers that emit different units for the same logical
indicator (e.g. WB GDP in current US$ vs DBnomics GDP in national currency).

Default no-key chain (order): World Bank -> IMF DataMapper -> DBnomics. FRED/BEA/
BLS-v2 are optional BYOK and are deliberately excluded from this default chain.

Capability skip: a source that does not map the requested indicator is skipped
without a network call (it does not count against ``max_attempts``), exactly like
the price client skips a source that does not support an interval.
"""
from __future__ import annotations

from dataclasses import replace

from ..exceptions import AllSourcesFailed, InvalidData
from ..failover import FailoverClient
from .dbnomics import DBnomicsSource
from .imf import IMFDataMapperSource
from .indicators import MacroIndicator, canonical_unit, normalize_indicator
from .models import IndicatorSeries
from .worldbank import WorldBankMacroSource

# Default no-key macro failover chain (primary first). FRED is BYOK -> excluded.
_DEFAULT_MACRO_SOURCE_CLASSES = (
    WorldBankMacroSource,
    IMFDataMapperSource,
    DBnomicsSource,
)


def default_macro_sources(http_get=None, timeout: float = 25.0):
    """Instantiate the default no-key macro failover chain.

    Order: World Bank -> IMF DataMapper -> DBnomics. All three are no-auth and
    serve the canonical percent indicators in the same unit; level indicators
    (GDP, CPI) are served only by the providers whose unit matches the canonical
    unit for that indicator (the per-indicator guard enforces this).
    """
    return [c(http_get=http_get, timeout=timeout) for c in _DEFAULT_MACRO_SOURCE_CLASSES]


def _fetch(source, country_iso3, indicator):
    """Call the right fetch method on a macro source for a canonical indicator.

    World Bank takes a raw WDI code on ``get_indicator`` and exposes a separate
    canonical entry; IMF/DBnomics take the canonical indicator directly.
    """
    fn = getattr(source, "get_canonical_indicator", None)
    if callable(fn):
        return fn(country_iso3, indicator)
    return source.get_indicator(country_iso3, indicator)


def _capable(source, country_iso3, indicator) -> bool:
    """Whether ``source`` can serve ``indicator`` (no network call)."""
    supports = getattr(source, "supports", None)
    if callable(supports):
        return bool(supports(indicator))
    # Sources without an explicit capability probe are assumed capable.
    return True


def _unit_of_for(indicator):
    """Build a ``unit_of`` accessor that returns each source's unit for ``indicator``.

    Sources that do not support the indicator declare no unit (``None``) so they
    do not anchor the guard; capable sources declare their per-indicator unit, and
    the guard rejects any chain mixing units for the same logical indicator.
    """

    def _unit_of(source):
        unit_for = getattr(source, "unit_for", None)
        if not callable(unit_for) or not _capable(source, None, indicator):
            return None
        try:
            return unit_for(indicator)
        except Exception:
            return None

    return _unit_of


class MacroClient:
    """Stable API for cross-country macro indicators with source failover.

    ``get_indicator(country_iso3, indicator)`` returns an :class:`IndicatorSeries`
    served by the first capable, healthy source whose unit matches the canonical
    unit for the logical indicator.
    """

    def __init__(self, sources=None, max_attempts: int = 3, http_get=None, timeout: float = 25.0):
        if sources is None:
            sources = default_macro_sources(http_get=http_get, timeout=timeout)
        self._sources = list(sources)
        self._max_attempts = max_attempts

    @property
    def sources(self):
        return list(self._sources)

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    def get_indicator(self, country_iso3: str, indicator) -> IndicatorSeries:
        """Fetch one canonical indicator for one country over the failover chain.

        Builds a per-indicator engine so the unit-homogeneity guard uses each
        source's unit *for this indicator*. Validates inputs up front; an unknown
        indicator raises ``ValueError`` and an empty country raises ``InvalidData``
        from the first attempted source.
        """
        ind = normalize_indicator(indicator)  # ValueError on unknown indicator
        if not (country_iso3 or "").strip():
            # Fail fast on bad caller input (failover-safe) before any source call.
            raise InvalidData("macro: empty country code")
        engine = FailoverClient(
            self._sources,
            operation=lambda src, country, i: _fetch(src, country, i),
            capability=lambda src, country, i: _capable(src, country, i),
            reject=self._reject_reason,
            unit_of=_unit_of_for(ind),
            max_attempts=self._max_attempts,
            failure_factory=lambda attempts, country, i: AllSourcesFailed(
                f"{country}/{getattr(i, 'value', i)}", None, attempts
            ),
            no_capable_factory=lambda country, i: AllSourcesFailed(
                f"{country}/{getattr(i, 'value', i)}", None, ()
            ),
            finalize=self._finalize_for(ind),
        )
        return engine.run(country_iso3, ind)

    @staticmethod
    def _reject_reason(series) -> str | None:
        if series is None or len(series.points) == 0:
            return "empty result"
        return None

    @staticmethod
    def _finalize_for(indicator):
        unit = canonical_unit(indicator)

        def _finalize(series, attempts, country, i) -> IndicatorSeries:
            # Stamp the canonical unit so the returned series is consistent across
            # providers, and attach the failover diagnostics via warnings.
            note = "; ".join(f"{a.name}:{a.reason}" for a in attempts)
            warnings = tuple(series.warnings) + ((f"failover: {note}",) if len(attempts) > 1 else ())
            return replace(series, unit=unit, value_unit=unit, warnings=warnings)

        return _finalize


def default_macro_client(
    sources=None, max_attempts: int = 3, http_get=None, timeout: float = 25.0
) -> MacroClient:
    """Primary macro entry: a :class:`MacroClient` over the default no-key chain.

    Order: World Bank -> IMF DataMapper -> DBnomics. FRED/BEA/BLS-v2 are optional
    BYOK and excluded from this default chain.
    """
    return MacroClient(sources=sources, max_attempts=max_attempts, http_get=http_get, timeout=timeout)


def get_indicator(
    country_iso3: str,
    indicator,
    *,
    sources=None,
    max_attempts: int = 3,
    http_get=None,
    timeout: float = 25.0,
) -> IndicatorSeries:
    """Convenience: one-shot canonical macro indicator over the default chain."""
    return default_macro_client(
        sources=sources, max_attempts=max_attempts, http_get=http_get, timeout=timeout
    ).get_indicator(country_iso3, indicator)
