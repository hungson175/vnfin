"""Tests for the FRED BYOK macro source — SYNTHETIC fixtures only.

FRED uses the OFFICIAL JSON API (``/fred/series/observations``) and a free
bring-your-own-key (``FRED_API_KEY``). No key bundled. Missing key -> a clean,
catchable error (never a silent network call, never a leaked exception). Fixtures
use the real envelope SHAPE but fabricated dates/values; ``"."`` denotes missing.
"""
import json
from datetime import date

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable
from vnfin.macro import FREDMacroSource, IndicatorSeries


def fred_success(obs=None, units="Fake Units"):
    if obs is None:
        obs = [("2021-01-01", "1.0"), ("2022-01-01", "2.0"), ("2023-01-01", "3.0")]
    return json.dumps({
        "realtime_start": "2026-01-01",
        "realtime_end": "2026-01-01",
        "units": units,
        "observations": [
            {"realtime_start": "x", "realtime_end": "y", "date": d, "value": v}
            for (d, v) in obs
        ],
    })


def fred_empty():
    return json.dumps({"units": "Fake Units", "observations": []})


def _static(text):
    def _g(url, params, headers):
        return text
    return _g


def _raising(exc):
    def _g(url, params, headers):
        raise exc
    return _g


def _src(text, key="FAKEKEY"):
    return FREDMacroSource(api_key=key, http_get=_static(text))


# --- BYOK: no key ----------------------------------------------------------

def test_no_key_has_key_false(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    assert FREDMacroSource().has_key is False


def test_no_key_get_series_raises_catchable_source_error(monkeypatch):
    # Must be a catchable SourceError subclass (failover-safe skip), NOT a raw raise.
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    s = FREDMacroSource()
    with pytest.raises(SourceUnavailable):
        s.get_series("FAKESERIES")


def test_no_key_does_not_call_network(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    called = {"n": 0}

    def _g(url, params, headers):
        called["n"] += 1
        return fred_success()

    s = FREDMacroSource(http_get=_g)
    with pytest.raises(SourceUnavailable):
        s.get_series("FAKESERIES")
    assert called["n"] == 0


def test_key_from_env(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "envkey")
    assert FREDMacroSource().has_key is True


def test_key_from_param_overrides_env(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "envkey")
    s = FREDMacroSource(api_key="paramkey")
    assert s.has_key is True


def test_supports_false_without_key(monkeypatch):
    # C4: capability probe is False without a key (so a chain skips it pre-network).
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    from vnfin.macro.indicators import MacroIndicator

    assert FREDMacroSource().supports(MacroIndicator.GDP_GROWTH) is False


def test_supports_true_with_key():
    from vnfin.macro.indicators import MacroIndicator

    assert FREDMacroSource(api_key="k").supports(MacroIndicator.GDP_GROWTH) is True


def test_currency_not_hardcoded_usd(monkeypatch):
    # B7: an arbitrary FRED series carries no guessed USD currency.
    res = _src(fred_success(units="Percent")).get_series("FAKESERIES")
    assert res.currency is None


# --- parsing (with key) ----------------------------------------------------

def test_parses_observations_into_series():
    res = _src(fred_success()).get_series("FAKESERIES")
    assert isinstance(res, IndicatorSeries)
    assert res.source == "fred"
    assert len(res.points) == 3
    assert res.points[0] == (date(2021, 1, 1), pytest.approx(1.0))


def test_missing_value_dot_skipped():
    res = _src(fred_success(obs=[("2021-01-01", "1.0"), ("2022-01-01", "."), ("2023-01-01", "3.0")])).get_series(
        "FAKESERIES"
    )
    assert [d.year for (d, _v) in res.points] == [2021, 2023]


def test_api_key_in_request_params():
    captured = {}

    def _g(url, params, headers):
        captured["url"] = url
        captured["params"] = params
        return fred_success()

    FREDMacroSource(api_key="secret123", http_get=_g).get_series("FAKESERIES")
    assert captured["url"] == "https://api.stlouisfed.org/fred/series/observations"
    assert captured["params"]["api_key"] == "secret123"
    assert captured["params"]["series_id"] == "FAKESERIES"
    assert captured["params"]["file_type"] == "json"


def test_never_uses_fredgraph_csv():
    captured = {}

    def _g(url, params, headers):
        captured["url"] = url
        return fred_success()

    FREDMacroSource(api_key="k", http_get=_g).get_series("FAKESERIES")
    assert "fredgraph" not in captured["url"]
    assert captured["url"].endswith("/fred/series/observations")


# --- empties / malformed ---------------------------------------------------

def test_empty_observations_raises_empty():
    with pytest.raises(EmptyData):
        _src(fred_empty()).get_series("FAKESERIES")


def test_all_missing_values_raises_empty():
    with pytest.raises(EmptyData):
        _src(fred_success(obs=[("2021-01-01", "."), ("2022-01-01", ".")])).get_series("FAKESERIES")


def test_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("<html>bad key</html>").get_series("FAKESERIES")


def test_missing_observations_key_raises_invalid():
    with pytest.raises(InvalidData):
        _src(json.dumps({"units": "x"})).get_series("FAKESERIES")


def test_garbage_value_raises_invalid():
    with pytest.raises(InvalidData):
        _src(fred_success(obs=[("2021-01-01", "not-a-number")])).get_series("FAKESERIES")


def test_garbage_date_raises_invalid():
    with pytest.raises(InvalidData):
        _src(fred_success(obs=[("not-a-date", "1.0")])).get_series("FAKESERIES")


# --- transport / input -----------------------------------------------------

def test_transport_error_wrapped_as_unavailable():
    with pytest.raises(SourceUnavailable):
        FREDMacroSource(api_key="k", http_get=_raising(ConnectionError("x"))).get_series("FAKESERIES")


def test_empty_series_id_raises_invalid():
    with pytest.raises(InvalidData):
        _src(fred_success()).get_series("")


def test_non_string_series_id_raises_invalid():
    # Issue #50: bytes/int/... must raise InvalidData, not leak AttributeError/EmptyData.
    for bad in (b"GDPC1", 123, []):
        with pytest.raises(InvalidData):
            _src(fred_success()).get_series(bad)


def test_date_bounds_validated_before_request():
    # Issue #49: malformed/non-date start/end must raise InvalidData before provider call.
    captured = {"n": 0}

    def _g(url, params, headers):
        captured["n"] += 1
        return fred_success()

    src = FREDMacroSource(api_key="k", http_get=_g)
    for bad in ("not-a-date", True, "2024-13-01"):
        with pytest.raises(InvalidData):
            src.get_series("GDPC1", start=bad)
        assert captured["n"] == 0, f"http_get called for bad start={bad!r}"

    for bad in ("not-a-date", 2024, "2024-02-30"):
        with pytest.raises(InvalidData):
            src.get_series("GDPC1", end=bad)
        assert captured["n"] == 0, f"http_get called for bad end={bad!r}"


def test_valid_date_bounds_accepted():
    captured = {"params": None}

    def _g(url, params, headers):
        captured["params"] = params
        return fred_success()

    from datetime import date
    FREDMacroSource(api_key="k", http_get=_g).get_series(
        "GDPC1", start=date(2020, 1, 1), end="2024-12-31"
    )
    assert captured["params"]["observation_start"] == "2020-01-01"
    assert captured["params"]["observation_end"] == "2024-12-31"


# --- Issue #51: FRED application error envelopes must not parse as data ---------

@pytest.mark.parametrize(
    "payload",
    [
        {"error_code": 400, "error_message": "Bad Request"},
        {"error_code": 400, "error_message": "Bad Request", "observations": []},
        {"error_code": 400, "error_message": "Bad Request", "observations": [{"date": "2024-01-01", "value": "1"}]},
    ],
)
def test_application_error_envelope_raises_invalid(payload):
    with pytest.raises(InvalidData):
        FREDMacroSource(api_key="KEY", http_get=_static(json.dumps(payload))).get_series("FAKE")


def test_application_error_message_redacts_api_key():
    # Issue #51 follow-up: provider-controlled error text must never echo the BYOK key.
    key = "SECRET_FRED_KEY_123"
    payload = json.dumps(
        {"error_code": 400, "error_message": f"Bad api_key={key}"}
    )
    with pytest.raises(InvalidData) as exc_info:
        FREDMacroSource(api_key=key, http_get=_static(payload)).get_series("FAKE")
    message = str(exc_info.value)
    assert key not in message
    assert "***" in message or "api_key=" not in message


# --- Issue #58: api_key must be a non-empty string after stripping ----------------

@pytest.mark.parametrize("bad_key", ["   ", "\t\n", b"abc", 123, ["k"]])
def test_non_string_or_whitespace_api_key_treated_as_missing(monkeypatch, bad_key):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    src = FREDMacroSource(api_key=bad_key)
    assert src.has_key is False
    with pytest.raises(SourceUnavailable):
        src.get_series("GDPC1")


def test_whitespace_api_key_does_not_call_network(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    called = {"n": 0}

    def _g(url, params, headers):
        called["n"] += 1
        return fred_success()

    src = FREDMacroSource(api_key="   ", http_get=_g)
    with pytest.raises(SourceUnavailable):
        src.get_series("GDPC1")
    assert called["n"] == 0


def test_stripped_api_key_is_used():
    captured = {"params": None}

    def _g(url, params, headers):
        captured["params"] = params
        return fred_success()

    FREDMacroSource(api_key="  secret123  ", http_get=_g).get_series("GDPC1")
    assert captured["params"]["api_key"] == "secret123"


# --- Issue #24: duplicate observation dates must be rejected at the source -------

def test_duplicate_observation_dates_raise_invalid_from_get_series():
    # The source must reject duplicate dates BEFORE returning an IndicatorSeries,
    # so failover chains do not accept invalid provider output.
    payload = fred_success(obs=[("2024-01-01", "1.0"), ("2024-01-01", "2.0")])
    with pytest.raises(InvalidData) as exc_info:
        _src(payload).get_series("FAKESERIES")
    assert "2024-01-01" in str(exc_info.value)


def test_duplicate_observation_dates_out_of_order_raise_invalid():
    # Duplicates must be detected even when they are not adjacent in the response.
    payload = fred_success(
        obs=[
            ("2024-01-01", "1.0"),
            ("2024-01-02", "2.0"),
            ("2024-01-01", "3.0"),
        ]
    )
    with pytest.raises(InvalidData) as exc_info:
        _src(payload).get_series("FAKESERIES")
    assert "2024-01-01" in str(exc_info.value)
