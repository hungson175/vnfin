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

def test_unit_guard_rejects_mixed_units_for_indicator():
    # Two sources claim to serve GDP but in different units -> guard must raise.
    a = FakeMacroSource("a", {MacroIndicator.GDP: "current US$"})
    b = FakeMacroSource("b", {MacroIndicator.GDP: "national currency"})
    with pytest.raises(UnitMismatchError):
        get_indicator("ZZZ", MacroIndicator.GDP, sources=[a, b])


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
