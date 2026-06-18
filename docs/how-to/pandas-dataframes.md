# How to use pandas DataFrames

Install the pandas extra:

```bash
pip install "vnfin[pandas] @ git+https://github.com/hungson175/vnfin.git"
```

Time-series result objects expose `.to_dataframe()`:

```python
from datetime import date
import vnfin

hist = vnfin.prices.history("FPT", date(2024, 1, 1), date(2024, 6, 30))
df = hist.to_dataframe()

print(df.tail())
print(df.attrs)
```

`df.attrs` carries provenance and unit metadata such as source, symbol, unit, currency, and interval.
Keep those attributes when saving derived data so you do not lose unit context.

Financial reports also support `.to_dataframe()` per report:

```python
report = vnfin.fundamentals.get_financials("FPT", "income", "annual")[0]
df = report.to_dataframe()
print(df[["item_code", "name", "value", "value_unit"]].head())
print(df.attrs)
```
