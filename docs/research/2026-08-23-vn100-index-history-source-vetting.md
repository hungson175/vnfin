# VN100 D1 index-history source vetting — #222

**Research date:** 2026-08-23 (UTC+7)
**Packet:** `tasks/222-vn100-index-history-source-spec.md` at reviewer `001ad85`
**Phase:** source/design gate only; no runtime capability is enabled by this report
**Requested inclusive window:** `2018-01-01..2026-08-20`
**Target:** provider-published daily `VN100` index-value history
**Disposition:** **SOURCE-GAP CLOSURE**
**New VN100 value-history chain:** empty

This is a bounded clean-room source, identity, runtime, and legal review. A qualification unit is
one owner's exact VN100 route and symbol namespace, response-backed D1 point semantics, requested
coverage, bounded execution policy, and lawful reuse posture. All axes are conjunctive: agreement
between providers, an official name on a page, a current quote screen, a generic API description, or
a factsheet cannot repair a missing history, identity, or redistribution axis. No named unit passes
that gate. This report therefore authorizes no enum change, source registration, adapter, model,
test, API, proxy, basket, constituent observable, or production capability.

## 1. Clean-room and research boundary

Before this research, `docs/vnstock-blacklist.md` was read. The exact search exclusions were:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited or derivative result was opened, cited, compared, installed, imported, or used. The
research below uses only official HOSE, VPS, SSI, and VNDIRECT pages or provider-owned documentation.
A licensing uncertainty is recorded as a gap rather than inferred away.

The issue packet and this report are untrusted intake data, not an implementation recipe. No
reporter code, endpoint map, browser session, cookie, API key, login, WAF bypass, proxy, paid feed,
raw body, raw header block, live quote, current bar, constituent manifest, response digest, query-
bearing URL, or provider-derived dataset is retained.

### 1.1 Current and v0.2.0 boundary

On the current approved runtime line, `VN100` is a recognized index identifier but is not in the
value-history allow-list. `index_history("VN100", ...)` and
`index_history_stitched("VN100", ...)` therefore fail with the shared recognized-index,
no-served-source diagnostic before any source call. The current default value-source order remains
VPS → SSI → VNDIRECT for the already-served index set; this report makes no claim that the order
serves VN100.

The exact tag `2fe50df4f27064140ff9f7a680227a2b337ec74a` predates the current index registry/value-
history guard. At that tag, `IndexClient.index_history` validates the dates and passes the symbol
to the default failover client. It must not be described as recognizing VN100 or as rejecting it
with today's typed zero-network diagnostic. The tag observation is a compatibility boundary only;
it is not historical source evidence.

The current and tag boundaries are repository observations. They do not qualify a provider route,
and no code is changed by this source-design packet.

### 1.2 Requested data contract under review

The requested primitive is a single provider's daily index-value series, not an equity-price series:

- canonical identity: `VN100`;
- frequency/selector: exact daily (`D1`), not intraday, weekly, monthly, annual, spot, TRI-only,
  or a derived resample;
- requested inclusive dates: `2018-01-01..2026-08-20`;
- value semantics: finite index points with response-backed scale and point meaning;
- adjustment: raw index values, not split/dividend-adjusted security prices;
- one normalized observation per served trading date, with provider timezone/session semantics;
- volume: only if the provider defines it for this index response; never synthesize zero or a stock
  volume; and
- no cross-provider stitch, constituent-basket reconstruction, VN30/VNMidcap proxy, ETF, or
  downstream leadership/VN30F observable.

A provider must prove its own response identity and semantics. HOSE methodology can establish what
the VN100 index is, but it cannot make a VPS, SSI, or VNDIRECT response a VN100 response.

## 2. Decision summary

| Candidate unit | Evidence that is established | Decisive gaps | Disposition |
|---|---|---|---|
| HOSE owner identity / official index presentation | Official Ground Rules define VN100 as VN30 plus VNMidcap; official factsheet supplies base-date, calculation, cadence, and ownership notices | No retained no-login machine-readable D1 history route with the requested window, row/page totals, response envelope, revision contract, and redistribution grant | `IDENTITY_EVIDENCE_ONLY` / `LEGAL_GAP` / `COVERAGE_GAP` |
| VPS `vps_index` chart-history candidate | Current repository identifies the provider-owned host/path and D1 selector as a candidate; official SmartOne pages show VN100 as a UI index | No fresh VN100 response identity, route contract, coverage, MIME/envelope, WAF/session posture, rate policy, or OSS redistribution permission; public UI is not a history API | `SOURCE-GAP` |
| SSI `ssi_index` / FastConnect candidate | Official docs describe index lists, historical index summaries, daily OHLC paging, JSON/CSV market data, and API rate headers | FastConnect requires SSI account/API key/secret/approval; generic examples are VNINDEX/SSI, not VN100; no response-backed VN100 D1 identity, full-span coverage, volume/RAW semantics, or redistribution grant | `SOURCE-GAP` |
| VNDIRECT `vndirect_index` chart-history candidate | Official VNDIRECT quote/support pages recognize VN100 and its index-futures underlying; current repository identifies a provider-owned chart host/path candidate | No documented or retained no-login historical D1 response contract, VN100 symbol binding, requested coverage, pagination/revision, rate policy, or redistribution grant | `SOURCE-GAP` |

No candidate has a single route pair that passes owner, response identity, D1 point/volume/time
semantics, full requested coverage, bounded runtime, and legal reuse together. The new source chain
stays empty.

## 3. Bounded method and dispatch ledger

Research consisted of official-domain search and documentation/page reads. The candidate data routes
were not called. In particular, no direct provider/API probe was made before design review PASS.
There was no login, API key, session, cookie, challenge solving, or retry. Browser-like rendering,
if used by an official page, is not evidence of an API response and is not a future runtime policy.

The ledger below is intentionally split into **research traffic** and **qualifying data dispatches**:

- `1` logical candidate unit means one provider/route/identity hypothesis was assessed.
- `0` qualifying physical dispatches means no provider data/API route was called in this review.
- `0` retries and `0` pages/cursors are exact for the qualifying data ledger, not a claim that the
  provider has no pages or data.
- Documentation/page traffic from the web research tool did not retain a deterministic per-request
  transport ledger, so its logical/physical/retry/page/status/MIME/redirect dimensions are
  `NOT_RETAINED` and are excluded from the data ledger.
- `NOT_PROBED` means that the candidate dimension was deliberately not called. `NOT_RETAINED`
  means a research page was read without retaining a transport record. Neither means empty,
  absent, or historically unavailable.

| Unit | Logical candidate units | Qualifying data logical / physical | Pages / cursors | Retries | Status / complete MIME / normalized MIME / redirect | Auth, session, UA, WAF | Retained response identity |
|---|---:|---:|---:|---:|---|---|---|
| HOSE owner history route | 1 | 0 / 0 | 0 | 0 | `NOT_PROBED` / `NOT_PROBED` / `NOT_PROBED` / `NOT_PROBED` | `NOT_PROBED` | no data response retained |
| VPS `vps_index` route | 1 | 0 / 0 | 0 | 0 | `NOT_PROBED` / `NOT_PROBED` / `NOT_PROBED` / `NOT_PROBED` | `NOT_PROBED` | no data response retained |
| SSI `ssi_index` route | 1 | 0 / 0 | 0 | 0 | `NOT_PROBED` / `NOT_PROBED` / `NOT_PROBED` / `NOT_PROBED` | documented key/secret gate; response posture `NOT_PROBED` | no data response retained |
| VNDIRECT `vndirect_index` route | 1 | 0 / 0 | 0 | 0 | `NOT_PROBED` / `NOT_PROBED` / `NOT_PROBED` / `NOT_PROBED` | `NOT_PROBED` | no data response retained |

No `SourceAttempt` or runtime diagnostic is fabricated from this table. If a future permitted
research pass calls a route, it must retain a sanitized complete Content-Type value before deriving
the normalized media type, the effective host after redirect, response envelope, bounded bytes,
logical/physical/page/retry counts, and the exact identity fields. A missing field remains
`NOT_RETAINED`; it is never silently converted to zero or success.

## 4. Official HOSE identity and same-owner evidence

### 4.1 Identity and index semantics

The official [HOSE-Index Ground Rules v4.0](https://staticfile.hsx.vn/Uploads/LocalFiles/ef15%66f11e7994%38abd11677%61d0443887/20250114_20241230_QD%20747%20HOSE%20Index%20Ground%20Rules.pdf), issued under Decision 747/QĐ-SGDHCM on 30 December 2024, defines the HOSE index series as price and total-return indices and defines VN100 as the constituents of VN30 and VNMidcap. This is strong owner/methodology evidence.

The official [VN100 factsheet](https://staticfile.hsx.vn/Uploads/UploadDocuments/2396611/Form_Factsheet_MCIndices_VN_T08.2025.pdf) records a VN100 base date of 24 January 2014, base value `560.19`, price and total-return forms, real-time VN100 calculation and end-of-day VN100TRI cadence, free-float market-cap methodology, a 10% cap, and a VND field. Those facts establish the index family and a static base-date reference. They do not establish an anonymous daily history response, an observation timezone, a provider page total, a revision/as-of contract, or a redistribution licence.

The newer [HOSE-Index factsheet](https://staticfile.hsx.vn/Uploads/UploadDocuments/2438018/Form_Factsheet_MCIndices_VN_T02.2026.pdf), updated 30 January 2026, repeats the VN100 identity and says the HOSE-Index family is calculated in real time or at end of day. Its growth chart and descriptive tables are not a dated machine-readable history for the requested window. No live values or constituent rows from the factsheets are retained here.

HOSE's official data presentation includes an index/total-return area, but this review did not call a
machine route or retain a response. Therefore the owner route has no proved D1 selector, response
envelope, MIME, page/cursor, total, first/last date, or historical coverage. A factsheet chart is
not a no-login API contract.

### 4.2 Rights and contact posture

The factsheet names `VN100` and the other HOSE-Index names as registered brands owned exclusively by
HOSE, says approval is required to use the family for index-related products, and provides
`index@hsx.vn` as the contact. The same publication contains a liability disclaimer for information
or data use. None of that is an open-data or OSS redistribution grant. The legal axis is therefore
`LEGAL_GAP`, with written permission or a clear licence required before storage, redistribution,
commercial use, or derivative/public API use.

### 4.3 HOSE disposition

HOSE is the authoritative identity owner, not a qualified runtime source in this review:

```text
IDENTITY_PASS (concept/methodology)
+ RESPONSE_IDENTITY_GAP
+ D1_HISTORY_ROUTE_GAP
+ COVERAGE_GAP
+ REVISION_GAP
+ RUNTIME/RATE_POLICY_GAP
+ LEGAL_GAP
= no qualified HOSE unit
```

A future HOSE owner response with exact VN100 identity, daily point rows, complete requested bounds,
page/revision semantics, and written reuse rights could reopen the source gap. Until then, no HOSE
route is registered.

## 5. VPS candidate: public UI is not a qualified history source

### 5.1 Candidate route and identity

The existing index adapter names a provider-owned chart-history candidate:

- owner: VPS Securities;
- runtime candidate name: `vps_index`;
- canonical host/path: `https://histdatafeed.vps.com.vn/tradingview/history`;
- non-secret D1 selectors to be evaluated only in a future permitted probe: provider symbol,
  daily resolution, and bounded from/to dates;
- candidate response family: a provider-owned UDF-style chart route as described by current local
  code, not freshly proven VN100 evidence.

The official [VPS SmartOne](https://smartoneweb.vps.com.vn/) search/page family displays VN100 among
market indices. The official [SmartOne web guide](https://smartone.vps.com.vn/en-US/Home/BriefUserGuide)
describes chart/price-history features for the platform, but it does not document a public VN100
history schema, exact symbol token, D1 response envelope, date bounds, or redistribution terms.
A UI label is not response-backed identity.

### 5.2 Axis result

| Axis | VPS result |
|---|---|
| Owner/route | Provider-owned candidate host/path above; exact VN100 route binding `NOT_ESTABLISHED` |
| Exact D1 token / non-D1 rejection | `NOT_PROBED`; no selector claim is frozen |
| Effective host/redirect/status/MIME/envelope | `NOT_PROBED`; no response retained |
| Auth/session/WAF/UA | `NOT_PROBED`; public page visibility is not an anonymous API permission |
| Response symbol / exchange / index type | `NOT_ESTABLISHED`; SmartOne VN100 text is not a response row |
| Point scale / price-vs-value / timezone/session | `NOT_ESTABLISHED` |
| Requested coverage and provider total | `NOT_ESTABLISHED`; no first/last/boundary/gap/duplicate evidence |
| OHLC/point/volume/RAW semantics | `NOT_ESTABLISHED`; no volume zero or null may be fabricated |
| Page/cursor/retry/rate/byte policy | `NOT_ESTABLISHED`; no numeric budget is frozen |
| Storage/cache/attribution/redistribution | `LEGAL_GAP`; no public OSS/data licence was found |
| Outcome | `SOURCE-GAP`, not confirmed non-service |

The official VPS [account terms](https://motaikhoan-doitac.vps.com.vn/Content/htmlTemp/BoTCHDMTK.htm)
describe access to electronic trading systems as a non-exclusive, non-transferable permission that
may be withdrawn. That is not a market-data redistribution permission. A future source review must
obtain a route-specific data and reuse position from VPS; a SmartOne account permission cannot be
silently generalized to an OSS library.

### 5.3 VPS disposition

`IDENTITY_GAP + COVERAGE_GAP + SEMANTICS_GAP + TRANSPORT_INCONCLUSIVE + RATE_POLICY_GAP + LEGAL_GAP`.
The candidate is not added to the VN100 chain and no no-login absence is claimed.

## 6. SSI candidate: documented API is authenticated and generic

### 6.1 Official documentation evidence

The [SSI FastConnect overview](https://developers.ssi.com.vn/docs/getting-started/overview) documents
REST/WebSocket market data, JSON/CSV formats, index channels, and API-key/secret bearer-JWT
authentication. The [official usage and environment page](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)
requires an SSI trading account, FastConnect registration, and approval; it documents API-key rate
headers and says historical data may be queried outside trading hours. The [auth-token reference](https://developers.ssi.com.vn/docs/api-reference/auth-token)
requires `apiKey` and `apiSecret`; OTP is optional for data queries but the key/secret gate remains.

The official [Python service documentation](https://developers.ssi.com.vn/docs/sdk/python/service-classes)
shows `get_indexes`, `get_index_summary`, `get_index_summary_historical`, and historical OHLC
methods with date and page/size parameters. Its examples use `VNINDEX` for index summary and `SSI`
for OHLC. The [model documentation](https://developers.ssi.com.vn/docs/sdk/go/utilities) describes
fields such as symbol, trading date, OHLC, volume, value, and market-index identity fields. These
are generic API schema/documentation leads, not a response-backed VN100 route.

### 6.2 Existing chart candidate versus FastConnect documentation

The current repository's `ssi_index` candidate is the provider-owned chart path
`https://iboard-api.ssi.com.vn/statistics/charts/history`, with a D1 selector and symbol/date
parameters. FastConnect's documented REST host is `https://api.ssi.com.vn`; the documentation does
not prove that the chart candidate and FastConnect are one owner/version/permission unit. They must
not be merged into a synthetic qualification unit. No direct chart or FastConnect data request was
made for VN100 in this review.

### 6.3 Axis result

| Axis | SSI result |
|---|---|
| Owner/route | SSI-owned documentation and two separately named candidate route families; binding to one VN100 unit `NOT_ESTABLISHED` |
| No-login posture | **Fails the requested no-auth posture in documented FastConnect:** account, registration, approval, API key and secret are required; chart candidate anonymous status `NOT_PROBED` |
| Exact D1 selector / provider symbol | Generic daily OHLC method exists; `VN100` response symbol and exact selector `NOT_ESTABLISHED` |
| Status/MIME/redirect/envelope | `NOT_PROBED`; no response retained |
| Exchange/index type/point scale/timezone/session | `NOT_ESTABLISHED`; generic model fields do not prove VN100 semantics |
| `2018-01-01..2026-08-20` coverage | `NOT_ESTABLISHED`; no provider-declared bounds, totals, pages, gaps, or revisions for VN100 |
| Volume/RAW/adjustment | Generic OHLC model mentions volume; VN100 volume meaning, nullability, unit, and raw policy `NOT_ESTABLISHED` |
| Rate/retry/byte policy | Rate-limit headers are documented; numeric limits and route-specific retry/reuse permission are not frozen |
| Storage/redistribution | `LEGAL_GAP`; reviewed documentation/terms do not grant OSS redistribution of the exact series |
| Outcome | `SOURCE-GAP`, not historical absence |

An authenticated API can be a future licensed source only after the owner authorizes the intended
client and redistribution posture. It does not satisfy this packet's no-login qualification today.
No API key, account, token, or login flow is introduced.

## 7. VNDIRECT candidate: official recognition without history qualification

### 7.1 Official recognition and candidate route

The existing `vndirect_index` adapter identifies the provider-owned chart-history candidate
`https://dchart-api.vndirect.com.vn/dchart/history`, with a symbol, daily resolution, and bounded
from/to selectors. No VN100 request was made and no response envelope is assumed in this report.

VNDIRECT's official [VN100 futures support page](https://support.vndirect.com.vn/hc/vi/articles/51381990427417-Th%C3%B4ng-tin-h%E1%BB%A3p-%C4%91%E1%BB%93ng-t%C6%B0%C6%B0ng-lai-ch%E1%BB%89-s%E1%BB%91-VN100)
recognizes VN100 as the underlying index for a futures product. The official [VN100 quote page](https://banggia.vndirect.com.vn/chung-khoan/vn100)
shows a provider-owned quote UI for the name. Neither page is an historical D1 route, a response
schema, or a reuse licence.

### 7.2 Axis result

| Axis | VNDIRECT result |
|---|---|
| Owner/route | Provider-owned chart candidate plus official quote/support pages; exact same-unit VN100 history binding `NOT_ESTABLISHED` |
| No-login posture | Quote/support page visibility is not an API permission; chart route `NOT_PROBED` |
| Exact D1 selector/provider symbol | `NOT_ESTABLISHED`; no response-backed symbol or D1 token |
| Status/MIME/redirect/envelope | `NOT_PROBED`; no response retained |
| Exchange/index type/point scale/timezone/session | Futures/quote recognition only; historical point semantics `NOT_ESTABLISHED` |
| Requested coverage, totals, pages, revisions | `NOT_ESTABLISHED`; no first/last/boundary/gap/duplicate evidence |
| OHLC/volume/RAW semantics | `NOT_ESTABLISHED`; no synthetic volume or adjustment claim |
| Rate/retry/byte/WAF policy | `NOT_ESTABLISHED` |
| Storage/redistribution | `LEGAL_GAP`; VNDIRECT [application terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) contain website/service disclaimers but no exact-series OSS redistribution grant |
| Outcome | `SOURCE-GAP`, not confirmed non-service |

The VNDIRECT page proves a product/index naming relationship, not that the chart route returns
VN100 D1 history or that a clean-room library may store and redistribute it. The candidate remains
unregistered.

## 8. Coverage, identity, and semantic gates

### 8.1 Full-span coverage is not inferred

The requested window is inclusive `2018-01-01..2026-08-20`. A future full result must use the
provider's own trading calendar/declared bounds and retain:

1. provider-declared first and last supported dates;
2. observed first and last local observation dates;
3. provider totals and distinct normalized dates;
4. exact page/cursor/window reconciliation;
5. presence or an explicitly provider-declared non-trading explanation for each requested boundary;
6. duplicate and conflicting-date handling;
7. internal missing-date diagnostics that distinguish exchange holidays from unexplained holes; and
8. revision/as-of semantics, including whether later responses replace a prior observation.

A factsheet growth chart, a current quote, a recent-only UI, a timeout, WAF/403, empty body, capped
page, or a provider label cannot prove historical absence or full coverage. If a future source only
supports a declared subrange, its result is `QUALIFIED_PARTIAL` only after the boundaries and pages
reconcile; it must not be advertised as the requested full span.

### 8.2 Identity and source wins

A qualified response must bind all of the following in one owner/version/route unit:

- requested canonical symbol `VN100` and provider symbol, with a documented reversible mapping;
- response-backed index name/type and exchange/owner identity;
- D1 interval token, local observation date, timezone/session/close meaning;
- price/value versus TRI distinction;
- point scale, finite numeric type, and explicit raw adjustment policy;
- volume presence, unit, nullability, and meaning, or an explicit provider declaration that the
  field is unsupported (never a synthesized zero); and
- route, MIME, envelope/status, redirect, pagination, retry/rate, attribution, storage, and
  redistribution terms.

HOSE identity cannot repair a provider response that lacks a VN100 field. VN30 + VNMidcap cannot
repair a missing VN100 response. No constituent list or local calculation is an acceptable source.

### 8.3 Diagnostic accounting

The future diagnostics grammar must be finite and sanitized. It may expose only bounded provider
names, canonical source roles, fixed outcome tokens, finite counts, and dates after validation. It
must not expose raw URLs or query strings, cookies, headers, response bodies, arbitrary provider
messages, live values, or unbounded names. A `SourceAttempt` is created only for an actual logical
source dispatch; a skipped or uncalled candidate is not described as failed.

Research-only statuses used in this report (`NOT_PROBED`, `NOT_RETAINED`, `NOT_ESTABLISHED`) are not
public runtime errors. They prevent an evidence gap from being mistaken for a provider absence.

## 9. Legal, rate, and redistribution gate

The legal/runtime axes are independent:

| Axis | Required proof before source qualification | Current result |
|---|---|---|
| Owner and identity | Owner confirmation plus response-backed VN100 binding | HOSE concept passes; provider rows absent |
| Anonymous access | Route-specific no-login permission or explicit credential contract accepted by project policy | SSI FastConnect is credential-gated; VPS/VNDIRECT route posture `NOT_PROBED` |
| Automation/rate | Published or written rate, retry, byte, page, and WAF policy | Not established for any candidate |
| Retrieval/storage | Permission to fetch and store/cache the exact rows | Not established |
| Attribution | Required source/brand notice and stable attribution wording | HOSE contact/brand restriction observed; grant absent |
| Public redistribution | Explicit licence or written permission for OSS callers and derived response objects | No candidate passes |
| Commercial/derivative use | Explicit permission for library use and downstream derived indicators | No candidate passes |

The word “public” means visible without a login in a web page; it does not grant automated access or
redistribution. The term “API” means documented transport; it does not prove an anonymous route or
license. These distinctions are hard gates, not caveats to be waived by provider agreement.

## 10. Future design only if a unit reopens

No public token, numeric budget, source registration, or runtime outcome is added now. If a fresh
primary-source packet later proves one unit, the implementation review must define the following
before RED:

### 10.1 Atomic request and budget contract

- Validate canonical `VN100`, exact D1, date range, and source capability before any network call.
- Use one request-scoped ledger across every source attempt, page/cursor, redirect, and retry; do
  not reset at source or calendar-year boundaries.
- Reserve an attempt before entering a source and reserve one physical dispatch immediately before
  each initial/page/retry/redirect request. A capability skip consumes neither.
- Count response/decompression bytes separately from dispatches; byte exhaustion cannot fabricate a
  successful empty series or a `SourceAttempt` for an uncalled source.
- The numeric ceilings must be derived from the qualified route's public/written policy. Until then
  no default number, retry count, page count, or timeout is frozen in a public API.
- On exhaustion, discard private partial rows and return one bounded terminal outcome; never return
  a partial accumulator as a full series and never turn a timeout/WAF/empty response into absence.

### 10.2 Whole-window and partial behavior

A strict result uses one qualified provider for the whole request. No cross-provider stitch,
constituent basket, local recomputation, ETF, or silent strict-to-stitched fallback is allowed. An
explicit future partial contract may return only provider-declared, page-reconciled bounds with an
unambiguous `PARTIAL` outcome; an unexplained interior gap, identity mismatch, conflicting duplicate,
unreconciled page, or truncated transport is terminal failure/unknown.

The current opt-in stitched API remains unchanged and the current VN100 guard remains deny-only.
A future VN100 implementation must separately prove whether a qualified source may participate in
that existing opt-in path; it cannot silently add a provider or a new helper.

### 10.3 Future bounded outcomes

The following are design vocabulary only, not current public enums:

```text
FULL | PARTIAL | NOT_SERVED | TRANSPORT_FAILURE | SCHEMA_DRIFT
IDENTITY_GAP | COVERAGE_GAP | TIMESTAMP_GAP | VOLUME_GAP
PAGINATION_GAP | RATE_POLICY_GAP | LEGAL_GAP | BUDGET_EXHAUSTED
```

`FULL` requires all provider-declared identity, semantics, and requested-span/page gates. A
`NOT_SERVED`, empty, failed, capped, recent-only, or WAF outcome proves only that bounded attempt's
outcome; it never proves the provider has no historical data. The exception-versus-sentinel public
carrier remains a separate API review decision.

## 11. Reopen evidence and future RED matrix

A source-gap reopen requires one fresh, primary-source evidence packet with all of these axes in one
candidate unit:

1. owner, exact route/version, non-secret D1 selector, effective host, complete and normalized MIME,
   envelope/status, redirect, auth/session/WAF posture;
2. response-backed `VN100` symbol, exchange/index type, price-vs-TRI identity, point scale,
   timezone/session, finite point and volume semantics, RAW policy;
3. inclusive requested coverage, provider bounds/totals, observed first/last dates, boundary/gap/
   duplicate/conflict and page/cursor reconciliation, revision/as-of behavior;
4. bounded logical/physical/page/retry/byte accounting with a published/written rate and
   automation policy;
5. attribution, storage/cache, commercial, derivative, and redistribution rights; and
6. exact public diagnostics and atomic failure behavior, with no false-absence path.

Only after those gates pass may a fresh review authorize synthetic RED fixtures. The RED matrix must
cover, at minimum:

| Dimension | Required future RED cases |
|---|---|
| Selector | exact/lowercase/padded `VN100` positives; proxy, constituent, unknown, punctuation, wrong index, and non-D1 zero-network negatives |
| Identity | provider symbol/owner/type/exchange positive; missing/wrong/ambiguous symbol, price-vs-TRI, wrong owner, wrong scale, and provenance mismatch negatives |
| Transport | exact MIME parsing after the first colon, normalized media type, expected envelope/status, redirect/effective-host, wrong status/MIME/HTML/login/WAF/JSON shape negatives |
| Values | finite point values, negative/zero where provider permits, OHLC consistency, timestamp/date/session, volume present/absent/null/unit; no synthesized volume or adjustment |
| Coverage | requested boundaries, provider bounds, total/page/cursor reconciliation, trading-calendar holidays, interior gaps, duplicate/conflict, revision and no-false-absence negatives |
| Atomicity | one-source whole-window behavior, source capability skip, retry/page/redirect/byte/global-budget exhaustion, no returned partial accumulator after terminal failure |
| Provenance | bounded canonical source identity, provider symbol, retrieval stamp, fixed warnings, finite attempts, no raw URL/query/header/body/value leakage |
| Compatibility | all currently served indices, all deny-only indices including VN100, price-path rejection, current strict/stitched guards, public snapshots/docs/imports |
| Release | docs/skill/CHANGELOG/API snapshot if public behavior changes; focused/full offline tests, build, blacklist/secret/diff/path/object/clean-tree gates |

This matrix is a release design, not permission to create tests or code in #222.

## 12. Final disposition

No single direct VPS, SSI, VNDIRECT, or same-owner HOSE unit proves the requested VN100 D1 history,
identity, semantics, bounded runtime, and lawful OSS reuse together. Cross-provider agreement,
provider UI recognition, generic SSI API documentation, an official factsheet, or a futures/quote
page cannot close the missing axes. The correct result is:

```text
Disposition: SOURCE-GAP CLOSURE
New VN100 history chain: empty
Current runtime: unchanged, recognized-but-not-served and zero-network
No proxy/basket/constituent/downstream observable
No probe, RED, code, source registration, push, or close authorized
```

A source-gap design PASS authorizes only this source/design/backlog publication, exact-anchor remote
verification, a clean no-capability resolution, and issue close/re-read. It does not authorize TDD
or runtime capability.

## 13. Primary references

- [HOSE-Index Ground Rules v4.0](https://staticfile.hsx.vn/Uploads/LocalFiles/ef15%66f11e7994%38abd11677%61d0443887/20250114_20241230_QD%20747%20HOSE%20Index%20Ground%20Rules.pdf)
- [HOSE VN100 factsheet, updated 31 July 2025](https://staticfile.hsx.vn/Uploads/UploadDocuments/2396611/Form_Factsheet_MCIndices_VN_T08.2025.pdf)
- [HOSE-Index factsheet, updated 30 January 2026](https://staticfile.hsx.vn/Uploads/UploadDocuments/2438018/Form_Factsheet_MCIndices_VN_T02.2026.pdf)
- [HOSE official index-data presentation](https://www1.hsx.vn/vi/du-lieu-giao-dich/quy-mo-giao-dich/theo-bo-chi-so-tri)
- [VPS SmartOne](https://smartoneweb.vps.com.vn/)
- [VPS SmartOne web guide](https://smartone.vps.com.vn/en-US/Home/BriefUserGuide)
- [VPS account terms](https://motaikhoan-doitac.vps.com.vn/Content/htmlTemp/BoTCHDMTK.htm)
- [SSI FastConnect overview](https://developers.ssi.com.vn/docs/getting-started/overview)
- [SSI usage and environments](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)
- [SSI authentication token](https://developers.ssi.com.vn/docs/api-reference/auth-token)
- [SSI Python API services](https://developers.ssi.com.vn/docs/sdk/python/service-classes)
- [SSI market-data models](https://developers.ssi.com.vn/docs/sdk/go/utilities)
- [VNDIRECT VN100 futures information](https://support.vndirect.com.vn/hc/vi/articles/51381990427417-Th%C3%B4ng-tin-h%E1%BB%A3p-%C4%91%E1%BB%93ng-t%C6%B0%C6%B0ng-lai-ch%E1%BB%89-s%E1%BB%91-VN100)
- [VNDIRECT VN100 quote page](https://banggia.vndirect.com.vn/chung-khoan/vn100)
- [VNDIRECT application terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/)

## Bottom summary

- #222 disposition: **SOURCE-GAP CLOSURE**; the new VN100 chain remains empty.
- HOSE proves VN100 identity/methodology, but not a licensed no-login D1 history route.
- VPS and VNDIRECT expose only candidate/UI recognition; SSI's documented API is account/key gated.
- No provider proves response identity, full 2018-01-01..2026-08-20 coverage, semantics, budgets, and reuse rights together.
- Current VN100 remains recognized-but-not-served and zero-network; v0.2.0 is kept as a separate boundary.
- No probe, proxy, basket, RED, code, source registration, push, or close is authorized.
- #223, #224, and #225 remain queued behind #222.
- Next handoff: commit the companion design/backlog and request exact-SHA design review.
