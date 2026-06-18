# Design: no-key-first macro + bring-your-own-key (BYOK)

**Date:** 2026-06-18  **Status:** IMPLEMENTED (macro blockers B6/B7/B8 + design items C1–C4, C6 closed).
**Evidence:** `docs/research/2026-06-18-macro-no-key-byok.md`.
**Provenance notes:** `docs/sources/macro-worldbank.md`, `docs/sources/macro-imf.md`, `docs/sources/macro-dbnomics.md`, `docs/sources/macro-fred.md`.

## Principle (applies library-wide)

1. **No-key-first** — every domain defaults to no-auth sources so `pip install` + import just works; no shared-key rate-limiting, ever.
2. **BYOK optional** — keyed sources are opt-in; the *user* supplies their own key via env var / constructor param. The library **never bundles, ships, or commits a key**. Missing key ⇒ that source is skipped, never an error.
3. The generic `FailoverClient` (with the unit-homogeneity guard) chains *no-key primary → optional user-key backup*, so a missing key is invisible to default users.

## Macro module plan (`vnfin/macro/`)

Default no-key chain, per indicator (failover only combines sources that emit the **same indicator unit** — guard enforced):

- **Cross-country incl. Vietnam (annual):** `WorldBankMacroSource` (have it) → `IMFDataMapperSource` (new) → `DBnomicsSource` (new, broad).
- **US high-frequency / rates:** `TreasuryFiscalDataSource` (new, no-key) + `BLSSource` v1 (new, no-key).
- **Germany / euro-area:** `ECBSource` / `EurostatSource` (new, no-key) — optional.

Optional **BYOK** sources (env var; graceful skip when unset):
- `BLSSource` auto-upgrades to v2 when `BLS_API_KEY` is set.
- `BEASource` (`BEA_API_KEY`) for US GDP.
- `FREDSource` via the **official API only** (`FRED_API_KEY`) — replace the current stub; **never** `fredgraph.csv` (ToU forbids scraping).

## Licensing posture (with Apache-2.0 code license)

- Runtime fetch only; **no bundled macro data** or cached-data artifacts in the package.
- **Attribution** emitted on every result + documented: World Bank (CC BY 4.0 — "Source: World Bank"), Eurostat ("Source: Eurostat"), ECB, OECD, IMF, DBnomics (ODbL + upstream).
- IMF/OECD are all-rights-reserved → on-demand API fetch is fine; do not redistribute their data as files.

## Why this fully answers the key-sharing problem

Published users get complete macro coverage (incl. Vietnam) with **zero keys**. FRED/BEA/BLS-v2 are opt-in upgrades keyed to the *user's own* free key — so no one shares a quota and no key is ever in the repo or the wheel.

## Semantic contract (C1/C2 — implemented)

A failover chain is only safe when every source serves the **same logical
indicator in the same unit**. The macro layer enforces this with a canonical
indicator registry (`vnfin/macro/indicators.py`), NOT generic source chaining.

### Canonical indicator registry

`MacroIndicator` (logical, provider-independent): `GDP`, `GDP_GROWTH`, `CPI`,
`INFLATION`, `UNEMPLOYMENT`. For each, the registry pins:

| Field | Meaning |
|-------|---------|
| `CANONICAL_UNIT[ind]` | the unit the chain promises the caller (e.g. GDP → `current US$`, percent indicators → `%`, CPI → `index`). |
| `CANONICAL_CURRENCY[ind]` | the money currency, or `None` for non-money series (percent/index). Never a hardcoded USD guess. |
| per-provider `MacroIndicatorSpec` | each adapter maps the canonical indicator → `(provider_code, unit, frequency, carries_projections, currency)`. |

### `IndicatorSeries` result fields (C1)

`country, indicator_code, indicator_name, points[(date,value)…], source, unit,
value_unit, currency (Optional — None for non-money), frequency (annual/quarterly/
monthly/daily), projection_from_year (Optional), country_name, fetched_at_utc,
warnings`. `to_dataframe()` adds an `is_projection` column.

### Unit homogeneity — pre-filter BEFORE the generic engine (B6/B7)

`MacroClient.get_indicator()`:

1. **`eligible_sources(sources, indicator)`** keeps only sources whose declared
   `unit_for(indicator) == canonical_unit(indicator)`. A source that would emit a
   noncanonical unit (IMF GDP `USD bn`, DBnomics GDP `national currency` vs
   canonical `current US$`) is **dropped up front**, never relabelled. This is the
   B6 fix: the default GDP/CPI/percent chains can no longer trip the
   `UnitMismatchError` guard, because the surviving chain is already homogeneous.
2. The generic `FailoverClient` is built **only after** step 1, with its
   unit-homogeneity guard remaining as a structural backstop.
3. **`_finalize` validates, never relabels** (B7): if a served result carries a
   genuinely different non-empty unit it raises `UnitMismatchError`; an empty
   placeholder unit is pinned to canonical; the indicator-specific currency is set.
4. If no source is eligible → clean `AllSourcesFailed` (capability), never a
   wrong-unit result.

### Frequency + actual-vs-projection (B8)

- `frequency` is explicit per source: WB/IMF annual, DBnomics CPI monthly, GDP annual.
- IMF WEO mixes actuals + forecasts with no per-point flag, so the IMF adapter
  applies a conservative rule — **years ≥ the current calendar year are
  projections** — and stamps `projection_from_year`. `IndicatorSeries.latest()`
  returns the latest **actual** (forecasts excluded); `latest_including_projections()`
  and `actual_points` are available for explicit forecast access.

### BYOK capability skip (C4)

A keyless `FREDMacroSource.supports(indicator)` returns `False`, so a failover
chain drops it **without any network call** — it is never advertised-then-crashing
and never raises `NotImplementedError`. A direct `get_series()` without a key
raises a catchable `SourceUnavailable` before any network call. No key is ever
bundled/committed; no shared quota.

### FRED scraping forbidden (C3)

Only the official `/fred/series/observations` JSON API (BYOK). `fredgraph.csv` is
**disallowed**; the older `docs/research/2026-06-18-macro-vietnam.md` recommendation
is marked SUPERSEDED/DISALLOWED. A regression test asserts the adapter never builds
a `fredgraph` URL.

## Macro test plan (C6 — implemented)

`tests/test_macro_*.py` (synthetic fixtures only; obviously-fake `ZZZ`/`ZZ`
countries, round fabricated values; no live-looking numbers):

- Per-source parse/empty/malformed/transport coverage (worldbank, imf, dbnomics, fred).
- **Default GDP / CPI / percent return without `UnitMismatchError`** (failover tests).
- A noncanonical-unit source is **filtered out** (not raised); if every source is
  noncanonical → `AllSourcesFailed`.
- **Projections not returned as actuals**: IMF future years flagged, `latest()`
  excludes them, `latest_including_projections()` exposes them.
- **Missing-key BYOK source skipped without a network call** (capability probe and
  in-chain, both assert zero network hits).
- Currency is indicator-specific: GDP → USD, percent/index → `None` (no hardcoded USD).
- FRED never uses `fredgraph.csv`.
- Live differential checks live only under `live_tests/` and require `VNFIN_LIVE=1`.

## For the reviewer

Implemented per this contract: (1) source list + default chain order (WB → IMF →
DBnomics), (2) BYOK env-var contract + graceful skip-without-network, (3)
no-FRED-scraping rule + supersession, (4) attribution/licensing posture,
(5) GSO/SBV deferred as BETA.
