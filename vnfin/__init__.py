"""vnfin — clean-room OSS Python library for Vietnam financial-market data.

Coherent facade / naming standard
---------------------------------
There is **one obvious entry per domain**, reachable as an attribute of ``vnfin``::

    import vnfin

    vnfin.prices        # equity OHLCV (VND)            -> .client() / .history()
    vnfin.fundamentals  # financial statements (VND)    -> .client()/.source() / get_financials()
    vnfin.funds         # mutual fund NAV (VND/unit)     -> .client()/.source()
    vnfin.indices       # index value (points) + members -> .client() / index_history()
    vnfin.gold          # gold spot/history              -> .vn() / .world() / .source()
    vnfin.crypto        # crypto OHLCV (USD)             -> .client()/.source()
    vnfin.macro         # macro indicators               -> .client()/.source()

Each domain keeps its own typed models and units (see ``docs/api.md`` and
``docs/units.md``); they are **not** funnelled through one client that returns
incompatible models. Every domain factory exposes the standard verbs ``client(...)``
and/or ``source(...)``; all existing submodule imports keep working unchanged.
"""
from . import (
    crypto,
    exceptions,
    fundamentals,
    funds,
    fx,
    gold,
    indices,
    macro,
    prices,
)
from .client import FailoverPriceClient
from .failover import FailoverClient
from .models import (
    AdjustmentPolicy,
    Interval,
    PriceBar,
    PriceHistory,
    SourceAttempt,
)

__all__ = [
    # price models / engines (long-standing top-level surface)
    "AdjustmentPolicy",
    "Interval",
    "PriceBar",
    "PriceHistory",
    "SourceAttempt",
    "FailoverClient",
    "FailoverPriceClient",
    "default_client",
    # facade: domain namespaces (one obvious entry per domain)
    "prices",
    "fundamentals",
    "funds",
    "indices",
    "gold",
    "crypto",
    "macro",
    "fx",
    "exceptions",
]
__version__ = "0.1.0"


def default_client(max_attempts: int = 3, http_get=None, timeout: float = 25.0) -> FailoverPriceClient:
    """A FailoverPriceClient over the default provider-adjusted broker chain.

    Order: SSI -> VNDirect -> VPS -> Pinetree (KIS excluded; its series is MIXED).
    """
    from .sources.registry import default_sources

    return FailoverPriceClient(
        default_sources(http_get=http_get, timeout=timeout), max_attempts=max_attempts
    )
