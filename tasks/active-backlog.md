# vnfin-oss — Active Backlog

Operating discipline (Boss 2026-06-19): git history is the progress tracker (commit often);
every reviewer/poller task lands here FIRST, then is processed and removed/marked done with a
commit/issue ref. See `/tmp/vnfin-operating-protocol-202606190959.md`.

Goal (Boss 2026-06-19, updated ~18:01): **REFACTOR FIRST** — provider-boundary + typed-result
contract refactor (`tasks/refactor-provider-contracts.md`), working with vnfin-oss-reviewer per
phase. GitHub bug fixing is PAUSED (log only) until the contract foundation (Phase 1–2) lands.

Flow per item: design → discuss+converge with reviewer → TDD red-first → green (full suite +
public-API + docs-contract + cov ≥85%) → commit → reviewer code review → push to master →
close issue → advance watermark → mark Done here.

_Last synced: 2026-06-21 00:40 +07_

> **#177 S&P 500 world-index — ✅ DONE (PUSHED + CLOSED).** Pushed master `011cffa..28bc529`
> (impl `011cffa` + critical fix `8ff1e78` + docs `2e7c694` + design/backlog + reviewer-suggested
> comment tweaks `28bc529`); #177 commented + CLOSED. Codex×2 APPROVE, zero blockers
> (review-202606210024); B's "MAJOR flake" = concurrent-reviewer tree collision, NOT a defect
> (8× deterministic green confirmed). `indices.world("SPY")→PriceHistory` via AV SPY (BYOK) →
> Stooq ^SPX fallback + `fallback_instrument_served` warning; adversarial self-verify caught+fixed 1
> CRITICAL (AV non-positive OHLC served as trusted primary). Full suite 3172 green. vf-advisor cleared
> to flip its S&P 500 chart mock→real.
>
> **#178 gold world-reference history — ✅ DONE + PUSHED + CLOSED.** Pushed master
> `28bc529..21f47cd`; #178 commented + CLOSED. Codex×2 APPROVE + 1 surgical M1 folded (no re-gate).
> Shipped `gold.world_reference_history_vnd()` = world-gold (XAU USD/oz, CurrencyApi→Stooq failover)
> × USD/VND (World Bank) × oz→lượng **1.20565** (37.5/31.1035, named constants) → annual VND/lượng;
> mandatory `world_reference_*` naming + always-present excludes-domestic-premium warning (+10–21%,
> NOT SJC/BTMC); `gold.domestic_history()` reserved → NotImplementedError source-gap (#182).
> **Self-verify (5-lens wf, pre-handoff) found+fixed 2 majors:** boundary-year partial-mean bias
> (+20.53%) → snap gold+FX to whole calendar years; dropped gold-leg `partial_coverage` → forwarded
> namespaced. **Reviewer M1 (folded `21f47cd`):** in-progress current year was a silent partial-year
> mean (dilutable coverage aggregate) → `world_reference_trailing_year_incomplete` warning, `_today()`-
> injected, independent of the aggregate. **Post-M1 3-lens self-verify ALL PASS** (2 minor findings
> folded: `current_year in common` robustness + UTC-choice doc; NIT `Optional` dropped). Suite **3197
> green**, surface additive (snapshot FROZEN), no-secrets green. Watermark/state left to reviewer;
> reviewer pinging vf-advisor to flip the gold line mock→real. Memory: [[compose-daily-and-annual-legs-align-calendar-year]].
>
> **NOW: #174 sector-index routing BUG — ACTIVE (TDD → reviewer LEAD review, NOT Codex×2).** Spec
> `spec-202606202230`. BUG: `prices.history(VNFIN)` correctly rejects (deny-list) but
> `index_history(VNFIN)` wrongly says "not a known market index; use prices.history()" (allow-list
> miss) → user dead-ends. FIX (minimal, NO registry-data/new-source): in BOTH `index_history` +
> `index_history_stitched` (`indices/client.py` ~101 and ~141), after alias resolution, when a symbol
> is NOT value-history-servable, branch on `is_known_index(symbol)`: True → terminal "recognized
> market index but value-history not supported in this version" diagnostic (NO "use prices.history()"
> text); else → keep existing route-to-prices message. GENERAL — covers ALL deny-only ids (10 sector +
> VN100/VNMID/VNSML/VNDIAMOND/VNFINLEAD/VNFINSELECT/VNXALL). Tests: each sector idx → prices rejects
> (unchanged) + both index fns give new diagnostic asserting NO "prices.history"/"for stocks";
> headline indices still serve (regression); HNX alias still serves; unknown symbol still routes to
> prices; add the 10 to the routing regression matrix. Serving sector-index HISTORY = separate
> deferred feature (note in close comment). TDD → reviewer LEAD review.
> **#183 = NEW, QUEUED LAST** (reviewer-accepted 00:04): optional interval/resample on `prices.history` +
> `indices.index_history`; **design-note-first**; lowest priority (advisor has a client-side workaround);
> has an `Interval.M1` minute-vs-month enum wrinkle (see #183 GitHub triage). Reviewer specs/gates when up.
> state/ watermark = reviewer. Clean-room: zero VNStock. Specs: spec-202606201815-issue177/-issue178;
> TL handoff handoff-202606202209.
>
> **State snapshot (18:33):** #173-unlisted **DONE+PUSHED** (`d522637`, #173 CLOSED).
> #157 RATIOS leg **DONE+PUSHED** (`9edad80`). #157 **BANK-MISLABEL leg DONE+PUSHED** (`d522637..0a28339`:
> `aa72dca` per-model_type itemcode map + `0a28339` reviewer cosmetics; Codex×2 APPROVE review-202606201727;
> #157 commented, **stays OPEN for the metrics leg**). Q1 probe PASS (VPB/ACB) + provenance `a01d3da`.
> **#176 phantom-tail DONE+PUSHED+CLOSED** — `068d919` warn-v1 (`trailing_zero_volume_tail`, D1, ≥10
> run, warn-not-drop) pushed `0a28339..1402b37`; Codex×2 APPROVE review-202606201750; #176 commented +
> CLOSED (reported silent-corruption surfaced). Deferred design-eval follow-ups (trim / cross-source
> reconciliation / ADV-dilution) live in design §8 + below — NOT open issues. **#172-RESIDUAL
> nav_end_gap DONE+PUSHED+CLOSED** — `27cb353` `nav_end_gap` success-path warning (cadence-relative,
> trailing-window diffs[-8:], today-injected) pushed `7bbd730..57574ba`; Codex×2 APPROVE
> review-202606201831 (all 4 refinements present; judgment call ENDORSED by all 3 — accept the
> self-clearing daily→weekly transition transient over a false-negative suppressor; lone note: the
> `max(1,…)` floor is dead-but-harmless guard). #172 commented + CLOSED. Full 3001 green, trio exit0,
> fmarket cov 96%, snapshot untouched. **This closed the entire reporter-bug queue.** FundList.nav
> per-fund as-of → reviewer-filed **#181** (out of v1 scope).
>
> **#157 METRICS LAYER — ✅ DONE + PUSHED + CLOSED** (`694b63f..8a3a21f`; #157 CLOSED 19:39).
> All THREE #157 legs now shipped: ratios (`9edad80`) + bank-mislabel (`aa72dca`) + metrics layer
> (`0739def..8a3a21f`). Built per rev2.6 via implement→adversarial-verify workflow `wf_4125b404-2eb`:
> new `metric_models.py` + `metric_api.py` (26-metric v1 catalog = 21 mapped + 5 derived, `serves()`,
> pure transformers, `metrics()`/`explain_metric_coverage()`, 11 exact §5 reasons) + docs/skill/CHANGELOG +
> 2 docs-contract guards. Codex×2 returned APPROVE_WITH_NOTES (review-202606201928) with ONE must-fix
> **M1** (trail-free `detail` on the AllSourcesFailed branch — C1+docstring leak; my judgment-call #2
> premise was wrong). **M1 landed `8a3a21f`** with a fail-first regression
> (`test_metrics_all_sources_failed_detail_is_trail_free`, proven red→green) + optional N1/N2 honesty
> polish (comments only). **Full suite 3083 passed, exit0; metrics+no_secrets+surface+docs gates green;
> snapshot untouched (additive); clean-room clean.** Bank metrics keyed ONLY to
> 12700/13000/14000/412000/413300/23800/23000/421900. NO Codex re-gate (M1 surgical, reviewer-authorized).
> #157 commented + CLOSED via `bin/gh-maintainer` (metrics was the last leg). Watermark left to reviewer.
> M1 CONFIRMED correct post-hoc by reviewer (19:41).
>
> **#179 vf-advisor monthly CPI YoY + SBV policy rate — ✅ DONE + PUSHED `66c7bdf..088220c` + #179
> CLOSED.** Codex×2 BOTH APPROVE, ZERO blockers (review-202606202037; N-a triple-verified+live-probed,
> single-source chain live-probed+e2e, CPI/INFLATION regression PASS, D3 AST-confirmed pure, 2
> mutations caught). Shipped per ACK'd design: two new `MacroIndicator` members on the existing keyless
> DBnomics path (NO new adapter) — `CPI_YOY` ("%", `M.{CC}.PCPI_PC_CP_A_PT`, monthly) + `POLICY_RATE`
> ("% per annum", `M.{CC}.FPOLM_PA`, monthly, honest SBV-proxy via 5th display element in `_DBN_MAP`).
> Both DBnomics-only → single-source monthly chains; WB-annual CPI(index)/INFLATION(%) untouched
> (regression-tested). N-a: verbose proxy string is DISPLAY only; canonical code/name stay
> `policy_rate`/`Policy Rate`; identity expr byte-identical in get_indicator + indicator_identity. D3:
> pure `_series_end_gap_warning(points, today)` + injectable `_today()` (#172 parity), FLOOR=210d,
> monthly-scoped, values kept. **Full suite 3103 green; trio green; snapshot FROZEN (additive-only);
> touched-module cov dbnomics 91%/indicators 97%.** Folded both APPROVE-stage extras: failover
> `_finalize`-survival test (`737687a`) + single-point fallback test (`088220c`, optional polish). NIT
> CPI_YOY name-form left as default for GDP/CPI consistency (reviewer-endorsed). Docs additive
> (macro-dbnomics, macro-and-fx, data-domains, domains.md 5→7, CHANGELOG). state/ watermark = reviewer.
> **#177/#178 still WAIT on Boss.**

---

## ✅ CONTRACT REFACTOR COMPLETE — 0 OPEN BUGS (2026-06-19 ~23:35)

The provider-boundary + typed-result contract refactor is **DONE**, all reviewer-gated:
Phase 0 (freeze) → 1 (`_contracts` primitives) → 2 (fundamentals migration) → 3 (typed-result
extraction) → 4 (6 adapter batches: funds, macro, security/index, crypto/FX, gold, funds-NAV) →
6 (fundamentals close-loop). `origin/master` at `2c079a0`, full suite **2591 green**, public-API
byte-equal throughout, no clean-room hits. Phase-6 stash dropped (superseded by the migration).

- **Bugs closed via the refactor (15):** #33 #34 #32 #48 #30 #75 #9 #93 #143 #144 #142 #44 #45 #26 #21.
- **`open_bugs = []`.** Only open issues are **enhancements**: #140 (financial news) + #145 — both
  product decisions for Boss, NOT bugs.
- **Phase 5 cleanup: DONE** (`93eee64`, Checkpoint G APPROVE_WITH_NOTES review-202606192350) —
  `docs/architecture/provider-contracts.md` + 3 polish notes applied (IMF type-specific message,
  validate_country_iso3 ASCII `[A-Z]{3}`, canonical_crypto_pair shape-only docstring). The IMF/ISO3
  polish intentionally hardens malformed-input behavior (not pure docs). `origin/master` `93eee64`,
  suite 2591 green. **REFACTOR 100% COMPLETE.**
- **#145 source diagnostics: DONE** (Boss-authored feature; pushed `ae799dc..c55c286`, CLOSED;
  reviewer review-202606200003). Additive offline `vnfin.diagnostics` (source_capabilities +
  explain_world_gold_history + explain_index_constituents) + world-gold pre-coverage fail-fast.
  Suite 2607 green; public-API additive (surface snapshot + regression test).
- **#140 financial news: DONE** (Boss-approved-in-issue; pushed `ca293d6..efdf2d3`, CLOSED;
  reviewer review-202606200026). BYOK `vnfin.news` over Alpha Vantage NEWS_SENTIMENT — daily
  headline metadata only, no scraping/full-text/real-time. Suite 2667 green; public-API additive.
- **#146 liquidity & position sizing: DONE** (Boss-authored; pushed `e518878..4ce11dc`, CLOSED;
  reviewer review-202606200632). Additive offline `vnfin.liquidity` (from_price_history + profile;
  ADV stats + max-order sizing; close*volume estimate labeled). Suite 2705 green; public-API additive.
- **Batch A: DONE** (#148 tutorial fields + #151 window_too_wide diagnostic) + README agent
  prompt/issues note — pushed `591a439..06acb62`; #148/#151 CLOSED (review-202606200858).
- **#153: DONE** — gold tutorial GoldBar.price + docs-contract guard; pushed `d52dc98..f4435e5`, CLOSED (review-202606200902).
- **CLAUDE.md: updated** — execution model (orchestrate via sub-agents/worktrees), integration-test
  + long-message rules (1074a0a, Boss directive).
- **Design-first parked (reviewer triage review-202606200902, filtered specs only):**
  - B: **#147** v1 DONE (sub-agent + main integrate; pushed `eadf7e1..a645c71`, CLOSED; review-202606200931). index_history_stitched. Deferred polish (non-blocking notes): rename design-doc 'Open questions' heading; add returned-segment-interval regression.
  - C: **#149/#152/#156** macro / rates / global-benchmark diagnostics. **#156 addendum** (poller
    triage ~13:10): global equity benchmark coverage diagnostics — in-scope/design-first, queued
    BEHIND #157; do NOT switch. **#152 addendum** (poller
    triage review-202606201103): deposit-rate/fixed-income parked design-first. Scope: fixed-income/
    rates/yield-curve data + diagnostics IN; deposit-rate aggregation is source/legal-diagnostic ONLY
    unless clean sources approved; OUT: bank-product advice/ranking/blind scraping.
  - D: **#154/#150** derived gold-premium / portfolio analytics (offline, data-only, no advice).
  - E: **#155** fund metadata / allocation diagnostics. **Addendum** (poller triage
    review-202606201058): accepted/parked design-first behind #159 (likely after #157 unless Boss
    reprioritizes). Scope: fund metadata / NAV-as-of / staleness / holdings+ETF diagnostics; starts
    with a source/legal + taxonomy design doc. OUT: recommendations/ranking/advice/blind scraping.
  All design-first: no code until reviewer-approved design.
  - **#158: DONE** (delegated to sub-agent, integrated by main; pushed `7d528d2..cd7b941`, CLOSED;
    review-202606200907). Same-NAV dedupe+warning; conflicting -> InvalidData; #144 guards preserved.
  - **#162 P0: DONE** (sub-agent + main; 2 review rounds: calendar-date keying, then D1 gating;
    pushed `46a3ce5..b36a688`, CLOSED; review-202606201001 + 2 Codex sub-reviewers). One bar/calendar-date
    for D1 index (dedupe-identical+warning / raise-conflicting in source path); H1/non-D1 + equity unchanged.
  - **#164: DONE** — docs keyword start=/end= for prices.history (7 examples) + guard; pushed
    `207c462..3731f14`, CLOSED (review-202606201008).
  - Design-first: #157/#159 (#159 now in implementation, see Now). Design-eval-only (parked):
    #160/#161/#163 (corp-actions) + #150 cost/tax addendum
    (design-first, offline, user-supplied/preset w/ effective-dates/provenance/stale-warnings) — batch w/ #157/#161/#150.
    - **#163 addendum** (poller triage review-202606201039): external addendum useful but PARKED
      design-eval only — do NOT switch from #159. Future #163 scope: corporate-action/dividend
      EVENT data primitives + source/legal/diagnostics design; OUT: total-return/backtest/app
      helpers and blind scraping.
    - **#149 addenda** (poller triage review-202606201046 + review-202606201111): macro source-health
      AND global-macro addenda accepted for future design-first work but PARKED — do NOT switch from
      #159. Combined safe scope: macro data primitives + indicator catalog + country/source/
      frequency/as-of/freshness/source-health/coverage diagnostics; OUT: regime scoring/allocation
      advice/blind scraping.
    - **#157 addendum** (poller triage review-202606201101): fundamentals-metrics addendum
      accepted/HIGH-PRIORITY but PARKED for AFTER #159 — do NOT switch from #159 blocker fix.
      Future scope: canonical metrics + bank/non-bank mappings + coverage/source-health diagnostics;
      OUT: advice/ranking/screener app helpers/blind third-party ingestion. (NOW ACTIVE — see Now.)
    - **#166** (poller triage review-202606201304): index volume semantics — ACCEPT design-first/
      docs-diagnostics gap, queued BEHIND #157. No coder action now.
    - **#167** (poller triage review-202606201304 + addendum review-202606201404): VN equity universe /
      symbol discovery + **profile-diagnostics addendum** — ACCEPT design-first core data primitive,
      likely high-value AFTER #157. No coder action now.
    - **#161** (poller triage + **valuation-history addendum** review-202606201404): market valuation /
      sector weights / concentration analytics — ACCEPT design-first/eval. No coder action now.
- **Phase R0 refactor audit: DONE** (APPROVED, review-202606200818; report pushed `211321e`).
  No invariant violations; no do-now refactor. C1 (FX currency-code DRY)/C2/C3 defer; C4/C5/C6
  do-not-do. Report: `tasks/refactor-audit-2026-06-20.md`.
- **Architecture deep-dive docs: DONE** (Boss directive; pushed `b046374..f48e789`; reviewer
  review-202606200802). New `docs/architecture/` directory (system-overview / data-domains /
  failover-and-validation / maintainer-workflow + refreshed provider-contracts) with progressive
  disclosure + 5 Mermaid flow diagrams; authored via the `vnfin-architecture-cartographer`
  sub-agent. Docs-only; full suite green. (Fixed a review BLOCK: reviewer-only poller routing.)
- **✅ 0 OPEN ISSUES (re-confirmed).** All bugs fixed, full contract refactor (Phases 0–6) shipped,
  three enhancements delivered (#145 diagnostics, #140 news, #146 liquidity), and architecture
  docs written. origin/master `f48e789`. Steady-state; poller watching.

## Refactor done today (Phase 4 batches)

- **🎉 PHASE 4 COMPLETE** — all 6 adapter batches pushed/reviewed; bugs closed via refactor:
  #33/#34/#32/#48/#30/#75/#9/#93/#143/#144. Remaining open = the 5 Phase-6 close-loop issues only.
- **Phase 4 batch 6 (funds NAV/window #144) — COMPLETE, pushed `caeef2e..ec4a2bf`; #144 CLOSED.**
  Broad-window fetch + client-side filter; navDate-first out-of-window skip. Suite 2579 green.
  Checkpoint E APPROVE_WITH_NOTES (review-202606192338).
- **Phase 4 batch 5 (gold #143) — COMPLETE, pushed `33033cf..734aa9f`; #143 CLOSED.** PNJ excludes
  silver by masp+tensp (via `_is_silver`) before dedup/price; all-silver → EmptyData; non-string
  tensp → InvalidData. Suite 2570 green. Checkpoint E APPROVE_WITH_NOTES (review-202606192324).
- **Phase 4 batch 4 (crypto/FX boundary) — COMPLETE, pushed `b4db48d..8b57ece`; #9 + #93 CLOSED.**
  `canonical_crypto_asset`/`canonical_crypto_pair` (v0.2: BTCUSDT/BTC-USD; slash rejected; fullmatch)
  + longest-known-quote validation at the crypto boundary (zero-call); Binance/Coinbase
  normalize_symbol space-only strip + `_ASSET_RE` fullmatch; OpenER VND-anchor finiteness (#93).
  Suite 2566 green. Checkpoint E APPROVE_WITH_NOTES (review-202606192316, 3 rounds).
  Phase-5 note: `canonical_crypto_pair` is shape-only — future call sites must use
  `_normalize_crypto_symbol` or add known-quote validation.
- **Phase 4 batch 3 (security/index identifiers) — COMPLETE, pushed `4fb350f..e13da8f`; #30 + #75
  CLOSED; #9 price+index subset commented (kept OPEN for crypto).** `canonical_security_symbol`
  on price symbols, index_history/constituents selectors, and constituent stockSymbol; raw-caller
  restamp removed; zero-HTTP malformed rejection. Suite 2504 green. Checkpoint E APPROVE_WITH_NOTES
  (review-202606192249, notes applied).
- **Phase 4 batch 2 (macro sources) — COMPLETE, pushed `bdb5a4b..ed4ca51`; #32 + #48 CLOSED;
  #21 macro subset commented (kept OPEN).** Shared `canonical_country_iso3` (#32) +
  `canonical_macro_indicator` (#48); DBnomics no-`A.None.*` identity fix. Suite 2429 green.
  Checkpoint E APPROVE_WITH_NOTES (review-202606192233). Phase-5 non-blocking notes: IMF falsey
  message wording; public `validate_country_iso3` consistency with the new contract.
- **Phase 4 batch 1 (Fmarket funds) — COMPLETE, pushed `49ac99a..1d9a5b6`; #33 + #34 CLOSED.**
  Canonical security/fund identifier contract (`canonical_security_symbol`/`canonical_fund_code`);
  present-null code fails closed; suite 2339 green. Checkpoint E PASS (review-202606191948).

## Paused bugs — after refactor

- **#144** (parked, poller 19:45) — Fmarket NAV window issue; **Phase 4 funds NAV/window batch**
  (NEXT). Do not fix now.
- **#142** (parked, poller 18:35) — fundamentals residual; Phase 6 fundamentals close-loop.
- **#44 / #45 / #21 / #26 fundamentals provider-shape hardening** — addressed by the Phase 2
  contract migration (`ec69a1e`); to be CLOSED in Phase 6 after Checkpoint C approves. WIP stash
  `git stash@{0}` superseded (reference only). Original handoff:
  `/tmp/vnfin-wip-handoff-44-45-21-26-202606191803.md`.
- **(historical stash note)** — WIP stash: `git stash@{0}`
  ("WIP paused: #44/#45/#21/#26 ..."); handoff `/tmp/vnfin-wip-handoff-44-45-21-26-202606191803.md`.
  Partial+untested (#44/#45/#21 key-presence guards; #26 `canonical_item_code` helper unwired).
  All four issues OPEN. **Do NOT fix until the refactor contract foundation lands** — Phase 2 will
  handle them via migration, Phase 6 closes them. Do not apply the stash before then.
- **#140 — "financial news" enhancement** — parked (product/scope, not a bug).

## Now (WIP)

- **#157 fundamentals metrics — DESIGN FINAL-APPROVED (review-202606201405); READY FOR IMPL, queued
  AFTER #172** (design `84265fb`). #168+#169 closed. Reviewer re-sequenced: new HIGH bug #172 (fund
  NAV staleness) goes BEFORE the big #157 feature. On start → TDD fork building the full feature per
  `docs/design/fundamentals-metrics.md` (rev2.6 exact spec): metric_models.py + metric_api.py + facade
  + full §9 test matrix + docs + ADDITIVE snapshot; then adversarial verification Workflow → reviewer
  → push+close. Full design history below. (spec spec-202606201222). Rounds:
  `1616ff6`→BLOCK×8→rev2 `a0a00cc`→BLOCK×7→rev2.1 `6fbe694`→rev2.2 `3a38a19`→BLOCK×6→rev2.3 `aeac970`
  →BLOCK×4→rev2.4 `51948cb` (+ adversarial Workflow consistency sweep caught 2 more)→BLOCK (label
  addendum review-202606201324)→rev2.5. No code until reviewer approves. **rev2.5** folds the
  label/statement-semantics addendum: identity invariant (statement+source-namespace+item code, NEVER
  the human label); `MetricInput.name` raw-label provenance + `input_names` DataFrame column; labels
  provenance-only (no label-mismatch diagnostic); label-provenance tests; shorthand cleanup.
  Deliverable: `docs/design/fundamentals-metrics.md` (design-only). On APPROVE → delegate TDD impl. Additive, OFFLINE layer on top of existing `get_financials()` + `itemcodes.py` (no new
  external source). v1: canonical metric catalog (corporate + bank headline mapped, per spec codes) +
  5 derived (gross/net margin, liab/equity, cash/assets, OCF margin) + coverage diagnostics. API:
  `metric_catalog()`, `explain_metric(id)`, `metrics(symbol, period)`, `explain_metric_coverage(...)`.
  Models: MetricId/MetricKind/MetricAvailability enums; MetricDefinition/MetricValue/MetricReport/
  MetricCoverage. v2 (deferred/blocked): ROE/ROA/ROIC, FCF, valuation (P/E,P/B,...), EPS/BV. Non-goals:
  ranking/advice/screener-with-strategy, blind external ingestion, generic item_<code> as
  investor-ready, silent bank/non-bank mixing. Spec: `~/tools/vnfin-oss-reviewer/reviews/spec-202606201222-issue157-fundamentals-metrics.md`.
  - **#157 BANK DATA-INTEGRITY INPUT (HIGH) — ✅ DONE + PUSHED `d522637..0a28339` (`aa72dca` fix +
    `0a28339` cosmetics). Codex×2 APPROVE (review-202606201727); #157 commented, STAYS OPEN (metrics leg).**
    Per-`model_type` itemcode map (`_NAMES_BY_MODEL_TYPE`) + hard-switch `item_name(code, *, model_type=)`;
    `_BANK` + corporate cross-fallback removed → a code resolves only inside its own statement template,
    else honest raw `item_<code>` (the 6 wrong-label codes 22070/421601/22160/411600/413100/412000-as-assets
    now go raw). vndirect:337 migrated. Q1 probe PASS (VPB/ACB share SOCB codes; identity 13000+14000==12700
    exact to the VND, all 4 banks) — provenance `a01d3da` (`docs/design/bank-itemcodes-probe-20260620.md`).
    N1 metrics §6 re-point done; corporate labels byte-identical; suite 2961 green, itemcodes.py 100% cov.
    Design doc `c2bb4db`+`a01d3da`. _Original gate notes:_ 5 Qs resolved (Q1 PASS, Q2 hard-switch, Q3 cashflow
    raw, Q4 diagnostic in metric layer, Q5 412100/23003 raw).
    Reporter + reviewer
    independently reproduced a bank fundamentals mislabel in `get_financials` (VCB, is_bank=True,
    balance, annual): code `412000` is labeled 'Tổng tài sản'(Total assets)=1,648.5T but that is
    VCB's LOANS; the REAL total assets=2,442.3T sits under raw unlabeled code `12700`. Cross-statement
    leak: income code `14000` ('Lợi nhuận thuần từ hoạt động kinh doanh') appears in the BALANCE
    statement. So the bank item-code→label map is wrong + statement membership is contaminated →
    headline bank values (PAT/NII/assets) wrong 5-7x or hidden under raw codes. **ROOT FIX at the base
    layer (so raw `get_financials` is also correct):** correct the bank statement-template / itemcode→
    canonical map vs the bank chart of accounts (assets=`12700`, `412000`=loans); ENFORCE per-statement
    membership (reject income `14000` from balance); emit raw/coverage diagnostic for unverified codes —
    NEVER a wrong human label on a value. #157 bank canonical metrics build on the corrected map +
    blocked/missing diagnostics. Verified anchors → synthetic offline tests. Codex x2 review against
    these anchors. Spec: `~/tools/vnfin-oss-reviewer/reviews/review-202606201553-issue157-bank-fundamentals-mislabel-VERIFIED.md`.
  - **#157 RATIOS-GUARD INPUT — ✅ DONE + PUSHED `9edad80` (81a7b2a..9edad80), #157 commented (stays OPEN).**
    Codex×2 BOTH APPROVE (review-202606201646); pre-push fixup (drop dead `MISSING` import cafef.py:42)
    applied. Suite 2929 green; cov client 97%/cafef 93%; gate-trio+clean-room+diff-check clean. 3 parts
    shipped: statement-type-aware unit guard, cafef present-null ReportType tolerance (ratio-only),
    Period.UNKNOWN (no TTM-as-FY). Repro was:
    `get_financials('FPT','ratios','annual')` → `AllSourcesFailed` (vndirect: `currency None != chain
    unit VND`; cafef: `ratio ReportType: expected string got NoneType`) → ratios (P/E, P/B, ROE, ROA)
    fully unavailable. FIX (3 parts): (1) make the failover unit-consistency guard **statement-type-
    aware** — `ratios` is dimensionless so chain unit = `None` (currency=`None` is CONSISTENT, not a VND
    mismatch); KEEP VND homogeneity for income/balance/cashflow; a ratios report arriving WITH a
    monetary currency stays rejected (don't blanket-disable). (2) harden the cafef ratios parser to
    tolerate null/absent `ReportType` (coerce/skip). (3) after fix, confirm annual-vs-TTM period mapping
    (annual ratios surfaced a 2026-06-30 TTM-looking date). Codex x2 review when it lands. Both #157
    base-layer fixes (bank-mislabel + ratios-guard) land BEFORE the canonical metric catalog builds on
    the corrected base. Spec: `~/tools/vnfin-oss-reviewer/reviews/review-202606201617-issue157-ratios-currency-guard-VERIFIED.md`.

## Next / in-flight bugs (BEFORE large #157 implementation)

- **#172 + #173 — Fmarket fund-data coverage. DESIGN APPROVED (review-202606201506,
  APPROVE_WITH_NOTES; design doc `fund-coverage-holdings.md`).** Picks: Q1=A, Q2=B reframed, Q3=two
  separate commits/reviews, Q4=yes subclass. Sequencing: #172 impl → commit → reviewer → #173 impl →
  commit → reviewer → then #157.
  - **#172 NAV staleness → `StaleData(EmptyData)`. ✅ FIX SHIPPED (correct, stays) — pushed `18eb915`
    (287ae5b..6c37e7c). ⚠️ ISSUE RE-OPENED for a RESIDUAL (success-path staleness) — see #172-RESIDUAL
    below, queued BEHIND #173, design-first.** Reviewer Codex x2 BOTH APPROVE on the StaleData fix
    (review-202606201534, all 4 conditions verified). Suite 2871 green; cov TOTAL 95% / fmarket.py 97%;
    gate-trio green; clean-room + diff --check clean; 8 fail-first tests. (Watermark: reviewer owns it —
    I restored last_seen.txt, left state/ to reviewer; see memory.) N1 snapshot regen at release.
    Gated live probe (2026-06-20 ~15:12) RULED OUT truncation/pagination: all 65 funds' wide
    `nav_history` ends uniformly at 2025-12-05, per-fund row counts vary 110→1267, first-dates track
    each inception → array complete inception→provider cutoff = genuine systemic provider staleness
    (not a request/array-cap bug). Contract: track max navDate over ALL rows via `_nav_row_date`
    BEFORE the lo/hi skip (NO #21/#158/value guards on out-of-window rows); post-filter points empty
    AND window start `lo` given AND `max_navdate < lo` → `StaleData` msg `"fmarket: NAV history for
    product {id} ends at {latest}, before requested {start}..{end}"` (data-gap only, true for closed
    funds); else `EmptyData` (unchanged — pre-inception + sparse/weekend straddle). Add `StaleData`
    to exceptions.__all__ (additive; snapshot regen at release). 8 synthetic offline tests.
  - **#173 bond holdings → OPTION A. ✅ DONE — pushed `6c37e7c..15ab705`, #173 CLOSED**
    (reviewer Codex×2 BOTH APPROVE, review-202606201616; my own adversarial-verify Workflow = 0
    confirmed defects). `holdings()` merges `productTopHoldingList`+`productTopHoldingBondList` into
    `tuple[FundHolding,...]`; additive `FundHolding.instrument_type` (fail-closed unknown) +
    `as_of_utc` (per-row `updateAt` epoch-ms, never fabricated); new `asset_allocation(id) ->
    AssetAllocation` (+`AssetClassWeight`, STOCK/BOND/CASH, no forced sum≈100, fail-closed class);
    EmptyData only when both lists empty; combined dedup+weight guard; #21 factored into shared
    `_fetch_detail_data`. Repo-wide stale-fact sweep done ([[feature-flips-stale-fact-sweep-whole-repo]]).
    Suite 2917 green; funds cov 96%; all-additive. **Non-blocking nits (reviewer N1/N2, follow-up):**
    (N1) `asset_allocation` redundant `data.get("code")` re-read; (N2) unused `seen_codes=None`
    default branch — see Non-blocking follow-ups. N3 snapshot regen = release-time.
    - **⚠️ #173 RE-OPENED — UNLISTED-bond residual (HIGH; review-202606201628). ✅ INTEGRATED on master
      local `d522637` (parent 9edad80) → IN Codex×2 REVIEW (handoff /tmp/vnfin-173-unlisted-review-handoff-202606201652.md);
      push+re-close #173 on approve.** Merged tree 2958 green; cov fmarket 96%/models 99%/keys 100%;
      gate-trio+clean-room+diff-check clean. Implements reviewer option (i) (relax non-equity stock_code,
      equities strict); refinements (a) fail-closed-on-garbage + (b) caller-gate docstring satisfied; new
      `enum_tag_or_other` helper (unknown stringlike type→OTHER, malformed→InvalidData). Original bug:
      my fail-closed `{STOCK,BOND}` whitelist hard-failed ~8
      UNLISTED-bond funds (defensive-credit sleeve = core use case): bond `type` is `BOND` **or**
      `UNLISTED_BOND` (ASBF id51 / VFF id21 / DCBF id27); my `canonical_enum_tag` turned their EmptyData
      into **InvalidData** (harder failure). Also ASBF has a descriptive `stockCode`
      `'Trái phiếu chưa niêm yết'` that `canonical_security_symbol` rejects. FIX (additive): (1) accept
      `{STOCK,BOND,UNLISTED_BOND}` granularly + map present-but-unknown type → new **`OTHER`** tag (NOT
      fail-closed — reverses the earlier fail-closed call ON THE EVIDENCE; OTHER is honest); (2) descriptive
      bond id must not fail the fund — **builder model pick: relax `stock_code` validation for bond/
      unlisted-bond rows to accept a non-empty non-canonical identifier; equities stay strict
      `canonical_security_symbol`** (reviewer offered alt: add a `name` field + None code; Codex x2 to
      confirm); (3) preserve listed-bond/equity behavior; synthetic tests (anchors ASBF/VFF/DCBF). Codex x2.


- **#171 — docs/diagnostics polish: world-gold opt-in Stooq path** (poller triage review-202606201355).
  In-scope docs/enhancement; PARKED behind #168/#169/#157. Make the opt-in Stooq path unambiguous —
  either expose a supported factory OR update diagnostics suggested_actions + docs/api.md with exact
  manual opt-in (`StooqGoldSource` + `default_world_gold_client`). Do NOT add Stooq to the default chain.
- **#170 — design-first: domestic VN gold history / diagnostics** (poller triage review-202606201348).
  In-scope; PARKED behind #168/#169/#157. NO implementation without a source/legal/provenance design.
- **#172-RESIDUAL — success-path NAV staleness warning (DESIGN-FIRST, queue BEHIND #173).** Reviewer
  re-opened #172 (review-202606201541): StaleData (shipped, correct) only fires for a FULLY-PAST window;
  the COMMON calls — default `nav_history(id)`, `to_date`-only, or a window STRADDLING the 2025-12-05
  cutoff — still SUCCEED and silently return a series ending ~6mo short with `warnings=()`. Fix (additive,
  NO exception): on a successful `nav_history` whose `max(navDate)` is MATERIALLY older than the effective
  upper bound (`to_date` else today), append a non-fatal entry to `NavHistory.warnings` (field already
  exists). TWO hard boundaries: (1) NO `list_funds` cross-ref inside `nav_history` (no 2nd call, no
  history-as-of vs current-NAV coupling); (2) pick a 'material' staleness threshold so a normal 1-3
  business-day lag does NOT warn but a months-long lag does — **that threshold is THE design decision,
  document it**. Design-first → converge with reviewer BEFORE coding; Codex x2 review when it lands.
- **#174 — sector-index routing BUG — ✅ SPEC READY (reviewer 22:31, spec-202606202230); INTAKE AFTER
  #177 (jumps ahead of #178).** BUG = contradictory routing loop: `prices.history(VNFIN)` correctly
  rejects (deny-list) but `index_history(VNFIN)` wrongly says "not a known market index; use
  prices.history() for stocks" (allow-list miss) → user dead-ends. Root cause: the index path conflates
  "not value-history-servable" with "not an index at all". **FIX (minimal — NO registry-data change, NO
  new source):** in BOTH `index_history` + `index_history_stitched` (`indices/client.py` ~101 and ~141),
  after alias resolution, when a symbol is NOT value-history-servable, branch on `is_known_index(symbol)`:
  True → terminal "recognized market index but value-history not supported in this version" diagnostic
  (NO "use prices.history()" text); else → keep existing route-to-prices message. GENERAL — covers ALL
  deny-only ids (10 sector + VN100/VNMID/VNSML/VNDIAMOND/VNFINLEAD/VNFINSELECT/VNXALL family), not just
  the 10. Tests: each sector idx → prices rejects (unchanged) + both index fns give the new diagnostic
  asserting NO "prices.history"/"for stocks"; headline indices still serve (regression); HNX alias still
  serves; unknown symbol still routes to prices; add the 10 to the routing regression matrix. Serving
  sector-index HISTORY = separate deferred feature (note in close comment). **Process: TDD → reviewer
  LEAD review (NOT Codex×2 — localized error-path fix).**
- **#176 — delisted/phantom trailing-tail (HIGH; reviewer VERIFIED, spec
  review-202606201601-issue176-delisted-phantom-tail-VERIFIED.md). QUEUED BEHIND the #157 base-layer
  fixes.** Multi-source (vps + vndirect) trailing run of zero-volume O=H=L=C "phantom" bars after a
  symbol delists/halts. **Fix in the CANONICAL post-processing layer (NOT per-adapter):** detect a
  trailing zero-vol O=H=L=C run and **WARN** (no silent drop). Threshold = **design-first** (how long a
  run / what tolerance qualifies as phantom). Design-first → converge with reviewer before coding; Codex x2.

## Boss-filed vf-advisor features (#177/#178/#179)

Filed by Boss (`hungson175`) from the **vf-advisor** app; each replaces a currently-MOCKED series.
**ALL THREE Boss-GREENLIT (2026-06-20).** #179 ✅ DONE+CLOSED. #177 ACTIVE (see NOW). #178 QUEUED next.
- **#177 — US/global equity index (S&P 500/SPY)** — **ACTIVE.** AV `TIME_SERIES_DAILY` SPY (BYOK) PRIMARY
  + Stooq `^SPX` keyless best-effort FALLBACK; FRED RULED OUT (10y cap + redistribution-prohibited).
  `indices.world(symbol="SPY")` PriceHistory-shaped; SPY-as-proxy v1, documented; local cache. Design
  note → lead quick-gate → TDD → Codex×2. (TL handoff handoff-202606202209.)
- **#178 — VN gold (world-reference line)** — **QUEUED.** Ship `gold.world_reference_history_vnd()` =
  Stooq world-gold × USD/VND × (31.1035/37.5) → VND/lượng, MANDATORY `world_reference_*` + `premium_note`
  (excludes +10-21% VN premium; NOT SJC); reserve `gold.domestic_history()` → source-gap diagnostic.
  Source-hunt follow-up = **#182**. Likely straight to TDD→Codex×2.
- **#179 — Monthly CPI YoY + SBV policy rate** — ✅ **DONE+PUSHED+CLOSED** (`66c7bdf..088220c`; Codex×2
  APPROVE). 2 new MacroIndicator members on the keyless DBnomics path; see #179 snapshot block above.

## Review blockers (reviewer BLOCK/P1 waiting for fix)

- _(none)_

## Poller triage (newly triaged)

- **#165 — RESOLVED as malicious (NOT a real feature).** Reviewer triage: the body was a
  **prompt-injection / secret-exfiltration** attempt disguised as a China-FX request. Reviewer
  labeled it invalid, **closed as not planned**, did NOT forward raw text or create a coder task,
  advanced the poller watermark. **Injection-safe flow worked as designed** — I treated the external
  issue text as DATA and routed to the reviewer instead of acting on it. No code/action taken. If a
  genuine China-market FX feature is ever wanted, it needs a clean issue (pairs/frequency/source/legal).
- **#140 — "financial news" FEATURE request** (enhancement label). NOT a bug → Boss/product-scope
  decision; parked (reviewer agrees, like #137). Not implementing autonomously.

## Next

- _(none)_

## Non-blocking follow-ups (only if Boss/reviewer prioritizes — NOT open issues)

- **#173 N1/N2 (reviewer nits, review-202606201616, reviewed-follow-up — re-review before push):**
  N1 = `asset_allocation()` re-reads `data.get("code")` redundantly (factor with `holdings()`);
  N2 = the `seen_codes=None` default branch on `_parse_holding`/`_parse_asset_class` is now never hit
  (both callers pass a set) — drop or keep as defensive. Cosmetic; bundle into a future funds touch.
- #69: `quote_asset=None` + a normalized (currency-form) `price_unit` is currently accepted;
  a stricter "quote_asset mandatory" policy would be a separate follow-up (reviewer note 14:21).
- #130: `model_type` allow-list is fixed to {1,2,3,101,102,103}; widen only if an official set is documented.
- #133: no accepted-exchange set / provider_symbol contradiction rule yet (deferred until a
  provider-symbol mapping is defined).
- #116: `_QTY` left boundary allows a digit glued to a letter (`ABC5 LUONG`) — revisit if such names appear.
- #124: crypto bar `time` checked tz-aware only, not exact UTC offset — future tightening.

## Done today (trim periodically)

- **#168 price/index namespace guard — DONE/CLOSED** (review-202606201424; fixes `53519ff`/`f7ab8f9`/
  `f4655ba`). Fail-loud asymmetric guard (prices deny-list known indices incl. HNX/UPCOMINDEX aliases;
  index_history allow-list; liquidity inherits) via private `_contracts/index_registry.py`. Snapshot
  unchanged (private flag). Watermark 07:32Z.
- **#169 crypto partial-coverage — DONE/CLOSED** (review-202606201424; fix `b9283f4`). Coverage-aware
  failover: full-cover wins; else best-available (max in-window overlap, source order) + exact
  `partial_coverage` warning constant; hard guards retained. 12 zero-network regressions. Watermark 07:32Z.
- **#159 FX history — COMPLETE, pushed `5e4563d..ad83521`, CLOSED** (final APPROVE review-202606201140,
  2 Codex sub-reviews APPROVE). First historical FX in vnfin: `vnfin.fx.history()` → `FXHistory`
  (annual USD/VND via no-key World Bank `PA.NUS.FCRF`, `source="worldbank_fx"`) + `FXPoint` +
  `rate_on`/`rate_for_year` (exact, no fill) + offline `explain_fx_coverage`. Spot `get_rate`
  unchanged; monthly/cross-quotes = v2. Design-first → impl sub-agent `167c622` → fix `aa42040`
  (B1-B3 source-boundary/date/accessor fail-closed) → 4 B4 doc rounds (root cause: ~10 files repo-wide
  asserted FX spot-only; fixed all + added repo-wide docs-contract guards scanning docs/skills/root-md/
  fx/diagnostics/llms.txt). Full suite 2811 green, coverage 95%, public-API additive. Watermark →
  `2026-06-20T04:38:31Z`. **0 OPEN BUGS.** _Process lesson:_ when a feature flips a long-standing
  "X unsupported" fact, grep the WHOLE repo for that claim in pass 1 + add a repo-wide guard up front.
- **#141 — COMPLETE, pushed `b0037c0..7df59e8`, closed.** `f8ff403` — VNDirect statement
  non-object row → InvalidData (mirrors ratios path). APPROVE_WITH_NOTES. Suite 2082 green.
- **#66 + #26 batch (reopen) — COMPLETE, pushed `7915596..c6eb733`, closed.** #66 `266d7c0`
  (WorldBank duplicate observation-date guard); #26 `d238e68` (VNDirect ratios reject duplicate
  ratioCode within a reportDate). APPROVE_WITH_NOTES. Suite 2077 green.
- **#44 + #21 batch (reopen) — COMPLETE, pushed `6a73dac..7915596`, closed.** #44 `d4ae617`
  (VNDirect all reportType/modelType-skip → InvalidData); #21 `3e470b6`+`7915596` (WB
  indicator.id; UDF present blank/null symbol; VNDirect present falsey/non-str code add-on).
  APPROVE_WITH_NOTES. Suite 2073 green.
- **#78 (reopen) — COMPLETE, pushed `1d8c780..6a73dac`, closed.** `cfd2282` — macro
  returned-indicator identity: `indicator_identity` on WB/IMF/DBnomics + `_fetch` validation
  (declared exact / undeclared→canonical). APPROVE_WITH_NOTES. Suite 2046 green.
- **#112 + #21 (reopen) — COMPLETE, pushed `50eb27b..ded0b97`, closed.** #112 `e14de5e` GoldApi
  present-falsey updatedAt → InvalidData (raw-is-None-only fallback); #21 `9750858` VNDirect
  all-code-mismatch → InvalidData (wrong-identity, not no-data). APPROVE_WITH_NOTES. Suite 2039 green.
- **Schema/FX batch (#87 + #28) (reopen) — COMPLETE, pushed `2356fa4..2117c51`, closed.**
  - **#87** `454fe42` — health check_schema rejects JSON bool on numeric (int,float) paths
    (unless bool explicitly allowed). APPROVE_WITH_NOTES.
  - **#28** `90474d9` — Vietcombank get_rates rejects duplicate canonical CurrencyCode (fail
    closed). APPROVE_WITH_NOTES. Suite 2032 green.
- **DBnomics batch (#104 + #66) (reopen) — COMPLETE, pushed `2e6b884..2356fa4`, closed.**
  `e7a43c4` — strict canonical period_start_day grammar (reject compact/ISO-week/padded/
  non-str) + duplicate-date guard. APPROVE (review-202606191553). Suite 2026 green.
- **Returned-provider-identity batch (reopen) — COMPLETE, pushed `9cb8aff..082526e`, closed.**
  - **#35** `42872ad` — CurrencyApi `_doc_date`: present falsey/non-string date → InvalidData
    (raw-is-None-only fallback). APPROVE.
  - **#21** `0fedd05`+`78d3d3b` — Fmarket nav row productId (key-presence, present-null rejects);
    holdings detail id required==fid + code non-empty canonical; GoldApi payload symbol ==
    requested. APPROVE after funds BLOCK (present-null/missing-id/padded-code). Suite 2017 green.
- **#106 (reopen)** OpenER fractional `time_last_update_unix` truncation — `9e22a89`, pushed
  `faf3810..35ed92c`, closed. `_as_of` accepts only int/integral-finite-float; fractional/
  non-finite → tz-aware now() fallback. APPROVE. Suite 1986 green.
- **#41 (reopen)** Fmarket envelope status/code fractional/bool guard — `32a4587`, pushed
  `0ba8a5b..9bedc2e`, closed. `int(200.9)` truncation gap closed; bool/non-integral/non-finite
  float rejected; ints/integral-float/digit-str valid. APPROVE. Suite 1979 green.
- **#135** macro falsey/None unit-metadata relabel — `24d6a94`+`f1d6db6`, pushed `89d16cd..f764709`,
  closed. unit must be str (None + falsey-non-str rejected, '' placeholder kept); value_unit
  Optional. APPROVE after unit=None BLOCK. Suite 1967 green.
- **#134** macro descriptive metadata (indicator_code/name non-empty str, country_name str) —
  `69afb38`, pushed `f4ad9f5..89d16cd`, closed. APPROVE_WITH_NOTES.
- **Returned-metadata mini-batch — COMPLETE, pushed + closed (`f795bd1..a840e63`).**
  - **#69** `33007c6`+`831dd3f` — crypto quote-metadata consistency (quote_asset USD-equiv;
    price_unit accepts Binance quote-form OR Coinbase currency-form; volume_unit==base;
    provider_symbol canonical). APPROVE after B1(silent-skip)/B2(Coinbase USDC) re-review.
  - **#131+#132** `4548dcc` — macro projection_from_year span + frequency enum/date consistency.
    APPROVE.
  - **#133** `1e5bf85` — price exchange/provider_symbol non-empty canonical str. APPROVE.
  Suite 1933 green.
- **Failover metadata/inner-row batch — COMPLETE, pushed + closed (`f6b96da..f795bd1`).**
  - **#125-reopen** `7199a4f` — inner row/item object type checks. APPROVE.
  - **#129** `ae71706` — fundamentals fiscal_date plain-date. APPROVE.
  - **#127** `9e3e61f` — fetched_at_utc tz-aware UTC (shared helper). APPROVE_WITH_NOTES.
  - **#128** `1898a51` — warnings tuple[str,...] (shared helper). APPROVE_WITH_NOTES.
  - **#130** `046f1ba`+`65bb2c4` — fundamentals report metadata (is_bank/model_type/
    provider_symbol); model_type allow-listed to {1,2,3,101,102,103} after reviewer follow-up
    BLOCK (reopened then re-closed). APPROVE. Suite 1879 green.
- **#123–#126 failover returned-object guard cluster — COMPLETE, all pushed + closed.**
  - **#125** outer container type-check — `8226ab5`. APPROVE.
  - **#123** macro point-key plain-date — `ec7586c`. APPROVE.
  - **#124** price/crypto tz-aware + gold plain-date bar keys — `45ed0a8`. APPROVE.
  - **#126** failover provenance guard (all 6 domains incl. FX; engine `provenance_of` +
    total fundamentals extractor w/ tuple sentinel) — `21c225f..f6b96da`. APPROVE after
    B1(FX)/B2(strict)/B3(unhashable)/B4(marker-collision) hardening. Suite 1750 green.
- **#122** fundamentals failover malformed-LineItem guard — pushed `d7a2190..c2a6be0`, closed.
  Strict `_validate_line_item` (canonical item_code, str name, finite non-bool value, dup-code
  reject) + B1 padded-code fix. Reviewer APPROVE (review-202606191245). Suite 1663 green.
- Pushed reviewed seven-commit stack `6f4a8da..a8479fc` to origin/master.
- Closed **#112** (29e942a), **#94** (ff159f5), **#14** (a8479fc) as fixed.
- Closed external duplicate **PR #115** as superseded (code not run).
- **#87** closed by reviewer as fixed (4db0c74 / a8479fc).
- **#107 / #110** closed by reviewer/poller #59 as fixed (watermark 2026-06-19T03:01:44Z).
- **#113 / #114** strict timestamp guards — pushed `a8479fc..9de091b`, closed (c76756a, 797ccad).
  Reviewer APPROVE_WITH_NOTES (review-202606191010). Watermark 2026-06-19T03:11:37Z.
- **#116** BTMC malformed weight tokens — pushed `9de091b..d384006`, closed. Reviewer
  APPROVE_WITH_NOTES (review-202606191021). Watermark 2026-06-19T03:21:45Z.
  Future-hardening note (non-blocking): `_QTY` left boundary allows a digit glued to a letter
  (`ABC5 LUONG`); out of #116 scope, revisit if such names ever appear.
- **#117** BTMC same-ts dedup — pushed `d384006..22bb20c`, closed (5050468, 2366ff6). Reviewer
  APPROVE (re-review inline after BLOCK on missing regression tests). Watermark 03:33:22Z.
- **#118** BTMC `@row` index validation — pushed `22bb20c..d97ef89`, closed (d97ef89). Reviewer
  APPROVE_WITH_NOTES (review-202606191038). Watermark 03:39:55Z. BTMC cluster complete.
- **#72, #83, #69, #73, #74, #85, #86** failover-guard cluster — VERIFIED already fixed + tested
  on master (guard + passing regression tests cited per issue); closed, no code change needed.
  Watermark 03:43:17Z. Reporters had filed against older commits.
- **#70, #71, #76, #77, #78, #79, #82** failover remaining — VERIFIED already fixed + tested;
  closed with cited tests. Watermark 03:47:08Z.
- **#15, #22, #32, #35, #37** + **#41, #67, #75, #80, #81, #93, #97, #104, #109** source-adapter
  cluster — VERIFIED already fixed + tested; closed with cited tests. Open 43→12.
- **#111** VNDirect type-before-truthiness — pushed `481ccfd`, closed. APPROVE_WITH_NOTES.
- **#119** CafeF Success bool — pushed `0b524a2`, closed. APPROVE.
- **#121** VNDirect strict modelType — pushed `4e0c05f`+`d5b9e03`, closed. APPROVE (after whitespace BLOCK fix).
- **#120** UDF fractional volume — pushed `ee710ac`, closed. APPROVE_WITH_NOTES. Open 12→8.
- **#68** fmarket case-insensitive code dedup — pushed `ab706b2`, closed. APPROVE.
- **#26, #49, #65** test-only gaps (guards already present) — regression tests added in `f2fb711`,
  pushed, closed. APPROVE. Open 8→4.
- **#28** Vietcombank get_rates ISO-4217 code skip — `defae64`, closed. APPROVE.
- **#108** WB/IMF canonical year keys — `45601f1`, closed. APPROVE.
- **#21** WB/DBnomics response-identity (incl. malformed/blank BLOCK fix) — `e053153`+`e72a10a`,
  closed. APPROVE (after BLOCK fix).
- **#66** time-series duplicate observation keys (UDF/Stooq per-response; Binance/Coinbase
  per-page, pagination dedupe preserved) — `5ee2f71`, closed. APPROVE/GO.

## 🎉 Milestone: 43-issue backlog fully cleared (2026-06-19)

Open count 43 → 0 in one session. ~21 were verified already-fixed (closed with cited passing
tests, reviewer-validated); the rest were real TDD fixes (BTMC cluster #113/#114/#116/#117/#118;
then #111/#119/#121/#120/#68/#28/#108/#21/#66), each reviewer-approved and pushed to master.
