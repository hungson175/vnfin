# VNREAL D1 sector-index history source vetting — #213

**Date:** 2026-08-23 (UTC+7)
**Phase:** source/design gate only; no runtime capability is enabled by this report
**Requested selector:** canonical `VNREAL`
**Requested inclusive window:** `2018-01-01..2026-08-19` (Vietnam local dates)
**Disposition:** **SOURCE-GAP CLOSURE**
**Capability status:** the new VNREAL source chain remains empty; no TDD, production code,
cache, archive, bundled data, or public foreign/source claim is authorized.

## 1. Boundary, method, and clean-room record

This is a fresh, provider-by-provider review of the Real Estate sector-index value
history. It is not a claim that a broker chart route is the official exchange feed, and
it does not turn a no-login observation into a licence to automate, cache, or redistribute
rows.

Before this research, `docs/vnstock-blacklist.md` was read. The exact exclusion applied to
every search was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited result or derivative material was opened, cited, compared, installed, or
used. The evidence below is limited to provider-owned VPS, SSI, and VNDirect routes,
official HOSE material, official provider terms/contact pages, the public UDF protocol,
and the repository's current clean-room adapter boundary. The prior VNFIN review is
methodology context only; its data, identity, or permission conclusions are not reused
for VNREAL.

The bounded observation was run on 2026-08-23 using direct HTTPS GETs, a sequential
no-login client, no `Authorization` header, no credential, no proxy, no browser
automation, no challenge-solving, and no cookie/session reuse. The client used this
browser-like User-Agent in the bounded observation because the routes were observed with
it:

```text
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36
```

No no-UA control was run. Therefore UA necessity is **untested**; the observation does
not establish transport necessity or permission to automate. Provider
`Set-Cookie` headers observed during the round were not retained or sent on another
request. Temporary response bodies were discarded after sanitized shape, identity, date,
and quality checks. No raw payload, live bar/value, query-bearing URL, cookie, token,
screenshot, short/live content digest, or provider dataset is committed here.

### Current clean ancestry and release boundary

The clean production boundary for this review is `origin/master` at the full SHA
`4c85fbc6a1101b3a904b1dc68ac37bc29477ef6`. The current registry and zero-network claims
are bound to that reachable clean base. Backlog-only commits `202b5d5` and later
commits in this review cycle record queue/review state only; they do not alter the
production boundary, registry, source chain, or runtime behavior.

In that clean base, `VNREAL` is present in the private index deny namespace but absent
from `_VALUE_HISTORY_INDICES`. Therefore the price namespace still rejects it as an
index, while both `index_history("VNREAL", ...)` and
`index_history_stitched("VNREAL", ...)` fail with the shared typed terminal diagnostic
before network access. This report does not change that boundary.

The annotated `v0.2.0` release boundary is the exact tag
`2fe50df4f27064140ff9f7a680227a2b337ec74a`. It is a historical release boundary and is
not evidence that VNREAL was served. Do not mix tag-era files with current clean-base
behavior in a later implementation review.

## 2. Official identifier evidence

Official HOSE annual reports list `VNREAL` within the exchange's sector-index family.
That establishes the exchange namespace/sector meaning only. It does not bind any
broker route to HOSE, prove a complete historical archive, or grant permission to
return provider rows from an OSS API.

- [HOSE 2023 annual report](https://staticfile.hsx.vn/Uploads/UploadDocuments/1896430/B%C3%A1o%20c%C3%A1o%20th%C6%B0%E1%BB%9Dng%20ni%C3%AAn%202023.pdf)
- [HOSE contact page](https://www1.hsx.vn/vi/lien-he)

Only the working 2023 report and contact path are retained. No dead-link claim or
unreachable 2024 citation is used in the identity decision. The official material is an
identifier reference, not a source-selection oracle. No constituent basket, equity proxy,
ETF, screenshot, search snippet, or cross-provider numeric agreement is used as VNREAL
identity.

## 3. Observation ledger and route contract

### 3.1 Exact bounded accounting

There were two sequential observation passes over the same six VNREAL route cells:

| Quantity | #213 VNREAL observation | Combined #213 + #214 batch |
|---|---:|---:|
| Providers | 3 (`VPS`, `SSI`, `VNDirect`) | 3 per symbol; symbols remain independent |
| Requested symbols | 1 (`VNREAL`) | 2 (`VNREAL`, `VNMID`) |
| Route cells per pass | 6 (history + same-owner identity per provider) | 12 (six per symbol) |
| Passes | 2 | 2 |
| Logical route operations | **12** (`6 × 2`) | **24** (`12 × 2`; 12 per symbol) |
| Physical HTTP dispatches | **12** | **24** (12 per symbol) |
| Automatic retries | 0 | 0 |
| Redirects followed | 0 | 0 |
| Cookies retained/reused | 0 | 0 |
| Parallel requests | 0 | 0 |

One **logical route operation** is one named provider route cell for one requested symbol
and window. In this observation, one logical route operation mapped to exactly one
**physical HTTP request**; there was no retry, redirect follow, hidden page, or second
identity dispatch. The combined 24/24 number is accounting for the two-symbol batch only,
not cross-symbol evidence or a runtime quota. The observation ledger is not a provider
permission or a future runtime budget.

The non-secret request contract was provider route + `symbol=VNREAL` + provider D1 token
and local-window `from`/`to` epoch parameters. The exact D1 tokens observed were `D` for
VPS and VNDirect, and `1D` for SSI. No query string is reproduced in this repository.

### 3.2 Provider route and transport matrix

Every row below is one qualification unit: one provider's history route, its same-owner
identity route, one symbol namespace, and one evidence/legal contract. A different
provider cannot repair a missing axis in that unit.

| Provider / owner | Canonical route pair | D1 token; envelope | Full observed Content-Type → normalized media type | Redirect/auth/WAF/session observation | Rate/retry/cache/legal posture |
|---|---|---|---|---|---|
| VPS / VPS Securities | History [`/tradingview/history`](https://histdatafeed.vps.com.vn/tradingview/history); identity [`/tradingview/symbols`](https://histdatafeed.vps.com.vn/tradingview/symbols) | `D`; bare UDF object | History and identity: `application/json; charset=utf-8` → `application/json` | HTTP 200 on both; no redirect; no auth challenge; no WAF/interstitial observed; metadata reports `session=0900-1500`; bounded observation used browser-like UA; no no-UA control | No route-specific quota or retry grant established; observation used zero retry; no cache/storage used; [VPS terms](https://vps.com.vn/dieu-khoan-su-dung) do not provide affirmative OSS caller-facing redistribution permission; **LEGAL_GAP + RATE_POLICY_GAP + TRANSPORT_INCONCLUSIVE** |
| SSI / SSI Securities Corporation | History [`/statistics/charts/history`](https://iboard-api.ssi.com.vn/statistics/charts/history); identity [`/statistics/charts/symbol`](https://iboard-api.ssi.com.vn/statistics/charts/symbol) | `1D`; `{code,data,message,status}` envelope with UDF data inside | History and identity: `application/json; charset=utf-8` → `application/json` | HTTP 200 on both; no redirect; no auth challenge; no WAF/interstitial observed; identity response proves timezone but does not close a stable session contract; `Set-Cookie` observed and discarded; browser-like UA used; no no-UA control | No route-specific quota or permitted retry policy established; observation used zero retry; no cache/storage used; [SSI service terms](https://www.ssi.com.vn/dieu-khoan-dich-vu) do not provide anonymous chart-row redistribution permission; keyed [SSI developer terms](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments) are not a grant for this route; **LEGAL_GAP + RATE_POLICY_GAP + TRANSPORT_INCONCLUSIVE** |
| VNDirect / VNDIRECT Securities | History [`/dchart/history`](https://dchart-api.vndirect.com.vn/dchart/history); identity [`/dchart/symbol`](https://dchart-api.vndirect.com.vn/dchart/symbol) | `D`; bare UDF object | History: `text/plain;charset=UTF-8` → `text/plain`; identity failure: `application/json` → `application/json` | History HTTP 200, identity HTTP 404; no redirect; no auth challenge or WAF/interstitial observed; no same-owner session metadata; browser-like UA used; no no-UA control | No route-specific quota or permitted retry policy established; observation used zero retry; no cache/storage used; [VNDIRECT terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) provide no affirmative route-specific OSS automation/caching/redistribution grant; [VNDIRECT support](https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/) is the contact path for written permission; **LEGAL_GAP + RATE_POLICY_GAP + TRANSPORT_INCONCLUSIVE** |

The full Content-Type is part of the evidence. A future parser must read the complete
header value after the first colon, compare the exact approved full value, then normalize
only the media type. An unexpected parameter/value, status, effective route, or generic
maintenance HTML response fails closed. In this observation no redirect was followed and
no WAF verdict can be inferred from a successful browser-like-UA request. HTTP
reachability is not legal, redistribution, automation permission, or proof that UA is
necessary.

### 3.3 Response identity and daily semantics

| Provider | Requested selector and response-backed identity | Daily point/volume/time observations | Identity/semantic gaps |
|---|---|---|---|
| VPS | History body included `symbol=VNREAL`; same-owner metadata returned `symbol=ticker=name=VNREAL`, `timezone=Asia/Ho_Chi_Minh`, `session=0900-1500`, `has_daily=true`, `has_no_volume=false`, `pricescale=100`, `pointvalue=1`. This is echo/metadata evidence only; provider-backed exchange/index type is not established | History exposed aligned `s,t,o,h,l,c,v` arrays; observed volumes were present, non-null, non-negative, and finite; timestamps mapped to Vietnam-local dates; metadata is consistent with index points | No complete identity binding, historical date calendar, timestamp open/close convention, RAW adjustment rule, page/total/cursor semantics, or reuse rights. Conflicting duplicate dates prevent a clean fixed-window result |
| SSI | History envelope had no symbol field. Same-owner identity response returned `symbol=ticker=name=VNREAL`, `exchange=HOSE`, `listed_exchange=HOSE`, `type=Chỉ số`, `timezone=Asia/Ho_Chi_Minh`, `has_daily=true`, `has_no_volume=false`, `pricescale=100`, `pointvalue=1`, and success status; history-to-identity binding remains unproven | Inner UDF data exposed aligned `s,t,o,h,l,c,v` arrays; observed volumes were present, non-null, non-negative, and finite; timestamps mapped to Vietnam-local dates; `s=ok`, outer `code=SUCCESS`, `status=ok` | No complete identity qualification because history has no symbol and no exact response-backed correlation rule; `nextTime=null` is not a total-count proof. Session/open-close, RAW adjustment, calendar, pagination, and reuse rights remain unproven |
| VNDirect | History body had no symbol. Same-owner identity route returned HTTP 404 with no usable VNREAL metadata | Bare UDF data exposed aligned `s,t,o,h,l,c,v` arrays; observed volumes were present, non-null, non-negative, and finite; timestamps mapped to Vietnam-local dates; `s=ok`; body MIME remained `text/plain;charset=UTF-8` | No response-backed symbol, exchange/index type, scale/pointvalue, timezone/session, D1 identity, or adjustment proof. A symbol-shaped request alone is not identity |

The data checks are shape observations, not a clean qualification. The desired future
contract is exactly one normalized daily point per served exchange session, finite positive
OHLC values with `low <= open/close <= high`, aligned non-null volume, documented volume
unit, `value_unit="points"`, `currency="points"`, and explicit `AdjustmentPolicy.RAW`.
None of the three routes published a complete provider-side statement covering all of
those semantics. Repository point/RAW settings are design defaults, not provider legal or
historical-adjustment proof.

## 4. Total provider disposition and fixed-window coverage

### 4.1 Stable total-disposition vocabulary

A provider disposition is a **total ordered tuple**, not a list of selected findings. For
this review the tuple order is fixed and every provider row must state every applicable
axis with no omission:

```text
IDENTITY_GAP, PARTIAL, COVERAGE_GAP, TIMESTAMP_GAP, VOLUME_GAP,
ADJUSTMENT_GAP, PAGINATION_GAP, TRANSPORT_INCONCLUSIVE, LEGAL_GAP, RATE_POLICY_GAP
```

`PARTIAL` is the observed outcome marker: rows or metadata were observed but a complete
qualification was not. `IDENTITY_GAP` is present even where the provider echoed the
request or returned same-owner metadata: VPS lacks provider-backed exchange/index type,
and SSI lacks history-to-metadata binding. `ADJUSTMENT_GAP` means RAW semantics are not
provider-proven. `TRANSPORT_INCONCLUSIVE` includes the untested UA necessity and any
status/MIME/effective-route policy not yet contractually closed. No complete VPS, SSI, or
VNDirect identity is claimed.

| Provider unit | Identity conclusion | Fixed-window observation | **Total technical + legal disposition (no omitted axes)** |
|---|---|---|---|
| `vps_index` | `IDENTITY_GAP`: history echo plus same-owner metadata only; exchange/index binding is incomplete | 1,649 raw / 1,615 distinct local dates; first `2020-03-03`, last `2026-08-19`; 34 duplicates, including 33 conflicting; requested start unserved | `IDENTITY_GAP + PARTIAL + COVERAGE_GAP + TIMESTAMP_GAP + VOLUME_GAP + ADJUSTMENT_GAP + PAGINATION_GAP + TRANSPORT_INCONCLUSIVE + LEGAL_GAP + RATE_POLICY_GAP` |
| `ssi_index` | `IDENTITY_GAP`: same-owner metadata exists, but history has no symbol and exact binding is unproven | 2,148 raw / 2,147 distinct; first `2018-01-02`, last `2026-08-19`; one identical duplicate; requested literal start unproven; no provider total | `IDENTITY_GAP + PARTIAL + COVERAGE_GAP + TIMESTAMP_GAP + VOLUME_GAP + ADJUSTMENT_GAP + PAGINATION_GAP + TRANSPORT_INCONCLUSIVE + LEGAL_GAP + RATE_POLICY_GAP` |
| `vndirect_index` | `IDENTITY_GAP`: history lacks symbol and identity route returned HTTP 404 | 2,152 raw / 2,152 distinct; first `2018-01-02`, last `2026-08-19`; requested literal start unproven | `IDENTITY_GAP + PARTIAL + COVERAGE_GAP + TIMESTAMP_GAP + VOLUME_GAP + ADJUSTMENT_GAP + PAGINATION_GAP + TRANSPORT_INCONCLUSIVE + LEGAL_GAP + RATE_POLICY_GAP` |

The three tuples are intentionally conservative and independent. A complete identity is
not inferred from a request echo, same-owner metadata, matching dates, or cross-provider
agreement. No row is a qualified release candidate.

### 4.2 Reviewed fixed horizon versus future arbitrary/stitched ranges

The reviewed fixed horizon is exactly the inclusive local-date interval
`2018-01-01..2026-08-19`. It is an observation boundary, not a provider retention
promise. The first literal date is a boundary observation, not an assertion that a
Sunday/holiday must have a bar. Because no provider supplied a route-specific exchange
calendar contract, an absent literal boundary is recorded as **unproven**, not as proof
that history starts there or that the source lacks older data.

A future API may receive arbitrary `from`/`to` dates syntactically, but this review
qualifies no arbitrary horizon. Until a new source/design review extends the contract,
the only full-range boundary is the reviewed interval above. A request whose inclusive
range is outside it, or crosses it, fails closed before network with the finite reason
`coverage_gap` and the warning token `out_of_reviewed_horizon`; it is not silently clipped
or converted into a full result. A separately reviewed qualified partial result may use
only the finite outcome `coverage_partial` and, when applicable, the warning tokens
`partial_start_coverage` and/or `partial_end_coverage`; it must expose its observed
bounds through existing bounded metadata and must never claim the full reviewed horizon.

The future coverage contract must bind the provider's documented exchange trading
calendar, base date, inclusive boundaries, total/page/cursor/window-cap reconciliation,
and internal-gap policy in the same source unit. It must not infer a missing date from
weekend/holiday intuition, first/last row alone, `nextTime=null`, or one bounded
observation. A missing date without the provider calendar is `COVERAGE_GAP`, not
`NO_DATA_OBSERVED`.

| Provider | Raw rows | Distinct local dates | Duplicate dates | First observed local date | Last observed local date | Start/end boundary | Fixed-window decision |
|---|---:|---:|---:|---|---|---|---|
| VPS | 1,649 | 1,615 | 34 (33 conflicting, 1 identical) | `2020-03-03` | `2026-08-19` | start absent; end present | **PARTIAL + COVERAGE_GAP**; requested 2018 span is not served and conflicting dates are not a clean series |
| SSI | 2,148 | 2,147 | 1 identical | `2018-01-02` | `2026-08-19` | start absent; end present | **PARTIAL + COVERAGE_GAP** pending official calendar/boundary and duplicate contract; not an end-to-end winner |
| VNDirect | 2,152 | 2,152 | 0 observed | `2018-01-02` | `2026-08-19` | start absent; end present | **PARTIAL + COVERAGE_GAP + IDENTITY_GAP**; complete-looking row count cannot repair missing identity |

No provider-declared total, page count, cursor, or window-cap field was observed. SSI's
`nextTime=null` means only that this response did not advertise another cursor; it does
not prove complete history. These are `PAGINATION_GAP` diagnostics, not claims of
absence.

**Fixed window** means one provider qualification unit returns one validated series for
the entire requested range. It cannot be created by taking SSI identity, VPS volume, and
VNDirect dates, and it cannot be inferred from first and last observed dates.

**Stitched window** is a separate, explicit future operation. The current entrypoint
shape is D1-only and divides `2018..2026` into nine calendar-year segments. It may be
considered only after strict VNREAL qualification; a segment may not use a different
provider to repair another provider's missing axis. A stitched series is not evidence
that any one provider covers the full span and is not a workaround for legal permission.

## 5. Future private response-metadata seam (design-only)

The current injected transport contract must remain backward-compatible: injected GET
callables with `(url, params, headers)` and POST callables with their existing four
arguments that return `str` remain valid. `_request_text` continues to return `str` to
all existing callers. This section defines a private future seam only; it is not a code
change or public API change.

The future transport module may define private immutable types named
`HttpResponseMetadata` and `HttpResponseText`:

```text
HttpResponseMetadata (immutable, module-private)
  status_code: int
  content_type: str | None          # complete value, not media type only
  effective_url: str
  redirect_count: int
  headers: tuple[tuple[str, str], ...] | None  # private, optional, bounded

HttpResponseText (module-private)
  body: str | bytes
  metadata: HttpResponseMetadata
```

The default transport captures status, the complete Content-Type, effective URL, redirect
count, and bounded private headers from the response **before** `raise_for_status`, then
unwraps the body and preserves `_request_text -> str` for legacy callers. A legacy
injected stub returning only `str` has unavailable metadata (`None`) and therefore any
metadata-sensitive VNREAL path fails closed; it remains valid for existing callers. A
synthetic offline future fixture may return the private wrapper through the same legacy
callable arity. No type is publicly exported or added to snapshots.

An optional private `response_observer: Callable[[HttpResponseMetadata | None], None]`
may receive exactly one metadata event per physical dispatch, including each future retry.
It is not public/re-exported and must not receive raw URLs, query strings, bodies, cookies,
provider exception text, credentials, or unbounded headers. A future route validator must
check exact status, the complete Content-Type value after the first header colon, the
approved normalized media type, exact effective host/path, redirect count, and envelope.
Generic maintenance HTML, an unexpected status, wrong full MIME, or wrong effective route
fails closed. This seam is required before any future qualification RED test; no seam or
runtime capability is added in this source-gap correction.

## 6. Exact global budget and closed diagnostic grammar (design-only)

The future VNREAL strict and stitched calls reuse the already approved #209 contract
verbatim. The public future exception is:

```text
vnfin.exceptions.BudgetGlobalExhausted(VnfinError)
  symbol: str
  interval: Interval
  attempts: tuple[SourceAttempt, ...]
  diagnostic: Literal["budget_global_exhausted"]
```

It is not `SourceError`, not a private sentinel, and not a public terminal object or
partial `PriceHistory`. It is exported only from `vnfin.exceptions` (and listed in that
module's `__all__`), not from `vnfin` or `vnfin.prices`; the future index wrappers
propagate it. There are no unspecified public counter fields.

`max_attempts` is one shared atomic logical-source budget, bounded to integer `1..3`,
with default `3`. A capability skip consumes zero logical or physical budget and creates
no attempt. A strict call has at most `3` logical attempts and `6` physical dispatches
(identity plus history per eligible role). The nine-segment stitched call has at most
`27` logical attempts and `54` physical dispatches, with no per-segment reset. One
logical attempt is one `(provider, symbol, interval, segment)` evaluation; one physical
dispatch is one actual HTTP request. Reservations are deterministic and atomic: reserve
the logical source slot and each physical slot before dispatch; no concurrent reservation,
hidden page, redirect, retry, or rate-policy dispatch is admitted by this design.

If the first reservation for an eligible source fails, raise
`BudgetGlobalExhausted` at the outer boundary with `attempts=tuple(prior_sanitized_attempts)`;
a fresh zero-call exhaustion has `attempts=()`, and an uninvoked source adds no attempt.
If exhaustion occurs after an adapter has started, discard its private in-progress buffer
and append exactly one failed logical `SourceAttempt` with canonical reason
`budget_global_exhausted`; page/retry reservations never create their own attempts. The
exception never fabricates a `diagnostics_truncated` attempt. Strict failover and stitched
assembly remain atomic: no partial `PriceHistory` is returned.

### Closed public attempt and warning grammar

`SourceAttempt` retains its current public shape `name, ok, reason`. Its `name` is exactly
one of `vps_index`, `ssi_index`, or `vndirect_index`; unknown, non-string, unhashable, or
malicious injected source members are filtered before dispatch, consume zero budget, and
may add only the bounded warning `source_unknown`. They never leak a custom name into a
public attempt. `ok` is true exactly when `reason=ok`.

Every public `reason` is ASCII, matches
`^[a-z][a-z0-9_]{0,47}$`, and belongs to this closed finite allow-list:

```text
ok
budget_global_exhausted
identity_gap
identity_missing
identity_mismatch
wrong_exchange
wrong_index_type
wrong_interval
point_invalid
volume_missing
volume_invalid
adjustment_gap
timestamp_invalid
coverage_gap
coverage_partial
duplicate_conflict
pagination_gap
transport_inconclusive
mime_mismatch
http_status_unexpected
redirect_mismatch
auth_required
waf_challenge
legal_gap
rate_policy_gap
not_served
no_data_observed
source_unknown
```

The public attempt tuple has at most 3 entries in strict mode and at most 27 entries in
stitched mode. The finite warning tuple has at most 32 tokens for a strict call or
segment and at most 64 tokens for a stitched aggregate. Each token is ASCII, at most 64
characters, and is either one of:

```text
stitched_multi_source
partial_start_coverage
partial_end_coverage
out_of_reviewed_horizon
diagnostics_truncated
deduped_duplicate_daily_index_bars
quarantined_invalid_bars
source_unknown
```

or matches exactly:

```text
^stitched_segment:[0-9]{4}:(vps_index|ssi_index|vndirect_index):[0-9]{1,6}$
```

No warning or attempt token contains a URL, query, body, cookie, header, provider
exception text, credential, or live value. `diagnostics_truncated` is a bounded warning
only when deterministic token truncation is needed; it never creates a synthetic attempt.
Counters remain private. Any pagination, redirect, retry, or rate-policy change requires
another finite formula and design review.

## 7. Legal, reuse, and runtime disposition

No-auth reachability is not a licence. The official provider pages reviewed for this
batch establish the following conservative posture:

| Provider | Official primary evidence | Current decision |
|---|---|---|
| VPS | [VPS terms](https://vps.com.vn/dieu-khoan-su-dung) and [VPS company/contact page](https://vps.com.vn/ve-chung-toi) | No affirmative route-specific permission for automated OSS retrieval, caller-facing return, caching/storage, commercial use, or redistribution; written permission required |
| SSI | [SSI service terms](https://www.ssi.com.vn/dieu-khoan-dich-vu), [SSI network/contact page](https://www.ssi.com.vn/mang-luoi), and separate [developer terms](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments) | Anonymous chart access is not a redistribution grant; keyed/developer terms do not qualify this route; written permission required |
| VNDirect | [VNDIRECT terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) and [support/contact page](https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/) | No affirmative chart-route OSS automation, cache, caller-facing, or redistribution grant; written permission and a response-backed identity route are required |

Current runtime disposition for all three is no cache, no storage, no bundled rows, no
archive, no bulk export, and no caller-facing source capability. The routes' current HTTP
behavior is an observation only; unknown rate limits are treated as finite/unsafe, not
unlimited.

## 8. Future-only #213 VNREAL RED and release matrix

This is an executable specification for a later, separately approved TDD cycle. It is
**future-only**: this source-gap correction adds no RED test, production code, fixture,
network guard, or runtime source. Each row must be implemented with committed synthetic
fixtures and offline HTTP mocks only after a fresh design PASS.

| Future case | Required RED assertion and release meaning |
|---|---|
| Selector positives | Exact `VNREAL`, case-normalized and padded forms canonicalize to one selector; exact `Interval.D1` and typed local range are accepted; no network is used by validation |
| Selector/namespace negatives | Wrong sector, `VNFIN`, constituent/basket/proxy/ETF, unknown, punctuation, malformed range, wrong interval, price namespace, and every deny-only identifier fail typed before network; existing served indices remain callable |
| Identity positive | A synthetic same-provider response pair proves symbol, exchange/index type, D1, point scale/value, timezone/session, and exact history/metadata binding; only then can a source succeed |
| Identity negatives | Request echo only, missing/mismatched symbol, SSI unbound history, wrong exchange/type/interval/point scale, missing/invalid adjustment or timestamp, and non-canonical provenance fail with finite reasons |
| Transport negatives | Metadata wrapper with unexpected status, full Content-Type mismatch (including generic HTML), wrong normalized media type, effective host/path mismatch, redirect mismatch, or missing metadata on a metadata-sensitive path fails closed; legacy string stubs remain valid for existing non-index callers |
| Coverage positive | Synthetic provider calendar/base date, inclusive reviewed horizon, total/page/cursor/window-cap, one row per session, aligned volume, and exact boundaries produce a complete strict series |
| Coverage negatives | Recent-only/recent cap, missing literal date without provider calendar, unexplained start/end, internal gap, duplicate conflict, missing/null volume, invalid OHLC, no total/cursor reconciliation, and `nextTime=null` without completeness evidence produce `coverage_gap`, `pagination_gap`, `volume_gap`, or `duplicate_conflict` as applicable; no false absence |
| Horizon/partial | Outside or crossing the reviewed horizon makes no request and emits `coverage_gap` plus `out_of_reviewed_horizon`; an explicitly reviewed partial emits only `coverage_partial` with `partial_start_coverage`/`partial_end_coverage`, never a full-range claim; no calendar inference is permitted |
| Strict atomicity | A failed first source leaves no partial bars; capable-role skip consumes zero budget; failover uses one shared ledger and only a fully validated one-provider result is returned |
| Strict budget | `max_attempts=1,2,3` is accepted; other values fail before network; maximum is 3 logical/6 physical; first-reservation exhaustion preserves prior sanitized attempts, fresh exhaustion is `()`, and mid-adapter exhaustion appends one budget attempt; page/retry reservations add none |
| Stitched segmentation | Nine calendar-year segments use one global 27 logical/54 physical budget with no reset; a missing, unqualified, or budget-exhausted segment returns no partial aggregate; identical seam bars may deduplicate, conflicting seams fail |
| Stitched provenance | Aggregate warnings contain only allow-listed tokens and `stitched_segment:YYYY:role:bar_count`; unknown injected sources are skipped with `source_unknown`; no URL/body/provider text is public; `diagnostics_truncated` never becomes an attempt |
| Stitched retrieval time | `fetched_at_utc` equals `max(segment.fetched_at_utc for successful segments)` after UTC normalization; a missing or timezone-naive segment timestamp fails the whole aggregate with `timestamp_invalid`; no current clock is fabricated |
| Response seam | Synthetic `HttpResponseText` positive metadata is observed once per physical dispatch, including retries; legacy 3-argument GET/4-argument POST text stubs still work; unavailable metadata fails only metadata-sensitive index qualification |
| Public compatibility | Existing `PriceHistory` fields, `source`, warnings, attempts, DataFrame conversion, import paths, snapshots, current served-index behavior, price deny behavior, and existing stitched semantics remain byte-compatible unless a separately reviewed export change is intentional |
| Release gates | Before any future release, run focused/full offline tests, build/import/version checks, zero-network deny guard, API/snapshot/docs/skill/CHANGELOG checks, blacklist and secret scans, diff/object/path/clean-tree checks, then request exact-SHA reviewer approval; no live provider rows are bundled |

## 9. Conjunctive reopen criteria and conclusion

Reopen to a fresh design review, and only then to TDD, when **one same provider** passes all
conditions together:

1. **Identity:** response-backed `VNREAL`, exchange/index type, point scale/value,
   timezone/session, D1 capability, and exact history/metadata binding.
2. **Fixed coverage:** the requested inclusive window is proven against a documented
   exchange calendar/base date, with total/page/cursor/window-cap reconciliation, one
   normalized daily point per session, no conflicting duplicates, and explicit partial
   boundary/internal-gap diagnostics.
3. **Semantics:** finite positive OHLC with the high/low envelope, aligned non-null volume
   with documented unit, exact D1 token, timestamp convention, and provider-backed RAW
   points declaration. Missing or unproven volume fails closed.
4. **Transport:** exact status/full Content-Type/effective route contract through the
   private metadata seam, stable redirect policy, UA necessity explicitly tested rather
   than inferred, explicit auth/session/cookie policy, and no maintenance HTML.
5. **Legal/runtime:** written permission covers automated retrieval, OSS use, caller-facing
   return, redistribution, storage/caching, attribution, commercial use, rate limits, and
   retry behavior for the named route.
6. **Budget/atomicity:** the shared `3 / 6` strict and `27 / 54` stitched ledger is
   deterministic and pre-dispatch atomic; strict failover is whole-window, stitched
   failure is whole-call, and no fake attempt/partial result is emitted.
7. **Diagnostics/compatibility:** the closed grammar, no-false-absence outcomes, current
   deny behavior, existing served indices, snapshots, docs, build, blacklist/secret, and
   merged-tree gates pass without changing current capability.

Until all seven conditions are evidenced for the same provider, the correct state is
`SOURCE-GAP CLOSURE`. A later source-gap approval authorizes documentation publication,
clean resolution, remote verification, and close/re-read only; it never authorizes TDD or
production capability.

Primary protocol and provider route references:

- [TradingView UDF protocol](https://www.tradingview.com/charting-library-docs/latest/connecting_data/UDF/)
- [VPS history route](https://histdatafeed.vps.com.vn/tradingview/history)
- [VPS symbol metadata route](https://histdatafeed.vps.com.vn/tradingview/symbols)
- [SSI history route](https://iboard-api.ssi.com.vn/statistics/charts/history)
- [SSI symbol metadata route](https://iboard-api.ssi.com.vn/statistics/charts/symbol)
- [VNDirect history route](https://dchart-api.vndirect.com.vn/dchart/history)
- [VNDirect symbol metadata route](https://dchart-api.vndirect.com.vn/dchart/symbol)

The direct evidence is sufficient to say that VPS, SSI, and VNDirect returned bounded
no-login VNREAL-shaped daily responses on 2026-08-23. It is not sufficient to say that
any one provider supplies a lawful, response-identified, complete, clean, rate-bounded,
redistributable `2018-01-01..2026-08-19` unit. VPS is recent and conflict-prone; SSI has
metadata but lacks history binding and a complete fixed-window/legal/runtime contract;
VNDirect lacks same-owner identity. Therefore **no source qualifies end-to-end**.

The design result is deliberately conservative: preserve the empty VNREAL chain and the
current typed zero-network behavior, record `SOURCE-GAP CLOSURE`, and do not begin RED,
production code, push, or issue closure from this report.
