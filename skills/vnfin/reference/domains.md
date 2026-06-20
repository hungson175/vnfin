# vnfin — full per-domain reference

Deep reference for the `vnfin` skill. Every signature/field below is verified against the library.
Load this when you need exact signatures, result fields, or domain-specific gotchas. For the prose
guide see the repo's `docs/ai-usage.md`; for units see `docs/units.md`.

Facade convention: `vnfin.<domain>.client()` = failover chain, `vnfin.<domain>.source()` = primary
single adapter. `gold` is the exception (no `client()`). All clients carry `.attempts`
(`tuple[SourceAttempt(name, ok, reason)]`). All `TimeSeriesResult` subclasses have
`.to_dataframe()` (needs `pandas`).

---

## prices — equity OHLCV (VND)

- **Entry:** `vnfin.prices.history(symbol, interval=Interval.D1, start=None, end=None, *, max_attempts=3, http_get=None, timeout=25.0)`; `vnfin.prices.client()` → `FailoverPriceClient` (== `vnfin.default_client()`) with `.get_history(symbol, interval=Interval.D1, start=None, end=None)` and `.get_daily(symbol, start, end)`; `vnfin.prices.source()` → `SSIiBoardSource`.
- **Failover:** SSI → VNDirect → VPS → Pinetree (provider-adjusted). KIS is registered but excluded (MIXED adjustment).
- **Result:** `vnfin.models.PriceHistory` — `symbol, interval, adjustment_policy, source, bars: tuple[PriceBar], currency='VND', value_unit='VND', exchange, provider_symbol, fetched_at_utc, warnings, attempts`. `PriceBar(time tz-aware Asia/Ho_Chi_Minh, open, high, low, close, volume)`.
- **Gotchas:** `start`/`end` required & validated up front (missing/typo/`start>end` → `InvalidData`). Daily guaranteed; intraday best-effort/capability-gated. Coverage shortfall → soft `warnings` (`partial_start_coverage`/`partial_end_coverage`), not error. All-fail → `AllSourcesFailed`; bad interval → `UnsupportedInterval`.

```python
import vnfin; from datetime import date
h = vnfin.prices.history("FPT", start=date(2024,1,1), end=date(2024,6,30))
print(h.source, h.currency, h.bars[-1].close)
```

## fundamentals — financial statements (raw VND)

- **Entry:** `vnfin.fundamentals.get_financials(symbol, statement, period, *, is_bank=None, limit=8, source=None, sources=None, max_attempts=3, http_get=None, timeout=25.0)` → `tuple[FinancialReport]` (newest first); `client()` → `FailoverFundamentalClient`; `source()` → `VNDirectFundamentalSource`. `StatementType`: `income/balance/cashflow/ratios` (strings accepted). `Period`: `QUARTER/ANNUAL` (case-insensitive). `AUTO` is the `is_bank` sentinel (`== None`).
- **Failover:** VNDirect → CafeF (both `unit='VND'`).
- **Result:** each `FinancialReport(symbol, statement_type, period, fiscal_date, items: tuple[LineItem], source, currency('VND'|None), is_bank, model_type, provider_symbol, fetched_at_utc, warnings)` — iterable over `LineItem(item_code, name, value, value_unit('VND'|'ratio'))`, plus `len()`, `.get(code)`, `.to_dataframe()`.
- **Gotchas:** money is **RAW VND** (unscaled). Line items keyed by opaque itemCode (e.g. `'11000'`); codes differ corporate (model_type 1/2/3) vs bank (101/102/103). `is_bank` AUTO-detects. `RATIOS` is not money (`value_unit='ratio'`, `currency=None`, `period=UNKNOWN`). Precedence: `source=` > `sources=` > default failover.

```python
from vnfin.fundamentals import get_financials, StatementType, Period
rep = get_financials("FPT", StatementType.INCOME, Period.ANNUAL)[0]
print(rep.fiscal_date, rep.get("11000"))   # raw VND
```

### fundamentals — canonical metrics (additive, offline transform; #157)

- **Entry:** `vnfin.fundamentals.metrics(symbol, period="annual", *, is_bank=None, limit=8, source=None, sources=None, max_attempts=3, http_get=None, timeout=25.0)` → `tuple[MetricReport]` (newest first); `vnfin.fundamentals.explain_metric_coverage(...)` (same kwargs) → `MetricCoverage` (non-fatal diagnostics); `vnfin.fundamentals.metric_catalog(applies_to=None)` → `tuple[MetricDefinition]` (pure); `vnfin.fundamentals.explain_metric(metric_id)` → `MetricDefinition` (pure). All importable from `vnfin.fundamentals`.
- **What it does:** fetches income+balance+cashflow once each via the same `get_financials` failover (NEVER `ratios`), then maps the verified **VNDirect** codes to a fixed **v1 catalog of 26 metrics** (21 raw-mapped + 5 derived ratios) — one `MetricReport` per fiscal period. Per-statement failures are non-fatal.
- **Result:** `MetricReport(symbol, period, fiscal_date, is_bank, metrics: tuple[MetricValue], statement_sources: tuple[StatementProvenance], warnings)` — `.get(id)` (returns the `MetricValue` even when unavailable), `.to_dataframe()` (one row per metric, all 26; `df.attrs` has **no** `source` key). `MetricValue(id, value, value_unit, kind, availability, fiscal_date, inputs: tuple[MetricInput], reason, warnings)` — `value` is `None` unless `availability=='available'`; `reason` carries the stable diagnostic. `MetricCoverage(symbol, period, periods: tuple[PeriodCoverage], notes)` with `PeriodCoverage(fiscal_date, is_bank, statement_provenance, per_metric, named_item_count, generic_item_count, unmapped_codes, ratio_status)`.
- **Enums (`.value`):** `MetricId` (e.g. `net_revenue`, `gross_margin`); `MetricKind` `raw_mapped`/`provider_native`/`derived`; `AppliesTo` `corporate`/`bank`/`both`; `MetricCategory` `profitability`/`liquidity`/`leverage`/`cashflow`/`size`; `MetricAvailability` `available`/`missing`/`blocked`/`not_applicable`/`unsupported`; `StatementCoverageStatus` `ok`/`missing`/`source_error`/`not_served`.
- **Gotchas:** every report carries ALL 26 metrics — gaps are `availability`, never omission. v1 maps **VNDirect only**: a statement that failed over to CafeF comes back `blocked` (`"metric map not available for source 'cafef'"`), NOT `missing`. Provenance is **per statement** (`rep.statement_sources`) — there is no single `rep.source` (income/balance/cashflow may resolve to different sources; cashflow is VNDirect-only → CafeF cashflow is `not_served`). Bank metrics use only the **#157-verified** bank codes (`net_interest_income`/`loans_to_customers`/`customer_deposits` + shared); a corporate-only id on a bank → `not_applicable` (and vice-versa). Derived ratios are guarded (zero/negative/non-finite denominator → `missing`, never `inf`/`NaN`). **Ratios deferred to v2** — `ratio_status` is always `not_requested`; `explain_metric("roe")` raises `VnfinError`. `metric_catalog("bank")` → BANK+BOTH; `("corporate")`/`("non_bank")` → CORPORATE+BOTH; other string → `VnfinError`.

```python
import vnfin
rep = vnfin.fundamentals.metrics("FPT", period="annual")[0]
print(rep.get("net_revenue").value, rep.get("gross_margin").value)   # raw VND, ratio
print(rep.get("net_interest_income").availability.value)             # 'not_applicable' (corporate)
cov = vnfin.fundamentals.explain_metric_coverage("FPT", period="annual")  # never raises
```

## funds — mutual-fund NAV (VND/unit) — single-source

- **Entry:** `vnfin.funds.source()` → `FmarketFundSource` (`vnfin.funds.client` is an alias). Verbs are **methods on the source**: `.list_funds(asset_type=None, search='', page_size=100)` → `FundList`; `.nav_history(product_id: int, from_date=None, to_date=None)` → `NavHistory`; `.holdings(product_id: int)` → `tuple[FundHolding]` (equities + bonds merged); `.asset_allocation(product_id: int)` → `AssetAllocation`. No module-level `list_funds`.
- **Result fields:** `Fund(code, name, id, nav, manager, asset_type, currency='VND')`; `FundList(funds, source, currency, ...)` iterable/indexable; `NavHistory(product_id, points: tuple[NavPoint(date, nav)], value_unit='VND/unit', currency='VND', ...)`; `FundHolding(stock_code, weight_pct, industry, price_raw, price_unit, instrument_type='STOCK', as_of_utc=None)`; `AssetAllocation(product_id, classes: tuple[AssetClassWeight(asset_class, weight_pct)], source, currency='VND', code, as_of_utc, ...)` iterable/indexable.
- **Gotchas:** `nav_history`/`holdings`/`asset_allocation` take the fund's internal **`Fund.id` (int)**, not the ticker. `holdings()` merges equity (`productTopHoldingList`) and bond (`productTopHoldingBondList`) rows — each tagged `instrument_type` (`'STOCK'`/`'BOND'`/`'UNLISTED_BOND'`/`'OTHER'` — an unknown provider type → `'OTHER'`, never a hard fail); a pure-bond fund returns its bond positions (no longer `EmptyData`). `stock_code` is a canonical ticker for equities, but for bond/unlisted-bond/other rows may be a non-canonical descriptive identifier (e.g. `'Trái phiếu chưa niêm yết'`). `FundHolding.price_raw` is opaque/unnormalized (`price_unit='raw'/None`) — not money; use `weight_pct` (0–100 % of NAV). `as_of_utc` is the provider `updateAt` or `None` (never fabricated). `asset_allocation()` class weights need not sum to 100% (partial disclosure). Inverted date window → `InvalidData`. A window after the provider's latest `navDate` (feed currently stale) → `StaleData` (an `EmptyData` subclass) naming the gap, not a silent empty.

```python
from vnfin.funds import source
src = source(); funds = src.list_funds(asset_type="STOCK")
hist = src.nav_history(funds[0].id, from_date="2024-01-01", to_date="2024-12-31")
```

## indices — index value (points) + constituents

- **Entry:** `vnfin.indices.IndexClient()` / `vnfin.indices.client()` with `.index_history(symbol, start=None, end=None, interval=Interval.D1)` → `PriceHistory`; module `vnfin.indices.index_history(symbol, start=None, end=None, interval=Interval.D1, *, http_get=None, timeout=25.0, max_attempts=3)`; `vnfin.indices.index_constituents(index, *, http_get=None, timeout=25.0)` → `IndexConstituents`; `vnfin.indices.source()` → primary `VPSIndexSource`.
- **Failover:** history VPS → SSI → VNDirect. Constituents single-source (SSI iBoard).
- **Result:** `PriceHistory` with `value_unit='points'`/`currency='points'`. `IndexConstituents(index, source, members: tuple[IndexMember(symbol, exchange, company_name, isin, weight)], provider_group, as_of, ...)`, props `.symbols`, `.has_weights`, `len()/iter()`, `.to_dataframe()`.
- **Gotchas:** values are **POINTS not VND** (read `value_unit`). `index_history` requires both dates (→ `VnfinError` up front). Constituents have **no weights** (`weight=None`, `has_weights=False`).

```python
from datetime import date; from vnfin.indices import index_history, index_constituents
h = index_history("VNINDEX", date(2024,1,1), date(2024,6,30)); print(h.value_unit)  # 'points'
print(index_constituents("VN30").symbols)
```

## gold — VN domestic (VND/lượng) & world XAU (USD/oz) — no `client()`

- **Entry:** `vnfin.gold.vn(provider="btmc")` (`"btmc"`/`"pnj"`) → domestic source, `.get_quotes()` → `tuple[GoldQuote]` (spot only); `vnfin.gold.world(provider="currency_api")` → world source, `.get_quotes()` + `.get_history(start: date, end: date)` → `GoldHistory`; `vnfin.gold.source(provider)` dispatches by name; `vnfin.gold.default_world_gold_client()` → `FailoverGoldClient` (world-only, USD/oz).
- **Result:** `GoldQuote(time, product, buy, sell, unit, currency, source, fetched_at_utc)` + props `.spread`, `.mid`. `GoldHistory(product, unit, currency, source, bars: tuple[GoldBar(date, price)], value_unit, ..., .to_dataframe())`.
- **Gotchas:** **no `client()`** (VND/lượng vs USD/oz). VN unit is **VND/lượng** (1 lượng = 10 chỉ = 37.5 g). VN sources spot-only (`get_history` raises). World default chain `[CurrencyApiGoldSource]`; `world("gold_api")` is spot-only; Stooq opt-in. Optional `VNFIN_BTMC_WIDGET_KEY` overrides the public `BTMC_PUBLIC_WIDGET_KEY`.

```python
from datetime import date; from vnfin.gold import vn, world
print(vn("btmc").get_quotes()[0].unit)                         # 'VND/luong'
print(world().get_history(date(2026,1,1), date(2026,3,31)).unit)  # 'USD/oz'
```

## crypto — OHLCV (USD)

- **Entry:** `vnfin.crypto.client()` → `FailoverCryptoClient`; `vnfin.crypto.source()` → `BinanceCryptoSource`. Both: `.get_klines(symbol, interval=Interval.D1, start=None, end=None)` → `CryptoHistory`. `Interval` is `vnfin.Interval` (top-level), not under `vnfin.crypto`.
- **Failover:** Binance → Coinbase (USD guard).
- **Result:** `CryptoHistory(symbol, interval, source, bars: tuple[CryptoBar(time tz-aware UTC, open, high, low, close, volume)], currency, value_unit, base_asset, quote_asset, price_unit, volume_unit, ...)`.
- **Gotchas:** USD = USD-stablecoin quotes (USDT/USDC/…) ~1:1; a non-USD pair (`ETHBTC`) → `currency='BTC'` and is **rejected** by the USD failover client. Coinbase has no W1/MN1. `start`/`end` optional. Timestamps UTC.

```python
from vnfin import crypto, Interval; from datetime import date
h = crypto.client().get_klines("BTCUSDT", Interval.D1, date(2024,1,1), date(2024,3,1))
print(h.currency, h.bars[-1].close)   # 'USD' ...
```

## fx — reference rates (VND per 1 base; spot + annual history)

- **Entry (spot):** `vnfin.fx.get_rate(base, quote="VND", *, http_get=None, timeout=25.0)` → `FXRate`; `vnfin.fx.client()` → `FailoverFXClient` with `.get_rate(base, quote="VND")`; `vnfin.fx.source()` → `OpenErApiFXSource`; `vnfin.fx.VietcombankFXSource()` for bid/ask.
- **Entry (history, #159):** `vnfin.fx.history(base="USD", quote="VND", start=None, end=None, *, frequency=Frequency.ANNUAL)` → `FXHistory` (annual USD/VND via World Bank `PA.NUS.FCRF`, no key); `vnfin.fx.WorldBankFXHistorySource().get_history(...)`. `FXHistory.rate_on(date)` / `rate_for_year(year)` are **exact-match-or-raise** (never fill/interpolate).
- **Failover:** spot open.er-api → Vietcombank; history is single-source (World Bank).
- **Result:** `FXRate(base, quote='VND', rate, unit='VND per 1 {base}', as_of_utc, source, bid, ask)`; `FXHistory(base, quote, points=(FXPoint(date, rate),...), unit, frequency, source='worldbank_fx', ...)`.
- **Gotchas:** spot (`get_rate`/`FXRate`) is point-in-time; **history (`history`/`FXHistory`) is annual USD/VND only** (monthly + non-USD cross-quotes are v2; period-average rate, not year-end/SBV-central). Quote VND-only (else `InvalidData`). Unit is **VND per 1 base**. `bid`/`ask` only from Vietcombank (its `Transfer` is a commercial reference quote, not the SBV central rate). Sources cache ~1h (reuse one `client()`). Malformed ISO / unsupported pair / bad dates → `InvalidData` pre-network (facade **and** direct source).

```python
import vnfin
r = vnfin.fx.get_rate("USD"); print(r.rate, r.unit)   # 26111.0 'VND per 1 USD'
```

## macro — cross-country indicators

- **Entry:** `vnfin.macro.client()` → `MacroClient` with `.get_indicator(country_iso3, indicator)` (**no extra kwargs**); module `vnfin.macro.get_indicator(country_iso3, indicator, *, sources=..., max_attempts=..., http_get=..., timeout=...)`; `vnfin.macro.source()` → `WorldBankMacroSource`. `MacroIndicator`: `GDP, GDP_GROWTH, CPI, INFLATION, UNEMPLOYMENT` (the only 5).
- **Failover:** World Bank → IMF → DBnomics (all no-key). `FREDMacroSource(api_key=...)` is **BYOK-only** (`FRED_API_KEY`), excluded from the default chain. No BEA/BLS sources.
- **Result:** `IndicatorSeries(country, indicator_code, indicator_name, points: tuple[(date, float)] oldest-first, source, unit, value_unit, currency, frequency, projection_from_year, warnings)` + `.latest()`, `.latest_including_projections()`, `.actual_points`, `.to_dataframe()`.
- **Units (pinned):** GDP = `current US$` (USD); CPI = `index`; GDP_GROWTH/INFLATION/UNEMPLOYMENT = `%`. Never relabeled.
- **Gotchas:** `client.get_indicator(country, indicator)` takes no kwargs; the **module** function does. `latest()` excludes IMF WEO projections. Unknown indicator → `ValueError`; empty country → `InvalidData`; annual points stamped Jan 1.

```python
import vnfin.macro as macro
s = macro.get_indicator("VNM", macro.MacroIndicator.GDP)
print(s.unit, s.currency, s.latest())   # 'current US$' 'USD' (date, value)
```
