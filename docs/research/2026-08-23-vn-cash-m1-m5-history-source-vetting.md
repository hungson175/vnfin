# VN cash-equity M1/M5 history source vetting — #209 + #210

**Date:** 23 August 2026 (UTC+7)
**Scope:** source/design gate only; no runtime capability is enabled by this note
**Requested public paths:** existing `prices.history(..., interval=Interval.M1)` and
`prices.history(..., interval=Interval.M5)`
**Requested inclusive window:** `2018-08-13..2026-08-19`
**Disposition:** **SOURCE-GAP CLOSURE** for M1 and M5 independently

## 1. Boundary and clean-room record

Issues #209 and #210 are one source-depth review, but M1 and M5 remain separate
qualification units. A result that proves one interval never qualifies the other. The
review does not add a basket/archive/backtest/helper, historical constituent
reconstruction, cross-source stitch, M1-to-M5 synthesis, first-ten helper, VN30F join,
or advice/signal behavior.

Before research, `docs/vnstock-blacklist.md` was read. Every web search used this exact
exclusion set:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited or derivative material was opened, cited, compared, installed, or used.
The evidence below uses only the five named provider-owned chart routes, same-provider
metadata where available, official provider terms, official SSI/HOSE pages, and the
official [TradingView UDF protocol](https://www.tradingview.com/charting-library-docs/latest/connecting_data/UDF/).

No raw response, live OHLCV value, cookie, query-bearing URL, screenshot, or provider
payload is committed. The probe parser retained only sanitized structure, counts,
timestamps/bounds, identity fields, MIME/status, and dispositions in this document.

### 1.1 Bounded probe protocol

The direct history matrix made exactly one sequential no-credential IPv4 request for
each of the eight representative symbols, each candidate, and each interval:

- **80 logical calls = 80 physical calls**: `5 sources × 8 symbols × 2 intervals`;
- no retry, no pagination follow, no parallelism, no cookie/session reuse, and a 25-second
  transport timeout;
- request dates encoded as local `2018-08-13T00:00:00+07:00` through
  `2026-08-19T23:59:59+07:00`, or Unix seconds `1534093200..1787158799`;
- one desktop browser `User-Agent` was sent because the existing adapters use it. This
  is an observed transport dependency, **not** evidence of automation permission;
- an additional **16 same-provider identity metadata calls** covered SSI and VPS for the
  same eight symbols, and one **current-snapshot cohort call** fetched SSI group `VN30`;
- the metadata/cohort observations were not used to repair another provider's history
  response. The evidence ledger therefore records 97 physical observations, while the
  qualification matrix itself remains the 80-call history matrix.

The matrix is a bounded observation, not an SLA, a retention guarantee, or permission
to repeat bulk requests. Empty, capped, failed, or partial responses prove only those
exact bounded observations.

## 2. Frozen current-snapshot cohort

The official no-login SSI group route
[`GET /stock/group/VN30`](https://iboard-query.ssi.com.vn/stock/group/VN30) returned
HTTP 200, full `Content-Type` `application/json; charset=utf-8`, normalized media
type `application/json`, `code="SUCCESS"`, 30 rows, and 30 unique `stockSymbol`
values on 23 August 2026. Every row in this snapshot reported `exchange="hose"` and
`stockType="s"` after normalization. SSI's keyed
[`IndexComponents` documentation](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/danh-sach-cac-api)
is a separate authenticated product and was not used as a no-login source.

The SSI-derived member values are not published because the provider terms do not grant
third-party publication/reproduction rights. The safe aggregate observation retained
here is only the row/uniqueness count,
the fact that the eight issue-required controls were present, and the route/snapshot
provenance. No all-30 history audit ran, so no member list is needed for this
source-gap closure.

Safe aggregate observation metadata:

```text
source              = ssi_iboard_query
provider_host       = iboard-query.ssi.com.vn
provider_route      = /stock/group/VN30
provider_group      = VN30
retrieved_at_utc    = 2026-08-23T04:18:57Z
as_of               = None
http_status         = 200
normalized_mime     = application/json
envelope_code       = SUCCESS
row_count           = 30
unique_symbol_count = 30
identity_fields     = stockSymbol, exchange, stockType
snapshot_semantics  = current snapshot only; not point-in-time
required_control_count = 8
```

The seven mandatory discovery controls and the VPL recent-listing control remain the
eight bounded audit cells in the private probe ledger; they are not a public allow-list
or a claim that any security was a VN30 member throughout 2018–2026. The existing
repository contract correctly keeps `as_of=None` and emits `current_snapshot_only`;
this note preserves that boundary. No all-30 history audit was run because no candidate
passed the source/legal gate, so no VN30 historical coverage claim is made.

## 3. Direct history matrix

Each cell below is an independent provider/route/interval observation. `rows` is the
number of returned timestamp rows, not a completeness count. The local timestamp span
is the first and last parseable provider timestamp after one UTC-to-`Asia/Ho_Chi_Minh`
conversion. All successful JSON cells had aligned `t/o/h/l/c/v` arrays, strictly
ascending parseable timestamps, and zero duplicate timestamps in this bounded probe.
That does not prove the provider's timestamp is an open or close label, nor prove its
volume or adjustment semantics.

### 3.0 Total request/response/coverage ledger

The following is the compact ledger for all ten provider × interval units and the same
eight controls. The non-secret request mapping is identical across the UDF history
routes unless stated otherwise: `symbol=<control>`, `resolution=1` for M1 or `5` for
M5, `from=1534093200`, and `to=1787158799`. `rows`, `dates`, `start/end`, `day-count`,
and `gap` are respectively the row-count range, distinct-date range, count of cells
containing each literal boundary, range of nonzero rows per observed day, and range of
**non-reproducible cadence-observation counts** across the eight cells. `g` is retained
only as a private probe annotation; it is not a reproducible claim about a holiday,
suspension, listing, lunch, halt, or calendar and is excluded from every qualification
and release gate. A day transition is not classified without an official
calendar/contract.

The **full Content-Type** column is the observed header value. The **normalized media
type** is lower-case media type after stripping parameters; a value containing a
charset is never called a normalized media type. `—` means the response was not usable
for that axis, not that the axis passed.

| Owner / unit | Exact non-secret request parameters | Effective host/path; redirect | Status; full Content-Type; normalized media type | Response identity | Coverage ledger (`rows; dates; start/end; day-count; gap`) | Page / rate axes | Disposition |
|---|---|---|---|---|---|---|---|
| SSI / M1 | `symbol=<control>; resolution=1; from=1534093200; to=1787158799` | `iboard-api.ssi.com.vn/statistics/charts/history`; none observed | 200; `application/json; charset=utf-8`; `application/json` | history symbol absent; same-provider metadata control only | `0–0; 0–0; 0/0; —; 0` | no page/total/cursor; no route-specific rate/automation policy | `TRANSPORT_INCONCLUSIVE + IDENTITY_GAP + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP` |
| SSI / M5 | `symbol=<control>; resolution=5; from=1534093200; to=1787158799` | same; none observed | 200; `application/json; charset=utf-8`; `application/json` | history symbol absent; same-provider metadata control only | `0–0; 0–0; 0/0; —; 0` | same | same |
| VNDirect / M1 | `symbol=<control>; resolution=1; from=1534093200; to=1787158799` | `dchart-api.vndirect.com.vn/dchart/history`; none observed | 200; `text/plain;charset=UTF-8`; `text/plain` | response symbol absent; symbol control 404 | `23164–34823; 128–154; 0/8; 30–228; 20–32` | no page/total/cursor; no route-specific rate/automation policy | `IDENTITY_GAP + COVERAGE_GAP + TIMESTAMP_GAP + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP` |
| VNDirect / M5 | `symbol=<control>; resolution=5; from=1534093200; to=1787158799` | same; none observed | 200; `text/plain;charset=UTF-8`; `text/plain` | response symbol absent; symbol control 404 | `5787–7106; 128–154; 0/8; 20–48; 13–19` | same | same |
| VPS / M1 | `symbol=<control>; resolution=1; from=1534093200; to=1787158799` | `histdatafeed.vps.com.vn/tradingview/history`; none observed | 200; `application/json; charset=utf-8`; `application/json` | response symbol matched all eight; same-provider metadata matched controls | `385–678; 3–3; 0/8; 112–226; 3–15` | no page/total/cursor; no route-specific rate/automation policy | `PARTIAL + COVERAGE_GAP + TIMESTAMP_GAP + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP` |
| VPS / M5 | `symbol=<control>; resolution=5; from=1534093200; to=1787158799` | same; none observed | 200; `application/json; charset=utf-8`; `application/json` | response symbol matched all eight; same-provider metadata matched controls | `354–368; 8–8; 0/8; 40–46; 4–5` | same | same |
| Pinetree / M1 | `symbol=<control>; resolution=1; from=1534093200; to=1787158799` | `charts.pinetree.vn/tv/history`; none observed | 200; `text/plain;charset=UTF-8`; `text/plain` | response symbol absent; negative `nextTime` has no published semantics | `7489–10131; 45–45; 0/8; 106–226; 5–22` | negative `nextTime` not a proven cursor; no rate/automation policy | `IDENTITY_GAP + COVERAGE_GAP + TIMESTAMP_GAP + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP` |
| Pinetree / M5 | `symbol=<control>; resolution=5; from=1534093200; to=1787158799` | same; none observed | 200; `text/plain;charset=UTF-8`; `text/plain` | response symbol absent; negative `nextTime` has no published semantics | `7489–10131; 45–45; 0/8; 106–226; 5–14`; observed cadence is 60 seconds | same; token is not native-M5 evidence | `IDENTITY_GAP + COVERAGE_GAP + TIMESTAMP_GAP + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP` |
| KIS / M1 | `symbol=<control>; resolution=1; from=1534093200; to=1787158799` | `api.ikis.kisvn.vn/api/v3/chart/history`; none observed; effective host matched | 500; no usable full Content-Type/body; `—` | no response identity or typed bars | `0; 0; 0/0; —; —` | no page/total/cursor; no route-specific rate/automation policy | `TRANSPORT_INCONCLUSIVE + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP` |
| KIS / M5 | `symbol=<control>; resolution=5; from=1534093200; to=1787158799` | same; none observed; effective host matched | 500; no usable full Content-Type/body; `—` | no response identity or typed bars | `0; 0; 0/0; —; —` | same | same |

The tables in sections 3.1–3.5 retain the exact eight-control row counts and first/
last local timestamps. This ledger makes the missing source, token, coverage, page,
rate, MIME, identity, and semantic axes explicit rather than treating an omitted value
as a pass.

Per-control day/gap distribution for every non-empty unit is encoded below as
`control: d<distinct dates>, day<minimum–maximum nonzero rows/day>, g<non-reproducible
cadence-observation count>`; `g` is a private, non-reproducible observation and is not
used by a release gate. The eight controls are the mandatory seven plus the recent-listing
control, not the restricted 30-member snapshot:

| Unit | Per-control bounded day/gap distribution |
|---|---|
| VNDirect / M1 | `ACB:d154 day191–227 g23; BID:d154 day156–226 g28; FPT:d154 day152–227 g24; HPG:d154 day224–228 g20; VCB:d154 day122–226 g28; VIC:d154 day153–227 g25; VNM:d154 day191–228 g23; VPL:d128 day30–226 g32` |
| VNDirect / M5 | `ACB:d154 day46–48 g19; BID:d154 day44–48 g19; FPT:d154 day46–48 g19; HPG:d154 day46–48 g19; VCB:d154 day43–48 g19; VIC:d154 day46–48 g19; VNM:d154 day46–48 g19; VPL:d128 day20–46 g13` |
| VPS / M1 | `ACB:d3 day221–226 g4; BID:d3 day214–224 g4; FPT:d3 day223–226 g4; HPG:d3 day226–226 g3; VCB:d3 day224–226 g3; VIC:d3 day225–226 g3; VNM:d3 day226–226 g3; VPL:d3 day112–138 g15` |
| VPS / M5 | `ACB:d8 day46–46 g4; BID:d8 day46–46 g4; FPT:d8 day46–46 g4; HPG:d8 day46–46 g4; VCB:d8 day46–46 g4; VIC:d8 day46–46 g4; VNM:d8 day46–46 g4; VPL:d8 day40–46 g5` |
| Pinetree / M1 | `ACB:d45 day187–226 g7; BID:d45 day186–226 g8; FPT:d45 day187–226 g6; HPG:d45 day187–226 g5; VCB:d45 day187–226 g6; VIC:d45 day187–226 g8; VNM:d45 day187–226 g10; VPL:d45 day106–226 g22` |
| Pinetree / M5 | `ACB:d45 day187–226 g5; BID:d45 day186–226 g6; FPT:d45 day187–226 g5; HPG:d45 day187–226 g5; VCB:d45 day187–226 g6; VIC:d45 day187–226 g7; VNM:d45 day187–226 g8; VPL:d45 day106–226 g14` |
| SSI / M1, SSI / M5 | all eight controls: `d0 day— g0`; no day distribution exists for an empty response |
| KIS / M1, KIS / M5 | all eight controls: no typed bars; `d0 day— g—`; transport failure prevents gap classification |

The same ten units also require explicit semantic axes; the following keyed table
records observed facts separately from unresolved provider proof:

| Unit | Timestamp unit / timezone / candle label | Price/value unit and scale | Volume unit and accumulation | Adjustment policy / basis |
|---|---|---|---|---|
| SSI / M1 | no history timestamp; metadata advertises `Asia/Ho_Chi_Minh`; candle label unresolved | no bar scale observed; adapter scale is not provider proof | empty arrays; metadata does not say volume is absent, but unit/accumulation unresolved | adapter declares `PROVIDER_ADJUSTED`; intraday basis unproven |
| SSI / M5 | same | same | same | same |
| VNDirect / M1 | epoch seconds observed and converted once to `Asia/Ho_Chi_Minh`; 60-second spacing; open/close label unresolved | adapter maps feed scale `1000` to VND; provider value-unit/scale proof unresolved | integer array observed; shares/unit and incremental/cumulative semantics unresolved | adapter declares `PROVIDER_ADJUSTED`; historical intraday homogeneity unproven |
| VNDirect / M5 | epoch seconds; `Asia/Ho_Chi_Minh`; 300-second spacing; open/close label unresolved | same feed-scale caveat | integer array; unit/accumulation unresolved | same |
| VPS / M1 | epoch seconds observed and converted once; metadata timezone `Asia/Ho_Chi_Minh`; 60-second spacing; candle label unresolved | adapter maps feed scale `1000` to VND; provider value-unit/scale proof unresolved | integer array observed; shares/unit and incremental/cumulative semantics unresolved | adapter declares `PROVIDER_ADJUSTED`; historical intraday homogeneity unproven |
| VPS / M5 | epoch seconds; `Asia/Ho_Chi_Minh`; 300-second spacing; candle label unresolved | same feed-scale caveat | integer array; unit/accumulation unresolved | same |
| Pinetree / M1 | epoch seconds observed and converted once; provider timezone/bar label unresolved; 60-second spacing | adapter treats feed as raw VND (`scale=1`); provider value-unit proof unresolved | floating-point array observed; unit/accumulation unresolved | adapter declares `PROVIDER_ADJUSTED`; historical intraday homogeneity unproven |
| Pinetree / M5 | epoch seconds; provider timezone/bar label unresolved; observed spacing is 60 seconds, not native M5 | same raw-VND caveat | floating-point array; unit/accumulation unresolved | same |
| KIS / M1 | no typed timestamp; timezone/candle label unresolved | no typed price/scale | no typed volume | registered policy `MIXED`; no homogeneous basis |
| KIS / M5 | same | same | same | same |

### 3.1 SSI iBoard

Route: `GET https://iboard-api.ssi.com.vn/statistics/charts/history`. The response is
an SSI envelope with inner UDF arrays. The eight SSI M1 and eight SSI M5 calls all
returned HTTP 200, `application/json; charset=utf-8`, `s="ok"`, and zero rows; the
history body did not echo a symbol. No boundary date was present and no timestamp
span existed. This is not historical absence: it is an exact empty observation.

| Symbol | M1 | M5 |
|---|---:|---:|
| ACB | 0; —..— | 0; —..— |
| BID | 0; —..— | 0; —..— |
| FPT | 0; —..— | 0; —..— |
| HPG | 0; —..— | 0; —..— |
| VCB | 0; —..— | 0; —..— |
| VIC | 0; —..— | 0; —..— |
| VNM | 0; —..— | 0; —..— |
| VPL | 0; —..— | 0; —..— |

The same-provider metadata route
[`/statistics/charts/symbol`](https://iboard-api.ssi.com.vn/statistics/charts/symbol)
returned response-backed identity for all eight controls: `symbol=ticker=name` matched,
the exchange was HOSE, timezone was `Asia/Ho_Chi_Minh`, session was `0900-1500`,
intraday was advertised, and volume was not declared absent. That metadata does not
turn the empty history response into coverage, nor prove adjustment or timestamp
semantics for the history route. SSI's official iBoard terms restrict information to
personal viewing/analysis and prohibit publishing, transmitting, or reproducing it to
third parties without written consent ([SSI service terms](https://www.ssi.com.vn/dieu-khoan-dich-vu)).

**Disposition:** M1 and M5 independently `TRANSPORT_INCONCLUSIVE + IDENTITY_GAP +
ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP`; the new qualified
deep-history chain remains empty.

### 3.2 VNDirect chart backend

Route: `GET https://dchart-api.vndirect.com.vn/dchart/history`. The eight M1 and eight
M5 responses were HTTP 200 JSON bodies with full `Content-Type`
`text/plain;charset=UTF-8`, normalized media type `text/plain`, bare UDF shape,
`s="ok"`, integer volume arrays, and no response symbol. The exact `text/plain` media
type is a route fact; JSON parsing alone is not an identity or reuse grant. The
same-provider `/dchart/symbol` control returned HTTP
404, so no response-backed metadata route closed the symbol identity gap.

| Symbol | M1 | M5 |
|---|---:|---:|
| ACB | 34371; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 7095; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| BID | 34073; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 7092; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| FPT | 34570; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 7097; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| HPG | 34823; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 7106; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VCB | 34128; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 7084; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VIC | 34434; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 7092; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VNM | 34287; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 7099; 2021-11-05T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VPL | 23164; 2025-08-29T09:39:00+07:00..2026-08-19T14:45:00+07:00 | 5787; 2025-08-29T09:35:00+07:00..2026-08-19T14:45:00+07:00 |

The seven established symbols therefore did not reach the requested start, and VPL's
first returned date is materially later. The response has real 60-second M1 and
300-second M5 cadence in this probe, but candle open/close meaning, exact volume unit
and incremental/cumulative semantics, and intraday adjustment homogeneity remain
unproven. VNDIRECT's official [Datafeed terms](https://datafeed.vndirect.com.vn/term-full)
require written approval for copying, distribution, publication, or other unauthorized
use; the public chart route has no separate open-data licence.

**Disposition:** M1 and M5 independently `IDENTITY_GAP + COVERAGE_GAP +
TIMESTAMP_GAP + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP`.

### 3.3 VPS chart backend

History route: `GET https://histdatafeed.vps.com.vn/tradingview/history`. The eight M1
and eight M5 responses were HTTP 200 with full `Content-Type`
`application/json; charset=utf-8`, normalized media type `application/json`, bare UDF,
`s="ok"`, and contained a response `symbol` exactly matching each request. The
same-provider metadata route
[`/tradingview/symbols`](https://histdatafeed.vps.com.vn/tradingview/symbols)
also echoed `symbol=ticker=name`, `timezone=Asia/Ho_Chi_Minh`, `session=0900-1500`,
`has_intraday=true`, `has_no_volume=false`, and `pricescale=100`/`pointvalue=1`.

| Symbol | M1 | M5 |
|---|---:|---:|
| ACB | 671; 2026-08-17T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 368; 2026-08-10T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| BID | 653; 2026-08-17T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 368; 2026-08-10T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| FPT | 675; 2026-08-17T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 368; 2026-08-10T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| HPG | 678; 2026-08-17T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 368; 2026-08-10T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VCB | 676; 2026-08-17T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 368; 2026-08-10T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VIC | 677; 2026-08-17T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 368; 2026-08-10T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VNM | 678; 2026-08-17T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 368; 2026-08-10T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VPL | 385; 2026-08-17T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 354; 2026-08-10T09:15:00+07:00..2026-08-19T14:45:00+07:00 |

The response-backed identity and observed cadence pass only those bounded technical
controls. The server returned a recent tail for the requested multi-year window and
did not expose a provider page/total/cursor contract in this observation. VPS's
official [website terms](https://vps.com.vn/dieu-khoan-su-dung) prohibit copying,
transferring, distributing, storing, or creating derivative versions without official
written consent; public no-login access is not reuse permission.

**Disposition:** M1 and M5 independently `PARTIAL + COVERAGE_GAP + TIMESTAMP_GAP +
ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP`.

### 3.4 Pinetree chart backend

Route: `GET https://charts.pinetree.vn/tv/history`. All 16 JSON cells were HTTP 200,
bare UDF, full `Content-Type` `text/plain;charset=UTF-8`, normalized media type
`text/plain`, `s="ok"`, and had aligned arrays with floating-point volume values. The
body did not echo a response symbol. A negative
integer `nextTime` was present but no page semantics or continuation contract was
published or followed.

| Symbol | M1 | M5 |
|---|---:|---:|
| ACB | 10082; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 10082; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| BID | 10015; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 10015; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| FPT | 10126; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 10126; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| HPG | 10131; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 10131; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VCB | 10085; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 10085; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VIC | 10098; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 10098; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VNM | 10033; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 10033; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 |
| VPL | 7489; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 | 7489; 2026-06-18T09:15:00+07:00..2026-08-19T14:45:00+07:00 |

Every Pinetree M5 response had the same row count and 60-second common cadence as its
M1 response in this probe. The requested `resolution=5` token therefore cannot be
treated as native five-minute evidence; it is a direct interval-identity/timestamp
failure, not a reason to aggregate M1 locally. Pinetree's official
[company page](https://pinetree.vn/gioi-thieu/) and [contact page](https://pinetree.vn/post/dich-vu/lien-he/)
identify the provider and a support path, but no route-specific open-data licence or
redistribution permission was found. The official [Stock123 terms](https://pinetree.vn/wp-content/uploads/2019/11/PINETREE-dieu-khoan-su-dung.pdf)
are not an API licence and do not close the chart-route rights axes.

**Disposition:** M1 independently `IDENTITY_GAP + COVERAGE_GAP + TIMESTAMP_GAP +
ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP`; M5 independently
has the same gaps and is explicitly rejected for the observed 60-second response.

### 3.5 KIS Vietnam chart backend

Route: `GET https://api.ikis.kisvn.vn/api/v3/chart/history`. All eight KIS M1 and
eight KIS M5 target-window requests returned HTTP 500 with no usable JSON body, no
response MIME/identity, and no typed bars. This proves only a bounded transport/server
failure for those exact requests. Existing repository source notes classify KIS as
`AdjustmentPolicy.MIXED`; that source therefore cannot enter the provider-adjusted
default chain even if a shorter probe later returns data.

| Symbol | M1 | M5 |
|---|---:|---:|
| ACB | HTTP 500; no body | HTTP 500; no body |
| BID | HTTP 500; no body | HTTP 500; no body |
| FPT | HTTP 500; no body | HTTP 500; no body |
| HPG | HTTP 500; no body | HTTP 500; no body |
| VCB | HTTP 500; no body | HTTP 500; no body |
| VIC | HTTP 500; no body | HTTP 500; no body |
| VNM | HTTP 500; no body | HTTP 500; no body |
| VPL | HTTP 500; no body | HTTP 500; no body |

KIS's official [terms of use](https://kisvn.vn/dieu-khoan-su-dung/) prohibit copying,
modifying, transferring, distributing, storing, or creating versions of site
information without prior written consent, and disallow commercial use. No route-
specific chart licence or rate contract was found. Contact details are published on
the same official terms page, including `cskh@kisvn.vn`.

**Disposition:** M1 and M5 independently `TRANSPORT_INCONCLUSIVE + ADJUSTMENT_GAP +
LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP`; the current `MIXED` policy is a hard
default-chain exclusion.

## 4. Cross-cutting semantic and coverage gates

### 4.1 Identity and MIME

Only VPS history echoed the requested provider symbol in the target matrix, and its
same-provider metadata echoed the same symbol. SSI history had a same-provider
metadata control but no history symbol. VNDirect and Pinetree history had no response
symbol and no usable same-provider symbol metadata control. KIS produced no target
response. A request parameter is not response-backed identity.

The route-specific MIME observations were:

| Route | Full observed `Content-Type` | Normalized media type |
|---|---|---|
| SSI | `application/json; charset=utf-8` | `application/json` |
| VNDirect | `text/plain;charset=UTF-8` despite a JSON body | `text/plain` |
| VPS | `application/json; charset=utf-8` | `application/json` |
| Pinetree | `text/plain;charset=UTF-8` despite a JSON body | `text/plain` |
| KIS | no usable target response | `—` |

Future code must use an exact route allow-list and reject status/MIME/envelope drift;
it must not accept arbitrary HTML or classify a JSON body as a licence or identity.

### 4.2 Candle time, session, volume, and adjustment

The matrix proves only common observed timestamp spacing: VNDirect and VPS were
60 seconds for M1 and 300 seconds for M5; Pinetree returned 60 seconds for both;
SSI's target response was empty; KIS failed. The provider meaning of the timestamp
(open time versus close time), no-trade-bar policy (omitted versus zero/flat), and
auction/halt/session treatment remain unresolved. The metadata session `0900-1500`
does not answer those questions, and lunch/holiday gaps must not be filled or called
absence without an official calendar/contract.

VND/VPS returned aligned integer volume arrays and Pinetree returned aligned floating-
point volume arrays in successful cells. No provider evidence here proves that volume
is shares, whether it is incremental or cumulative, or how put-through/block trades
are treated. The legacy missing-volume-to-zero shortcut is not evidence of volume
coverage. All candidates therefore fail the real-volume/unit semantics gate.

The existing source declarations (`PROVIDER_ADJUSTED` for SSI/VNDirect/VPS/Pinetree
and `MIXED` for KIS) are adapter policy, not provider proof that the requested
intraday history is homogeneous over eight years. No candidate proves a single
adjustment basis for both M1 and M5 over the requested horizon; no raw/adjusted splice
or cross-source repair is allowed.

### 4.3 Pagination, internal gaps, and exact coverage

No target response exposed a provider-declared total/page count or a safe continuation
contract that was followed. Pinetree exposed a negative `nextTime` marker, but its
meaning and direction were not documented. The target results show finite recent tails
or an empty response, not complete eight-year retrieval. Observed per-day counts are
session-shaped. The complete bounded ranges are in the ledger: VNDirect M1/M5
`30–228`/`20–48` rows per nonempty day, VPS M1/M5 `112–226`/`40–46`, and Pinetree
M1/M5 `106–226`/`106–226`; private non-reproducible cadence observations are also
recorded per unit, outside the release gate. These observations include session breaks
and calendar gaps; no holiday, suspension, listing, or transfer classification was
fabricated from spacing.

The required `2018-08-13` boundary was absent for every non-empty candidate cell; the
required `2026-08-19` boundary was present for VNDirect, VPS, and Pinetree. For VNDirect,
seven symbols began on 5 November 2021 and VPL began on 29 August 2025. VPS returned
only 17–19 August 2026 for M1 and 10–19 August 2026 for M5. Pinetree returned 18 June
2026 onward for both tokens. These are partial observations, not evidence that older
bars never existed.

No single provider/route/interval unit passes identity, timestamp semantics, volume
semantics, adjustment homogeneity, exact target coverage, legal reuse, and bounded
pagination together. M1 and M5 are therefore both **SOURCE-GAP**, not `QUALIFIED` and
not an implementation-ready `PARTIAL` release.

## 5. Legal and runtime posture

Public/no-login reachability is an access observation, not permission for automation,
large backfill, caching/storage, caller-facing return, commercial use, attribution, or
redistribution. The official sources support a conservative fail-closed posture:

| Provider | Primary terms/runtime evidence | Current disposition |
|---|---|---|
| SSI | [SSI service terms](https://www.ssi.com.vn/dieu-khoan-dich-vu) limit use to personal viewing/analysis and reserve publication/reproduction rights; [FastConnect terms](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments) require approved account/API access and document a one-year intraday scope for that separate product. | `LEGAL_GAP`; written permission/contract required for this anonymous chart route. |
| VNDirect | [VNDIRECT website terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) disclaim website/data warranties; [Datafeed terms](https://datafeed.vndirect.com.vn/term-full) prohibit copying, distribution, publication, or unauthorized use without written consent. | `LEGAL_GAP`; chart-host access is not a Datafeed licence. |
| VPS | [VPS terms](https://vps.com.vn/dieu-khoan-su-dung) prohibit copying, transfer, display, distribution, storage, and derivative versions without official written consent. | `LEGAL_GAP`; no runtime bulk/reuse assumption. |
| Pinetree | Official [provider identity/contact](https://pinetree.vn/post/dich-vu/lien-he/) is available, but no chart-route open-data licence was found; the [Stock123 terms](https://pinetree.vn/wp-content/uploads/2019/11/PINETREE-dieu-khoan-su-dung.pdf) do not grant one. | `LEGAL_GAP`; request route-specific permission. |
| KIS | [KIS terms](https://kisvn.vn/dieu-khoan-su-dung/) reserve copying/distribution/storage and prohibit commercial website-information use without written consent. | `LEGAL_GAP`; plus `MIXED` adjustment exclusion. |

No provider disclosed a route-specific finite automation quota, page contract, cache
right, or caller-facing redistribution grant for this review. SSI's public developer
documentation describes key-based rate limits and HTTP 429 handling, but that does not
transfer to the anonymous iBoard chart host. Any future permission request must cover
automation, pacing, retries, retention, storage, attribution, caller return,
redistribution, and commercial use as separate axes.

## 6. Existing runtime and compatibility boundary

The current public call remains:

```python
prices.history(symbol, interval, start, end, *, max_attempts, http_get, timeout)
```

The existing default provider-adjusted chain is SSI → VNDirect → VPS → Pinetree;
KIS is registered but excluded because its policy is `MIXED`. The current UDF adapters
make one physical request for a range and do not paginate. The failover client accepts
the first structurally valid non-empty result and attaches soft partial-start/end
warnings only after the winner is selected. Therefore a recent tail is not a retention
oracle and failover is not a safe cross-source historian.

The compatibility-safe decision for this batch is **option 3: keep current runtime
behavior and document the source gap**. Do not reorder D1 or other intervals, do not
make every partial result a failover failure, do not add KIS to the adjusted chain, and
do not expose a new bulk helper. M1/M5 remain existing best-effort primitives with no
new deep-history claim.

### 6.1 Annotated `v0.2.0` versus current-master boundary

The annotated `v0.2.0` tag is `2fe50df4f27064140ff9f7a680227a2b337ec74a`. The tag
comparison below is read-only source behavior, not a claim that the tag had the live
23 August 2026 observations. Current code means the implementation at the correction
base (`5f9c4d6`); later local commits in this batch change only docs/backlog.

| Axis for M1/M5 | Annotated `v0.2.0` tag | Current master before this correction |
|---|---|---|
| Public one-shot signature | `prices.history(symbol: str, interval: Interval = Interval.D1, start: Optional[date] = None, end: Optional[date] = None, *, max_attempts: int = 3, http_get=None, timeout: float = 25.0) -> PriceHistory` | same signature and defaults |
| Default source order | SSI → VNDirect → VPS → Pinetree; KIS registered but excluded as `MIXED` | same |
| Logical attempt budget | `max_attempts=3` default; capability skips do not consume calls | same |
| Interval dispatch | one-shot calls `FailoverPriceClient.get_history` directly for the requested interval | `apply_interval` wraps the call; M1/M5 still dispatch unchanged, while only coarser W1/MN1/Q1/Y1 use D1 resampling |
| Adapter request behavior | one physical range request per called adapter; no pagination or `nextTime` follow | same |
| Winner/coverage warnings | first accepted nonempty result wins; partial start/end warnings are appended after winner selection | same for M1/M5, with current validation/finalization retaining other existing diagnostics |
| Declared interval capability | SSI, VNDirect, VPS, Pinetree, and KIS advertise M1/M5; KIS remains outside default adjusted chain | same |
| Live source evidence | no live matrix is attributed to the release tag | 80 direct history cells + 16 metadata controls + 1 aggregate cohort observation, all bounded to 23 August 2026 and not a retention/legal guarantee |

The tag cannot be used to claim current live coverage, and current live observations
cannot be back-projected into the release. The source-gap decision is about the named
direct routes and the current runtime boundary only.

## 7. Exact future design (not implemented)

This section is a conditional design contract only. It does not authorize RED tests,
production code, a new public parameter, a source reorder, or a push.

### 7.1 Single-call API

Keep the existing signature and default behavior byte-for-byte. A future qualified
source may deepen only its own adapter through same-source pagination. M1 and M5 each
need their own provider route/token, page plan, adjustment proof, and coverage result.
There is no `history_bulk`, basket/archive, first-ten, or M1-to-M5 helper in this issue.

### 7.2 Public facade reachability gate

Direct-source qualification is insufficient. A future unit passes the public-path gate
only if `prices.history(..., interval=Interval.M1/M5, max_attempts=n)` reaches that same
unit under the approved chain and returns the same source/provenance contract. The
reachability matrix must execute `n=1,2,3,4`, capability skips, an earlier valid recent
tail, and a later qualified source. A capability skip consumes zero logical attempts;
an invoked source consumes one; no hidden page call changes `max_attempts`.

The qualified unit must either (a) deepen the already reachable winner through
same-source pagination, or (b) have a separately reviewed M1/M5-only ordering or
attempt change that makes the unit reachable while leaving D1 and every other interval
byte-for-byte compatible. A valid earlier recent-tail result cannot silently shadow a
later `FULL_SPAN` or `QUALIFIED_PARTIAL` unit. The future tests must assert exact direct
source versus facade calls/results for every `max_attempts` value, including the
negative case where a qualified source is beyond the allowed attempt budget. The
current facade remains option 3 and adds no such capability now.

### 7.3 Deterministic physical budget

The following is a safety envelope, not a claim that any current provider can meet it;
a provider-specific plan must be derived from a documented/response-backed page size,
cursor/total contract, and written rate permission before activation:

| Ledger | Conditional maximum | Rule |
|---|---:|---|
| Logical source attempts | existing `max_attempts=3` default | one `SourceAttempt` per called adapter; capability skips consume zero |
| Pages per source attempt | 8 | monotone same-source pages only; no date-by-date fan-out |
| Retry per physical page | 1 after the initial call | only transport/408/429/5xx when owner policy permits; both calls are charged |
| Physical calls per source attempt | 16 | atomically reserve before dispatch |
| Request-scoped physical calls per public call | 32 | one shared per-call ceiling across all sources/pages/retries |
| Audit-global physical calls | `audit_global_physical_ceiling` | absolute hard envelope `30 × 2 × 16 = 960`; exact finite plan `A_plan` must be `≤ 960` and include every identity call |
| Concurrency | 1 | deterministic sequential scheduler; no hidden parallelism |

These maxima are fail-closed ceilings, not a completeness promise. A source whose
provider-derived page plan exceeds them is a source/legal gap, not an instruction to
raise the ceiling. M1 may not borrow unused M5 budget, and M5 may not borrow M1
evidence. No request is sent after a reservation failure, fatal identity/schema/MIME
failure, cursor stall, or successful atomic completion.

`FailoverPriceClient.get_history()` owns one private request-scoped coordinator (the
facade ledger). `prices.history()` creates/configures that client and delegates to its
`get_history()`; it does not create a second or nested coordinator. A direct
`PriceSource.get_history()` call made outside the facade gets its own coordinator. The
client passes the same coordinator to every eligible source attempt; it is never
recreated inside an adapter. Its reservation key is
`(request_id, source_role, symbol, interval, logical_attempt, kind, page_ordinal,
retry_ordinal)`, where `kind` is exactly `identity` or `history_page`. A duplicate key
is a deterministic planning error and sends no request.

Every network request, including an identity control, initial page, or retry, reserves
one unit from both the source counter and the shared global counter before dispatch.
Capability skips, input validation, parsing, and local reconciliation consume zero.
The source and global checks plus key insertion are one atomic operation under the
coordinator's private lock, even though the approved scheduler is sequential. A retry
is a new reservation and is charged independently.

There are two exhaustion seams, with one exact public terminal contract. If the
coordinator cannot reserve the first request of an otherwise eligible source, the
outer `FailoverPriceClient.get_history()` boundary raises the future public
`vnfin.exceptions.BudgetGlobalExhausted`, a subclass of `VnfinError`, with exactly
these stable fields: `symbol: str`, `interval: Interval`,
`attempts: tuple[SourceAttempt, ...]`, and
`diagnostic: Literal["budget_global_exhausted"]`. The `attempts` value is exactly
`tuple(prior_sanitized_attempts)`: a fresh zero-call ledger has `()`, while exhaustion
before a later source preserves every earlier sanitized attempt. The uninvoked source
adds no attempt. This is a public exception exported only from `vnfin.exceptions` (not re-exported from
`vnfin` or `vnfin.prices`), listed in `vnfin.exceptions.__all__`, and catchable
specifically or as `VnfinError`; no private sentinel crosses the public boundary, and it
is not a `SourceError` failover trigger. `prices.history()` delegates
to `get_history()` and propagates this exception; it returns only `PriceHistory`, never
a terminal object.

If exhaustion occurs after an adapter has been invoked (for example, before a later
page or identity control), the adapter discards its private buffer and returns one
failed logical source attempt with the canonical budget reason; page/retry reservations
never create their own attempts. This is a future public engine seam, not current
runtime behavior.

The aggregate ceiling for a future frozen-cohort qualification is distinct from the
request-scoped 32-call ceiling and is named `audit_global_physical_ceiling`. It is a
finite absolute envelope of `30 symbols × 2 intervals × 16 calls = 960`. For each
unit `u`, let `I_u` be its unit-local identity requests, `P_u` its exact initial page
count, and `R_u` its exact permitted retry count; `C_u = I_u + P_u + R_u ≤ 16`.
Every physical identity request is assigned to exactly one explicit unit ledger row,
even when a provider reuses an identity result; it is counted once, not added as an
open-ended shared term. The approved finite audit plan is exactly
`A_plan = Σ(u in 30×{M1,M5}) C_u`, with `A_plan ≤ audit_global_physical_ceiling` and
all terms enumerated before dispatch. `A_plan` must also fit written provider/rate
permission. This audit was **not run** because no candidate passed the gate.

### 7.4 Atomic no-false-partial algorithm

1. Validate one canonical security symbol and exact `Interval.M1` or `Interval.M5` before
   network access.
2. Build a finite call plan containing the exact provider symbol, interval token,
   expected route MIME/envelope, identity route (if needed), page direction, source
   and global physical budgets, and retry policy.
3. Reserve each `(source, page, retry)` atomically before dispatch. Pages/retries never
   create synthetic logical attempts.
4. Parse each page into a private buffer. Require response-backed symbol/identity, exact
   interval token, exact route MIME/status/envelope, aligned OHLCV arrays including
   real volume, proven timestamp unit/convention, monotone cursor, no overlap/conflict,
   valid provider totals/pages, and no hidden source switch.
5. Reconcile all pages and the requested coverage before publishing. Any missing page,
   transport error, status/MIME drift, cursor stall, budget exhaustion, unknown candle
   convention, adjustment mismatch, or identity failure discards the buffer atomically.
6. Return only one provider's `PriceHistory`, with bounded sanitized diagnostics. A
   valid recent-only response may retain the existing partial-coverage warning, but it
   must never be relabeled as full span and must never be stitched to another source.

### 7.5 Required interval/bar invariants

For each independently qualified interval, the same unit must prove: exact requested
and response provider symbol; exact M1/M5 token; `currency=value_unit="VND"`; one
homogeneous adjustment basis; timezone-aware `Asia/Ho_Chi_Minh` timestamps converted
once from the provider epoch; strictly ascending unique timestamps; finite positive
OHLC; non-negative integer volume in a proven unit; high/low envelope; exact cadence
and provider candle-time convention; legitimate session/holiday/auction/halts left as
gaps; and fail-loud incomplete start/end diagnostics. No missing volume may become a
historical zero, and no daily/M15/synthetic bar may be relabeled M1 or M5.

### 7.6 Conditional public diagnostics grammar

This is an executable future contract, not a change to today's raw diagnostic
behavior. The only canonical source-role values are exactly
`ssi`, `vndirect`, `vps`, `pinetree`, and `kis`. Future paginated attempts must use
one of those roles, `ok`, or one finite reason token from this total mapping:

| Failure class | Canonical reason token(s) |
|---|---|
| transport/offline | `transport_timeout`, `transport_unavailable` |
| HTTP/redirect/challenge | `http_status_unexpected`, `redirect_or_challenge` |
| MIME/envelope | `mime_unexpected`, `envelope_invalid` |
| schema/identity/interval | `schema_invalid`, `identity_missing`, `identity_mismatch`, `interval_mismatch` |
| timestamp/volume/adjustment | `timestamp_invalid`, `volume_invalid`, `adjustment_unproven` |
| page/cursor/coverage | `pagination_unavailable`, `pagination_cursor_stalled`, `pagination_overlap_conflict`, `pagination_total_mismatch`, `coverage_unreconciled` |
| rate/legal | `rate_policy_unproven`, `legal_reuse_unproven` |
| budget/facade | `budget_source_exhausted`, `budget_global_exhausted`, `facade_unreachable` |
| bounded coverage warnings | `partial_start_coverage`, `partial_end_coverage` |

The future qualified built-in M1/M5 facade grammar uses the frozen public field
`SourceAttempt.name`, matching `^(ssi|vndirect|vps|pinetree|kis)$`; it never refers to
a `.source` field. This finite role allow-list applies only to that future qualified
built-in facade path. The exported `FailoverPriceClient` remains compatible with
arbitrary custom `PriceSource` members and their configured `SourceAttempt.name`
values; it must not reject or rewrite custom names merely because they are outside the
built-in role list. A new qualified `SourceAttempt.reason` is exactly `ok` or one
listed token (ASCII, 1–48 characters), never an exception class, URL, query, provider
text, body excerpt, cursor, or live value. Capability skips are private routing events
and create no `SourceAttempt` or public reason token. A future qualified facade
finalizer sanitizes every returned attempt, including earlier failures, not only the
winner. Existing UDF warning prefixes `quarantined_invalid_bars`,
`recovered_midnight_open_placeholder`, `partial_start_coverage`, and
`partial_end_coverage` are preserved as bounded allow-listed warnings with their
existing meaning; unknown provider warnings are mapped to a safe token or fail closed.
A future warning is one listed token or `TOKEN: count=<1..999999>`; legacy partial
coverage messages may retain their existing ISO-date/count fields but must remain
bounded, ASCII, and URL/provider-text free. The warning tuple is capped at 16 entries,
each entry at 160 characters; the attempt tuple is capped at four entries for a
qualified `max_attempts=1..4` matrix; counts are non-negative integers no wider than
six digits. Any unmapped internal exception, malformed role/token, over-cap diagnostic,
or unsafe text fails closed to `transport_unavailable`/`schema_invalid` as applicable
and is never surfaced raw.

### 7.7 Conditional qualified-release checklist

If a later design ever reaches `FULL_SPAN` or `QUALIFIED_PARTIAL`, the release gate
must pass all of these in one reviewed change; this source-gap commit does none of
them:

1. update the qualified source research, `prices` API/AI usage, architecture/failover,
   source/coverage/retention diagnostics, and the legal/runtime caveat;
2. preserve the public API snapshot and DataFrame/model compatibility, adding any
   typed metadata only through explicit compatibility review;
3. add docs-contract coverage and CHANGELOG/release notes when the public behavior or
   capability changes;
4. write synthetic RED fixtures first, then green tests for direct source, facade,
   pagination, identity/MIME, `FULL_SPAN`/`QUALIFIED_PARTIAL`, budgets, atomicity,
   diagnostics, and D1/other-interval compatibility;
5. run focused source/failover/docs/blacklist/secret tests, the full offline merged-tree
   suite, offline import/public snapshots, `git diff --check`, and an isolated sdist/
   wheel build; and
6. obtain exact-SHA reviewer approval before push or closure. No raw provider rows,
   live values, screenshots, archives, or unlicensed member lists may enter the release.

## 8. Source-gap reopen criteria

Reopen #209 or #210 only when **all** applicable conditions pass for one named provider,
one exact interval, one route/version, and one legal/runtime contract. M1 and M5 may
reopen separately; an M1 pass never carries M5.

There are two mutually exclusive, explicit future qualification outcomes:

Before either outcome is audited, a future release must reacquire a legally publishable,
reproducible frozen cohort, or use a separately approved caller-supplied manifest. The
current SSI-derived membership values are withheld and may not be used as an implicit
future audit input.

- **`FULL_SPAN`:** one unit accounts for every applicable symbol in the frozen audit
  manifest across the complete inclusive `2018-08-13..2026-08-19` window, with any
  documented listing/transfer boundary represented separately. It may not rely on a
  recent-tail warning, a second provider, or a resampled interval.
- **`QUALIFIED_PARTIAL`:** one unit passes every identity, MIME/status, timestamp,
  volume, adjustment, legal, rate, pagination, atomicity, and facade gate, but its
  exact proven horizon does not reach one or both requested edges. The release manifest
  must declare a per-symbol/per-interval `first_local`, `last_local`, row count, and
  boundary flags, plus machine-matchable `partial_start_coverage` and/or
  `partial_end_coverage` diagnostics. “Materially deeper” is not prose: the approved
  design must pin the exact manifest and minimum boundary for that unit, and RED tests
  must compare returned values to it. A partial unit never implies full-span coverage.

Both outcomes require the same independent M1/M5 qualification and the same public
facade reachability. If neither outcome's manifest is complete, the issue remains
`SOURCE-GAP CLOSURE` and the new qualified deep-history chain remains empty.

1. Written owner permission or a clear licence covers the exact route's automation,
   pacing, retries, caching/storage, retention, attribution, caller-facing return,
   redistribution, and commercial use.
2. The response or a same-provider identity route binds the requested symbol, exchange/
   listing identity, exact interval, unit/scale, and source role. Missing response
   identity cannot be filled from the request parameter.
3. The route's exact status, normalized media type, envelope, browser/WAF behavior, redirects,
   and authentication/session requirements are documented and deterministic. Generic
   maintenance HTML, a challenge page, or a JSON body under an unexpected MIME fails.
4. Provider documentation or response-backed evidence proves timestamp unit and candle
   meaning, incremental/cumulative volume and unit, no-trade-bar policy, session
   convention, and a homogeneous historical adjustment basis.
5. The selected outcome's manifest passes: `FULL_SPAN` accounts for the inclusive
   target span for the reacquired/approved frozen-cohort manifest, subject to documented
   listing/transfer boundaries; `QUALIFIED_PARTIAL` pins an approved materially-deeper
   per-symbol/per-interval horizon and exact machine-matchable warnings. Neither
   outcome permits cross-source stitching.
6. Provider totals/pages/cursors and request-window limits support the finite atomic
   scheduler above, with deterministic retry/rate policy and no retry storm.
7. Direct-source and facade results remain deterministic; D1 and all other interval
   source order/results stay compatible; KIS remains excluded unless its adjustment
   basis is independently changed and reviewed.
8. Future RED fixtures cover positive single-page/multi-page/final-page paths plus
   repeated/reversing/out-of-range cursor, overlap/conflict, MIME/status drift, wrong
   symbol/interval, timestamp-unit/convention, volume, adjustment, cap exhaustion,
   atomic discard, no date fan-out, no calls after success, public diagnostic
   sanitization, arbitrary custom-source names outside the qualified built-in path,
   success and all-failure attempt sanitization, all four preserved UDF warning
   prefixes, and both `FULL_SPAN` and `QUALIFIED_PARTIAL` manifests. The budget
   terminal matrix must cover zero-call exhaustion, later-source exhaustion with prior
   attempts preserved, no attempt for the uninvoked source, zero network calls after
   failure, and the exact exception export/public snapshot. All fixtures must be
   synthetic and visibly non-provider data.

## 9. Current decision

M1 and M5 are both **SOURCE-GAP CLOSURE**. The new qualified deep-history chain remains empty for the
requested deep-history capability. This note records evidence and a future reopen
contract only; it does not authorize RED tests, production code, a bulk API, push, or
issue closure.

## Sources

- [SSI iBoard history route](https://iboard-api.ssi.com.vn/statistics/charts/history)
- [SSI iBoard symbol metadata route](https://iboard-api.ssi.com.vn/statistics/charts/symbol)
- [SSI current group snapshot](https://iboard-query.ssi.com.vn/stock/group/VN30)
- [SSI service terms](https://www.ssi.com.vn/dieu-khoan-dich-vu)
- [SSI developer terms and data limits](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)
- [SSI FastConnect API catalogue](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/danh-sach-cac-api)
- [VNDirect history route](https://dchart-api.vndirect.com.vn/dchart/history)
- [VNDirect website terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/)
- [VNDirect Datafeed terms](https://datafeed.vndirect.com.vn/term-full)
- [VPS history route](https://histdatafeed.vps.com.vn/tradingview/history)
- [VPS symbol metadata route](https://histdatafeed.vps.com.vn/tradingview/symbols)
- [VPS website terms](https://vps.com.vn/dieu-khoan-su-dung)
- [Pinetree history route](https://charts.pinetree.vn/tv/history)
- [Pinetree provider/contact page](https://pinetree.vn/post/dich-vu/lien-he/)
- [Pinetree Stock123 terms](https://pinetree.vn/wp-content/uploads/2019/11/PINETREE-dieu-khoan-su-dung.pdf)
- [KIS chart history route](https://api.ikis.kisvn.vn/api/v3/chart/history)
- [KIS terms of use](https://kisvn.vn/dieu-khoan-su-dung/)
- [TradingView UDF protocol](https://www.tradingview.com/charting-library-docs/latest/connecting_data/UDF/)
