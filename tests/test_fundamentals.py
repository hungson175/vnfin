"""TDD for vnfin.fundamentals — VNDirect api-finfo financial statements + ratios.

All fixtures are SYNTHETIC and OBVIOUSLY FAKE: hand-crafted JSON that preserves
the real api-finfo *shapes* (long/tall itemCode rows, bank vs corporate
modelType split, validation cases) documented in
docs/research/2026-06-18-vn-fundamental-data-sources.md — but with made-up
symbols ("TESTCO", "ZZBANK") and FABRICATED numbers. No real provider rows or
research-doc proof values are committed here. Tests inject http_get so no
network is touched.

Real shapes (synthesized below):
  /v4/financial_statements -> {"data":[{code,itemCode(float),reportType,
    modelType(float),numericValue,fiscalDate,...}], totalElements,...}
    LONG/tall: one row per (line-item, period). Corporate IS/BS/CF = modelType
    1/2/3; banks = 101/102/103. Units = RAW VND.
  /v4/ratios -> {"data":[{code,group,reportDate,itemCode(str),ratioCode,
    itemName,value}], ...}  — period-agnostic; value is dimensionless/per-share.
"""
from __future__ import annotations

import json
from datetime import date

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable, VnfinError
from vnfin.fundamentals import (
    FinancialReport,
    LineItem,
    Period,
    StatementType,
    VNDirectFundamentalSource,
    get_financials,
)


# --------------------------------------------------------------------------- #
# Synthetic fixtures — FAKE symbols + FABRICATED numbers, real provider shape.
# Values are deliberately round/obviously-invented so they cannot be mistaken
# for real provider rows or research-doc proof snippets.
# --------------------------------------------------------------------------- #
def _stmt_row(code, item_code, value, fiscal_date, report_type, model_type):
    return {
        "code": code,
        "itemCode": float(item_code),
        "reportType": report_type,
        "modelType": float(model_type),
        "numericValue": value,
        "fiscalDate": fiscal_date,
        "createdDate": "2000-01-01 00:00:00",
        "modifiedDate": "2000-01-01 00:00:00",
    }


def _stmt_envelope(rows, total=None):
    return json.dumps(
        {
            "data": rows,
            "currentPage": 1,
            "size": len(rows),
            "totalElements": total if total is not None else len(rows),
            "totalPages": 1,
        }
    )


def corp_income_two_periods():
    """Corporate income statement (modelType 1), two fiscal years, tall rows.

    itemCode 11000 = net revenue, 20000 = profit before tax (synthetic mapping
    that overlaps the headline itemCode->name map we ship). Values are obviously
    fabricated round raw-VND numbers, NOT real provider figures.
    """
    rows = [
        _stmt_row("TESTCO", 11000, 12_000_000_000_000.0, "2025-12-31", "ANNUAL", 1),
        _stmt_row("TESTCO", 20000, 3_000_000_000_000.0, "2025-12-31", "ANNUAL", 1),
        _stmt_row("TESTCO", 11000, 10_000_000_000_000.0, "2024-12-31", "ANNUAL", 1),
        _stmt_row("TESTCO", 20000, 2_000_000_000_000.0, "2024-12-31", "ANNUAL", 1),
    ]
    return _stmt_envelope(rows, total=400)


def bank_income_one_period():
    """Bank income statement (modelType 102) — single period, fabricated values."""
    rows = [
        _stmt_row("ZZBANK", 421601, 5_000_000_000_000.0, "2025-12-31", "ANNUAL", 102),
        _stmt_row("ZZBANK", 22070, 8_000_000_000_000.0, "2025-12-31", "ANNUAL", 102),
    ]
    return _stmt_envelope(rows, total=100)


def _ratio_row(code, ratio_code, value, report_date, item_name="x"):
    return {
        "code": code,
        "group": "STOCK",
        "reportDate": report_date,
        "itemCode": "99999",
        "ratioCode": ratio_code,
        "itemName": item_name,
        "value": value,
    }


def ratios_two_dates():
    rows = [
        _ratio_row("TESTCO", "PRICE_TO_EARNINGS", 10.00, "2026-03-31", "Tỷ lệ PE"),
        _ratio_row("TESTCO", "PRICE_TO_BOOK", 2.00, "2026-03-31", "Tỷ lệ PB"),
        _ratio_row("TESTCO", "PRICE_TO_EARNINGS", 9.00, "2025-12-31", "Tỷ lệ PE"),
    ]
    return _stmt_envelope(rows, total=300)


def _src(text):
    return VNDirectFundamentalSource(http_get=lambda url, params, headers: text)


def _capturing_src(text):
    """A source that records the url+params it was asked to fetch."""
    captured = {}

    def _g(url, params, headers):
        captured["url"] = url
        captured["params"] = params
        captured["headers"] = headers
        return text

    return VNDirectFundamentalSource(http_get=_g), captured


# --------------------------------------------------------------------------- #
# Enums / models
# --------------------------------------------------------------------------- #
def test_statement_type_enum_values():
    assert {s.name for s in StatementType} >= {"INCOME", "BALANCE", "CASHFLOW", "RATIOS"}


def test_period_enum_values():
    assert {p.value for p in Period} >= {"QUARTER", "ANNUAL"}
    # period-agnostic sentinel exists for ratios (see ratio tests below)
    assert "UNKNOWN" in {p.value for p in Period}


# --------------------------------------------------------------------------- #
# Regression — issue #25: source.get_financials must accept string statement and
# period values (matches top-level get_financials behavior).
# --------------------------------------------------------------------------- #
def test_source_get_financials_accepts_string_statement_and_period():
    reports = _src(corp_income_two_periods()).get_financials(
        "TESTCO", "income", "annual"
    )
    assert reports[0].statement_type is StatementType.INCOME
    assert reports[0].period is Period.ANNUAL


def test_source_get_financials_rejects_bad_statement_string():
    with pytest.raises(VnfinError):
        _src(corp_income_two_periods()).get_financials(
            "TESTCO", "not-a-statement", "annual"
        )


def test_source_get_financials_rejects_bad_period_string():
    with pytest.raises(VnfinError):
        _src(corp_income_two_periods()).get_financials(
            "TESTCO", "income", "not-a-period"
        )


# --------------------------------------------------------------------------- #
# Normal parse: long/tall rows pivot per fiscalDate -> one report per period
# --------------------------------------------------------------------------- #
def test_income_parses_into_reports_per_period():
    reports = _src(corp_income_two_periods()).get_financials(
        "testco", StatementType.INCOME, Period.ANNUAL
    )
    assert isinstance(reports, tuple)
    assert len(reports) == 2  # two fiscal years -> two reports
    assert all(isinstance(r, FinancialReport) for r in reports)

    newest = reports[0]
    assert newest.symbol == "TESTCO"  # normalized uppercase
    assert newest.statement_type is StatementType.INCOME
    assert newest.period is Period.ANNUAL
    assert newest.currency == "VND"
    assert newest.source == "vndirect"
    assert newest.fetched_at_utc is not None


def test_reports_sorted_newest_first():
    reports = _src(corp_income_two_periods()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    dates = [r.fiscal_date.isoformat() for r in reports]
    assert dates == ["2025-12-31", "2024-12-31"]


def test_line_items_grouped_under_their_period():
    reports = _src(corp_income_two_periods()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    newest = reports[0]
    # two line items per period in the fixture
    assert len(newest.items) == 2
    assert all(isinstance(li, LineItem) for li in newest.items)
    codes = {li.item_code for li in newest.items}
    assert codes == {"11000", "20000"}


def test_units_are_raw_vnd_no_scaling():
    reports = _src(corp_income_two_periods()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    val = reports[0].get("11000")
    assert val == pytest.approx(12_000_000_000_000.0)  # raw VND, unscaled


def test_statement_line_items_carry_vnd_value_unit():
    """Each statement line states VND explicitly (per-line unit, not just report)."""
    reports = _src(corp_income_two_periods()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    for li in reports[0].items:
        assert li.value_unit == "VND"


def test_get_accessor_and_name_map():
    reports = _src(corp_income_two_periods()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    r = reports[0]
    # value accessor by itemCode
    assert r.get("11000") == pytest.approx(12_000_000_000_000.0)
    assert r.get("does-not-exist") is None
    # the LineItem exposes a best-effort human name from the client-side map
    li = next(li for li in r.items if li.item_code == "11000")
    assert li.name  # non-empty string (mapped or fallback)


# --------------------------------------------------------------------------- #
# Bank vs corporate modelType detection
# --------------------------------------------------------------------------- #
def test_bank_uses_modelType_10x_in_params():
    src, captured = _capturing_src(bank_income_one_period())
    src.get_financials("ZZBANK", StatementType.INCOME, Period.ANNUAL, is_bank=True)
    q = captured["params"]["q"]
    assert "modelType:102" in q
    assert "code:ZZBANK" in q
    assert "reportType:ANNUAL" in q


def test_corporate_uses_modelType_single_digit_in_params():
    src, captured = _capturing_src(corp_income_two_periods())
    src.get_financials("TESTCO", StatementType.BALANCE, Period.QUARTER)
    q = captured["params"]["q"]
    assert "modelType:2" in q  # balance sheet corporate
    assert "reportType:QUARTER" in q


def test_cashflow_corporate_modelType_3():
    src, captured = _capturing_src(corp_income_two_periods())
    src.get_financials("TESTCO", StatementType.CASHFLOW, Period.ANNUAL)
    assert "modelType:3" in captured["params"]["q"]


def test_cashflow_bank_modelType_103():
    src, captured = _capturing_src(bank_income_one_period())
    src.get_financials("ZZBANK", StatementType.CASHFLOW, Period.ANNUAL, is_bank=True)
    assert "modelType:103" in captured["params"]["q"]


def test_bank_reports_carry_bank_model_metadata():
    reports = _src(bank_income_one_period()).get_financials(
        "ZZBANK", StatementType.INCOME, Period.ANNUAL, is_bank=True
    )
    assert reports[0].is_bank is True
    assert reports[0].model_type == 102


# --------------------------------------------------------------------------- #
# Auto-detection of bank vs corporate (caller does NOT pass is_bank)
# The response rows carry the provider's real modelType (corporate 1/2/3, bank
# 101/102/103); the adapter must read that tag and classify the template without
# the caller knowing. Explicit is_bank always overrides the auto-detection.
# --------------------------------------------------------------------------- #
def test_auto_detects_corporate_sample_as_corporate():
    """A corporate response (modelType 1) is auto-detected as corporate."""
    reports = _src(corp_income_two_periods()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL  # no is_bank -> AUTO
    )
    assert reports[0].is_bank is False
    assert reports[0].model_type == 1


def test_auto_detects_bank_sample_as_bank():
    """A bank response (modelType 102) is auto-detected as bank even when the
    caller never passes is_bank and the ticker is not in the known-bank list."""
    reports = _src(bank_income_one_period()).get_financials(
        "ZZBANK", StatementType.INCOME, Period.ANNUAL  # no is_bank -> AUTO
    )
    assert reports[0].is_bank is True
    assert reports[0].model_type == 102


def test_auto_detected_bank_uses_bank_name_map():
    """After auto-detecting a bank, line-item names come from the bank map."""
    reports = _src(bank_income_one_period()).get_financials(
        "ZZBANK", StatementType.INCOME, Period.ANNUAL  # AUTO
    )
    nii = next(li for li in reports[0].items if li.item_code == "22070")
    assert nii.name == "Thu nhập lãi thuần"  # bank net interest income label


def test_explicit_is_bank_false_overrides_auto_on_bank_rows():
    """Explicit is_bank=False uses the corporate query and label.

    The corporate query is used (modelType:102 must NOT appear). Rows returned
    for that query are parsed; mismatched bank-template rows are skipped as a
    provider contract violation.
    """
    rows = [
        _stmt_row("ZZBANK", 11000, 12_000_000_000_000.0, "2025-12-31", "ANNUAL", 1),
    ]
    src, captured = _capturing_src(_stmt_envelope(rows))
    reports = src.get_financials(
        "ZZBANK", StatementType.INCOME, Period.ANNUAL, is_bank=False
    )
    assert "modelType:1" in captured["params"]["q"]
    assert "modelType:102" not in captured["params"]["q"]
    assert reports[0].is_bank is False
    assert reports[0].model_type == 1


def test_explicit_is_bank_true_overrides_auto_on_corporate_rows():
    """Explicit is_bank=True uses the bank query and label."""
    rows = [
        _stmt_row("TESTCO", 421601, 5_000_000_000_000.0, "2025-12-31", "ANNUAL", 102),
    ]
    src, captured = _capturing_src(_stmt_envelope(rows))
    reports = src.get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=True
    )
    assert "modelType:102" in captured["params"]["q"]
    assert reports[0].is_bank is True
    assert reports[0].model_type == 102


def test_auto_prefers_corporate_query_first_for_unknown_ticker():
    """An unrecognised ticker is probed as corporate first (modelType single-digit)."""
    src, captured = _capturing_src(corp_income_two_periods())
    src.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)  # AUTO
    assert "modelType:1" in captured["params"]["q"]


def test_auto_prefers_bank_query_first_for_known_bank_ticker():
    """A known-bank ticker is probed as the bank template first (modelType 10x)."""
    src, captured = _capturing_src(bank_income_one_period())
    src.get_financials("VCB", StatementType.INCOME, Period.ANNUAL)  # AUTO, VCB is a bank
    assert "modelType:102" in captured["params"]["q"]


def test_auto_falls_back_to_other_template_when_first_is_empty():
    """If the heuristic-preferred template returns no rows, the other is probed.

    A known bank (VCB) is tried as bank first; an empty bank response forces a
    fall-back probe to the corporate template instead of failing outright.
    """
    queries = []

    def _g(url, params, headers):
        queries.append(params["q"])
        # First (bank, modelType:102) probe -> empty; corporate probe -> data.
        if "modelType:102" in params["q"]:
            return _stmt_envelope([], total=0)
        return corp_income_two_periods()

    src = VNDirectFundamentalSource(http_get=_g)
    reports = src.get_financials("VCB", StatementType.INCOME, Period.ANNUAL)  # AUTO
    assert any("modelType:102" in q for q in queries)  # bank probed first
    assert any("modelType:1" in q for q in queries)  # then corporate
    assert reports[0].is_bank is False  # detected corporate from the fallback rows


def test_auto_raises_empty_when_both_templates_empty():
    """Both templates empty -> EmptyData so a failover chain can fall through."""
    src = _src(_stmt_envelope([], total=0))
    with pytest.raises(EmptyData):
        src.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)  # AUTO


def test_period_unknown_rejected_for_statements():
    # Issue #10: Period.UNKNOWN is only meaningful for ratios; statements must
    # reject it before touching the network.
    src = VNDirectFundamentalSource(http_get=lambda *a: _stmt_envelope([]))
    with pytest.raises(VnfinError):
        src.get_financials("TESTCO", StatementType.INCOME, Period.UNKNOWN)


def test_vndirect_rejects_wrong_report_type_rows():
    # Issue #44: rows whose reportType does not match the requested period are
    # provider contract violations and must be skipped (with a warning).
    rows = [
        _stmt_row("TESTCO", 11000, 12_000_000_000_000.0, "2025-12-31", "ANNUAL", 1),
        _stmt_row("TESTCO", 11000, 11_000_000_000_000.0, "2025-09-30", "QUARTER", 1),
    ]
    reports = _src(_stmt_envelope(rows)).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    assert len(reports) == 1
    assert reports[0].fiscal_date == date(2025, 12, 31)
    assert any("skipped" in w for w in reports[0].warnings)


def test_vndirect_rejects_wrong_model_type_rows():
    # Issue #44: rows whose modelType does not match the requested/corporate bank
    # template are provider contract violations and must be skipped.
    rows = [
        _stmt_row("TESTCO", 11000, 12_000_000_000_000.0, "2025-12-31", "ANNUAL", 1),
        _stmt_row("TESTCO", 11000, 11_000_000_000_000.0, "2024-12-31", "ANNUAL", 101),
    ]
    reports = _src(_stmt_envelope(rows)).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=False
    )
    assert len(reports) == 1
    assert reports[0].fiscal_date == date(2025, 12, 31)
    assert reports[0].is_bank is False
    assert any("skipped" in w for w in reports[0].warnings)


def test_vndirect_duplicate_item_code_in_same_period_raises_invalid():
    # Issue #26: duplicate itemCode within one fiscal period is a contract
    # violation and must raise InvalidData.
    rows = [
        _stmt_row("TESTCO", 11000, 12_000_000_000_000.0, "2025-12-31", "ANNUAL", 1),
        _stmt_row("TESTCO", 11000, 11_000_000_000_000.0, "2025-12-31", "ANNUAL", 1),
    ]
    with pytest.raises(InvalidData):
        _src(_stmt_envelope(rows)).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


def test_vndirect_ratio_eps_bv_use_vnd_per_share_unit():
    # Issue #19: VNDirect EPS/BV ratio codes are per-share monetary values, not
    # dimensionless ratios, and must carry value_unit="vnd_per_share".
    rows = [
        _ratio_row("TESTCO", "EPS", 5_000.0, "2025-12-31", "EPS"),
        _ratio_row("TESTCO", "BV", 20_000.0, "2025-12-31", "BV"),
        _ratio_row("TESTCO", "PRICE_TO_EARNINGS", 10.0, "2025-12-31", "PE"),
    ]
    reports = _src(_stmt_envelope(rows)).get_financials(
        "TESTCO", StatementType.RATIOS, Period.ANNUAL
    )
    units = {li.item_code: li.value_unit for li in reports[0].items}
    assert units["EPS"] == "vnd_per_share"
    assert units["BV"] == "vnd_per_share"
    assert units["PRICE_TO_EARNINGS"] == "ratio"


def test_is_bank_string_false_treated_as_false():
    # Issue #11: a string "False" must not be truthy; explicit is_bank must be
    # a real bool (or AUTO/None). String values are rejected with VnfinError.
    with pytest.raises(VnfinError):
        _src(corp_income_two_periods()).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank="False"
        )


def test_vndirect_malformed_ratio_row_raises_invalid():
    # Issue #62: malformed ratioCode/itemName fields must raise InvalidData, not
    # leak raw TypeError/AttributeError.
    cases = [
        {"ratioCode": ["EPS"], "itemName": "EPS"},
        {"ratioCode": {"x": "EPS"}, "itemName": "EPS"},
        {"ratioCode": 123, "itemName": None},
        {"ratioCode": "PE", "itemName": ["PE"]},
    ]
    for overrides in cases:
        row = {
            "code": "TESTCO",
            "reportDate": "2025-12-31",
            "value": 1.0,
            **overrides,
        }
        src = VNDirectFundamentalSource(
            http_get=lambda *a, row=row: json.dumps({"data": [row]})
        )
        with pytest.raises(InvalidData):
            src.get_financials("TESTCO", StatementType.RATIOS, Period.ANNUAL)


def test_get_financials_function_auto_detects_without_is_bank():
    """The public get_financials() auto-detects a bank with no is_bank arg."""
    reports = get_financials(
        "ZZBANK", StatementType.INCOME, Period.ANNUAL, source=_src(bank_income_one_period())
    )
    assert reports[0].is_bank is True
    assert reports[0].model_type == 102


# --------------------------------------------------------------------------- #
# Ratios path (different shape: ratioCode/reportDate/value)
# Ratios are PERIOD-AGNOSTIC and NOT monetary: the report must not claim a
# requested Period or report-wide VND currency.
# --------------------------------------------------------------------------- #
def test_ratios_parse_per_report_date():
    reports = _src(ratios_two_dates()).get_financials(
        "TESTCO", StatementType.RATIOS, Period.QUARTER
    )
    assert len(reports) == 2  # two distinct reportDates
    newest = reports[0]
    assert newest.statement_type is StatementType.RATIOS
    assert newest.get("PRICE_TO_EARNINGS") == pytest.approx(10.00)
    assert newest.get("PRICE_TO_BOOK") == pytest.approx(2.00)


def test_ratios_report_is_period_agnostic_not_requested_period():
    """The ratios endpoint has no period filter, so the report must NOT pretend
    to honour the requested Period — it reports Period.UNKNOWN regardless."""
    for requested in (Period.QUARTER, Period.ANNUAL):
        reports = _src(ratios_two_dates()).get_financials(
            "TESTCO", StatementType.RATIOS, requested
        )
        assert reports[0].period is Period.UNKNOWN


def test_ratios_report_is_not_monetary_vnd():
    """Ratios are dimensionless/per-share — the report must not claim currency VND."""
    reports = _src(ratios_two_dates()).get_financials(
        "TESTCO", StatementType.RATIOS, Period.QUARTER
    )
    assert reports[0].currency is None


def test_ratio_line_items_have_ratio_value_unit():
    reports = _src(ratios_two_dates()).get_financials(
        "TESTCO", StatementType.RATIOS, Period.QUARTER
    )
    for li in reports[0].items:
        assert li.value_unit == "ratio"


def test_ratios_hit_ratios_endpoint_not_statements():
    src, captured = _capturing_src(ratios_two_dates())
    src.get_financials("TESTCO", StatementType.RATIOS, Period.QUARTER)
    assert captured["url"].endswith("/v4/ratios")


def test_statements_hit_financial_statements_endpoint():
    src, captured = _capturing_src(corp_income_two_periods())
    src.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert captured["url"].endswith("/v4/financial_statements")


# --------------------------------------------------------------------------- #
# Input validation (user-supplied args — not source errors)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad_symbol", ["", "   ", "\t"])
def test_empty_symbol_raises_vnfin_error(bad_symbol):
    with pytest.raises(VnfinError):
        _src(corp_income_two_periods()).get_financials(
            bad_symbol, StatementType.INCOME, Period.ANNUAL
        )


@pytest.mark.parametrize("bad_limit", [0, -1, -100])
def test_non_positive_limit_raises_vnfin_error(bad_limit):
    with pytest.raises(VnfinError):
        _src(corp_income_two_periods()).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL, limit=bad_limit
        )


def test_empty_symbol_validated_before_network():
    """Validation must reject bad input even if the source would crash."""
    def boom(url, params, headers):  # pragma: no cover - must not be reached
        raise AssertionError("network must not be touched on invalid input")

    src = VNDirectFundamentalSource(http_get=boom)
    with pytest.raises(VnfinError):
        src.get_financials("", StatementType.INCOME, Period.ANNUAL)


def test_get_financials_function_validates_empty_symbol():
    with pytest.raises(VnfinError):
        get_financials("", StatementType.INCOME, Period.ANNUAL, source=_src(corp_income_two_periods()))


def test_get_financials_function_validates_limit():
    with pytest.raises(VnfinError):
        get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL, limit=0,
            source=_src(corp_income_two_periods()),
        )


# --------------------------------------------------------------------------- #
# Failover-safe error handling (reuse vnfin.exceptions)
# --------------------------------------------------------------------------- #
def test_empty_data_array_raises_empty():
    with pytest.raises(EmptyData):
        _src(_stmt_envelope([], total=0)).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


def test_missing_data_key_raises_empty():
    with pytest.raises(EmptyData):
        _src(json.dumps({"currentPage": 1})).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("<html>503</html>").get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


def test_malformed_numericValue_raises_invalid():
    bad = _stmt_envelope(
        [
            {
                "code": "TESTCO",
                "itemCode": 11000.0,
                "reportType": "ANNUAL",
                "modelType": 1.0,
                "numericValue": "not-a-number",
                "fiscalDate": "2025-12-31",
            }
        ]
    )
    with pytest.raises(InvalidData):
        _src(bad).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_nan_numericValue_raises_invalid():
    payload = (
        '{"data":[{"code":"TESTCO","itemCode":11000.0,"reportType":"ANNUAL",'
        '"modelType":1.0,"numericValue":NaN,"fiscalDate":"2025-12-31"}],'
        '"totalElements":1}'
    )
    with pytest.raises(InvalidData):
        _src(payload).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_missing_fiscalDate_raises_invalid():
    bad = _stmt_envelope(
        [
            {
                "code": "TESTCO",
                "itemCode": 11000.0,
                "reportType": "ANNUAL",
                "modelType": 1.0,
                "numericValue": 1.0,
            }
        ]
    )
    with pytest.raises(InvalidData):
        _src(bad).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_garbage_fiscalDate_raises_invalid():
    bad = _stmt_envelope(
        [_stmt_row("TESTCO", 11000, 1.0, "31/12/2025", "ANNUAL", 1)]
    )
    with pytest.raises(InvalidData):
        _src(bad).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_data_not_a_list_raises_invalid():
    bad = json.dumps({"data": {"unexpected": "object"}, "totalElements": 1})
    with pytest.raises(InvalidData):
        _src(bad).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_ratio_row_missing_ratioCode_raises_invalid():
    bad = _stmt_envelope(
        [{"code": "TESTCO", "reportDate": "2026-03-31", "value": 1.0}]
    )
    with pytest.raises(InvalidData):
        _src(bad).get_financials("TESTCO", StatementType.RATIOS, Period.QUARTER)


def test_transport_error_wrapped_as_source_unavailable():
    def boom(url, params, headers):
        raise ConnectionError("network down")

    src = VNDirectFundamentalSource(http_get=boom)
    with pytest.raises(SourceUnavailable):
        src.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


# --------------------------------------------------------------------------- #
# Public convenience API
# --------------------------------------------------------------------------- #
def test_get_financials_function_uses_injected_source():
    src = _src(corp_income_two_periods())
    reports = get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, source=src)
    assert len(reports) == 2
    assert reports[0].statement_type is StatementType.INCOME


def test_get_financials_accepts_string_args():
    src = _src(corp_income_two_periods())
    reports = get_financials("TESTCO", "income", "annual", source=src)
    assert reports[0].statement_type is StatementType.INCOME
    assert reports[0].period is Period.ANNUAL


def test_invalid_statement_string_raises_vnfin_error():
    with pytest.raises(VnfinError):
        get_financials("TESTCO", "nonsense", "annual", source=_src(corp_income_two_periods()))


# --------------------------------------------------------------------------- #
# to_dataframe convenience (parity with PriceHistory.to_dataframe)
# --------------------------------------------------------------------------- #
def test_report_to_dataframe():
    reports = _src(corp_income_two_periods()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    df = reports[0].to_dataframe()
    assert list(df.columns) >= ["item_code", "name", "value"]
    assert "value_unit" in df.columns
    assert df.attrs["symbol"] == "TESTCO"
    assert df.attrs["currency"] == "VND"


def test_ratio_report_to_dataframe_has_no_vnd_currency():
    reports = _src(ratios_two_dates()).get_financials(
        "TESTCO", StatementType.RATIOS, Period.QUARTER
    )
    df = reports[0].to_dataframe()
    assert df.attrs["currency"] is None
    assert df.attrs["period"] == "UNKNOWN"


# --------------------------------------------------------------------------- #
# Known-bank heuristic + AUTO sentinel resolution helpers
# --------------------------------------------------------------------------- #
def test_is_known_bank_recognises_known_tickers_case_insensitively():
    from vnfin.fundamentals import is_known_bank

    assert is_known_bank("VCB") is True
    assert is_known_bank("vcb") is True
    assert is_known_bank(" Vcb ") is True


def test_is_known_bank_rejects_non_bank_and_garbage():
    from vnfin.fundamentals import is_known_bank

    assert is_known_bank("TESTCO") is False  # fabricated non-bank ticker
    assert is_known_bank("") is False
    assert is_known_bank(None) is False  # type: ignore[arg-type]


def test_resolve_is_bank_explicit_overrides_win():
    from vnfin.fundamentals.base import AUTO, resolve_is_bank

    # explicit flags ignore the heuristic entirely
    assert resolve_is_bank("VCB", False) is False  # bank ticker, forced corporate
    assert resolve_is_bank("TESTCO", True) is True  # non-bank, forced bank
    # AUTO defers to the heuristic
    assert resolve_is_bank("VCB", AUTO) is True
    assert resolve_is_bank("TESTCO", AUTO) is False


def test_auto_is_the_none_sentinel():
    from vnfin.fundamentals import AUTO

    assert AUTO is None


# --------------------------------------------------------------------------- #
# Expanded headline itemCode -> name map (more common lines than before)
# --------------------------------------------------------------------------- #
def test_item_name_maps_expanded_corporate_headlines():
    from vnfin.fundamentals.itemcodes import item_name

    # net income / total assets / equity / operating cash flow now mapped
    assert item_name("21000") == "Lợi nhuận sau thuế"  # net income
    assert item_name("25000") == "Tổng tài sản"  # total assets
    assert item_name("40000") == "Vốn chủ sở hữu"  # equity
    assert item_name("31000") == "Lưu chuyển tiền từ hoạt động kinh doanh"  # operating CF
    # newly added headline lines
    assert item_name("23400") == "Hàng tồn kho"  # inventories
    assert item_name("40200") == "Lợi nhuận sau thuế chưa phân phối"  # retained earnings


def test_item_name_maps_expanded_bank_headlines():
    from vnfin.fundamentals.itemcodes import item_name

    assert item_name("22070", is_bank=True) == "Thu nhập lãi thuần"  # net interest income
    assert item_name("412000", is_bank=True) == "Tổng tài sản"  # total assets
    # newly added bank headline lines
    assert item_name("411600", is_bank=True) == "Cho vay khách hàng"  # loans to customers
    assert item_name("413100", is_bank=True) == "Tiền gửi của khách hàng"  # deposits


def test_item_name_unknown_code_falls_back():
    from vnfin.fundamentals.itemcodes import item_name

    assert item_name("99999") == "item_99999"
