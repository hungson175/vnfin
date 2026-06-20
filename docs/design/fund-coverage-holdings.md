# Design — Fmarket fund coverage & holdings diagnostics (#172 + #173)

**Status:** SHIPPED. #172 = option A (`StaleData(EmptyData)`, defer C) — shipped. #173 = **option A**
(live-probe flip, review-202606201528: `productTopHoldingBondList` exists → `holdings()` merges equity +
bond rows + `asset_allocation()` accessor; the earlier "option B reframed" / `NonEquityHoldings` was
dropped) — shipped, micro-decisions approved review-202606201557. A **batch** of two related Fmarket
fund-data-quality bugs the reviewer asked to design together **before** the large #157 feature.
**Reviewer specs:** review-202606201432 (#172 NAV staleness) + review-202606201436/...1528 (#173 bond holdings).
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

## #173 — bond fund holdings coverage / model gap  — SHIPPED (Option A)

### Original behavior (recon)

`FmarketSource.holdings(product_id)` parsed **only** `data.productTopHoldingList` into
`FundHolding(stock_code, weight_pct, …)` — an **equity** shape (`stockCode`, `netAssetPercent`). A
**bond fund** (empty `productTopHoldingList`) → `EmptyData`, indistinguishable from "no holdings". This
was a **category-wide blind spot** (22 BOND funds + at-par BALANCED funds returned bare `EmptyData`).

### Premise correction — Option A (reviewer live-probe, review-202606201528)

The earlier recon premise ("no per-bond list; bond funds expose only a BOND allocation %") was **WRONG**.
A reviewer live-probe of `/res/products/{id}` showed the detail payload carries **a fourth array**:

- `productTopHoldingList` — **equity** rows (`stockCode`, `netAssetPercent`, `industry`, `price`, `type`, `updateAt`)
- **`productTopHoldingBondList`** — **per-bond** rows with the SAME shape (`stockCode` = bond code e.g.
  `BAF126003`, `netAssetPercent`, `industry`, `price` null, `type:"BOND"`, `updateAt`)
- `productAssetHoldingList` — **asset-class split** (`assetType.code` ∈ {STOCK, CASH, BOND}, `assetPercent`)
- `productIndustriesHoldingList` — sector split

So per-bond holdings ARE disclosed under `productTopHoldingBondList`. **There is NO
`productBondHoldingList`** key (the bond list key is `productTopHoldingBondList`) — do not look for the
former name. The full typed per-security model (Option A) is therefore buildable from this source.

### Shipped model (Option A — the v1 contract)

1. **`holdings()` merges both line-item lists.** It now parses `productTopHoldingList` (equity, first)
   **and** `productTopHoldingBondList` (bonds), reusing one row parser. The return type stays
   `tuple[FundHolding, ...]` (no breaking change). A bond/balanced fund now returns its real positions.
2. **`FundHolding.instrument_type`** (`"STOCK"`/`"BOND"`, appended field, default `"STOCK"`) tags each
   row. A row's own `type` is validated against `{STOCK, BOND}` and **fails closed if unrecognized**
   (a holdings tuple has no per-row warning channel — never silently mislabel); an absent `type` falls
   back to the per-list default (equity list → STOCK, bond list → BOND).
3. **`FundHolding.as_of_utc`** (appended, default `None`) carries the provider's per-row `updateAt`
   (epoch-**ms** → tz-aware UTC; absent/malformed → `None`, never a fabricated `now()`), so a holdings
   tuple is no longer freshness-blind.
4. **One dedup set + combined weight guard span BOTH lists.** The same code in equity and bond is a
   provider self-inconsistency → `InvalidData`; aggregate weight > 100% (equity + bond) → `InvalidData`.
5. **`EmptyData` fires only when BOTH lists are empty/absent** (the fund has published no holdings yet).
6. **New sibling accessor** `funds.source().asset_allocation(product_id) -> AssetAllocation` exposes the
   asset-class split (`productAssetHoldingList`) typed (class code ∈ {STOCK, BOND, CASH} fail-closed,
   percent 0-100, `as_of_utc` = freshest row `updateAt`). Disclosed weights are **not** forced to sum to
   100% (partial disclosure allowed). New `AssetAllocation` + `AssetClassWeight` models.
7. **#21 identity guard** (the detail doc must identify the requested fund) is shared by both accessors
   via `_fetch_detail_data`. Same already-used endpoint — no scraping, no new endpoint, clean-room intact.

### #173 tests (synthetic, offline)

- bond-only fund (equity `[]` + bond list populated) → `holdings()` returns the bond rows, all
  `instrument_type == "BOND"`, `price_raw is None`.
- balanced fund (equity + bond rows) → combined, equity first, types tagged correctly.
- equity fund holdings unchanged + now carry `instrument_type == "STOCK"`.
- both lists empty/absent → `EmptyData`; malformed bond row / non-array bond list → `InvalidData`;
  combined weight > 100% → `InvalidData`; same code across lists → `InvalidData`.
- per-holding `as_of_utc` from `updateAt`; malformed `updateAt` → `None` (no fabricated now()).
- `asset_allocation()` returns typed split, uses `/res/products/{id}`, `as_of_utc` = max row `updateAt`,
  empty/absent → `EmptyData`, unknown class / malformed percent → `InvalidData`, partial sum < 100% ok.
- Public-API **additive** (two appended `FundHolding` fields + `AssetAllocation`/`AssetClassWeight`
  models + `asset_allocation` method); snapshot regenerated additively at release time only.

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
2. **#173 v1 scope → A (live-probe flip, review-202606201528).** `productTopHoldingBondList` exists, so
   `holdings()` merges equity + bond rows into the typed `FundHolding` model (with `instrument_type` +
   `as_of_utc`), plus a sibling `asset_allocation()` accessor. The earlier B-reframe / `NonEquityHoldings`
   diagnostic was **dropped** — Option A returns the real bond rows, so no diagnostic exception is needed.
3. **One combined #173 change** (`holdings()` + `asset_allocation()` share the detail endpoint + identity
   guard); reviewer Codex×2 on the diff.
4. **Yes** — a `StaleData` exception subclass in public exceptions is acceptable (additive).
