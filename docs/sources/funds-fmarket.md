# Source: `fmarket` (Fmarket fund data)

Adapter: `vnfin.funds.fmarket.FmarketFundSource`.
Models: `vnfin.funds.models` (`Fund`, `FundList`, `NavPoint`, `NavHistory`, `FundHolding`,
`AssetAllocation`, `AssetClassWeight`, `SectorWeight`).

> **CURRENT STATUS (#221): `DISABLE_PENDING_PERMISSION`.** This page is a historical provenance,
> schema, and synthetic-parser reference. It is **not** a live-access guide or permission grant.
> `FmarketFundSource` construction is lazy, and every valid `list_funds`, `nav_history`,
> `holdings`, or `asset_allocation` call raises
> `SourceUnavailable("SOURCE_DISABLED_PENDING_PERMISSION")` before cache lookup, transport, retry,
> or network. No Fmarket request is made by the current runtime; no alternate source is used.
> The route/shape notes below were recorded before #221 and are retained only to explain the
> compatibility surface.

This document records historical provenance and compliance posture for the Fmarket public fund-data
API. It was written clean-room from the provider's own public server and inspection of historical
JSON shapes — no third-party library, code, or documentation was consulted. The VNStock clean-room
exclusion was applied throughout. The historical observations do not establish current permission
to automate, return, cache, retain, or redistribute provider data.

## Scope

Covers the historical VN **open-ended mutual-fund** model distributed on Fmarket (equity / bond /
balanced). At the time of the historical probe, the provider response shapes supported the three
required data types below. Current production calls are disabled pending permission.

1. **Fund list** — code, name, internal id, latest NAV, manager, asset type.
2. **NAV history** — daily/business-day NAV time series (VND per unit).
3. **Holdings / allocation** — top disclosed holdings (equities **and** bonds, each tagged with an
   `instrument_type`) with per-line-item weight + industry, plus an `asset_allocation()` class split.

ETF iNAV for HOSE-listed ETFs is a known gap (not on Fmarket); out of scope here.

## Historical route inventory (not a callable runtime contract)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `https://api.fmarket.vn/res/products/filter` | fund list (filterable) |
| `POST` | `https://api.fmarket.vn/res/product/get-nav-history` | NAV history for one fund |
| `GET`  | `https://api.fmarket.vn/res/products/{id}` | fund detail incl. holdings + asset allocation |

`{id}` is the provider's internal product id returned by the filter endpoint
(the examples below use a fabricated `999`/`DEMO1` identity). It is used as `productId` for NAV history and as
the path id for holdings. `holdings()` and `asset_allocation()` both read this one
detail document (and both enforce the #21 fund-identity guard on it).

### Historical fund-list request shape (synthetic reference only)

```json
{
  "types": ["NEW_FUND", "TRADING_FUND"],
  "sortField": "navTo6Months",
  "sortOrder": "DESC",
  "page": 1,
  "pageSize": 100,
  "isIpo": false,
  "fundAssetTypes": [],
  "searchField": ""
}
```

`fundAssetTypes` accepts e.g. `["STOCK"]` to filter to equity funds;
`searchField` does free-text name/code search.

### Fund list response shape

```json
{
  "status": 200,
  "code": 200,
  "data": {
    "total": 1,
    "rows": [
      {
        "id": 999,
        "code": "DEMO1",
        "shortName": "DEMO1",
        "name": "Synthetic fund fixture",
        "nav": 12345.67,
        "dataFundAssetType": {"code": "STOCK", "name": "..."},
        "owner": {"name": "...", "shortName": "..."}
      }
    ]
  }
}
```

Mapping: `id`→`Fund.id`, `code`→`Fund.code`, `name`→`Fund.name`,
`nav`→`Fund.nav` (VND/unit), `owner.name` (fallback `owner.shortName`)→
`Fund.manager`, `dataFundAssetType.code`→`Fund.asset_type`.

### Historical NAV request shape (synthetic reference only)

```json
{"isAllData": 1, "productId": 999, "fromDate": "2000-01-01", "toDate": "2026-06-18"}
```

Historical server observations (live probes, 2026-06-18; retained as provenance, not a current
runtime guarantee):

- **Both `fromDate` and `toDate` are mandatory.** A body with neither (e.g.
  `{"isAllData":1,"productId":20}`) returns **HTTP 400**.
- `isAllData:1` returns the full inception-to-`toDate` series. With wide dates,
  VEOF returns 1729 rows (`2014-07-01` … `2025-12-05`).
- The server only enforces the **`toDate` upper bound** server-side; it does not
  reliably honor `fromDate` as a lower bound (and its `toDate` row-count handling
  is itself irregular near recent boundaries).
- `isAllData:0` returns a single snapshot row (not a window).

**Adapter strategy:** always send `isAllData:1` + a far-past default `fromDate`
(`2000-01-01`) + a `toDate` (caller's `to_date` or today), then apply the
caller's `from_date` lower bound **client-side** for an exact window. If no rows
fall in range, the adapter raises `EmptyData` (failover-safe) — except when the
history's newest `navDate` is strictly before the requested window start, in which
case it raises `StaleData` (an `EmptyData` subclass) naming the gap, so a stale or
closed feed is distinguishable from a genuinely-empty / pre-inception result.

### Historical NAV response shape (synthetic reference only)

```json
{
  "status": 200,
  "data": [
  {"id": 1, "createdAt": 1761537393929, "nav": 10000.0, "navDate": "2014-07-01", "productId": 999}
  ]
}
```

Mapping: `navDate` (`YYYY-MM-DD`)→`NavPoint.date`, `nav`→`NavPoint.nav`
(VND/unit). `createdAt` (epoch ms, sometimes `null`) is ignored. Points are
sorted ascending by date.

### Historical holdings response shape (synthetic reference only)

```json
{
  "status": 200,
  "data": {
    "code": "DEMO1",
    "nav": 12345.67,
    "productTopHoldingList": [
      {"stockCode": "DEMO", "netAssetPercent": 7.99, "industry": "Synthetic industry", "price": 25.2, "type": "STOCK", "updateAt": 1700000000000}
    ],
    "productTopHoldingBondList": [
      {"stockCode": "SYNTHBOND", "netAssetPercent": 11.59, "industry": "Synthetic bond", "price": null, "type": "BOND", "updateAt": 1700000000000}
    ],
    "productAssetHoldingList": [
      {"assetType": {"code": "STOCK"}, "assetPercent": 97.44, "updateAt": 1700000000000}
    ],
    "productIndustriesHoldingList": [
      {"industry": "Synthetic industry", "assetPercent": 33.36}
    ]
  }
}
```

The detail document carries **two** per-line-item holdings arrays with the **same row shape** —
`productTopHoldingList` (equities) and `productTopHoldingBondList` (bonds; `stockCode` is the bond code
e.g. `BAF126003`, `price` is typically `null`, `type:"BOND"`). A pure-bond fund populates **only** the
bond list. (There is no `productBondHoldingList` key — the bond array is `productTopHoldingBondList`.)

`holdings(product_id)` historical mapping (equity rows first, then bond rows, merged into one tuple):

| Provider field | Model field | Notes |
|----------------|-------------|-------|
| `stockCode` | `FundHolding.stock_code` | canonical `[A-Z][A-Z0-9]*` ticker for equities; for bond / unlisted-bond / other rows a relaxed identifier (required present + non-empty, stored verbatim — may be a descriptive phrase e.g. `'Trái phiếu chưa niêm yết'`) |
| `netAssetPercent` | `FundHolding.weight_pct` | percent of NAV, 0–100 |
| `industry` | `FundHolding.industry` | nullable |
| `price` | `FundHolding.price_raw` (+ `price_unit="raw"`) | unverified scale, kept RAW; bonds usually `null` |
| `type` | `FundHolding.instrument_type` | known reals `{STOCK, BOND, UNLISTED_BOND}`; present-but-unknown stringlike → `OTHER` (honest, not fail-closed); present-malformed (non-string/blank) fails closed; absent → per-list default |
| `updateAt` | `FundHolding.as_of_utc` | epoch-**ms** → UTC; absent/malformed → `None` (never fabricated) |

`asset_allocation(product_id)` reads `productAssetHoldingList` off the same document:
`assetType.code` (∈ `{STOCK, BOND, CASH, OTHER}`, fail-closed on another tag) →
`AssetClassWeight.asset_class`; `OTHER` is preserved as the provider-declared class, not a future-tag
catch-all. `assetPercent` (finite, 0–100) → `AssetClassWeight.weight_pct`. `AssetAllocation.as_of_utc`
is the freshest row `updateAt`. Disclosed class weights are **not** required to sum to 100% (partial
disclosure allowed). When the list is absent, `null`, or `[]`, the accessor returns a successful typed
empty allocation (`classes == ()`, `as_of_utc is None`) with exactly one
`no_asset_allocation_published` warning, while retaining any existing detail-coverage warning(s) and
metadata from the same response. This is a known-empty disclosure, not proof of no assets. A present
non-array list, `OTHER2`, malformed/duplicate class, or bad weight remains `InvalidData`.
## Authentication and permission boundary

Historical probes observed anonymous reachability with a browser-like `User-Agent`, but reachability
is not permission. The current source is disabled pending written permission; no API key, cookie,
token, session, or browser header may be added as a bypass. The production guard runs before any
transport or cache path.

## Currency and units

All NAV values (`Fund.nav`, `NavPoint.nav`) are **VND per fund unit**. Holding
weights are **percent of NAV (0–100)**. `NavPoint.date` is a plain
`datetime.date` (NAV is a daily/business-day quantity; no intraday meaning).

## Historical parser error mapping (private synthetic-fixture contract)

The mapping below is retained for parser/schema tests using fabricated payloads. It is not a promise
that a current public operation can reach a provider response.

| Condition | Exception |
|-----------|-----------|
| Transport / network / non-2xx | `SourceUnavailable` |
| Non-2xx application `status`/`code` (e.g. 500/403) | `SourceUnavailable` |
| Missing both `status` and `code` envelope fields | `InvalidData` |
| Non-integer `status`/`code` envelope value | `InvalidData` |
| Non-JSON / unexpected top-level shape | `InvalidData` |
| Malformed scalar (bad/`null` nav, bad date, out-of-range weight, negative nav) | `InvalidData` |
| Missing required field (id, stockCode, navDate) | `InvalidData` |
| Empty holdings / no NAV data in range | `EmptyData` |
| Asset allocation absent, `null`, or `[]` | Successful empty `AssetAllocation` plus `no_asset_allocation_published` |
| NAV history non-empty but its latest `navDate` is before the requested window start (stale/closed feed) | `StaleData` (an `EmptyData` subclass) |

These reuse `vnfin.exceptions` so the adapter never leaks raw exceptions.

## Historical robots.txt / terms observation

`fmarket.vn/robots.txt` disallows only `/assets/params/` and certain
`/blog|help-center/...` search pages. `api.fmarket.vn` has no `robots.txt`; it is
the public read API powering the fund-browse UI. No explicit programmatic-access
grant was published on these endpoints.

## Historical rate-limit observation (not an authorization)

No rate-limit headers or throttling were observed during the historical light, sequential probe.
That observation is not a quota, reuse grant, or current runtime instruction. The disabled adapter
does not fetch, retry, back off, or force a provider session.

## Compliance caveat

- **Current runtime:** no provider fetch occurs. Valid calls fail closed with
  `SOURCE_UNAVAILABLE` reason `SOURCE_DISABLED_PENDING_PERMISSION` before cache/network.
- **Historical runtime posture:** the pre-#221 adapter was designed as runtime fetch only and did
  not bundle, cache to disk, or redistribute provider data. That historical design does not cure
  the current permission gap.
- **No published redistribution grant.** Treat the data as the provider's
  property; do not republish, resell, or redistribute. Personal/internal research
  use only.
- **No real rows in the repo.** All tests use hand-crafted synthetic payloads. No
  real fund rows are committed.
- If the provider publishes terms restricting programmatic access, those terms
  govern; be conservative and stop on any access restriction.
- VNStock and all derivatives were completely excluded from research and design.
```
