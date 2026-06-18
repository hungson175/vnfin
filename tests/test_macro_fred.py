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
