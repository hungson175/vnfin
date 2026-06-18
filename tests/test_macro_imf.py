"""Tests for the IMF DataMapper macro source — SYNTHETIC fixtures only.

Shapes mirror the IMF DataMapper v1 envelope
(``{"values": {"<IND>": {"<ISO3>": {"<year>": value}}}, "api": {...}}``) but
contain NO real provider rows: the country code is OBVIOUSLY FAKE (``ZZZ``), the
indicator codes are the real *shape* but values are fabricated. Only the JSON
SHAPE and validation cases mirror the provider.
"""
import json
from datetime import date

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable
from vnfin.macro import IMFDataMapperSource, IndicatorSeries
from vnfin.macro.indicators import MacroIndicator

COUNTRY = "ZZZ"  # obviously-fake ISO3
IMF_CODE = "NGDP_RPCH"  # real shape; values below are fabricated


def imf_success(code=IMF_CODE, iso3=COUNTRY, obs=None):
    """obs: dict of year-str -> value. Fabricated numbers only."""
    if obs is None:
        obs = {"2021": 1.1, "2022": 2.2, "2023": 3.3}
    return json.dumps({"values": {code: {iso3: obs}}, "api": {"version": "1", "output-method": "json"}})


def imf_empty_country(code=IMF_CODE):
    # indicator present but no entry for the requested country
    return json.dumps({"values": {code: {"AAA": {"2023": 9.9}}}, "api": {"version": "1"}})


def imf_no_values():
    return json.dumps({"values": {}, "api": {"version": "1"}})


def _static(text):
    def _g(url, params, headers):
        return text
    return _g


def _raising(exc):
    def _g(url, params, headers):
        raise exc
    return _g


def _src(text):
    return IMFDataMapperSource(http_get=_static(text))


# --- parsing ---------------------------------------------------------------

def test_parses_success_into_indicator_series():
    res = _src(imf_success()).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)
    assert isinstance(res, IndicatorSeries)
    assert res.country == COUNTRY
    assert res.source == "imf_datamapper"
    assert len(res.points) == 3


def test_points_sorted_ascending_jan1():
    res = _src(imf_success()).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)
    years = [d.year for (d, _v) in res.points]
    assert years == [2021, 2022, 2023]
    d0, v0 = res.points[0]
    assert (d0.month, d0.day) == (1, 1)
    assert v0 == pytest.approx(1.1)


def test_unit_is_canonical_for_indicator():
    res = _src(imf_success()).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)
    assert res.unit == "%"


def test_source_unit_attr_matches_requested_indicator_unit():
    # The source declares the unit for the indicator it is asked about.
    s = _src(imf_success())
    assert s.unit_for(MacroIndicator.GDP_GROWTH) == "%"
    assert s.unit_for(MacroIndicator.INFLATION) == "%"


def test_carries_fetched_at_utc():
    from datetime import timezone
    res = _src(imf_success()).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)
    assert res.fetched_at_utc is not None
    assert res.fetched_at_utc.tzinfo == timezone.utc


def test_country_normalized_uppercase():
    res = IMFDataMapperSource(http_get=_static(imf_success(iso3="ZZZ"))).get_indicator(
        "zzz", MacroIndicator.GDP_GROWTH
    )
    assert res.country == "ZZZ"


# --- request shape ---------------------------------------------------------

def test_request_url_uses_indicator_code_and_iso3():
    captured = {}

    def _g(url, params, headers):
        captured["url"] = url
        return imf_success()

    IMFDataMapperSource(http_get=_g).get_indicator("zzz", MacroIndicator.GDP_GROWTH)
    assert captured["url"] == "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/ZZZ"


def test_inflation_maps_to_pcpipch():
    captured = {}

    def _g(url, params, headers):
        captured["url"] = url
        return imf_success(code="PCPIPCH")

    IMFDataMapperSource(http_get=_g).get_indicator("zzz", MacroIndicator.INFLATION)
    assert captured["url"].endswith("/PCPIPCH/ZZZ")


# --- empties ---------------------------------------------------------------

def test_country_absent_raises_empty():
    with pytest.raises(EmptyData):
        _src(imf_empty_country()).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)


def test_no_values_raises_empty():
    with pytest.raises(EmptyData):
        _src(imf_no_values()).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)


def test_all_null_obs_raises_empty():
    res_text = imf_success(obs={"2022": None, "2023": None})
    with pytest.raises(EmptyData):
        _src(res_text).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)


def test_null_obs_skipped_not_invalid():
    res = _src(imf_success(obs={"2021": 1.0, "2022": None, "2023": 3.0})).get_indicator(
        COUNTRY, MacroIndicator.GDP_GROWTH
    )
    years = [d.year for (d, _v) in res.points]
    assert years == [2021, 2023]


# --- malformed -------------------------------------------------------------

def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("<html>oops</html>").get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)


def test_missing_values_key_raises_invalid():
    with pytest.raises(InvalidData):
        _src(json.dumps({"api": {"version": "1"}})).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)


def test_garbage_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(imf_success(obs={"2023": "not-a-number"})).get_indicator(
            COUNTRY, MacroIndicator.GDP_GROWTH
        )


def test_garbage_year_raises_invalid():
    with pytest.raises(InvalidData):
        _src(imf_success(obs={"not-a-year": 1.1})).get_indicator(
            COUNTRY, MacroIndicator.GDP_GROWTH
        )


def test_unsupported_indicator_raises_invalid():
    # IMF DataMapper has no canonical CPI *index* in our map -> InvalidData (catchable)
    with pytest.raises(InvalidData):
        _src(imf_success()).get_indicator(COUNTRY, MacroIndicator.CPI)


# --- transport -------------------------------------------------------------

def test_transport_error_wrapped_as_unavailable():
    s = IMFDataMapperSource(http_get=_raising(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        s.get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)


# --- input validation ------------------------------------------------------

def test_empty_country_raises_invalid():
    with pytest.raises(InvalidData):
        _src(imf_success()).get_indicator("", MacroIndicator.GDP_GROWTH)


def test_validation_runs_before_network():
    called = {"n": 0}

    def _g(url, params, headers):
        called["n"] += 1
        return imf_success()

    with pytest.raises(InvalidData):
        IMFDataMapperSource(http_get=_g).get_indicator("  ", MacroIndicator.GDP_GROWTH)
    assert called["n"] == 0
