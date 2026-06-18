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
SBV (no machine-readable endpoint — **downgraded to candidate**, not used; VCB `Transfer` is a
close proxy to the SBV central rate).

## Canonical unit (the contract)

**`rate` = VND per 1 unit of the base currency**, i.e. for USD/VND, `rate ≈ 26000` means
"26,000 VND = 1 USD". Both sources are normalized to this single convention so the
unit-homogeneity guard is satisfied trivially:

- **open.er-api** (base=USD): `USD/VND = rates["VND"]`; any `X/VND = rates["VND"] / rates[X]`
  (cross-rate). One fetch covers every pair vs VND.
- **Vietcombank**: `X/VND = Transfer(X)` directly (already VND per 1 X). Parse `"26,111.00"`
  with `float(v.replace(",", ""))`.

`unit` string = `"VND per 1 {base}"` (e.g. `"VND per 1 USD"`). The failover `unit_of` returns
this; a source emitting a different convention is rejected (cannot silently invert).

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
- `unit_of(result)` = `result.unit`; reject on unit mismatch (guards against an inverted feed);
- reject empty / non-positive / out-of-band rate; ≤3 attempts; per-source diagnostics.
- **value sanity:** `rate > 0`; for USD/VND a plausible band (e.g. 15,000–40,000) used by the
  health probe and a live parity test (not a hard runtime reject beyond `> 0`).

## Testing (TDD, synthetic only)

- Commit small **synthetic** fixtures (obviously fake round numbers, e.g. USD/VND = 25,000):
  `tests/fixtures/fx/open_er_api_usd.json`, `tests/fixtures/fx/vietcombank.xml`.
- Unit tests (mock `http_get`): parse + convention for each source; cross-rate derivation
  (EUR/VND from open-er-api); comma parsing + timestamp tz for VCB; failover primary→backup;
  unit guard rejects an inverted/mismatched source; empty/garbage → SourceError.
- Opt-in **live USD/VND cross-source parity** test in `live_tests/`: both sources within a
  tolerance (e.g. ±2%) — accepts the normal commercial-vs-market spread (per Boss's "accept small
  difference" guidance).
- Add an FX probe to `vnfin/_health.py::default_probes` (open-er-api USD/VND, band check).

## Limitations (documented for users)

- **Spot/current only** — no historical FX in v0.2 (no-key sources don't offer it). Historical FX
  is a future BYOK enhancement (paid ExchangeRate-API / fixer / ECB for non-VND).
- open-er-api redistribution is **prohibited**; VCB is "for reference only" — runtime-fetch only,
  no bundled FX datasets (same posture as every other domain; see README data-use note).
- Quote currency is **VND only** in v0.2; arbitrary cross-quotes are out of scope.

## Open question for reviewer

1. Is a single mid `rate` (+ optional bid/ask) the right minimal shape, or do you want
   Buy/Transfer/Sell modeled explicitly? (I lean: mid `rate` from VCB `Transfer` / open-er-api
   direct, with optional `bid`/`ask`, to keep the cross-source contract uniform.)
2. OK to keep FX **out** of `TimeSeriesResult`/`to_dataframe()` for v0.2 (it's point-in-time)?
