"""FX failover client: open.er-api (primary) -> Vietcombank (failover).

Wraps the generic :class:`vnfin.failover.FailoverClient`. Both sources declare the same unit
family (``"VND-per-foreign-unit"``), so the construction-time unit-homogeneity guard accepts the
chain. A wrong-base / inverted / non-positive result is caught by the **request-aware** guard in
``_operation`` (it validates the returned base/quote/unit/rate against the *requested* base and
raises so failover moves on) — the two-layer guard described in ``docs/design/fx-sources.md``.
"""
from __future__ import annotations

from ..exceptions import InvalidData
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


def _validate(result, req_base: str, req_quote: str) -> str | None:
    """Request-aware result guard: the returned rate must answer THIS request, in the
    canonical unit, with a positive value. (`reject` only sees the result, so this runs
    inside the operation where the requested base/quote are in scope.)"""
    if not isinstance(result, FXRate):
        return f"unexpected result type {type(result).__name__}"
    if result.base != req_base:
        return f"base {result.base!r} != requested {req_base!r}"
    if result.quote != req_quote:
        return f"quote {result.quote!r} != requested {req_quote!r}"
    if result.unit != f"{req_quote} per 1 {req_base}":
        return f"unit {result.unit!r} != '{req_quote} per 1 {req_base}'"
    if not (result.rate > 0):
        return f"non-positive rate {result.rate!r}"
    return None


def _operation(src, base, quote="VND"):
    req_base = base.strip().upper() if isinstance(base, str) else base
    req_quote = quote.strip().upper() if isinstance(quote, str) else quote
    result = src.get_rate(base, quote)
    reason = _validate(result, req_base, req_quote)
    if reason:
        # raise a SourceError so failover records the attempt and moves to the next source
        raise InvalidData(f"{getattr(src, 'name', '?')}: {reason}")
    return result


class FailoverFXClient:
    """Sequential FX failover over a homogeneous (VND-per-foreign-unit) source chain."""

    def __init__(self, sources, *, max_attempts: int = 3):
        self._engine = FailoverClient(
            sources,
            operation=_operation,
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
