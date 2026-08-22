# Issue #205 design/source gate — quarterly operating profit and margins

**Status:** `SOURCE_GAP_CLOSURE` / design review requested; no implementation authorization<br>
**Date:** 22 August 2026 (UTC+7)<br>
**Packet:** `/home/hungson175/tools/vnfin-oss-reviewer/tasks/205-quarterly-operating-profit-ratio-spec.md`<br>
**Evidence:** [`docs/research/2026-08-22-quarterly-operating-profit-margin-source-vetting.md`](../docs/research/2026-08-22-quarterly-operating-profit-margin-source-vetting.md)

## 1. Boundary and decision

This round is docs/source design only. It does not add a source, change a parser, add a
template, change the metric catalog, fetch ratios, add a reporter/failover oracle, or claim
SSI/TCX production coverage. The complete 12-cell quarterly matrix is in the research note.

**Decision:** no named `VNDirectFundamentalSource` or `CafeFFundamentalSource` cell meets the
legal + response-identity + template + unit + period-basis gate. Close the source gap rather than
guessing. The official issuer statements prove the securities-company accounting concept but not
the provider mapping or reuse rights.

## 2. Exact operating-profit identity

For a future qualified B02-CTCK(/HN) template, `operating_profit` means exact issuer income row
`70`, not a label-selected provider row:

```text
row 70 = row 20 total operating income/revenue
       + row 50 total financial income
       - row 40 total operating expenses
       - row 60 total financial expenses
       - row 62 general and administrative expenses
```

The identity key is `(source namespace, income statement, provider template/model, entity
scope, cadence, exact source-namespaced item code, currency, flow basis)`. Because the existing
metric is `RAW_MAPPED`, one exact non-empty provider item code is mandatory; a same-report formula
cannot construct or substitute its runtime value. The issuer row-70 formula is cross-check
evidence only. A calculated operating-profit metric would require a separately reviewed metric
kind/API design. The code must be cross-checked for at least two periods and two issuers on the
same template. `14000` remains an explicit negative: it is owners' equity in the balance sheet,
never operating profit. The current catalog's `operating_profit` code remains unset and its
availability remains `BLOCKED`.

## 3. Provisional quarterly lineage requirements for a future reopen

`Period.QUARTER` is one discrete quarter for flow metrics. Fiscal end alone is not enough. The
following is unresolved future-reopen design only, not an implementation contract or current API
authorization. A fresh design must define the enum/export locations, reconcile `template_id` with
existing `FinancialReport.model_type`, make consolidation scope typed rather than free-form, and
specify malformed/mismatch validation plus every parser, `MetricInput`, DataFrame, constructor, and
public-snapshot compatibility seam before TDD.

```python
period_start: date | None = None
period_end: date | None = None
flow_basis: FlowBasis = FlowBasis.UNKNOWN  # quarter_only/year_to_date/trailing/annual/instant/unknown
template_id: FutureTypedTemplate | None = None
consolidation_scope: FutureTypedScope = FutureTypedScope.UNKNOWN
```

Future-reopen invariants are: income and cashflow quarter joins require `period_end == fiscal_date`,
a real start date, and `quarter_only`; balance is `instant`. YTD, trailing, annual, and unknown are
blocked for quarter joins. No adjacent-quarter subtraction is allowed. Gross/net margin inputs must
share the same qualified income report/date/scope/template/basis. Operating-cash-flow margin
additionally requires exact equality of normalized `(period_start, period_end, flow_basis,
consolidation_scope)` across cashflow and income, plus the same normalized symbol, template,
currency, unit, and requested cadence. These fields must eventually propagate into `MetricInput`
lineage and parser invariants before any positive output is enabled; no such change is authorized
by this source-gap packet.

## 4. Metric and API invariants

* Preserve exactly 26 metric IDs and all existing signatures/exports.
* Keep `operating_profit` `RAW_MAPPED` and blocked until a qualified source-specific mapping;
  keep the three margins `DERIVED`.
* Fetch exactly income, balance, and cashflow. `StatementType.RATIOS` calls remain zero and
  `ratio_status=NOT_REQUESTED`.
* Never place CafeF codes into the VNDirect namespace; never infer a template from `is_bank`,
  ticker, label, or a foreign stream. `89`, `90`, and `91` remain independent fail-closed
  negatives. CafeF cashflow remains `NOT_SERVED`.
* Preserve bounded source errors and no-false-absence diagnostics. Empty/failed/identity/basis
  outcomes are not converted into `MISSING` history.
* No VN30/breadth/ranking/screener/universe/investment-rule behavior is in scope.

## 5. Per-input disposition

| Target | Required inputs | Current design disposition |
|---|---|---|
| `operating_profit` | Exact non-empty source-namespaced row-70 item code with source/template/entity/cadence/unit/basis lineage; issuer formula is cross-check only | `BLOCKED` / source gap |
| `gross_margin` | `gross_profit` + `net_revenue`, same qualified income report/date/basis | `BLOCKED`; no `NOT_APPLICABLE` until a fresh design defines an exact typed template-applicability selector |
| `net_margin` | `net_income` + `net_revenue`, same qualified income report/date/basis | `BLOCKED`; #204 net-income source gap remains binding |
| `operating_cash_flow_margin` | `operating_cash_flow` + `net_revenue`, exact normalized `(period_start, period_end, flow_basis, consolidation_scope)` across cashflow/income | `BLOCKED`; CafeF is not served and VNDirect `91` is foreign/unqualified |

No coverage percentage or 18/30 threshold is defined. The caller owns breadth policy.

## 6. Conjunctive reopen gate

Reopen only when the source owner grants runtime/automation/caching/retention/attribution/
redistribution rights; responses prove symbol, statement, template, entity, unit/scale, fiscal
date, and flow basis; VNDirect `89/90/91` are qualified independently; CafeF `H/N/K/QUY/NAM`
semantics and identity are proven; one exact source-namespaced row-70 item code is cross-checked
across two periods and two issuers (the issuer formula is cross-check evidence only); and
deterministic page/retry budgets plus synthetic RED fixtures are reviewed.
Unknown/YTD basis, wrong scope, wrong namespace, `14000`, mixed/redirected identity, and
unserved cashflow must all fail closed. Exact criteria and owner contact paths are in the
[research note](../docs/research/2026-08-22-quarterly-operating-profit-margin-source-vetting.md#8-conjunctive-reopen-criteria).

## 7. Bound packet section 6 RED/release matrix (future qualified reopen only)

This is the complete RED and release contract from the tech-lead packet section 6, bound here so a
future reopen cannot substitute an abbreviated test list. It is not an implementation
authorization for this source-gap closure. All fixtures must be synthetic and offline:

1. Preserve a RED commit in which intended positive cases fail before any production change.
2. Only a later `QUALIFIED FOR TDD` design may enable the positive rows below.

### 7.1 Positive rows

- Exact qualified source/template/cadence/item-code resolution returns `operating_profit` with
  raw-VND value and complete lineage.
- Quarterly gross, net, and operating-cash-flow margins resolve from exact same-period inputs
  and return finite `ratio` values.
- Direct and single-source-chain selections produce identical availability, value, and lineage.
- A bad capable primary fails over to a qualified backup without namespace mixing.

### 7.2 Identity and period negatives

- Same label with wrong code; same code in the wrong source, statement, entity, template/model, or
  cadence; unknown, missing, and malformed model discriminators.
- Disproved `14000`; SSI/TCX foreign-template `89`/`90`/`91` cases unless explicitly qualified
  by a future design; annual response to a quarter request.
- Mismatched and duplicate fiscal dates; all Q1/Q2/Q3/Q4 quarter-end boundaries; newest-first
  ordering and limit behavior.
- Cumulative, year-to-date, trailing, and unknown quarter bases; income/cashflow basis mismatch;
  exact cross-statement interval mismatch, including a different normalized period start.
- Cross-symbol report; wrong consolidated/separate scope; wrong currency, unit, or scale;
  duplicate item code/date; non-finite value; malformed outer report.
- CafeF `H`/`N`/`K`/`QUY`/`NAM` tag boundaries, including `H`/`QUY` accepted individually,
  `N`/`K` rejected for quarterly calls, and `NAM` skipped as annual on a quarterly call;
  query-only symbol identity; missing response identity; zero physical cashflow calls.
- Direct/chain parity for every rejection, with exact bounded public diagnostics and no raw
  source text, URL, exception text, or attempt-trail leakage.

### 7.3 Availability and calculation rows

- For each derived metric: numerator missing, denominator missing, either input blocked,
  statement source error, statement not served, denominator zero, denominator negative,
  denominator non-finite, and valid inputs.
- No fiscal-date cross-join; partial statements still yield typed per-period coverage.
- CafeF cashflow remains `NOT_SERVED` unless a separately qualified capability changes that fact.
- An unmapped source/template is `BLOCKED`, while a qualified-but-absent line is `MISSING`.
- Full `MetricInput` code/source/name/unit/date lineage and any mixed-source warning are exact.
- `metrics()` fail-loud all-empty behavior and non-fatal recoverable-coverage behavior stay
  unchanged.

### 7.4 Calls, API, and release rows

- Exactly zero `StatementType.RATIOS` calls in success, partial, error, direct, and failover
  cases; `ratio_status=NOT_REQUESTED`.
- Normalized and malformed symbol zero-call behavior, source precedence, empty effective chain,
  and capability filtering remain bound.
- Catalog count/IDs/kinds/formulas, public signatures/exports, dataclass construction, DataFrame
  columns/attrs, and API snapshots remain compatible.
- Full suite; focused fundamentals/metrics/failover/docs/public-API tests; `git diff --check`;
  blacklist and secret scans; import/version checks; and isolated sdist/wheel build all pass.

If a future fresh design is `QUALIFIED FOR TDD`, these rows run RED-first and then on the merged
tree. If this design receives source-gap PASS instead, none of these positive rows or TDD steps
run: rerun the merged docs/full/build/blacklist/secret/diff gates, push the exact approved
research/design/backlog anchor, verify remote ancestry and changed paths, post a clean source-gap
resolution, and close/re-read #205. Source-gap PASS never transitions to TDD.

## 8. Next transition

Before an exact-SHA design PASS: docs only, no production code, no push, and no issue close.
At this source-gap disposition, an exact design PASS authorizes only the docs publication/
resolution/close sequence in section 7.4, never TDD. TDD requires all conjunctive reopen evidence
and a fresh `QUALIFIED FOR TDD` design PASS.
