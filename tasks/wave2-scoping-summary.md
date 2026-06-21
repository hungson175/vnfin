# Wave-2 scoping summary (#152/#155/#163/#175/#182)

Source: scoping Workflow `wf_46081884-f22` (5 parallel general-purpose agents, VNStock blacklist
enforced; all returned `vnstock_exclusion_confirmed=true`). Full raw notes:
`/tmp/claude-1000/.../tasks/wxj5palls.output` (volatile — this file is the durable digest).

**ROLE BOUNDARY (reviewer 2026-06-21 11:16):** source-vetting / ToS verdict is the REVIEWER's call.
The `clean_room_sources` verdicts below are **candidate lists to route to the reviewer**, NOT settled.
#182 + #163 already have reviewer source verdicts — do not re-vet blind; route candidate lists.

Reviewer's stated W2 gate order: **#152 / #155 / #163 / #175**; but #175 Tier-1 is the build-now-small
quick win and was sent FIRST by agreement. One design gate at a time.

---

## #175 — PIT/historical index membership → 3-tier split. **GATE SENT (Tier-1)**
- **Tier-1 (build-now-small, NO source):** populate `as_of` (provider date if present, else None, never
  fabricated) + never-silent `current_snapshot_only` warning. Full gate note:
  `tasks/175-tier1-as-of-disclosure-design.md` (committed 4ea4cd7) — SENT to reviewer.
- **Tier-2 (source-gated):** `as_of=date` PIT lookup + `IndexMembershipChangeLog`. NO clean
  machine-readable redistributable historical-membership source (HOSE = date-stamped human PDFs, no PIT
  API, no redistribution grant). Reviewer source gate: curated effective-dated data file vs defer.
- **Tier-3 (build-now, NO source):** offline `diagnostics.explain_index_constituents` coverage status +
  FIX the existing misleading `suggested_action: "treat membership as point-in-time"` (asserts the
  opposite of reality). Small follow-up gate after Tier-1.

## #182 — VN domestic gold history re-probe tracker → **DOCUMENT + CLOSE** (matches reviewer verdict)
Re-probe (clean-room) found NO qualifying source:
- vAPI/VNAppMob gold v2: reachable but returns exactly **1 record** for an 8-yr range (date params
  IGNORED) + 15-day self-issued JWT + **no published ToS** → unusable.
- sjc.com.vn: HTTP **403** (Cloudflare datacenter block) → unusable.
- BTMC/PNJ/DOJI: **spot-only**, no multi-day history (already known, `provides_history=False`) → unusable.
- giavangonline.com: sandbox DNS stubbed to `::1` → genuinely **unverifiable here** (not a real refusal);
  no published ToS either → needs-confirmation.
- world gold APIs: world XAU × FX = the world-reference vnfin already ships (misses +10-21% domestic premium).
- **Recommendation:** post per-candidate findings + 4 reopen criteria [(a) machine-readable VN DOMESTIC
  history, (b) multi-year depth, (c) WRITTEN ToS permitting runtime-fetch/redistribution, (d) stable
  non-expiring key] as a close comment; CLOSE. No code, no surface change (`gold.domestic_history()`
  reserved-accessor + tests already green). Reviewer's only judgment call: attempt one off-sandbox
  giavangonline probe first (low expected value — absent ToS). Route to reviewer before posting/closing.

## #152 — fixed-income rates + VN yield curve → **DESIGN GATE** (narrow honest v1)
- **No clean source for the HEADLINE ask** (govt-bond yield CURVE by tenor + history): AsianBondsOnline
  portal footer = "reproduction prohibited" + no public API; HNX = JS chart, no feed, no license; Trading
  Economics = redistribution prohibited (paid). **All reviewer-owned verdicts — route candidate list.**
- **Clean + redistributable + already-wired:** World Bank WDI rate indicators (FR.INR.LEND lending,
  FR.INR.RINR real, FR.INR.DPST deposit; CC BY 4.0, annual) + DBnomics IMF-IFS FPOLM_PA policy-rate
  proxy (already in `vnfin.macro` #179; STALE ~Dec 2023).
- **Proposed buildable v1:** additive `vnfin.rates` (RateSeries + RateKind; `policy_rate`/`lending_rate`/
  `real_rate`/`deposit_rates` facade over WB+DBnomics; `% per annum`, provider as-of, staleness +
  `policy_rate_is_proxy` warnings) + `diagnostics.explain_fixed_income_coverage` that EXPLICITLY says
  "govt-bond yield curve unavailable" and distinguishes policy/interbank/deposit/govt-bond.
  **DEFER `vnfin.bonds.yield_curve/yield_history`** (no licensed curve source).
- **Open Qs for gate:** (a) ship narrow v1 vs hold whole issue vs email ADB for AsianBondsOnline
  redistribution/API; (b) policy_rate facade vs just-document the existing macro path (avoid 2 ways);
  (c) deposit_rates annual-aggregate-only acceptable (no retail per-tenor source); (d) register
  `vnfin.bonds` namespace now or omit until backed (lean omit).

## #163 — dividends / corp-actions / total-return → **DESIGN GATE** + SOURCE DISCREPANCY to route
- **SOURCE DISCREPANCY (route to reviewer):** reviewer's prior vetted source was HNX+VSDC, but the fresh
  clean-room probe found **VSDC = news-only HTML (unusable)** and **HNX = TLS-broken/no structured
  per-symbol endpoint (unusable)**. The only viable clean structured source found = **VNDirect finfo
  `/v4/events`** (no-auth, structured JSON, ex/record/payment dates + VND/share + stock ratio; **~2021
  history floor**; MEDIUM redistribution risk — same posture as the existing
  `vnfin/fundamentals/vndirect.py`). Backlog also notes #163 source was escalated to Boss. **Reviewer/Boss
  own the source verdict — route this candidate list; do not build until they rule.**
- **Proposed v1 (if source approved):** additive `vnfin.corporate_actions` (CorporateAction +
  CorporateActionHistory; EventType enum) + `vnfin.dividends` (cash view + `trailing_yield`) +
  `prices.explain_adjustment_policy` (offline: equity bars are PROVIDER_ADJUSTED, NOT verified
  total-return) + `diagnostics.explain_corporate_actions_coverage`. **DEFER `prices.total_return_history`**
  (double-count risk vs PROVIDER_ADJUSTED bars) or ship behind a loud `possible_double_count` warning.
- **Hard part = normalization** (locale dedup VN/EN, event-type taxonomy, cash %-par vs stock shares/100
  ratio semantics, rights-via-note, no-SPLIT gap, ~2021 coverage floor warning) — pin in tests first.

## #155 — richer fund metadata + allocation diagnostics → **build-after-#190** (now UNBLOCKED)
- **Dep satisfied in working tree:** #190 landed (HEAD includes 21c39b9). Branch off current master
  (has #181 `Fund.nav_as_of` + #190 `fund_nav_stale` constants/channel + #180 baseline), NOT origin's
  old state. New funds tokens add ON TOP of `fund_nav_stale`, no collision.
- **Confirmed Fmarket fields (clean-room probe):** management fee + inception (firstIssueAt) +
  description + asset allocation (already parsed) + **sector allocation** (`productIndustriesHoldingList`
  — in payload + fixtures, currently UNPARSED). Top-holdings coverage% derivable offline from
  `FundHolding.weight`.
- **NEEDS a reviewer-authorized live probe:** benchmark, risk-category, subscription/redemption fees,
  factsheet URL are NOT confirmed on the Fmarket detail doc (only mgmt-fee/inception/description are).
  Ship confirmed fields + `missing_*` diagnostic; never fabricate.
- **Proposed v1:** additive optional `Fund` fields (inception_date, management_fee_pct, + gated 4) +
  `fund_detail(product_id)`/`allocation(product_id)` + `SectorWeight` model + `list_funds(include_metadata=)`
  + `diagnostics.explain_fund_coverage` + tokens `fund_missing_fees`/`fund_partial_holdings` (#180 lockstep).
- **Open Qs:** the gated live-probe field set; include_metadata default (lean TRUE — fees/inception are
  free on the filter row); fund_partial_holdings threshold (bounded coverage% vs blanket top-N).
