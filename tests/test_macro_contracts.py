"""Phase 4 macro batch — shared country (#32) + indicator (#48) contracts.

No-network: country/indicator validation happens before any HTTP call, so a
default ``http_get=None`` source never reaches the network for these cases.
"""
from __future__ import annotations

import pytest

from vnfin.exceptions import InvalidData
from vnfin.macro.dbnomics import DBnomicsSource
from vnfin.macro.imf import IMFDataMapperSource
from vnfin.macro.worldbank import WorldBankMacroSource

_SOURCES = [WorldBankMacroSource, IMFDataMapperSource, DBnomicsSource]
_BAD_INDICATORS = ["bad", "UNKNOWN", 123, True, None]
_BAD_COUNTRIES = ["US", "123", None, [], "ZZ"]


# --- #48: unknown/malformed indicators -> InvalidData, never raw ValueError ----
@pytest.mark.parametrize("cls", _SOURCES)
@pytest.mark.parametrize("bad", _BAD_INDICATORS)
def test_unit_for_unknown_indicator_raises_invaliddata(cls, bad):
    with pytest.raises(InvalidData):
        cls().unit_for(bad)


@pytest.mark.parametrize("cls", _SOURCES)
@pytest.mark.parametrize("bad", _BAD_INDICATORS)
def test_indicator_identity_unknown_indicator_raises_invaliddata(cls, bad):
    with pytest.raises(InvalidData):
        cls().indicator_identity("VNM", bad)


@pytest.mark.parametrize("cls", _SOURCES)
@pytest.mark.parametrize("bad", _BAD_INDICATORS)
def test_supports_unknown_indicator_is_quiet_false(cls, bad):
    # supports() must stay quiet (False), never raise.
    assert cls().supports(bad) is False


@pytest.mark.parametrize("bad", _BAD_INDICATORS)
def test_wb_get_canonical_indicator_unknown_raises_invaliddata(bad):
    with pytest.raises(InvalidData):
        WorldBankMacroSource().get_canonical_indicator("VNM", bad)


@pytest.mark.parametrize("bad", _BAD_INDICATORS)
def test_dbnomics_frequency_for_unknown_raises_invaliddata(bad):
    with pytest.raises(InvalidData):
        DBnomicsSource().frequency_for(bad)


# --- #32: malformed country -> InvalidData before any network call -------------
@pytest.mark.parametrize("bad", _BAD_COUNTRIES)
def test_imf_get_indicator_bad_country_raises_invaliddata(bad):
    with pytest.raises(InvalidData):
        IMFDataMapperSource().get_indicator(bad, "gdp")


@pytest.mark.parametrize("bad", _BAD_COUNTRIES)
def test_dbnomics_get_indicator_bad_country_raises_invaliddata(bad):
    with pytest.raises(InvalidData):
        DBnomicsSource().get_indicator(bad, "gdp")


@pytest.mark.parametrize("bad", _BAD_COUNTRIES)
def test_wb_get_canonical_indicator_bad_country_raises_invaliddata(bad):
    with pytest.raises(InvalidData):
        WorldBankMacroSource().get_canonical_indicator(bad, "gdp")


# --- DBnomics indicator_identity must not build an "A.None.*" series id ---------
@pytest.mark.parametrize("bad_country", ["US", "123", None, []])
def test_dbnomics_indicator_identity_malformed_country_raises(bad_country):
    with pytest.raises(InvalidData):
        DBnomicsSource().indicator_identity(bad_country, "gdp")


def test_dbnomics_indicator_identity_unmapped_country_raises_not_none():
    # valid ISO3 shape but no IFS mapping -> InvalidData (not "A.None.<concept>").
    with pytest.raises(InvalidData, match="no IFS country code"):
        DBnomicsSource().indicator_identity("QQQ", "gdp")
