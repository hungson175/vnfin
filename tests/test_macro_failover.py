"""Tests for the macro failover client + default chain — SYNTHETIC only.

Exercises ``default_macro_sources()`` and ``get_indicator(country, indicator)``
wired over the generic :class:`vnfin.failover.FailoverClient` with a per-indicator
unit-homogeneity guard. Uses fake in-memory sources and fabricated values; no
network, no real provider rows.
"""
import json
from datetime import date, datetime, timezone

import pytest

from vnfin.exceptions import (
    AllSourcesFailed,
    EmptyData,
    InvalidData,
    SourceUnavailable,
    UnitMismatchError,
)
from vnfin.macro import (
    DBnomicsSource,
    IMFDataMapperSource,
    IndicatorSeries,
    MacroIndicator,
    WorldBankMacroSource,
    default_macro_client,
    default_macro_sources,
    get_indicator,
)


# ---- fake sources (declare unit_for + get_indicator like the real ones) ----

class FakeMacroSource:
    def __init__(self, name, units, behavior=None):
        # units: {MacroIndicator: unit-str-or-None(unsupported)}
        self._name = name
        self._units = units
        self._behavior = behavior or {}

    @property
    def name(self):
        return self._name

    def unit_for(self, indicator):
        u = self._units.get(MacroIndicator(indicator))
        if u is None:
            raise InvalidData(f"{self._name}: unsupported indicator {indicator}")
        return u

    def get_indicator(self, country_iso3, indicator):
        ind = MacroIndicator(indicator)
        b = self._behavior.get(ind, "ok")
        if b == "unavailable":
            raise SourceUnavailable(f"{self._name}: down")
        if b == "empty":
            raise EmptyData(f"{self._name}: empty")
        if b == "invalid":
            raise InvalidData(f"{self._name}: bad")
        unit = self.unit_for(ind)
        return IndicatorSeries(
            country=country_iso3.upper(),
            indicator_code=f"FAKE_{ind.value}",
            indicator_name=f"Fake {ind.value}",
            points=((date(2023, 1, 1), 42.0),),
            source=self._name,
            unit=unit,
            currency="USD",
            fetched_at_utc=datetime.now(timezone.utc),
        )


PCT = {MacroIndicator.GDP_GROWTH: "%", MacroIndicator.INFLATION: "%", MacroIndicator.UNEMPLOYMENT: "%"}


# ---- default chain composition --------------------------------------------

def test_default_macro_sources_order_is_wb_imf_dbnomics():
    srcs = default_macro_sources()
    assert isinstance(srcs[0], WorldBankMacroSource)
    assert isinstance(srcs[1], IMFDataMapperSource)
    assert isinstance(srcs[2], DBnomicsSource)
    assert len(srcs) == 3


def test_default_chain_excludes_fred_byok():
    from vnfin.macro import FREDMacroSource
    srcs = default_macro_sources()
    assert not any(isinstance(s, FREDMacroSource) for s in srcs)


# ---- happy path failover ---------------------------------------------------

def test_first_source_serves_when_healthy():
    a = FakeMacroSource("a", PCT)
    b = FakeMacroSource("b", PCT)
    res = get_indicator("ZZZ", MacroIndicator.GDP_GROWTH, sources=[a, b])
    assert res.source == "a"
    assert res.unit == "%"


def test_fails_over_to_second_on_unavailable():
    a = FakeMacroSource("a", PCT, behavior={MacroIndicator.GDP_GROWTH: "unavailable"})
    b = FakeMacroSource("b", PCT)
    res = get_indicator("ZZZ", MacroIndicator.GDP_GROWTH, sources=[a, b])
    assert res.source == "b"


def test_fails_over_on_empty_then_invalid_then_ok():
    a = FakeMacroSource("a", PCT, behavior={MacroIndicator.INFLATION: "empty"})
    b = FakeMacroSource("b", PCT, behavior={MacroIndicator.INFLATION: "invalid"})
    c = FakeMacroSource("c", PCT)
    res = get_indicator("ZZZ", MacroIndicator.INFLATION, sources=[a, b, c])
    assert res.source == "c"


def test_all_fail_raises_all_sources_failed():
    a = FakeMacroSource("a", PCT, behavior={MacroIndicator.INFLATION: "unavailable"})
    b = FakeMacroSource("b", PCT, behavior={MacroIndicator.INFLATION: "empty"})
    with pytest.raises(AllSourcesFailed):
        get_indicator("ZZZ", MacroIndicator.INFLATION, sources=[a, b])


# ---- per-indicator unit guard ---------------------------------------------

def test_noncanonical_unit_source_is_filtered_out_not_raised():
    # B6/B7: the canonical GDP unit is "current US$". A source declaring a
    # different unit ("national currency") must be DROPPED before the engine is
    # built (so the default GDP chain never raises UnitMismatchError), and the
    # canonical-unit source must serve the request.
    a = FakeMacroSource("a", {MacroIndicator.GDP: "current US$"})
    b = FakeMacroSource("b", {MacroIndicator.GDP: "national currency"})
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[a, b])
    assert res.source == "a"
    assert res.unit == "current US$"


def test_only_noncanonical_unit_sources_raises_all_sources_failed():
    # If EVERY source for the indicator emits a noncanonical unit, none are
    # eligible -> a clean AllSourcesFailed (capability), never a wrong-unit result.
    a = FakeMacroSource("a", {MacroIndicator.GDP: "national currency"})
    b = FakeMacroSource("b", {MacroIndicator.GDP: "USD bn"})
    with pytest.raises(AllSourcesFailed):
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[a, b])


def test_finalize_refuses_to_relabel_a_drifted_unit():
    # B7 backstop: a source declares the canonical unit (passes the pre-filter)
    # but its returned series carries a DIFFERENT non-empty unit. finalize must
    # refuse to relabel it -> UnitMismatchError, not a silently relabelled result.
    class DriftingSource:
        name = "drift"

        def unit_for(self, indicator):
            return "current US$"  # declares canonical -> survives pre-filter

        def supports(self, indicator):
            return MacroIndicator(indicator) == MacroIndicator.GDP

        def get_indicator(self, country_iso3, indicator):
            return IndicatorSeries(
                country=country_iso3.upper(),
                indicator_code="DRIFT_GDP",
                indicator_name="Drift GDP",
                points=((date(2022, 1, 1), 1000.0),),
                source=self.name,
                unit="national currency",  # drifted away from canonical at fetch time
                fetched_at_utc=datetime.now(timezone.utc),
            )

    with pytest.raises(UnitMismatchError):
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[DriftingSource()])


def test_default_gdp_chain_does_not_raise_unit_mismatch():
    # The real default chain (WB current US$, IMF USD bn, DBnomics national
    # currency) must NOT raise UnitMismatchError for GDP: only WB is canonical, so
    # the chain reduces to WB and serves a synthetic GDP level.
    import json as _json
    from vnfin.macro import default_macro_client

    wb_text = _json.dumps([
        {"page": 1, "pages": 1, "per_page": 50, "total": 1},
        [{"indicator": {"id": "NY.GDP.MKTP.CD", "value": "Fake GDP"},
          "country": {"id": "ZZ", "value": "Fakeland"}, "countryiso3code": "ZZZ",
          "date": "2022", "value": 777000000.0, "unit": "current US$"}],
    ])
    wb = WorldBankMacroSource(http_get=lambda u, p, h: wb_text)
    imf = IMFDataMapperSource(http_get=lambda u, p, h: _json.dumps({"values": {}}))
    dbn = DBnomicsSource(http_get=lambda u, p, h: _json.dumps({"series": {"docs": []}}))
    res = default_macro_client(sources=[wb, imf, dbn]).get_indicator("ZZZ", MacroIndicator.GDP)
    assert res.source == "worldbank"
    assert res.unit == "current US$"
    assert res.currency == "USD"
    assert res.points[0][1] == pytest.approx(777000000.0)


def test_default_cpi_chain_does_not_raise_unit_mismatch():
    # CPI canonical unit is "index"; only DBnomics serves it -> chain reduces to
    # DBnomics, returns a synthetic monthly index without UnitMismatchError.
    import json as _json
    from vnfin.macro import default_macro_client

    dbn_text = _json.dumps({"series": {"docs": [{
        "series_code": "M.ZZ.PCPI_IX",
        "period_start_day": ["2022-01-01", "2022-02-01"],
        "period": ["2022", "2022"],
        "value": [110.0, 111.0],
    }]}})
    wb = WorldBankMacroSource(http_get=lambda u, p, h: _json.dumps([{"total": 0}, None]))
    imf = IMFDataMapperSource(http_get=lambda u, p, h: _json.dumps({"values": {}}))
    dbn = DBnomicsSource(http_get=lambda u, p, h: dbn_text)
    res = default_macro_client(sources=[wb, imf, dbn]).get_indicator("ZZZ", MacroIndicator.CPI)
    assert res.source == "dbnomics"
    assert res.unit == "index"
    assert res.currency is None
    assert res.frequency.value == "monthly"


def test_unit_guard_allows_same_unit_chain():
    a = FakeMacroSource("a", {MacroIndicator.GDP: "current US$"},
                        behavior={MacroIndicator.GDP: "unavailable"})
    b = FakeMacroSource("b", {MacroIndicator.GDP: "current US$"})
    res = get_indicator("ZZZ", MacroIndicator.GDP, sources=[a, b])
    assert res.source == "b"
    assert res.unit == "current US$"


def test_source_not_supporting_indicator_is_skipped_not_a_failure():
    # 'a' does not support UNEMPLOYMENT -> skipped (capability), 'b' serves it.
    a = FakeMacroSource("a", {MacroIndicator.GDP_GROWTH: "%"})  # no UNEMPLOYMENT
    b = FakeMacroSource("b", PCT)
    res = get_indicator("ZZZ", MacroIndicator.UNEMPLOYMENT, sources=[a, b])
    assert res.source == "b"


def test_no_source_supports_indicator_raises():
    a = FakeMacroSource("a", {MacroIndicator.GDP_GROWTH: "%"})
    b = FakeMacroSource("b", {MacroIndicator.GDP_GROWTH: "%"})
    with pytest.raises((AllSourcesFailed, InvalidData)):
        get_indicator("ZZZ", MacroIndicator.UNEMPLOYMENT, sources=[a, b])


# ---- BYOK skip-without-network (C4) ---------------------------------------

def test_keyless_fred_skipped_without_network_in_chain(monkeypatch):
    # C4: a BYOK source with no key must be skipped BEFORE any network call when
    # placed in a failover chain (not advertised-then-crashing, no NotImplemented).
    from vnfin.macro import FREDMacroSource

    monkeypatch.delenv("FRED_API_KEY", raising=False)
    calls = {"fred": 0}

    def fred_get(url, params, headers):
        calls["fred"] += 1
        return "{}"

    keyless_fred = FREDMacroSource(http_get=fred_get)  # no key
    wb = FakeMacroSource("wb", PCT)  # canonical percent source serves it
    res = get_indicator("ZZZ", MacroIndicator.GDP_GROWTH, sources=[keyless_fred, wb])
    assert res.source == "wb"
    assert calls["fred"] == 0  # keyless FRED never touched the network


def test_keyless_fred_supports_is_false_no_network(monkeypatch):
    # The capability probe itself must not hit the network.
    from vnfin.macro import FREDMacroSource

    monkeypatch.delenv("FRED_API_KEY", raising=False)
    calls = {"n": 0}

    def fred_get(url, params, headers):
        calls["n"] += 1
        return "{}"

    s = FREDMacroSource(http_get=fred_get)
    assert s.supports(MacroIndicator.GDP_GROWTH) is False
    assert calls["n"] == 0


# ---- client object ---------------------------------------------------------

def test_default_macro_client_get_indicator_real_sources_offline():
    # Build the real client but feed each real source a static fake http_get so
    # no network is touched; confirm WB (first) wins with synthetic GDP_GROWTH.
    wb_text = json.dumps([
        {"page": 1, "pages": 1, "per_page": 50, "total": 1},
        [{"indicator": {"id": "X", "value": "Fake growth"},
          "country": {"id": "ZZ", "value": "Fakeland"}, "countryiso3code": "ZZZ",
          "date": "2023", "value": 5.5, "unit": "", "obs_status": "", "decimal": 1}],
    ])

    def wb_get(url, params, headers):
        return wb_text

    wb = WorldBankMacroSource(http_get=wb_get)
    imf = IMFDataMapperSource(http_get=lambda u, p, h: json.dumps({"values": {}}))
    dbn = DBnomicsSource(http_get=lambda u, p, h: json.dumps({"series": {"docs": []}}))
    client = default_macro_client(sources=[wb, imf, dbn])
    res = client.get_indicator("ZZZ", MacroIndicator.GDP_GROWTH)
    assert res.source == "worldbank"
    assert res.unit == "%"
    assert res.points[0][1] == pytest.approx(5.5)


def test_client_unit_property_reflects_indicator():
    a = FakeMacroSource("a", PCT)
    b = FakeMacroSource("b", PCT)
    client = default_macro_client(sources=[a, b])
    # The client serves per-indicator; the chain unit for GDP_GROWTH is "%".
    res = client.get_indicator("ZZZ", MacroIndicator.GDP_GROWTH)
    assert res.unit == "%"


def test_empty_country_raises_invalid_before_network():
    a = FakeMacroSource("a", PCT)
    with pytest.raises(InvalidData):
        get_indicator("", MacroIndicator.GDP_GROWTH, sources=[a])


def test_unknown_indicator_raises_value_error():
    a = FakeMacroSource("a", PCT)
    with pytest.raises(ValueError):
        get_indicator("ZZZ", "not_a_real_indicator", sources=[a])
