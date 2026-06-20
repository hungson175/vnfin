"""Contract tests for the published documentation.

The README is the human entry point; docs/index.md fans out into progressive-disclosure
tutorial/how-to/reference pages; AI docs are a secondary lane. These tests also pin the
documented facade verbs, signatures, and invariants OFFLINE (no network) so docs/skill examples
cannot silently rot.

It is deliberately about the *documented* contract (a superset overlaps the public-API snapshot
in test_public_api_surface.py, but here the assertions mirror the exact examples the docs show).
"""
from __future__ import annotations

import inspect
import pathlib

import vnfin
import vnfin.crypto as crypto
import vnfin.fx as fx
import vnfin.macro as macro
from vnfin import Interval


REPO = pathlib.Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def test_readme_is_human_first_progressive_entrypoint():
    readme = _read("README.md")
    assert "Start here" in readme
    assert "docs/getting-started.md" in readme
    assert "docs/index.md" in readme
    assert "Common jobs" in readme

    # AI material must be discoverable, but not presented before the human path.
    assert readme.index("Start here") < readme.index("Using an AI agent?")
    assert "docs/ai-usage.md" in readme


def test_docs_index_has_progressive_disclosure_sections():
    index = _read("docs/index.md")
    for heading in (
        "## Recommended path",
        "## Tutorials",
        "## How-to guides",
        "## Reference",
        "## For AI agents",
        "## Maintainer-only context",
    ):
        assert heading in index

    for path in (
        "getting-started.md",
        "tutorials/stock-prices.md",
        "tutorials/fundamentals.md",
        "tutorials/funds-and-indices.md",
        "tutorials/macro-and-fx.md",
        "tutorials/gold-and-crypto.md",
        "how-to/pandas-dataframes.md",
        "how-to/errors.md",
        "how-to/cache-retry.md",
        "how-to/byok-fred.md",
        "how-to/live-tests.md",
        "reference/index.md",
    ):
        assert path in index
        assert (REPO / "docs" / path).exists(), path


def test_llms_indexes_human_docs_before_ai_agent_material():
    llms = _read("llms.txt")
    assert "## Human documentation path" in llms
    assert "## AI-agent material" in llms
    assert llms.index("## Human documentation path") < llms.index("## AI-agent material")
    assert "docs/tutorials/stock-prices.md" in llms
    assert "docs/how-to/errors.md" in llms


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


# Issue #148 — funds/indices tutorial must use real model fields, not non-existent attrs.
def test_funds_indices_tutorial_uses_real_model_fields():
    import dataclasses
    from vnfin.funds.models import FundHolding
    from vnfin.indices.models import IndexConstituents, IndexMember

    fh = {f.name for f in dataclasses.fields(FundHolding)}
    assert {"stock_code", "weight_pct"} <= fh and "symbol" not in fh and "weight" not in fh
    ic = {f.name for f in dataclasses.fields(IndexConstituents)}
    assert "members" in ic and "constituents" not in ic
    im = {f.name for f in dataclasses.fields(IndexMember)}
    assert {"symbol", "exchange"} <= im

    tut = _read("docs/tutorials/funds-and-indices.md")
    # correct fields present
    assert "h.stock_code" in tut and "h.weight_pct" in tut
    assert "members.members" in tut
    # non-existent / wrong attrs absent
    assert "h.symbol" not in tut and "h.weight)" not in tut
    assert "members.constituents" not in tut


# Issue #151 — public docs must enumerate the window_too_wide diagnostic status so the
# documented status set stays in sync with vnfin.diagnostics.
def test_diagnostics_docs_mention_window_too_wide_status():
    for path in (
        "docs/how-to/source-diagnostics.md",
        "docs/api.md",
        "docs/architecture/data-domains.md",
    ):
        assert "window_too_wide" in _read(path), f"{path} missing window_too_wide status"


# Issue #153 — gold tutorial must use GoldBar.price (GoldBar has no .close, unlike PriceBar).
def test_gold_tutorial_uses_goldbar_price_not_close():
    import dataclasses
    from vnfin.gold.models import GoldBar

    fields = {f.name for f in dataclasses.fields(GoldBar)}
    assert "price" in fields and "close" not in fields
    tut = _read("docs/tutorials/gold-and-crypto.md")
    world_block = tut.split("## Crypto", 1)[0]  # the World gold section only
    assert "hist.bars[-1].price" in world_block
    assert "hist.bars[-1].close" not in world_block  # no PriceBar-style .close on a GoldBar


# Issue #164 — prices.history(symbol, interval=D1, start=None, end=None): a date passed
# positionally lands in `interval` and breaks. Docs must always use start=/end= keywords.
def test_docs_prices_history_uses_keyword_dates():
    import pathlib, re
    bad = re.compile(r"prices\.history\([^)]*,\s*date\(")  # positional date as 2nd arg
    root = pathlib.Path(__file__).resolve().parent.parent
    offenders = []
    for md in list(root.glob("docs/**/*.md")) + [root / "README.md"]:
        for ln in md.read_text().splitlines():
            if "start=" not in ln and bad.search(ln):
                offenders.append(f"{md.relative_to(root)}: {ln.strip()}")
    assert not offenders, "positional-date prices.history in docs: " + "; ".join(offenders)


# Issue #159 — historical FX (annual USD/VND) public surface + docs.
def test_fx_history_entrypoints_and_docs():
    from vnfin.fx import FXHistory, FXPoint

    assert callable(vnfin.fx.history)
    assert callable(vnfin.diagnostics.explain_fx_coverage)
    # exact-match accessors exist (no-fill contract)
    assert hasattr(FXHistory, "rate_on") and hasattr(FXHistory, "rate_for_year")
    # docs present + period-average caveat stated; tutorial uses keyword start=/end=
    tut = _read("docs/tutorials/fx-history.md")
    assert "period-average" in tut
    assert "start=date(" in tut and "vnfin.fx.history(" in tut
    src = _read("docs/sources/fx-history-worldbank.md")
    assert "PA.NUS.FCRF" in src and "CC-BY 4.0" in src
    assert "runtime-fetch only" in src.lower()
    # fx.history(...) examples in docs must never pass a positional date (mirrors #164)
    import pathlib, re
    bad = re.compile(r"fx\.history\([^)]*,\s*date\(")
    root = pathlib.Path(__file__).resolve().parent.parent
    offenders = []
    for md in list(root.glob("docs/**/*.md")) + [root / "README.md"]:
        for ln in md.read_text().splitlines():
            if "start=" not in ln and bad.search(ln):
                offenders.append(f"{md.relative_to(root)}: {ln.strip()}")
    assert not offenders, "positional-date fx.history in docs: " + "; ".join(offenders)
