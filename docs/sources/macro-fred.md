# Source provenance — FRED (St. Louis Fed) — optional BYOK

**Adapter:** `vnfin.macro.FREDMacroSource`
**Domain:** Macro — arbitrary FRED series (US + redistributed international series).
**Role in chain:** **optional bring-your-own-key (BYOK)**. **Excluded from the
default no-key chain** (World Bank → IMF DataMapper → DBnomics). FRED is accessed
directly via `get_series(series_id)`; it does not carry a canonical-indicator map,
so it is not auto-chained into the canonical GDP/CPI/percent failover.
**Verified:** 2026-06-18 (official API docs; no live key on this host).
**Clean-room:** endpoint + response shape taken only from FRED's own official API
docs (`api.stlouisfed.org/fred/series/observations`) and
`docs/research/2026-06-18-macro-no-key-byok.md`. No vnstock/derivative source.

## Endpoint — official JSON API ONLY

```
GET https://api.stlouisfed.org/fred/series/observations?series_id={ID}&api_key={KEY}&file_type=json
```

- **`fredgraph.csv` is DISALLOWED** (C3). FRED's Terms of Use prohibit automated
  scraping outside the API (June-2024 anti-caching/anti-AI clauses). The adapter
  only ever hits `/fred/series/observations`; a regression test asserts it never
  builds a `fredgraph` URL. The older `docs/research/2026-06-18-macro-vietnam.md`
  `fredgraph.csv` recommendation is marked SUPERSEDED/DISALLOWED.

## Auth / key behavior (BYOK) — C4

- **Auth:** required free 32-char key. The library **NEVER bundles, ships, or
  commits a key.** The *user* supplies it via the `api_key` constructor argument or
  the `FRED_API_KEY` environment variable (constructor wins over env).
- **No key → not capable, no network call:** `has_key` is `False`,
  `supports(indicator)` returns `False` (so a failover chain skips it **before** any
  network call), and a direct `get_series()` raises a catchable `SourceUnavailable`
  before any request — never `NotImplementedError`, never a hard crash, never a
  leaked raw exception.
- No shared quota: every user uses their own free key.

## Response shape

```json
{"units": "...", "observations": [{"date": "YYYY-MM-DD", "value": "<str>"}, ...]}
```

The string `"."` denotes a missing value (skipped).

| Case | Adapter mapping |
|------|-----------------|
| Success | `IndicatorSeries` |
| `"."` value | point skipped |
| No key configured | `SourceUnavailable` (skippable, no network) |
| Transport/network error | `SourceUnavailable` |
| Non-JSON / missing `observations` | `InvalidData` |
| Malformed scalar / bad date | `InvalidData` |
| Empty / all-missing | `EmptyData` |

## Units / currency

- `unit` comes from the response `units` string (arbitrary: %, index, USD, persons…).
- `currency=None` — an arbitrary FRED series has no known fixed money currency, so
  the adapter never stamps a guessed `USD` (B7).

## Rate limits / attribution

- FRED documents per-key rate limits; be polite. Emit FRED attribution downstream.
- License: FRED is free; underlying series may be third-party (e.g. World Bank
  CC-BY 4.0). Runtime fetch only; no bundled data.

## Result model

`IndicatorSeries(country="", indicator_code=series_id, indicator_name=series_id, points, source="fred", unit, value_unit, currency=None, fetched_at_utc)`.
