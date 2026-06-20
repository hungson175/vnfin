# Source provenance — CafeF AJAX fundamentals (backup)

**Domain:** Step 2 — fundamental reports (income / balance / ratios).
**Adapter:** `vnfin.fundamentals.CafeFFundamentalSource` (`vnfin/fundamentals/cafef.py`).
**Role in chain:** no-auth **backup** for fundamentals
(default chain: VNDirect primary → **CafeF** backup; both emit RAW VND so the
unit-homogeneity guard accepts the chain).
**Clean-room:** endpoint + response shapes learned only from CafeF's own server +
`docs/research/2026-06-18-vn-fundamental-data-sources.md`. No vnstock or
derivative material was consulted, cited, or copied.

## Endpoints

```
STATEMENTS (income=1, balance=2):
GET https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx
    ?Type={1|2}&Symbol={T}&TotalRow={N}&EndDate={anchor}
    &ReportType={NAM|QUY}&Sort=DESC

RATIOS (EPS / BV / PE / ROA / ROE ...):
GET https://cafef.vn/du-lieu/Ajax/PageNew/GetDataChiSoTaiChinh.ashx
    ?Symbol={T}&TotalRow={N}&EndDate={anchor}&ReportType={NAM|QUY}&Sort=DESC
```

- `EndDate` is the **newest** anchor: annual → current calendar year (`"2026"`),
  quarterly → `"{quarter}-{year}"` (e.g. `"2-2026"`). CafeF clamps to what exists.
- `TotalRow` is budgeted as `max(10, min(400, limit*4))` (one period per row).

## Auth / access

- **No API key, no cookie, no token.** Keyless public AJAX handlers used by
  CafeF's own data pages.
- Requires IPv4 + a browser User-Agent (the shared transport `DEFAULT_UA`).

## Response shape

```json
{"Data": {"Count": <periods avail>,
          "Value": [{"Time":"2025","Year":2025,"Quater":0,"ReportType":"HK",
                     "Conten":"...",
                     "Value":[{"Code":"DTTBHCCDV","Name":"...","Value":70207688945}, ...]},
                    ...]},
 "Message": null, "Success": true}
```

- One object per fiscal period, **newest first**; `Quater` 0 = annual, 1..4 = quarter.
- The adapter synthesizes a `fiscal_date` CafeF does not expose directly: annual →
  Dec 31 of `Year`; quarterly → the Vietnamese fiscal quarter-end
  (Q1 03-31, Q2 06-30, Q3 09-30, Q4 12-31).
- One shape covers **both banks and corporates** — there is no modelType template,
  so `is_bank` is metadata only (auto-detected via the known-bank heuristic unless
  the caller forces it). `model_type` is `None`.

## Units

- **Emitted as RAW VND** for statement money lines. CafeF's feed reports statement money in
  **thousand-VND**, so the adapter multiplies each monetary line by **1000** on ingest to emit
  raw VND — the SAME scale/currency as the VNDirect primary, so the source declares `unit = "VND"`
  and the failover unit-homogeneity guard accepts the VNDirect → CafeF chain **without a silent
  scale mismatch** (ratio lines are dimensionless and are NOT scaled). Statement
  `LineItem.value_unit == "VND"` and `FinancialReport.currency == "VND"`.
- **Ratios are NOT monetary**: ratio `LineItem.value_unit == "ratio"`
  (dimensionless / per-share) and the report's `currency is None`. Ratio reports
  carry `period == Period.UNKNOWN` (CafeF ratios have no trustworthy period
  dimension), mirroring the VNDirect ratios contract. The dimensionless `currency
  is None` is consistent with the failover unit guard, which is statement-type-aware
  — a `ratios` report's chain "unit" is dimensionless, so `None` is accepted (a
  ratios report carrying a monetary currency is rejected; the VND check is intact
  for income/balance/cashflow). A `ratios` `fiscal_date` is the provider's own
  reporting date and may be a **TTM** (trailing-twelve-month) snapshot; because the
  report is `Period.UNKNOWN` it is **never relabeled as a fiscal-year annual** figure.

### `ReportType` on ratio rows (non-identity descriptive field)

For ratios the `ReportType` tag is **not** identity-bearing — the ratio endpoint is
always hit with the annual anchor and the result is `Period.UNKNOWN`, so no cadence
filtering is applied. CafeF's real ratios feed sends rows with **`"ReportType": null`**;
a present-null (or absent) `ReportType` is therefore **tolerated** (parsed, not
rejected). A present **non-null** `ReportType` is still validated against the
`{NAM, HK, QUY, H}` union (padded / unknown / blank / non-string fail closed), so a
genuinely corrupt descriptive value still raises `InvalidData`. (On the **statement**
path `ReportType` IS cadence identity, so there a present-null fails closed.)

## Cashflow caveat (single-source)

CafeF's summary handlers do **not** serve cash flow (`Type=3` returns an empty
`Value`). A CASHFLOW request to this adapter raises `EmptyData` (failover-safe), so
in the default chain **cashflow falls through to VNDirect only** — i.e. cashflow
remains effectively single-source. Income / balance / ratios have true VNDirect →
CafeF redundancy.

## Error mapping (failover-safe)

| Case | Adapter mapping |
|------|-----------------|
| `Success: false` / `Data: null` (unknown symbol) / empty `Value` | `EmptyData` |
| Cashflow request (not served by CafeF) | `EmptyData` |
| Non-object response / wrong types / malformed scalar / bad `Year`/`Quater` | `InvalidData` |
| Empty / whitespace symbol or bad `limit` (usage error) | `VnfinError` |
| Transport / network failure | `SourceUnavailable` (via shared transport) |

## Rate limits / backoff

No documented key/limit; treat as on-demand fetch only and back off on transport
errors (wrapped as `SourceUnavailable`). Use small `limit` values; `TotalRow` is
already bounded to avoid large pulls.

## Redistribution / terms

- Public AJAX handlers intended for CafeF's own data pages. No published
  redistribution grant and no ToS served at the handler host.
- Treat as **runtime-fetch only** for personal/internal research — do NOT bundle
  or redistribute bulk fundamentals. Emit CafeF attribution downstream.
- No real provider rows are committed; all test fixtures in
  `tests/test_fundamentals_cafef.py` use **obviously-fake symbols** and
  **fabricated round numbers** that only preserve the JSON shape, units, and
  validation cases. Real proof snippets live only in the research doc.

## Live test policy

Live VNDirect ↔ CafeF cross-source agreement checks live in
`live_tests/test_fundamentals_failover_live.py` (require `VNFIN_LIVE=1`, outside
default collection).
