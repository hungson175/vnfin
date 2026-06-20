# Tutorial — historical FX (annual USD/VND)

`vnfin.fx.history(...)` gives you a typed **historical** foreign-exchange series, separate from
the spot `vnfin.fx.get_rate(...)`. v1 serves **annual USD/VND** from the no-key World Bank WDI
indicator `PA.NUS.FCRF` ("Official exchange rate, LCU per US$, period average"). For Vietnam this
is **VND per 1 USD** — the same convention as the spot `FXRate.rate`.

> The annual value is an annual **period-average** rate — not a year-end snapshot and not the SBV
> central rate. Use it for long-horizon, year-over-year context, not for a specific trade date.

## Fetch a window

```python
from datetime import date
import vnfin

# Always pass dates as keywords (start=/end=).
h = vnfin.fx.history(start=date(2010, 1, 1), end=date(2024, 12, 31))

print(h.base, h.quote, h.unit)   # USD VND "VND per 1 USD"
print(h.frequency.value)         # "annual"
print(h.source)                  # "worldbank_fx"
print(len(h))                    # number of annual points

latest = h.latest()              # most recent FXPoint, or None
print(latest.date, latest.rate)  # e.g. date(2024, 1, 1) 25000.0
```

`start`/`end` are an inclusive **calendar-year** window: a mid-year `start` still keeps that year's
point (annual points are stamped on Jan 1). Omit a bound for an open-ended side; omit both for the
full available series.

## Exact lookups — no fills, no guessing

```python
h.rate_on(date(2022, 1, 1))   # exact observation -> float
h.rate_for_year(2022)         # sugar over rate_on(date(2022, 1, 1))

h.rate_on(date(2022, 6, 30))  # raises InvalidData — never forward-fills or interpolates
```

This is deliberate: vnfin will not invent an FX rate for a date it does not have. Converting an
asset price series into VND (joining daily prices to annual FX) is **left to you** — vnfin does not
ship a `normalize_to_vnd(...)` helper, so any alignment policy stays explicit and visible.

## DataFrame output

```python
df = h.to_dataframe()   # requires the [pandas] extra
print(df.columns.tolist())   # ["rate"]
print(df.index.name)         # "date"
print(df.attrs["source"])    # "worldbank_fx" (+ base/quote/unit/frequency in attrs)
```

## Check coverage before you call (offline)

```python
d = vnfin.diagnostics.explain_fx_coverage("USD", "VND", date(1970, 1, 1), date(1975, 12, 31))
print(d.status)             # "coverage_gap" — before the known coverage start
print(d.suggested_actions)
```

`explain_fx_coverage` is offline (no network). It reports `unsupported_pair` (anything but
USD/VND in v1), `unsupported_frequency` (anything but annual), `coverage_gap` (window entirely
before the known coverage start), or `ok`. See
[How to explain source coverage](../how-to/source-diagnostics.md).

## Limits (v1)

- **Annual only.** Monthly/daily no-key FX history is not available; monthly (IMF/DBnomics) is a
  future v2 item.
- **USD/VND only.** Non-USD cross-quotes (e.g. EUR/VND) are deferred to v2.
- **Runtime-fetch only**, no bundled provider rows. Provider terms + provenance:
  [World Bank FX history source](../sources/fx-history-worldbank.md).
