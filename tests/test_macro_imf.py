"""Tests for the IMF DataMapper macro source — SYNTHETIC fixtures only.

Shapes mirror the IMF DataMapper v1 envelope
(``{"values": {"<IND>": {"<ISO3>": {"<year>": value}}}, "api": {...}}``) but
contain NO real provider rows: the country code is OBVIOUSLY FAKE (``ZZZ``), the
indicator codes are the real *shape* but values are fabricated. Only the JSON
SHAPE and validation cases mirror the provider.
"""
import json
import inspect
from datetime import date, datetime, timezone

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable
from vnfin.macro import IMFDataMapperSource, IndicatorSeries
from vnfin.macro.indicators import MacroIndicator
from vnfin.transport import HttpDataSource

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


# --- Issue #61: out-of-range numeric years must raise InvalidData -----------------

@pytest.mark.parametrize("bad_year", ["0", "10000", "-1", "-2023"])
def test_out_of_range_year_raises_invalid(bad_year):
    payload = imf_success(obs={bad_year: 1.23})
    with pytest.raises(InvalidData):
        _src(payload).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)


def test_valid_boundary_year_9999_accepted():
    payload = imf_success(obs={"9999": 1.23})
    res = _src(payload).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)
    assert res.points[0][0].year == 9999


@pytest.mark.parametrize("bad_year", ["+2024", "02024", " 2024", "2024 ", "2024.0"])
def test_noncanonical_year_key_raises_invalid(bad_year):
    # Issue #108: non-canonical year keys (signed, leading-zero, whitespace, fractional)
    # are malformed provider observation keys, not year 2024.
    payload = imf_success(obs={bad_year: 1.23})
    with pytest.raises(InvalidData):
        _src(payload).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)


# --- Issue #61 follow-up: country input validation before network -------------

@pytest.mark.parametrize("bad_country", [123, True, b"vnm", "VN/M", "V N", "VN", "USAA"])
def test_invalid_country_raises_invalid_before_network(bad_country):
    called = {"n": 0}

    def _g(url, params, headers):
        called["n"] += 1
        return imf_success()

    with pytest.raises(InvalidData):
        IMFDataMapperSource(http_get=_g).get_indicator(bad_country, MacroIndicator.GDP_GROWTH)
    assert called["n"] == 0


# --- Issue #61 follow-up: bad indicator values must raise InvalidData ---------

@pytest.mark.parametrize("bad_indicator", ["bad", 123, None])
def test_invalid_indicator_raises_invalid(bad_indicator):
    with pytest.raises(InvalidData):
        _src(imf_success()).get_indicator(COUNTRY, bad_indicator)


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


# --- projections vs actuals (B8) -------------------------------------------

def test_non_sgp_projection_boundary_warning_and_latest_are_exact(monkeypatch):
    # IMF WEO mixes actuals + forecasts. Build a series spanning past..future
    # relative to "now"; the future years must be flagged as projections and
    # latest() must return the most recent ACTUAL, never a forecast.
    now_year = 2040

    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(now_year, 6, 15, tzinfo=tz)

    monkeypatch.setattr("vnfin.macro.imf.datetime", _FrozenDateTime)
    past1, past2 = now_year - 2, now_year - 1
    future = now_year + 1
    obs = {str(past1): 1.0, str(past2): 2.0, str(now_year): 3.0, str(future): 4.0}

    res = _src(imf_success(obs=obs)).get_indicator(COUNTRY, MacroIndicator.GDP_GROWTH)

    # current year and beyond are projections.
    assert res.projection_from_year == now_year
    assert res.warnings == (
        f"imf_weo: years >= {now_year} are WEO projections "
        "(forecasts), excluded from latest()",
    )
    # latest() returns the last realized actual (the year BEFORE the projection cut).
    d, v = res.latest()
    assert d.year == past2
    assert v == pytest.approx(2.0)
    # the forecast is still available explicitly.
    di, vi = res.latest_including_projections()
    assert di.year == future
    assert vi == pytest.approx(4.0)
    # actual_points excludes the projected years.
    assert [d.year for (d, _v) in res.actual_points] == [past1, past2]


def test_non_sgp_historical_series_has_no_projection_boundary(monkeypatch):
    # A series that never reaches the current year carries no projection cut.
    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2040, 6, 15, tzinfo=tz)

    monkeypatch.setattr("vnfin.macro.imf.datetime", _FrozenDateTime)
    res = _src(imf_success(obs={"2018": 1.0, "2019": 2.0, "2020": 3.0})).get_indicator(
        COUNTRY, MacroIndicator.GDP_GROWTH
    )
    assert res.projection_from_year is None
    assert res.warnings == ()
    assert res.actual_points == res.points
    assert res.latest()[0].year == 2020


def test_gdp_carries_usd_currency_percent_carries_none():
    # B7: IMF GDP (USD bn money level) -> currency USD; percent series -> None.
    gdp = _src(imf_success(code="NGDPD", obs={"2018": 1000.0})).get_indicator(
        COUNTRY, MacroIndicator.GDP
    )
    assert gdp.currency == "USD"
    assert gdp.unit == "USD bn"
    pct = _src(imf_success(obs={"2018": 2.0})).get_indicator(
        COUNTRY, MacroIndicator.GDP_GROWTH
    )
    assert pct.currency is None


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


# --- level-indicator positivity guard (issue #16) --------------------------
def test_gdp_negative_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(imf_success(code="NGDPD", obs={"2023": -100.0})).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_gdp_zero_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(imf_success(code="NGDPD", obs={"2023": 0.0})).get_indicator(
            COUNTRY, MacroIndicator.GDP
        )


def test_percent_indicator_negative_value_allowed():
    res = _src(imf_success(obs={"2023": -2.0})).get_indicator(
        COUNTRY, MacroIndicator.GDP_GROWTH
    )
    assert res.points[0][1] == pytest.approx(-2.0)


# ---------------------------------------------------------------------------
# Issue #236 RED manifest — country-qualified IMF routing.
# ---------------------------------------------------------------------------

_GATED_IMF_CASES = [
    (MacroIndicator.GDP_GROWTH, "NGDP_RPCH"),
    (MacroIndicator.INFLATION, "PCPIPCH"),
    (MacroIndicator.UNEMPLOYMENT, "LUR"),
]


def _issue236_preflight_source(monkeypatch):
    calls = []

    def _get(url, params, headers):
        calls.append(("http", url, params, headers))
        raise AssertionError("capability preflight must run before transport")

    source = IMFDataMapperSource(http_get=_get)

    def _cache_tripwire(*args, **kwargs):
        calls.append(("raw-cache", args, kwargs))
        raise AssertionError("capability preflight must run before raw-cache lookup")

    monkeypatch.setattr(source, "_request_text", _cache_tripwire)
    return source, calls


@pytest.mark.parametrize("country", ["SGP", "sgp", " SGP "])
@pytest.mark.parametrize("indicator,_code", _GATED_IMF_CASES)
def test_sgp_gated_supports_country_is_quiet_false(
    monkeypatch, country, indicator, _code
):
    source, calls = _issue236_preflight_source(monkeypatch)
    supports_country = getattr(source, "supports_country", None)
    assert callable(supports_country), "approved supports_country API is missing"
    assert supports_country(country, indicator) is False
    assert calls == []


@pytest.mark.parametrize("country", [None, "", "SG", "USA"])
@pytest.mark.parametrize("indicator", ["not_an_indicator", MacroIndicator.CPI])
def test_imf_supports_country_quiet_false_for_malformed_or_unmapped_inputs(
    monkeypatch, country, indicator
):
    source, calls = _issue236_preflight_source(monkeypatch)
    supports_country = getattr(source, "supports_country", None)
    assert callable(supports_country), "approved supports_country API is missing"
    assert supports_country(country, indicator) is False
    assert calls == []


@pytest.mark.parametrize("country", ["USA", "usa", " USA "])
@pytest.mark.parametrize("indicator,_code", _GATED_IMF_CASES)
def test_imf_supports_country_preserves_eligible_pairs(
    monkeypatch, country, indicator, _code
):
    source, calls = _issue236_preflight_source(monkeypatch)
    supports_country = getattr(source, "supports_country", None)
    assert callable(supports_country), "approved supports_country API is missing"
    assert supports_country(country, indicator) is True
    assert supports_country("SGP", MacroIndicator.GDP) is True
    assert calls == []


def test_imf_three_entrypoints_share_one_canonical_pair_predicate(monkeypatch):
    source = IMFDataMapperSource(http_get=lambda *_: pytest.fail("transport reached"))
    predicate = getattr(source, "_supports_country_pair", None)
    assert callable(predicate), "the ratified canonical-pair predicate is missing"
    signature = inspect.signature(type(source)._supports_country_pair)
    assert tuple(signature.parameters) == ("self", "country_iso3", "indicator")
    assert signature.parameters["country_iso3"].annotation in (str, "str")
    assert signature.parameters["indicator"].annotation in (
        MacroIndicator,
        "MacroIndicator",
    )
    assert signature.return_annotation in (bool, "bool")
    seen = []

    def _spy(country, indicator):
        seen.append((country, indicator))
        return predicate(country, indicator)

    monkeypatch.setattr(source, "_supports_country_pair", _spy)
    assert source.supports_country(" sgp ", MacroIndicator.GDP_GROWTH) is False
    with pytest.raises(InvalidData, match="route is not qualified"):
        source.get_indicator("sgp", MacroIndicator.GDP_GROWTH)
    with pytest.raises(InvalidData, match="route is not qualified"):
        source.indicator_identity(" SGP ", MacroIndicator.GDP_GROWTH)
    assert seen == [
        ("SGP", MacroIndicator.GDP_GROWTH),
        ("SGP", MacroIndicator.GDP_GROWTH),
        ("SGP", MacroIndicator.GDP_GROWTH),
    ]


@pytest.mark.parametrize("country", ["SGP", "sgp", " SGP "])
@pytest.mark.parametrize("indicator,_code", _GATED_IMF_CASES)
def test_sgp_gated_direct_fetch_rejects_canonical_country_forms_before_cache_transport(
    monkeypatch, country, indicator, _code
):
    http_calls = []

    def _http_get(url, params, headers):
        http_calls.append((url, params, headers))
        raise AssertionError("country gate must run before transport")

    source = IMFDataMapperSource(http_get=_http_get)
    HttpDataSource.__init__(
        source,
        http_get=_http_get,
        timeout=25.0,
        cache_ttl=60.0,
        clock=lambda: 1000.0,
    )

    def _cache_tripwire(*args, **kwargs):
        raise AssertionError("country gate must run before raw-cache lookup")

    monkeypatch.setattr(source, "_request_text", _cache_tripwire)
    expected = (
        f"imf_datamapper: {indicator.value} route is not qualified for country=SGP"
    )
    with pytest.raises(InvalidData) as exc_info:
        source.get_indicator(country, indicator)
    assert str(exc_info.value) == expected
    assert http_calls == []


@pytest.mark.parametrize("country", ["SGP", "sgp", " SGP "])
@pytest.mark.parametrize("indicator,_code", _GATED_IMF_CASES)
def test_sgp_gated_identity_rejects_canonical_country_forms(
    country, indicator, _code
):
    source = IMFDataMapperSource(http_get=lambda *_: pytest.fail("transport reached"))
    expected = (
        f"imf_datamapper: {indicator.value} route is not qualified for country=SGP"
    )
    with pytest.raises(InvalidData) as exc_info:
        source.indicator_identity(country, indicator)
    assert str(exc_info.value) == expected


@pytest.mark.parametrize(
    "country,indicator,expected",
    [
        (
            None,
            "not_an_indicator",
            "imf_datamapper: country must be a 3-letter ISO3 code, got NoneType",
        ),
        (
            "SG",
            "not_an_indicator",
            "imf_datamapper: country must be a 3-letter ISO3 code, got 'SG'",
        ),
        (
            "",
            "not_an_indicator",
            "imf_datamapper: country must be a 3-letter ISO3 code, got ''",
        ),
        (
            None,
            MacroIndicator.CPI,
            "imf_datamapper: country must be a 3-letter ISO3 code, got NoneType",
        ),
        (
            "SG",
            MacroIndicator.CPI,
            "imf_datamapper: country must be a 3-letter ISO3 code, got 'SG'",
        ),
        (
            "",
            MacroIndicator.CPI,
            "imf_datamapper: country must be a 3-letter ISO3 code, got ''",
        ),
        (
            "USA",
            "not_an_indicator",
            "imf_datamapper: unsupported indicator 'not_an_indicator'",
        ),
        ("USA", MacroIndicator.CPI, "imf_datamapper: unsupported indicator cpi"),
    ],
)
def test_imf_fetch_mixed_invalid_remains_country_first_before_transport(
    country, indicator, expected
):
    calls = []

    def _get(url, params, headers):
        calls.append((url, params, headers))
        raise AssertionError("validation must run before transport")

    with pytest.raises(InvalidData) as exc_info:
        IMFDataMapperSource(http_get=_get).get_indicator(country, indicator)
    assert str(exc_info.value) == expected
    assert calls == []


@pytest.mark.parametrize("country", [None, "", "SG"])
@pytest.mark.parametrize(
    "indicator,expected_fragment",
    [
        ("not_an_indicator", "macro: unknown macro indicator 'not_an_indicator'"),
        (MacroIndicator.CPI, "imf_datamapper: unsupported indicator cpi"),
    ],
)
def test_imf_identity_mixed_invalid_remains_indicator_mapping_first(
    country, indicator, expected_fragment
):
    source = IMFDataMapperSource(http_get=lambda *_: pytest.fail("transport reached"))
    with pytest.raises(InvalidData) as exc_info:
        source.indicator_identity(country, indicator)
    assert str(exc_info.value).startswith(expected_fragment)


@pytest.mark.parametrize("country", ["USA", "usa", " USA "])
@pytest.mark.parametrize(
    "indicator,expected",
    [
        (MacroIndicator.GDP_GROWTH, ("NGDP_RPCH", "gdp_growth (NGDP_RPCH)")),
        (MacroIndicator.INFLATION, ("PCPIPCH", "inflation (PCPIPCH)")),
        (MacroIndicator.UNEMPLOYMENT, ("LUR", "unemployment (LUR)")),
    ],
)
def test_imf_eligible_non_sgp_identity_tuple_is_unchanged(
    country, indicator, expected
):
    source = IMFDataMapperSource(http_get=lambda *_: pytest.fail("transport reached"))
    assert source.indicator_identity(country, indicator) == expected


def test_sgp_imf_gdp_remains_unit_filtered_without_transport(monkeypatch):
    from vnfin.exceptions import AllSourcesFailed
    from vnfin.macro import default_macro_client

    calls = []

    def _get(url, params, headers):
        calls.append((url, params, headers))
        raise AssertionError("unit filter must run before transport")

    source = IMFDataMapperSource(http_get=_get)

    def _cache_tripwire(*args, **kwargs):
        raise AssertionError("unit filter must run before raw-cache lookup")

    monkeypatch.setattr(source, "_request_text", _cache_tripwire)
    with pytest.raises(AllSourcesFailed) as exc_info:
        default_macro_client(sources=[source]).get_indicator(
            "SGP", MacroIndicator.GDP
        )
    assert exc_info.value.symbol == "SGP/gdp"
    assert exc_info.value.interval is None
    assert exc_info.value.attempts == ()
    assert str(exc_info.value) == (
        "all sources failed for SGP/gdp None -> no sources attempted"
    )
    assert calls == []
