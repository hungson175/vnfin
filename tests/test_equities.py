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
