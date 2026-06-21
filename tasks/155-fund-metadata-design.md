# #155 design note — richer fund metadata + allocation diagnostics

**Issue #155** (richer Fmarket fund metadata + allocation coverage diagnostics). Dep #190 landed; branch
off current master (`#181 Fund.nav_as_of` + `#190 fund_nav_stale` + `#180` baseline + `#163` corp_actions
de-scope, HEAD `a94ddf0`), NOT origin's old state. Source ToS = REVIEWER's call.

> **Fact-checked vs committed code 2026-06-21** (read-only sub-agent, line-cited). 1 gate-blocker found +
> corrected: the earlier "`inception`/`description` confirmed in fixtures" claim was FALSE (grep = zero
> hits) → demoted to probe-gated. Only `management_fee_pct` + `SectorWeight` are genuinely confirmed.

## Field inventory (confirmed vs needs-probe)
**Confirmed in committed synthetic fixtures `tests/test_funds.py` (fact-checked vs code):**
- `managementFee` — on the **fund LIST row** (`_fund_list_payload`, `tests/test_funds.py:50`, value `1.0`
  on the EQUITY row ONLY; the bond row omits it) → `management_fee_pct: Optional[float]` (`None` when
  absent, never fabricated), free on the existing list call (no extra request). The list-row parser
  `_parse_fund` (`fmarket.py:463`) tolerates unknown keys → adding the read is non-breaking.
- `sector allocation` — `productIndustriesHoldingList` is **already in the HOLDINGS payload**
  (`_holdings_payload`, `tests/test_funds.py:123`; shape `[{"industry": <str>, "assetPercent": <float>}, …]`)
  but currently **UNPARSED** (grep: zero hits in `vnfin/`) → net-new `SectorWeight(industry, weight_pct)`
  parsed off the EXISTING holdings endpoint (NO new request), fail-closed like `_parse_asset_class_row`.
- `asset allocation` — already parsed (`AssetAllocation`, `models.py:162`; keyed on `assetType.{code,name}`
  + `assetPercent`), via the existing accessor `asset_allocation(product_id)` (`fmarket.py:421`).

**⚠️ CORRECTED (fact-check gate-blocker):** `inception`/`firstIssueAt` and `description` are **NOT** in any
fixture or in `vnfin/funds/` (grep = zero hits) — the prior "present in payload" claim was false. They are
moved to the probe-gated bucket; do NOT ship as confirmed. (For shape reference, the analogous shipped date
`nav_as_of` (#181) is parsed from `extra.lastNAVDate` epoch-ms, `fmarket.py:511` — not a top-level field, so
even inception's assumed path is unverified.)

**NOT confirmed — needs a reviewer-authorized live probe before we design fields for them (6 fields):**
`inception_date` (`firstIssueAt`?), `description`, `benchmark`, `risk-category`, `subscription/redemption
fees`, `factsheet URL`. **Never fabricate** — ship the confirmed core + a `missing_*` diagnostic; add any of
the 6 only if the probe confirms its exact JSON path.

## Proposed v1 (additive — confirmed core only; probe-gated fields deferred)
- **`Fund` optional field** (`models.py:20`; current fields code/name/**id**/nav/manager/asset_type/
  currency/nav_as_of): append AFTER `nav_as_of` (line 39) + defaulted → `management_fee_pct: Optional[float]
  = None` (confirmed). Appended+defaulted so the snapshot comparator treats it additive, not breaking
  (`dump_api_surface.py:279`: insert-before or required-add = breaking). `inception_date` added ONLY if the
  probe confirms its path.
- **`SectorWeight(industry: str, weight_pct: float)` model** (frozen, mirror `AssetClassWeight`
  `models.py:151`) + parse `productIndustriesHoldingList` off the EXISTING holdings endpoint (NO new
  request), fail-closed like `_parse_asset_class_row` (`fmarket.py:634`): non-blank industry string,
  `_as_float` weight, malformed row → fails closed. Add `SectorWeight` to `vnfin/funds/__init__.__all__`.
- **Accessors:** extend the existing `holdings()` / `asset_allocation(product_id)` to surface
  `sector_weights` + `management_fee_pct` (REUSE — do NOT add a clashing `allocation`/`fund_detail` name;
  neither exists today and `/res/products/{id}` is not wired). A new detail call is needed ONLY for the
  probe-gated fields, not the confirmed core.
- **`vnfin.diagnostics.explain_fund_coverage()`** (no-arg, offline) — mirror
  `explain_corp_actions_coverage()` / `explain_fixed_income_coverage()` (`diagnostics.py:577`/`:517`):
  return a `RequestDiagnostic` enumerating available-vs-source-missing metadata. Add to
  `diagnostics.__all__` (`diagnostics.py:41`) + a `_FUND_COVERAGE_CAPS` tuple + the diagnostics-enumerating
  docs (`docs/api.md`, `docs/architecture/data-domains.md`, `docs/how-to/source-diagnostics.md`).
- **Warning tokens** `fund_missing_fees`, `fund_partial_holdings` (top-holdings coverage% below a bound).

## Proposed live-probe spec (reviewer authorizes; I do NOT run it unprompted)
- Endpoint: `GET https://api.fmarket.vn/res/products/{id}` (same domain as the already-wired list/NAV).
- Goal: confirm the JSON PATH + presence of the **6** unconfirmed fields on ≥2 distinct funds (one equity,
  one bond) — confirm field EXISTENCE only; **fixtures stay synthetic** (no real rows committed).
- Output: a path→field map I fold into the design; without it the 6 fields are dropped from v1.

## Surface / snapshot
Additive: new optional `Fund` field + new `SectorWeight` model + new accessor/diagnostic. Snapshot is
additive-tolerant (`test_public_api_surface.py:273` asserts only `not breaking`) — do NOT regen
`dump_api_surface.py` mid-feature; regen at release. New `Fund` field MUST be appended after `nav_as_of` +
defaulted (else flagged breaking). Confirm the surface test is additive-green vs the frozen baseline.

## Warning tokens (#180/#188 lockstep — IN THIS CHANGE)
2 new tokens (`fund_missing_fees`, `fund_partial_holdings`): add to the SKILL.md Warning-tokens table
(`skills/vnfin/SKILL.md:116`; copy the `fund_nav_stale` row at `:161`) + `_WARNING_TOKENS_180`
(`tests/test_docs_contract.py:551`) + emit verbatim as string literals so #188's AST forward-discovery sees
them at a `warnings=`/accumulator/`_*warning(s)`-helper sink ([[new-warning-token-must-update-180-reference]]).
**Baseline: `_WARNING_TOKENS_180` = 44 NOW** (#163 de-scope landed 2026-06-21 — `vsdc_ratio_tax_deferred`
already in the tuple), so these 2 take it **44→46** — but **gate on the doc↔code bijection sweep being
green, NOT a magic count** ([[multi-hop-crawl-silent-loss-surfaces-checklist]]: gate on the sweep).

## TDD (fail-first; synthetic fixtures only)
- Parse: synthetic fixture w/ `productIndustriesHoldingList` + mgmt-fee → `SectorWeight` list +
  `management_fee_pct` populated (Optional: bond row w/o fee → `None`); malformed industry/weight → fails
  closed. (`inception_date` parse test added only if the probe confirms its path.)
- Accessors: extended `holdings`/`asset_allocation` happy + canonicalization + bad-id paths.
- Diagnostic: offline `explain_fund_coverage` asserts available-vs-missing enumeration + is in `__all__`
  + the docs-enumerate convention.
- Tokens: `fund_missing_fees` when fees absent; `fund_partial_holdings` at the coverage bound; doc-contract
  bijection (#180) + forward-discovery (#188) green.

## Open questions for the reviewer (gate)
1. **AUTHORIZE the live probe?** It now covers **6** unconfirmed fields (incl. `inception_date` +
   `description`, demoted after the fact-check). If yes, confirmed paths enter v1; if no, v1 ships the
   confirmed core (`management_fee_pct` + `SectorWeight`) + `fund_missing_*` only.
2. **`include_metadata` default** — lean TRUE (`management_fee_pct` is free on the existing filter row, no
   extra request; inception is NOT free — probe-gated) — OK?
3. **`fund_partial_holdings` threshold** — bounded coverage% (warn if top-holdings sum < X%) vs blanket
   top-N? Recommend a coverage% bound (mirrors the staleness-warning bounded-false-positive principle).
4. **2 new tokens** (`fund_missing_fees`, `fund_partial_holdings`) confirmed for #180/#188 (44→46; gate on
   the sweep not the count)?
5. **Source verdict:** Fmarket `/res/products/{id}` detail endpoint (same domain as already-wired list/NAV)
   — approved for runtime fetch? (Needed ONLY for the 6 probe-gated fields; the confirmed core needs no new
   endpoint.)
6. **Accessor shape:** OK to extend `holdings()`/`asset_allocation()` for `sector_weights` +
   `management_fee_pct` (reuse), rather than add a new `fund_detail`/`allocation` accessor?

---

## BUILD CONTRACT — reviewer APPROVED 2026-06-21 + live-probe results (THIS is the spec to build)

Reviewer rulings (all 6 Qs): (1) live probe AUTHORIZED, narrow, non-gating; (2) `include_metadata`
default **TRUE**; (3) `fund_partial_holdings` = **coverage% bound** (warn when top-holdings sum < a
documented bound), NOT blanket top-N; (4) 2 tokens CONFIRMED 44→46, **gate on the doc↔code SWEEP not the
count**, emit as **literal stems at a `warnings=` sink** so #188 forward-discovers; (5) source
`/res/products/{id}` APPROVED (same `api.fmarket.vn` domain/posture as wired list/NAV/holdings); (6)
**REUSE** accessors — extend `holdings()`/`asset_allocation()`, do NOT add a clashing
`fund_detail`/`allocation` name.

**Live-probe outcome (reviewer-authorized, opt-in, ran 2026-06-21 on id=38 equity + id=21 bond; values
NOT committed, fixtures stay synthetic):** of the 6 probe-gated fields, **2 confirmed with exact paths →
LAND; 4 deferred:**
- ✅ `inception_date` ← `data.firstIssueAt` (int **epoch-ms**, parse exactly like `nav_as_of` from
  `extra.lastNAVDate`, `fmarket.py:511`) → `Optional[date]`.
- ✅ `description` ← `data.description` (str) → `Optional[str]`.
- ❌ `benchmark`, `risk-category` — **absent** from the detail doc → dropped (do not add).
- ⚠️ subscription/redemption fees — present only as a tiered `productFeeList[]` schedule
  (`fee`+`feeUnitType`+holding-tier program), NOT a flat scalar → **DEFERRED** (mapping flat = fabrication;
  needs its own typed model in a follow-up). `managementFee` IS also on the detail doc (corroborates list).
- ⚠️ factsheet URL — only ambiguous `productDocuments[].url` + `websiteURL` (which document is the
  factsheet is unknowable) → **DEFERRED** (never fabricate). 

### What to build (additive, TDD-first, synthetic fixtures only)
1. **`Fund`** (`models.py:20`): append AFTER `nav_as_of` (line 39), each defaulted →
   `management_fee_pct: Optional[float] = None`, `inception_date: Optional[date] = None`,
   `description: Optional[str] = None`. (Appended+defaulted ⇒ snapshot additive, not breaking.)
   `management_fee_pct` from the LIST row `managementFee` (equity-row-only → Optional, None when absent,
   never fabricated); `inception_date`/`description` from the DETAIL doc (the same `/res/products/{id}`
   `holdings()`/`asset_allocation()` already fetch) — populate on the detail-sourced path, leave None on
   the list-only path. Choose the cleanest additive seam (reuse existing accessors; no new public name).
2. **`SectorWeight`** (`models.py`, frozen `@dataclass`, mirror `AssetClassWeight` `models.py:151`):
   `industry: str`, `weight_pct: float`. Parse `data.productIndustriesHoldingList`
   (`[{"industry","assetPercent"}]`) off the EXISTING holdings detail doc → `tuple[SectorWeight, ...]`,
   surfaced on the `holdings()`/`asset_allocation()` result. **Fail-closed like `_parse_asset_class_row`
   (`fmarket.py:634`)**: non-blank `industry` str, `_as_float` weight, malformed row → drop/closed (never
   crash, never fabricate). Add `SectorWeight` to `vnfin/funds/__init__.__all__`.
3. **`include_metadata` default TRUE** on `list_funds` (populates `management_fee_pct` from the row; no
   extra request).
4. **`vnfin.diagnostics.explain_fund_coverage()`** (no-arg, offline) — mirror
   `explain_corp_actions_coverage()`/`explain_fixed_income_coverage()` (`diagnostics.py:577`/`:517`):
   return `RequestDiagnostic` enumerating available-vs-source-missing metadata (note benchmark/risk/fee-
   schedule/factsheet as source-missing). Add to `diagnostics.__all__` (`diagnostics.py:41`) + a
   `_FUND_COVERAGE_CAPS` tuple + the diagnostics-enumerating docs (`docs/api.md`,
   `docs/architecture/data-domains.md`, `docs/how-to/source-diagnostics.md`).
5. **2 warning tokens** `fund_missing_fees` (when `managementFee` absent on a fund) + `fund_partial_holdings`
   (top-holdings coverage% below a **documented bound** — pick + document the bound, mirror the
   bounded-false-positive staleness principle). Emit verbatim as **literal stems at a `warnings=` sink**
   (#188 forward-discovery); add to `_WARNING_TOKENS_180` (`tests/test_docs_contract.py:551`, 44→46) + the
   SKILL.md table (`skills/vnfin/SKILL.md:116`; copy the `fund_nav_stale` row at `:161`).
6. **Docs + CHANGELOG + SKILL** updated in the SAME change (public-API change rule). **Snapshot:** do NOT
   regen `dump_api_surface.py`; confirm `test_public_api_surface.py` is additive-green vs the frozen
   baseline.

### Gates before reviewer handoff (merged tree)
Full suite green; #180 reverse + #188 forward bijection SWEEP green (not a count); snapshot frozen
(additive only); no real rows committed (synthetic fixtures); live-probe test (if any) opt-in/CI-skipped.
Then route **Codex x1** (reviewer's call; additive low-risk). On APPROVE + green → push + close #155 =
**backlog FULLY CLEARED**.
