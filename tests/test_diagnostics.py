"""Issue #145 — source-coverage diagnostics (offline, additive public API)."""
from __future__ import annotations

from datetime import date, timedelta

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


# Issue #175 Tier-3 — the offline diagnostic must NOT advise treating membership as
# point-in-time (the exact misuse the live ``current_snapshot_only`` warning guards
# against); it must say the basket is the CURRENT snapshot and flag survivorship bias.
def test_index_constituents_diagnostic_warns_current_snapshot_not_point_in_time():
    d = explain_index_constituents("VN30")
    actions = [a.lower() for a in d.suggested_actions]
    assert not any("as point-in-time" in a for a in actions)
    assert any("current snapshot" in a for a in actions)
    assert any("not point-in-time" in a for a in actions)
    assert any("survivorship" in a for a in actions)
    # do-not-expect-weights guidance + status preserved
    assert d.status == "single_source"
    assert any("weight" in a for a in actions)


def test_index_constituents_capability_warns_current_snapshot_not_point_in_time():
    cap = next(
        c
        for c in source_capabilities()
        if c.domain == "indices" and c.endpoint == "constituents"
    )
    sa = cap.suggested_action.lower()
    assert "as point-in-time" not in sa
    assert "current" in sa and "not point-in-time" in sa
    assert "survivorship" in sa
    # do-not-expect-weights guidance preserved
    assert "weight" in sa


# --- public namespace --------------------------------------------------------
def test_diagnostics_exposed_on_package():
    assert vnfin.diagnostics.source_capabilities() == source_capabilities()


# Issue #151 — explain_world_gold_history surfaces the max-day/range-width blocker too.
from vnfin.gold.currency_api import _MAX_DAYS as _GOLD_MAX_DAYS


def test_world_gold_pre_coverage_and_too_wide_reports_both():
    d = explain_world_gold_history(date(2018, 1, 1), date(2021, 6, 1))  # pre-cov AND > _MAX_DAYS
    assert d.status == "coverage_gap"  # coverage fails first
    notes = " ".join(d.notes).lower()
    assert "coverage start" in notes and "exceeding" in notes  # BOTH blocker notes present
    assert any("chunk" in s.lower() for s in d.suggested_actions)        # width action
    assert any("on/after" in s.lower() for s in d.suggested_actions)     # coverage action


def test_world_gold_covered_but_too_wide_is_window_too_wide():
    d = explain_world_gold_history(date(2024, 4, 1), date(2027, 6, 1))  # covered, span > _MAX_DAYS
    assert d.status == "window_too_wide"
    assert any("chunk" in s.lower() for s in d.suggested_actions)


def test_world_gold_acceptable_width_covered_stays_ok():
    d = explain_world_gold_history(date(2025, 1, 1), date(2025, 3, 31))
    assert d.status == "ok"
    assert not any("exceeding" in n.lower() for n in d.notes)


def test_world_gold_max_day_boundary_exact():
    # span == _MAX_DAYS days is allowed (mirrors live `.days > _MAX_DAYS`); +1 day is too wide.
    base = date(2024, 4, 1)
    ok = explain_world_gold_history(base, base + timedelta(days=_GOLD_MAX_DAYS))
    assert ok.status == "ok"
    wide = explain_world_gold_history(base, base + timedelta(days=_GOLD_MAX_DAYS + 1))
    assert wide.status == "window_too_wide"


# --- Issue #152: explain_fixed_income_coverage() (offline) ------------------
from vnfin.diagnostics import explain_fixed_income_coverage


def test_fixed_income_coverage_is_offline_zero_network():
    # Mirror the _no_network discipline of the sibling diagnostics: pure metadata,
    # never a provider call.
    import vnfin.diagnostics as diag

    called = {"n": 0}
    # Any accidental http_get-like call would bump this; the function takes no
    # http_get, so simply assert it runs and returns without touching the net.
    d = explain_fixed_income_coverage()
    assert isinstance(d, RequestDiagnostic)
    assert called["n"] == 0
    # exposed on the package namespace like the siblings
    assert diag.explain_fixed_income_coverage() == d


def test_fixed_income_coverage_states_yield_curve_unavailable():
    d = explain_fixed_income_coverage()
    assert d.status == "yield_curve_unavailable"
    blob = " ".join(d.notes).lower()
    # (a) the govt-bond yield CURVE is unavailable (no clean source)
    assert "yield curve" in blob
    assert "unavailable" in blob or "no clean" in blob


def test_fixed_income_coverage_enumerates_the_four_rate_kinds():
    d = explain_fixed_income_coverage()
    blob = " ".join(d.notes).lower()
    # (b) enumerate what IS available — policy + lending + deposit + real interest
    for kind in ("policy", "lending", "deposit", "real"):
        assert kind in blob, kind
    # policy is the DBnomics monthly proxy; the WB rates are ANNUAL
    assert "annual" in blob
    assert "monthly" in blob
    # the policy proxy + its staleness is disclosed
    assert "proxy" in blob
    # the SourceCapability records cover the four kinds
    sources_blob = " ".join(
        (c.source + " " + " ".join(c.instruments) + " " + " ".join(c.limitations)).lower()
        for c in d.sources
    )
    for kind in ("policy", "lending", "deposit", "real"):
        assert kind in sources_blob, kind


def test_fixed_income_coverage_discloses_deposit_is_annual_aggregate():
    d = explain_fixed_income_coverage()
    blob = " ".join(d.notes + d.suggested_actions).lower()
    sources_blob = " ".join(" ".join(c.limitations).lower() for c in d.sources)
    full = blob + " " + sources_blob
    # (c) deposit_rate is an annual AGGREGATE with no clean per-tenor retail source
    assert "aggregate" in full
    assert "per-tenor" in full or "per tenor" in full
    assert "retail" in full


def test_fixed_income_coverage_distinguishes_rate_concepts():
    d = explain_fixed_income_coverage()
    blob = " ".join(d.notes).lower()
    # (d) distinguish policy vs interbank vs deposit vs govt-bond so users don't conflate
    assert "interbank" in blob
    assert "government bond" in blob or "govt-bond" in blob or "govt bond" in blob
    assert "policy" in blob
    assert "deposit" in blob


def test_fixed_income_coverage_in_source_capabilities_registry():
    caps = source_capabilities()
    fi = [c for c in caps if c.domain == "rates"]
    assert fi, "fixed-income rate capabilities missing from source_capabilities()"
    sources = {c.source for c in fi}
    # World Bank annual rates + the DBnomics policy proxy are both registered
    assert any("worldbank" in s for s in sources)
    assert any("dbnomics" in s for s in sources)
