# Source: Binance Public REST — klines (crypto OHLCV)

**Domain:** Crypto major coins, USD-denominated OHLCV.
**Adapter:** `vnfin.crypto.BinanceCryptoSource` (`vnfin/crypto/binance.py`).
**Models:** `vnfin.crypto.CryptoBar`, `vnfin.crypto.CryptoHistory` (`vnfin/crypto/models.py`).
**Provenance:** Endpoint learned from general knowledge of public exchange APIs and the
project research doc `docs/research/2026-06-18-crypto.md`; verified by live `curl` and a
live adapter probe against Binance's own server. **Clean-room:** no vnstock / VNStock or any
derivative was browsed, cloned, cited, or referenced.

## Endpoint

```
GET https://api.binance.com/api/v3/klines
    ?symbol={SYMBOL}        e.g. BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT
    &interval={token}       1m,5m,15m,30m,1h,1d,1w,1M (and 3m,2h,4h,6h,8h,12h,3d — not all mapped)
    &limit={1..1000}        default cap used by adapter: 1000
    &startTime={epoch_ms}   optional; startTime=0 returns genesis
    &endTime={epoch_ms}     optional
```

- **Auth:** None. Keyless public market-data endpoint.
- **Quote currency:** USDT, treated as **USD ~1:1**. Adapter sets `currency="USD"`. No
  price scaling. No native crypto/VND pair exists (`BTCVND` -> `-1121 Invalid symbol`); derive
  VND downstream by multiplying a USD/VND FX series.
- **History:** Deep. BTCUSDT daily genesis = 2017-08-17. Up to 1000 rows/call; paginate via
  `startTime`/`endTime`.

## Response shape (live-verified)

Success = a JSON **array of arrays**, oldest-first. Each kline row (12 fields):

| idx | field | type | adapter use |
|-----|-------|------|-------------|
| 0 | openTime (epoch **ms**) | int | `CryptoBar.time` (UTC) |
| 1 | open | **string** | `open` (float) |
| 2 | high | **string** | `high` (float) |
| 3 | low | **string** | `low` (float) |
| 4 | close | **string** | `close` (float) |
| 5 | volume (base asset) | **string** | `volume` (**float**, fractional) |
| 6 | closeTime (epoch ms) | int | unused |
| 7 | quoteAssetVolume | string | unused |
| 8 | numberOfTrades | int | unused |
| 9 | takerBuyBaseVolume | string | unused |
| 10 | takerBuyQuoteVolume | string | unused |
| 11 | ignore | string | unused |

Numeric scalars are strings; the adapter parses them to `float`. Base-asset volume is
fractional, so `CryptoBar.volume` is a `float` (not `int` like the VN equity `PriceBar`).

Live proof (BTCUSDT 1d, 2 rows):
```
[[1781568000000,"66328.74000000","66992.00000000","65360.92000000","65675.01000000","14302.05801000",1781654399999,"945125184.25184060",2964629,...]]
```

## Errors

- Bad symbol / bad params -> **HTTP 400** with body `{"code":-1121,"msg":"Invalid symbol."}`
  (a JSON **object**, not an array).
- With the **default** httpx `http_get` (which calls `raise_for_status()`), an HTTP 400 surfaces
  as `SourceUnavailable` (transport). With an injected `http_get` that returns the body on non-2xx,
  the JSON error object is parsed and surfaces as `EmptyData`. Both are `SourceError` subclasses,
  so either way the adapter is **failover-safe**.
- Empty array `[]` -> `EmptyData`. Non-JSON body -> `InvalidData`. Malformed/garbage/null scalar,
  non-finite (NaN/Inf), negative volume, OHLC-invariant violation, or short row -> `InvalidData`.

## Rate limits

Request-weight based. `klines` weight is roughly 1–10 per call depending on `limit` (~10 at
`limit=1000`). Budget ~1200 weight/min per IP. Used weight is exposed in response headers
`x-mbx-used-weight` / `x-mbx-used-weight-1m`. Live probe observed `x-mbx-used-weight: 3`.
Back off when approaching the budget; deep-history backfills should paginate with small sleeps.

## Compliance

- `api.binance.com/robots.txt` is `Disallow: /` — that governs HTML crawlers, not this documented
  keyless JSON market-data API.
- **Redistribution:** no published grant on this endpoint. Treat as personal/internal
  research, **runtime-fetch only, no bundled/redistributed data**. All committed test fixtures are
  synthetic (hand-crafted to match the shape) — no real provider rows are stored.
