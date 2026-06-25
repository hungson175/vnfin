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
6. **Resample (#183):** `prices.history` and `indices.index_history` take an optional `interval` —
   an `Interval` member OR a pandas alias string (`'D'/'W'/'M'/'Q'/'Y'`, case-insensitive). Default
   `D1` = daily (unchanged). Coarser periods (`W1/MN1/Q1/Y1`) are aggregated **client-side** from the
   fetched daily series: full OHLC per period, bar dated at the last actual trading day. **TRAP:
   `'M'` = MONTH (`Interval.MN1`), NOT minute — `Interval.M1` is 1 minute.** `D1` and intraday
   (`M1/M5/M15/M30/H1`) are **unchanged** — served natively by the sources that support them (#183 is
   purely additive; only `W1/MN1/Q1/Y1` are resampled). Resampled results always carry a
   `resampled_from_d1` warning, plus `resample_partial_period` when an edge period is incomplete (bars
   kept). Network still fetches full daily range — the win is fewer returned rows.
   (`index_history_stitched` stays D1-only.)

## Domain cheat-sheet

| Need | Call | Result · unit |
|------|------|---------------|
| Stock OHLCV | `vnfin.prices.history(sym, start=, end=)` | `PriceHistory` · VND |
| Financials | `vnfin.fundamentals.get_financials(sym, stmt, period)` | `tuple[FinancialReport]` · raw VND |
| Fund NAV/holdings | `vnfin.funds.source().nav_history(fund_id, ...)` · `.holdings(fund_id)` (stocks+bonds) · `.asset_allocation(fund_id)` | `NavHistory` · `tuple[FundHolding]` · `AssetAllocation` |
| Index value | `vnfin.indices.index_history(idx, start, end)` | `PriceHistory` · **points** (bar `volume` = constituent **shares**, directional proxy only — not exact for liquidity) |
| Index members | `vnfin.indices.index_constituents(idx)` | `IndexConstituents` (no weights) |
| World index (5 symbols) | `vnfin.indices.world("SPY", start=, end=)` — `SPY`,`QQQ`,`^N225`,`^SSEC`,`^STI` | `PriceHistory` · all **USD** (US ETFs); `^N225`/`^SSEC`/`^STI` are **USD ETF proxies** (`proxy_for` + `proxy_substitution`, embed FX, not faithful trackers); series are **price-return, not total-return**. **Needs `ALPHAVANTAGE_API_KEY` on servers** — no key + walled fallback → `MissingKey` (names the env var); keyless Stooq `^SPX` fallback is residential-only |
| VN gold spot | `vnfin.gold.vn("btmc").get_quotes()` | `GoldQuote` · VND/lượng |
| World gold | `vnfin.gold.world().get_history(start, end)` | `GoldHistory` · USD/oz |
| Silver / platinum (annual) | `vnfin.metals.history(metal, start, end)` — `metal` ∈ `"silver"`/`"XAG"`/`"platinum"`/`"XPT"`; `SUPPORTED_METALS == ("silver","platinum")` | `MetalHistory` of `MetalBar` · **USD/oz**, annual (Jan-1). World Bank CMO Pink Sheet. **`history("gold")`/`"XAU"` → `InvalidData` routing to `vnfin.gold`** (gold lives there, not here); any other metal (palladium/XPD/copper) → `InvalidData` naming it, **before network**. Never-silent typed `frequency="annual"` + CC-BY `attribution` |
| Crypto OHLCV | `vnfin.crypto.client().get_klines(sym, vnfin.Interval.D1, start, end)` | `CryptoHistory` · USD |
| FX rate | `vnfin.fx.get_rate("USD")` | `FXRate` · VND per 1 USD |
| Macro | `vnfin.macro.get_indicator("VNM", vnfin.macro.MacroIndicator.GDP)` — indicators: `GDP`, `GDP_GROWTH`, `CPI`, `INFLATION`, `UNEMPLOYMENT`, `CPI_YOY`, `POLICY_RATE` (monthly SBV proxy), `LENDING_RATE` / `DEPOSIT_RATE` / `REAL_INTEREST_RATE` (annual, World Bank `FR.INR.*`) | `IndicatorSeries` |
| Fixed-income coverage | `vnfin.diagnostics.explain_fixed_income_coverage()` (offline) — govt-bond yield curve is unavailable (deferred); discloses the policy proxy + the three annual WB rates and that `DEPOSIT_RATE` is an annual aggregate | `RequestDiagnostic` |
| Equity universe | `vnfin.equities.universe("HOSE")` (or `"HNX"`/`"UPCOM"`; `None` merges all three) | `EquityUniverse` of `EquitySecurity` — current snapshot per board; `partial_universe_coverage` ~96% |
| Equity GICS sector | `vnfin.equities.profile(sym)` · `vnfin.equities.sectors()` · `vnfin.equities.by_sector("VNFIN"\|"Financials")` · `vnfin.equities.universe("HOSE", with_sector=True)` | `EquityProfile` (wraps the sector-enriched `.security` + a `.warnings` coverage line) · `tuple[GicsSector]` (10) · `EquitySector` (basket members) — **derived** (clean-room) by inverting the 10 VNAllShare sector baskets; HOSE-only ~74%, unmapped HOSE + all HNX/UPCoM → `None` (`sector_partial_coverage`, never fabricated); current-snapshot |
| Cash dividends | `vnfin.corp_actions.dividends(sym, seed_id=)` | `DividendHistory` of `CashDividendEvent` · VND/share — v1 CASH only, `ex_date=None`, `ratio_pct` withheld on tax-qualified lines (`vsdc_ratio_tax_deferred`) |

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

# Silver / platinum — ANNUAL history (USD/oz), World Bank CMO Pink Sheet
mh = vnfin.metals.history("silver", date(2000, 1, 1), date(2025, 12, 31))
print(mh.product, mh.value_unit, mh.frequency, len(mh.bars))  # 'XAG' 'USD/oz' 'annual' ...
# vnfin.metals.history("gold") -> InvalidData (use vnfin.gold); "palladium" -> InvalidData (named)
```

## Errors

Failures are `vnfin.exceptions`: `SourceUnavailable`, `EmptyData`, `StaleData` (an `EmptyData`
subclass — data ends before the requested window), `InvalidData`,
`UnsupportedInterval`, `UnitMismatchError`, `AllSourcesFailed` (carries per-source `.attempts`).
Bad input (missing/inverted dates, malformed currency) raises before any network call.

**Bad bars are quarantined, not fatal (#186).** In `prices.history` / `index_history`, an
*isolated* corrupt bar (OHLC-invariant violation, non-positive/non-finite price, bad volume,
unparseable scalar, or a conflicting same-date duplicate) is **dropped from the series, never
served** — the rest of the window is returned and the result carries a `quarantined_invalid_bars`
warning naming the dropped dates + reasons (so one bad day no longer blocks a 10-year chart). A
*systematically* broken source (too many bad rows) still fails the source → failover. Structural
faults (misaligned/missing arrays, malformed envelope) still hard-raise `InvalidData`.

## Warning tokens

Every typed result carries a `warnings` tuple (`result.warnings`) — possibly empty, each entry a
string `token` or `token: human-readable detail`. **Match on the token prefix** (the part before
any `:`); the tail is descriptive and may change. Warnings are namespaced, **never silent, never
fabricated** — they disclose a quality/coverage/provenance signal without failing the call. The
complete caller-facing set (each with the issue that introduced it; `—` = pre-existing):

| Token (prefix) | Result / accessor | Meaning | Issue |
|---|---|---|---|
| `partial_start_coverage` | `prices.history` | First bar is more than the tolerance after the requested start (clipped / newly-listed / source lag). | — |
| `partial_end_coverage` | `prices.history` | Last bar is more than the tolerance before the requested end (VN trading-calendar aware); series may be stale. | — |
| `trailing_zero_volume_tail` | `prices.history` / `index_history` | Trailing run of ≥10 zero-volume flat (O=H=L=C) bars — likely suspended/delisted or forward-filled phantom data (bars kept, not dropped). | #176 |
| `quarantined_invalid_bars` | `prices.history` / `index_history` | Isolated corrupt bars dropped (OHLC-invariant, non-positive/non-finite, bad volume, duplicate timestamp); the rest of the window is served. | #186 |
| `resampled_from_d1` | `prices.history` / `index_history` | Series aggregated client-side from D1 to a coarser period (W1/MN1/Q1/Y1), not native to the interval. | #183 |
| `resample_partial_period` | `prices.history` / `index_history` | An edge resampled period is incomplete relative to the window (bars kept, marked provisional). | #183 |
| `deduped_duplicate_daily_index_bars` | `index_history` | Identical same-date duplicate index bar kept once; a *conflicting* same-date pair drops that date entirely. | #162 |
| `recovered_midnight_open_placeholder` | `index_history` | A same-date D1 pair identical in high/low/close/volume but differing only in `open`, where exactly one row is at VN-local 00:00 — that midnight row is a synthetic open placeholder, so it is dropped and the real (non-midnight) row is kept. A *recovery* (not a quarantine): the date is served and is not charged to the failover threshold. | #187 |
| `stitched_multi_source` | `index_history_stitched` | History stitched across per-calendar-year segments (each stitched year also emits a `stitched_segment` provenance line). | #147 |
| `stitched_segment` | `index_history_stitched` | Per-segment provenance of a stitched series — which source served a given calendar year and how many bars (`stitched_segment: <year> <source> (<n> bars)`). | #147 |
| `weights_not_available` | `index_constituents` | Membership only — no per-stock index weights (`weight=None`); never fabricated. | — |
| `current_snapshot_only` | `index_constituents` | **Always present** — the basket is the CURRENT membership as fetched, NOT a point-in-time/historical snapshot (`as_of=None`, never fabricated); backtests using it inherit survivorship and look-ahead bias. | #175 |
| `fallback_instrument_served` | `indices.world` | Requested SPY (USD/share) unavailable; served Stooq `^SPX` (index points, ~10× different magnitude) — rebase before comparing. | #177 |
| `proxy_substitution` | `indices.world` | Asked a raw index (`^N225`/`^SSEC`/`^STI`) but served a **USD ETF proxy** (`EWJ`/`FXI`/`EWS`) — embeds USD/local FX, NOT a faithful tracker of the raw index. Also exposed via the structured `PriceHistory.proxy_for` field. | #193 |
| `world_reference_excludes_domestic_premium` | `gold.world_reference_history_vnd` | **Always present** — world-gold-implied VND, excludes the +10–21% VN domestic (SJC/BTMC) premium; NOT the domestic price. | #178 |
| `world_reference_annual_basis` | `gold.world_reference_history_vnd` | **Always present** — one point per calendar year (annual-avg gold × annual USD/VND × 37.5/31.1035), stamped Jan-1; not a daily series. | #178 |
| `world_reference_partial_year_coverage` | `gold.world_reference_history_vnd` | Some requested years dropped for lack of a paired gold+FX observation (honest intersection). | #178 |
| `world_reference_trailing_year_incomplete` | `gold.world_reference_history_vnd` | Latest emitted year is the current in-progress year — its mean is year-to-date, not a full-year value. | #178 |
| `world_reference_gold_source_fallback` | `gold.world_reference_history_vnd` | Primary World Bank CMO annual source failed → daily-averaging (CurrencyApi→Stooq) fallback used. | #185 |
| `world_reference_gold_leg_*` / `world_reference_fx_leg_*` | `gold.world_reference_history_vnd` | **Family:** an upstream gold-/FX-leg warning forwarded, namespaced by leg (e.g. `world_reference_gold_leg_partial_coverage`). | #178 |
| `partial_coverage` | `gold.world()` / `crypto` | Series covers below the warn threshold of expected trading days or the requested range (accepted-but-gappy). | #169 |
| `mixed_source` | `fundamentals.metrics` | Metric inputs span more than one source. | #157 |
| `skipped_mismatched_report_rows` | `fundamentals.get_financials` | Provider statement rows whose `reportType`/`modelType` did not match the requested period/template were dropped (contract violation, never a silent drop). | #44 |
| `skipped_period_rows` | `fundamentals.get_financials` | Provider period rows that could not be mapped to the requested cadence were dropped (CafeF; never a silent drop). | #45 |
| `traded_value_estimated_from_close_x_volume` | `liquidity` | Daily traded value estimated as close × volume (not provider-published turnover). | #146 |
| `zero_liquidity` | `liquidity` | Average daily traded value is zero over the requested window. | #146 |
| `series_end_gap` | `macro.get_indicator` | Latest monthly observation lags the series' own cadence (possible staleness/discontinuation). | #179 |
| `imf_weo` | `macro.get_indicator` | Years ≥ the projection year are WEO forecasts (excluded from `latest()`). | — |
| `failover` | `macro.get_indicator` | Result required failover across sources (carries the per-source note). | — |
| `nav_end_gap` | `funds.nav_history` | Latest fund NAV is older than the fund's own trailing cadence allows (stale / paused / dormant feed). | #172 |
| `deduped_duplicate_nav_rows` | `funds.nav_history` | Identical-value duplicate `navDate` rows collapsed to one (kept once + warned); a *conflicting* same-date NAV is quarantined (see `quarantined_conflicting_navdates`). | #158 |
| `quarantined_conflicting_navdates` | `funds.nav_history` | Same-date NAV conflict(s) quarantined — two different NAV values for one `navDate`; that date is **dropped** entirely (never picked, never averaged) and the rest of the series is served. Names the dropped dates. A systematically-conflicting feed (>10% of in-window dates, floor 3) still raises `InvalidData`. | #194 |
| `partial_universe_coverage` | `equities.universe` | **Always present** per board — the universe is index-basket-derived (~96% of the full SSC roster), not the complete listing. | #167 |
| `listing_date_not_available` | `equities.universe` | **Always present** per board — the provider's `firstTradingDate` is `'0'` (unusable), so no listing date is exposed. | #167 |
| `sector_not_available` | `equities.universe` | **Always present** per board on the plain `universe()` path — sector/industry is absent from this payload (not fabricated). Replaced by `sector_partial_coverage` when sector data is derived (`with_sector=True`). | #167 |
| `sector_partial_coverage` | `equities.profile` / `by_sector` / `universe(with_sector)` | Derived GICS sector is HOSE-only (~74%); unmapped HOSE + all HNX/UPCoM → null, never fabricated; also flags any multi-basket symbol | #195 |
| `cross_board_duplicate_symbol` | `equities.universe` | On an `exchange=None` merge, a symbol seen on more than one board is kept-first (board order HOSE, HNX, UPCOM) and the dropped copy is disclosed (never silent). | #167 |
| `board_unavailable` | `equities.universe` | On an `exchange=None` merge, one board's fetch failed (`SourceUnavailable`/`EmptyData`/`InvalidData`); it is **skipped, not fatal** — the other boards still merge, and the skip is disclosed (`board_unavailable: {board} — fetch skipped ({ExcType}): {reason}`). If **all** boards fail the merge re-raises. A single-board `universe("HNX")` still raises (merge-only skip). | #189 |
| `fund_nav_stale` | `funds.list_funds` | List-level: ≥1 listed fund's own `nav_as_of` is older than 7 calendar days (stale NAV feed); enumerates the stale codes@date, capped at 5 + `+M more`. Funds with unknown `nav_as_of` are never flagged. | #190 |
| `fund_missing_fees` | `funds.list_funds` | List-level: ≥1 listed fund has **no disclosed management fee** (`management_fee_pct=None` — the provider lists `managementFee` on equity rows only), so an absent fee is never mistaken for a zero fee; enumerates the affected codes, capped at 5 + `+M more`. Suppressed when `include_metadata=False`. | #155 |
| `fund_partial_holdings` | `funds.asset_allocation` | Detail-doc: the disclosed top holdings (equity + bond) sum to **less than 50% of NAV**, i.e. substantial portfolio exposure is undisclosed (top-N disclosure, not the full book). A bounded false-positive (a genuinely concentrated fund may trip it) is preferred over a false-negative that hides an opaque book. | #155 |
| `ex_date_unavailable` | `corp_actions.dividends` | **Always present** per event — v1 serves the VSDC depository spine, which publishes no ex-date (the VNDirect finfo enrichment leg is held for v2), so `ex_date` is always `None` and is never fabricated or derived. | #163 |
| `corp_action_source_partial` | `corp_actions.dividends` | **Always present** per result (`DividendHistory`) — the result is from the VSDC depository spine ALONE; the ex-date enrichment leg is not active in v1 (in v2 it fires when the finfo leg is down). | #163 |
| `vsdc_parse_degraded` | `corp_actions.dividends` | Per event: a page IS a cash dividend (title/reason) but the parse is not fully trustworthy — ≥1 **primary field** unparseable (the record date, or both `ratio_pct` AND `cash_per_share`); OR the cash↔ratio pairing could not be trusted so `ratio_pct` was left `None` rather than mis-paired. This covers an implausible `> 100%` ratio; a `Mệnh giá` cross-check that confirms **more than one** distinct candidate (ambiguous twins, e.g. a gross + a "sau điều chỉnh" adjusted rate); OR a ratio stated on a **different `<br />` line** than the cash anchor (v1 does not pair across lines, so the unpaired ratio is dropped, never silently). Ratio percentages are parsed **decimal-aware** (`8.5%`/`8,5%` → `8.5`, never `85`). OR the page listed **multiple cash tranches** — in EITHER phrasing (`…được nhận X đồng` or `…số tiền X đồng/cổ phiếu`) — and only the first is surfaced in v1. The affected fields are left `None`; the event is surfaced, never silently dropped or fabricated; an undated event is windowed by its `pay_date`. A **net-of-tax** ratio line is NOT this token — see `vsdc_ratio_tax_deferred`. | #163 |
| `vsdc_ratio_tax_deferred` | `corp_actions.dividends` | Per event: the ratio line carries a **tax/withholding signal** (thuế / TNCN / khấu trừ) so its `%` is net-vs-gross ambiguous; under the #163 v1 de-scope the library no longer classifies net-vs-gross (an open-ended, silent-wrong-prone problem), so the ratio is **withheld** (`ratio_pct=None`) and disclosed via this token (net-vs-gross classification deferred to v2). **Distinct from `vsdc_parse_degraded`** (a parse fault): here the line parsed fine but is intentionally withheld. A single-tranche tax line carries this token only; a multi-tranche tax line carries both. | #163 |
| `coverage_truncated_at_max_fetch` | `corp_actions.dividends` | Per result (`DividendHistory`): the bounded same-org crawl stopped at `max_fetch` with announcements still un-fetched, so the returned history is **NOT exhaustive** — raise `max_fetch` (or pass a `seed_id`) for fuller coverage. Absent when the crawl exhausts the frontier. | #163 |
| `corp_action_fetch_incomplete` | `corp_actions.dividends` | Per result (`DividendHistory`): ≥1 same-org announcement page failed to **fetch** (`SourceError`) or to **parse** (`InvalidData` — empty/whitespace body or no resolvable ticker) during the crawl, so its (and any onward-linked) events are absent — the history may be incomplete. The crawl tolerates per-page failures rather than aborting, but discloses the gap (never silent). Suffix: `: {n} announcement page(s) skipped (fetch or parse failed)`. | #163 |
| `corp_action_seed_not_found` | `corp_actions.dividends` | Per result (`DividendHistory`): no-seed auto-discovery scanned its recent-ID window WITHOUT finding any announcement page for the ticker, so the **empty** history is NOT a confirmed never-paid — the discovery window may be too small/recent. Pass a `seed_id` (or widen the window) for an authoritative result. Absent whenever a seed was found or supplied. | #163 |

## Full reference

For every domain — all factory verbs, signatures, result fields, gotchas, and verified examples —
read **[reference/domains.md](reference/domains.md)**. For canonical units see the library's
`docs/units.md`; for the full prose guide see `docs/ai-usage.md`. Pin a version for
reproducibility (the public API is SemVer-stable — see `docs/stability.md`).
