# VNCOND D1 sector-index history source vetting — #223

**Research/handoff date:** 2026-08-24 (UTC+7)
**Phase:** source/design gate only; no runtime capability is enabled by this report
**Requested selector:** canonical `VNCOND`
**Requested inclusive window:** `2018-01-01..2026-08-20` (Vietnam local dates)
**Disposition:** **SOURCE-GAP CLOSURE**
**Capability status:** the new VNCOND value-history chain remains empty; no probe, RED test,
production code, source registration, cache, archive, proxy, basket, bundled data, or
downstream signal is authorized.

## 1. Boundary, method, and clean-room record

This is a fresh VNCOND-specific source/design review. It audits the owner identity, candidate
route shape, response identity, D1 semantics, coverage, bounded runtime, and rights axes before
any implementation. It is not a claim that a broker chart route is an official HOSE feed, and it
does not turn a public page into permission to automate, cache, or redistribute rows.

Before this research, `docs/vnstock-blacklist.md` was read. The exact exclusion applied to every
search was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited result or derivative material was opened, cited, compared, installed, or used. The
evidence below is limited to official HOSE material, provider-owned VPS/SSI/VNDirect documentation
and legal/contact pages, and the repository's current clean-room adapter boundary. Other sector
reviews are methodology context only; their live rows, identity conclusions, route responses, and
permission conclusions are not reused for VNCOND.

This round deliberately made **no provider/API probe**. Official documents and public landing/UI
pages were read as source/legal evidence, but no history or identity route was dispatched. There
was no login, API key, secret, cookie, proxy, browser challenge solving, response-body capture, or
attempt to enumerate VNCOND. Consequently every response-backed field in the candidate matrix is
`NOT_PROBED` or `NOT_RETAINED`; repository route names and resolution tokens are inventory facts,
not fresh response evidence.

No raw payload, live bar/value, query-bearing URL, header block, cookie, screenshot, response
digest, constituent manifest, or provider-derived dataset is committed here.

### 1.1 Clean production and release boundary

The clean production boundary for this review is `origin/master` at:

```text
c3921a1a7a31c5de8b21f838173fd1c288b0e698
```

The clean base is the published #222 completion; this #223 source/design handoff is a
docs/backlog-only descendant and does not change the registry, source chain, or runtime behavior.
On the clean base,
`VNCOND` is present in `_KNOWN_INDEX_IDENTIFIERS` but absent from
`_VALUE_HISTORY_INDICES` in `vnfin/_contracts/index_registry.py`. The guard in both
`index_history` and `index_history_stitched` runs before the failover chain, so a recognized
deny-only index receives the typed no-served-source diagnostic with zero provider-network calls.
This report preserves that behavior.

The exact historical tag boundary named by the packet is:

```text
v0.2.0 tag: 2fe50df4f27064140ff9f7a680227a2b337ec74a
```

That tag predates the current registry/value-history guard. It is not evidence that v0.2.0
recognizes or serves VNCOND, and it must not be used to assert today's behavior. There is no
VNCOND runtime claim in this source-gap handoff.

## 2. Official VNCOND identity and legal posture

The official [HOSE 2024 Annual Report](https://staticfile.hsx.vn/Uploads/UploadDocuments/1896445/B%C3%81O%20C%C3%81O%20TH%C6%AF%E1%BB%9CNG%20NI%C3%8AN%20%28ANUAL%20REPORT%29%202024.pdf)
is the direct official code anchor reviewed for `VNCOND`; it associates that code with the
exchange's consumer-goods sector entry. The official sector factsheet separately names the
`VNAllShare Consumer Discretionary` family, while the repository taxonomy uses the canonical
selector `VNCOND`. The code anchor and family label establish namespace meaning only. They do not
bind `VNCOND` to a historical data route, provider symbol, point series, date calendar, or license.

The [HOSE VNAllShare sector factsheet](https://staticfile.hsx.vn/Uploads/UploadDocuments/2374581/Form_Factsheet_Sector_VN_T05.2025.pdf)
also declares family-level static metadata: base date `25/01/2016`, base value `533.49`,
real-time frequency, and currency unit `VND`. Those facts are methodology/factsheet evidence, not
a provider response: they do not prove the requested-window bounds, a response point scale, D1
volume, timestamp/session semantics, pagination, or reuse rights. The [HOSE index-family landing
page](https://www.hsx.vn/vi/du-lieu-giao-dich/quy-mo-giao-dich/bo-chi-so) is retained as the
transparent owner route. No opaque direct-file URL is used as a citation in this report.

The factsheet identifies HOSE brands and provides `index@hsx.vn` for index contact. No open-data
or OSS redistribution license is stated in the material retained here. Therefore the owner/legal
axis remains `LEGAL_GAP`; an implementation cannot publish HOSE-derived rows without a later rights
decision.

The official material is a methodology and identity source, not a no-login machine-history
contract. No HOSE history response was requested in this round.

## 3. Candidate evidence and bounded accounting

### 3.1 Provider-document evidence

The following primary pages establish only the stated facts:

| Owner | Official material read | Evidence that it provides | What it does **not** prove for VNCOND |
|---|---|---|---|
| HOSE | 2024 Annual Report, sector factsheet, index landing | Direct `VNCOND` code anchor, sector-family/GICS meaning, family base date/value/frequency/unit, and contact/legal posture | A no-login D1 history route, response schema, response point scale, requested-span coverage, pagination, rate policy, or OSS reuse |
| VPS | [SmartOne](https://smartoneweb.vps.com.vn/), [official web guide](https://smartone.vps.com.vn/en-US/Home/BriefUserGuide), [terms](https://vps.com.vn/dieu-khoan-su-dung) | VPS service/UI context; the guide documents customer login/password/CAPTCHA behavior; terms reserve website-content rights and describe personal-use limits | That the chart-history candidate accepts anonymous VNCOND, that a same-owner identity route exists, or that rows may be redistributed |
| SSI | [API overview](https://developers.ssi.com.vn/docs/getting-started/overview), [terms/environments](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments), [auth](https://developers.ssi.com.vn/docs/api-reference/auth-token), [Python services](https://developers.ssi.com.vn/docs/sdk/python/service-classes) | Auth/key requirements, REST/WebSocket families, generic daily OHLCV/index examples, paging parameters, and rate-limit/429 documentation | VNCOND-specific public identity/history, no-auth use, response-backed sector identity, coverage, or an anonymous redistribution grant |
| VNDIRECT | [Dstock index-history UI](https://dstock.vndirect.com.vn/du-lieu-thi-truong/lich-su-gia), [official terms lead](https://www.vndirect.com.vn/dieu-khoan-su-dung/) | A public UI category for index historical price/trading fields; the terms URL returned HTTP 403 with a Cloudflare challenge on 2026-08-24 and was not interpreted | A machine-readable VNCOND route, response identity, exact D1 coverage/pagination, rate/reuse terms, or a public redistribution license |

The SSI documentation's generic examples are not VNCOND evidence. A UI label or a generic index
list is not a response-backed identity, and a public page is not an authorization to reuse its
underlying data.

### 3.2 Provider/API probe ledger

This is a source/design review, not a live endpoint experiment. Official-document page reads are
research reads and are not counted as provider data dispatches.

| Ledger axis | Recorded value | Interpretation |
|---|---:|---|
| VNCOND history/identity logical route operations | **0** | No candidate route was called |
| Physical provider/API HTTP dispatches | **0** | No status, redirect, MIME, WAF, or response claim is made |
| Automatic retries | **0** | No retry policy was exercised |
| Redirects followed | **0** | No effective URL was observed |
| Auth/session/cookie reuse | **0** | No credential, cookie, or session was created or retained |
| Response bodies/headers retained | **0** | There is no live payload or raw header evidence in this artifact |
| Live rows, dates, pages, totals, or volumes retained | **0** | Coverage and semantics remain unproven |

The zero count is a safety boundary, not a finding that any provider has no VNCOND history. An
empty, blocked, capped, recent-only, or WAF response in a later bounded probe would prove only that
bounded outcome. It could never by itself prove universal absence.

### 3.3 Candidate route matrix

Paths below are current-repository candidate inventory only. They are not freshly probed, and the
resolution token is an adapter mapping, not response evidence. A qualification unit requires one
provider's exact history route plus a same-owner identity route; every incomplete pair is a gap.

| Candidate owner/unit | Current repository history candidate | Same-owner identity route | D1 mapping in current adapter | Response-backed route/identity/transport fields | Total status |
|---|---|---|---|---|---|
| HOSE owner | `NOT_RETAINED`; official material exposes no retained machine route in this review | `NOT_RETAINED` | `NOT_RETAINED` | response status, MIME, envelope, selector, redirect, effective host, session/WAF, rows, dates and pages/totals: `NOT_PROBED`; detail `NO_ROUTE_RETAINED` | `TRANSPORT_INCONCLUSIVE` |
| VPS / `vps_index` | `https://histdatafeed.vps.com.vn/tradingview/history` | No VNCOND-specific same-owner identity route is established; any future pair must be separately documented | `D` | all response and legal/runtime proof axes: `NOT_PROBED`/`NOT_RETAINED`; SmartOne login/UI evidence does not bind this route | `IDENTITY_GAP` |
| SSI / `ssi_index` | `https://iboard-api.ssi.com.vn/statistics/charts/history` | No VNCOND-specific same-owner identity route is established in the current index adapter | `1D` | generic SSI API documentation is not a VNCOND response; status, full MIME, envelope, selector, identity, dates, pages, rate and reuse: `NOT_PROBED`/`NOT_RETAINED` | `IDENTITY_GAP` |
| VNDIRECT / `vndirect_index` | `https://dchart-api.vndirect.com.vn/dchart/history` | No VNCOND-specific same-owner identity route is established in the current index adapter | `D` | Dstock UI evidence is not a response; status, full MIME, envelope, selector, identity, dates, pages, rate and reuse: `NOT_PROBED`/`NOT_RETAINED` | `IDENTITY_GAP` |

The route hosts and paths above must not be read as permission, reachability, or a promise that
the provider recognizes `VNCOND`. The source chain remains empty. In particular, current adapter
defaults such as `value_unit="points"`, `currency="points"`, and `AdjustmentPolicy.RAW` are
clean-room output contracts for already-qualified index sources; they do not prove provider point
scale, volume unit, timestamp/session semantics, or adjustment policy for VNCOND.

## 4. Qualification axes and total disposition

### 4.1 One provider unit, no cross-source repair

One qualification unit is one provider's exact VNCOND history/identity route pair and its complete
semantic, runtime, and rights contract. Every unit must report all of the following axes:

1. owner, canonical role/host/path, non-secret selector, D1 token, redirect/effective host,
   **complete** Content-Type and normalized MIME, envelope, auth/session/WAF posture, and
   logical/physical/page/retry counts;
2. response-backed VNCOND symbol, exchange/index/sector identity, same-owner binding, point scale,
   timezone/session, and D1 capability;
3. inclusive `2018-01-01..2026-08-20` request, provider-declared and observed first/last local
   dates, total/distinct rows, requested-bound presence, duplicate/conflicting dates, internal
   gaps, inception/base-date evidence, and reconciled page/total/cursor/window limits;
4. finite OHLC point semantics, timestamp date/open/close meaning, volume presence/unit/null
   policy, RAW adjustment, and exactly one normalized D1 point per observation; and
5. automation, rate/retry, caller-facing return, cache/storage/retention, attribution,
   commercial-use, and redistribution rights.

The result is one total status from:

```text
QUALIFIED | PARTIAL | NOT_SERVED | IDENTITY_GAP | COVERAGE_GAP | TIMESTAMP_GAP |
VOLUME_GAP | PAGINATION_GAP | LEGAL_GAP | RATE_POLICY_GAP | TRANSPORT_INCONCLUSIVE
```

Secondary axes are not allowed to disappear behind a friendly `PARTIAL`. A candidate whose route
has not been probed is `TRANSPORT_INCONCLUSIVE` or, where the missing same-owner binding is the
decisive defect, `IDENTITY_GAP`; that is not a claim of provider absence.

### 4.2 Per-unit gap ledger

| Unit | Identity | D1 points/volume/time | Coverage/pagination | Runtime/legal | Total status |
|---|---|---|---|---|---|
| HOSE owner publication | Official annual-report code anchor and factsheet family identity; no machine history/identity pair is retained | `NOT_PROBED`; factsheet family unit is VND, but response point scale, timestamps, volume and RAW semantics are unproven | `COVERAGE_GAP + PAGINATION_GAP`; no provider bounds or observed rows; detail `NO_ROUTE_RETAINED` | `RATE_POLICY_GAP + LEGAL_GAP`; no OSS reuse grant | **`TRANSPORT_INCONCLUSIVE`** |
| VPS candidate | No response-backed provider symbol/exchange/index binding | `VOLUME_GAP + TIMESTAMP_GAP` are unresolved; all response fields `NOT_PROBED` | `COVERAGE_GAP + PAGINATION_GAP`; no declared/observed window | `RATE_POLICY_GAP + LEGAL_GAP + TRANSPORT_INCONCLUSIVE` | **`IDENTITY_GAP`** |
| SSI candidate | Generic keyed API examples do not prove VNCOND; no same-owner response pair | `VOLUME_GAP + TIMESTAMP_GAP` are unresolved; all response fields `NOT_PROBED` | `COVERAGE_GAP + PAGINATION_GAP`; no VNCOND bounds/rows | `RATE_POLICY_GAP + LEGAL_GAP + TRANSPORT_INCONCLUSIVE` | **`IDENTITY_GAP`** |
| VNDIRECT candidate | Public UI category does not provide response-backed VNCOND identity | `VOLUME_GAP + TIMESTAMP_GAP` are unresolved; all response fields `NOT_PROBED` | `COVERAGE_GAP + PAGINATION_GAP`; no VNCOND bounds/rows | `RATE_POLICY_GAP + LEGAL_GAP + TRANSPORT_INCONCLUSIVE` | **`IDENTITY_GAP`** |

No unit is `QUALIFIED` or `PARTIAL-qualified`: no unit has a response-backed identity and complete
lawful contract. The conclusion is a source gap, not a false-absence claim.

### 4.3 Fixed-window and future stitched coverage

The requested fixed window is the inclusive local-date interval
`2018-01-01..2026-08-20`. No candidate gets `FULL` or `PARTIAL` coverage in this review because
no response, provider-declared boundary, observed first/last date, total, page, cursor, or
exchange-calendar contract was retained.

Fixed-window qualification means one provider unit returns one validated VNCOND series for the
whole requested range. It cannot be assembled from VPS identity, SSI volume, and VNDIRECT dates.
First/last rows, `nextTime=null`, a chart's visual extent, or agreement with another provider do
not prove completeness.

The existing opt-in stitched entry point is a separate future operation, not a source-gap escape
hatch. If a later source qualifies, stitched D1 may use calendar-year segments only when every
segment is independently validated, the request-scoped budget is shared, overlaps are checked,
seams are deterministic, and failure is atomic. A stitched result may never be used to claim that
one provider covers the fixed window or to repair a missing identity, volume, legal, or coverage
axis. Every segment must carry a non-`None`, timezone-aware `fetched_at_utc` whose
`utcoffset() == timedelta(0)`. Missing, naive, or non-UTC segment stamps fail the aggregate
atomically. The aggregate is exactly the maximum of those validated UTC stamps; it must not be
fabricated or downgraded when a segment stamp is unavailable. This is a future design constraint,
not current runtime behavior.

## 5. Future contract, reopen gate, and no-capability boundary

### 5.1 Reopen criteria are conjunctive

The source gap may reopen only when one named provider unit supplies **all** of these, with
response-backed evidence and conservative legal disposition:

1. official owner/path and an exact same-owner identity route, or written owner permission that
   explicitly covers the proposed access;
2. a response that identifies `VNCOND` as the requested exchange/sector index, with a deterministic
   history-to-identity binding and no proxy, basket, or locally inferred mapping;
3. exact D1 response semantics: status/envelope/complete MIME, finite positive OHLC, documented
   point scale, timezone/session/date interpretation, non-null volume with documented unit/null
   policy, and explicit RAW adjustment;
4. provider-declared and observed coverage for the requested inclusive window, reconciled totals and
   pages/cursors, duplicate/conflict/internal-gap policy, and a clearly separated partial outcome;
5. bounded automation, rate, retry, page, byte, and total physical-request policy, with a single
   atomic request-scoped ledger for identity/history/pagination/retries; and
6. attribution, retention, cache/storage, commercial-use, and redistribution rights sufficient
   for the proposed public API, plus offline synthetic RED fixtures that exercise every contract.

Failure of any one conjunct keeps the new source chain empty. A route that is reachable but lacks
rights is not qualified; a licensed route with no response identity is not qualified; and a
complete-looking row set with no reconciled bounds is not qualified.

### 5.2 Runtime design reserved for a later qualified-source PASS

This document does not authorize code or a public API. If a later exact design PASS qualifies a
unit, the implementation packet may then specify:

- add `VNCOND` exactly once to `_VALUE_HISTORY_INDICES`; preserve all other deny-only identifiers
  and the price-path type guard;
- accept exact D1 only; reject wrong/proxy/non-D1 selectors before network; preserve canonical
  requested and response-backed identities;
- return one provider's complete validated `PriceHistory` with `currency="points"`,
  `value_unit="points"`, `AdjustmentPolicy.RAW`, canonical source identity, bounded warnings,
  and no synthesized volume or metadata;
- build a VNCOND capability filter from independently qualified provider roles only. Preserve the
  relative VPS → SSI → VNDirect order among qualified roles; exclude every unqualified or unknown
  role before scheduling, creating no call and no `SourceAttempt` for it. If the filtered set is
  empty, return the typed no-qualified-source terminal without a provider call. Never silently
  route strict calls to stitched;
- use stitched D1 only as an explicit future operation with independent segment validation, seam
  checks, source/segment provenance, atomic failure, and deterministic aggregate metadata; and
- expose only finite sanitized diagnostics. No raw query, response body, cookie, token, unbounded
  provider text, or fabricated `SourceAttempt` is public.

### 5.3 Shared global budget contract

The future budget is one request-scoped, atomic ledger across strict history, identity, page/cursor
fetches, retries, and every stitched segment. Its qualified numeric ceilings must be recorded from
provider evidence before implementation; this review intentionally assigns no unsourced number.
Each reservation must atomically charge the logical operation, physical dispatch, page, and retry
unit before the dispatch occurs. Wire bytes and decompressed bytes cannot be known before reading:
the transport must increment separate counters for each bounded chunk, abort as soon as the next
chunk would exceed its cap, discard the accumulator, and return a deterministic terminal budget
outcome. A non-streaming transport that cannot enforce those incremental caps is not eligible for
qualification. A failed pre-dispatch reservation makes no network call; byte exhaustion aborts the
stream and returns no partial bars. All outcomes preserve prior sanitized attempts. The ledger must
not reset per source/year, retry in a loop, or hide concurrency. The exact public exception/result
carrier remains deferred to a later qualified-source API PASS; this source-gap design specifies
only the typed terminal kind and sanitized internal fields. A candidate with no route-specific
limit remains `RATE_POLICY_GAP`.

### 5.4 Future RED/release matrix

Only after a qualified-source design PASS may RED tests be written, using committed synthetic
fixtures only. The matrix must include:

| Area | Required RED cases |
|---|---|
| Selector/routing | exact, lowercase, padded `VNCOND`; wrong index, proxy, unknown, punctuation, and non-D1 selectors fail typed and zero-network |
| Identity | history/identity pair agrees on symbol, exchange/index/sector, interval, point scale, timezone/session, and provenance; missing/wrong/mismatched values fail closed |
| Transport/data | unexpected status, redirect/effective-host change, full MIME mismatch, generic HTML, malformed envelope/status, non-finite/invalid OHLC, volume null/unit mismatch, wrong adjustment fail closed |
| Coverage | requested-bound presence, provider declared totals, page/cursor reconciliation, duplicate/conflicting dates, internal gaps, inception/base-date, full versus partial, and no false absence |
| Budget/atomicity | shared logical/physical/page/retry ledger, incremental wire/decompressed byte caps, pre-dispatch reservation, chunk-boundary abort/discard, deterministic scheduling, preserved sanitized attempts on exhaustion, no hidden per-year reset, deferred public carrier, and no partial return after failure |
| Stitching | one/multiple calendar years, inclusive boundaries, identical/conflicting overlaps, seam order, segment provenance, non-`None` UTC-aware zero-offset stamps, exact UTC maximum, missing/naive/non-UTC atomic failures, mid-range failure, and global exhaustion |
| Compatibility | all currently served indices, every other deny-only index including VNCOND before enablement, price-path rejection, public DataFrame/snapshot/docs/import surfaces, and D1/non-D1 behavior |

## 6. Final source-gap disposition and delivery boundary

The official annual report anchors the `VNCOND` code and the sector factsheet supplies family-level
Consumer Discretionary/static metadata, but neither establishes a lawful, response-backed, bounded,
complete D1 history unit. VPS, SSI, and VNDIRECT candidates remain identity/runtime/legal gaps
because this round made no provider/API probe and retained no VNCOND response. Therefore the only
safe disposition is:

```text
SOURCE-GAP CLOSURE
new VNCOND history chain = empty
current recognized-index deny-only / zero-network behavior = preserved
```

This source/design handoff authorizes only exact-anchor review of the two documents and backlog
lifecycle, followed—if approved—by the documented source-gap publication/resolution/close flow.
It does not authorize a probe, RED test, TDD, production code, source registration, proxy/basket,
downstream signal, push, or issue close before the reviewer returns an exact design PASS.

### Evidence links

- [HOSE 2024 Annual Report](https://staticfile.hsx.vn/Uploads/UploadDocuments/1896445/B%C3%81O%20C%C3%81O%20TH%C6%AF%E1%BB%9CNG%20NI%C3%8AN%20%28ANUAL%20REPORT%29%202024.pdf)
- [HOSE VNAllShare sector factsheet](https://staticfile.hsx.vn/Uploads/UploadDocuments/2374581/Form_Factsheet_Sector_VN_T05.2025.pdf)
- [HOSE index-family landing page](https://www.hsx.vn/vi/du-lieu-giao-dich/quy-mo-giao-dich/bo-chi-so)
- [VPS SmartOne](https://smartoneweb.vps.com.vn/) · [VPS web guide](https://smartone.vps.com.vn/en-US/Home/BriefUserGuide) · [VPS terms](https://vps.com.vn/dieu-khoan-su-dung)
- [SSI API overview](https://developers.ssi.com.vn/docs/getting-started/overview) · [SSI terms/environments](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments) · [SSI auth](https://developers.ssi.com.vn/docs/api-reference/auth-token) · [SSI Python services](https://developers.ssi.com.vn/docs/sdk/python/service-classes)
- [VNDIRECT Dstock index history](https://dstock.vndirect.com.vn/du-lieu-thi-truong/lich-su-gia) · [VNDIRECT terms lead (HTTP 403; not interpreted)](https://www.vndirect.com.vn/dieu-khoan-su-dung/)
