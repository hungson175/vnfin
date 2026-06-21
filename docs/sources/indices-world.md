# World/US equity-index sources (S&P 500) — provenance & vetting notes

Clean-room: every endpoint, parameter, column order and unit below was learned **only**
from Alpha Vantage's and Stooq's own official documentation / servers and the project
design note (`docs/design/world-index-sp500.md`). No vnstock / VNStock / derivative was
read, cited, or copied.

> **Redistribution:** neither provider grants redistribution here. Treat as
> personal/internal research, **runtime-fetch only** — do not bundle/redistribute data.
> Attribute the provider; poll modestly. Alpha Vantage is **bring-your-own-key (BYOK)**:
> the end user is the API customer.

These power **`vnfin.indices.world(symbol="SPY", start=None, end=None, *, interval=Interval.D1)`**
— a daily `PriceHistory` for the S&P 500 over its **own** 2-source failover chain. This is
entirely separate from the VN HOSE/HNX `index_history()` / `index_constituents()` path, which
is untouched.

## Accessor & chain (`vnfin/indices/world_client.py`)

- `world(...)` → `default_world_index_client(...)` → `FailoverWorldIndexClient`, a thin
  specialization of the domain-agnostic `vnfin.failover.FailoverClient`.
- **Chain:** `[AlphaVantageIndexSource (if key), StooqIndexSource]`. AV throttle/keyless and
  Stooq anti-bot are all `SourceUnavailable` (best-effort) → the chain tries the next, raising
  `AllSourcesFailed` only if **both** are unavailable. An incapable (keyless) AV source is
  skipped **before any network call** and does not burn `max_attempts`.
- **v1 supports `symbol="SPY"` only.** Any other symbol → a clear `InvalidData`. `symbol` is a
  defaulted param kept for forward-compat (future world indices), not because v1 accepts others.

## Server-side / deployment reality — a keyless datacenter `AllSourcesFailed` is EXPECTED

The two source facts compound on a typical **server / cloud / CI host (a datacenter IP)**:

- **No `ALPHAVANTAGE_API_KEY`** → the BYOK AV primary is skipped *before any network call*.
- **Stooq from a datacenter IP** → almost always the anti-bot HTML challenge → `SourceUnavailable`.

So **on a datacenter host with no AV key, `vnfin.indices.world("SPY", ...)` raising `AllSourcesFailed`
is the correct, EXPECTED outcome — not a transient bug or a flaky test.** Both legs are legitimately
unavailable and the chain has nothing left to serve. To use world-index from a server, **set
`ALPHAVANTAGE_API_KEY`** (BYOK): the AV primary then serves SPY directly and never depends on Stooq.
The keyless Stooq `^SPX` fallback is **residential-only / best-effort** — the path for a developer on
a residential IP, never something a server deployment should rely on.

## Sources

| Adapter | Host | Auth | Instrument · unit | Role |
|---|---|---|---|---|
| `AlphaVantageIndexSource` | `www.alphavantage.co/query` | **BYOK** `ALPHAVANTAGE_API_KEY` | **SPY ETF** · `USD/share (SPY ETF, S&P 500 proxy)` / `USD` | **PRIMARY** |
| `StooqIndexSource` | `stooq.com/q/d/l/?s=^spx&i=d` | none | **^SPX index level** · `index points` / `points` | **FALLBACK** (keyless, best-effort) |

### `AlphaVantageIndexSource` — PRIMARY (BYOK)

- `function=TIME_SERIES_DAILY`, `symbol=SPY`, `outputsize=full` (20y+ daily in one call),
  `datatype=json`. Reads the key from `api_key=` or the `ALPHAVANTAGE_API_KEY` env var (the
  **same** key as the #140 news source).
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
  errors; no data bundled or redistributed. **SPY (ETF market price), not `^GSPC`:** lighter IP
  than S&P DJI's proprietary index; ~0.1%/yr ETF tracking divergence, negligible for a
  rebased chart; SPY-only in v1 with the proxy provenance documented in the unit label + here.
- **Stooq:** keyless, runtime-fetched by the end user, best-effort, **no redistribution claim**,
  no bundled data.
- **Ruled out:** FRED (≤10y S&P license cap + S&P DJI redistribution prohibited); yfinance/Yahoo
  (ToS); Nasdaq Data Link (paid).

## Failover safety

Both adapters wrap transport errors as `SourceUnavailable`, malformed payloads / non-finite /
non-positive / OHLC-invariant violations as `InvalidData`, and no-rows as `EmptyData` — all
`vnfin.exceptions` subclasses, so the failover layer fails over cleanly.
