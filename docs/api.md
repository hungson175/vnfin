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
| `client(...)` | The **failover client** for the domain (multi-source, ≤3 attempts, unit-homogeneity guard). This is the recommended entry. |
| `source(...)` | The **primary single-source adapter** only — no failover. Use it to pin one provider explicitly. |
| `history(...)` / `index_history(...)` / `get_financials(...)` | Domain-specific one-shot convenience functions (kept where they already existed). |

> `client()` is **not** an alias of `source()`. `client()` returns the failover
> chain; `source()` returns just the primary adapter. (The only domains whose
> `client()` is currently still effectively single-source are `funds` (no clean
> no-auth backup exists — accepted single-source for v0.1) and `gold` world
> history when Stooq is not opted in; see [units.md](units.md) and
> [design/redundancy-failover.md](design/redundancy-failover.md).)

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

# fundamentals — financial statements (raw VND). Failover VNDirect -> CafeF.
c       = vnfin.fundamentals.client()        # FailoverFundamentalClient (VNDirect -> CafeF)
src     = vnfin.fundamentals.source()        # VNDirectFundamentalSource (primary only)
reports = vnfin.fundamentals.get_financials("FAKECORP", "income", "annual")  # uses the failover chain

# funds — mutual-fund NAV (VND/unit). No clean no-auth backup exists -> single-source (v0.1).
src   = vnfin.funds.client()                 # FmarketFundSource (accepted single-source; client() == source())
funds = src.list_funds()

# indices — index value (points) + members.
ic   = vnfin.indices.client()                # IndexClient
hist = vnfin.indices.index_history("FAKEINDEX")   # PriceHistory in points

# gold — VN domestic (VND/lượng) and world XAU (USD/oz). Provider is explicit.
vn    = vnfin.gold.vn("btmc")                # BTMCGoldSource (default), or "pnj"
world = vnfin.gold.world("currency_api")     # CurrencyApiGoldSource (default), or "gold_api"
any_  = vnfin.gold.source("btmc")            # generic provider selector (vn + world)
# World-gold daily history has a failover client (currency-api; opt-in Stooq backup):
wc    = vnfin.gold.default_world_gold_client()  # FailoverGoldClient (USD/oz)

# crypto — OHLCV (USD). Failover Binance -> Coinbase.
c   = vnfin.crypto.client()                  # FailoverCryptoClient (Binance -> Coinbase)
src = vnfin.crypto.source()                  # BinanceCryptoSource (primary only)

# macro — cross-country indicators. No-key failover World Bank -> IMF -> DBnomics.
c   = vnfin.macro.client()                   # MacroClient (World Bank -> IMF DataMapper -> DBnomics, no-key)
src = vnfin.macro.source()                   # WorldBankMacroSource (primary only)
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

> Note: the default macro chain is **no-key**: World Bank (primary) → IMF DataMapper
> → DBnomics, served by `vnfin.macro.client()` over the *same canonical indicator*
> (unit pre-filtered, then guarded). `vnfin.macro.FREDMacroSource` is an advanced
> **bring-your-own-key** alternative requiring `FRED_API_KEY` (official API only,
> never `fredgraph.csv`); without a key it is *not capable* and is skipped in a
> failover chain with no network call — it is excluded from the no-key default chain.
