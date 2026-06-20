"""World/US equity-index (S&P 500) failover client + ``world()`` accessor (#177).

A thin specialization of the domain-agnostic :class:`vnfin.failover.FailoverClient`
(mirroring :class:`vnfin.gold.failover.FailoverGoldClient`) that wires the two
world-index sources — :class:`~vnfin.indices.world_sources.AlphaVantageIndexSource`
(PRIMARY, BYOK, SPY USD/share) and
:class:`~vnfin.indices.world_sources.StooqIndexSource` (FALLBACK, keyless, ^SPX
index points) — into one disclosed-failover chain that returns the shared
:class:`~vnfin.models.PriceHistory`.

This chain is INTENTIONALLY cross-instrument and INTENTIONALLY *not*
unit-homogeneous: SPY (USD/share) and ^SPX (index points) are different
instruments. Only ONE leg is ever served per call (a disclosed failover-pick, not
a merge), so the engine's unit-homogeneity guard is disabled (``unit_of`` returns
``None`` for every source — see #157's "guards are for merges, not disclosed
single-source picks"). The served result self-discloses via ``source`` +
``value_unit`` + ``provider_symbol``.

**Required never-silent warning.** Because the two legs' magnitudes differ ~10x, a
caller that ignores ``value_unit`` and mixes them un-rebased makes a 10x error.
Therefore whenever the ^SPX (Stooq) leg is served *instead of* the requested SPY
(covering BOTH the AV-throttle fallback path AND the keyless-skip path), a
mechanical ``fallback_instrument_served`` warning is appended in ``finalize`` (the
failover seam, so it survives like #179's ``series_end_gap``). The SPY-primary
success path carries no such warning.
"""
from __future__ import annotations

import os
from dataclasses import replace
from typing import Optional

from ..exceptions import AllSourcesFailed, InvalidData
from ..failover import FailoverClient
from ..models import Interval, PriceHistory
from .world_sources import (
    SPX_VALUE_UNIT,
    SPY_VALUE_UNIT,
    AlphaVantageIndexSource,
    StooqIndexSource,
)

# v1 supports the S&P 500 only, fetched as the SPY ETF proxy. ``symbol`` is kept as
# a defaulted param for forward compat (future world indices), not because v1
# accepts other symbols.
SUPPORTED_SYMBOL = "SPY"

_FALLBACK_WARNING = (
    "fallback_instrument_served: requested SPY (USD/share, S&P 500 proxy) "
    "unavailable; served Stooq ^SPX index points (~10x different magnitude) "
    "— rebase before comparing"
)


def default_world_index_sources(
    *,
    api_key: Optional[str] = None,
    http_get=None,
    timeout: float = 25.0,
):
    """Default world-index source chain: ``[AlphaVantage (BYOK), Stooq]``.

    Alpha Vantage is always constructed (it reads ``api_key``/``ALPHAVANTAGE_API_KEY``
    itself); with no key it is keyless-incapable (``supports()`` is ``False``) and
    the failover engine skips it BEFORE any network call, so Stooq serves directly.
    """
    av = AlphaVantageIndexSource(api_key=api_key, http_get=http_get, timeout=timeout)
    stooq = StooqIndexSource(http_get=http_get, timeout=timeout)
    return [av, stooq]


class FailoverWorldIndexClient:
    """Try world-index sources in priority order until one serves a result.

    AV-throttle/keyless and Stooq anti-bot are all ``SourceUnavailable`` (best
    effort); the engine falls through and only raises ``AllSourcesFailed`` if BOTH
    are unavailable. Incapable (keyless AV) sources are skipped without a network
    call and do not count against ``max_attempts``. The unit-homogeneity guard is
    disabled for this disclosed cross-instrument chain.
    """

    def __init__(self, sources, *, max_attempts: int = 3):
        self._engine = FailoverClient(
            list(sources),
            operation=lambda src, start, end, interval: src.get_history(
                SUPPORTED_SYMBOL, start, end, interval=interval
            ),
            capability=lambda src, start, end, interval: src.supports(SUPPORTED_SYMBOL),
            # Disclosed single-source pick (NOT a merge): do not enforce unit/currency
            # homogeneity — returning None for every source disables the guard.
            unit_of=lambda src: None,
            provenance_of=lambda hist: getattr(hist, "source", None),
            max_attempts=max_attempts,
            failure_factory=lambda attempts, start, end, interval: AllSourcesFailed(
                SUPPORTED_SYMBOL, getattr(interval, "value", str(interval)), attempts
            ),
            finalize=self._finalize,
        )

    @property
    def sources(self):
        return self._engine.sources

    @property
    def max_attempts(self) -> int:
        return self._engine.max_attempts

    def get_history(
        self,
        symbol: str = SUPPORTED_SYMBOL,
        start=None,
        end=None,
        *,
        interval: Interval = Interval.D1,
    ) -> PriceHistory:
        canonical = _validate_symbol(symbol)
        hist = self._engine.run(start, end, interval)
        if hist.symbol != canonical:
            hist = replace(hist, symbol=canonical)
        return hist

    def _finalize(self, hist, attempts, start, end, interval) -> PriceHistory:
        warnings = tuple(hist.warnings) + self._substitution_warnings(hist)
        return replace(hist, attempts=attempts, warnings=warnings)

    @staticmethod
    def _substitution_warnings(hist) -> tuple[str, ...]:
        """Mechanical ``fallback_instrument_served`` warning when ^SPX is served.

        Keyed on the served leg being the Stooq/^SPX instrument (index points)
        rather than the requested SPY (USD/share). This covers BOTH substitution
        paths — AV throttle -> Stooq fallback, and keyless AV skipped -> Stooq
        served directly — since both substitute the requested SPY. The SPY-primary
        success path (source=alphavantage, USD/share) emits nothing.
        """
        served_spx = (
            getattr(hist, "source", None) == StooqIndexSource.NAME
            or getattr(hist, "value_unit", None) == SPX_VALUE_UNIT
            or getattr(hist, "provider_symbol", None) == "^SPX"
        )
        if served_spx:
            return (_FALLBACK_WARNING,)
        return ()


def default_world_index_client(
    sources=None,
    *,
    api_key: Optional[str] = None,
    http_get=None,
    timeout: float = 25.0,
    max_attempts: int = 3,
) -> FailoverWorldIndexClient:
    """Default world-index failover client (gold-style factory).

    Pass ``sources`` to inject a custom/synthetic chain; otherwise build the
    default ``[AlphaVantage (BYOK), Stooq]`` chain.
    """
    if sources is None:
        sources = default_world_index_sources(
            api_key=api_key, http_get=http_get, timeout=timeout
        )
    return FailoverWorldIndexClient(sources, max_attempts=max_attempts)


def world(
    symbol: str = SUPPORTED_SYMBOL,
    start=None,
    end=None,
    *,
    interval: Interval = Interval.D1,
    sources=None,
    api_key: Optional[str] = None,
    http_get=None,
    timeout: float = 25.0,
    max_attempts: int = 3,
) -> PriceHistory:
    """World/US equity index (S&P 500) daily history via a 2-source failover chain.

    v1 supports ``symbol="SPY"`` only (fetched as the SPY ETF, an S&P 500 proxy, on
    the Alpha Vantage primary; or the ^SPX index level on the Stooq fallback). Any
    other symbol raises a clear :class:`~vnfin.exceptions.InvalidData`.

    The returned :class:`~vnfin.models.PriceHistory` self-discloses its instrument
    via ``source`` / ``value_unit`` / ``provider_symbol``. When the keyless or
    throttled primary forces the ^SPX (index points) fallback, the result carries a
    mechanical ``fallback_instrument_served`` warning (SPY and ^SPX magnitudes
    differ ~10x — rebase before comparing). This is purely the world-index path; the
    VN HOSE/HNX ``index_history`` chain is untouched.
    """
    canonical = _validate_symbol(symbol)
    client = default_world_index_client(
        sources,
        api_key=api_key,
        http_get=http_get,
        timeout=timeout,
        max_attempts=max_attempts,
    )
    return client.get_history(canonical, start, end, interval=interval)


def _validate_symbol(symbol) -> str:
    if not isinstance(symbol, str) or not symbol.strip():
        raise InvalidData(
            f"world index symbol must be a non-empty string; only {SUPPORTED_SYMBOL!r} "
            "is supported in v1"
        )
    canonical = symbol.strip().upper()
    if canonical != SUPPORTED_SYMBOL:
        raise InvalidData(
            f"world index {symbol!r} not supported in v1; only {SUPPORTED_SYMBOL!r} "
            "(the S&P 500, fetched as the SPY ETF proxy / ^SPX index)"
        )
    return canonical
