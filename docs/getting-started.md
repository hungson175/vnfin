# Getting started with vnfin

This guide takes you from install to your first data pulls. It assumes Python 3.10+.

## 1. Install

Core install:

```bash
pip install git+https://github.com/hungson175/vnfin.git
```

Install with pandas support:

```bash
pip install "vnfin[pandas] @ git+https://github.com/hungson175/vnfin.git"
```

Verify the import:

```python
import vnfin
print(vnfin.__version__)
```

## 2. The mental model

Most domains have two entry points:

```python
vnfin.<domain>.client()  # recommended failover client
vnfin.<domain>.source()  # primary single-source adapter
```

Use `client()` for normal analysis. Use `source()` only when you intentionally want one provider.
`gold` is different: use `vnfin.gold.vn()` for Vietnam domestic gold and `vnfin.gold.world()` for
world XAU because their units are different.

Every returned object carries its unit and source. Read those fields before comparing numbers.

## 3. First stock price history

```python
from datetime import date
import vnfin

hist = vnfin.prices.history("FPT", date(2024, 1, 1), date(2024, 6, 30))

print(hist.symbol)       # FPT
print(hist.source)       # provider that served the data, e.g. ssi
print(hist.value_unit)   # VND
print(len(hist.bars))
print(hist.bars[-1].close)
```

Daily history requires `start` and `end`. Missing or invalid dates raise a `vnfin` exception before
network I/O.

## 4. First financial statement

```python
import vnfin
from vnfin.fundamentals import StatementType, Period

reports = vnfin.fundamentals.get_financials(
    "FPT",
    StatementType.INCOME,
    Period.ANNUAL,
)
latest = reports[0]

print(latest.fiscal_date)
print(latest.currency)       # VND for money statements
for item in latest.items[:5]:
    print(item.item_code, item.name, item.value, item.value_unit)
```

Statement money is normalized to **raw VND**. Ratio reports use per-line units such as `ratio` or
`vnd_per_share`.

## 5. First FX and macro data

```python
import vnfin

# FX: VND per one unit of the base currency.
fx = vnfin.fx.client()
print(fx.get_rate("USD").rate)
print(fx.get_rate("EUR").rate)

# Macro: indicator series with an indicator-specific unit.
gdp = vnfin.macro.get_indicator("VNM", vnfin.macro.MacroIndicator.GDP)
print(gdp.unit)
print(gdp.latest())
```

No key is needed. Optional FRED support is covered in [Use FRED BYOK](how-to/byok-fred.md).

## 6. Convert to pandas

Install the pandas extra, then call `.to_dataframe()` on time-series results:

```python
df = hist.to_dataframe()
print(df.tail())
print(df.attrs)  # symbol, source, unit, currency, etc.
```

See [Use pandas DataFrames](how-to/pandas-dataframes.md) for per-domain examples.

## 7. Handle errors

Catch `VnfinError` for application-level handling:

```python
from vnfin.exceptions import VnfinError

try:
    hist = vnfin.prices.history("FPT", date(2024, 1, 1), date(2024, 6, 30))
except VnfinError as exc:
    print(f"vnfin could not fetch data: {exc}")
```

For more detail, see [Handle errors and failover](how-to/errors.md).

## What to read next

- [Stock prices tutorial](tutorials/stock-prices.md)
- [Fundamentals tutorial](tutorials/fundamentals.md)
- [Macro and FX tutorial](tutorials/macro-and-fx.md)
- [Units reference](units.md)
