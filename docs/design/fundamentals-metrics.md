# Design — fundamentals metrics & coverage diagnostics (#157)

**Status:** DESIGN — reviewer gate (must be APPROVED before any metrics code).
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
- **Coverage diagnostics**: missing/unmapped/blocked per metric; named-vs-generic item-label stats;
  statement vs ratio source failures; not-applicable per bank/non-bank; failover source attempts.
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

### Proposed final names (refining the spec)

`metric_catalog`, `explain_metric`, `metrics`, `explain_metric_coverage` — kept as the spec
proposed (they read well and mirror the `diagnostics.explain_*` family). `screen(...)` is **not**
added in v1 (non-goal); batch coverage is served by calling `explain_metric_coverage` per symbol
(see §5 batch).

---

## 4. Data model (new, in `vnfin/fundamentals/metric_models.py`)

```python
class MetricId(str, Enum):           # stable canonical ids, e.g. "net_income", "gross_margin"
    REVENUE = "revenue"; GROSS_PROFIT = "gross_profit"; ...   # full list in §6

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
    formula: Optional[str] = None            # human formula for derived, e.g. "gross_profit / revenue"
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
class MetricReport:                  # all metrics for one symbol + one fiscal period
    symbol: str
    period: Period
    fiscal_date: date
    is_bank: bool
    metrics: tuple[MetricValue, ...]
    source: str
    warnings: tuple[str, ...] = ()
    def get(self, metric_id) -> Optional[MetricValue]: ...
    def to_dataframe(self) -> "pd.DataFrame": ...   # one row per metric (id/value/unit/kind/availability)

@dataclass(frozen=True)
class MetricCoverage:               # offline-friendly diagnosis for a symbol+period
    symbol: str
    period: Period
    is_bank: Optional[bool]                 # None if undetermined
    per_metric: tuple[tuple[MetricId, MetricAvailability, Optional[str]], ...]
    named_item_count: int                   # LineItems with a real name
    generic_item_count: int                 # LineItems still "item_<code>"
    unmapped_codes: tuple[str, ...]         # codes present but not in itemcodes/metric map
    statement_status: dict                  # {StatementType: "ok"|"missing"|"source_error"}
    ratio_status: str                       # separate from statement failures
    source_attempts: tuple[str, ...]        # failover provenance
    notes: tuple[str, ...] = ()
```

`MetricReport` reuses the same `to_dataframe()` convention (metadata in `df.attrs`). It does **not**
need `TimeSeriesResult` (it is one period; the *tuple* of reports is the series — callers concat).

---

## 5. Behavior

### Extraction (`metrics`)

1. Resolve bank vs corporate via the existing `is_bank` AUTO detection in `get_financials`.
2. Fetch income+balance+cashflow `FinancialReport`s (newest-first, shared `limit`).
3. Align reports by `fiscal_date` → one `MetricReport` per period.
4. For each `MetricDefinition` whose `applies_to` matches the entity type:
   - **raw_mapped:** read `report.get(corporate_code or bank_code)`; unit from the line.
   - **derived:** compute `formula` from already-resolved `MetricValue`s with **guards** —
     denominator zero/negative/missing → `availability=MISSING`/`BLOCKED` with a stable `reason`,
     value `None` (never `inf`/`NaN`, never a silent wrong number).
   - metric not applicable to this entity → `NOT_APPLICABLE` (e.g. `gross_margin` for a bank).
   - input statement missing/failed → `MISSING` with reason naming the input.
5. Carry failover `warnings` + `source` onto the report.

### Coverage (`explain_metric_coverage`)

Same fetch, but never raises on a per-statement failure — it records `statement_status` /
`ratio_status` (statement vs ratio failures **separately**, per spec), counts named-vs-generic item
labels, lists unmapped codes, and reports each metric's availability + reason. Designed so a caller
can loop over a universe of symbols catching nothing and get a per-symbol `MetricCoverage`.

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

| MetricId | code | category |
|----------|------|----------|
| revenue | 11000 | size/profitability |
| gross_profit | 11200 | profitability |
| operating_profit | 14000 | profitability |
| profit_before_tax | 20000 | profitability |
| net_income | 21000 | profitability |
| net_income_parent | 21100 | profitability |
| cash_and_equivalents | 23100 | liquidity |
| current_assets | 23000 | liquidity |
| total_assets | 25000 | size |
| liabilities | 30000 | leverage |
| current_liabilities | 30100 | leverage |
| long_term_liabilities | 30200 | leverage |
| equity | 40000 | size |
| operating_cash_flow | 31000 | cashflow |
| investing_cash_flow | 32000 | cashflow |
| financing_cash_flow | 33000 | cashflow |
| net_cash_flow | 34000 | cashflow |
| cash_end | 35000 | cashflow |

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
| liabilities (bank) | 414000 | leverage |
| equity (bank) | 415000 | size |
| operating_cash_flow (bank) | 431000 | cashflow |
| investing_cash_flow (bank) | 432000 | cashflow |
| financing_cash_flow (bank) | 433000 | cashflow |

> `profit_before_tax`, `net_income`, `total_assets`, `liabilities`, `equity`, and the cashflow trio
> are **shared canonical ids** with **different underlying codes per entity type** (one `MetricId`,
> `corporate_code` + `bank_code` on the definition). `applies_to=BOTH` for those; corporate-only
> margins are `applies_to=CORPORATE`; bank-specific lines are `applies_to=BANK`.

### v1 — derived (formula-backed, guarded)

| MetricId | formula | applies_to | unit |
|----------|---------|------------|------|
| gross_margin | gross_profit / revenue | CORPORATE | ratio |
| net_margin | net_income / revenue | CORPORATE | ratio |
| liabilities_to_equity | liabilities / equity | BOTH | ratio |
| cash_to_assets | cash_and_equivalents / total_assets | CORPORATE | ratio |
| operating_cash_flow_margin | operating_cash_flow / revenue | CORPORATE | ratio |

(For banks, revenue-based margins are `NOT_APPLICABLE`; `liabilities_to_equity` uses the bank codes.)

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
| statement availability by source/type/period/fiscal_date | `MetricCoverage.statement_status` + per-period reports |
| ratio failures separate from statement failures | `MetricCoverage.ratio_status` (distinct field) |
| item-label coverage: named vs generic + unmapped codes | `named_item_count` / `generic_item_count` / `unmapped_codes` |
| missing inputs per metric with stable reason | `MetricValue.reason` + `MetricCoverage.per_metric` |
| not-applicable for bank vs non-bank | `MetricAvailability.NOT_APPLICABLE` via `applies_to` |
| source attempts + failover warnings | `MetricCoverage.source_attempts` + `MetricReport.warnings` |
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
- **ratio source failure shown as non-fatal coverage issue:** ratios fetch fails → `ratio_status`
  reflects it while statements still produce metrics (statement vs ratio isolation).
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
- [ ] **No implementation code** until the reviewer approves this design.

## 11. Open questions for the reviewer

1. **Module split:** `vnfin/fundamentals/metric_models.py` (dataclasses/enums) +
   `vnfin/fundamentals/metrics.py` (catalog + extraction + coverage), facade verbs re-exported from
   `vnfin/fundamentals/__init__.py`. OK? (I lean yes — mirrors fx history/diagnostics split.)
2. **Shared-id vs split-id:** model `net_income`/`profit_before_tax`/`total_assets`/`liabilities`/
   `equity`/cashflow as **one canonical `MetricId` with both `corporate_code` and `bank_code`** (my
   lean), or as separate bank ids? Shared ids make cross-entity series cleaner but require the
   taxonomy metadata to prevent silent mixing (which `applies_to` + `is_bank` on the report provide).
3. **EPS/BV in v1.x:** include `provider_native` EPS/book_value_per_share from the `ratios` statement
   now (with verified `vnd_per_share` unit), or defer to v2 with valuation? (I lean defer — keep v1
   to statements + derived, avoid the ratios-unit verification in this slice.)
4. **`metrics_batch` helper:** ship a thin non-ranking `metrics_batch(symbols, ...)` in v1, or keep
   batch as a docs-only loop over `explain_metric_coverage`? (I lean docs-only loop for v1 to stay
   clearly on the data-primitive side of the advice/screener line.)
5. **`MetricReport.to_dataframe()`** column set — confirm `(metric_id, value, value_unit, kind,
   availability, reason)` is the right shape.
