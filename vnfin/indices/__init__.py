"""vnfin.indices — VN market index VALUE history + CONSTITUENTS.

Public API:

    from vnfin.indices import IndexClient, index_history, index_constituents

    c = IndexClient()
    hist = c.index_history("VNINDEX", date(2024, 1, 1), date(2024, 6, 30))  # PriceHistory, currency="points"
    vn30 = c.constituents("VN30")                                            # IndexConstituents

Index VALUE history reuses the existing price stack (the TradingView-UDF transport
+ FailoverPriceClient), but with index-aware adapters that keep values in *points*
(PRICE_SCALE=1.0) instead of the x1000 thousands-of-VND scaling used for stocks.
The underlying price sources are not modified — composition only.

Constituents come from the public SSI iBoard group endpoint and carry membership
only (no per-stock weights; weights are never fabricated).
"""
from __future__ import annotations

from .client import (
    IndexClient,
    default_index_sources,
    index_constituents,
    index_history,
    index_history_stitched,
)
from .models import IndexConstituents, IndexMember
from .sources import (
    IndexConstituentsSource,
    SSIIndexSource,
    VNDirectIndexSource,
    VPSIndexSource,
)

__all__ = [
    "IndexClient",
    "index_history",
    "index_history_stitched",
    "index_constituents",
    "default_index_sources",
    "IndexConstituents",
    "IndexMember",
    "IndexConstituentsSource",
    "VPSIndexSource",
    "SSIIndexSource",
    "VNDirectIndexSource",
    "client",
    "source",
]


def client(http_get=None, timeout: float = 25.0, max_attempts: int = 3) -> IndexClient:
    """Primary indices entry: the default :class:`IndexClient` (VN index VALUE + members).

    Standard ``<domain>.client(...)`` factory. Use ``.index_history(...)`` for value
    history (in *points*) and ``.constituents(index)`` for membership.
    """
    return IndexClient(http_get=http_get, timeout=timeout, max_attempts=max_attempts)


def source(http_get=None, timeout: float = 25.0) -> VPSIndexSource:
    """Primary indices SOURCE: the single first adapter of the default chain (no failover).

    Standard ``<domain>.source(...)`` factory — returns the PRIMARY index-value
    source, currently :class:`VPSIndexSource` (first of
    :func:`default_index_sources`; the only source that serves UPCOM and all sector
    indices correctly). Index values stay in *points*. Prefer :func:`client` for the
    failover chain plus constituents.
    """
    return VPSIndexSource(http_get=http_get, timeout=timeout)
