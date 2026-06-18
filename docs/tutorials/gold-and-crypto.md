# Tutorial: gold and crypto

Use this guide for domestic Vietnam gold, world gold, and major crypto OHLCV.

## Vietnam domestic gold

Vietnam domestic gold is spot-only and normalized to **VND/lượng**.

```python
import vnfin

quotes = vnfin.gold.vn("btmc").get_quotes()
for q in quotes[:10]:
    print(q.name, q.buy, q.sell, q.unit, q.source)
```

You can choose `"btmc"` or `"pnj"`. There is no cross-unit gold `client()` because Vietnam domestic
gold and world XAU are different markets and units.

## World gold

```python
from datetime import date
import vnfin

world = vnfin.gold.world()
hist = world.get_history(date(2024, 1, 1), date(2024, 6, 30))
print(hist.unit, hist.bars[-1].close)  # USD/oz
```

## Crypto OHLCV

```python
from datetime import date
import vnfin
from vnfin import Interval

btc = vnfin.crypto.client().get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 6, 30))
print(btc.source, btc.value_unit, btc.bars[-1].close)
```

Crypto data is USD-denominated. The default failover is Binance → Coinbase.

## Related reference

- [Gold source notes](../sources/gold-adapters.md)
- [Crypto source notes](../sources/crypto-binance.md) and [Coinbase notes](../sources/crypto-coinbase.md)
- [Units](../units.md)
