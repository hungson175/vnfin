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
# holdings merges equities and bonds; each row is tagged with instrument_type
# ("STOCK"/"BOND") and an optional as_of_utc freshness stamp. A pure-bond fund
# returns its bond positions (it no longer raises EmptyData).
for h in holdings[:10]:
    print(h.stock_code, h.weight_pct, h.instrument_type)  # FundHolding fields

# The top-level asset-class split (equity/bond/cash) is a separate accessor:
alloc = fund_src.asset_allocation(first.id)   # AssetAllocation
for c in alloc:
    print(c.asset_class, c.weight_pct)        # AssetClassWeight: asset_class, weight_pct
print(alloc.as_of_utc)                        # freshest provider updateAt, or None
```

## Index levels

> **Indices only.** `index_history()` accepts recognised market indices (`VNINDEX`, `VN30`,
> `HNXINDEX`, `HNX30`, `UPCOM`, `VNALLSHARE`). A stock symbol (e.g. `FPT`) raises `InvalidData` —
> use [`vnfin.prices.history()`](stock-prices.md) for equity prices instead.

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
