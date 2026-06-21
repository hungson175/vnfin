"""The corp-actions source port plus the shared VN timezone (issue #163).

Every corp-actions adapter implements :class:`CorpActionSource`, a small port over the
shared injectable HTTP transport (:class:`vnfin.transport.HttpDataSource`). v1 has one
concrete adapter — the VSDC cash-dividend scrape (:mod:`vnfin.corp_actions.vsdc`).

``http_get(url, params, headers) -> text`` is injectable for trivial unit testing; the
default (from :class:`vnfin.transport.HttpDataSource`) forces IPv4, sends a browser
User-Agent, applies a 25s timeout, and wraps transport failures as
:class:`vnfin.exceptions.SourceUnavailable` — the shared transport convention.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from zoneinfo import ZoneInfo

from ..transport import HttpDataSource
from .models import DividendHistory

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class CorpActionSource(HttpDataSource, ABC):
    """A swappable corporate-actions source. Adapters are constructed once and reused."""

    name: str = "base"

    @abstractmethod
    def dividends(self, symbol: str, *, start=None, end=None) -> DividendHistory:
        """Return a company's cash-dividend history. Raises a ``SourceError`` on failure."""

    def health(self) -> bool:  # pragma: no cover - default liveness probe
        return True
