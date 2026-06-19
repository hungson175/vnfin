"""FX failover client: open.er-api (primary) -> Vietcombank (failover).

Wraps the generic :class:`vnfin.failover.FailoverClient`. Both sources declare the same unit
family (``"VND-per-foreign-unit"``), so the construction-time unit-homogeneity guard accepts the
chain. A wrong-base / inverted / non-positive result is caught by the **request-aware** guard in
``_operation`` (it validates the returned base/quote/unit/rate against the *requested* base and
raises so failover moves on) — the two-layer guard described in ``docs/design/fx-sources.md``.
"""
from __future__ import annotations

import math
import re
import datetime as dt

from ..exceptions import InvalidData
from ..failover import FailoverClient
from .models import FXRate
from .open_er_api import OpenErApiFXSource
from .vietcombank import VietcombankFXSource

_ISO4217 = re.compile(r"[A-Za-z]{3}")


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
    if isinstance(result.rate, bool) or not isinstance(result.rate, (int, float)):
        return f"malformed rate type {type(result.rate).__name__}"
    if not math.isfinite(result.rate) or not (result.rate > 0):
        return f"non-positive or non-finite rate {result.rate!r}"

    # Issue #83: as_of_utc must be a timezone-aware UTC datetime.
    if not isinstance(result.as_of_utc, dt.datetime) or result.as_of_utc.tzinfo is None:
        return f"as_of_utc must be a timezone-aware datetime, got {result.as_of_utc!r}"
    if result.as_of_utc.tzinfo is not dt.timezone.utc:
        return f"as_of_utc must be UTC, got timezone {result.as_of_utc.tzinfo!r}"

    # Issue #72: bid/ask metadata validation.
    if result.bid is not None:
        if isinstance(result.bid, bool) or not isinstance(result.bid, (int, float)):
            return f"malformed bid type {type(result.bid).__name__}"
        if not math.isfinite(result.bid) or not (result.bid > 0):
            return f"non-positive or non-finite bid {result.bid!r}"
    if result.ask is not None:
        if isinstance(result.ask, bool) or not isinstance(result.ask, (int, float)):
            return f"malformed ask type {type(result.ask).__name__}"
        if not math.isfinite(result.ask) or not (result.ask > 0):
            return f"non-positive or non-finite ask {result.ask!r}"
    if result.bid is not None and result.ask is not None and result.ask < result.bid:
        return f"ask {result.ask!r} < bid {result.bid!r}"
    if (
        result.bid is not None
        and result.ask is not None
        and not (result.bid <= result.rate <= result.ask)
    ):
        return f"rate {result.rate!r} not in bid-ask spread [{result.bid!r}, {result.ask!r}]"
    return None


def _validate_ccy(code, name="base") -> str:
    """Issue #9: validate FX currency codes before entering failover."""
    if not isinstance(code, str) or not _ISO4217.fullmatch(code.strip()):
        raise InvalidData(f"fx: invalid ISO-4217 {name} currency code {code!r}")
    return code.strip().upper()


def _operation(src, base, quote="VND"):
    req_base = _validate_ccy(base, "base")
    req_quote = _validate_ccy(quote, "quote")
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
            # Issue #126: reject an FXRate whose stamped source does not match the
            # source that produced it (provenance/audit integrity); never relabel.
            provenance_of=lambda rate: getattr(rate, "source", None),
            max_attempts=max_attempts,
        )

    @property
    def sources(self):
        return self._engine.sources

    def get_rate(self, base: str, quote: str = "VND") -> FXRate:
        # Issue #9: validate inputs before failover so malformed requests raise
        # InvalidData, not AllSourcesFailed.
        _validate_ccy(base, "base")
        _validate_ccy(quote, "quote")
        return self._engine.run(base, quote)


def default_fx_client(http_get=None, timeout: float = 25.0, max_attempts: int = 3) -> FailoverFXClient:
    return FailoverFXClient(
        default_fx_sources(http_get=http_get, timeout=timeout), max_attempts=max_attempts
    )
