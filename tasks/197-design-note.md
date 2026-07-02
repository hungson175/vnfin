# #197 design note — CN/KR/JP world indices as loudly-labeled USD ETF proxies

Status: **DESIGN NOTE FOR REVIEWER GATE — no implementation yet**  
Date checked: 2026-07-02 +07  
Intake/spec: `/home/hungson175/tools/vnfin-oss-reviewer/tasks/197-world-indices-cn-kr-jp-spec.md`

## Clean-room / source-vetting posture

- VNStock blacklist checklist read before this research. Searches used the required exclusions:
  `-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"`.
- No VNStock/vnstock/VNStock-derived result, code, docs, endpoint map, schema, or behavior was opened or used.
- Evidence is from primary/official sources only: Alpha Vantage official documentation/listing-status
  endpoint, iShares/BlackRock official fund fact sheets, and DWS/Xtrackers official fund fact sheet.
- Redistribution posture remains #193's: runtime-fetch via the end user's Alpha Vantage BYOK account;
  no market data is bundled or redistributed.

## Existing code facts (checked before design)

`vnfin/indices/world_sources.py` currently has exactly 5 `WORLD_INDEX_SPECS` entries, in this order:

1. `SPY` → `SPY` (direct)
2. `QQQ` → `QQQ` (direct)
3. `^N225` → `EWJ` (proxy)
4. `^SSEC` → `FXI` (proxy)
5. `^STI` → `EWS` (proxy)

`SUPPORTED_WORLD_SYMBOLS = tuple(WORLD_INDEX_SPECS)`. The public/client gate is
`world_client._validate_symbol(...)`, which rejects non-members before the source default-to-SPY
behavior can apply. `_proxy_warnings(...)` already emits the loud `proxy_substitution` warning whenever
`PriceHistory.proxy_for` is present; direct results (`proxy_for is None`) emit no proxy warning.

## Proposed final symbol list

Add exactly three canonical world symbols, all as **USD/share US-listed ETF proxies** through the
existing Alpha Vantage `TIME_SERIES_DAILY` adapter:

| Asked canonical symbol | Served AV ticker | Public index label | ETF actually tracks | `value_unit` | `currency` | `proxy_for` | `fx_pair` | Accuracy posture |
|---|---:|---|---|---|---|---|---|---|
| `^KS11` | `EWY` | KOSPI Composite | MSCI Korea 25/50 Index (Net) | `USD/share (EWY ETF)` | `USD` | `^KS11` | `USD/KRW` | broad Korea proxy; **not** raw KOSPI |
| `^CSI300` | `ASHR` | CSI 300 | CSI 300 Index | `USD/share (ASHR ETF)` | `USD` | `^CSI300` | `USD/CNY` | closest/exact named-index proxy, still ETF price not index points |
| `^HSI` | `EWH` | Hang Seng Index | MSCI Hong Kong 25-50 Index (USD) (Net) | `USD/share (EWH ETF)` | `USD` | `^HSI` | `USD/HKD` | broad Hong Kong proxy; **not** raw Hang Seng |

No new bare aliases in #197. The existing world accessor's convention is uppercase exact membership in
`SUPPORTED_WORLD_SYMBOLS`, including caret-prefixed raw-index asked symbols (`^N225`, `^SSEC`, `^STI`).
There is no world-index alias resolver today; adding `KOSPI`/`CSI300`/`HSI` aliases would require either
client-code changes or duplicate table members and would move this beyond the requested declarative
extension. If Boss wants aliases later, treat that as a separate additive ergonomics task with its own
membership/proxy-label tests.

## AV-serviceability evidence

Alpha Vantage official docs state `TIME_SERIES_DAILY` returns raw daily OHLCV for the requested **global
equity** and instruct users to use its Search Endpoint for supported global stock, **ETF**, or mutual-fund
symbols. The current code already uses that endpoint shape.

I also probed Alpha Vantage's official `LISTING_STATUS` endpoint with the public `demo` key and confirmed
all three served ETF tickers are active ETF listings in Alpha Vantage's own instrument universe:

```text
EWY  | ISHARES MSCI SOUTH KOREA ETF                 | NYSE | ETF | Active
ASHR | XTRACKERS HARVEST CSI 300 CHINA A-SHARES ETF | NYSE | ETF | Active
EWH  | ISHARES MSCI HONG KONG ETF                   | NYSE | ETF | Active
```

I did **not** run live `TIME_SERIES_DAILY` because this environment has no `ALPHAVANTAGE_API_KEY`; CI will
remain offline/synthetic per project policy. The serviceability basis is therefore: official AV daily API
supports global equity/ETF symbols + official AV listing-status marks each served ticker active.

## Proxy-accuracy evidence and labels

- `EWY` is iShares MSCI South Korea ETF. BlackRock's fact sheet lists benchmark
  `MSCI Korea 25/50 Index (Net)` and exchange `NYSE Arca`. This is a defensible broad South Korea ETF
  proxy for a KOSPI ask, but it is **not** KOSPI Composite; the existing warning text says "not the raw
  <index> index" and "not a faithful tracker", which is exactly the right loud label.
- `ASHR` is Xtrackers Harvest CSI 300 China A-Shares ETF. DWS's fact sheet says it seeks results
  corresponding generally to the `CSI 300 Index`; index details list `Name CSI 300 Index` and `NYSE ticker
  ASHR`. This is the closest of the three: named-index proxy is exact, but the served series is still a
  USD ETF market price, not raw CNY index points.
- `EWH` is iShares MSCI Hong Kong ETF. BlackRock's fact sheet lists benchmark
  `MSCI Hong Kong 25-50 Index (USD) (Net)` and exchange `NYSE Arca`. This is a defensible Hong Kong equity
  ETF proxy for Hang Seng, but **not** the Hang Seng Index itself; the `proxy_substitution` label must remain loud.

## Implementation shape after gate

Declarative-only code change:

```python
"^KS11": _WorldIndexSpec(
    "^KS11", "EWY", "USD/share (EWY ETF)", "USD",
    "KOSPI Composite", "^KS11", "USD/KRW",
),
"^CSI300": _WorldIndexSpec(
    "^CSI300", "ASHR", "USD/share (ASHR ETF)", "USD",
    "CSI 300", "^CSI300", "USD/CNY",
),
"^HSI": _WorldIndexSpec(
    "^HSI", "EWH", "USD/share (EWH ETF)", "USD",
    "Hang Seng Index", "^HSI", "USD/HKD",
),
```

Placement: append after the existing five entries to keep the current 5 specs byte-for-byte unchanged and
preserve tuple order for existing users/tests. The top-of-file comments/docstrings that say "5" and list
the three old Asian proxies will be updated, but `_proxy_warnings`, `_validate_symbol`,
`world_index_spec`, Stooq SPY-only gating, and failover mechanics remain untouched.

## Japan / TOPIX decision

Do **not** add TOPIX. Japan is already covered as `^N225` → `EWJ`; `EWJ` tracks MSCI Japan (not Nikkei
225 and not TOPIX), so adding TOPIX with the same `EWJ` ticker would be a duplicate proxy with a different
raw-index label and would increase user confusion. Keep only the existing `^N225` entry in #197.

## Tests to write red-first after gate

1. Parametrize the proxy-labeling tests for `^KS11`, `^CSI300`, `^HSI`: result has correct
   `provider_symbol`, `value_unit`, `currency`, `proxy_for`, `fx_pair`-driven warning detail, and
   `proxy_substitution` names requested index + served ETF.
2. Membership invariant: the three new symbols are supported, while non-members such as `^DAX` and
   `^FTSE` still raise before network / ultimately name the unsupported symbol; they must never be served
   as `SPY` or Stooq `^SPX`.
3. Regression pin: the existing five specs' object fields and warning strings for `SPY`, `QQQ`, `^N225`,
   `^SSEC`, `^STI` remain byte-identical; `SPY`/`QQQ` still have no proxy warning.
4. Token/doc lockstep: no new warning token; `_WARNING_TOKENS_180` remains unchanged because all new
   proxies reuse `proxy_substitution`.
5. Docs/skill/changelog/coverage doc update in lockstep: `docs/api.md`, `docs/sources/indices-world.md`,
   `skills/vnfin/SKILL.md`, and `CHANGELOG.md` list 8 supported symbols and loud proxy caveats.
6. Clean-room diff check: no vnstock string beyond existing blacklist references; no bundled live data.

## Gate request

Please gate this design with Codex×2 review focus on:

- whether `^KS11`/`^CSI300`/`^HSI` as **canonical-only** symbols is accepted (no aliases in #197),
- whether `EWY`/`ASHR`/`EWH` are accepted as the final ETFs with the accuracy caveats above,
- whether appending the three specs after the existing five satisfies the "existing 5 byte-unchanged" invariant.

## Sources checked

- Alpha Vantage official API docs, `TIME_SERIES_DAILY` and supported symbol/search guidance:
  https://www.alphavantage.co/documentation/
- Alpha Vantage official listing-status endpoint probe:
  https://www.alphavantage.co/query?function=LISTING_STATUS&apikey=demo
- iShares/BlackRock EWY fact sheet:
  https://www.ishares.com/us/literature/fact-sheet/ewy-ishares-msci-south-korea-etf-fund-fact-sheet-en-us.pdf
- DWS/Xtrackers ASHR fact sheet:
  https://www.dws.com/US/EN/resources/Xtrackers-Harvest-CSI-300-China-A-Shares-ETF/ASHR_fact-sheet.pdf
- iShares/BlackRock EWH fact sheet:
  https://www.ishares.com/us/literature/fact-sheet/ewh-ishares-msci-hong-kong-etf-fund-fact-sheet-en-us.pdf
