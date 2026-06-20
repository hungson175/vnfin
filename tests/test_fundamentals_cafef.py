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
    CafeF money is THOUSAND-VND; the adapter scales x1000 to emit raw VND
    (consistent with VNDirect). Fixtures below use thousand-VND inputs.
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
    # CafeF response rows use "HK" for annual and "H" for quarterly report tags,
    # even though the request params are NAM/QUY. Fixtures default to the
    # documented provider shape (see docs/sources/fundamentals-cafef.md).
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
    """Corporate annual income, two fiscal years — fabricated thousand-VND inputs
    (the adapter scales x1000, so assertions check raw-VND outputs)."""
    periods = [
        _period(
            "2025",
            2025,
            0,
            [
                # CafeF reports thousand-VND; adapter scales x1000 -> raw VND (12e12).
                ("DTTBHCCDV", "Doanh thu bán hàng và CCDV", 12_000_000_000),
                ("GV", "Giá vốn hàng bán", 7_000_000_000),
                ("LNGBHCCDV", "Lợi nhuận gộp", 5_000_000_000),
            ],
        ),
        _period(
            "2024",
            2024,
            0,
            [
                ("DTTBHCCDV", "Doanh thu bán hàng và CCDV", 10_000_000_000),
                ("GV", "Giá vốn hàng bán", 6_000_000_000),
                ("LNGBHCCDV", "Lợi nhuận gộp", 4_000_000_000),
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
            [("DTTBHCCDV", "Doanh thu bán hàng và CCDV", 3_000_000_000)],
            report_type="H",
        ),
        _period(
            "Q4-2025",
            2025,
            4,
            [("DTTBHCCDV", "Doanh thu bán hàng và CCDV", 2_500_000_000)],
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
                ("TotalAsset", "Tổng tài sản", 88_000_000_000),
                ("TotalShortTermDebt", "Nợ ngắn hạn", 40_000_000_000),
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


# --------------------------------------------------------------------------- #
# Regression — issue #25: source.get_financials must accept string statement and
# period values (matches top-level get_financials behavior).
# --------------------------------------------------------------------------- #
def test_cafef_source_accepts_string_statement_and_period():
    reports = _src(corp_income_two_years()).get_financials(
        "TESTCO", "income", "annual"
    )
    assert reports[0].statement_type is StatementType.INCOME
    assert reports[0].period is Period.ANNUAL


def test_cafef_source_rejects_bad_statement_string():
    with pytest.raises(VnfinError):
        _src(corp_income_two_years()).get_financials(
            "TESTCO", "not-a-statement", "annual"
        )


def test_cafef_source_rejects_bad_period_string():
    with pytest.raises(VnfinError):
        _src(corp_income_two_years()).get_financials(
            "TESTCO", "income", "not-a-period"
        )


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


def test_statement_money_emitted_as_raw_vnd():
    # CafeF thousand-VND input (12e9) -> raw-VND output (12e12) after the x1000 scale
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
# Regression — issue #4: CafeF ratio endpoint rejects quarterly EndDate anchors
# like "2-2026"; it expects a plain year. Request must coerce to annual anchor.
# --------------------------------------------------------------------------- #
def test_ratios_quarter_request_uses_year_end_date_anchor():
    src, captured = _capturing_src(ratios_two_years())
    src.get_financials("TESTCO", StatementType.RATIOS, Period.QUARTER)
    end_date = captured["params"]["EndDate"]
    # must be a plain 4-digit year, not "Q-YYYY"
    assert isinstance(end_date, str) and end_date.isdigit() and len(end_date) == 4


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
    # EPS/BV are per-share monetary values scaled to raw VND/share
    assert newest.get("EPS") == pytest.approx(5_000_000.0)
    assert newest.get("BV") == pytest.approx(20_000_000.0)
    # dimensionless ratios are unscaled
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
        if li.item_code in {"EPS", "BV"}:
            assert li.value_unit == "vnd_per_share"
        else:
            assert li.value_unit == "ratio"


# --------------------------------------------------------------------------- #
# Regression — issue #5: EPS/BV are per-share monetary values, not dimensionless
# ratios. CafeF reports them in thousand VND/share; emit raw VND/share.
# --------------------------------------------------------------------------- #
def test_eps_and_bv_emitted_as_vnd_per_share_and_scaled_to_raw_vnd():
    reports = _src(ratios_two_years()).get_financials(
        "TESTCO", StatementType.RATIOS, Period.ANNUAL
    )
    newest = reports[0]
    eps = next(li for li in newest.items if li.item_code == "EPS")
    bv = next(li for li in newest.items if li.item_code == "BV")
    pe = next(li for li in newest.items if li.item_code == "PE")

    # per-share monetary values scaled x1000 (thousand-VND -> raw VND/share)
    assert eps.value == pytest.approx(5_000_000.0)
    assert eps.value_unit == "vnd_per_share"
    assert bv.value == pytest.approx(20_000_000.0)
    assert bv.value_unit == "vnd_per_share"

    # dimensionless ratios stay unscaled and labelled "ratio"
    assert pe.value == pytest.approx(18.0)
    assert pe.value_unit == "ratio"


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


@pytest.mark.parametrize("bad_success", [None, 0, 1, "false", "true", [], {}])
def test_cafef_malformed_success_raises_invalid(bad_success):
    # Issue #119: the CafeF envelope's Success must be a real bool. Success is True -> parse;
    # Success is False -> EmptyData (failover-safe); any other shape (missing/0/1/"false"/
    # arrays/objects) is a malformed provider envelope -> InvalidData, not silently parsed.
    env = json.loads(corp_income_two_years())
    env["Success"] = bad_success
    with pytest.raises(InvalidData):
        _src(json.dumps(env)).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_cafef_missing_success_raises_invalid():
    env = json.loads(corp_income_two_years())
    env.pop("Success", None)
    with pytest.raises(InvalidData):
        _src(json.dumps(env)).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_cafef_duplicate_item_code_in_period_raises_invalid():
    # Issue #26: duplicate line-item codes within one period are schema drift and must
    # raise InvalidData rather than silently collapsing to one line item.
    env = _envelope(
        [_period("2025", 2025, 0, [("DTT", "Doanh thu", "1000"), ("DTT", "Doanh thu", "2000")])]
    )
    with pytest.raises(InvalidData):
        _src(env).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


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
        '"ReportType":"NAM","Conten":"x","Value":[{"Code":"DTTBHCCDV","Name":"x",'
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
                "ReportType": "NAM",
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


@pytest.mark.parametrize("bad", ["False", "True", 0, 1, "yes"])
def test_cafef_non_bool_is_bank_raises_vnfin_error(bad):
    """Issue #11: non-bool is_bank values are rejected, never truthy-coerced."""
    with pytest.raises(VnfinError):
        _src(corp_income_two_years()).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=bad
        )


# --------------------------------------------------------------------------- #
# Regression — issue #1: CafeF annual rows use Quater=5 (older ReportType=NAM)
# and must NOT abort the whole annual response (synthetic fixtures, FAKE values).
# --------------------------------------------------------------------------- #
from datetime import date  # noqa: E402


def _annual_income_quater_0_and_5():
    """Annual income where recent years carry Quater=0 and older years Quater=5."""
    periods = [
        _period("2025", 2025, 0, [("REV", "Revenue", 100_000)]),
        _period("2024", 2024, 0, [("REV", "Revenue", 90_000)]),
        _period("2023", 2023, 5, [("REV", "Revenue", 80_000)]),  # older annual row
        _period("2022", 2022, 5, [("REV", "Revenue", 70_000)]),
    ]
    return _envelope(periods)


def test_fiscal_date_annual_treats_quater_5_as_year_end():
    src = CafeFFundamentalSource()
    assert src._fiscal_date({"Year": 2023, "Quater": 5}, Period.ANNUAL) == date(2023, 12, 31)
    assert src._fiscal_date({"Year": 2023, "Quater": 0}, Period.ANNUAL) == date(2023, 12, 31)


def test_annual_income_with_quater_5_rows_returns_all_reports():
    reports = _src(_annual_income_quater_0_and_5()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    # before the fix, the Quater=5 rows raised InvalidData and aborted everything
    assert len(reports) == 4
    assert [r.fiscal_date.year for r in reports] == [2025, 2024, 2023, 2022]
    assert all(r.fiscal_date.month == 12 and r.fiscal_date.day == 31 for r in reports)
    assert all(not r.warnings for r in reports)  # no rows skipped here


# --------------------------------------------------------------------------- #
# Regression — issue #44: CafeF response rows use ReportType="HK" (annual) and
# "H" (quarterly), not the request-side NAM/QUY strings.
# --------------------------------------------------------------------------- #
def test_annual_request_accepts_hk_report_type():
    periods = [
        _period("2025", 2025, 0, [("REV", "Revenue", 1_000_000)], report_type="HK")
    ]
    reports = _src(_envelope(periods)).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    assert len(reports) == 1
    assert reports[0].fiscal_date == date(2025, 12, 31)


def test_quarterly_request_accepts_h_report_type():
    periods = [
        _period("Q1-2026", 2026, 1, [("REV", "Revenue", 1_000_000)], report_type="H")
    ]
    reports = _src(_envelope(periods)).get_financials(
        "TESTCO", StatementType.INCOME, Period.QUARTER
    )
    assert len(reports) == 1
    assert reports[0].fiscal_date == date(2026, 3, 31)


def test_quarterly_request_skips_annual_tagged_rows():
    # a QUARTER pull with one anomalous marker row among valid quarterly rows
    periods = [
        _period("Q2 2025", 2025, 2, [("REV", "Revenue", 50_000)], report_type="H"),
        _period("Q1 2025", 2025, 1, [("REV", "Revenue", 40_000)], report_type="H"),
        _period("odd", 2024, 9, [("REV", "Revenue", 30_000)], report_type="H"),  # out-of-range quarter marker
    ]
    reports = _src(_envelope(periods)).get_financials(
        "TESTCO", StatementType.INCOME, Period.QUARTER
    )
    assert len(reports) == 2  # odd row skipped, valid quarters preserved
    assert all(r.fiscal_date.year == 2025 for r in reports)
    # the skip is surfaced (never a silent drop)
    assert all(any("skipped" in w for w in r.warnings) for r in reports)


def test_all_rows_unparseable_fiscal_date_raises_emptydata():
    periods = [
        _period("odd1", 2025, 9, [("REV", "Revenue", 1)]),
        _period("odd2", 2024, 7, [("REV", "Revenue", 2)]),
    ]
    with pytest.raises(EmptyData):
        _src(_envelope(periods)).get_financials("TESTCO", StatementType.INCOME, Period.QUARTER)


def test_quarterly_request_skips_annual_tagged_rows():
    # Issue #45: a quarterly request must not relabel rows tagged ReportType=HK
    # as quarterly. Such rows should be skipped (with a warning) rather than
    # misreported under the requested period.
    periods = [
        _period("Q2 2025", 2025, 2, [("REV", "Revenue", 50_000)], report_type="H"),
        _period("Q1 2025", 2025, 1, [("REV", "Revenue", 40_000)], report_type="H"),
        _period("2024 annual", 2024, 0, [("REV", "Revenue", 90_000)], report_type="HK"),
    ]
    reports = _src(_envelope(periods)).get_financials(
        "TESTCO", StatementType.INCOME, Period.QUARTER
    )
    assert len(reports) == 2
    assert all(r.period is Period.QUARTER for r in reports)
    assert all(r.fiscal_date.year == 2025 for r in reports)
    assert all(any("skipped" in w for w in r.warnings) for r in reports)


def test_annual_request_skips_quarterly_tagged_rows():
    # Issue #45: an annual request must not relabel rows tagged ReportType=H
    # as annual.
    periods = [
        _period("2025", 2025, 0, [("REV", "Revenue", 100_000)], report_type="HK"),
        _period("Q4 2024", 2024, 4, [("REV", "Revenue", 30_000)], report_type="H"),
    ]
    reports = _src(_envelope(periods)).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    assert len(reports) == 1
    assert reports[0].fiscal_date == date(2025, 12, 31)
    assert any("skipped" in w for w in reports[0].warnings)


def test_period_unknown_rejected_for_statements():
    # Issue #10: Period.UNKNOWN is only meaningful for ratios; statements must
    # reject it before touching the network.
    src = CafeFFundamentalSource(http_get=lambda *a: _envelope([]))  # must not be called
    with pytest.raises(VnfinError):
        src.get_financials("TESTCO", StatementType.INCOME, Period.UNKNOWN)


def test_statement_period_with_empty_value_array_raises_empty():
    """Issue: a period object with an empty Value array must not produce a
    zero-item FinancialReport when called directly (failover-safe)."""
    periods = [
        {
            "Time": "2025",
            "Year": 2025,
            "Quater": 0,
            "ReportType": "HK",
            "Conten": "x",
            "Value": [],
        }
    ]
    with pytest.raises(EmptyData):
        _src(_envelope(periods)).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


def test_ratio_period_with_empty_value_array_raises_empty():
    """Issue: a ratio period object with an empty Value array must not produce
    a zero-item FinancialReport when called directly (failover-safe)."""
    periods = [
        {
            "Time": "2025",
            "Year": 2025,
            "Quater": 0,
            "ReportType": "HK",
            "Conten": "x",
            "Value": [],
        }
    ]
    with pytest.raises(EmptyData):
        _src(_envelope(periods)).get_financials(
            "TESTCO", StatementType.RATIOS, Period.ANNUAL
        )


# --------------------------------------------------------------------------- #
# Regression — issue #3: CafeF reports thousand-VND; adapter must emit raw VND.
# --------------------------------------------------------------------------- #
def test_cafef_statement_money_scaled_thousand_vnd_to_raw_vnd():
    # input is CafeF's thousand-VND; expected output is raw VND (x1000)
    periods = [_period("2025", 2025, 0, [("REV", "Net revenue", 62_000_000)])]  # 62M thousand-VND
    reports = _src(_envelope(periods)).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    assert reports[0].get("REV") == pytest.approx(62_000_000_000.0)  # 62B raw VND
    assert reports[0].currency == "VND"


def test_cafef_ratios_dimensionless_unscaled_per_share_monetary_scaled():
    # dimensionless ratios must NOT be multiplied by 1000; per-share monetary
    # values (EPS/BV) are scaled from thousand-VND/share to raw VND/share.
    reports = _src(ratios_two_years()).get_financials(
        "TESTCO", StatementType.RATIOS, Period.ANNUAL
    )
    assert reports[0].get("EPS") == pytest.approx(5_000_000.0)
    assert reports[0].get("BV") == pytest.approx(20_000_000.0)
    assert reports[0].get("PE") == pytest.approx(18.0)


# --------------------------------------------------------------------------- #
# Regression — issue #94: malformed Name / Year metadata must not leak or coerce
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "items,statement",
    [
        ([{"Code": "REV", "Name": ["Revenue"], "Value": 1.0}], StatementType.INCOME),
        ([{"Code": "REV", "Name": {"en": "Revenue"}, "Value": 1.0}], StatementType.INCOME),
        ([{"Code": "PE", "Name": ["PE"], "Value": 10.0}], StatementType.RATIOS),
    ],
)
def test_cafef_malformed_line_item_name_raises_invalid(items, statement):
    periods = [
        {
            "Time": "2025",
            "Year": 2025,
            "Quater": 0,
            "ReportType": "HK",
            "Conten": "x",
            "Value": items,
        }
    ]
    with pytest.raises(InvalidData, match="Name"):
        _src(_envelope(periods)).get_financials("TESTCO", statement, Period.ANNUAL)


def test_cafef_bool_year_raises_invalid():
    periods = [
        {
            "Time": "2025",
            "Year": True,
            "Quater": 0,
            "ReportType": "HK",
            "Conten": "x",
            "Value": [{"Code": "REV", "Name": "Revenue", "Value": 1.0}],
        }
    ]
    with pytest.raises(InvalidData, match="Year"):
        _src(_envelope(periods)).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


@pytest.mark.parametrize(
    "year",
    [
        2024.9,  # fractional numeric
        "+2024",  # signed string
        "02024",  # leading-zero string
    ],
)
def test_cafef_noncanonical_year_raises_invalid(year):
    """Issue #94: broad int() coercion must not normalize schema-drift values."""
    periods = [
        {
            "Time": "2025",
            "Year": year,
            "Quater": 0,
            "ReportType": "HK",
            "Conten": "x",
            "Value": [{"Code": "REV", "Name": "Revenue", "Value": 1.0}],
        }
    ]
    with pytest.raises(InvalidData, match="Year"):
        _src(_envelope(periods)).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


@pytest.mark.parametrize(
    "quater",
    [
        1.9,  # fractional numeric
        "+1",  # signed string
        "01",  # leading-zero string
    ],
)
def test_cafef_noncanonical_quater_raises_invalid(quater):
    """Issue #94: broad int() coercion must not normalize schema-drift values."""
    periods = [
        {
            "Time": "2025",
            "Year": 2025,
            "Quater": quater,
            "ReportType": "HK",
            "Conten": "x",
            "Value": [{"Code": "REV", "Name": "Revenue", "Value": 1.0}],
        }
    ]
    with pytest.raises(InvalidData, match="Quater"):
        _src(_envelope(periods)).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


def test_cafef_canonical_string_year_and_quater_accepted():
    """Valid integer strings must keep working after strict parsing."""
    periods = [
        {
            "Time": "2025",
            "Year": "2025",
            "Quater": "0",
            "ReportType": "HK",
            "Conten": "x",
            "Value": [{"Code": "REV", "Name": "Revenue", "Value": 1.0}],
        }
    ]
    reports = _src(_envelope(periods)).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    assert reports[0].fiscal_date == date(2025, 12, 31)


# --------------------------------------------------------------------------- #
# Regression — issue #26: CafeF statement/ratio periods must reject duplicate
# line-item Code values within a single period.
# --------------------------------------------------------------------------- #
def test_cafef_duplicate_statement_line_item_code_raises_invalid():
    periods = [
        _period(
            "2025",
            2025,
            0,
            [
                ("REV", "Revenue", 100_000),
                ("REV", "Revenue dup", 200_000),
            ],
        )
    ]
    with pytest.raises(InvalidData, match="duplicate"):
        _src(_envelope(periods)).get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL
        )


def test_cafef_duplicate_ratio_line_item_code_raises_invalid():
    periods = [
        _period(
            "2025",
            2025,
            0,
            [
                ("ROA", "ROA", 10.0),
                ("ROA", "ROA dup", 11.0),
            ],
        )
    ]
    with pytest.raises(InvalidData, match="duplicate"):
        _src(_envelope(periods)).get_financials(
            "TESTCO", StatementType.RATIOS, Period.ANNUAL
        )


# --------------------------------------------------------------------------- #
# Regression — issue #21: CafeF should validate response identity where the
# payload exposes it (ticker / ReportType). ReportType filtering is already
# covered above; this guards a mismatched response-level ticker field.
# --------------------------------------------------------------------------- #
def test_cafef_response_symbol_mismatch_raises_invalid():
    payload = json.dumps(
        {
            "Data": {
                "Count": 1,
                "Value": [
                    _period("2025", 2025, 0, [("REV", "Revenue", 100_000)])
                ],
            },
            "Message": None,
            "Success": True,
            "Symbol": "OTHER",
        }
    )
    with pytest.raises(InvalidData, match="OTHER"):
        _src(payload).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


# --------------------------------------------------------------------------- #
# Regression — issue #70: per-source line-item value_unit guard
# --------------------------------------------------------------------------- #
def test_cafef_rejects_invalid_line_item_value_unit():
    with pytest.raises(InvalidData):
        CafeFFundamentalSource._validate_value_unit("USD")


@pytest.mark.parametrize(
    "unit",
    ["VND", "vnd_per_share", "ratio", None],
)
def test_cafef_accepts_allowed_line_item_value_units(unit):
    CafeFFundamentalSource._validate_value_unit(unit)


def test_cafef_statement_and_ratio_line_units_are_allowed():
    allowed = {"VND", "vnd_per_share", "ratio", None}
    stmt_reports = _src(corp_income_two_years()).get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL
    )
    for li in stmt_reports[0].items:
        assert li.value_unit in allowed
    ratio_reports = _src(ratios_two_years()).get_financials(
        "TESTCO", StatementType.RATIOS, Period.ANNUAL
    )
    for li in ratio_reports[0].items:
        assert li.value_unit in allowed


# --------------------------------------------------------------------------- #
# Phase 2 contract migration — fundamentals provider-shape matrices
# (#45 ReportType, #21 Symbol top/Data, #26 Code) via vnfin._contracts.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad_rt", [None, [], {}, False, True, 123, "", "   "], ids=["null", "list", "dict", "false", "true", "int", "blank", "ws"])
def test_cafef_statement_present_malformed_reporttype_rejected(bad_rt):
    # #45: a PRESENT malformed/falsey/non-string ReportType fails closed.
    p = _period("2025", 2025, 0, [("DTTBHCCDV", "x", 1)], report_type=bad_rt)
    with pytest.raises(InvalidData):
        _src(_envelope([p])).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


@pytest.mark.parametrize("bad_rt", [[], {}, False, 123], ids=["list", "dict", "false", "int"])
def test_cafef_ratio_present_malformed_reporttype_rejected(bad_rt):
    # #45 ratio path: a present NON-NULL malformed ReportType (wrong shape) fails
    # closed (period-agnostic, so no cadence skip, but a corrupt shape still
    # rejected). NOTE: a present-NULL ReportType is tolerated for ratios — see
    # test_cafef_ratio_null_reporttype_tolerated (issue #157).
    p = _period("2025", 2025, 0, [("EPS", "EPS", 1.0)], report_type=bad_rt)
    with pytest.raises(InvalidData):
        _src(_envelope([p])).get_financials("TESTCO", StatementType.RATIOS, Period.ANNUAL)


# Issue #157: CafeF's real ratios endpoint sends rows with ``"ReportType": null``.
# Ratios are cadence-agnostic (always emitted as Period.UNKNOWN), so ReportType is
# a purely descriptive, NON-identity field there — a present-null (or absent) value
# must be TOLERATED (parsed, not raise InvalidData), consistent with the
# present-malformed-vs-absent contract: fail-closed only where identity matters.
# Before the fix this raised "cafef ratio ReportType: expected a string, got
# NoneType" and made ALL ratios unavailable for every symbol via the CafeF leg.
def test_cafef_ratio_null_reporttype_tolerated():
    p = _period("2025", 2025, 0, [("EPS", "EPS", 5_000.0), ("PE", "P/E", 18.0)], report_type=None)
    reports = _src(_envelope([p])).get_financials("TESTCO", StatementType.RATIOS, Period.ANNUAL)
    assert len(reports) == 1
    assert reports[0].statement_type is StatementType.RATIOS
    assert reports[0].period is Period.UNKNOWN
    assert reports[0].currency is None
    assert reports[0].get("PE") == 18.0


def test_cafef_ratio_missing_reporttype_key_tolerated():
    # An ABSENT ReportType key (legacy) is likewise tolerated for ratios.
    p = {
        "Time": "2025",
        "Year": 2025,
        "Quater": 0,
        "Conten": "x",
        "Value": [{"Code": "PE", "Name": "P/E", "Value": 18.0}],
    }
    reports = _src(_envelope([p])).get_financials("TESTCO", StatementType.RATIOS, Period.ANNUAL)
    assert len(reports) == 1 and reports[0].get("PE") == 18.0


@pytest.mark.parametrize("loc", ["top", "data"])
@pytest.mark.parametrize("bad", [None, "", "   ", [], {}, 123, True, "OTHER"], ids=["null", "blank", "ws", "list", "dict", "int", "bool", "mismatch"])
def test_cafef_present_malformed_or_mismatched_symbol_rejected(loc, bad):
    # #21: present Symbol (top-level OR Data) malformed/null/blank/mismatch rejected.
    payload = json.loads(corp_income_two_years())
    if loc == "top":
        payload["Symbol"] = bad
    else:
        payload["Data"]["Symbol"] = bad
    with pytest.raises(InvalidData):
        _src(json.dumps(payload)).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_cafef_valid_top_symbol_does_not_mask_contradictory_data_symbol():
    # #21 (masking note): a valid top-level Symbol must NOT cause the contradictory
    # Data.Symbol to be skipped.
    payload = json.loads(corp_income_two_years())
    payload["Symbol"] = "TESTCO"
    payload["Data"]["Symbol"] = "OTHER"
    with pytest.raises(InvalidData, match="does not match"):
        _src(json.dumps(payload)).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


@pytest.mark.parametrize(
    "bad_code",
    [None, "", "   ", 123.4, [11000], {}, True, "11000.5", "A B", "+11000", "011000", "A.B"],
    ids=["null", "blank", "ws", "frac", "list", "dict", "bool", "decimal", "space", "signed", "leadzero", "dot"],
)
def test_cafef_statement_malformed_code_rejected(bad_code):
    # #26: Code must be a canonical provider key.
    p = _period("2025", 2025, 0, [(bad_code, "x", 1)])
    with pytest.raises(InvalidData):
        _src(_envelope([p])).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


# Checkpoint C re-fix — CafeF ReportType enum contract (statements + ratio).
@pytest.mark.parametrize("bad_rt", ["UNKNOWN", " HK ", "hk ", " NAM"], ids=["unknown", "padded", "trail", "lead"])
def test_cafef_statement_unknown_or_padded_reporttype_rejected(bad_rt):
    # #45 B1: present padded/unknown ReportType fails closed (not skipped/stripped).
    p = _period("2025", 2025, 0, [("DTTBHCCDV", "x", 1)], report_type=bad_rt)
    with pytest.raises(InvalidData):
        _src(_envelope([p])).get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


@pytest.mark.parametrize("bad_rt", ["UNKNOWN", " HK ", "", "   ", True, []], ids=["unknown", "padded", "blank", "ws", "bool", "list"])
def test_cafef_ratio_unknown_or_padded_or_malformed_reporttype_rejected(bad_rt):
    # #45 B2: ratio path enforces the enum contract for a PRESENT NON-NULL value
    # (padded/unknown/blank/non-string fail closed). A present-null ReportType is
    # tolerated for ratios (see test_cafef_ratio_null_reporttype_tolerated, #157).
    p = _period("2025", 2025, 0, [("EPS", "EPS", 1.0)], report_type=bad_rt)
    with pytest.raises(InvalidData):
        _src(_envelope([p])).get_financials("TESTCO", StatementType.RATIOS, Period.ANNUAL)


@pytest.mark.parametrize("req,tag", [(Period.ANNUAL, "H"), (Period.QUARTER, "HK")])
def test_cafef_ratio_accepts_any_valid_cadence_tag(req, tag):
    # #45 B2 (documented exception): ratios are cadence-agnostic — a valid union tag
    # of either cadence is accepted and emitted as Period.UNKNOWN; only padded/unknown
    # tags reject (covered above).
    p = _period("2025", 2025, 0, [("EPS", "EPS", 1.0)], report_type=tag)
    reports = _src(_envelope([p])).get_financials("TESTCO", StatementType.RATIOS, req)
    assert len(reports) == 1 and reports[0].period is Period.UNKNOWN


@pytest.mark.parametrize(
    "bad_code",
    [None, "", 123.4, [11000], {}, True, "11000.5", "A B", "+11000", "011000"],
    ids=["null", "blank", "frac", "list", "dict", "bool", "decimal", "space", "signed", "leadzero"],
)
def test_cafef_ratio_malformed_code_rejected(bad_code):
    # #26: ratio Code matrix (not just statement Code).
    p = _period("2025", 2025, 0, [(bad_code, "x", 1.0)])
    with pytest.raises(InvalidData):
        _src(_envelope([p])).get_financials("TESTCO", StatementType.RATIOS, Period.ANNUAL)
