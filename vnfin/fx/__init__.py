"""FX domain: daily/current foreign-exchange reference rates vs VND (no-key).

Canonical unit: **VND per 1 unit of the base currency** (e.g. USD/VND ≈ 26,000). Spot/current
only — no history in v0.2 (see ``docs/design/fx-sources.md``). Standard facade verbs:

    import vnfin
    r  = vnfin.fx.get_rate("USD")          # one-shot FXRate (failover chain)
    c  = vnfin.fx.client()                 # FailoverFXClient (open.er-api -> Vietcombank)
    s  = vnfin.fx.source()                 # OpenErApiFXSource (primary only)

Sources are clean-room, no-key: open.er-api (primary) + Vietcombank XML (failover). Both quote
VND-per-foreign-unit, so the unit-homogeneity guard is satisfied. Data is runtime-fetch only;
open.er-api prohibits redistribution and Vietcombank is "for reference only" — do not bundle.
"""
from __future__ import annotations

from .base import FXSource
from .client import (
    FailoverFXClient,
    default_fx_client,
    default_fx_sources,
)
from .models import FXRate
from .open_er_api import OpenErApiFXSource
from .vietcombank import VietcombankFXSource

__all__ = [
    "FXRate",
    "FXSource",
    "OpenErApiFXSource",
    "VietcombankFXSource",
    "FailoverFXClient",
    "default_fx_sources",
    "default_fx_client",
    "client",
    "source",
    "get_rate",
]


def source(http_get=None, timeout: float = 25.0) -> OpenErApiFXSource:
    """Primary FX entry: :class:`OpenErApiFXSource` (open.er-api, no-key)."""
    return OpenErApiFXSource(http_get=http_get, timeout=timeout)


def client(http_get=None, timeout: float = 25.0, max_attempts: int = 3) -> FailoverFXClient:
    """Standard ``<domain>.client(...)`` — the open.er-api -> Vietcombank failover chain (VND)."""
    return default_fx_client(http_get=http_get, timeout=timeout, max_attempts=max_attempts)


def get_rate(base: str, quote: str = "VND", *, http_get=None, timeout: float = 25.0) -> FXRate:
    """One-shot convenience: current ``base``/``quote`` rate via the failover chain."""
    return client(http_get=http_get, timeout=timeout).get_rate(base, quote)
