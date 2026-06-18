# Tutorial: funds and indices

Use this guide for open-ended mutual funds, NAV, index levels, and constituents.

## List funds

```python
import vnfin

fund_src = vnfin.funds.source()
funds = fund_src.list_funds(asset_type="STOCK")

for fund in funds.funds[:10]:
    print(fund.id, fund.name, fund.short_name)
```

Funds are currently single-source via Fmarket. Values are VND per fund unit.

## NAV history and holdings

```python
first = funds.funds[0]
nav = fund_src.nav_history(first.id)
holdings = fund_src.holdings(first.id)

print(nav.value_unit, nav.points[-1])
for h in holdings[:10]:
    print(h.symbol, h.weight)
```

## Index levels

```python
from datetime import date
import vnfin

vni = vnfin.indices.index_history("VNINDEX", date(2024, 1, 1), date(2024, 6, 30))
print(vni.source, vni.value_unit, vni.bars[-1].close)  # points, not VND
```

Index levels use the same bar shape as prices but the unit is `points`. Do not compare index values
as money.

## Constituents

```python
members = vnfin.indices.index_constituents("VN30")
for m in members.constituents[:10]:
    print(m.symbol, m.weight)
```

## Related reference

- [Units](../units.md)
- [Indices source notes](../sources/indices-constituents.md)
- [Funds source notes](../sources/funds-fmarket.md)
