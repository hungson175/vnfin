"""The price-source port (interface) all adapters implement."""
from __future__ import annotations

from abc import ABC, abstractmethod
from zoneinfo import ZoneInfo

from ..models import Interval, PriceHistory

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class PriceSource(ABC):
    """A swappable price source. Adapters are constructed once and reused."""

    name: str = "base"

    @abstractmethod
    def supports(self, interval: Interval) -> bool:
        """Whether this source can serve the given interval (no network call)."""

    @abstractmethod
    def get_history(self, symbol: str, interval: Interval, start, end) -> PriceHistory:
        """Fetch normalized OHLCV history. Raises a ``SourceError`` subclass on failure."""

    def health(self) -> bool:  # pragma: no cover - default liveness probe
        return True
