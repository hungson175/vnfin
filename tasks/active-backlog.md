# vnfin-oss — Active Backlog

Operating discipline (Boss 2026-06-19): git history is the progress tracker (commit often);
every reviewer/poller task lands here FIRST, then is processed and removed/marked done with a
commit/issue ref. See `/tmp/vnfin-operating-protocol-202606190959.md`.

Goal (Boss standing directive, active 2026-06-21): **RESOLVE ALL GITHUB ISSUES** with
vnfin-oss-reviewer — discuss + resolve autonomously, don't stop. Batch-flow active (cluster +
fan out + integrate on merged tree). Refactor-first pause (2026-06-19) is LIFTED.

Flow per item: design → discuss+converge with reviewer → TDD red-first → green (full suite +
public-API + docs-contract + cov ≥85%) → commit → reviewer code review → push to master →
close issue → advance watermark → mark Done here.

_Last synced: 2026-07-20 +07_

> **🔵 NOW (active 2026-07-20): #198 corporate fundamentals P0 — inverted balance/income routing +
> broken catalog + pagination truncation — DESIGN-NOTE-FIRST, no code yet.**
> Reviewer-routed intake, external GitHub issue (not a PR, no reporter code run); reviewer **ACCEPT
> P0** + upgraded scope from "2 missing codes" to a systemic-correctness repair
> (`~/tools/vnfin-oss-reviewer/reviews/triage-202607202156-issue198-corporate-fundamentals.md`,
> reviewer commit `d794c71`). Root cause: `vndirect.py:_CORP_MODEL` routes corporate
> `INCOME→modelType 1`/`BALANCE→modelType 2` — **inverted** (1=balance, 2=income); AND the corporate
> `itemcodes.py`/`metric_api.py` catalog codes (25000/30000/40000/20000/21000/etc.) **do not exist**
> in real provider data at all — the catalog was never derived from a live query. Some current
> "AVAILABLE" values are silently a DIFFERENT statement's number under the wrong label — more
> dangerous than reported MISSING. Separately: single-page tall-row fetch (`size=limit*80`, no
> `page`/`totalPages` follow) silently truncates a wide fiscal period (live-reproduced: VIC's 142-item
> newest annual balance drops to 80, losing `14000`/owners' equity with no warning).
> **Live-probed 2026-07-20 (FPT/VIC/HPG/VNM, clean-room, no VNStock) — every identity below holds to
> the EXACT VND:** balance `13000+14000==12700` (6 ticker/period combos); income
> `21001-22100==23100` (gross profit), `23800-22070==23003` (PBT-tax=PAT total),
> `23000+23500==23003` (parent+NCI=total — **independently corroborates** the reviewer's
> flagged-open `23000` candidate as CONFIRMED parent-PAT). Bonus find: cashflow `37000` (not the
> catalog's `35000`) exactly matches balance `11100` (cash) — `CASH_END_OF_PERIOD` is ALSO
> mismapped, a second independent defect. New pagination finding (not in reviewer's packet): page
> ≥2's envelope OMITS `totalElements`/`totalPages` entirely (only page 1 carries them) — the fix must
> cache page-1's `totalPages`, not re-read it every page. Reproduced live via the adapter itself:
> `scripts/probe_corporate_itemcodes.py` (`VNFIN_LIVE=1`) FAILS on current `master` by design (proves
> both bugs at once); must flip to PASS post-fix (regression check).
> **Design/evidence note committed:** `tasks/198-design-note.md` + companion
> `docs/design/corporate-itemcodes-probe-20260720.md` + probe script
> `scripts/probe_corporate_itemcodes.py`. Proposes: atomic `_CORP_MODEL` swap (balance=1/income=2,
> cashflow=3 unchanged, no aliasing); full corporate balance+income catalog replacement (HIGH-confidence
> codes only — 12700/13000/14000/11000/13100/13300/11100 balance, 21001/23100/23800/23003/23000
> income); `OPERATING_PROFIT` → unmapped (no closing identity found, never guess); bounded multi-page
> pagination loop (stop on first row of fiscal-date `limit+1`, or provider-declared final page;
> fail-closed on any transport/schema error mid-pagination; reuses existing per-date duplicate-itemCode
> guard, no new dup-check needed). **4 open gate questions for the reviewer** (§7 of the design note):
> Q1 operating-profit unmapped-vs-guess, Q2 `NET_INCOME`(total,23003) vs `NET_INCOME_PARENT`(23000)
> asymmetry confirm, Q3 corporate cashflow headline codes (31000/32000/33000/34000) unverified —
> descope to a non-blocking follow-up (mirrors #157 Q3 bank-cashflow-fully-raw precedent) except the
> proven `CASH_END_OF_PERIOD` fix, Q4 sub-line display names (11200-11500) MEDIUM-confidence via
> aggregate-sum proof only. **STATUS (2026-07-21):** first design gate BLOCKED
> (`gate-202607202233-issue198-design-note.md`, reviewer `0345fcc`, revisions B1–B10). **Revised +
> recommitted `aa17412`** (design/evidence only, no package code) and **RE-GATE requested**: exact-VND
> matrix (integer residual 0) + official-filing cross-check per code (FPT FY2025 PwC full 22-code
> matrix incl. cash-flow section labels; VIC FY2024 EY parent/NCI neg-split); BLOCKED-not-guess
> unmapped contract (B2); full cash-flow audit operating=32000/investing=33000/financing=34000/
> net-change=35000/end-cash=37000 (B4); enumerated name-map, sub-lines left raw (B5); finite
> validated pagination loop (B6/B7); empty-page≥2→InvalidData through AUTO (B8); relational
> (statement,is_bank,model_type) tuple guard (B9); 3-leg probe rewrite (B10). Q1–Q4 resolved per
> reviewer rulings. **Round-2 gate also BLOCKED** (`gate-202607212049-issue198-regate-round2.md`,
> reviewer `bf60ecb`, R1–R7: executable failure paths). **Revised again → `20041cb`, RE-GATE
> (round 3) requested:** R1 empty-page at the real `_rows()` EmptyData seam; R2 source-aware tuple
> guard (VNDirect-stmt≠None, non-VNDirect=None); R3 defined pagination helpers + missing-key→
> InvalidData; R4 23-code map incl `12000` + all-4 FY2024 balance (8 checks); R5 probe LEG B
> tuple-assert + LEG C raw newest-date oracle (no 142 magic) + all-tickers; R6 five derived metrics
> pinned; R7 FPT matrix re-read directly from the official PwC PDF. **Round-3 gate also BLOCKED**
> (`gate-202607212112-issue198-regate-round3.md`, reviewer `9e74f50`, R8–R10 + strict-int: 3
> completeness-proof defects). **Revised again → `80808c9`, RE-GATE (round 4):** R8 shared
> `_row_eligible` pre-count (builder-skipped rows can't prove completeness); R9 LEG C finite/validated/
> fail-closed raw oracle w/ exact `Decimal` compare; R10 LEG A requires 2 balance periods; strict
> non-bool int prefilter before the tuple guard. **Round-4 gate also BLOCKED**
> (`gate-202607212126-issue198-regate-round4.md`, reviewer `f20f457`, R11–R13). **Revised again →
> `b22f8a6`, RE-GATE (round 5):** R11 AUTO detects template from raw rows + paginates under DETECTED
> model (no candidate-relative erase of model-102 rows); R12 two-state validation (all-row vs
> eligible-boundary) + structured `_row_disposition`, NO keep-filter (builder keeps skip-warning/
> all-dropped InvalidData/cap); R13 oracle whole-stream date validation + raw-int totalPages +
> Decimal/fail-closed >2^53, LEG A narrowed to identity-bearing. **Round-5 gate also BLOCKED**
> (`gate-202607212143-issue198-regate-round5.md`, reviewer `49d4e9b`, R14–R16). **Revised again →
> `82ea1c7`, RE-GATE (round 6):** R14 AUTO ONE atomic query (restart page1 under detected model, ≤1
> redirect, no cross-query stitch, call-sequence assertion); R15 SKIP_CODE bumps both skipped_rows+
> code_mismatches (mixed warning + all-dropped precedence); R16 probe fail-closed on non-integral/
> abs>=2^53 both signs + real-calendar parse (2025-99-99 reject) + raw identity match + fetched-prefix
> claim. **Round-6 gate also BLOCKED** (`gate-202607212156-issue198-regate-round6.md`, reviewer
> `c9855e3`, R17–R18). **Revised again → `65948e9`, RE-GATE (round 7):** R17 AUTO exact-model
> detection (_dominant_model restricted to statement's valid {corp,bank} models; redirect-once;
> restart validates exact tag; tag-less/101/contradictory/empty restart → InvalidData; seed page1
> once; exact fetch-seq + mixed-warning pinned); R18 probe strict Decimal-aware _canonical_int
> (modelType 1.9/True + itemCode 11000.9 no longer false-pass). **Round-7 gate also BLOCKED**
> (`gate-202607212207-issue198-regate-round7.md`, reviewer `091f237`, R19–R20). **Revised again →
> `2805ec0`, RE-GATE (round 8):** R19 explicit `page1_envelope` seed re-validated identically +
> fresh-state redirect + `_dominant_model` fails on out-of-VALID minority tag & corporate/bank tie;
> R20 runtime `_require_item_code` reuses `canonical_provider_key` (no str(int)); evidence wording
> fixed (LEG A + pre-fix B/C observed). Probe green (LEG A PASS, B/C pre-fix FAIL, exit 2 offline).
> NO code/tests changed; do not build until GATE PASS. **7 gate rounds; mappings/evidence settled
> since round 2 — deltas now micro-seams in pagination/AUTO/probe edge-handling.**
> **✅ DESIGN GATE PASS 2026-07-21 on `2805ec0`** (`gate-202607212217-issue198-design-pass.md`,
> reviewer `cfec0ef`) — RED-first package implementation AUTHORIZED against the accumulated spec
> `tasks/198-design-note.md`. Mandatory code-review inclusions: focused pagination/AUTO/tuple/catalog/
> metric tests; full offline + warning-token/docs/public-surface gates; deterministic probe unit seams
> + opt-in live post-fix 3-leg PASS; CHANGELOG/API/tutorial/AI-skill/mapping/provenance docs lockstep;
> merged-tree diff/secrets/blacklist/package checks. Duplicate invariant covers every fetched row; NO
> extra fetch for the dropped limit+1 boundary. No ROE/app-helpers/redistribution/unrelated-refactor.
> **NO push/close until implementation-review APPROVE.**
> **✅ IMPLEMENTATION COMPLETE + merged-tree-verified — CODE REVIEW REQUESTED.** Range
> `2ec1421..f94f945` (P1 data `fd1f24e`+`f97e113`, P2 pagination/AUTO `133e8d7`, P3 docs `f94f945`).
> Full offline suite **3907 passed**; warning-token/docs/public-surface/blacklist/no-secrets gates
> green; public_api snapshot NOT regenerated. **Live post-fix probe 3-leg PASS** (routing + 142-item
> complete pagination proven live). Handoff: `/tmp/.../scratchpad/198-impl-review-handoff.md`. Awaiting
> reviewer APPROVE; then push to master (no PR — maintainer own-fix) + close #198 (reviewer owns the
> watermark).
> **Impl-review round 1 BLOCK** (`review-202607212322`, `753eaa4`, B1–B4: evidence/tests/docs
> completeness — runtime ACCEPTED). **Corrected → range `c3c5677..f76c33a`, RE-REVIEW REQUESTED:**
> B1 offline `tests/test_probe_seams.py` (35) + post-fix evidence wording + durable §5 live receipt
> (`f76c33a`, SHA 466c11a, 3-leg PASS); B2 pagination/CF/23-name pins (80+62→142, dropped-boundary dup,
> ineligible reappearance, 2nd CF identity 35000+36000+36100==37000, independent 23-name pin); B3 doc
> lockstep incl ai-usage bank-balance 101 + BLOCKED tutorial + vndirect docstrings; B4 durable RED-first
> (c3da29c 2 docs-contract tests RED → 6a1941a GREEN). Merged-tree: **3951 passed**, wheel builds,
> gates green, vndirect change docstring-only. Handoff `/tmp/.../scratchpad/198-correction-handoff.md`.
> No push/close pending APPROVE.
>
> **✅ DONE 2026-07-02: #197 main CN/KR/HK world indices as loudly-labeled USD ETF proxies — PUSHED + CLOSED.**
> Boss/reviewer-routed intake; design note `tasks/197-design-note.md` (`8b981bb`) GATE PASS
> (`gate-202607021733-issue197-design-note.md`). Build `8c5676e` pushed to `master` (`d3ba214..8c5676e`) and #197
> CLOSED (comment `#issuecomment-4864919431`). Added canonical-only `^KS11`→EWY, `^CSI300`→ASHR, `^HSI`→EWH
> as USD ETF proxies; no aliases, no TOPIX duplicate. Existing 5 specs byte-identical; SPY/QQQ still no proxy warning;
> unsupported `^DAX`/`^FTSE` reject before network, never SPY/Stooq `^SPX`. Reused existing `proxy_substitution` token
> (NO new warning token); each proxy carries `proxy_for` + `value_unit` + FX-pair disclosure. Docs/SKILL/CHANGELOG/source
> coverage updated to 8 symbols. Full suite green; Codex×2 APPROVE
> (`review-202607021747-issue197-codex2-APPROVE.md`). Clean-room: zero VNStock-derived material. Optional non-blocking:
> cosmetic `Index index` warning wording polish for `^STI`/`^HSI`; handoff wording note only.

> **✅ DONE 2026-06-25: #196 public ANNUAL precious-metals history (silver + platinum, USD/oz) — PUSHED + CLOSED.**
> Reporter `hungle03111987` (3rd-party; reviewer-ACCEPTED). New public `vnfin/metals/` domain serving annual
> silver+platinum USD/oz from the EXISTING World Bank CMO "Pink Sheet" (`Annual Prices (Nominal)` sheet, CC-BY 4.0).
> Shared xlsx parser EXTRACTED to `_contracts/worldbank_cmo.py` (gold output byte-identical + value-identity pinned);
> NEW frozen `MetalBar`/`MetalHistory` carry `frequency="annual"` + CC-BY `attribution` as TYPED fields → NO new warning
> token (#180 stays 49). Evidence-based bands: Au [20,10000] UNCHANGED, Ag [0.10,75.0], Pt [50,5000]. Never-fabricate:
> unsupported metal → InvalidData naming it BEFORE network; `metals.history("gold")` → InvalidData routing to `vnfin.gold`;
> dup-header ambiguity → InvalidData. Design GATE PASS + adversarial-verify Workflow `wf_e3ddaf5a-b2e` (6 lenses; Finding A
> dup-header FIXED `ef17999`, Finding B fetched_at_utc reviewer-ruled KEEP now()) + **Codex×2 APPROVE**
> (`reviews/review-202606251718-issue196-codex2-APPROVE.md`). **PUSHED `963d2c2..83ad886` to master; closed #196**
> (comment `#issuecomment-4798215571`). Commits: 5d39f3f/817d04a/57609b3/248fc57/ef17999.
>
> **Follow-up candidates from #196 Codex×2 (non-blocking; NOT yet filed — reviewer/Boss to triage, do NOT auto-file):**
> (1) integrity-vs-availability: dup-header/band rejections surface as `SourceUnavailable` (availability) not `InvalidData`
>     (data-integrity) at the public layer — gold-symmetric. (2) `to_dataframe().attrs` omits `fetched_at_utc` (both gold +
>     metals). (3) gold band fully overlaps platinum → only the split-header name-match defends platinum from a gold
>     mis-column (accepted as-is). RELEASE task: regen public-API surface baseline (`scripts/dump_api_surface.py`) —
>     escalate to Boss at release.
>
> **✅ DONE 2026-06-25: #195 `vnfin.equities` GICS sector classification (PUSHED + CLOSED).**
> Reviewer-routed intake; **triage = ACCEPTED, source CONFIRMED clean** (spec `/tmp/spec-195.md` + reviewer
> reviews/). **CLEAN-ROOM CRITICAL:** derive GICS sector by fetching the 10 VNAllShare sector-index baskets we
> ALREADY fetch (`index_registry.py:84+`, `IndexConstituentsSource.get_constituents`) and **inverting membership**
> (symbol→sector). **ZERO vnstock**; do NOT adopt its `industryID`/`industryIDv2`/Vietnamese `industry_name` — the
> issue's source suggestion is BLACKLISTED. Field shape: `sector_code`/`sector_name` (GICS English)/`sector_scheme`
> ="GICS"/`sector_source`="ssi_iboard_query". GICS map: VNFIN=Financials, VNIT=Information Technology, VNREAL=Real
> Estate, VNMAT=Materials, VNCONS=Consumer Staples, VNCOND=Consumer Discretionary, VNIND=Industrials, VNENE=Energy,
> VNHEAL=Health Care, VNUTI=Utilities. **HONEST-COVERAGE core invariant:** HOSE-only ~74% (~297/403); unmapped
> HOSE + ALL HNX/UPCoM → `None` + NEW `sector_partial_coverage` warning (full #180/#188 token lockstep), NEVER a
> fabricated sector; two-basket symbol handled deterministically + flagged. **v1 surface = GICS L1 ONLY**: enrich
> EquitySecurity/universe (additive→snapshot-safe) + `profile()`/`sectors()`/`by_sector(code_or_name)`; **NO
> industries() tier** (no clean finer data); `industry_peers` composes over by_sector (DEFER). **STATUS
(2026-06-25 01:38):** intake → Explore-mapped → design note `tasks/195-design-note.md` (`fdf7393`; fact-checked:
constituents path has NO allow-list gate, tuple=48, surface additive-safe) → reviewer **GATE APPROVED**
(`gate-202606250135-issue195-design-note.md`; all 3 RECs ratified: Q1 opt-in `with_sector`, Q2 overlap fold under
prefix, Q3 6h lazy cache) → binding build spec `tasks/195-build-spec.md` (`5cfbbcc`, 10-case matrix) → **fresh
general-purpose agent BUILT @ `3fe21bd` (3713 green; merged-tree verified by me: snapshot byte-identical, tuple=49,
no vnstock)** → **adversarial-verify Workflow `wf_9b83088f-8a9` (5 fresh skeptics) found 1 CONFIRMED major
silent-gap:** `profile()` serves a mapped sector but returns a bare `EquitySecurity` (NO `.warnings`) → never-silent
contract broken on the single-symbol entry point; violates gate-approved matrix case-5 + design-note L91 + SKILL.md
L164 + docs/api.md:351-355 (4 surfaces); masking test `..._with_coverage_token` asserts NO token (green-blind). Other
4 skeptics: 0 defects. **Reviewer RULED a1** (`gate-202606250208-issue195-profile-gap.md`): new frozen
`EquityProfile(security, warnings)` wrapper (matches result-carries-warnings convention; reject a3/b). Fix-spec
`tasks/195-fix-spec.md` (`7db6798`, locked to a1) → fresh-agent TDD (rewrote masking test to assert the token RED-first +
added overlap-profile test) → **integrated + committed @ `91d1bdc`**; merged-tree verified by me (suite exit0, tuple=49,
snapshot byte-identical, #180/#188 bijection, no vnstock) → **adversarial re-verify Workflow `wf_8a360ee5-acc` (3 lenses,
real probes) = CLEAN, 0 defects** → **routed to Codex×2** (handoff `/tmp/195-codereview-handoff-20260625.md`; flagged the
`cross_board_duplicate` deviation as review-focus) → **reviewer Codex×2 = APPROVE** (`review-202606250230-issue195-codex2-
APPROVE.md`; 0 blockers; REVIEW-FOCUS profile sector-scoped ACCEPTED as-is; 3 optional non-blocking notes) → **PUSHED to
master `5b5318d`** (feature `3fe21bd` + a1 fix `91d1bdc`, 10-commit fast-forward, no private-path leak, suite exit0) →
**#195 CLOSED completed** (public scope comment: v1 = GICS L1 only; finer industry/sub-industry tier deferred = no
clean-room finer source). RELEASE follow-up (NOT now): regen the public-API surface baseline (`scripts/dump_api_surface.py`).
state/ left to the reviewer (owns watermark).
>
> **✅ DONE 2026-06-24: #194 `funds.nav_history` aborts whole series on one conflicting navDate — port the #186 quarantine.**
> Reviewer-routed poller intake; **triage = ACCEPTED** (trusted vf-advisor↔vnfin reporter, clean repro, no
> untrusted code). Real degrade-not-fabricate / never-silent defect: `funds.source().nav_history()` hard-raises
> `InvalidData` on ONE conflicting `navDate` (`vnfin/funds/fmarket.py:356-373`, the #158 hard-raise) → nukes a
> fund's whole multi-year series; **21/65 VN funds lose all NAV** over one bad date (repro `nav_history(21)` VFF
> 2018-07-31 / 2017-01-31). Fix = **port the #186 VN-Index quarantine** to the Fmarket NAV parser: conflicting
> navDate → quarantine the date + never-silent warning + return the rest; identical-dup → dedup keep-first;
> **threshold guard preserved** (`max(_QUARANTINE_ABS_FLOOR, _QUARANTINE_FRACTION×n)` → systematically-broken
> still raises); **NEVER average**. **DESIGN-NOTE-FIRST → reviewer gate before any code.** 3 gate questions
> (my recs after fact-check, some DIVERGE from triage lean): (1) keep policy — **DROP-the-date (#186 mirror,
> firm rec)**; (2) token — **NEW `quarantined_conflicting_navdates` (DIVERGE from triage's reuse lean)**
> because the existing token says `..._bars` but `NavHistory` has `points` (name/scope honesty wart) + funds
> already has a `nav_`/`deduped_duplicate_nav_rows` token family — this is the ONE open gate call; (3) threshold
> — **reuse `_QUARANTINE_FRACTION=0.10`/`_QUARANTINE_ABS_FLOOR=3` UNCHANGED but count each conflicting DATE once
> (not #186's `+2` rows)** → ≤3 conflicts always serve, solves the short-series worry without a magic floor
> (NB: fmarket NAV is DAILY per the parser docstring, not monthly — cadence varies by issuer). Tests (8):
> one-conflict→rest+warning (not raise); systematically-conflicting→still raises; threshold boundary 3-serves/
> 4-raises; identical-dup→dedup unchanged; never-averages; 2-dates-under-threshold; conflict-vs-dedup
> precedence; #172 empty/stale unchanged. Offline synthetic fixtures only, zero VNStock. NavHistory.warnings
> already defaulted + in frozen snapshot → NO surface change. **✅ DONE 2026-06-24:** design GATED→APPROVED
> (Q2 divergence RATIFIED) → fresh-agent TDD build (8-case RED-first + 2 inverted #158 tests) → integrated
> `4228242` (merged tree **3690 green**, docs-contract 35, tuple 47→48, snapshot frozen, no contamination) →
> adversarial-verify Workflow (5 skeptics×distinct lenses, all RAN repros) **0 defects** → reviewer Codex×2
> **APPROVE** (`review-202606241615-issue194-codex2-APPROVE.md`, 0 blockers + 2 optional cosmetic notes) →
> pushed master + closed #194. Cosmetic note 1 (StaleData-reachability test comment) = follow-up.
>
> **✅ DONE TODAY (2026-06-24): #193 `vnfin.indices.world` — world-index coverage + keyless-from-server reliability.**
> Design note `tasks/193-world-index-design.md` (`9c219b2`, fact-checked clean) **GATED → APPROVED to TDD**
> (gate `~/tools/vnfin-oss-reviewer/reviews/gate-202606241410-issue193-design-note.md`). Probe verdict: NO
> keyless-from-server source (Yahoo 429 / Stooq JS-wall) → AlphaVantage BYOK is the only server source.
> **Gate rulings (binding):** Q1 ship all 5 (SPY,QQQ direct + labeled USD ETF proxies EWJ/FXI/EWS for
> ^N225/^SSEC/^STI); Q2 `proxy_for` field MUST-HAVE + `proxy_substitution` token (both); Q3 DEFER
> `adjusted_close`, document price-return-not-total-return; Q4 synthetic http_get injection = VCR; Q5 hard
> guard InvalidData-naming-symbol on empty AV; MissingKey(no-key) vs AllSourcesFailed(key-set-fail) cleanly
> branched; token sweep 46→47; snapshot frozen. **Build spec:** `tasks/193-build-spec.md`.
> Build `c79325a` (green merged tree) → **Codex×2 round-1 = BLOCK**
> (`review-202606241450-issue193-codex2-verdict-BLOCK.md`): AV-only paths + all gate housekeeping CORRECT; 3
> blockers in the Stooq-fallback + client-reuse seam — **B1** Stooq `^SPX`-pinned for ANY symbol →
> `world(^N225)`+working-Stooq returns S&P500 relabeled (silent wrong-MARKET, violates Q2); **B2** proxy
> empty-window → EmptyData fallover to `^SPX` bypassing Q5; **B3** `FailoverWorldIndexClient` concurrency-unsafe
> (mutable `_requested_symbol`) + public + 6h cache incentivizes reuse. **Fix spec:** `tasks/193-fix-spec-round2.md`
> — gate Stooq SPY-only + stateless closures (thread symbol through `engine.run`) + non-SPY-working-Stooq /
> empty-window / stateless tests, ONE commit, SPY unchanged.
> **STATUS: ✅ DONE + PUSHED + CLOSED (2026-06-24).** Round-2 fix `3ad1a3a` (B1 Stooq SPY-only via
> `supports()`==SPY + defense-in-depth `InvalidData` refuse + spec-not-payload labeling; B2 empty-window names
> symbol; B3 stateless — symbol threaded through `engine.run`, 0 `_requested_symbol`). **Codex×2 round-2 verdict
> = APPROVE** (`reviews/review-202606241510-issue193-round2-APPROVE.md`): all 3 blockers genuinely fixed +
> verified, no collateral break to the other 6 FailoverClient domains, housekeeping green (snapshot frozen,
> token 47, additive-only, zero VNStock). My 3-skeptic adversarial verify was CLEAN before handoff. **PUSHED
> `e0e37aa..e25151b`** (whole #193 series), **#193 CLOSED** (issuecomment-4787257540) with a public coverage +
> never-silent + keyless-MissingKey + thread-safe resolution comment. Watermark = reviewer's (NOT advanced).
> **NON-BLOCKING FAST-FOLLOW — ✅ DONE + PUSHED `5fe026f` (Codex×1 lead APPROVE 2026-06-24 15:23):** committed
> threaded/barrier-synced B3 concurrency stress test (1 shared client, 1 thread/symbol ×50 on a Barrier,
> asserts per-thread symbol+proxy_for+provider+distinct close). Mutation-verified load-bearing (stateful
> pre-#193 clone 19 bleeds/8 trials, stateless 0/8); 3× non-flaky; suite 3681; snapshot frozen; token 47.
> Pushed `4e4ded6..5fe026f`. Closes the round-2 non-blocking note. **#193 + fast-follow FULLY DONE.**

> **🚀 BATCH FLOW ACTIVE (Boss directive 2026-06-21 ~10:50):** cluster similar issues, fan out
> worktree sub-agents in PARALLEL, integrate + run integration tests on the MERGED tree, GO FAST
> (stop the serial one-issue crawl). Plan: `/tmp/vnfin-batch-plan-202606211040.md`.
> - **WAVE 1 — ✅ DONE + PUSHED + CLOSED (2026-06-21 ~11:2x):** #189 `board_unavailable` (equities),
>   #190 `fund_nav_stale` (funds), #191 test-harden #187 matrix, #192 def-use trace. Workflow
>   `wf_0493ba36-1dd` fanned out 4 parallel worktree builds; integrated linear cherry-pick onto `0870a37`
>   (`1d9dd25` #191 → `e3bd6ce` #192 → `bbb10c0` #189 → `21c39b9` #190) + backlog `f865f5a`. **Reviewer
>   BATCH VERDICT = APPROVE all 4** (4 parallel sub-agents, NO disagreement, ZERO blockers;
>   review-202606211112-wave1-batch-189-190-191-192; #191 gap-(B) reversal independently re-derived +
>   mutation-RAN by reviewer = CORRECT). **Pushed `60459ef..f865f5a`; all 4 closed w/ resolution
>   comments.** Merged-tree gate was ALL GREEN (3468 pass, forward-discovery 36==36, snapshot frozen).
>   2 non-blocking nits NOT actioned (would change approved SHAs): (a) #191 commit-msg says 34 not 36
>   cosmetic, file untouched so snapshot truly frozen; (b) #192 N1 shape-(c) helper-return convention.
>   Watermark left to reviewer.
> - **WAVE 2 — ACTIVE (scoping DONE; digest `tasks/wave2-scoping-summary.md`; one gate at a time).**
>   Scoping Workflow `wf_46081884-f22` (5 agents, VNStock-blacklist enforced) → durable digest committed.
>   **ROLE BOUNDARY:** source ToS-verdict is the REVIEWER's; my agents only surface candidate lists.
>   - **#175** — **✅ DONE + CLOSED** (both Codex×1 APPROVE). Tier-1 `current_snapshot_only` live
>     disclosure (`3d33859`) + Tier-3 diagnostic correction (`16d0042`) PUSHED (`60459ef..6282a5d`);
>     issue CLOSED as source-gap-documented for **Tier-2** (historical PIT membership: no clean
>     redistributable feed, HOSE = human PDFs) with 4 reopen criteria. Watermark = reviewer's.
>   - **#152** fixed-income — **✅ DONE + CLOSED** (Codex×1 APPROVE, zero blockers). `dc39cef` PUSHED
>     (`6282a5d..f3cd479`); issue closed. Extended `vnfin.macro` w/ lending/deposit/real (WB FR.INR.*) +
>     `explain_fixed_income_coverage`; yield CURVE deferred (no `vnfin.bonds`, reopen criteria in close
>     comment). Additive, snapshot frozen, NO new token (#180 stays 37), suite 3498. Watermark=reviewer's.
>   - **#163** dividends/corp-actions (Boss-decided BUILD) — **✅ DONE + PUSHED + CLOSED** (Codex×2
>     APPROVE_WITH_NOTES 2026-06-21, `reviews/review-202606211542-163-descope-codex-x2-APPROVE.md`;
>     `f3cd479..8e7df60` PUSHED; #163 CLOSED w/ de-scope resolution comment; 2 notes→v2 corpus.
>     Watermark=reviewer's). New `corp_actions` domain; VSDC HTML SCRAPE `GET https://vsd.vn/vi/ad/{id}` (seq id ~197000,
>     keyless: ticker/exch, record Ngày ĐKCC, pay Ngày thanh toán|Thời gian thực hiện, cash %+VND/sh; NO
>     ex-date); CASH-first v1; total-return DEFER v2. Spine built by fresh agent (`ec2b0d7` feat +
>     `197d9fd` docs vs spec `b37044a`). **Reviewer 2 MUST-ADDS folded in TDD-first (`1af8196`):** (1)
>     **single-hop → bounded multi-hop BFS** over the same-org "Tin cùng tổ chức" sidebar graph — visited-id
>     dedup + cycle guard (each page fetched ≤1×, terminates on loops), single fetch per page (no more
>     double-fetch). **⚠️ BEYOND literal ask — flag to reviewer:** the agent built single-hop (seed + its
>     direct sidebar), which silently under-covers deep history for any issuer w/ >1 sidebar of
>     announcements; BFS fixes that silent under-coverage. (2) 4th never-silent token
>     `coverage_truncated_at_max_fetch` (per-result) when the crawl stops at `max_fetch` with frontier
>     unexhausted. **4 tokens** (#180/#188 lockstep, gate on the SWEEP not count): `ex_date_unavailable`
>     (per-event) + `corp_action_source_partial` (per-result) + `vsdc_parse_degraded` (per-event) +
>     `coverage_truncated_at_max_fetch` (per-result). finfo ex-date leg HELD (Boss-nod+cassette).
>     **Adversarial self-verify Workflow `wf_0df9f8f1-718` found 4 REAL defects → all FIXED TDD-first
>     (next commit):** (a) **silent fetch-failure gap** — a same-org page raising `SourceError` dropped
>     its whole branch with no token (sibling equities discloses via `board_unavailable`) → NEW **5th
>     token `corp_action_fetch_incomplete`** (per-result, `: {n} page(s) skipped`); (b) **`max_fetch<=0`
>     silent empty** — early-return hard-coded `truncated=False` + param unvalidated → now `raise
>     InvalidData`; (c) **undated event silently dropped under a window** — record_date=None real cash
>     event vanished under any start/end → now windowed by `pay_date` fallback + flagged
>     `vsdc_parse_degraded` (degraded condition broadened to ≥1 missing PRIMARY field incl. record date);
>     (d) **ratio fabrication on a bundled un-split line** — first `%` (bonus) paired w/ cash amount → now
>     take the `%` CLOSEST BEFORE the cash parenthetical. Verify's other 2 lenses (cycle/termination +
>     doc-bijection/snapshot) confirmed CLEAN. **5 tokens now** (gate on the SWEEP not count). **GATES
>     GREEN on merged tree:** full suite 3533 pass, public-API snapshot additive-green (no regen), #180/#188
>     doc-contract green. 6 fail-first tests added (cycle/dedup + truncation + 4 verify fixes). Raw real
>     pages gitignored `tests/cassettes_private/`. 4 self-fixes committed `edd8011`; routed to Codex x2.
>     **REVIEWER VERDICT 2026-06-21: BLOCK** (`reviews/review-202606211309-163-vsdc-spine-codex-x2-BLOCK.md`,
>     in reviewer worktree) — 4 self-fixes GENUINE + 5-token lockstep clean + seeded-BFS solid, BUT 3 fresh
>     blockers (FIX PHASE, TDD-first, all in `vsdc.py`): **B1** `parse_announcement` is OUTSIDE the `_crawl`
>     `except SourceError` (line 414) + `_find_seed` (442); it raises `InvalidData` (not a `SourceError`) on
>     an empty/whitespace sibling body (219) or unresolvable ticker (237) → ONE bad sibling CRASHES the whole
>     `dividends()` → catch `(SourceError, InvalidData)` around parse in BOTH, count+disclose via
>     `corp_action_fetch_incomplete`. **B2 (heaviest re-pass)** cash loop captures only the FIRST parenthetical
>     → a MULTI-TRANCHE page SILENTLY DROPS the 2nd + an intervening `sau thuế 10%/cp` MIS-PAIRS ratio (10 not
>     12) = silent WRONG data → degrade-token when >1 cash paren + `Mệnh giá` par cross-check (cash≈ratio/100×par,
>     recovers gross 12) + reject `ratio_pct>100`. **NOTE-1 (pre-push must-fix)** no-seed `_find_seed`
>     window-miss returns EMPTY history indistinguishable from never-paid → NEW 6th token
>     `corp_action_seed_not_found` (or enforce seed_id); no-seed path currently UNTESTED. Fast-follows
>     (non-blocking, track later): seed-scan fetch failures uncounted; doubly-undated event dropped; no-seed
>     double-spend; `DividendHistory` no `__post_init__` token enforcement. **FIX PHASE DONE — AWAITING
>     RE-REVIEW** (`edc9898`): all 3 blockers fixed TDD-first (8 fail-first regressions #9.20a/#9.20–#9.26
>     incl. a COMBINED multi-tranche+sau-thué case for B2), 6th token `corp_action_seed_not_found` +
>     #180/#188 lockstep (baseline 42→43), parse moved INSIDE the try in `_crawl`+`_find_seed`, par
>     cross-check recovers gross ratio + reject>100 + degrade-on-ambiguity. Full suite **3541 green** on
>     merged tree, snapshot additive (no regen), doc-contract green. Routed to Codex x2 (handoff
>     `/tmp/vnfin-163-rereview-handoff-20260621.md`). **B1 mechanism correction surfaced to reviewer:
>     InvalidData IS a SourceError subtype — the real bug was parse OUTSIDE the try, conclusion/fix
>     unchanged.** **ROUND-2 BLOCK 2026-06-21** (`reviews/review-202606211334-...-BLOCK2.md`): B1+NOTE-1
>     VERIFIED FIXED, original B2 symptoms fixed, BUT a NEW same-class silent-wrong-data defect (D-REV:
>     dot-decimal ratio — `_parse_vn_number("8.5")==85.0`, `_RATIO_RE` accepts dot-decimal but parser
>     treats `.` as thousands → "8.5%" served as 85 on no-par real pages; par is ABSENT on real VSDC
>     pages so no-par IS the real path). My PARALLEL adversarial verifier found COMPLEMENTARY same-class
>     defects: D1 net-only-no-par serves NET, D2 net-cash, D3 alt-phrased tranche silent-drop, L1
>     twin-confirm (findings `/tmp/vnfin-163-b2-verifier-findings-20260621.md`). **UNION fix-2 spec
>     committed `0369b13` (`tasks/163-b2-fix2-spec.md`); impl DELEGATED to fresh agent TDD-first** (8
>     fail-first #9.27–#9.34): dot-decimal ratio parser + net-of-tax candidate exclusion + alt-tranche
>     count (`_CASH_MENTION_RE`) + cross-line degrade + par≥1000 guard + unique-confirm. ALL via existing
>     `vsdc_parse_degraded` (NO new token, tuple stays 43, NO snapshot regen). **FIX-2 INTEGRATED + GREEN**
>     (`c0f5f70`): impl applied verbatim per spec `0369b13`, my held `_crawl` except-comment fix folded in,
>     + reviewer-required NEGATIVE guards #9.35 (clean single gross still SERVES, not degraded) / #9.36
>     ('trước thuế' before-tax ≠ net marker). Both repro sets encoded green on merged tree (reviewer
>     8.5%-no-par #9.27/#9.28 + my D1/D2/D3/L1 #9.29–#9.34 + cross-line #9.33). Full suite **3551 green**,
>     tuple 43, snapshot clean. Routed round-3. **ROUND-3 BLOCK 2026-06-21**
>     (`reviews/review-202606211402-163-vsdc-rereview-BLOCK3.md`) — CONVERGENT with my parallel verifier:
>     round-3 fixes (dot-decimal/multi-tranche/cross-line/twins) VERIFIED good, BUT a 3rd silent-wrong-ratio
>     path survives (same class), 3 mechanisms: (1) `_NET_MARKERS` fragile 5-string allowlist misses canonical
>     tax phrasings (`khấu trừ thuế`/`đã trừ thuế`/`thuế TNCN`/`NET`/`ròng`; listed `sau khi tru thue` ≠
>     substring of `sau khi khau tru thue`); (2) PLACEMENT — net detection scans only text BEFORE each `%`, a
>     TRAILING marker (`12%/cp sau thuế (…)`) leaks (my verifier finding, empirically `11,4% sau thuế`→served
>     11.4); (3) WORST par-confirms-net — escaped net candidate still in `gross_cands` so par rubber-stamps it.
>     **FIX-3 SPEC `tasks/163-b2-fix3-spec.md`**: token-based `_segment_is_net` (word-boundary co-occurrence —
>     validated vs traps: `thực hiện`/`trước thuế`/`internet`/`trong` all correctly NOT-net) replacing the
>     allowlist + leading-gap/last-candidate-tail attribution + net excluded from `gross_cands` (→ from par).
>     Tests #9.37–#9.42 (incl. par-confirms-net + negative trailing-`trước thuế`). NO new token (tuple 43),
>     NO snapshot regen. NOTE fast-follows (out of scope): malformed `8.5.0%`→5.0; `/cp` in `_CASH_MENTION_RE`
>     not `_RATIO_RE`. **Reviewer 14:14 VALIDATED fix-3** (retracted blunt gap-list parts) + 2 edge flags:
>     (A) `trước thuế TNCN` would over-degrade a gross ratio; (B) bare `khấu trừ` (thuế omitted) missed-net.
>     Both FOLDED IN: `_segment_is_net` gets a before/not-yet/exempt override (`trước/chưa/không/miễn` win →
>     GROSS) + a bare `khấu`+`trừ` net rule; tests #9.43–#9.45. **ROUND-4 SUBMITTED — commit `ca2cce0`**
>     (base fix-3 by delegated agent + edges layered TDD-first by me). Merged-tree: 3560 passed, tuple 43,
>     snapshot clean, #9.35/#9.36/#9.42 no-over-degrade green. Handoff `/tmp/vnfin-163-round4-handoff-20260621.md`.
>     **ROUND-4 BLOCK 2026-06-21** (`reviews/review-202606211421-163-vsdc-rereview-BLOCK4.md`) — CONVERGENT
>     (I reproduced it before the verdict): the edge-A guard INTRODUCED an INVERSION — a segment-wide
>     `trước/chưa/không/miễn` token forced GROSS even when the before-word qualified an UNRELATED clause, so a
>     genuine net rate beside a stray before-word (`10% sau thuế (chưa gồm phí)` / `không gồm phí` / `miễn phí`
>     / `trước ngày`) was served as gross + par rubber-stamped it. Same silent-wrong class, GREEN-BUILD (matrix
>     lacked net-marker+stray-before). **ROUND-5 FIX — commit `6e2c71a`**: clause-scope restructure of
>     `_segment_is_net` — STRONG net markers (thực nhận/sau thuế/NET/ròng) win FIRST; before-veto fires ONLY
>     when adjacent ≤2 tokens to a tax token (`thuế/khấu/trừ/TNCN`); net excluded from `gross_cands` (par can't
>     rubber-stamp). Tests #9.46–#9.52 (6 stash-verified fail-first + 1 adjacency neg-guard). Merged-tree:
>     3567 passed, tuple 43, snapshot clean; #9.43/#9.45 legit-gross + #9.35/#9.36/#9.42 no-over-degrade green.
>     Handoff `/tmp/vnfin-163-round5-handoff-20260621.md`. **ROUND-5 BLOCK5 (convergent, 5th round)**:
>     `_TAXISH_TOKENS` included the fee verbs `khấu`/`trừ`, so a fee clause carrying a before-word
>     (`chưa khấu trừ phí`) vetoed a genuine `khấu trừ thuế` net → 10/12/8 served as gross. **ROUND-6 FIX —
>     commit `7b35066`**: before-veto target = TAX NOUN only `_TAX_NOUN_TOKENS={thue,tncn}` (verbs kept for
>     POSITIVE detection); window ≤2→≤4 so `chưa khấu trừ thuế`/`trước khi khấu trừ thuế` stay gross; bare
>     `không khấu trừ` now degrades (safe). Tests #9.53–#9.55 (3 fail-first on 6e2c71a). Merged-tree: 3570
>     passed, tuple 43, snapshot frozen; all must-stay-green + BLOCK4 inversions intact; 0 misclassified.
>     Handoff `/tmp/vnfin-163-round6-handoff-20260621.md`. **ROUND-6 BLOCK6 + reviewer DE-SCOPE call; my
>     parallel hunter independently found a 7TH silent-wrong path (net-first `8,5% sau thuế; 10%` + par → net
>     served as gross). DECISION 2026-06-21 14:53 — DE-SCOPE CONFIRMED (reviewer's call, Boss delegated):** the
>     free-text net-vs-gross classifier is open-ended NLP on scraped HTML (7 distinct silent-wrong bugs / 6
>     rounds) → STOP CLASSIFYING. v1 round-7 = DELETE `_segment_is_net` + all net/gross logic, replace with ONE
>     LINE-level gate: any thuế/thue/tncn token in the ratio context → `ratio_pct=None` + NEW token
>     `vsdc_ratio_tax_deferred` (semantic ≠ vsdc_parse_degraded; #180/#188 lockstep 43→44); ratio served ONLY
>     from a tax-free context. KEEP BFS/record/pay/cash_per_share/structured/NOTE-1/snapshot; clean
>     multi-candidate (par/twins/>100%/malformed) logic stays → still `vsdc_parse_degraded` (runs only on
>     tax-free text). Existing tax→served-gross tests INVERT to degraded (intended contract change). v2 =
>     classifier behind a committed corpus (the 7 phrasings + hunter safe-surface list = fixture seed).
>     `7b35066` push DROPPED (superseded). **ROUND-7 DE-SCOPE BUILT (`42fb7a7` spec → `47a688d` impl,
>     fresh agent TDD-first):** `_segment_is_net`+all net/gross classification DELETED; ONE line-level gate
>     `_line_has_tax_signal` → any tax/withholding signal on the ratio line ⇒ `ratio_pct=None` + NEW token
>     `vsdc_ratio_tax_deferred` (semantic ≠ vsdc_parse_degraded). #180/#188 lockstep 43→44. Tax→served-gross
>     tests INVERTED to deferred; corpus parametrized (`_TAX_DEFERRED_CORPUS` / `_CLEAN_SERVED_CORPUS`).
>     **My fresh-skeptic adversarial verify caught a REAL bar breach BEFORE reviewer handoff:** the gate
>     ({thuế,TNCN}|khấu-trừ) MISSED thuế-ELIDED net markers (`thực nhận`/`thực lĩnh`/`thực lãnh`/`ròng`/
>     `net`) → net % served as gross w/ no token + Defect-2 over-withhold (khấu-hao depreciation false-trip).
>     **FIXED `56cde90` TDD-first** (+5 fail-first withhold + 1 over-withhold guard): `_RATIO_NET_NOUNS`
>     adds ròng/net; `_RATIO_NET_BIGRAMS` catches net-received as ADJACENT bigrams (not set co-occurrence —
>     boilerplate 'thực hiện…được nhận' safe); 'khấu trừ' matched as the adjacent bigram only (kills
>     Defect-2). Bare 'đã trừ' w/o tax/net noun stays served (v2 corpus edge, documented). Merged-tree GREEN:
>     full suite **3584 passed**, tuple **44** unique, snapshot frozen. **2ND fresh-skeptic adversarial verify
>     on `56cde90` = CLEAN** (~50 inputs; all 15 real VN after-tax phrasings withheld; zero over-degrade FPs).
>     ONE LOW-realism residual `thực được nhận` (inserted `được` breaks the bigram; fixing re-breaks the
>     universal `thực hiện…được nhận` boilerplate → over-degrade every clean page) — NOT patched, DISCLOSED
>     to reviewer + tracked for v2 corpus. **CODEX×2 APPROVE_WITH_NOTES (2026-06-21): A=core invariant
>     0-wrong (22/24 attacks withheld, zero over-withhold); B=classifier genuinely deleted, token lockstep
>     44 distinct, spine intact, inverted-tests load-bearing, snapshot frozen, 3584 green. 2 NON-blocking
>     notes→v2 corpus (do NOT hold): N1 English after-tax (never on a VN gov depository; v2 fix=add `tax`
>     to noun set, 0-over-withhold, verified), N2 `thực được nhận` (serves gross correctly, cash-qualifier,
>     low realism). PUSHED `f3cd479..8e7df60` (whole `vnfin.corp_actions`) + #163 CLOSED.**
>   - **#182** gold domestic history — **✅ DONE + CLOSED** (reviewer ruled CLOSE-NOW-with-reopen-criteria
>     2026-06-21, #178 pattern; draft approved as-is, posted; no code change; world-reference gold line
>     stands; 4 reopen gates = the source-watch; giavangonline probe SKIPPED — fails reopen-crit #3 anyway).
>     Watermark=reviewer's.
>   - **#155** fund metadata — **✅ DONE + PUSHED + CLOSED** (2026-06-21). Codex x1 APPROVE (zero
>     blockers; report `reviews/review-202606211619-155-fund-metadata-approve.md`). Pushed
>     `bbed285..9ca0a96` (code `04d5e05..71c050b`); #155 CLOSED (issuecomment-4761515918). All 6 items:
>     Fund +3 optional (mgmt_fee/inception/description), `SectorWeight` (fail-closed, NO new request),
>     `include_metadata=True`, `explain_fund_coverage()`, 2 tokens (44→46 bijection green), docs lockstep.
>     32 fail-first TDD; suite 3637 green; snapshot frozen. Watermark=reviewer's.
>   - Reviewer's W2 gate order: #152 ✅ / #163 ✅ / #182 ✅ / #155 ✅ — **ALL CLOSED.**
>
> ### 🎉 BACKLOG FULLY CLEARED (2026-06-21) — 0 open issues on `hungson175/vnfin`.
> All GitHub issues resolved (#152/#163/#182/#155 + prior). Standing goal "resolve all issues on
> github" satisfied. Next work = poller-surfaced new issues (reviewer-routed) only.
>
> **#188 forward-discovery guard — ✅ DONE + PUSHED + CLOSED** (`ae7829d..60459ef`; Codex×1 APPROVE +
> 1 doc-comment must-fix folded). AST forward-discovers emitted `.warnings` tokens, asserts
> `code-emits ⊆ documented`. Test-only; tuple stays 34; snapshot frozen. Known limitation (warns/
> note/dup_notes accumulators) → #192. Worktrees pruned; only master remains.

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
> **#174 sector-index routing BUG — ✅ DONE + PUSHED + CLOSED.** Pushed master `21f47cd..17b3f5d`;
> #174 commented + CLOSED. Reviewer LEAD review APPROVE, no must-fix (review-202606210145).
> `_unservable_index_error()` branches on `is_known_index()` at BOTH `index_history` +
> `index_history_stitched` — recognised-but-unservable index → terminal diagnostic (no
> prices.history/for-stocks, loop broken), unknown/equity → unchanged route-to-prices. No registry-set
> change; routing-regression matrix locked to the registry diff (19 deny-only ids) so a future set edit
> can't re-open the loop. Full suite **3260 green**. Close comment carries the tracked-enhancement note
> (serving sector-index HISTORY = separate feature needing a clean source + per-symbol tests).
> Watermark/state left to reviewer.
>
> **#183 optional interval/resample — ✅ DONE + PUSHED + CLOSED.** Pushed master `17b3f5d..9f660df`
> (design notes `0bb59cd`/`6e03048` + feat `c6e8a23` + must-fix `7c5ec2c` + backlog); #183 commented +
> CLOSED (completed). `prices.history` + `index_history` take optional `interval` (Interval member OR
> pandas alias `'D'/'W'/'M'/'Q'/'Y'`); `W1/MN1/Q1/Y1` resampled CLIENT-SIDE from D1 (OHLC/period, bar=
> last actual trading day); `Interval.Q1="1Q"`/`Y1="1Y"` additive. Codex×2 = APPROVE_WITH_NOTES + ONE
> must-fix (reviewer's owned gate miss): original code hardcoded fetch=D1 + rejected intraday pre-fetch
> → silently broke existing native-intraday callers. **Must-fix `7c5ec2c`:** resample ONLY W1/MN1/Q1/Y1
> from `fetch(D1)`; D1+intraday → `fetch(interval)` native passthrough for BOTH prices AND index (source
> `supports()` the only reject) → truly additive. **My factual correction confirmed by reviewer:** index
> sources inherit intraday (`_IndexUDFMixin` doesn't override SUPPORTED), so index intraday is NATIVELY
> served, NOT rejected (reviewer's "index doesn't serve intraday" premise was wrong; passthrough-both is
> final, no design change). `resampled_from_d1` always + `resample_partial_period` bars-kept warnings.
> Suite **3290 green**, surface additive (snapshot FROZEN), no-secrets green. Reviewer pinging vf-advisor
> to drop its client-side aggregation workaround. state/ watermark = reviewer.
>
> **#186 quarantine-and-warn for bad upstream bars — ✅ DONE + PUSHED + CLOSED.** Pushed master
> `2c1ed62..5e5edf6`; #186 commented + CLOSED (06:1x). Codex×2 APPROVE, ZERO blockers, no must-fix
> (review-202606210614); BOTH self-found fixes verified genuine + LOAD-BEARING (red-first regressions are
> RED on the parent commits, not backfilled); 3 mutations + 9 boundary probes each caught a test; modified-test
> honesty confirmed (no structural-failure assertion weakened). **What shipped:** `UDFSource._build_bars`
> (SHARED loop, benefits index_history AND prices.history) QUARANTINES isolated bad bars — drop+record, emit
> `quarantined_invalid_bars` warning (never silent); conflicting same-date → drop the date; equity exact-ts dup
> → drop the ts; structural/shape faults still hard-raise; #162 identical-dedupe UNCHANGED; failover threshold
> `bad_inrange > max(3, 0.10*considered)` judged over the REQUESTED window only. **2 self-found fixes (pre-handoff
> adversarial wf):** MAJOR `24171b0` (threshold counted out-of-window padding → spuriously failed clean windows;
> range-filter moved INSIDE _build_bars) + MINOR `34e0ce1` (#162 identical-dedupe diluted the denominator;
> `considered -= 1` in dedupe branch). 4 fail-first regressions; full suite 3321 green; snapshot FROZEN; docs+
> skill+CHANGELOG updated. **Watermark/state = reviewer.** Confirmed back to reviewer → reviewer pings vf-advisor
> to flip the 10y/Max VN-Index chart mock→real. **Non-gating follow-ups (deferred, NOT issues):** (1) a bool
> scalar now reports generic 'malformed scalar' not the specific #87 bool reason (still correct, less specific);
> (2) quarantine constants module-level not per-adapter. Dev-box note: `~/.local` vnfin is a STALE pre-#186
> build that shadows naive `python -c` probes — `pip install -e .` before #185 dev to avoid false probes.
>
> **#185 annual world-gold source — ✅ DONE (PUSHED + CLOSED).** Pushed master `a23ac15..d250afe`;
> #185 commented + CLOSED (completed). **Codex×2 APPROVE, ZERO blockers** (review-202606210706); A
> verified my binary CRITICAL fix genuinely covers the prod path (spy-after-construction reverts → RED
> with exact symptom); B live-proved a non-SourceError parse bug PROPAGATES past `except` (N2 holds).
> Shipped INTERNAL `WorldBankCmoGoldSource` (annual XAU/USD from WB CMO Pink Sheet, stdlib xlsx parse) as
> the `world_reference_history_vnd` gold leg PRIMARY + daily `FailoverGoldClient` fallback with a
> never-silent `world_reference_gold_source_fallback` warning; synthesis byte-identical; `gold.world()`
> daily untouched; public-API snapshot FROZEN (source internal). **Pre-handoff adversarial-verify
> (5-lens wf + per-finding refute) self-caught+fixed 2 defects all green tests had hidden:** CRITICAL
> binary-transport routing on a bound-method `is` (always False → `binary=` never forwarded → CMO
> silently failed server-side; `57ecb86`, construction-time flag) + xlsx worksheet path normalization
> (`c4d269b`, `posixpath.normpath`); 2 findings refuted (`fetched_at_utc=now()` is lib-wide convention).
> Suite **3377 green**, no-secrets green. Optional v1.x NITs (deferred, NOT issues): (1) raise on >1
> full Gold split-header match; (2) N1 band headroom. Watermark/state left to reviewer; reviewer pinging
> vf-advisor to flip its gold chart mock→real (makes EVERY advisor view real; SPY pending their AV key).
> Memory: [[default-vs-injected-flag-not-bound-method-identity]].
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

- **DOCS BATCH (reviewer-routed 07:23) — ✅ FULLY DONE + PUSHED + CLOSED** (#166/#171 + #180 all on
  master, all closed). **#167 (VN equity universe) — ✅ DONE + PUSHED + CLOSED** (Codex×2
  APPROVE_WITH_NOTES; pushed `d35b712..e9d0c42`, #167 closed). Active WIP: **#181 + #187 both ✅
  DONE+PUSHED+CLOSED** (#181 Codex×1 APPROVE `1cc8a44`; #187 Codex×2 APPROVE_WITH_NOTES `ac7ca65`).
  Both delegated to fresh general-purpose agents in separate worktrees, TDD vs committed specs, synthetic
  fixtures; **#191** (test-hardening) filed from #187's 2 non-blocking notes. **#184 docs ✅ DONE+PUSHED+
  CLOSED** (Codex×1 APPROVE zero blockers; pushed `ac7ca65..ae7829d`, auto-closed via "Closes #184",
  resolution comment posted). **IN FLIGHT:** **#188** forward-discovery guard design APPROVED
  (`/tmp/vnfin-188-gate.md`, coverage refinement = exact-match unless `_`-family prefix) → TDD build
  delegated to a fresh general-purpose agent in worktree `wt-188` (spec `2a414f4`); awaiting agent green
  → then integrate on merged tree + route Codex×1. **NEXT:** #189 (board_unavailable) rides #188's
  hardened guard — design gate AFTER #188 lands.

  **LANDED THIS BATCH (#181 + #187 — both closed):**
  - **#187 (bug) — midnight-open placeholder recovery (index D1) — ✅ DONE + PUSHED + CLOSED.** Codex×2
    **APPROVE_WITH_NOTES** (review-202606211004; both reviewers, mutation-tested invariants, zero blockers).
    Re-rebased onto master (had moved) → `ac7ca65`, tree byte-identical to reviewed `61e6dd7`; pushed
    `1cc8a44..ac7ca65`, #187 closed. Final master 3444 passed, snapshot frozen, #180 guard 34. Signature =
    H/L/C/V identical + open differs + one row at LOCAL 00:00 VN-tz → keep non-midnight, drop midnight,
    recover (considered-=1 only, NOT charged to failover); genuine-conflict/no-midnight → UNCHANGED #186
    poison. **2 non-blocking test-hardening notes filed as #191.**
  - **#181 (enh) — additive `Fund.nav_as_of` — ✅ DONE + PUSHED + CLOSED.** Codex×1 **APPROVE** zero
    blockers (review-202606210958-181-nav-as-of-approve; pinned SHA `1cc8a44`, all 7 check-points PASS).
    Pushed master `e9d0c42..1cc8a44` (spec `d064244` + impl `1cc8a44`); #181 closed with resolution
    comment. Source = `extra.lastNAVDate` via existing `_parse_update_at`→`VN_TZ.date()`; distractors
    ignored; never-fabricated; additive (snapshot frozen, NO token). **Deferred list-level staleness
    warning (`fund_nav_stale` + clock seam + bounded threshold) filed as #190** (design-first).

  **QUEUED (reviewer source-vet DONE + triaged; batch AFTER #187/#181):**
  - **#184 — DOCS-ONLY ✅ DONE+PUSHED+CLOSED** (`ae7829d` on origin, Codex×1 APPROVE zero blockers,
    review-202606211021-184-world-index-docs-approve). NO clean keyless server-reachable ToS-safe
    SPY/^GSPC source exists → documented: (1) world-index from a server effectively requires
    `ALPHAVANTAGE_API_KEY` (BYOK); (2) Stooq ^SPX relabelled **residential-only** (anti-bot-blocked from
    datacenter IPs since ~2020-12, KEPT in chain not removed) so a keyless datacenter `AllSourcesFailed`
    reads as EXPECTED not flaky; (3) Yahoo deliberately NOT added (ToS). Docstrings-only in
    `world_sources.py`; no chain/code change, no new token, snapshot frozen; `docs/api.md` SKIP confirmed
    correct (no existing indices.world entry). 5 files: indices-world.md, world_sources.py, SKILL.md,
    domains.md, CHANGELOG.
  - **#182 — domestic VN gold history source-hunt → accept-pending-source (reviewer triaged).** Still NO
    clean domestic-gold history source; `gold.domestic_history()` stays a source-gap NotImplementedError.
    No build action until a source is found.
  - ✅ **#166/#171 — DONE + PUSHED + CLOSED** (`8463592` impl + `acfc3ad` backlog; pushed
    `cefe777..acfc3ad`; both issues closed w/ resolution comments). Reviewer APPROVED both CLEAN.
    #166 index-VOLUME-semantics section + units/SKILL caveats + doc↔code guard; #171 end-to-end gold
    coverage map (gold-world-reference.md hub) + cross-links + guard.
  - ✅ **#180 — DONE + PUSHED + CLOSED** (`dd3ee1c` impl + `d35b712` backlog; pushed `acfc3ad..d35b712`;
    #180 closed w/ resolution comment). Reviewer **APPROVE** (review-202606210822) after an independent
    reverse completeness re-sweep (AST bijection over all 84 `vnfin/` files): emitted prefixes = 29,
    documented = 29, both diffs empty. Namespaced all 4 prose/unstable warnings fact-first/cause-in-tail:
    `deduped_duplicate_nav_rows` (fmarket), `skipped_mismatched_report_rows` (vndirect),
    `skipped_period_rows` (cafef), `stitched_segment` (indices/client — year moved AFTER the `:`; the
    bonus 4th, ratified). Each has a fail-first regression (RED→GREEN). SKILL "Warning tokens" section at
    the COMPLETE 29-token set + **bidirectional** `_WARNING_TOKENS_180` guard, **proven fails-red BOTH
    ways**. Suite green, snapshot FROZEN, CHANGELOG updated. Watermark/state left to reviewer.
    Memory: [[new-warning-token-must-update-180-reference]].
  - 📋 **#188 — guard forward-discovery hardening (NON-BLOCKING follow-up, filed by reviewer).** My #180
    guard is a regression-LOCK (loops the hardcoded 29-tuple), not a forward-DISCOVERY gate — a FUTURE new
    prose `.warnings` would still ship green (same blind spot that caused #180). Durable fix = guard
    AST-extracts leading tokens from every `.warnings` site and asserts subset-of-documented. Tracked, not
    urgent; schedule after #167.

## Next (code queue — after docs batch)

- **#167 — VN equity universe / symbol discovery** — **ACCEPTED, NEXT CODE ITEM** (reviewer 07:35,
  source confirmed clean-room). Process: SHORT design note → LEAD gate → TDD → Codex×2.
  - Source report: `~/tools/vnfin-oss-reviewer/reviews/source-202606211100-issue167-vn-equity-universe.md`;
    spec direction in the #167 GitHub comment.
  - **Source = SSI iBoard query groups on `iboard-query.ssi.com.vn`** — SAME host + SUCCESS-envelope the
    existing `ssi_iboard_query` index-constituents source uses → **REUSE that transport/host/posture** (no
    new clean-room/legal risk; runtime-fetch-only / no-redistribution).
  - `GET /stock/group/{token}`; tokens NON-OBVIOUS: HOSE=`VNINDEX`, HNX=`HnxIndex`, UPCOM=`HNXUpcomIndex`
    (plain HOSE/HNX/UPCOM → empty). Filter `stockType=='s'` (equities only; drop warrants/ETFs/funds).
  - Expose: ticker / exchange / companyNameEn+Vi / ISIN / stockType / adminStatus(listing-status) /
    parValue / currency.
  - HONEST gaps as never-silent warnings (mirror `weights_not_available`): `listing_date_not_available`
    (firstTradingDate=='0'), `sector_not_available`, `coverage_partial` (index basket ~96%, NOT full
    regulatory roster — never claim a complete roster; cross-check totals vs SSC portal in provenance doc).
  - New internal `ssi_iboard_universe` source + public accessor (propose home/name in the design note).
  - Clean-room: SSI iBoard host only, zero VNStock.
  - ✅ **DESIGN GATE: APPROVE-WITH-CHANGES** (reviewer 08:21, `/tmp/vnfin-167-gate-verdict.md`) — **GREEN
    TO CODE** once the blockers are folded into the spec. All decisions LOCKED:
    - (a) **NEW `vnfin.equities` domain** (funds-style `client = source`; register in `vnfin/__init__.py`
      `from . import equities` + `__all__`).
    - (b) **DEFER `profile(symbol)`** — out-of-scope convenience filter; ship `universe()`-only, document
      "call `universe(exchange=)` and filter".
    - (c) **`exchange=None` merges all 3 boards** (default), with a FIXED dedup (blocker #2 below).
    - **Tokens (4, ratified): `partial_universe_coverage`** (renamed from `coverage_partial` — collided
      w/ existing `partial_coverage`; new name slots into the `partial_<qualifier>_coverage` family),
      `listing_date_not_available`, `sector_not_available`, **`cross_board_duplicate_symbol`** (blocker
      #2 fix). → **#180 lockstep guard 29→33** in the SAME change (gate on the sweep, not the count).
    - **Blocker #2 DECISION = route (a) warning+keep-first:** cross-board symbol collision must NOT
      hard-raise (one live-provider glitch would nuke all 3 boards). Keep-first + never-silent
      `cross_board_duplicate_symbol` warning; per-board warnings stay attributed (namespace by board).
    - **Must-fix-in-spec:** do NOT inherit `_optional_member_str`/`_member_company_name` as-is — they
      hard-code `IndexConstituentsSource.NAME` (`vnfin/indices/sources.py:240,255`) → would mislabel the
      new source's errors as `ssi_iboard_query`. Lift to a name-parameterized helper / own copy. **Drop**
      the always-`"s"` `security_type` field (structurally constant = misleading). Add a **CI-skipped
      opt-in live probe** test (pins payload shape) + `docs/sources/equities-universe.md` provenance
      (cite the reviewer source report: HOSE/VNINDEX=403, HNX/HnxIndex=300, UPCOM/HNXUpcomIndex=828; ~96%
      vs SSC; runtime-fetch/no-redistribution).
    - Code map (for spec): `IndexConstituentsSource` `vnfin/indices/sources.py:145-261`; models
      `vnfin/indices/models.py`; `HttpDataSource._request_json` `vnfin/transport.py`; funds `client=source`
      `vnfin/funds/__init__.py:45-56`; `canonical_security_symbol`/`reject_duplicate`/`require_present`
      from `vnfin._contracts`. **Provenance satisfied** (reviewer corrected the sub-agent's false
      provenance blocker — the source report lives in the reviewer workspace, not the builder repo).
  - ✅ **DONE + PUSHED + CLOSED.** Codex×2 **APPROVE_WITH_NOTES** (review-202606210945-167-equities-codex-x2;
    A=correctness zero-blockers, B=clean-room/scope; all 7 check-points PASS). Pushed master
    `d35b712..e9d0c42` (spec `42e615d` + code `8e50cc7` + backlog); #167 closed with resolution comment.
    Merged tree **3420 passed**, equities pkg **100%** cov, #180 guard **33 bijective**, snapshot FROZEN
    (additive). Integrator adversarial pass clean; I ADDED `test_negative_par_value_is_none`
    ([[new-source-must-mirror-sibling-data-integrity-guards]] negative-value blind spot). Watermark left
    to reviewer (I do NOT advance `state/last_seen.txt`).
  - 📋 **#189 — non-blocking follow-up (filed by reviewer).** `exchange=None` merge has no try/except per
    board (`vnfin/equities/sources.py:152-169`) → a SINGLE board's EmptyData/SourceUnavailable aborts all
    three. Spec-conformant as written (NOT a blocker), but harden via `board_unavailable` skip-and-warn +
    the missing test. New token → #180 guard +1, so schedule AFTER #187 (shared `test_docs_contract.py`).
- **#163 — dividends / corp-actions** — ACCEPTED in scope but **BLOCKED**: source choice (clean-thin
  HOSE-JSON vs full-but-HTML HNX/VSDC scrape vs paid FiinGroup-BYOK) is a legal/product decision the
  reviewer escalated to Boss. **Do NOT start until reviewer sends the chosen-source spec.**

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

- _(none — #185 promoted to NOW above)_

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
