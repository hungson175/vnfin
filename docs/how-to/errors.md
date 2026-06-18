# How to handle errors and failover

All public exceptions inherit from `vnfin.exceptions.VnfinError`.

```python
from datetime import date
import vnfin
from vnfin.exceptions import VnfinError

try:
    hist = vnfin.prices.history("FPT", date(2024, 1, 1), date(2024, 6, 30))
except VnfinError as exc:
    print(f"data unavailable or invalid: {exc}")
```

Common exception types:

| Exception | Meaning |
|-----------|---------|
| `SourceUnavailable` | Provider/network/source-specific failure; failover clients can try the next source. |
| `EmptyData` | Provider returned no usable rows for the request. |
| `InvalidData` | Input or provider payload is malformed. |
| `UnsupportedInterval` | Requested interval is not supported by any eligible source. |
| `UnitMismatchError` | Failover would mix incompatible units/scales, so the result is rejected. |
| `AllSourcesFailed` | Every source in a failover chain failed or was rejected. |

For normal applications, catch `VnfinError`; for diagnostics, inspect `AllSourcesFailed.attempts`
when present to see per-source reasons.
