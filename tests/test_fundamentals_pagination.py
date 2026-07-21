"""TDD for #198 PHASE 2 — VNDirect statement pagination + AUTO atomic-query.

All fixtures are SYNTHETIC (fake symbols, fabricated round numbers) and mock the
HTTP layer via an injected ``http_get`` — no network. Covers §8 (pagination +
row-stream + metadata guards + helper contracts + the Explicit-vs-AUTO flows),
§9 (empty later page = InvalidData) and the §11 TDD bullets for Phase 2.

Clean-room: shapes learned only from the provider's own server + the research
doc; no vnstock or derivative material consulted.
"""
from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable
from vnfin.fundamentals import Period, StatementType, VNDirectFundamentalSource
from vnfin.fundamentals.vndirect import _Disposition


# --------------------------------------------------------------------------- #
# Synthetic envelope + paged-http_get helpers.
# --------------------------------------------------------------------------- #
def _row(code, item_code, value, fiscal_date, report_type="ANNUAL", model_type=2):
    return {
        "code": code,
        "itemCode": float(item_code),
        "reportType": report_type,
        "modelType": float(model_type),
        "numericValue": value,
        "fiscalDate": fiscal_date,
    }


def _env(rows, *, current_page=1, total_pages=1, include_total_pages=True, size=None):
    """A statement envelope with EXPLICIT pagination metadata.

    ``include_total_pages=False`` omits ``totalPages`` entirely (later pages may).
    """
    d = {
        "data": rows,
        "currentPage": current_page,
        "size": size if size is not None else len(rows),
        "totalElements": len(rows),
    }
    if include_total_pages:
        d["totalPages"] = total_pages
    return json.dumps(d)


def _model_of(q):
    m = re.search(r"modelType:(\d+)", q)
    return int(m.group(1)) if m else None


def _paged_get(pages_by_model, *, record=None):
    """Route each fetch by (requested modelType, requested page).

    ``pages_by_model``: {model_int: {page_int: envelope_text_or_callable}}.
    A missing (model, page) raises KeyError (an unexpected fetch = test bug).
    """

    def _g(url, params, headers):
        q = params["q"]
        model = _model_of(q)
        page = params.get("page", 1)
        if record is not None:
            record.append((model, page))
        entry = pages_by_model[model][page]
        return entry() if callable(entry) else entry

    return _g


def _src_paged(pages_by_model, *, record=None):
    return VNDirectFundamentalSource(http_get=_paged_get(pages_by_model, record=record))


A, B, C = "2025-12-31", "2024-12-31", "2023-12-31"


# =========================================================================== #
# Helper contract: _require_raw_int (§8, B6)
# =========================================================================== #
@pytest.mark.parametrize("bad", [True, False, 1.0, "1", "  ", None, [1], {"x": 1}])
def test_require_raw_int_rejects_non_raw_int(bad):
    with pytest.raises(InvalidData):
        VNDirectFundamentalSource._require_raw_int({"k": bad}, "k")


def test_require_raw_int_rejects_absent_key():
    with pytest.raises(InvalidData):
        VNDirectFundamentalSource._require_raw_int({}, "k")


@pytest.mark.parametrize("good", [0, 1, 2, 33])
def test_require_raw_int_accepts_raw_int(good):
    assert VNDirectFundamentalSource._require_raw_int({"k": good}, "k") == good


# =========================================================================== #
# Helper contract: _require_iso_fiscal_date (§8, R3)
# =========================================================================== #
def test_require_iso_fiscal_date_accepts_exact():
    assert VNDirectFundamentalSource._require_iso_fiscal_date({"fiscalDate": "2025-12-31"}) == "2025-12-31"


@pytest.mark.parametrize(
    "bad",
    [
        "2025-12-31 ",       # trailing space
        " 2025-12-31",       # leading space
        "2025-1-1",          # unpadded
        "2025-01-1",
        "2025/12/31",        # wrong sep
        "2025-99-99",        # malformed calendar
        "20251231",          # no sep
        date(2025, 12, 31),  # a date OBJECT, not a string
        123,
        None,
    ],
)
def test_require_iso_fiscal_date_rejects(bad):
    with pytest.raises(InvalidData):
        VNDirectFundamentalSource._require_iso_fiscal_date({"fiscalDate": bad})


def test_require_iso_fiscal_date_rejects_absent_key():
    with pytest.raises(InvalidData):
        VNDirectFundamentalSource._require_iso_fiscal_date({})


# =========================================================================== #
# Helper contract: _require_item_code (§8, R20 — reuse _item_code_str)
# =========================================================================== #
@pytest.mark.parametrize(
    "bad",
    [True, False, 11000.9, "11000.9", -5, -5.0, " 11000 ", "+11000", "011000", None, [11000], {}],
    ids=["true", "false", "frac", "fracstr", "neg", "negf", "ws", "signed", "leadzero", "null", "list", "dict"],
)
def test_require_item_code_rejects(bad):
    with pytest.raises(InvalidData):
        VNDirectFundamentalSource._require_item_code({"itemCode": bad})


@pytest.mark.parametrize("good,expected", [(11000.0, "11000"), (11000, "11000"), ("11000", "11000"), ("0", "0"), (0, "0")])
def test_require_item_code_accepts_canonical(good, expected):
    assert VNDirectFundamentalSource._require_item_code({"itemCode": good}) == expected


def test_require_item_code_rejects_absent_key():
    with pytest.raises(InvalidData):
        VNDirectFundamentalSource._require_item_code({})


def test_require_item_code_is_byte_identical_to_builder_key():
    # R20: the pagination key MUST equal the builder's _item_code_str key.
    for raw in (11000.0, 11000, "11000", "0"):
        assert (
            VNDirectFundamentalSource._require_item_code({"itemCode": raw})
            == VNDirectFundamentalSource._item_code_str(raw)
        )


# =========================================================================== #
# Helper contract: _row_disposition (§8, R8 + R12)
# =========================================================================== #
def _disp(row, *, psym="TESTCO", period=Period.ANNUAL, model_type=2):
    return VNDirectFundamentalSource._row_disposition(
        row, psym=psym, period=period, model_type=model_type
    )


def test_row_disposition_eligible():
    assert _disp(_row("TESTCO", 11000, 1.0, A)) is _Disposition.ELIGIBLE


def test_row_disposition_skip_cadence():
    assert _disp(_row("TESTCO", 11000, 1.0, A, report_type="QUARTER")) is _Disposition.SKIP_CADENCE


def test_row_disposition_skip_model():
    assert _disp(_row("TESTCO", 11000, 1.0, A, model_type=3)) is _Disposition.SKIP_MODEL


def test_row_disposition_skip_code():
    assert _disp(_row("OTHER", 11000, 1.0, A)) is _Disposition.SKIP_CODE


def test_row_disposition_absent_keys_eligible_legacy():
    assert _disp({"itemCode": 11000.0, "fiscalDate": A}) is _Disposition.ELIGIBLE


def test_row_disposition_malformed_modeltype_still_raises():
    with pytest.raises(InvalidData):
        _disp(_row_raw_modeltype("1.9"))


def _row_raw_modeltype(mt):
    r = _row("TESTCO", 11000, 1.0, A)
    r["modelType"] = mt
    return r


# =========================================================================== #
# Pagination core — limit=1 / 2 / 8, date split across pages, exact exhaustion.
# =========================================================================== #
def _three_date_two_page(model=2):
    """Dates A/B/C, two codes each, model tag ``model``, split so B spans pages."""
    page1 = _env(
        [
            _row("TESTCO", 11000, 100.0, A, model_type=model),
            _row("TESTCO", 20000, 200.0, A, model_type=model),
            _row("TESTCO", 11000, 90.0, B, model_type=model),
        ],
        current_page=1,
        total_pages=2,
    )
    page2 = _env(
        [
            _row("TESTCO", 20000, 190.0, B, model_type=model),
            _row("TESTCO", 11000, 80.0, C, model_type=model),
            _row("TESTCO", 20000, 180.0, C, model_type=model),
        ],
        current_page=2,
        include_total_pages=False,  # later page omits totalPages (verified live)
    )
    return {model: {1: page1, 2: page2}}


def test_paginate_limit2_returns_two_newest_dropping_boundary():
    record = []
    src = _src_paged(_three_date_two_page(), record=record)
    reports = src.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=2)
    assert [r.fiscal_date for r in reports] == [date(2025, 12, 31), date(2024, 12, 31)]
    assert record == [(2, 1), (2, 2)]  # B split across the two pages


def test_paginate_limit1_stops_after_page1_no_extra_fetch():
    record = []
    src = _src_paged(_three_date_two_page(), record=record)
    reports = src.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=1)
    assert [r.fiscal_date for r in reports] == [date(2025, 12, 31)]
    # limit+1-th eligible date (B) appears on page 1 -> stop; do NOT fetch page 2
    # just to complete the dropped boundary date.
    assert record == [(2, 1)]


def test_paginate_limit8_exact_exhaustion_fetches_all_pages():
    record = []
    src = _src_paged(_three_date_two_page(), record=record)
    reports = src.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=8)
    assert [r.fiscal_date for r in reports] == [date(2025, 12, 31), date(2024, 12, 31), date(2023, 12, 31)]
    assert record == [(2, 1), (2, 2)]  # exhausted at provider-declared totalPages


# =========================================================================== #
# Metadata guards (§8, B6) — raw non-bool ints only.
# =========================================================================== #
def test_page1_missing_total_pages_raises():
    pages = {2: {1: _env([_row("TESTCO", 11000, 1.0, A)], include_total_pages=False)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


def test_page1_total_pages_below_one_raises():
    pages = {2: {1: _env([_row("TESTCO", 11000, 1.0, A)], total_pages=0)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


@pytest.mark.parametrize("bad", [True, 1.0, "1"], ids=["bool", "float", "str"])
def test_current_page_non_raw_int_raises(bad):
    d = {"data": [_row("TESTCO", 11000, 1.0, A)], "currentPage": bad, "totalPages": 1, "size": 1}
    pages = {2: {1: json.dumps(d)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


@pytest.mark.parametrize("bad", [True, 1.0, "1"], ids=["bool", "float", "str"])
def test_page1_total_pages_non_raw_int_raises(bad):
    d = {"data": [_row("TESTCO", 11000, 1.0, A)], "currentPage": 1, "totalPages": bad, "size": 1}
    pages = {2: {1: json.dumps(d)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


def test_later_page_total_pages_mismatch_raises():
    page1 = _env([_row("TESTCO", 11000, 1.0, A)], current_page=1, total_pages=2)
    page2 = _env([_row("TESTCO", 11000, 1.0, B)], current_page=2, total_pages=3)  # != cached 2
    pages = {2: {1: page1, 2: page2}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=8)


def test_later_page_total_pages_non_int_raises():
    page1 = _env([_row("TESTCO", 11000, 1.0, A)], current_page=1, total_pages=2)
    d2 = {"data": [_row("TESTCO", 11000, 1.0, B)], "currentPage": 2, "totalPages": 2.0, "size": 1}
    pages = {2: {1: page1, 2: json.dumps(d2)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=8)


def test_later_page_omitting_total_pages_ok():
    page1 = _env([_row("TESTCO", 11000, 1.0, A)], current_page=1, total_pages=2)
    page2 = _env([_row("TESTCO", 11000, 1.0, B)], current_page=2, include_total_pages=False)
    pages = {2: {1: page1, 2: page2}}
    reports = _src_paged(pages).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=8
    )
    assert [r.fiscal_date for r in reports] == [date(2025, 12, 31), date(2024, 12, 31)]


def test_repeated_current_page_header_raises():
    page1 = _env([_row("TESTCO", 11000, 1.0, A)], current_page=1, total_pages=2)
    page2 = _env([_row("TESTCO", 11000, 1.0, B)], current_page=1, include_total_pages=False)  # repeats page 1
    pages = {2: {1: page1, 2: page2}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=8)


def test_ahead_current_page_header_raises():
    pages = {2: {1: _env([_row("TESTCO", 11000, 1.0, A)], current_page=2, total_pages=3)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


# =========================================================================== #
# Row-stream STATE-1 (§8, B7 + R12) — validates EVERY fetched row.
# =========================================================================== #
def test_row_missing_fiscal_date_key_raises():
    row = {"code": "TESTCO", "itemCode": 11000.0, "reportType": "ANNUAL", "modelType": 2.0, "numericValue": 1.0}
    pages = {2: {1: _env([row])}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


def test_row_missing_item_code_key_raises():
    row = {"code": "TESTCO", "reportType": "ANNUAL", "modelType": 2.0, "numericValue": 1.0, "fiscalDate": A}
    pages = {2: {1: _env([row])}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


@pytest.mark.parametrize("bad", ["a string", 123, None, [1, 2]])
def test_non_object_row_raises(bad):
    pages = {2: {1: _env([bad])}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


def test_out_of_order_date_raw_stream_raises():
    rows = [_row("TESTCO", 11000, 1.0, B), _row("TESTCO", 11000, 1.0, A)]  # 2024 then 2025 (ascending)
    pages = {2: {1: _env(rows)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


def test_reappearing_closed_date_raises():
    rows = [
        _row("TESTCO", 11000, 1.0, A),
        _row("TESTCO", 11000, 1.0, B),
        _row("TESTCO", 12000, 1.0, A),  # A reappears after its group closed
    ]
    pages = {2: {1: _env(rows)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


def test_duplicate_fd_code_across_pages_raises():
    page1 = _env([_row("TESTCO", 11000, 1.0, A)], current_page=1, total_pages=2)
    page2 = _env([_row("TESTCO", 11000, 2.0, A)], current_page=2, include_total_pages=False)  # dup (A,11000)
    pages = {2: {1: page1, 2: page2}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=8)


def test_two_state_out_of_order_ineligible_row_still_raises():
    # R12: a raw out-of-order row raises even though it is SKIP_CADENCE ineligible.
    rows = [
        _row("TESTCO", 11000, 1.0, A),                       # eligible 2025
        _row("TESTCO", 11000, 1.0, "2026-12-31", report_type="QUARTER"),  # ineligible + ASCENDING
    ]
    pages = {2: {1: _env(rows)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


def test_two_state_duplicate_ineligible_row_still_raises():
    rows = [
        _row("TESTCO", 11000, 1.0, A),
        _row("TESTCO", 11000, 1.0, A, report_type="QUARTER"),  # dup (A,11000), SKIP_CADENCE
    ]
    pages = {2: {1: _env(rows)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


# =========================================================================== #
# Empty-page seam (§9, B8 + R1).
# =========================================================================== #
def test_empty_page1_explicit_raises_empty_data():
    pages = {2: {1: _env([], total_pages=1)}}
    with pytest.raises(EmptyData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


def test_empty_page2_explicit_raises_invalid_data():
    page1 = _env([_row("TESTCO", 11000, 1.0, A)], current_page=1, total_pages=2)
    page2 = _env([], current_page=2, include_total_pages=False)
    pages = {2: {1: page1, 2: page2}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=8)


def test_empty_page1_auto_raises_empty_data():
    # both corporate + bank candidate templates empty -> EmptyData (failover-safe)
    pages = {2: {1: _env([], total_pages=1)}, 102: {1: _env([], total_pages=1)}}
    with pytest.raises(EmptyData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_empty_page2_auto_raises_invalid_data():
    page1 = _env([_row("TESTCO", 11000, 1.0, A, model_type=2)], current_page=1, total_pages=2)
    page2 = _env([], current_page=2, include_total_pages=False)
    pages = {2: {1: page1, 2: page2}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, limit=8)


# =========================================================================== #
# Mid-pagination transport failure propagates (§8 fail-closed).
# =========================================================================== #
def test_mid_pagination_transport_failure_propagates():
    page1 = _env([_row("TESTCO", 11000, 1.0, A)], current_page=1, total_pages=2)

    def _boom():
        raise RuntimeError("network down on page 2")

    pages = {2: {1: page1, 2: _boom}}
    with pytest.raises(SourceUnavailable):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=8)


# =========================================================================== #
# Row-eligibility pre-count + dual counters (§8, R8 + R12 + R15).
# 3-date regression: A eligible, B ineligible, C eligible, limit=2 -> A + C.
# =========================================================================== #
def _mixed_warning(n):
    return f"skipped_mismatched_report_rows: {n} row(s) with mismatched reportType/modelType/code"


def test_three_date_reporttype_mismatch_returns_A_and_C_with_warning():
    rows = [
        _row("TESTCO", 11000, 1.0, A),
        _row("TESTCO", 11000, 1.0, B, report_type="QUARTER"),  # ineligible cadence
        _row("TESTCO", 11000, 1.0, C),
    ]
    pages = {2: {1: _env(rows)}}
    reports = _src_paged(pages).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=2
    )
    assert [r.fiscal_date for r in reports] == [date(2025, 12, 31), date(2023, 12, 31)]
    assert _mixed_warning(1) in reports[0].warnings


def test_three_date_modeltype_mismatch_returns_A_and_C_with_warning():
    rows = [
        _row("TESTCO", 11000, 1.0, A),
        _row("TESTCO", 11000, 1.0, B, model_type=3),  # ineligible model
        _row("TESTCO", 11000, 1.0, C),
    ]
    pages = {2: {1: _env(rows)}}
    reports = _src_paged(pages).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=2
    )
    assert [r.fiscal_date for r in reports] == [date(2025, 12, 31), date(2023, 12, 31)]
    assert _mixed_warning(1) in reports[0].warnings


def test_three_date_code_mismatch_returns_A_and_C_with_warning():
    rows = [
        _row("TESTCO", 11000, 1.0, A),
        _row("OTHER", 11000, 1.0, B),  # ineligible code
        _row("TESTCO", 11000, 1.0, C),
    ]
    pages = {2: {1: _env(rows)}}
    reports = _src_paged(pages).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=2
    )
    assert [r.fiscal_date for r in reports] == [date(2025, 12, 31), date(2023, 12, 31)]
    assert _mixed_warning(1) in reports[0].warnings


def test_all_code_mismatch_raises_wrong_identity_before_cadence_precedence():
    # R15 precedence: an all-dropped mix of code + cadence mismatch raises the
    # wrong-identity (code_mismatches>0) diagnostic BEFORE the cadence/model one.
    rows = [
        _row("OTHER", 11000, 1.0, A),                       # SKIP_CODE (code_mismatches)
        _row("TESTCO", 11000, 1.0, B, report_type="QUARTER"),  # SKIP_CADENCE
    ]
    pages = {2: {1: _env(rows)}}
    with pytest.raises(InvalidData, match="provider code"):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


def test_all_cadence_mismatch_raises_template_diagnostic():
    rows = [_row("TESTCO", 11000, 1.0, A, report_type="QUARTER")]
    pages = {2: {1: _env(rows)}}
    with pytest.raises(InvalidData, match="reportType/modelType"):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False)


# =========================================================================== #
# AUTO atomic-query detection under pagination (§8, R11 + R14 + R17 + R19).
# =========================================================================== #
def _bank_rows(fd, model=102):
    return [
        _row("ZZBANK", 421900, 58.0, fd, model_type=model),
        _row("ZZBANK", 421601, 5.0, fd, model_type=model),
    ]


def test_auto_candidate_redirect_completes_bank_report_atomic_sequence():
    # candidate corporate(2) page reports dominant 102 -> restart under 102 ->
    # a COMPLETE multi-page bank report; sequence (2,1)->(102,1)->(102,2); the
    # seed page is NOT fetched twice, and there is no (2,1)->(102,2) stitch.
    cand_p1 = _env(_bank_rows(A, model=102), current_page=1, total_pages=1)  # tagged 102
    bank_p1 = _env(
        _bank_rows(A, model=102) + [_row("ZZBANK", 421900, 40.0, B, model_type=102)],
        current_page=1,
        total_pages=2,
    )
    bank_p2 = _env([_row("ZZBANK", 421601, 4.0, B, model_type=102)], current_page=2, include_total_pages=False)
    record = []
    pages = {2: {1: cand_p1}, 102: {1: bank_p1, 2: bank_p2}}
    reports = _src_paged(pages, record=record).get_financials(
        "ZZBANK", StatementType.INCOME, Period.ANNUAL, limit=8
    )
    assert record == [(2, 1), (102, 1), (102, 2)]
    assert reports[0].is_bank is True
    assert reports[0].model_type == 102
    assert [r.fiscal_date for r in reports] == [date(2025, 12, 31), date(2024, 12, 31)]


def test_auto_same_model_candidate_seeds_page1_once():
    # detected == candidate -> seed pagination with the SAME page (fetched once).
    cand_p1 = _env(_bank_rows(A, model=2), current_page=1, total_pages=1)  # corporate rows
    record = []
    pages = {2: {1: cand_p1}}
    reports = _src_paged(pages, record=record).get_financials(
        "ZZBANK", StatementType.INCOME, Period.ANNUAL, limit=8
    )
    assert record == [(2, 1)]  # exactly one fetch; page1 seed not re-fetched
    assert reports[0].is_bank is False and reports[0].model_type == 2


def test_auto_corporate_pagination_path():
    record = []
    src = _src_paged(_three_date_two_page(model=2), record=record)
    reports = src.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, limit=8)
    assert record == [(2, 1), (2, 2)]  # candidate corporate seeds page1, fetches page2
    assert reports[0].is_bank is False and reports[0].model_type == 2
    assert [r.fiscal_date for r in reports] == [date(2025, 12, 31), date(2024, 12, 31), date(2023, 12, 31)]


def test_auto_restart_same_class_wrong_statement_raises():
    # restart returns 101 (bank BALANCE — foreign to INCOME's {2,102}) -> InvalidData
    cand_p1 = _env(_bank_rows(A, model=102), current_page=1, total_pages=1)
    restart_p1 = _env(_bank_rows(A, model=101), current_page=1, total_pages=1)
    pages = {2: {1: cand_p1}, 102: {1: restart_p1}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("ZZBANK", StatementType.INCOME, Period.ANNUAL)


def test_auto_restart_tagless_raises():
    cand_p1 = _env(_bank_rows(A, model=102), current_page=1, total_pages=1)
    tagless = [
        {"code": "ZZBANK", "itemCode": 421900.0, "reportType": "ANNUAL", "numericValue": 1.0, "fiscalDate": A},
        {"code": "ZZBANK", "itemCode": 421601.0, "reportType": "ANNUAL", "numericValue": 2.0, "fiscalDate": A},
    ]
    restart_p1 = _env(tagless, current_page=1, total_pages=1)
    pages = {2: {1: cand_p1}, 102: {1: restart_p1}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("ZZBANK", StatementType.INCOME, Period.ANNUAL)


def test_auto_restart_empty_raises_invalid_not_empty():
    cand_p1 = _env(_bank_rows(A, model=102), current_page=1, total_pages=1)
    restart_p1 = _env([], current_page=1, total_pages=1)
    pages = {2: {1: cand_p1}, 102: {1: restart_p1}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("ZZBANK", StatementType.INCOME, Period.ANNUAL)


def test_auto_restart_contradicts_again_raises():
    # candidate(2) -> dominant 102 -> restart(102) returns dominant 2 -> InvalidData (one redirect only)
    cand_p1 = _env(_bank_rows(A, model=102), current_page=1, total_pages=1)
    restart_p1 = _env(_bank_rows(A, model=2), current_page=1, total_pages=1)
    pages = {2: {1: cand_p1}, 102: {1: restart_p1}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("ZZBANK", StatementType.INCOME, Period.ANNUAL)


def test_auto_candidate_foreign_minority_tag_raises():
    rows = [
        _row("TESTCO", 11000, 1.0, A, model_type=2),
        _row("TESTCO", 20000, 1.0, A, model_type=101),  # foreign minority -> fail closed
    ]
    pages = {2: {1: _env(rows, current_page=1, total_pages=1)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_auto_candidate_valid_model_tie_raises():
    rows = [
        _row("TESTCO", 11000, 1.0, A, model_type=2),
        _row("TESTCO", 20000, 1.0, A, model_type=102),
        _row("TESTCO", 11000, 1.0, B, model_type=2),
        _row("TESTCO", 20000, 1.0, B, model_type=102),
    ]
    pages = {2: {1: _env(rows, current_page=1, total_pages=1)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_auto_malformed_candidate_metadata_raises_before_tags_trusted():
    d = {"data": _bank_rows(A, model=102), "currentPage": "1", "totalPages": 1, "size": 2}
    pages = {2: {1: json.dumps(d)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials("ZZBANK", StatementType.INCOME, Period.ANNUAL)


def test_auto_redirect_runs_on_fresh_state_no_bleed():
    # candidate page1 (date A) and the restart page1 (date A, same codes) must NOT
    # trip a duplicate/reappearing error — the redirect's _paginate state is fresh.
    cand_p1 = _env(_bank_rows(A, model=102), current_page=1, total_pages=1)
    restart_p1 = _env(_bank_rows(A, model=102), current_page=1, total_pages=1)
    record = []
    pages = {2: {1: cand_p1}, 102: {1: restart_p1}}
    reports = _src_paged(pages, record=record).get_financials(
        "ZZBANK", StatementType.INCOME, Period.ANNUAL
    )
    assert record == [(2, 1), (102, 1)]  # candidate, restart; no page-2 (totalPages=1)
    assert reports[0].is_bank is True and reports[0].model_type == 102
    assert reports[0].fiscal_date == date(2025, 12, 31)


def test_explicit_is_bank_overrides_auto_under_pagination():
    # explicit path goes straight to _paginate under the resolved model.
    record = []
    src = _src_paged(_three_date_two_page(model=2), record=record)
    reports = src.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=8)
    assert record == [(2, 1), (2, 2)]
    assert reports[0].is_bank is False


# =========================================================================== #
# #198 B2 — additional pagination/catalog pins (synthetic, mock HTTP).
# =========================================================================== #
def test_wide_period_reassembles_all_142_items_across_two_pages():
    # A SINGLE fiscalDate whose 142 line items span two pages (80 + 62) must
    # reassemble into ONE complete report of all 142 items — the VIC 80+62 case.
    codes = list(range(11000, 11142))  # 142 distinct itemCodes
    assert len(codes) == 142
    page1 = _env(
        [_row("TESTCO", c, float(c), A) for c in codes[:80]],
        current_page=1,
        total_pages=2,
    )
    page2 = _env(
        [_row("TESTCO", c, float(c), A) for c in codes[80:]],
        current_page=2,
        include_total_pages=False,
    )
    pages = {2: {1: page1, 2: page2}}
    reports = _src_paged(pages).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=1
    )
    assert len(reports) == 1
    assert reports[0].fiscal_date == date(2025, 12, 31)
    assert len(reports[0].items) == 142
    assert {li.item_code for li in reports[0].items} == {str(c) for c in codes}


def test_duplicate_on_dropped_limit_plus_one_boundary_cross_page_raises():
    # limit=1 retains A and DROPS the (limit+1)-th eligible date B. The duplicate
    # (B, 11000) is split ACROSS pages: an INELIGIBLE B row on page 1 (which does
    # NOT advance the eligible boundary, so the loop still fetches page 2) and its
    # ELIGIBLE duplicate on page 2 -> InvalidData. Proves seen_keys spans pages and
    # the dup fires on the dropped boundary even when its two rows are cross-page.
    page1 = _env(
        [
            _row("TESTCO", 11000, 1.0, A),                          # eligible A (retained)
            _row("TESTCO", 11000, 9.0, B, report_type="QUARTER"),   # (B,11000) INELIGIBLE
        ],
        current_page=1,
        total_pages=2,
    )
    page2 = _env(
        [_row("TESTCO", 11000, 2.0, B)],                            # (B,11000) duplicate, eligible
        current_page=2,
        include_total_pages=False,
    )
    pages = {2: {1: page1, 2: page2}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=1
        )


def test_ineligible_row_reappearance_on_later_page_raises():
    # A closed date reappearing on a later page as an INELIGIBLE (wrong-cadence) row
    # still raises — STATE-1 validates every row, independent of eligibility.
    page1 = _env(
        [_row("TESTCO", 11000, 1.0, A), _row("TESTCO", 11000, 1.0, B)],
        current_page=1,
        total_pages=2,
    )
    page2 = _env(
        [_row("TESTCO", 12000, 1.0, A, report_type="QUARTER")],  # A reappears, ineligible
        current_page=2,
        include_total_pages=False,
    )
    pages = {2: {1: page1, 2: page2}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=8
        )


def test_page_with_dates_older_than_limit_plus_one_retains_exact_newest_limit():
    # A page carrying dates older than the (limit+1)-th eligible date is validated
    # in full, but the builder caps to the newest `limit` periods EXACTLY.
    D = "2022-12-31"
    rows = [
        _row("TESTCO", 11000, 100.0, A),
        _row("TESTCO", 11000, 90.0, B),
        _row("TESTCO", 11000, 80.0, C),   # (limit+1)-th eligible date (limit=2)
        _row("TESTCO", 11000, 70.0, D),   # older still
    ]
    pages = {2: {1: _env(rows, current_page=1, total_pages=1)}}
    reports = _src_paged(pages).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False, limit=2
    )
    assert [r.fiscal_date for r in reports] == [date(2025, 12, 31), date(2024, 12, 31)]
    assert reports[0].get("11000") == 100.0
    assert reports[1].get("11000") == 90.0


@pytest.mark.parametrize("bad_code", [11000.9, True], ids=["fractional", "bool"])
def test_runtime_fractional_item_code_raises_via_adapter(bad_code):
    # #198 R20: a runtime adapter row whose itemCode is fractional (11000.9) or a
    # bool must raise InvalidData via _require_item_code — the ADAPTER path, not
    # the probe.
    row = {
        "code": "TESTCO",
        "itemCode": bad_code,
        "reportType": "ANNUAL",
        "modelType": 2.0,
        "numericValue": 1.0,
        "fiscalDate": A,
    }
    pages = {2: {1: _env([row], current_page=1, total_pages=1)}}
    with pytest.raises(InvalidData):
        _src_paged(pages).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False
        )


def test_runtime_decimal_fractional_item_code_raises_row_level():
    # #198 R20: a runtime statement row whose itemCode is a FRACTIONAL Decimal
    # (11000.9) must raise InvalidData through the exact per-row seam the pagination
    # loop uses (_require_item_code -> canonical_provider_key). Synthetic-defensive:
    # stdlib json yields a float at runtime, so a Decimal cannot arrive via the HTTP
    # path — the assertion is the row-level InvalidData, byte-identical to the
    # builder key.
    row = {
        "code": "TESTCO",
        "itemCode": Decimal("11000.9"),
        "reportType": "ANNUAL",
        "modelType": 2,
        "numericValue": 1.0,
        "fiscalDate": A,
    }
    with pytest.raises(InvalidData):
        VNDirectFundamentalSource._require_item_code(row)
