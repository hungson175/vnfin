"""Derived GICS L1 sector classification for VN equities (#195) — clean-room.

The SSI iBoard stock-group payload (``vnfin.equities``) carries **no** sector/industry
field (hence the always-on ``sector_not_available`` token). Rather than adopt a
provider industry id, this module DERIVES the GICS L1 sector by **inverting the 10
VNAllShare sector baskets** — the same membership baskets ``vnfin.indices`` already
fetches via :class:`~vnfin.indices.sources.IndexConstituentsSource`. A symbol's sector
is the basket it belongs to; the pinned ``_GICS_L1`` map gives the public MSCI/S&P L1
English name.

Honest-coverage contract (never silent, never fabricated):

* The baskets are **HOSE-only** and partial (~74% of HOSE), so an unmapped HOSE symbol
  and **every** HNX/UPCoM symbol map to ``None`` — all four sector fields stay ``None``
  as a unit. The exact % is never pinned in code (encode the invariant, not a constant).
* A symbol seen in **≥2** baskets is an **overlap** (should not happen for GICS L1): it
  degrades to a deterministic ``None`` (refuse to pick), recorded for disclosure under
  the same ``sector_partial_coverage:`` prefix that the coverage line uses.

Caching mirrors the AlphaVantage precedent: the inverted map is built **lazily on first
sector access**, cached per-instance, TTL-bounded (``_SECTOR_MAP_CACHE_TTL`` = 6h). One
build fetches each of the 10 baskets EXACTLY ONCE; subsequent calls within the TTL reuse
the cached map.

Clean-room: ZERO vnstock. No ``industryID`` / ``industryIDv2`` / Vietnamese
``industry_name``. The derivation composes one-way over the existing indices source
(equities → indices); the constituents fetcher is injectable so CI never hits iboard.
"""
from __future__ import annotations

import time as _time
from typing import Optional

from ..indices.sources import IndexConstituentsSource

# Pinned GICS L1 code -> public MSCI/S&P standard English name. Clean-room safe (the GICS
# L1 sector names are the public standard, not a provider taxonomy). EXACTLY 10 codes,
# matching the VNAllShare sector index basket codes registered in the index registry.
_GICS_L1: dict[str, str] = {
    "VNFIN": "Financials",
    "VNIT": "Information Technology",
    "VNREAL": "Real Estate",
    "VNMAT": "Materials",
    "VNCONS": "Consumer Staples",
    "VNCOND": "Consumer Discretionary",
    "VNIND": "Industrials",
    "VNENE": "Energy",
    "VNHEAL": "Health Care",
    "VNUTI": "Utilities",
}

# The 10 sector basket codes to invert, in a stable (sorted) fetch order.
_SECTOR_CODES: tuple[str, ...] = tuple(sorted(_GICS_L1))

# Provenance constant: every mapped sector carries this scheme + source.
_SECTOR_SCHEME = "GICS"
_SECTOR_SOURCE = IndexConstituentsSource.NAME  # "ssi_iboard_query"

# Lazy, per-instance cache TTL (seconds). 6h — mirrors ``_AV_DEFAULT_CACHE_TTL``.
_SECTOR_MAP_CACHE_TTL = 21600.0  # 6h

# Sentinel mapping value meaning "ambiguous (≥2 baskets) → None, never picked".
_OVERLAP = object()


class SectorClassifier:
    """Derive a VN equity's GICS L1 sector by inverting the 10 VNAllShare sector baskets.

    The inverted ``symbol -> sector_code`` map is built lazily on first sector access,
    cached on the instance, and TTL-bounded. ``fetch_constituents`` is an injected
    callable ``code -> IndexConstituents`` (default: a private
    :class:`~vnfin.indices.sources.IndexConstituentsSource`'s bound
    ``get_constituents``) so tests can supply synthetic baskets — CI never hits iboard.
    """

    def __init__(
        self,
        *,
        fetch_constituents=None,
        cache_ttl: float = _SECTOR_MAP_CACHE_TTL,
        clock=None,
        http_get=None,
        timeout: float = 25.0,
    ):
        if fetch_constituents is None:
            # Default: a private constituents source. The 6h cache_ttl on the source
            # isolates same-process re-fetches; the classifier's own TTL governs rebuilds.
            src = IndexConstituentsSource(
                http_get=http_get, timeout=timeout, cache_ttl=_SECTOR_MAP_CACHE_TTL
            )
            fetch_constituents = src.get_constituents
        self._fetch_constituents = fetch_constituents
        self._cache_ttl = cache_ttl
        self._clock = clock or _time.monotonic
        # Lazy state — never touched until first sector access (so construction is
        # side-effect-free / network-free).
        self._map: Optional[dict[str, object]] = None
        self._overlaps: dict[str, tuple[str, ...]] = {}
        self._built_at: Optional[float] = None

    # ------------------------------- map build ------------------------------- #

    def _ensure_map(self) -> dict[str, object]:
        """Return the cached inverted map, building it once per TTL window.

        Each of the 10 baskets is fetched EXACTLY ONCE per build. A symbol seen in ≥2
        baskets is recorded as an overlap and mapped to ``_OVERLAP`` (deterministic
        ``None`` at classify time — never picked).
        """
        now = self._clock()
        if (
            self._map is not None
            and self._built_at is not None
            and (now - self._built_at) < self._cache_ttl
        ):
            return self._map
        return self._build_map(now)

    def _build_map(self, now: float) -> dict[str, object]:
        mapping: dict[str, object] = {}
        baskets_of: dict[str, list[str]] = {}  # overlap tracking: symbol -> [codes]
        for code in _SECTOR_CODES:
            constituents = self._fetch_constituents(code)
            for member in constituents.members:
                sym = member.symbol
                baskets_of.setdefault(sym, []).append(code)
                if sym in mapping:
                    # Seen before → overlap (≥2 baskets) → ambiguous, never picked.
                    mapping[sym] = _OVERLAP
                else:
                    mapping[sym] = code
        overlaps = {
            sym: tuple(codes) for sym, codes in baskets_of.items() if len(codes) >= 2
        }
        self._map = mapping
        self._overlaps = overlaps
        self._built_at = now
        return mapping

    # ------------------------------- public API ------------------------------ #

    def classify(
        self, symbol: str
    ) -> Optional[tuple[str, str, str, str]]:
        """Return ``(sector_code, sector_name, "GICS", "ssi_iboard_query")`` for a mapped
        symbol, else ``None`` (unmapped / HNX / UPCoM / multi-basket overlap)."""
        canon = symbol.strip().upper() if isinstance(symbol, str) else symbol
        mapping = self._ensure_map()
        code = mapping.get(canon)
        if code is None or code is _OVERLAP:
            return None
        return (code, _GICS_L1[code], _SECTOR_SCHEME, _SECTOR_SOURCE)

    def overlaps(self) -> dict[str, tuple[str, ...]]:
        """``{symbol: (code, ...)}`` for every symbol seen in ≥2 baskets (disclosure)."""
        self._ensure_map()
        return dict(self._overlaps)
