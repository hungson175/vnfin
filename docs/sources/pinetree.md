# Source: pinetree

Clean-room price-history adapter for the Pinetree Securities public charting
backend, which speaks the open **TradingView UDF** (Universal Data Feed)
protocol. This document records provenance, the verified response shape, and
compliance reasoning. No third-party financial library was read, cited, or used
to build this adapter — only the provider's own server plus the public UDF
protocol.

## Endpoint

- **Base URL:** `https://charts.pinetree.vn`
- **History path:** `/tv/history`
- **Full request:** `GET /tv/history?symbol=<SYM>&resolution=<TOKEN>&from=<UNIX>&to=<UNIX>`
- **Query params:** `symbol`, `resolution`, `from`, `to` (UNIX seconds, UTC).
- **Server:** `nginx/1.20.1`; `Content-Type: text/plain;charset=UTF-8`;
  `Allow: GET, POST, HEAD`.

## Auth

None. The history endpoint is an unauthenticated public GET. No API key,
cookie, token, or referer is required. We send only a browser `User-Agent`.

## Response shape (verified live, bare UDF)

The endpoint returns a **bare** TradingView UDF object at the top level — there
is **no** wrapping envelope (no `code`/`message`/`data` layer). Example fields
observed for `FPT` (values illustrative, not committed to tests):

```json
{
  "t": [1780272000, 1780358400, ...],   // bar open time, UNIX seconds UTC
  "o": [72200.0, 73000.0, ...],          // open
  "h": [73400.0, 75600.0, ...],          // high
  "l": [72100.0, 73000.0, ...],          // low
  "c": [72900.0, 74800.0, ...],          // close
  "v": [5972700.0, 1.7368E7, ...],       // volume (shares)
  "s": "ok",                              // status: "ok" | "no_data" | "error"
  "nextTime": -1                          // pagination hint (ignored)
}
```

Because the payload is bare, the adapter uses the base-class `_extract` as-is
(no override) and does **not** set an envelope.

## Price scale: 1.0 (raw VND)

FPT daily closes print around **72,900–76,500** in June 2026. The real HOSE
price of FPT in that period is on the order of tens of thousands of VND, so the
feed is already in **raw VND**. Therefore `PRICE_SCALE = 1.0` (no
thousands-of-VND multiplier).

## Adjustment policy: PROVIDER_ADJUSTED

A 2015-01 daily probe for FPT returns opens around **7,360 / 7,290 / 7,380**
(raw VND), while June-2026 FPT trades around **73,000** raw VND — roughly a 10x
gap. Nominal historical FPT was not ~7,000 VND in early 2015; that low level is
the signature of **split/dividend back-adjustment** applied to the historical
series. The provider therefore serves a back-adjusted series, so
`ADJUSTMENT_POLICY = AdjustmentPolicy.PROVIDER_ADJUSTED`.

## Intraday capability + retention

All intraday resolution tokens were verified to return real bars
(`s == "ok"`) for FPT over a recent window:

| Interval enum | UDF token | Verified |
|---------------|-----------|----------|
| `D1`          | `1D`      | yes (REQUIRED) |
| `M1`          | `1`       | yes (453 bars / 2 days) |
| `M5`          | `5`       | yes |
| `M15`         | `15`      | yes |
| `M30`         | `30`      | yes |
| `H1`          | `60`      | yes |

The `120` (2-hour) token also returns data, but the `Interval` enum has no
2-hour member, so it is not mapped. `W1` (weekly) and `MN1` (monthly) are **not**
mapped — they are outside the verified token set for this adapter and are left
unsupported (requesting them raises `UnsupportedInterval`).

Retention: the 2015 daily probe succeeded, so multi-year daily history is
available. Intraday retention was not exhaustively measured; recent windows
return dense bars (1-minute returned hundreds of bars over two days).

## robots.txt / ToS observation

`GET /robots.txt` did **not** return a parseable robots policy — it returned a
binary blob prefixed with a Fasoo DRM marker (`DRMONE … Fasoo DRM`), i.e. the
host does not publish a conventional `robots.txt` disallow set for this charting
backend. There is consequently no machine-readable crawl directive to honor or
violate at this path. No public API terms-of-use document was located at the
host root for this charting endpoint.

## Rate-limit note

No explicit rate-limit headers (`X-RateLimit-*`, `Retry-After`) were observed on
responses. Treat the endpoint conservatively: the adapter fetches only on demand
(one request per `get_history` call), uses a bounded timeout, and forces IPv4
via the base transport. Callers should avoid tight polling loops.

## Compliance caveat

- **Runtime fetch only.** This adapter fetches data live at call time for the
  user's own analysis. It does **not** bulk-download, cache to disk, or
  redistribute the provider's data.
- **No redistribution.** Pinetree's price data is not re-published or bundled
  with this library; only the synthetic test fixtures (hand-crafted, not real
  rows) are committed to the repository.
- **Clean-room.** Endpoint, params, and shape were learned solely from the
  provider's own server and the public TradingView UDF specification.
- If the provider publishes terms that restrict programmatic access, those terms
  govern and usage should be revisited.
