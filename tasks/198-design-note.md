# Design/evidence note — #198 corporate fundamentals: inverted routing + broken catalog + pagination

- Status: **DESIGN RE-GATE REQUESTED (round 8).** Revised against reviewer gates round-1..6 (B1–B10,
  R1–R18) and round-7 `gate-202607212207-issue198-regate-round7.md` (`091f237`, R19–R20 + evidence
  wording). Round-7 fixes: **R19** `_paginate` takes an explicit `page1_envelope` seed that is
  re-validated identically to a fetched page (no double-fetch); a redirect uses a **fresh** `_paginate`
  with local state sharing nothing with the candidate; `_dominant_model` fails closed on **any**
  out-of-`VALID` tag (even a minority) and on a corporate/bank **tie**, confirming only a unique
  dominant exact model; candidate page-1 metadata is validated before its tags are trusted. **R20**
  the runtime `_require_item_code` reuses `_item_code_str`/`canonical_provider_key` (no `str(int(...))`)
  so `11000.9`/`True`/negative/padded fail closed. Probe evidence wording corrected (LEG A + pre-fix
  B/C failures observed; full live PASS reserved for post-fix). **No package runtime code or tests
  changed** (evidence + design only).
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
- `_require_item_code(row) -> str` (reviewer R20) — `row["itemCode"]` must be present and canonical
  via **direct reuse of `_item_code_str` → `canonical_provider_key`** (`vndirect.py:523-529`,
  `_contracts/keys.py`), **not** `str(int(...))`. So a supported integral provider float (`11000.0`
  → `"11000"`) and a canonical digit string (`"11000"`, `"0"`) pass, while `True`, a fractional
  float/`Decimal` (`11000.9`), a negative, a padded/signed/non-canonical string, `null`, and
  containers all raise `InvalidData` — the exact contract the builder already applies at
  `vndirect.py:332`, so the pagination key and the builder key are byte-for-byte identical (an absent
  key raises too).
- `_row_disposition(row, *, psym, period, model_type) -> Disposition` (reviewer R8 + R12) — the
  **single shared, structured classifier** returning `ELIGIBLE` / `SKIP_CADENCE` / `SKIP_MODEL` /
  `SKIP_CODE`, extracted from the three existing skip conditions in `_build_statement_reports`
  (`vndirect.py:294-331`): a **present** `reportType` tag naming a different cadence → `SKIP_CADENCE`;
  a **present** `modelType` (`_parse_model_type`) `!= model_type` → `SKIP_MODEL`; a **present** `code`
  that is non-string / blank / `!= psym` → `SKIP_CODE`; otherwise `ELIGIBLE` (absent keys keep the
  legacy "no-signal → eligible" behavior). Both the pagination loop AND `_build_statement_reports`
  call this ONE function, so the completeness contract and the skip contract cannot drift: pagination
  treats only `ELIGIBLE` as eligible; the builder preserves its EXACT current counter semantics
  (reviewer R15) — `SKIP_CODE` increments **both** `skipped_rows` **and** `code_mismatches`
  (`vndirect.py:329-330`); `SKIP_CADENCE`/`SKIP_MODEL` increment `skipped_rows` **only** — so the
  mixed-row warning (driven by `skipped_rows`) still fires for a skipped wrong-`code` row, and the
  two all-dropped diagnostics keep their precedence (`vndirect.py:353-357` wrong-identity
  `code_mismatches>0` is checked **before** `:365-370` cadence/model `skipped_rows>0`). Structural
  `InvalidData` guards (malformed `modelType` etc.) still raise inside the parser; the classifier only
  answers which contract bucket a **well-formed** row falls in.

The loop keeps **two distinct states** (reviewer R12): (1) **raw-stream validation** runs on EVERY
fetched row; (2) an **eligible-date boundary** (via `_row_disposition`) drives only the stop condition.
It hands **all fetched rows** to `_build_statement_reports` — never a pre-filtered subset — so the
builder's skip-warning, its two all-dropped `InvalidData` diagnostics, its duplicate-code guard, and
its `[:limit]` cap all run exactly as today (`vndirect.py:341-392`).

```
# _paginate(psym, statement, period, *, model_type, limit, page1_envelope=None) — eligibility is gated
# on `model_type` (the model reports are BUILT under). `page1_envelope` (reviewer R19) is an ALREADY-
# FETCHED page-1 response to SEED the loop (the candidate/restarted page). It is processed through the
# SAME page-1 validation as a fetched page (no double-fetch, no un-validated shortcut). ALL state below
# is LOCAL to this call, so a redirect's fresh `_paginate` invocation shares NO metadata/state with the
# candidate's — the two envelopes can never cross-contaminate.
PAGE_SIZE = _row_budget(limit)
page, cached_total_pages, last_fd = 1, None, None
closed = set()                     # dates whose contiguous group has ended (raw-stream state)
seen_keys = set()                  # (fiscalDate, itemCode) across ALL fetched rows (raw-stream state)
eligible_order = []                # distinct ELIGIBLE fiscalDates, newest-first (boundary state ONLY)
all_rows = []                      # every fetched raw row, unfiltered -> handed to the builder

while True:
    if page == 1 and page1_envelope is not None:
        resp = page1_envelope       # SEED: use the already-fetched page 1 (candidate/restarted)...
    else:
        resp = self._fetch_json(...page=page, size=PAGE_SIZE)   # ...page 2+ (or an unseeded page 1) is fetched
    # --- B8 empty-page semantics AT THE ACTUAL _rows() SEAM (reviewer R1) ---
    # NB: the seed still flows through _rows / currentPage==1 / totalPages>=1 / row-stream / eligibility
    # validation below — a seeded page is validated identically to a fetched one (reviewer R19).
    try:
        data = self._rows(resp)                 # dict-envelope + list contract; RAISES EmptyData on []
    except EmptyData:
        if page == 1:
            raise                                # template miss -> existing AUTO failover
        raise InvalidData(f"{self.name}: empty page {page} after a non-empty page 1")
    # --- B6 metadata identity (raw, canonical, non-bool ints only) ---
    current_page = _require_raw_int(resp, "currentPage")
    if page == 1:
        cached_total_pages = _require_raw_int(resp, "totalPages")
        if cached_total_pages < 1: raise InvalidData(...)          # page-1 totalPages >= 1
    elif "totalPages" in resp:                                     # later pages MAY omit it (verified)
        if _require_raw_int(resp, "totalPages") != cached_total_pages: raise InvalidData(...)  # 2.0!=2
    if current_page != page: raise InvalidData(...)               # repeated/ahead header -> raise, never loop
    if not (1 <= current_page <= cached_total_pages): raise InvalidData(...)
    for row in data:
        # === STATE 1: raw-stream validation for EVERY row (eligible or not) ===
        row  = require_object(row, ...)                           # non-object -> InvalidData
        fd   = _require_iso_fiscal_date(row)                      # present + exact YYYY-MM-DD; else InvalidData
        code = _require_item_code(row)                            # present + canonical; else InvalidData
        if fd != last_fd:                                        # date changed in the raw stream
            if fd in closed: raise InvalidData(...)               # reappearance of a CLOSED date (any row)
            if last_fd is not None:
                if fd >= last_fd: raise InvalidData(...)          # raw stream must be strictly descending
                closed.add(last_fd)                               # previous date group closes
            last_fd = fd
        if (fd, code) in seen_keys: raise InvalidData(...)        # duplicate (fd,code) across ALL fetched rows
        seen_keys.add((fd, code))
        all_rows.append(row)                                      # hand EVERYTHING to the builder
        # === STATE 2: eligible-date boundary ONLY (does not gate validation) ===
        if _row_disposition(row, psym=psym, period=period, model_type=model_type) is ELIGIBLE:
            if fd not in eligible_order: eligible_order.append(fd)
    # --- stop conditions (eligible boundary; builder caps to `limit`) ---
    if len(eligible_order) > limit: break         # (limit+1)-th ELIGIBLE date seen -> newest `limit` complete
    if current_page >= cached_total_pages: break  # provider declares exhaustion
    page += 1

return all_rows   # -> _build_statement_reports(..., rows=all_rows, limit=limit) UNCHANGED:
                  #    it skips SKIP_* rows (warning), raises the all-dropped diagnostics, and caps [:limit].
```

**Explicit vs. AUTO flows (reviewer R11 + R14) — ONE atomic pagination stream has ONE query/model/
metadata envelope; the eligibility model is the DETECTED template, never the initial candidate:**

- **Explicit** (`is_bank` given): `model_type = model_type_for(statement, is_bank=resolved)`;
  `_paginate(..., model_type=model_type)` — one query, one envelope; build under `resolved`.
- **AUTO** (`_get_statements_auto`). The template is identified by the **EXACT** provider `modelType`,
  not the `is_bank` class — the two models valid for the requested statement are
  `VALID = {model_type_for(statement, False), model_type_for(statement, True)}` (e.g. INCOME → `{2,
  102}`). `_dominant_model(rows, statement)` (reviewer R19) strict-parses (`_parse_model_type`) each
  **present** `modelType`; then:
  - **any** parsed model **outside `VALID`** → `InvalidData`, even as a minority tag (a foreign /
    wrong-statement template like `101` for INCOME can never appear in a clean stream);
  - **no** present tags → `None` (tag-less);
  - a **tie** between the two `VALID` models (corporate vs bank, equal counts) → `InvalidData` (no
    dominant identity);
  - otherwise → the **unique dominant** `VALID` model.

  For each candidate (bank-first if `is_known_bank`, else corporate-first):
  1. Fetch **page 1** under the candidate's model query. On `EmptyData`, record the miss and try the
     other candidate (existing template failover — a wrong `modelType` filter returns zero rows in
     production).
  2. **Validate the candidate page-1 envelope/rows first** (`_rows`, `currentPage==1`,
     `totalPages>=1`, STATE-1 row-stream) — *before* trusting its tags — then
     `observed = _dominant_model(page1_rows, statement)`.
  3. **Atomic query resolution (R14 + R17 + R19):**
     - `observed is None` (tag-less) **or** `observed == candidate_model`: the candidate is confirmed;
       call `_paginate(..., model_type=candidate_model, page1_envelope=candidate_page1)` — the seed is
       re-validated by `_paginate` and page 1 is **not** re-fetched; build under the candidate.
     - `observed != candidate_model` (a redirect, **allowed once**): **discard the candidate page and
       its state**, fetch a **fresh page 1 under `observed`'s query**, validate that restarted
       envelope, then require `_dominant_model(restart_rows, statement) == observed` **exactly** — a
       **tag-less**, **same-class-wrong-statement** (`101`), **tie**, or **contradictory** restart
       raises `InvalidData`; a **restart `EmptyData` after the non-empty candidate page** raises
       `InvalidData` (never a template `EmptyData` that resumes candidate fall-through). Then call a
       **fresh** `_paginate(..., model_type=observed, page1_envelope=restart_page1)` (new local state,
       shares nothing with the candidate); build under `is_bank = observed >= 100`. **No second
       redirect.**
  4. So an unknown bank whose income response is model `102` produces a **complete** bank report from
     one all-`102` query — never `order=[]` → corporate fallback, never a page-1(candidate)/
     page-2(detected) cross-query stitch, and never a page fetched twice.

- **Finite (B6):** every fetch requests the local `page`; termination is bounded by
  `cached_total_pages`, and a header that does not equal the requested page or falls outside
  `[1, cached_total_pages]` raises immediately.
- **Two-state validation (B7 + R12):** STATE 1 (object / ISO date / itemCode presence, strictly-
  descending contiguous date groups, no reappearance, no duplicate `(fd,code)`) runs on **every**
  fetched row — an out-of-order/reappearing/duplicate row raises even when it is `SKIP_*` ineligible.
  STATE 2 (`eligible_order`) only sets the stop boundary. The two are independent.
- **No pre-filtering (R12):** the loop hands **all** fetched rows to the builder; the builder does the
  skipping (with warning), the two all-dropped `InvalidData` diagnostics, the duplicate-code guard,
  and the `[:limit]` cap — so mixed-row warnings and the all-wrong-`code` wrong-identity error survive
  (they were being erased by the prior `keep`-filter). The `(limit+1)`-th eligible date may be fetched
  partially; the builder's `[:limit]` cap drops it.
- **Fail-closed:** the only `try/except` is the narrow `EmptyData` seam (page-1 re-raise /
  page≥2→`InvalidData`); any transport or other schema error propagates, so a half-fetched multi-page
  request never surfaces as a partial success.
- `PAGE_SIZE` keeps the `_row_budget(limit)` heuristic as the per-page size; the fix is the multi-page
  LOOP, not a larger single page.

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
    # STRICT non-bool int prefilter FIRST: in Python `2.0 == 2` and `True == 1`, so the
    # relational compare alone would accept an integral float / bool. Reject any non-int,
    # bool, or numeric string BEFORE comparing to `expected`.
    expected = _EXPECTED_MODEL_TYPE[(statement, report.is_bank)]
    if not isinstance(mt, int) or isinstance(mt, bool) or mt != expected:  # None/2.0/"2"/True/wrong-int all fail
        return (f"vndirect {statement.value} report for a "
                f"{'bank' if report.is_bank else 'corporate'} entity must carry a strict int "
                f"model_type {expected}, got {mt!r}")
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
- **Runtime item-code strict key (reviewer R20):** `_require_item_code` reuses `_item_code_str` →
  `canonical_provider_key`, so an `itemCode` of `True`, a fractional float/`Decimal` (`11000.9`), a
  **negative**, a padded/signed/non-canonical string, `null`, or a container → `InvalidData`, while a
  supported integral provider float (`11000.0` → `"11000"`) and a canonical digit string pass —
  byte-for-byte the builder's `vndirect.py:332` key (no `str(int(...))`).
- **Row eligibility pre-count + dual counters (reviewer R8 + R12 + R15):** for each of `reportType`,
  `modelType`, and provider `code` mismatch, the three-date regression — valid annual 2025,
  **ineligible** 2024, valid annual 2023, `limit=2` — returns **2025 + 2023** (the ineligible 2024
  never advances the eligible boundary), **with the builder's skip-warning surfaced**. Assert the
  shared `_row_disposition` drives both the pagination boundary and the builder skip, and the exact
  counter semantics: `SKIP_CODE` bumps **both** `skipped_rows` and `code_mismatches` (so a mixed
  wrong-`code` response still warns); an **all-wrong-`code`** response raises the wrong-identity
  `InvalidData` (`vndirect.py:353-357`) — checked **before** the all-cadence/model `:365-370`
  `InvalidData` (precedence pinned). Pin the **exact** mixed warning string
  (`skipped_mismatched_report_rows: <n> row(s) with mismatched reportType/modelType/code`) — the count
  and the `/code` suffix — not merely that a warning was surfaced (reviewer R15/R17).
- **Two-state validation (reviewer R12):** a raw **out-of-order / reappearing / duplicate** row raises
  `InvalidData` **even when that offending row is `SKIP_*` ineligible** (STATE-1 validates every row,
  independent of the eligible boundary).
- **AUTO atomic-query detection under pagination (reviewer R11 + R14 + R17):** with a **call-sequence
  assertion** on the exact `(query model, requested page)` of **every** fetch (not only the final
  report). Pin these exact cases:
  - candidate income-`2` page reports dominant `102` → **restart** income-`102` → **complete bank
    report** (`is_bank=True`, `model_type=102`); the fetch sequence is `(2,1)` then `(102,1)` then
    `(102,2…)` — page 1 re-issued under `102`, **never** a `(2,1)`→`(102,2)` stitch, and the seed page
    is **not** fetched twice;
  - restart returns dominant `101` (same class, wrong statement) → **`InvalidData`** (fail closed);
  - restart is **tag-less** → `InvalidData` (a missing tag must not confirm the redirect);
  - restart is **empty** (after the non-empty candidate page) → `InvalidData`, **not** an `EmptyData`
    that resumes candidate fall-through;
  - restart **contradicts again** (dominant tag ≠ the detected model) → `InvalidData` (one redirect
    only);
  - a **same-model** candidate page (`detected == candidate`) seeds pagination with that page (assert
    it is fetched **once** — `page1_envelope` seed, **no double-fetch**);
  - a candidate page with a **foreign minority tag** (any `modelType` outside the statement's `VALID`
    pair, even non-dominant) → `InvalidData`;
  - a candidate page with a **tie** between the two `VALID` models → `InvalidData` (no dominant
    identity);
  - **malformed candidate page-1 metadata** (bad `currentPage`/`totalPages`) → `InvalidData` **before**
    its tags are trusted for a redirect;
  - the redirect's `_paginate` runs on **fresh state** (no metadata/dates/keys carried from the
    candidate envelope).
  Explicit `is_bank` still overrides. Cover a corporate (1/2/3) and a bank (101/102/103) AUTO+
  pagination path.
- **Empty-page seam (B8 + R1):** page-1 empty → `EmptyData` (failover) under explicit and AUTO calls;
  page-2 empty after non-empty page-1 → `InvalidData` under explicit **and** AUTO calls — asserted at
  the actual `_rows()` `EmptyData`-raising seam (not a non-raising `if not data`), so the translation
  is reachable.
- **Tuple guard (B9 + R2 + strict int):** every valid `(source, statement, is_bank, model_type)`
  accepted; a **VNDirect statement with `model_type=None`** → rejected; a **non-VNDirect report
  carrying a canonical VNDirect model type** → rejected; every canonical-but-wrong-paired VNDirect
  tuple → rejected; **an otherwise-correct VNDirect tuple with `model_type` `2.0` / `"2"` / `True`**
  → rejected (strict non-bool int prefilter, since `2.0 == 2`); RATIOS and non-VNDirect with
  `model_type=None` accepted.
- **End-to-end:** `metrics(..., source=injected_vndirect_source)` tests, not transformer-only fixtures.
- **Probe unit seams (B10 + R5 + R9 + R10 + R16):** unit tests proving Leg B rejects a wrong
  `model_type` (e.g. 999) even when headline codes exist; Leg A **fails when only one balance period
  exists** (two required); the raw-oracle helper **fails a truncated oracle** (page-1 declares 3
  pages, page-2 premature-empty), **rejects a duplicate code / out-of-order or higher-date boundary /
  reappearing newest date / over-`totalPages` page / non-bool `totalPages` (`2.0`)**; **rejects a
  malformed-calendar date (`2025-99-99`)** and a row whose **raw `code`/`reportType`/`modelType`
  identity mismatches** the request; **fails closed on a non-integral or `abs(value) >= 2**53` VND
  value, both signs, through the real `_num()`/`LineItem.value` float seam** (an adjacent 1-VND value
  must not alias). **Strict identity parsing (reviewer R18):** a raw `modelType` of `True` / `1.9` /
  `Decimal("1.9")` is **not** model 1, and an `itemCode` of `11000.9` does **not** canonicalize to
  `"11000"` — both reject via the strict `_canonical_int` contract (Leg A + oracle). Live:
  `scripts/probe_corporate_itemcodes.py` LEG A/B/C all PASS post-fix (pre-fix
  LEG A PASS, LEG B/C FAIL by design).
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
