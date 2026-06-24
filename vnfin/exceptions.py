"""Exception hierarchy for vnfin.

`SourceError` and its subclasses are the failover triggers: when a single source
raises one, `FailoverPriceClient` records the attempt and moves to the next source.
`UnsupportedInterval` is a capability signal (not a failover trigger) — the client
filters it out before calling a source.
"""
from __future__ import annotations

__all__ = [
    "VnfinError",
    "SourceError",
    "SourceUnavailable",
    "EmptyData",
    "StaleData",
    "InvalidData",
    "UnsupportedInterval",
    "AdjustmentPolicyError",
    "UnitMismatchError",
    "AllSourcesFailed",
    "MissingKey",
]


class VnfinError(Exception):
    """Base class for all vnfin errors."""


class SourceError(VnfinError):
    """A recoverable single-source failure that should trigger failover."""


class SourceUnavailable(SourceError):
    """Transport/network failure reaching a source."""


class EmptyData(SourceError):
    """Source responded but returned no usable rows for the request."""


class StaleData(EmptyData):
    """Data exists but ends before the requested window (stale/closed feed).

    A subclass of :class:`EmptyData` so existing ``except EmptyData`` /
    ``except SourceError`` callers still catch it, while the distinct type and
    message name the gap (the source's latest observation predates the requested
    window start) — distinguishable from a genuinely empty / pre-inception result.
    """


class InvalidData(SourceError):
    """Source returned malformed or self-inconsistent data."""


class UnsupportedInterval(VnfinError):
    """The requested interval is not offered by this source (capability signal)."""


class AdjustmentPolicyError(VnfinError):
    """The adjustment policy of the returned series is unknown or non-homogeneous."""


class UnitMismatchError(VnfinError):
    """A failover chain was configured with sources that emit different units.

    Raised by the unit-homogeneity guard when two sources in one failover client
    declare different unit/currency/scale values — failing over between them could
    silently mix scales (e.g. VND vs index points, or x1000 vs x1 feeds).
    """


class AllSourcesFailed(VnfinError):
    """Every attempted source failed. Carries the per-source diagnostics."""

    def __init__(self, symbol, interval, attempts):
        self.symbol = symbol
        self.interval = interval
        self.attempts = attempts
        iv = getattr(interval, "value", interval)
        reasons = "; ".join(f"{a.name}:{a.reason}" for a in attempts) or "no sources attempted"
        super().__init__(f"all sources failed for {symbol} {iv} -> {reasons}")


class MissingKey(VnfinError):
    """A BYOK source needs an API key that is not set, and no keyless fallback could
    serve the request.

    Distinct from :class:`AllSourcesFailed`: that means a key WAS configured but every
    source still failed (throttle/network/anti-bot). ``MissingKey`` is the cleaner,
    actionable config signal — no API key anywhere AND the keyless fallback is walled
    (e.g. Stooq's anti-bot challenge from a datacenter IP). The message names the env
    var and the symbol; it deliberately carries **no** per-source attempt trail (the
    #157 lesson — do not fold the aggregated failover trail onto a public message).
    """

    def __init__(self, symbol, env_var="ALPHAVANTAGE_API_KEY"):
        self.symbol = symbol
        self.env_var = env_var
        super().__init__(
            f"world index {symbol}: no {env_var} configured and no keyless source is "
            f"reachable from this environment; set {env_var} or pass api_key= to use "
            "world-index data server-side"
        )
