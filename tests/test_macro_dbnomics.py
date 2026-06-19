"""Tests for the DBnomics (IMF/IFS) macro source — SYNTHETIC fixtures only.

Shape mirrors the DBnomics v22 series envelope
(``{"series": {"docs": [{"period_start_day": [...], "value": [...], ...}]}}``)
with NO real provider rows: fabricated periods/values, fake country ``ZZ``.
"""
import json
from datetime import date

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable
from vnfin.macro import DBnomicsSource, IndicatorSeries
from vnfin.macro.indicators import MacroIndicator

COUNTRY = "ZZZ"  # ISO3 requested by callers; DBnomics IFS uses a 2-letter code internally


def dbn_success(series_code="A.ZZ.NGDP_XDC", periods=None, values=None):
    if periods is None:
        periods = ["2021-01-01", "2022-01-01", "2023-01-01"]
    if values is None:
        values = [100.0, 200.0, 300.0]
    doc = {
        "@frequency": "annual",
        "dataset_code": "IFS",
        "dataset_name": "International Financial Statistics (fake)",
        "provider_code": "IMF",
        "series_code": series_code,
        "series_name": "Fake series",
        "period": [p[:4] for p in periods],
        "period_start_day": periods,
        "value": values,
    }
    return json.dumps({"series": {"docs": [doc], "num_found": 1, "limit": 1000, "offset": 0}})


def dbn_no_docs():
    return json.dumps({"series": {"docs": [], "num_found": 0}})


def _static(text):
    def _g(url, params, headers):
        return text
    return _g


def _raising(exc):
    def _g(url, params, headers):
        raise exc
    return _g


def _src(text):
    return DBnomicsSource(http_get=_static(text))


# --- parsing ---------------------------------------------------------------

def test_parses_success_into_indicator_series():
    res = _src(dbn_success()).get_indicator(COUNTRY, MacroIndicator.GDP)
    assert isinstance(res, IndicatorSeries)
    assert res.source == "dbnomics"
    assert len(res.points) == 3


def test_parallel_arrays_zipped_in_order():
    res = _src(dbn_success(
        periods=["2021-01-01", "2022-01-01"], values=[11.0, 22.0]
    )).get_indicator(COUNTRY, MacroIndicator.GDP)
    assert res.points[0] == (date(2021, 1, 1), pytest.approx(11.0))
    assert res.points[1] == (date(2022, 1, 1), pytest.approx(22.0))


def test_monthly_period_start_day_parsed():
    res = _src(dbn_success(
        series_code="M.ZZ.PCPI_IX",
        periods=["2022-01-01", "2022-02-01", "2022-03-01"],
        values=[101.0, 102.0, 103.0],
    )).get_indicator(COUNTRY, MacroIndicator.CPI)
    months = [(d.year, d.month) for (d, _v) in res.points]
    assert months == [(2022, 1), (2022, 2), (2022, 3)]


def test_unit_is_canonical_for_indicator():
    res = _src(dbn_success()).get_indicator(COUNTRY, MacroIndicator.GDP)
    # DBnomics GDP is national currency -> NOT the canonical USD level.
    assert res.unit == "national currency"


def test_cpi_unit_is_index():
    res = _src(dbn_success(series_code="M.ZZ.PCPI_IX")).get_indicator(COUNTRY, MacroIndicator.CPI)
    assert res.unit == "index"


def test_dbnomics_series_code_mismatch_raises_invalid():
    # Issue #21: a doc whose series_code names a different series (e.g. another country) must
    # raise InvalidData, not be stamped with the requested indicator identity.
    payload = dbn_success(series_code="M.US.PCPI_IX")  # request resolves to M.ZZ.PCPI_IX
    with pytest.raises(InvalidData):
        _src(payload).get_indicator(COUNTRY, MacroIndicator.CPI)


def test_source_unit_for_indicator():
    s = _src(dbn_success())
    assert s.unit_for(MacroIndicator.CPI) == "index"
    assert s.unit_for(MacroIndicator.GDP) == "national currency"


# --- request shape ---------------------------------------------------------

def test_request_url_and_observations_param():
    captured = {}

    def _g(url, params, headers):
        captured["url"] = url
        captured["params"] = params
        return dbn_success()

    DBnomicsSource(http_get=_g).get_indicator("zzz", MacroIndicator.GDP)
    assert captured["url"].startswith("https://api.db.nomics.world/v22/series/IMF/IFS/")
    assert "ZZ" in captured["url"]  # ISO3 -> ISO2 mapping in series id
    assert str(captured["params"]["observations"]) == "1"


# --- empties / nulls -------------------------------------------------------

def test_no_docs_raises_empty():
    with pytest.raises(EmptyData):
        _src(dbn_no_docs()).get_indicator(COUNTRY, MacroIndicator.GDP)


def test_null_values_skipped():
    res = _src(dbn_success(
        periods=["2021-01-01", "2022-01-01", "2023-01-01"], values=[1.0, None, 3.0]
    )).get_indicator(COUNTRY, MacroIndicator.GDP)
    years = [d.year for (d, _v) in res.points]
    assert years == [2021, 2023]


def test_na_string_value_skipped():
    # DBnomics encodes missing as the string "NA"
    res = _src(dbn_success(
        periods=["2021-01-01", "2022-01-01"], values=["NA", 5.0]
    )).get_indicator(COUNTRY, MacroIndicator.GDP)
    assert [d.year for (d, _v) in res.points] == [2022]


def test_all_null_raises_empty():
    with pytest.raises(EmptyData):
        _src(dbn_success(periods=["2021-01-01"], values=[None])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


# --- malformed -------------------------------------------------------------

def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("<html/>").get_indicator(COUNTRY, MacroIndicator.GDP)


def test_missing_series_key_raises_invalid():
    with pytest.raises(InvalidData):
        _src(json.dumps({"_meta": {}})).get_indicator(COUNTRY, MacroIndicator.GDP)


def test_length_mismatch_arrays_raises_invalid():
    with pytest.raises(InvalidData):
        _src(dbn_success(periods=["2021-01-01", "2022-01-01"], values=[1.0])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_garbage_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(dbn_success(periods=["2021-01-01"], values=["definitely-not-a-number"])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_garbage_period_raises_invalid():
    with pytest.raises(InvalidData):
        _src(dbn_success(periods=["nonsense"], values=[1.0])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_unsupported_indicator_raises_invalid():
    # GDP_GROWTH (%) is not in DBnomics/IFS map here -> InvalidData
    with pytest.raises(InvalidData):
        _src(dbn_success()).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)


# --- transport / validation ------------------------------------------------

def test_transport_error_wrapped_as_unavailable():
    with pytest.raises(SourceUnavailable):
        DBnomicsSource(http_get=_raising(TimeoutError("t"))).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_empty_country_raises_invalid():
    with pytest.raises(InvalidData):
        _src(dbn_success()).get_indicator("", MacroIndicator.GDP)


def test_unknown_country_iso3_raises_invalid():
    # A fake ISO3 with no ISO2 mapping must fail cleanly (InvalidData), not crash.
    with pytest.raises(InvalidData):
        _src(dbn_success()).get_indicator("QQQ", MacroIndicator.GDP)


# --- level-indicator positivity guard (issue #16) --------------------------
def test_gdp_negative_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(dbn_success(periods=["2023-01-01"], values=[-100.0])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_cpi_negative_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(
            dbn_success(
                series_code="M.ZZ.PCPI_IX", periods=["2023-01-01"], values=[-10.0]
            )
        ).get_indicator(COUNTRY, MacroIndicator.CPI)


def test_cpi_zero_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(
            dbn_success(
                series_code="M.ZZ.PCPI_IX", periods=["2023-01-01"], values=[0.0]
            )
        ).get_indicator(COUNTRY, MacroIndicator.CPI)


# --- period_start_day vs frequency contract (issue #104) -------------------

def test_annual_gdp_non_jan_1_raises_invalid():
    with pytest.raises(InvalidData, match="period"):
        _src(dbn_success(periods=["2024-02-01"], values=[123.0])).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_monthly_cpi_non_month_start_raises_invalid():
    with pytest.raises(InvalidData, match="period"):
        _src(
            dbn_success(
                series_code="M.ZZ.PCPI_IX", periods=["2024-01-15"], values=[123.0]
            )
        ).get_indicator(COUNTRY, MacroIndicator.CPI)

