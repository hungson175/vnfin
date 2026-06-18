"""The gold-source port plus the shared injectable HTTP transport.

Every adapter implements :class:`GoldSource`. Spot is the common denominator (every
gold source can quote a current price); daily history is a capability only some sources
have, gated by :attr:`GoldSource.provides_history`.

``http_get(url, params, headers) -> text`` is injectable for trivial unit testing; the
default (from :class:`vnfin.transport.HttpDataSource`) forces IPv4 (datacenter IPv6 is
frequently blocked by these providers), sends a browser User-Agent, and applies a 25s
timeout — the shared transport convention.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from zoneinfo import ZoneInfo

from ..transport import HttpDataSource
from .models import GoldHistory, GoldQuote

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class GoldSource(HttpDataSource, ABC):
    """A swappable gold price source. Adapters are constructed once and reused.

    Capability flags let a caller (or a future failover layer) pick the right source
    without a network call:

    * ``provides_spot`` — can return a current :class:`GoldQuote` (always True here).
    * ``provides_history`` — can return a daily :class:`GoldHistory` series.
    """

    name: str = "base"
    provides_spot: bool = True
    provides_history: bool = False

    @abstractmethod
    def get_quotes(self) -> tuple[GoldQuote, ...]:
        """Return all current spot quotes this source publishes.

        World single-tick sources return a one-element tuple. Raises a
        :class:`vnfin.exceptions.SourceError` subclass on failure.
        """

    def get_quote(self, *args, **kwargs) -> GoldQuote:  # pragma: no cover - overridden
        """Return one quote. Subclasses define selection semantics."""
        raise NotImplementedError

    def get_history(self, start: date, end: date) -> GoldHistory:
        """Return a daily price series. Only meaningful when ``provides_history``."""
        from ..exceptions import VnfinError

        raise VnfinError(f"{self.name} does not provide gold history (spot only)")

    def health(self) -> bool:  # pragma: no cover - default liveness probe
        return True
