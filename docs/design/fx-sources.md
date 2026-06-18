# FX domain — source vetting & design (v0.2 MVP)

**Status:** design for reviewer gate 3 (must be APPROVED before any FX adapter code).
**Scope:** narrow **daily / current** FX (market reference rates), not historical, not macro
FX. Macro annual FX-style series remain in `vnfin.macro` (World Bank). Source research:
[`docs/research/2026-06-18-fx-rates-sources.md`](../research/2026-06-18-fx-rates-sources.md).
**Clean-room:** VNStock/vnstock fully excluded; both sources are primary/official and were
live-verified 2026-06-18.

## Why FX, why now

FX is the cleanest separable new domain: two **no-key** sources exist with the **same quoting
convention**, it is immediately useful (convert world gold/crypto → VND; daily USD/VND for
analysis), and it has no semantic dependency on a security master (unlike dividends).

## Sources (vetted)

| Role | Source | Endpoint | Auth | Convention | Notes |
|------|--------|----------|------|------------|-------|
| **Primary** | ExchangeRate-API open | `GET https://open.er-api.com/v6/latest/USD` (JSON) | none | `rates[X]` = X per 1 USD | 166 currencies; daily refresh; spot only; 429 if >1/day |
| **Failover** | Vietcombank XML | `GET https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10` | none | `Transfer` = **VND per 1 foreign unit** | official VN bank; intraday; 20 ccy; "1 request / 5 min" |

Rejected (documented in research): frankfurter/ECB (no VND), exchangerate.host (now needs key),
SBV (no machine-readable endpoint — **downgraded to candidate**, not used).

> **VCB `Transfer` is a commercial-bank telegraphic-transfer/reference quote**, used here as a
> pragmatic VND mid proxy. It is **not** the SBV central rate and must not be labelled as such in
> docs or field names (it tracks the SBV central rate only loosely, within a band).

## Canonical unit (the contract)

**`rate` = VND per 1 unit of the base currency**, i.e. for USD/VND, `rate ≈ 26000` means
"26,000 VND = 1 USD". Both sources are normalized to this single convention so the
unit-homogeneity guard is satisfied trivially:

- **open.er-api** (base=USD): `USD/VND = rates["VND"]`; any `X/VND = rates["VND"] / rates[X]`
  (cross-rate). One fetch covers every pair vs VND.
- **Vietcombank**: `X/VND = Transfer(X)` directly (already VND per 1 X). Parse `"26,111.00"`
  with `float(v.replace(",", ""))`.

`unit` string = `"VND per 1 {base}"` (e.g. `"VND per 1 USD"`). The unit safety is **two-layer**
(matching how `vnfin.failover.FailoverClient` actually works — it calls `unit_of(source)` and
enforces source-unit homogeneity at *construction*, and validates results via `reject(result)`):

1. **Source-level convention guard** — every FX source declares the same unit family via
   `unit_of(source)` (e.g. `"VND-per-foreign-unit"`); the failover client refuses to chain
   sources of different families at construction.
2. **Result/request guard** — a **request-aware** check (implemented in `_operation`, which has
   the requested base/quote in scope — `reject(result)` alone only sees the result) validates the
   returned `base`/`quote` *match the request*, `unit == f"VND per 1 {requested_base}"`, and
   `rate > 0`; a source returning the wrong currency or a silently inverted quote (USD-per-VND)
   fails this and the client falls over / fails loudly.

## Public model

```python
@dataclass(frozen=True)
class FXRate:
    base: str            # ISO 4217, e.g. "USD"
    quote: str           # "VND" (the only quote in v0.2)
    rate: float          # VND per 1 base
    unit: str            # "VND per 1 USD"
    as_of_utc: datetime  # provider timestamp normalized to UTC
    source: str          # "open_er_api" | "vietcombank"
    bid: float | None = None   # VCB Buy (optional; None for open-er-api)
    ask: float | None = None   # VCB Sell (optional)
```

Single, flat result (no time series). `to_dataframe()` is **out of scope** for v0.2 (FX is
point-in-time, not a `TimeSeriesResult`).

## Module layout (mirrors crypto/gold)

```text
vnfin/fx/__init__.py     # facade: client(), source(), get_rate(base, quote="VND")
vnfin/fx/models.py       # FXRate
vnfin/fx/base.py         # FXSource ABC: get_rate(base, quote="VND") -> FXRate
                         #               get_rates(quote="VND") -> tuple[FXRate, ...]
vnfin/fx/open_er_api.py  # OpenErApiFXSource (primary)
vnfin/fx/vietcombank.py  # VietcombankFXSource (failover)
vnfin/fx/client.py       # FailoverFXClient over the generic FailoverClient + unit guard
```

Facade verbs (consistent with the standard): `client()` = failover (open-er-api → vietcombank),
`source()` = primary only, `get_rate(...)` = one-shot convenience.

## Failover semantics

Reuse the generic `vnfin.failover.FailoverClient`:
- operation: `get_rate(base, quote)`; capability: source supports the base currency;
- `unit_of(source)` declares the source's convention family (construction-time homogeneity guard);
- `reject(result)` validates `base`/`quote`/`unit`/`rate > 0` (the two-layer guard above);
- ≤3 attempts; per-source diagnostics.
- **value sanity:** `rate > 0`; for USD/VND a plausible band (e.g. 15,000–40,000) used by the
  live parity test (not a hard runtime reject beyond `> 0`).

## Testing (TDD, synthetic only)

- Commit small **synthetic** fixtures (obviously fake round numbers, e.g. USD/VND = 25,000):
  `tests/fixtures/fx/open_er_api_usd.json`, `tests/fixtures/fx/vietcombank.xml`.
- Unit tests (mock `http_get`): parse + convention for each source; cross-rate derivation
  (EUR/VND from open-er-api); comma parsing + timestamp tz for VCB; failover primary→backup;
  the two-layer unit guard rejects an inverted/mismatched source.
- **Input/validation tests**: reject an **unsupported quote** (≠ VND), a **malformed/unknown ISO
  code**, an **unsupported base** (not in the source's rate set), a **non-positive rate**, and a
  returned `base`/`quote`/`unit` mismatch → all surface as `SourceError`/`ValueError`, not bad data.
- Opt-in **live USD/VND cross-source parity** test in `live_tests/`: both sources within a
  tolerance (e.g. ±2%) — accepts the normal commercial-vs-market spread (per Boss's "accept small
  difference" guidance).
- **Health probe (rate-limit aware):** open-er-api 429s if hit >1/day and VCB asks for ≤1
  request/5 min, so the FX probe is **NOT** added to the default scheduled `default_probes` hammer.
  It lives in an **opt-in / cached** monitor path (e.g. a `--fx` flag on the healthcheck CLI, or a
  cached probe respecting a daily TTL), so routine monitoring never trips provider limits.

## Limitations (documented for users)

- **Spot/current only** — no historical FX in v0.2 (no-key sources don't offer it). Historical FX
  is a future BYOK enhancement (paid ExchangeRate-API / fixer / ECB for non-VND).
- Quote currency is **VND only** in v0.2; arbitrary cross-quotes are out of scope.

## Legal / provenance (must appear in the adapter docs)

`docs/sources/fx-open-er-api.md` and `docs/sources/fx-vietcombank.md` must each record terms +
provenance explicitly:

- **open.er-api.com** — [Terms of Use](https://www.exchangerate-api.com/terms): **redistribution
  of raw data is prohibited**; commercial use allowed; caching permitted; attribution requested
  (`Rates By Exchange Rate API`). Runtime-fetch only; **no bundled FX datasets**.
- **Vietcombank XML** — feed is marked **"for reference only"** with **no explicit open-data
  license**; conservative posture: runtime-fetch only, no republishing/bundling. Respect the
  self-declared "1 request / 5 min" cadence.
- This matches the library-wide data-use posture (README data-use note): `vnfin` is an API
  *client*; redistributing raw provider data may require the provider's licence.

## Open question for reviewer

1. Is a single mid `rate` (+ optional bid/ask) the right minimal shape, or do you want
   Buy/Transfer/Sell modeled explicitly? (I lean: mid `rate` from VCB `Transfer` / open-er-api
   direct, with optional `bid`/`ask`, to keep the cross-source contract uniform.)
2. OK to keep FX **out** of `TimeSeriesResult`/`to_dataframe()` for v0.2 (it's point-in-time)?
