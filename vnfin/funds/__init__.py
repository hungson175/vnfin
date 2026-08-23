"""vnfin.funds — VN open-ended mutual-fund contracts (clean-room).

Public API:
    - Typed models: ``Fund``, ``FundList``, ``NavPoint``, ``NavHistory``, ``FundHolding``,
      ``AssetAllocation``, ``AssetClassWeight``, ``SectorWeight``.
    - Adapter: ``FmarketFundSource`` (currently disabled pending permission).

The source and model imports remain compatible. Valid Fmarket operation calls fail
closed with ``SourceUnavailable("SOURCE_DISABLED_PENDING_PERMISSION")`` before any
cache or network work; construction remains lazy and offline.
"""
from __future__ import annotations

from .fmarket import FmarketFundSource
from .models import (
    AssetAllocation,
    AssetClassWeight,
    Fund,
    FundHolding,
    FundList,
    NavHistory,
    NavPoint,
    SectorWeight,
)

__all__ = [
    "Fund",
    "FundList",
    "NavPoint",
    "NavHistory",
    "FundHolding",
    "AssetAllocation",
    "AssetClassWeight",
    "SectorWeight",
    "FmarketFundSource",
    "client",
    "source",
]


def source(http_get=None, timeout: float = 25.0) -> FmarketFundSource:
    """Return the lazy, policy-disabled :class:`FmarketFundSource` entrypoint.

    Construction makes no network call and preserves the existing ``http_get`` and
    ``timeout`` signature. Valid operations currently raise the bounded
    ``SOURCE_DISABLED_PENDING_PERMISSION`` error before transport.
    """
    return FmarketFundSource(http_get=http_get, timeout=timeout)


# ``client`` is an alias of ``source`` so the funds domain matches the shared
# ``<domain>.client(...)`` naming used elsewhere; funds has a single source surface.
client = source
