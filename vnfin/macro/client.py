"""Macro failover client + default no-key chain.

Wraps the generic :class:`vnfin.failover.FailoverClient` for the macro domain,
mirroring how :class:`vnfin.client.FailoverPriceClient` wraps it for prices. The
chain serves the SAME logical :class:`~vnfin.macro.indicators.MacroIndicator`
across providers via the canonical indicator registry.

Unit safety (B6/B7) — the macro client does TWO things before the generic engine
ever runs:

1. **Pre-filter by unit** (:func:`~vnfin.macro.indicators.eligible_sources`):
   keep only sources whose declared unit for the requested indicator equals the
   canonical unit. This means the surviving chain is already unit-homogeneous, so
   the default GDP/CPI/percent chains never raise ``UnitMismatchError`` (the old
   bug) and a source that would emit a noncanonical unit (e.g. IMF GDP in
   ``USD bn`` vs canonical ``current US$``) is dropped up front rather than having
   its values relabelled.
2. **Validate on finalize** (not relabel): the result is checked to already carry
   the canonical unit; it is never blindly stamped over a different unit.

The generic :class:`vnfin.failover.FailoverClient` is built only AFTER step 1, and
its unit-homogeneity guard remains as a structural backstop (it can only ever see
already-homogeneous sources).

Default no-key chain (order): World Bank -> IMF DataMapper -> DBnomics. FRED is the
only optional BYOK source and is deliberately excluded from this default chain.

Capability skip: a source that does not map the requested indicator is skipped
without a network call (it does not count against ``max_attempts``), exactly like
the price client skips a source that does not support an interval.
"""
from __future__ import annotations

import math
from dataclasses import replace
from datetime import date, datetime

from ..exceptions import AllSourcesFailed, InvalidData, UnitMismatchError
from ..failover import FailoverClient
from ..validation import validate_country_iso3
from .dbnomics import DBnomicsSource
from .imf import IMFDataMapperSource
from .indicators import (
    MacroIndicator,
    canonical_currency,
    canonical_indicator_code,
    canonical_indicator_name,
    canonical_unit,
    eligible_sources,
    normalize_indicator,
    validate_indicator_values,
)
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
        source's unit *for this indicator*. Validates inputs up front; unknown
        indicators and malformed countries both raise ``InvalidData`` before any
        source is contacted.
        """
        country = validate_country_iso3(country_iso3)
        ind = normalize_indicator(indicator, _invalid_to_valueerror=False)

        # B6/B7: filter to sources whose declared unit == the canonical unit for
        # this indicator BEFORE building the engine. The surviving chain is
        # unit-homogeneous (so default GDP/CPI/percent never raise
        # UnitMismatchError) and no value can be relabelled into a foreign unit.
        sources = eligible_sources(self._sources, ind)
        if not sources:
            # No source can serve this indicator in the canonical unit; this is a
            # capability outcome, not a network failure -> AllSourcesFailed (no attempts).
            raise AllSourcesFailed(f"{country}/{ind.value}", None, ())

        engine = FailoverClient(
            sources,
            operation=lambda src, country, i: _fetch(src, country, i),
            capability=lambda src, country, i: _capable(src, country, i),
            reject=self._reject_reason_for(ind),
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
        return engine.run(country, ind)

    @staticmethod
    def _reject_reason_for(indicator):
        unit = canonical_unit(indicator)
        currency = canonical_currency(indicator)

        def _reject_reason(series, country, i) -> str | None:
            # Issue #125: a malformed (non-typed) result container must be a
            # recorded rejected attempt, not a raw AttributeError from
            # len(series.points).
            if not isinstance(series, IndicatorSeries):
                return f"unexpected result type {type(series).__name__}"
            if len(series.points) == 0:
                return "empty result"

            # Issue #78: reject returned identity that contradicts the request.
            if series.country != country:
                return (
                    f"country mismatch: source {series.source!r} returned "
                    f"country {series.country!r} but requested {country!r}"
                )

            # Issue #71: reject conflicting explicit unit/currency metadata.
            got_unit = series.unit or ""
            if got_unit and got_unit != unit:
                return (
                    f"unit mismatch: source {series.source!r} returned "
                    f"unit {got_unit!r} but the canonical unit is {unit!r}"
                )
            got_value_unit = series.value_unit or ""
            if got_value_unit and got_value_unit != unit:
                return (
                    f"value_unit mismatch: source {series.source!r} returned "
                    f"value_unit {got_value_unit!r} but the canonical unit is {unit!r}"
                )
            got_currency = series.currency
            if got_currency is not None and got_currency != currency:
                return (
                    f"currency mismatch: source {series.source!r} returned "
                    f"currency {got_currency!r} but the canonical currency is {currency!r}"
                )

            # Issue #78 follow-up: returned series must answer the requested indicator.
            if not series.indicator_code:
                return f"indicator_code is empty for {indicator.value}"
            if not series.indicator_name:
                return f"indicator_name is empty for {indicator.value}"
            for other in MacroIndicator:
                if other == indicator:
                    continue
                if series.indicator_code == canonical_indicator_code(other):
                    return (
                        f"indicator_code mismatch: source {series.source!r} returned "
                        f"{series.indicator_code!r} (canonical code for {other.value}) "
                        f"but requested {indicator.value}"
                    )
                if series.indicator_name == canonical_indicator_name(other):
                    return (
                        f"indicator_name mismatch: source {series.source!r} returned "
                        f"{series.indicator_name!r} (canonical name for {other.value}) "
                        f"but requested {indicator.value}"
                    )

            # Issue #123: each point key must be a plain calendar ``date``, the
            # documented IndicatorSeries contract. ``datetime`` is rejected
            # explicitly because it subclasses ``date`` but carries intraday/tz
            # meaning a macro observation must not have; ``str``/``int``/``None``
            # are rejected outright. Done before the ascending-order check so a
            # malformed key cannot leak a raw TypeError from the ``<=`` compare.
            for d, _v in series.points:
                if not isinstance(d, date) or isinstance(d, datetime):
                    return (
                        f"malformed point date {d!r} from source {series.source!r}: "
                        "expected a plain datetime.date"
                    )

            # Issue #95: points must be strictly ascending by date.
            prev_date = None
            for d, _v in series.points:
                if prev_date is not None and d <= prev_date:
                    return (
                        f"points are not strictly ascending by date: "
                        f"{d} <= {prev_date} from source {series.source!r}"
                    )
                prev_date = d

            # Issue #96: every point value must be finite (no NaN/inf).
            for d, v in series.points:
                if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                    return (
                        f"non-finite value {v!r} at {d} from source {series.source!r}"
                    )

            # Issue #86: level indicators must be positive; unemployment bounded.
            try:
                validate_indicator_values(indicator, list(series.points), series.source)
            except InvalidData as exc:
                return str(exc)
            return None

        return _reject_reason

    @staticmethod
    def _finalize_for(indicator):
        unit = canonical_unit(indicator)
        currency = canonical_currency(indicator)

        def _finalize(series, attempts, country, i) -> IndicatorSeries:
            # B7: validate — never relabel a foreign unit. Because sources were
            # pre-filtered to the canonical unit, the result must already match;
            # if a source emitted an empty/placeholder unit we pin the canonical
            # one, but a genuinely DIFFERENT unit is a contract violation we refuse
            # rather than silently overwrite.
            got = series.unit or ""
            if got and got != unit:
                raise UnitMismatchError(
                    f"macro {getattr(i, 'value', i)}: source {series.source!r} returned "
                    f"unit {got!r} but the canonical unit is {unit!r}; refusing to relabel"
                )
            note = "; ".join(f"{a.name}:{a.reason}" for a in attempts)
            warnings = tuple(series.warnings) + ((f"failover: {note}",) if len(attempts) > 1 else ())
            return replace(
                series,
                unit=unit,
                value_unit=unit,
                currency=currency,
                warnings=warnings,
            )

        return _finalize


def default_macro_client(
    sources=None, max_attempts: int = 3, http_get=None, timeout: float = 25.0
) -> MacroClient:
    """Primary macro entry: a :class:`MacroClient` over the default no-key chain.

    Order: World Bank -> IMF DataMapper -> DBnomics. FRED is the only optional BYOK
    source and is excluded from this default chain.
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
