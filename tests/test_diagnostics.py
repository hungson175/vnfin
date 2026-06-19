"""Issue #145 — source-coverage diagnostics (offline, additive public API)."""
from __future__ import annotations

from datetime import date

import pytest

import vnfin
from vnfin.diagnostics import (
    RequestDiagnostic,
    SourceCapability,
    explain_index_constituents,
    explain_world_gold_history,
    source_capabilities,
)
from vnfin.exceptions import EmptyData, InvalidData, VnfinError
from vnfin.gold.currency_api import COVERAGE_START, CurrencyApiGoldSource

_COV = COVERAGE_START


def _no_network(url, params=None, headers=None):
    raise AssertionError("diagnostics/preflight must not perform any network call")


# --- source_capabilities ----------------------------------------------------
def test_source_capabilities_offline_immutable_records():
    caps = source_capabilities()
    assert caps and all(isinstance(c, SourceCapability) for c in caps)
    domains = {c.domain for c in caps}
    assert {"gold", "indices"} <= domains
    # frozen dataclass: cannot mutate
    with pytest.raises(Exception):
        caps[0].source = "x"
    # gold has a default no-key source + an opt-in stooq; indices is single-source
    gold = [c for c in caps if c.domain == "gold"]
    assert any(c.source == "currency-api" and c.is_default for c in gold)
    assert any(c.source == "stooq" and c.is_opt_in and not c.is_default for c in gold)
    idx = [c for c in caps if c.domain == "indices"]
    assert idx and idx[0].is_single_source


# --- explain_world_gold_history ---------------------------------------------
def test_world_gold_pre_coverage_is_coverage_gap():
    d = explain_world_gold_history(date(2020, 1, 1), date(2020, 1, 7))
    assert isinstance(d, RequestDiagnostic) and d.status == "coverage_gap"
    sources = {c.source for c in d.sources}
    assert {"currency-api", "stooq"} <= sources  # both capability notes present
    assert d.suggested_actions  # offers a later window / opt-in


def test_world_gold_overlapping_window_is_partial_coverage():
    d = explain_world_gold_history(_COV.replace(day=1), _COV.replace(month=_COV.month + 1))
    assert d.status == "partial_coverage"


def test_world_gold_post_coverage_is_ok():
    d = explain_world_gold_history(date(2025, 1, 1), date(2025, 1, 7))
    assert d.status == "ok"


@pytest.mark.parametrize("bad", [("2024-13-01", "2024-01-07"), (date(2024, 6, 1), date(2024, 1, 1))])
def test_world_gold_invalid_or_inverted_dates_raise(bad):
    with pytest.raises(VnfinError):
        explain_world_gold_history(*bad)


# --- fail-fast in the live source -------------------------------------------
def test_currency_api_pre_coverage_fail_fast_zero_network():
    src = CurrencyApiGoldSource(http_get=_no_network)
    with pytest.raises(EmptyData, match="coverage"):
        src.get_history(date(2020, 1, 1), date(2020, 12, 31))


# --- explain_index_constituents ---------------------------------------------
def test_index_constituents_canonicalizes_and_reports_single_source():
    d = explain_index_constituents("  vn30  ")
    assert d.status == "single_source"
    assert d.request["index"] == "VN30"
    assert d.sources and d.sources[0].is_single_source
    assert any("weight" in n.lower() for n in d.notes)


@pytest.mark.parametrize("bad", [None, 123, "VN 30", "VN/30", "", "   "])
def test_index_constituents_malformed_selector_fails_closed(bad):
    with pytest.raises(InvalidData):
        explain_index_constituents(bad)


# --- public namespace --------------------------------------------------------
def test_diagnostics_exposed_on_package():
    assert vnfin.diagnostics.source_capabilities() == source_capabilities()
