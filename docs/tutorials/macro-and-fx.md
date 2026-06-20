# Tutorial: macro and FX

Use this guide for Vietnam macro indicators and VND FX reference rates.

## FX rates

FX has two shapes. `vnfin.fx.get_rate()` / `vnfin.fx.client()` return the **spot/current**
rate; `vnfin.fx.history()` returns **annual USD/VND history** (`FXHistory`, World Bank
`PA.NUS.FCRF`, no-key — see [Historical FX](fx-history.md)). Rates are expressed as
**VND per 1 base currency**.

```python
import vnfin

fx = vnfin.fx.client()  # reuse one client for multiple lookups and shared response cache
usd = fx.get_rate("USD")
eur = fx.get_rate("EUR")

print(usd.rate, usd.unit, usd.source)
print(eur.rate, eur.unit, eur.source)
```

Default FX failover is open.er-api → Vietcombank. Both are normalized to VND-per-base.

## Macro indicators

```python
import vnfin
from vnfin.macro import MacroIndicator

gdp = vnfin.macro.get_indicator("VNM", MacroIndicator.GDP)
cpi = vnfin.macro.get_indicator("VNM", MacroIndicator.CPI)

print(gdp.unit, gdp.latest())
print(cpi.unit, cpi.latest())
```

The no-key macro chain is World Bank → IMF DataMapper → DBnomics. Indicator units differ; read
`series.unit` and `series.currency`.

## Optional FRED key

FRED is opt-in and excluded from the no-key default chain. See [Use FRED BYOK](../how-to/byok-fred.md).

## Related reference

- [FX source notes](../sources/fx-open-er-api.md) and [Vietcombank notes](../sources/fx-vietcombank.md)
- [Macro no-key + BYOK design](../design/macro-no-key-byok.md)
- [Units](../units.md)
