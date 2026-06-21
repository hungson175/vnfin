"""Tests for the canonical macro-indicator map — SYNTHETIC, no provider rows.

Only the enum/code/unit mapping logic is exercised; no network, no fixtures with
real macro values.
"""
import pytest

from datetime import date

from vnfin.macro.indicators import (
    CANONICAL_CURRENCY,
    CANONICAL_UNIT,
    Frequency,
    MacroIndicator,
    MacroIndicatorSpec,
    canonical_currency,
    canonical_indicator_code,
    canonical_indicator_name,
    canonical_unit,
    eligible_sources,
    is_level_indicator,
    normalize_indicator,
    validate_indicator_values,
)


def test_enum_members_present():
    names = {m.name for m in MacroIndicator}
    assert names == {
        "GDP",
        "GDP_GROWTH",
        "CPI",
        "INFLATION",
        "UNEMPLOYMENT",
        "CPI_YOY",
        "POLICY_RATE",
        # #152: World Bank annual fixed-income rate indicators.
        "LENDING_RATE",
        "DEPOSIT_RATE",
        "REAL_INTEREST_RATE",
    }


# --- #152: World Bank annual fixed-income rates -----------------------------

def test_lending_rate_canonical_maps():
    # #152: a NEW dedicated WB-annual indicator (% p.a., not a rate level).
    assert MacroIndicator.LENDING_RATE.value == "lending_rate"
    assert canonical_unit(MacroIndicator.LENDING_RATE) == "%"
    assert canonical_currency(MacroIndicator.LENDING_RATE) is None
    assert canonical_indicator_code(MacroIndicator.LENDING_RATE) == "lending_rate"
    assert canonical_indicator_name(MacroIndicator.LENDING_RATE) == "Lending Rate"


def test_deposit_rate_canonical_maps():
    assert MacroIndicator.DEPOSIT_RATE.value == "deposit_rate"
    assert canonical_unit(MacroIndicator.DEPOSIT_RATE) == "%"
    assert canonical_currency(MacroIndicator.DEPOSIT_RATE) is None
    assert canonical_indicator_code(MacroIndicator.DEPOSIT_RATE) == "deposit_rate"
    assert canonical_indicator_name(MacroIndicator.DEPOSIT_RATE) == "Deposit Rate"


def test_real_interest_rate_canonical_maps():
    assert MacroIndicator.REAL_INTEREST_RATE.value == "real_interest_rate"
    assert canonical_unit(MacroIndicator.REAL_INTEREST_RATE) == "%"
    assert canonical_currency(MacroIndicator.REAL_INTEREST_RATE) is None
    assert canonical_indicator_code(MacroIndicator.REAL_INTEREST_RATE) == "real_interest_rate"
    assert canonical_indicator_name(MacroIndicator.REAL_INTEREST_RATE) == "Real Interest Rate"


def test_new_rate_indicators_not_level_or_bounded():
    # Rates are percent series, not >0 levels; a real interest rate may be negative.
    for ind in (
        MacroIndicator.LENDING_RATE,
        MacroIndicator.DEPOSIT_RATE,
        MacroIndicator.REAL_INTEREST_RATE,
    ):
        assert is_level_indicator(ind) is False
        validate_indicator_values(ind, [(date(2023, 1, 1), 5.0)], "x")  # accepted unbounded
    # a negative real interest rate (inflation > nominal) is legitimate
    validate_indicator_values(
        MacroIndicator.REAL_INTEREST_RATE, [(date(2023, 1, 1), -1.5)], "x"
    )


# --- #179: monthly CPI YoY + SBV policy rate (DBnomics-only) ----------------

def test_cpi_yoy_canonical_maps():
    # #179 D1: a NEW dedicated indicator (not an overload of CPI/INFLATION).
    assert canonical_unit(MacroIndicator.CPI_YOY) == "%"
    assert canonical_currency(MacroIndicator.CPI_YOY) is None
    assert canonical_indicator_code(MacroIndicator.CPI_YOY) == "cpi_yoy"
    assert canonical_indicator_name(MacroIndicator.CPI_YOY) == "CPI Year-over-Year"


def test_policy_rate_canonical_maps():
    # #179 D2 + N-a: canonical identity stays the SHORT stable strings; the verbose
    # SBV-proxy disclosure is a DISPLAY label carried only on the DBnomics result.
    assert canonical_unit(MacroIndicator.POLICY_RATE) == "% per annum"
    assert canonical_currency(MacroIndicator.POLICY_RATE) is None
    assert canonical_indicator_code(MacroIndicator.POLICY_RATE) == "policy_rate"
    assert canonical_indicator_name(MacroIndicator.POLICY_RATE) == "Policy Rate"


def test_new_monthly_indicators_not_level_or_bounded():
    # CPI_YOY may deflate (negative); a policy rate is a rate, not a >0 level, and
    # we deliberately do not hard-bound it. validate_indicator_values is a no-op.
    for ind in (MacroIndicator.CPI_YOY, MacroIndicator.POLICY_RATE):
        assert is_level_indicator(ind) is False
    validate_indicator_values(
        MacroIndicator.CPI_YOY, [(date(2023, 1, 1), -0.5)], "x"
    )  # deflation negative accepted
    validate_indicator_values(
        MacroIndicator.POLICY_RATE, [(date(2023, 1, 1), 4.5)], "x"
    )  # rate accepted unbounded


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


def test_unknown_indicator_raises_invalid_data_not_value_error():
    # Issue #48: an unknown indicator must raise InvalidData (failover-safe),
    # not leak a raw ValueError out of the macro client.
    from vnfin.exceptions import InvalidData
    from vnfin.macro import default_macro_client

    c = default_macro_client(http_get=lambda *a: '{"observations":[]}')
    with pytest.raises(InvalidData):
        c.get_indicator("USA", "not_an_indicator")


def test_unknown_indicator_bytes_raises_invalid_data():
    # Issue #48: bytes or other non-string indicators must also raise InvalidData.
    from vnfin.exceptions import InvalidData
    from vnfin.macro import default_macro_client

    c = default_macro_client(http_get=lambda *a: '{"observations":[]}')
    for bad in (b"gdp", 123, None):
        with pytest.raises(InvalidData):
            c.get_indicator("USA", bad)


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
