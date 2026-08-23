# #217 daily CNY/VND history — source vetting

**Date:** 2026-08-23 (UTC+7)
**Packet:** `tasks/217-daily-cnyvnd-fx-history-spec.md` (reviewer packet `4159d74`)
**Reviewed block:** exact `262c6b8508f6b87cdaae48f761960b5d4da392c4`; report
`reviews/review-202608231719-issue217-final-design-rereview.md` at reviewer `5a45543`
**Requested window:** inclusive `2018-01-01..2026-08-19`
**Decision:** **SOURCE-GAP CLOSURE** — no daily CNY/VND capability, RED tests, production
code, source registration, or source-backed daily API claim is authorized by this report.

The requested economic series is exact `CNY` base / `VND` quote: **VND per 1 CNY**. A
USD/VND value, a CNY/USD value, a current quote, a bank quote with a different basis, a
midpoint, or a cross-derived value is not a substitute. Existing annual World Bank USD/VND
behavior remains unchanged.

## 1. Disposition and hard boundary

No investigated unit passes all of the following as one tuple:

```text
owner + exact route/version + direct CNY/VND identity + one provider field/basis
+ VND per 1 CNY scale + requested coverage + date/revision semantics
+ bounded no-auth runtime + lawful automated access/caller return/storage posture
```

Therefore:

- the future daily CNY/VND source chain remains empty (`()`), not merely unconfigured;
- `vnfin.fx.history(..., frequency=Frequency.DAILY)` remains unserved and unchanged;
- no provider is promoted by numerical agreement, cross-rate arithmetic, a facade, a
  current quote, a search result, or an empty response;
- no raw response, live rate, cookie, header, query-bearing URL, or live fixture is
  retained in this repository; and
- a later implementation requires a fresh design/implementation authorization. This
  report is not a production capability.

## 2. Clean-room and research protocol

Before this correction I read `docs/vnstock-blacklist.md`. Every search used this exclusion:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited source, derivative artifact, endpoint map, schema, code, test, notebook,
package, or behavior was opened, cited, compared, or used. Evidence below is limited to
owner-operated official portals/APIs, official provider terms, current Frankfurter-owned
v2 documentation, and the repository's already-reviewed annual FX source notes. Public
reachability is recorded separately from permission to automate, cache, return, or
redistribute data.

The initial direct-probe session used a fresh process, no credentials, no cookie jar, no
browser session, no proxy, IPv4, a 5-second connect timeout, a 15-second total timeout, no
automatic retry, and a benign desktop-class User-Agent. Its retained session-start marker is
`initial_session_start=2026-08-23T16:17:20+07:00`; its end marker is
`initial_session_end=NOT_RETAINED`, and its exact User-Agent is
`initial_user_agent=NOT_RETAINED`. One bounded manual repeat was
made for the Vietcombank 2018 date route after a DNS timeout; it is recorded as retry `1`,
not a hidden library retry. The correction session repeated the same bounded policy and added
current Frankfurter v2 and BIS v2 probes with redirect following disabled. The exact benign
correction-session User-Agent value was `correction_user_agent=vnfin-oss source-design probe`
(a descriptive, non-browser probe identifier). The Frankfurter correction-session timestamp
marker was `correction_session_start=2026-08-23T16:46:44.967256+07:00` (the corresponding UTC
probe start); `correction_session_end=NOT_RETAINED` and
`bis_correction_session_marker=NOT_RETAINED`. No body, credential, or cookie was retained.
Only status, complete MIME, effective host/path, envelope shape, counts, dates, and legal
statements were retained. Query-bearing date/format parameters were used only during probes and
are not written below or committed; canonical route references are path-only.

## 3. Exact bounded probe accounting

A **logical target** is one unique route plus date/key intent. A provider field observed in
the same response does not multiply calls. A **physical call** is one actual HTTP dispatch.
A **retry** reuses an existing logical target after its first physical dispatch. `complete
MIME` means the complete `Content-Type` value after the first colon, including parameters;
`effective route` is the final host/path with redirect following disabled. `NONE_BEFORE_RESPONSE`
means a timeout occurred before a response. `NOT_RETAINED` is used only for two earlier BIS
exploratory probes and is never used as qualification evidence.

### 3.1 Direct dispatch ledger

The following table is the complete **evidence-complete for retained response fields** dispatch accounting for
the source/design packet. Two earlier exploratory BIS requests were real direct research
traffic but did not retain full MIME/effective-route evidence. They remain visible as retired
`NOT_RETAINED` rows below and are excluded from this retained-field evidence subset; the exact v2 correction
rows supersede them for evidence. They are not used to make an absence or qualification claim.

| Dispatch group | Canonical route/path | Logical targets | Physical calls | Retry reservations | Status / complete MIME / effective route |
| --- | --- | ---: | ---: | ---: | --- |
| VCB dated: 2018 initial + repeat, 2020, 2026-08-19 | `www.vietcombank.com.vn/api/exchangerates` | 3 | 4 | 1 | 2 × HTTP 200 / `application/json; charset=utf-8` / canonical path; 2 × timeout / `NONE_BEFORE_RESPONSE` / `NONE_BEFORE_RESPONSE` |
| VCB XML current quote | `portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx` | 1 | 1 | 0 | HTTP 200 / `text/xml; charset=utf-8` / canonical path |
| SBV SGD, cross-rate, central-rate routes | `dttktt.sbv.gov.vn/TyGia/faces/` route family | 3 | 3 | 0 | 3 × timeout / `NONE_BEFORE_RESPONSE` / `NONE_BEFORE_RESPONSE` |
| World Bank WDI annual probe | `api.worldbank.org/v2/country/VNM/indicator/PA.NUS.FCRF` | 1 | 1 | 0 | HTTP 200 / `application/json;charset=utf-8` / canonical path |
| Federal Reserve H.10 page dispatch | `www.federalreserve.gov/releases/h10/current/` | 1 | 1 | 0 | HTTP 200 / `text/html` / canonical path; HTML is not a data response |
| BIS v2 daily average key | `stats.bis.org/api/v2/data/dataflow/BIS/WS_XRU/1.0/D.VN.VND.A` | 1 | 1 | 0 | HTTP 404 / `application/xml;charset=UTF-8` / canonical path |
| BIS v2 monthly average key | `stats.bis.org/api/v2/data/dataflow/BIS/WS_XRU/1.0/M.VN.VND.A` | 1 | 1 | 0 | HTTP 200 / `text/csv;charset=UTF-8` / canonical path; monthly VND/USD, not direct CNY/VND |
| BIS v2 daily end-period key | `stats.bis.org/api/v2/data/dataflow/BIS/WS_XRU/1.0/D.VN.VND.E` | 1 | 1 | 0 | HTTP 404 / `application/xml;charset=UTF-8` / canonical path |
| BIS v2 monthly end-period key | `stats.bis.org/api/v2/data/dataflow/BIS/WS_XRU/1.0/M.VN.VND.E` | 1 | 1 | 0 | HTTP 200 / `text/csv;charset=UTF-8` / canonical path; monthly VND/USD, not direct CNY/VND |
| Frankfurter v2 direct pair | `api.frankfurter.dev/v2/rate/CNY/VND` | 1 | 1 | 0 | HTTP 200 / `application/json; charset=utf-8` / canonical path; response keys `base,date,quote,rate`, no provider/basis field |
| Frankfurter v2 CNY metadata | `api.frankfurter.dev/v2/currency/CNY` | 1 | 1 | 0 | HTTP 200 / `application/json; charset=utf-8` / canonical path |
| Frankfurter v2 VND metadata | `api.frankfurter.dev/v2/currency/VND` | 1 | 1 | 0 | HTTP 200 / `application/json; charset=utf-8` / canonical path |
| Frankfurter v2 provider catalogue | `api.frankfurter.dev/v2/providers` | 1 | 1 | 0 | HTTP 200 / `application/json; charset=utf-8` / canonical path |
| **Evidence-complete-for-retained-fields dispatches** | — | **17** | **18** | **1** | **11 × HTTP 200, 2 × HTTP 404, 5 × timeout; 13 complete MIME values retained** |

The two earlier BIS dispatches are counted in total research traffic even though their exact
target/path and response headers were not retained:

| Retired direct dispatch | Sanitized target record | Logical targets | Physical calls | Retry reservations | Status / complete MIME / effective route |
| --- | --- | ---: | ---: | ---: | --- |
| Earlier BIS exploratory A | `BIS v2 exploratory target; exact path not retained` | 1 | 1 | 0 | `NOT_RETAINED` / `NOT_RETAINED` / `NOT_RETAINED` |
| Earlier BIS exploratory B | `BIS v2 exploratory target; exact path not retained` | 1 | 1 | 0 | `NOT_RETAINED` / `NOT_RETAINED` / `NOT_RETAINED` |
| **All direct research traffic, including retired rows** | — | **at least 19** | **at least 20** | **1** | Evidence subset plus two non-authoritative retired dispatches |

The retained-field evidence subset reports **17 logical targets, 18 physical calls, and one
explicit retry**. The all-traffic accounting reports **at least 19 logical targets, at least 20
physical calls, and one retry**; the lower bound preserves the fact that the two retired
rows were performed without turning their missing metadata into evidence. The 11 HTTP 200 rows
include current/annual/page data and do not imply a qualified daily pair. The two exact BIS v2
404s are not absence oracles; the two successful BIS v2 rows prove only that the available VND
series in those keys is monthly VND/USD. No body or live rate is stored.

### 3.2 Sanitized target and session detail

These fields describe the evidence-complete-for-retained-fields subset without storing
query-bearing URLs, response data, credentials, cookies, or raw headers. They do not establish
subset replayability because the session/UA fields explicitly marked `NOT_RETAINED` are missing.
A target date or parameter below is an intent label, not a claim that the provider served that
date.

| Target intent | Canonical path (path-only) | Physical/outcome detail |
| --- | --- | --- |
| VCB dated `2018-01-01` initial | `www.vietcombank.com.vn/api/exchangerates` | 1 timeout before response; no MIME/effective route |
| VCB dated `2018-01-01` bounded repeat | `www.vietcombank.com.vn/api/exchangerates` | 1 retry, HTTP 200, `application/json; charset=utf-8`, canonical path |
| VCB dated `2020-01-01` | `www.vietcombank.com.vn/api/exchangerates` | 1 timeout before response; no MIME/effective route |
| VCB dated `2026-08-19` | `www.vietcombank.com.vn/api/exchangerates` | 1 HTTP 200, `application/json; charset=utf-8`, canonical path |
| SBV SGD route | `dttktt.sbv.gov.vn/TyGia/faces/TyGiaSGD.jspx` | 1 timeout before response; no MIME/effective route |
| SBV cross-rate route | `dttktt.sbv.gov.vn/TyGia/faces/TyGiaCheo.jspx` | 1 timeout before response; no MIME/effective route |
| SBV central-rate route | `dttktt.sbv.gov.vn/TyGia/faces/TyGiaTrungTam.jspx` | 1 timeout before response; no MIME/effective route |
| WDI annual JSON probe intent | `api.worldbank.org/v2/country/VNM/indicator/PA.NUS.FCRF` | Parameter intent `format=json`, `per_page=20000`; 1 HTTP 200 JSON response, canonical path; query omitted |

| Session field | Retained value |
| --- | --- |
| `initial_session_start` | `2026-08-23T16:17:20+07:00` |
| `initial_session_end` | `NOT_RETAINED` |
| `initial_user_agent` | `NOT_RETAINED` |
| `correction_session_start` | `2026-08-23T16:46:44.967256+07:00` |
| `correction_session_end` | `NOT_RETAINED` |
| `correction_user_agent` | `vnfin-oss source-design probe` |
| `bis_correction_session_marker` | `NOT_RETAINED` |

These markers identify bounded research sessions only; they do not establish replayability.
The two retired BIS rows remain counted all-traffic rows but are not in the retained-field
evidence table.

### 3.3 Non-dispatch source and legal inspections

These are page/document inspections, not successful retrievals and not rows in the direct
ledger: the Vietcombank quote page; the SBV home/menu; the PBOC RMB-parity announcement;
CFETS spot-instrument and market-data-terms pages; BIS data/methodology/legal/API pages;
ECB reference-rate roster; the World Bank catalogue; FRED's DEXCHUS page; the repository's
open.er-api source note and terms; and the Frankfurter v2, CNY, VND, provider, and underlying
provider-terms pages. A timeout while navigating an official menu is reported in the SBV
candidate record, not converted into a successful route response.

## 4. Candidate records and source/legal axes

### 4.1 Vietcombank — six independent field/basis cells

The current page and dated response show bank-side CNY columns, but each field is a separate
candidate unit. The response does not state a stable base/quote, scale, historical retention,
publication time, or revision rule. The 2018 empty envelope is not historical absence and the
2020 timeout is transport-unknown.

| Candidate unit | Response-backed observation and retained type/nullability | Direction / scale / route-specific rate-retry status | Missing for qualification | Disposition |
| --- | --- | --- | --- | --- |
| VCB dated `cash` | Recent CNY JSON object has the `cash` key; `observed_type=NOT_RETAINED`; `observed_nullability=NOT_RETAINED`; historical nullability `UNKNOWN`; the 2018 empty `Data` response has no field instance | Direction `UNKNOWN`; scale `UNKNOWN`; dated-route rate/retry policy `UNKNOWN` (one bounded retry observed, not a policy grant) | Economic basis, historical coverage, revisions, caller/storage/redistribution rights | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_UNKNOWN` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| VCB dated `transfer` | Recent CNY JSON object has the `transfer` key; `observed_type=NOT_RETAINED`; `observed_nullability=NOT_RETAINED`; historical nullability `UNKNOWN`; the 2018 empty `Data` response has no field instance | Direction `UNKNOWN`; scale `UNKNOWN`; dated-route rate/retry policy `UNKNOWN` (one bounded retry observed, not a policy grant) | Economic basis, historical coverage, revisions, caller/storage/redistribution rights; no averaging or substitution with another field | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_UNKNOWN` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| VCB dated `sell` | Recent CNY JSON object has the `sell` key; `observed_type=NOT_RETAINED`; `observed_nullability=NOT_RETAINED`; historical nullability `UNKNOWN`; the 2018 empty `Data` response has no field instance | Direction `UNKNOWN`; scale `UNKNOWN`; dated-route rate/retry policy `UNKNOWN` (one bounded retry observed, not a policy grant) | Economic basis, historical coverage, revisions, caller/storage/redistribution rights; bank sale is not central parity or a midpoint | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_UNKNOWN` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| VCB XML `Buy` | Current CNY `Buy` attribute text was observed in a complete XML response; XML attribute lexical type is string at the parser boundary, while historical absence/null semantics are unknown | Direction `UNKNOWN`; scale `UNKNOWN`; route note says one request per five minutes, but automated rate/retry permission is unknown; 0 retry observed | Current/spot only, no dated-history identity, selected economic basis, retention, or reuse permission | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| VCB XML `Transfer` | Current CNY `Transfer` attribute text was observed in a complete XML response; XML attribute lexical type is string at the parser boundary, while historical absence/null semantics are unknown | Direction `UNKNOWN`; scale `UNKNOWN`; route note says one request per five minutes, but automated rate/retry permission is unknown; 0 retry observed | Same independent current/spot and legal gaps | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| VCB XML `Sell` | Current CNY `Sell` attribute text was observed in a complete XML response; XML attribute lexical type is string at the parser boundary, while historical absence/null semantics are unknown | Direction `UNKNOWN`; scale `UNKNOWN`; route note says one request per five minutes, but automated rate/retry permission is unknown; 0 retry observed | Same independent current/spot and legal gaps | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_GAP` + `LEGAL_GAP` + `RATE_POLICY_GAP` |

The dated fields share the VCB dated ledger rows but do not share qualification. The XML
fields share one current response but do not become historical candidates. The XML route's
five-minute note is recorded independently for each XML field and is not silently applied to
the dated route. No field is averaged, inverted, midpointed, or used to fill another field.

**VCB legal axes:** owner identity is visible; automated access, caller-facing return,
storage/cache, redistribution/commercial use, attribution, dated-route rate/retry/WAF
policy, and revision/publication semantics are not granted by a public page or “for reference
only” text. The XML comment's one-request-per-five-minutes statement is not silently applied
to the dated route. A future VCB unit needs written permission or exact terms for the exact
field, route, request pattern, storage, and downstream use.

### 4.2 State Bank of Vietnam — route identities remain unresolved

The official home separates central rate, reference rates, and cross-rate surfaces. The
three direct routes timed out before a response, so this report does not assert a schema,
CNY row, unit, scale, date, pagination, retention, calendar, or count. The central USD/VND
concept cannot be converted into CNY/VND. SBV ownership is not a licence for automation,
cache, caller return, redistribution, rate, or retry.

### 4.3 PBOC / CFETS — no direct public pair and licence gate

The official PBOC announcement and CFETS spot list inspected do not show VND among the shown
direct RMB instruments. CFETS market-data terms require written authorization and restrict
copying, transmitting, saving, using, publishing, selling, or processing without it. A hidden
instrument, guessed endpoint, or regional-pair substitution is not used. Even written
permission would still need exact CNY/VND identity, date/scale/coverage, and bounded runtime.

### 4.4 BIS — published USD bilateral data is the wrong identity

The BIS data page and methodology describe nominal rates against USD; the Vietnam series is
VND/USD and the v2 probes above confirm monthly keys while daily keys returned typed 404
responses. The dataset also combines sources for consistency and may be cross-calculated.
That is not a direct CNY/VND unit. BIS terms permit use with attribution subject to their
conditions, but legal permissiveness cannot repair the wrong pair, frequency, or identity.

### 4.5 ECB and current Frankfurter v2 — current facade evidence, not a qualified unit

This correction does not inherit the old ECB-v1 “no VND” conclusion. The official Frankfurter
v2 documentation is a distinct candidate source. It states that the no-key public API tracks
daily rates from many central banks, supports historical/range routes, blends providers by
default, permits a `providers` filter, and exposes provider attribution with an expansion
option. The current V2 probes returned:

- the direct route response had `base=CNY`, `quote=VND`, a provider-free `date`, and one
  `rate`; the observed date was `2026-08-21`, outside the requested end date;
- CNY metadata reported a provider catalogue and observed bounds, while VND metadata reported
  `1998-07-07..2026-08-21` and 23 providers; the public VND page labels its shown dataset
  “Monthly dataset”;
- the provider catalogue had 84 entries; the default pair response did not identify one
  owner field/basis, and the provider list alone does not prove that every provider supplies
  a direct CNY/VND rate; and
- the owner FAQ says the API is free for commercial use but directs users to each underlying
  provider's terms, and says requests are rate-limited to prevent abuse without publishing
  a route-specific retry/cache/redistribution contract for this library.

The current [Frankfurter owner changelog](https://github.com/lineofflight/frankfurter/blob/main/CHANGELOG.md)
documents under the v2.0.0 entry (2026-05-18) that default `/v2/rates` values are a blend
derived from a USD-anchored blend; its current release notes also describe the materialized
blend as refreshed when provider data arrives. Accordingly, the default CNY/VND response is
syntactic pair output from a USD-anchored, cross-derived blend, not a direct owner-published
CNY/VND observation. Provider updates can therefore change the default output. This is a
positive basis/lineage observation about the facade, not a direct-source or false-absence claim.

Therefore Frankfurter v2 is **not** a qualified direct source. It is a multi-provider facade
with response-backed pair syntax but unresolved one-owner identity, direct economic basis, exact
requested-span coverage, underlying terms, and bounded reuse posture. It is recorded as
`IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_UNKNOWN` + `LEGAL_GAP` + `RATE_POLICY_GAP`, not as an
ECB-v1 absence and not as a route to implement. Provider filtering and attribution would
need a fresh owner/provider-specific qualification; no cross-provider blending is allowed.

ECB's own roster remains EUR-base and does not provide a direct CNY/VND unit. No ECB or
Frankfurter cross-rate is used.

### 4.6 World Bank — preserve annual USD/VND only

The official WDI indicator `PA.NUS.FCRF` is annual official exchange rate in local currency
per US dollar, period average. It is the existing `vnfin.fx.history()` source and remains
untouched. It cannot be stamped daily, converted into CNY/VND, or used as a fallback. Its
terms/attribution do not change this frequency and pair boundary.

### 4.7 H.10 / FRED / current open endpoints

The Federal Reserve H.10 page is HTML and has no Vietnam/VND row. FRED's concrete daily
series is **USD base / CNY quote** (CNY per 1 USD), not CNY base / VND quote. No arithmetic
combination is permitted. The existing open.er-api note remains a current/spot source with
no historical retention contract and restrictive raw-data redistribution terms.

### 4.8 Existing spot legal scope is unchanged

The VCB XML and open.er-api findings above concern only a possible **new historical CNY/VND
use**. #217 changes neither active spot adapter, source registration, endpoint, credential,
cache policy, nor caller-facing spot contract, and it grants no new legal clearance to those
existing adapters. “Legal gap” here means the source cannot be promoted for #217 history; it
is not a retroactive invalidation or expansion of the current spot behavior.

## 5. Future contract — non-authoritative until a qualified source exists

This section is a design boundary only. It deliberately does not freeze numeric budgets,
new public error names, a public `rate_basis` field, or a runtime API.

### 5.1 Qualification and identity

One future candidate is one same-provider tuple:

```text
provider_token + exact owner route/version + response-backed CNY/VND
+ one provider field/basis + VND per 1 CNY scale
+ observation/publication/revision semantics + coverage/calendar contract
+ lawful automated-access, caller-return, storage, redistribution, and runtime contract
```

A value quoted per 100 CNY may be divided by 100 only when the same response or owner
documentation proves that scale. Reversal, midpoint, interpolation, fill, resampling,
nearest-date matching, and cross-rate arithmetic are rejected. Provider names, URLs,
response prose, and arbitrary basis strings are not public values. A future source-specific
basis vocabulary is chosen only after a provider qualifies; no basis token or public field
is published by #217.

### 5.2 Validation ownership and model compatibility

The future design must validate at every public construction seam without changing the
current annual contract:

1. **Input/facade boundary:** `start` and `end` are exact plain `datetime.date` objects;
   `datetime`, timezone-bearing input, malformed pair, and unsupported frequency fail before
   network. Only normalized `(base=CNY, quote=VND, frequency=daily)` can enter a source.
2. **Adapter boundary:** response identity, selected field, basis, scale, date meaning,
   complete MIME, page/cursor/count, and revision metadata are validated before an
   `FXPoint` is constructed.
3. **Model boundary:** a future daily construction seam defensively rejects any point that
   is not an exact plain date; any rate that is boolean, non-numeric, non-finite, zero, or
   negative; any non-ascending or duplicate point; any base/quote/unit/value-unit mismatch;
   and any non-UTC `fetched_at_utc`. The observation date is not a timestamp. If retrieval
   time is exposed, it is a timezone-aware UTC datetime and never publication time.
4. **Facade/result boundary:** the final result rechecks the same invariants and preserves
   one source, one basis, exact dates, and sanitized diagnostics. Existing annual
   `FXHistory` construction, repr, equality, serialization, DataFrame columns, Jan-1
   period-average semantics, `rate_on()`, and source token remain byte compatible. A future
   `rate_for_year(year)` is annual-only: on a daily history it raises a typed frequency error
   before any Jan-1 lookup, so a Jan-1 daily observation can never be misread as an annual
   period average; annual history retains the current exact Jan-1 behavior. The later RED
   matrix must exercise both the daily rejection (with a Jan-1 daily point) and the unchanged
   annual positive path.

The current public `FXPoint`/`FXHistory` shape has no `rate_basis` field. #217 does not add or
populate one, and annual history is not relabeled. A future qualified-source design must
separately choose a compatibility-safe carrier and prove field flags/property/versioning,
repr/equality, serialization, DataFrame, snapshots, and positional construction before
any public basis metadata is authorized.

### 5.3 Total coverage and non-publication behavior

The future coverage record keeps three different bounds:

```text
requested_start / requested_end  = caller's inclusive request
served_start / served_end        = provider-declared archive/service bounds
observed_start / observed_end    = first/last actual returned observations
```

- Every required page/cursor must reconcile provider totals, rows, cursors, and complete
  response bodies. A no-row or malformed page before reconciliation is a failure, never a
  zero contribution or absence oracle.
- `FULL` means the provider-served bounds cover the request, all pages reconcile, returned
  dates are distinct/ordered/in-range, and every non-publication hole is explained by the
  provider's own calendar/status. Actual observation bounds remain separately exposed.
- `PARTIAL` is allowed only when the same provider declares narrower `served_start/end`, all
  pages reconcile, and exact `observed_start/end` are reported. It never claims the requested
  span and never switches source.
- If provider metadata confirms a weekend/holiday or other non-publication date, that date
  is accounted rather than filled. For a range containing both observations and confirmed
  non-publication dates, the typed result contains only actual points plus one finite
  non-publication warning. If every requested date is confirmed non-publication, the typed
  result is empty with `points=()`, `observed_start = observed_end = None`, `latest() is None`,
  a full evaluated-coverage status, and the same warning. Its future DataFrame contract is
  exact and testable: `columns == ["date", "rate"]`, an empty `RangeIndex` (the current
  `TimeSeriesResult.to_dataframe()` shape, not an implicit empty date index), and the usual
  provenance attrs; any additive coverage/warning attrs must not alter those columns or index.
  `rate_on(d)` remains exact-match-only and raises for that date; it never returns zero, a prior
  point, or a nearest date.
- A no-row page without provider confirmation is `UNKNOWN`/coverage failure and returns no
  history. Timeout, HTML/WAF, redirect, 404, truncation, invalid MIME, reservation-budget
  exhaustion, streaming byte-cap failure, and unreconciled pages never become confirmed
  non-publication.

The exact public carrier for coverage status, served/observed bounds, and finite warnings is
not frozen until a source qualifies. It must preserve the total behavior above and current
annual API compatibility.

### 5.4 Sequential budget and byte/retry mechanics

No numeric ceiling is frozen before a provider supplies route, pagination, body, rate, and
retry evidence. The future request nevertheless has these non-negotiable invariants:

- one request-scoped, sequential ledger; no per-source reset, date fan-out, cross-source
  row stitch, or accidental partial result;
- atomic pre-dispatch reservation for source/page/retry/physical counters; a failed
  reservation is `reservation_budget_exhausted`, performs no network call, creates no attempt
  row, and charges no physical dispatch;
- response bytes are not pre-reserved from an unknown `Content-Length`; while streaming and
  decompressing, each chunk is atomically charged to both the response and global byte
  counters; a response/global cap failure is `stream_byte_cap_exhausted` after dispatch,
  retains the real attempt row and physical-call charge, returns no history, and cannot
  fabricate a successful empty page;
- a retry reuses the same logical page/cursor, validates its existing ledger row, increments
  only retry and physical counters, and cannot reserve a second logical page for the same
  cursor;
- capability selection and a source-level skip consume no dispatch budget and create no
  dispatch attempt record. Reservation exhaustion is pre-dispatch as specified above, while
  stream-byte exhaustion is post-dispatch and retains the real attempt. Dispatch records exist
  only after a real reservation, so no `SKIPPED` or reservation-budget phantom attempt is
  emitted; and
- every real dispatch records status, complete MIME, effective route, row count, and
  provider cursor/total once. Missing, duplicate, or unreconciled rows fail the source as a
  whole. Public diagnostic names and exact numeric ceilings are deferred to a qualified
  source plus a compatibility review. `reservation_budget_exhausted` and
  `stream_byte_cap_exhausted` are internal design/test labels here, not frozen public enum or
  message names.

Only HTTP 200 with an exact source-approved complete MIME may be data-success. A complete
MIME is parsed after the first colon; 3xx is not followed, and 204/4xx/5xx, DNS/connection/
TLS/timeout, HTML/WAF, parse, and body-limit outcomes remain distinct internal categories.
Raw status codes, URLs, query strings, headers, bodies, cookies, credentials, provider
prose, and exception text never cross the public boundary.

## 6. Legal/runtime gate and conjunctive reopen

These rights are separate decisions, not one `public=true` shortcut:

```text
owner_identity
automated_access
caller_facing_return
storage_or_cache
redistribution
attribution
commercial_use
rate_and_retry
revision_and_correction
```

Every required axis must be granted or covered by an explicit licence for the exact route
and use. “Public page”, “reference only”, publication duty, no-key access, and a facade are
not grants. Login, paid keys, broker credentials, browser automation, challenge solving,
proxy bypass, cookie reuse, and private endpoints remain excluded.

The source gap can be reopened only when all gates pass for one same provider/route/basis:

1. owner response has an exact approved complete MIME, effective route, bounded body, and
   no unapproved redirect/WAF/challenge;
2. response plus owner documentation prove direct CNY/VND, VND per 1 CNY, one field/basis,
   scale, observation/publication/revision semantics;
3. requested or provider-declared partial bounds, actual observation bounds, pages/cursors,
   counts, calendar/non-publication status, and duplicates/internal gaps reconcile;
4. owner-approved rate, retry, pagination, body, and runtime behavior fits one atomic
   sequential ledger without date fan-out;
5. all nine legal/reuse axes are explicit; and
6. a compatibility design preserves annual behavior and defines the future diagnostics
   carrier, with a fresh RED-first implementation review only after this design PASS.

Evidence from another provider, a facade's blended rate, a current spot response, an empty
response, or a search snippet cannot satisfy a missing gate. Until this conjunction passes,
the chain remains empty and the disposition remains `SOURCE-GAP CLOSURE`.

## 7. Documentation-only lifecycle and publish boundary

A source-gap closure has no implementation step. After a final docs-only design PASS:

1. publish exactly the three paths `docs/research/2026-08-23-daily-cnyvnd-fx-history-source-vetting.md`,
   `tasks/217-design-note.md`, and `tasks/active-backlog.md` from the clean published base
   `8350329d3d881e34df62937aacf7ea4d74f99f91` through the exact correction anchor returned
   with the handoff;
2. verify remote HEAD, ancestry, exact paths, diff, blacklist/secret, offline tests,
   import/version, and isolated build;
3. post a clean `SOURCE-GAP`/no-capability resolution and close/re-read #217; and
4. leave #218 queued and untouched.

Only if a future source qualifies does a fresh source design plus implementation review
become necessary. Before final docs-only PASS, no push or close is authorized. After that PASS,
the exact publication, remote-verification, resolution, and close sequence above is allowed;
this correction still authorizes no RED, model/accessor, source registration, code, or runtime
capability.

## 8. Sources

- [SBV official home and rate menu](https://www.sbv.gov.vn/vi/trang-chu)
- [Vietcombank rate page](https://www.vietcombank.com.vn/KHCN/Cong-cu-tien-ich/Ty-gia)
- [Vietcombank XML route](https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx)
- [PBOC/CFETS RMB parity announcement](https://www.pbc.gov.cn/zhengcehuobisi/125207/125217/125925/2025122609114878612/index.html)
- [CFETS RMB/FX spot instruments](https://www.chinamoney.com.cn/english/prdfsmrfs/)
- [CFETS market-data service and written-licence terms](https://www.chinamoney.com.cn/english/svcmds/)
- [BIS Vietnam VND/USD data page](https://data.bis.org/topics/XRU/BIS%2CWS_XRU%2C1.0/M.VN.VND.E)
- [BIS SDMX API documentation](https://stats.bis.org/api-doc/v2/)
- [BIS USD bilateral-rate documentation](https://www.bis.org/statistics/xrusd/xrusd_doc.pdf)
- [BIS permitted-use/API terms](https://data.bis.org/help/legal)
- [ECB reference-rate roster](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)
- [Frankfurter v2 API documentation](https://frankfurter.dev/)
- [Frankfurter owner v2 changelog](https://github.com/lineofflight/frankfurter/blob/main/CHANGELOG.md)
- [Frankfurter currency catalogue](https://frankfurter.dev/currencies/)
- [Frankfurter CNY coverage page](https://frankfurter.dev/currencies/cny/)
- [Frankfurter VND coverage page](https://frankfurter.dev/currencies/vnd/)
- [Frankfurter provider catalogue](https://frankfurter.dev/providers/)
- [World Bank WDI catalogue](https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators)
- [Federal Reserve H.10](https://www.federalreserve.gov/releases/h10/current/)
- [FRED USD/CNY series](https://fred.stlouisfed.org/series/DEXCHUS)
