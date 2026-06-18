# Source provenance — VNDirect api-finfo fundamentals

**Domain:** Step 2 — fundamental reports (income / balance / cashflow / ratios).
**Adapter:** `vnfin.fundamentals.VNDirectFundamentalSource`.
**Clean-room:** endpoint shapes learned only from the provider's own server +
`docs/research/2026-06-18-vn-fundamental-data-sources.md`. No vnstock or
derivative material consulted, cited, or copied.

## Endpoints

- Host: `https://api-finfo.vndirect.com.vn` (NOT `finfo-api...`, which is dead).
- Statements: `/v4/financial_statements?q=code:{T}~reportType:{QUARTER|ANNUAL}~modelType:{N}&sort=fiscalDate:desc&size={N}`
- Ratios: `/v4/ratios?q=code:{T}&sort=reportDate:desc&size={N}`

## Auth / access

- No API key, no cookie, no token, no Referer.
- Requires IPv4 (the default `http_get` forces `local_address=0.0.0.0`) + a
  browser User-Agent. Responds in ~0.2s.

## Response shape

- Envelope: `{"data":[...], "currentPage", "size", "totalElements", "totalPages"}`.
- Statement rows are **LONG/tall** — one row per (line-item, period):
  `{code, itemCode(float, e.g. 11000.0), reportType, modelType(float),
  numericValue, fiscalDate, createdDate, modifiedDate}`.
  The adapter pivots rows by `fiscalDate` into one `FinancialReport` per period.
- Ratio rows: `{code, group, reportDate, itemCode(str), ratioCode, itemName,
  value}` — pivoted by `reportDate`; `LineItem.item_code` holds the `ratioCode`
  and the API-supplied `itemName` becomes `LineItem.name`.
  The ratios endpoint has **no period filter** (rows are keyed by `reportDate`
  only), so the adapter does NOT echo the caller's requested `Period`: ratio
  reports carry `period == Period.UNKNOWN`.

## Units

- **RAW VND, unscaled** for statements (full VND, no PRICE_SCALE applied).
  Each statement `LineItem.value_unit == "VND"` and the report-wide
  `FinancialReport.currency == "VND"` (currency is reserved for actual monetary
  denomination).
- **Ratios are NOT monetary**: each ratio `LineItem.value_unit == "ratio"`
  (dimensionless / per-share) and the report's `currency is None`. Do not treat
  ratio values as VND amounts.

## Bank vs corporate template (modelType)

- Corporate: income=1, balance=2, cashflow=3.
- Bank: income=102, balance=101, cashflow=103.
- Caller selects via `is_bank=True`; the chosen `model_type` is recorded on each
  `FinancialReport` and `is_bank` exposed for downstream interpretation.

## Coverage / history

- HOSE confirmed (FPT corporate, VCB bank). Code-keyed with no exchange gating
  observed; HNX/UPCOM likely covered (unverified in this lane).
- Deep history (FPT annual to ~2002). `size` is budgeted as `max(50, min(1000,
  limit*80))` because statement rows are tall; callers wanting deeper history
  can raise `limit` or subclass.

## Redistribution / terms

- Broker financial-data API intended for VNDirect's own web/app clients. No
  published redistribution grant; no robots.txt or ToS served at the API host.
- Treat as **runtime-fetch only** for personal/internal research — do NOT bundle
  or redistribute bulk fundamentals. No real provider rows are committed; all
  test fixtures in `tests/test_fundamentals.py` use **obviously-fake symbols**
  (`TESTCO`, `ZZBANK`) and **fabricated round numbers** that only preserve the
  provider's JSON shape, units, the bank/corporate `modelType` split, and the
  validation cases. Real proof snippets live only in the research/provenance
  docs (`docs/research/...`), never in tests.

## itemCode -> name map

`vnfin/fundamentals/itemcodes.py` ships a compact, best-effort map of headline
corporate/bank lines so `LineItem.name` is human-readable. It is illustrative,
not an authoritative full chart of accounts; unknown codes fall back to
`item_<code>`. Ratio names come straight from the API's own `itemName`.
