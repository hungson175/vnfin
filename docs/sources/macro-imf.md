# Source provenance — IMF DataMapper API (WEO, v1)

**Adapter:** `vnfin.macro.IMFDataMapperSource`
**Domain:** Macro — cross-country annual indicators (GDP level, real GDP growth, CPI inflation, unemployment) incl. WEO projections.
**Role in chain:** no-key **backup** (default chain position 2: World Bank → **IMF DataMapper** → DBnomics).
**Verified:** 2026-06-18 (live curl + live Python probe from this host).
**Clean-room:** endpoint + response shape learned only from the provider's own server (`www.imf.org/external/datamapper/api/v1`) and `docs/research/2026-06-18-macro-no-key-byok.md` / `docs/research/2026-06-18-macro-vietnam.md`. No vnstock/derivative source consulted.

## Endpoint

```
GET https://www.imf.org/external/datamapper/api/v1/{INDICATOR}/{ISO3}
```

- `{INDICATOR}` — IMF WEO code. Canonical mapping (this adapter):
  - `GDP_GROWTH` → `NGDP_RPCH` (real GDP growth, **%**)
  - `INFLATION` → `PCPIPCH` (CPI inflation avg, **%**)
  - `UNEMPLOYMENT` → `LUR` (unemployment, **%**)
  - `GDP` → `NGDPD` (GDP, **USD bn**) — distinct unit from the canonical
    `current US$`, so the unit pre-filter keeps IMF GDP out of the WB-USD chain.
- `{ISO3}` — ISO-3 country code (e.g. `USA`, `VNM`).

## Singapore country qualification

The DataMapper routes for `SGP/GDP_GROWTH` (`NGDP_RPCH`), `SGP/INFLATION`
(`PCPIPCH`), and `SGP/UNEMPLOYMENT` (`LUR`) are **country-ineligible** in this
adapter. `IMFDataMapperSource.supports_country()` reports those pairs as false,
and the macro client removes them before cache, transport, and failover attempt
accounting. Consequently, a skipped IMF route is absent from attempts; it is a
capability preflight outcome, not provider `NO_DATA` or a provider failure.

World Bank remains primary. If it fails for one of those SGP indicators, a
country-aware custom source may still be tried in caller order. A custom source
without the optional hook (a hookless source) remains eligible under the normal
unit and returned-identity guards. The same mapped routes for a valid non-SGP
country retain their existing behavior.

Direct `get_indicator()` and `indicator_identity()` calls enforce the same gate.
For a gated pair they raise `InvalidData` before cache or transport. Identity
lookup continues to check the indicator mapping first, then validates the
country; eligible identity tuples are unchanged.

This country gate does not fill adjacent data gaps. `SGP/CPI_YOY` and
`SGP/POLICY_RATE` remain missing in the built-in chain: there is no SingStat
source and no proxy substitution from SORA, an interbank rate, a facility,
lending or deposit rates, a bond yield, or FX. A caller may provide a truthful
custom source under the normal capability and result contracts.

## Auth / limits / terms

- **Auth:** NONE (no key, no token).
- **Rate:** no documented key/limit; on-demand fetch only. Observed HTTP 403 from
  some hosts/IPs (anti-bot) — adapter wraps that as `SourceUnavailable` (failover-safe).
- **License/terms:** IMF data is all-rights-reserved; on-demand API fetch is fine,
  **do not bundle/redistribute IMF rows as files**. Emit IMF attribution downstream.
- **Redistribution:** runtime fetch only; tests use synthetic fixtures.

## Response shape (verified)

```json
{"values": {"<INDICATOR>": {"<ISO3>": {"<year-str>": <float|null>, ...}}},
 "api": {"version": "1", "output-method": "json"}}
```

| Case | Adapter mapping |
|------|-----------------|
| Success | `IndicatorSeries` (annual, Jan-1 points) |
| Year value `null` | point skipped |
| Country absent / indicator key absent / all-null | `EmptyData` |
| Non-JSON / wrong shape | `InvalidData` |
| Unsupported indicator (e.g. CPI index) | `InvalidData` |
| Malformed scalar / bad year | `InvalidData` |
| Transport/network error / HTTP 403 | `SourceUnavailable` |

## Projections (actual vs forecast) — B8

IMF WEO mixes historical actuals with multi-year **forecasts** and the basic
DataMapper response carries no per-point actual/forecast flag. The adapter applies
a conservative deterministic rule: **any year ≥ the current calendar year is a
projection.** It stamps `projection_from_year` on the result and adds a warning, so:

- `IndicatorSeries.latest()` returns the most recent **actual** (never a forecast),
- `latest_including_projections()` / `actual_points` expose forecasts explicitly,
- `to_dataframe()` carries a per-row `is_projection` column.

## Units / currency

- Percent indicators → `unit="%"`, `currency=None`.
- `GDP` (NGDPD) → `unit="USD bn"`, `currency="USD"` (money-denominated).

## Result model

`IndicatorSeries(country, indicator_code, indicator_name, points, source="imf_datamapper", unit, value_unit, currency, frequency=ANNUAL, projection_from_year, fetched_at_utc, warnings)`.
