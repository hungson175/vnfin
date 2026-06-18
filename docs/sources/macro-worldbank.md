# Source provenance — World Bank Indicators API (v2)

**Adapter:** `vnfin.macro.WorldBankMacroSource`
**Domain:** Macro — cross-country annual indicators (GDP, CPI/inflation, unemployment, FX, trade, FDI, M2, ...)
**Verified:** 2026-06-18 (live curl + live Python probe from this host)
**Clean-room:** endpoints learned only from the provider's own server + `docs/research/2026-06-18-macro-global-cross-country.md` and `docs/research/2026-06-18-macro-vietnam.md`. No vnstock/derivative source consulted.

## Endpoint

```
GET https://api.worldbank.org/v2/country/{ISO3}/indicator/{CODE}?format=json&per_page={N}&date={Y1}:{Y2}
```

- `{ISO3}` — country code, e.g. `USA`, `CHN`, `JPN`, `DEU`, `VNM` (multi-country via `;` separator, not used by this adapter which is single-country).
- `{CODE}` — World Development Indicator code, e.g. `FP.CPI.TOTL.ZG` (inflation %), `NY.GDP.MKTP.CD` (GDP current US$), `SL.UEM.TOTL.ZS` (unemployment %), `PA.NUS.FCRF` (VND/USD rate).
- `date` param omitted when no year range requested.

## Auth / limits / terms

- **Auth:** NONE (no key, no token). Public open data.
- **Rate:** no documented key/limit; be polite with paging. Observed transient `ReadTimeout` under rapid repeated calls from this host — adapter wraps that as `SourceUnavailable` (failover-safe).
- **License/terms:** World Development Indicators are CC-BY 4.0 (World Bank Open Data). Attribution required; redistribution allowed. The research note flags no published redistribution grant on the raw API endpoint itself — treat as runtime-fetch, no bundled data.
- **Redistribution:** runtime fetch only; do not bundle/commit provider rows. (Tests use synthetic fixtures.)

## Response shapes (verified)

| Case | Body | Adapter mapping |
|------|------|-----------------|
| Success | `[meta, [obs, ...]]` | parsed to `IndicatorSeries` |
| Missing year inside series | obs with `"value": null` | point skipped |
| No data (valid params) | `[{...,"total":0}, null]` | `EmptyData` |
| Empty page | `[meta, []]` | `EmptyData` |
| Invalid country/indicator | `[{"message":[{"id","key","value"}]}]` | `InvalidData` |
| Non-JSON / wrong shape / NaN / garbage scalar | — | `InvalidData` |
| Transport/network error | — | `SourceUnavailable` |

Each observation object: `indicator{id,value}`, `country{id,value}`, `countryiso3code`, `date` (year string), `value` (float | null), `unit`. Response may carry a UTF-8 BOM — adapter decodes with `utf-8-sig` / strips BOM.

## Result model

`IndicatorSeries(country, indicator_code, indicator_name, points: tuple[(date, float), ...], source, unit, currency="USD", country_name, fetched_at_utc, warnings)` — frozen, ascending-by-date, `len()`/iter/`latest()`/`to_dataframe()`.

## Related macro sources

- `docs/sources/macro-imf.md` — IMF DataMapper (no-key backup, WEO + projections).
- `docs/sources/macro-dbnomics.md` — DBnomics IMF/IFS (no-key backup, CPI index).
- `docs/sources/macro-fred.md` — FRED official JSON API, optional **BYOK**
  (`FRED_API_KEY`). No key → the source is **not capable** and is skipped without a
  network call (never `NotImplementedError`). `fredgraph.csv` scraping is disallowed.

## Default no-key chain + unit safety

`vnfin.macro.client()` chains World Bank → IMF DataMapper → DBnomics, serving the
SAME canonical `MacroIndicator` across providers. Before the generic failover engine
is built, sources are **pre-filtered by unit** so only sources emitting the exact
canonical unit for the indicator survive (`vnfin/macro/indicators.py:eligible_sources`).
This is why GDP resolves to World Bank (`current US$`), CPI-index to DBnomics, and the
percent indicators to all three — without ever tripping `UnitMismatchError`. See
`docs/design/macro-no-key-byok.md` for the full semantic contract.
