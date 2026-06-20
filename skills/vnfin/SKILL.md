---
name: vnfin
description: >-
  Use when the user needs Vietnam (VN) financial-market data in Python — daily/historical
  stock prices (OHLCV), company fundamentals (income/balance/cashflow/ratios), mutual-fund NAV
  and holdings, market indices and constituents (VNINDEX, VN30, HNX, UPCOM), domestic and world
  gold prices, foreign-exchange rates vs VND, major crypto OHLCV, or cross-country macro
  indicators (GDP, CPI, inflation, unemployment). Provides the clean-room, no-API-key `vnfin`
  library with multi-source failover and typed, unit-explicit results. Trigger on requests like
  "get FPT stock prices", "Vietnam GDP", "VNINDEX history", "SJC/gold price", "USD to VND",
  "fund NAV", "VN30 constituents", or any task building a VN-market data/analysis/advisor tool.
---

# vnfin — Vietnam financial-market data

`vnfin` is a clean-room, **no-API-key**, open-source Python library for Vietnam financial data.
Most domains fetch over a multi-source **failover** chain (where a clean same-unit backup exists;
`funds` is single-source and `gold` ships separate VN/world adapters) and every result is a
**typed** object with **explicit units**. Use it whenever a task needs VN stocks, fundamentals,
funds, indices, gold, FX, crypto, or macro indicators.

## Install

```bash
pip install git+https://github.com/hungson175/vnfin.git          # core (httpx only)
pip install "vnfin[pandas] @ git+https://github.com/hungson175/vnfin.git"   # + .to_dataframe()
```

Python ≥ 3.10. No key, no env var, no login for the default path of any domain.

## Five rules (apply to every domain)

1. **No key needed.** The only optional BYOK knobs anywhere are `FRED_API_KEY` (macro, opt-in,
   excluded from the default chain) and `VNFIN_BTMC_WIDGET_KEY` (gold, public-token override).
   Never add authentication.
2. **`client()` = failover, `source()` = single primary.** `gold` is the exception — no
   `client()` (two unit families); use `vn()` / `world()`.
3. **Read the unit off the result; never assume.** Equities `VND`; **indices reuse the price
   shape but `value_unit="points"`**; gold `VND/lượng` (domestic) or `USD/oz` (world), plus
   `gold.world_reference_history_vnd()` = **annual world-reference `VND/luong`, NOT the SJC/BTMC
   domestic price** (it understates it; carries a `world_reference_excludes_domestic_premium`
   warning); fundamentals **raw, unscaled VND**; FX `VND per 1 base`. A unit-homogeneity guard
   inside every failover client refuses to mix/relabel units.
4. **`start`/`end` are required for history** (`prices.history`, `indices.index_history`,
   `gold ...get_history`) and validated **before any network call** (→ `InvalidData`/`VnfinError`).
   FX has **two shapes**: `fx.get_rate()`/`FXRate` = spot/current quote; `fx.history()`/`FXHistory`
   = **annual USD/VND history** (World Bank `PA.NUS.FCRF`, no-key).
5. **`.to_dataframe()` needs the `pandas` extra**; the typed dataclasses work without it.

## Domain cheat-sheet

| Need | Call | Result · unit |
|------|------|---------------|
| Stock OHLCV | `vnfin.prices.history(sym, start=, end=)` | `PriceHistory` · VND |
| Financials | `vnfin.fundamentals.get_financials(sym, stmt, period)` | `tuple[FinancialReport]` · raw VND |
| Fund NAV/holdings | `vnfin.funds.source().nav_history(fund_id, ...)` · `.holdings(fund_id)` (stocks+bonds) · `.asset_allocation(fund_id)` | `NavHistory` · `tuple[FundHolding]` · `AssetAllocation` |
| Index value | `vnfin.indices.index_history(idx, start, end)` | `PriceHistory` · **points** |
| Index members | `vnfin.indices.index_constituents(idx)` | `IndexConstituents` (no weights) |
| World index (S&P 500) | `vnfin.indices.world("SPY", start=, end=)` | `PriceHistory` · `USD/share` (SPY) or `index points` (^SPX) |
| VN gold spot | `vnfin.gold.vn("btmc").get_quotes()` | `GoldQuote` · VND/lượng |
| World gold | `vnfin.gold.world().get_history(start, end)` | `GoldHistory` · USD/oz |
| Crypto OHLCV | `vnfin.crypto.client().get_klines(sym, vnfin.Interval.D1, start, end)` | `CryptoHistory` · USD |
| FX rate | `vnfin.fx.get_rate("USD")` | `FXRate` · VND per 1 USD |
| Macro | `vnfin.macro.get_indicator("VNM", vnfin.macro.MacroIndicator.GDP)` | `IndicatorSeries` |

## Canonical examples

```python
from datetime import date
import vnfin

# Stock prices (VND) — failover SSI→VNDirect→VPS→Pinetree
h = vnfin.prices.history("FPT", start=date(2024, 1, 1), end=date(2024, 6, 30))
print(h.source, h.currency, len(h.bars), h.bars[-1].close)

# Fundamentals (raw VND) — newest period first, line items by itemCode
from vnfin.fundamentals import get_financials, StatementType, Period
rep = get_financials("FPT", StatementType.INCOME, Period.ANNUAL)[0]
print(rep.fiscal_date, rep.get("11000"))

# Index value in POINTS (read value_unit!)
idx = vnfin.indices.index_history("VNINDEX", date(2024, 1, 1), date(2024, 6, 30))
print(idx.value_unit, idx.bars[-1].close)         # 'points' ...

# FX (spot, VND per 1 USD) and Macro (Vietnam GDP, current US$)
print(vnfin.fx.get_rate("USD").rate)
print(vnfin.macro.get_indicator("VNM", vnfin.macro.MacroIndicator.GDP).latest())
```

## Errors

Failures are `vnfin.exceptions`: `SourceUnavailable`, `EmptyData`, `StaleData` (an `EmptyData`
subclass — data ends before the requested window), `InvalidData`,
`UnsupportedInterval`, `UnitMismatchError`, `AllSourcesFailed` (carries per-source `.attempts`).
Bad input (missing/inverted dates, malformed currency) raises before any network call.

## Full reference

For every domain — all factory verbs, signatures, result fields, gotchas, and verified examples —
read **[reference/domains.md](reference/domains.md)**. For canonical units see the library's
`docs/units.md`; for the full prose guide see `docs/ai-usage.md`. Pin a version for
reproducibility (the public API is SemVer-stable — see `docs/stability.md`).
