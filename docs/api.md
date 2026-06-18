# Public API — coherent facade + naming standard (P1.4)

`vnfin` exposes **one obvious entry per domain**. Each domain owns its typed models and
units (see [units.md](units.md)); they are **not** funnelled through a single client that
would otherwise have to return incompatible result types behind one surface. Instead,
after `import vnfin` you reach each domain as an attribute:

```python
import vnfin

vnfin.prices        # equity OHLCV price history (VND)
vnfin.fundamentals  # financial statements (raw VND)
vnfin.funds         # mutual-fund NAV (VND / fund unit)
vnfin.indices       # index value (points) + constituents
vnfin.gold          # gold spot / history (VN domestic + world XAU)
vnfin.crypto        # crypto OHLCV (USD)
vnfin.macro         # macroeconomic indicators
```

## Naming standard

Every domain offers the standard **factory verbs** so the entry is predictable:

| Verb | Meaning |
|------|---------|
| `client(...)` | Build the primary domain client/source object (the obvious entry). |
| `source(...)` | The primary single-source adapter. For single-source domains, `client` is an alias of `source`. |
| `history(...)` / `index_history(...)` / `get_financials(...)` | Domain-specific one-shot convenience functions (kept where they already existed). |

All factories accept the shared transport kwargs `http_get=None` (injectable for tests)
and `timeout=25.0`; price/index clients also accept `max_attempts`.

## Per-domain entry points

```python
# prices — equity OHLCV (VND). Failover over the default broker chain.
# start/end dates are REQUIRED; omitting them raises vnfin.exceptions.InvalidData.
from datetime import date
c    = vnfin.prices.client()                 # FailoverPriceClient
hist = vnfin.prices.history("FAKECORP", start=date(2024, 1, 1), end=date(2024, 6, 30))   # one-shot PriceHistory
hist = vnfin.default_client().get_history("FAKECORP", start=date(2024, 1, 1), end=date(2024, 6, 30))  # long-standing equivalent

# fundamentals — financial statements (raw VND).
src     = vnfin.fundamentals.client()        # == .source(), VNDirectFundamentalSource
reports = vnfin.fundamentals.get_financials("FAKECORP", "income", "annual")

# funds — mutual-fund NAV (VND/unit).
src   = vnfin.funds.client()                 # == .source(), FmarketFundSource
funds = src.list_funds()

# indices — index value (points) + members.
ic   = vnfin.indices.client()                # IndexClient
hist = vnfin.indices.index_history("FAKEINDEX")   # PriceHistory in points

# gold — VN domestic (VND/lượng) and world XAU (USD/oz). Provider is explicit.
vn    = vnfin.gold.vn("btmc")                # BTMCGoldSource (default), or "pnj"
world = vnfin.gold.world("currency_api")     # CurrencyApiGoldSource (default), or "gold_api"
any_  = vnfin.gold.source("btmc")            # generic provider selector (vn + world)

# crypto — OHLCV (USD).
src = vnfin.crypto.client()                  # == .source(), BinanceCryptoSource

# macro — cross-country indicators.
src = vnfin.macro.client()                   # == .source(), WorldBankMacroSource
```

### Why gold takes an explicit provider

Gold spans two unit families — VN domestic (**VND/lượng**) and world XAU (**USD/oz**) —
so there is no single cross-unit default. `vnfin.gold.vn(...)`, `vnfin.gold.world(...)`,
and `vnfin.gold.source(provider=...)` make the choice explicit. Unknown provider names
raise `ValueError`.

## Stability and backwards compatibility

This facade is **additive**. Every previously documented import still works unchanged,
e.g. `from vnfin import default_client, PriceHistory`, `from vnfin.funds import
FmarketFundSource`, `from vnfin.indices import IndexClient, index_history`,
`from vnfin.gold import BTMCGoldSource`. The raw adapter classes remain importable for
advanced use — the domain factories are simply the recommended one-obvious-entry surface.

> Note: `vnfin.macro.FREDMacroSource` is an advanced/opt-in alternative that currently
> requires `FRED_API_KEY` and is a stub; the default macro source is World Bank
> (`vnfin.macro.client()`).
