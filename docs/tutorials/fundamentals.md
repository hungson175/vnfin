# Tutorial: fundamentals

Use this guide for financial statements and ratios.

## Fetch annual income statements

```python
import vnfin
from vnfin.fundamentals import StatementType, Period

reports = vnfin.fundamentals.get_financials("FPT", StatementType.INCOME, Period.ANNUAL)
latest = reports[0]

print(latest.symbol, latest.fiscal_date, latest.source)
print(latest.currency)  # VND
```

## Read line items

`FinancialReport.items` is a tuple of line items. Provider item codes are stable identifiers; names
are best-effort labels.

```python
for item in latest.items[:10]:
    print(item.item_code, item.name, item.value, item.value_unit)

# If you know a provider code, use .get(). Returns None when absent.
print(latest.get("11000"))
```

Money statement values are normalized to **raw VND**. CafeF raw values are scaled when necessary so
failover does not mix thousand-VND with raw VND. Ratios are not scaled.

## Ratios

```python
ratios = vnfin.fundamentals.get_financials("FPT", "ratios", "annual")
for item in ratios[0].items[:10]:
    print(item.name, item.value, item.value_unit)  # ratio or vnd_per_share
```

## Bank vs non-bank templates

`is_bank` can be set explicitly when you know the issuer type. The default `AUTO` path is intended
for normal use.

```python
reports = vnfin.fundamentals.get_financials("VCB", "income", "annual", is_bank=True)
```

## Canonical metrics & coverage

`get_financials(...)` above returns the raw provider line items keyed by opaque provider codes
(e.g. `"11000"`). For analysis you usually want **stable, named, cross-statement metrics** instead.
`vnfin.fundamentals.metrics(...)` is an additive, OFFLINE transform on top of those reports: it
fetches income + balance + cashflow once each, then maps the verified provider codes to a fixed
**v1 catalog of 26 canonical metrics** — 21 raw-mapped line items plus 5 derived ratios — one
`MetricReport` per fiscal period (newest first).

```python
import vnfin

reports = vnfin.fundamentals.metrics("FPT", period="annual")  # tuple[MetricReport], newest first
rep = reports[0]
print(rep.symbol, rep.fiscal_date, rep.is_bank)

nr = rep.get("net_revenue")            # a MetricValue, even when unavailable
print(nr.value, nr.value_unit, nr.kind.value, nr.availability.value)  # ... 'VND' 'raw_mapped' 'available'

gm = rep.get("gross_margin")           # a DERIVED ratio (gross_profit / net_revenue)
print(gm.value, gm.value_unit)         # 0.31... 'ratio'

df = rep.to_dataframe()                # one row per metric (all 26)
```

### Availability vs omission

Every `MetricReport` carries a `MetricValue` for **all 26 catalog metrics every period** —
applicability and gaps are expressed by `MetricValue.availability`, never by omitting a metric. When
`availability != "available"`, `value` is `None` and `reason` carries a stable diagnostic string:

- `available` — resolved; `value` is set.
- `missing` — the line item / statement is absent for this period (e.g. `"missing line item 11000 in income"`).
- `blocked` — the succeeding source's namespace is not mapped in v1 (see below).
- `not_applicable` — the metric does not apply to this entity type (e.g. a bank-only metric on a corporate, or vice-versa: `"metric 'net_revenue' does not apply to bank entities"`).

```python
nii = rep.get("net_interest_income")   # bank-only metric on a corporate symbol
print(nii.availability.value, nii.reason)
# not_applicable  metric 'net_interest_income' does not apply to non-bank entities
```

### Source-namespace BLOCKED (v1 maps VNDirect only)

The v1 catalog maps only the **VNDirect** code namespace. The failover chain may still serve a
statement from CafeF — when it does, those metrics come back `blocked` (not `missing`): the data is
there, but v1 has no CafeF code map yet.

```python
nr = rep.get("net_revenue")
# if income resolved from CafeF:
# nr.availability.value == "blocked"
# nr.reason == "metric map not available for source 'cafef'"
```

Provenance is **per statement**, not per report (income/balance/cashflow can resolve to different
sources — cashflow is VNDirect-only): read `rep.statement_sources`, and per-value lineage on
`MetricValue.inputs[].source`. There is deliberately no single `rep.source`.

### Bank metrics — verified codes only

Bank symbols resolve via the bank code (VNDirect modelType 101/102/103). v1 ships **only the
#157-verified bank anchors**: `net_interest_income`, `loans_to_customers`, `customer_deposits`, plus
the shared metrics (`profit_before_tax`, `net_income`, `total_assets`, `total_liabilities`,
`owners_equity`, `liabilities_to_equity`). Unverified bank line items are deliberately NOT mapped in
v1 rather than guessed.

```python
reports = vnfin.fundamentals.metrics("VCB", period="annual")  # is_bank auto-detected
rep = reports[0]
print(rep.is_bank)                                 # True
print(rep.get("net_interest_income").value)        # bank-only metric, resolved via bank_code
print(rep.get("total_assets").value)               # shared metric, resolved via bank_code
print(rep.get("net_revenue").availability.value)   # 'not_applicable' (corporate-only)
```

### Ratios deferred to v2

The metrics layer **never fetches the `ratios` statement** — every `PeriodCoverage.ratio_status` is
`not_requested`. The 5 v1 derived ratios are computed in-library from the raw metrics with explicit
denominator guards (zero / negative / non-finite denominators yield `missing`, never `inf`/`NaN`).
Provider-native valuation ratios (P/E, P/B, ROE, ROA, EPS, book value, FCF, …) are **deferred to
v2** and are not in the v1 catalog (`explain_metric("roe")` raises `VnfinError`).

### Browse the catalog (offline)

`metric_catalog(...)` and `explain_metric(...)` are pure, network-free lookups:

```python
from vnfin.fundamentals import metric_catalog, explain_metric

for d in metric_catalog():                 # all 26; or metric_catalog("bank") / ("corporate")
    print(d.id.value, d.kind.value, d.applies_to.value, d.category.value)

d = explain_metric("liabilities_to_equity")
print(d.formula, [i.value for i in d.inputs])   # 'total_liabilities / owners_equity' [...]
```

### Coverage diagnostics (non-fatal)

For a per-symbol audit that never raises (ideal for a loop over a universe), use
`explain_metric_coverage(...)`. It runs the same 3-statement fetch but catches every per-statement
failure and returns a `MetricCoverage` with one `PeriodCoverage` per fiscal date — each carrying
per-statement provenance, per-metric availability + reasons, named-vs-generic item counts, and
unmapped provider codes.

```python
cov = vnfin.fundamentals.explain_metric_coverage("FPT", period="annual")
for pc in cov.periods:
    print(pc.fiscal_date, pc.named_item_count, pc.generic_item_count, pc.unmapped_codes)
df = cov.to_dataframe()   # one row per (fiscal_date, metric)
```

## Related reference

- [Units](../units.md#cross-source-differential-testing)
- [VNDirect source notes](../sources/fundamentals-vndirect.md)
- [CafeF source notes](../sources/fundamentals-cafef.md)
