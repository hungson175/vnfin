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

## Terms / licensing

SSI iBoard data is fetched at **runtime only** — no bundled dataset, no redistribution of
provider rows (synthetic fixtures only in the test suite). Treat the payload as
runtime-fetch / no-redistribution, consistent with the index-constituents source.

## Deferred

`profile(symbol)` (per-symbol lookup) is deferred. To get one symbol, call
`universe(exchange=...)` and filter the returned securities
(`next(s for s in universe("HOSE") if s.symbol == "FPT")`).
