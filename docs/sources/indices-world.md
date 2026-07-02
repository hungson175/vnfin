# World/US equity-index sources — provenance & vetting notes

Clean-room: every endpoint, parameter, column order and unit below was learned **only**
from Alpha Vantage's and Stooq's own official documentation / servers and the project
design note (`docs/design/world-index-sp500.md`). No vnstock / VNStock / derivative was
read, cited, or copied.

> **Redistribution:** neither provider grants redistribution here. Treat as
> personal/internal research, **runtime-fetch only** — do not bundle/redistribute data.
> Attribute the provider; poll modestly. Alpha Vantage is **bring-your-own-key (BYOK)**:
> the end user is the API customer. No market data is vendored in the package.

These power **`vnfin.indices.world(symbol="SPY", start=None, end=None, *, interval=Interval.D1)`**
— a daily `PriceHistory` over its **own** 2-source failover chain. This is entirely separate from
the VN HOSE/HNX `index_history()` / `index_constituents()` path, which is untouched.

## Supported symbols (#193/#197) — all served in USD as US-listed ETFs

`world(...)` supports **8 symbols**, all fetched from Alpha Vantage `TIME_SERIES_DAILY` in **USD**
(every served instrument is a US-listed ETF):

| Asked symbol | Served AV ticker | `value_unit` | Proxy? (`proxy_for`) | Note |
|---|---|---|---|---|
| `SPY` | `SPY` | `USD/share (SPY ETF, S&P 500 proxy)` | — (direct) | caller asked the ETF; got the ETF |
| `QQQ` | `QQQ` | `USD/share (QQQ ETF, Nasdaq-100 proxy)` | — (direct) | caller asked the ETF; got the ETF |
| `^N225` | `EWJ` | `USD/share (EWJ ETF)` | `^N225` | EWJ = MSCI Japan ETF — **not** the JPY Nikkei 225 index |
| `^SSEC` | `FXI` | `USD/share (FXI ETF)` | `^SSEC` | FXI = FTSE China 50 ETF — **not** the CNY SSE Composite |
| `^STI` | `EWS` | `USD/share (EWS ETF)` | `^STI` | EWS = MSCI Singapore ETF — **not** the SGD Straits Times Index |
| `^KS11` | `EWY` | `USD/share (EWY ETF)` | `^KS11` | EWY = MSCI Korea 25/50 ETF — **not** the KRW KOSPI Composite |
| `^CSI300` | `ASHR` | `USD/share (ASHR ETF)` | `^CSI300` | ASHR tracks CSI 300, but this is a USD ETF price — **not** CNY index points |
| `^HSI` | `EWH` | `USD/share (EWH ETF)` | `^HSI` | EWH = MSCI Hong Kong 25-50 ETF — **not** the Hang Seng Index |

Any other symbol → a clear `InvalidData` enumerating the supported set.

> ## ⚠️ Caveat 1 — the Asian symbols are USD ETF PROXIES (FX-embedding, not faithful trackers)
>
> `^N225`/`^SSEC`/`^STI`/`^KS11`/`^CSI300`/`^HSI` are **not** served as the raw
> local-currency index. There is no
> keyless-from-server raw-index OHLCV source (Yahoo is blocked + ToS-prohibited; FRED is close-only
> and S&P-license-capped; the rest are key-gated/wrong-shape), so the only server-usable feed serves
> **US-listed ETFs in USD**. Two distortions follow, **never silent**:
>
> 1. **Not even precise trackers.** EWJ = MSCI Japan ≠ Nikkei 225; FXI = FTSE China 50 ≠ SSE
>    Composite; EWS = MSCI Singapore ≠ STI; EWY = MSCI Korea 25/50 ≠ KOSPI Composite;
>    EWH = MSCI Hong Kong 25-50 ≠ Hang Seng. ASHR is closest because its benchmark is CSI 300,
>    but the served series is still a USD ETF market price, not raw CNY index points.
> 2. **They embed USD/local FX.** A USD ETF series rebased ≠ the raw local-currency index rebased —
>    they diverge by the local currency's move against the dollar (USD/JPY, USD/CNY, USD/SGD,
>    USD/KRW, USD/HKD). For a rebasing/normalized chart this is a **real distortion**.
>
> Both are disclosed on every proxy result via the structured **`PriceHistory.proxy_for`** field
> (the asked index symbol) AND a **`proxy_substitution`** warning. Detect a proxy via `proxy_for`,
> never by regexing `warnings`. `SPY`/`QQQ` are direct (`proxy_for is None`, no proxy warning).

> ## ⚠️ Caveat 2 — v1 world series are PRICE-RETURN, not total-return
>
> AV's **free** `TIME_SERIES_DAILY` returns raw OHLCV only (`adjustment_policy=RAW`); the adjusted
> close (dividend-reinvested total return) needs the **premium** `TIME_SERIES_DAILY_ADJUSTED` endpoint,
> which v1 does not use. So **dividends are NOT reinvested** in these series. Over a long horizon this
> is material: a price-return chart understates total return by the cumulative dividend yield —
> **material over 10–25 years** (roughly the dividend yield compounded). Do not treat a v1 world series
> as a total-return index.

## Accessor & chain (`vnfin/indices/world_client.py`)

- `world(...)` → `default_world_index_client(...)` → `FailoverWorldIndexClient`, a thin
  specialization of the domain-agnostic `vnfin.failover.FailoverClient`.
- **Chain:** `[AlphaVantageIndexSource (if key), StooqIndexSource]`. AV throttle/keyless and
  Stooq anti-bot are all `SourceUnavailable` (best-effort) → the chain tries the next. An incapable
  (keyless) AV source is skipped **before any network call** and does not burn `max_attempts`.

## `MissingKey` contract + server-side deployment reality

The two source facts compound on a typical **server / cloud / CI host (a datacenter IP)**:

- **No `ALPHAVANTAGE_API_KEY`** → the BYOK AV primary is skipped *before any network call*.
- **Stooq from a datacenter IP** → almost always the anti-bot HTML challenge → `SourceUnavailable`.

So on a datacenter host with no AV key, both legs are legitimately unavailable. **`world(...)` then
raises `MissingKey`** (a `VnfinError`) whose message names **`ALPHAVANTAGE_API_KEY`** + the requested
symbol and the fix (`set ALPHAVANTAGE_API_KEY or pass api_key=`) — the actionable config signal, with
**no per-source attempt trail**. This is the correct, EXPECTED outcome there — not a transient bug.

`AllSourcesFailed` is **reserved** for the genuinely-failed case: a key **was** configured but AV still
failed (throttle/network) and the keyless fallback is down too. (No key + walled fallback → `MissingKey`;
key set + AV fail + fallback down → `AllSourcesFailed`.)

To use world-index from a server, **set `ALPHAVANTAGE_API_KEY`** (BYOK): the AV primary then serves
directly and never depends on Stooq. The keyless Stooq `^SPX` fallback is **residential-only /
best-effort** — never something a server deployment should rely on.

## Sources

| Adapter | Host | Auth | Instrument · unit | Role |
|---|---|---|---|---|
| `AlphaVantageIndexSource` | `www.alphavantage.co/query` | **BYOK** `ALPHAVANTAGE_API_KEY` | **8 US-listed ETFs** (SPY/QQQ direct; EWJ/FXI/EWS/EWY/ASHR/EWH proxies) · all `USD` | **PRIMARY** (only server-usable) |
| `StooqIndexSource` | `stooq.com/q/d/l/?s=^spx&i=d` | none | **^SPX index level** · `index points` / `points` | **FALLBACK** (keyless, residential-only) |

### `AlphaVantageIndexSource` — PRIMARY (BYOK)

- `function=TIME_SERIES_DAILY`, `symbol=<per-symbol av_ticker>` (resolved from the declarative
  `WORLD_INDEX_SPECS` table: SPY→SPY, QQQ→QQQ, ^N225→EWJ, ^SSEC→FXI, ^STI→EWS,
  ^KS11→EWY, ^CSI300→ASHR, ^HSI→EWH), `outputsize=full` (20y+ daily in one call),
  `datatype=json`. Reads the key from `api_key=` or the
  `ALPHAVANTAGE_API_KEY` env var (the **same** key as the #140 news source).
- **Q5 hard guard:** if AV returns an `"Error Message"` envelope or no `Time Series (Daily)` for an
  allowlisted symbol (the ETF is uncovered), the source raises `InvalidData` **naming the symbol** —
  never an empty or fabricated series.
- **Keyless → skip with no network call:** `supports()` returns `has_key`; `get_history` raises
  `SourceUnavailable` before any request (exact FRED BYOK pattern).
- **Key redaction:** every error/transport message is passed through `_redact_key(...)` so the
  key can never leak into an exception, even if the provider echoes it.
- **AV response-status mapping (failover-critical):**
  - `"Error Message"` (bad params/key) → `InvalidData` (redacted).
  - `"Note"` / `"Information"` (free-tier throttle; AV free tier is **25 req/day**) →
    `SourceUnavailable` (best-effort → Stooq fallback runs), **not** a crash.
  - non-dict / missing series / non-finite OHLC / OHLC-invariant violation → `InvalidData`.
- **Caching:** in-memory opt-in `cache_ttl` defaults to **6h** so repeated same-process calls
  don't spend the 25/day budget. No on-disk cache in v1 (a documented v2 follow-up).

### `StooqIndexSource` — FALLBACK (keyless, best-effort)

- CSV GET `https://stooq.com/q/d/l/?s=^spx&i=d`, parsing `Date,Open,High,Low,Close,Volume` →
  daily bars (the S&P 500 **index level**, in points).
- **Anti-bot challenge from datacenter IPs — residential-only / best-effort.** From datacenter IPs
  Stooq has structurally returned a JavaScript challenge page (HTML) instead of CSV since ~2020-12,
  so the CSV path is effectively dead from servers/cloud/CI. The adapter detects that body and raises
  `SourceUnavailable` (the chain moves on rather than choking). It still works from **residential**
  IPs, which is why it stays in the chain as the only keyless path — but it is best-effort and
  **never** something a server deployment should rely on (see *Server-side / deployment reality*
  above). Hence: **fallback, never primary.**
- malformed CSV / non-positive prices / OHLC-invariant violation → `InvalidData`.

## Cross-instrument failover (the one real wrinkle) — `fallback_instrument_served`

SPY (an ETF, **USD/share**, ~600) and ^SPX (the **index level**, in points, ~6000) are
**different instruments** whose magnitudes differ ~10×. The chain returns **only one** leg per
call — a disclosed failover-pick, **not a merge** — so the engine's unit-homogeneity guard is
**disabled** for this client (`unit_of` returns `None` for every source). This is deliberate
and safe because nothing is being mixed; the served `PriceHistory` self-discloses its instrument
via `source` + `value_unit` + `provider_symbol`. (Enforcing homogeneity here would repeat the
#157 "guards are for merges, not disclosed single-source picks" trap.)

Because a caller that ignores `value_unit` and mixes the two un-rebased would make a 10× error,
the result is **never silent about a substitution**: whenever the ^SPX (Stooq) leg is served
*instead of* the requested SPY — covering **both** the AV-throttle fallback path **and** the
keyless-AV-skipped path — a mechanical `fallback_instrument_served` warning is appended on
`PriceHistory.warnings` (emitted in the client `finalize`, so it survives like #179's
`series_end_gap`). The SPY-primary success path carries **no** such warning.

```python
from datetime import date
import vnfin

h = vnfin.indices.world("SPY", start=date(2024, 1, 1), end=date(2024, 6, 30))
print(h.source, h.provider_symbol, h.value_unit)   # 'alphavantage' 'SPY' 'USD/share (SPY ETF, S&P 500 proxy)'
for w in h.warnings:                                # 'fallback_instrument_served: ...' iff ^SPX was served
    print(w)
```

## Licensing / redistribution posture

- **Alpha Vantage:** BYOK — the end user is the API customer; official API only; key redacted in
  errors; no data bundled or redistributed. All 8 symbols are served as **US-listed ETF market
  prices** (SPY/QQQ/EWJ/FXI/EWS/EWY/ASHR/EWH), never the proprietary raw indices
  (`^GSPC`/`^NDX`/`^N225`/etc.) —
  lighter IP than S&P DJI / index-licensor data; the proxy provenance is documented in the unit
  label, the `proxy_for` field, the `proxy_substitution` warning, and the caveats above.
- **Stooq:** keyless, runtime-fetched by the end user, best-effort, **no redistribution claim**,
  no bundled data. ToS body not machine-readable in 2026; no explicit permit/prohibit — runtime-fetch
  tolerated, redistribution treated as prohibited.
- **Yahoo NOT used:** its ToS **explicitly prohibits automated access AND redistribution** (data from
  ICE/LSEG/CSI/S&P/CME, each with its own bans); also structurally blocked from datacenter IPs.
- **Ruled out:** FRED (≤10y S&P license cap + S&P DJI redistribution prohibited; also close-only);
  Nasdaq Data Link / Tiingo / TwelveData / FMP (paid / key-gated).

## Failover safety

Both adapters wrap transport errors as `SourceUnavailable`, malformed payloads / non-finite /
non-positive / OHLC-invariant violations as `InvalidData`, and no-rows as `EmptyData` — all
`vnfin.exceptions` subclasses, so the failover layer fails over cleanly.
