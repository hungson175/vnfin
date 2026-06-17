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
    "index_constituents",
    "default_index_sources",
    "IndexConstituents",
    "IndexMember",
    "IndexConstituentsSource",
    "VPSIndexSource",
    "SSIIndexSource",
    "VNDirectIndexSource",
]
