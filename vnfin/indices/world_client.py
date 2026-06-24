"""World/US equity-index failover client + ``world()`` accessor (#177, extended #193).

A thin specialization of the domain-agnostic :class:`vnfin.failover.FailoverClient`
(mirroring :class:`vnfin.gold.failover.FailoverGoldClient`) that wires the two
world-index sources — :class:`~vnfin.indices.world_sources.AlphaVantageIndexSource`
(PRIMARY, BYOK; 5 allowlisted symbols, all USD US-listed ETFs) and
:class:`~vnfin.indices.world_sources.StooqIndexSource` (FALLBACK, keyless, ^SPX
index points) — into one disclosed-failover chain that returns the shared
:class:`~vnfin.models.PriceHistory`.

**Coverage (#193):** ``SPY``→SPY and ``QQQ``→QQQ are direct; ``^N225``→EWJ,
``^SSEC``→FXI, ``^STI``→EWS are loudly-labeled USD ETF proxies (the result carries
both ``proxy_for`` and a ``proxy_substitution`` warning). **Keyless reliability
(#193):** with no key + a walled keyless fallback, ``get_history`` raises
:class:`~vnfin.exceptions.MissingKey` (naming ``ALPHAVANTAGE_API_KEY`` + the symbol),
the actionable config signal; ``AllSourcesFailed`` is reserved for a key-set-but-AV-failed
chain.

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

from ..exceptions import AllSourcesFailed, InvalidData, MissingKey
from ..failover import FailoverClient
from ..models import Interval, PriceHistory
from .world_sources import (
    SPX_VALUE_UNIT,
    SPY_VALUE_UNIT,
    SUPPORTED_WORLD_SYMBOLS,
    AlphaVantageIndexSource,
    StooqIndexSource,
    world_index_spec,
)

# The default/forward-compat symbol. The full supported set is now
# ``SUPPORTED_WORLD_SYMBOLS`` (SPY, QQQ, ^N225, ^SSEC, ^STI) — see #193. ``symbol``
# stays a defaulted param (default SPY) for the common case + forward compat.
SUPPORTED_SYMBOL = "SPY"
_SUPPORTED_SET_REPR = ", ".join(repr(s) for s in SUPPORTED_WORLD_SYMBOLS)

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
        # The requested symbol for the in-flight call. ``get_history`` sets this before
        # ``self._engine.run(...)`` so the operation/capability/failure closures fetch
        # the per-symbol AV ticker (QQQ→QQQ, ^N225→EWJ, ...) instead of a pinned SPY.
        self._requested_symbol = SUPPORTED_SYMBOL
        self._engine = FailoverClient(
            list(sources),
            operation=lambda src, start, end, interval: src.get_history(
                self._requested_symbol, start, end, interval=interval
            ),
            capability=lambda src, start, end, interval: src.supports(self._requested_symbol),
            # Disclosed single-source pick (NOT a merge): do not enforce unit/currency
            # homogeneity — returning None for every source disables the guard.
            unit_of=lambda src: None,
            provenance_of=lambda hist: getattr(hist, "source", None),
            max_attempts=max_attempts,
            failure_factory=lambda attempts, start, end, interval: AllSourcesFailed(
                self._requested_symbol, getattr(interval, "value", str(interval)), attempts
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
        self._requested_symbol = canonical
        try:
            hist = self._engine.run(start, end, interval)
        except AllSourcesFailed:
            # MissingKey vs AllSourcesFailed clean branch (#193): if NO source has a key
            # (the BYOK AV primary is unconfigured) AND the chain still failed (the
            # keyless fallback is walled), this is an actionable config error, not a
            # generic all-sources failure. ``from None`` keeps the message trail-free
            # (the #157 lesson). When a key WAS set, re-raise AllSourcesFailed verbatim.
            if not any(getattr(s, "has_key", False) for s in self.sources):
                raise MissingKey(canonical) from None
            raise
        if hist.symbol != canonical:
            hist = replace(hist, symbol=canonical)
        return hist

    def _finalize(self, hist, attempts, start, end, interval) -> PriceHistory:
        warnings = (
            tuple(hist.warnings)
            + self._substitution_warnings(hist)
            + self._proxy_warnings(hist)
        )
        return replace(hist, attempts=attempts, warnings=warnings)

    @staticmethod
    def _proxy_warnings(hist) -> tuple[str, ...]:
        """Mechanical ``proxy_substitution`` warning when a USD ETF proxy is served.

        Mirrors ``_substitution_warnings``: keyed on the served result carrying a
        ``proxy_for`` (the caller asked for a raw index, e.g. ``^N225``, but a US-listed
        USD ETF, e.g. ``EWJ``, was served). Built from the symbol's spec so the loud
        human-readable detail names the asked index, the served ticker, and the embedded
        FX pair. A direct (non-proxy) result (``proxy_for is None``) emits nothing.
        """
        proxy_for = getattr(hist, "proxy_for", None)
        if not proxy_for:
            return ()
        spec = world_index_spec(proxy_for)
        return (
            f"proxy_substitution: requested {proxy_for} ({spec.index_name}) served as "
            f"{spec.av_ticker} (USD ETF proxy, not the raw {spec.index_name} index; "
            f"embeds {spec.fx_pair} FX) — not a faithful tracker",
        )

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
    """World/US equity index daily history via a 2-source failover chain (#177, #193).

    Supported symbols: ``SPY``, ``QQQ``, ``^N225``, ``^SSEC``, ``^STI`` — ALL served in
    USD via Alpha Vantage (US-listed ETFs). ``SPY``/``QQQ`` are direct; ``^N225``/
    ``^SSEC``/``^STI`` are **loudly-labeled USD ETF proxies** (``EWJ``/``FXI``/``EWS``):
    the result carries ``proxy_for=<asked>`` AND a ``proxy_substitution`` warning. These
    proxies embed USD/local FX and are NOT faithful trackers of the raw local-currency
    index. Any unsupported symbol raises a clear :class:`~vnfin.exceptions.InvalidData`
    enumerating the supported set.

    **v1 series are PRICE-RETURN, not total-return** (dividends are not reinvested) —
    material over 10–25y. The returned :class:`~vnfin.models.PriceHistory` self-discloses
    its instrument via ``source`` / ``value_unit`` / ``provider_symbol`` / ``proxy_for``.
    When the keyless or throttled primary forces the ^SPX (index points) Stooq fallback,
    the result carries a mechanical ``fallback_instrument_served`` warning (SPY and ^SPX
    magnitudes differ ~10x — rebase before comparing).

    With **no key** configured and the keyless fallback walled (e.g. Stooq's anti-bot
    challenge from a datacenter IP), raises :class:`~vnfin.exceptions.MissingKey` naming
    ``ALPHAVANTAGE_API_KEY`` + the symbol. This is purely the world-index path; the VN
    HOSE/HNX ``index_history`` chain is untouched.
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
            "world index symbol must be a non-empty string; supported: "
            f"{_SUPPORTED_SET_REPR}"
        )
    canonical = symbol.strip().upper()
    if canonical not in SUPPORTED_WORLD_SYMBOLS:
        raise InvalidData(
            f"world index {symbol!r} not supported; supported: {_SUPPORTED_SET_REPR} "
            "(US ETFs in USD; the three ^-prefixed Asian symbols are loudly-labeled "
            "USD ETF proxies, not the raw local-currency index)"
        )
    return canonical
