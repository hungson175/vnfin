"""vnfin.prices — equity (stock) OHLCV price history, the first-class price namespace.

This package is the coherent, one-obvious-entry facade for the **prices** domain. It
re-exports the existing price models and the failover client/factory that historically
lived at the top level of :mod:`vnfin`, and adds the standard facade verbs shared by
every domain:

* :func:`client` — build the primary domain entry (a :class:`FailoverPriceClient` over
  the default provider-adjusted broker chain). This is the standard ``<domain>.client()``
  factory used across the library.
* :func:`source` — build the PRIMARY single price source (no failover): the first of
  the default chain, currently :class:`~vnfin.sources.ssi.SSIiBoardSource`. This is the
  standard ``<domain>.source()`` factory.
* :func:`history` — one-shot convenience: fetch a :class:`PriceHistory` over the default
  chain without first holding a client.

Nothing here changes price behavior — it is composition over the existing
:mod:`vnfin.client`, :mod:`vnfin.models`, and :mod:`vnfin.sources` stack. Equity prices
are quoted in **VND** (see ``docs/units.md``).

Both ``start`` and ``end`` dates are **required** (see :func:`history`); omitting
either raises :class:`~vnfin.exceptions.InvalidData` up front rather than leaking a
raw ``TypeError``.

Example::

    import vnfin
    from datetime import date

    c = vnfin.prices.client()
    hist = c.get_history("FAKECORP", start=date(2024, 1, 1), end=date(2024, 6, 30))  # PriceHistory, VND
    # or one-shot:
    hist = vnfin.prices.history("FAKECORP", start=date(2024, 1, 1), end=date(2024, 6, 30))
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from .._resample import apply_interval
from ..client import FailoverPriceClient
from ..models import (
    AdjustmentPolicy,
    Interval,
    PriceBar,
    PriceHistory,
    SourceAttempt,
)
from ..sources.ssi import SSIiBoardSource


def client(max_attempts: int = 3, http_get=None, timeout: float = 25.0) -> FailoverPriceClient:
    """Primary prices entry: a :class:`FailoverPriceClient` over the default broker chain.

    Order: SSI -> VNDirect -> VPS -> Pinetree (KIS excluded; its series is MIXED).
    Identical to the long-standing :func:`vnfin.default_client`; kept here so every
    domain has a consistent ``<domain>.client(...)`` factory.
    """
    from ..sources.registry import default_sources

    return FailoverPriceClient(
        default_sources(http_get=http_get, timeout=timeout), max_attempts=max_attempts
    )


def source(http_get=None, timeout: float = 25.0) -> SSIiBoardSource:
    """Primary prices SOURCE: the single first adapter of the default chain (no failover).

    Standard ``<domain>.source(...)`` factory — returns the PRIMARY broker source,
    currently :class:`~vnfin.sources.ssi.SSIiBoardSource` (first of
    :func:`~vnfin.sources.registry.default_sources`). Use ``.get_history(...)`` on it,
    or prefer :func:`client` / :func:`history` for the failover chain. Equity prices
    are quoted in **VND**.
    """
    return SSIiBoardSource(http_get=http_get, timeout=timeout)


def history(
    symbol: str,
    interval: Interval = Interval.D1,
    start: Optional[date] = None,
    end: Optional[date] = None,
    *,
    max_attempts: int = 3,
    http_get=None,
    timeout: float = 25.0,
) -> PriceHistory:
    """Convenience: one-shot equity price history over the default failover chain.

    ``start`` and ``end`` are **required** (a ``date`` or ``datetime``) and are
    validated before any source call. Omitting either, passing a non-date, or
    passing ``start > end`` raises a stable :class:`~vnfin.exceptions.InvalidData`
    (a ``VnfinError``) — never a raw ``TypeError``.
    """
    c = client(max_attempts=max_attempts, http_get=http_get, timeout=timeout)
    return apply_interval(
        interval, start, end, lambda: c.get_history(symbol, Interval.D1, start, end)
    )


__all__ = [
    "AdjustmentPolicy",
    "Interval",
    "PriceBar",
    "PriceHistory",
    "SourceAttempt",
    "FailoverPriceClient",
    "SSIiBoardSource",
    "client",
    "source",
    "history",
]
