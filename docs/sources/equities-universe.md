# Source provenance — VN equity universe (SSI iBoard)

Clean-room. VNStock and all derivatives were excluded from research and implementation.
The endpoint below is the same public SSI iBoard query host already used for index
constituents (`docs/sources/indices-constituents.md`); it was confirmed empirically with
`curl -4` + a browser User-Agent. The `vnfin.equities` domain (issue #167) enumerates the
investable VN equity universe per board — a **data primitive only**, NOT a
screener/ranker/advisor.

## Endpoint

    GET https://iboard-query.ssi.com.vn/stock/group/{BOARD_TOKEN}

Returns `{"code":"SUCCESS","data":[{stockSymbol, exchange, market, stockType, companyNameEn,
companyNameVi, isin, adminStatus, parValue, tradingCurrencyISOCode, firstTradingDate, ...}, ...]}`
— one object per security on the board.

### Board-token aliasing (NON-OBVIOUS)

Plain `HOSE` / `HNX` / `UPCOM` return an **empty** list. The full per-board stock list is
addressed by the board's index-group token (case-sensitive):

| Board (input) | Group token (URL) | Approx. rows returned (per reviewer source report) |
|---|---|---|
| `HOSE` | `VNINDEX` | ~403 |
| `HNX` | `HnxIndex` | ~300 |
| `UPCOM` | `HNXUpcomIndex` | ~828 |

`SsiIboardUniverseSource.normalize_board(...)` upper/strips the input and maps it to the
token; an unknown board raises `InvalidData` **before** any network call.

### Equities-only filter

Only rows with `stockType == "s"` are kept. Covered warrants (`w`), ETFs (`e`), and funds
(`m`) are silently skipped — they are simply not equities, not an error.

## Per-symbol reference metadata

Each kept row maps to an `EquitySecurity`:

| Field | Payload key | Notes |
|---|---|---|
| `symbol` (required) | `stockSymbol` | canonicalized (upper/strip; malformed → `InvalidData`) |
| `exchange` (required) | `exchange` | `.upper()` |
| `company_name_en` | `companyNameEn` | optional → `None` if absent/blank |
| `company_name_vi` | `companyNameVi` | optional → `None` |
| `isin` | `isin` | optional → `None` |
| `listing_status` | `adminStatus` | optional → `None` |
| `par_value` | `parValue` | parsed to a number (shared provider-float parser); `0`/non-positive → `None` (provider uses `0` as "not set") |
| `currency` | `tradingCurrencyISOCode` | optional → `None` |

Every optional field is `None` whenever the provider omits/blanks it — **never fabricated**.

## The three honest gaps (always-present warnings)

This payload is index-basket-derived and does **not** cover the full statutory roster, so the
result's `warnings` ALWAYS disclose the known gaps (one entry per contributing board; the
token prefix is stable, the board + detail follow the `:`):

- `partial_universe_coverage: <BOARD> — index-basket-derived, ~96% of the full SSC roster (not complete)` —
  cross-checked against the SSC (State Securities Commission) listed-company count; the
  index-group lists cover roughly 96% of the roster, not 100%. This is **not** the complete
  legal listing.
- `listing_date_not_available: <BOARD> — provider firstTradingDate is '0' (unusable)` — the
  provider returns `firstTradingDate == '0'` for ~all rows, so no listing date is exposed
  (the field is intentionally absent from the model rather than fabricated).
- `sector_not_available: <BOARD> — sector/industry absent from this payload` — sector/industry
  classification is not in this endpoint's payload.

`security_type` is also intentionally **not** a model field: after the `stockType=='s'` filter
it is structurally always `"s"`, so exposing it would be misleading.

## `exchange=None` merge — cross-board keep-first

`universe()` (no board) fetches all three boards in order (HOSE, HNX, UPCOM) and concatenates
their securities. A symbol that appears on more than one board is **kept-first** (the HOSE
copy wins over HNX over UPCOM) and the dropped copy is disclosed — never silently removed,
never a raise (a single live-provider glitch must not nuke all three boards):

    cross_board_duplicate_symbol: <SYM> kept from <board_a>, dropped from <board_b>

The merged result carries `board="ALL"`, every contributing board's honest-gap tokens
(attributed by board), and one `cross_board_duplicate_symbol` entry per collision. A duplicate
symbol *within a single board* is a contract violation and DOES raise `InvalidData`.

## Derived GICS L1 sector (issue #195)

The stock-group payload carries **no** sector/industry field (hence the always-on
`sector_not_available` token on the plain `universe()` path). Rather than adopt a provider
industry id, the GICS L1 sector is **derived** — clean-room — by inverting the **10
VNAllShare sector index baskets** that `vnfin.indices` already fetches via the same SSI
iBoard query group endpoint (see [indices-constituents.md](indices-constituents.md)):

| GICS code | GICS L1 sector (public MSCI/S&P name) |
|---|---|
| `VNFIN` | Financials |
| `VNIT` | Information Technology |
| `VNREAL` | Real Estate |
| `VNMAT` | Materials |
| `VNCONS` | Consumer Staples |
| `VNCOND` | Consumer Discretionary |
| `VNIND` | Industrials |
| `VNENE` | Energy |
| `VNHEAL` | Health Care |
| `VNUTI` | Utilities |

A symbol's sector is the basket it belongs to; the pinned code→name map gives the L1 name.

- **Provenance:** derived from the VNAllShare sector indices via the SSI iboard-query group
  endpoint (`sector_source == "ssi_iboard_query"`, `sector_scheme == "GICS"`). The 10
  baskets are fetched at **runtime only** (one fetch per basket, cached 6h per process) — no
  bundled dataset, no redistribution; synthetic baskets only in the test suite.
- **Coverage is HOSE-only (~74% of HOSE).** An unmapped HOSE symbol and **every** HNX/UPCoM
  symbol keep all four sector fields (`sector_code`/`sector_name`/`sector_scheme`/
  `sector_source`) `None` **as a unit** — never fabricated. A symbol seen in ≥2 baskets
  (should not happen for GICS L1) degrades to a deterministic `None` (refuse to pick),
  named in the disclosure. The `sector_partial_coverage` token discloses both gaps.
- **Current snapshot (survivorship).** The baskets are the CURRENT membership (the
  underlying constituents source emits `current_snapshot_only`), so the derived sector is
  the symbol's *current* GICS sector, **not** point-in-time — backtests inherit survivorship.
- **Clean-room.** No vnstock; no `industryID`/`industryIDv2`/Vietnamese `industry_name`.

Accessors: `vnfin.equities.profile(symbol)` (an `EquityProfile` wrapping the full sector-enriched
`EquitySecurity` in `.security` + a `sector_partial_coverage` coverage line in `.warnings`),
`vnfin.equities.sectors()` (the static 10 `GicsSector`), `vnfin.equities.by_sector(code_or_name)`
(one basket's members), and `vnfin.equities.universe(..., with_sector=True)` (enriched rows;
the per-board `sector_not_available` token becomes `sector_partial_coverage`).

## Terms / licensing

SSI iBoard data is fetched at **runtime only** — no bundled dataset, no redistribution of
provider rows (synthetic fixtures only in the test suite). Treat the payload as
runtime-fetch / no-redistribution, consistent with the index-constituents source.

## Deferred

`profile(symbol)` now exists (issue #195) and returns the symbol's full sector-enriched
`EquitySecurity` from the merged all-board universe. A non-sector one-symbol lookup can
still use the filter pattern (`next(s for s in universe("HOSE") if s.symbol == "FPT")`).
The finer `industries()`/`by_industry()` tier and `industry_peers(symbol)` remain deferred
(no clean finer data — the library does not imply data it lacks).
