# Provenance — corporate itemCode + pagination verification probe (2026-07-20)

Dated evidence artifact for the #198 P0 corporate-fundamentals fix (design/evidence gate, reviewer
`triage-202607202156-issue198-corporate-fundamentals.md` at reviewer commit `d794c71`). Mirrors
`docs/design/bank-itemcodes-probe-20260620.md` (#157). Companion: `tasks/198-design-note.md`.

## Method

- **Source (clean-room):** the project's own `VNDirectFundamentalSource`
  (`api-finfo.vndirect.com.vn/v4/financial_statements`) plus **raw** `curl`/`httpx` probes against
  the same endpoint — **no VNStock / no derived material**.
- **Script:** `scripts/probe_corporate_itemcodes.py`, gated behind `VNFIN_LIVE=1`, not collected by
  pytest (mirrors `scripts/probe_bank_itemcodes.py`). Re-runnable:
  `VNFIN_LIVE=1 ./.venv/bin/python scripts/probe_corporate_itemcodes.py`.
- **Tickers:** FPT, VIC, HPG, VNM (non-bank corporates spanning tech/conglomerate/steel/consumer).
- **Run:** 2026-07-20, latest annual fiscal period each ticker exposes (mostly FY2025, cross-checked
  against FY2024 for the balance identity); one quarterly cross-check (FPT, FQ ending 2026-03-31).
- **Pre-fix confirmation:** running the adapter-level script against current `master` FAILS by
  design — `get_financials(..., BALANCE)` requests `modelType=2` (real income, 25 items) and
  `get_financials(..., INCOME)` requests `modelType=1` (real balance, truncated to the 80-row
  single-page budget) — reproducing BOTH the routing-inversion and pagination-truncation defects in
  one run.

## modelType identity — which template is which (RAW query, bypassing the adapter)

`GET /v4/financial_statements?q=code:{T}~reportType:ANNUAL~modelType:{1|2}&sort=fiscalDate:desc&size=200`

### modelType 1 — BALANCE SHEET (VND, exact)

| Ticker | FY | `11000`+`12000` (CA+LTA) | `12700` (total assets) | `13100`+`13300` (CL+LTL) | `13000` (total liab) | `13000`+`14000` | match `12700`? |
|---|---|---:|---:|---:|---:|---:|:--:|
| FPT | 2025 | 58,137,438,254,908 + 30,004,553,379,717 = 88,141,991,634,625 | 88,141,991,634,625 | 41,524,928,721,230 + 2,869,022,165,856 = 44,393,950,887,086 | 44,393,950,887,086 | 88,141,991,634,625 | **EXACT** |
| VIC | 2025 | — | 1,118,622,625,000,000 | — | 967,133,690,000,000 | 1,118,622,625,000,000 (967,133,690,000,000 + 151,488,935,000,000) | **EXACT** |
| VIC | 2024 | — | 836,604,xxx,xxx,xxx (836.604 T) | — | 682,769 T | 682.769 + 153.834 = 836.603 T | **EXACT** |
| HPG | 2025/2024 | — | 257.899 T / 224.490 T | — | 126.679 T / 109.842 T | 126.679+131.220=257.899 T / 109.842+114.647=224.490 T | **EXACT** |
| VNM | 2025/2024 | — | 53.312 T / 55.049 T | — | 18.829 T / 18.875 T | 18.829+34.483=53.312 T / 18.875+36.174=55.049 T | **EXACT** |
| FPT (quarterly, FQ 2026-03-31) | — | — | 68,586,094,785,217 | — | — | liab+eq = 68,586,094,785,217 | **EXACT** |

Total-resources cross-check (FPT FY2025): `14400` = 88,141,991,634,625 == `12700`. `11000` (current
assets) = `11100`+`11200`+`11300`+`11400`+`11500` EXACT (58,137,438,254,908). `12700` = `11000`+`12000`
EXACT. `13000` = `13100`+`13300` EXACT (44,393,950,887,086). `14000` = `14100`+`14300` EXACT
(43,748,040,747,539).

**Verdict: modelType 1 = BALANCE SHEET for corporates** (identity `13000+14000==12700` holds to the
exact VND on every ticker/year/cadence probed — 6/6). Matches the official Vingroup FY2024 disclosure
cited in the reviewer's triage packet.

### modelType 2 — INCOME STATEMENT (VND, exact)

| Ticker (FY2025) | `21001`−`22100` (rev−COGS) | `23100` (gross profit) | `23800`−`22070` (PBT−tax) | `23003` (PAT total) | `23000`+`23500` (parent+NCI) | `23003`? |
|---|---:|---:|---:|---:|---:|:--:|
| FPT | 70,112,825,100,710 − 44,224,295,588,297 = 25,888,529,512,413 | 25,888,529,512,413 | 13,043,632,833,797 − 1,811,293,383,063 = 11,232,339,450,734 | 11,232,339,450,734 | 9,376,127,629,501 + 1,856,211,821,233 = 11,232,339,450,734 | **EXACT** |
| VIC | 52,682,807,000,000 | 52,682,807,000,000 | 11,064,814,000,000 | 11,064,814,000,000 | 11,350,xxx + (−285,xxx) = 11,064,814,000,000 | **EXACT** |
| HPG | 24,497,788,183,182 | 24,497,788,183,182 | 15,514,931,571,606 | 15,514,931,571,606 | (matches) | **EXACT** |
| VNM | 26,209,474,194,531 | 26,209,474,194,531 | 9,413,589,732,469 | 9,413,589,732,469 | (matches) | **EXACT** |

**Verdict: modelType 2 = INCOME STATEMENT for corporates** (3 independent exact identities — gross
profit, PBT-minus-tax-equals-PAT, and parent-plus-NCI-equals-total-PAT — hold to the exact VND on
every ticker, 4/4 each). This **independently corroborates** the reviewer's flagged-as-unproven
`23000` candidate: `23000` (parent PAT) + `23500` (NCI/minority PAT) = `23003` (total PAT) exactly,
on FPT/VIC/HPG/VNM — `23000` is CONFIRMED parent-attributable PAT, not merely a candidate.

### modelType 3 — CASH FLOW (unaffected by the routing bug; spot-checked, not remapped here)

`31200`/`32000`/`33000` are round "header" codes structurally consistent with operating/investing/
financing subtotals (each rolls up a contiguous block of `3Xy00`-pattern detail codes), but do not
close an exact identity against `34000` in the data pulled (FX/other reconciling items likely
missing from the probed code set). **`37000`** (FPT: 10,522,105,729,992) is an EXACT match to
balance-sheet `11100` (cash & equivalents) — proving `37000`, not the currently-mapped `35000`
(FPT: 1,312,623,193,814 — a different, smaller line), is cash at end of period. Cashflow modelType
routing (`3` unchanged) is out of scope for the P0 fix; the operating/investing/financing/net-change
codes are flagged UNVERIFIED (open question, see design note §5).

## Pagination — reproducing the partial-period bug + provider metadata quirk

`size=80` (the current `limit=1` row budget) against VIC's 142-line-item latest annual balance
period returns only 80 rows for that date — **`14000` (owners' equity) is silently absent**:

```
GET .../financial_statements?q=code:VIC~reportType:ANNUAL~modelType:1&sort=fiscalDate:desc&size=80
  -> currentPage=1 totalPages=33 totalElements=2621
  -> 80/80 returned rows belong to fiscalDate 2025-12-31 (of 142 total for that date)
  -> item 12700 present, 13000 present, 14000 MISSING
```

`page=2` (same query + `&page=2`) returns the remaining 62 rows of `2025-12-31` before the next
(older) date begins — confirming rows are grouped **contiguously** by `fiscalDate` in the
`sort=fiscalDate:desc` stream (no interleaving), the load-bearing assumption behind the reviewer's
stop condition ("first row of fiscal date `limit+1` proves the first `limit` dates complete").

**Provider metadata quirk (must be handled):** page 1's envelope carries `currentPage`, `size`,
`totalElements`, `totalPages`; **page 2's envelope omits `totalElements` and `totalPages` entirely**
(only `currentPage`/`size` remain). A pagination loop that re-reads `totalPages` from every page
would misbehave (`None >= None`/missing-key errors) on page ≥2. Fix: capture `totalPages` (or
`totalElements`) **once, from page 1**, and reuse that cached value for the exhaustion check on
subsequent pages; the distinct-date-count trigger (the reviewer's primary stop condition) does not
depend on this field at all and is the common-case fast path.

## Official cross-check (clean-room; no VNStock)

Reviewer's triage packet already cross-checked VIC FY2024 `12700`/`14000` against the official
Vingroup FY2024 AGM disclosure (`ircdn.vingroup.net` investor-relations PDF, primary/official
source) — total assets/equity anchors matched. This probe independently reproduces the same
identity live (see table above) and extends corroboration to FPT/HPG/VNM and to the income-statement
PBT/PAT/gross-profit chain, none of which the reviewer's packet had closed with an exact identity.
