# FX source — ExchangeRate-API open endpoint (`open_er_api`)

**Adapter:** `vnfin.fx.OpenErApiFXSource` · **Role:** FX primary · **Auth:** none (no key).

## Endpoint

```
GET https://open.er-api.com/v6/latest/USD
```

JSON. `base_code = "USD"`; `rates[X]` = **X per 1 USD**. The adapter anchors on `rates["VND"]`
and derives `X/VND = rates["VND"] / rates[X]` (USD/VND = `rates["VND"]`). Timestamp from
`time_last_update_unix` (epoch → UTC), falling back to now if absent.

## Units / convention

Canonical vnfin unit: **VND per 1 unit of the base** (`unit = "VND per 1 {base}"`). USD/VND ≈
26,000 means 26,000 VND = 1 USD. See [units.md](../units.md).

## Behaviour / limits

- Updates ~once/24h; **HTTP 429 if requested more than ~once/day** (window resets ~20 min).
  → the library caches the daily rate; the health probe is opt-in (`scripts/healthcheck.py --fx`),
  never in the default scheduled sweep.
- Spot/current only — **no historical** series on the open (no-key) tier.
- 166 currencies; CDN-backed, globally reachable (live-verified 2026-06-18).

## Terms / provenance (IMPORTANT)

- [Terms of Use](https://www.exchangerate-api.com/terms): **redistribution of raw data is
  prohibited**; commercial use allowed; **caching permitted**.
- Attribution requested: *"Rates By Exchange Rate API"* (`https://www.exchangerate-api.com`).
- vnfin is a runtime **client**: it fetches on demand and **does not bundle or republish** FX
  datasets. Downstream redistribution of fetched rates may require the provider's licence.
- Research provenance: [`docs/research/2026-06-18-fx-rates-sources.md`](../research/2026-06-18-fx-rates-sources.md).
