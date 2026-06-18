# Source: Coinbase Exchange Public REST — product candles (crypto OHLCV)

**Domain:** Crypto major coins, USD-denominated OHLCV. **Backup** source in the crypto
failover chain (Binance primary -> Coinbase backup).
**Adapter:** `vnfin.crypto.CoinbaseCryptoSource` (`vnfin/crypto/coinbase.py`).
**Models:** `vnfin.crypto.CryptoBar`, `vnfin.crypto.CryptoHistory` (`vnfin/crypto/models.py`).
**Provenance:** Endpoint learned from general knowledge of public exchange APIs and the
project research doc `docs/research/2026-06-18-crypto.md`; verified by live `curl` and a
live adapter probe against Coinbase's own server. **Clean-room:** no vnstock / VNStock or
any derivative was browsed, cloned, cited, or referenced.

## Endpoint

```
GET https://api.exchange.coinbase.com/products/{PRODUCT}/candles
    ?granularity={sec}      one of 60,300,900,3600,21600,86400 (= 1m,5m,15m,1h,6h,1d)
    &start={ISO8601}        UTC, e.g. 2024-01-01T00:00:00
    &end={ISO8601}          UTC; inclusive window
```

- **Auth:** None. Keyless public market-data endpoint.
- **Product symbols:** `BASE-QUOTE` with a hyphen (e.g. `BTC-USD`, `ETH-USD`). The adapter
  also accepts the Binance-style concatenated form (`BTCUSDT`) and normalizes a USD-stablecoin
  quote (USDT/BUSD/FDUSD/...) to the native `BASE-USD` fiat product; `USDC`/`USD` keep their
  own native product leg.
- **Quote currency:** native fiat **USD** (and USDC). USD-stablecoin quotes are reported as
  `currency="USD"` (~1:1) so this source is unit-homogeneous with the Binance primary. A
  non-USD quote (e.g. an `-BTC` product) keeps its actual quote asset as `currency`.
- **Granularity gaps:** Coinbase has **no 30m, weekly, or monthly** candle. Those intervals are
  unsupported; the failover capability guard skips this source for them (no network call) and
  stays on a source that supports them (e.g. Binance).
- **History:** Long (years), but only **~300 candles per call** — paginate backward via
  `start`/`end` windows.

## Pagination (≤300 candles/call) — boundary-candle safety (B10)

Coinbase caps each call at ~300 candles and, when asked for an inclusive `[start, end]` window
that contains more than 300 candle slots, returns only the **300 newest**, silently dropping the
oldest boundary candles.

The adapter therefore:

1. Windows each page to **exactly `PAGE_CANDLES` candle slots**:
   `page_span = step_sec * (PAGE_CANDLES - 1)` (an inclusive `[lo, hi]` window of
   `step * (n-1)` holds exactly `n` slots). Using `step * PAGE_CANDLES` would request 301
   inclusive slots, so the provider's 300-row cap drops one boundary candle per page — and the
   backward step then skips it. This was bug **B10** (a 750-bar synthetic range returned 748).
2. **Overlaps** consecutive backward slabs (the upper bound of the next slab equals the lower
   bound of the current one) and **de-duplicates** by candle open time (`seen_sec`), so a candle
   straddling a slab boundary is always fetched and never double-counted.

Regression tests assert an exact 750-bar count for a multi-page range
(`tests/test_crypto_coinbase.py::test_pagination_multi_page_covers_exact_bar_count_no_boundary_drop`)
and that overlap does not double-count
(`...::test_pagination_deduplicates_overlapping_slabs`).

## Response shape (live-verified)

Success = a JSON **array of arrays**, **newest-first**. Each candle row (6 fields):

| idx | field | type | adapter use |
|-----|-------|------|-------------|
| 0 | time (epoch **seconds**) | number | `CryptoBar.time` (UTC) |
| 1 | low | number | `low` (float) |
| 2 | high | number | `high` (float) |
| 3 | open | number | `open` (float) |
| 4 | close | number | `close` (float) |
| 5 | volume (base asset) | number | `volume` (**float**, fractional) |

Two differences vs Binance: time is epoch **seconds** (not ms), and the order is
**low, high, open, close** (not open, high, low, close). Scalars are JSON **numbers** (not
strings). The adapter sorts to oldest-first internally.

Live proof (BTC-USD 1d, 2 rows):
```
[[1781654400,64491.88,66384.01,65616.64,65794.87,4159.143],[1781568000,65300.03,66944,66276.79,65616.64,6347.81]]
```
(order = time, low, high, open, close, volume)

## Errors

- Bad product -> JSON **object** `{"message":"NotFound"}`; unsupported granularity ->
  `{"message":"Unsupported granularity"}`. Both surface as `EmptyData` (a `SourceError`
  subclass) so the adapter is **failover-safe**.
- Empty array `[]` (or no rows in range) -> `EmptyData`. Non-JSON / unexpected payload type ->
  `InvalidData`. Malformed/garbage/null scalar, non-finite (NaN/Inf), negative price/volume,
  OHLC-invariant violation, or short row -> `InvalidData`. Transport failure -> `SourceUnavailable`.

## Result unit guard (B9)

Both crypto adapters can serve a non-USD pair (e.g. an `-BTC` product or a Binance `ETHBTC`),
returning `currency`/`value_unit="BTC"`. The default crypto chain promises **USD**, so
`FailoverCryptoClient` validates the **result's** actual `currency`/`value_unit` against the
chain's declared unit in the accept path and **rejects** a non-USD series (it never serves a
BTC-quoted series mislabeled as USD). Regression:
`tests/test_crypto_failover.py::test_ethbtc_btc_quoted_result_is_rejected_in_usd_chain`.

## Rate limits

Public market-data ~**10 req/s** per IP (per Coinbase docs). Deep-history backfills should
paginate with small sleeps and back off on `429`.

## Compliance

- `api.exchange.coinbase.com/robots.txt` returns `{"message":"Unauthorized."}` (no crawl policy
  served); the keyless JSON market-data API is documented and public.
- **Redistribution:** no published grant on this endpoint. Treat as personal/internal research,
  **runtime-fetch only, no bundled/redistributed data**. All committed test fixtures are
  synthetic (hand-crafted to match the shape, obviously-fake round numbers) — no real provider
  rows are stored. Real proof snippets live only in `docs/research/2026-06-18-crypto.md`.

## Live test policy

Live cross-source agreement and USD-series checks are in
`live_tests/test_crypto_failover_live.py` (require `VNFIN_LIVE=1`, outside default collection).
