"""Exception hierarchy for vnfin.

`SourceError` and its subclasses are the failover triggers: when a single source
raises one, `FailoverPriceClient` records the attempt and moves to the next source.
`UnsupportedInterval` is a capability signal (not a failover trigger) — the client
filters it out before calling a source.
"""
from __future__ import annotations


class VnfinError(Exception):
    """Base class for all vnfin errors."""


class SourceError(VnfinError):
    """A recoverable single-source failure that should trigger failover."""


class SourceUnavailable(SourceError):
    """Transport/network failure reaching a source."""


class EmptyData(SourceError):
    """Source responded but returned no usable rows for the request."""


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
