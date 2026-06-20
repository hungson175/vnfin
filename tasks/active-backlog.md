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

_Last synced: 2026-06-19 ~10:12 +07_

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
    - **#167** (poller triage review-202606201304): VN equity universe / symbol discovery — ACCEPT
      design-first core data primitive, likely high-value AFTER #157. No coder action now.
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

- **#157 fundamentals metrics — DESIGN REV2.6 — last 1-line fixed (design APPROVED-pending-verify); awaiting final re-review** (spec spec-202606201222). Rounds:
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

## Next / in-flight bugs (BEFORE large #157 implementation)

- **#168 — DONE (impl), INTEGRATED GREEN, AWAITING CODE REVIEW** (reviewer spec review-202606201318;
  fix sub-agent commit `53519ff`). Fail-loud price/index namespace guard shipped. **Integration verified
  ON MERGED TREE:** full suite **2842 passed** (+31), gate trio **68** (public-API snapshot UNCHANGED —
  guard uses a private instance flag `_reject_index_symbols`, not a ctor param), coverage **95%**,
  clean-room clean, diff clean. Smoke-verified: prices rejects indices (incl. alias UPCOMINDEX, sector
  VNFIN, case/ws) with 0 network; index_history rejects stocks + deny-only sector indices; FPT passes
  prices guard, VNINDEX passes index guard; liquidity inherits. New private `_contracts/index_registry.py`.
  **ONE judgment call for reviewer:** sector indices (VNCOND…VNUTI) are **deny-only** (rejected in
  prices) but **NOT allow-listed** in index_history (no per-symbol value-history test; doc says VPS
  serves them) — a later reviewer-gated 1-line expansion. Code-review BLOCK (review-202606201352):
  missing alias HNXUPCOMINDEX in price deny-list → FIXED `f7ab8f9` (deny-only + 5 zero-network
  regressions; suite 2847, snapshot unchanged, cov 95%). NEXT: reviewer re-review (range
  `b20b246..f7ab8f9`) → push+close #168 on APPROVE.

- **#168 (orig spec):** price/index namespaces must **fail loud on wrong asset type**, not silently
  return wrong-typed data:
  1. known index (`VNINDEX`/`VN30`) via `prices.history()` → raise (not VND security prices);
  2. known equity (`FPT`) via `indices.index_history()` → raise (not index points);
  3. liquidity (calls `prices.history`) **inherits** the price guard;
  4. TDD-first + boundary tests + document public behavior;
  5. NOT via broad provider pass-through / scraping / silent-warning-only.
  **Design nuance to settle first (discuss w/ reviewer):** indices are a CLOSED known set, equities
  are OPEN-ended → guard is asymmetric (index_history allow-lists known indices; prices.history
  deny-lists known indices; unknown symbols still pass to price providers). Investigate existing
  known-index registry / symbol classifier in `vnfin/indices/` + `_contracts` before coding.
  Sequencing: do AFTER the tiny #157 rev2.4 design patch, BEFORE #157 implementation.
  **STATUS:** design **APPROVE_WITH_TWEAKS** (reviewer 13:25). Chokepoints: prices `client.py:138`;
  indices `indices/client.py:84`+`:115`; liquidity inherits (offline `from_price_history` + symbol-fetch
  via default_client). **Tweaks:** PRIVATE `_contracts` registry (NO public API/snapshot); **two sets** —
  deny-list (prices/liquidity) = ALL known index aliases incl. provider aliases (UPCOMINDEX, VNALL) +
  sector indices; allow-list (index_history) = only **value-history-SUPPORTED** indices (sector indices
  ONLY if current sources/tests prove support, else deny-in-price-but-not-allow-in-index). Seed:
  VNINDEX/VN30/VN100/VNMID/VNSML/VNALLSHARE(+VNALL)/HNXINDEX/HNX30/UPCOM(+UPCOMINDEX)/VNDIAMOND/
  VNFINLEAD/VNFINSELECT. Zero-network TDD; liquidity inherits price guard only. **PROCEED with TDD
  now (#157 rev2.5 patch done).** → delegate to a sub-agent.

- **#171 — docs/diagnostics polish: world-gold opt-in Stooq path** (poller triage review-202606201355).
  In-scope docs/enhancement; PARKED behind #168/#169/#157. Make the opt-in Stooq path unambiguous —
  either expose a supported factory OR update diagnostics suggested_actions + docs/api.md with exact
  manual opt-in (`StooqGoldSource` + `default_world_gold_client`). Do NOT add Stooq to the default chain.
- **#170 — design-first: domestic VN gold history / diagnostics** (poller triage review-202606201348).
  In-scope; PARKED behind #168/#169/#157. NO implementation without a source/legal/provenance design.
- **#169 — HIGH data-coverage BUG: crypto long-window partial coverage — DESIGN APPROVED (option B)**
  (spec review-202606201334; design choice review-202606201356). Queue AFTER #168 closes, BEFORE large
  #157 impl. **Approved contract:** failover-first; full-coverage = `first_bar.date<=start AND
  last_bar.date>=end`; partial primary → reject → backup; if a backup fully covers → select it; if NONE
  covers → return **best-available** (maximize covered requested-day overlap, then source order) + an
  exact `partial_coverage` warning constant naming requested start/end + returned first/last dates;
  no coverage check when start/end unset; retain identity/unit/value guards. Zero-network synthetic TDD
  (short-prefix primary + full backup; both-partial; prefix+suffix gaps; full unchanged; unbounded
  unchanged). No new provider/scraping; no explain_crypto_coverage in this slice. → delegate TDD after #168. Crypto daily history must
  not silently accept a primary-source result whose returned window starts after requested `start` /
  ends before requested `end`:
  1. client/failover-level requested-window coverage validation for crypto daily history;
  2. partial primary prefix/suffix → fail over to backup;
  3. backup covering the window → select it;
  4. no source covers it → NOT a silent full-success — either explicit coverage warnings/diagnostics
     by contract OR fail-closed typed error (**design decision — quick design-check w/ reviewer first**);
  5. TDD synthetic sources incl. short-prefix primary + full-window backup;
  6. no scraping / unreviewed providers.
  Crypto domain (`vnfin/crypto/`), independent of #168 (prices/indices). Likely a small design-check
  before coding (option 4 contract choice).

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

- #69: `quote_asset=None` + a normalized (currency-form) `price_unit` is currently accepted;
  a stricter "quote_asset mandatory" policy would be a separate follow-up (reviewer note 14:21).
- #130: `model_type` allow-list is fixed to {1,2,3,101,102,103}; widen only if an official set is documented.
- #133: no accepted-exchange set / provider_symbol contradiction rule yet (deferred until a
  provider-symbol mapping is defined).
- #116: `_QTY` left boundary allows a digit glued to a letter (`ABC5 LUONG`) — revisit if such names appear.
- #124: crypto bar `time` checked tz-aware only, not exact UTC offset — future tightening.

## Done today (trim periodically)

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
