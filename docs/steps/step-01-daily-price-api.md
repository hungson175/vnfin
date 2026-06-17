# Step 1 — Daily price API (done)

**Date:** 2026-06-18  **Status:** implemented, unit-green, live-smoke-passed; awaiting reviewer post-impl review.

## What shipped

A clean-room, ports-and-adapters daily-price API with multi-source failover.

- `vnfin/models.py` — `Interval`, `AdjustmentPolicy`, `PriceBar`, `PriceHistory` (+ `.to_dataframe()`), `SourceAttempt`.
- `vnfin/sources/base.py` — `PriceSource` port + `VN_TZ`.
- `vnfin/sources/udf.py` — `UDFSource` base: TradingView-UDF transport, envelope/array parsing, VND scaling, Vietnam-tz conversion, OHLC/structural validation.
- `vnfin/sources/{ssi,vndirect,vps,kis,pinetree}.py` — 5 broker-native adapters.
- `vnfin/sources/registry.py` — registry + default chain.
- `vnfin/client.py` — `FailoverPriceClient` (sequential, ≤3 attempts, per-source diagnostics).
- `vnfin/__init__.py` — `vnfin.default_client()` convenience.

## The 5 adapters (all verified live, daily guaranteed)

| Source | Class | Envelope | Price scale | Adjustment | Intervals | In default chain |
|--------|-------|----------|-------------|------------|-----------|------------------|
| SSI iBoard | `SSIiBoardSource` | yes (`data`) | ×1000 | provider_adjusted | D1,H1,M30,M15,M5,M1 | ✅ (1st) |
| VNDirect | `VNDirectSource` | no | ×1000 | provider_adjusted | D1,H1,M30,M15,M5,M1 | ✅ (2nd) |
| VPS | `VPSSource` | no | ×1000 | provider_adjusted | D1,H1,M30,M15,M5,M1 | ✅ (3rd) |
| Pinetree/DSC | `PinetreeSource` | no | ×1 (raw VND) | provider_adjusted | D1,H1,M30,M15,M5,M1 | ✅ (4th) |
| KIS Vietnam | `KISVietnamSource` | no | ×1 (raw VND) | **mixed** | D1,H1,M30,M15,M5,M1 | ❌ excluded (MIXED) |

All output prices normalized to **VND**; timestamps tz-aware **Asia/Ho_Chi_Minh**. KIS is registered (`all_sources()`) but excluded from the default chain because its series adjustment is `MIXED` — it must not be blended with adjusted series (reviewer B3). Per-source provenance/compliance: `docs/sources/<name>.md`.

## Usage

```python
from datetime import date, timedelta
import vnfin

client = vnfin.default_client()                 # SSI -> VNDirect -> VPS -> Pinetree, max 3 attempts
h = client.get_daily("FPT", date(2026, 6, 1), date(2026, 6, 17))
print(h.source, len(h), h.adjustment_policy.value)   # e.g. "ssi 11 provider_adjusted"
df = h.to_dataframe()                            # pandas, indexed by time, metadata in df.attrs
```

## Tests

- **79 unit/contract tests, 98% coverage** (`./.venv/bin/python -m pytest --cov=vnfin`).
- Synthetic UDF fixtures only — **no real broker rows used as test fixtures or bundled datasets** (docs may carry short illustrative provenance snippets).
- Live integration tests are opt-in and CI-skipped: `VNFIN_LIVE=1 ./.venv/bin/python -m pytest -m integration`.
- Live smoke (2026-06-18): `default_client().get_daily("FPT", …)` → served by `ssi`, 11 bars, last close 72,300 VND, tz +07.

## Compliance

Runtime fetch only; no bundled data or real-price cassettes; source attribution in every `PriceHistory`; FireAnt/Yahoo/Wichart and any bearer/encrypted sources excluded from the default chain. Data is for personal/internal research; raw redistribution needs a provider/exchange license.

## Deferred (tracked for later steps)

- VN trading-calendar-aware staleness check (currently a soft no-op).
- Intraday retention differs per source (SSI ~weeks, VPS recent-only, VNDirect hourly ~4.5y) — documented per source, not yet uniformly enforced.
- Symbol universe is lazy (uppercase + provider response); official exchange list pending a license-clear vetting note.
- Local cache + retry/backoff.

## Next

Step 2 — scrape **fundamental reports** (financial statements / ratios) for long-term analysis, same TDD + reviewer rhythm. Reviewer architecture review due after Step 2 (every 2–3 steps).
