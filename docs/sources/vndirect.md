# Source: vndirect

TradingView-UDF price-history adapter for the VNDirect public charting backend.

## Provenance

| Field | Value |
|-------|-------|
| Source key | `vndirect` |
| Class | `VNDirectSource` |
| Base URL | `https://dchart-api.vndirect.com.vn` |
| History path | `/dchart/history` |
| Protocol | Public TradingView UDF (Universal Data Feed) |
| Envelope | None — response is a bare UDF object |
| Auth | None observed (no API key, no cookie, no `Authorization` header required) |
| Currency | VND |
| Exchange | symbol-dependent / lazy (`EXCHANGE = None` for MVP) |

This adapter is a **clean-room** implementation built only against the provider's
own server and the publicly documented TradingView UDF protocol. No third-party
Vietnamese-finance library was read, cited, or used as a source.

## Endpoint and parameters

```
GET https://dchart-api.vndirect.com.vn/dchart/history
    ?symbol=FPT
    &resolution=D
    &from=<unix_seconds>
    &to=<unix_seconds>
```

Parameter names (exact, verified live): `symbol`, `resolution`, `from`, `to`.
`from`/`to` are UNIX epoch seconds (UTC). The adapter computes them from the
requested VN-local date range.

### Response shape (bare UDF — verified live 2026-06-17)

```json
{
  "t": [1704153600, 1704240000, ...],
  "c": [69.23, 69.519, ...],
  "o": [69.952, 69.013, ...],
  "h": [69.952, 69.663, ...],
  "l": [69.085, 68.869, ...],
  "v": [1714500, 1436900, ...],
  "s": "ok"
}
```

- `s` is the UDF status string (`ok`, `no_data`, `error`).
- Arrays `t/o/h/l/c/v` are parallel and equal-length.
- A bogus symbol returns HTTP 200 with an **empty body** (no JSON). The base
  transport surfaces that as `InvalidData` (non-JSON response). The standard
  `s: "no_data"` UDF status maps to `EmptyData`.

## Price scale

FPT daily close prints ~`69`–`72` in the feed, while FPT's real market price is
~69,000–72,000 VND. The feed is therefore quoted in **thousands of VND**, so
`PRICE_SCALE = 1000.0` to normalize bars to plain VND.

Verified live magnitudes (FPT, daily):
- 2026-06-16 close `72.3` → `72,300 VND`.

## Adjustment policy

`AdjustmentPolicy.PROVIDER_ADJUSTED`.

Reasoning (verified live): FPT daily close on 2015-01-05 is `7.139` (i.e.
~7,139 VND after scaling) while the 2026-06-16 close is `72.3` (~72,300 VND).
A roughly 10x rise across that span is consistent with the series being
**split/dividend back-adjusted** by the provider — older prices are scaled down so
the historical series is continuous with the current price. This is the canonical
back-adjusted signature, so the policy is `PROVIDER_ADJUSTED`.

## Intraday capability and retention

Verified live (2026-06-17) that the following resolutions return real bars:

| Interval | `resolution` token | Verified |
|----------|--------------------|----------|
| D1 (daily)   | `D`  | yes (required) |
| M1 (1-min)   | `1`  | yes |
| M5 (5-min)   | `5`  | yes |
| M15 (15-min) | `15` | yes |
| M30 (30-min) | `30` | yes |
| H1 (60-min)  | `60` | yes |

All six are wired into `SUPPORTED`. Weekly/monthly (`W1`/`MN1`) are **not**
included (no token verified for this MVP); requesting them raises
`UnsupportedInterval`.

Retention note: intraday history is finite — recent windows return full bars,
but very old intraday ranges may be thin or empty. Daily history goes back at
least to 2015 (verified). Callers should treat intraday as best-effort and
recent-window oriented.

## robots.txt / ToS observation

`GET /robots.txt` on the charting host returns **HTTP 404** (no robots policy
published at this path) as of 2026-06-17. There is no published robots directive
to honor or violate at the host root for the charting backend. No authentication
or click-through gate was encountered for the history endpoint.

Because no machine-readable crawl policy is published and the feed is the
provider's own charting backend, treat access conservatively: low request volume,
descriptive User-Agent, runtime-only fetches.

## Rate-limit note

No explicit rate-limit headers or documented quota were observed. Be polite:
single requests per user action, no bulk scraping, reasonable timeouts (default
25s, IPv4-forced transport). Back off on transport errors rather than retrying
aggressively.

## Compliance caveat

- **Runtime fetch only.** This adapter fetches data on demand at runtime for the
  end user's own analysis. It does **not** cache, bulk-download, redistribute, or
  resell provider data.
- No provider price rows are committed to this repository. All tests use
  hand-crafted **synthetic** UDF payloads (see `tests/test_vndirect.py`).
- Downstream users are responsible for complying with VNDirect's terms of use for
  their own usage. If the provider publishes terms restricting programmatic
  access, those terms govern and this adapter should be reconfigured or disabled.
