# Source: `fmarket` (Fmarket fund data)

Adapter: `vnfin.funds.fmarket.FmarketFundSource`.
Models: `vnfin.funds.models` (`Fund`, `FundList`, `NavPoint`, `NavHistory`, `FundHolding`).

This document records the provenance and compliance posture for the Fmarket
public fund-data API. It was written clean-room from direct live probes of the
provider's own public server (`api.fmarket.vn`) and inspection of the raw JSON
shapes — no third-party library, code, or documentation was consulted. The
VNStock clean-room exclusion was applied throughout.

## Scope

Covers VN **open-ended mutual funds** distributed on Fmarket (equity / bond /
balanced) — 65 funds at time of probing, no auth required. Provides the three
required fund data types:

1. **Fund list** — code, name, internal id, latest NAV, manager, asset type.
2. **NAV history** — daily/business-day NAV time series (VND per unit).
3. **Holdings / allocation** — top disclosed holdings with per-stock weight + industry.

ETF iNAV for HOSE-listed ETFs is a known gap (not on Fmarket); out of scope here.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `https://api.fmarket.vn/res/products/filter` | fund list (filterable) |
| `POST` | `https://api.fmarket.vn/res/product/get-nav-history` | NAV history for one fund |
| `GET`  | `https://api.fmarket.vn/res/products/{id}` | fund detail incl. holdings |

`{id}` is the provider's internal product id returned by the filter endpoint
(e.g. `20` = VEOF, `38` = VNDAF). It is used as `productId` for NAV history and as
the path id for holdings.

### Fund list request body

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
    "total": 65,
    "rows": [
      {
        "id": 20,
        "code": "VEOF",
        "shortName": "VEOF",
        "name": "...",
        "nav": 34942.66,
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

### NAV history request body (IMPORTANT upstream quirks)

```json
{"isAllData": 1, "productId": 20, "fromDate": "2000-01-01", "toDate": "2026-06-18"}
```

Verified server behavior (live probes, 2026-06-18):

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
fall in range, the adapter raises `EmptyData` (failover-safe).

### NAV history response shape

```json
{
  "status": 200,
  "data": [
    {"id": 1, "createdAt": 1761537393929, "nav": 10000.0, "navDate": "2014-07-01", "productId": 20}
  ]
}
```

Mapping: `navDate` (`YYYY-MM-DD`)→`NavPoint.date`, `nav`→`NavPoint.nav`
(VND/unit). `createdAt` (epoch ms, sometimes `null`) is ignored. Points are
sorted ascending by date.

### Holdings response shape

```json
{
  "status": 200,
  "data": {
    "code": "VEOF",
    "nav": 34942.66,
    "productTopHoldingList": [
      {"stockCode": "MBB", "netAssetPercent": 7.99, "industry": "Ngân hàng", "price": 25.2, "type": "STOCK"}
    ],
    "productAssetHoldingList": [
      {"assetType": {"code": "STOCK"}, "assetPercent": 97.44}
    ],
    "productIndustriesHoldingList": [
      {"industry": "Ngân hàng", "assetPercent": 33.36}
    ]
  }
}
```

Mapping (MVP exposes top holdings): `productTopHoldingList[].stockCode`→
`FundHolding.stock_code`, `netAssetPercent`→`FundHolding.weight_pct` (0–100),
`industry`→`FundHolding.industry`, `price`→`FundHolding.price`. Asset-class and
industry allocation lists are present in the payload and can be exposed later.

## Authentication

None. The endpoints are reachable anonymously with a normal browser
`User-Agent`; no API key, cookie, or token was required during probing.

## Currency and units

All NAV values (`Fund.nav`, `NavPoint.nav`) are **VND per fund unit**. Holding
weights are **percent of NAV (0–100)**. `NavPoint.date` is a plain
`datetime.date` (NAV is a daily/business-day quantity; no intraday meaning).

## Error mapping (failover-safe)

| Condition | Exception |
|-----------|-----------|
| Transport / network / non-2xx | `SourceUnavailable` |
| Non-JSON / unexpected top-level shape | `InvalidData` |
| Malformed scalar (bad/`null` nav, bad date, out-of-range weight, negative nav) | `InvalidData` |
| Missing required field (id, stockCode, navDate) | `InvalidData` |
| Empty rows / no data in range | `EmptyData` |

These reuse `vnfin.exceptions` so the adapter never leaks raw exceptions.

## robots.txt / ToS observation

`fmarket.vn/robots.txt` disallows only `/assets/params/` and certain
`/blog|help-center/...` search pages. `api.fmarket.vn` has no `robots.txt`; it is
the public read API powering the fund-browse UI. No explicit programmatic-access
grant was published on these endpoints.

## Rate-limit note

No rate-limit headers or throttling were observed during light, sequential
probing (a handful of requests over a few minutes). No documented quota is known.
Keep request volume low, fetch sequentially, add backoff on errors. The adapter
forces IPv4 and uses a 25s timeout via its default transport.

## Compliance caveat

- **Runtime fetch only.** This adapter fetches fund data at runtime on behalf of
  the end user from the provider's own public server. It does **not** bundle,
  cache to disk, or redistribute provider data.
- **No published redistribution grant.** Treat the data as the provider's
  property; do not republish, resell, or redistribute. Personal/internal research
  use only.
- **No real rows in the repo.** All tests use hand-crafted synthetic payloads. No
  real fund rows are committed.
- If the provider publishes terms restricting programmatic access, those terms
  govern; be conservative and stop on any access restriction.
- VNStock and all derivatives were completely excluded from research and design.
```
