# Design note — #177 US/global equity index (S&P 500) — world-index accessor

> **SUPERSEDED in part by #193 (coverage + keyless-from-server reliability).** This note records the
> ORIGINAL #177 SPY-only design. As of #193 `world(...)` supports **5 symbols** — `SPY`,`QQQ`,`^N225`,
> `^SSEC`,`^STI`, all served via Alpha Vantage in USD (US-listed ETFs; the three Asian symbols are
> loudly-labeled USD ETF proxies EWJ/FXI/EWS with `proxy_for` + a `proxy_substitution` warning) — and the
> no-key path now raises **`MissingKey`** (not `AllSourcesFailed`). See `tasks/193-world-index-design.md`
> + `docs/sources/indices-world.md` for current behavior; the SPY-only statements below are historical.

**Status:** design-first, awaiting `vnfin-oss-reviewer` lead quick-gate (no code yet).
**Scope:** additive — new source adapters + one accessor; reuses `PriceHistory`. Boss-greenlit (2026-06-20);
TL handoff `handoff-202606202209`; specs `spec-202606201815-issue177`.
**Clean-room:** zero VNStock. Official AV API + runtime Stooq fetch only; no redistribution; BYOK for AV.

## 1. Accessor home + name

- **`vnfin.indices.world(symbol="SPY", start=None, end=None, *, interval=Interval.D1) -> PriceHistory`** —
  a module-level function in `vnfin/indices/__init__.py`, mirroring the gold module's per-provider factory
  split (`gold.vn()` / `gold.world()`, `gold/__init__.py:119-149`).
- **VN indices stay separate and untouched:** `index_history()` / `index_history_stitched()` /
  `index_constituents()` (`indices/client.py:76-185`) keep their HOSE/HNX chain. `world()` gets its own
  source chain + client factory, so no VN-semantic guard touches the world path.
- **v1 supports `symbol="SPY"` only.** Any other symbol → clear `ValueError`/`InvalidData`
  ("world index 'X' not supported in v1; only SPY"). `symbol` is kept as a defaulted param for forward
  compat (future world indices), not because v1 accepts others.

## 2. Two new sources (own chain) + factory

Both subclass `HttpDataSource` (auto transport→`SourceUnavailable`, IPv4, UA, opt-in cache). New files under
`vnfin/indices/` (e.g. `world_sources.py`); a `default_world_index_sources()` + `default_world_index_client()`
factory (gold-style, `gold/__init__.py:66-109`), exported additively in `indices/__init__.py.__all__`.

### 2a. `AlphaVantageIndexSource` — PRIMARY (BYOK)
- Reads `ALPHAVANTAGE_API_KEY` (param or env), mirroring `news/alpha_vantage.py:59-63` — **same key** as #140 news.
- `BASE_URL = "https://www.alphavantage.co/query"`; params `function="TIME_SERIES_DAILY"`, `symbol="SPY"`,
  `outputsize="full"` (20y+ in one call), `apikey`, `datatype="json"`.
- **Keyless → skip with NO network call:** `supports(...)` returns `has_key` and `get_history` raises
  `SourceUnavailable` before any request — exact FRED pattern (`macro/fred.py:85-110`).
- **Key redaction:** `_redact_key(text)` applied to all error text (`macro/fred.py:74-78`,
  `news/alpha_vantage.py:76-79`).
- Parse `"Time Series (Daily)"` → `PriceBar`s (`1. open`…`5. volume`); window-filter to `[start, end]`.
- **Unit/provenance:** `value_unit="USD/share (SPY ETF, S&P 500 proxy)"`, `currency="USD"`,
  `source="alphavantage"`, `provider_symbol="SPY"`.
- **AV response-status mapping (failover-critical):**
  - `"Error Message"` (bad params) → `InvalidData` (redacted).
  - `"Note"` / `"Information"` (rate-limit/throttle, AV free tier) → **`SourceUnavailable`** (best-effort →
    Stooq fallback runs), NOT a crash.
  - non-finite / missing OHLC / non-dict → `InvalidData` (`macro/fred.py:166-189` pattern).

### 2b. `StooqIndexSource` — FALLBACK (keyless, best-effort)
- CSV GET `https://stooq.com/q/d/l/?s=^spx&i=d`, mirroring `gold/stooq.py:43-59`.
- **Anti-bot/403 → `SourceUnavailable` (best-effort, never a hard crash)** — HTML-page detection exactly as
  `gold/stooq.py:64-70`.
- Parse CSV `Date,Open,High,Low,Close,Volume` → bars; window-filter. `value_unit="index points"`,
  `currency="points"` (matches VN index unit convention), `source="stooq"`, `provider_symbol="^SPX"`.
- malformed CSV → `InvalidData`.

## 3. Failover classification (the one real wrinkle — please confirm)

- **Chain:** `[AlphaVantageIndexSource (if key), StooqIndexSource]`. AV throttle/keyless and Stooq anti-bot
  are all `SourceUnavailable` (capability/best-effort) → the chain tries the next, and only
  `AllSourcesFailed` if BOTH are unavailable. Incapable sources don't burn `max_attempts`
  (`failover.py:251,261`).
- **Cross-instrument failover (SPY ↔ ^SPX):** the two legs return **different instruments and units**
  (SPY USD/share vs ^SPX index points). Only ONE leg's result is ever returned per call (failover-pick,
  **not a merge**), and the returned `PriceHistory` self-discloses via `source` + `value_unit` +
  `provider_symbol`. For a rebased-to-100 chart both are proportional. **RESOLVED (reviewer 22:24):**
  ACCEPT the disclosed cross-instrument fallback; the world-index client `finalize` must NOT impose
  unit/VND homogeneity (that guard is for MERGES; this is a single-source disclosed pick — the
  #157-ratios-guard-trap analog).
- **REQUIRED never-silent warning (reviewer 22:24):** magnitudes differ ~10× (SPY ~600 USD/share vs ^SPX
  ~6000 index points), so a caller ignoring `value_unit` and mixing them in a non-rebased calc is a 10×
  error. Therefore: whenever the **^SPX (Stooq) instrument is served instead of the SPY primary**, append a
  **mechanical** warning to `PriceHistory.warnings` — token `fallback_instrument_served`, human cause in the
  tail, e.g. `"fallback_instrument_served: requested SPY (USD/share, S&P 500 proxy) unavailable; served
  Stooq ^SPX index points (~10x different magnitude) — rebase before comparing"`. Emitted in the
  world-index client `finalize` (the failover seam, so it survives like #179's `series_end_gap`), keyed on
  the served result being the Stooq/^SPX leg — covers BOTH the AV-throttle fallback AND the keyless-skip
  (AV skipped → Stooq served directly) paths, since both substitute the requested SPY. Never silent
  (cf. #176/#172/#179).

## 4. Caching

- **Use the EXISTING opt-in in-memory `cache_ttl`** on `HttpDataSource` (`transport.py:309-320`, keyed by
  url+params+secret-hash) — set a sensible default (e.g. 6h) on the AV source so repeated same-process calls
  don't spend AV's 25-req/day free-tier budget. `outputsize=full` = 1 request per (uncached) call.
- **No new persistent/on-disk cache in v1** (would be new surface). If 25/day proves tight in real use, a
  persistent cache is a documented v2 follow-up. **Decision for you:** in-memory `cache_ttl` v1 — OK?

## 5. Licensing / redistribution posture

- **AV:** BYOK — the end user is the API customer; official API only; key redacted in errors; no data bundled
  or redistributed. **SPY (ETF market price) not `^GSPC`** — lighter IP than S&P DJI's proprietary index;
  ~0.1%/yr ETF tracking divergence, negligible for a rebased chart; **SPY-only v1**, proxy provenance
  documented in the unit label + docs.
- **Stooq:** keyless, runtime-fetched by the end user, best-effort, **no redistribution claim**, no bundled data.
- **FRED RULED OUT** (≤10y S&P license cap + S&P DJI redistribution prohibited). yfinance/Yahoo (ToS) and
  Nasdaq DL (paid) also out.

## 6. Test matrix (synthetic, offline — TDD red-first)

1. AV full payload → typed daily `PriceHistory`, USD/share unit, `source=alphavantage`, full history, window-filtered.
2. AV error text → key redacted (assert raw key absent from message).
3. keyless → AV skipped **with no network call** (assert injected `http_get` not called) + Stooq fallback used.
4. AV `"Note"`/`"Information"` throttle → `SourceUnavailable` → Stooq fallback runs.
5. Stooq `^SPX` CSV → index-points series, `source=stooq`.
6. Stooq anti-bot HTML/403 → `SourceUnavailable` handled (no crash); AV also down → `AllSourcesFailed` with clear reasons.
7. malformed payloads (both) → `InvalidData`.
8. `cache_ttl` → 2nd same-process call makes no 2nd network call (assert `http_get` called once).
9. non-SPY symbol in v1 → clear error.
10. public-API additive: new accessor + sources exported; `PriceHistory` reused; frozen snapshot stays
    additive-green (regen at release only — see [[public-api-snapshot-is-release-time-not-per-feature]]).
11. **`fallback_instrument_served` warning (REQUIRED):** AV-throttle → Stooq ^SPX served → result carries the
    mechanical warning (token + magnitude cause in tail); AND keyless (AV skipped) → Stooq ^SPX served →
    same warning. The SPY-primary success path carries NO such warning. Assert it survives the `finalize`
    seam (mirror #179's `_finalize`-survival test).

## 7. Decisions — RESOLVED (reviewer lead quick-gate, 2026-06-20 22:24, APPROVE)
- **(1) Cross-instrument SPY↔^SPX failover + no-homogeneity finalize — ACCEPTED.** PLUS the REQUIRED
  `fallback_instrument_served` mechanical never-silent warning when ^SPX is served instead of SPY (see §3).
- **(2) In-memory `cache_ttl` ~6h default on the AV source for v1 — OK;** persistent on-disk cache deferred to v2.
- **(3) Accessor `indices.world(symbol="SPY")` — OK** (mirrors `gold.world()`).
- **(4) `value_unit="USD/share (SPY ETF, S&P 500 proxy)"` — OK.** v1 SPY-only with a clear error for other
  symbols — OK. AV `Note`/`Information`→`SourceUnavailable`, keyless-skip-no-network, key-redaction — all confirmed correct.
- **Process:** TDD red-first → Codex×2 before push. **Re-prioritization (reviewer 22:24):** after #177 code
  lands, **#174 (HOSE sector-index routing BUG) jumps ahead of #178** — bugs before features. Order: #177 → #174 → #178.
