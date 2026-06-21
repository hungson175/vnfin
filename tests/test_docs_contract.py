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
        # #152: World Bank annual fixed-income rate indicators.
        "LENDING_RATE",
        "DEPOSIT_RATE",
        "REAL_INTEREST_RATE",
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


# Issue #166 — index VOLUME semantics must be documented (shares passthrough, directional only)
# and the doc's scale claim must stay in lockstep with the code: the index adapters keep
# VOLUME_SCALE = 1.0 (no constituent aggregation), only PRICE_SCALE is overridden to points.
def test_index_volume_semantics_documented_and_in_lockstep_with_code():
    # (a) code: the scale literals the doc cites really exist.
    udf = _read("vnfin/sources/udf.py")
    idx = _read("vnfin/indices/sources.py")
    assert "VOLUME_SCALE = 1.0" in udf, "base UDF source no longer keeps VOLUME_SCALE = 1.0"
    assert "PRICE_SCALE = 1.0" in idx, "index adapters no longer override PRICE_SCALE = 1.0"

    # (b) source doc: the dedicated VOLUME-semantics section exists and states the contract.
    src = _read("docs/sources/indices-constituents.md")
    assert "Index VOLUME semantics" in src, "indices doc missing the VOLUME-semantics section"
    for needle in ("VOLUME_SCALE = 1.0", "no constituent", "directional"):
        assert needle in src, f"indices doc VOLUME section missing {needle!r}"

    # (c) units.md indices row + SKILL.md index-value row must carry the volume caveat too,
    # so a caller reading either quick reference learns volume is a passthrough proxy.
    units = _read("docs/units.md")
    assert "shares" in units and "volume" in units.lower()
    skill = _read("skills/vnfin/SKILL.md")
    assert "directional proxy" in skill, "SKILL.md index row missing the volume caveat"


# Issue #171 — the end-to-end gold coverage & backup map must exist in the hub doc and stay tied
# to the real accessors; the daily + annual sibling docs must cross-link to it for discoverability.
def test_gold_coverage_map_documented_and_cross_linked():
    import vnfin.gold as gold

    # (a) code: the accessors the map names really exist with the documented behavior.
    assert callable(gold.world_reference_history_vnd)
    assert callable(gold.vn) and callable(gold.world)
    try:
        gold.domestic_history()
        raise AssertionError("gold.domestic_history() must raise NotImplementedError (reserved)")
    except NotImplementedError:
        pass

    # (b) hub doc: the coverage-map section names all three live paths + the never-silent backups.
    hub = _read("docs/sources/gold-world-reference.md")
    assert "End-to-end gold coverage & backup paths" in hub, "gold hub missing the coverage map"
    for needle in (
        "world_reference_history_vnd",
        "gold.world()",
        'gold.vn("btmc"',
        "domestic_history()",
        "world_reference_gold_source_fallback",
        "opt-in",
    ):
        assert needle in hub, f"gold coverage map missing {needle!r}"

    # (c) the daily + annual sibling docs cross-link back to the hub map.
    assert "gold-world-reference.md#end-to-end-gold-coverage" in _read("docs/sources/gold-adapters.md")
    assert "gold-world-reference.md#end-to-end-gold-coverage" in _read("docs/sources/cmo-gold-annual.md")


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


# Issue #180 — the SKILL.md "Warning tokens" table is the caller's contract for matching on
# result.warnings prefixes. It must stay in lockstep with code in BOTH directions, because a
# forward-only check (only confirming documented tokens are emitted) is exactly what let three
# un-tokenized PROSE warnings ship undocumented. The guard enumerates the COMPLETE caller-facing
# set; gate is the sweep, not a magic count (folds #167's pending tokens in when that lands).
_WARNING_TOKENS_180 = (
    "partial_start_coverage",
    "partial_end_coverage",
    "trailing_zero_volume_tail",
    "quarantined_invalid_bars",
    "resampled_from_d1",
    "resample_partial_period",
    "deduped_duplicate_daily_index_bars",
    "recovered_midnight_open_placeholder",
    "stitched_multi_source",
    "stitched_segment",
    "weights_not_available",
    # #175 Tier-1 — index_constituents is the CURRENT basket, not point-in-time.
    "current_snapshot_only",
    "fallback_instrument_served",
    "world_reference_excludes_domestic_premium",
    "world_reference_annual_basis",
    "world_reference_partial_year_coverage",
    "world_reference_trailing_year_incomplete",
    "world_reference_gold_source_fallback",
    "world_reference_gold_leg_",
    "world_reference_fx_leg_",
    "partial_coverage",
    "mixed_source",
    "traded_value_estimated_from_close_x_volume",
    "zero_liquidity",
    "series_end_gap",
    "imf_weo",
    "failover",
    "nav_end_gap",
    "deduped_duplicate_nav_rows",
    "skipped_mismatched_report_rows",
    "skipped_period_rows",
    # #167 — equity-universe honest-gap + cross-board dedup tokens.
    "partial_universe_coverage",
    "listing_date_not_available",
    "sector_not_available",
    "cross_board_duplicate_symbol",
    # #189 — a board skipped during the all-boards merge (partial availability).
    "board_unavailable",
    # #190 — list-level NAV-staleness warning on FundList.
    "fund_nav_stale",
)


def _skill_warning_tokens_section() -> str:
    """The text of the SKILL.md '## Warning tokens' section (up to the next H2)."""
    skill = _read("skills/vnfin/SKILL.md")
    start = skill.index("## Warning tokens")
    end = skill.index("\n## ", start + 1)
    return skill[start:end]


def _vnfin_source_blob() -> str:
    return "\n".join(
        p.read_text(encoding="utf-8") for p in sorted((REPO / "vnfin").rglob("*.py"))
    )


def test_skill_warning_tokens_section_in_lockstep_with_code():
    """Bidirectional doc<->code guard for result.warnings tokens (#180).

    (a) code->doc: every token the library can emit is documented in the SKILL table.
    (b) doc->code: every documented token is still emitted as a STRING LITERAL in vnfin/,
        so deleting either the row or the emission goes red (no silent rot in either lane).
    """
    section = _skill_warning_tokens_section()
    src = _vnfin_source_blob()

    for token in _WARNING_TOKENS_180:
        # (a) documented
        assert token in section, f"warning token {token!r} emitted by code but missing from the SKILL table"
        # (b) still emitted as a literal (quote-anchored so a mere comment mention won't satisfy it)
        assert (
            f'"{token}' in src or f"'{token}" in src
        ), f"warning token {token!r} documented but no longer emitted as a literal in vnfin/"


# Issue #188 — FORWARD-DISCOVERY hardening of the #180 guard.
#
# ``test_skill_warning_tokens_section_in_lockstep_with_code`` iterates only over the
# hardcoded ``_WARNING_TOKENS_180`` tuple, so a token a dev EMITS in ``vnfin/`` but never
# adds to the tuple is INVISIBLE to it (that exact failure shipped 4 undocumented warnings
# historically). #188 makes the guard DISCOVER the emitted token set from the code AST and
# assert it is a subset of the documented tuple — so a new emission with no doc row goes red
# automatically. Net invariant: code-emits ⊆ tuple ⊆ {SKILL table ∧ code-literal}.
from _warning_token_scan import (  # noqa: E402  (sibling test helper; tests/ on sys.path)
    _NON_TOKEN_WARNING_LITERALS,
    _covered,
    _discover_emitted_warning_tokens,
    _extract_warning_tokens_from_source,
)


# --- per-shape extractor unit tests (synthetic snippets; fail-first then implement) ----- #

def test_extract_shape_a_literal_in_warnings_kwarg_and_assign():
    """Shape A — a str literal in a ``warnings=`` kwarg or a ``warnings = (...)`` assign."""
    snippet = '''
def f(hist):
    return replace(hist, warnings=("deduped_duplicate_daily_index_bars",))

def g():
    warnings = ("weights_not_available: SSI group endpoint exposes membership only",)
    return warnings

def h(extra):
    warnings = ("stitched_multi_source",) + tuple(extra)
    return Thing(warnings=warnings)
'''
    assert _extract_warning_tokens_from_source(snippet) == {
        "deduped_duplicate_daily_index_bars",
        "weights_not_available",
        "stitched_multi_source",
    }


def test_extract_shape_b_append_and_extend_to_warnings_list():
    """Shape B — ``.append(literal | f"…")`` / ``.extend(...)`` to a ``warnings`` list.

    A pure ``.extend(other.warnings)`` pass-through yields no literal.
    """
    snippet = '''
def f(other):
    warnings = []
    warnings.append("zero_liquidity: average daily value is 0 over the window")
    warnings.extend(other.warnings)
    return warnings
'''
    assert _extract_warning_tokens_from_source(snippet) == {"zero_liquidity"}


def test_extract_shape_c_module_constant_resolved_to_literal():
    """Shape C — a module/class CONSTANT resolved through the name→literal map."""
    snippet = '''
RESAMPLED_FROM_D1 = "resampled_from_d1"
_TRAILING_ZERO_VOLUME_TAIL = "trailing_zero_volume_tail"

def f(daily):
    return replace(daily, warnings=(RESAMPLED_FROM_D1,))

def g(hist):
    warnings = (_TRAILING_ZERO_VOLUME_TAIL,)
    return warnings
'''
    assert _extract_warning_tokens_from_source(snippet) == {
        "resampled_from_d1",
        "trailing_zero_volume_tail",
    }


def test_extract_shape_d_warnings_helper_return():
    """Shape D — a ``_*warnings()`` helper whose RETURN carries the literal."""
    snippet = '''
_FALLBACK_WARNING = "fallback_instrument_served"

def _board_warnings(board):
    return (
        f"partial_universe_coverage: {board} — index-basket-derived",
        f"listing_date_not_available: {board} — provider firstTradingDate is '0'",
        f"sector_not_available: {board} — sector/industry absent",
    )

def _substitution_warnings(hist):
    if served_spx:
        return (_FALLBACK_WARNING,)
    return ()
'''
    assert _extract_warning_tokens_from_source(snippet) == {
        "partial_universe_coverage",
        "listing_date_not_available",
        "sector_not_available",
        "fallback_instrument_served",
    }


def test_extract_shape_e_leading_text_fstring():
    """Shape E (sub-shape 1) — f-string LEADING with static text: ``f"world_reference_gold_leg_{w}"``.

    The ``*_leg_`` family token KEEPS its trailing underscore (it is a declared family
    prefix). A ``"failover: {note}"`` form normalizes on the leading ``:`` segment.
    """
    snippet = '''
def f(gold_hist, fx_hist, note, year, seg):
    warnings = []
    for w in gold_hist.warnings:
        warnings.append(f"world_reference_gold_leg_{w}")
    for w in fx_hist.warnings:
        warnings.append(f"world_reference_fx_leg_{w}")
    warnings.append(f"failover: {note}")
    warnings.append(f"stitched_segment: {year} {seg.source} ({len(seg.bars)} bars)")
    return warnings
'''
    assert _extract_warning_tokens_from_source(snippet) == {
        "world_reference_gold_leg_",
        "world_reference_fx_leg_",
        "failover",
        "stitched_segment",
    }


def test_extract_shape_e_leading_resolved_constant_fstring():
    """Shape E (sub-shape 2, the SUBTLE one) — f-string LEADING with a resolved CONSTANT
    then ``:`` then dynamic text: ``f"{QUARANTINED_INVALID_BARS}: dropped {n} — {detail}"``.

    The extractor must resolve the leading ``FormattedValue`` Name → its str literal while
    building the static prefix, then ``split(":", 1)[0].strip()``. This is the highest-value
    case — it proves the extractor does not silently miss the quarantine/recovery family.
    """
    snippet = '''
QUARANTINED_INVALID_BARS = "quarantined_invalid_bars"
RECOVERED_MIDNIGHT_OPEN_PLACEHOLDER = "recovered_midnight_open_placeholder"
_PARTIAL_COVERAGE_TOKEN = "world_reference_partial_year_coverage"
_TRAILING_YEAR_TOKEN = "world_reference_trailing_year_incomplete"

def _quarantine_warnings(self):
    return (
        f"{QUARANTINED_INVALID_BARS}: dropped {len(q)} bar(s) — {detail}",
    )

def _recovery_warnings(self):
    return (
        f"{RECOVERED_MIDNIGHT_OPEN_PLACEHOLDER}: recovered {len(r)} bar(s) — {detail}",
    )

def synth(warnings):
    warnings.append(
        f"{_PARTIAL_COVERAGE_TOKEN}: years not synthesized for lack of a paired obs"
    )
    warnings.append(
        f"{_TRAILING_YEAR_TOKEN}: the emitted year {y} is the current calendar year"
    )
    return warnings
'''
    assert _extract_warning_tokens_from_source(snippet) == {
        "quarantined_invalid_bars",
        "recovered_midnight_open_placeholder",
        "world_reference_partial_year_coverage",
        "world_reference_trailing_year_incomplete",
    }


def test_extract_excludes_non_warnings_positions():
    """A ``SourceAttempt(..., reason)`` literal and a ``_warnings_reason`` def (name ends in
    ``reason``, not ``warnings``) are NOT ``.warnings`` positions → extractor returns ∅."""
    snippet = '''
def _warnings_reason(warnings):
    if not isinstance(warnings, tuple):
        return f"malformed warnings {warnings!r}: expected a tuple of strings"
    return None

def record(attempts, src):
    attempts.append(SourceAttempt(src.name, False, "source raised: boom"))
    return attempts
'''
    assert _extract_warning_tokens_from_source(snippet) == set()


# --- #192 def-use trace: locals that FLOW INTO a warnings sink (close the #188 blind spot) - #

def test_extract_traces_dup_notes_style_accumulator():
    """#192 — a local accumulator named something OTHER than ``*warnings`` (``dup_notes`` /
    ``warns`` / ``note``) whose contents demonstrably FLOW INTO a ``warnings=`` sink (or a
    ``_*warnings`` helper return) must be forward-discovered. These are the three real
    blind-spot shapes that ship FIVE documented tokens today:

    - ``dup_notes`` → ``warnings=tuple(warnings) + tuple(dup_notes)`` (kwarg BinOp, tuple-wrapped)
    - ``warns``     → ``warns.append(...)`` then ``return tuple(warns)`` inside a ``_*warnings`` helper
    - ``note``      → ``warnings=tuple(r.warnings) + (note,)`` (kwarg BinOp, tuple-element)
    """
    snippet = '''
def _merged_universe(self):
    warnings = []
    dup_notes = []
    for sec in secs:
        dup_notes.append(f"cross_board_duplicate_symbol: {sec.symbol} kept from {board}")
    return EquityUniverse(warnings=tuple(warnings) + tuple(dup_notes))

def _coverage_warnings(hist, start, end):
    warns = []
    warns.append(f"partial_start_coverage: first bar {first} after start {sd}")
    warns.append(f"partial_end_coverage: last bar {last} before end {ed}")
    return tuple(warns)

def _with_skip_warning(reports, skipped):
    note = f"skipped_period_rows: {skipped} period row(s)"
    return [replace(r, warnings=tuple(r.warnings) + (note,)) for r in reports]
'''
    assert _extract_warning_tokens_from_source(snippet) == {
        "cross_board_duplicate_symbol",
        "partial_start_coverage",
        "partial_end_coverage",
        "skipped_period_rows",
    }


def test_extract_does_not_trace_local_that_never_reaches_a_warnings_sink():
    """#192 NEGATIVE — proves we trace FLOW, not the variable NAME. A local ``note`` that is
    logged/returned plainly but NEVER flows into a ``warnings=`` arg (nor a ``_*warnings``
    helper return) must NOT be surfaced. Broadening the name regex would red this incorrectly.
    """
    snippet = '''
def do_thing(reports):
    note = "debug: not a warning"
    logger.info(note)
    return note

def other(reports):
    warns = ["skipped_period_rows: should NOT leak — never reaches a warnings sink"]
    return [r for r in reports if warns]
'''
    assert _extract_warning_tokens_from_source(snippet) == set()


# --- coverage-rule REVIEWER REFINEMENT (exact vs declared-family-prefix) ---------------- #

def test_covered_exact_token_does_not_prefix_absorb_but_family_prefix_does():
    """Pins the reviewer's refinement: a plain documented token requires an EXACT match
    (so ``partial_coverage`` does NOT cover ``partial_coverage_xyz`` — that must be flagged),
    while a ``_``-suffixed FAMILY prefix (``world_reference_gold_leg_``) DOES prefix-cover."""
    # plain token -> exact match only
    assert _covered("partial_coverage", _WARNING_TOKENS_180) is True
    assert _covered("partial_coverage_xyz", _WARNING_TOKENS_180) is False
    # declared family prefix (ends in "_") -> prefix-covers a concrete instance
    assert _covered("world_reference_gold_leg_2024", _WARNING_TOKENS_180) is True
    assert _covered("world_reference_fx_leg_partial_coverage", _WARNING_TOKENS_180) is True
    # the family prefix itself is covered (e == t)
    assert _covered("world_reference_gold_leg_", _WARNING_TOKENS_180) is True


# --- whole-repo forward-discovery guard (must be GREEN on the real tree) ---------------- #

def test_emitted_warning_tokens_are_all_documented():
    """#188 forward gap: DISCOVER the token set straight from ``vnfin/`` AST and assert every
    discovered token is ``_covered`` by ``_WARNING_TOKENS_180``. A new emission with no doc
    row goes red automatically. GREEN on the current tree (the tuple is complete after #187).
    """
    discovered = _discover_emitted_warning_tokens(REPO)
    undocumented = {
        tok: locs
        for tok, locs in discovered.items()
        if tok not in _NON_TOKEN_WARNING_LITERALS and not _covered(tok, _WARNING_TOKENS_180)
    }
    assert not undocumented, "emitted warning token(s) not in _WARNING_TOKENS_180: " + ", ".join(
        f"{tok} @ {locs}" for tok, locs in sorted(undocumented.items())
    )


def test_forward_discovery_finds_the_known_emission_corpus():
    """Sanity: the discovered set actually contains the tricky/representative tokens (so the
    guard is not green merely because the extractor found nothing)."""
    discovered = set(_discover_emitted_warning_tokens(REPO))
    for tok in (
        # the four leading-resolved-constant f-string tokens (the subtle Shape-E sub-shape)
        "quarantined_invalid_bars",
        "recovered_midnight_open_placeholder",
        "world_reference_partial_year_coverage",
        "world_reference_trailing_year_incomplete",
        # the leg families (trailing underscore kept)
        "world_reference_gold_leg_",
        "world_reference_fx_leg_",
        # a representative from each other shape
        "deduped_duplicate_daily_index_bars",  # A
        "zero_liquidity",                        # B
        "trailing_zero_volume_tail",             # C
        "fallback_instrument_served",            # D
        "stitched_segment",                      # E leading-text
    ):
        assert tok in discovered, f"forward discovery missed {tok!r}"


def test_forward_discovery_guard_catches_a_planted_gap():
    """Meta-test: prove the guard CATCHES an undocumented emission. Build a COPY of the tuple
    with one real emitted PLAIN token removed and assert discovery flags it (the real tuple is
    never mutated)."""
    reduced = tuple(t for t in _WARNING_TOKENS_180 if t != "zero_liquidity")
    assert "zero_liquidity" not in reduced
    discovered = _discover_emitted_warning_tokens(REPO)
    flagged = {
        tok
        for tok in discovered
        if tok not in _NON_TOKEN_WARNING_LITERALS and not _covered(tok, reduced)
    }
    assert "zero_liquidity" in flagged, (
        "the forward-discovery guard failed to flag a removed (undocumented) emitted token"
    )
