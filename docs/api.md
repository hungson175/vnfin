# Public API — coherent facade + naming standard (P1.4)

`vnfin` exposes **one obvious entry per domain**. Each domain owns its typed models and
units (see [units.md](units.md)); they are **not** funnelled through a single client that
would otherwise have to return incompatible result types behind one surface. Instead,
after `import vnfin` you reach each domain as an attribute:

```python
import vnfin

vnfin.prices        # equity OHLCV price history (VND)
vnfin.equities      # VN equity universe per board (HOSE/HNX/UPCOM)
vnfin.fundamentals  # financial statements (raw VND)
vnfin.funds         # mutual-fund NAV (VND / fund unit)
vnfin.indices       # index value (points) + constituents
vnfin.gold          # gold spot / history (VN domestic + world XAU)
vnfin.crypto        # crypto OHLCV (USD)
vnfin.fx            # FX reference rates (daily/current, VND per 1 unit)
vnfin.macro         # macroeconomic indicators
```

## Naming standard

**Standard domains** (`prices`, `fundamentals`, `funds`, `indices`, `crypto`, `macro`)
offer the predictable **factory verbs**:

| Verb | Meaning |
|------|---------|
| `client(...)` | The **failover client** for the domain (multi-source, ≤3 attempts, unit-homogeneity guard). This is the recommended entry. |
| `source(...)` | The **primary single-source adapter** only — no failover. Use it to pin one provider explicitly. |
| `history(...)` / `index_history(...)` / `get_financials(...)` | Domain-specific one-shot convenience functions (kept where they already existed). |

> `client()` is **not** an alias of `source()`. `client()` returns the failover
> chain; `source()` returns just the primary adapter. (The only standard domain
> whose `client()` is currently still effectively single-source is `funds` — no
> clean no-auth backup exists, accepted single-source for v0.1, so
> `client() == source()`; see [units.md](units.md) and
> [design/redundancy-failover.md](design/redundancy-failover.md).)

### `gold` is the deliberate exception

`gold` does **not** follow the `client()` + `source()` standard, because VN domestic
gold (**VND/lượng**) and world XAU (**USD/oz**) are different unit families — a single
cross-unit `client()` would be nonsensical. Instead `gold` exposes:

| Verb | Meaning |
|------|---------|
| `vn(provider="btmc")` | VN domestic spot source (**VND/lượng**): `"btmc"` (default) or `"pnj"`. |
| `world(provider="currency_api")` | World XAU source (**USD/oz**): `"currency_api"` (default) or `"gold_api"`. |
| `source(provider="btmc")` | Generic provider selector routing to both families (no default cross-unit chain). |
| `default_world_gold_client(...)` | The **world-gold-only** daily-history failover client (USD/oz; opt-in Stooq backup). There is no VN domestic failover client. |

See [Why gold takes an explicit provider](#why-gold-takes-an-explicit-provider).

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

# equities — the investable VN equity universe per board (SSI iBoard). Single-source
# (client() == source()); a data primitive only (NOT a screener/ranker/advisor).
src   = vnfin.equities.source()              # SsiIboardUniverseSource (client() == source())
uni   = vnfin.equities.universe("HOSE")      # EquityUniverse for one board
allu  = vnfin.equities.universe()            # merges HOSE + HNX + UPCOM (cross-board keep-first)
fpt   = next(s for s in vnfin.equities.universe("HOSE") if s.symbol == "FPT")  # one-symbol pattern

# fundamentals — financial statements (raw VND). Failover VNDirect -> CafeF.
c       = vnfin.fundamentals.client()        # FailoverFundamentalClient (VNDirect -> CafeF)
src     = vnfin.fundamentals.source()        # VNDirectFundamentalSource (primary only)
reports = vnfin.fundamentals.get_financials("FAKECORP", "income", "annual")  # uses the failover chain

# funds — mutual-fund NAV (VND/unit). No clean no-auth backup exists -> single-source (v0.1).
src   = vnfin.funds.client()                 # FmarketFundSource (accepted single-source; client() == source())
funds = src.list_funds()
holds = src.holdings(funds[0].id)            # tuple[FundHolding] — equities + bonds merged; each has
                                             # .instrument_type (STOCK/BOND/UNLISTED_BOND/OTHER) + .as_of_utc
alloc = src.asset_allocation(funds[0].id)    # AssetAllocation — asset-class split (equity/bond/cash)

# indices — index value (points) + members.
ic   = vnfin.indices.client()                # IndexClient
hist = vnfin.indices.index_history("FAKEINDEX", date(2024, 1, 1), date(2024, 6, 30))  # PriceHistory in points (start/end required)
# Long multi-year windows: opt-in calendar-year stitching (#147). Each year is fetched
# via the failover chain (routing around a source's single bad day), then stitched into
# one PriceHistory with source="stitched_index_history" and per-segment provenance
# warnings. Default index_history stays strict (unchanged).
hist = vnfin.indices.index_history_stitched("VNINDEX", date(2016, 1, 1), date(2026, 6, 1))  # D1 only

# gold — VN domestic (VND/lượng) and world XAU (USD/oz). Provider is explicit.
vn    = vnfin.gold.vn("btmc")                # BTMCGoldSource (default), or "pnj"
world = vnfin.gold.world("currency_api")     # CurrencyApiGoldSource (default), or "gold_api"
any_  = vnfin.gold.source("btmc")            # generic provider selector (vn + world)
# World-gold daily history has a failover client (currency-api; opt-in Stooq backup):
wc    = vnfin.gold.default_world_gold_client()  # FailoverGoldClient (USD/oz)

# crypto — OHLCV (USD). Failover Binance -> Coinbase.
c   = vnfin.crypto.client()                  # FailoverCryptoClient (Binance -> Coinbase)
src = vnfin.crypto.source()                  # BinanceCryptoSource (primary only)

# fx — daily/current FX reference rates (VND per 1 unit of base). Failover open.er-api -> Vietcombank.
c   = vnfin.fx.client()                       # FailoverFXClient (open.er-api -> Vietcombank)
src = vnfin.fx.source()                       # OpenErApiFXSource (primary only)
r   = vnfin.fx.get_rate("USD")                # one-shot FXRate; rate = VND per 1 USD (spot/current quote)
h   = vnfin.fx.history(start=date(2010, 1, 1), end=date(2024, 12, 31))  # FXHistory; annual USD/VND (period-average)

# macro — cross-country indicators. No-key failover World Bank -> IMF -> DBnomics.
c   = vnfin.macro.client()                   # MacroClient (World Bank -> IMF DataMapper -> DBnomics, no-key)
src = vnfin.macro.source()                   # WorldBankMacroSource (primary only)

# corp_actions — CASH dividends (VND/share) scraped from the VSDC depository. v1 CASH
# only; ex-date is ALWAYS None (depository publishes none, finfo leg held for v2).
hist = vnfin.corp_actions.dividends("FAKECORP", seed_id=197900)  # DividendHistory of CashDividendEvent
src  = vnfin.corp_actions.VsdcCashDividendSource()               # the VSDC scrape adapter
```

### Why gold takes an explicit provider

Gold spans two unit families — VN domestic (**VND/lượng**) and world XAU (**USD/oz**) —
so there is no single cross-unit default. `vnfin.gold.vn(...)`, `vnfin.gold.world(...)`,
and `vnfin.gold.source(provider=...)` make the choice explicit. Unknown provider names
raise `ValueError`.

## `vnfin.fx.history` — historical FX (annual USD/VND)

`vnfin.fx.history(...)` (issue #159) returns an `FXHistory` time series of `FXPoint`
(`date`, `rate` = quote per 1 base) — distinct from the spot `FXRate`, which is unchanged.

- `vnfin.fx.history(base="USD", quote="VND", start=None, end=None, *, frequency=Frequency.ANNUAL,
  http_get=None, timeout=25.0) -> FXHistory` — annual USD/VND from the no-key World Bank WDI
  `PA.NUS.FCRF` series. `start`/`end` are an inclusive **calendar-year** window (filtered by
  `.year`, so a mid-year `start` never drops that year's Jan-1-stamped point). v1 supports
  USD/VND + annual only — any other pair/frequency raises `InvalidData` (monthly and non-USD
  cross-quotes are deferred to v2).
- `FXHistory.rate_on(date) -> float` / `FXHistory.rate_for_year(year) -> float` — **exact-match
  or raise**; they never forward-fill, interpolate, or pick a nearest date.
- `FXHistory.to_dataframe()` — indexed by `date`, column `rate`, provenance in `df.attrs`.

The annual value is an annual **period-average** rate (not year-end, not the SBV central rate).
There is no asset-join/`normalize_to_vnd` helper — converting an asset series to VND is left to
the caller (a deliberate, separate design). See
[tutorials/fx-history.md](tutorials/fx-history.md) and
[sources/fx-history-worldbank.md](sources/fx-history-worldbank.md).

## `vnfin.fundamentals.metrics` — canonical metrics (additive, offline transform)

`vnfin.fundamentals.metrics(...)` (issue #157) is an additive, **offline** layer over the existing
`get_financials(...)` reports. It fetches income+balance+cashflow once each through the same failover
chain, then maps the verified VNDirect provider codes to a fixed **v1 catalog of 26 canonical
metrics** — 21 raw-mapped line items + 5 derived ratios — returning one `MetricReport` per fiscal
period (newest first). It **never fetches the `ratios` statement** (provider-native valuation ratios
are deferred to v2) and per-statement failures are non-fatal.

- `vnfin.fundamentals.metrics(symbol, period="annual", *, is_bank=None, limit=8, source=None,
  sources=None, max_attempts=3, http_get=None, timeout=25.0) -> tuple[MetricReport, ...]` — newest
  fiscal period first. Mirrors `get_financials`' injection knobs. `is_bank=None` (`AUTO`)
  auto-detects bank vs corporate from the first OK report.
- `vnfin.fundamentals.explain_metric_coverage(symbol, period="annual", *, is_bank=None, limit=8,
  source=None, sources=None, max_attempts=3, http_get=None, timeout=25.0) -> MetricCoverage` — same
  3-statement fetch, but **never raises** on a per-statement failure; one `PeriodCoverage` per fiscal
  date with per-statement provenance, per-metric availability + reasons, named/generic item counts,
  and unmapped codes. Designed for a batch loop over a universe.
- `vnfin.fundamentals.metric_catalog(applies_to=None) -> tuple[MetricDefinition, ...]` — pure, no
  network. `None` → all 26; `"bank"`/`AppliesTo.BANK` → `BANK`+`BOTH`; `"corporate"`/`"non_bank"`/
  `AppliesTo.CORPORATE` → `CORPORATE`+`BOTH`. Any other string raises `VnfinError`.
- `vnfin.fundamentals.explain_metric(metric_id) -> MetricDefinition` — pure lookup; accepts a
  `MetricId` or its string value. An unknown id (including a v2-deferred metric like `"roe"`) raises
  `VnfinError`.

**Result types** (all frozen dataclasses, importable from `vnfin.fundamentals`):

- `MetricReport(symbol, period, fiscal_date, is_bank, metrics: tuple[MetricValue, ...],
  statement_sources: tuple[StatementProvenance, ...], warnings)` — `.get(metric_id)` returns the
  `MetricValue` even when unavailable; `.to_dataframe()` is one row per metric (all 26). There is
  deliberately **no single `source`** field (provenance is per statement, `df.attrs` has no
  `"source"` key).
- `MetricValue(id, value, value_unit, kind, availability, fiscal_date, inputs, reason, warnings)` —
  `value` is `None` whenever `availability != "available"`; `reason` then carries the stable
  diagnostic string. `inputs` is per-value lineage (`MetricInput(statement, item_code, value,
  value_unit, fiscal_date, source, name)`).
- `MetricDefinition(id, name, category, kind, applies_to, value_unit, statement, codes_by_source,
  formula, inputs)` — a static catalog entry. v1 maps only the `"vndirect"` namespace.
- `MetricCoverage(symbol, period, periods: tuple[PeriodCoverage, ...], notes)` and
  `PeriodCoverage(fiscal_date, is_bank, statement_provenance, per_metric, named_item_count,
  generic_item_count, unmapped_codes, ratio_status)` — `ratio_status` is always `not_requested` in
  v1.

**Enums** (`.value` strings): `MetricKind` = `raw_mapped` / `provider_native` / `derived`;
`AppliesTo` = `corporate` / `bank` / `both`; `MetricCategory` = `profitability` / `liquidity` /
`leverage` / `cashflow` / `size`.

**`MetricValue.availability` statuses** (the per-value outcome):

- `available` — resolved; `value` is set.
- `missing` — line item / statement absent for this period (e.g. `"missing line item 11000 in income"`,
  `"missing statement cashflow for 2022-12-31"`, `"missing input metric net_revenue"`,
  `"denominator net_revenue is zero"`).
- `blocked` — the succeeding source's namespace is not mapped in v1 (e.g. `"metric map not available
  for source 'cafef'"`).
- `not_applicable` — the metric does not apply to this entity type (e.g. `"metric 'net_revenue' does
  not apply to bank entities"`).
- `unsupported` — reserved for v2 valuation metrics absent from the v1 catalog.

**`StatementProvenance.status` statuses** (per-statement, per-period): `ok` / `missing` /
`source_error` / `not_served` (CafeF does not serve cashflow → `not_served`).

The v1 catalog ships **21 raw-mapped** (corporate/bank/shared) + **5 derived** ratios (`gross_margin`,
`net_margin`, `liabilities_to_equity`, `cash_to_assets`, `operating_cash_flow_margin`); bank metrics
map only the #157-verified bank codes. Derived ratios are computed in-library with denominator guards
(zero/negative/non-finite → `missing`, never `inf`/`NaN`). See
[tutorials/fundamentals.md](tutorials/fundamentals.md#canonical-metrics--coverage) and
[design/fundamentals-metrics.md](design/fundamentals-metrics.md).

## `vnfin.diagnostics` — source-coverage preflight (offline)

`vnfin.diagnostics` is an additive, **offline** namespace for explaining source coverage
and source-limit gaps (issue #145) — metadata/preflight only, never a network call and
never fabricated data:

- `vnfin.diagnostics.source_capabilities() -> tuple[SourceCapability, ...]` — known,
  conservative coverage metadata for the source-limited legs (world-gold history,
  index constituents, FX history `worldbank_fx` — annual USD/VND).
- `vnfin.diagnostics.explain_world_gold_history(start, end) -> RequestDiagnostic` —
  classify a window as `coverage_gap` / `partial_coverage` / `window_too_wide` / `ok` vs the
  default source's known coverage start and max range width (the live `vnfin.gold.world(...)`
  history call fails fast with `EmptyData` for an entirely-pre-coverage window and raises
  `InvalidData` for a window wider than `_MAX_DAYS`; the diagnostic reports both blockers).
- `vnfin.diagnostics.explain_index_constituents(index) -> RequestDiagnostic` — canonicalize
  the selector and report the `single_source` (membership-only, no-weights) limitation.
- `vnfin.diagnostics.explain_fx_coverage(base="USD", quote="VND", start=None, end=None, *,
  frequency=None) -> RequestDiagnostic` (issue #159) — classify a historical-FX request as
  `unsupported_pair` / `unsupported_frequency` / `coverage_gap` / `ok` vs the only v1 source
  (World Bank `PA.NUS.FCRF`, annual USD/VND, `window_too_wide` is not applicable here).
- `vnfin.diagnostics.explain_corp_actions_coverage() -> RequestDiagnostic` (issue #163) —
  state the corporate-actions coverage: v1 serves CASH dividends only (VSDC depository
  scrape), `ex_date` is **UNAVAILABLE** (depository publishes none; finfo enrichment leg
  held for v2 with a pre-2022 floor), and STOCK/RIGHTS/BONUS are deferred to v2 (status
  `ex_date_unavailable`).

`SourceCapability` and `RequestDiagnostic` are frozen dataclasses. This is preflight
metadata, not a live health monitor (use `scripts/healthcheck.py` for live checks). See
[how-to/source-diagnostics.md](how-to/source-diagnostics.md).

## `vnfin.equities` — the VN equity universe (per board)

`vnfin.equities` is an additive domain namespace (issue #167) that enumerates the
investable VN equity universe per board from the public SSI iBoard stock-group endpoint.
It is a **data primitive only** — NOT a screener/ranker/advisor. Single-source
(`client()` is an alias of `source()`, mirroring `funds`):

- `vnfin.equities.universe(exchange=None, *, http_get=None, timeout=25.0) -> EquityUniverse`
  — one-shot enumeration. `exchange="HOSE"` (or `"HNX"`/`"UPCOM"`) returns one board;
  `exchange=None` merges all three boards with cross-board keep-first dedup (board order
  HOSE, HNX, UPCOM). An unknown board raises `InvalidData` **before** any network call.
- `vnfin.equities.source(...)` / `vnfin.equities.client(...)` — construct a
  `SsiIboardUniverseSource` (`.universe(exchange=...)`).
- `EquitySecurity` / `EquityUniverse` are frozen dataclasses. `EquityUniverse` supports
  `len()`, iteration, `.symbols`, and `.to_dataframe()`. Each `EquitySecurity` carries
  `symbol`, `exchange`, `company_name_en`, `company_name_vi`, `isin`, `listing_status`,
  `par_value`, `currency` — every optional field is `None` when the provider omits it
  (never fabricated).

`profile(symbol)` is **deferred**: to get one symbol, call `universe(exchange=...)` and
filter (`next(s for s in universe("HOSE") if s.symbol == "FPT")`). The result's
`warnings` ALWAYS disclose the known gaps — `partial_universe_coverage` (index-basket
derived, ~96% of the full SSC roster), `listing_date_not_available` (provider
`firstTradingDate` is `'0'`), `sector_not_available` — plus `cross_board_duplicate_symbol`
on a merge. See [sources/equities-universe.md](sources/equities-universe.md).

## `vnfin.corp_actions` — cash dividends (VND/share, VSDC scrape)

`vnfin.corp_actions` is an additive domain namespace (issue #163) serving **v1 CASH
dividends** scraped from the VSDC (Vietnam Securities Depository & Clearing) public
announcement pages (`https://vsd.vn/vi/ad/{id}`). The depository publishes the record
date, the pay date, and the ratio/cash per share — but **no ex-date** — so in v1:

- **ex-date is ALWAYS `None`** (the VNDirect finfo enrichment leg is held for v2); every
  `CashDividendEvent` carries the `ex_date_unavailable` token. Never fabricated/derived.
- **CASH dividends only** — STOCK / RIGHTS / BONUS are deferred to v2.
- the source is an **HTML scrape** (more fragile than the library's JSON sources): a
  recognized cash dividend whose amounts cannot be parsed keeps `cash_per_share` /
  `ratio_pct` as `None` and carries `vsdc_parse_degraded` (never silently dropped), and
  every `DividendHistory` carries `corp_action_source_partial` (the VSDC spine alone).

- `vnfin.corp_actions.dividends(symbol, *, start=None, end=None, http_get=None,
  timeout=25.0, seed_id=None, max_fetch=300) -> DividendHistory` — discover (a supplied
  `seed_id`, else a bounded recent-ID window scan), crawl the seed's same-org sidebar,
  fetch+parse each page, and return the company's cash-dividend events within
  `[start, end]` (by record date). `currency="VND"`.
- `vnfin.corp_actions.VsdcCashDividendSource(...)` — the scrape adapter
  (`.dividends(...)`, `.parse_announcement(html)`, `.discover_same_org_ids(html)`).
- `CashDividendEvent` / `DividendHistory` / `CorpActionSource` are the typed models +
  port. `CashDividendEvent` carries `code`, `kind` (always `"CASH"`), `cash_per_share`,
  `ratio_pct`, `ex_date` (`None`), `record_date`, `pay_date`, `div_year`, `source`,
  `as_of` (provider publish time), `exchange`, `announcement_id`, `warnings`.

Use `vnfin.diagnostics.explain_corp_actions_coverage()` for the offline coverage
statement. See the warning-tokens table in the skill for the always-present tokens.

## `vnfin.news` — daily financial-news headlines (BYOK)

`vnfin.news` is an additive domain namespace for **daily/historical headline metadata**
(issue #140) via Alpha Vantage's official `NEWS_SENTIMENT` API — **bring-your-own-key**,
metadata only, **no raw scraping / full text / real-time**:

- `vnfin.news.search(*, tickers=None, topics=None, start=None, end=None, sort="latest",
  limit=50, provider="alpha_vantage", api_key=None, ...) -> NewsResult` — one-shot search
  (requires at least one of `tickers`/`topics`).
- `vnfin.news.source(provider="alpha_vantage", *, api_key=None, ...)` — construct a source
  (v1 supports only `alpha_vantage`).
- `NewsItem` / `NewsResult` are frozen dataclasses; `AlphaVantageNewsSource` is the adapter.

The API key comes from `api_key=` or the `ALPHAVANTAGE_API_KEY` env var (no no-key default;
a missing key raises `SourceUnavailable`, with the key redacted from all errors). Results
are links + provider metadata/sentiment only — never article bodies. See
[design/news-sources.md](design/news-sources.md) and [how-to/news.md](how-to/news.md).

## `vnfin.liquidity` — daily liquidity & position sizing (offline)

`vnfin.liquidity` is an additive, **offline** namespace (issue #146) that derives
liquidity/marketability stats and a max-order estimate from an existing daily
`PriceHistory` — never a new data source, never provider-published turnover:

- `vnfin.liquidity.from_price_history(history, *, adv_fraction=0.10, capital_vnd=None) -> LiquidityProfile`
- `vnfin.liquidity.profile(symbol, start, end, *, adv_fraction=0.10, capital_vnd=None, client=None, ...) -> LiquidityProfile`
- `LiquidityPoint` / `LiquidityProfile` are frozen dataclasses.

Traded value is `close * volume` (`value_kind="close_x_volume_estimate"`, with a warning) —
an estimate, not a turnover field. Accepts only daily VND equity series (index points /
crypto / non-VND rejected). See [design/liquidity-position-sizing.md](design/liquidity-position-sizing.md)
and [how-to/liquidity.md](how-to/liquidity.md).

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
