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
    for verb in ("list_funds", "nav_history", "holdings", "asset_allocation"):
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
        "CPI_YOY",
        "POLICY_RATE",
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
    from vnfin.funds.models import AssetAllocation, AssetClassWeight, FundHolding
    from vnfin.indices.models import IndexConstituents, IndexMember

    fh = {f.name for f in dataclasses.fields(FundHolding)}
    assert {"stock_code", "weight_pct", "instrument_type", "as_of_utc"} <= fh
    assert "symbol" not in fh and "weight" not in fh
    # #173 asset-allocation model fields the tutorial/skill examples rely on.
    acw = {f.name for f in dataclasses.fields(AssetClassWeight)}
    assert {"asset_class", "weight_pct"} <= acw
    aa = {f.name for f in dataclasses.fields(AssetAllocation)}
    assert {"classes", "as_of_utc"} <= aa
    ic = {f.name for f in dataclasses.fields(IndexConstituents)}
    assert "members" in ic and "constituents" not in ic
    im = {f.name for f in dataclasses.fields(IndexMember)}
    assert {"symbol", "exchange"} <= im

    tut = _read("docs/tutorials/funds-and-indices.md")
    # correct fields present
    assert "h.stock_code" in tut and "h.weight_pct" in tut
    assert "h.instrument_type" in tut and "asset_allocation" in tut
    assert "c.asset_class" in tut and "c.weight_pct" in tut
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


def test_fx_docs_do_not_claim_fx_has_no_history():
    """Guard (review-202606201054 B4): now that vnfin.fx.history exists, agent-/user-facing
    docs must not regress to claiming FX is spot-only / has no history.

    Two-sided: (a) FX-specific no-history phrases (which never describe gold's separate
    "spot only" sources) are forbidden anywhere in the FX doc files; (b) each FX doc must
    positively affirm the history entrypoint, so deleting the history docs also fails.
    """
    import pathlib, re

    root = pathlib.Path(__file__).resolve().parent.parent

    # (a) Forbidden FX-no-history phrases are banned REPO-WIDE (every doc/agent file, present or
    # future) — not a curated list, because the stale text kept reappearing in files the list
    # had not enumerated (SKILL.md, then macro-and-fx.md). Each phrase is FX-specific and does
    # NOT match gold's legitimate bare "spot only" rows.
    scan_roots = [
        *root.glob("docs/**/*.md"),
        *root.glob("skills/**/*.md"),
        *root.glob("*.md"),  # all root markdown (README.md, CHANGELOG.md, AGENTS.md, ...)
        *root.glob("vnfin/fx/*.py"),
        root / "vnfin/diagnostics.py",
        root / "llms.txt",
    ]
    forbidden = re.compile(
        r"fx has \*?\*?no\*?\*? ?history|no history in v0\.2|no historical fx|"
        r"spot/current only|spot/current in v0\.\d|fx is spot|"
        r"history deferred to a future issue",
        re.I,
    )
    forbidden_offenders = []
    for path in scan_roots:
        if not path.exists():
            continue
        for ln in path.read_text().splitlines():
            if forbidden.search(ln):
                forbidden_offenders.append(f"{path.relative_to(root)}: {ln.strip()}")

    # (b) FX-primary docs must positively affirm the history entrypoint, so deleting the history
    # docs also fails. This stays a curated list (these files MUST mention fx.history).
    fx_doc_files = [
        "docs/ai-usage.md",
        "skills/vnfin/reference/domains.md",
        "skills/vnfin/SKILL.md",
        "docs/architecture/data-domains.md",
        "docs/tutorials/macro-and-fx.md",
        "vnfin/fx/__init__.py",
    ]
    affirm_missing = []
    for rel in fx_doc_files:
        low = (root / rel).read_text().lower()
        if "fx.history" not in low and "fxhistory" not in low:
            affirm_missing.append(rel)
    assert not forbidden_offenders, (
        "stale 'FX has no history' doc claims: " + " | ".join(forbidden_offenders)
    )
    assert not affirm_missing, (
        "FX docs must document the history entrypoint (fx.history/FXHistory): "
        + ", ".join(affirm_missing)
    )


def test_diagnostics_docs_enumerate_fx_coverage():
    """Guard (review-202606201115 B4.5): the docs that enumerate the offline
    ``vnfin.diagnostics`` API must not describe it as only gold + indices once
    ``explain_fx_coverage`` ships. Each diagnostics-enumerating doc must mention the FX
    coverage function so 'source_capabilities = world-gold + index constituents'-only text
    cannot silently go stale again.
    """
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent
    # Docs that enumerate the diagnostics function set / source_capabilities legs.
    diag_doc_files = [
        "docs/api.md",
        "docs/architecture/data-domains.md",
        "docs/how-to/source-diagnostics.md",
    ]
    missing = []
    for rel in diag_doc_files:
        text = (root / rel).read_text().lower()
        # If a file talks about source_capabilities at all, it must also name the FX leg.
        if "source_capabilities" in text and (
            "explain_fx_coverage" not in text and "worldbank_fx" not in text
        ):
            missing.append(rel)
    assert not missing, (
        "diagnostics docs enumerate source_capabilities but omit FX coverage "
        "(explain_fx_coverage / worldbank_fx): " + ", ".join(missing)
    )


# Issue #157 — canonical-metrics layer public surface + docs (Stage D). The four
# documentation surfaces (tutorial, api.md, skill domains.md, CHANGELOG) and the docs-
# contract guard must stay pinned to the REAL surface so the documented examples/enum
# values/result fields cannot silently rot.
def test_metrics_layer_public_surface_offline():
    """The documented metrics entry points + result types are importable OFFLINE and the
    exact enum ``.value`` strings / dataclass field names the docs cite really exist."""
    import dataclasses

    from vnfin.fundamentals import (
        AppliesTo,
        MetricAvailability,
        MetricCategory,
        MetricCoverage,
        MetricDefinition,
        MetricId,
        MetricKind,
        MetricReport,
        MetricValue,
        StatementCoverageStatus,
        explain_metric,
        explain_metric_coverage,
        metric_catalog,
        metrics,
    )

    # documented callables
    for fn in (metrics, explain_metric_coverage, metric_catalog, explain_metric):
        assert callable(fn), fn

    # documented enum .value strings the docs/skill examples cite verbatim
    assert MetricKind.RAW_MAPPED.value == "raw_mapped"
    assert MetricKind.DERIVED.value == "derived"
    assert {a.value for a in AppliesTo} == {"corporate", "bank", "both"}
    assert {a.value for a in MetricAvailability} >= {
        "available",
        "missing",
        "blocked",
        "not_applicable",
    }
    assert {s.value for s in StatementCoverageStatus} == {
        "ok",
        "missing",
        "source_error",
        "not_served",
    }
    assert {c.value for c in MetricCategory} == {
        "profitability",
        "liquidity",
        "leverage",
        "cashflow",
        "size",
    }
    # a documented metric id + a documented derived id really exist
    assert MetricId.NET_REVENUE.value == "net_revenue"
    assert MetricId.GROSS_MARGIN.value == "gross_margin"

    # the v1 catalog the docs describe: 26 metrics, offline, immutable tuple
    cat = metric_catalog()
    assert isinstance(cat, tuple) and len(cat) == 26
    # documented filter behavior (bank => BANK + BOTH; net_interest_income is bank-only)
    bank_ids = {d.id.value for d in metric_catalog("bank")}
    assert "net_interest_income" in bank_ids and "net_revenue" not in bank_ids

    # explain_metric returns a MetricDefinition with the documented derived formula
    gm = explain_metric("gross_margin")
    assert isinstance(gm, MetricDefinition)
    assert gm.formula == "gross_profit / net_revenue"

    # documented result-type fields the docs/skill examples read
    mv_fields = {f.name for f in dataclasses.fields(MetricValue)}
    assert {"id", "value", "value_unit", "kind", "availability", "reason", "inputs"} <= mv_fields
    mr_fields = {f.name for f in dataclasses.fields(MetricReport)}
    assert {"symbol", "period", "fiscal_date", "is_bank", "metrics", "statement_sources"} <= mr_fields
    assert hasattr(MetricReport, "get") and hasattr(MetricReport, "to_dataframe")
    cov_fields = {f.name for f in dataclasses.fields(MetricCoverage)}
    assert {"symbol", "period", "periods"} <= cov_fields


def test_metrics_layer_documented_everywhere():
    """Public-API change ⇒ docs + skill + CHANGELOG in the SAME change. Each of the four
    documentation surfaces must document the new metrics entry points (so dropping any one
    fails the suite)."""
    # 1) tutorial — the canonical-metrics section with runnable examples
    tut = _read("docs/tutorials/fundamentals.md")
    assert "Canonical metrics" in tut
    for needle in (
        "vnfin.fundamentals.metrics(",
        "explain_metric_coverage(",
        "metric_catalog(",
        "explain_metric(",
        "not_applicable",
        "blocked",
    ):
        assert needle in tut, f"fundamentals tutorial missing {needle!r}"

    # 2) api.md — a reference section for the new functions + result types
    api = _read("docs/api.md")
    assert "vnfin.fundamentals.metrics" in api
    for needle in (
        "explain_metric_coverage",
        "metric_catalog",
        "explain_metric(",
        "MetricReport",
        "MetricValue",
        "MetricCoverage",
    ):
        assert needle in api, f"docs/api.md missing {needle!r}"

    # 3) skill domains.md — the fundamentals section expanded with the metrics entries
    dom = _read("skills/vnfin/reference/domains.md")
    for needle in (
        "vnfin.fundamentals.metrics(",
        "explain_metric_coverage(",
        "metric_catalog(",
        "MetricReport",
    ):
        assert needle in dom, f"skill domains.md missing {needle!r}"

    # 4) CHANGELOG — an Unreleased entry linking the issue
    changelog = _read("CHANGELOG.md")
    assert "vnfin.fundamentals.metrics" in changelog
    assert "https://github.com/hungson175/vnfin/issues/157" in changelog
    # the entry must state the v1 scope the docs describe
    assert "26" in changelog and "deferred to v2" in changelog.lower()
