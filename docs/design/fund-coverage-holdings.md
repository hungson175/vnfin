# Design — Fmarket fund coverage & holdings diagnostics (#172 + #173)

**Status:** APPROVED (reviewer gate review-202606201506, APPROVE_WITH_NOTES). #172 = option A
(`StaleData(EmptyData)`, defer C). #173 = option B **reframed allocation-aware** (premise corrected
below — no second gate needed). Two separate commits/reviews (Q3). A **batch** of two related Fmarket
fund-data-quality bugs the reviewer asked to design together **before** the large #157 feature.
**Reviewer specs:** review-202606201432 (#172 NAV staleness) + review-202606201436 (#173 bond holdings).
**Clean-room:** VNStock/vnstock excluded. **No HTML scraping** — only the documented/official Fmarket
endpoints already used by `vnfin/funds/fmarket.py`. Default tests synthetic/offline; any live probe gated.
**Preserve:** all existing #144 (wide-fetch + client-filter), #158 (dup-navDate), #21 (product-id/code)
guards and existing equity-holdings behavior.

---

## #172 — NAV history staleness vs silent `EmptyData`

### Current behavior (recon)

`FMarketSource.nav_history(product_id, from_date, to_date)` (`vnfin/funds/fmarket.py:166`) already
does the #144 fix: it requests the **wide** window (`isAllData=1, fromDate=_DEFAULT_FROM,
toDate=today`) and filters the caller's bounds **client-side**. It raises `EmptyData` in two places:
(a) the provider returns zero rows; (b) zero rows fall inside the caller's window.

**Bug:** when the provider's history endpoint is **stale** (e.g. latest `navDate` is in 2025) while
`list_funds()` shows a fresher 2026 NAV, a bounded **recent** window (2026) hits case (b) → a silent
`EmptyData` that is indistinguishable from "this fund has no data" — blocking YTD/drawdown/compare.

### Root-cause investigation (the implementing fork must determine which, with synthetic fixtures)

1. **Request body / pagination / page-size** — does the wide request actually return recent rows, or
   is there an undocumented cap/pagination that truncates the newest rows? (Preferred outcome: if a
   corrected request returns 2026 rows, fix the request — no contract change needed.)
2. **Genuinely stale history endpoint** despite a fresher list/current NAV.
3. **product-id/code mismatch** or **date filter/order** bug.
4. **A secondary/"latest NAV" endpoint** the project doesn't yet use (only if documented/official).

### Proposed contract (the decision)

After a correct wide fetch, classify a bounded request with **zero in-window points**:

- **genuinely no data** (history is empty, or the window is entirely before the fund's first
  `navDate`) → `EmptyData` (unchanged — correct).
- **stale history** — history is non-empty but its **latest `navDate` < requested window start**
  (data exists, just ends before the window) → **DO NOT** return a silent `EmptyData`. Instead
  surface an explicit staleness signal naming the gap.

**DECISION (approved, option A; C deferred):** add a `StaleData(EmptyData)` subclass. Existing
`except EmptyData` / `except SourceError` callers still catch it; the distinct type + message name the
gap. (B annotated-empty rejected as misuse-prone; C `explain_fund_nav_coverage` deferred — not needed
to fix the bug, adds a public function now.)

**Probe result (gated live, 2026-06-20 ~15:12 — truncation RULED OUT).** All 65 funds' wide
`nav_history` fetch ends uniformly at **2025-12-05**, while per-fund row counts vary widely
(110→1267) and first-dates track each fund's true inception (ENF 2014 … EVESG 2024). A flat-array
cap/pagination would show a *constant* row count and a uniform first-date; instead the array is
**complete from inception to a provider-wide cutoff**. So the wide fetch is correct and the staleness
is genuine systemic provider lag (the `get-nav-history` endpoint has no `page`/`pageSize`), not a
request/array-cap bug. `list_funds` shows current NAVs (e.g. VNDAF 19630.53) while history ends
2025-12-05 — exactly the silent-`EmptyData` scenario. → implement `StaleData`.

**Conditions of approval (fold into the coder spec):**
1. **Compute latest navDate from the PRE-window-filter row set** — track `max(_nav_row_date(r))` over
   ALL parsed rows BEFORE the `lo/hi` skip; do **NOT** run the #21 productId / #158 dup / value guards
   on out-of-window rows (that would reintroduce the #144 bug).
2. **Truncation ruled out first** (done — see probe). Implement `StaleData` regardless, for the
   genuinely-stale / closed-fund case (defensive, synthetic-tested).
3. **Message states the DATA GAP only**, not endpoint fault — must be true for a closed/delisted fund
   too: `"fmarket: NAV history for product {id} ends at {latest_navdate}, before requested {start}..{end}"`.
4. Add `StaleData` to `exceptions.__all__`; regenerate the surface snapshot **at release** (additive).

**Trigger (precise):** after the wide fetch + parse, when post-filter `points` is empty AND a window
start `lo` was given AND `max_navdate < lo` → raise `StaleData`. Otherwise `EmptyData` (unchanged) —
this keeps pre-inception windows and the sparse/weekend straddle (`lo <= max_navdate`) as `EmptyData`.

### #172 tests (synthetic, offline)

- stale history (rows end 2025) + bounded 2026 window → the chosen staleness signal (not bare `EmptyData`).
- correct wide request returns 2026 rows → bounded 2026 call returns them.
- genuinely pre-inception window → `EmptyData` (unchanged).
- #144/#158/#21 preserved: out-of-window rows/dups skipped before fatal guards; in-window conflict → `InvalidData`.

---

## #173 — bond fund holdings coverage / model gap

### Current behavior (recon)

`FMarketSource.holdings(product_id)` (`fmarket.py:256`) parses only `data.productTopHoldingList` into
`FundHolding(stock_code, weight_pct, …)` — an **equity** shape (`stockCode`, `netAssetPercent`). A
**bond fund** with empty `productTopHoldingList` (but non-empty bond holdings / asset allocation under
other provider fields) → `EmptyData`, indistinguishable from "no holdings". `FundSummary.asset_type`
already records the provider class (`STOCK`/`BOND`/…), so the entity type is known.

### Premise correction (reviewer review-202606201506 — MUST fold in before code)

The original design's premise ("non-empty **bond holdings** under other provider fields") is **not
supported by the blessed recon.** `docs/sources/funds-fmarket.md:121-139` documents the
`/res/products/{id}` detail payload as exactly three arrays:

- `productTopHoldingList` — **equity** rows (`stockCode`, `netAssetPercent`, `industry`, …)
- `productAssetHoldingList` — **asset-class split** (`assetType.code` ∈ {STOCK, CASH, BOND}, `assetPercent`)
- `productIndustriesHoldingList` — sector split

There is **NO `productBondHoldingList`** — no per-bond issuer/code/name/weight rows on this endpoint.
A bond fund exposes a **BOND allocation %**, not a typed list of bond securities. Therefore option A
(full typed per-bond `Holding`/`kind` model) is **over-scoped/speculative** (nothing to populate) →
**DEFERRED** (a real per-bond source, if ever found + license-cleared, is a separate clean-room design).

### Approved model (option B reframed, allocation-aware — the v1 contract)

1. **Kill the silent `EmptyData`** on the bond/empty path. When `productTopHoldingList` is empty/absent
   **AND** `productAssetHoldingList` shows a non-STOCK class (`BOND`/`CASH`) > 0% → raise
   `NonEquityHoldings(EmptyData)` (mirror the #172 `StaleData(EmptyData)` idiom for a consistent,
   backward-compatible signal) naming the non-equity allocation, e.g. `"fmarket: product {id} discloses
   asset-class allocation (BOND {x}%, CASH {y}%) but no per-security equity holdings; this source
   exposes no per-bond holdings list — see asset_allocation()"`.
2. **Expose the asset-class split as a primitive** via a **NEW sibling accessor**
   `funds.source().asset_allocation(product_id) -> AssetAllocation`, typed (class code + percent 0-100
   + as-of from `updateAt`), read directly from the source. **Do NOT mutate `holdings()`'s return
   type** (`tuple[FundHolding, ...]` must stay stable — changing it is a BREAKING surface change).
3. **Detect from the detail response itself**, NOT `Fund.asset_type` (`holdings(product_id)` takes only
   an int id and never sees `Fund.asset_type`, which comes from `list_funds`).
4. **Preserve genuine `EmptyData`** when `productTopHoldingList` AND `productAssetHoldingList` are both
   empty/absent (no false-positive diagnostic).
5. **Balanced/mixed funds** populate `productTopHoldingList` (equity rows) AND show BOND% — they already
   return equity holdings today; the new path is in the rows-empty branch only, so it does NOT fire.
6. **Update `docs/sources/funds-fmarket.md`** mapping table: `productAssetHoldingList`
   (`assetType.code`→class / `assetPercent`→percent 0-100), `updateAt` as-of semantics, a note that
   BOND appears only as an allocation % (no per-security disclosure), and the `NonEquityHoldings` error
   row. Same already-used endpoint — no scraping, no new endpoint, clean-room intact.

### #173 tests (synthetic, offline)

- bond fund: empty `productTopHoldingList` + `productAssetHoldingList` BOND>0% → `NonEquityHoldings`
  (an `EmptyData` subclass), NOT bare `EmptyData`; `asset_allocation()` returns the typed split.
- equity fund holdings unchanged; balanced fund (equity rows + BOND%) → `holdings()` returns equity
  rows as today (the new diagnostic does NOT fire).
- truly empty (no top-holdings AND no allocation) → `EmptyData` (unchanged, no false positive).
- malformed allocation rows/percent → fail closed (`InvalidData`).
- as-of/`updateAt` parsed or explicitly diagnosed if absent. Public-API additive (new exception +
  `AssetAllocation` model + accessor); snapshot regenerated additively.

---

## Cross-cutting

- **Source/legal:** documented Fmarket endpoints only; record provenance/terms for any new field/
  endpoint; no scraping. Public-API changes are additive (snapshot updated additively); private where
  possible.
- **Sequencing:** design-gate this doc → on APPROVE, implement (TDD, synthetic) — likely one fork for
  #172 and one for #173 (disjoint code paths: `nav_history` vs `holdings`), integrated separately →
  reviewer code review each → then proceed to #157.

## Resolved (reviewer picks, review-202606201506)

1. **#172 contract → A.** `StaleData(EmptyData)` typed exception naming the gap. C deferred.
2. **#173 v1 scope → B reframed (allocation-aware).** `NonEquityHoldings(EmptyData)` diagnostic +
   `asset_allocation()` accessor; full typed per-bond model A deferred (unbuildable from this source).
3. **Two separate commits/reviews** (disjoint paths: `nav_history` vs `holdings`/`asset_allocation`).
4. **Yes** — a `StaleData` exception subclass in public exceptions is acceptable (additive); use an
   `EmptyData` subclass for #173's diagnostic too.
