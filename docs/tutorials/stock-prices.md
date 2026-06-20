# Tutorial: stock prices

Use this guide for Vietnam equity OHLCV bars.

## Fetch daily history

```python
from datetime import date
import vnfin

hist = vnfin.prices.history("FPT", start=date(2024, 1, 1), end=date(2024, 6, 30))
print(hist.source, hist.value_unit, len(hist.bars))
```

`hist.value_unit` is `VND`. Bars are provider-adjusted by the broker feed; read
`hist.adjustment_policy` when doing backtests.

## Reuse the failover client

```python
from datetime import date
import vnfin

client = vnfin.prices.client()
for symbol in ["FPT", "VNM", "VCB"]:
    hist = client.get_history(symbol, date(2024, 1, 1), date(2024, 6, 30))
    print(symbol, hist.source, hist.bars[-1].close)
```

The default chain is SSI → VNDirect → VPS → Pinetree. KIS exists as a source adapter but is excluded
from the default chain because its adjustment policy is mixed.

## Convert to pandas

```python
df = hist.to_dataframe()
print(df[["open", "high", "low", "close", "volume"]].tail())
print(df.attrs["source"], df.attrs["value_unit"])
```

Install with `vnfin[pandas]` first.

## Intraday notes

Daily (`Interval.D1`) is the guaranteed common denominator. Intraday intervals are best-effort and
retention differs by provider. For durable workflows, design around daily data unless you have live
checks for the specific source and interval.

## Related reference

- [Public API](../api.md)
- [Units](../units.md)
- [Source notes](../sources/)
