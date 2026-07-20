# Design/evidence note — #198 corporate fundamentals: inverted routing + broken catalog + pagination

- Status: **DESIGN REQUIRED (reviewer triage `triage-202607202156-issue198-corporate-fundamentals.md`,
  reviewer commit `d794c71`) — awaiting gate. No code changed.**
- Date: 2026-07-20
- Related: `docs/design/bank-fundamentals-itemcodes.md` + `docs/design/bank-itemcodes-probe-20260620.md`
  (#157, the sibling bank fix this mirrors); `docs/design/corporate-itemcodes-probe-20260720.md`
  (companion evidence artifact, live probe detail).

## 1. Problem & root cause

`vnfin/fundamentals/vndirect.py:55-59` (`_CORP_MODEL`) routes corporate `INCOME`→modelType `1` and
`BALANCE`→modelType `2`. **This is inverted**: modelType `1` is the balance sheet, modelType `2` is
the income statement (bank templates, `101/102/103`, are unaffected and correct). Independently
worse: the corporate name/code catalogs (`itemcodes.py:_NAMES_BY_MODEL_TYPE[1]`/`[2]`,
`metric_api.py`'s `corporate_code=` values) are not merely statement-swapped — **the numeric codes
themselves do not exist in the real provider data for the concepts they claim**. E.g. the current
catalog's `25000`/`30000`/`40000` ("total assets"/"total liabilities"/"equity") never appear anywhere
in a live corporate balance-sheet response; the real total-assets/liabilities/equity codes are
`12700`/`13000`/`14000` — the SAME numeric codes the bank templates already use (verified #157). The
catalog was evidently authored without ever querying the live corporate endpoint. Net effect: every
corporate `INCOME`/`BALANCE` metric currently either (a) resolves to `None` (the guessed code doesn't
exist), or (b) — more dangerously — resolves to a REAL value under the WRONG statement/concept label
(a plausible-looking number that is actually something else entirely), because a metric declared
`statement=INCOME` is fetched from real-balance data (modelType 1) or vice versa.

Independently, the tall/long statement endpoint is paginated (`currentPage`/`size`/`totalElements`/
`totalPages`) but the adapter (`vndirect.py:266-272,498-502`) requests one page sized `limit*80` and
never follows `page`/`totalPages` — a fiscal period wider than that budget is silently truncated
(reproduced live: VIC's newest annual balance period has 142 line items; the `limit=1` budget of 80
drops 62 of them, including `14000`/owners' equity, with no warning).

## 2. Evidence (live-probed 2026-07-20; full detail in the companion probe doc)

Companion: `docs/design/corporate-itemcodes-probe-20260720.md`. Summary — **every accounting
identity below holds to the exact VND**, on FPT/VIC/HPG/VNM (balance: 2 fiscal years each + 1
quarterly cross-check; income: latest FY each):

- **Balance (modelType 1):** `13000` (liab) + `14000` (equity) == `12700` (total assets). Also
  `11000` (current assets) + `12000` (non-current assets) == `12700`; `13100`+`13300`==`13000`;
  `14100`+`14300`==`14000`; `11100`+`11200`+`11300`+`11400`+`11500`==`11000`.
- **Income (modelType 2):** `21001` (net revenue) − `22100` (COGS) == `23100` (gross profit);
  `23800` (PBT) − `22070` (tax expense) == `23003` (PAT, total consolidated); `23000` (PAT
  attributable to parent) + `23500` (PAT attributable to non-controlling interests) == `23003`.
- The last identity **independently corroborates** the reviewer's flagged-open `23000` candidate
  (triage packet: "must be independently corroborated before shipping") — CONFIRMED: parent PAT.
- **Cross-statement bonus find:** cashflow's `37000` (not the currently-mapped `35000`) exactly
  matches balance-sheet `11100` (cash & equivalents) — proving the CURRENT `CASH_END_OF_PERIOD`
  mapping (`35000`) is ALSO wrong, independent of the routing-inversion bug.
- **Pagination:** live `size=80` against VIC's 142-item newest annual balance period silently drops
  `14000` (owners' equity); `page=2` returns the remaining 62 rows of the SAME date before the next
  date begins (confirms rows are grouped contiguously by `fiscalDate`, the load-bearing assumption
  behind the reviewer's stop condition).
- **Provider metadata quirk (new finding, not in the reviewer's original packet):** page 1's envelope
  carries `totalElements`/`totalPages`; **page ≥2's envelope OMITS both fields** (only `currentPage`/
  `size` remain). The pagination loop must cache `totalPages` from page 1 rather than re-reading it
  every page.
- Reproduced live via the adapter itself, not just raw queries: `scripts/probe_corporate_itemcodes.py`
  (`VNFIN_LIVE=1`) — on current `master` it **fails by design** (BALANCE request hits real-income
  modelType 2, INCOME request hits real-balance modelType 1 truncated to 80 rows), and must **PASS**
  once #198 ships (this is the regression check).

## 3. Proposed fix — routing (atomic swap, no aliasing)

```python
_CORP_MODEL = {
    StatementType.BALANCE: 1,
    StatementType.INCOME: 2,
    StatementType.CASHFLOW: 3,   # unchanged
}
```
`_BANK_MODEL` is untouched. No transition shim, no dual-read — per reviewer instruction ("do not add
two aliases over the inverted routing"), this is a hard atomic swap gated entirely behind the
TDD matrix (§6) and the reviewer's re-review, exactly mirroring the #157 bank hard-switch precedent.

## 4. Proposed fix — corporate itemCode/metric catalog (mapping table)

Every corporate `MetricSourceCodes.corporate_code` and every `itemcodes.py` corporate name-map entry
is replaced. Confidence follows the #157 bank-probe convention (HIGH = closed by an exact accounting
identity across ≥3 tickers; unlisted = left **raw/unmapped**, never guessed).

### Balance (modelType 1)

| Concept | Old (wrong) code | **New code** | Proof | Confidence |
|---|---|---|---|---|
| Total assets | `25000` | **`12700`** | `13000+14000==12700` (4 tickers × 2 FYs + 1Q) | HIGH |
| Total liabilities | `30000` | **`13000`** | same identity | HIGH |
| Owners' equity | `40000` | **`14000`** | same identity | HIGH |
| Current assets | `23000` | **`11000`** | `11100..11500` sum == `11000`; `11000+12000==12700` | HIGH |
| Current liabilities | `30100` | **`13100`** | `13100+13300==13000` | HIGH |
| Long-term liabilities | `30200` | **`13300`** | same | HIGH |
| Cash and equivalents | `23100` (was labeled BALANCE, is actually income gross-profit) | **`11100`** | sums into `11000`; EXACT match to cashflow `37000` | HIGH |

`12700`/`13000`/`14000` are **identical numeric codes to the already-verified bank codes** (#157) —
corporate and bank share this headline code space; only the surrounding template (`modelType`)
differs.

### Income (modelType 2)

| Concept | Old (wrong) code | **New code** | Proof | Confidence |
|---|---|---|---|---|
| Net revenue | `11000` | **`21001`** | magnitude sanity + reviewer anchor; feeds gross-profit identity | HIGH |
| Gross profit | `11200` | **`23100`** | `21001-22100==23100` (4/4 tickers exact) | HIGH |
| Profit before tax | `20000` | **`23800`** | `23800-22070==23003` (4/4 exact); same code as bank | HIGH |
| Net income (total, consolidated) | `21000` | **`23003`** | `23000+23500==23003` (4/4 exact) | HIGH |
| Net income (parent-attributable) | `21100` | **`23000`** | same split identity | HIGH |
| *(new, not previously in catalog)* | — | `23500` NCI/minority PAT | same split identity | HIGH (internal use only — not currently a public `MetricId`) |
| Operating profit | `14000` | *(none — leave unmapped)* | no closing identity found in the probed code set | **UNPROVEN — do not ship a guess** |

### Cash flow (modelType 3 — routing unchanged, out of P0 scope except one proven fix)

| Concept | Old code | **New code** | Proof | Confidence |
|---|---|---|---|---|
| Cash at end of period | `35000` | **`37000`** | EXACT match to balance-sheet `11100` | HIGH |
| Operating/investing/financing/net-change CF | `31000`/`32000`/`33000`/`34000` | *(no change proposed)* | `32000`/`33000` are structurally plausible section headers but do not close an identity against `34000` in the probed code set | **UNVERIFIED — gate question, see §7 Q3** |

### Bank (`101/102/103`) — untouched, unaffected by this issue.

## 5. Proposed pagination fix

Replace the single-page `size=limit*80` fetch with a bounded multi-page loop, reusing the EXISTING
per-date pivot/validation logic in `_build_statement_reports` unchanged (the loop's only job is to
gather the right SET of raw rows before handing them to that function):

```
page = 1
cached_total_pages = None      # captured from page 1 only (provider omits it on page >=2)
order = []                     # distinct fiscalDates seen, in stream order (desc)
all_rows = []                  # concatenated raw rows for the retained window
while True:
    resp = fetch(q=..., sort=fiscalDate:desc, size=PAGE_SIZE, page=page)
    validate resp is a dict with a list `data`  # existing _rows() contract
    if page == 1:
        cached_total_pages = require_int(resp, "totalPages")   # InvalidData if missing/non-int
    current_page = require_int(resp, "currentPage")            # present on every page (verified)
    for row in resp["data"]:
        fd = row["fiscalDate"]
        if fd not in order:
            order.append(fd)
        all_rows.append(row)
    if len(order) > limit:
        break     # first row of the (limit+1)-th distinct date observed -> prior `limit` dates complete
    if current_page >= cached_total_pages:
        break     # provider declares exhaustion -> whatever we have is everything there is
    page += 1

if len(order) > limit:
    boundary_fd = order[limit]                       # the (limit+1)-th date: INCOMPLETE, discard
    all_rows = [r for r in all_rows if r["fiscalDate"] != boundary_fd]

# hand `all_rows` to the existing _build_statement_reports(...) unchanged
```

- **Stop condition (reviewer invariant, verbatim):** the first row of fiscal date `limit+1` proves
  the first `limit` dates are complete (rows are contiguously grouped by `fiscalDate` in the
  `sort=fiscalDate:desc` stream — verified live, §2); OR the provider declares the final page.
- **Duplicate `(fiscalDate, itemCode)` across pages:** NOT re-implemented in the fetch loop — the
  existing `_build_statement_reports` duplicate-itemCode-within-a-date check (`vndirect.py:344-346`)
  already fires on the concatenated row list unchanged, since duplicated raw rows land in the same
  bucket regardless of which page they arrived on.
- **Fail-closed on transport/schema failure mid-pagination:** no try/except wraps the loop — an
  exception on any page (network, malformed envelope) propagates through the whole call, so a
  half-fetched multi-page request can never surface as a successful partial report.
- **Malformed pagination metadata:** a present-but-non-integer/missing `totalPages` on page 1, or a
  present-but-non-integer/missing `currentPage` on any page, raises `InvalidData` rather than
  looping forever or silently stopping early.
- **`PAGE_SIZE`:** keep the existing `_row_budget(limit)` heuristic as the per-page size (reduces
  round-trips for small `limit`); the fix is the multi-page LOOP, not a bigger single page (reviewer:
  "merely raising the single-page size to 1000 is not sufficient" — a `limit` spanning many periods
  can still exceed any fixed page size).

## 6. TDD matrix (build phase — not run yet)

- RED-first: corporate `income→2, balance→1, cashflow→3` model-type routing (regression for the
  inversion); bank `income→102, balance→101, cashflow→103` unchanged (regression).
- Exact `(statement_type, model_type, is_bank)` tuple assertions, not membership-in-six-numbers.
- Synthetic model-1 balance fixture: assets/liabilities/equity resolve via `12700`/`13000`/`14000`
  and the identity holds.
- Synthetic model-2 income fixture: net revenue/PBT/net income(parent)/net income(total)/net_margin
  resolve via `21001`/`23800`/`23000`/`23003`.
- Negative assertions: old `21000=net_income`/`25000=total_assets`/`20000=PBT`/etc. never resolve to
  those (wrong) meanings again.
- Pagination: `limit=1/2/8`; a fiscal date split across two pages (the VIC 80+62 case); exact-limit
  page exhaustion (provider's last page ends exactly on the `limit`-th date); malformed page-1
  metadata (`totalPages` missing/non-int) → `InvalidData`; malformed page≥2 `currentPage` →
  `InvalidData`; duplicate `(fiscalDate, itemCode)` reintroduced across two pages → `InvalidData`
  (reuses the existing per-date duplicate check); mid-pagination transport failure on page 2 →
  exception propagates, no partial success.
- End-to-end `metrics(..., source=injected_vndirect_source)` tests, not transformer-only fixtures.
- `scripts/probe_corporate_itemcodes.py` (`VNFIN_LIVE=1`, opt-in, not CI) must flip FAIL→PASS.
- Deterministic CI fixtures only (synthetic, no real provider rows bundled); run focused tests, full
  offline suite, warning-token/docs/public-surface gates on the merged tree.

## 7. Open questions for the reviewer gate

- **Q1 — Operating profit (§4 income table):** no closing identity found for the current
  `OPERATING_PROFIT` metric's code. Recommend: ship v1 **unmapped** (drop `corporate_code`, metric
  reports honest `MISSING` for corporates) rather than guess. Confirm/override?
- **Q2 — `NET_INCOME` code asymmetry:** corporate `NET_INCOME` now maps to `23003` (total consolidated
  PAT) while bank `NET_INCOME` maps to `23000` (bank's own PAT total) — same `MetricId`, intentionally
  different numeric code per source, because corporate `23000` means something different (parent-only)
  from bank `23000` (whole-entity PAT, no separately-broken-out NCI in the bank template). Confirm
  this is acceptable (mirrors how `PROFIT_BEFORE_TAX`/`TOTAL_ASSETS`/etc. already carry independent
  `corporate_code`/`bank_code` fields) — or should `NET_INCOME` for corporates instead resolve to
  `23000` (parent) to match `NET_INCOME_PARENT`'s existing separate metric becoming redundant?
  Design leans: keep `NET_INCOME`=total(`23003`)/`NET_INCOME_PARENT`=parent(`23000`) — distinct,
  useful metrics, matches how `NET_INCOME_PARENT` already exists in the v1 catalog for exactly this
  purpose.
- **Q3 — Corporate cashflow headline codes (`31000`/`32000`/`33000`/`34000`):** routing (modelType 3)
  is unaffected by this P0 bug and out of scope for #198's blocking fix. The current codes are
  UNVERIFIED (not proven wrong, but not proven right either — `32000`/`33000` are structurally
  plausible headers that don't close an identity against `34000` in the probed set). Recommend:
  (a) leave `OPERATING_CASH_FLOW`/`INVESTING_CASH_FLOW`/`FINANCING_CASH_FLOW`/`NET_CASH_FLOW`
  UNCHANGED (no active proof they're wrong, no active proof they're right) and file a NON-BLOCKING
  follow-up for a dedicated cashflow-code identity audit (mirrors the #157 Q3 precedent: bank
  cashflow shipped fully-raw in v1 for the same reason); (b) fix ONLY `CASH_END_OF_PERIOD`
  (`35000`→`37000`, exact cross-statement proof) in this same change since it's cheap and
  high-confidence. Confirm this split, or require the full cashflow audit before shipping #198?
- **Q4 — `itemcodes.py` sub-line names below headline (`11200`/`11300`/`11400`/`11500` etc.):** these
  are proven only via an AGGREGATE sum identity (their total equals `11000`), not individually
  identity-proven per line (unlike bank's #157 approach of only mapping individually-verified codes).
  Recommend: map them at MEDIUM confidence with an explicit code comment citing the aggregate proof
  (matches typical VN statement line order: cash, ST investments, ST receivables, inventories, other
  CA) since they're internal display-only `LineItem.name` strings, not `MetricId` codes consumed by
  `metrics()`/formulas — or leave them raw pending individual proof? Design leans: map at MEDIUM
  (display-only blast radius, not metric-correctness), documented as such.

No code, tests, or docs changed in this note — evidence-gathering + proposal only, per the reviewer's
"design/evidence gate first" instruction.
