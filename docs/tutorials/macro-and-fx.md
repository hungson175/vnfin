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

### Monthly inflation (CPI YoY) and the policy rate

`CPI_YOY` (consumer-price inflation, % vs the same month a year earlier) and `POLICY_RATE`
(the monetary-policy rate, % per annum) are **monthly** series. Both are served **only** by the
DBnomics/IMF-IFS source, so each resolves to a single-source monthly chain — distinct from the
annual World Bank `CPI` (index level) and `INFLATION` (annual %).

```python
cpi_yoy = vnfin.macro.get_indicator("VNM", MacroIndicator.CPI_YOY)
policy = vnfin.macro.get_indicator("VNM", MacroIndicator.POLICY_RATE)

print(cpi_yoy.unit, cpi_yoy.latest())   # '%' , e.g. ~3.0
print(policy.unit, policy.latest())     # '% per annum', e.g. ~4.5
print(policy.indicator_name)            # honest proxy disclosure (see below)
for w in policy.warnings:
    print("warning:", w)
```

Honest-disclosure caveats — read these before relying on the values:

- **`POLICY_RATE` is a proxy, not the announced rate.** The series is IMF/IFS `FPOLM_PA`, a
  monetary-policy-related rate; `indicator_name` says so explicitly
  (`"Policy Rate (SBV refinancing-rate proxy, IMF IFS FPOLM_PA)"`). For the *official* announced
  refinancing/discount rate, consult the State Bank of Vietnam directly: <https://sbv.gov.vn>.
- **`CPI_YOY` source authority.** The headline monthly CPI is published by the General Statistics
  Office: <https://gso.gov.vn>. The DBnomics figure is the IMF/IFS re-publication.
- **Publication lag + staleness warning.** IMF/IFS routinely lags the source authority by ~2–6
  months. When the latest observation is far enough past the series' own cadence to suggest a
  delayed or discontinued feed, the result carries a `series_end_gap` entry in `series.warnings`
  (the values are kept, never dropped). Always check `series.warnings` and `series.points[-1][0]`
  (the latest observation date) for monthly series.

## Optional FRED key

FRED is opt-in and excluded from the no-key default chain. See [Use FRED BYOK](../how-to/byok-fred.md).

## Related reference

- [FX source notes](../sources/fx-open-er-api.md) and [Vietcombank notes](../sources/fx-vietcombank.md)
- [Macro no-key + BYOK design](../design/macro-no-key-byok.md)
- [Units](../units.md)
