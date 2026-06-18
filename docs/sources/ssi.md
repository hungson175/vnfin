# Source: `ssi` (SSI iBoard chart history)

Adapter: `vnfin.sources.ssi.SSIiBoardSource` (subclass of `vnfin.sources.udf.UDFSource`).

This document records the provenance and compliance posture for the SSI iBoard
TradingView-UDF style price-history endpoint. It is written clean-room from a
direct live probe of the provider's own public server and the public TradingView
UDF protocol shape — no third-party library, code, or documentation was consulted.

## Endpoint

- **Base URL:** `https://iboard-api.ssi.com.vn`
- **History path:** `/statistics/charts/history`
- **Full example:**
  `https://iboard-api.ssi.com.vn/statistics/charts/history?resolution=1D&symbol=FPT&from=<unix_seconds>&to=<unix_seconds>`
- **Method:** `GET`
- **Query parameters:**
  - `resolution` — bar resolution token (see resolution map below)
  - `symbol` — provider ticker, e.g. `FPT`
  - `from` — range start, UNIX seconds (UTC)
  - `to` — range end, UNIX seconds (UTC)

## Authentication

None observed. The history endpoint is reachable anonymously with a normal
browser `User-Agent`; no API key, cookie, or token was required during probing.

## Response shape (enveloped)

The response is a JSON **envelope** wrapping the UDF arrays in a `data` object:

```json
{
  "code": "SUCCESS",
  "message": "Get chart history data success",
  "data": {
    "t": [ ... ],  "o": [ ... ],  "h": [ ... ],
    "l": [ ... ],  "c": [ ... ],  "v": [ ... ],
    "s": "ok",
    "nextTime": null
  },
  "status": "ok"
}
```

The UDF status field `s` lives **inside** `data` (values seen: `"ok"`). The
adapter overrides `_extract` to return `parsed["data"]` so the shared base sees a
plain UDF dict. The base treats only `s == "ok"` as success; `s in {"no_data","error"}`
raises `EmptyData`, and any other/missing value raises `InvalidData`. A request for
a non-existent symbol returns `code:"SUCCESS"`, `s:"ok"`, and **empty arrays**,
which the base also surfaces as `EmptyData` ("no bars in requested range").

Before unwrapping `data`, `_extract` validates the outer envelope:

- `code` must equal `"SUCCESS"` (observed success value). `code in {"FAIL","ERROR"}`
  raises `SourceUnavailable`; any other/missing value raises `InvalidData`.
- `status` must equal `"ok"` (observed success value). `status == "error"` raises
  `SourceUnavailable`; any other/missing value raises `InvalidData`.

This ensures a provider-side error envelope never parses as empty/success data.

## Price magnitude and `PRICE_SCALE`

FPT (HOSE) daily close in June 2026 prints as ~72–76 in the feed. The Vietnamese
exchanges quote FPT in the tens-of-thousands of VND, so the feed is denominated
in **thousands of VND**. Therefore `PRICE_SCALE = 1000.0` (feed × 1000 → VND).

## Adjustment policy

`AdjustmentPolicy.PROVIDER_ADJUSTED`.

Reasoning (clean-room, from price magnitude only): FPT daily close in January
2015 prints ~7.1 in the feed (~7,100 VND), versus ~72–76 in June 2026 (~72,000–
76,000 VND) — roughly a 10× rise. FPT's nominal market price did not rise 10×
purely from price appreciation; the old prints are clearly **back-adjusted** for
the stock's split/dividend history (an adjusted series rebases historical prices
downward). A raw/unadjusted series would show old prices in the same nominal band
as recent ones. The downward-rebased history is the signature of a provider-
adjusted series, hence `PROVIDER_ADJUSTED`.

## Resolutions / intraday capability

Probed live against FPT; all of the following returned real, correctly-spaced
bars:

| `vnfin` `Interval` | feed token | verified |
|--------------------|-----------|----------|
| `D1` (daily)       | `1D`      | yes (required) |
| `H1` (1 hour)      | `60`      | yes |
| `M30` (30 min)     | `30`      | yes |
| `M15` (15 min)     | `15`      | yes |
| `M5` (5 min)       | `5`       | yes |
| `M1` (1 min)       | `1`       | yes |

`W1`/`MN1` are intentionally **omitted** for the MVP: the `1W`/`1M` tokens
returned daily-spaced timestamps (i.e. they silently fell back to daily rather
than aggregating), and while bare `W`/`M` tokens produced weekly/monthly spacing,
the inconsistency makes weekly/monthly support ambiguous. We expose only the
resolutions whose semantics we verified. Requesting an unsupported interval
raises `UnsupportedInterval` before any network call.

### Intraday retention

Minute and hourly bars were available for the most recent trading sessions
during probing. Deep historical intraday retention was not exhaustively measured;
callers needing long intraday histories should not assume unlimited backfill.
Daily history reaches back many years (verified to at least 2015).

## robots.txt / ToS observation

`GET https://iboard-api.ssi.com.vn/robots.txt` does not return a robots file; the
API gateway responds with a JSON "no Route matched with those values" message.
There is therefore no machine-readable crawl directive at the API host. This is a
provider API host (not an HTML site), so no `robots.txt` allow/deny applies to
the history endpoint. No explicit programmatic-access terms were retrievable from
the API host itself; treat the data as the provider's property.

## Rate-limit note

No rate-limit headers or throttling were observed during light, sequential
probing (a handful of requests over a few seconds). No documented quota is known.
Treat the endpoint conservatively: keep request volume low, fetch sequentially,
add backoff on errors, and avoid bursty/parallel scraping. The adapter forces
IPv4 and a 25s timeout via the shared base transport.

## Compliance caveat

- **Runtime fetch only.** This adapter fetches price history at runtime on behalf
  of the end user from the provider's own public server. It does **not** bundle,
  cache to disk, or redistribute provider data.
- **No redistribution.** Do not republish, resell, or redistribute SSI price data
  obtained through this adapter. The data belongs to the provider/exchange.
- **No real rows in the repo.** All tests use hand-crafted synthetic payloads. No
  real broker price rows are committed.
- If the provider publishes terms restricting programmatic access, those terms
  govern; be conservative and stop on any access restriction.
