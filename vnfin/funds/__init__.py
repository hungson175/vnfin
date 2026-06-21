"""vnfin.funds — VN open-ended mutual fund data (clean-room).

Public API:
    - Typed models: ``Fund``, ``FundList``, ``NavPoint``, ``NavHistory``, ``FundHolding``,
      ``AssetAllocation``, ``AssetClassWeight``, ``SectorWeight``.
    - Adapter: ``FmarketFundSource`` (Fmarket public, no-auth API).

Example::

    from vnfin.funds import FmarketFundSource

    src = FmarketFundSource()
    funds = src.list_funds(asset_type="STOCK")
    hist = src.nav_history(funds[0].id)         # full NAV history (VND/unit)
    holdings = src.holdings(funds[0].id)        # top disclosed holdings (stocks + bonds)
    alloc = src.asset_allocation(funds[0].id)   # asset-class split (equity/bond/cash)
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
    """Primary funds entry: the default :class:`FmarketFundSource` (Fmarket, no-auth).

    Standard ``<domain>.source(...)`` factory. Use ``.list_funds()``, ``.nav_history(id)``
    and ``.holdings(id)`` on the returned object.
    """
    return FmarketFundSource(http_get=http_get, timeout=timeout)


# ``client`` is an alias of ``source`` so the funds domain matches the shared
# ``<domain>.client(...)`` naming used elsewhere; funds has a single source surface.
client = source
