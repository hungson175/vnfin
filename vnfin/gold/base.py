"""The gold-source port plus a shared injectable HTTP helper.

Every adapter implements :class:`GoldSource`. Spot is the common denominator (every
gold source can quote a current price); daily history is a capability only some sources
have, gated by :attr:`GoldSource.provides_history`.

``http_get(url, params, headers) -> text`` is injectable for trivial unit testing; the
default forces IPv4 (datacenter IPv6 is frequently blocked by these providers), sends a
browser User-Agent, and applies a 25s timeout — mirroring the price-source convention.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from zoneinfo import ZoneInfo

from .models import GoldHistory, GoldQuote

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _default_http_get(url, params=None, headers=None, timeout: float = 25.0) -> str:  # pragma: no cover - network
    """Default transport: IPv4-forced httpx GET returning response text."""
    import httpx

    transport = httpx.HTTPTransport(local_address="0.0.0.0")  # force IPv4
    hdrs = {"User-Agent": _UA}
    if headers:
        hdrs.update(headers)
    with httpx.Client(transport=transport, timeout=timeout, headers=hdrs) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.text


class GoldSource(ABC):
    """A swappable gold price source. Adapters are constructed once and reused.

    Capability flags let a caller (or a future failover layer) pick the right source
    without a network call:

    * ``provides_spot`` — can return a current :class:`GoldQuote` (always True here).
    * ``provides_history`` — can return a daily :class:`GoldHistory` series.
    """

    name: str = "base"
    provides_spot: bool = True
    provides_history: bool = False

    def __init__(self, http_get=None, timeout: float = 25.0):
        self._timeout = timeout
        if http_get is None:
            self._http_get = lambda url, params=None, headers=None: _default_http_get(
                url, params, headers, timeout
            )
        else:
            self._http_get = http_get

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
