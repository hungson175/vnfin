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
