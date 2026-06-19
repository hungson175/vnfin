"""Tests for vnfin.macro World Bank adapter — SYNTHETIC fixtures only.

Shapes are hand-crafted to match the World Bank Indicators API v2 envelope but
contain NO real provider rows. Per the synthetic-fixture policy (P0.4) the country
code is OBVIOUSLY FAKE (``ZZZ`` / ``FAKELAND``), the indicator code/name are
fabricated (``FK.TEST.IND.ZG``), and every observation value is invented — no real
country, indicator code, name, inflation %, or GDP figure from the research docs is
reused. Only the JSON envelope SHAPE and validation cases mirror the real provider.

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
from vnfin.macro.indicators import MacroIndicator


# ---------------------------------------------------------------------------
# Synthetic fixtures (match WB envelope shape; fabricated codes + values)
# ---------------------------------------------------------------------------

COUNTRY = "ZZZ"  # obviously-fake ISO3 (not a real World Bank member)
COUNTRY_NAME = "Fakeland"
INDICATOR = "FK.TEST.IND.ZG"  # fabricated WDI-style code
INDICATOR_NAME = "Fake test indicator (annual %)"


def _obs(country_id, iso3, year, value, *, name=INDICATOR_NAME, code=INDICATOR, unit=""):
    return {
        "indicator": {"id": code, "value": name},
        "country": {"id": country_id, "value": COUNTRY_NAME},
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
    """rows: list of (year, value). Newest-first like the real API.

    Values are fabricated (no real inflation/GDP figures).
    """
    if rows is None:
        rows = [(2023, 1.1), (2022, 2.2), (2021, 3.3)]
    obs = [_obs("ZZ", COUNTRY, y, v) for (y, v) in rows]
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
    res = s.get_indicator(COUNTRY, INDICATOR, 2021, 2023)
    assert isinstance(res, IndicatorSeries)
    assert res.country == COUNTRY
    assert res.indicator_code == INDICATOR
    assert res.indicator_name == INDICATOR_NAME
    assert res.source == "worldbank"
    assert len(res.points) == 3


def test_points_sorted_ascending_by_date():
    # API returns newest-first; result must be chronological (oldest first).
    s = _src(wb_success())
    res = s.get_indicator(COUNTRY, INDICATOR, 2021, 2023)
    years = [d.year for (d, _v) in res.points]
    assert years == [2021, 2022, 2023]


def test_point_dates_are_plain_date_jan1():
    from datetime import date

    res = _src(wb_success()).get_indicator(COUNTRY, INDICATOR, 2021, 2023)
    d, v = res.points[0]
    assert isinstance(d, date)
    assert (d.year, d.month, d.day) == (2021, 1, 1)
    assert v == pytest.approx(3.3)


def test_carries_source_and_fetched_at_utc():
    from datetime import timezone

    res = _src(wb_success()).get_indicator(COUNTRY, INDICATOR, 2021, 2023)
    assert res.source == "worldbank"
    assert res.fetched_at_utc is not None
    assert res.fetched_at_utc.tzinfo == timezone.utc


def test_raw_indicator_carries_no_guessed_currency():
    # B7: a raw WDI fetch does not know the canonical indicator, so the money
    # currency is unknown -> currency is None (never a hardcoded USD guess).
    res = _src(wb_success()).get_indicator(COUNTRY, INDICATOR, 2021, 2023)
    assert res.currency is None


def test_canonical_gdp_carries_usd_currency_percent_carries_none():
    # B7: currency is indicator-specific. GDP (money-denominated) -> "USD";
    # a percent series (e.g. GDP_GROWTH) -> None.
    from vnfin.macro import MacroIndicator

    gdp_text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, 2023, 999000000.0, name="Fake GDP (current US$)",
              code="NY.GDP.MKTP.CD", unit="current US$")],
    ])
    gdp = WorldBankMacroSource(http_get=lambda u, p, h: gdp_text).get_canonical_indicator(
        COUNTRY, MacroIndicator.GDP
    )
    assert gdp.currency == "USD"
    assert gdp.unit == "current US$"

    pct_text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, 2023, 4.2, name="Fake growth (%)",
              code="NY.GDP.MKTP.KD.ZG", unit="")],
    ])
    pct = WorldBankMacroSource(http_get=lambda u, p, h: pct_text).get_canonical_indicator(
        COUNTRY, MacroIndicator.GDP_GROWTH
    )
    assert pct.currency is None
    assert pct.unit == "%"


def test_canonical_gdp_negative_value_raises_invalid():
    # Level indicators (GDP) must be strictly positive.
    from vnfin.macro import MacroIndicator

    gdp_text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, 2023, -1.0, name="Fake GDP (current US$)",
              code="NY.GDP.MKTP.CD", unit="current US$")],
    ])
    with pytest.raises(InvalidData):
        WorldBankMacroSource(http_get=lambda u, p, h: gdp_text).get_canonical_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_canonical_gdp_zero_value_raises_invalid():
    from vnfin.macro import MacroIndicator

    gdp_text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, 2023, 0.0, name="Fake GDP (current US$)",
              code="NY.GDP.MKTP.CD", unit="current US$")],
    ])
    with pytest.raises(InvalidData):
        WorldBankMacroSource(http_get=lambda u, p, h: gdp_text).get_canonical_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_canonical_percent_indicator_negative_value_allowed():
    # Percent/rate indicators can legitimately be negative (e.g. deflation).
    from vnfin.macro import MacroIndicator

    pct_text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, 2023, -2.5, name="Fake growth (%)",
              code="NY.GDP.MKTP.KD.ZG", unit="")],
    ])
    res = WorldBankMacroSource(http_get=lambda u, p, h: pct_text).get_canonical_indicator(
        COUNTRY, MacroIndicator.GDP_GROWTH
    )
    assert res.points[0][1] == pytest.approx(-2.5)


# --- Issue #27: unemployment is a bounded percent rate ---------------------------


def test_canonical_unemployment_out_of_range_raises_invalid():
    from vnfin.macro import MacroIndicator

    text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, 2023, 150.0, name="Unemployment, total (% of total labor force)",
              code="SL.UEM.TOTL.ZS", unit="")],
    ])
    with pytest.raises(InvalidData):
        WorldBankMacroSource(http_get=lambda u, p, h: text).get_canonical_indicator(
            COUNTRY, MacroIndicator.UNEMPLOYMENT
        )


def test_canonical_unemployment_negative_raises_invalid():
    from vnfin.macro import MacroIndicator

    text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, 2023, -1.0, name="Unemployment, total (% of total labor force)",
              code="SL.UEM.TOTL.ZS", unit="")],
    ])
    with pytest.raises(InvalidData):
        WorldBankMacroSource(http_get=lambda u, p, h: text).get_canonical_indicator(
            COUNTRY, MacroIndicator.UNEMPLOYMENT
        )


@pytest.mark.parametrize("value", [0.0, 100.0])
def test_canonical_unemployment_boundary_values_accepted(value):
    from vnfin.macro import MacroIndicator

    text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, 2023, value, name="Unemployment, total (% of total labor force)",
              code="SL.UEM.TOTL.ZS", unit="")],
    ])
    res = WorldBankMacroSource(http_get=lambda u, p, h: text).get_canonical_indicator(
        COUNTRY, MacroIndicator.UNEMPLOYMENT
    )
    assert res.points[0][1] == pytest.approx(value)


# --- Issue #20: World Bank CPI index coverage ------------------------------------


def test_canonical_cpi_from_world_bank():
    from vnfin.macro import MacroIndicator

    text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, 2023, 126.5, name="Consumer price index (2010 = 100)",
              code="FP.CPI.TOTL", unit="")],
    ])
    res = WorldBankMacroSource(http_get=lambda u, p, h: text).get_canonical_indicator(
        COUNTRY, MacroIndicator.CPI
    )
    assert res.indicator_code == "FP.CPI.TOTL"
    assert res.unit == "index"
    assert res.currency is None
    assert res.points[0][1] == pytest.approx(126.5)


# ---------------------------------------------------------------------------
# Units / metadata
# ---------------------------------------------------------------------------

def test_unit_captured_from_obs():
    # Fabricated money-like indicator (code/name/value all invented).
    rows_text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, 2023, 123456.0, name="Fake money indicator (current US$)",
              code="FK.MONEY.CD", unit="")],
    ])
    res = _src(rows_text).get_indicator(COUNTRY, "FK.MONEY.CD", 2023, 2023)
    assert res.indicator_name == "Fake money indicator (current US$)"
    assert res.indicator_code == "FK.MONEY.CD"


def test_country_iso3_normalized_uppercase():
    res = _src(wb_success()).get_indicator("zzz", INDICATOR, 2021, 2023)
    assert res.country == "ZZZ"


# ---------------------------------------------------------------------------
# Null observation value -> skipped (NOT InvalidData)
# ---------------------------------------------------------------------------

def test_null_obs_value_skipped_not_invalid():
    rows = [(2024, None), (2023, 1.1), (2022, 2.2)]
    res = _src(wb_success(rows)).get_indicator(COUNTRY, INDICATOR, 2022, 2024)
    years = [d.year for (d, _v) in res.points]
    assert 2024 not in years          # null year dropped
    assert years == [2022, 2023]
    assert len(res.points) == 2


def test_all_null_values_raise_empty():
    rows = [(2024, None), (2023, None)]
    with pytest.raises(EmptyData):
        _src(wb_success(rows)).get_indicator(COUNTRY, INDICATOR, 2023, 2024)


# ---------------------------------------------------------------------------
# Empty / no-data -> EmptyData
# ---------------------------------------------------------------------------

def test_no_data_second_element_null_raises_empty():
    with pytest.raises(EmptyData):
        _src(wb_no_data()).get_indicator(COUNTRY, INDICATOR, 1800, 1800)


def test_empty_page_raises_empty():
    with pytest.raises(EmptyData):
        _src(wb_empty_page()).get_indicator(COUNTRY, INDICATOR, 1800, 1800)


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
        _src("<html>503 Service Unavailable</html>").get_indicator(COUNTRY, INDICATOR, 2020, 2023)


def test_non_array_top_level_raises_invalid():
    with pytest.raises(InvalidData):
        _src(json.dumps({"unexpected": "object"})).get_indicator(COUNTRY, INDICATOR, 2020, 2023)


def test_malformed_scalar_value_raises_invalid():
    # value is a garbage non-numeric string -> InvalidData (failover-safe)
    rows_text = json.dumps([_meta(1), [_obs("ZZ", COUNTRY, 2023, "not-a-number")]])
    with pytest.raises(InvalidData):
        _src(rows_text).get_indicator(COUNTRY, INDICATOR, 2023, 2023)


def test_nan_value_raises_invalid():
    # bare NaN -> float('nan') -> non-finite guard
    payload = (
        '[{"page":1,"pages":1,"per_page":50,"total":1,"sourceid":"2","lastupdated":"x"},'
        '[{"indicator":{"id":"FK.TEST.IND.ZG","value":"Fake test indicator"},'
        '"country":{"id":"ZZ","value":"Fakeland"},"countryiso3code":"ZZZ",'
        '"date":"2023","value":NaN,"unit":"","obs_status":"","decimal":1}]]'
    )
    with pytest.raises(InvalidData):
        _src(payload).get_indicator(COUNTRY, INDICATOR, 2023, 2023)


def test_garbage_date_raises_invalid():
    rows_text = json.dumps([
        _meta(1),
        [{"indicator": {"id": INDICATOR, "value": INDICATOR_NAME},
          "country": {"id": "ZZ", "value": COUNTRY_NAME},
          "countryiso3code": COUNTRY, "date": "not-a-year", "value": 1.1,
          "unit": "", "obs_status": "", "decimal": 1}],
    ])
    with pytest.raises(InvalidData):
        _src(rows_text).get_indicator(COUNTRY, INDICATOR, 2020, 2023)


# ---------------------------------------------------------------------------
# Transport error -> SourceUnavailable (failover-safe)
# ---------------------------------------------------------------------------

def test_transport_error_wrapped_as_unavailable():
    s = WorldBankMacroSource(http_get=_raising(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        s.get_indicator(COUNTRY, INDICATOR, 2020, 2023)


# ---------------------------------------------------------------------------
# BOM tolerance (research doc noted WB can prepend a UTF-8 BOM)
# ---------------------------------------------------------------------------

def test_utf8_bom_prefix_tolerated():
    s = _src("﻿" + wb_success())
    res = s.get_indicator(COUNTRY, INDICATOR, 2021, 2023)
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

    WorldBankMacroSource(http_get=_g).get_indicator("zzz", INDICATOR, 2021, 2023)
    assert captured["url"] == f"https://api.worldbank.org/v2/country/ZZZ/indicator/{INDICATOR}"
    assert captured["params"]["format"] == "json"
    assert captured["params"]["date"] == "2021:2023"
    assert int(captured["params"]["per_page"]) >= 100
    assert "User-Agent" in captured["headers"]


def test_no_year_range_omits_date_param():
    captured = {}

    def _g(url, params, headers):
        captured["params"] = params
        return wb_success()

    WorldBankMacroSource(http_get=_g).get_indicator(COUNTRY, INDICATOR)
    assert "date" not in captured["params"]


# ---------------------------------------------------------------------------
# Input validation (failover-safe: bad caller input -> InvalidData)
# ---------------------------------------------------------------------------

def test_empty_country_raises_invalid():
    with pytest.raises(InvalidData):
        _src(wb_success()).get_indicator("", INDICATOR, 2021, 2023)


def test_whitespace_country_raises_invalid():
    with pytest.raises(InvalidData):
        _src(wb_success()).get_indicator("   ", INDICATOR, 2021, 2023)


@pytest.mark.parametrize("bad_country", [123, True, False, b"vnm", ["VNM"], "VN/M", "US", "USAA"])
def test_country_must_be_string_iso3_before_network(bad_country):
    # Reviewer B1: non-string/malformed country must raise InvalidData before network.
    called = {"n": 0}

    def _g(url, params, headers):
        called["n"] += 1
        return wb_success()

    src = WorldBankMacroSource(http_get=_g)
    with pytest.raises(InvalidData):
        src.get_indicator(bad_country, INDICATOR, 2021, 2023)
    assert called["n"] == 0


def test_empty_indicator_raises_invalid():
    with pytest.raises(InvalidData):
        _src(wb_success()).get_indicator(COUNTRY, "", 2021, 2023)


def test_whitespace_indicator_raises_invalid():
    with pytest.raises(InvalidData):
        _src(wb_success()).get_indicator(COUNTRY, "   ", 2021, 2023)


def test_reversed_year_range_raises_invalid():
    # start_year after end_year is a caller error, not a silent swap.
    with pytest.raises(InvalidData):
        _src(wb_success()).get_indicator(COUNTRY, INDICATOR, 2023, 2021)


def test_validation_runs_before_network():
    # Bad input must short-circuit before any http_get call (no leaked request).
    called = {"n": 0}

    def _g(url, params, headers):
        called["n"] += 1
        return wb_success()

    src = WorldBankMacroSource(http_get=_g)
    with pytest.raises(InvalidData):
        src.get_indicator("", INDICATOR, 2021, 2023)
    assert called["n"] == 0


# --- Issue #57: indicator_code must be a non-empty string -------------------------

@pytest.mark.parametrize("bad_code", [123, ["NY.GDP"], {"code": "NY.GDP"}, b"NY.GDP", "", "   "])
def test_indicator_code_must_be_non_empty_string(bad_code):
    with pytest.raises(InvalidData):
        _src(wb_success()).get_indicator(COUNTRY, bad_code, 2021, 2023)


def test_bytes_indicator_code_rejected_before_network():
    called = {"n": 0}

    def _g(url, params, headers):
        called["n"] += 1
        return wb_success()

    src = WorldBankMacroSource(http_get=_g)
    with pytest.raises(InvalidData):
        src.get_indicator(COUNTRY, b"NY.GDP", 2021, 2023)
    assert called["n"] == 0


def test_indicator_code_is_normalized_string():
    res = _src(wb_success()).get_indicator(COUNTRY, "  fk.test.ind.zg  ", 2021, 2023)
    assert res.indicator_code == "FK.TEST.IND.ZG"


# --- Issue #63: out-of-range observation years must raise InvalidData -------------

@pytest.mark.parametrize("bad_year", ["0", "10000", "-1"])
def test_out_of_range_observation_year_raises_invalid(bad_year):
    rows_text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, bad_year, 1.23)],
    ])
    with pytest.raises(InvalidData):
        _src(rows_text).get_indicator(COUNTRY, INDICATOR, int(bad_year), int(bad_year))


def test_boundary_year_9999_accepted():
    rows_text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, 9999, 1.23)],
    ])
    res = _src(rows_text).get_indicator(COUNTRY, INDICATOR, 9999, 9999)
    assert res.points[0][0].year == 9999


@pytest.mark.parametrize("bad_year", ["+2024", "02024", " 2024", "2024 ", "2024.0"])
def test_noncanonical_observation_year_raises_invalid(bad_year):
    # Issue #108: non-canonical observation date keys (signed, leading-zero, whitespace,
    # fractional) are malformed provider keys, not year 2024.
    rows_text = json.dumps([
        _meta(1),
        [_obs("ZZ", COUNTRY, bad_year, 1.23)],
    ])
    with pytest.raises(InvalidData):
        _src(rows_text).get_indicator(COUNTRY, INDICATOR, 2024, 2024)


def test_worldbank_observation_country_mismatch_raises_invalid():
    # Issue #21: an observation whose countryiso3code does not match the requested country
    # must raise InvalidData, not be silently stamped with the requested country.
    rows_text = json.dumps([
        _meta(1),
        [_obs("US", "USA", 2024, 1.23)],  # countryiso3code USA, but request is ZZZ
    ])
    with pytest.raises(InvalidData):
        _src(rows_text).get_indicator(COUNTRY, INDICATOR, 2024, 2024)


# --- Issue #46: year bounds must be integers, not floats/bools --------------------

@pytest.mark.parametrize("bad_start", [2023.9, True, False, "not-a-year"])
def test_invalid_start_year_raises_invalid(bad_start):
    with pytest.raises(InvalidData):
        _src(wb_success()).get_indicator(COUNTRY, INDICATOR, bad_start, 2024)


@pytest.mark.parametrize("bad_end", [2024.1, True, False, "not-a-year"])
def test_invalid_end_year_raises_invalid(bad_end):
    with pytest.raises(InvalidData):
        _src(wb_success()).get_indicator(COUNTRY, INDICATOR, 2023, bad_end)


def test_year_bounds_validated_before_network():
    called = {"n": 0}

    def _g(url, params, headers):
        called["n"] += 1
        return wb_success()

    src = WorldBankMacroSource(http_get=_g)
    with pytest.raises(InvalidData):
        src.get_indicator(COUNTRY, INDICATOR, 2023.5, 2024)
    assert called["n"] == 0


def test_string_year_bounds_accepted_if_numeric():
    captured = {"params": None}

    def _g(url, params, headers):
        captured["params"] = params
        return wb_success()

    WorldBankMacroSource(http_get=_g).get_indicator(COUNTRY, INDICATOR, "2021", "2023")
    assert captured["params"]["date"] == "2021:2023"


# --- Reviewer B2: request year bounds must be within datetime.date range ----------

@pytest.mark.parametrize("bad_year", [0, -1, 10000])
def test_out_of_range_request_year_raises_invalid_before_network(bad_year):
    called = {"n": 0}

    def _g(url, params, headers):
        called["n"] += 1
        return wb_success()

    src = WorldBankMacroSource(http_get=_g)
    with pytest.raises(InvalidData):
        src.get_indicator(COUNTRY, INDICATOR, bad_year, bad_year)
    assert called["n"] == 0


@pytest.mark.parametrize("bad_year", [0, -1, 10000])
def test_out_of_range_request_end_year_raises_invalid_before_network(bad_year):
    called = {"n": 0}

    def _g(url, params, headers):
        called["n"] += 1
        return wb_success()

    src = WorldBankMacroSource(http_get=_g)
    with pytest.raises(InvalidData):
        src.get_indicator(COUNTRY, INDICATOR, 2020, bad_year)
    assert called["n"] == 0


# --- response containment (issue #105) -------------------------------------

def test_out_of_window_year_raises_empty():
    payload = wb_success(rows=[(2030, 1.0)])
    with pytest.raises(EmptyData, match="window"):
        _src(payload).get_indicator(COUNTRY, INDICATOR, 2025, 2025)


def test_in_window_years_kept_when_bounds_supplied():
    payload = wb_success(rows=[(2025, 1.0), (2030, 9.0)])
    res = _src(payload).get_indicator(COUNTRY, INDICATOR, 2025, 2025)
    assert len(res.points) == 1
    assert res.points[0][0].year == 2025


# --- descriptive metadata typing (issue #101) ----------------------------

@pytest.mark.parametrize(
    "indicator_value,country_value,unit,match",
    [
        (["GDP"], "Vietnam", "fake unit", "indicator.value"),
        ("Fake indicator", {"name": "Vietnam"}, "fake unit", "country.value"),
        ("Fake indicator", "Vietnam", ["USD"], "unit metadata"),
        (True, False, True, "indicator.value"),
    ],
)
def test_malformed_descriptive_metadata_raises_invalid(
    indicator_value, country_value, unit, match
):
    obs = {
        "indicator": {"id": INDICATOR, "value": indicator_value},
        "country": {"id": "ZZ", "value": country_value},
        "countryiso3code": COUNTRY,
        "date": "2024",
        "value": 123.0,
        "unit": unit,
        "obs_status": "",
        "decimal": 1,
    }
    payload = json.dumps([_meta(1), [obs]])
    with pytest.raises(InvalidData, match=match):
        _src(payload).get_indicator(COUNTRY, INDICATOR)


def test_malformed_canonical_metadata_raises_invalid():
    obs = {
        "indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": ["GDP growth"]},
        "country": {"id": "ZZ", "value": {"name": "Vietnam"}},
        "countryiso3code": COUNTRY,
        "date": "2024",
        "value": 3.0,
        "unit": "",
        "obs_status": "",
        "decimal": 1,
    }
    payload = json.dumps([_meta(1), [obs]])
    with pytest.raises(InvalidData):
        WorldBankMacroSource(http_get=_static(payload)).get_canonical_indicator(
            COUNTRY, MacroIndicator.GDP_GROWTH
        )


@pytest.mark.parametrize(
    "field,bad_container",
    [
        ("indicator", ["GDP"]),
        ("country", ["Vietnam"]),
    ],
)
def test_malformed_metadata_container_raises_invalid(field, bad_container):
    obs = {
        "indicator": {"id": INDICATOR, "value": INDICATOR_NAME},
        "country": {"id": "ZZ", "value": COUNTRY_NAME},
        "countryiso3code": COUNTRY,
        "date": "2024",
        "value": 123.0,
        "unit": "",
        "obs_status": "",
        "decimal": 1,
    }
    obs[field] = bad_container
    payload = json.dumps([_meta(1), [obs]])
    with pytest.raises(InvalidData, match=f"malformed {field} metadata"):
        _src(payload).get_indicator(COUNTRY, INDICATOR)



# ---------------------------------------------------------------------------
# IndicatorSeries model conveniences
# ---------------------------------------------------------------------------

def test_indicator_series_len_and_iter():
    res = _src(wb_success()).get_indicator(COUNTRY, INDICATOR, 2021, 2023)
    assert len(res) == 3
    assert len(list(res)) == 3


def test_indicator_series_latest_returns_most_recent_point():
    res = _src(wb_success()).get_indicator(COUNTRY, INDICATOR, 2021, 2023)
    d, v = res.latest()
    assert d.year == 2023


def test_indicator_series_is_frozen():
    import dataclasses

    res = _src(wb_success()).get_indicator(COUNTRY, INDICATOR, 2021, 2023)
    with pytest.raises(dataclasses.FrozenInstanceError):
        res.country = "FAK"  # type: ignore[misc]


def test_to_dataframe_has_value_column_and_attrs():
    res = _src(wb_success()).get_indicator(COUNTRY, INDICATOR, 2021, 2023)
    df = res.to_dataframe()
    # B8: an explicit per-point projection flag is part of the frame.
    assert list(df.columns) == ["value", "is_projection"]
    assert df.attrs["country"] == COUNTRY
    assert df.attrs["indicator_code"] == INDICATOR
    assert df.attrs["source"] == "worldbank"
    assert df.attrs["frequency"] == "annual"
    assert len(df) == 3
    # Annual WB series carry no projections -> all actuals.
    assert not df["is_projection"].any()


# ---------------------------------------------------------------------------
# FRED — now optional BYOK (official API). No key -> cleanly skippable
# (catchable SourceUnavailable), NOT NotImplementedError. Full FRED coverage
# lives in tests/test_macro_fred.py.
# ---------------------------------------------------------------------------

def test_fred_without_key_raises_catchable_source_error(monkeypatch):
    from vnfin.exceptions import SourceUnavailable
    from vnfin.macro import FREDMacroSource

    monkeypatch.delenv("FRED_API_KEY", raising=False)
    s = FREDMacroSource()  # no key -> BYOK skip, not a hard crash
    with pytest.raises(SourceUnavailable):
        s.get_series("FAKESERIES")
