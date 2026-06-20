# Source — World Bank historical FX (`PA.NUS.FCRF`)

**Domain:** `vnfin.fx.history` (issue #159) · **Source name:** `worldbank_fx` · **Auth:** none (no key).

## Endpoint & contract

Historical annual USD/VND is served by the World Bank Indicators API v2, indicator
**`PA.NUS.FCRF`** — *"Official exchange rate (LCU per US$, period average)"*:

```text
GET https://api.worldbank.org/v2/country/VNM/indicator/PA.NUS.FCRF?format=json&per_page=20000
```

For country `VNM` the local currency unit is VND, so each observation is **VND per 1 USD** —
already vnfin's canonical FX convention (`FXRate.rate` / `FXHistory.unit = "VND per 1 USD"`). No
unit re-derivation is needed.

The response envelope (`[meta, [obs…]]`, BOM-tolerant, null-year skip, duplicate-date reject,
country/indicator identity guards) is parsed by the existing, well-tested
`vnfin.macro.worldbank.WorldBankMacroSource`. `vnfin/fx/history_worldbank.py` **composes** that
source rather than re-parsing — it only maps `(date, value)` points into `FXPoint`s (with an
explicit positive-rate guard) and filters to the requested inclusive calendar-year window.

## Semantics

- **Frequency:** annual. Each point is stamped on **Jan 1** of the reference year.
- **`PA.NUS.FCRF` is an annual _period-average_ rate** — *not* a year-end snapshot and *not* the
  State Bank of Vietnam (SBV) central rate. Documentation and field names must not imply otherwise.
- **Coverage:** the official API currently returns its first non-null VNM observation at **1983**.
  `vnfin.diagnostics.explain_fx_coverage(...)` uses `date(1983, 1, 1)` as a conservative documented
  lower bound (not a generic 1960 promise). Coverage bounds are *known lower bounds*, not promises.
- **Positive-rate guard:** macro series may validly be negative, but an FX rate must be a finite
  value `> 0`; the adapter rejects `<= 0` / non-finite / bool values as `InvalidData`.

## Terms / provenance

- **License:** World Bank WDI is **CC-BY 4.0** — attribution required: *"Source: World Bank"*.
- **Posture:** v1 is **runtime-fetch only — no bundled provider rows**. (CC-BY would permit
  redistribution with attribution, but bundling/caching raw rows is **not** done in v1 and would
  require a separate design approval, not an inline relaxation.)
- This matches the library-wide data-use note: `vnfin` is an API *client*; provider data remains
  provider data.

## Limits

- **Annual only** in v1 — no monthly/daily no-key FX history. Monthly (IMF IFS via DBnomics) is a
  v2 candidate, gated on a separate clean-room terms + convention review.
- **USD/VND only** in v1 — non-USD cross-quotes (e.g. EUR/VND) are deferred to v2.
