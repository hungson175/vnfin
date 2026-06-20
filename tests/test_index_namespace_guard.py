"""Issue #168: price/index namespaces must FAIL LOUD on the wrong asset type.

- ``prices.history`` (and ``liquidity`` by inheritance) reject any KNOWN INDEX symbol
  (deny-list) — an index is not a VND security price.
- ``indices.index_history`` / ``index_history_stitched`` accept ONLY value-history-supported
  indices (allow-list) — a stock/unknown symbol is rejected.
All rejections happen BEFORE any network call (zero-network).
"""
from __future__ import annotations

from datetime import date

import pytest

import vnfin
from vnfin._contracts.index_registry import (
    _KNOWN_INDEX_IDENTIFIERS,
    _VALUE_HISTORY_INDICES,
    is_known_index,
    is_value_history_index,
)
from vnfin.exceptions import InvalidData

_START = date(2024, 1, 1)
_END = date(2024, 6, 30)


class _NetReached(Exception):
    """Raised by the fake http_get to prove the call passed the guard to the network layer."""


def _recorder():
    calls: list = []

    def _http_get(*args, **kwargs):
        calls.append((args, kwargs))
        raise _NetReached()

    return calls, _http_get


# --------------------------------------------------------------------------- #
# registry unit tables
# --------------------------------------------------------------------------- #
def test_is_known_index_membership():
    for sym in ("VNINDEX", "VN30", "HNXINDEX", "HNX30", "UPCOM", "UPCOMINDEX",
                "VNALLSHARE", "VNALL", "VN100", "VNMID", "VNSML", "VNDIAMOND",
                "VNFINLEAD", "VNFINSELECT", "VNXALL", "VNFIN", "VNIT", "VNREAL",
                "HNXUPCOMINDEX"):
        assert is_known_index(sym), sym
    # normalization
    assert is_known_index(" vn30 ")
    assert is_known_index("vnindex")
    assert is_known_index("HNXUpcomIndex")  # #168 review-202606201352: provider-form alias
    # non-indices / malformed
    for sym in ("FPT", "VCB", "VNM", "", "   ", "ABC", None, 123, b"VN30"):
        assert not is_known_index(sym), sym


def test_is_value_history_index_membership():
    for sym in ("VNINDEX", "VN30", "HNXINDEX", "HNX30", "UPCOM", "UPCOMINDEX",
                "VNALLSHARE", "VNALL"):
        assert is_value_history_index(sym), sym
    assert is_value_history_index(" vnindex ")
    # deny-only indices (known index but NOT value-history allow-listed yet)
    for sym in ("VN100", "VNMID", "VNSML", "VNDIAMOND", "VNFINLEAD", "VNFINSELECT",
                "VNXALL", "VNFIN", "VNIT", "VNREAL", "HNXUPCOMINDEX"):
        assert not is_value_history_index(sym), sym
    assert not is_value_history_index("HNXUpcomIndex")  # #168: deny-only, not value-history
    # non-indices
    for sym in ("FPT", "", None, 123):
        assert not is_value_history_index(sym), sym


def test_allow_list_is_subset_of_deny_list():
    assert _VALUE_HISTORY_INDICES <= _KNOWN_INDEX_IDENTIFIERS


# --------------------------------------------------------------------------- #
# prices path — deny known indices (zero-network)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("sym", ["VNINDEX", "VN30", "UPCOMINDEX", "VNFIN", "VNMID", "VNDIAMOND"])
def test_prices_history_rejects_index_symbol(sym):
    calls, http_get = _recorder()
    with pytest.raises(InvalidData) as exc:
        vnfin.prices.history(sym, start=_START, end=_END, http_get=http_get)
    assert "index" in str(exc.value).lower()
    assert calls == []  # zero network


def test_prices_history_rejects_index_with_whitespace_lowercase():
    calls, http_get = _recorder()
    with pytest.raises(InvalidData):
        vnfin.prices.history(" vn30 ", start=_START, end=_END, http_get=http_get)
    assert calls == []


@pytest.mark.parametrize("sym", ["FPT", "VCB", "ABC"])
def test_prices_history_allows_non_index_symbol_to_reach_network(sym):
    # An equity / unknown ticker must PASS the guard (reach the network layer), not be
    # rejected as an index. The fake http_get records the call then raises.
    calls, http_get = _recorder()
    with pytest.raises(Exception) as exc:
        vnfin.prices.history(sym, start=_START, end=_END, http_get=http_get)
    assert not isinstance(exc.value, InvalidData) or "index" not in str(exc.value).lower()
    assert calls, f"{sym} should have reached the network (passed the guard)"


# --------------------------------------------------------------------------- #
# index path — allow only value-history indices (zero-network on reject)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("sym", ["FPT", "VCB", "ABC", "VN100", "VNFIN", "VNDIAMOND"])
def test_index_history_rejects_non_value_history_symbol(sym):
    calls, http_get = _recorder()
    with pytest.raises(InvalidData) as exc:
        vnfin.indices.index_history(sym, _START, _END, http_get=http_get)
    assert "index" in str(exc.value).lower()
    assert calls == []


@pytest.mark.parametrize("sym", ["FPT", "VN100", "VNFIN"])
def test_index_history_stitched_rejects_non_value_history_symbol(sym):
    calls, http_get = _recorder()
    with pytest.raises(InvalidData):
        vnfin.indices.index_history_stitched(sym, _START, _END, http_get=http_get)
    assert calls == []


@pytest.mark.parametrize("sym", ["VNINDEX", "VN30", "HNXINDEX", "HNX30", "UPCOM", "VNALLSHARE"])
def test_index_history_allows_value_history_index_to_reach_network(sym):
    calls, http_get = _recorder()
    with pytest.raises(Exception) as exc:
        vnfin.indices.index_history(sym, _START, _END, http_get=http_get)
    assert not isinstance(exc.value, InvalidData) or "not a known market index" not in str(exc.value).lower()
    assert calls, f"{sym} should have reached the network (passed the allow-list guard)"


def test_index_history_allows_whitespace_lowercase_index():
    calls, http_get = _recorder()
    with pytest.raises(Exception):
        vnfin.indices.index_history(" vnindex ", _START, _END, http_get=http_get)
    assert calls, "normalized index should pass the allow-list guard"


# --------------------------------------------------------------------------- #
# sector index is deny-only: rejected by BOTH paths
# --------------------------------------------------------------------------- #
def test_sector_index_rejected_by_both_paths():
    sym = "VNFIN"  # known index (deny-list) but NOT value-history allow-listed
    calls_p, http_p = _recorder()
    with pytest.raises(InvalidData):
        vnfin.prices.history(sym, start=_START, end=_END, http_get=http_p)
    assert calls_p == []
    calls_i, http_i = _recorder()
    with pytest.raises(InvalidData):
        vnfin.indices.index_history(sym, _START, _END, http_get=http_i)
    assert calls_i == []


# --------------------------------------------------------------------------- #
# liquidity inherits the price guard (no separate guard)
# --------------------------------------------------------------------------- #
def test_liquidity_profile_inherits_price_index_guard():
    calls, http_get = _recorder()
    with pytest.raises(InvalidData) as exc:
        vnfin.liquidity.profile("VNINDEX", _START, _END, http_get=http_get)
    assert "index" in str(exc.value).lower()
    assert calls == []  # zero network — guard fired before the price client fetched


# --------------------------------------------------------------------------- #
# #168 review-202606201352: HNXUPCOMINDEX provider-form alias must be deny-listed
# (price path) but NOT value-history allow-listed (index path).
# --------------------------------------------------------------------------- #
def test_hnxupcomindex_alias_deny_only():
    assert is_known_index("HNXUpcomIndex") is True
    assert is_known_index("HNXUPCOMINDEX") is True
    assert is_value_history_index("HNXUpcomIndex") is False


def test_prices_history_rejects_hnxupcomindex_zero_network():
    calls, http_get = _recorder()
    with pytest.raises(InvalidData) as exc:
        vnfin.prices.history("HNXUPCOMINDEX", start=_START, end=_END, http_get=http_get)
    assert "index" in str(exc.value).lower()
    assert calls == []  # zero network


def test_index_history_rejects_hnxupcomindex_zero_network():
    # Deny-only: not value-history allow-listed, so index_history also rejects it (no network).
    calls, http_get = _recorder()
    with pytest.raises(InvalidData):
        vnfin.indices.index_history("HNXUPCOMINDEX", _START, _END, http_get=http_get)
    assert calls == []


# --------------------------------------------------------------------------- #
# Non-blocking boundary (reviewer note): allow-listed provider aliases reach the
# index network path (pass the allow-list guard).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("sym", ["UPCOMINDEX", "VNALL"])
def test_index_history_allows_provider_alias_to_reach_network(sym):
    calls, http_get = _recorder()
    with pytest.raises(Exception) as exc:
        vnfin.indices.index_history(sym, _START, _END, http_get=http_get)
    # passed the allow-list guard -> reached the network (not rejected as a non-index)
    assert not (isinstance(exc.value, InvalidData) and "not a known" in str(exc.value).lower())
    assert calls, f"{sym} should have reached the network (passed the allow-list guard)"


# --------------------------------------------------------------------------- #
# #168 reopen review-202606201410: bare "HNX" short alias — deny in prices,
# canonicalize HNX -> HNXINDEX in the index path.
# --------------------------------------------------------------------------- #
def test_hnx_alias_known_and_resolves():
    from vnfin._contracts.index_registry import resolve_index_alias
    assert is_known_index("HNX") is True          # deny-listed (price path rejects)
    assert is_known_index("hnx") is True
    assert resolve_index_alias("HNX") == "HNXINDEX"
    assert resolve_index_alias(" hnx ") == "HNXINDEX"
    assert resolve_index_alias("VN30") == "VN30"  # identity for non-aliases


def test_prices_history_rejects_bare_hnx_zero_network():
    calls, http_get = _recorder()
    with pytest.raises(InvalidData) as exc:
        vnfin.prices.history("HNX", start=_START, end=_END, http_get=http_get)
    assert "index" in str(exc.value).lower()
    assert calls == []  # zero network


def test_index_history_routes_bare_hnx_to_hnxindex():
    # HNX must NOT be rejected with "use prices"; it routes to HNXINDEX and reaches the network.
    calls, http_get = _recorder()
    with pytest.raises(Exception) as exc:
        vnfin.indices.index_history("HNX", _START, _END, http_get=http_get)
    assert not (isinstance(exc.value, InvalidData) and "not a known market index" in str(exc.value).lower())
    assert calls, "HNX should route to HNXINDEX and reach the network (passed allow-list)"


def test_index_history_stitched_routes_bare_hnx():
    calls, http_get = _recorder()
    with pytest.raises(Exception) as exc:
        vnfin.indices.index_history_stitched("hnx", _START, _END, http_get=http_get)
    assert not (isinstance(exc.value, InvalidData) and "not a known market index" in str(exc.value).lower())
    assert calls, "stitched HNX should route to HNXINDEX and reach the network"


# --------------------------------------------------------------------------- #
# #174: contradictory routing LOOP. A deny-only identifier (a recognized index that
# is NOT value-history-servable) must get a TERMINAL "recognized index, history-
# unsupported" diagnostic from index_history / index_history_stitched — it must NEVER
# be told to "use prices.history()", because the price path correctly rejects it as an
# index, so that guidance bounces the user between the two namespaces forever. A
# genuinely unknown / equity symbol still (correctly) routes to prices.history().
# --------------------------------------------------------------------------- #

#: Every deny-only identifier: in the deny-list but NOT the value-history allow-list,
#: EXCLUDING the bare "HNX" alias (it canonicalizes to HNXINDEX, which IS served, so it
#: never reaches the loop). This is the routing regression matrix the reporter asked for.
_DENY_ONLY_INDICES = [
    # 10 HOSE sector indices
    "VNCOND", "VNCONS", "VNENE", "VNFIN", "VNHEAL", "VNIND", "VNIT", "VNMAT", "VNREAL", "VNUTI",
    # other deny-only groups (membership attested; value-history not allow-listed)
    "VN100", "VNMID", "VNSML", "VNDIAMOND", "VNFINLEAD", "VNFINSELECT", "VNXALL", "VNXALLSHARE",
    # provider-form UPCOM alias (deny-only)
    "HNXUPCOMINDEX",
]


def test_deny_only_matrix_matches_registry_difference():
    # Lock the matrix to the registry so a future set edit cannot silently shrink it and
    # re-open the loop: deny-only == known minus value-history, minus the served HNX alias.
    expected = set(_KNOWN_INDEX_IDENTIFIERS) - set(_VALUE_HISTORY_INDICES)
    expected.discard("HNX")  # canonicalizes to HNXINDEX (served) before the guard
    assert set(_DENY_ONLY_INDICES) == expected


def _assert_recognized_index_diagnostic(msg: str):
    """The #174 invariant on the terminal diagnostic for a known-but-unservable index."""
    low = msg.lower()
    assert "prices.history" not in low, msg       # never bounce back to the price path
    assert "for stocks" not in low, msg           # it is an index, not a stock
    assert "recognized market index" in low, msg  # tell the user it IS a known index
    assert ("not supported" in low) or ("not available" in low), msg


@pytest.mark.parametrize("sym", _DENY_ONLY_INDICES)
def test_index_history_deny_only_gives_terminal_diagnostic(sym):
    calls, http_get = _recorder()
    with pytest.raises(InvalidData) as exc:
        vnfin.indices.index_history(sym, _START, _END, http_get=http_get)
    _assert_recognized_index_diagnostic(str(exc.value))
    assert calls == []  # zero network


@pytest.mark.parametrize("sym", _DENY_ONLY_INDICES)
def test_index_history_stitched_deny_only_gives_terminal_diagnostic(sym):
    calls, http_get = _recorder()
    with pytest.raises(InvalidData) as exc:
        vnfin.indices.index_history_stitched(sym, _START, _END, http_get=http_get)
    _assert_recognized_index_diagnostic(str(exc.value))
    assert calls == []  # zero network


@pytest.mark.parametrize("sym", _DENY_ONLY_INDICES)
def test_prices_history_still_rejects_deny_only_index_unchanged(sym):
    # The price path is unchanged: a deny-only index is still pointed at index_history()
    # (correct — it IS an index), never at itself. Regression lock for the other half of the loop.
    calls, http_get = _recorder()
    with pytest.raises(InvalidData) as exc:
        vnfin.prices.history(sym, start=_START, end=_END, http_get=http_get)
    low = str(exc.value).lower()
    assert "market index" in low and "index_history" in low
    assert calls == []


@pytest.mark.parametrize("sym", ["NOTAREALSYMBOL", "FPT", "VCB", "ABC"])
def test_index_history_unknown_or_equity_still_routes_to_prices(sym):
    # The route-to-prices guidance is correct ONLY for a genuinely unknown / equity symbol.
    for fn in (vnfin.indices.index_history, vnfin.indices.index_history_stitched):
        calls, http_get = _recorder()
        with pytest.raises(InvalidData) as exc:
            fn(sym, _START, _END, http_get=http_get)
        low = str(exc.value).lower()
        assert "not a known market index" in low, (fn.__name__, sym, exc.value)
        assert "prices.history" in low, (fn.__name__, sym, exc.value)  # correct branch here
        assert calls == []


def test_index_history_headline_indices_still_serve():
    # Regression lock: real value-history indices are unaffected — they pass the guard and
    # reach the network (no InvalidData routing error).
    for sym in ("VNINDEX", "VN30", "HNXINDEX", "HNX30", "UPCOM", "VNALLSHARE"):
        calls, http_get = _recorder()
        with pytest.raises(Exception) as exc:
            vnfin.indices.index_history(sym, _START, _END, http_get=http_get)
        assert not isinstance(exc.value, InvalidData), (sym, exc.value)
        assert calls, f"{sym} should reach the network (passed the allow-list guard)"
