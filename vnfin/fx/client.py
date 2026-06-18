"""FX failover client: open.er-api (primary) -> Vietcombank (failover).

Wraps the generic :class:`vnfin.failover.FailoverClient`. Both sources declare the same unit
family (``"VND-per-foreign-unit"``), so the construction-time unit-homogeneity guard accepts the
chain; an inverted/mismatched result is caught by ``reject`` (the two-layer guard described in
``docs/design/fx-sources.md``).
"""
from __future__ import annotations

from ..failover import FailoverClient
from .models import FXRate
from .open_er_api import OpenErApiFXSource
from .vietcombank import VietcombankFXSource


def default_fx_sources(http_get=None, timeout: float = 25.0):
    """The default FX chain: open.er-api (primary) then Vietcombank XML (failover)."""
    return [
        OpenErApiFXSource(http_get=http_get, timeout=timeout),
        VietcombankFXSource(http_get=http_get, timeout=timeout),
    ]


def _reject(result) -> str | None:
    if result is None:
        return "empty result"
    if not isinstance(result, FXRate):
        return f"unexpected result type {type(result).__name__}"
    if result.quote != "VND":
        return f"quote {result.quote!r} != VND"
    if result.unit != f"VND per 1 {result.base}":
        return f"unit {result.unit!r} != canonical 'VND per 1 {result.base}'"
    if not (result.rate > 0):
        return f"non-positive rate {result.rate!r}"
    return None


class FailoverFXClient:
    """Sequential FX failover over a homogeneous (VND-per-foreign-unit) source chain."""

    def __init__(self, sources, *, max_attempts: int = 3):
        self._engine = FailoverClient(
            sources,
            operation=lambda src, base, quote="VND": src.get_rate(base, quote),
            reject=_reject,
            unit_of=lambda src: getattr(src, "unit", None),
            max_attempts=max_attempts,
        )

    @property
    def sources(self):
        return self._engine.sources

    def get_rate(self, base: str, quote: str = "VND") -> FXRate:
        return self._engine.run(base, quote)


def default_fx_client(http_get=None, timeout: float = 25.0, max_attempts: int = 3) -> FailoverFXClient:
    return FailoverFXClient(
        default_fx_sources(http_get=http_get, timeout=timeout), max_attempts=max_attempts
    )
