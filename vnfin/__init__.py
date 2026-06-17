"""vnfin — clean-room OSS Python library for Vietnam financial-market data."""
from . import exceptions
from .client import FailoverPriceClient
from .models import (
    AdjustmentPolicy,
    Interval,
    PriceBar,
    PriceHistory,
    SourceAttempt,
)

__all__ = [
    "AdjustmentPolicy",
    "Interval",
    "PriceBar",
    "PriceHistory",
    "SourceAttempt",
    "FailoverPriceClient",
    "default_client",
    "exceptions",
]
__version__ = "0.0.1"


def default_client(max_attempts: int = 3, http_get=None, timeout: float = 25.0) -> FailoverPriceClient:
    """A FailoverPriceClient over the default provider-adjusted broker chain.

    Order: SSI -> VNDirect -> VPS -> Pinetree (KIS excluded; its series is MIXED).
    """
    from .sources.registry import default_sources

    return FailoverPriceClient(
        default_sources(http_get=http_get, timeout=timeout), max_attempts=max_attempts
    )
