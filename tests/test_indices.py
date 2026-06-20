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


# --- Issue #64: index history must return the canonical symbol, not the provider alias

def test_index_history_returns_canonical_symbol_not_provider_alias():
    s = VPSIndexSource(http_get=_get(_bare_udf()))
    h = s.get_history("UPCOM", Interval.D1, *WIDE)
    assert h.symbol == "UPCOM"
    assert h.provider_symbol == "UPCOMINDEX"


def test_index_client_history_returns_canonical_symbol():
    c = IndexClient(http_get=_get(_bare_udf()))
    h = c.index_history("UPCOM", date(2024, 6, 1), date(2024, 6, 30))
    assert h.symbol == "UPCOM"
    assert h.provider_symbol == "UPCOMINDEX"


def test_index_client_history_normalizes_lowercase_symbol():
    # Regression: callers may pass lowercase selectors; identity checks must compare
    # normalized/canonical symbols, not the raw caller string.
    c = IndexClient(http_get=_get(_bare_udf()))
    h = c.index_history("vnindex", date(2024, 6, 1), date(2024, 6, 30))
    assert h.symbol == "VNINDEX"
    assert h.provider_symbol == "VNINDEX"


def test_index_client_history_normalizes_lowercase_alias():
    c = IndexClient(http_get=_get(_bare_udf()))
    h = c.index_history("upcom", date(2024, 6, 1), date(2024, 6, 30))
    assert h.symbol == "UPCOM"
    assert h.provider_symbol == "UPCOMINDEX"


def test_no_data_status_raises_empty():
    s = VPSIndexSource(http_get=_get(_bare_udf(status="no_data")))
    with pytest.raises(EmptyData):
        s.get_history("VNINDEX", Interval.D1, *WIDE)


def test_empty_rows_raise_empty():
    s = VPSIndexSource(http_get=_get(_bare_udf(rows=[])))
    with pytest.raises(EmptyData):
        s.get_history("VNINDEX", Interval.D1, *WIDE)


def test_malformed_scalar_quarantined_lone_row_empty():
    # #186: a malformed scalar (null close) is quarantined (the row is dropped), never
    # served. A lone bad row leaves zero bars → EmptyData (a SourceError → failover-safe).
    payload = json.dumps(
        {"symbol": "VNINDEX", "s": "ok", "t": [_ts("2024-06-10")], "o": [1000.0],
         "h": [1010.0], "l": [995.0], "c": [None], "v": [100]}
    )
    with pytest.raises(EmptyData):
        VPSIndexSource(http_get=_get(payload)).get_history("VNINDEX", Interval.D1, *WIDE)


def test_transport_error_wrapped_unavailable():
    s = VPSIndexSource(http_get=_raising(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        s.get_history("VNINDEX", Interval.D1, *WIDE)


# ----- Issue #162 (+ #186): one public bar per calendar date for a D1 index source -----
# An index D1 source result must expose exactly one bar per calendar date. Identical
# same-date OHLCV duplicates dedupe deterministically (keep first) + a warning token.
# #186: a CONFLICTING same-date bar is no longer a hard raise — the whole date is
# QUARANTINED (dropped entirely, both bars removed; we can't tell which is right) and the
# rest of the series is served + a quarantine warning. The source only fails over when
# quarantined rows exceed the #186 threshold (systematically broken). Never a silent
# conflicting-row selection either way.

# Same date as the second _INDEX_ROWS bar, IDENTICAL OHLCV -> must dedupe to one bar.
_INDEX_ROWS_IDENTICAL_DUP = [
    ("2024-06-10", 1000.0, 1010.0, 995.0, 1005.0, 100_000_000),
    ("2024-06-11", 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),
    ("2024-06-11", 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),  # identical duplicate
    ("2024-06-12", 1012.0, 1020.0, 1008.0, 1018.0, 120_000_000),
]

# Same date, DIFFERENT OHLCV -> conflicting; #186 quarantines the whole 06-11 date.
_INDEX_ROWS_CONFLICTING_DUP = [
    ("2024-06-10", 1000.0, 1010.0, 995.0, 1005.0, 100_000_000),
    ("2024-06-11", 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),
    ("2024-06-11", 1007.0, 1016.0, 1003.0, 1013.0, 111_000_000),  # conflicting same date
    ("2024-06-12", 1012.0, 1020.0, 1008.0, 1018.0, 120_000_000),
]

# Every row non-positive -> quarantined count exceeds the #186 threshold -> the source is
# deemed systematically broken (InvalidData in the source path -> failover).
_INDEX_ROWS_SYSTEMICALLY_BAD = [
    ("2024-06-10", -1.0, -1.0, -1.0, -1.0, 100_000_000),
    ("2024-06-11", -1.0, -1.0, -1.0, -1.0, 110_000_000),
    ("2024-06-12", -1.0, -1.0, -1.0, -1.0, 120_000_000),
    ("2024-06-13", -1.0, -1.0, -1.0, -1.0, 130_000_000),
]


def test_index_identical_same_date_duplicate_deduped_with_warning():
    s = VPSIndexSource(http_get=_get(_bare_udf(rows=_INDEX_ROWS_IDENTICAL_DUP)))
    h = s.get_history("VNINDEX", Interval.D1, *WIDE)
    # 4 input rows with one identical duplicate -> 3 unique calendar-date bars.
    assert len(h.bars) == 3
    assert [b.time.date() for b in h.bars] == [
        date(2024, 6, 10), date(2024, 6, 11), date(2024, 6, 12)
    ]
    # exactly one bar per calendar date (no duplicates survive)
    assert len({b.time.date() for b in h.bars}) == len(h.bars)
    assert "deduped_duplicate_daily_index_bars" in h.warnings
    assert h.currency == "points"


def test_index_no_duplicate_has_no_dedup_warning():
    s = VPSIndexSource(http_get=_get(_bare_udf()))  # the clean 3-row fixture
    h = s.get_history("VNINDEX", Interval.D1, *WIDE)
    assert len(h.bars) == 3
    assert "deduped_duplicate_daily_index_bars" not in h.warnings


def test_index_conflicting_same_date_duplicate_quarantined_with_warning():
    # #186: an isolated conflicting same-date pair drops the WHOLE date (06-11); the other
    # two dates survive and a quarantine warning is surfaced. The #162 identical-dedupe
    # token must NOT fire (this is a conflict, not an identical duplicate).
    s = VPSIndexSource(http_get=_get(_bare_udf(rows=_INDEX_ROWS_CONFLICTING_DUP)))
    h = s.get_history("VNINDEX", Interval.D1, *WIDE)
    assert [b.time.date() for b in h.bars] == [date(2024, 6, 10), date(2024, 6, 12)]
    assert any("quarantined_invalid_bars" in w for w in h.warnings)
    assert "deduped_duplicate_daily_index_bars" not in h.warnings


def _udf_explicit_times(rows):
    # rows: (epoch_seconds, o, h, l, c, v) — lets a test put two bars on the SAME VN
    # calendar date at DIFFERENT intraday timestamps (#162 keys by date, not timestamp).
    return json.dumps({
        "s": "ok",
        "t": [r[0] for r in rows],
        "o": [r[1] for r in rows], "h": [r[2] for r in rows],
        "l": [r[3] for r in rows], "c": [r[4] for r in rows], "v": [r[5] for r in rows],
    })


# Two UTC instants that are the SAME VN (UTC+7) calendar date 2024-06-11 but different times.
_T_0611_A = int(datetime(2024, 6, 11, 1, 0, tzinfo=timezone.utc).timestamp())   # 08:00 VN
_T_0611_B = int(datetime(2024, 6, 11, 6, 0, tzinfo=timezone.utc).timestamp())   # 13:00 VN
_T_0612 = int(datetime(2024, 6, 12, 1, 0, tzinfo=timezone.utc).timestamp())


def test_index_same_date_different_timestamp_identical_ohlcv_deduped():
    # #162 reviewer case: same calendar date, DIFFERENT intraday timestamps (08:00/13:00),
    # IDENTICAL OHLCV -> must dedupe to ONE bar per date + warning (was surviving before).
    rows = [
        (_T_0611_A, 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),
        (_T_0611_B, 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),  # same date, other time
        (_T_0612, 1012.0, 1020.0, 1008.0, 1018.0, 120_000_000),
    ]
    s = VPSIndexSource(http_get=_get(_udf_explicit_times(rows)))
    h = s.get_history("VNINDEX", Interval.D1, *WIDE)
    assert [b.time.date() for b in h.bars] == [date(2024, 6, 11), date(2024, 6, 12)]
    assert len({b.time.date() for b in h.bars}) == len(h.bars)  # one bar per calendar date
    assert "deduped_duplicate_daily_index_bars" in h.warnings


def test_index_same_date_different_timestamp_conflicting_dropped_with_warning():
    # #186: same calendar date, different timestamps, CONFLICTING OHLCV -> the whole 06-11
    # date is quarantined (both intraday timestamps dropped); a clean other date survives.
    rows = [
        (_T_0611_A, 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),
        (_T_0611_B, 1007.0, 1016.0, 1003.0, 1013.0, 111_000_000),  # same date, conflicting
        (_T_0612, 1012.0, 1020.0, 1008.0, 1018.0, 120_000_000),    # clean other date survives
    ]
    s = VPSIndexSource(http_get=_get(_udf_explicit_times(rows)))
    h = s.get_history("VNINDEX", Interval.D1, *WIDE)
    assert [b.time.date() for b in h.bars] == [date(2024, 6, 12)]  # 06-11 dropped entirely
    assert any("quarantined_invalid_bars" in w for w in h.warnings)


def test_index_h1_same_date_different_timestamp_not_collapsed():
    # #162 must NOT collapse intraday: two H1 bars on the same calendar date at different
    # hours are distinct and must both survive (date-dedupe is D1-only; no daily warning).
    rows = [
        (_T_0611_A, 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),
        (_T_0611_B, 1008.0, 1018.0, 1004.0, 1016.0, 115_000_000),  # same date, later hour
    ]
    s = VPSIndexSource(http_get=_get(_udf_explicit_times(rows)))
    h = s.get_history("VNINDEX", Interval.H1, *WIDE)
    assert len(h.bars) == 2  # both intraday bars kept
    assert "deduped_duplicate_daily_index_bars" not in h.warnings


def test_index_h1_exact_duplicate_timestamp_dropped_with_warning():
    # Non-D1 keeps exact-timestamp keying (no date dedupe). #186: an exact-timestamp
    # duplicate drops that timestamp ENTIRELY (both rows quarantined); a distinct-hour bar
    # on the same date survives.
    rows = [
        (_T_0611_A, 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),
        (_T_0611_A, 1005.0, 1015.0, 1002.0, 1012.0, 110_000_000),  # exact same timestamp -> dropped
        (_T_0611_B, 1008.0, 1018.0, 1004.0, 1016.0, 115_000_000),  # distinct hour survives
    ]
    s = VPSIndexSource(http_get=_get(_udf_explicit_times(rows)))
    h = s.get_history("VNINDEX", Interval.H1, *WIDE)
    assert len(h.bars) == 1  # the duplicated timestamp dropped; the distinct-hour bar kept
    assert h.bars[0].time.date() == date(2024, 6, 11)
    assert h.bars[0].time.hour == 13  # _T_0611_B = 06:00 UTC = 13:00 VN (UTC+7)
    assert any("quarantined_invalid_bars" in w for w in h.warnings)


def test_index_isolated_conflict_quarantined_and_served_no_failover():
    # #186: an ISOLATED conflicting-duplicate date is quarantined (06-11 dropped) and the
    # rest of the vps series is served DIRECTLY — no failover (the source is not
    # systematically broken). The dropped date is surfaced via a quarantine warning.
    def router(url, params, headers):
        if "vps.com.vn" in url:
            return _bare_udf(rows=_INDEX_ROWS_CONFLICTING_DUP)
        return _ssi_envelope()

    c = IndexClient(http_get=router)
    h = c.index_history("VNINDEX", date(2024, 6, 1), date(2024, 6, 30))
    assert h.source == "vps_index"  # served from vps, NOT failed over to ssi
    assert [b.time.date() for b in h.bars] == [date(2024, 6, 10), date(2024, 6, 12)]
    assert any("quarantined_invalid_bars" in w for w in h.warnings)
    assert "deduped_duplicate_daily_index_bars" not in h.warnings


def test_index_systematically_broken_source_fails_over_to_next():
    # #186 threshold: when the in-range quality failures exceed max(_QUARANTINE_ABS_FLOOR,
    # _QUARANTINE_FRACTION * considered) over the in-range rows, the source is deemed
    # systematically broken — it raises InvalidData in the source path and the failover client
    # records that failed attempt and serves the clean ssi source (no silent partial-garbage).
    def router(url, params, headers):
        if "vps.com.vn" in url:
            return _bare_udf(rows=_INDEX_ROWS_SYSTEMICALLY_BAD)
        return _ssi_envelope()

    c = IndexClient(http_get=router)
    h = c.index_history("VNINDEX", date(2024, 6, 1), date(2024, 6, 30))
    assert h.source == "ssi_index"
    assert any(a.name == "vps_index" and not a.ok for a in h.attempts)
    assert "deduped_duplicate_daily_index_bars" not in h.warnings


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


# --- Issue #9: empty/malformed symbols must be rejected before failover -----------


@pytest.mark.parametrize("bad_symbol", ["", "   ", "\t", None, 123])
def test_index_history_rejects_empty_symbol_before_source_call(bad_symbol):
    calls = {"n": 0}

    def no_http(url, params, headers):
        calls["n"] += 1
        return _bare_udf()

    c = IndexClient(http_get=no_http)
    with pytest.raises(VnfinError):
        c.index_history(bad_symbol, date(2024, 6, 1), date(2024, 6, 30))
    assert calls["n"] == 0


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


@pytest.mark.parametrize(
    "data",
    [{}, "", 0, False, None],
    ids=["empty_dict", "empty_string", "zero", "false", "none"],
)
def test_constituents_malformed_data_container_raises_invalid(data):
    payload = json.dumps({"code": "SUCCESS", "data": data})
    with pytest.raises(InvalidData, match="not a list"):
        IndexConstituentsSource(http_get=_get(payload)).get_constituents("VN30")


def _constituents_member_payload(row: dict) -> str:
    return json.dumps({"code": "SUCCESS", "data": [row]})


@pytest.mark.parametrize(
    "row,match",
    [
        ({"stockSymbol": "FAKE1", "exchange": ["HOSE"], "companyNameEn": "Fake Co", "isin": "VN000FAKE"}, "exchange"),
        ({"stockSymbol": "FAKE1", "exchange": "HOSE", "companyNameEn": {"name": "Fake Co"}, "isin": "VN000FAKE"}, "companyNameEn"),
        ({"stockSymbol": "FAKE1", "exchange": "HOSE", "companyNameEn": "Fake Co", "isin": True}, "isin"),
    ],
)
def test_constituents_malformed_member_metadata_raises_invalid(row, match):
    with pytest.raises(InvalidData, match=match):
        IndexConstituentsSource(http_get=_get(_constituents_member_payload(row))).get_constituents("VN30")


def test_constituents_error_code_raises_invalid():
    payload = json.dumps({"code": "ERROR", "message": "bad group", "data": None})
    with pytest.raises(InvalidData):
        IndexConstituentsSource(http_get=_get(payload)).get_constituents("NOPE")


# --- Issue #54: constituents success envelope must require code == "SUCCESS" -----

def test_constituents_missing_code_raises_invalid():
    payload = json.dumps({"message": "ok", "data": [("TESTCO", "hose")]})
    with pytest.raises(InvalidData):
        IndexConstituentsSource(http_get=_get(payload)).get_constituents("VN30")


def test_constituents_null_code_raises_invalid():
    payload = json.dumps({"code": None, "message": "ok", "data": [("TESTCO", "hose")]})
    with pytest.raises(InvalidData):
        IndexConstituentsSource(http_get=_get(payload)).get_constituents("VN30")


def test_constituents_non_success_code_raises_invalid():
    payload = json.dumps({"code": "UNAUTHORIZED", "message": "bad group", "data": None})
    with pytest.raises(InvalidData):
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


# --- Issue #30: constituents must reject empty/duplicate normalized symbols --------

def test_constituents_empty_symbol_raises_invalid():
    payload = _constituents_payload(members=[("TESTCO", "hose"), ("", "hose")])
    with pytest.raises(InvalidData):
        IndexConstituentsSource(http_get=_get(payload)).get_constituents("VN30")


def test_constituents_whitespace_symbol_raises_invalid():
    payload = _constituents_payload(members=[("TESTCO", "hose"), ("   ", "hose")])
    with pytest.raises(InvalidData):
        IndexConstituentsSource(http_get=_get(payload)).get_constituents("VN30")


def test_constituents_duplicate_symbol_raises_invalid():
    payload = _constituents_payload(members=[("TESTCO", "hose"), ("testco", "hose")])
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


# --- Batch-1 issue #75: malformed index selectors ---------------------------


@pytest.mark.parametrize("bad_index", [None, "", "   ", 123, []])
def test_constituents_source_rejects_malformed_index_selector(bad_index):
    s = IndexConstituentsSource(http_get=_get(_constituents_payload()))
    with pytest.raises(InvalidData):
        s.get_constituents(bad_index)


@pytest.mark.parametrize("bad_index", [None, "", "   ", 123])
def test_index_client_constituents_rejects_malformed_index_selector(bad_index):
    c = IndexClient(http_get=_get(_constituents_payload()))
    with pytest.raises(InvalidData):
        c.constituents(bad_index)


# --------------------------------------------------------------------------- #
# Phase 4 #75/#30/#9 — security/index identifier contract on selectors + members.
# --------------------------------------------------------------------------- #
_BAD_SELECTORS = [None, 123, b"VN30", "", "   ", "VN 30", "VN/30", "VN\n30", "1VN", "VN$"]


@pytest.mark.parametrize("bad", _BAD_SELECTORS)
def test_constituents_source_malformed_selector_zero_http(bad):
    # #75: reject before URL construction -> http_get (which would assert) never runs.
    s = IndexConstituentsSource(http_get=_raising(AssertionError("HTTP called for invalid selector")))
    with pytest.raises(InvalidData):
        s.get_constituents(bad)


@pytest.mark.parametrize("bad", _BAD_SELECTORS)
def test_constituents_client_malformed_selector_zero_http(bad):
    with pytest.raises(InvalidData):
        IndexClient(http_get=_raising(AssertionError("HTTP called"))).constituents(bad)


@pytest.mark.parametrize("bad", _BAD_SELECTORS)
def test_constituents_facade_malformed_selector_zero_http(bad):
    with pytest.raises(InvalidData):
        index_constituents(bad, http_get=_raising(AssertionError("HTTP called")))


@pytest.mark.parametrize("bad", _BAD_SELECTORS)
def test_index_history_malformed_selector_zero_http(bad):
    with pytest.raises(InvalidData):
        IndexClient(http_get=_raising(AssertionError("HTTP called"))).index_history(bad)


def test_constituents_selector_normalizes_source_client_facade():
    p = _constituents_payload()
    assert IndexConstituentsSource(http_get=_get(p)).get_constituents("  vn30  ").index == "VN30"
    assert IndexClient(http_get=_get(p)).constituents("  vn30  ").index == "VN30"
    assert index_constituents("vn30", http_get=_get(p)).index == "VN30"


def test_constituents_hnxindex_alias_keeps_public_identity_and_provider_group():
    res = IndexConstituentsSource(http_get=_get(_constituents_payload())).get_constituents("hnxindex")
    assert res.index == "HNXINDEX"  # canonical public identity, not provider group
    assert res.provider_group == "HNXIndex"  # case-sensitive provider group preserved


def test_constituent_stocksymbol_normalizes_padded_lower():
    res = IndexConstituentsSource(
        http_get=_get(_constituents_payload(members=[(" fake1 ", "hose")]))
    ).get_constituents("VN30")
    assert res.symbols == ("FAKE1",)


@pytest.mark.parametrize("bad_sym", ["FA KE", "FA/KE", "FA.KE", "FA\nKE", "1FAKE", "FAKE$", 123, None])
def test_constituent_malformed_stocksymbol_rejected(bad_sym):
    with pytest.raises(InvalidData):
        IndexConstituentsSource(
            http_get=_get(_constituents_member_payload({"stockSymbol": bad_sym, "exchange": "hose"}))
        ).get_constituents("VN30")


def test_constituent_duplicate_after_canonicalization_rejected():
    # "fake1" and "FAKE1" canonicalize to the same symbol -> duplicate rejected.
    with pytest.raises(InvalidData):
        IndexConstituentsSource(
            http_get=_get(_constituents_payload(members=[("fake1", "hose"), ("FAKE1", "hose")]))
        ).get_constituents("VN30")


# --------------------------------------------------------------------------- #
# Issue #147 — index_history_stitched (opt-in long-window calendar-year stitching).
# --------------------------------------------------------------------------- #
from vnfin.models import PriceBar, PriceHistory


def _pb(d, close):
    return PriceBar(time=datetime(d.year, d.month, d.day, tzinfo=timezone.utc),
                    open=close, high=close, low=close, close=close, volume=1000)


def _idx_ph(symbol, bars, source, *, adj=AdjustmentPolicy.RAW, value_unit="points", currency="points"):
    return PriceHistory(symbol=symbol, interval=Interval.D1, adjustment_policy=adj,
                        source=source, bars=tuple(bars), currency=currency, value_unit=value_unit)


def _no_http(url, params=None, headers=None):
    raise AssertionError("no network expected")


class _FakeIdxSource:
    """Index source double: clean per-year bars, but raises OHLC-invariant for a bad year."""
    unit = "points"

    def __init__(self, name, bad_year=None):
        self._name = name
        self._bad_year = bad_year

    @property
    def name(self):
        return self._name

    def supports(self, interval):
        return interval is Interval.D1

    def get_history(self, symbol, interval, start, end):
        if self._bad_year is not None and start.year <= self._bad_year <= end.year:
            raise InvalidData(f"{self._name}: OHLC invariant violated in {self._bad_year}")
        bars = (_pb(start, 1000.0 + start.year), _pb(end, 1010.0 + end.year))
        return _idx_ph(symbol, bars, self._name)


def test_index_history_stitched_segment_failover():
    # source A is bad for 2018; B is clean -> 2018 segment falls over to B.
    a = _FakeIdxSource("idx_a", bad_year=2018)
    b = _FakeIdxSource("idx_b")
    c = IndexClient(sources=[a, b])
    h = c.index_history_stitched("vnindex", date(2016, 1, 1), date(2019, 12, 31))
    assert h.symbol == "VNINDEX" and h.source == "stitched_index_history"
    assert h.value_unit == "points" and h.adjustment_policy is AdjustmentPolicy.RAW
    dates = [bar.time.date() for bar in h.bars]
    assert dates == sorted(dates) and len(dates) == len(set(dates))  # strictly ascending, deduped
    assert any("segment 2018: idx_b" in w for w in h.warnings)       # 2018 served by B
    assert any("segment 2016: idx_a" in w for w in h.warnings)       # others by A


def test_index_history_stitched_rejects_non_daily():
    with pytest.raises(InvalidData, match="only daily"):
        IndexClient(http_get=_no_http).index_history_stitched(
            "VNINDEX", date(2016, 1, 1), date(2016, 12, 31), interval=Interval.H1)


def test_index_history_stitched_homogeneity_violation_raises(monkeypatch):
    c = IndexClient(http_get=_no_http)

    def fake(symbol, start, end, interval=Interval.D1):
        pol = AdjustmentPolicy.RAW if start.year == 2016 else AdjustmentPolicy.UNKNOWN
        return _idx_ph(symbol, (_pb(date(start.year, 6, 1), 100.0),), "src", adj=pol)

    monkeypatch.setattr(c, "index_history", fake)
    with pytest.raises(InvalidData, match="is not RAW"):
        c.index_history_stitched("VNINDEX", date(2016, 1, 1), date(2017, 12, 31))


def test_index_history_stitched_rejects_consistently_wrong_unit(monkeypatch):
    # B1: segments that are mutually CONSISTENT but uniformly WRONG (e.g. VND, not
    # points) must still fail — enforcement is absolute (points/points), not relative.
    c = IndexClient(http_get=_no_http)

    def fake(symbol, start, end, interval=Interval.D1):
        return _idx_ph(symbol, (_pb(date(start.year, 6, 1), 100.0),), "src",
                       value_unit="VND", currency="VND")

    monkeypatch.setattr(c, "index_history", fake)
    with pytest.raises(InvalidData, match="not index points"):
        c.index_history_stitched("VNINDEX", date(2016, 1, 1), date(2017, 12, 31))


def test_index_history_stitched_has_multi_source_warning():
    # B2: the result carries the explicit stitched_multi_source token.
    a = _FakeIdxSource("idx_a", bad_year=2018)
    b = _FakeIdxSource("idx_b")
    h = IndexClient(sources=[a, b]).index_history_stitched(
        "VNINDEX", date(2016, 1, 1), date(2019, 12, 31))
    assert "stitched_multi_source" in h.warnings


def test_index_history_stitched_conflicting_seam_raises(monkeypatch):
    c = IndexClient(http_get=_no_http)

    def fake(symbol, start, end, interval=Interval.D1):
        if start.year == 2016:
            bars = (_pb(date(2016, 6, 1), 100.0), _pb(date(2017, 1, 1), 111.0))  # boundary
        else:
            bars = (_pb(date(2017, 1, 1), 999.0), _pb(date(2017, 6, 1), 120.0))  # conflicting close
        return _idx_ph(symbol, bars, "src")

    monkeypatch.setattr(c, "index_history", fake)
    with pytest.raises(InvalidData, match="conflicting duplicate date"):
        c.index_history_stitched("VNINDEX", date(2016, 1, 1), date(2017, 12, 31))


def test_index_history_stitched_identical_seam_deduped(monkeypatch):
    c = IndexClient(http_get=_no_http)

    def fake(symbol, start, end, interval=Interval.D1):
        if start.year == 2016:
            bars = (_pb(date(2016, 6, 1), 100.0), _pb(date(2017, 1, 1), 111.0))
        else:
            bars = (_pb(date(2017, 1, 1), 111.0), _pb(date(2017, 6, 1), 120.0))  # identical boundary
        return _idx_ph(symbol, bars, "src")

    monkeypatch.setattr(c, "index_history", fake)
    h = c.index_history_stitched("VNINDEX", date(2016, 1, 1), date(2017, 12, 31))
    dates = [bar.time.date() for bar in h.bars]
    assert dates == sorted(dates) and len(dates) == len(set(dates))  # 2017-01-01 deduped once
    assert dates.count(date(2017, 1, 1)) == 1
