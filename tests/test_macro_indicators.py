"""Tests for the canonical macro-indicator map — SYNTHETIC, no provider rows.

Only the enum/code/unit mapping logic is exercised; no network, no fixtures with
real macro values.
"""
import pytest

from vnfin.macro.indicators import (
    CANONICAL_UNIT,
    MacroIndicator,
    canonical_unit,
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
