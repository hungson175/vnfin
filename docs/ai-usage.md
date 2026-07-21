# vnfin — AI usage guide

> **For AI agents and coding assistants.** This is the single, comprehensive, copy-paste
> reference for using `vnfin`. It is written with **progressive disclosure**: read
> [§1 (rules)](#1-five-rules-that-apply-to-every-domain), [§2 (map)](#2-domain-map) and
> [§3 (quickstart)](#3-quickstart) first — that covers most tasks — then jump to the one
> [domain section in §5](#5-domains) you need. Every example below was verified against the
> library's real API (imports, signatures, units).

`vnfin` is a **clean-room, no-key, open-source** Python library for Vietnam financial-market
data: stocks, fundamentals, mutual funds, indices, gold, FX, crypto, and macro indicators —
each with multi-source **failover** and **typed** results carrying explicit units.

## 0. Install

```bash
pip install git+https://github.com/hungson175/vnfin.git          # core (httpx only)
pip install "vnfin[pandas] @ git+https://github.com/hungson175/vnfin.git"   # + .to_dataframe()
```

Requires Python ≥ 3.10. No API key is needed for the default path of any domain.

## 1. Five rules that apply to every domain

1. **No key needed; BYOK is the rare exception.** Every domain's **default path is keyless**. The
   only optional keys anywhere are `FRED_API_KEY` (macro — an opt-in source *excluded* from the
   default chain), `VNFIN_BTMC_WIDGET_KEY` (gold — overrides a public token), and
   `ALPHAVANTAGE_API_KEY` (the **primary** of `indices.world()` for the S&P 500 — but the keyless
   Stooq `^SPX` fallback serves without it, so even `world()` works key-free). **Never invent
   authentication.**
2. **`client()` = failover chain, `source()` = single primary.** Every domain exposes
   `vnfin.<domain>.client()` (multi-source, ≤3 attempts, recommended) and
   `vnfin.<domain>.source()` (the primary adapter only). **Exception: `gold` has no `client()`** —
   VN domestic (VND/lượng) and world (USD/oz) are different unit families; use `vn()` / `world()`.
3. **Units are explicit on the result — read them, never assume.** Every typed result carries a
   unit/currency field (`value_unit`, `currency`, `unit`). Watch the traps: equities are `VND`
   but **indices reuse the same shape with `value_unit="points"`**; gold is `VND/lượng` (domestic)
   or `USD/oz` (world); fundamentals money is **raw, unscaled VND**. A **unit-homogeneity guard**
   runs inside every failover client — it refuses to mix or relabel units, so a chain can never
   silently return a wrong-scale number.
4. **History dates are validated up front (before any network call).** `prices.history`,
   `indices.index_history`, and `gold ...get_history` **require** `start`/`end` and raise
   `vnfin.exceptions.InvalidData` / `VnfinError` if a date is missing/mistyped or `start > end`.
   `fx.history` is the exception: `start`/`end` are **optional** (`None` → all available annual
   points), but any **provided** bound is still validated before network (malformed/reversed →
   `InvalidData`). (FX has **two shapes**: `fx.get_rate()`/`FXRate` is a single current quote;
   `fx.history()`/`FXHistory` is an annual USD/VND series via World Bank.)
5. **`.to_dataframe()` needs the optional `pandas` extra.** The typed dataclasses work without
   pandas; install `vnfin[pandas]` to enable DataFrame conversion.

## 2. Domain map

| Domain | Entry | Returns | Unit | No key |
|--------|-------|---------|------|:------:|
| `vnfin.prices` | `client()` / `source()` / `history()` | `PriceHistory` (OHLCV bars) | **VND** | ✅ |
| `vnfin.fundamentals` | `client()` / `source()` / `get_financials()` | `tuple[FinancialReport]` | **raw VND** (ratios: dimensionless) | ✅ |
| `vnfin.funds` | `source()` (single; `client` is an alias) | `FundList` / `NavHistory` / holdings | **VND/unit** | ✅ |
| `vnfin.indices` | `client()` / `index_history()` / `index_constituents()` / `world()` (S&P 500) | `PriceHistory` (+ `IndexConstituents`) | **points** (VN) · `USD/share` or `index points` (world) | ✅ |
| `vnfin.gold` | `vn()` / `world()` / `source(provider)` (**no `client()`**) | `GoldQuote` / `GoldHistory` | **VND/lượng** or **USD/oz** | ✅ |
| `vnfin.crypto` | `client()` / `source()` | `CryptoHistory` (OHLCV) | **USD** | ✅ |
| `vnfin.fx` | `client()` / `source()` / `get_rate()` (spot); `history()` (annual USD/VND) | `FXRate` (spot) / `FXHistory` (history) | **VND per 1 base** | ✅ |
| `vnfin.macro` | `client()` / `source()` / `get_indicator()` | `IndicatorSeries` | per-indicator | ✅ (FRED BYOK opt-in) |

## 3. Quickstart

```python
from datetime import date
import vnfin

# Daily stock prices (VND) — failover SSI→VNDirect→VPS→Pinetree
h = vnfin.prices.history("FPT", start=date(2024, 1, 1), end=date(2024, 6, 30))
print(h.symbol, h.source, h.currency, len(h.bars), h.bars[-1].close)

# Annual income statement (raw VND) — failover VNDirect→CafeF
from vnfin.fundamentals import get_financials, StatementType, Period
reports = get_financials("FPT", StatementType.INCOME, Period.ANNUAL)
print(reports[0].fiscal_date, reports[0].get("21001"))   # net revenue, by provider itemCode

# FX (no key, spot) — VND per 1 USD
print(vnfin.fx.get_rate("USD").rate)        # e.g. 26111.0

# Macro (no key) — Vietnam GDP, current US$
import vnfin.macro as macro
print(macro.get_indicator("VNM", macro.MacroIndicator.GDP).latest())
```

## 4. Common patterns

- **Recommended call shape:** `vnfin.<domain>.client().get_*(...)` (failover). Reuse one client to
  share its response cache (notably FX, which caches ~1h to respect provider rate limits).
- **Pin a single provider:** `vnfin.<domain>.source()` returns the primary adapter only.
- **Inspect failover diagnostics:** results from a client carry `.attempts` —
  `tuple[SourceAttempt(name, ok, reason)]` — so you can see which source served the data and why
  others were skipped/rejected.
- **DataFrames:** any `TimeSeriesResult` (`PriceHistory`, `NavHistory`, `GoldHistory`,
  `CryptoHistory`, `IndicatorSeries`) has `.to_dataframe()` (needs `pandas`); metadata lands in
  `df.attrs`.

## 5. Domains

### 5.1 `vnfin.prices` — equity OHLCV (VND)

Daily/intraday OHLCV for VN stocks; daily bars reach back ~2006. Failover **SSI → VNDirect → VPS →
Pinetree** (all provider-adjusted; KIS is registered but excluded — its series is MIXED-adjusted).

```python
import vnfin
from datetime import date
from vnfin.models import Interval

# one-shot over the failover chain
hist = vnfin.prices.history("FPT", start=date(2024, 1, 1), end=date(2024, 6, 30))
print(hist.symbol, hist.source, hist.currency, len(hist.bars))   # ... 'VND' ...
last = hist.bars[-1]
print(last.time, last.close, last.volume)

# reuse a client; get_daily is a convenience for Interval.D1
c = vnfin.prices.client()                 # == vnfin.default_client()
hist = c.get_daily("VNM", date(2023, 1, 1), date(2023, 12, 31))
for a in hist.attempts:                    # failover diagnostics
    print(a.name, a.ok, a.reason)

# pin the primary source (no failover)
src = vnfin.prices.source()                # SSIiBoardSource
```

- **Result:** `PriceHistory` — `.bars` is `tuple[PriceBar(time, open, high, low, close, volume)]`
  (`time` tz-aware Asia/Ho_Chi_Minh); plus `symbol, interval, adjustment_policy, source, currency,
  value_unit ('VND'), warnings, attempts`.
- **Gotchas:** `start`/`end` required & validated up front (→ `InvalidData`). Daily is guaranteed;
  intraday is best-effort/capability-gated. Coverage shortfalls are soft `warnings`
  (`partial_start_coverage`/`partial_end_coverage`), not errors. A D1 series that ends in a long run of
  forward-filled phantom bars (delisted/suspended) adds a `trailing_zero_volume_tail` warning.

### 5.2 `vnfin.fundamentals` — financial statements (raw VND)

One `FinancialReport` per fiscal period (**newest first**); line items keyed by provider
itemCode. Failover **VNDirect → CafeF**.

```python
from vnfin.fundamentals import get_financials, StatementType, Period

reports = get_financials("FPT", StatementType.INCOME, Period.ANNUAL)   # no key
latest = reports[0]                                  # newest fiscal period
print(latest.symbol, latest.fiscal_date, latest.source, latest.currency)
net_revenue = latest.get("21001")                    # raw VND, by itemCode (corporate income)
for li in latest:                                    # iterate LineItem
    print(li.item_code, li.name, li.value, li.value_unit)

# strings accepted; force bank template; limit periods
reports = get_financials("VCB", "balance", "quarter", is_bank=True, limit=4)
print(reports[0].is_bank, reports[0].model_type)     # True 102
```

- **Result:** `tuple[FinancialReport]`; each is iterable over `LineItem(item_code, name, value,
  value_unit)`, supports `len()`, `.get(code)`, `.to_dataframe()`.
- **Gotchas:** money is **RAW VND** (unscaled — divide yourself). `is_bank` defaults to AUTO
  (auto-detect). `StatementType.RATIOS` is **not money** (`value_unit='ratio'`, `currency=None`).
  Codes differ between corporate (model_type 1/2/3) and bank (101/102/103) templates.

### 5.3 `vnfin.funds` — mutual-fund NAV (VND/unit)

VN open-ended funds via Fmarket's public API. **Single-source** (`vnfin.funds.client` is an alias
of `source`). The verbs live on the source object.

```python
from vnfin.funds import source

src = source()                                   # FmarketFundSource
funds = src.list_funds(asset_type="STOCK")        # FundList (iterable/indexable)
print(len(funds), funds.source, funds.currency)   # ... 'fmarket' 'VND'
f0 = funds[0]
print(f0.code, f0.name, f0.id, f0.nav)            # nav = latest VND/unit

hist = src.nav_history(f0.id, from_date="2024-01-01", to_date="2024-12-31")
print(hist.value_unit, hist.currency)             # 'VND/unit' 'VND'

holdings = src.holdings(f0.id)                     # tuple[FundHolding] — equities + bonds merged
for h in holdings:
    print(h.stock_code, h.weight_pct, h.instrument_type)  # STOCK/BOND/UNLISTED_BOND/OTHER; weight_pct = % of NAV (0–100)

alloc = src.asset_allocation(f0.id)                # AssetAllocation — asset-class split
for c in alloc:
    print(c.asset_class, c.weight_pct)             # e.g. 'BOND' 88.0
```

- **Gotchas:** `nav_history`/`holdings`/`asset_allocation` take the fund's **internal `Fund.id`
  (int)**, not the ticker. `holdings()` merges equity + bond rows (a pure-bond fund returns its bond
  positions, no longer `EmptyData`); each row has `instrument_type`
  (`STOCK`/`BOND`/`UNLISTED_BOND`/`OTHER` — an unknown provider type → `OTHER`, never a hard fail) and
  an optional `as_of_utc` (provider `updateAt`, or `None`). `stock_code` is a canonical ticker for
  equities, but for bond/unlisted-bond/other rows it may be a non-canonical descriptive identifier.
  `FundHolding.price_raw` is **opaque/unnormalized** (`price_unit='raw'/None`) — don't treat as money;
  `weight_pct` is the safe numeric.

### 5.4 `vnfin.indices` — index value (points) + constituents

Daily OHLCV for VN indices in **points** (VNINDEX, VN30, HNX, UPCOM, sectors) + membership
baskets. History failover **VPS → SSI → VNDirect**; constituents are single-source (SSI iBoard).

```python
from datetime import date
from vnfin.indices import IndexClient, index_history, index_constituents

c = IndexClient()
hist = c.index_history("VNINDEX", date(2024, 1, 1), date(2024, 6, 30))
print(hist.value_unit, hist.source)               # 'points' ...
hist = index_history("VN30", date(2024, 1, 1), date(2024, 3, 31))   # one-shot
src = IndexClient()                                # (vnfin.indices.source() = primary VPS only)

vn30 = index_constituents("VN30")                  # IndexConstituents (no weights)
print(vn30.symbols, len(vn30), vn30.has_weights)   # (...), N, False
```

- **Gotchas:** values are **POINTS, not VND** — read `value_unit` (`PriceHistory` defaults to VND
  for equities but index sources override to `points`). `index_history` requires both dates
  (→ `VnfinError` up front). Constituents carry **no weights** (`weight is None`, `has_weights`
  False) — official weighted baskets are never fabricated.

#### World/US index (S&P 500) — `vnfin.indices.world()`

A separate accessor for the **S&P 500** (a global benchmark for VN-vs-world comparisons), backed
by its **own** 2-source failover chain — completely separate from the VN HOSE/HNX path above.

```python
from datetime import date
import vnfin

# default chain: Alpha Vantage SPY (BYOK primary) → Stooq ^SPX (keyless fallback)
spy = vnfin.indices.world("SPY", start=date(2024, 1, 1), end=date(2024, 6, 30))
print(spy.source, spy.provider_symbol, spy.value_unit)   # 'alphavantage' 'SPY' 'USD/share (SPY ETF, S&P 500 proxy)'
for w in spy.warnings:                                    # 'fallback_instrument_served: ...' iff ^SPX served
    print(w)
```

- **v1 is `symbol="SPY"` only** (any other symbol → clear `InvalidData`). SPY (the ETF) is a
  documented **proxy** for the S&P 500 — not the proprietary `^GSPC`.
- **Cross-instrument fallback — read `value_unit`!** The primary serves SPY in
  `USD/share` (~600); the keyless Stooq fallback serves the `^SPX` **index level** in
  `index points` (~6000), ~10× different. Only one disclosed leg is returned per call
  (`source`/`value_unit`/`provider_symbol` say which). When the ^SPX fallback is served instead of
  SPY (AV throttled or no key), the result carries a mechanical **`fallback_instrument_served`**
  warning — **rebase before comparing** the two; never mix them un-rebased.
- **BYOK:** the AV primary reads `ALPHAVANTAGE_API_KEY` (param or env); with no key it is skipped
  with **no network call** and Stooq serves directly. The key is **redacted** from every error.

### 5.5 `vnfin.gold` — VN domestic (VND/lượng) & world XAU (USD/oz)

**No single `client()`** — two unit families. Pick a provider.

```python
from datetime import date
from vnfin.gold import vn, world, default_world_gold_client

q = vn("btmc").get_quotes()                        # or vn("pnj") — VND/lượng, SPOT only
for x in q:
    print(x.product, x.buy, x.sell, x.unit, x.currency)   # ... 'VND/luong' 'VND'

w = world("currency_api")                          # USD/oz; spot + daily history
hist = w.get_history(date(2026, 1, 1), date(2026, 3, 31))  # GoldHistory
print(hist.unit, len(hist.bars), hist.bars[0].date, hist.bars[0].price)  # 'USD/oz' ...

client = default_world_gold_client()               # world-only failover client (USD/oz)

# World-reference VND/lượng history (#178) — ANNUAL; NOT the SJC/BTMC domestic price.
# Needs network. Multi-year windows rely on Stooq for long world-gold history; from
# datacenter/CI IPs Stooq may answer with an anti-bot challenge -> the call can raise
# AllSourcesFailed (run from a normal residential IP, or catch and degrade).
from vnfin.gold import world_reference_history_vnd
ref = world_reference_history_vnd(date(2018, 1, 1), date(2024, 12, 31))     # GoldHistory
print(ref.unit, ref.currency, len(ref.bars))       # 'VND/luong' 'VND' 7  (one point per year)
for w in ref.warnings:
    print(w)                                        # 'world_reference_excludes_domestic_premium: ...'
```

- **Gotchas:** VN unit is **VND/lượng** (1 lượng = 10 chỉ = 37.5 g), not plain VND. VN domestic
  sources are **spot-only** (`get_history` raises). World history default chain is
  `[CurrencyApiGoldSource]` (Stooq is opt-in). `gold` has **no `client()`**.
- **`world_reference_history_vnd(start, end)` is the world-gold-implied VND/lượng value, ANNUAL
  (one Jan-1 point per year), and is NOT the VN domestic price** — SJC/BTMC trade a large,
  time-varying premium (+10–21%) above it, so it understates the domestic price; it self-discloses
  via the accessor name, `source`, `value_unit`, and a mechanical
  `world_reference_excludes_domestic_premium` warning. `gold.domestic_history()` is **reserved**
  and raises a source-gap diagnostic (→ #182), never this synthesis. See
  [`docs/sources/gold-world-reference.md`](sources/gold-world-reference.md).

### 5.6 `vnfin.crypto` — crypto OHLCV (USD)

Keyless candles for major coins. Failover **Binance → Coinbase**.

```python
from vnfin import crypto, Interval
from datetime import date

client = crypto.client()                           # FailoverCryptoClient
hist = client.get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 3, 1))
print(hist.symbol, hist.source, hist.currency, hist.bars[-1].close)   # ... 'USD' ...

src = crypto.source()                              # bare Binance adapter
hist = src.get_klines("ETHUSDT", Interval.H1, date(2024, 1, 1), date(2024, 1, 2))
print(hist.base_asset, hist.quote_asset, hist.price_unit)   # ETH USD 'USD per ETH'
```

- **Gotchas:** `Interval` is `vnfin.Interval` (not under `vnfin.crypto`). USD means USD-stablecoin
  quotes (USDT/USDC/…) ~1:1; a non-USD pair (e.g. `ETHBTC`) reports `currency='BTC'` and is
  **rejected by the USD failover client** (never mislabeled). Coinbase has no W1/MN1 bars (skipped
  for those). Timestamps are tz-aware **UTC** (crypto is 24/7).

### 5.7 `vnfin.fx` — FX reference rates (VND per 1 unit; spot + annual history)

```python
from datetime import date
import vnfin

# Spot/current
r = vnfin.fx.get_rate("USD")                       # FXRate; failover open.er-api → Vietcombank
print(r.base, r.quote, r.rate, r.unit)             # 'USD' 'VND' 26111.0 'VND per 1 USD'

c = vnfin.fx.client()                              # reuse to share the ~1h cache
print(c.get_rate("USD").rate, c.get_rate("EUR").rate)

vcb = vnfin.fx.VietcombankFXSource().get_rate("USD")   # bid/ask (Buy/Sell) populated by VCB
print(vcb.rate, vcb.bid, vcb.ask)

# Annual history (issue #159) — USD/VND via World Bank PA.NUS.FCRF (no key)
h = vnfin.fx.history("USD", "VND", start=date(2010, 1, 1), end=date(2024, 12, 31))
print(h.source, h.unit, h.frequency.value, len(h))     # 'worldbank_fx' 'VND per 1 USD' 'annual' 15
print(h.rate_for_year(2024))                            # exact-match-or-raise (never fills)
```

- **Gotchas (spot):** `get_rate()`/`FXRate` is **point-in-time** (one quote). Quote is **VND-only**
  (other quote → `InvalidData`). Unit is **VND per 1 base** (not base per VND). `bid`/`ask` only
  from Vietcombank (its `Transfer` rate is a commercial reference quote, **not** the SBV central
  rate). Malformed ISO code → `InvalidData` before any network call.
- **Gotchas (history):** `history()`/`FXHistory` is **annual USD/VND only** (monthly + non-USD
  cross-quotes are deferred to v2). The annual point is a **period-average** rate stamped Jan 1
  (not year-end, not SBV central). `rate_on(date)` / `rate_for_year(year)` are **exact-match-or-
  raise** — they never forward-fill or interpolate. Unsupported pair, bad frequency, or
  missing/mistyped/reversed dates → `InvalidData` before any network call (via the `history()`
  facade **and** a direct `WorldBankFXHistorySource().get_history(...)` call).

### 5.8 `vnfin.macro` — cross-country macro indicators

Time series by ISO3 country code. Failover **World Bank → IMF → DBnomics** (all no-key).

```python
import vnfin.macro as macro

client = macro.client()
series = client.get_indicator("USA", macro.MacroIndicator.GDP_GROWTH)   # NOTE: no kwargs here
print(series.source, series.unit)                  # e.g. 'world_bank' '%'
print(series.latest())                             # (date, value), excludes IMF projections

# one-shot module function (takes http_get/timeout/sources kwargs); GDP is current US$
s = macro.get_indicator("VNM", macro.MacroIndicator.GDP)
print(s.unit, s.currency)                          # 'current US$' 'USD'

# BYOK (optional): arbitrary FRED series — needs FRED_API_KEY, NOT in the default chain
# from vnfin.macro import FREDMacroSource; FREDMacroSource(api_key=...).get_indicator("", "CPIAUCSL")
```

- **Indicators (only 5):** `GDP`, `GDP_GROWTH`, `CPI`, `INFLATION`, `UNEMPLOYMENT`. Units pinned
  per indicator (GDP = `current US$`/USD; CPI = `index`; the rest = `%`) and never relabeled.
- **Gotchas:** `client.get_indicator(country, indicator)` takes **no** extra kwargs (config is on
  the client/constructor); the **module** `macro.get_indicator(...)` accepts `http_get`/`timeout`/
  `sources`. `latest()` excludes IMF WEO projections (use `latest_including_projections()` /
  `actual_points`). FRED is BYOK-only; there are **no** BEA/BLS sources.

## 6. Errors

All adapters wrap failures as `vnfin.exceptions` subclasses so a failover client can recover:
`SourceUnavailable` (transport), `EmptyData` (no rows), `InvalidData` (malformed / bad caller
input), `UnsupportedInterval` (capability), `UnitMismatchError` (guard), and `AllSourcesFailed`
(every source failed — carries per-source `.attempts`). Bad caller input (missing/inverted dates,
malformed currency code) raises **before** any network call.

## 7. Stability & monitoring

- **Public API is SemVer-stable** and guarded by a snapshot test — see
  [`stability.md`](stability.md). Pin a version for reproducibility.
- **Upstream health** (is a provider still up / same shape?) is monitored, opt-in, by
  `python scripts/healthcheck.py` (never in CI; see [`stability.md`](stability.md)).

## 8. Deeper references

- [`README.md`](../README.md) — human getting-started + domains/sources table.
- [`docs/api.md`](api.md) — the public facade & naming standard.
- [`docs/units.md`](units.md) — canonical units per domain (read this when a number looks off).
- [`docs/sources/`](sources/) — per-source provenance, terms, rate limits.
- [`skills/vnfin/SKILL.md`](../skills/vnfin/SKILL.md) — the installable agent skill.
- [`llms.txt`](../llms.txt) — machine-readable index of these resources.
