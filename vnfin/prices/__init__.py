"""vnfin.prices — equity (stock) OHLCV price history, the first-class price namespace.

This package is the coherent, one-obvious-entry facade for the **prices** domain. It
re-exports the existing price models and the failover client/factory that historically
lived at the top level of :mod:`vnfin`, and adds the standard facade verbs shared by
every domain:

* :func:`client` — build the primary domain entry (a :class:`FailoverPriceClient` over
  the default provider-adjusted broker chain). This is the standard ``<domain>.client()``
  factory used across the library.
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

from ..client import FailoverPriceClient
from ..models import (
    AdjustmentPolicy,
    Interval,
    PriceBar,
    PriceHistory,
    SourceAttempt,
)


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
    return client(max_attempts=max_attempts, http_get=http_get, timeout=timeout).get_history(
        symbol, interval, start, end
    )


__all__ = [
    "AdjustmentPolicy",
    "Interval",
    "PriceBar",
    "PriceHistory",
    "SourceAttempt",
    "FailoverPriceClient",
    "client",
    "history",
]
