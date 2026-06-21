# #152 design note — fixed-income rates coverage (yield curve deferred)

**Issue #152** (fixed-income rates + VN government-bond yield curve). Source verdicts below are the
REVIEWER's call — candidate lists only; and per [[sandbox-probe-false-negative-not-a-source-verdict]]
do NOT take my sandbox connectivity probes as verdicts.

## Headline ask (govt-bond yield CURVE by tenor + history) → DEFER (no clean source)
Candidate sources my scoping surfaced, all reviewer-owned verdicts:
- AsianBondsOnline (ADB) — portal footer "reproduction prohibited"; no public API.
- HNX bond board — JS chart, no structured feed, no stated license.
- Trading Economics — redistribution prohibited (paid).
No clean, redistributable yield-curve source → **defer `vnfin.bonds.yield_curve/yield_history`**; do NOT
register a `vnfin.bonds` namespace until one is backed.

## Already shipped (do NOT duplicate)
`vnfin.macro.get_indicator(iso3, "policy_rate")` already returns the monetary policy rate — DBnomics
IMF-IFS `M.{CC}.FPOLM_PA`, **% per annum, monthly, an SBV refinancing-rate PROXY, stale ~Dec 2023**
(`vnfin/macro/dbnomics.py:80`, `MacroIndicator.POLICY_RATE` at `indicators.py:52`). So `policy_rate` is
DONE via the existing macro domain — #152 must not add a second way to fetch it.

## Recommendation — Option B: EXTEND the existing macro domain (minimal, no duplication)
Rates already live in `vnfin.macro`. Add the net-new, clean, redistributable rate indicators as
`MacroIndicator` members + `_WB_MAP` entries (mirror the GDP/CPI/policy_rate pattern at
`worldbank.py:55`), reachable through the existing `vnfin.macro.get_indicator(...)` + failover:
- `lending_rate` → WB WDI `FR.INR.LEND` (% p.a., annual, CC BY 4.0)
- `deposit_rate` → WB WDI `FR.INR.DPST` (% p.a., annual)
- `real_interest_rate` → WB WDI `FR.INR.RINR` (% p.a., annual)

Plus an offline `vnfin.diagnostics.explain_fixed_income_coverage()` that (a) states the govt-bond yield
CURVE is unavailable (no clean source), (b) enumerates what IS available — policy (proxy, monthly,
stale) / lending / deposit / real (annual) — with frequency + caveats, and (c) distinguishes
policy vs interbank vs deposit vs govt-bond so users don't conflate them. Pattern mirrors the existing
`explain_world_gold_history` / `explain_fx_coverage`.

**No new `vnfin.rates` domain.** This avoids duplicating `policy_rate`, follows the existing structure,
and keeps complexity minimal (mission principle).

### Alternative — Option A (scoping's original): new `vnfin.rates` facade domain
`RateSeries`/`RateKind` + `policy_rate()/lending_rate()/real_rate()/deposit_rates()` over WB+DBnomics.
Rejected-lean: it creates a parallel second way to fetch `policy_rate` (already in macro) and a new
top-level domain for 3 annual series — heavier than the need.

## Surface / snapshot
Additive: new `MacroIndicator` enum members + one new diagnostic function. Public-API snapshot is
additive-tolerant — do NOT regen `dump_api_surface.py` mid-feature; regen at release only. Confirm the
surface test is additive-green against the frozen baseline.

## Warning tokens (#180/#188)
Lean: REUSE the existing staleness + policy-proxy disclosure machinery; the WB annual nature is
documented, not a per-result warning. **If** v1 introduces any NEW `result.warnings` token (e.g. an
annual-only disclosure), it rides the #180 reverse + #188 forward lockstep in the same change
([[new-warning-token-must-update-180-reference]]). Flag at the gate which way the reviewer wants.

## TDD (fail-first; synthetic fixtures; live WB opt-in/CI-skipped)
- Per-indicator: `_WB_MAP`/unit/identity mapping for lending/deposit/real (mirror existing macro tests);
  failover + reject-reason + unit-guard behavior unchanged for the new indicators.
- Diagnostic: offline `explain_fixed_income_coverage()` asserts yield-curve-unavailable status +
  enumerates the available rate kinds + caveats; canonicalizes/fails-closed like the siblings.
- Regression: existing `policy_rate`/GDP/CPI paths unchanged.

## Open questions for the reviewer (gate)
1. **Option B (extend macro) vs Option A (new `vnfin.rates`)** — I recommend B.
2. **Source verdict:** WB `FR.INR.LEND/DPST/RINR` (same already-wired, CC BY 4.0 WB source as GDP/CPI —
   low risk) approved? And confirm the yield-curve sources stay deferred (AsianBondsOnline/HNX/TE = your
   verdict; don't act on my probe).
3. **deposit_rate** is a WB annual AGGREGATE (no clean retail per-tenor source) — acceptable for v1?
4. **Warning token:** reuse existing staleness/proxy disclosures, or add a new annual-only token (→ #180/#188)?
5. Keep canonical macro names `lending_rate` / `deposit_rate` / `real_interest_rate`?

## ✅ APPROVED — final build contract (reviewer 2026-06-21 11:47)
1. **Option B (extend macro), NOT a new domain** — confirmed (no duplicate `policy_rate`).
2. **Source APPROVED:** WB `FR.INR.LEND` / `FR.INR.DPST` / `FR.INR.RINR` (same already-wired CC-BY 4.0
   WB source as GDP/CPI, `_WB_MAP` at `worldbank.py:55`, `api.worldbank.org/v2`) — low risk. Yield
   CURVE stays DEFERRED; do NOT register `vnfin.bonds`.
3. `deposit_rate` as a WB **annual aggregate** is acceptable — **the diagnostic MUST disclose it is an
   annual aggregate (no clean per-tenor retail source).**
4. **NO new warning token** — REUSE existing staleness / policy-proxy disclosures (WB-annual nature is
   documented in `explain_fixed_income_coverage`, not a per-result token). Lean firmly no.
5. Canonical names `lending_rate` / `deposit_rate` / `real_interest_rate` — APPROVED.

**Must-hold:** additive (new `MacroIndicator` members + WB `_WB_MAP` entries + ONE diagnostic
`explain_fixed_income_coverage`); snapshot additive-green, **do NOT regen** `dump_api_surface.py`;
`explain_fixed_income_coverage` must distinguish **policy vs interbank vs deposit vs govt-bond** so
users don't conflate them, AND disclose `deposit_rate` is an annual aggregate + the govt-bond yield
curve is unavailable; TDD fail-first synthetic fixtures + WB live opt-in/CI-skipped; existing
`policy_rate`/GDP/CPI paths unchanged. Codex x1 on the merged tree.
