# Design/evidence note — #198 corporate fundamentals: inverted routing + broken catalog + pagination

- Status: **DESIGN RE-GATE REQUESTED (round 3).** Revised against reviewer round-1 gate
  `reviews/gate-202607202233-issue198-design-note.md` (`0345fcc`, B1–B10) **and** round-2 gate
  `reviews/gate-202607212049-issue198-regate-round2.md` (`bf60ecb`, R1–R7) — all addressed below
  (R1 empty-page seam, R2 source-aware tuple guard, R3 pagination helper contracts, R4 count/`12000`
  reconciliation, R5 probe oracle + tuple assertion + all-tickers, R6 five derived metrics, R7
  primary-source provenance). **No package runtime code or tests changed** (evidence + design only;
  two docs + one executable probe script).
- Binding spec: `reviews/triage-202607202156-issue198-corporate-fundamentals.md` (reviewer `d794c71`).
- Date: 2026-07-20 (revised 2026-07-21).
- Related: `docs/design/bank-fundamentals-itemcodes.md` + `docs/design/bank-itemcodes-probe-20260620.md`
  (#157, the sibling bank fix this mirrors); `docs/design/corporate-itemcodes-probe-20260720.md`
  (companion evidence artifact — exact-VND values + official-filing cross-check per code).

## 1. Problem & root cause

Three independent defects on the corporate (non-bank) path; bank templates `101/102/103` are correct
and untouched throughout.

1. **Routing inverted.** `vnfin/fundamentals/vndirect.py:54-58` (`_CORP_MODEL`) maps
   `INCOME→1, BALANCE→2`. Live probe proves modelType `1` is the **balance sheet** and `2` is the
   **income statement** (§2). So a metric declared `statement=INCOME` is fetched from real-balance
   rows and vice-versa.
2. **Catalog codes wrong.** The corporate `MetricSourceCodes.corporate_code` values
   (`metric_api.py:133-182`) and the `itemcodes.py:_NAMES_BY_MODEL_TYPE` corporate name maps do not
   merely swap statements — the numeric codes do not exist for the concepts they claim. E.g. the
   catalog's `25000`/`30000`/`40000` ("total assets/liabilities/equity") never appear in a live
   corporate balance response; the real codes are `12700`/`13000`/`14000` (the same headline code
   space the bank templates use, verified #157). Net effect: every corporate INCOME/BALANCE metric
   currently resolves to `None`, or worse to a REAL value under the WRONG concept label — a
   plausible-looking number that is actually something else.
3. **Pagination truncates.** The tall/long statement endpoint is paginated but the adapter
   (`vndirect.py:_fetch_statement_rows`) requests one page sized `_row_budget(limit)` and never
   follows `page`/`totalPages`. A fiscal period wider than one page is silently truncated —
   reproduced live: VIC's newest annual balance period has **142** line items; a `size=80` page drops
   62 of them including `14000` (owners' equity), with no warning (§2, §8).

## 2. Evidence (live-probed 2026-07-20/21; exact-VND detail in the companion probe doc)

Companion `docs/design/corporate-itemcodes-probe-20260720.md` now records, for **FPT/VIC/HPG/VNM**:
(a) the **exact-VND** value of every retained code; (b) each accounting identity with an **exact
integer residual of `0`** (not a tolerance); (c) an **official-filing cross-check** naming each
operand against the issuer's own audited consolidated statements (FPT FY2025 full matrix; VIC FY2024
for the parent/NCI split and the reviewer's total-assets/equity anchor). Summary:

- **Balance (modelType 1):** `13000+14000==12700`; `11000+12000==12700`; `13100+13300==13000`;
  `14100+14300==14000`; `11100+11200+11300+11400+11500==11000` — all **exact-0 on all 4 tickers**.
- **Income (modelType 2):** `21001−22100==23100`; `23800−22070==23003`; `23000+23500==23003` — all
  **exact-0 on all 4 tickers**. The last independently confirms `23000`=parent PAT, `23500`=NCI PAT.
- **Cash flow (modelType 3):** `32000+33000+34000==35000` and `35000+36000+36100==37000` — both
  **exact-0 on all 4 tickers** (the standard IAS-7 reconciliation: net-change + begin-cash + FX =
  end-cash). `31000` does not exist in the probed periods.
- **Pagination + metadata quirk (live-confirmed 2026-07-21):** VIC balance page 1 (`size=80`) returns
  only date `2025-12-31` with `14000` **absent**; page-1 envelope carries
  `currentPage/size/totalElements/totalPages` (`totalPages=33`); **page ≥2 omits `totalPages` and
  `totalElements`** (only `currentPage`/`size` remain); dates are **contiguous and strictly
  descending** across pages (`2025-12-31` spans pages 1–2, then `2024-12-31`), and `currentPage` is
  present on every page.

**Identity vs. naming (reviewer B1):** an equality proves the operands participate in a relationship;
it does not by itself name which operand is "current assets" or "operating cash flow". Every retained
code is therefore additionally cross-checked to an **official issuer filing** in the probe doc;
unproven codes are left raw/unmapped (never guessed).

## 3. Fix — routing (atomic swap, no aliasing)

```python
_CORP_MODEL = {
    StatementType.BALANCE: 1,
    StatementType.INCOME: 2,
    StatementType.CASHFLOW: 3,   # unchanged
}
```
`_BANK_MODEL` untouched. Hard atomic swap, no transition shim (reviewer: "do not add two aliases"),
gated entirely behind the TDD matrix (§11) and re-review — mirrors the #157 bank hard-switch.

## 4. Fix — corporate itemCode/metric catalog (`metric_api.py`)

Every corporate `MetricSourceCodes.corporate_code` is replaced. **Proof** = exact identity (4 tickers)
**and** an official-filing line cross-check (probe doc). Bank codes are byte-for-byte unchanged.

### Balance (modelType 1)

| MetricId | Concept | Old code | **New code** | Confidence |
|---|---|---|---|---|
| `TOTAL_ASSETS` | Total assets | `25000` | **`12700`** | HIGH |
| `TOTAL_LIABILITIES` | Total liabilities | `30000` | **`13000`** | HIGH |
| `OWNERS_EQUITY` | Owners' equity | `40000` | **`14000`** | HIGH |
| `CURRENT_ASSETS` | Current assets | `23000` | **`11000`** | HIGH |
| `CURRENT_LIABILITIES` | Current liabilities | `30100` | **`13100`** | HIGH |
| `LONG_TERM_LIABILITIES` | Long-term liabilities | `30200` | **`13300`** | HIGH |
| `CASH_AND_EQUIVALENTS` | Cash & equivalents | `23100` | **`11100`** | HIGH |

`TOTAL_ASSETS`/`TOTAL_LIABILITIES`/`OWNERS_EQUITY` are `AppliesTo.BOTH`; only the `corporate_code`
changes (bank `12700`/`13000`/`14000` unchanged — corporate and bank share this headline code space).

### Income (modelType 2)

| MetricId | Concept | Old code | **New code** | Confidence |
|---|---|---|---|---|
| `NET_REVENUE` | Net revenue | `11000` | **`21001`** | HIGH |
| `GROSS_PROFIT` | Gross profit | `11200` | **`23100`** | HIGH |
| `PROFIT_BEFORE_TAX` | Profit before tax | corp `20000` | **corp `23800`** | HIGH |
| `NET_INCOME` | Net income (total consolidated PAT) | corp `21000` | **corp `23003`** | HIGH |
| `NET_INCOME_PARENT` | Net income (parent-attributable PAT) | `21100` | **`23000`** | HIGH |
| `OPERATING_PROFIT` | Operating profit | `14000` | **`None` → BLOCKED (§5)** | UNMAPPED |

`PROFIT_BEFORE_TAX`/`NET_INCOME` are `AppliesTo.BOTH`; bank codes (`23800`/`23000`) unchanged. Note
`NET_INCOME` corp `23003` (total) ≠ `NET_INCOME_PARENT` corp `23000` (parent) — see Q2 (§12, ruling
ACCEPT). `23500` (NCI PAT) is identity-proven but is **not** promoted to a public `MetricId` in #198.

### Cash flow (modelType 3) — full audit (reviewer B4, ruling reject-the-status-quo)

| MetricId | Concept | Old code | **New code** | Confidence |
|---|---|---|---|---|
| `OPERATING_CASH_FLOW` | Net CF from operating | `31000` | **`32000`** | HIGH |
| `INVESTING_CASH_FLOW` | Net CF from investing | `32000` | **`33000`** | HIGH |
| `FINANCING_CASH_FLOW` | Net CF from financing | `33000` | **`34000`** | HIGH |
| `NET_CASH_FLOW` | Net change in cash | `34000` | **`35000`** | HIGH |
| `CASH_END_OF_PERIOD` | Cash at end of period | `35000` | **`37000`** | HIGH |

The old catalog shifted every section under the wrong metric (old `OPERATING_CASH_FLOW=31000` does not
exist; old `INVESTING=32000` is actually **operating**, etc.). Both cash-flow identities close exact-0
on all 4 tickers, and the individual operating/investing/financing section meanings are cross-checked
against an official issuer cash-flow statement in the probe doc. If any single section fails the
official cross-check, that metric is unmapped via the §5 BLOCKED contract instead — under no outcome
does the old shifted mapping remain.

### Bank (`101/102/103`) — untouched, unaffected by this issue.

## 5. Unmapped-code contract — honest BLOCKED, never guess (reviewer B2, ruling ACCEPT Q1)

Today `_code_for` returns `None` for an unmapped corporate metric and `metric_api.py:498-503` folds
that into `MISSING` with reason `missing line item None in income` — falsely describing an upstream
absence. Split the branch:

```python
code = _code_for(defn, source, is_bank)          # None when this entity type has no verified code
if code is None:
    return _unavailable(defn, MetricAvailability.BLOCKED, fiscal_date,
        REASON_METRIC_CODE_UNMAPPED.format(id=defn.id.value, source=source,
                                           entity=("bank" if is_bank else "corporate")))
line = _line_for(report, code)                   # search report.items for the code
if line is None:                                 # code IS mapped but genuinely absent upstream
    return _unavailable(defn, MetricAvailability.MISSING, fiscal_date,
        REASON_MISSING_LINE_ITEM.format(code=code, statement=st_value))
```

- New reason constant:
  `REASON_METRIC_CODE_UNMAPPED = "metric '{id}' has no verified code for source '{source}' and {entity} entities"`.
- Availability = **`BLOCKED`** (the statement exists; the library lacks a verified mapping). **Not**
  `UNSUPPORTED` (reserved for future valuation primitives) and **not** `MISSING` (which means the
  provider omitted a mapped line).
- `OPERATING_PROFIT` is the only #198 metric set to `corporate_code=None`. It feeds **no** derived
  metric (there is no `OPERATING_MARGIN` in `_V1_CATALOG`), so real-world propagation is nil; the
  existing input-BLOCKED→BLOCKED rule (`metric_api.py:546-556`) is nonetheless exercised by a
  synthetic derived-propagation test so the mechanism is proven for the `None`-code case.

## 6. `itemcodes.py` name map — only official-correlated labels (reviewer B5, ruling REJECT Q4)

`LineItem.name` is public financial semantics. Only codes whose label is **individually** confirmed by
an official filing get a name; every other code (including aggregate-only sub-lines) stays the honest
raw `item_<code>`. The corporate blocks of `_NAMES_BY_MODEL_TYPE` are replaced in full with exactly:

```python
# ----- Corporate BALANCE sheet (modelType 1) -----
1: {
    "12700": "Tổng cộng tài sản",            # total assets
    "13000": "Nợ phải trả",                  # total liabilities
    "14000": "Vốn chủ sở hữu",               # owners' equity
    "11000": "Tài sản ngắn hạn",             # current assets
    "12000": "Tài sản dài hạn",              # non-current assets
    "13100": "Nợ ngắn hạn",                  # current liabilities
    "13300": "Nợ dài hạn",                   # long-term liabilities
    "11100": "Tiền và các khoản tương đương tiền",  # cash & equivalents
},
# ----- Corporate INCOME statement (modelType 2) -----
2: {
    "21001": "Doanh thu thuần",              # net revenue
    "22100": "Giá vốn hàng bán",             # cost of goods sold
    "23100": "Lợi nhuận gộp",                # gross profit
    "23800": "Tổng lợi nhuận kế toán trước thuế",   # profit before tax
    "22070": "Chi phí thuế TNDN",            # income tax expense
    "23003": "Lợi nhuận sau thuế TNDN",      # profit after tax (total consolidated)
    "23000": "LNST của cổ đông công ty mẹ",  # PAT attributable to parent
    "23500": "LNST của cổ đông không kiểm soát",    # PAT attributable to NCI
},
# ----- Corporate CASH FLOW (modelType 3) -----
3: {
    "32000": "Lưu chuyển tiền thuần từ HĐ kinh doanh",  # operating
    "33000": "Lưu chuyển tiền thuần từ HĐ đầu tư",      # investing
    "34000": "Lưu chuyển tiền thuần từ HĐ tài chính",   # financing
    "35000": "Lưu chuyển tiền thuần trong kỳ",          # net change in cash
    "36000": "Tiền và tương đương tiền đầu kỳ",         # cash at beginning of period
    "36100": "Ảnh hưởng của thay đổi tỷ giá",           # FX effect
    "37000": "Tiền và tương đương tiền cuối kỳ",        # cash at end of period
},
```

The aggregate current-asset sub-lines `11200`/`11300`/`11400`/`11500` are **left raw** (`item_<code>`):
their sum equals `11000` but the aggregate identity does not identify each component individually, and
no official line was correlated to each in this pass. (A future non-blocking issue may add them if
each is individually official-confirmed.) The exact final label strings are pinned by the official
cross-check in the probe doc; any label the cross-check does not confirm is dropped to `item_<code>`.

**Count reconciliation (reviewer R4):** this map names **23** provider codes (8 balance incl. `12000`
non-current assets, 8 income, 7 cash flow). All 23 are cross-checked to the official filings in the
probe doc — **22 map 1:1 to a single printed official line; `22070` is the exact net of two disclosed
tax lines** (current tax mã 51 − deferred-tax benefit mã 52). The FPT evidence matrix therefore lists
23 rows (the earlier 22-row/omitted-`12000` matrix is corrected there).

## 8. Pagination + row-stream + metadata guards (reviewer B6 + B7)

Replace the single-page fetch in `_fetch_statement_rows` with a bounded, validated multi-page loop.
The loop's only job is to gather the correct SET of raw rows, then hand them to the existing
`_build_statement_reports` unchanged. All validation happens **before** any row affects the stop
condition.

**Helper contracts (reviewer R3 — all defined at the raw-envelope boundary; none reuse a lenient
existing parser):**

- `_require_raw_int(obj, key) -> int` — `key` must be present and its value a **raw, non-bool
  `int`**. `True`/`False` (bool is an int subclass), a `float` (incl. `1.0`), a numeric `str`
  (`"1"`), and an absent key all raise `InvalidData`. (Does **not** reuse `parse_canonical_int`,
  which accepts numeric strings.)
- `_require_iso_fiscal_date(row) -> str` — `row["fiscalDate"]` must be present and an **exact
  unpadded `YYYY-MM-DD` string** (`re.fullmatch(r"\d{4}-\d{2}-\d{2}")` **and** a real calendar date
  via `validate_iso_date_string`); a `date` object, a padded/whitespace string, or an absent key
  raises `InvalidData`. The returned canonical string is the grouping/retention key throughout, so
  the final membership filter never mismatches a normalized vs. raw form. (Does **not** reuse
  `validate_iso_date_string` directly, which returns a `date` and tolerates padding/date objects.)
- `_require_item_code(row) -> str` — `row["itemCode"]` must be present; normalized with the **same**
  rule the row parser uses (`str(int(11200.0)) == "11200"`); an absent key or non-coercible value
  raises `InvalidData`.

```
PAGE_SIZE = _row_budget(limit)
page = 1
cached_total_pages = None          # captured on page 1 only (provider omits it on page >= 2)
order = []                         # distinct canonical fiscalDate strings, stream order (strictly desc)
closed = set()                     # dates whose contiguous group has ended
seen_keys = set()                  # (fiscalDate, itemCode) across ALL fetched rows
last_fd = None
all_rows = []                      # (raw_row, canonical_fd) pairs

while True:
    resp = self._fetch_json(...page=page, size=PAGE_SIZE)
    # --- B8 empty-page semantics AT THE ACTUAL _rows() SEAM (reviewer R1) ---
    # _rows() RAISES EmptyData on []; it never returns an empty list. So catch it
    # exactly here and translate by page position (page-1 EmptyData is preserved
    # for the existing AUTO failover; page>=2 becomes InvalidData, which AUTO does
    # not catch and therefore cannot recast as a template miss).
    try:
        data = self._rows(resp)                 # dict-envelope + list contract; raises EmptyData/[]
    except EmptyData:
        if page == 1:
            raise                                # template miss -> existing failover
        raise InvalidData(f"{self.name}: empty page {page} after a non-empty page 1")
    # --- B6 metadata identity (raw, canonical, non-bool ints only) ---
    current_page = _require_raw_int(resp, "currentPage")
    if page == 1:
        cached_total_pages = _require_raw_int(resp, "totalPages")
        if cached_total_pages < 1: raise InvalidData(...)          # page-1 totalPages >= 1
    elif "totalPages" in resp:                                     # later pages MAY omit it (verified)
        if _require_raw_int(resp, "totalPages") != cached_total_pages: raise InvalidData(...)
    if current_page != page: raise InvalidData(...)               # repeated/ahead header -> raise, never loop
    if not (1 <= current_page <= cached_total_pages): raise InvalidData(...)
    # --- B7 row-stream validation BEFORE it can affect the stop condition ---
    for row in data:
        row = require_object(row, ...)                            # non-object row -> InvalidData
        fd  = _require_iso_fiscal_date(row)                       # present + exact YYYY-MM-DD; else InvalidData
        code = _require_item_code(row)                            # present + canonical; else InvalidData
        if fd != last_fd:                                         # new date group
            if fd in closed: raise InvalidData(...)               # reappearing closed date
            if last_fd is not None:
                if fd >= last_fd: raise InvalidData(...)          # must be strictly descending
                closed.add(last_fd)                               # previous group closes
            if fd not in order: order.append(fd)
            last_fd = fd
        if (fd, code) in seen_keys: raise InvalidData(...)        # duplicate across ALL fetched rows
        seen_keys.add((fd, code))
        all_rows.append((row, fd))
    # --- stop conditions (use VALIDATED order) ---
    if len(order) > limit: break                # first row of the (limit+1)-th date -> newest `limit` complete
    if current_page >= cached_total_pages: break  # provider declares exhaustion
    page += 1

# retain ONLY the newest `limit` distinct dates (drops limit+1, limit+2, ... — one page may hold several),
# filtering on the CANONICAL fd captured above (never a re-read raw string)
keep = set(order[:limit])
rows_out = [raw for (raw, fd) in all_rows if fd in keep]
# hand `rows_out` to _build_statement_reports(...) unchanged
```

- **Finite (B6):** every fetch requests the local `page`; termination is bounded by
  `cached_total_pages` (page-1 `totalPages`), and a header that does not equal the requested page or
  falls outside `[1, cached_total_pages]` raises immediately. A repeated page-1 header or an ahead/
  out-of-range header can never masquerade as exhaustion.
- **Row-stream validated before it counts (B7):** a malformed/non-object row, a non-ISO or
  out-of-order or reappearing `fiscalDate`, or a duplicate `(fiscalDate, itemCode)` across any pages
  raises **before** it can inflate `order` past `limit` and cause a partial success. Contiguous,
  strictly-descending date groups are enforced across page boundaries.
- **Correct retention (B7):** rows are filtered to the newest `limit` distinct dates, not merely by
  dropping the single boundary date — so a page containing dates `limit+2` and older is handled.
- **Fail-closed:** the only `try/except` is the narrow `EmptyData` seam above (page-1 re-raise /
  page≥2→`InvalidData`); it catches nothing else, so any transport error or other schema failure on
  any page propagates unchanged and a half-fetched multi-page request never surfaces as a successful
  partial report.
- `PAGE_SIZE` keeps the `_row_budget(limit)` heuristic as the per-page size; the fix is the multi-page
  LOOP, not a larger single page (a `limit` spanning many periods can exceed any fixed page size).

## 9. Empty later page = schema failure, not source absence (reviewer B8)

`_rows()` raises `EmptyData` on an empty list, and the AUTO path (`_get_statements_auto`) treats
`EmptyData` as "try the other template". That is valid only for **page 1**. An empty page ≥2 after a
non-empty page 1 must raise **`InvalidData`** (§8), which — being distinct from `EmptyData` — is not
caught by the AUTO `except EmptyData` handler and therefore propagates, so a partial fetch is never
recast as a clean template miss / failover.

## 10. Statement/entity/model tuple guard (reviewer B9)

Replace the pure membership check in `client.py:_validate_fundamental_result`
(`mt not in _CANONICAL_MODEL_TYPES`, six numbers) with **source-aware relational** validation that
branches on `report.source` — the prior draft branched only on `model_type is not None`, which wrongly
accepted (a) a VNDirect *statement* report tagged `model_type=None` and (b) a non-VNDirect report
carrying a canonical VNDirect model type (reviewer R2). The exact contract:

```python
_VNDIRECT = "vndirect"
_EXPECTED_MODEL_TYPE = {   # VNDirect STATEMENT templates only (RATIOS has no template)
    (StatementType.BALANCE,  False): 1,   (StatementType.BALANCE,  True): 101,
    (StatementType.INCOME,   False): 2,   (StatementType.INCOME,   True): 102,
    (StatementType.CASHFLOW, False): 3,   (StatementType.CASHFLOW, True): 103,
}
mt = report.model_type
if report.source == _VNDIRECT and statement in (BALANCE, INCOME, CASHFLOW):
    # VNDirect statements MUST carry exactly the registered (statement, is_bank) -> model tuple.
    expected = _EXPECTED_MODEL_TYPE[(statement, report.is_bank)]
    if isinstance(mt, bool) or mt != expected:            # None, wrong int, or bool all fail
        return (f"vndirect {statement.value} report for a "
                f"{'bank' if report.is_bank else 'corporate'} entity must carry model_type "
                f"{expected}, got {mt!r}")
else:
    # RATIOS (any source) and every non-VNDirect report MUST carry model_type None,
    # unless a separate source contract is explicitly registered (none in v1).
    if mt is not None:
        return (f"{report.source} {statement.value} report must carry model_type None, got {mt!r}")
```

Valid tuples: `(vndirect, BALANCE, False, 1)`, `(vndirect, INCOME, False, 2)`,
`(vndirect, CASHFLOW, False, 3)`, `(vndirect, BALANCE, True, 101)`, `(vndirect, INCOME, True, 102)`,
`(vndirect, CASHFLOW, True, 103)`; `model_type=None` for RATIOS and all non-VNDirect sources.
Negative tests (reviewer R2): **VNDirect statement with `model_type=None`** → rejected; **non-VNDirect
(e.g. CafeF) report carrying a canonical VNDirect model type** → rejected; plus each canonical-but-
wrong-paired VNDirect tuple (`(BALANCE,False,2)`, `(INCOME,True,101)`, …) → rejected. The
`_CANONICAL_MODEL_TYPES` membership set stays only as a coarse pre-filter for the arbitrary-int case
(`-1/0/4/99/104/999`), subordinate to the relational check above.

## 11. TDD matrix (build phase — not run yet)

RED-first, then green; deterministic synthetic CI fixtures only (no real provider rows bundled);
opt-in live probe (`scripts/probe_corporate_itemcodes.py`, `VNFIN_LIVE=1`) is not in CI.

- **Routing:** corporate `BALANCE→1, INCOME→2, CASHFLOW→3` (regression for the inversion); bank
  `BALANCE→101, INCOME→102, CASHFLOW→103` unchanged. Annual + quarterly.
- **Catalog (positive):** model-1 balance fixture resolves `12700`/`13000`/`14000`/`11000`/`12000`/
  `13100`/`13300`/`11100` and the balance identity holds; model-2 income fixture resolves `21001`/
  `23100`/`23800`/`23003`/`23000`; model-3 cashflow fixture resolves `32000`/`33000`/`34000`/`35000`/
  `37000` with **both** cash-flow identities.
- **Derived metrics end-to-end (reviewer R6):** through an injected VNDirect source, assert exact
  values for **all five** derived metrics that consume remapped primitives —
  `GROSS_MARGIN`(=`23100`/`21001`), `NET_MARGIN`(=`23003`/`21001`),
  `LIABILITIES_TO_EQUITY`(=`13000`/`14000`), `CASH_TO_ASSETS`(=`11100`/`12700`),
  `OPERATING_CASH_FLOW_MARGIN`(=`32000`/`21001`) — not `net_margin` alone.
- **Catalog (negative):** old `21000=net_income` / `25000=total_assets` / `20000=PBT` / `31000=oper CF`
  / `35000=cash_end` never resolve to those meanings again.
- **BLOCKED contract (B2):** `OPERATING_PROFIT` (corp `code=None`) → `BLOCKED` with
  `REASON_METRIC_CODE_UNMAPPED`, **not** `MISSING`/`missing line item None`; a code that IS mapped but
  absent upstream still → `MISSING`; a synthetic derived metric consuming a `None`-code input → BLOCKED
  naming it.
- **Name map (B5):** each mapped label resolves; `11200`/`11300`/`11400`/`11500` and any other
  unmapped code return `item_<code>`.
- **Pagination (B6/B7 + R3):** `limit=1/2/8`; a fiscal date split across two pages (VIC 80+62);
  exact-limit exhaustion; page-1 `totalPages` missing/`<1` → `InvalidData`; **raw metadata types** —
  `True`/`1.0`/`"1"` for `currentPage` and `totalPages` each → `InvalidData` (via `_require_raw_int`);
  later-page `totalPages` present but ≠ cached → `InvalidData`; later-page omitting `totalPages` → OK;
  repeated page-1 header and ahead/out-of-range `currentPage` → `InvalidData`; **row keys** — missing
  `fiscalDate` key, missing `itemCode` key, a **padded** date string, and a **`date` object** all →
  `InvalidData`; non-object / non-ISO / out-of-order / reappearing `fiscalDate` → `InvalidData`;
  duplicate `(fiscalDate, itemCode)` across pages (retained window **and** boundary date) →
  `InvalidData`; a page containing dates older than `limit+1` retained correctly; mid-pagination
  transport failure on page 2 → exception propagates, no partial success.
- **Empty-page seam (B8 + R1):** page-1 empty → `EmptyData` (failover) under explicit and AUTO calls;
  page-2 empty after non-empty page-1 → `InvalidData` under explicit **and** AUTO calls — asserted at
  the actual `_rows()` `EmptyData`-raising seam (not a non-raising `if not data`), so the translation
  is reachable.
- **Tuple guard (B9 + R2):** every valid `(source, statement, is_bank, model_type)` accepted; a
  **VNDirect statement with `model_type=None`** → rejected; a **non-VNDirect report carrying a
  canonical VNDirect model type** → rejected; every canonical-but-wrong-paired VNDirect tuple →
  rejected; RATIOS and non-VNDirect with `model_type=None` accepted.
- **End-to-end:** `metrics(..., source=injected_vndirect_source)` tests, not transformer-only fixtures.
- **Probe unit seams (B10 + R5):** unit tests proving Leg B rejects a wrong `model_type` (e.g. 999)
  even when headline codes exist, and Leg C's oracle labels a 142-of-200 partial newest-date response
  as incomplete (FAIL). Live: `scripts/probe_corporate_itemcodes.py` LEG A/B/C all PASS post-fix
  (pre-fix LEG A PASS, LEG B/C FAIL by design).
- Run focused tests, full offline suite, and warning-token / docs / public-surface gates on the merged
  tree (not per-branch).

## 12. Gate questions — reviewer rulings applied

- **Q1 (operating profit) — ACCEPT unmap.** `OPERATING_PROFIT` ships `corporate_code=None` and reports
  honest `BLOCKED` via the §5 contract. Never guessed.
- **Q2 (`NET_INCOME` asymmetry) — ACCEPT.** Corporate `NET_INCOME=23003` (total consolidated PAT),
  `NET_INCOME_PARENT=23000` (parent-attributable). Distinct, non-redundant; keeps consolidated
  revenue/net-margin coherent. Official VIC PAT/parent/NCI cross-check recorded in the probe doc.
- **Q3 (cash flow) — REJECT status-quo; full audit inside #198.** Operating/investing/financing/
  net-change/end-cash remapped per §4, both identities exact-0, section meanings official-cross-checked
  (§2, probe doc). No code left under its old shifted mapping.
- **Q4 (sub-line names) — REJECT medium-confidence labels.** Aggregate-only sub-lines stay
  `item_<code>`; only individually official-correlated labels are mapped (§6).

## Scope / legal

Public signatures and result types preserved; this is a data-correctness repair (`model_type`,
`LineItem.item_code`/`name`, metric values) documented in `CHANGELOG.md` in lockstep with the API /
tutorial / AI-skill docs and the mapping tables. No first-class ROE (out of scope per the triage).
Legal posture unchanged: bounded runtime fetch only, no bundled provider rows, no new source; the
pagination loop makes only the bounded calls needed for the complete requested periods.
