# VNMID D1 index-history source vetting — #214

**Date:** 2026-08-23 (UTC+7)
**Phase:** source/design gate only; no runtime capability is enabled by this note
**Canonical selector:** `VNMID`
**Requested inclusive window:** `2018-08-13..2026-08-19`
**Disposition:** **SOURCE-GAP CLOSURE**
**Qualification rule:** one provider, one exact VNMID history/identity unit, and all identity,
coverage, points/time/volume, transport, rate, and legal/reuse axes must pass together.

This is a bounded clean-room review. It does not claim that any broker chart route is the
official exchange feed, and it does not combine providers to manufacture a full series. No
raw response, bar/value, cookie, token, screenshot, URL with query parameters, or live-content
digest is committed.

## 1. Clean-room boundary and current product boundary

Before this research, `docs/vnstock-blacklist.md` was read. The exact exclusion applied to
searches was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited result or derivative material was opened, cited, compared, installed, or used.
Evidence below is limited to official HOSE material, provider-owned terms/contact pages, and
fresh bounded observations of the three named provider route pairs. Licensing uncertainty is
reported as a gap rather than inferred away.

The current repository boundary is deny-only: `VNMID` is a recognized index identifier used to
reject the stock-price namespace, but it is absent from the private value-history allow-list.
Therefore both strict and explicit stitched index-history calls fail typed and zero-network
for `VNMID`. This note does not authorize changing that behavior. The annotated `v0.2.0` tag
is a historical boundary, not evidence of capability: it resolves to
[`2fe50df4f27064140ff9f7a680227a2b337ec74a`](https://github.com/hungson175/vnfin/commit/2fe50df4f27064140ff9f7a680227a2b337ec74a),
which predates the later private namespace guard. Current deny-only behavior and the tag's
older tree must not be conflated.

The only future product primitive under consideration is the existing strict call, returning
provider-reported daily index points. This batch does **not** authorize a constituent basket,
proxy, ETF, equity substitution, current-membership reconstruction, signal, backtest, archive,
cache, intraday history, or a new public API. `index_history_stitched()` remains an explicit
future opt-in only; it is never a silent fallback for strict history.

## 2. Official identifier and ownership boundary

HOSE's current [VNMidcap factsheet](https://staticfile.hsx.vn/Uploads/UploadDocuments/2438018/Form_Factsheet_MCIndices_VN_T02.2026.pdf)
describes **VNMidcap** as an HOSE-Index measuring the growth of 70 medium-sized companies in
VNAllshare, with an official base-date and methodology. The [HOSE-Index factsheet](https://staticfile.hsx.vn/Uploads/UploadDocuments/2396611/Form_Factsheet_MCIndices_VN_T08.2025.pdf)
likewise identifies VNMidcap as part of the HOSE-Index family and states that the index names
are HOSE-owned marks. These documents establish the exchange-side identifier and methodology
boundary only. They do not establish that a broker chart route is an official historical-data
API, nor do they grant this library redistribution rights.

The repository's `VNMID` selector is a canonical library/provider token. A response that merely
returns the request string `VNMID` is not sufficient to assert the official HOSE VNMidcap
identity. A future accepted unit must bind the provider response to the requested symbol and
index type on that same provider, and must keep the exchange-side name distinct from the
provider's producer identity.

For a written identity/licensing question, the official HOSE [contact page](https://www1.hsx.vn/vi/lien-he)
and the factsheet's index contact route are the escalation paths. No HOSE permission was
obtained in this review.

## 3. Method and bounded observation ledger

The observation date was 2026-08-23. Requests were no-login, no-credential IPv4 HTTP calls
using the repository's desktop browser user-agent:

```text
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36
```

The browser-like UA was a bounded transport choice in this observation. No no-UA control was
run, so its necessity is untested. It is not evidence of public automation permission. No
`Authorization` header, API key, login, browser session, challenge solving, proxy bypass, or
private route was used. SSI and VNDirect emitted response cookies in the
observed batch; no cookie was retained or reused. The request used the requested local
Vietnam-time window, but query-bearing request URLs and epoch values are intentionally not
stored here.

The route templates were:

| Provider/owner | History route | Same-owner identity route | D1 request token |
|---|---|---|---|
| VPS | [VPS history route](https://histdatafeed.vps.com.vn/tradingview/history) | [VPS symbol route](https://histdatafeed.vps.com.vn/tradingview/symbols) | `D` |
| SSI | [SSI history route](https://iboard-api.ssi.com.vn/statistics/charts/history) | [SSI symbol route](https://iboard-api.ssi.com.vn/statistics/charts/symbol) | `1D` |
| VNDirect | [VNDirect history route](https://dchart-api.vndirect.com.vn/dchart/history) | [VNDirect symbol route](https://dchart-api.vndirect.com.vn/dchart/symbol) | `D` |

Parameters were supplied separately as non-secret `symbol`, resolution, and bounded `from`/`to`
fields. No query-bearing URL is part of the repository.

There were two bounded observation passes over the batch's three providers × two symbols
(`VNMID` and the independently audited `VNREAL`) × two routes (history and identity). For
`VNMID`, 6 route cells per pass × two passes are **12 logical / 12 physical** operations.
The combined #213/#214 batch is **24 logical / 24 physical**.

| Ledger scope | Logical route operations | Physical HTTP dispatches | Retries | Parallelism | Retained payload |
|---|---:|---:|---:|---|---|
| `VNMID`: 6 route cells/pass × 2 passes | 12 | 12 | 0 | none | none |
| Whole #213/#214 observation batch | 24 | 24 | 0 | none | none |

Here one logical operation is one planned provider route cell, and one physical dispatch is one
actual HTTP request; there was no retry, redirect follow-up, or hidden request. This is an observation ledger, not a runtime budget or a promise of
future availability. A response cookie, redirect, timeout, WAF behavior, or empty body would
be recorded as an outcome axis, never as proof that historical VNMID data did not exist.

## 4. Fresh VNMID provider matrix

The following values are sanitized shape, metadata, count, date, and header observations. No
OHLC or volume values are reproduced. “Normalized MIME” means the complete `Content-Type`
value after outer whitespace normalization; media-type-only reduction is not allowed.

### 4.1 Qualification summary

The following table records bounded observations, not complete identity qualification. VPS and SSI
returned same-owner metadata, but neither observation proved a provider-backed exchange/index-type
binding for its history unit; VNDirect lacked usable identity altogether. The stable uppercase
disposition vocabulary is: `IDENTITY_GAP`, `PARTIAL`, `COVERAGE_GAP`, `TIMESTAMP_GAP`,
`VOLUME_GAP`, `ADJUSTMENT_GAP`, `PAGINATION_GAP`, `TRANSPORT_INCONCLUSIVE`, `LEGAL_GAP`, and
`RATE_POLICY_GAP`. Every provider receives the complete ordered tuple
`(IDENTITY_GAP, PARTIAL, COVERAGE_GAP, TIMESTAMP_GAP, VOLUME_GAP, ADJUSTMENT_GAP, PAGINATION_GAP, TRANSPORT_INCONCLUSIVE, LEGAL_GAP, RATE_POLICY_GAP)` with no omitted axis; it is not shortened to the first failing token.

| Provider unit | Transport and MIME | Identity observation (not complete qualification) | Fixed-window and semantic observation | Total ordered disposition |
|---|---|---|---|---|
| VPS `VNMID` history + symbol | History `200`, no redirect, effective host/path unchanged, `application/json; charset=utf-8`; identity `200`, same normalized MIME; no auth challenge observed | Response-backed echo and same-owner metadata: `symbol=ticker=name=VNMID`, timezone/session/daily/scale fields. Provider-backed exchange/index-type binding for the history unit is not established | 1,649 rows / 1,615 dates; first `2020-03-03`, last `2026-08-19`; requested start absent/end present; aligned `t/o/h/l/c/v`; 34 duplicate dates, 33 conflicting; four OHLC quality flags | `(IDENTITY_GAP, PARTIAL, COVERAGE_GAP, TIMESTAMP_GAP, VOLUME_GAP, ADJUSTMENT_GAP, PAGINATION_GAP, TRANSPORT_INCONCLUSIVE, LEGAL_GAP, RATE_POLICY_GAP)` |
| SSI `VNMID` history + symbol | History `200`, no redirect, effective host/path unchanged, `application/json; charset=utf-8`; identity `200`, same normalized MIME; response cookie seen and discarded | Response-backed `symbol=ticker=name=VNMID`, `exchange=HOSE`, `type=Chỉ số`, timezone/daily/scale fields. Complete history-to-identity binding and rights are not proven | 1,915 rows / 1,915 dates; first `2018-12-11`, last `2026-08-19`; requested start absent/end present; `nextTime=null`; aligned `t/o/h/l/c/v` | `(IDENTITY_GAP, PARTIAL, COVERAGE_GAP, TIMESTAMP_GAP, VOLUME_GAP, ADJUSTMENT_GAP, PAGINATION_GAP, TRANSPORT_INCONCLUSIVE, LEGAL_GAP, RATE_POLICY_GAP)` |
| VNDirect `VNMID` history + symbol | History `200`, no redirect, effective host/path unchanged, full normalized MIME `text/plain;charset=UTF-8`; identity `404`, `application/json` | History body did not echo a symbol; same-owner identity route yielded no usable identity record | 2,003 rows / 2,003 dates; both requested boundaries present; aligned `t/o/h/l/c/v`; no provider scale/type metadata | `(IDENTITY_GAP, PARTIAL, COVERAGE_GAP, TIMESTAMP_GAP, VOLUME_GAP, ADJUSTMENT_GAP, PAGINATION_GAP, TRANSPORT_INCONCLUSIVE, LEGAL_GAP, RATE_POLICY_GAP)` |

All three providers therefore lack complete qualification. The observed shape cannot promote VPS or
SSI to qualified identity, cannot repair VNDirect's identity gap, and cannot close legal, rate,
transport, timestamp, volume, adjustment, pagination, or coverage axes. No provider qualifies for
TDD.

### 4.2 Route, envelope, identity, and semantic cells

| Provider | History envelope and selector binding | Identity/owner binding | Point/time/volume evidence | Unresolved seam |
|---|---|---|---|---|
| VPS | Bare object with `symbol`, `s`, `t`, `o`, `h`, `l`, `c`, `v`; the observed body echoed `VNMID`; daily selector `D` | Same-owner symbol route returned the exact requested token and index-like metadata; this is stronger than a request-only label but does not complete provider-backed exchange/index-type identity or prove HOSE ownership/rights | `type` is not claimed from the identity response; `pricescale=100`, `pointvalue=1`, and `has_daily=true` support points/D1 interpretation; timestamps were converted to `Asia/Ho_Chi_Minh`; `session=0900-1500`; raw `v` was present/aligned | Coverage starts in 2020; duplicate/conflicting dates and invalid observations prevent clean full-span acceptance; provider did not document volume units or adjustment policy in this observation |
| SSI | Outer `{code,data,message,status}` with inner `t`, `o`, `h`, `l`, `c`, `v`, `nextTime`; history has no symbol field; daily selector `1D` | Same-owner symbol route returned `VNMID`, `HOSE`, `Chỉ số`, daily capability, timezone, and point scale; this is an observation only, and complete history-to-metadata binding must be enforced, not inferred from the request string | `pricescale=100`, `pointvalue=1`, `has_daily=true`, `has_no_volume=false`; timestamps were converted to local dates; volume was present/aligned; no session claim | Coverage starts in 2018-12; `nextTime=null` is not a provider total; no provider documentation establishes internal date completeness, volume unit, RAW adjustment, or rights |
| VNDirect | Bare object with `s`, `t`, `o`, `h`, `l`, `c`, `v`; daily selector `D`; no symbol echo; full MIME is `text/plain;charset=UTF-8`, not a media-type-only `application/json` claim | Same-owner symbol route returned `404`; no response-backed VNMID identity or exchange/type/scale metadata | Timestamps converted to local dates; volume field was present/aligned; no response-backed point scale, timezone, session, or adjustment metadata | Exact boundary coverage cannot repair missing identity. A changed body fingerprint or successful HTTP status is not identity proof and no digest is retained |

The source observations support the library's future *interpretation* of index values as
`points`, not VND prices, only when the same-provider identity/scale contract is accepted.
They do not prove that the provider's `v` field is shares, money, turnover, or a comparable
constituent aggregate. The future contract must call it provider-reported volume, document its
unit only if the provider does, and never fill absent/null volume with zero.

The chart responses did not expose a reliable adjustment flag. `AdjustmentPolicy.RAW` is a
future library contract that requires provider documentation or an equivalent response-backed
no-adjustment guarantee; it is not established merely because the route is named “history.”
The observed timestamp conversion establishes only a local-date normalization procedure. It
does not prove the provider's market-open/close timestamp convention, holiday calendar, or
historical session policy for every date.

### 4.3 Transport, access, retry, cache, and diagnostic axes

The following axes are intentionally independent:

- **Redirect:** no redirect was observed for six VNMID route cells per pass, or 12 physical
  dispatches across two passes; effective host/path remained the requested provider route. This
  is not a permanent redirect guarantee.
- **MIME:** the full normalized values were `application/json; charset=utf-8` for VPS/SSI
  history and identity, and `text/plain;charset=UTF-8` for VNDirect history. VNDirect identity
  was `404` with `application/json`. A future route validator must parse the complete value and
  reject an unexpected status or MIME, including a colon-suffixed MIME/value; it must not truncate
  the value or accept a JSON-shaped body as permission to ignore the header.
- **Authentication/session:** no login, API key, authorization header, or pre-existing session
  was used. SSI and VNDirect emitted cookies, which were discarded. Cookie issuance is not a
  requirement to reuse the cookie and is not evidence of public redistribution rights.
- **Browser/WAF:** the browser-like UA was used for this bounded transport observation. No no-UA
  control was run, so necessity is untested; no WAF challenge was retained or solved. A successful
  response with that UA does not establish a stable automation or permission policy. An
  HTML/challenge response, 403, timeout, or connection failure is a transport diagnostic, not a
  historical absence.
- **Rate/retry:** no route-specific quota, `Retry-After`, or public retry policy was established
  by these observations. The observation made zero retries. The [SSI developer terms and
  environments page](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)
  describes authenticated API environments and rate/429 behavior, but it does not grant this
  unauthenticated chart route a quota or reuse permission. VPS and VNDirect route limits were
  not found in the reviewed official terms. Unknown is not unlimited.
- **Cache/storage:** no response was cached, archived, bundled, or retained. The reviewed terms
  do not give this library a storage/redistribution grant. Any future cache policy must be
  written into provider permission and the public contract, not inferred from HTTP success.
- **Logical versus physical:** each route dispatch counted once in the ledger; no retry,
  pagination, redirect follow-up, or hidden parallel request was counted away. Future identity,
  history, page, and retry dispatches must have separate physical reservations under one
  request budget.

### 4.4 Future private response-metadata seam (design only)

The current transport contract is frozen for compatibility: an injected GET callable has the
shape `http_get(url, params, headers) -> str`, an injected POST callable `(url, params, headers, json_body) -> str`, and `_request_text` continues to return `str`. The current default
transport discards status, headers, and effective URL before returning text; this docs-only note
changes no code or public snapshot.

A later implementation may add only a private observer seam:

- immutable private `HttpResponseMetadata` with exactly `status_code: int`,
  `content_type: str | None` (the complete `Content-Type` value after the first header colon and
  outer whitespace normalization, not media-type-only), `effective_url: str`,
  `redirect_count: int`, and optional private headers held as a bounded tuple;
- private `HttpResponseText(body: str | bytes, metadata: HttpResponseMetadata)` accepted by
  internal code, then unwrapped so `_request_text` still returns `str` to existing callers;
- legacy injected GET/POST stubs returning `str` remain valid, but metadata is unavailable
  (`None`) and any metadata-sensitive index qualification fails closed; synthetic tests may return
  the private wrapper through the same legacy callable arity;
- the default transport captures status, full headers, effective URL, and redirect count before
  `raise_for_status`, then unwraps the body; an optional private
  `response_observer: Callable[[HttpResponseMetadata | None], None]` runs exactly once per
  physical dispatch, including any future retry; and
- the types, observer, headers, URLs, query values, bodies, provider prose, and raw exceptions
  are not public exports, re-exports, snapshots, or diagnostics. Route validation checks exact
  expected status, the complete MIME value, exact effective host/path, and redirect policy; a
  colon-suffixed MIME/value fails closed. A JSON-shaped body cannot override a
  status/full-MIME/effective-route mismatch.

This seam preserves the current three-/four-argument injection boundary and makes metadata absence
an explicit transport/identity gap instead of inferred success. It is not implemented here.

## 5. Official legal and reuse posture

No-auth reachability is a transport observation, not a licence. The provider-owned pages below
are primary terms/contact evidence and are kept separate from the technical matrix:

| Owner | Official evidence | Conservative legal conclusion for this library |
|---|---|---|
| VPS | [VPS terms of use](https://vps.com.vn/dieu-khoan-su-dung) and [VPS company/contact page](https://vps.com.vn/ve-chung-toi) | The terms state that website products/content are VPS-owned and restrict copying, transfer, display, distribution, storage, and derivative versions without official written consent; personal download/print language does not grant an OSS runtime redistribution licence. **LEGAL_GAP.** |
| SSI | [SSI service terms](https://www.ssi.com.vn/dieu-khoan-dich-vu) and [SSI network/contact page](https://www.ssi.com.vn/mang-luoi) | The terms permit personal viewing/analysis/reformatting/printing but prohibit publishing, transmitting, or reproducing the information to third parties without written SSI consent. **LEGAL_GAP.** |
| VNDirect | [VNDIRECT online-application terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) and [VNDIRECT support/contact](https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/) | The terms identify VNDIRECT-provided website information/services and contain no affirmative route-specific grant for automated OSS retrieval, caching, commercial use, or caller-facing redistribution. **LEGAL_GAP.** |
| HOSE | [VNMidcap factsheet](https://staticfile.hsx.vn/Uploads/UploadDocuments/2438018/Form_Factsheet_MCIndices_VN_T02.2026.pdf) and [HOSE contact](https://www1.hsx.vn/vi/lien-he) | HOSE material establishes the exchange identifier and protected index-family boundary. It is not permission to redistribute a broker's chart response. Written identity/mark and data-use permission remains unproven. |

The runtime-safe status is **no capability**: no provider rows in fixtures/examples, no cache or
archive, no bulk export, no public live-value examples, and no source chain entry. A future
permission request must address automated retrieval, caller-facing return, storage/caching,
attribution, commercial use, rate limits, user-agent/session policy, and redistribution of
both points and provider-reported volume.

## 6. Fixed-window versus stitched coverage

The requested window is a fixed qualification observation, not a generic promise:

- VPS: first served local date `2020-03-03`; requested `2018-08-13` is absent; last date
  `2026-08-19` is present. The 34 duplicate dates include 33 conflicting and one identical
  duplicate; the quality pass also flagged four invalid OHLC observations. No duplicate,
  invalid row, or gap is silently repaired.
- SSI: first served local date `2018-12-11`; requested `2018-08-13` is absent; last date
  `2026-08-19` is present. `nextTime=null` is not a total or proof of completeness.
- VNDirect: both requested literal boundary dates were present, but the history response has
  no response-backed symbol identity and its identity route returned `404`.

The fixed-window contract is exactly the reviewed literal `2018-08-13..2026-08-19` horizon. A
future provider unit must publish a supported horizon and official trading-calendar rule before
accepting arbitrary dates. An out-of-horizon request is a typed `COVERAGE_GAP`/`NOT_SERVED`
boundary outcome before network, never an empty success, a zero-volume fill, or false absence.
A `PARTIAL` result is allowed only when response-backed first/last boundaries and the official
calendar explain the boundary; it must expose `partial_start_coverage` or
`partial_end_coverage` and can never be promoted to `FULL`. A weekend/holiday boundary is distinct
from an unexplained missing date. Counts are array counts, not provider-declared totals; internal
date completeness remains unproven. Empty, capped, recent-only, or failed results are bounded
outcomes and never evidence that VNMID was historically absent.

The existing explicit stitched shape is calendar-year segmentation, so this requested range would
span nine calendar segments (`2018` through `2026`). A future stitched implementation would have
to:

1. keep D1, points, RAW, canonical VNMID identity, and aligned volume checks per segment;
2. reserve all identity/history/page/retry dispatches from one request-scoped global ledger, with
   no per-segment reset or hidden concurrency;
3. preserve canonical segment producer provenance and fail atomically if any segment is missing,
   identity-inconsistent, conflicting, over budget, or legally unserved;
4. distinguish fixed-window, arbitrary-range, and stitched calendar semantics; weekend/holiday
   boundaries cannot be fabricated or silently labeled absent; and
5. remain opt-in and separate from strict whole-window failover. Cross-provider numerical
   agreement cannot repair a missing identity, coverage, unit, or legal axis.

The stitched aggregate, if ever authorized, must set `fetched_at_utc = max(segment.fetched_at_utc)`
over successful segments. A missing or tz-naive segment time is `timestamp_invalid` and aborts the
aggregate. No stitched capability is enabled by this report; strict and stitched chains remain
empty under the current SOURCE-GAP closure.

## 7. Future global-budget and diagnostic design (not implemented)

This is the bounded, deterministic reopen contract, not an implementation authorization. Strict
and stitched calls own one request-scoped ledger and one single deterministic scheduler.
Reservations are atomic and checked before network. Capability skips reserve zero logical or
physical budget and create no `SourceAttempt`.

### 7.1 Exact request budgets and `BudgetGlobalExhausted`

`max_attempts` is an integer in `[1, 3]`, default `3`, and means eligible logical provider
attempts. Strict whole-window maximum: **3 logical / 6 physical** dispatches (identity then
history per attempt). The nine-segment VNMID stitched maximum: **27 logical / 54 physical**
dispatches (`9 × 3`, then `27 × 2`). An identity failure does not dispatch history. A page,
cursor, redirect follow-up, or retry would be another physical reservation under the same cap; the
current source-gap design admits no page or retry and no per-segment reset.

Reuse the exact approved #209/#210 public contract, without adding fields or changing its meaning:

- future public `vnfin.exceptions.BudgetGlobalExhausted(VnfinError)` has exactly
  `symbol: str`, `interval: Interval`, `attempts: tuple[SourceAttempt, ...]`, and
  `diagnostic: Literal["budget_global_exhausted"]`;
- it is not `SourceError`, not a private sentinel, and not a public terminal result; it is exported
  only from `vnfin.exceptions`, not from `vnfin` or `vnfin.prices`; index-history wrappers propagate
  it unchanged;
- if the first reservation for an eligible source fails, preserve prior sanitized attempts; a
  fresh zero-call request has `attempts=()` and an uninvoked source adds no attempt;
- if exhaustion occurs after an adapter is invoked (before a later page or identity control),
  discard its private buffer and add exactly one failed logical `SourceAttempt` with the canonical
  budget reason; page and retry reservations never create their own attempts; and
- the scheduler reserves the logical attempt before adapter entry and each physical dispatch
  immediately before HTTP. Exhaustion raises before that operation and publishes no sentinel,
  partial `PriceHistory`, or false full-span result. Private counters are not exception fields.

Strict failover is whole-window only. Stitched mode is explicit, uses this same global ledger
across all nine segments, and commits the aggregate atomically only after every segment passes.

### 7.2 Exact finite `SourceAttempt` and warning grammar

The public attempt shape remains `SourceAttempt(name: str, ok: bool, reason: str)`. Canonical
names are only `vps_index`, `ssi_index`, and `vndirect_index`; arbitrary injected names are
rejected or skipped before dispatch and never appear in a public attempt. `reason` must match
`^[a-z][a-z0-9_]{0,47}$` and belong to this closed allow-list:

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

Attempts are capped at 3 entries in strict mode and 27 entries across one stitched call. `ok` is
true only for reason `ok`; every other reason is false. Warning tuples are capped at 32 entries
per strict call/segment and 64 entries for a stitched aggregate. Each warning is ASCII, at most
64 characters, and must be one of:

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

A stitched provenance warning may additionally be exactly
`stitched_segment:YYYY:role:bar_count`, matching
`^stitched_segment:[0-9]{4}:(vps_index|ssi_index|vndirect_index):[0-9]{1,6}$`. No warning,
attempt, or public error may contain a URL, query, body, cookie, credential, raw exception,
provider prose, live value, or unbounded date list. `diagnostics_truncated` is a bounded warning
only and never a synthetic attempt.

A 404 identity route is `identity_missing`, not proof that VNMID was never served. Empty,
recent-only, capped, or partial data, 403/429/5xx, timeout, WAF challenge, wrong MIME, and
unknown rate policy are bounded failures, not historical absence. `NOT_SERVED`/source-gap closure
is allowed only after the finite candidate set is attempted or mechanically skipped with explicit
reasons while unresolved transport/identity states remain visible.

## 8. Future per-symbol RED/release matrix — `VNMID` (design-only)

This is a future, per-symbol `VNMID` matrix restored as an executable contract for a later exact
design PASS. It authorizes no tests, fixtures, network calls, production code, or source-chain
entry now. Every fixture is synthetic and contains no broker row or live payload.

| Future case | RED assertion / synthetic fixture | Release assertion |
|---|---|---|
| Selector and zero-network | Exact/lower/padded `VNMID` normalize once; wrong-sector, proxy, unknown, punctuation, non-string, internal-space, and non-D1 fail typed before transport. Current deny-only strict and explicit stitched calls make zero calls. | Existing selectors, errors, imports, snapshots, and deny-only behavior remain unchanged. |
| Identity and routing | For each `vps_index`, `ssi_index`, and `vndirect_index`, wrong/missing symbol, exchange, index type, interval, point scale, timezone, or provenance fails closed; request echo is insufficient. | Same-provider identity/history binding is mandatory; VPS/SSI observations are not promoted to complete identity. |
| Status/MIME/metadata | Wrong status, redirect, complete MIME (including a colon-suffixed MIME/value), effective host/path, or missing metadata fails closed; JSON-shaped body with wrong full MIME fails. | Legacy 3-arg GET/4-arg POST string stubs remain valid; private metadata is not exported. |
| Points/D1/RAW/volume | Non-finite points, wrong D1, timestamp/date errors, unknown RAW, missing/null/wrong-type/misaligned/negative/non-finite volume, and missing-volume-to-zero are RED. | Only finite provider-reported points with documented D1/RAW/time/volume are released. |
| Coverage/calendar | Fixed boundary, official calendar/horizon, gaps, duplicates/conflicts, invalid rows, page/total/cursor, capped/recent-only, and out-of-horizon cases are distinct. Out-of-horizon is typed `COVERAGE_GAP`/`NOT_SERVED`, never false absence. | Fixed, arbitrary, and `PARTIAL` contracts remain separate; no fabricated or silently repaired bars. |
| Strict atomicity | Failed capable source gives the next source the same whole range; incapable source consumes zero calls/attempts. No date merge, fill, strict-to-stitched fallback, or partial result. | Strict result is whole-window atomic and canonical. |
| Stitched atomicity/time | Nine segments share one ledger; any failure aborts all output. Seam duplicates/conflicts and provenance are RED. With UTC-aware synthetic segment times, assert `fetched_at_utc=max(segment.fetched_at_utc)`; missing/tz-naive time is `timestamp_invalid` and aborts; no clock fabrication. | Explicit D1 stitched result only, with deterministic aggregate retrieval time and no false full span. |
| Budget/diagnostics | Bounds, atomic reservations, 3/6 strict and 27/54 stitched caps, prior-attempt preservation, no sentinel/partial, bounded names/reasons/warnings, and non-synthetic `diagnostics_truncated` are RED. | Exact `BudgetGlobalExhausted` and finite grammar pass. |
| Observer/public release | Private observer fires once per physical dispatch including retry; metadata absence fails metadata-sensitive qualification; legacy stubs remain accepted. | API/AI/tutorial/architecture docs, snapshots, `CHANGELOG`, blacklist/secret/diff/build/import, focused tests, and full merged suite pass together. |

The current completion path remains docs-only SOURCE-GAP; no row above is a current test or code
claim.

## 9. Conjunctive reopen criteria and completion disposition

Reopen to TDD only when **all** conditions below pass for one named provider unit; evidence
from another provider cannot fill a missing cell:

1. **Identity:** the same provider's response-backed metadata binds exact `VNMID` to the
   intended HOSE index type, D1 capability, local timezone/session convention, point scale,
   and producer provenance; request echo alone is insufficient.
2. **Coverage:** the same unit documents the requested inclusive `2018-08-13..2026-08-19`
   boundaries, an official trading-calendar/horizon rule for arbitrary ranges, and internal
   date completeness. No unexplained duplicate/conflicting date, invalid OHLC, or silent
   truncation remains. A non-trading literal boundary must be handled by the explicit calendar
   contract, not fabricated.
3. **Semantics:** the response provides finite index points, `AdjustmentPolicy.RAW` is justified
   by provider evidence, timestamps have a documented timezone/date convention, and aligned
   non-null volume has a documented unit/meaning. Missing/null/malformed volume fails the whole
   attempt; a provider-reported integer zero remains zero.
4. **Transport/runtime:** exact full MIME, status, redirect, WAF/session, pagination, rate,
   retry, and cache behavior are documented and stable. Any cookie requirement is explicit and
   lawful; no hidden cookie/session reuse or retry loop is allowed.
5. **Legal/reuse:** written provider/HOSE permission covers automated retrieval, OSS use,
   caller-facing return, storage/cache, attribution, commercial restrictions, rate policy, and
   redistribution of the selected fields. Public reachability and personal-use terms are not
   substituted for that permission.
6. **Budget/diagnostics:** the one request ledger, strict whole-window failover, explicit
   stitched atomicity, finite physical/logical caps, no-false-absence diagnostics, and complete
   sanitization are specified and pass synthetic offline tests and merged-tree gates.

If no provider satisfies all six gates, the completion action is docs-only: commit these two
source/design artifacts, request exact-SHA design review, and after PASS publish the exact
approved anchor, post a clean `SOURCE-GAP`/no-capability resolution, close and re-read #214.
That path never authorizes RED tests, production code, a source-chain entry, or a capability
claim. This review is currently on that path.
