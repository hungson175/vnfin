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

That browser-UA dependency is an access/transport fact, not evidence of public automation
permission. No `Authorization` header, API key, login, browser session, challenge solving,
proxy bypass, or private route was used. SSI and VNDirect emitted response cookies in the
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
(`VNMID` and the independently audited `VNREAL`) × two routes (history and identity):

| Ledger scope | Logical route operations | Physical HTTP dispatches | Retries | Parallelism | Retained payload |
|---|---:|---:|---:|---|---|
| `VNMID` cell in both passes | 12 | 12 | 0 | none | none |
| Whole #213/#214 observation batch | 24 | 24 | 0 | none | none |

Here one logical operation is one planned provider route call, and one physical dispatch is
one actual HTTP request. This is an observation ledger, not a runtime budget or a promise of
future availability. A response cookie, redirect, timeout, WAF behavior, or empty body would
be recorded as an outcome axis, never as proof that historical VNMID data did not exist.

## 4. Fresh VNMID provider matrix

The following values are sanitized shape, metadata, count, date, and header observations. No
OHLC or volume values are reproduced. “Normalized MIME” means the complete `Content-Type`
value after outer whitespace normalization; media-type-only reduction is not allowed.

### 4.1 Qualification summary

| Provider unit | Transport and MIME | Same-provider identity | Fixed-window observation | D1/volume observation | Total technical disposition | Legal/reuse axis |
|---|---|---|---|---|---|---|
| VPS `VNMID` history + symbol | History `200`, no redirect, effective host/path unchanged, `application/json; charset=utf-8`; identity `200`, same normalized MIME; no auth challenge observed | Identity response was response-backed: `symbol=ticker=name=VNMID`, `timezone=Asia/Ho_Chi_Minh`, `session=0900-1500`, `has_daily=true`, `has_no_volume=false`, `pricescale=100`, `pointvalue=1` | History had 1,649 rows and 1,615 distinct local dates; 34 duplicate dates; first `2020-03-03`, last `2026-08-19`; requested start absent, end present | Bare UDF shape with aligned `t/o/h/l/c/v`, `s=ok`; volume was present, aligned, finite, and non-negative in the bounded check; the quality pass flagged four invalid OHLC observations and 33 conflicting duplicate dates plus one identical duplicate | **COVERAGE_GAP** | `LEGAL_GAP` independently; no automated/reuse grant found |
| SSI `VNMID` history + symbol | History `200`, no redirect, effective host/path unchanged, `application/json; charset=utf-8`; identity `200`, same normalized MIME; no auth challenge observed; response cookie seen and discarded | Identity response was response-backed: `symbol=ticker=name=VNMID`, `exchange=HOSE`, `listed_exchange=HOSE`, `type=Chỉ số`, `timezone=Asia/Ho_Chi_Minh`, `has_daily=true`, `has_no_volume=false`, `pricescale=100`, `pointvalue=1`; no session value is claimed from this observation | Enveloped history had 1,915 rows and 1,915 distinct local dates; first `2018-12-11`, last `2026-08-19`; requested start absent, end present; `nextTime=null` | Outer `{code,data,message,status}` was `SUCCESS`/`ok`; inner UDF status was `s=ok`; aligned `t/o/h/l/c/v`; volume was present and aligned; no invalid OHLC observation was flagged in this bounded quality pass | **COVERAGE_GAP** | `LEGAL_GAP` independently; public no-login access is not redistribution permission |
| VNDirect `VNMID` history + symbol | History `200`, no redirect, effective host/path unchanged, full normalized MIME `text/plain;charset=UTF-8` while the body was JSON-shaped; identity `404`, `application/json`; response cookie seen and discarded | History body did not echo a symbol; same-owner identity route yielded no usable identity record | Bare UDF-shaped history had 2,003 rows and 2,003 distinct local dates; first `2018-08-13`, last `2026-08-19`; both requested boundaries present | `s=ok`; aligned `t/o/h/l/c/v`; volume was present and aligned in the bounded check; no provider identity/scale/point metadata was available | **IDENTITY_GAP** | `LEGAL_GAP` independently; no route-specific permission found |

The date/count observations are bounded results at one observation time. They do not prove
that an arbitrary range, future response, or exchange calendar has the same shape. The VPS
and SSI units fail the requested fixed start, while VNDirect lacks response-backed identity.
Even a technically clean unit would still fail the end-to-end gate without written rights.
No provider therefore qualifies for TDD.

### 4.2 Route, envelope, identity, and semantic cells

| Provider | History envelope and selector binding | Identity/owner binding | Point/time/volume evidence | Unresolved seam |
|---|---|---|---|---|
| VPS | Bare object with `symbol`, `s`, `t`, `o`, `h`, `l`, `c`, `v`; the observed body echoed `VNMID`; daily selector `D` | Same-owner symbol route returned the exact requested token and index-like metadata; this is stronger than a request-only label but does not prove HOSE ownership or rights | `type` is not claimed from the identity response; `pricescale=100`, `pointvalue=1`, and `has_daily=true` support points/D1 interpretation; timestamps were converted to `Asia/Ho_Chi_Minh`; `session=0900-1500`; raw `v` was present/aligned | Coverage starts in 2020; duplicate/conflicting dates and invalid observations prevent clean full-span acceptance; provider did not document volume units or adjustment policy in this observation |
| SSI | Outer `{code,data,message,status}` with inner `t`, `o`, `h`, `l`, `c`, `v`, `nextTime`; history has no symbol field; daily selector `1D` | Same-owner symbol route returned `VNMID`, `HOSE`, `Chỉ số`, daily capability, timezone, and point scale; the history-to-metadata binding must be enforced, not inferred from the request string | `pricescale=100`, `pointvalue=1`, `has_daily=true`, `has_no_volume=false`; timestamps were converted to local dates; volume was present/aligned; no session claim | Coverage starts in 2018-12; `nextTime=null` is not a provider total; no provider documentation establishes internal date completeness, volume unit, RAW adjustment, or rights |
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

- **Redirect:** no redirect was observed for the six VNMID route calls; effective host/path
  remained the requested provider route. This is not a permanent redirect guarantee.
- **MIME:** the full normalized values were `application/json; charset=utf-8` for VPS/SSI
  history and identity, and `text/plain;charset=UTF-8` for VNDirect history. VNDirect identity
  was `404` with `application/json`. A future route validator must parse the complete value and
  reject an unexpected status or MIME; it must not accept a JSON-shaped body as permission to
  ignore the header.
- **Authentication/session:** no login, API key, authorization header, or pre-existing session
  was used. SSI and VNDirect emitted cookies, which were discarded. Cookie issuance is not a
  requirement to reuse the cookie and is not evidence of public redistribution rights.
- **Browser/WAF:** the browser UA was required by the bounded transport convention. No WAF
  challenge was retained or solved. A successful response with that UA does not establish a
  stable automation policy; an HTML/challenge response, 403, timeout, or connection failure
  is a transport diagnostic, not a historical absence.
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

A missing literal first date may be a non-trading boundary in another request, but the requested
VNMID start is an explicit acceptance boundary here. No official HOSE trading-calendar artifact
was used to reclassify it. Counts are array counts, not provider-declared totals; internal date
completeness remains unproven. An empty, capped, recent-only, or failed result is a bounded
outcome and never evidence that VNMID was historically absent.

The existing explicit stitched shape is calendar-year segmentation, so this requested range
would span nine calendar segments (`2018` through `2026`). A future stitched implementation
would have to:

1. keep D1, points, RAW, canonical VNMID identity, and aligned volume checks per segment;
2. reserve all identity/history/page/retry dispatches from one request-scoped global ledger,
   with no per-segment reset or hidden concurrency;
3. preserve canonical segment producer provenance and fail atomically if any segment is
   missing, identity-inconsistent, conflicting, over budget, or legally unserved;
4. distinguish a fixed-window endpoint result from an arbitrary-range trading-calendar claim;
   weekend/holiday boundaries cannot be filled or silently labeled absent; and
5. remain opt-in and separate from strict whole-window failover. Cross-provider numerical
   agreement cannot repair a missing identity, coverage, unit, or legal axis.

No stitched capability is enabled by this report. If no provider unit qualifies, both strict and
stitched chains remain empty and the correct disposition is documentation-only source-gap
closure.

## 7. Future global-budget and diagnostic design (not implemented)

This section is a bounded reopen design, not an implementation recipe authorized for this
commit. It makes logical/physical accounting and exhaustion deterministic:

### 7.1 One atomic request ledger

A future request owns one ledger for its entire strict or stitched call. It tracks at least
`logical_attempts`, `physical_dispatches`, `physical_reserved`, `segments_started`, and
`retries`, with private integers only. A single deterministic scheduler performs reservations;
there is no hidden parallelism.

For a range covering nine calendar segments, the initial design budget is:

- at most **3 logical provider attempts per segment**, hence **27 logical attempts for the
  whole request**; and
- at most **2 physical calls per logical attempt** (same-owner identity then history), hence
  **54 physical dispatches for the whole nine-segment request**.

There is **no retry allowance** in this source-gap design. A future provider-specific retry
policy must be approved separately and must reserve each retry as a new physical dispatch; it
may not reset a segment or extend the cap. An identity failure may consume only its actual one
physical call; the history call is never dispatched after a failed identity check. A page or
cursor call, if ever authorized, is another physical dispatch and must fit the same ledger;
there is no unbounded page loop. This design admits no page/cursor dispatch for the current
source-gap unit; adding pagination, redirects, retries, or a provider rate policy requires a
new reviewed finite formula. This source-gap note makes no arbitrary-range scheduler or
calendar-cap promise; any such range requires a fresh trading-calendar, segment-cap, and API
design review. The nine-segment request never receives a per-segment budget reset.

A reservation occurs atomically immediately before a logical attempt or physical dispatch:
if the next reservation would exceed the precomputed cap, the public strict/stitched call raises
the typed future `BudgetGlobalExhausted` (`VnfinError`) with all prior sanitized attempts and
bounded counters before making that call; it returns no sentinel or partial `PriceHistory`. A
logical `SourceAttempt` is created only for an actual capable provider attempt; a physical counter
is incremented only after its HTTP dispatch. Capability skips reserve neither budget and create no
attempt. The scheduler never publishes a partial or false full-span result after exhaustion.

Strict mode uses one whole-window operation: a failed capable provider receives one logical
attempt and the next provider receives the same window, with no date-level merge. Stitched mode
is explicit: each segment may use the ordered failover chain, but every segment and every
physical operation consumes the same request ledger, and the final result is atomic.

### 7.2 Fail-closed diagnostic axes

Diagnostics must preserve separate typed axes rather than collapse all failures into “not
served”:

- **transport:** `http_status_unexpected`, `redirect`, `mime_mismatch`, `timeout`,
  `connection_error`, `auth_required`, `waf_challenge`, `rate_limited`;
- **identity:** `identity_missing`, `identity_mismatch`, `wrong_exchange`, `wrong_index_type`,
  `wrong_interval`, `provenance_mismatch`;
- **outcome:** `empty_result`, `coverage_gap`, `coverage_partial`, `timestamp_invalid`,
  `duplicate_conflict`, `point_invalid`, `volume_missing`, `volume_invalid`, `adjustment_unknown`,
  `budget_exhausted`, `legal_gap`, `not_served`; and
- **accounting:** actual logical-attempt count, actual physical-dispatch count, and retry count,
  each bounded and independent. A synthetic attempt must never represent a budget ceiling.

The public token vocabulary, lengths, warning count, and source-name fields must be finite and
allow-listed before any future code is written. URLs, query strings, response bodies, cookies,
credentials, raw exceptions, HTML, provider text, and unbounded dates/count lists must be
sanitized or omitted. `diagnostics_truncated` may be a bounded warning only; it is never an
invented `SourceAttempt` and never evidence of historical absence.

The following rules prevent false absence:

- a `404` identity route is `identity_missing`, not `NOT_SERVED` for the index itself;
- an empty/partial/recent-only/capped response is a bounded outcome, not proof of no historical
  data;
- 403/429/5xx, timeout, redirect, malformed MIME, WAF/challenge, and rate-policy unknown are
  transport/policy outcomes, not `COVERAGE_GAP` unless a valid provider response establishes a
  bounded coverage boundary;
- a response that lacks a symbol or provider identity cannot be repaired by the request
  parameter, another source, a current constituent list, or a content fingerprint; and
- `NOT_SERVED` or source-gap closure is a conclusion only after the finite candidate set has
  been attempted or mechanically skipped with an explicit reason, all axes are recorded, and
  no candidate has an unresolved transport/identity state that could be mistaken for absence.

## 8. Conjunctive reopen criteria and completion disposition

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
4. **Transport/runtime:** exact full MIME, status, redirect, WAF/UA/session, pagination, rate,
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
