"""High-level index client.

``IndexClient`` composes the existing ``FailoverPriceClient`` over index-aware UDF
sources (part a — index VALUE history) and wraps the SSI constituents source
(part b — membership). It deliberately does NOT modify the price sources; it builds
its own failover chain over index-specific adapters so index values stay in points.

Failover order for index values: VPS (deepest history, widest symbol set) -> SSI
(deep, enveloped) -> VNDIRECT (shallower, good cross-check). VPS is first because it
is the only source that serves UPCOM correctly and covers all sector indices.
"""
from __future__ import annotations

from datetime import date
from typing import Optional, Union

from ..client import FailoverPriceClient
from ..models import Interval, PriceHistory
from .models import IndexConstituents
from .sources import (
    IndexConstituentsSource,
    SSIIndexSource,
    VNDirectIndexSource,
    VPSIndexSource,
)

# Default index-value failover chain (deepest/widest first).
_DEFAULT_INDEX_SOURCE_CLASSES = (VPSIndexSource, SSIIndexSource, VNDirectIndexSource)


def default_index_sources(http_get=None, timeout: float = 25.0):
    """Instantiate the default index-value failover chain (values in points)."""
    return [c(http_get=http_get, timeout=timeout) for c in _DEFAULT_INDEX_SOURCE_CLASSES]


class IndexClient:
    """Stable API for VN market-index data.

    - ``index_history(symbol, start, end)`` -> ``PriceHistory`` with ``currency='points'``.
    - ``constituents(index)`` -> ``IndexConstituents`` (membership; no weights).
    """

    def __init__(
        self,
        sources=None,
        constituents_source: Optional[IndexConstituentsSource] = None,
        max_attempts: int = 3,
        http_get=None,
        timeout: float = 25.0,
    ):
        if sources is None:
            sources = default_index_sources(http_get=http_get, timeout=timeout)
        self._client = FailoverPriceClient(sources, max_attempts=max_attempts)
        self._constituents = constituents_source or IndexConstituentsSource(
            http_get=http_get, timeout=timeout
        )

    def index_history(
        self,
        symbol: str,
        start: Union[date, None] = None,
        end: Union[date, None] = None,
        interval: Interval = Interval.D1,
    ) -> PriceHistory:
        """Index VALUE history (OHLCV in index points) with source failover."""
        return self._client.get_history(symbol, interval, start, end)

    def constituents(self, index: str) -> IndexConstituents:
        """Current index membership (no weights from this source)."""
        return self._constituents.get_constituents(index)


def index_history(
    symbol: str,
    start: Union[date, None] = None,
    end: Union[date, None] = None,
    interval: Interval = Interval.D1,
    *,
    http_get=None,
    timeout: float = 25.0,
    max_attempts: int = 3,
) -> PriceHistory:
    """Convenience: one-shot index value history over the default index chain."""
    client = IndexClient(http_get=http_get, timeout=timeout, max_attempts=max_attempts)
    return client.index_history(symbol, start, end, interval)


def index_constituents(
    index: str,
    *,
    http_get=None,
    timeout: float = 25.0,
) -> IndexConstituents:
    """Convenience: one-shot index membership lookup."""
    return IndexClient(http_get=http_get, timeout=timeout).constituents(index)
