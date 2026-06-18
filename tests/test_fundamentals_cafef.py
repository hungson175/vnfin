"""TDD for vnfin.fundamentals CafeF backup adapter (no-auth AJAX).

All fixtures are SYNTHETIC and OBVIOUSLY FAKE: hand-crafted JSON that preserves
the real CafeF *shapes* documented in
docs/research/2026-06-18-vn-fundamental-data-sources.md — but with made-up
symbols ("TESTCO", "ZZBANK") and FABRICATED round numbers. No real provider rows
or research-doc proof values are committed here. Tests inject ``http_get`` so no
network is touched.

Real CafeF shapes (synthesized below):
  FinanceReport.ashx?Type={1=income,2=balance}&Symbol={T}&TotalRow={N}
    &EndDate={anchor}&ReportType={NAM|QUY}&Sort=DESC
  -> {"Data":{"Count":<periods avail>,"Value":[
        {"Time":"2025","Year":2025,"Quater":0,"ReportType":"HK",
         "Conten":"Đã kiểm toán ",
         "Value":[{"Code":"DTTBHCCDV","Name":"...","Value":70207688945}, ...]},
        ...]},"Message":null,"Success":true}
    One object per fiscal period (newest first); each holds Value[] of
    {Code,Name,Value} line items. Quater=0 => annual, 1..4 => that quarter.
    Money values are RAW VND (unscaled), consistent with VNDirect.
  GetDataChiSoTaiChinh.ashx -> same outer shape, ratio Codes (EPS/BV/PE/ROA...).
  Bad/empty symbol -> {"Data":null,"Message":"...","Success":false}.
"""
from __future__ import annotations

import json

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable, VnfinError
from vnfin.fundamentals import (
    CafeFFundamentalSource,
    FinancialReport,
    LineItem,
    Period,
    StatementType,
)


# --------------------------------------------------------------------------- #
# Synthetic fixtures — FAKE symbols + FABRICATED numbers, real CafeF shape.
# --------------------------------------------------------------------------- #
def _period(time, year, quater, items, report_type="HK", conten="Đã kiểm toán "):
    return {
        "Time": time,
        "Year": year,
        "Quater": quater,
        "ReportType": report_type,
        "Conten": conten,
        "Value": [{"Code": c, "Name": n, "Value": v} for (c, n, v) in items],
    }


def _envelope(periods, count=None, success=True):
    return json.dumps(
        {
            "Data": {
                "Count": count if count is not None else len(periods),
                "Value": periods,
            },
            "Message": None,
            "Success": success,
        }
    )


def corp_income_two_years():
    """Corporate annual income, two fiscal years, fabricated round raw VND."""
    periods = [
        _period(
            "2025",
            2025,
            0,
            [
                ("DTTBHCCDV", "Doanh thu bán hàng và CCDV", 12_000_000_000_000),
                ("GV", "Giá vốn hàng bán", 7_000_000_000_000),
                ("LNGBHCCDV", "Lợi nhuận gộp", 5_000_000_000_000),
            ],
        ),
        _period(
            "2024",
            2024,
            0,
            [
                ("DTTBHCCDV", "Doanh thu bán hàng và CCDV", 10_000_000_000_000),
                ("GV", "Giá vốn hàng bán", 6_000_000_000_000),
                ("LNGBHCCDV", "Lợi nhuận gộp", 4_000_000_000_000),
            ],
        ),
    ]
    return _envelope(periods, count=25)


def corp_income_two_quarters():
    """Corporate quarterly income — Time like 'Q1-2026', Quater in 1..4."""
    periods = [
        _period(
            "Q1-2026",
            2026,
            1,
            [("DTTBHCCDV", "Doanh thu bán hàng và CCDV", 3_000_000_000_000)],
            report_type="H",
        ),
        _period(
            "Q4-2025",
            2025,
            4,
            [("DTTBHCCDV", "Doanh thu bán hàng và CCDV", 2_500_000_000_000)],
            report_type="H",
        ),
    ]
    return _envelope(periods, count=85)


def corp_balance_one_year():
    periods = [
        _period(
            "2025",
            2025,
            0,
            [
                ("TotalAsset", "Tổng tài sản", 88_000_000_000_000),
                ("TotalShortTermDebt", "Nợ ngắn hạn", 40_000_000_000_000),
            ],
        )
    ]
    return _envelope(periods, count=20)


def ratios_two_years():
    periods = [
        _period(
            "2025",
            2025,
            0,
            [
                ("EPS", "EPS ", 5_000.0),
                ("BV", "BV", 20_000.0),
                ("PE", "P/E", 18.0),
                ("ROA", "ROA ", 10.0),
            ],
        ),
        _period(
            "2024",
            2024,
            0,
            [
                ("EPS", "EPS ", 4_000.0),
                ("PE", "P/E", 15.0),
            ],
        ),
    ]
    return _envelope(periods, count=10)


def empty_data_null():
    """CafeF response for an unknown symbol: Data is null, Success false."""
    return json.dumps({"Data": None, "Message": "không có key symbol", "Success": False})


def cashflow_empty_value():
    """Type=3 (cashflow) returns Success:true but an empty Value array."""
    return json.dumps(
        {"Data": {"Count": 25, "Value": []}, "Message": None, "Success": True}
    )


def _src(text):
    return CafeFFundamentalSource(http_get=lambda url, params, headers: text)


def _capturing_src(text):
    captured = {}

    def _g(url, params, headers):
        captured["url"] = url
        captured["params"] = params
        captured["headers"] = headers
        return text

    return CafeFFundamentalSource(http_get=_g), captured


# --------------------------------------------------------------------------- #
# Interface parity: same method, same typed model, same unit declaration
# --------------------------------------------------------------------------- #
def test_implements_same_interface_and_unit():
    from vnfin.fundamentals.base import FundamentalSource

    src = CafeFFundamentalSource()
    assert isinstance(src, FundamentalSource)
    # declares unit for the failover unit-homogeneity guard
    assert src.unit == "VND"
    assert CafeFFundamentalSource.unit == "VND"
    assert src.name == "cafef"


def test_returns_same_typed_model():
    reports = _src(corp_income_two_years()).get_financials(
        "testco", StatementType.INCOME, Period.ANNUAL
    )
    assert isinstance(reports, tuple)
    assert all(isinstance(r, FinancialReport) for r in reports)
    assert all(isinstance(li, LineItem) for r in reports for li in r.items)


# --------------------------------------------------------------------------- #
# Normal parse: one report per fiscal period, newest first, raw VND
# --------------------------------------------------------------------------- #
def test_income_annual_parses_per_period():
    reports = _src(corp_income_two_years()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    assert len(reports) == 2
    newest = reports[0]
    assert newest.symbol == "TESTCO"
    assert newest.statement_type is StatementType.INCOME
    assert newest.period is Period.ANNUAL
    assert newest.currency == "VND"
    assert newest.source == "cafef"
    assert newest.fetched_at_utc is not None


def test_reports_sorted_newest_first():
    reports = _src(corp_income_two_years()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    dates = [r.fiscal_date.isoformat() for r in reports]
    assert dates == ["2025-12-31", "2024-12-31"]


def test_units_are_raw_vnd_no_scaling():
    reports = _src(corp_income_two_years()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    assert reports[0].get("DTTBHCCDV") == pytest.approx(12_000_000_000_000.0)


def test_statement_line_items_carry_vnd_value_unit():
    reports = _src(corp_income_two_years()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    for li in reports[0].items:
        assert li.value_unit == "VND"


def test_line_items_grouped_under_their_period():
    reports = _src(corp_income_two_years()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    newest = reports[0]
    assert len(newest.items) == 3
    codes = {li.item_code for li in newest.items}
    assert codes == {"DTTBHCCDV", "GV", "LNGBHCCDV"}
    li = next(li for li in newest.items if li.item_code == "DTTBHCCDV")
    assert li.name  # CafeF supplies a human Name


def test_quarterly_fiscal_dates_are_quarter_ends():
    reports = _src(corp_income_two_quarters()).get_financials(
        "TESTCO", StatementType.INCOME, Period.QUARTER
    )
    assert reports[0].period is Period.QUARTER
    dates = [r.fiscal_date.isoformat() for r in reports]
    # Q1-2026 -> 2026-03-31 ; Q4-2025 -> 2025-12-31
    assert dates == ["2026-03-31", "2025-12-31"]


def test_balance_type_2():
    src, captured = _capturing_src(corp_balance_one_year())
    reports = src.get_financials("TESTCO", StatementType.BALANCE, Period.ANNUAL)
    assert captured["params"]["Type"] in (2, "2")
    assert reports[0].statement_type is StatementType.BALANCE
    assert reports[0].get("TotalAsset") == pytest.approx(88_000_000_000_000.0)


def test_limit_caps_returned_periods():
    reports = _src(corp_income_two_years()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, limit=1
    )
    assert len(reports) == 1
    assert reports[0].fiscal_date.isoformat() == "2025-12-31"


# --------------------------------------------------------------------------- #
# Request shaping (endpoint + params)
# --------------------------------------------------------------------------- #
def test_income_uses_financereport_endpoint_type_1():
    src, captured = _capturing_src(corp_income_two_years())
    src.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert captured["url"].endswith("/FinanceReport.ashx")
    assert captured["params"]["Type"] in (1, "1")
    assert captured["params"]["Symbol"] == "TESTCO"
    assert captured["params"]["ReportType"] == "NAM"
    assert captured["params"]["Sort"] == "DESC"


def test_quarterly_uses_quy_reporttype():
    src, captured = _capturing_src(corp_income_two_quarters())
    src.get_financials("TESTCO", StatementType.INCOME, Period.QUARTER)
    assert captured["params"]["ReportType"] == "QUY"


def test_ratios_hit_chisotaichinh_endpoint():
    src, captured = _capturing_src(ratios_two_years())
    src.get_financials("TESTCO", StatementType.RATIOS, Period.ANNUAL)
    assert captured["url"].endswith("/GetDataChiSoTaiChinh.ashx")


# --------------------------------------------------------------------------- #
# Ratios path: period-agnostic, NOT monetary VND
# --------------------------------------------------------------------------- #
def test_ratios_parse_per_period():
    reports = _src(ratios_two_years()).get_financials(
        "TESTCO", StatementType.RATIOS, Period.ANNUAL
    )
    assert len(reports) == 2
    newest = reports[0]
    assert newest.statement_type is StatementType.RATIOS
    assert newest.get("EPS") == pytest.approx(5_000.0)
    assert newest.get("PE") == pytest.approx(18.0)


def test_ratios_report_is_period_agnostic():
    for requested in (Period.QUARTER, Period.ANNUAL):
        reports = _src(ratios_two_years()).get_financials(
            "TESTCO", StatementType.RATIOS, requested
        )
        assert reports[0].period is Period.UNKNOWN


def test_ratios_report_not_monetary_vnd():
    reports = _src(ratios_two_years()).get_financials(
        "TESTCO", StatementType.RATIOS, Period.ANNUAL
    )
    assert reports[0].currency is None


def test_ratio_line_items_have_ratio_value_unit():
    reports = _src(ratios_two_years()).get_financials(
        "TESTCO", StatementType.RATIOS, Period.ANNUAL
    )
    for li in reports[0].items:
        assert li.value_unit == "ratio"


# --------------------------------------------------------------------------- #
# Input validation (caller error, not source failure)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad_symbol", ["", "   ", "\t"])
def test_empty_symbol_raises_vnfin_error(bad_symbol):
    with pytest.raises(VnfinError):
        _src(corp_income_two_years()).get_financials(
            bad_symbol, StatementType.INCOME, Period.ANNUAL
        )


@pytest.mark.parametrize("bad_limit", [0, -1, -100])
def test_non_positive_limit_raises_vnfin_error(bad_limit):
    with pytest.raises(VnfinError):
        _src(corp_income_two_years()).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL, limit=bad_limit
        )


def test_empty_symbol_validated_before_network():
    def boom(url, params, headers):  # pragma: no cover - must not be reached
        raise AssertionError("network must not be touched on invalid input")

    src = CafeFFundamentalSource(http_get=boom)
    with pytest.raises(VnfinError):
        src.get_financials("", StatementType.INCOME, Period.ANNUAL)


# --------------------------------------------------------------------------- #
# Failover-safe error handling (reuse vnfin.exceptions, never leak raw)
# --------------------------------------------------------------------------- #
def test_unknown_symbol_data_null_raises_empty():
    with pytest.raises(EmptyData):
        _src(empty_data_null()).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


def test_empty_value_array_raises_empty():
    with pytest.raises(EmptyData):
        _src(cashflow_empty_value()).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


def test_cashflow_unsupported_raises_empty():
    """CafeF summary endpoints do not serve cash flow -> EmptyData (failover-safe)."""
    with pytest.raises(EmptyData):
        _src(cashflow_empty_value()).get_financials(
            "TESTCO", StatementType.CASHFLOW, Period.ANNUAL
        )


def test_success_false_raises_empty():
    payload = json.dumps(
        {"Data": {"Count": 0, "Value": []}, "Message": "x", "Success": False}
    )
    with pytest.raises(EmptyData):
        _src(payload).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("<html>503</html>").get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


def test_malformed_value_raises_invalid():
    bad = _envelope(
        [_period("2025", 2025, 0, [("DTTBHCCDV", "x", "not-a-number")])]
    )
    with pytest.raises(InvalidData):
        _src(bad).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_nan_value_raises_invalid():
    payload = (
        '{"Data":{"Count":1,"Value":[{"Time":"2025","Year":2025,"Quater":0,'
        '"ReportType":"HK","Conten":"x","Value":[{"Code":"DTTBHCCDV","Name":"x",'
        '"Value":NaN}]}]},"Message":null,"Success":true}'
    )
    with pytest.raises(InvalidData):
        _src(payload).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_period_missing_code_raises_invalid():
    bad = _envelope(
        [
            {
                "Time": "2025",
                "Year": 2025,
                "Quater": 0,
                "ReportType": "HK",
                "Conten": "x",
                "Value": [{"Name": "no code", "Value": 1.0}],
            }
        ]
    )
    with pytest.raises(InvalidData):
        _src(bad).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_data_not_a_dict_raises_invalid():
    bad = json.dumps({"Data": [1, 2, 3], "Message": None, "Success": True})
    with pytest.raises(InvalidData):
        _src(bad).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_value_not_a_list_raises_invalid():
    bad = json.dumps(
        {"Data": {"Count": 1, "Value": {"oops": 1}}, "Message": None, "Success": True}
    )
    with pytest.raises(InvalidData):
        _src(bad).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_transport_error_wrapped_as_source_unavailable():
    def boom(url, params, headers):
        raise ConnectionError("network down")

    src = CafeFFundamentalSource(http_get=boom)
    with pytest.raises(SourceUnavailable):
        src.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


# --------------------------------------------------------------------------- #
# to_dataframe parity
# --------------------------------------------------------------------------- #
def test_report_to_dataframe():
    reports = _src(corp_income_two_years()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    df = reports[0].to_dataframe()
    assert list(df.columns) >= ["item_code", "name", "value"]
    assert df.attrs["symbol"] == "TESTCO"
    assert df.attrs["currency"] == "VND"
    assert df.attrs["source"] == "cafef"


# --------------------------------------------------------------------------- #
# is_bank is optional (AUTO): CafeF has one shape for banks and corporates (no
# modelType template), so is_bank is purely metadata. AUTO resolves via the
# known-bank heuristic; an explicit flag always overrides it.
# --------------------------------------------------------------------------- #
def test_auto_without_is_bank_works_and_marks_corporate_for_unknown():
    """No is_bank arg succeeds and labels an unknown ticker as corporate."""
    reports = _src(corp_income_two_years()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL  # AUTO
    )
    assert reports[0].is_bank is False


def test_auto_marks_known_bank_ticker_as_bank():
    """A known-bank ticker is labelled is_bank=True under AUTO (heuristic)."""
    reports = _src(corp_income_two_years()).get_financials(
        "VCB", StatementType.INCOME, Period.ANNUAL  # AUTO, VCB is a known bank
    )
    assert reports[0].is_bank is True


def test_explicit_is_bank_true_overrides_auto():
    """Explicit is_bank=True wins for an otherwise-unknown ticker."""
    reports = _src(corp_income_two_years()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=True
    )
    assert reports[0].is_bank is True


def test_explicit_is_bank_false_overrides_heuristic_for_known_bank():
    """Explicit is_bank=False wins even for a known-bank ticker."""
    reports = _src(corp_income_two_years()).get_financials(
        "VCB", StatementType.INCOME, Period.ANNUAL, is_bank=False
    )
    assert reports[0].is_bank is False
