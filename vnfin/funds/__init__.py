"""vnfin.funds — VN open-ended mutual fund data (clean-room).

Public API:
    - Typed models: ``Fund``, ``FundList``, ``NavPoint``, ``NavHistory``, ``FundHolding``.
    - Adapter: ``FmarketFundSource`` (Fmarket public, no-auth API).

Example::

    from vnfin.funds import FmarketFundSource

    src = FmarketFundSource()
    funds = src.list_funds(asset_type="STOCK")
    hist = src.nav_history(funds[0].id)         # full NAV history (VND/unit)
    holdings = src.holdings(funds[0].id)        # top disclosed holdings
"""
from .fmarket import FmarketFundSource
from .models import Fund, FundHolding, FundList, NavHistory, NavPoint

__all__ = [
    "Fund",
    "FundList",
    "NavPoint",
    "NavHistory",
    "FundHolding",
    "FmarketFundSource",
]
