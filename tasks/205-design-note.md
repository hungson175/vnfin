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
scope, cadence, exact code/formula, currency, flow basis)`. It must be cross-checked for at least
two periods and two issuers on the same template. `14000` remains an explicit negative: it is
owners' equity in the balance sheet, never operating profit. The current catalog's
`operating_profit` code remains unset and its availability remains `BLOCKED`.

## 3. Quarterly lineage contract for a future implementation

`Period.QUARTER` is one discrete quarter for flow metrics. Fiscal end alone is not enough. The
additive, defaulted lineage fields proposed after existing `FinancialReport`/`MetricInput`
fields are:

```python
period_start: date | None = None
period_end: date | None = None
flow_basis: FlowBasis = FlowBasis.UNKNOWN  # quarter_only/year_to_date/trailing/annual/instant/unknown
template_id: str | None = None
consolidation_scope: str = "unknown"  # consolidated/separate/unknown
```

Income and cashflow quarter joins require `period_end == fiscal_date`, a real start date, and
`quarter_only`; balance is `instant`. YTD, trailing, annual, and unknown are blocked for quarter
joins. No adjacent-quarter subtraction is allowed. Gross/net margin inputs must share the same
qualified income report/date/scope/template/basis; operating-cash-flow margin additionally needs
the same qualified discrete basis across cashflow and income. These fields must propagate into
`MetricInput` lineage and parser invariants before any positive output is enabled.

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
| `operating_profit` | Exact row-70 code/formula with source/template/entity/cadence/unit/basis lineage | `BLOCKED` / source gap |
| `gross_margin` | `gross_profit` + `net_revenue`, same qualified income report/date/basis | `BLOCKED`; a proven B02-CTCK template may classify absent generic gross profit as `NOT_APPLICABLE` |
| `net_margin` | `net_income` + `net_revenue`, same qualified income report/date/basis | `BLOCKED`; #204 net-income source gap remains binding |
| `operating_cash_flow_margin` | `operating_cash_flow` + `net_revenue`, same qualified discrete basis | `BLOCKED`; CafeF is not served and VNDirect `91` is foreign/unqualified |

No coverage percentage or 18/30 threshold is defined. The caller owns breadth policy.

## 6. Conjunctive reopen gate

Reopen only when the source owner grants runtime/automation/caching/retention/attribution/
redistribution rights; responses prove symbol, statement, template, entity, unit/scale, fiscal
date, and flow basis; VNDirect `89/90/91` are qualified independently; CafeF `H/N/K/QUY/NAM`
semantics and identity are proven; row 70/code/formula is cross-checked across two periods and
two issuers; and deterministic page/retry budgets plus synthetic RED fixtures are reviewed.
Unknown/YTD basis, wrong scope, wrong namespace, `14000`, mixed/redirected identity, and
unserved cashflow must all fail closed. Exact criteria and owner contact paths are in the
[research note](../docs/research/2026-08-22-quarterly-operating-profit-margin-source-vetting.md#8-conjunctive-reopen-criteria).

## 7. Next transition

After exact-SHA design PASS only, begin TDD with failing synthetic fixtures first. The future RED
matrix must include direct/chain parity, zero ratio calls, all `89/90/91` negatives, `14000`,
CafeF `K/H/QUY` boundaries, discrete-vs-YTD mismatch, unit/scope/template mismatch, derived
input statuses, and zero physical CafeF cashflow calls. Until then: docs only, no production
code, no push, and no issue close.
