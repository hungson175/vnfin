# Size a position by daily liquidity

`vnfin.liquidity` estimates how marketable a stock is from its **daily** price history and
how large an order your capital implies. Traded value is an **estimate** (`close * volume`),
not a provider-published turnover figure — see the
[design notes](../design/liquidity-position-sizing.md).

## From a price history you already have

```python
import vnfin
from datetime import date

hist = vnfin.prices.history("FPT", date(2025, 1, 1), date(2025, 3, 31))
prof = vnfin.liquidity.from_price_history(hist, adv_fraction=0.10, capital_vnd=1_000_000_000)

print(prof.avg_daily_value_vnd)        # avg estimated daily traded value (VND)
print(prof.max_order_value_vnd)        # 10% of ADV -> a polite max order
print(prof.max_order_as_capital_pct)   # that order as % of a 1B VND book
print(prof.warnings)                   # includes the close*volume estimate warning
```

## One-shot fetch

```python
import vnfin
from datetime import date

prof = vnfin.liquidity.profile("FPT", date(2025, 1, 1), date(2025, 3, 31),
                               adv_fraction=0.10, capital_vnd=1_000_000_000)
```

`profile()` validates/canonicalizes the symbol and dates before any network call. It accepts
only daily VND equity series; index/crypto/non-VND inputs are rejected. A 1B VND book whose
implied max order is a large share of average daily value is a marketability flag for a
long-term allocation.
