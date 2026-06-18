"""Contract test for the AI-facing docs + skill (docs/ai-usage.md, llms.txt, skills/vnfin/).

The AI documentation and the installable skill promise specific facade verbs, signatures, and
invariants. If the code drifts from those promises, an AI following the docs breaks. This test
pins the documented public surface OFFLINE (no network) so the docs/skill can't silently rot.

It is deliberately about the *documented* contract (a superset overlaps the public-API snapshot
in test_public_api_surface.py, but here the assertions mirror the exact examples the docs show).
"""
from __future__ import annotations

import inspect

import vnfin
import vnfin.crypto as crypto
import vnfin.fx as fx
import vnfin.macro as macro
from vnfin import Interval


def test_rule2_client_and_source_per_domain_with_gold_exception():
    for dom in (vnfin.prices, vnfin.fundamentals, vnfin.indices, crypto, fx, macro):
        assert callable(dom.client) and callable(dom.source), dom.__name__
    # gold is the documented exception: no client()
    assert not hasattr(vnfin.gold, "client")
    assert callable(vnfin.gold.vn) and callable(vnfin.gold.world) and callable(vnfin.gold.source)
    # funds is single-source: client is an alias of source
    assert vnfin.funds.client is vnfin.funds.source


def test_documented_history_entrypoints_exist():
    assert callable(vnfin.prices.history)
    assert callable(vnfin.default_client)
    assert callable(vnfin.indices.index_history)
    assert callable(vnfin.indices.index_constituents)
    assert callable(vnfin.fundamentals.get_financials)
    assert callable(fx.get_rate)
    assert callable(macro.get_indicator)
    for verb in ("list_funds", "nav_history", "holdings"):
        assert hasattr(vnfin.funds.source(), verb)
    assert hasattr(vnfin.gold.vn("btmc"), "get_quotes")
    assert hasattr(vnfin.gold.world(), "get_history")
    assert hasattr(crypto.client(), "get_klines") and hasattr(crypto.source(), "get_klines")


def test_documented_enums_and_units():
    from vnfin.fundamentals import AUTO, Period, StatementType

    assert {s.value for s in StatementType} >= {"income", "balance", "cashflow", "ratios"}
    assert {p.name for p in Period} >= {"ANNUAL", "QUARTER"}
    assert AUTO is None  # the is_bank sentinel documented as AUTO
    assert Interval.D1.value == "1d" and Interval.H1.value == "1h"
    assert {m.name for m in macro.MacroIndicator} == {
        "GDP",
        "GDP_GROWTH",
        "CPI",
        "INFLATION",
        "UNEMPLOYMENT",
    }
    assert macro.canonical_unit(macro.MacroIndicator.GDP) == "current US$"


def test_macro_client_method_takes_no_extra_kwargs_but_module_fn_does():
    # docs call client.get_indicator(country, indicator) with no kwargs, but module get_indicator
    # accepts http_get/timeout/sources — pin both shapes so the docs stay correct.
    assert list(inspect.signature(macro.MacroClient.get_indicator).parameters) == [
        "self",
        "country_iso3",
        "indicator",
    ]
    assert "http_get" in inspect.signature(macro.get_indicator).parameters


def test_fx_get_rate_signature_and_byok_surface():
    params = list(inspect.signature(fx.get_rate).parameters)
    assert params[:2] == ["base", "quote"]
    # documented BYOK: FRED source exists but is opt-in; no BEA/BLS
    assert hasattr(macro, "FREDMacroSource")
    assert not hasattr(macro, "BEAMacroSource") and not hasattr(macro, "BLSMacroSource")


def test_documented_exceptions_exist():
    from vnfin import exceptions as exc

    for name in (
        "SourceUnavailable",
        "EmptyData",
        "InvalidData",
        "UnsupportedInterval",
        "UnitMismatchError",
        "AllSourcesFailed",
        "VnfinError",
    ):
        assert hasattr(exc, name), name


def test_skill_files_present_and_have_frontmatter():
    import pathlib

    repo = pathlib.Path(__file__).resolve().parents[1]
    skill = repo / "skills" / "vnfin" / "SKILL.md"
    assert skill.exists(), "skills/vnfin/SKILL.md missing"
    head = skill.read_text()[:600]
    assert head.startswith("---") and "name: vnfin" in head and "description:" in head
    assert (repo / "skills" / "vnfin" / "reference" / "domains.md").exists()
    assert (repo / "llms.txt").exists()
    assert (repo / "docs" / "ai-usage.md").exists()
