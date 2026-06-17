# Source: `kis` — KIS Vietnam (KIS Securities Vietnam)

Adapter class: `KISVietnamSource` (`vnfin/sources/kis.py`), subclass of the shared
`UDFSource` TradingView-UDF transport base.

## Endpoint / protocol

- **Base URL:** `https://api.ikis.kisvn.vn`
- **History path:** `/api/v3/chart/history`
- **Protocol:** TradingView UDF-style price history (public UDF query contract).
- **Request (GET) params:** `symbol`, `resolution`, `from` (unix seconds, UTC), `to` (unix seconds, UTC).
  - Example: `?symbol=FPT&resolution=1D&from=1717174800&to=1718298000`
- **Response shape:** **BARE** UDF object at the top level — no envelope.
  Keys: `t` (unix-second timestamps), `o`, `h`, `l`, `c`, `v` (parallel arrays),
  `s` (status string, e.g. `"ok"`), plus a `nextTime` paging hint.
  Because it is bare, the adapter does **not** override `_extract`.

## Authentication

- **None.** The endpoint served full history for FPT over plain HTTPS GET with no
  API key, no cookie, and no auth header (only a browser `User-Agent` was sent).
- The adapter sends only the inherited default `User-Agent`. No credentials are
  stored, required, or transmitted.

## robots.txt / ToS observation

- `GET https://api.ikis.kisvn.vn/robots.txt` → **HTTP 404** (no robots policy
  published at the API host on the probe date, 2026-06-18).
- This is a brokerage charting backend, not a documented public data API. There is
  **no published redistribution license**. We therefore treat all data as
  **runtime-fetch-only**: it is fetched live on behalf of the end user for their
  own analysis and is **never cached, redistributed, or republished** by vnfin.
- No real price rows from this feed are committed to the repository. All tests use
  hand-crafted synthetic payloads only.

## Rate limits

- No documented rate limit and no `Retry-After`/`X-RateLimit-*` headers observed on
  the probe responses. Treat the endpoint **conservatively**: serialize requests,
  keep request volume low, and back off on transport errors. The base class wraps
  transport failures as `SourceUnavailable` so the failover client can route away.

## Price scaling — `PRICE_SCALE = 1.0`

- Recent daily FPT closes print as clean integer VND, e.g. `72200.0`, `74800.0`,
  `76500.0` (mid-2026). FPT trades around 70k–80k VND/share, so the feed is in
  **raw VND**, not thousands-of-VND. Therefore `PRICE_SCALE = 1.0`.

## Adjustment policy — `AdjustmentPolicy.MIXED`

KIS history is **not homogeneous** across time. Probing FPT at three epochs:

| Window      | Close magnitude | Decimals                |
|-------------|-----------------|-------------------------|
| Jan 2015    | ~1142–1175      | long fractional         |
| Jun 2024    | ~98k–113k       | long fractional         |
| Jun 2026    | ~72k–77k        | clean integers (`72900.0`) |

- Recent bars are clean raw-VND quotes (round lots). Older bars carry long
  fractional values and are scaled to a different basis (2015 FPT printing ~1150 is
  far below its real ~2015 raw quote, i.e. heavily back-adjusted **down** for
  cumulative dividends/splits), while 2024 prints ~100k.
- The series therefore **mixes** an adjusted historical tail with a raw recent
  head — the hallmark of a non-homogeneous feed. We cannot guarantee a single
  consistent adjustment basis across an arbitrary requested range.
- Conservative, accurate choice: **`AdjustmentPolicy.MIXED`** (the model exposes a
  `MIXED` value precisely for non-homogeneous series). Downstream code that needs a
  guaranteed homogeneous basis should treat MIXED as "do not assume adjusted" and
  prefer a single-basis source for long-horizon split/dividend math.

## Intraday capability + retention

- Verified working resolutions (FPT, recent week): `1D` (daily) plus intraday
  `60`, `30`, `15`, `5`, `1` minutes — **all returned populated arrays**.
- Resolution token map (vnfin `Interval` → KIS token):
  `D1→"1D"`, `H1→"60"`, `M30→"30"`, `M15→"15"`, `M5→"5"`, `M1→"1"`.
- Intraday timestamps land inside the HOSE trading session in Asia/Ho_Chi_Minh
  (e.g. 10:00, 11:00 local), confirming correct UTC→VN conversion.
- **Retention:** intraday history depth was not stress-tested; brokerage charting
  backends typically retain limited intraday lookback. Treat deep intraday history
  as best-effort; daily is the reliable long-horizon series.

## `no_data` / empty handling

- A bogus symbol returns `s:"ok"` with **empty** OHLCV arrays (not `s:"no_data"`).
  The base class maps empty/range-empty results to `EmptyData`.
- The base also honors an explicit `s:"no_data"` (or `"error"`) status → `EmptyData`.
  The adapter relies on the inherited base handling for both paths.

## Compliance caveat

- Runtime fetch only, on behalf of the requesting user, for their own analysis.
- No redistribution, no republication, no bulk export, no committed real rows.
- No auth/credentials used or stored. If KIS later publishes a robots policy or ToS
  restricting access, this source must be re-vetted before continued use.

## Clean-room note

This adapter was built solely against the provider's own server responses and the
public TradingView UDF query protocol. No third-party financial-data library, its
docs, schemas, naming, or behavior were consulted.
