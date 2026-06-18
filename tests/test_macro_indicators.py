"""Tests for the canonical macro-indicator map — SYNTHETIC, no provider rows.

Only the enum/code/unit mapping logic is exercised; no network, no fixtures with
real macro values.
"""
import pytest

from vnfin.macro.indicators import (
    CANONICAL_CURRENCY,
    CANONICAL_UNIT,
    Frequency,
    MacroIndicator,
    MacroIndicatorSpec,
    canonical_currency,
    canonical_unit,
    eligible_sources,
    normalize_indicator,
)


def test_enum_members_present():
    names = {m.name for m in MacroIndicator}
    assert names == {"GDP", "GDP_GROWTH", "CPI", "INFLATION", "UNEMPLOYMENT"}


def test_percent_indicators_have_percent_unit():
    for ind in (MacroIndicator.GDP_GROWTH, MacroIndicator.INFLATION, MacroIndicator.UNEMPLOYMENT):
        assert canonical_unit(ind) == "%"


def test_level_indicators_have_distinct_units():
    assert canonical_unit(MacroIndicator.GDP) != "%"
    assert canonical_unit(MacroIndicator.CPI) != "%"


def test_every_indicator_has_a_canonical_unit():
    for m in MacroIndicator:
        assert m in CANONICAL_UNIT
        assert isinstance(CANONICAL_UNIT[m], str) and CANONICAL_UNIT[m]


def test_normalize_accepts_enum():
    assert normalize_indicator(MacroIndicator.GDP_GROWTH) is MacroIndicator.GDP_GROWTH


def test_normalize_accepts_value_string():
    assert normalize_indicator("gdp_growth") is MacroIndicator.GDP_GROWTH


def test_normalize_accepts_member_name_case_insensitive():
    assert normalize_indicator("GDP_GROWTH") is MacroIndicator.GDP_GROWTH
    assert normalize_indicator("inflation") is MacroIndicator.INFLATION


def test_normalize_rejects_unknown():
    with pytest.raises(ValueError):
        normalize_indicator("not_an_indicator")


# --- canonical currency (B7) ------------------------------------------------

def test_gdp_currency_is_usd_others_none():
    assert canonical_currency(MacroIndicator.GDP) == "USD"
    for ind in (
        MacroIndicator.GDP_GROWTH,
        MacroIndicator.INFLATION,
        MacroIndicator.UNEMPLOYMENT,
        MacroIndicator.CPI,
    ):
        assert canonical_currency(ind) is None


def test_every_indicator_has_a_currency_entry():
    for m in MacroIndicator:
        assert m in CANONICAL_CURRENCY  # value may be None


# --- MacroIndicatorSpec dataclass -------------------------------------------

def test_indicator_spec_fields():
    spec = MacroIndicatorSpec(
        provider_code="NGDP_RPCH", unit="%", frequency=Frequency.ANNUAL,
        carries_projections=True, currency=None,
    )
    assert spec.provider_code == "NGDP_RPCH"
    assert spec.unit == "%"
    assert spec.frequency is Frequency.ANNUAL
    assert spec.carries_projections is True
    assert spec.currency is None


# --- eligible_sources unit pre-filter (B6/B7) -------------------------------

class _FakeSrc:
    def __init__(self, name, unit_map):
        self.name = name
        self._unit_map = unit_map  # {MacroIndicator: unit-or-None}

    def supports(self, indicator):
        return self._unit_map.get(MacroIndicator(indicator)) is not None

    def unit_for(self, indicator):
        u = self._unit_map.get(MacroIndicator(indicator))
        if u is None:
            raise ValueError("unsupported")
        return u


def test_eligible_keeps_only_canonical_unit_sources():
    # GDP canonical unit is "current US$".
    a = _FakeSrc("a", {MacroIndicator.GDP: "current US$"})
    b = _FakeSrc("b", {MacroIndicator.GDP: "national currency"})
    c = _FakeSrc("c", {MacroIndicator.GDP: "USD bn"})
    kept = eligible_sources([a, b, c], MacroIndicator.GDP)
    assert kept == [a]


def test_eligible_drops_source_not_supporting_indicator():
    a = _FakeSrc("a", {MacroIndicator.GDP_GROWTH: "%"})  # no UNEMPLOYMENT
    b = _FakeSrc("b", {MacroIndicator.UNEMPLOYMENT: "%"})
    kept = eligible_sources([a, b], MacroIndicator.UNEMPLOYMENT)
    assert kept == [b]


def test_eligible_keeps_unit_undeclared_source():
    # A bare object with no supports/unit_for probe is unit-undeclared -> kept.
    class Bare:
        name = "bare"

    bare = Bare()
    kept = eligible_sources([bare], MacroIndicator.GDP)
    assert kept == [bare]


def test_eligible_empty_when_no_match():
    a = _FakeSrc("a", {MacroIndicator.GDP: "national currency"})
    assert eligible_sources([a], MacroIndicator.GDP) == []


def test_frequency_enum_values():
    assert {f.value for f in Frequency} == {"annual", "quarterly", "monthly", "daily"}
