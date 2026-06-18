# Source provenance — DBnomics (IMF / IFS via DBnomics, v22)

**Adapter:** `vnfin.macro.DBnomicsSource`
**Domain:** Macro — cross-country GDP (national currency, annual) and CPI (index level, monthly) from the IMF International Financial Statistics (IFS) dataset, served through DBnomics.
**Role in chain:** no-key **broad backup** (default chain position 3: World Bank → IMF DataMapper → **DBnomics**). It is the **only** default source for the canonical CPI *index* indicator.
**Verified:** 2026-06-18 (live curl + live Python probe from this host).
**Clean-room:** endpoint + response shape learned only from DBnomics' own public API (`api.db.nomics.world/v22`) and `docs/research/2026-06-18-macro-no-key-byok.md`. No vnstock/derivative source consulted.

## Endpoint

```
GET https://api.db.nomics.world/v22/series/IMF/IFS/{FREQ}.{CC}.{IFS_CODE}?observations=1
```

- `{FREQ}` — IFS frequency code: `A` (annual) or `M` (monthly).
- `{CC}` — IMF 2-letter country code (adapter maps ISO-3 → ISO-2 for the documented
  coverage: USA→US, CHN→CN, JPN→JP, DEU→DE, VNM→VN; unknown ISO-3 → `InvalidData`).
- `{IFS_CODE}` — IFS concept. Canonical mapping (this adapter):
  - `GDP` → `A.{CC}.NGDP_XDC` (GDP, **national currency**, annual) — distinct from
    the canonical `current US$`, so the unit pre-filter keeps DBnomics GDP out of
    the WB-USD chain.
  - `CPI` → `M.{CC}.PCPI_IX` (CPI **index** level, **monthly**) — this is the
    canonical CPI-index source.

## Auth / limits / terms

- **Auth:** NONE (no key, no token).
- **Rate:** no documented key/limit; on-demand fetch only. Transport errors wrap as
  `SourceUnavailable` (failover-safe).
- **License/terms:** DBnomics aggregation is **ODbL**; the underlying IFS data is
  IMF (all-rights-reserved). On-demand API fetch only; **do not bundle/redistribute**
  the rows as files. Emit DBnomics + IMF attribution downstream.
- **Redistribution:** runtime fetch only; tests use synthetic fixtures.

## Response shape (verified)

```json
{"series": {"docs": [{"period_start_day": ["<ISO date>", ...],
                      "period": ["<label>", ...],
                      "value": [<float|null|"NA">, ...],
                      "series_code", "dataset_code", ...}]}}
```

`period_start_day` and `value` are **parallel arrays** (zipped in order). Missing
observations are `null` or the string `"NA"`.

| Case | Adapter mapping |
|------|-----------------|
| Success | `IndicatorSeries` (frequency per indicator) |
| `null` / `"NA"` value | point skipped |
| No docs / all-null | `EmptyData` |
| Non-JSON / wrong shape / array length mismatch | `InvalidData` |
| Unsupported indicator (e.g. GDP_GROWTH) | `InvalidData` |
| Unknown ISO-3 (no IFS code) | `InvalidData` |
| Malformed scalar / bad period | `InvalidData` |
| Transport/network error | `SourceUnavailable` |

## Units / currency / frequency

- `GDP` → `unit="national currency"`, `currency=None` (currency varies by country —
  never a fixed USD), `frequency=annual`.
- `CPI` → `unit="index"`, `currency=None`, `frequency=monthly`.

## Result model

`IndicatorSeries(country, indicator_code=series_id, indicator_name, points, source="dbnomics", unit, value_unit, currency=None, frequency, fetched_at_utc)`.
