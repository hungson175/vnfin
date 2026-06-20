# Design — fundamentals metrics & coverage diagnostics (#157)

**Status:** DESIGN (rev 2 — addresses design-review BLOCK 2026-06-20: per-fiscal-date/per-statement
source shape, multi-source safety, CafeF code-namespace mapping). Must be APPROVED before any code.
**Scope:** an **additive, offline** canonical-metrics + coverage-diagnostics layer on top of the
existing `vnfin.fundamentals` reports — fundamental **data primitives and diagnostics** for
long-term investors, *not* an advice/ranking/screener layer.
**Reviewer spec:** `spec-202606201222-issue157-fundamentals-metrics.md`.
**Clean-room:** VNStock/vnstock fully excluded. v1 consumes only existing clean-room outputs
(`fundamentals.get_financials()`) and the existing `vnfin/fundamentals/itemcodes.py` map — **no new
external source** (TradingView/Vietstock/annual-report PDFs are NOT approved by this spec).

---

## 1. Why now, and the key insight

`vnfin.fundamentals.get_financials()` already returns typed `FinancialReport`s (income/balance/
cashflow/ratios) of `LineItem`s keyed by numeric VNDirect `item_code`, with `is_bank` /
`model_type` taxonomy and per-line `value_unit`. But a caller still has to **know the raw item
codes** (`revenue = report.get("11000")`), know **which codes apply to banks vs corporates**, and
hand-roll **derived ratios** — exactly the friction #157 raises.

> **The mapping already exists.** `itemcodes.py` carries the clean-room corporate (modelType 1/2/3)
> and bank (101/102/103) headline maps. #157 promotes those raw codes into **stable canonical
> metric ids** with definitions, units, bank/non-bank applicability, derived formulas, and coverage
> diagnostics — a thin, honest layer, no new network and no new provider contract.

This keeps v1 small, deterministic, fully offline-testable (it transforms `FinancialReport`s), and
clean-room.

---

## 2. Scope

### In scope (v1)

- **Canonical metric identifiers + definitions** (`MetricId` enum + `MetricDefinition` catalog).
- **Bank vs non-bank mappings** kept as separate maps with explicit `applies_to` taxonomy.
- **raw_mapped / provider_native / derived** kind flags + formula/source lineage per metric.
- Explicit **value units** and fiscal-period metadata on every value.
- **Coverage diagnostics** (per fiscal_date): missing/unmapped/blocked per metric; named-vs-generic
  item-label stats; per-statement status + **succeeding source** (ratios `not_requested` in v1, B7;
  no failed-attempt trail in v1, B2); not-applicable per bank/non-bank.
- **Batch-friendly, non-fatal** diagnostics (a bad symbol yields a per-symbol diagnostic, never
  aborts a universe) so users can build their *own* screeners.
- 5 derived metrics (margins/leverage) with zero/negative/missing denominator guards.
- Synthetic-only default tests; additive public-API snapshot.

### Out of scope (v1) — explicit non-goals (from the reviewer spec)

- Stock ranking / recommendations / buy-sell advice.
- An opinionated `screen(...)` that sorts/filters by an investment strategy (any batch helper is a
  thin data-retrieval/diagnostic convenience with **no ranking/advice defaults**; strategy screening
  stays in docs examples only).
- Blind ingestion of TradingView / Vietstock / annual-report PDFs / third-party metric pages.
- Pretending generic `item_<code>` labels are investor-ready metrics.
- Silently comparing bank and non-bank metrics without taxonomy metadata.
- Valuation / EPS / BV / ROE-family until their inputs are designed (see §6 v2).

---

## 3. Public API (additive to `vnfin.fundamentals`)

```python
from vnfin import fundamentals

# 1. The catalog — immutable, offline, no symbol needed.
cat = fundamentals.metric_catalog()                          # tuple[MetricDefinition, ...]
cat = fundamentals.metric_catalog(applies_to="bank")         # optional filter

# 2. Explain one metric — definition + mapping/formula/lineage.
defn = fundamentals.explain_metric("net_income")             # MetricDefinition (or MetricId)

# 3. Extract metrics for a symbol — newest fiscal period first.
reports = fundamentals.metrics("FPT", period="annual")       # tuple[MetricReport, ...]
latest = reports[0]
gm = latest.get("gross_margin")                              # MetricValue | None

# 4. Coverage diagnostics — offline-friendly, non-fatal, batch-ready.
cov = fundamentals.explain_metric_coverage("FPT", period="annual")   # MetricCoverage
```

- `metric_catalog()` / `explain_metric()` are **fully offline** (no network) — pure registry.
- `metrics()` / `explain_metric_coverage()` call `get_financials()` for the income+balance+cashflow
  statements (and `ratios` only where a provider-native metric needs it), then transform offline.
  They reuse the existing failover chain and surface its `warnings`/attempts.
- All names are additive; **spot/existing `get_financials` is unchanged**. Exported via
  `vnfin.fundamentals.__all__` and captured additively in the public-API snapshot.

### Exact final signatures (B4) + pure transformer

```python
def metric_catalog(applies_to: AppliesTo | str | None = None) -> tuple[MetricDefinition, ...]: ...
def explain_metric(metric_id: MetricId | str) -> MetricDefinition: ...

def metrics(
    symbol: str,
    period="annual",
    *,
    is_bank: bool | None = AUTO,
    limit: int = 8,
    source: FundamentalSource | None = None,
    sources=None,
    max_attempts: int = 3,
    http_get=None,
    timeout: float = 25.0,
) -> tuple[MetricReport, ...]: ...

def explain_metric_coverage(
    symbol: str,
    period="annual",
    *,
    is_bank: bool | None = AUTO,
    limit: int = 8,
    source: FundamentalSource | None = None,
    sources=None,
    max_attempts: int = 3,
    http_get=None,
    timeout: float = 25.0,
) -> MetricCoverage: ...

# Private PURE transformer (B4) — no network; synthetic tests build FinancialReports and call this
# directly, so unit tests need no fake HTTP plumbing. The fetching wrappers above call get_financials
# per statement then delegate to this.
def _metrics_from_reports(
    symbol, period, is_bank,
    by_statement: dict,   # {StatementType: tuple[FinancialReport, ...]} aligned-by-fiscal_date upstream
) -> tuple[MetricReport, ...]: ...
```

- `metrics()`/`explain_metric_coverage()` mirror `get_financials`' injection knobs (`is_bank`,
  `limit`, `source`/`sources`, `http_get`, `timeout`, `max_attempts`) so tests can inject a fake
  `http_get` or a stub `source`, and callers keep the same controls.
- `metric_catalog()`/`explain_metric()` make **zero** network calls (pure registry).
- The pure `_metrics_from_reports(...)` transformer is the TDD seam: synthetic `FinancialReport`
  fixtures → `MetricReport`s with **no HTTP**.

### Proposed final names

`metric_catalog`, `explain_metric`, `metrics`, `explain_metric_coverage` — kept as the spec proposed.
**Implementation module is `vnfin/fundamentals/metric_api.py`, NOT `metrics.py`** (B5: a `metrics.py`
submodule would shadow the `fundamentals.metrics` function attribute — a known Python footgun); models
in `vnfin/fundamentals/metric_models.py`. `screen(...)` / `metrics_batch(...)` are **not** added in
v1 (non-goal); batch coverage is a docs-only loop over `explain_metric_coverage` (see §5 batch).

---

## 3.5 Failover & source-namespace constraints (the design-review blockers)

Three hard constraints from the existing fundamentals layer shape the model below. Getting these
wrong would make the metrics layer silently produce empty/mislabeled data, so they are first-class.

### C1 — `get_financials` exposes only the SUCCEEDING source, not failed attempts (B2)

The public `get_financials()` returns just `tuple[FinancialReport]`. The failover engine's
**attempt history (which sources were tried and rejected) is internal and NOT exposed** through any
public method. Therefore the metrics layer **cannot** report a full source-attempt log without a new
client API — which is **out of v1 scope**.

- v1 coverage reports the **succeeding source per statement** (each `FinancialReport.source`) and a
  per-statement `status` (`ok` / `missing` / `source_error`). It does **not** claim a failed-attempt
  trail. (A future `get_financials(..., return_attempts=True)` could add it — flagged as v2.)

### C2 — a metrics request fans out to 3 statements → sources can differ → no single report `source` (B2)

`metrics()` must fetch income + balance + cashflow **separately**, each through its own failover.
They can resolve to **different sources** — most concretely, **CafeF does not serve cashflow**
(`Type=3` → `EmptyData`), so cashflow is VNDirect-only while income/balance may have fallen over to
CafeF. A single `MetricReport.source` is therefore **unsafe/ambiguous** and is **removed**.

- Replace it with **per-statement** provenance: `MetricReport.statement_sources` (`{StatementType:
  source}`), and per-value lineage already on `MetricValue.inputs[].source`. A derived metric whose
  inputs span >1 source is flagged with a `mixed_source` warning (honest, never hidden).

### C3 — CafeF uses a DIFFERENT code namespace than VNDirect (B3)

`itemcodes.py` and the spec's metric taxonomy are the **VNDirect numeric** namespace (`11000`,
`21000`, …). **CafeF uses string codes** (`"DTTBHCCDV"`, and ratio codes `EPS`/`BV`/`PE`/`ROE`…).
So `report.get("11000")` returns `None` for a CafeF-sourced report even though the data is present
under a different code — a silent all-MISSING trap.

- The metric code map is **source-namespaced**. **v1 maps the VNDirect namespace only.** For a
  report whose `source != "vndirect"` (e.g. CafeF), raw_mapped metrics are marked
  `availability=BLOCKED` with the stable reason `"metric map not available for source <name>"` —
  **never silently MISSING**. A **CafeF headline-code map is a defined v1.x follow-up** (needs its
  own clean-room derivation of CafeF's string codes), kept out of this slice to stay small+correct.
- Note: because VNDirect is the primary and the only cashflow source, in practice most metrics
  resolve via VNDirect; CafeF only backstops income/balance, and when it does, v1 is honest that the
  mapped metrics are BLOCKED rather than wrong.

## 4. Data model (new, in `vnfin/fundamentals/metric_models.py`)

```python
class MetricId(str, Enum):           # stable canonical ids, e.g. "net_income", "gross_margin"
    NET_REVENUE = "net_revenue"; GROSS_PROFIT = "gross_profit"; ...   # full list in §6

class MetricCategory(str, Enum):     # PROFITABILITY | LIQUIDITY | LEVERAGE | CASHFLOW | SIZE | ...
class MetricKind(str, Enum):         # RAW_MAPPED | PROVIDER_NATIVE | DERIVED
class AppliesTo(str, Enum):          # CORPORATE | BANK | BOTH
class MetricAvailability(str, Enum): # AVAILABLE | MISSING | BLOCKED | NOT_APPLICABLE | UNSUPPORTED

@dataclass(frozen=True)
class MetricInput:                   # one source line a metric was built from (lineage)
    statement: StatementType
    item_code: str                   # mapped raw code (or ratioCode for provider_native)
    value: float
    value_unit: str                  # "VND" | "vnd_per_share" | "ratio"
    fiscal_date: date
    source: str

@dataclass(frozen=True)
class MetricDefinition:              # static catalog entry (no symbol)
    id: MetricId
    name: str                        # human label, e.g. "Net income"
    category: MetricCategory
    kind: MetricKind
    applies_to: AppliesTo
    value_unit: str                  # canonical unit of the metric value
    # raw_mapped: which statement+code(s) supply it (per corporate/bank);
    # derived: the formula + the MetricIds it consumes.
    corporate_code: Optional[str] = None
    bank_code: Optional[str] = None
    statement: Optional[StatementType] = None
    formula: Optional[str] = None            # human formula for derived, e.g. "gross_profit / net_revenue"
    inputs: tuple[MetricId, ...] = ()        # derived dependencies

@dataclass(frozen=True)
class MetricValue:
    id: MetricId
    value: Optional[float]           # None when not AVAILABLE
    value_unit: str
    kind: MetricKind
    availability: MetricAvailability
    fiscal_date: date
    inputs: tuple[MetricInput, ...]  # lineage (raw lines / dependency values used)
    reason: Optional[str] = None     # stable reason when not AVAILABLE (e.g. "missing input revenue")
    warnings: tuple[str, ...] = ()

@dataclass(frozen=True)
class StatementProvenance:           # per-statement outcome for one fiscal period
    statement: StatementType
    status: str                      # "ok" | "missing" | "source_error" | "not_served"
    source: Optional[str]            # SUCCEEDING source (C1: no failed-attempt trail in v1)
    detail: Optional[str] = None     # e.g. the SourceError message class

@dataclass(frozen=True)
class MetricReport:                  # all metrics for one symbol + one fiscal period
    symbol: str
    period: Period
    fiscal_date: date
    is_bank: bool
    metrics: tuple[MetricValue, ...]
    # C2: NO single `source` — provenance is PER STATEMENT (sources can differ; cashflow is
    # VNDirect-only). Per-value lineage lives on MetricValue.inputs[].source.
    statement_sources: tuple[StatementProvenance, ...]
    warnings: tuple[str, ...] = ()   # incl. "mixed_source" when a value's inputs span >1 source
    def get(self, metric_id) -> Optional[MetricValue]: ...   # B6: returns a value even when unavailable
    # to_dataframe() — one row per metric; columns (Q5):
    #   metric_id, name, value, value_unit, kind, availability, reason, category, applies_to,
    #   fiscal_date (+ input_codes, input_sources where practical). Metadata in df.attrs.
    def to_dataframe(self) -> "pd.DataFrame": ...

@dataclass(frozen=True)
class PeriodCoverage:               # B1: coverage is PER fiscal_date
    fiscal_date: date
    is_bank: Optional[bool]
    statement_provenance: tuple[StatementProvenance, ...]   # per-statement status + succeeding source
    ratio_status: str = "not_requested"                     # B7: v1 never fetches ratios
    per_metric: tuple[tuple[MetricId, MetricAvailability, Optional[str]], ...]
    named_item_count: int                                   # LineItems with a real name
    generic_item_count: int                                 # LineItems still "item_<code>"
    unmapped_codes: tuple[str, ...]                         # present codes not in the metric map

@dataclass(frozen=True)
class MetricCoverage:               # offline-friendly diagnosis for a symbol over the fetched periods
    symbol: str
    period: Period
    periods: tuple[PeriodCoverage, ...]     # B1: one entry per fiscal_date (newest first)
    notes: tuple[str, ...] = ()
```

`MetricReport` reuses the same `to_dataframe()` convention (metadata in `df.attrs`). It does **not**
need `TimeSeriesResult` (it is one period; the *tuple* of reports is the series — callers concat).

---

## 5. Behavior

### Extraction (`metrics`)

1. Resolve bank vs corporate via the existing `is_bank` AUTO detection in `get_financials`.
2. Fetch income+balance+cashflow `FinancialReport`s **separately** (each its own failover), newest-
   first, shared `limit`. Record each statement's outcome as a `StatementProvenance` (status +
   **succeeding source**; C1/C2). A statement that raises a recoverable `SourceError` →
   `status="source_error"` (not a crash); cashflow via CafeF → `status="not_served"`.
3. Align reports by `fiscal_date` → one `MetricReport` per period, carrying its `statement_sources`.
   For each statement build a **`code -> LineItem` index** from `report.items` (B8 — `LineItem`
   carries `value` + `value_unit`; `FinancialReport.get()` returns only `float` and is **not** used
   for lineage).
4. **Full-catalog invariant (B6):** every `MetricReport` contains a `MetricValue` for **every** v1
   catalog metric — applicability is expressed by `availability`, never by omission. `MetricReport.get(id)`
   returns a `MetricValue` (possibly unavailable) for any known id. For each `MetricDefinition`:
   - **`applies_to` mismatch** (e.g. `gross_margin` for a bank, or a bank-only id for a corporate)
     → `NOT_APPLICABLE`, value `None`. (It is still present in the report.)
   - **Source-namespace gate (C3):** pick the code for the metric's statement by that statement's
     **succeeding source** — `corporate_code`/`bank_code` are VNDirect-namespace; if the source is not
     `vndirect` (unmapped in v1, e.g. CafeF) → `BLOCKED`, reason `"metric map not available for
     source <name>"` (never silent MISSING).
   - **raw_mapped:** look the code up in the statement's `code -> LineItem` index; build a
     `MetricInput` from the full `LineItem` (statement, code, value, `value_unit`, fiscal_date,
     **source**). Missing code / missing-or-failed statement → `MISSING` with a reason naming the input.
   - **derived:** compute `formula` from already-resolved `MetricValue`s with **guards** —
     denominator zero/negative/missing/non-finite → `MISSING`/`BLOCKED` with a stable `reason`,
     value `None` (never `inf`/`NaN`, never a silent wrong number); if inputs span >1 source add a
     `mixed_source` warning.
5. Carry per-statement provenance + any `mixed_source`/failover warnings onto the report (no single
   `source` field — C2).

### Coverage (`explain_metric_coverage`)

Same fetch, but never raises on a per-statement failure. It returns a `MetricCoverage` whose
`periods` is **one `PeriodCoverage` per fiscal_date** (B1). Each period entry records: per-statement
`StatementProvenance` (status + **succeeding source**), named-vs-generic item-label counts, unmapped
codes, and each metric's availability + reason (including `BLOCKED` for an unmapped source namespace,
C3). It does **not** fabricate a failed-attempt trail (C1). Designed so a caller can loop over a
universe catching nothing and get a per-symbol, per-period `MetricCoverage`.

**Ratios in v1 (B7):** v1 ships **no** ratio/provider-native metric, so `metrics()` and
`explain_metric_coverage()` fetch only income+balance+cashflow and make **zero** ratio calls;
`PeriodCoverage.ratio_status` is the constant `"not_requested"`. Ratio fetching is added only when a
provider-native metric (EPS/BV) actually ships (v2).

### Batch (non-fatal, no ranking)

No `screen()` in v1. The documented pattern is a plain loop:

```python
rows = []
for sym in universe:
    try:
        rows.append(fundamentals.explain_metric_coverage(sym, period="annual"))
    except VnfinError as e:
        rows.append(("error", sym, str(e)))   # caller decides; nothing is ranked/advised
```

If a future `metrics_batch(symbols)` helper is added, it returns per-symbol results/diagnostics with
**no sort/filter/advice defaults** — a thin retrieval convenience only.

---

## 6. Metric taxonomy — v1 vs v2

### v1 — raw_mapped (corporate, from `itemcodes._CORPORATE`)

> **Id renames (reviewer Q2)** for clarity/disambiguation: `net_revenue` (not `revenue`),
> `total_liabilities` (not `liabilities`), `owners_equity` (not `equity`), `cash_end_of_period`
> (not `cash_end`). Bank `total_liabilities`/`owners_equity` reuse the same canonical ids via
> `bank_code`.

| MetricId | code | category |
|----------|------|----------|
| net_revenue | 11000 | size/profitability |
| gross_profit | 11200 | profitability |
| operating_profit | 14000 | profitability |
| profit_before_tax | 20000 | profitability |
| net_income | 21000 | profitability |
| net_income_parent | 21100 | profitability |
| cash_and_equivalents | 23100 | liquidity |
| current_assets | 23000 | liquidity |
| total_assets | 25000 | size |
| total_liabilities | 30000 | leverage |
| current_liabilities | 30100 | leverage |
| long_term_liabilities | 30200 | leverage |
| owners_equity | 40000 | size |
| operating_cash_flow | 31000 | cashflow |
| investing_cash_flow | 32000 | cashflow |
| financing_cash_flow | 33000 | cashflow |
| net_cash_flow | 34000 | cashflow |
| cash_end_of_period | 35000 | cashflow |

### v1 — raw_mapped (bank, from `itemcodes._BANK`)

| MetricId | code | category |
|----------|------|----------|
| net_interest_income | 22070 | profitability |
| net_fee_income | 22080 | profitability |
| total_operating_income | 22120 | profitability |
| operating_expenses | 22130 | profitability |
| credit_provision_expense | 22150 | profitability |
| profit_before_tax (bank) | 22160 | profitability |
| net_income (bank) | 421601 | profitability |
| loans_to_customers | 411600 | size |
| total_assets (bank) | 412000 | size |
| customer_deposits | 413100 | leverage |
| total_liabilities (bank) | 414000 | leverage |
| owners_equity (bank) | 415000 | size |
| operating_cash_flow (bank) | 431000 | cashflow |
| investing_cash_flow (bank) | 432000 | cashflow |
| financing_cash_flow (bank) | 433000 | cashflow |

> `profit_before_tax`, `net_income`, `total_assets`, `total_liabilities`, `owners_equity`, and the
> cashflow trio are **shared canonical ids** (reviewer Q2 APPROVED) with **different underlying codes
> per entity type** (one `MetricId`,
> `corporate_code` + `bank_code` on the definition). `applies_to=BOTH` for those; corporate-only
> margins are `applies_to=CORPORATE`; bank-specific lines are `applies_to=BANK`.

### v1 — derived (formula-backed, guarded)

| MetricId | formula | applies_to | unit |
|----------|---------|------------|------|
| gross_margin | gross_profit / net_revenue | CORPORATE | ratio |
| net_margin | net_income / net_revenue | CORPORATE | ratio |
| liabilities_to_equity | total_liabilities / owners_equity | BOTH | ratio |
| cash_to_assets | cash_and_equivalents / total_assets | CORPORATE | ratio |
| operating_cash_flow_margin | operating_cash_flow / net_revenue | CORPORATE | ratio |

(For banks, revenue-based margins are `NOT_APPLICABLE`; `liabilities_to_equity` uses the bank codes
via `bank_code` on the shared `total_liabilities`/`owners_equity` definitions.)

### v1.x — CafeF code-namespace map (deferred, C3)

A clean-room map of **CafeF's string headline codes** (e.g. `"DTTBHCCDV"` → `revenue`) so a
CafeF-sourced statement also resolves canonical metrics instead of `BLOCKED`. Deferred out of v1 to
keep the slice small + correct; until then CafeF-sourced metrics are `BLOCKED` with an explicit
reason (never silently MISSING). Needs its own clean-room derivation from CafeF's own responses.

### v2 — deferred / blocked (explicit, with reason)

- **ROE / ROA / ROIC** — need average denominators (≥2 periods of equity/assets); `BLOCKED` with
  reason when insufficient periods. (Design later: averaging policy + min-period guard.)
- **free_cash_flow** — needs a mapped capex line (not in the headline map); `BLOCKED` until mapped.
- **Valuation (P/E, P/B, P/S, EV/EBITDA, dividend_yield)** — need market-cap / share-count /
  dividend primitives that don't exist yet; `UNSUPPORTED` until those domains are designed.
- **EPS / book_value_per_share** — `provider_native` from the `ratios` statement; only shipped once
  the ratioCode mapping + `vnd_per_share` unit are verified (don't emit generic VND). Candidate v1.x.

---

## 7. Diagnostics requirements coverage (spec §"Coverage and diagnostics")

| Requirement | Where |
|-------------|-------|
| statement availability by source/type/period/fiscal_date | `PeriodCoverage.statement_provenance` (per fiscal_date, B1) with succeeding source |
| ratio failures separate from statement failures | `PeriodCoverage.ratio_status` (distinct field; v1 = constant `"not_requested"`, B7 — no ratio fetch until a provider-native metric ships) |
| item-label coverage: named vs generic + unmapped codes | `PeriodCoverage.named_item_count` / `generic_item_count` / `unmapped_codes` |
| missing inputs per metric with stable reason | `MetricValue.reason` + `PeriodCoverage.per_metric` |
| not-applicable for bank vs non-bank | `MetricAvailability.NOT_APPLICABLE` via `applies_to` |
| unmapped source namespace (e.g. CafeF) | `MetricAvailability.BLOCKED` + reason (C3) — never silent MISSING |
| source provenance (succeeding source per statement) | `StatementProvenance.source` + `MetricInput.source` lineage (C1: no failed-attempt trail in v1) |
| batch mode without aborting a universe | non-fatal `explain_metric_coverage`, per-symbol loop (§5) |

---

## 8. Source / legal

- v1 uses **only** existing clean-room `fundamentals.get_financials()` outputs + `itemcodes.py`. No
  new external source, no scraping, no bundled provider rows; the metrics layer adds **no network
  call of its own** beyond what `get_financials` already does.
- Any future external metric/source (annual-report PDFs, Vietstock, TradingView) requires a
  **separate source/legal design** and is explicitly NOT approved here.
- The clean-room itemCode→name pairings already documented in `itemcodes.py` remain the only
  provenance; the metric map is derived from those codes + public Vietnamese statement structure.

---

## 9. Test matrix (TDD, synthetic-only default)

Build `FinancialReport`/`LineItem` fixtures in-memory (fake round numbers) — no network:

- **corporate extraction:** fake income+balance+cashflow → `MetricReport` with correct raw_mapped
  ids/units/values, newest-first, `is_bank=False`.
- **bank extraction:** fake bank reports (modelType 101/102/103 codes) → bank metrics; corporate-only
  margins `NOT_APPLICABLE`; shared ids resolve via `bank_code`.
- **derived metrics:** correct values; **denominator zero / negative / missing → MISSING/BLOCKED**
  with stable `reason`, value `None` (assert never `inf`/`NaN`).
- **missing-input diagnostics:** drop a required line → metric `MISSING`, reason names the input.
- **generic-label coverage:** fixture with unmapped `item_<code>` lines → `generic_item_count` /
  `unmapped_codes` populated; named count correct.
- **ratios NOT fetched in v1 (B7):** assert `metrics()`/`explain_metric_coverage()` make **zero**
  ratio (`StatementType.RATIOS`) calls and `ratio_status == "not_requested"` for every period.
- **pure transformer (B4):** `_metrics_from_reports(...)` builds correct `MetricReport`s from
  synthetic `FinancialReport`s with **no HTTP** (the primary unit-test seam).
- **full-catalog invariant (B6):** every `MetricReport` contains a `MetricValue` for every v1 metric;
  `get()` returns a value (possibly `NOT_APPLICABLE`/`MISSING`/`BLOCKED`) for any known id.
- **lineage not via `get()` (B8):** a raw_mapped `MetricValue.inputs[0]` carries `value_unit`/code/
  source from the `LineItem` (not just a float).
- **per-statement source / multi-source (C2):** fixture where income+balance resolve to one source
  and cashflow to VNDirect → `MetricReport.statement_sources` records each; a derived metric whose
  inputs span >1 source carries a `mixed_source` warning; assert NO single `source` field exists.
- **unmapped CafeF namespace (C3):** a CafeF-sourced statement (string codes) → its raw_mapped
  metrics are `BLOCKED` with reason `"metric map not available for source 'cafef'"`, **not** MISSING.
- **per-fiscal-date coverage (B1):** multi-period fixture → `MetricCoverage.periods` has one
  `PeriodCoverage` per fiscal_date, each with its own statement_provenance + per_metric.
- **not-applicable:** bank report → `gross_margin` `NOT_APPLICABLE`; corporate → bank-only ids `N/A`.
- **catalog/explain offline:** `metric_catalog()` immutable + filterable; `explain_metric()` returns
  definition with formula/lineage; both make **zero** network calls.
- **batch non-fatal:** a symbol whose fetch raises is caught by the documented loop without aborting.
- **public-API snapshot:** additive only (`metric_catalog`, `explain_metric`, `metrics`,
  `explain_metric_coverage`, the new models/enums) — regenerate baseline, snapshot test green.
- **docs-contract guards** for the new tutorial/how-to references.

---

## 10. Acceptance gate for design review

- [x] Proposed final public API names (§3).
- [x] Data models / enums (§4).
- [x] v1 vs v2 metric list (§6).
- [x] Exact non-goals (§2).
- [x] Test matrix (§9).
- [x] Source / legal statement (§8).
- [x] **rev2:** all 8 review blockers (B1-B8, review-202606201230) resolved in §3/§3.5/§4/§5/§6/§9 (§11).
- [ ] **No implementation code** until the reviewer approves this revised design.

## 11. Blocker resolutions (review-202606201230) + reviewer-answered questions

**B1 — VNDirect-vs-CafeF namespace:** resolved via option 3 (§3.5 C3) — a source whose namespace the
catalog doesn't map yields `BLOCKED`/explicit reason, never silent MISSING. CafeF code map = v1.x (§6).
**B2 — attempts/provenance not exposed:** dropped `source_attempts`; v1 exposes the **succeeding**
source per statement (`StatementProvenance`) + per-`MetricInput.source` lineage; full failed-attempt
trail deferred to a possible `get_financials(..., return_attempts=True)` v2 (§3.5 C1/C2).
**B3 — vague coverage:** replaced loose dict/tuple with frozen typed records `StatementProvenance` /
`PeriodCoverage`; coverage is **per fiscal_date** (§4).
**B4 — signatures/injection:** exact `metrics()`/`explain_metric_coverage()` signatures with
`is_bank/limit/source/sources/http_get/timeout/max_attempts` + private pure `_metrics_from_reports`
transformer for HTTP-free tests (§3, §9).
**B5 — module collision:** implementation module is `metric_api.py`, not `metrics.py` (§3).
**B6 — NOT_APPLICABLE invariant:** every report carries the **full catalog**; applicability via
`availability`, never omission; `get()` returns a value even when unavailable (§5).
**B7 — ratios:** v1 fetches **no** ratios; `ratio_status="not_requested"`; test asserts zero ratio
calls (§5, §9). EPS/BV/provider-native deferred to v2.
**B8 — lineage:** raw mapping indexes `report.items` into a `code -> LineItem` map and builds lineage
from the full `LineItem`, never from `FinancialReport.get()` (float-only) (§5).

**Reviewer-answered open questions (review-202606201230):** Q1 module split — yes, impl `metric_api.py`
(not `metrics.py`). Q2 shared ids — approved for true common concepts + required `is_bank`/`applies_to`/
lineage + id renames (`net_revenue`/`total_liabilities`/`owners_equity`/`cash_end_of_period`) (§6).
Q3 EPS/BV — defer (v2). Q4 `metrics_batch` — not in v1 (docs-only loop). Q5 `to_dataframe` columns —
expanded to `metric_id,name,value,value_unit,kind,availability,reason,category,applies_to,fiscal_date`
(+ `input_codes`/`input_sources` where practical) (§4).

## 12. Remaining question for the reviewer

1. The reviewer mentioned "a clearer end-of-period cash id" — this design uses `cash_end_of_period`
   (VNDirect `35000`). Confirm that id name, or suggest an alternative.
