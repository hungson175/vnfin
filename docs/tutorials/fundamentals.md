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

## Related reference

- [Units](../units.md#cross-source-differential-testing)
- [VNDirect source notes](../sources/fundamentals-vndirect.md)
- [CafeF source notes](../sources/fundamentals-cafef.md)
