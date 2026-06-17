# Design: Swappable Price-Source Adapters + Failover Client

**Date:** 2026-06-18  **Author:** vnfin-oss  **Status:** PROPOSAL — for reviewer discussion
**Depends on:** `docs/research/2026-06-18-vn-historical-price-scraping-sources.md`

## Goal

Scrape VN historical OHLCV (daily priority, intraday best-effort) from several **broker-native** sources behind one normalized interface, so adapters are hot-swappable and a failed call transparently falls back to another source (up to 3 attempts).

## Chosen 5 sources (broker-native, NOT data providers)

Boss directive: prefer the exchange/brokers themselves, not data providers like FireAnt. The HOSE/HNX exchanges expose no free public API, so we use **licensed securities firms** (exchange members) with public, no-auth chart backends. All five speak the **TradingView UDF** protocol → one adapter shape.

| Priority | Source | Host | Daily depth | Intraday | Auth |
|----------|--------|------|-------------|----------|------|
| P1 | SSI iBoard | `iboard-api.ssi.com.vn/statistics/charts/history` | 2006 (FPT) | 1/5/15/30/60m (recent window) | none |
| P2 | VNDirect dchart | `dchart-api.vndirect.com.vn/dchart/history` | 2013 | 1/5/15/30/60m | none |
| P3 | VPS SmartOne | `histdatafeed.vps.com.vn/tradingview/history` | 2010 (VCB) | 1/5/15/30/60m | none |
| Bench | KIS Vietnam | `api.ikis.kisvn.vn/api/v3/chart/history` | full listing | 1/5/15/30/60m | none |
| Bench | Pinetree/DSC | `charts.pinetree.vn/tv/history` | 2010 (FPT) | 1/5/15/30/60/120m | none |

Excluded by directive: FireAnt, CafeF, Simplize, Wichart, 24hMoney, Yahoo, Vietstock (data providers/portals). DNSE/Entrade & Vietcap are broker-native alternates on the bench. All endpoints verified + adversarially reproduced 2026-06-18.

## Architecture: ports & adapters (hexagonal)

```
                ┌─────────────────────────────────────────┐
   caller  ──►  │ FailoverPriceClient(sources, max=3)      │
                │  try P1 → validate → P2 → … (≤3)          │
                └───────────────┬─────────────────────────┘
                                │ PriceSource port (ABC/Protocol)
        ┌───────────┬───────────┼───────────┬───────────┐
     SSISource  VNDirectSrc  VPSSource   KISSource   PinetreeSrc   ← adapters (1 file each)
        └───────────┴───────────┴───────────┴───────────┘
                         shared _UDFSource base
```

### Standard contract (the port)

> ⚠️ **Superseded draft.** The block below is the original sketch. The authoritative
> contract is the **RESOLVED** section near the end of this doc (`AdjustmentPolicy` enum
> + full `PriceHistory` metadata + `UnsupportedInterval` + coverage warnings). Implement
> against that, not the `adjusted: bool` shown here.

**Normalized inputs:**
- `symbol: str` — e.g. `"FPT"` (HOSE/HNX/UPCOM)
- `interval: Interval` — enum `D1 | W1 | MN1 | M1 | M5 | M15 | M30 | H1`
- `start, end: date | datetime`
- `adjusted: bool = True`

**Normalized output:** typed `PriceHistory`
```python
@dataclass(frozen=True)
class PriceBar:
    time: datetime      # tz-aware, normalized to Asia/Ho_Chi_Minh
    open: float; high: float; low: float; close: float   # VND (scaling normalized)
    volume: int

@dataclass(frozen=True)
class PriceHistory:
    symbol: str; interval: Interval; adjusted: bool
    source: str                 # which adapter served it
    bars: list[PriceBar]
    def to_dataframe(self) -> "pandas.DataFrame": ...   # analyst convenience
```

**Port:**
```python
class PriceSource(Protocol):
    name: str
    def get_history(self, symbol, interval, start, end, *, adjusted=True) -> PriceHistory: ...
    def health(self) -> bool: ...     # cheap liveness probe
```

### Adapters (one swappable class/file per source)

`sources/ssi.py`, `vndirect.py`, `vps.py`, `kis.py`, `pinetree.py`. Each owns: base URL, path, `RESOLUTION_MAP`, response-envelope unwrap, and normalization (tz, price scale, volume int, adjustment label). Since 4–5 are UDF, propose an internal `sources/_udf.py:_UDFSource` base that implements the shared GET + parallel-array (`t/o/h/l/c/v/s`) parse; each adapter subclasses it and overrides only what differs (e.g. SSI wraps payload in `{data:{…}}`, VPS/VNDirect return bare arrays). Each remains a separate, independently swappable class.

### Failover orchestrator

`FailoverPriceClient(sources: list[PriceSource], max_attempts=3)`:
1. Iterate sources in priority order, up to `max_attempts` (default **3**).
2. Accept a result only if it **passes validation**: transport ok, status ok, non-empty, OHLC invariants (`low ≤ open,close ≤ high`, `volume ≥ 0`), requested range substantially covered, last bar not stale.
3. On exception / empty / validation fail → log (source + reason) and try next.
4. Return `PriceHistory` tagged with the serving `source`.
- Per source: IPv4 + browser UA, ~25s timeout, polite rate limiting, optional TTL cache.

## Open decisions for the reviewer

1. **Return type:** typed `PriceHistory` core + `.to_dataframe()` helper (my pick) vs DataFrame-first?
2. **Intraday scope:** daily is the only reliable common denominator; intraday windows are shallow & inconsistent (SSI ~4 wks 1-min; VNDirect hourly ~4.5y). Ship daily uniformly + intraday "best-effort, per-source-limited"? 
3. **Adjusted vs raw:** all 5 are split/div-**adjusted**. Raw needs a *data provider* (Simplize/CafeF) which the directive excludes. Ship adjusted-only now and keep `adjusted` flag for later, or carve an exception for one raw source for corporate-action validation?
4. **Failover policy:** sequential (simple) vs hedged race-of-2 (faster, more load)? Add a cross-source close-price reconciliation check (catch bad data / adjustment drift)?
5. **DRY vs strict independence:** shared `_UDFSource` base (my pick — DRY, still per-file swappable) vs fully independent adapters?
6. **Symbol universe:** clean-room source for the valid-ticker list + exchange mapping?
7. **Compliance:** runtime fetch only, no bundled data, source attribution, per-broker ToS review, rate-limit etiquette. Agreed?

## Proposed package layout
```
vnfin/
  models.py            # Interval, PriceBar, PriceHistory
  sources/
    _udf.py            # _UDFSource base
    ssi.py vndirect.py vps.py kis.py pinetree.py
  client.py            # FailoverPriceClient
```

## RESOLVED — agreed contract (reviewer APPROVE_WITH_NOTES, 2026-06-18)

Reviewer: `vnfin-oss-reviewer/reviews/review-202606180012-price-source-adapters.md`. Blocker B1 (FireAnt token) redacted. Final decisions:

1. **Return type:** typed `PriceHistory` core + `.to_dataframe()`. Add fields: `currency="VND"`, `exchange`, `adjustment_policy`, `provider_symbol`, `fetched_at_utc`, `warnings`, plus failover `attempts` diagnostics.
2. **Intraday:** `D1` guaranteed for all 5; intraday is capability-gated best-effort. Unsupported interval → raise `UnsupportedInterval` (never silently fall back to daily). Document per-source intraday retention.
3. **Adjustment:** enum `AdjustmentPolicy = PROVIDER_ADJUSTED | RAW | MIXED | UNKNOWN` (not a bool). Default chain returns provider-adjusted only; `MIXED`/`UNKNOWN` excluded from default failover. No raw via data providers (Simplize/CafeF) in the broker-native default.
4. **Failover:** sequential, all 5 configured, max 3 attempts. Validate transport/status/non-empty/array-lengths/OHLC/volume/range. "Last bar stale" is a **soft warning** (VN trading-calendar aware), never a hard fail. Cross-source reconciliation = separate diagnostic mode.
5. **DRY:** shared `_UDFSource` (HTTP + envelope parse + array alignment + tz + common validation); each adapter owns URL, resolution map, price scale, envelope unwrap, capabilities, headers, adjustment policy — and its **own tests + synthetic fixtures**.
6. **Symbol universe:** lazy for MVP (uppercase-normalize, call provider, surface `UnknownSymbol`/empty). No bundled ticker universe; official exchange lists only after a separate license-clear vetting note.
7. **Compliance:** runtime fetch only; no bundled broker data or real-price cassettes; source attribution in every `PriceHistory`; low concurrency + retry/backoff + local cache; per-source ToS/robots/provenance note before coding each adapter; FireAnt/Yahoo/Wichart and any bearer/encrypted source excluded from the default chain.

**Acceptance criteria before merge to main:** RED tests first (models, each adapter, failover); synthetic fixtures cover normal / empty / malformed / unsupported-interval / envelope-variant / price-scaling / timezone / OHLC-failure; failover tests prove stop-after-first-valid, ≤3 attempts, diagnostics recorded, no unnecessary later calls; integration tests opt-in & CI-skipped; per-source capability + compliance docs; secret scan clean.
