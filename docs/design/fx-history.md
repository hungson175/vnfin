# Design — historical FX data primitives (#159)

**Status:** DESIGN — reviewer gate (must be APPROVED before any FX-history adapter code).
**Scope:** add **historical** foreign-exchange time series + capability diagnostics, alongside the
existing **spot/current** `vnfin.fx` (see [`docs/design/fx-sources.md`](fx-sources.md)). v1 is
**annual, no-key, official-source** FX history — the deterministic data primitive a Vietnam-based
long-term investor needs to express past values in VND.
**Reviewer spec:** `review-202606201018-open-backlog-spec-159-fx-history.md`.
**Clean-room:** VNStock/vnstock fully excluded. Every source below is primary/official; the World
Bank adapter is already integrated and live-verified (2026-06-18). FX-source research:
[`docs/research/2026-06-18-fx-rates-sources.md`](../research/2026-06-18-fx-rates-sources.md).

---

## 1. Why now, and the key insight

The current `vnfin.fx` is deliberately **spot-only** — `fx-sources.md` lists "no historical FX in
v0.2" as a known limitation, deferring it to "a future BYOK enhancement". #159 closes that gap with
a **no-key** path that already exists in the codebase:

> **The World Bank Indicators API already serves official historical FX, and we already have a
> battle-tested clean-room adapter for it (`WorldBankMacroSource`).**

WB indicator **`PA.NUS.FCRF`** = *"Official exchange rate (LCU per US$, period average)"*, **annual**.
For country `VNM` it returns **VND per 1 USD** — which is *exactly* vnfin's canonical FX convention
(`FXRate.rate = VND per 1 base`, base=USD). So the historical series needs **no unit re-derivation**
for the primary USD/VND path; it reuses the WB envelope parser (`[meta, [obs…]]`, BOM-tolerant,
null-year skip, duplicate-date reject, country/indicator identity guards) that is already covered by
the macro test suite.

This makes v1 small, deterministic, offline-testable, and clean-room — no new provider contract to
reverse-engineer.

---

## 2. Scope

### In scope (v1)

- A **typed historical FX time series** result with explicit `base`, `quote`, `unit`, per-point
  `(date, rate)`, `frequency`, `source`, `fetched_at_utc`, and `warnings`/coverage metadata.
- A facade verb `vnfin.fx.history(base="USD", quote="VND", start=…, end=…, frequency=ANNUAL)`.
- **Annual USD/VND** via WB `PA.NUS.FCRF` (country `VNM`), no key.
- An **offline capability diagnostic** `vnfin.diagnostics.explain_fx_coverage(base, quote, start,
  end, frequency)` mirroring the existing `explain_world_gold_history` shape.
- A **strictly deterministic** point accessor `FXHistory.rate_on(date)` that returns the exact
  observation or raises — **never** forward-fills or interpolates.
- Synthetic-only default tests; live tests opt-in. Public-API snapshot **additive only**.

### Out of scope (v1) — explicit exclusions (from the reviewer spec)

- Portfolio / backtest / asset-allocation engines.
- `normalize_to_vnd(asset_history)`-style application-layer helpers (joining an asset series to FX).
- Scraping unofficial pages.
- Fabricating history from the current spot APIs (no spot back-fill).
- Silently mixing current spot FX with historical asset prices.
- Real-time / minute / hourly / business-day FX feeds.
- Arbitrary cross-quotes beyond the documented derivation in §4 (kept narrow).

---

## 3. Source feasibility

| Source | Indicator / dataset | Freq | Key | Convention | Terms | v1 verdict |
|--------|--------------------|------|-----|------------|-------|------------|
| **World Bank** (integrated) | `PA.NUS.FCRF` — official exchange rate, period average | **annual** | none | **LCU per 1 USD** (VNM → VND/USD) | CC-BY 4.0, attribution; **redistribution allowed** | **v1 PRIMARY** |
| World Bank | `PA.NUS.ATLS` (Atlas conversion factor) | annual | none | LCU/USD (smoothed) | CC-BY 4.0 | Reject v1 (smoothed, not a market rate) |
| IMF IFS via **DBnomics** | IFS exchange-rate series (e.g. `ENDA`/`ENDE`) | monthly | none | provider-specific (per-USD or per-LCU) | DBnomics ToS; IMF redistribution caveats | **v2 candidate** — defer pending clean terms + convention verification |
| ECB / Frankfurter | — | daily | none | EUR-based, **no VND** | open | Reject (no VND, same as spot design) |
| open.er-api / Vietcombank (spot sources) | — | spot | none | VND/foreign | redistribution prohibited / "reference only" | **Never** for history (no historical endpoint; back-fill is out of scope) |

**v1 decision:** ship **WB `PA.NUS.FCRF` annual only**. It is no-key, official, already adapted,
unit-aligned to our canonical convention, and the most permissive on terms (CC-BY 4.0). Monthly
(IMF/DBnomics) is deferred to v2 because the per-USD-vs-per-LCU convention and redistribution terms
must be independently verified clean-room before we trust a monthly series — out of v1's safe core.

> **Provenance / legal (must appear in `docs/sources/fx-history-worldbank.md`):** World Bank WDI is
> **CC-BY 4.0** — redistribution permitted **with attribution** ("Source: World Bank"). Even so, v1
> is **runtime-fetch only — no bundled provider rows** (consistent with every other domain and
> avoiding stale snapshots); any future bundling/caching of raw rows would require a **separate
> design approval**, not an inline relaxation. Annual `PA.NUS.FCRF` is a **period-average** rate, not
> a year-end or central rate — this must be stated in field docs and the tutorial so no one mistakes
> it for a point-in-time or SBV central rate.

---

## 4. Public API & data model

### Result types (new, in `vnfin/fx/history_models.py`)

```python
@dataclass(frozen=True)
class FXPoint:
    date: date          # observation date (annual → Jan 1 of the reference year)
    rate: float         # quote per 1 base (e.g. VND per 1 USD), > 0, finite

@dataclass(frozen=True)
class FXHistory(TimeSeriesResult):
    base: str                      # ISO 4217, e.g. "USD"
    quote: str                     # "VND" in v1
    points: tuple[FXPoint, ...]    # ascending (oldest-first)
    unit: str                      # "VND per 1 USD"
    frequency: Frequency           # Frequency.ANNUAL in v1 (reuse macro enum)
    source: str                    # "worldbank_fx" (PA.NUS.FCRF)
    value_unit: Optional[str] = None       # mirrors `unit` (cross-domain alias)
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()

    # TimeSeriesResult wiring: _items_attr="points", _index_column="date",
    #   _df_columns=("date", "rate")  -> free __len__/__iter__/to_dataframe()

    def rate_on(self, d: date) -> float:
        """Exact observation for `d`, else InvalidData. NEVER fills/interpolates."""

    def latest(self) -> Optional[FXPoint]: ...
```

`FXHistory` subclasses `TimeSeriesResult` (same mixin as `IndicatorSeries`/`PriceHistory`) so it
gets `__len__`/`__iter__`/`to_dataframe()` with provenance in `df.attrs` for free, and the duplicate-
key backstop applies. This is the **first time `to_dataframe()` is offered for FX** — intentional,
because history *is* a series (spot stayed flat by design).

### Facade (additive to `vnfin/fx/__init__.py`)

```python
def history(
    base: str = "USD",
    quote: str = "VND",
    start: date | None = None,
    end: date | None = None,
    *,
    frequency: Frequency = Frequency.ANNUAL,
    http_get=None,
    timeout: float = 25.0,
) -> FXHistory: ...
```

- Validates `base`/`quote` ISO-4217 shape (reuse `_normalize_ccy` contract) **before** any call.
- v1 supports `quote="VND"` and `frequency=ANNUAL` only; anything else → `InvalidData` (loud, not
  silent), keeping the door open for v2 without changing the signature.
- `start`/`end` validated via `validate_date_range` (same contract as every other domain).

### Source adapter (`vnfin/fx/history_worldbank.py`)

A thin FX-specific wrapper that **reuses `WorldBankMacroSource`** (composition, not a fork): it calls
the WB Indicators API for `PA.NUS.FCRF` on the country implied by the quote currency (`VND → VNM`),
then maps the returned `(date, value)` points into `FXPoint`s and stamps `unit="VND per 1 USD"`,
`source="worldbank_fx"`. No new envelope parsing — it leans on the already-tested WB parser.

- **No failover chain in v1** (single official source). `source="worldbank_fx"`; if a v2 monthly
  source lands, a `FailoverFXHistoryClient` can be added then, mirroring `FailoverFXClient`.

### Cross-quote handling (narrow, explicit)

v1 ships **USD/VND only**. A non-USD base (e.g. `EUR/VND`) is **rejected with a clear message** in
v1 rather than silently cross-deriving. Rationale: an `EUR/VND` annual series would require dividing
two WB `PA.NUS.FCRF` series (`VNM` and the Euro-area country), introducing alignment + missing-year
semantics that deserve their own design. Documented as a v2 item, not a silent half-feature.

---

## 5. Conversion primitives (minimal, deterministic, or deferred)

The reviewer allows "minimal safe conversion primitives **only** if they are deterministic data
transforms over an explicit FX history/rate input." v1 ships exactly one, and **only** the accessor:

- **`FXHistory.rate_on(d) -> float`** — returns the rate for the exact observation date `d`, else
  raises `InvalidData`. It never forward-fills, interpolates, or picks "nearest". For annual data the
  caller must pass the stamped key (Jan 1 of the year); a convenience `rate_for_year(year)` may be
  added as sugar over the same exact-match rule.

**Deferred (out of v1):** any `convert(amount, base→quote, on=date)` that *combines* an external
amount with FX, and absolutely any `normalize_to_vnd(asset_history)` that joins an asset series to
FX. These are the application-layer helpers the reviewer excluded; the date-alignment policy they
need (§6) is precisely why they are a separate, later design.

---

## 6. Date-alignment & coverage policy (the core safety question)

This is where silent wrongness would live, so v1 is conservative **by refusing to align for the
caller**:

1. **No auto-join.** v1 returns an `FXHistory`; it does **not** accept an asset series and align FX
   onto it. The annual-FX-vs-daily-asset mismatch is therefore never resolved silently inside vnfin.
2. **Exact-match accessor only.** `rate_on(d)` is exact-or-raise (§5). There is no "as-of"/"nearest"
   mode in v1 — adding one is a deliberate v2 decision with explicit semantics.
3. **Frequency is explicit** on `FXHistory.frequency`, so any future alignment helper can *see* that
   FX is annual and warn/fail when an asset is daily/7-day.
4. **Coverage is reported, not guessed** — see the diagnostic below.

### Capability diagnostic (additive to `vnfin/diagnostics.py`)

```python
def explain_fx_coverage(
    base="USD", quote="VND", start=None, end=None, *, frequency=Frequency.ANNUAL,
) -> RequestDiagnostic
```

Reuses the existing `SourceCapability` / `RequestDiagnostic` shapes. It is **offline** (no network),
canonicalizes `base`/`quote` with the same contract as the live call, validates the date range, and
reports:

- `status="ok"` when base/quote/frequency are supported and the window is plausibly covered;
- `status="coverage_gap"` when the window predates the WB FX series start (WB `PA.NUS.FCRF` generally
  begins ~1960 for VNM's reporting; the exact documented lower bound is a known *lower bound*, not a
  promise — encoded as a `SourceCapability.coverage_start`);
- `status="unsupported_pair"` for a non-VND quote or non-USD base in v1;
- `status="unsupported_frequency"` for anything but annual in v1;
- with `notes` + `suggested_actions` (e.g. "annual period-average only; for sub-annual FX no no-key
  source is configured in v1").

A new FX `SourceCapability` (domain `"fx"`, endpoint `"history"`, source `"worldbank_fx"`,
granularity `"annual"`, `is_single_source=True`, limitations = period-average / annual-only /
USD-VND-only) is added to the static registry and surfaced by `source_capabilities()`.

---

## 7. Answers to the reviewer's design questions

1. **Source choice:** WB `PA.NUS.FCRF` (no-key, CC-BY 4.0, already adapted, unit-aligned to VND/USD).
2. **Frequency:** **annual only** in v1 (WB). Monthly (IMF IFS via DBnomics) deferred to v2 pending
   clean-room convention + terms verification — not in the safe core.
3. **API shape:** `vnfin.fx.history(...)` facade → new `FXHistory` (TimeSeriesResult) of `FXPoint`,
   plus `vnfin.diagnostics.explain_fx_coverage(...)`. Spot `FXRate`/`get_rate`/`client` unchanged.
4. **Conversion:** only `FXHistory.rate_on(date)` — exact-match-or-raise over an explicit FX series.
   No amount-conversion or asset-normalization helper in v1 (those need §6 alignment policy first).
5. **Date alignment:** v1 does **not** align FX to assets at all (no auto-join); `rate_on` is exact-
   or-raise (never fills); `frequency` is explicit so a future helper can warn/fail on a daily-vs-
   annual mismatch. This is the deliberate guard against silent mixing.
6. **Coverage:** `explain_fx_coverage` (offline) + an FX `SourceCapability` report missing
   start/end windows, unsupported pairs, and unsupported frequency — no fabrication.
7. **Source/legal:** WB WDI is CC-BY 4.0 (attribution; redistribution permitted), runtime-fetch in
   v1 for consistency. `PA.NUS.FCRF` is a **period-average** rate (documented; not central/year-end).

---

## 8. Test matrix (TDD, synthetic-only default; live opt-in)

**Offline unit (mock `http_get`, synthetic WB envelope fixtures — obvious fake round numbers):**

- Parse a synthetic `PA.NUS.FCRF` VNM envelope → `FXHistory` with `unit="VND per 1 USD"`,
  `frequency=ANNUAL`, ascending points, correct `source`.
- `rate_on(exact date)` returns the value; `rate_on(missing date)` raises `InvalidData` (no fill).
- `to_dataframe()` indexed by `date`, columns `("date","rate")`, provenance in `df.attrs`; duplicate
  observation date → `InvalidData` (TimeSeriesResult backstop).
- **Validation:** non-VND quote → `InvalidData`; non-USD base → `InvalidData` (unsupported in v1);
  non-annual frequency → `InvalidData`; malformed ISO code → `InvalidData`; `start>end` → `VnfinError`;
  non-positive/non-finite provider rate → `InvalidData` (reuse WB parser guards).
- Empty/null-only WB window → `EmptyData`.
- **Diagnostics:** `explain_fx_coverage` statuses — `ok`, `coverage_gap` (window before series start),
  `unsupported_pair`, `unsupported_frequency`; offline (no network); FX cap appears in
  `source_capabilities()`.
- **Docs-contract guard:** the FX-history tutorial example uses keyword `start=`/`end=` (consistent
  with #164) and references the period-average caveat.
- **Public-API snapshot:** additive entries only (`fx.history`, `FXHistory`, `FXPoint`,
  `explain_fx_coverage`) — regenerate `tests/snapshots/public_api_v0_2_0.json`, snapshot test green.

**Opt-in live (`live_tests/`, skipped in CI):** real WB `PA.NUS.FCRF` VNM fetch returns a plausible
USD/VND band (e.g. last actual within 15,000–40,000) and ascending annual dates.

---

## 9. Acceptance gate for design review

- [x] `docs/design/fx-history.md` (this doc).
- [x] Proposed dataclasses / API signatures (§4).
- [x] Source feasibility table (§3).
- [x] Test matrix — offline synthetic + opt-in live (§8).
- [x] Explicit scope exclusions (§2).
- [ ] **No implementation code** until the reviewer approves this design.

## 10. Open questions for the reviewer

1. **Module placement:** `FXHistory`/`FXPoint` in a new `vnfin/fx/history_models.py` + adapter in
   `vnfin/fx/history_worldbank.py`, reusing `WorldBankMacroSource` by composition — OK? (I lean yes;
   keeps the FX domain coherent while not duplicating WB parsing.)
2. **`source` label:** `"worldbank_fx"` to distinguish from the macro `"worldbank"` source, or reuse
   `"worldbank"`? (I lean `"worldbank_fx"` for clear FX provenance.)
3. **`rate_for_year(year)` sugar:** include the year-convenience accessor over the exact-match rule,
   or ship only `rate_on(date)` in v1? (I lean: include it — annual data makes year-keying natural.)
4. **v2 scope confirmation:** agree monthly (IMF/DBnomics) and non-USD cross-quotes are explicitly
   v2, gated on a separate clean-room terms+convention check?
