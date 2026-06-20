"""Private market-index identity registry (#168 namespace type-confusion guard).

The price and index namespaces must **fail loud** on the wrong asset type instead of
silently returning wrong-typed data (a stock-price call for ``VNINDEX``, or an
index-history call for ``FPT``). Indices are a **closed, known set** while the equity
universe is **open**, so the guard is asymmetric and uses two sets:

* :data:`_KNOWN_INDEX_IDENTIFIERS` — the **deny-list** for the *price* path
  (``prices.history`` / ``FailoverPriceClient`` and, by inheritance, ``liquidity``).
  EVERY market-index identifier the project recognises, including provider aliases
  (``UPCOMINDEX``, ``VNALL``) and the sector / constituents-only groups. Any of these
  is rejected from the price path — none is a VND security price.
* :data:`_VALUE_HISTORY_INDICES` — the **allow-list** for the *index-history* path
  (``indices.index_history`` / ``index_history_stitched``). ONLY indices whose value
  (OHLCV-in-points) history is documented as supported by the index sources. A symbol
  not in this set is rejected by ``index_history`` (use ``prices.history`` for stocks).

Both sets are **private** (no public API / snapshot surface) and seeded **clean-room**
from repo-internal evidence only — ``docs/sources/indices-constituents.md`` (the blessed
headline value-history set), ``docs/research/2026-06-18-indices.md`` (full provider
coverage), and ``vnfin/indices/sources.py`` alias maps. No VNStock/external material was
consulted.

Conservative choice (reviewer tweak review-202606201325): the value-history allow-list is
the documented **headline** set (VNINDEX, VN30, HNXINDEX, HNX30, UPCOM, VNALLSHARE) plus
the provider aliases that resolve to them. The wider VPS-served set (VN100/VNMID/VNSML/
VNDIAMOND/VNFINLEAD/VNFINSELECT/VNXALL + the 10 sector indices) is **deny-listed in the
price path but NOT yet allow-listed for index_history** — those are added (with tests)
when value-history support is exercised, never silently. Expanding the allow-list later is
a one-line, reviewer-gated change.
"""
from __future__ import annotations

#: Allow-list: indices with documented value (OHLCV-points) history support.
#: Headline canonical set (docs/sources/indices-constituents.md) + the provider aliases
#: that resolve to a supported index (so a caller using the provider form is not wrongly
#: rejected): UPCOM<->UPCOMINDEX, VNALLSHARE<->VNALL.
_VALUE_HISTORY_INDICES: frozenset[str] = frozenset(
    {
        "VNINDEX",
        "VN30",
        "HNXINDEX",
        "HNX30",
        "UPCOM",
        "UPCOMINDEX",
        "VNALLSHARE",
        "VNALL",
    }
)

#: Deny-list: every market-index identifier the project recognises (a superset of the
#: allow-list). Used by the PRICE path so no index can be mistaken for a stock. Includes
#: the constituents-only groups and the 10 HOSE sector indices + the VNXALL family +
#: provider aliases — all attested in repo docs (indices-constituents.md / research doc).
_KNOWN_INDEX_IDENTIFIERS: frozenset[str] = _VALUE_HISTORY_INDICES | frozenset(
    {
        # constituents-only / additional groups (membership attested; value-history not
        # yet allow-listed)
        "VN100",
        "VNMID",
        "VNSML",
        "VNDIAMOND",
        "VNFINLEAD",
        "VNFINSELECT",
        "VNXALL",
        "VNXALLSHARE",
        # 10 HOSE sector indices (docs/research/2026-06-18-indices.md)
        "VNCOND",
        "VNCONS",
        "VNENE",
        "VNFIN",
        "VNHEAL",
        "VNIND",
        "VNIT",
        "VNMAT",
        "VNREAL",
        "VNUTI",
    }
)


def _normalize(value) -> str:
    """Best-effort canonicalization for membership only (strip + upper).

    The guards call these helpers AFTER ``canonical_security_symbol`` has already
    validated/normalized the symbol, so this is a defensive no-op for valid input. A
    non-string or malformed value simply will not match any set member (returns a value
    that fails membership) — truly malformed symbols are rejected upstream by
    ``canonical_security_symbol`` before these helpers are reached.
    """
    if not isinstance(value, str):
        return ""
    return value.strip().upper()


def is_known_index(value) -> bool:
    """True if ``value`` is any recognised market-index identifier (deny-list).

    Used by the price path (and, by inheritance, liquidity) to reject an index symbol
    that is not a VND security price.
    """
    return _normalize(value) in _KNOWN_INDEX_IDENTIFIERS


def is_value_history_index(value) -> bool:
    """True if ``value`` is an index with documented value-history support (allow-list).

    Used by ``index_history`` / ``index_history_stitched`` to accept only recognised
    indices and reject stocks/unknown symbols.
    """
    return _normalize(value) in _VALUE_HISTORY_INDICES
