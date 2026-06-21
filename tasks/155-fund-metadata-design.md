# #155 design note — richer fund metadata + allocation diagnostics

**Issue #155** (richer Fmarket fund metadata + allocation coverage diagnostics). Dep #190 landed
(HEAD has `21c39b9`); branch off current master (`#181 Fund.nav_as_of` + `#190 fund_nav_stale` +
`#180` baseline), NOT origin's old state. Source ToS = REVIEWER's call.

## Field inventory (confirmed vs needs-probe)
**Confirmed on the Fmarket payload (clean-room — verified present in committed synthetic fixtures
`tests/test_funds.py`, 2026-06-21):**
- `managementFee` — on the **fund LIST row** (`_fund_list_payload`, `1.0` for the equity fixture), so
  `management_fee_pct` is free on the existing list call (no extra request → `include_metadata=True`
  costs nothing). `inception` (`firstIssueAt`), `description` present in payload.
- `asset allocation` — already parsed (`AssetAllocation`, `models.py:162`; keyed on
  `assetType.{code,name}` + `assetPercent`).
- `sector allocation` — `productIndustriesHoldingList`, shape
  `[{"industry": <str>, "assetPercent": <float>}, …]` (e.g. `{"industry":"Fake industry one",
  "assetPercent":50.0}`) — present in the holdings fixture but currently **UNPARSED** → net-new
  `SectorWeight(industry: str, weight_pct: float)` parse target (mirror `AssetAllocation` but keyed on
  a plain `industry` string, not an `assetType` object).

**NOT confirmed — needs a reviewer-authorized live probe before we design fields for them:**
`benchmark`, `risk-category`, `subscription/redemption fees`, `factsheet URL`. **Never fabricate** —
ship the confirmed set + a `missing_*` diagnostic; add the 4 only if the probe confirms their paths.

## Proposed v1 (additive)
- **`Fund` optional fields** (`models.py:20`, currently code/name/nav/manager/asset_type/currency/
  nav_as_of): add `inception_date`, `management_fee_pct` (confirmed). The 4 gated fields added ONLY if
  the probe confirms.
- **`SectorWeight` model** + parse `productIndustriesHoldingList` (confirmed in fixtures).
- **Accessors** `fund_detail(product_id)` / `allocation(product_id)`; `list_funds(include_metadata=)`.
- **`vnfin.diagnostics.explain_fund_coverage()`** (offline) — enumerates which metadata is available vs
  source-missing, mirrors the existing `explain_*` siblings.
- **Warning tokens** `fund_missing_fees`, `fund_partial_holdings` (top-holdings coverage% below a bound).

## Proposed live-probe spec (reviewer authorizes; I do NOT run it unprompted)
- Endpoint: `GET https://api.fmarket.vn/res/products/{id}` (same domain as the already-wired list/NAV).
- Goal: confirm the JSON PATH + presence of the 4 unconfirmed fields on ≥2 distinct funds (one equity,
  one bond) — confirm field EXISTENCE only; **fixtures stay synthetic** (no real rows committed,
  per the no-broker-rows rule).
- Output: a path→field map I fold into the design; without it the 4 fields are dropped from v1.

## Surface / snapshot
Additive: new optional `Fund` fields + new `SectorWeight` model + new functions. Snapshot is
additive-tolerant — do NOT regen `dump_api_surface.py` mid-feature; regen at release. Confirm the
surface test is additive-green vs the frozen baseline.

## Warning tokens (#180/#188 lockstep — IN THIS CHANGE)
2 new tokens (`fund_missing_fees`, `fund_partial_holdings`): add to the SKILL.md Warning-tokens table +
`_WARNING_TOKENS_180` + emit as literals so #188's AST forward-discovery sees them
([[new-warning-token-must-update-180-reference]]). **Baseline moved: `_WARNING_TOKENS_180` = 42 once
#163 lands (37 + #163's 5 corp-action tokens)**, so these 2 take it 42→44. The exact start count
depends on #163 merging first — **gate on the doc↔code bijection sweep being green, NOT a magic
count** ([[multi-hop-crawl-silent-loss-surfaces-checklist]] reinforces: gate on the sweep).

## TDD (fail-first; synthetic fixtures only)
- Parse: synthetic fixture w/ `productIndustriesHoldingList` + mgmt-fee + `firstIssueAt` → `SectorWeight`
  list + `inception_date`/`management_fee_pct` populated; malformed → fails closed.
- Accessors: `fund_detail`/`allocation` happy + canonicalization + bad-id paths.
- Diagnostic: offline `explain_fund_coverage` asserts available-vs-missing enumeration.
- Tokens: `fund_missing_fees` when fees absent; `fund_partial_holdings` at the coverage bound;
  doc-contract bijection (#180) + forward-discovery (#188) green.

## Open questions for the reviewer (gate)
1. **AUTHORIZE the live probe?** If yes, I (under your direction) or you confirm the 4 fields' paths,
   then they enter v1. If no, v1 ships the 5 confirmed fields + `fund_missing_*` only.
2. **`include_metadata` default** — lean TRUE (fees/inception are free on the existing filter row, no
   extra request) — OK?
3. **`fund_partial_holdings` threshold** — bounded coverage% (warn if top-holdings sum < X%) vs blanket
   top-N? Recommend a coverage% bound (mirrors the staleness-warning bounded-false-positive principle).
4. **2 new tokens** (`fund_missing_fees`, `fund_partial_holdings`) confirmed for #180/#188 (42→44
   post-#163; gate on the sweep not the count)?
5. **Source verdict:** Fmarket `/res/products/{id}` detail endpoint (same domain as already-wired
   list/NAV) — approved for runtime fetch?
