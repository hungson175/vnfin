# Source: `vps`

Clean-room adapter for the public **TradingView UDF** history feed served by the
VPS data host. Implemented solely against the host's own server and the public
[TradingView UDF protocol](https://www.tradingview.com/charting-library-docs/latest/connecting_data/UDF/).
No third-party library, schema, or naming pattern was consulted.

## Endpoint

| Field | Value |
|-------|-------|
| `BASE_URL` | `https://histdatafeed.vps.com.vn` |
| `HISTORY_PATH` | `/tradingview/history` |
| Method | `GET` |
| Envelope | none — **bare UDF** (arrays at top level) |
| Daily resolution token | `D` |
| Intraday resolution tokens | `1`, `5`, `15`, `30`, `60` (minutes) |

### Request parameters

```
GET /tradingview/history?symbol=FPT&resolution=D&from=<unix>&to=<unix>
```

- `symbol` — provider ticker (e.g. `FPT`), upper-cased.
- `resolution` — UDF token (`D`, or minute count for intraday).
- `from`, `to` — inclusive UNIX-second window bounds (UTC).

### Response shape (verified live, FPT)

Bare UDF object, prices in **thousands of VND**:

```json
{
  "symbol": "FPT",
  "s": "ok",
  "t": [1704153600, ...],
  "o": [69.951, ...],
  "h": [69.951, ...],
  "l": [69.085, ...],
  "c": [69.229, ...],
  "v": [1717109, ...]
}
```

- `s` is the UDF status: `ok` (data), `no_data` (empty arrays, e.g. interval/window
  with no bars), or `error`. Empty/`no_data` is mapped to `EmptyData` by the base.
- There is no enclosing `data`/`code` wrapper, so `_extract` is **not** overridden.

## Price scale

Live FPT daily close prints **~69-70** (Jan 2024) and intraday **~73-74** (Jun 2026).
The Vietnamese exchange quotes FPT in the tens-of-thousands of VND, so the feed is in
**thousands of VND** → `PRICE_SCALE = 1000.0` (e.g. `73.4` → `73,400 VND`).

## Adjustment policy

`PROVIDER_ADJUSTED`.

Reasoning: the same FPT daily series prints **~8.3** in early Jan 2015 vs **~69-70** in
Jan 2024 and **~73-74** in mid-2026. FPT's *nominal* market price in 2015 was already in
the tens of thousands of VND; the deflated ~8,300 VND back-history is only consistent
with split/dividend **back-adjustment** of older bars. The series is therefore treated
as provider-adjusted, not raw.

## Intraday capability and retention

All five intraday resolutions (`1`, `5`, `15`, `30`, `60`) return `s: "ok"` with bars
for **recent** windows (verified for the last several trading days). The **same**
resolutions return `s: "no_data"` for older windows (e.g. mid-2024), so intraday history
has a **limited retention window** — only daily (`D`) is reliable for deep history.

Daily (`D`) is the guaranteed common denominator and is always included. The intraday
tokens are advertised in `RESOLUTION_MAP`/`SUPPORTED` because they are live-verified to
work; callers requesting deep intraday history should expect `EmptyData` outside the
retention window and fall back to daily.

## Auth, rate limits, ToS / robots

- **Auth:** none. The endpoint is an unauthenticated public GET (`Access-Control-Allow-Origin: *`).
- **robots.txt:** the feed host `histdatafeed.vps.com.vn` returns **HTTP 404** for
  `/robots.txt` (no crawl policy published → no disallow). The parent site
  `vps.com.vn/robots.txt` is `User-Agent: * / Allow: /` (permissive).
- **Rate limits:** none documented and none observed during light probing. The adapter
  is courteous by default (single request per `get_history` call, IPv4 transport,
  browser User-Agent, 25 s timeout). Callers should self-throttle bulk backfills.

## Compliance caveat

This adapter performs **runtime fetch only**: it requests data on demand for the caller's
own use. vnfin does **not** cache, mirror, bundle, or redistribute VPS price rows, and the
test suite uses **hand-crafted synthetic payloads only** — no real broker rows are
committed to the repository. Downstream redistribution of the fetched data is the
caller's responsibility and may be restricted by the provider's terms; consumers should
review VPS's terms of use before republishing.

## Provenance

- Live probes (FPT, daily + all intraday resolutions, 2015 / 2024 / 2026 windows) run on
  2026-06-17/18 to confirm param names, bare-vs-envelope shape, price magnitude,
  intraday capability/retention, and adjustment behavior.
- Protocol reference: public TradingView UDF spec.
- No VNStock / vnstock material was read, cited, or used (clean-room).
