# Design — Fmarket fund coverage & holdings diagnostics (#172 + #173)

**Status:** DESIGN — reviewer gate (must be APPROVED before code). A **batch** of two related Fmarket
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

**Decision needed (pick one):**
- **(A) typed staleness exception** — a distinct error (e.g. a new `StaleData` subclass of `EmptyData`
  so existing `except EmptyData` callers still catch it, but the type/message name the gap:
  `"fmarket: NAV history for product {id} is stale — latest {latest_navdate} is before requested
  {start}..{end}"`). Fail-loud, consistent with the library; actionable.
- **(B) annotated result** — return a `NavHistory` with the available (pre-window) latest carried as
  `latest_available_navdate` metadata + a `stale_history` warning, and... (awkward: callers expect
  in-window points; an empty-but-annotated history is easy to misuse).
- **(C) offline diagnostic** — keep `EmptyData` on the live call but add
  `vnfin.diagnostics.explain_fund_nav_coverage(...)` to explain staleness preflight.

**My lean: (A)** — a `StaleData(EmptyData)` subclass keeps backward compatibility (still an
`EmptyData`) while making the stale case distinguishable + actionable; optionally add (C) later. Please
confirm (A) vs (B) vs (A+C).

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

### Investigation

Map the `/res/products/{id}` response: which fields carry bond holdings (issuer/code/name/industry/
weight) and the asset-allocation split (stock/bond/cash %), and the as-of/update metadata. Record
provenance/terms before relying on any field.

### Proposed model (additive — the decision)

Do **not** force bonds into the equity `stock_code` shape. Options:

- **(A) typed holdings model (full fix):** add a `security_type`/`kind` enum (`EQUITY`/`BOND`/`CASH`/
  `OTHER`) and a typed `Holding(kind, code, name, weight_pct, industry=None, …)`; keep `FundHolding`
  (equity) working; add an `AssetAllocation` (class split %) + as-of metadata; surface bond holdings +
  split via the holdings path (or a sibling accessor). Larger, but the real fix.
- **(B) explicit diagnostic v1 (smaller):** keep `holdings()` equity-only, but when the fund has
  **non-equity** holdings the API doesn't map (detectable via `asset_type`/the presence of bond
  fields), return an explicit `"source has non-equity (bond/...) holdings not mapped by this API"`
  diagnostic instead of plain `EmptyData`; design the typed model (A) as the follow-up.

**My lean: confirm v1 scope with the reviewer.** Given the batch is "before #157," I lean **(B) for
the immediate bug** (stop the silent `EmptyData`, ship the diagnostic + asset-allocation split if
trivially available) + **(A) typed bond-holdings model as a fast follow-up** — unless you want the
full typed model now. Either way: preserve equity behavior + product-id/code guards; additive
public-API snapshot.

### #173 tests (synthetic, offline)

- bond fund: empty equity `productTopHoldingList` + non-empty bond holdings → NOT a bare `EmptyData`
  (either typed bond holdings (A) or the explicit non-equity diagnostic (B)).
- equity fund holdings unchanged.
- malformed bond rows/weights fail closed (or are diagnosed per the chosen model).
- as-of/update metadata parsed or explicitly diagnosed if absent.

---

## Cross-cutting

- **Source/legal:** documented Fmarket endpoints only; record provenance/terms for any new field/
  endpoint; no scraping. Public-API changes are additive (snapshot updated additively); private where
  possible.
- **Sequencing:** design-gate this doc → on APPROVE, implement (TDD, synthetic) — likely one fork for
  #172 and one for #173 (disjoint code paths: `nav_history` vs `holdings`), integrated separately →
  reviewer code review each → then proceed to #157.

## Open questions for the reviewer

1. **#172 contract:** (A) `StaleData(EmptyData)` typed exception naming the gap [my lean] / (B)
   annotated empty result / (A+C with an offline `explain_fund_nav_coverage`)?
2. **#173 v1 scope:** (A) full typed bond-holdings + asset-split model now / (B) explicit non-equity
   diagnostic now + typed model as fast follow-up [my lean]?
3. Should #172 and #173 ship as **two separate commits/reviews** (disjoint paths) or one batch?
4. For #172, is adding a **`StaleData` exception subclass** to the public exceptions acceptable
   (additive), or prefer keeping it within `EmptyData` + a warning?
