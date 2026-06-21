"""vnfin.equities — the investable VN equity universe (clean-room, SSI iBoard).

One obvious entry: :func:`universe` (a convenience over :class:`SsiIboardUniverseSource`).
It enumerates the investable equities per board with source-backed per-symbol reference
metadata + honest coverage diagnostics — a data primitive only, NOT a screener/ranker/
advisor. ``profile(symbol)`` is deferred: to get one symbol, call ``universe(exchange=...)``
and filter the returned securities.

    import vnfin
    from vnfin.equities import universe

    hose = universe("HOSE")          # one board
    everything = universe()          # merges HOSE + HNX + UPCOM (cross-board keep-first)
    for sec in hose:
        print(sec.symbol, sec.exchange, sec.company_name_en)
    fpt = next(s for s in universe("HOSE") if s.symbol == "FPT")  # one-symbol pattern

The board token is non-obvious (plain HOSE/HNX/UPCOM return empty); the source maps each
board to its index-group token. The result's ``warnings`` ALWAYS disclose the known gaps
(index-basket-derived ~96% coverage, no listing date, no sector) and never fabricate data.
"""
from __future__ import annotations

from .models import EquitySecurity, EquityUniverse
from .sources import SsiIboardUniverseSource

__all__ = [
    "EquitySecurity",
    "EquityUniverse",
    "SsiIboardUniverseSource",
    "client",
    "source",
    "universe",
]


def source(http_get=None, timeout: float = 25.0) -> SsiIboardUniverseSource:
    """Primary equities entry: the default :class:`SsiIboardUniverseSource` (SSI iBoard).

    Standard ``<domain>.source(...)`` factory. Call ``.universe(exchange=...)`` on the
    returned object.
    """
    return SsiIboardUniverseSource(http_get=http_get, timeout=timeout)


# ``client`` is an alias of ``source`` so the equities domain matches the shared
# ``<domain>.client(...)`` naming; equities has a single source surface (mirror funds).
client = source


def universe(exchange=None, *, http_get=None, timeout: float = 25.0) -> EquityUniverse:
    """One-shot equity-universe enumeration.

    ``exchange=None`` merges all three boards (HOSE, HNX, UPCOM) with cross-board
    keep-first dedup; an ``exchange`` board name returns just that board.
    """
    return source(http_get=http_get, timeout=timeout).universe(exchange)
