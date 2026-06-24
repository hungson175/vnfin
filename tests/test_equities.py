"""Tests for vnfin.equities — the VN equity universe (SSI iBoard group endpoint).

Synthetic fixtures only: hand-crafted JSON that matches the provider JSON *shape*
(SUCCESS envelope, ``data`` list of stock objects) but uses OBVIOUSLY-FAKE symbols
(TESTCO/ZZZ/FAKE1) and FABRICATED numbers. No real provider rows are copied here —
real provenance values live only in docs/research. The one real-endpoint probe is
opt-in in ``live_tests/`` (VNFIN_LIVE=1), never in the default suite.

The universe enumerates investable equities per board with per-symbol reference
metadata + honest coverage diagnostics (it is NOT a screener/ranker/advisor).
"""
from __future__ import annotations

import json

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable
from vnfin.equities import (
    EquitySecurity,
    EquityUniverse,
    SsiIboardUniverseSource,
    source,
    universe,
)


# ----------------------------- synthetic fixtures -----------------------------


def _row(sym, exch="HOSE", *, stock_type="s", **overrides):
    """One OBVIOUSLY-FAKE stock-group row. Shape matches the provider; values fake."""
    row = {
        "stockSymbol": sym,
        "exchange": exch,
        "market": exch,
        "stockType": stock_type,
        "companyNameEn": f"{sym} Corp",
        "companyNameVi": f"Cong ty {sym}",
        "isin": f"VN000000{sym}",
        "adminStatus": "NORMAL",
        "parValue": 10000,
        "tradingCurrencyISOCode": "VND",
        "firstTradingDate": "0",
    }
    row.update(overrides)
    return row


def _payload(rows=None, code="SUCCESS"):
    if rows is None:
        rows = [_row("TESTCO"), _row("ZZZ"), _row("FAKE1")]
    return json.dumps({"code": code, "message": "ok", "data": rows})


def _get(text):
    def _g(url, params, headers):
        return text

    return _g


def _raising(exc):
    def _g(url, params, headers):
        raise exc

    return _g


def _board_router(by_board):
    """Route the request to a per-board payload by inspecting the URL token."""
    tokens = {"VNINDEX": "HOSE", "HnxIndex": "HNX", "HNXUpcomIndex": "UPCOM"}

    def _g(url, params, headers):
        for token, board in tokens.items():
            if url.endswith("/" + token):
                return by_board[board]
        raise AssertionError(f"unexpected url {url}")

    return _g


# --------------------------- (1) stockType filter -----------------------------


def test_only_equity_rows_kept_others_dropped():
    rows = [
        _row("TESTCO", stock_type="s"),
        _row("WARR1", stock_type="w"),   # covered warrant -> dropped
        _row("ETF1", stock_type="e"),    # ETF -> dropped
        _row("MFND1", stock_type="m"),   # fund -> dropped
        _row("FAKE1", stock_type="s"),
    ]
    res = source(http_get=_get(_payload(rows))).universe("HOSE")
    assert res.symbols == ("TESTCO", "FAKE1")


# --------------------------- (2) optional -> None -----------------------------


def test_missing_optional_fields_are_none_not_fabricated():
    row = {
        "stockSymbol": "FAKE1",
        "exchange": "HOSE",
        "stockType": "s",
        # no companyNameEn/Vi, no isin, no parValue, no currency, no adminStatus
    }
    res = source(http_get=_get(_payload([row]))).universe("HOSE")
    sec = res.securities[0]
    assert sec.symbol == "FAKE1"
    assert sec.company_name_en is None
    assert sec.company_name_vi is None
    assert sec.isin is None
    assert sec.par_value is None
    assert sec.currency is None
    assert sec.listing_status is None


def test_blank_optional_strings_are_none():
    row = _row("FAKE1", companyNameEn="", companyNameVi="   ", isin="")
    res = source(http_get=_get(_payload([row]))).universe("HOSE")
    sec = res.securities[0]
    assert sec.company_name_en is None
    assert sec.company_name_vi is None
    assert sec.isin is None


def test_par_value_parsed_to_number():
    row = _row("FAKE1", parValue=10000)
    res = source(http_get=_get(_payload([row]))).universe("HOSE")
    assert res.securities[0].par_value == pytest.approx(10000.0)


# ------------------------ (3) envelope guards ---------------------------------


def test_non_success_code_raises_invalid():
    with pytest.raises(InvalidData):
        source(http_get=_get(_payload(code="ERROR"))).universe("HOSE")


@pytest.mark.parametrize("data", [{}, "", 0, False, None])
def test_data_not_a_list_raises_invalid(data):
    payload = json.dumps({"code": "SUCCESS", "data": data})
    with pytest.raises(InvalidData, match="not a list"):
        source(http_get=_get(payload)).universe("HOSE")


def test_empty_data_raises_empty():
    with pytest.raises(EmptyData):
        source(http_get=_get(_payload(rows=[]))).universe("HOSE")


def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        source(http_get=_get("<html>nope</html>")).universe("HOSE")


# ---------------------- (4) within-board duplicate ----------------------------


def test_duplicate_symbol_within_one_board_raises_invalid():
    rows = [_row("FAKE1"), _row("fake1")]  # canonicalize to same symbol
    with pytest.raises(InvalidData):
        source(http_get=_get(_payload(rows))).universe("HOSE")


def test_malformed_symbol_rejected():
    with pytest.raises(InvalidData):
        source(http_get=_get(_payload([_row("FA KE")]))).universe("HOSE")


def test_missing_symbol_field_raises_invalid():
    row = {"exchange": "HOSE", "stockType": "s"}
    with pytest.raises(InvalidData):
        source(http_get=_get(_payload([row]))).universe("HOSE")


# ----------------- (5) cross-board duplicate (exchange=None) ------------------


def test_cross_board_duplicate_kept_first_with_warning_no_raise():
    by_board = {
        "HOSE": _payload([_row("DUP", "HOSE"), _row("HOSEONLY", "HOSE")]),
        "HNX": _payload([_row("DUP", "HNX"), _row("HNXONLY", "HNX")]),
        "UPCOM": _payload([_row("UPONLY", "UPCOM")]),
    }
    res = universe(http_get=_board_router(by_board))
    # keep-first: DUP kept from HOSE, dropped from HNX
    assert res.symbols.count("DUP") == 1
    assert "HOSEONLY" in res.symbols and "HNXONLY" in res.symbols and "UPONLY" in res.symbols
    assert any(w.startswith("cross_board_duplicate_symbol") for w in res.warnings)
    # the DUP kept is the HOSE one (board order HOSE, HNX, UPCOM)
    dup = next(s for s in res.securities if s.symbol == "DUP")
    assert dup.exchange == "HOSE"


# ------------------- (6) honest-gap warnings always present -------------------


def test_three_honest_gap_warnings_always_present_single_board():
    res = source(http_get=_get(_payload())).universe("HOSE")
    prefixes = [w.split(":", 1)[0] for w in res.warnings]
    assert "partial_universe_coverage" in prefixes
    assert "listing_date_not_available" in prefixes
    assert "sector_not_available" in prefixes
    # board attributed in the detail
    assert any("HOSE" in w for w in res.warnings)


# ------------------------ (7) board-token aliasing ----------------------------


def test_board_token_aliasing_hits_correct_token():
    seen = {}

    def _capture(url, params, headers):
        seen["url"] = url
        return _payload()

    source(http_get=_capture).universe("HOSE")
    assert seen["url"].endswith("/VNINDEX")
    source(http_get=_capture).universe("HNX")
    assert seen["url"].endswith("/HnxIndex")
    source(http_get=_capture).universe("UPCOM")
    assert seen["url"].endswith("/HNXUpcomIndex")


def test_board_normalized_padded_lowercase():
    seen = {}

    def _capture(url, params, headers):
        seen["url"] = url
        return _payload()

    source(http_get=_capture).universe("  hose  ")
    assert seen["url"].endswith("/VNINDEX")


def test_unknown_board_raises_before_network():
    s = source(http_get=_raising(AssertionError("HTTP called for unknown board")))
    with pytest.raises((InvalidData, ValueError)):
        s.universe("NASDAQ")


@pytest.mark.parametrize("bad_board", [123, ["HOSE"], object()])
def test_non_string_board_raises_before_network(bad_board):
    s = source(http_get=_raising(AssertionError("HTTP called for non-string board")))
    with pytest.raises((InvalidData, ValueError)):
        s.universe(bad_board)


def test_non_dict_response_raises_invalid():
    with pytest.raises(InvalidData, match="unexpected response shape"):
        source(http_get=_get(json.dumps([1, 2, 3]))).universe("HOSE")


def test_non_object_row_raises_invalid():
    payload = json.dumps({"code": "SUCCESS", "data": ["not-an-object"]})
    with pytest.raises(InvalidData, match="not an object"):
        source(http_get=_get(payload)).universe("HOSE")


def test_all_rows_non_equity_raises_empty():
    rows = [_row("WARR1", stock_type="w"), _row("ETF1", stock_type="e")]
    with pytest.raises(EmptyData):
        source(http_get=_get(_payload(rows))).universe("HOSE")


def test_blank_par_value_is_none():
    res = source(http_get=_get(_payload([_row("FAKE1", parValue="")]))).universe("HOSE")
    assert res.securities[0].par_value is None


def test_zero_par_value_is_none():
    res = source(http_get=_get(_payload([_row("FAKE1", parValue=0)]))).universe("HOSE")
    assert res.securities[0].par_value is None


def test_negative_par_value_is_none():
    # #167 / sibling data-integrity guard: a non-positive provider value is not a
    # meaningful par value and must never be served as trusted (parse_provider_float
    # alone would let a sign through) -> coerced to None.
    res = source(http_get=_get(_payload([_row("FAKE1", parValue=-10000)]))).universe("HOSE")
    assert res.securities[0].par_value is None


# ----------------------- (8) exchange=None merges all -------------------------


def test_exchange_none_merges_all_three_boards():
    by_board = {
        "HOSE": _payload([_row("HOSE1", "HOSE")]),
        "HNX": _payload([_row("HNX1", "HNX")]),
        "UPCOM": _payload([_row("UP1", "UPCOM")]),
    }
    res = universe(http_get=_board_router(by_board))
    assert set(res.symbols) == {"HOSE1", "HNX1", "UP1"}
    assert res.board == "ALL"
    # every board's honest-gap tokens are attributed in the merged result
    for board in ("HOSE", "HNX", "UPCOM"):
        assert any(w.startswith("partial_universe_coverage") and board in w for w in res.warnings)
        assert any(w.startswith("listing_date_not_available") and board in w for w in res.warnings)
        assert any(w.startswith("sector_not_available") and board in w for w in res.warnings)


def test_exchange_none_no_cross_board_dup_has_no_dup_warning():
    by_board = {
        "HOSE": _payload([_row("HOSE1", "HOSE")]),
        "HNX": _payload([_row("HNX1", "HNX")]),
        "UPCOM": _payload([_row("UP1", "UPCOM")]),
    }
    res = universe(http_get=_board_router(by_board))
    assert not any(w.startswith("cross_board_duplicate_symbol") for w in res.warnings)


# ------------- (8b) #189 board_unavailable skip-and-warn on merge -------------
#
# The merge skip path discriminates on the concrete ``SourceError`` SUBTYPE that
# ``_fetch_board`` raises (its ``{ExcType}``). The fake ``http_get`` is wrapped by the
# transport layer, which re-wraps any in-callable raise as ``SourceUnavailable`` — that
# would hide the real subtype. So these tests inject at the ``_fetch_board`` boundary:
# ``_patch_fetch_board`` returns a stand-in that serves a real per-board universe for
# the healthy boards and re-raises the designated ``SourceError`` for the down board(s).


def _patch_fetch_board(monkeypatch, src, *, payloads=None, raising=None):
    """Patch ``src._fetch_board`` to raise per-board ``SourceError`` (``raising``) or to
    return that board's real universe parsed from ``payloads`` (synthetic), so the merge
    sees the concrete exception subtype unwrapped."""
    payloads = payloads or {}
    raising = raising or {}
    real_fetch = SsiIboardUniverseSource._fetch_board

    def _fake(self, board):
        if board in raising:
            raise raising[board]
        parsed = source(http_get=_get(payloads[board]))
        return real_fetch(parsed, board)

    monkeypatch.setattr(src, "_fetch_board", _fake.__get__(src, type(src)))


def test_exchange_none_skips_unavailable_board_and_warns(monkeypatch):
    s = source(http_get=_raising(AssertionError("merge must go through _fetch_board")))
    _patch_fetch_board(
        monkeypatch,
        s,
        payloads={
            "HOSE": _payload([_row("HOSE1", "HOSE")]),
            "UPCOM": _payload([_row("UP1", "UPCOM")]),
        },
        raising={"HNX": SourceUnavailable("ssi_iboard_universe: HNX boom")},
    )
    res = s.universe()
    # partial failure does NOT abort the merge
    assert res.board == "ALL"
    assert set(res.symbols) == {"HOSE1", "UP1"}
    # the skipped board is disclosed with a board_unavailable warning
    assert any(w.startswith("board_unavailable: HNX") for w in res.warnings)
    # a skipped board contributes NONE of its 3 honest-gap tokens
    assert not any(w.startswith("partial_universe_coverage") and "HNX" in w for w in res.warnings)
    assert not any(w.startswith("listing_date_not_available") and "HNX" in w for w in res.warnings)
    assert not any(w.startswith("sector_not_available") and "HNX" in w for w in res.warnings)
    # the surviving boards still attribute their honest-gap tokens
    for board in ("HOSE", "UPCOM"):
        assert any(w.startswith("partial_universe_coverage") and board in w for w in res.warnings)


def test_exchange_none_all_boards_unavailable_raises(monkeypatch):
    s = source(http_get=_raising(AssertionError("merge must go through _fetch_board")))
    _patch_fetch_board(
        monkeypatch,
        s,
        raising={
            "HOSE": SourceUnavailable("ssi_iboard_universe: HOSE down"),
            "HNX": EmptyData("ssi_iboard_universe: HNX empty"),
            "UPCOM": SourceUnavailable("ssi_iboard_universe: UPCOM down"),
        },
    )
    # all three boards raised → re-raise the LAST SourceError, never a silent empty universe
    with pytest.raises(SourceUnavailable):
        s.universe()


def test_single_board_unavailable_still_raises(monkeypatch):
    # exchange="HNX" asks for exactly that board; on failure it STILL raises (merge-only skip).
    s = source(http_get=_raising(AssertionError("single board must go through _fetch_board")))
    _patch_fetch_board(
        monkeypatch,
        s,
        raising={"HNX": SourceUnavailable("ssi_iboard_universe: HNX boom")},
    )
    with pytest.raises(SourceUnavailable):
        s.universe("HNX")


def test_board_unavailable_token_format_stable(monkeypatch):
    s = source(http_get=_raising(AssertionError("merge must go through _fetch_board")))
    _patch_fetch_board(
        monkeypatch,
        s,
        payloads={
            "HOSE": _payload([_row("HOSE1", "HOSE")]),
            "UPCOM": _payload([_row("UP1", "UPCOM")]),
        },
        raising={"HNX": EmptyData("ssi_iboard_universe: no equities for board HNX")},
    )
    res = s.universe()
    tok = next(w for w in res.warnings if w.startswith("board_unavailable:"))
    # board_unavailable: {board} — fetch skipped ({ExcType}): {reason}
    assert tok.startswith("board_unavailable: HNX")
    assert "fetch skipped" in tok
    assert "(EmptyData)" in tok


# -------------------- (9) NAME-mislabel regression ---------------------------


def test_malformed_field_error_message_uses_ssi_iboard_universe_name():
    # a non-string exchange is a malformed-field contract violation; the error label
    # must be ssi_iboard_universe (NOT the index source's ssi_iboard_query).
    row = _row("FAKE1", exchange=["HOSE"])
    with pytest.raises(InvalidData) as exc:
        source(http_get=_get(_payload([row]))).universe("HOSE")
    msg = str(exc.value)
    assert "ssi_iboard_universe" in msg
    assert "ssi_iboard_query" not in msg


def test_source_name_is_ssi_iboard_universe():
    assert SsiIboardUniverseSource(http_get=_get(_payload())).name == "ssi_iboard_universe"
    res = source(http_get=_get(_payload())).universe("HOSE")
    assert res.source == "ssi_iboard_universe"


# --------------------------- (10) DataFrame / API ----------------------------


def test_to_dataframe_columns_and_attrs():
    res = source(http_get=_get(_payload())).universe("HOSE")
    df = res.to_dataframe()
    assert list(df["symbol"]) == ["TESTCO", "ZZZ", "FAKE1"]
    for col in (
        "symbol",
        "exchange",
        "company_name_en",
        "company_name_vi",
        "isin",
        "listing_status",
        "par_value",
        "currency",
    ):
        assert col in df.columns
    assert df.attrs["board"] == "HOSE"
    assert df.attrs["source"] == "ssi_iboard_universe"


def test_len_iter_symbols_property():
    res = source(http_get=_get(_payload())).universe("HOSE")
    assert len(res) == 3
    assert [s.symbol for s in res] == ["TESTCO", "ZZZ", "FAKE1"]
    assert res.symbols == ("TESTCO", "ZZZ", "FAKE1")
    assert isinstance(res, EquityUniverse)
    assert isinstance(res.securities[0], EquitySecurity)


def test_security_type_field_not_on_model():
    import dataclasses

    fields = {f.name for f in dataclasses.fields(EquitySecurity)}
    assert "security_type" not in fields
    assert "listing_date" not in fields


# --------------------------- transport / facade ------------------------------


def test_transport_error_wrapped_unavailable():
    s = source(http_get=_raising(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        s.universe("HOSE")


def test_module_level_universe_single_board():
    res = universe("HOSE", http_get=_get(_payload()))
    assert res.board == "HOSE"
    assert res.symbols == ("TESTCO", "ZZZ", "FAKE1")


def test_client_is_alias_of_source():
    import vnfin.equities as eq

    assert eq.client is eq.source


def test_fetched_at_utc_is_aware():
    res = source(http_get=_get(_payload())).universe("HOSE")
    assert res.fetched_at_utc is not None
    assert res.fetched_at_utc.tzinfo is not None
    assert res.as_of is None


# =============================================================================
# #195 — GICS sector classification (clean-room; derived by inverting the 10
# VNAllShare sector baskets through the existing IndexConstituentsSource).
#
# Synthetic baskets only — CI never hits iboard. The classifier takes an injected
# ``fetch_constituents`` callable (code -> IndexConstituents); the facade routes the
# 10 sector-group URLs + the 3 board URLs through one injected ``http_get`` stub.
# =============================================================================

from vnfin.exceptions import VnfinError  # noqa: E402
from vnfin.indices.models import IndexConstituents, IndexMember  # noqa: E402
from vnfin.equities.sectors import (  # noqa: E402
    _GICS_L1,
    _SECTOR_MAP_CACHE_TTL,
    SectorClassifier,
)
from vnfin.equities.models import EquitySector, GicsSector  # noqa: E402
import vnfin.equities as eq  # noqa: E402

# The 10 VNAllShare GICS L1 sector basket codes (clean-room: derived from the index
# registry, never from vnstock industry ids).
_SECTOR_CODES = (
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
)

# Expected GICS L1 code -> public MSCI/S&P name (asserted for ALL 10 in case 1).
_EXPECTED_GICS = {
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


def _members(symbols, exch="HOSE"):
    return tuple(
        IndexMember(symbol=s, exchange=exch, company_name=f"{s} Corp", isin=f"VN000000{s}")
        for s in symbols
    )


def _constituents(code, symbols):
    return IndexConstituents(
        index=code,
        source="ssi_iboard_query",
        members=_members(symbols),
        provider_group=code,
        warnings=("current_snapshot_only: ...", "weights_not_available: ..."),
    )


def _fake_fetch(baskets):
    """A synthetic ``fetch_constituents`` (code -> IndexConstituents) + a call counter.

    ``baskets`` maps sector code -> tuple of member symbols. Unlisted codes return an
    empty basket. Returns ``(fetch, calls)`` where ``calls`` is a list of fetched codes.
    """
    calls = []

    def _fetch(code):
        calls.append(code)
        return _constituents(code, baskets.get(code, ()))

    return _fetch, calls


# --------------------------- (1) known symbol mapped --------------------------


def test_classify_known_symbol_in_vnfin_basket():
    fetch, _ = _fake_fetch({"VNFIN": ("AAA", "BBB"), "VNIT": ("CCC",)})
    clf = SectorClassifier(fetch_constituents=fetch)
    got = clf.classify("AAA")
    assert got == ("VNFIN", "Financials", "GICS", "ssi_iboard_query")


def test_gics_l1_map_correct_for_all_ten_codes():
    # _GICS_L1 must carry EXACTLY the 10 codes with the public MSCI/S&P L1 names.
    assert set(_GICS_L1) == set(_SECTOR_CODES)
    for code, name in _EXPECTED_GICS.items():
        assert _GICS_L1[code] == name


# ----------------------- (2) unmapped HOSE -> all None ------------------------


def test_classify_unmapped_symbol_returns_none():
    fetch, _ = _fake_fetch({"VNFIN": ("AAA",)})
    clf = SectorClassifier(fetch_constituents=fetch)
    assert clf.classify("ZZZ") is None


def test_universe_with_sector_unmapped_hose_all_four_fields_none():
    # An unmapped HOSE symbol gets all 4 sector fields None as a unit (never fabricated).
    by_board = {
        "HOSE": _payload([_row("AAA", "HOSE"), _row("NOPE", "HOSE")]),
        "HNX": _payload([_row("HNX1", "HNX")]),
        "UPCOM": _payload([_row("UP1", "UPCOM")]),
    }
    fetch, _ = _fake_fetch({"VNFIN": ("AAA",)})
    res = universe(http_get=_board_router(by_board), with_sector=True, _fetch_constituents=fetch)
    nope = next(s for s in res.securities if s.symbol == "NOPE")
    assert nope.sector_code is None
    assert nope.sector_name is None
    assert nope.sector_scheme is None
    assert nope.sector_source is None
    aaa = next(s for s in res.securities if s.symbol == "AAA")
    assert aaa.sector_code == "VNFIN"
    assert aaa.sector_name == "Financials"
    assert aaa.sector_scheme == "GICS"
    assert aaa.sector_source == "ssi_iboard_query"
    assert any(w.startswith("sector_partial_coverage") for w in res.warnings)


# ----------------------- (3) HNX/UPCoM -> all None ----------------------------


def test_universe_with_sector_hnx_upcom_rows_all_four_none():
    by_board = {
        "HOSE": _payload([_row("AAA", "HOSE")]),
        "HNX": _payload([_row("HNX1", "HNX")]),
        "UPCOM": _payload([_row("UP1", "UPCOM")]),
    }
    fetch, _ = _fake_fetch({"VNFIN": ("AAA",)})  # baskets are HOSE-only by nature
    res = universe(http_get=_board_router(by_board), with_sector=True, _fetch_constituents=fetch)
    for sym in ("HNX1", "UP1"):
        sec = next(s for s in res.securities if s.symbol == sym)
        assert sec.sector_code is None
        assert sec.sector_name is None
        assert sec.sector_scheme is None
        assert sec.sector_source is None
    # coverage token present
    assert any(w.startswith("sector_partial_coverage") for w in res.warnings)


# ------------------- (4) by_sector + sectors() static -------------------------


def test_by_sector_code_and_name_case_insensitive_equivalent():
    fetch, _ = _fake_fetch({"VNFIN": ("AAA", "BBB", "CCC")})
    by_code = eq.by_sector("VNFIN", _fetch_constituents=fetch)
    by_name = eq.by_sector("financials", _fetch_constituents=fetch)
    by_code2 = eq.by_sector("vnfin", _fetch_constituents=fetch)
    assert isinstance(by_code, EquitySector)
    assert by_code.sector_code == "VNFIN"
    assert by_code.sector_name == "Financials"
    assert by_code.sector_scheme == "GICS"
    assert by_code.sector_source == "ssi_iboard_query"
    assert by_code.members == ("AAA", "BBB", "CCC")  # sorted
    assert by_name.members == by_code.members
    assert by_code2.members == by_code.members
    assert any(w.startswith("sector_partial_coverage") for w in by_code.warnings)


def test_sectors_static_ten_no_fetch():
    # sectors() is static from _GICS_L1 — no constituents fetch at all.
    def _boom(code):
        raise AssertionError("sectors() must NOT fetch any basket")

    secs = eq.sectors(_fetch_constituents=_boom)
    assert len(secs) == 10
    assert all(isinstance(s, GicsSector) for s in secs)
    # sorted by code
    assert [s.code for s in secs] == sorted(_SECTOR_CODES)
    by = {s.code: s.name for s in secs}
    assert by == _EXPECTED_GICS


def test_by_sector_unknown_raises_clear_error():
    fetch, _ = _fake_fetch({})
    with pytest.raises((InvalidData, ValueError)):
        eq.by_sector("NotASector", _fetch_constituents=fetch)


# ---------- (5) coverage token whenever sector data is served -----------------


def test_profile_returns_full_enriched_security_with_coverage_token():
    by_board = {
        "HOSE": _payload([_row("AAA", "HOSE")]),
        "HNX": _payload([_row("HNX1", "HNX")]),
        "UPCOM": _payload([_row("UP1", "UPCOM")]),
    }
    fetch, _ = _fake_fetch({"VNFIN": ("AAA",)})
    prof = eq.profile("AAA", http_get=_board_router(by_board), _fetch_constituents=fetch)
    assert isinstance(prof, EquitySecurity)
    # full enriched row — not a sector-only fragment (reuses EquitySecurity)
    assert prof.symbol == "AAA"
    assert prof.company_name_en == "AAA Corp"
    assert prof.sector_code == "VNFIN"
    assert prof.sector_name == "Financials"
    assert prof.sector_scheme == "GICS"
    assert prof.sector_source == "ssi_iboard_query"


def test_profile_unmapped_symbol_full_row_all_sector_none():
    by_board = {
        "HOSE": _payload([_row("NOPE", "HOSE")]),
        "HNX": _payload([_row("HNX1", "HNX")]),
        "UPCOM": _payload([_row("UP1", "UPCOM")]),
    }
    fetch, _ = _fake_fetch({"VNFIN": ("AAA",)})
    prof = eq.profile("NOPE", http_get=_board_router(by_board), _fetch_constituents=fetch)
    assert prof.symbol == "NOPE"
    assert prof.sector_code is None and prof.sector_name is None
    assert prof.sector_scheme is None and prof.sector_source is None


def test_profile_absent_symbol_raises_not_found_naming_symbol():
    by_board = {
        "HOSE": _payload([_row("AAA", "HOSE")]),
        "HNX": _payload([_row("HNX1", "HNX")]),
        "UPCOM": _payload([_row("UP1", "UPCOM")]),
    }
    fetch, _ = _fake_fetch({"VNFIN": ("AAA",)})
    with pytest.raises(VnfinError) as exc:
        eq.profile("MISSING", http_get=_board_router(by_board), _fetch_constituents=fetch)
    assert "MISSING" in str(exc.value)


# ------------------------ (6) overlap -> deterministic None -------------------


def test_overlap_symbol_in_two_baskets_is_none_and_disclosed():
    # DUP is synthesized into 2 baskets -> ambiguous -> None (never picked), disclosed.
    fetch, _ = _fake_fetch({"VNFIN": ("AAA", "DUP"), "VNIT": ("DUP", "CCC")})
    clf = SectorClassifier(fetch_constituents=fetch)
    assert clf.classify("DUP") is None
    # the single-basket symbols still classify
    assert clf.classify("AAA")[0] == "VNFIN"
    assert clf.classify("CCC")[0] == "VNIT"
    # overlap disclosed
    ov = clf.overlaps()
    assert "DUP" in ov
    assert set(ov["DUP"]) == {"VNFIN", "VNIT"}


def test_overlap_deterministic_across_reruns():
    baskets = {"VNFIN": ("DUP",), "VNIT": ("DUP",)}
    fetch1, _ = _fake_fetch(baskets)
    fetch2, _ = _fake_fetch(baskets)
    assert SectorClassifier(fetch_constituents=fetch1).classify("DUP") is None
    assert SectorClassifier(fetch_constituents=fetch2).classify("DUP") is None


def test_universe_with_sector_overlap_emits_named_disclosure_line():
    by_board = {
        "HOSE": _payload([_row("DUP", "HOSE")]),
        "HNX": _payload([_row("HNX1", "HNX")]),
        "UPCOM": _payload([_row("UP1", "UPCOM")]),
    }
    fetch, _ = _fake_fetch({"VNFIN": ("DUP",), "VNIT": ("DUP",)})
    res = universe(http_get=_board_router(by_board), with_sector=True, _fetch_constituents=fetch)
    dup = next(s for s in res.securities if s.symbol == "DUP")
    assert dup.sector_code is None  # overlap -> None, never picked
    overlap_lines = [
        w for w in res.warnings if w.startswith("sector_partial_coverage:") and "DUP" in w
    ]
    assert overlap_lines, "expected an overlap disclosure line naming the symbol"
    assert "baskets" in overlap_lines[0]


# ---------------------------- (7) caching -------------------------------------


def test_build_map_fetches_each_basket_exactly_once():
    fetch, calls = _fake_fetch({"VNFIN": ("AAA",)})
    clf = SectorClassifier(fetch_constituents=fetch)
    clf.classify("AAA")  # triggers the lazy build
    # exactly 10 baskets fetched, one per code, no duplicates
    assert len(calls) == 10
    assert sorted(calls) == sorted(_SECTOR_CODES)


def test_second_sector_call_within_ttl_does_not_refetch():
    fetch, calls = _fake_fetch({"VNFIN": ("AAA",)})
    clf = SectorClassifier(fetch_constituents=fetch)
    clf.classify("AAA")
    assert len(calls) == 10
    clf.classify("AAA")  # second call within TTL — no new fetch
    clf.classify("ZZZ")
    assert len(calls) == 10


def test_cache_ttl_default_is_six_hours():
    assert _SECTOR_MAP_CACHE_TTL == 21600.0


def test_cache_expiry_rebuilds_after_ttl():
    fetch, calls = _fake_fetch({"VNFIN": ("AAA",)})
    clock = {"t": 1000.0}
    clf = SectorClassifier(fetch_constituents=fetch, clock=lambda: clock["t"])
    clf.classify("AAA")
    assert len(calls) == 10
    clock["t"] += _SECTOR_MAP_CACHE_TTL + 1.0  # past the TTL
    clf.classify("AAA")
    assert len(calls) == 20  # rebuilt


# ------------------------ (9) plain universe() unchanged ----------------------


def test_plain_universe_default_does_not_fetch_baskets_and_keeps_sector_not_available():
    by_board = {
        "HOSE": _payload([_row("AAA", "HOSE")]),
        "HNX": _payload([_row("HNX1", "HNX")]),
        "UPCOM": _payload([_row("UP1", "UPCOM")]),
    }

    def _boom(code):
        raise AssertionError("plain universe() must NOT fetch any sector basket")

    res = universe(http_get=_board_router(by_board), _fetch_constituents=_boom)
    # default with_sector=False: sector fields stay None, sector_not_available retained,
    # NO sector_partial_coverage anywhere.
    prefixes = {w.split(":", 1)[0].strip() for w in res.warnings}
    assert "sector_not_available" in prefixes
    assert "sector_partial_coverage" not in prefixes
    for sec in res.securities:
        assert sec.sector_code is None
        assert sec.sector_scheme is None


def test_with_sector_swaps_sector_not_available_for_partial_coverage():
    by_board = {
        "HOSE": _payload([_row("AAA", "HOSE")]),
        "HNX": _payload([_row("HNX1", "HNX")]),
        "UPCOM": _payload([_row("UP1", "UPCOM")]),
    }
    fetch, _ = _fake_fetch({"VNFIN": ("AAA",)})
    res = universe(http_get=_board_router(by_board), with_sector=True, _fetch_constituents=fetch)
    prefixes = {w.split(":", 1)[0].strip() for w in res.warnings}
    # the per-board sector_not_available is REPLACED by sector_partial_coverage
    assert "sector_partial_coverage" in prefixes
    assert "sector_not_available" not in prefixes
    # the other honest-gap tokens are untouched
    assert "partial_universe_coverage" in prefixes
    assert "listing_date_not_available" in prefixes


def test_default_universe_unchanged_byte_for_byte():
    # Plain universe() with no sector kwargs is identical to the pre-#195 result.
    by_board = {
        "HOSE": _payload([_row("AAA", "HOSE")]),
        "HNX": _payload([_row("HNX1", "HNX")]),
        "UPCOM": _payload([_row("UP1", "UPCOM")]),
    }
    res = universe(http_get=_board_router(by_board))
    # 4 additive fields are present but default None (additive dataclass)
    sec = res.securities[0]
    assert sec.sector_code is None and sec.sector_name is None


# ------------------------ (10) offline-only / no network ----------------------


def test_classifier_default_fetch_is_index_constituents_source():
    # With no injected fetch, the default is a private IndexConstituentsSource bound method;
    # constructing the classifier must NOT touch the network.
    clf = SectorClassifier()
    assert callable(clf._fetch_constituents)


def test_classify_blank_symbol_returns_none():
    fetch, _ = _fake_fetch({"VNFIN": ("AAA",)})
    clf = SectorClassifier(fetch_constituents=fetch)
    assert clf.classify("aaa") == ("VNFIN", "Financials", "GICS", "ssi_iboard_query")
