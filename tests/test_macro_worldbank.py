"""Tests for vnfin.macro World Bank adapter — SYNTHETIC fixtures only.

Shapes are hand-crafted to match the real World Bank Indicators API v2 envelope
(verified live 2026-06-18) but contain NO real provider rows beyond what is needed
to exercise parsing. The synthetic numbers below are illustrative, not authoritative.

World Bank response shapes covered:
- success:        [meta, [obs, ...]]
- error param:    [{"message": [{"id","key","value"}]}]
- no data:        [{"total":0,...}, null]
- empty page:     [meta, []]
- null obs value: an obs whose "value" is null (missing year) -> skipped, not InvalidData
"""
import json

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable
from vnfin.macro import IndicatorSeries, WorldBankMacroSource


# ---------------------------------------------------------------------------
# Synthetic fixtures (match real WB envelope shape, fabricated values)
# ---------------------------------------------------------------------------

INDICATOR = "FP.CPI.TOTL.ZG"
INDICATOR_NAME = "Inflation, consumer prices (annual %)"


def _obs(country_id, iso3, year, value, *, name=INDICATOR_NAME, code=INDICATOR, unit=""):
    return {
        "indicator": {"id": code, "value": name},
        "country": {"id": country_id, "value": "United States"},
        "countryiso3code": iso3,
        "date": str(year),
        "value": value,
        "unit": unit,
        "obs_status": "",
        "decimal": 1,
    }


def _meta(total, **kw):
    base = {
        "page": 1,
        "pages": 1,
        "per_page": 50,
        "total": total,
        "sourceid": "2",
        "lastupdated": "2026-04-08",
    }
    base.update(kw)
    return base


def wb_success(rows=None):
    """rows: list of (year, value). Newest-first like the real API."""
    if rows is None:
        rows = [(2023, 4.1), (2022, 8.0), (2021, 4.7)]
    obs = [_obs("US", "USA", y, v) for (y, v) in rows]
    return json.dumps([_meta(len(obs)), obs])


def wb_error():
    return json.dumps([{"message": [{"id": "120", "key": "Invalid value",
                                     "value": "The provided parameter value is not valid"}]}])


def wb_no_data():
    return json.dumps([_meta(0, page=0, pages=0, per_page=0, sourceid=None, lastupdated=None), None])


def wb_empty_page():
    return json.dumps([_meta(0), []])


def _static(text):
    def _g(url, params, headers):
        return text

    return _g


def _raising(exc):
    def _g(url, params, headers):
        raise exc

    return _g


def _src(text):
    return WorldBankMacroSource(http_get=_static(text))


# ---------------------------------------------------------------------------
# Normal parse
# ---------------------------------------------------------------------------

def test_parses_success_into_indicator_series():
    s = _src(wb_success())
    res = s.get_indicator("USA", INDICATOR, 2021, 2023)
    assert isinstance(res, IndicatorSeries)
    assert res.country == "USA"
    assert res.indicator_code == INDICATOR
    assert res.indicator_name == INDICATOR_NAME
    assert res.source == "worldbank"
    assert len(res.points) == 3


def test_points_sorted_ascending_by_date():
    # API returns newest-first; result must be chronological (oldest first).
    s = _src(wb_success())
    res = s.get_indicator("USA", INDICATOR, 2021, 2023)
    years = [d.year for (d, _v) in res.points]
    assert years == [2021, 2022, 2023]


def test_point_dates_are_plain_date_jan1():
    from datetime import date

    res = _src(wb_success()).get_indicator("USA", INDICATOR, 2021, 2023)
    d, v = res.points[0]
    assert isinstance(d, date)
    assert (d.year, d.month, d.day) == (2021, 1, 1)
    assert v == pytest.approx(4.7)


def test_carries_source_and_fetched_at_utc():
    from datetime import timezone

    res = _src(wb_success()).get_indicator("USA", INDICATOR, 2021, 2023)
    assert res.source == "worldbank"
    assert res.fetched_at_utc is not None
    assert res.fetched_at_utc.tzinfo == timezone.utc


def test_currency_is_usd_default():
    # World Bank world money series are US$; the result states currency explicitly.
    res = _src(wb_success()).get_indicator("USA", INDICATOR, 2021, 2023)
    assert res.currency == "USD"


# ---------------------------------------------------------------------------
# Units / metadata
# ---------------------------------------------------------------------------

def test_unit_captured_from_obs():
    rows_text = json.dumps([
        _meta(1),
        [_obs("US", "USA", 2023, 27_000_000.0, name="GDP (current US$)",
              code="NY.GDP.MKTP.CD", unit="")],
    ])
    res = _src(rows_text).get_indicator("USA", "NY.GDP.MKTP.CD", 2023, 2023)
    assert res.indicator_name == "GDP (current US$)"
    assert res.indicator_code == "NY.GDP.MKTP.CD"


def test_country_iso3_normalized_uppercase():
    res = _src(wb_success()).get_indicator("usa", INDICATOR, 2021, 2023)
    assert res.country == "USA"


# ---------------------------------------------------------------------------
# Null observation value -> skipped (NOT InvalidData)
# ---------------------------------------------------------------------------

def test_null_obs_value_skipped_not_invalid():
    rows = [(2024, None), (2023, 4.1), (2022, 8.0)]
    res = _src(wb_success(rows)).get_indicator("USA", INDICATOR, 2022, 2024)
    years = [d.year for (d, _v) in res.points]
    assert 2024 not in years          # null year dropped
    assert years == [2022, 2023]
    assert len(res.points) == 2


def test_all_null_values_raise_empty():
    rows = [(2024, None), (2023, None)]
    with pytest.raises(EmptyData):
        _src(wb_success(rows)).get_indicator("USA", INDICATOR, 2023, 2024)


# ---------------------------------------------------------------------------
# Empty / no-data -> EmptyData
# ---------------------------------------------------------------------------

def test_no_data_second_element_null_raises_empty():
    with pytest.raises(EmptyData):
        _src(wb_no_data()).get_indicator("USA", INDICATOR, 1800, 1800)


def test_empty_page_raises_empty():
    with pytest.raises(EmptyData):
        _src(wb_empty_page()).get_indicator("USA", INDICATOR, 1800, 1800)


# ---------------------------------------------------------------------------
# Error envelope (invalid country/indicator) -> InvalidData
# ---------------------------------------------------------------------------

def test_message_error_envelope_raises_invalid():
    with pytest.raises(InvalidData):
        _src(wb_error()).get_indicator("ZZZ", INDICATOR, 2020, 2023)


# ---------------------------------------------------------------------------
# Malformed responses -> InvalidData
# ---------------------------------------------------------------------------

def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("<html>503 Service Unavailable</html>").get_indicator("USA", INDICATOR, 2020, 2023)


def test_non_array_top_level_raises_invalid():
    with pytest.raises(InvalidData):
        _src(json.dumps({"unexpected": "object"})).get_indicator("USA", INDICATOR, 2020, 2023)


def test_malformed_scalar_value_raises_invalid():
    # value is a garbage non-numeric string -> InvalidData (failover-safe)
    rows_text = json.dumps([_meta(1), [_obs("US", "USA", 2023, "not-a-number")]])
    with pytest.raises(InvalidData):
        _src(rows_text).get_indicator("USA", INDICATOR, 2023, 2023)


def test_nan_value_raises_invalid():
    # bare NaN -> float('nan') -> non-finite guard
    payload = (
        '[{"page":1,"pages":1,"per_page":50,"total":1,"sourceid":"2","lastupdated":"x"},'
        '[{"indicator":{"id":"FP.CPI.TOTL.ZG","value":"Inflation"},'
        '"country":{"id":"US","value":"United States"},"countryiso3code":"USA",'
        '"date":"2023","value":NaN,"unit":"","obs_status":"","decimal":1}]]'
    )
    with pytest.raises(InvalidData):
        _src(payload).get_indicator("USA", INDICATOR, 2023, 2023)


def test_garbage_date_raises_invalid():
    rows_text = json.dumps([
        _meta(1),
        [{"indicator": {"id": INDICATOR, "value": INDICATOR_NAME},
          "country": {"id": "US", "value": "United States"},
          "countryiso3code": "USA", "date": "not-a-year", "value": 4.1,
          "unit": "", "obs_status": "", "decimal": 1}],
    ])
    with pytest.raises(InvalidData):
        _src(rows_text).get_indicator("USA", INDICATOR, 2020, 2023)


# ---------------------------------------------------------------------------
# Transport error -> SourceUnavailable (failover-safe)
# ---------------------------------------------------------------------------

def test_transport_error_wrapped_as_unavailable():
    s = WorldBankMacroSource(http_get=_raising(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        s.get_indicator("USA", INDICATOR, 2020, 2023)


# ---------------------------------------------------------------------------
# BOM tolerance (research doc noted WB can prepend a UTF-8 BOM)
# ---------------------------------------------------------------------------

def test_utf8_bom_prefix_tolerated():
    s = _src("﻿" + wb_success())
    res = s.get_indicator("USA", INDICATOR, 2021, 2023)
    assert len(res.points) == 3


# ---------------------------------------------------------------------------
# Request building (URL + params) — verify endpoint shape without network
# ---------------------------------------------------------------------------

def test_request_url_and_params_shape():
    captured = {}

    def _g(url, params, headers):
        captured["url"] = url
        captured["params"] = params
        captured["headers"] = headers
        return wb_success()

    WorldBankMacroSource(http_get=_g).get_indicator("usa", INDICATOR, 2021, 2023)
    assert captured["url"] == "https://api.worldbank.org/v2/country/USA/indicator/FP.CPI.TOTL.ZG"
    assert captured["params"]["format"] == "json"
    assert captured["params"]["date"] == "2021:2023"
    assert int(captured["params"]["per_page"]) >= 100
    assert "User-Agent" in captured["headers"]


def test_no_year_range_omits_date_param():
    captured = {}

    def _g(url, params, headers):
        captured["params"] = params
        return wb_success()

    WorldBankMacroSource(http_get=_g).get_indicator("USA", INDICATOR)
    assert "date" not in captured["params"]


# ---------------------------------------------------------------------------
# IndicatorSeries model conveniences
# ---------------------------------------------------------------------------

def test_indicator_series_len_and_iter():
    res = _src(wb_success()).get_indicator("USA", INDICATOR, 2021, 2023)
    assert len(res) == 3
    assert len(list(res)) == 3


def test_indicator_series_latest_returns_most_recent_point():
    res = _src(wb_success()).get_indicator("USA", INDICATOR, 2021, 2023)
    d, v = res.latest()
    assert d.year == 2023


def test_indicator_series_is_frozen():
    import dataclasses

    res = _src(wb_success()).get_indicator("USA", INDICATOR, 2021, 2023)
    with pytest.raises(dataclasses.FrozenInstanceError):
        res.country = "VNM"  # type: ignore[misc]


def test_to_dataframe_has_value_column_and_attrs():
    res = _src(wb_success()).get_indicator("USA", INDICATOR, 2021, 2023)
    df = res.to_dataframe()
    assert list(df.columns) == ["value"]
    assert df.attrs["country"] == "USA"
    assert df.attrs["indicator_code"] == INDICATOR
    assert df.attrs["source"] == "worldbank"
    assert len(df) == 3


# ---------------------------------------------------------------------------
# FRED stub — present but clearly TODO/unimplemented (no key in env yet)
# ---------------------------------------------------------------------------

def test_fred_stub_raises_not_implemented_without_key():
    from vnfin.macro import FREDMacroSource

    s = FREDMacroSource()  # no key
    with pytest.raises(NotImplementedError):
        s.get_series("CPIAUCSL")
