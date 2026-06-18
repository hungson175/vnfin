"""Tests for vnfin.indices — index VALUE history + CONSTITUENTS.

Synthetic fixtures only: hand-crafted JSON that matches the provider JSON *shape*
(arrays, envelope, status) but uses OBVIOUSLY-FAKE symbols (TESTCO/ZZZ/FAKE1) and
FABRICATED numbers (round ~1000-point levels). No real provider proof values are
copied here — real snippets stay in docs/research provenance only.

Two domains:
  (a) index value history — index-aware UDF sources that reuse the price stack but
      keep index values in POINTS (PRICE_SCALE=1.0), unlike the x1000 stock feeds.
  (b) index constituents — SSI iboard-query /stock/group/{GROUP} member lists.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable, VnfinError
from vnfin.models import AdjustmentPolicy, Interval
from vnfin.indices import (
    IndexClient,
    IndexConstituents,
    IndexConstituentsSource,
    IndexMember,
    SSIIndexSource,
    VNDirectIndexSource,
    VPSIndexSource,
    index_constituents,
    index_history,
)

WIDE = (date(2024, 6, 1), date(2024, 6, 30))


# ----------------------------- synthetic fixtures -----------------------------

# OBVIOUSLY-FAKE index series. These are FABRICATED, internally-consistent numbers
# (round levels around 1000 points, satisfying low<=open/close<=high) — NOT real
# provider proof values. Real provider snippets live only in the provenance docs.
# (date, open, high, low, close, volume) — index values in POINTS, volume in shares.
_INDEX_ROWS = [
    ("2024-06-10", 1000.0, 1010.0, 995.0, 1005.0, 100_000_000),
    ("2024-06-11", 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),
    ("2024-06-12", 1012.0, 1020.0, 1008.0, 1018.0, 120_000_000),
]


def _ts(d: str) -> int:
    return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _bare_udf(rows=None, status="ok") -> str:
    rows = _INDEX_ROWS if rows is None else rows
    return json.dumps(
        {
            "symbol": "VNINDEX",
            "s": status,
            "t": [_ts(r[0]) for r in rows],
            "o": [r[1] for r in rows],
            "h": [r[2] for r in rows],
            "l": [r[3] for r in rows],
            "c": [r[4] for r in rows],
            "v": [r[5] for r in rows],
        }
    )


def _ssi_envelope(rows=None, status="ok") -> str:
    inner = json.loads(_bare_udf(rows, status))
    inner["nextTime"] = None
    return json.dumps({"code": "SUCCESS", "message": "ok", "data": inner, "status": "ok"})


def _constituents_payload(members=None, code="SUCCESS") -> str:
    # OBVIOUSLY-FAKE constituents. Symbols are fabricated placeholders (not real
    # index members) but the JSON shape matches the provider's group endpoint.
    members = (
        [("TESTCO", "hose"), ("ZZZ", "hose"), ("FAKE1", "hose")] if members is None else members
    )
    data = [
        {
            "stockSymbol": sym,
            "exchange": exch,
            "isin": f"VN000000{sym}",
            "companyNameEn": f"{sym} Corp",
            "companyNameVi": f"Cong ty {sym}",
            "refPrice": 22300,
            "matchedPrice": 22000,
        }
        for sym, exch in members
    ]
    return json.dumps({"code": code, "message": "Call API /stock/group/X successful", "data": data})


def _get(text):
    def _g(url, params, headers):
        return text

    return _g


def _raising(exc):
    def _g(url, params, headers):
        raise exc

    return _g


# ============================ (a) VALUE history ==============================


def test_vps_index_source_values_in_points_not_vnd():
    """Critical: a synthetic index close of 1005.0 stays 1005.0 (points), NOT x1000."""
    s = VPSIndexSource(http_get=_get(_bare_udf()))
    h = s.get_history("VNINDEX", Interval.D1, *WIDE)
    assert h.bars[0].close == pytest.approx(1005.0)
    assert h.bars[0].open == pytest.approx(1000.0)
    # Hard scale check: index point levels must never be x1000-scaled into VND.
    assert h.bars[0].close < 10_000
    assert h.currency == "points"
    assert h.source == "vps_index"


def test_ssi_index_source_envelope_unwrap_points():
    s = SSIIndexSource(http_get=_get(_ssi_envelope()))
    h = s.get_history("VNINDEX", Interval.D1, *WIDE)
    assert len(h) == 3
    assert h.bars[-1].close == pytest.approx(1018.0)
    assert h.currency == "points"
    assert h.source == "ssi_index"


def test_vndirect_index_source_points():
    s = VNDirectIndexSource(http_get=_get(_bare_udf()))
    h = s.get_history("VNINDEX", Interval.D1, *WIDE)
    assert h.currency == "points"
    assert h.bars[0].close == pytest.approx(1005.0)
    assert h.source == "vndirect_index"


def test_adjustment_policy_is_raw_for_index_values():
    # Index VALUES are not split/dividend adjusted — RAW, not PROVIDER_ADJUSTED.
    s = VPSIndexSource(http_get=_get(_bare_udf()))
    h = s.get_history("VNINDEX", Interval.D1, *WIDE)
    assert h.adjustment_policy is AdjustmentPolicy.RAW


def test_volume_preserved_as_shares():
    s = VPSIndexSource(http_get=_get(_bare_udf()))
    h = s.get_history("VNINDEX", Interval.D1, *WIDE)
    assert h.bars[0].volume == 100_000_000


def test_per_source_symbol_aliasing():
    # Canonical UPCOM -> VPS 'UPCOMINDEX', VNDIRECT 'UPCOM'; VNALLSHARE -> 'VNALL'.
    assert VPSIndexSource(http_get=_get("{}")).normalize_symbol("UPCOM") == "UPCOMINDEX"
    assert VPSIndexSource(http_get=_get("{}")).normalize_symbol("VNALLSHARE") == "VNALL"
    assert VNDirectIndexSource(http_get=_get("{}")).normalize_symbol("UPCOM") == "UPCOM"
    assert VNDirectIndexSource(http_get=_get("{}")).normalize_symbol("VNALLSHARE") == "VNALL"
    assert SSIIndexSource(http_get=_get("{}")).normalize_symbol("VNALLSHARE") == "VNALL"
    # Canonical pass-through for the common indices.
    assert VPSIndexSource(http_get=_get("{}")).normalize_symbol("vnindex") == "VNINDEX"


def test_provider_symbol_recorded_after_aliasing():
    s = VPSIndexSource(http_get=_get(_bare_udf()))
    h = s.get_history("UPCOM", Interval.D1, *WIDE)
    # Symbol the user asked for stays VNINDEX-style canonical-uppercased; provider_symbol
    # is the aliased provider symbol actually sent.
    assert h.provider_symbol == "UPCOMINDEX"


def test_no_data_status_raises_empty():
    s = VPSIndexSource(http_get=_get(_bare_udf(status="no_data")))
    with pytest.raises(EmptyData):
        s.get_history("VNINDEX", Interval.D1, *WIDE)


def test_empty_rows_raise_empty():
    s = VPSIndexSource(http_get=_get(_bare_udf(rows=[])))
    with pytest.raises(EmptyData):
        s.get_history("VNINDEX", Interval.D1, *WIDE)


def test_malformed_scalar_raises_invalid():
    payload = json.dumps(
        {"symbol": "VNINDEX", "s": "ok", "t": [_ts("2024-06-10")], "o": [1000.0],
         "h": [1010.0], "l": [995.0], "c": [None], "v": [100]}
    )
    with pytest.raises(InvalidData):
        VPSIndexSource(http_get=_get(payload)).get_history("VNINDEX", Interval.D1, *WIDE)


def test_transport_error_wrapped_unavailable():
    s = VPSIndexSource(http_get=_raising(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        s.get_history("VNINDEX", Interval.D1, *WIDE)


# ------------------- B2: index sources must stay POINT-scaled -----------------
# Indices are POINTS, never VND. The index adapters must never apply the x1000
# equity price scaling. Guard against a misconfigured/wrong-scaled index source
# silently returning 1000x-corrupted, plausible-looking values.


def test_all_default_index_sources_are_point_scaled():
    # Every adapter in the index failover chain must use PRICE_SCALE == 1.0 and
    # advertise 'points', so no x1000 equity scaling can ever apply to an index.
    for cls in (VPSIndexSource, SSIIndexSource, VNDirectIndexSource):
        assert cls.PRICE_SCALE == 1.0, f"{cls.__name__} is not point-scaled"
        assert cls.CURRENCY == "points"


def test_index_source_rejects_non_point_scale_instead_of_corrupting():
    """A misconfigured index source (x1000 equity scale) must raise a stable
    VnfinError, NOT silently return 1000x-inflated index values."""

    class _MisscaledIndexSource(VPSIndexSource):
        PRICE_SCALE = 1000.0  # wrong for an index — would corrupt points -> VND

    s = _MisscaledIndexSource(http_get=_get(_bare_udf()))
    with pytest.raises(VnfinError):
        s.get_history("VNINDEX", Interval.D1, *WIDE)


def test_misscaled_index_source_does_not_return_inflated_close():
    """Belt-and-suspenders: confirm the guard fires before any 1000x value escapes."""

    class _MisscaledIndexSource(VPSIndexSource):
        PRICE_SCALE = 1000.0

    s = _MisscaledIndexSource(http_get=_get(_bare_udf()))
    try:
        h = s.get_history("VNINDEX", Interval.D1, *WIDE)
    except VnfinError:
        return  # guard fired — correct
    pytest.fail(f"misscaled index source silently returned close={h.bars[0].close}")


# ----------------------------- IndexClient ----------------------------------


def test_index_client_failover_order_default():
    c = IndexClient()
    assert [s.name for s in c._client.sources] == ["vps_index", "ssi_index", "vndirect_index"]


def test_index_client_history_returns_pricehistory():
    c = IndexClient(http_get=_get(_bare_udf()))
    h = c.index_history("VNINDEX", date(2024, 6, 1), date(2024, 6, 30))
    assert h.currency == "points"
    assert len(h) == 3
    # source is the first that succeeded in the index chain
    assert h.source == "vps_index"
    assert h.attempts[-1].ok is True


def test_index_client_failover_to_second_source():
    # First source (vps) raises transport error -> fail over to ssi (envelope).
    def router(url, params, headers):
        if "vps.com.vn" in url:
            raise ConnectionError("vps down")
        return _ssi_envelope()

    c = IndexClient(http_get=router)
    h = c.index_history("VNINDEX", date(2024, 6, 1), date(2024, 6, 30))
    assert h.source == "ssi_index"
    assert h.attempts[0].ok is False
    assert h.attempts[-1].ok is True


def test_module_level_index_history():
    h = index_history("VNINDEX", date(2024, 6, 1), date(2024, 6, 30), http_get=_get(_bare_udf()))
    assert h.currency == "points"
    assert len(h) == 3


# ------------------------- B1: date-argument validation ----------------------
# Public API must never leak a raw TypeError/ValueError when dates are omitted or
# inverted; it must raise a stable VnfinError BEFORE any source/failover call.


def test_index_history_missing_both_dates_raises_vnfin_error():
    # Was the B1 bug: omitting dates reached datetime.combine(None) -> raw TypeError.
    c = IndexClient(http_get=_get(_bare_udf()))
    with pytest.raises(VnfinError):
        c.index_history("VNINDEX")


def test_index_history_missing_start_raises_vnfin_error():
    c = IndexClient(http_get=_get(_bare_udf()))
    with pytest.raises(VnfinError):
        c.index_history("VNINDEX", end=date(2024, 6, 30))


def test_index_history_missing_end_raises_vnfin_error():
    c = IndexClient(http_get=_get(_bare_udf()))
    with pytest.raises(VnfinError):
        c.index_history("VNINDEX", start=date(2024, 6, 1))


def test_index_history_reversed_range_raises_vnfin_error():
    c = IndexClient(http_get=_get(_bare_udf()))
    with pytest.raises(VnfinError):
        c.index_history("VNINDEX", date(2024, 6, 30), date(2024, 6, 1))


def test_index_history_missing_dates_does_not_leak_typeerror():
    # Stronger than the above: assert it is NOT a bare TypeError/ValueError escaping.
    c = IndexClient(http_get=_get(_bare_udf()))
    with pytest.raises(VnfinError):
        try:
            c.index_history("VNINDEX")
        except (TypeError, ValueError) as exc:  # pragma: no cover - guard
            if not isinstance(exc, VnfinError):
                pytest.fail(f"leaked raw {type(exc).__name__}: {exc}")
            raise


def test_module_level_index_history_missing_dates_raises_vnfin_error():
    with pytest.raises(VnfinError):
        index_history("VNINDEX", http_get=_get(_bare_udf()))


def test_index_history_valid_range_still_works_after_validation():
    # Sanity: validation does not reject a valid window.
    c = IndexClient(http_get=_get(_bare_udf()))
    h = c.index_history("VNINDEX", date(2024, 6, 1), date(2024, 6, 30))
    assert len(h) == 3


# ========================== (b) CONSTITUENTS =================================


def test_constituents_source_parses_members():
    s = IndexConstituentsSource(http_get=_get(_constituents_payload()))
    res = s.get_constituents("VN30")
    assert isinstance(res, IndexConstituents)
    assert res.index == "VN30"
    assert res.symbols == ("TESTCO", "ZZZ", "FAKE1")
    assert len(res) == 3
    assert isinstance(res.members[0], IndexMember)
    assert res.members[0].symbol == "TESTCO"
    assert res.members[0].exchange == "HOSE"


def test_constituents_carry_source_and_fetched_at():
    s = IndexConstituentsSource(http_get=_get(_constituents_payload()))
    res = s.get_constituents("VN30")
    assert res.source == "ssi_iboard_query"
    assert res.fetched_at_utc is not None
    assert res.fetched_at_utc.tzinfo is not None


def test_constituents_group_aliasing():
    # Canonical HNXINDEX maps to provider group 'HNXIndex' (case-sensitive).
    s = IndexConstituentsSource(http_get=_get(_constituents_payload()))
    assert s.normalize_group("HNXINDEX") == "HNXIndex"
    assert s.normalize_group("vn30") == "VN30"


def test_constituents_no_weights_flag():
    s = IndexConstituentsSource(http_get=_get(_constituents_payload()))
    res = s.get_constituents("VN30")
    # Weights are not exposed by this endpoint — must be explicitly None, not fabricated.
    assert res.has_weights is False
    assert res.members[0].weight is None


def test_constituents_empty_data_raises_empty():
    s = IndexConstituentsSource(http_get=_get(_constituents_payload(members=[])))
    with pytest.raises(EmptyData):
        s.get_constituents("VN30")


def test_constituents_error_code_raises_empty():
    payload = json.dumps({"code": "ERROR", "message": "bad group", "data": None})
    with pytest.raises(EmptyData):
        IndexConstituentsSource(http_get=_get(payload)).get_constituents("NOPE")


def test_constituents_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        IndexConstituentsSource(http_get=_get("<html>nope</html>")).get_constituents("VN30")


def test_constituents_missing_symbol_field_raises_invalid():
    payload = json.dumps(
        {"code": "SUCCESS", "message": "ok", "data": [{"exchange": "hose"}]}  # no stockSymbol
    )
    with pytest.raises(InvalidData):
        IndexConstituentsSource(http_get=_get(payload)).get_constituents("VN30")


def test_constituents_transport_error_wrapped():
    s = IndexConstituentsSource(http_get=_raising(ConnectionError("down")))
    with pytest.raises(SourceUnavailable):
        s.get_constituents("VN30")


def test_index_client_constituents_convenience():
    c = IndexClient(http_get=_get(_constituents_payload()))
    res = c.constituents("VN30")
    assert res.symbols == ("TESTCO", "ZZZ", "FAKE1")


def test_module_level_index_constituents():
    res = index_constituents("VN30", http_get=_get(_constituents_payload()))
    assert res.index == "VN30"
    assert res.symbols == ("TESTCO", "ZZZ", "FAKE1")


def test_constituents_to_dataframe():
    res = IndexConstituentsSource(http_get=_get(_constituents_payload())).get_constituents("VN30")
    df = res.to_dataframe()
    assert list(df["symbol"]) == ["TESTCO", "ZZZ", "FAKE1"]
    assert df.attrs["index"] == "VN30"
    assert df.attrs["source"] == "ssi_iboard_query"
