# Changelog

All notable changes to `vnfin` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/) — see [`docs/stability.md`](docs/stability.md).

## [Unreleased]

### Documentation
- **World-index deployment reality clarified** (#184) — `docs/sources/indices-world.md` (+ the skill
  world-index entries and the adapter docstrings) now state explicitly that from a **server /
  datacenter IP with no `ALPHAVANTAGE_API_KEY`**, `vnfin.indices.world("SPY", ...)` raising
  `AllSourcesFailed` is the **expected** outcome — not a transient bug or a flaky test: the keyless
  BYOK AV primary is skipped *and* the keyless Stooq `^SPX` fallback is structurally anti-bot-blocked
  from datacenter IPs (residential-only, dead from servers since ~2020-12). Set the BYOK AV key to use
  world-index server-side. No code or chain change; Stooq stays in the chain as the residential-only
  keyless path. ([#184](https://github.com/hungson175/vnfin/issues/184))
- **Warning-token guard hardened to forward-discovery** (#188) — `tests/_warning_token_scan.py`
  AST-scans every `result.warnings` emission site in `vnfin/` and asserts the discovered token set is a
  subset of the documented `_WARNING_TOKENS_180`, so a newly-emitted-but-undocumented token now fails
  the doc↔code lockstep guard red (closing the forward-direction blind spot in the #180 reverse guard).
  Test-infrastructure only; no public-API change. ([#188](https://github.com/hungson175/vnfin/issues/188))
- **Maintainer architecture docs synced to the v0.2 domain surface** — `docs/architecture/system-overview.md`
  and `docs/architecture/data-domains.md` now document the `vnfin.equities` (#167) and `vnfin.corp_actions`
  (#163) domains (facade count 12→14, domain table + sections), and `docs/api.md` adds
  `explain_fixed_income_coverage()` (#152), the `LENDING_RATE`/`DEPOSIT_RATE`/`REAL_INTEREST_RATE`
  indicators (#152), and the `board_unavailable` (#189) / `current_snapshot_only` (#175) tokens. Docs only.

### Added
- **World-index coverage to 8 symbols** (#197) — `vnfin.indices.world` now adds three
  canonical, loudly-labeled Asian USD ETF proxies to the existing #193 set:
  `^KS11`→EWY (KOSPI Composite proxy; MSCI Korea 25/50 ETF), `^CSI300`→ASHR (CSI 300 ETF
  price, not raw CNY index points), and `^HSI`→EWH (Hang Seng proxy; MSCI Hong Kong
  25-50 ETF). The existing five entries (`SPY`, `QQQ`, `^N225`, `^SSEC`, `^STI`) keep
  their order and labels. No aliases were added; unsupported symbols such as `^DAX` and
  `^FTSE` still raise before network and are never served as SPY/Stooq `^SPX`. No new
  warning token: all six raw-index asks reuse `proxy_substitution` plus structured
  `PriceHistory.proxy_for` and FX-pair disclosure. ([#197](https://github.com/hungson175/vnfin/issues/197))
- **Public annual silver + platinum history — `vnfin.metals`** (#196) — a new public domain serving
  annual precious-metals price history (USD/oz) from the **World Bank Commodity Markets "Pink Sheet"**
  annual `.xlsx` — the same workbook the internal gold annual source (#185) reads, now via one
  **shared, domain-neutral stdlib parser** (`vnfin/_contracts/worldbank_cmo.py`, `parse_cmo_annual(raw,
  spec)`) parameterized per metal by a frozen `MetalSpec`. Gold's observable output is **byte-for-byte
  identical** to its pre-extraction behaviour (`WorldBankCmoGoldSource` unchanged). New surface:
  **`vnfin.metals.history(metal, start, end)`** → a `MetalHistory` of `MetalBar` (one Jan-1-stamped
  point per calendar year), **`vnfin.metals.source(metal)`**, **`vnfin.metals.SUPPORTED_METALS ==
  ("silver", "platinum")`**. `metal` accepts a name (`"silver"`/`"platinum"`) or ISO-4217 code
  (`"XAG"`/`"XPT"`). **Never-fabricate:** `history("gold")`/`"XAU"` raises `InvalidData` **routing the
  caller to `vnfin.gold`** (gold annual history stays there, untouched); any other unsupported metal
  (`"palladium"`/`"XPD"`/`"copper"`/…) raises `InvalidData` **naming the metal**, raised **before** any
  network call. **Never-silent:** every `MetalHistory` carries typed `frequency="annual"` and the CC-BY
  `attribution` (no new `result.warnings` token). Per-metal plausibility bands (`Silver [0.10, 75.0]`,
  `Platinum [50.0, 5000.0]` USD/oz) are re-derived per metal from each metal's own measured range — a
  magnitude backstop behind the split-header name-match, exploiting that silver's all-time ceiling sits
  below platinum's floor so an adjacent-column mis-read is rejected. Annual only (no palladium, no
  daily/spot). ([#196](https://github.com/hungson175/vnfin/issues/196))
- **Derived GICS L1 sector classification for equities** (#195) — `vnfin.equities` now derives the
  GICS L1 sector for VN equities **clean-room**, by inverting the 10 VNAllShare sector index baskets it
  already fetches via `vnfin.indices` (no vnstock; no `industryID`/`industryIDv2`/`industry_name`). New
  primitives: **`vnfin.equities.profile(symbol)`** (un-defers the previously-deferred `profile` —
  returns a disclosure-carrying **`EquityProfile`** that wraps the symbol's full sector-enriched
  `EquitySecurity` in `.security` plus an always-on `sector_partial_coverage` coverage line in
  `.warnings`, so the single-symbol entry point is never silent about the HOSE-only ~74% derivation),
  **`vnfin.equities.sectors()`** (the
  static 10 `GicsSector(code, name)` pairs — no fetch), **`vnfin.equities.by_sector(code_or_name)`**
  (one sector's basket members; accepts a code `"VNFIN"` or GICS name `"Financials"`, case-insensitive),
  and a new **`universe(..., with_sector=True)`** opt-in that enriches each row. `EquitySecurity` gains
  four additive `Optional[str]` fields (`sector_code`/`sector_name`/`sector_scheme`/`sector_source`),
  and three new result types (`GicsSector`, `EquitySector`, `EquityProfile`) are exported. **Honest coverage:** the
  baskets are **HOSE-only (~74%)** and **current-snapshot** (survivorship), so an unmapped HOSE symbol
  and **every** HNX/UPCoM symbol keep all four sector fields `None` **as a unit** (never fabricated), and
  a multi-basket symbol degrades to a deterministic `None` — all disclosed via the new
  **`sector_partial_coverage`** warning token (which replaces the per-board `sector_not_available` on the
  enriched path; the plain default `universe()` is byte-for-byte unchanged, with no basket fetch). The
  inverted map is built once (≤10 fetches) and cached 6h per process. The finer
  `industries()`/`industry_peers()` tier is intentionally **not** shipped (no clean finer data).
  ([#195](https://github.com/hungson175/vnfin/issues/195))
- **World-index coverage to 5 symbols + keyless-from-server reliability** (#193) — `vnfin.indices.world`
  now serves **`SPY`, `QQQ`, `^N225`, `^SSEC`, `^STI`** (was SPY only), ALL via Alpha Vantage
  `TIME_SERIES_DAILY` in **USD** (US-listed ETFs) through a declarative per-symbol mapping. `SPY`→SPY
  and `QQQ`→QQQ are direct; the three Asian indices are **loudly-labeled USD ETF proxies** —
  `^N225`→EWJ, `^SSEC`→FXI, `^STI`→EWS. A proxy result carries BOTH a new structured
  **`PriceHistory.proxy_for`** field (the asked index; `None` for a direct result — additive, defaulted)
  AND a new **`proxy_substitution`** warning token. **Caveats (documented prominently):** the proxy ETFs
  embed USD/local FX and are **not faithful trackers** (EWJ≠Nikkei 225, FXI≠SSE Composite, EWS≠STI); and
  v1 world series are **PRICE-RETURN, not total-return** (dividends not reinvested — material over
  10–25y). **Reliability:** with **no `ALPHAVANTAGE_API_KEY`** and the keyless Stooq fallback walled
  (datacenter anti-bot), `world(...)` now raises a new **`MissingKey`** (naming the env var + the symbol,
  trail-free) — the actionable config signal — instead of an opaque `AllSourcesFailed`; `AllSourcesFailed`
  is reserved for a key-set-but-AV-failed chain. An AV error/no-data envelope for an allowlisted symbol
  raises `InvalidData` **naming the symbol** (never an empty/fabricated series). All changes are
  additive (the v0.2 surface snapshot is unchanged). See
  [`docs/sources/indices-world.md`](docs/sources/indices-world.md).
  ([#193](https://github.com/hungson175/vnfin/issues/193))
- **Richer Fmarket fund metadata + allocation coverage diagnostics** (#155) — the `vnfin.funds`
  domain now serves a confirmed metadata core, never fabricated. `Fund` gains three appended,
  defaulted optional fields: `management_fee_pct` (annual management fee %, populated from the
  **list** row — equity rows only, `None` when the provider omits it), `inception_date`, and
  `description`. `AssetAllocation` (returned by `asset_allocation(id)`) gains `sector_weights`
  (a tuple of the new frozen `SectorWeight(industry, weight_pct)` model, parsed fail-closed —
  malformed rows are dropped), plus `inception_date` and `description` off the detail document.
  `list_funds(...)` takes a new appended `include_metadata=True` keyword (set `False` for a
  fee-agnostic list with no `fund_missing_fees` warning). Two new never-silent warning tokens:
  `fund_missing_fees` (list-level: ≥1 fund has no disclosed management fee — an absent fee is
  never mistaken for zero) and `fund_partial_holdings` (detail-doc: disclosed top holdings sum to
  under 50% of NAV — a bounded false-positive preferred over hiding an opaque book). Adds the
  **offline** diagnostic `vnfin.diagnostics.explain_fund_coverage()` (status
  `metadata_core_available`) + a `funds` `SourceCapability`, stating the available core vs the
  source-missing/deferred fields (`benchmark`, `risk-category`, a flat subscription/redemption fee —
  the provider exposes only a tiered `productFeeList[]` schedule — and a factsheet URL). Additive
  only: all new `Fund`/`AssetAllocation` fields are appended and defaulted, the new `list_funds`
  parameter is an appended keyword, and `SectorWeight` + the diagnostic are new exports.
  ([#155](https://github.com/hungson175/vnfin/issues/155))
- **`vnfin.corp_actions.dividends(...)` — the VSDC cash-dividend spine** (#163) — a new additive
  `vnfin.corp_actions` domain serving **v1 CASH dividends** scraped from the VSDC (Vietnam Securities
  Depository & Clearing) public announcement pages (`https://vsd.vn/vi/ad/{id}`), returning a
  `DividendHistory` of typed `CashDividendEvent` (`code`, `kind="CASH"`, `cash_per_share` VND/share,
  `ratio_pct`, `record_date`, `pay_date`, `div_year`, `as_of` = the provider's own publish time,
  `exchange`, `announcement_id`, `warnings`). Discovery is a **bounded multi-hop BFS** over the
  same-org "Tin cùng tổ chức" sidebar graph from a `seed_id` (auto-found via a bounded recent-ID
  window scan when omitted), with a visited-set cycle guard and a single fetch per page, capped by
  `max_fetch` (a positive int — a non-positive budget raises `InvalidData`). The pure parser pairs
  label→value by the `item-info` / `item-info-main` CSS classes (never by `col-md-*` width), binds
  each cash amount to the `%/cổ phiếu` ratio **closest before** its `được nhận … đồng` parenthetical
  (never the first % on a bundled line), and isolates all HTML parsing behind a tight, fixture-pinned
  contract. **Scope/limits, disclosed via never-silent warning tokens:** `ex_date` is **ALWAYS `None`**
  in v1 — the depository publishes no ex-date and the VNDirect finfo enrichment leg is **held** for v2
  (pre-2022 floor noted) — so every event carries `ex_date_unavailable` (never fabricated/derived);
  every result carries `corp_action_source_partial` (the VSDC depository spine alone); a recognized
  cash dividend with ≥1 unparseable PRIMARY field (the record date, or both ratio and cash) keeps those
  fields `None` and carries `vsdc_parse_degraded` (surfaced, never dropped — an undated event is then
  windowed by its `pay_date`); and an incomplete crawl is disclosed per-result via
  `coverage_truncated_at_max_fetch` (stopped at `max_fetch` with the frontier unexhausted) and
  `corp_action_fetch_incomplete` (≥1 same-org page failed to fetch). STOCK / RIGHTS / BONUS dividends
  are deferred to v2. Also adds the **offline** diagnostic
  `vnfin.diagnostics.explain_corp_actions_coverage()` (status `ex_date_unavailable`) stating the
  cash-only + ex-date-unavailable + v2 scope and a `corp_actions` `SourceCapability`. Additive only:
  new domain + diagnostic, no change to existing surfaces. ([#163](https://github.com/hungson175/vnfin/issues/163))
- **Annual fixed-income rate indicators + `explain_fixed_income_coverage()`** (#152) — three new
  `MacroIndicator` members reachable through the existing macro domain
  (`vnfin.macro.get_indicator(iso3, ...)` + failover): `LENDING_RATE` (World Bank WDI `FR.INR.LEND`),
  `DEPOSIT_RATE` (`FR.INR.DPST`), and `REAL_INTEREST_RATE` (`FR.INR.RINR`) — all **annual**, `% p.a.`,
  served by the same no-key CC-BY 4.0 World Bank source as GDP/CPI. World Bank is the only source that
  maps them, so each resolves to a single-source annual chain (IMF DataMapper / DBnomics return
  `supports()==False` and are skipped without a network call). Also adds a new **offline** diagnostic
  `vnfin.diagnostics.explain_fixed_income_coverage()` that (a) states the government-bond **yield
  CURVE** is UNAVAILABLE (no clean redistributable no-key source — DEFERRED, no `vnfin.bonds`
  namespace), (b) enumerates what IS available — `policy_rate` (DBnomics/IMF-IFS `FPOLM_PA` monthly
  monetary-policy **proxy**, stale ~Dec 2023) and the three World Bank annual rates, (c) discloses that
  `deposit_rate` is an annual **aggregate** with no clean per-tenor retail source, and (d) distinguishes
  policy vs interbank vs deposit vs government-bond yields so callers do not conflate them. Additive
  only: new enum members + WB `_WB_MAP` entries + one diagnostic; no signature/result-type change,
  existing `policy_rate`/GDP/CPI paths unchanged. ([#152](https://github.com/hungson175/vnfin/issues/152))
- **`current_snapshot_only` — current-vs-point-in-time disclosure on `index_constituents`** (#175,
  Tier-1) — `vnfin.indices.index_constituents(...)` now appends an **always-present, never-silent**
  `current_snapshot_only` token to `IndexConstituents.warnings` on every successful basket, disclosing
  that the membership is the **CURRENT** basket as fetched, NOT a point-in-time/historical snapshot, so
  backtests using it inherit survivorship and look-ahead bias. The SSI group endpoint exposes no
  provider data/effective date, so `IndexConstituents.as_of` stays the honest `None` — never fabricated
  from `now()` or the fetch clock. Additive only: no `index_constituents` signature change and no
  result-type/surface change (the `as_of` field already existed). Point-in-time/historical membership
  lookup is out of scope (source-gated). ([#175](https://github.com/hungson175/vnfin/issues/175))
- **`fund_nav_stale` — list-level NAV-staleness warning on `FundList`** (#190) — `funds.list_funds()`
  now appends a single `fund_nav_stale` token to `FundList.warnings` when ≥1 listed fund's own
  `nav_as_of` is older than 7 calendar days, ending the silent staleness that #172/#173 fixed for
  series results. The detail enumerates the stale fund codes@date (capped at 5 + `+M more` so a
  wholesale outage stays bounded); it is leak-safe (codes + dates only, no exception trail). Funds
  with an unknown `nav_as_of` (`None`) are never flagged — unknown is not stale and a date is never
  invented. Additive only: no `list_funds` signature change and no result-type change.
  ([#190](https://github.com/hungson175/vnfin/issues/190))
- **`Fund.nav_as_of` — the provider's own per-fund NAV date** (#181) — an additive optional
  `Optional[date]` field on the frozen `Fund` result, parsed from the Fmarket filter row's
  `extra.lastNAVDate` (epoch-ms at VN-local midnight) and converted to the VN calendar date so callers
  can tell how fresh `nav` is. Never fabricated: absent/null/non-positive/garbage `lastNAVDate` →
  `None` (no raise). ([#181](https://github.com/hungson175/vnfin/issues/181))
- **`vnfin.equities.universe(...)` — the investable VN equity universe per board** (#167) — a new
  additive `vnfin.equities` domain that enumerates the investable equities per board (HOSE/HNX/UPCOM)
  from the public SSI iBoard stock-group endpoint, with source-backed per-symbol reference metadata
  (`symbol`, `exchange`, `company_name_en/vi`, `isin`, `listing_status`, `par_value`, `currency`) and
  honest coverage diagnostics. It is a **data primitive only** — NOT a screener/ranker/advisor.
  Single-source (`vnfin.equities.client` is an alias of `vnfin.equities.source`, mirroring `funds`);
  the board token is non-obvious (plain HOSE/HNX/UPCOM return empty, so the source maps
  `HOSE→VNINDEX`, `HNX→HnxIndex`, `UPCOM→HNXUpcomIndex`) and only `stockType=='s'` rows are kept
  (warrants/ETFs/funds dropped). `universe(exchange=None)` merges all three boards with **cross-board
  keep-first** dedup (board order HOSE, HNX, UPCOM → `board="ALL"`); an unknown board raises
  `InvalidData` before any network. Frozen `EquitySecurity`/`EquityUniverse` result types
  (`len()`/iteration/`.symbols`/`.to_dataframe()`); every optional field is `None` when the provider
  omits it (never fabricated). Never-silent `warnings`: the three always-present honest-gap tokens
  `partial_universe_coverage` (index-basket derived, ~96% of the full SSC roster),
  `listing_date_not_available` (provider `firstTradingDate` is `'0'`), `sector_not_available`, plus
  `cross_board_duplicate_symbol` on a merge. `profile(symbol)` is deferred (filter `universe(...)`).
  See [`docs/sources/equities-universe.md`](docs/sources/equities-universe.md).
  ([#167](https://github.com/hungson175/vnfin/issues/167))
- **Optional interval/resample on `prices.history` + `index_history`** (#183) — both daily-native
  accessors now accept the existing `interval` arg as an `Interval` member **or** a pandas-style
  alias string (`'D'/'W'/'M'/'Q'/'Y'`, case-insensitive). Default `Interval.D1` is unchanged
  (back-compat passthrough — existing callers untouched). Coarser periods (`W1`/`MN1`/`Q1`/`Y1`) are
  aggregated **client-side** from the fetched daily series (pure in-memory OHLC aggregation — no new
  source, no new network call): `open`=first, `high`=max, `low`=min, `close`=last, `volume`=sum per
  calendar period, with each aggregated bar labelled at the **last actual trading day** in the period
  (a real market date, never a synthetic calendar boundary). OHLC-per-period for BOTH prices (VND) and
  index (points) — units/`source`/metadata are preserved. **Two new additive `Interval` members:
  `Q1="1Q"` (calendar quarter) and `Y1="1Y"` (calendar year)**, resample-only (each source's
  `supports()` gates native serving, so crypto/world sources cleanly reject them). The pandas alias
  **`'M'` maps to `MN1` (MONTH), never `M1` (one minute)** — the single highest-risk mapping, with a
  dedicated test. **`D1` and the intraday intervals (`M1/M5/M15/M30/H1`) are unchanged** — they pass
  straight through to the native fetch (the resample layer only handles the coarser-than-daily
  `W1`/`MN1`/`Q1`/`Y1`, which the VN sources do not serve natively). #183 introduces **no** behavior
  change for existing daily or intraday callers — it is purely additive; a truly-unsupported interval
  is still rejected by the source's own capability gate (`UnsupportedInterval`), as before. Resampled results
  are never-silent: `warnings` always contains `resampled_from_d1` (the series discloses it is
  aggregated, not native), plus a `resample_partial_period` warning when the first/last emitted bar
  covers an incomplete calendar period relative to the requested window (the partial bars are KEPT,
  not dropped). The network still fetches the full **daily** range — the win is the returned row count
  (10y → ~10 yearly / ~120 monthly rows vs ~2,500 daily), which is the reported pain (agent context
  overflow on long pulls). `index_history_stitched` resample is a tracked **follow-up** (it stays
  D1-only). See [`docs/tutorials/stock-prices.md`](docs/tutorials/stock-prices.md),
  [`docs/tutorials/funds-and-indices.md`](docs/tutorials/funds-and-indices.md),
  [`docs/design/prices-index-resample.md`](docs/design/prices-index-resample.md).
  ([#183](https://github.com/hungson175/vnfin/issues/183))
- **World Bank CMO annual gold is now the primary world-gold leg of `world_reference_history_vnd`**
  (#185) — `vnfin.gold.world_reference_history_vnd(...)` now fetches its world-gold leg from a new
  **internal** `WorldBankCmoGoldSource` (World Bank Commodity Markets "Pink Sheet" **annual `.xlsx`**,
  XAU/USD, no key) **as the primary**, falling back to the existing daily `CurrencyApiGoldSource →
  StooqGoldSource` path only on a recoverable `SourceError`. This **unblocks the synthesis
  server-side**: the daily legs are unfetchable from a datacenter host (CurrencyApi sparse + ~1100-day
  cap, Stooq anti-bot-blocked), so the 50% coverage gate correctly failed safe and the call could not
  run. CMO is **annual** and reachable, and because CMO gold IS *"spot average of daily rates"*
  (LBMA-sourced — already an annual average of daily spot) it is a **lossless drop-in**: the
  `annual-avg × annual-avg` basis and **every #178 output, warning and guard are preserved unchanged**
  (the pure synthesis is byte-identical — one CMO annual bar per year means `mean(one) = that value`).
  CMO is fetched **directly**, bypassing `FailoverGoldClient` whose daily-weekday coverage gate would
  wrongly reject a 1-bar-per-year series; it self-validates instead (non-finite/`<=0`,
  duplicate/non-monotonic year, and a plausible **20…10000 USD/oz** magnitude band, all →
  `InvalidData`; `EmptyData` if no years fall in the span). When the daily fallback engages, the result
  carries a never-silent **`world_reference_gold_source_fallback`** warning. The xlsx is parsed with
  **stdlib only** (`zipfile` + `xml.etree` — no openpyxl/pandas, so vnfin's only core dep stays
  `httpx`): the `Annual Prices (Nominal)` sheet is resolved via workbook+rels (not a hard-coded sheet
  number) and the gold column is located by its **split header** (`Gold` name cell + `($/troy oz)`
  units cell directly below, same column) — never a hard-coded index, since both shift between
  vintages. A supporting additive transport helper **`HttpDataSource._request_bytes`** (+ a
  keyword-only `binary=` path on `_default_http_get`/`_fetch_with_retry`) fetches binary payloads;
  it is fully backward compatible (every existing text/JSON caller is unchanged). The CMO source class
  stays **internal** — the public API surface is **unchanged**. License: World Bank CMO data is
  **CC-BY 4.0** (*"Source: The World Bank — Commodity Markets (Pink Sheet)"*); runtime-fetch only, no
  bundled rows. See [`docs/sources/cmo-gold-annual.md`](docs/sources/cmo-gold-annual.md),
  [`docs/sources/gold-world-reference.md`](docs/sources/gold-world-reference.md).
  ([#185](https://github.com/hungson175/vnfin/issues/185))
- **World-reference VND/lượng gold history** (#178) — new `vnfin.gold.world_reference_history_vnd(start,
  end, *, http_get=None, timeout=25.0, max_attempts=3)` returning a `GoldHistory` in **`VND/luong`**,
  **ANNUAL** (one Jan-1 point per calendar year). It composes the existing world-gold daily history
  (USD/oz; `CurrencyApiGoldSource` → `StooqGoldSource` failover — a multi-year window exceeds
  CurrencyApi's ~1100-day range and **fails over to Stooq**, the only full-history world-gold source)
  with annual USD/VND FX (World Bank `PA.NUS.FCRF`, via `vnfin.fx.history`):
  `VND/lượng[y] = annual_avg(gold_USD/oz)[y] × annual_USD_VND[y] × (GRAMS_PER_LUONG / GRAMS_PER_TROY_OZ)`,
  the oz→lượng factor (37.5 / 31.1035 ≈ **1.20565**) computed from named, auditable constants. The
  basis is annual to match the annual-only FX (a daily output would imply false daily-FX precision).
  `start`/`end` are interpreted as an inclusive **calendar-year** window — each year's gold mean is
  computed from the full calendar year (the fetch window is snapped to `Jan-1…Dec-31`), matching the
  FX leg so a mid-year bound never yields a partial-year mean; the world-gold leg's own soft
  `partial_coverage` warning (a gappy-but-accepted series) is forwarded (namespaced by leg). The one
  unavoidable partial year — the **in-progress current year**, whose mean is only year-to-date —
  carries its own mechanical `world_reference_trailing_year_incomplete` warning, flagged independently
  of the (dilutable) coverage aggregate so the trailing point is never read as a settled full-year value.
  **This is the world-gold-implied VND value, NOT the VN domestic (SJC/BTMC) price** — domestic gold
  trades a large, time-varying premium (historically **+10–21%**) above it, so the series understates
  the domestic price. It self-discloses **redundantly**: the accessor name, `product="XAU/VND
  (world-reference)"`, `value_unit="VND/luong"`, `source="world-gold (failover) × USD/VND (World
  Bank)"`, and an always-present mechanical **`world_reference_excludes_domestic_premium`** warning
  (plus a `world_reference_annual_basis` note). Year alignment is an honest intersection: an empty
  overlap raises `EmptyData`, dropped years emit a `world_reference_partial_year_coverage` warning, and
  a total failure of either leg propagates (`AllSourcesFailed` / `EmptyData`) — never a silent
  half-result. `vnfin.gold.domestic_history(...)` is **reserved**: it raises a clear source-gap
  diagnostic (no clean-room multi-year domestic source vetted yet — tracked in #182) and never falls
  back to this synthesis. Additive new exports `world_reference_history_vnd`, `domestic_history` under
  `vnfin.gold`. See [`docs/sources/gold-world-reference.md`](docs/sources/gold-world-reference.md),
  [`docs/ai-usage.md`](docs/ai-usage.md).
  ([#178](https://github.com/hungson175/vnfin/issues/178))
- **World/US equity index (S&P 500) accessor** (#177) — new `vnfin.indices.world(symbol="SPY",
  start=None, end=None, *, interval=Interval.D1)` returning the shared `PriceHistory` over its **own**
  2-source failover chain, separate from the VN HOSE/HNX index path (which is untouched).
  `AlphaVantageIndexSource` is the **PRIMARY**, bring-your-own-key source (Alpha Vantage
  `TIME_SERIES_DAILY` for the **SPY ETF**, an S&P 500 proxy; reuses the existing `ALPHAVANTAGE_API_KEY`;
  keyless → skipped with **no network call**; the key is **redacted** from every error; free-tier
  `Note`/`Information` throttle → `SourceUnavailable` so the chain falls over; in-memory `cache_ttl`
  defaults to 6h). `StooqIndexSource` is the keyless best-effort **FALLBACK** (Stooq `^SPX` daily CSV,
  the S&P 500 **index level** in points; anti-bot HTML → `SourceUnavailable`). The two legs are
  **different instruments** (SPY `USD/share` ~600 vs ^SPX `index points` ~6000, ~10× magnitude), so the
  chain is intentionally cross-instrument and **not** unit-homogeneous (only one disclosed leg is served
  per call; the result self-discloses via `source`/`value_unit`/`provider_symbol`). Whenever the ^SPX
  fallback is served instead of the requested SPY — covering both the AV-throttle and keyless-skip paths
  — the result carries a mechanical **`fallback_instrument_served`** warning naming the ~10× substitution
  (never silent; rebase before comparing). v1 supports **`symbol="SPY"` only** (any other symbol →
  clear `InvalidData`). All changes are additive; SPY is fetched as a documented proxy (not the
  proprietary `^GSPC`). New `AlphaVantageIndexSource`, `StooqIndexSource`, `default_world_index_sources`,
  `default_world_index_client`, `FailoverWorldIndexClient` exports under `vnfin.indices`. See
  [`docs/sources/indices-world.md`](docs/sources/indices-world.md),
  [`docs/ai-usage.md`](docs/ai-usage.md).
  ([#177](https://github.com/hungson175/vnfin/issues/177))
- **Monthly CPI YoY + SBV policy-rate indicators** (#179) — two new `MacroIndicator` members,
  both served via the existing keyless DBnomics/IMF-IFS path (no new adapter): `CPI_YOY`
  (consumer-price inflation, **% vs the same month a year earlier**, monthly, `PCPI_PC_CP_A_PT`)
  and `POLICY_RATE` (the monetary-policy rate, **% per annum**, monthly, `FPOLM_PA`). Both are
  **DBnomics-only**, so each resolves to a single-source monthly chain — distinct from the annual
  World Bank `CPI` (index level) and `INFLATION` (annual %). `POLICY_RATE` is an **honest proxy**
  for the announced State Bank of Vietnam refinancing rate: the result's `indicator_name` discloses
  this (`"Policy Rate (SBV refinancing-rate proxy, IMF IFS FPOLM_PA)"`) while the **canonical**
  code/name stay `policy_rate`/`Policy Rate` (stable identity). Monthly results also gain an
  additive, cadence-relative **`series_end_gap`** staleness warning in `IndicatorSeries.warnings`
  when the latest observation lags the series' own cadence by more than `max(2 × typical_gap, 210d)`
  — the 210-day floor sits above IMF/IFS's normal ~2–6-month publication lag, so healthy series
  never warn (values are kept, never dropped). All changes are additive. See
  [`docs/sources/macro-dbnomics.md`](docs/sources/macro-dbnomics.md),
  [`docs/tutorials/macro-and-fx.md`](docs/tutorials/macro-and-fx.md).
  ([#179](https://github.com/hungson175/vnfin/issues/179))
- **Delisted/suspended phantom-tail warning** (#176) — `vnfin.prices` `get_history(...)` now appends a
  soft `trailing_zero_volume_tail` warning to `PriceHistory.warnings` when a **D1** series ends in a run
  of **≥10** trailing *phantom* bars — each `volume == 0` and `open == high == low == close` (a flat
  carried-forward price) — the forward-fill some sources emit after a symbol is suspended/delisted
  instead of ending the series at the last real trading day. The warning names the run length,
  through-date, and last real-volume bar (`"none in window"` when the whole window is phantom); **bars
  are kept, not dropped** (v1 warns only). `LiquidityProfile` inherits the warning. Intraday is
  unaffected (zero-volume bars are normal off-hours). All changes are additive. See
  [`docs/architecture/failover-and-validation.md`](docs/architecture/failover-and-validation.md),
  [`docs/design/price-phantom-tail.md`](docs/design/price-phantom-tail.md).
  ([#176](https://github.com/hungson175/vnfin/issues/176))
- **Fund bond holdings + asset allocation** (#173) — `vnfin.funds` `holdings(product_id)` now merges
  per-security **equity** (`productTopHoldingList`) **and bond** (`productTopHoldingBondList`) rows into
  one `tuple[FundHolding]`, so a bond or balanced fund returns its real positions instead of a bare
  `EmptyData` (a category-wide blind spot: 22 BOND funds + at-par BALANCED funds). Each `FundHolding`
  gains two **appended, defaulted** (additive) fields: `instrument_type`
  (`"STOCK"`/`"BOND"`/`"UNLISTED_BOND"`/`"OTHER"` — an unknown-but-stringlike provider type maps to the
  honest `"OTHER"` tag, a malformed type fails closed) and `as_of_utc` (the row's `updateAt`, epoch-ms → UTC, or
  `None` — never fabricated). A new sibling accessor **`asset_allocation(product_id)` → `AssetAllocation`**
  (with `AssetClassWeight`) exposes the typed equity/bond/cash split (class codes `{STOCK, BOND, CASH}`,
  weights 0–100 not forced to sum to 100%, `as_of_utc` from `updateAt`). All changes are additive.
  See [`docs/sources/funds-fmarket.md`](docs/sources/funds-fmarket.md),
  [`docs/tutorials/funds-and-indices.md`](docs/tutorials/funds-and-indices.md).
  ([#173](https://github.com/hungson175/vnfin/issues/173))
- **`vnfin.exceptions.StaleData`** (#172) — a subclass of `EmptyData` raised when a source's history
  exists but ends before the requested window (a stale or closed feed). Backward compatible: existing
  `except EmptyData` / `except SourceError` handlers still catch it.
- **`vnfin.fundamentals.metrics(symbol, period="annual", *, is_bank=None, limit=8, ...)`** (#157) —
  a canonical-metrics layer: an additive, **offline** transform over the existing `get_financials`
  reports (no new source, no `ratios` fetch). It fetches income+balance+cashflow once each via the
  same VNDirect→CafeF failover, then maps the verified **VNDirect** provider codes to a fixed **v1
  catalog of 26 metrics** — 21 raw-mapped line items (corporate / bank / shared) + 5 derived ratios
  (`gross_margin`, `net_margin`, `liabilities_to_equity`, `cash_to_assets`,
  `operating_cash_flow_margin`) — returning one `MetricReport` per fiscal period (newest first).
  Every report carries ALL 26 metrics: applicability and gaps are expressed by
  `MetricValue.availability` (`available`/`missing`/`blocked`/`not_applicable`), never by omission, and
  every unavailable value carries a stable `reason`. Bank metrics map **only the #157-verified bank
  codes** (`net_interest_income`/`loans_to_customers`/`customer_deposits` + the shared metrics);
  unverified bank lines are deliberately not guessed. Provenance is **per statement**
  (`MetricReport.statement_sources`) — there is no single report `source` (income/balance/cashflow can
  resolve to different sources; CafeF does not serve cashflow → `not_served`); a statement that failed
  over to CafeF comes back `blocked` (`"metric map not available for source 'cafef'"`) since v1 maps
  only the VNDirect namespace. Derived ratios are computed in-library with denominator guards
  (zero/negative/non-finite → `missing`, never `inf`/`NaN`). Companion entry points:
  `explain_metric_coverage(...)` → `MetricCoverage` (the same fetch, **non-fatal**, per-fiscal-date
  diagnostics for a batch loop), and pure offline lookups `metric_catalog(applies_to=None)` →
  `tuple[MetricDefinition]` and `explain_metric(metric_id)` → `MetricDefinition`. **Provider-native
  valuation ratios (P/E, P/B, ROE/ROA/ROIC, EPS, book value, FCF) and extra bank lines are deferred to
  v2** — the layer never fetches the `ratios` statement (`ratio_status` is always `not_requested`) and
  these ids are absent from the v1 catalog. Result types `MetricReport` / `MetricValue` /
  `MetricDefinition` / `MetricCoverage` / `PeriodCoverage` / `MetricInput` / `StatementProvenance`
  (frozen dataclasses) and enums `MetricId` / `MetricKind` / `AppliesTo` / `MetricCategory` /
  `MetricAvailability` / `StatementCoverageStatus` are all importable from `vnfin.fundamentals`. All
  changes are additive. See [`docs/tutorials/fundamentals.md`](docs/tutorials/fundamentals.md),
  [`docs/api.md`](docs/api.md), [`docs/design/fundamentals-metrics.md`](docs/design/fundamentals-metrics.md).
  ([#157](https://github.com/hungson175/vnfin/issues/157))
- **`vnfin.fx.history(base="USD", quote="VND", start=None, end=None, *, frequency=ANNUAL)`** (#159) —
  historical FX time series, the first historical FX in `vnfin` (spot `get_rate`/`FXRate` is
  unchanged). v1 serves **annual USD/VND** from the no-key World Bank `PA.NUS.FCRF` series
  (`source="worldbank_fx"`), returning a typed `FXHistory` (of `FXPoint`, a `TimeSeriesResult` with
  `to_dataframe()`). Exact accessors `rate_on(date)` / `rate_for_year(year)` never fill or
  interpolate. Plus offline `vnfin.diagnostics.explain_fx_coverage(...)` (statuses `ok` /
  `coverage_gap` / `unsupported_pair` / `unsupported_frequency`). Monthly and non-USD cross-quotes
  are deferred to v2. See [`docs/tutorials/fx-history.md`](docs/tutorials/fx-history.md),
  [`docs/sources/fx-history-worldbank.md`](docs/sources/fx-history-worldbank.md),
  [`docs/design/fx-history.md`](docs/design/fx-history.md).
- **`vnfin.indices.index_history_stitched(symbol, start, end)`** (#147) — opt-in long-window index
  history stitched from per-calendar-year segments, each fetched via the failover chain (so a
  source's single OHLC-invariant day in one year is routed around by another clean source). Returns
  one `PriceHistory` with `source="stitched_index_history"` and per-segment provenance warnings;
  enforces points/RAW/symbol homogeneity and rejects conflicting seam dates. D1 only. The default
  strict `index_history` is unchanged.

### Changed
- **`funds.nav_history` no longer aborts the whole series on a single conflicting `navDate`** (#194) —
  a same-date NAV conflict (two DIFFERENT NAV values for one `navDate`) previously raised `InvalidData`
  and discarded the fund's ENTIRE NAV history over one bad date (~21/65 VN funds affected). It now
  mirrors the #186 VN-Index quarantine: the conflicting date is **dropped** entirely (never picked,
  never averaged), the rest of the series is served, and the drop is disclosed via the new never-silent
  **`quarantined_conflicting_navdates`** warning token (names the dropped dates). A *systematically*-
  conflicting feed still fails over — `InvalidData` is raised (naming the `N/considered` ratio) when the
  number of conflicting in-window dates exceeds `max(floor 3, 10% of distinct in-window dates)`, reusing
  #186's `_QUARANTINE_FRACTION`/`_QUARANTINE_ABS_FLOOR` unchanged but counting each conflicting **date**
  once (so a short fund with ≤3 conflicting dates always serves). Identical-value duplicate rows still
  dedupe with `deduped_duplicate_nav_rows` (conflict beats dedup on the same date); a window emptied by a
  sub-threshold quarantine still yields the existing `EmptyData`/`StaleData`. Behavior change only — the
  v0.2 public-API surface is unchanged (`NavHistory.warnings` was already defaulted).
  ([#194](https://github.com/hungson175/vnfin/issues/194))
- **VSDC no longer classifies net-vs-gross dividend ratios — conservative v1-surface shrink** (#163
  v1 de-scope) — a ratio line carrying a **tax/withholding signal** (thuế / TNCN / khấu trừ) is
  net-vs-gross ambiguous; rather than classify it (an open-ended, silent-wrong-prone problem that
  produced 7 distinct silent-wrong-ratio bugs over 6 rounds), `vnfin.corp_actions.dividends(...)` now
  WITHHOLDS the ratio (`ratio_pct=None`) and discloses it via the **new `vsdc_ratio_tax_deferred`**
  per-event token (distinct from `vsdc_parse_degraded`, which remains a parse fault). A ratio is
  served only from a fully tax-free line; clean lines are unaffected. Net-vs-gross classification is
  deferred to v2 behind a committed test corpus. ([#163](https://github.com/hungson175/vnfin/issues/163))

### Fixed
- **Index-constituents diagnostic no longer advises treating membership as point-in-time** (#175,
  Tier-3) — `vnfin.diagnostics.explain_index_constituents(...)` and the static
  `source_capabilities()` entry previously suggested *"treat membership as point-in-time"*, the exact
  misuse the live `current_snapshot_only` warning guards against (it injects survivorship/look-ahead
  bias into backtests) — the offline diagnostic contradicted the live result. Both now advise treating
  the basket as the **CURRENT** snapshot, **NOT** point-in-time, and flag the bias; a note records that
  point-in-time/historical membership is unavailable from this source. The do-not-expect-weights
  guidance and `single_source` status are unchanged; string-value-only fix, no surface change.
  ([#175](https://github.com/hungson175/vnfin/issues/175))
- **An `exchange=None` equity-universe merge no longer aborts when ONE board is down** (#189) —
  `vnfin.equities.universe()` iterates HOSE→HNX→UPCOM and merges them. Previously a single board's
  `_fetch_board` raising (`SourceUnavailable`/`EmptyData`/`InvalidData`) propagated and aborted the
  **whole** merge, so the caller got nothing even though the other two boards succeeded — the wrong
  failure mode for an all-boards listing. The merge now **skips-and-warns on a partial failure**: a
  down board is skipped with a never-silent `board_unavailable: {board} — fetch skipped ({ExcType}):
  {reason}` warning (added to the SKILL "Warning tokens" table) and the surviving boards still merge.
  A skipped board contributes **only** that token (its three always-present honest-gap tokens come
  from a *successful* fetch, so a skipped board emits none of them). On a **total** failure (all three
  boards down → no securities), the merge **re-raises the last `SourceError`** rather than returning a
  near-silent empty universe. A single-board call (`universe("HNX")`) is unchanged — it still raises
  on failure (the skip-and-warn is merge-only). **No public-API surface change** (warning strings are
  not public surface). ([#189](https://github.com/hungson175/vnfin/issues/189))
- **A real index trading day no longer vanishes to a midnight-open placeholder** (#187) — some
  index-D1 UDF feeds (e.g. `vps_index`) emit **two same-date D1 rows**: one at VN-local 00:00 (+07)
  and one at the real session time, **identical in high/low/close/volume** and differing **only in
  `open`** (the 00:00 row is a synthetic midnight placeholder whose `open` is the prior session's
  close). The shared UDF parse previously treated the pair as a #186 *conflict* and **poisoned the
  whole date (dropped BOTH rows)**, so a genuine trading day disappeared. It now detects this exact
  three-part signature — identical `(high, low, close, volume)`, differing `open`, and **exactly one**
  row at VN-local 00:00:00 (computed on the VN timezone, not naive UTC) — **keeps the non-midnight
  (real) row and drops the placeholder**. Because only `open` differs, the result is provably
  non-lossy, so this is a **recovery, not a quarantine**: the date is served, it is **not** charged to
  the failover threshold, and it is disclosed via a new, distinct, never-silent warning token
  **`recovered_midnight_open_placeholder`** (added to the SKILL "Warning tokens" table; the #180
  doc↔code lockstep guard now covers 34 tokens). A genuine conflict (any difference in high/low/close/
  volume), or an open-only diff where neither row is at VN-midnight, still poisons unchanged; equity /
  intraday (exact-timestamp keying) is unaffected. Order-independent (works whether the midnight or the
  real row arrives first). **No public-API surface change.**
  ([#187](https://github.com/hungson175/vnfin/issues/187))
- **Four caller-facing `result.warnings` strings are now namespaced tokens** (#180) — `NavHistory`,
  `FinancialReport` (VNDirect + CafeF), and stitched-index results were appending free-form **prose**
  warnings (`"deduped N duplicate navDate row(s)…"`, `"skipped N row(s) with mismatched
  reportType/modelType"`, `"skipped N period row(s)"`, `"segment <year>: <source> …"`) that callers
  could not match on a stable prefix and that were **absent from the SKILL "Warning tokens" table**.
  Each now carries a mechanical, fact-first token prefix consistent with the rest of the contract:
  **`deduped_duplicate_nav_rows`**, **`skipped_mismatched_report_rows`**, **`skipped_period_rows`**,
  and **`stitched_segment`** (the per-segment provenance line — the year moved into the tail so the
  prefix is stable). The complete caller-facing warning set is now documented in the SKILL table and
  pinned by a **bidirectional doc↔code lockstep guard** (`tests/test_docs_contract.py`): every emitted
  token must be documented *and* every documented token must still be emitted as a literal, so neither
  lane can silently rot. **No public-API surface change** (the API snapshot is unchanged) — only the
  `warnings` string content; a caller that matched the old prose substring must switch to the token
  prefix. ([#180](https://github.com/hungson175/vnfin/issues/180))
- **One bad upstream bar no longer blocks an entire price/index window** (#186) — the shared UDF parse
  (`UDFSource._build_bars`, behind both `prices.history` and `index_history`) used to `raise InvalidData`
  on the **first** per-bar data-quality failure, aborting the whole response. Because the same bad day
  (e.g. an OHLC-invariant-violating 2018-08-22, or a conflicting same-date 2020-12-25) exists in *every*
  source, one bad bar anywhere in a 10-year window failed the whole failover chain → `AllSourcesFailed`,
  making a 10y/Max VN-Index chart unrenderable. The parse now **quarantines** the offending bar instead:
  isolated per-row value-quality failures (OHLC-invariant violation, non-positive/non-finite price,
  negative/fractional volume, unparseable scalar) are **dropped from the series — never served** — and
  the rest of the window is returned. **Conflicting / duplicate keys drop the whole key**: a *conflicting*
  same-date index bar removes that entire date (both bars — we cannot tell which is right; an *identical*
  same-date duplicate still dedupes keep-first as before, #162), and any duplicate exact timestamp
  (equity / intraday) drops that timestamp. **Never silent:** the result carries a new
  `quarantined_invalid_bars` warning naming the dropped dates + reasons (surfaced on both equity and index
  results). **A systematically-broken source still fails over — judged over the requested window:** when
  the in-range quality failures exceed `max(_QUARANTINE_ABS_FLOOR=3, _QUARANTINE_FRACTION=0.10 ×
  considered)` over the in-range, timestamp-parseable rows (each calendar date counted once), the parse
  raises `InvalidData` → the next source is tried (all-bad → `AllSourcesFailed`). Bad rows *outside* the
  requested `[start, end]` (provider padding), rows with an unparseable timestamp, and identical same-date
  duplicates collapsed by the #162 dedupe are excluded from that verdict, so a provider's out-of-window
  junk — or merely sending each date twice — can't spuriously fail an otherwise-clean window. **Structural/shape faults
  still hard-raise** (misaligned/missing arrays, malformed envelope/status). Behavior change: a *lone*
  bad row now yields `EmptyData` (still a `SourceError` → failover) rather than `InvalidData`. No
  public-API surface change (the warning is just a string). See
  [`docs/architecture/failover-and-validation.md`](docs/architecture/failover-and-validation.md) →
  "Source-side bad-bar quarantine". ([#186](https://github.com/hungson175/vnfin/issues/186))
- **Contradictory index/price routing loop for recognised-but-unservable indices** (#174) —
  `index_history()` / `index_history_stitched()` rejected a recognised index whose value history is
  not served (the 10 HOSE **sector** indices `VNCOND…VNUTI`, plus `VN100`/`VNMID`/`VNSML`/`VNDIAMOND`/
  `VNFINLEAD`/`VNFINSELECT`/`VNXALL`/`VNXALLSHARE` and the `HNXUPCOMINDEX` provider alias) with
  *"not a known market index; use vnfin.prices.history() for stocks"* — but the price path correctly
  rejects the same symbol as an index and points back to `index_history()`, bouncing the caller
  between the two namespaces forever (a sector-allocation dashboard dead-ended). The index path now
  branches on `is_known_index()`: a recognised index returns a **terminal** diagnostic naming it as a
  recognised market index with unsupported value history (never *"use prices.history()"*), while a
  genuinely unknown / equity symbol keeps the correct route-to-prices guidance. Error-text/diagnostic
  change only — no public-API, value-behavior, or registry-set change; serving sector-index *history*
  remains a separate tracked enhancement. ([#174](https://github.com/hungson175/vnfin/issues/174))
- **Financial ratios completely unavailable** (#157) — `get_financials(sym, "ratios", ...)` (P/E, P/B,
  ROE, ROA, ROS, EPS, BV, per-share) raised `AllSourcesFailed` for **every** symbol because of two
  independent defects, now both fixed: (1) the failover **unit-homogeneity guard is now
  statement-type-aware** — ratios are dimensionless/non-monetary, so a `ratios` report legitimately
  carries `currency=None` and is no longer rejected as a `VND` mismatch (the VND homogeneity check is
  unchanged for the monetary income/balance/cashflow statements, and a `ratios` report arriving WITH a
  monetary currency is still rejected); (2) the **CafeF ratios parser now tolerates a present-null /
  absent `ReportType`** (the real CafeF ratios shape), which previously raised `InvalidData`
  ("expected a string, got NoneType") — `ReportType` is a non-identity descriptive field for
  cadence-agnostic ratios, so a null/absent value is tolerated while a present non-null malformed value
  still fails closed. Ratios remain `Period.UNKNOWN` (the provider's `reportDate`, which may be a TTM
  snapshot, is surfaced faithfully and never relabeled as a fiscal-year annual figure). Internal-only;
  no public-API change. ([#157](https://github.com/hungson175/vnfin/issues/157))
- **Fund unlisted-bond holdings** (#173 residual) — `vnfin.funds` `holdings(product_id)` no longer
  hard-fails (`InvalidData`) the ~8 real Fmarket unlisted-bond funds (e.g. ASBF id 51, VFF id 21,
  DCBF id 27) whose rows carry `type="UNLISTED_BOND"` and/or a **descriptive** `stockCode` (e.g.
  `'Trái phiếu chưa niêm yết'`). `FundHolding.instrument_type` now also reports `"UNLISTED_BOND"` and
  `"OTHER"` (a present-but-unknown stringlike provider `type` → `"OTHER"` instead of fail-closed; a
  present-malformed `type` still fails closed). `stock_code` validation is now relaxed for
  bond/unlisted-bond/other rows (required present + non-empty, stored verbatim) while equities stay
  strict (`[A-Z][A-Z0-9]*`). Additive — existing listed-bond/equity behavior is unchanged.
  ([#173](https://github.com/hungson175/vnfin/issues/173))
- **Fmarket NAV-history staleness** — `vnfin.funds` `nav_history(...)` no longer returns a silent
  `EmptyData` (indistinguishable from "no data") when the provider's history is stale. When the
  newest `navDate` is strictly before the requested window start, it now raises the new `StaleData`
  (an `EmptyData` subclass) naming the gap (`"... ends at <latest>, before requested <start>..<end>"`).
  Genuinely-empty and pre-inception / sparse-window cases stay plain `EmptyData`. A live probe
  confirmed Fmarket's history feed is systemically stale while `list_funds` shows current NAVs.
  ([#172](https://github.com/hungson175/vnfin/issues/172))
- **Crypto long-window partial coverage** — `vnfin.crypto` daily history no longer silently accepts a
  primary-source result that does not span the requested bounded window. The failover client now
  validates requested-window coverage: a source that fully covers (`first_bar.date <= start` and
  `last_bar.date >= end`) wins; a partial primary is not accepted as a clean success so backups get a
  chance; if no source fully covers, the **best-available** series (max in-window overlap, then source
  order) is returned with an explicit `partial_coverage: requested <start>..<end>, returned
  <first>..<last>` warning instead of a misleading full-success. Unbounded requests are unchanged.
  ([#169](https://github.com/hungson175/vnfin/issues/169))
- **Price/index namespace type confusion** — the price and index namespaces now **fail loud** on the
  wrong asset type instead of silently returning wrong-typed data.
  `vnfin.prices.history()` (and `vnfin.liquidity` by inheritance) reject a **market-index** symbol
  (`VNINDEX`, `VN30`, sector indices, …) with `InvalidData` before any network call; equities/unknown
  tickers are unaffected. `vnfin.indices.index_history()` / `index_history_stitched()` accept **only**
  recognised value-history indices and reject a **stock** symbol (e.g. `FPT`) with `InvalidData`.
  ([#168](https://github.com/hungson175/vnfin/issues/168))
- **Index daily duplicate-date handling** — a D1 **index** source result now exposes exactly one
  public bar per calendar date: an *identical* same-date OHLCV duplicate is deduped deterministically
  (keep-first) with a ``deduped_duplicate_daily_index_bars`` warning, while a *conflicting* same-date
  bar raises ``InvalidData`` inside the source path so the failover client records the attempt and
  tries the next source (never a silent conflicting-row selection). Equity behavior is unchanged
  (any duplicate timestamp still raises, #66). ([#162](https://github.com/hungson175/vnfin/issues/162))
- **Fmarket NAV duplicate-date handling** — ``nav_history`` now dedupes a duplicate ``navDate``
  whose NAV is identical (keeping one point and adding a ``deduped ... duplicate navDate`` warning)
  and raises ``InvalidData`` only when a duplicate date carries a *conflicting* NAV. Previously any
  duplicate date raised. ([#158](https://github.com/hungson175/vnfin/issues/158))
- **VNDirect statement row type guard** — the VNDirect statement parser now rejects a non-object
  row with ``InvalidData`` (``statement row is not an object``) before dereferencing it, mirroring
  the ratios path, instead of leaking a raw ``AttributeError``.
  ([#141](https://github.com/hungson175/vnfin/issues/141))
- **WorldBank duplicate observation-date guard** — ``WorldBankMacroSource`` now rejects a
  duplicate observation date within one response (``InvalidData``) instead of silently keeping
  both ambiguous observations. ([#66](https://github.com/hungson175/vnfin/issues/66))
- **VNDirect duplicate ratioCode guard** — the VNDirect ratios path now rejects a duplicate
  ``ratioCode`` within one ``reportDate`` (``InvalidData``) instead of silently keeping the first,
  matching how the statement path already rejects a duplicate ``itemCode``.
  ([#26](https://github.com/hungson175/vnfin/issues/26))
- **VNDirect all-skipped-rows response guard** — when a non-empty VNDirect statement response has
  *every* row skipped because its ``reportType``/``modelType`` contradicts the requested statement
  contract, ``VNDirectFundamentalSource`` now raises ``InvalidData`` (template/cadence mismatch)
  instead of returning an empty tuple that reads as clean no-data. A mix of valid + skipped rows
  still returns the valid reports with a skip warning. ([#44](https://github.com/hungson175/vnfin/issues/44))
- **WorldBank observation indicator.id guard** — ``WorldBankMacroSource`` now validates each
  observation's ``indicator.id`` (present ⇒ non-blank string equal, canonical-normalized, to the
  requested WDI code) before returning, matching the existing ``countryiso3code`` identity check.
  ([#21](https://github.com/hungson175/vnfin/issues/21))
- **UDF present blank/null symbol guard** — ``UDFSource.get_history`` now keys the response-symbol
  identity check on presence, not truthiness: a present blank/``null``/non-string ``symbol`` is
  rejected rather than treated as an absent field and stamped as the requested ticker (a truly
  missing key stays legacy-compatible). ([#21](https://github.com/hungson175/vnfin/issues/21))
- **Macro returned-indicator-identity guard** — the macro failover boundary now validates that a
  returned ``IndicatorSeries`` actually identifies the requested indicator. A source may declare
  its expected identity via ``indicator_identity(country_iso3, indicator) -> (code, name | None)``
  (built-in WB/IMF/DBnomics adapters declare their provider-specific codes); the returned
  ``indicator_code`` must equal it exactly and ``indicator_name`` must match when a name is
  declared. A source that does not declare an identity must return the canonical code+name, so an
  arbitrary wrong identity (e.g. ``indicator_code="WRONG_INDICATOR"``) from a custom source is
  rejected and the chain fails over. ([#78](https://github.com/hungson175/vnfin/issues/78))
- **GoldApi present-falsey updatedAt guard** — ``GoldApiSource`` now only falls back to a
  tz-aware "now" when ``updatedAt`` is truly absent/``null``. A present but falsey/non-string
  value (``False``/``0``/``""``/``[]``/``{}``) is corrupted freshness metadata and is rejected via
  the strict ISO-8601 check instead of being silently relabeled with the current time.
  ([#112](https://github.com/hungson175/vnfin/issues/112))
- **VNDirect all-mismatched-code response guard** — when *every* returned statement (or ratio)
  row carries a provider ``code`` that contradicts the requested symbol,
  ``VNDirectFundamentalSource`` now raises ``InvalidData`` (wrong-identity payload) instead of
  returning an empty tuple that reads as legitimate no-data.
  ([#21](https://github.com/hungson175/vnfin/issues/21))
- **Health raw-schema boolean guard** — ``vnfin._health.check_schema`` now rejects a JSON boolean
  for a numeric ``(int, float)`` schema path (``bool`` is an ``int`` subclass, so it previously
  passed). A boolean is accepted only when ``bool`` is explicitly in the declared types, so
  provider drift from ``26000.0`` to ``true`` is no longer marked schema-ok.
  ([#87](https://github.com/hungson175/vnfin/issues/87))
- **Vietcombank duplicate currency-code guard** — ``VietcombankFXSource.get_rates`` now raises
  ``InvalidData`` on a duplicate canonical ``CurrencyCode`` within one feed (e.g. two ``USD`` rows
  with conflicting rates) instead of returning ambiguous duplicate ``FXRate`` rows.
  ([#28](https://github.com/hungson175/vnfin/issues/28))
- **DBnomics period/duplicate parser hardening** — ``DBnomicsSource`` now requires each
  ``period_start_day`` to be a canonical ``YYYY-MM-DD`` *string* (no ``str()``/``strip()``
  coercion): compact (``20240101``), ISO week-date (``2024-W01-1``), whitespace-padded,
  non-zero-padded, and non-string period keys raise ``InvalidData``. It also rejects a duplicate
  canonical ``period_start_day`` within one response instead of returning ambiguous duplicate
  observation keys. ([#104](https://github.com/hungson175/vnfin/issues/104),
  [#66](https://github.com/hungson175/vnfin/issues/66))
- **Fmarket & GoldApi returned-identity guards** — provider responses are now checked against the
  requested identity before their data is trusted: ``FmarketFundSource.nav_history`` rejects a NAV
  row whose present ``productId`` is not the requested fund id (non-bool int equal to the request);
  ``FmarketFundSource.holdings`` rejects a detail document whose present ``id`` is not the requested
  fund id (and requires a present ``code`` to be a non-empty canonical string); and
  ``GoldApiSource`` rejects a payload whose present ``symbol`` does not match the requested
  commodity (case-insensitive) and always returns the validated requested symbol as the product
  rather than the trusted payload value. ([#21](https://github.com/hungson175/vnfin/issues/21))
- **CurrencyApi document-date identity guard** — ``CurrencyApiGoldSource._doc_date`` now only
  falls back to the requested loop date when the provider ``date`` is truly absent/``null``. A
  *present* but malformed value — a falsey non-string (``False``/``0``/``[]``/``{}``) or a
  blank/non-canonical string — is corrupted provider identity and raises ``InvalidData`` instead
  of being silently relabeled with the requested date.
  ([#35](https://github.com/hungson175/vnfin/issues/35))
- **OpenER fractional timestamp guard** — ``OpenErApiFXSource`` no longer truncates a fractional
  ``time_last_update_unix`` (e.g. ``1700000000.9``) via ``int()`` into a falsely-precise
  ``as_of_utc``. Only an integer or an integral, finite float is used as the provider timestamp;
  a fractional or non-finite value is treated like missing/malformed freshness metadata and falls
  back to a timezone-aware "now". ([#106](https://github.com/hungson175/vnfin/issues/106))
- **Fmarket envelope status/code integer guard** — the Fmarket application-envelope check no
  longer accepts a fractional or boolean ``status``/``code``: ``int(200.9)`` previously truncated
  to ``200`` and passed the 2xx gate, and a ``bool`` would coerce. A non-integral float, a
  non-finite float, or a ``bool`` is now rejected as a malformed envelope (``InvalidData``);
  integers, integral floats, and digit strings remain valid.
  ([#41](https://github.com/hungson175/vnfin/issues/41))
- **Macro unit-metadata relabel guard** — the macro failover result guard now rejects a present
  ``unit`` or ``value_unit`` that is not a string. Previously a falsey non-string (``[]``, ``{}``,
  ``0``, ``False``) was coerced to ``""`` by the placeholder handling and silently relabeled to
  the canonical unit instead of failing over; an empty *string* remains a legitimate placeholder.
  ([#135](https://github.com/hungson175/vnfin/issues/135))
- **Macro descriptive-metadata guard** — the macro failover result guard now requires
  ``indicator_code`` and ``indicator_name`` to be non-empty **strings** (a truthy non-string such
  as ``123`` previously passed the bare emptiness check and was accepted) and ``country_name``,
  when present, to be a string. These feed ``IndicatorSeries`` and ``to_dataframe().attrs`` as
  audit labels, so a malformed value is rejected as a failover attempt instead of surfacing as a
  clean result. ([#134](https://github.com/hungson175/vnfin/issues/134))
- **Price security-metadata guard** — the price failover result guard now rejects a returned
  ``PriceHistory`` whose ``exchange`` or ``provider_symbol`` is present but not a non-empty
  canonical string (containers, booleans, numbers, blank, or whitespace-padded values are
  rejected; ``None`` is allowed). ([#133](https://github.com/hungson175/vnfin/issues/133))
- **Macro frequency metadata guard** — the macro failover result guard now requires
  ``IndicatorSeries.frequency`` to be a :class:`~vnfin.macro.Frequency` enum (a plain string,
  bool, int, container, or ``None`` is rejected) and the point dates to be consistent with it
  (annual → Jan 1; quarterly → Jan/Apr/Jul/Oct day 1; monthly → day 1; daily → unconstrained).
  ([#132](https://github.com/hungson175/vnfin/issues/132))
- **Macro projection metadata guard** — the macro failover result guard now requires
  ``IndicatorSeries.projection_from_year`` to be ``None`` or a real non-bool integer year that
  falls within the returned series span (``first_year <= year <= last_year``); booleans,
  non-integers, and impossible out-of-span years are rejected.
  ([#131](https://github.com/hungson175/vnfin/issues/131))
- **Crypto quote-metadata consistency guard** — the crypto failover result guard now rejects a
  result whose returned quote metadata is malformed or internally contradictory: in a USD chain
  ``quote_asset`` must be a recognized USD-equivalent quote (and a non-empty canonical string),
  ``price_unit`` must equal ``"{quote_asset} per {base_asset}"``, ``volume_unit`` must equal the
  base asset, and ``provider_symbol`` (when present) must be a non-empty canonical string. A
  plausible-but-contradictory series (``currency="USD"`` with ``quote_asset="BTC"``, or
  ``price_unit="BTC per BTC"``) is rejected so it cannot block a healthy backup.
  ([#69](https://github.com/hungson175/vnfin/issues/69))
- **Fundamental report metadata guard** — the fundamentals failover result guard now validates
  returned ``FinancialReport`` metadata regardless of caller AUTO: ``is_bank`` must be a real
  ``bool`` (a truthy string like ``"False"`` is rejected), ``model_type`` must be ``None`` or one
  of the canonical VNDirect template ids (``1``/``2``/``3`` corporate, ``101``/``102``/``103``
  bank — booleans, floats, strings, containers, and arbitrary ints such as ``-1``/``0``/``4``/
  ``999`` are rejected), and ``provider_symbol``, when present, must be a non-empty string. A
  malformed report is
  rejected and the chain fails over instead of returning plausible statements with broken
  classification metadata. ([#130](https://github.com/hungson175/vnfin/issues/130))
- **Failover warnings metadata guard** — the price, crypto, gold, macro, and fundamentals
  failover result guards now reject a malformed ``warnings`` field: it must be a ``tuple`` whose
  members are all strings (the public ``tuple[str, ...]`` contract). A ``None`` (which previously
  crashed finalization via ``tuple(hist.warnings)``), a list, a bare string, or a tuple with a
  non-string member is rejected as a failover attempt. For fundamentals the check is per
  ``FinancialReport``. ([#128](https://github.com/hungson175/vnfin/issues/128))
- **Failover fetched_at_utc freshness guard** — the price, crypto, gold, macro, and fundamentals
  failover result guards now reject a present-but-malformed ``fetched_at_utc``: a value must be a
  timezone-aware ``datetime`` at UTC offset (naive datetimes, non-UTC datetimes, strings, and
  other types are rejected). ``None`` remains allowed (the field is optional). For fundamentals
  the check is applied per ``FinancialReport``. This matches the FX ``as_of_utc`` boundary so a
  corrupt source can no longer block a healthy backup with untrustworthy freshness metadata.
  ([#127](https://github.com/hungson175/vnfin/issues/127))
- **Fundamental fiscal_date type guard** — the fundamentals failover result guard now rejects a
  ``FinancialReport`` whose ``fiscal_date`` is not a plain ``datetime.date`` (``datetime`` — aware
  or naive — as well as ``str`` / ``None`` / ``int`` / ``list`` are rejected). The check runs
  before the zero-line and identity checks so a malformed date is the canonical rejection reason
  and the chain fails over instead of accepting a misdated report.
  ([#129](https://github.com/hungson175/vnfin/issues/129))
- **Failover inner row/item type guard** — the price, crypto, gold, macro, and fundamentals
  failover result guards now validate each inner row/item object before dereferencing it: bars
  must be the domain bar type (``PriceBar`` / ``CryptoBar`` / ``GoldBar``), macro points must be
  a ``(date, value)`` 2-tuple/list (a mapping is rejected, never unpacked), and fundamentals line
  items must be ``LineItem``. A malformed inner object (dict, ``None``, scalar, wrong-shape pair)
  is now a recorded rejected source attempt and the chain fails over, instead of leaking a raw
  ``AttributeError`` / ``ValueError``. ([#125](https://github.com/hungson175/vnfin/issues/125))
- **Failover provenance guard** — every domain failover client (price, crypto, gold, macro,
  fundamentals, FX) now verifies that an accepted result's stamped ``source`` matches the source
  that actually produced it. A result whose provenance does not match (e.g. a primary returning
  a result labelled with another provider's name) is recorded as a rejected source attempt and
  the chain fails over — the provenance is never silently relabelled — so audit logs, backtests,
  and reconciliation can trust ``result.source`` / ``report.source``. Implemented as an optional
  engine-level ``provenance_of`` guard with a result-source extractor that also handles composite
  results (the fundamentals report tuple). ([#126](https://github.com/hungson175/vnfin/issues/126))
- **Failover bar time-key type guard** — the price, crypto, and gold failover result guards now
  validate each bar's time key before the ascending-order compare and window/coverage logic.
  ``PriceBar.time`` and ``CryptoBar.time`` must be timezone-aware ``datetime`` values (naive
  datetimes and non-datetime keys are rejected); ``GoldBar.date`` must be a plain ``datetime.date``
  (``datetime`` keys are rejected since they subclass ``date``). A malformed key is recorded as a
  rejected source attempt instead of leaking a raw ``TypeError``/``AttributeError``.
  ([#124](https://github.com/hungson175/vnfin/issues/124))
- **Macro point-key type guard** — the macro failover result guard now rejects an
  ``IndicatorSeries`` whose ``points`` keys are not plain ``datetime.date`` values. ``datetime``
  keys (which subclass ``date`` but carry intraday/timezone meaning), as well as ``str`` /
  ``int`` / ``None`` keys, are rejected before the ascending-order comparison so a malformed key
  is a recorded rejected attempt instead of a leaked ``TypeError``.
  ([#123](https://github.com/hungson175/vnfin/issues/123))
- **Failover malformed result-container guard** — the price, crypto, gold, and macro failover
  result guards now type-check the returned container (``PriceHistory`` / ``CryptoHistory`` /
  ``GoldHistory`` / ``IndicatorSeries``) before reading ``.bars`` / ``.points``. A source
  returning a malformed non-typed result (e.g. a plain ``dict`` or ``None``) is now recorded as
  a rejected source attempt — and the chain fails over to the next source or raises a clean
  ``AllSourcesFailed`` — instead of leaking a raw ``AttributeError`` to the caller.
  ([#125](https://github.com/hungson175/vnfin/issues/125))
- **Fundamental failover line-item guard** — the fundamentals failover result guard now
  validates returned ``LineItem`` fields before accepting a source result: ``item_code`` must
  be a non-empty string, ``name`` must be a string (empty allowed), ``value`` must be a finite
  non-bool number, and duplicate ``item_code`` values in one report are rejected. A custom or
  future source returning ``NaN``/``Infinity``/bool/str values, blank/non-string codes, or
  duplicate-conflicting codes is now rejected and the backup attempted instead.
  ([#122](https://github.com/hungson175/vnfin/issues/122))
- **Provider timestamp coercion** — shared ``parse_provider_int()`` rejects JSON booleans
  before epoch timestamp conversion in UDF, Binance, and Coinbase paths; OpenER bool
  timestamps fall back to now instead of epoch. ([#106](https://github.com/hungson175/vnfin/issues/106))
- **World Bank metadata containers** — reject present non-object ``indicator`` and
  ``country`` observation containers, not just malformed ``value`` fields. ([#101](https://github.com/hungson175/vnfin/issues/101))
- **CafeF fiscal/display metadata** — reject non-string line-item ``Name`` values and
  boolean ``Year``/``Quater`` before integer coercion instead of leaking
  ``AttributeError`` or year-1 reports. ([#94](https://github.com/hungson175/vnfin/issues/94))
- **FX failover rate guard** — reject infinite and boolean main rates in the
  request-aware result guard, matching direct source validation. ([#88](https://github.com/hungson175/vnfin/issues/88))
- **Index member metadata** — reject present non-string ``exchange``, company name,
  and ``isin`` fields instead of silently erasing malformed provider metadata.
  ([#100](https://github.com/hungson175/vnfin/issues/100))
- **BTMC product/karat metadata** — validate ``@n_<row>`` and ``@k_<row>`` types
  before normalization so malformed rows raise ``InvalidData`` instead of leaking
  raw ``TypeError`` or typed non-string ``GoldQuote.karat``. ([#98](https://github.com/hungson175/vnfin/issues/98))
- **Gold failover coverage thresholds** — reject boolean and non-numeric
  ``min_coverage`` / ``warn_coverage`` values so ``False`` cannot silently disable
  the sparse-history guard. ([#96](https://github.com/hungson175/vnfin/issues/96))
- **World Bank descriptive metadata** — reject present non-string
  ``indicator.value``, ``country.value``, and ``unit`` fields instead of letting
  malformed provider metadata enter typed ``IndicatorSeries``. ([#101](https://github.com/hungson175/vnfin/issues/101))
- **FRED units metadata** — reject present non-string top-level ``units`` values instead
  of silently stamping an empty unit label. ([#102](https://github.com/hungson175/vnfin/issues/102))
- **FX failover UTC strictness** — `FailoverFXClient` now rejects timezone-aware `as_of_utc`
  timestamps that are not exactly UTC (e.g. `+07:00`), not only naive datetimes.
- **Macro failover result validation** — `MacroClient` now rejects a returned series whose
  `indicator_code`/`indicator_name` match a different canonical indicator, points that are
  not strictly ascending by date, or non-finite (NaN/inf) point values.
- **Index constituents data envelope** — validate ``data`` is a list before treating
  falsy containers as empty membership; malformed SUCCESS payloads raise
  ``InvalidData`` instead of ``EmptyData``. ([#103](https://github.com/hungson175/vnfin/issues/103))
- **Macro response containment** — FRED and World Bank adapters drop observations
  outside the requested date/year window and raise ``EmptyData`` when no in-window
  points remain. ([#105](https://github.com/hungson175/vnfin/issues/105))
- **DBnomics period/frequency validation** — reject `period_start_day` values that contradict
  the declared observation frequency (annual must be Jan 1; monthly must be month-start).
  ([#104](https://github.com/hungson175/vnfin/issues/104))
- **VN trading calendar** — add missing 2025-05-02 and 2026-08-31 official market closures so
  `expected_latest_trading_day()` no longer treats National Day / Labor Day bridge sessions as
  trading days. ([#92](https://github.com/hungson175/vnfin/issues/92))
- **Health STATUS.md renderer** — escape pipe and newline characters in every Markdown table cell
  so provider/exception text cannot inject forged health rows. ([#89](https://github.com/hungson175/vnfin/issues/89))
- **Secret redaction (`client_secret`)** — classify OAuth-style `client_secret` / `X-Client-Secret`
  names as sensitive for redaction and deterministic cache-key hashing; wrapped transport errors no
  longer leak plaintext credentials. ([#38](https://github.com/hungson175/vnfin/issues/38))
- **Fmarket nested `data` validation** — `list_funds()` and `holdings()` raise `InvalidData` when
  the success envelope carries a non-object `data` payload instead of leaking `AttributeError`.
  ([#91](https://github.com/hungson175/vnfin/issues/91))
- **Provider numeric coercion** — shared `parse_provider_float()` rejects JSON booleans before
  coercion across price, crypto, fund, fundamental, and FX parsers so `true` cannot become
  plausible financial values. ([#87](https://github.com/hungson175/vnfin/issues/87))
- **OpenER USD self-rate anchor** — reject USD-base payloads whose `rates["USD"]` drifts from 1
  before deriving cross-rates, preventing silently wrong USD/VND values. ([#93](https://github.com/hungson175/vnfin/issues/93))
- **FailoverCryptoClient iterator sources** — materialize `sources` before unit-guard and engine
  wiring so generator/iterator chains keep the primary source. ([#95](https://github.com/hungson175/vnfin/issues/95))
- **Fmarket metadata typing** — `list_funds()` and `holdings()` reject non-string fund name,
  manager, asset-type, and industry fields instead of stringifying malformed provider values.
  ([#97](https://github.com/hungson175/vnfin/issues/97), [#99](https://github.com/hungson175/vnfin/issues/99))
- **Fmarket holdings aggregate weight** — reject top-holdings baskets whose weights sum above
  100%. ([#90](https://github.com/hungson175/vnfin/issues/90))
- **Price/crypto failover date window** — reject non-empty histories with no bars inside the
  requested `[start, end]` range so out-of-window results fail over instead of succeeding.
  ([#84](https://github.com/hungson175/vnfin/issues/84))
- **CafeF fundamentals (`Quater=5`)** — annual reports whose older rows carry CafeF's
  `ReportType=NAM` marker `Quater=5` no longer abort the entire response: an annual report's
  fiscal date is the year-end regardless of the `Quater` marker, and a single period-marker
  anomaly is skipped (surfaced via a `warnings` note) rather than failing the whole request.
  Line-item validation stays strict (malformed data still raises). ([#1](https://github.com/hungson175/vnfin/issues/1))
- **Health harness label honesty** — `run_probe` now reports the *actual* serving `source` from
  the typed result, and each default probe targets its **primary single source** directly, so a
  `prices` probe can no longer report `ssi` healthy when a backup actually served the bar.
  ([#1](https://github.com/hungson175/vnfin/issues/1))
- **CafeF unit/scale (`thousand-VND`)** — CafeF reports statement money in **thousand-VND** but it
  was labeled raw VND, so the failover unit-homogeneity guard accepted VNDirect (raw VND) and CafeF
  (thousand-VND) with matching labels but a 1000× scale mismatch. The CafeF adapter now multiplies
  monetary statement lines by **1000** to emit raw VND (ratios unscaled), matching the VNDirect
  primary. Verified via cross-source magnitude. ([#3](https://github.com/hungson175/vnfin/issues/3))
- **CafeF ratios — quarterly EndDate anchor** — `CafeFFundamentalSource.get_financials(...,
  StatementType.RATIOS, Period.QUARTER)` previously sent a quarterly `EndDate` like `"2-2026"`, which
  CafeF's ratio endpoint rejects (`Time sai dinh dang`). The adapter now always sends a plain year
  anchor for ratios (the typed contract treats ratios as period-agnostic `Period.UNKNOWN`).
  ([#4](https://github.com/hungson175/vnfin/issues/4))
- **Fundamental ratio unit labels** — EPS and BV are per-share monetary values, not dimensionless
  ratios. CafeF reports them in **thousand-VND per share**; they were previously emitted with
  `LineItem.value_unit == "ratio"`. The CafeF adapter now scales EPS/BV by **1000** and labels them
  `"vnd_per_share"`, while dimensionless metrics (PE, ROE, ROA, ROS, DAR, GOS) remain `"ratio"`.
  ([#5](https://github.com/hungson175/vnfin/issues/5))
- **Macro level-indicator positivity guard** — canonical level indicators (`GDP`, `CPI`) now reject
  non-positive values as provider drift / parse errors. Percent/rate indicators (`GDP_GROWTH`,
  `INFLATION`, `UNEMPLOYMENT`) continue to allow negative values. Guard applies to World Bank,
  DBnomics, and IMF DataMapper sources. ([#16](https://github.com/hungson175/vnfin/issues/16))
- **VN gold selector validation** — `BTMCGoldSource.get_quote()` and `PNJGoldSource.get_quote()` now
  reject empty, whitespace-only, or non-string product selectors with `VnfinError` before scanning
  the feed, instead of silently returning the first product or leaking `AttributeError`.
  ([#17](https://github.com/hungson175/vnfin/issues/17))
- **Fundamentals string-input parity** — `vnfin.fundamentals.client().get_financials()` and
  `vnfin.fundamentals.source().get_financials()` now accept string `statement` and `period` values
  (e.g. `"income"`, `"annual"`) just like the top-level `get_financials()` convenience function,
  and raise `VnfinError` for unknown strings instead of leaking `AttributeError`/`KeyError`.
  Coercion helpers are shared across all entry points. ([#25](https://github.com/hungson175/vnfin/issues/25))
- **Currency-api gold history date identity** — `CurrencyApiGoldSource.get_history()` now validates
  the date-pinned document's own `date` field against the requested date. A mismatch raises
  `InvalidData` instead of silently stamping the requested date onto the wrong day's price. If the
  document omits `date`, the requested loop date is still used as a documented fallback.
  ([#35](https://github.com/hungson175/vnfin/issues/35))
- **UDF status strictness** — shared `UDFSource` now requires the inner UDF status field `s`
  to equal `"ok"` for success. `"no_data"` / `"error"` still raise `EmptyData`, but missing or
  unknown status values now raise `InvalidData` so a failover chain does not silently treat a
  drifting provider response as valid price data. ([#39](https://github.com/hungson175/vnfin/issues/39))
- **UDF envelope/array hardening** — `UDFSource` now validates that the extracted payload is a
  `dict` and that the OHLCV arrays are sequences before indexing/length checks. Malformed
  envelopes, missing `data` keys, and scalar/null arrays raise `InvalidData` instead of leaking
  raw `AttributeError`/`TypeError`/`KeyError`. ([#55](https://github.com/hungson175/vnfin/issues/55))
- **VNDirect ratio row shape safety** — ratio rows that are not JSON objects (list, `None`,
  string, number) now raise `InvalidData` instead of leaking raw `AttributeError`.
  ([#62](https://github.com/hungson175/vnfin/issues/62))
- **Crypto base-asset validation** — `BinanceCryptoSource` and `CoinbaseCryptoSource` now
  validate the base token before any network call, rejecting symbols with spaces, slashes, or
  other non-alphanumeric characters. ([#60](https://github.com/hungson175/vnfin/issues/60))
- **FRED BYOK key redaction** — provider error envelopes from FRED now redact the configured
  `api_key` from `error_message` before raising `InvalidData`, preventing the BYOK secret from
  leaking in exception text. ([#51](https://github.com/hungson175/vnfin/issues/51))
- **IMF input validation** — `IMFDataMapperSource` now validates `country_iso3` as a 3-letter
  alphabetic string and converts unsupported indicator values to `InvalidData` before any
  network call. ([#61](https://github.com/hungson175/vnfin/issues/61))
- **GoldAPI symbol whitelist** — `GoldApiSource` now restricts symbols to the supported world
  spot tickers `XAU` and `XAG`, rejecting unsupported or malformed symbols before the provider
  is contacted. ([#52](https://github.com/hungson175/vnfin/issues/52))
- **Fmarket filter hygiene** — `FmarketFundSource.list_funds()` treats whitespace-only
  `asset_type`/`search` as absent so the provider body never contains blank filters, and the
  invalid `product_id` tests now assert zero transport calls for every rejected value.
  ([#56](https://github.com/hungson175/vnfin/issues/56))
- **SSI envelope validation** — `SSIiBoardSource` now validates the outer response envelope
  (`code == "SUCCESS"` and `status == "ok"`) before unwrapping `data`. Provider-side failures
  raise `SourceUnavailable`; malformed or missing envelope fields raise `InvalidData`.
  ([#40](https://github.com/hungson175/vnfin/issues/40))
- **Fmarket envelope requirement** — `FmarketFundSource` now requires at least one of the
  application-level envelope fields `status` or `code` in every response. A response missing both
  raises `InvalidData`; non-2xx application statuses continue to raise `SourceUnavailable`.
  ([#41](https://github.com/hungson175/vnfin/issues/41))
- **CafeF statement period-tag honesty** — `CafeFFundamentalSource` now skips rows whose
  `ReportType` disagrees with the requested `Period` (e.g. annual-tagged rows in a quarterly pull),
  surfaced via a `warnings` note, instead of silently relabeling them. Ratios remain period-agnostic.
  ([#45](https://github.com/hungson175/vnfin/issues/45))
- **CafeF statement row ReportType vocabulary** — `CafeFFundamentalSource` now accepts the
  documented response row tags `HK` (annual) and `H` (quarterly) in addition to the request-side
  strings `NAM`/`QUY`, so real CafeF payloads are no longer rejected as `EmptyData`.
  ([#44](https://github.com/hungson175/vnfin/issues/44))
- **CafeF `is_bank` strict validation** — `CafeFFundamentalSource` now resolves `is_bank` through
  `resolve_is_bank()`, rejecting non-boolean values such as the string `"False"` with `VnfinError`
  instead of truthy-coercing them. ([#11](https://github.com/hungson175/vnfin/issues/11))
- **VNDirect statement contract strictness** — `VNDirectFundamentalSource` now skips rows whose
  `reportType` or `modelType` contradicts the request, and raises `InvalidData` on duplicate
  `itemCode` values within the same fiscal period. ([#44](https://github.com/hungson175/vnfin/issues/44),
  [#26](https://github.com/hungson175/vnfin/issues/26))
- **VNDirect ratio units** — EPS and BV are per-share monetary values; the VNDirect adapter now
  labels them `"vnd_per_share"` instead of `"ratio"`. ([#19](https://github.com/hungson175/vnfin/issues/19))
- **`is_bank` strict validation** — `resolve_is_bank()` now rejects non-boolean, non-`AUTO`
  values such as the string `"False"` with `VnfinError`, eliminating truthiness bugs.
  ([#11](https://github.com/hungson175/vnfin/issues/11))
- **Fundamental statement `Period.UNKNOWN` guard** — Both CafeF and VNDirect adapters reject
  `Period.UNKNOWN` for income/balance/cashflow statements (it is only meaningful for ratios).
  ([#10](https://github.com/hungson175/vnfin/issues/10))
- **FRED API-key hygiene** — `FREDMacroSource` now treats whitespace-only or non-string
  `api_key` values as missing, keeping the source cleanly skippable and preventing bytes or
  whitespace from being sent to the provider. ([#58](https://github.com/hungson175/vnfin/issues/58))
- **World Bank indicator-code validation** — `WorldBankMacroSource.get_indicator()` now rejects
  non-string `indicator_code` values (including `bytes`) with `InvalidData` before any URL is built.
  ([#57](https://github.com/hungson175/vnfin/issues/57))
- **Fmarket filter validation** — `FmarketFundSource.list_funds()` now rejects non-string
  `asset_type` and `search` filter values with `InvalidData` before building the provider request.
  ([#56](https://github.com/hungson175/vnfin/issues/56))
- **UDF empty-volume strictness** — `UDFSource` now treats a present-but-empty `v` array as a
  malformed response (`InvalidData`) while still allowing a missing `v` field to default to zero
  volume. ([#55](https://github.com/hungson175/vnfin/issues/55))
- **Index constituents envelope requirement** — `IndexConstituentsSource` now requires
  `code == "SUCCESS"`; missing, null, or non-success codes raise `InvalidData` instead of being
  parsed as a valid basket. ([#54](https://github.com/hungson175/vnfin/issues/54))
- **Stooq OHLC validation** — `StooqGoldSource` now validates the full OHLC row (numeric, positive,
  self-consistent high/low/open/close) and rejects malformed rows as `InvalidData`.
  ([#53](https://github.com/hungson175/vnfin/issues/53))
- **VNDirect ratio row strictness** — `VNDirectFundamentalSource._get_ratios()` now validates that
  `ratioCode` is a non-empty string and `itemName` is a string or `None`, raising `InvalidData` for
  malformed provider rows instead of leaking raw `TypeError`/`AttributeError`. ([#62](https://github.com/hungson175/vnfin/issues/62))
- **IMF year-range validation** — `IMFDataMapperSource` now rejects out-of-range numeric years with
  `InvalidData` instead of leaking raw `ValueError`. ([#61](https://github.com/hungson175/vnfin/issues/61))
- **Coinbase hyphenated quote validation** — `CoinbaseCryptoSource.parse_symbol()` now validates the
  quote leg of hyphenated products against the recognized quote-asset set; unknown quote legs raise
  `InvalidData` before any request. ([#60](https://github.com/hungson175/vnfin/issues/60))
- **Crypto zero-price rejection** — `BinanceCryptoSource` and `CoinbaseCryptoSource` now reject
  zero-price OHLC candles as `InvalidData`; volume may still be zero. ([#59](https://github.com/hungson175/vnfin/issues/59))
- **GoldApi symbol validation** — `GoldApiSource` now validates `symbol` as a non-empty string in the
  constructor, raising `VnfinError` for `None`, non-string, empty, or whitespace-only values.
  ([#52](https://github.com/hungson175/vnfin/issues/52))
- **FRED application-error envelope detection** — `FREDMacroSource` now detects FRED error envelopes
  (`error_code` / `error_message`) and raises `InvalidData` instead of parsing them as data or
  treating them as empty. ([#51](https://github.com/hungson175/vnfin/issues/51))
- **World Bank country validation** — `WorldBankMacroSource.get_indicator()` now validates
  `country_iso3` as a string before any string operation and requires a 3-letter alphabetic ISO3
  code, raising `InvalidData` before network for non-string/malformed values.
  ([#32](https://github.com/hungson175/vnfin/issues/32))
- **World Bank year-bound validation** — `WorldBankMacroSource` now rejects request years outside
  the `datetime.date` supported range `1..9999` with `InvalidData` before contacting the provider,
  complementing the existing out-of-range observation-year guard.
  ([#46](https://github.com/hungson175/vnfin/issues/46),
  [#63](https://github.com/hungson175/vnfin/issues/63))
- **Macro client country validation** — `MacroClient.get_indicator()` validates the country as a
  3-letter ISO3 code before building the failover engine. ([#32](https://github.com/hungson175/vnfin/issues/32))
- **Vietcombank self-rate skip** — `VietcombankFXSource` now skips the provider's VND/VND self-rate.
  ([#47](https://github.com/hungson175/vnfin/issues/47))
- **OpenER timestamp overflow guard** — `OpenErApiFXSource` now catches out-of-range
  `time_last_update_unix` timestamps and falls back to UTC now instead of leaking `OverflowError`.
  ([#43](https://github.com/hungson175/vnfin/issues/43))
- **World gold history date-bound validation** — `CurrencyApiGoldSource.get_history()` and
  `StooqGoldSource.get_history()` now reject non-date `start`/`end` bounds with `InvalidData`
  before any fetch. ([#42](https://github.com/hungson175/vnfin/issues/42))
- **Health macro probe failover path** — the default macro health probe now routes through
  `vnfin.macro.get_indicator()` so `MacroIndicator.CPI` maps to the correct provider series; the
  probe label is updated to `macro/canonical/VNM-CPI` to reflect that it exercises failover.
  ([#36](https://github.com/hungson175/vnfin/issues/36))
- **Index history canonical symbol** — `IndexClient` and index UDF sources now return the
  canonical symbol the caller requested (e.g. "UPCOM") while keeping the provider alias in
  `provider_symbol`. Previously the provider alias leaked into the public `symbol` field.
  ([#64](https://github.com/hungson175/vnfin/issues/64))
- **Index constituents validation** — `IndexConstituentsSource` now rejects empty/whitespace
  normalized member symbols and duplicate symbols as `InvalidData`.
  ([#30](https://github.com/hungson175/vnfin/issues/30))
- **Price interval validation** — `FailoverPriceClient.get_history()` validates that the
  `interval` argument is an `Interval` enum before the failover engine touches it, preventing
  a raw `AttributeError` from malformed caller input.
  ([#23](https://github.com/hungson175/vnfin/issues/23))
- **UDF response identity guard** — `UDFSource` now validates a provider-echoed `symbol` field
  in the response against the requested symbol/alias, raising `InvalidData` on mismatch before
  stamping identifiers onto the result. ([#21](https://github.com/hungson175/vnfin/issues/21))
- **Zero market-observation rejection** — `UDFSource` now rejects zero OHLC prices and
  `FmarketFundSource` rejects zero NAV values as `InvalidData`; volume may still be zero.
  ([#13](https://github.com/hungson175/vnfin/issues/13))
- **Price adjustment-policy guard** — `FailoverPriceClient` now rejects chains that mix declared
  adjustment policies (e.g. `PROVIDER_ADJUSTED` with `RAW`/`MIXED`) at construction time, mirroring
  the existing unit-homogeneity guard. ([#7](https://github.com/hungson175/vnfin/issues/7))

## [0.2.0] — 2026-06-18

> Version bumped and release-ready. **Tag/push/PyPI publish are pending maintainer approval**
> (not yet performed).

### Added
- **API stability gate** — `tests/test_public_api_surface.py` introspects the public surface
  (per-module `__all__`, factory/method signatures, frozen-dataclass fields, enum members/values,
  public-class constructors, and canonical unit/currency defaults) and diffs it against a committed
  per-release baseline snapshot (`tests/snapshots/public_api_v0_2_0.json`; v0.1.0 retained for
  audit) with a **compatibility-aware** comparator (`scripts/dump_api_surface.py`). Accidental
  breaking changes fail the suite; additive changes are reported. SemVer + deprecation policy
  documented in [`docs/stability.md`](docs/stability.md).
- **Upstream health monitoring** (opt-in, private `vnfin/_health.py` + `scripts/healthcheck.py`) —
  typed `SourceHealth` per probe (reachability, schema conformance, value sanity, latency),
  schema-drift detection via required-paths/types, a 5-domain critical probe set, and sanitised
  `STATUS.md`/JSON renderers. Live-only; never runs in CI; never auto-pushed.
- **FX domain** (`vnfin.fx`) — daily/current foreign-exchange reference rates vs VND, no-key
  failover **open.er-api → Vietcombank XML**, canonical unit *VND per 1 unit of base* (USD/VND,
  plus cross-rates EUR/CNY/JPY/…), typed `FXRate`, two-layer unit guard, optional `bid`/`ask`.
  At this release the FX domain shipped the spot/current quote only; historical USD/VND was added
  later via `vnfin.fx.history()` (#159, see Unreleased). Opt-in live USD/VND cross-source parity test;
  opt-in (rate-limit-aware) FX health probe. See [`docs/design/fx-sources.md`](docs/design/fx-sources.md),
  [`docs/sources/fx-open-er-api.md`](docs/sources/fx-open-er-api.md),
  [`docs/sources/fx-vietcombank.md`](docs/sources/fx-vietcombank.md).
- Explicit `__all__` for `vnfin.exceptions`; `vnfin.sources` now covered by the stability snapshot.

### Notes
- Corporate-actions/dividends are **designed only** ([`docs/design/corporate-actions.md`](docs/design/corporate-actions.md));
  implementation deferred to 0.3.1 after the security master.
- No public push / tag / PyPI publish performed — held for maintainer approval.

## [0.1.0] — 2026-06-18

### Added
- Initial clean-room release. No-key-first + optional BYOK across 7 domains: **prices** (daily
  OHLCV, VND), **fundamentals** (statements, VND), **funds** (NAV, VND/unit), **indices** (points),
  **gold** (VN VND/lượng + world USD/oz), **crypto** (USD), **macro** (no-key World Bank → IMF →
  DBnomics; FRED/BEA/BLS BYOK).
- Generic `FailoverClient` with a **unit-homogeneity guard**; typed frozen-dataclass results with
  explicit units/currency; VN trading-calendar staleness checks.
- 750+ offline tests (94% coverage, synthetic fixtures only) + opt-in live cross-source checks;
  CI coverage gate (≥85%). Apache-2.0.

[0.2.0]: https://github.com/hungson175/vnfin/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/hungson175/vnfin/releases/tag/v0.1.0
