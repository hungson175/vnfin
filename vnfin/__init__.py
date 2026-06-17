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
    "exceptions",
]
__version__ = "0.0.1"
