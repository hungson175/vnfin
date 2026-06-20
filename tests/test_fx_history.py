"""Issue #159 — historical FX primitives (annual USD/VND via World Bank PA.NUS.FCRF).

Synthetic fixtures only (fake round numbers, e.g. USD/VND = 23,000..25,000). v1 scope:
annual USD/VND from World Bank WDI ``PA.NUS.FCRF`` (country VNM), no-key, reusing the
already-tested World Bank envelope parser by composition. Spot FX (``FXRate``/``get_rate``)
is unchanged. No monthly, no non-USD cross-quotes, no asset-join/normalization helpers.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import pathlib

import pytest

import vnfin
from vnfin.diagnostics import (
    RequestDiagnostic,
    SourceCapability,
    explain_fx_coverage,
    source_capabilities,
)
from vnfin.exceptions import EmptyData, InvalidData, VnfinError
from vnfin.fx import FXHistory, FXPoint, history
from vnfin.fx.history_worldbank import WorldBankFXHistorySource
from vnfin.macro.indicators import Frequency

_FIX = pathlib.Path(__file__).parent / "fixtures" / "fx"
_WB_VNM = (_FIX / "worldbank_fx_vnm.json").read_text()


def _http(text):
    """An http_get stub returning fixed text regardless of url/params/headers."""

    def _get(url, params=None, headers=None, json_body=None):
        return text

    return _get


def _no_network(url, params=None, headers=None, json_body=None):
    raise AssertionError("must not perform any network call")


def _wb_variant(mutate):
    """Deep-copy the VNM fixture, apply ``mutate(observations_list)``, return JSON text."""
    parsed = json.loads(_WB_VNM)
    mutate(parsed[1])
    return json.dumps(parsed)


# --------------------------------------------------------------------------- #
# source: parse WB PA.NUS.FCRF -> FXHistory
# --------------------------------------------------------------------------- #
def test_source_parses_vnm_fcrf_into_fxhistory():
    src = WorldBankFXHistorySource(http_get=_http(_WB_VNM))
    h = src.get_history("USD", "VND")
    assert isinstance(h, FXHistory)
    assert h.base == "USD" and h.quote == "VND"
    assert h.unit == "VND per 1 USD" and h.value_unit == "VND per 1 USD"
    assert h.frequency is Frequency.ANNUAL
    assert h.source == "worldbank_fx"
    # null 2019 skipped; 2020..2024 present, ascending (oldest first)
    years = [p.date.year for p in h.points]
    assert years == [2020, 2021, 2022, 2023, 2024]
    assert all(isinstance(p, FXPoint) for p in h.points)
    assert h.points[0].date == dt.date(2020, 1, 1)
    assert h.points[-1].rate == pytest.approx(25000.0)
    assert h.fetched_at_utc is not None and h.fetched_at_utc.tzinfo is not None


def test_source_rejects_non_positive_rate():
    text = _wb_variant(lambda obs: obs.__setitem__(0, {**obs[0], "value": -1.0}))
    src = WorldBankFXHistorySource(http_get=_http(text))
    with pytest.raises(InvalidData):
        src.get_history("USD", "VND")


def test_source_rejects_zero_rate():
    text = _wb_variant(lambda obs: obs.__setitem__(0, {**obs[0], "value": 0.0}))
    src = WorldBankFXHistorySource(http_get=_http(text))
    with pytest.raises(InvalidData):
        src.get_history("USD", "VND")


def test_source_name_property():
    src = WorldBankFXHistorySource(http_get=_no_network)
    assert src.name == "worldbank_fx"


@pytest.mark.parametrize("bad", [True, "25000", None])
def test_validate_rate_rejects_non_numeric_or_bool(bad):
    # Defensive FX positive-rate guard (macro values may be negative; FX must be > 0 float).
    src = WorldBankFXHistorySource(http_get=_no_network)
    with pytest.raises(InvalidData):
        src._validate_rate(bad, dt.date(2024, 1, 1))


def test_source_all_null_window_is_empty_data():
    def _null_all(obs):
        for o in obs:
            o["value"] = None

    src = WorldBankFXHistorySource(http_get=_http(_wb_variant(_null_all)))
    with pytest.raises(EmptyData):
        src.get_history("USD", "VND")


# --------------------------------------------------------------------------- #
# facade: vnfin.fx.history(...)
# --------------------------------------------------------------------------- #
def test_history_facade_default_usd_vnd():
    h = history(http_get=_http(_WB_VNM))
    assert isinstance(h, FXHistory)
    assert h.base == "USD" and h.quote == "VND" and len(h) == 5


def test_history_namespaced_on_package():
    h = vnfin.fx.history(http_get=_http(_WB_VNM))
    assert isinstance(h, FXHistory)


@pytest.mark.parametrize("quote", ["usd", "EUR", "JPY"])
def test_history_rejects_non_vnd_quote(quote):
    with pytest.raises(InvalidData):
        history(quote=quote, http_get=_no_network)


@pytest.mark.parametrize("base", ["EUR", "JPY", "vnd"])
def test_history_rejects_non_usd_base(base):
    with pytest.raises(InvalidData):
        history(base=base, http_get=_no_network)


@pytest.mark.parametrize("bad", [None, 123, "US", "US D", "US/D", "", "   "])
def test_history_rejects_malformed_iso_code(bad):
    with pytest.raises(InvalidData):
        history(base=bad, http_get=_no_network)


def test_history_rejects_non_annual_frequency():
    with pytest.raises(InvalidData):
        history(frequency=Frequency.MONTHLY, http_get=_no_network)
    with pytest.raises(InvalidData):
        history(frequency="monthly", http_get=_no_network)


def test_history_accepts_annual_string_frequency():
    h = history(frequency="annual", http_get=_http(_WB_VNM))
    assert h.frequency is Frequency.ANNUAL


def test_history_inverted_dates_raise():
    with pytest.raises(VnfinError):
        history(start=dt.date(2024, 1, 1), end=dt.date(2020, 1, 1), http_get=_no_network)


# --------------------------------------------------------------------------- #
# annual start/end YEAR-inclusive semantics
# --------------------------------------------------------------------------- #
def test_year_window_both_bounds_inclusive():
    h = history(start=dt.date(2021, 1, 1), end=dt.date(2023, 12, 31), http_get=_http(_WB_VNM))
    assert [p.date.year for p in h.points] == [2021, 2022, 2023]


def test_year_window_midyear_start_does_not_drop_jan1_year():
    # start is mid-2021; the 2021 annual point is stamped Jan 1 and MUST be kept.
    h = history(start=dt.date(2021, 7, 15), end=dt.date(2022, 6, 30), http_get=_http(_WB_VNM))
    assert [p.date.year for p in h.points] == [2021, 2022]


def test_year_window_start_only():
    h = history(start=dt.date(2023, 1, 1), http_get=_http(_WB_VNM))
    assert [p.date.year for p in h.points] == [2023, 2024]


def test_year_window_end_only():
    h = history(end=dt.date(2021, 12, 31), http_get=_http(_WB_VNM))
    assert [p.date.year for p in h.points] == [2020, 2021]


def test_year_window_no_bounds_returns_all():
    h = history(http_get=_http(_WB_VNM))
    assert [p.date.year for p in h.points] == [2020, 2021, 2022, 2023, 2024]


def test_year_window_empty_selection_is_empty_data():
    with pytest.raises(EmptyData):
        history(start=dt.date(2030, 1, 1), end=dt.date(2031, 12, 31), http_get=_http(_WB_VNM))


# --------------------------------------------------------------------------- #
# FXHistory accessors
# --------------------------------------------------------------------------- #
def test_rate_on_exact_match():
    h = history(http_get=_http(_WB_VNM))
    assert h.rate_on(dt.date(2022, 1, 1)) == pytest.approx(24000.0)


def test_rate_on_missing_raises_never_fills():
    h = history(http_get=_http(_WB_VNM))
    with pytest.raises(InvalidData):
        h.rate_on(dt.date(2022, 6, 30))  # mid-year: no fill/interpolation
    with pytest.raises(InvalidData):
        h.rate_on(dt.date(2019, 1, 1))  # outside coverage


def test_rate_for_year_sugar():
    h = history(http_get=_http(_WB_VNM))
    assert h.rate_for_year(2021) == pytest.approx(23500.0)
    with pytest.raises(InvalidData):
        h.rate_for_year(1999)


def test_latest_returns_most_recent_point():
    h = history(http_get=_http(_WB_VNM))
    latest = h.latest()
    assert isinstance(latest, FXPoint)
    assert latest.date == dt.date(2024, 1, 1) and latest.rate == pytest.approx(25000.0)


# --------------------------------------------------------------------------- #
# to_dataframe
# --------------------------------------------------------------------------- #
def test_to_dataframe_shape_and_attrs():
    pytest.importorskip("pandas")
    h = history(http_get=_http(_WB_VNM))
    df = h.to_dataframe()
    assert list(df.columns) == ["rate"]
    assert df.index.name == "date"
    assert len(df) == 5
    assert df.attrs["base"] == "USD" and df.attrs["quote"] == "VND"
    assert df.attrs["unit"] == "VND per 1 USD"
    assert df.attrs["source"] == "worldbank_fx"
    assert df.attrs["frequency"] == "annual"


# --------------------------------------------------------------------------- #
# diagnostics: explain_fx_coverage (offline)
# --------------------------------------------------------------------------- #
def test_explain_fx_coverage_ok_offline():
    d = explain_fx_coverage("USD", "VND", dt.date(2010, 1, 1), dt.date(2020, 12, 31))
    assert isinstance(d, RequestDiagnostic)
    assert d.status == "ok"
    assert d.sources and d.sources[0].source == "worldbank_fx"


def test_explain_fx_coverage_pre_coverage_is_gap():
    d = explain_fx_coverage("USD", "VND", dt.date(1970, 1, 1), dt.date(1975, 12, 31))
    assert d.status == "coverage_gap"
    assert d.suggested_actions


def test_explain_fx_coverage_unsupported_pair():
    d = explain_fx_coverage("EUR", "VND", dt.date(2010, 1, 1), dt.date(2020, 12, 31))
    assert d.status == "unsupported_pair"
    d2 = explain_fx_coverage("USD", "JPY", dt.date(2010, 1, 1), dt.date(2020, 12, 31))
    assert d2.status == "unsupported_pair"


def test_explain_fx_coverage_unsupported_frequency():
    d = explain_fx_coverage(
        "USD", "VND", dt.date(2010, 1, 1), dt.date(2020, 12, 31), frequency=Frequency.MONTHLY
    )
    assert d.status == "unsupported_frequency"


def test_explain_fx_coverage_is_offline():
    # no http_get parameter exists; the call must never touch the network
    explain_fx_coverage("USD", "VND", dt.date(2010, 1, 1), dt.date(2020, 12, 31))


def test_explain_fx_coverage_inverted_dates_raise():
    with pytest.raises(VnfinError):
        explain_fx_coverage("USD", "VND", dt.date(2024, 1, 1), dt.date(2020, 1, 1))


def test_fx_capability_in_registry():
    caps = source_capabilities()
    fx = [c for c in caps if c.domain == "fx"]
    assert fx and fx[0].source == "worldbank_fx"
    assert fx[0].granularity == "annual"
    assert fx[0].coverage_start == dt.date(1983, 1, 1)
    assert fx[0].is_single_source
