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
    print(h.stock_code, h.weight_pct)  # FundHolding: stock_code, weight_pct (0-100)
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

For a **long multi-year** window (e.g. a 10-year VNINDEX backtest) where a single source has one
bad day somewhere in the range, use the opt-in stitcher — it fetches each calendar year via the
failover chain (routing around each source's bad day) and stitches the years into one series:

```python
hist = vnfin.indices.index_history_stitched("VNINDEX", date(2016, 1, 1), date(2026, 6, 1))
print(hist.source)        # "stitched_index_history"
print(hist.warnings)      # one "segment <year>: <source> (<n> bars)" provenance line per year
```

The default `index_history` stays strict (it fails closed on a bad row); `index_history_stitched`
is the explicit, multi-source-provenance opt-in (D1 only).

## Constituents

```python
members = vnfin.indices.index_constituents("VN30")
for m in members.members[:10]:            # IndexConstituents.members -> tuple[IndexMember]
    print(m.symbol, m.exchange)           # this endpoint exposes membership only (no weights)
```

## Related reference

- [Units](../units.md)
- [Indices source notes](../sources/indices-constituents.md)
- [Funds source notes](../sources/funds-fmarket.md)
