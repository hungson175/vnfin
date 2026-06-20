# Tutorial: stock prices

Use this guide for Vietnam equity OHLCV bars.

> **Stocks only.** `vnfin.prices.history()` is for equities. A market-index symbol
> (`VNINDEX`, `VN30`, …) raises `InvalidData` — use
> [`vnfin.indices.index_history()`](funds-and-indices.md) for index points instead.

## Fetch daily history

```python
from datetime import date
import vnfin

hist = vnfin.prices.history("FPT", start=date(2024, 1, 1), end=date(2024, 6, 30))
print(hist.source, hist.value_unit, len(hist.bars))
```

`hist.value_unit` is `VND`. Bars are provider-adjusted by the broker feed; read
`hist.adjustment_policy` when doing backtests.

## Resample to a coarser cadence (weekly/monthly/quarterly/yearly)

Pass `interval` to aggregate the daily series into coarser calendar periods — useful when a
long window (e.g. 10 years) returns thousands of daily rows. Daily (`Interval.D1`, the default)
is unchanged. Accept an `Interval` member **or** a pandas-style alias string
(`'D'`/`'W'`/`'M'`/`'Q'`/`'Y'`, case-insensitive):

```python
# Interval.MN1 == monthly; the alias 'M' ALSO means MONTH (not minute — Interval.M1 is 1 minute).
monthly = vnfin.prices.history("FPT", "M", start=date(2015, 1, 1), end=date(2024, 12, 31))
yearly = vnfin.prices.history("FPT", Interval.Y1, start=date(2015, 1, 1), end=date(2024, 12, 31))
print(len(yearly.bars), yearly.warnings)
```

- Each aggregated bar is full **OHLC** per period (`open`=first, `high`=max, `low`=min,
  `close`=last day's close, `volume`=sum), labelled at the **last actual trading day** in the period.
- **`'M'` = MONTH (`Interval.MN1`), never minute.** Resampling is daily → coarser only:
  intraday (`M1`/`M5`/`M15`/`M30`/`H1`) is rejected (`UnsupportedInterval`).
- The network still fetches the full **daily** range — the win is the returned row count
  (10y → ~10 yearly / ~120 monthly rows), not fewer requests.
- The result self-discloses: `warnings` always contains `resampled_from_d1`, and a
  `resample_partial_period` warning is added when the first/last bar covers an incomplete
  calendar period relative to your window (the partial bars are kept, not dropped).

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
