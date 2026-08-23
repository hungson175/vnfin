# #214 design note — VNMID daily index-value history

**Issue:** #214
**Date:** 2026-08-23 (UTC+7)
**Phase:** `SOURCE_DESIGN` / docs-only
**Builder:** `vnfin-oss`
**Canonical selector:** `VNMID`
**Requested window:** `2018-08-13..2026-08-19` inclusive
**Current capability:** none; VNMID remains deny-only and strict/stitched calls are typed,
zero-network failures
**Disposition:** **SOURCE-GAP CLOSURE**
**Review gate:** exact-SHA design review is required before any RED test, production change,
push, or close

The companion evidence is
[`docs/research/2026-08-23-vnmid-index-history-source-vetting.md`](../docs/research/2026-08-23-vnmid-index-history-source-vetting.md).
This note binds the future design boundary but authorizes no implementation.

## 1. Product and clean-room boundary

The only requested primitive is the existing strict index-value entry point:

```python
index_history(
    "VNMID",
    date(2018, 8, 13),
    date(2026, 8, 19),
    interval=Interval.D1,
)
```

A future result would contain daily OHLCV **index points**, not an equity price in VND. It
would not expose a constituent basket, proxy, ETF, current-membership substitution, signal,
backtest, archive, cache, or new helper. `index_history_stitched()` is an explicit D1-only
future path and is never a silent strict fallback. VNMID evidence is independent of VNREAL;
no symbol, identity, coverage, or legal cell cross-qualifies the other.

Before research, `docs/vnstock-blacklist.md` was read and the exact search exclusion was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited or derivative material was used. Only official HOSE/provider terms and
provider-owned no-login observations are used in the companion report. No raw provider data,
query-bearing URL, cookie, token, live bar/value, screenshot, or digest is stored.

The annotated `v0.2.0` tag is the exact historical commit
`2fe50df4f27064140ff9f7a680227a2b337ec74a`. It predates the later private index namespace
registry. It is recorded only as a tag-vs-current boundary: current master recognizes VNMID
for price-path denial but does not allow value history; neither the tag nor current code grants
VNMID capability.

## 2. Evidence decision

| Provider unit | Response-backed observations (not complete identity qualification) | Requested fixed-window observation | Semantics/quality | Total ordered disposition |
|---|---|---|---|---|
| VPS history + same-owner symbol route | Echo plus `symbol=ticker=name=VNMID`; timezone/session/daily/scale fields observed, but no complete provider-backed exchange/index-type binding for history | 1,649 rows / 1,615 local dates; first `2020-03-03`, last `2026-08-19`; requested start absent; 34 duplicate dates, including 33 conflicts | Aligned `t/o/h/l/c/v`; `s=ok`; volume present/aligned; four OHLC quality flags | `(IDENTITY_GAP, PARTIAL, COVERAGE_GAP, TIMESTAMP_GAP, VOLUME_GAP, ADJUSTMENT_GAP, PAGINATION_GAP, TRANSPORT_INCONCLUSIVE, LEGAL_GAP, RATE_POLICY_GAP)` |
| SSI history + same-owner symbol route | `VNMID`, `HOSE`, `listed_exchange=HOSE`, `type=Chỉ số`; metadata observed, but complete history-to-identity binding and rights are not proven | 1,915 rows / 1,915 dates; first `2018-12-11`, last `2026-08-19`; requested start absent; `nextTime=null` | `SUCCESS`/`ok` envelope and `s=ok`; aligned volume; no invalid OHLC flag | `(IDENTITY_GAP, PARTIAL, COVERAGE_GAP, TIMESTAMP_GAP, VOLUME_GAP, ADJUSTMENT_GAP, PAGINATION_GAP, TRANSPORT_INCONCLUSIVE, LEGAL_GAP, RATE_POLICY_GAP)` |
| VNDirect history + same-owner symbol route | History has no symbol; identity route returned `404`; no usable response identity | 2,003 rows / 2,003 dates; both requested boundaries present | `s=ok`, aligned volume, full MIME `text/plain;charset=UTF-8`; no same-provider scale/type proof | `(IDENTITY_GAP, PARTIAL, COVERAGE_GAP, TIMESTAMP_GAP, VOLUME_GAP, ADJUSTMENT_GAP, PAGINATION_GAP, TRANSPORT_INCONCLUSIVE, LEGAL_GAP, RATE_POLICY_GAP)` |

The stable ordered disposition vocabulary is `IDENTITY_GAP`, `PARTIAL`, `COVERAGE_GAP`,
`TIMESTAMP_GAP`, `VOLUME_GAP`, `ADJUSTMENT_GAP`, `PAGINATION_GAP`, `TRANSPORT_INCONCLUSIVE`,
`LEGAL_GAP`, and `RATE_POLICY_GAP`. Each provider receives the complete tuple `(IDENTITY_GAP, PARTIAL, COVERAGE_GAP, TIMESTAMP_GAP, VOLUME_GAP, ADJUSTMENT_GAP, PAGINATION_GAP, TRANSPORT_INCONCLUSIVE, LEGAL_GAP, RATE_POLICY_GAP)`
with no omitted axis; it is not shortened to the first failure. VPS and SSI are partial response
observations, not complete identity qualification, and VNDirect retains its identity gap. All
three remain unqualified. HTTP success, request echo, exact dates, or technical shape cannot
substitute for missing permission or independent cells. The current status is source-gap closure,
not “qualified for TDD” or “qualified partial.”

## 3. Source-unit contract

One qualification unit is exactly:

```text
(provider owner, VNMID namespace, provider history route, same-owner identity route,
D1 selector, points/RAW/time/volume semantics, fixed-window coverage, transport policy,
rate/retry/cache policy, and written legal/reuse permission)
```

The provider routes are named without query strings:

- VPS: history `/tradingview/history`, identity `/tradingview/symbols`, D1 token `D`;
- SSI: history `/statistics/charts/history`, identity `/statistics/charts/symbol`, D1 token `1D`;
- VNDirect: history `/dchart/history`, identity `/dchart/symbol`, D1 token `D`.

A future accepted result must be bound to the same provider unit. The request parameter is not
identity. A missing identity response, wrong exchange/type, wrong symbol, wrong MIME/status,
unknown adjustment policy, incomplete coverage, or legal gap fails that unit; another provider
cannot repair it. The provider source token and public `PriceHistory.source` must be canonical
and finite; raw provider names, URLs, response text, cookies, and exceptions cannot leak into
public diagnostics.

The companion observation used a browser-like UA as a bounded transport choice. No no-UA control
was run, so necessity is untested; this is not permission or a stable automation contract. SSI and
VNDirect cookies were discarded and no session reuse is designed.

## 3.1 Future private response-metadata seam (design only)

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
  expected status, the complete MIME value, exact effective host/path, and redirect policy. A
  JSON-shaped body cannot override a status/full-MIME/effective-route mismatch.

This seam preserves the current three-/four-argument injection boundary and makes metadata absence
an explicit transport/identity gap instead of inferred success. It is not implemented here.

### 3.2 Bounded observation ledger

The VNMID observation had two passes over three providers × history/identity routes: 6 route cells per pass × two passes = **12 logical / 12 physical** VNMID operations. The combined #213/#214
batch is **24 logical / 24 physical**. One logical route cell equals one physical HTTP dispatch;
there were no retries, redirects, hidden parallel calls, or retained payloads. These are bounded
research observations, not runtime budget promises.

## 4. Future registry and API boundary — design only

No registry or production file is changed by this commit. If a later evidence packet closes the
conjunctive gate:

1. Add `VNMID` exactly once to the private `_VALUE_HISTORY_INDICES` allow-list. Keep it in
   `_KNOWN_INDEX_IDENTIFIERS` so `prices.history("VNMID", ...)` remains a typed zero-network
   rejection. Do not alter any existing served or deny-only index.
2. Normalize padded/lowercase valid selectors once. Malformed, punctuation, non-string, and
   internal-space selectors fail typed before network. VNMID is request-capable only for exact
   `Interval.D1`; non-D1, proxy, or unknown selectors fail before `apply_interval` and network.
3. Apply a separate per-source capability predicate to the default and injected chains. An
   incapable source is skipped with zero physical calls, consumes no logical attempt budget,
   and creates no `SourceAttempt`.
4. Keep the default source order VPS → SSI → VNDirect unless a fresh review justifies a
   VNMID-specific order. Strict failover is whole-window only: the next source sees the same
   range, with no date-level merge, fill, interpolation, or strict-to-stitched fallback.
5. Return only a fully validated `PriceHistory` with canonical VNMID identity,
   `Interval.D1`, `AdjustmentPolicy.RAW`, `value_unit=currency="points"`, timezone-aware
   timestamps, provider-reported volume, and bounded sanitized diagnostics. Do not synthesize
   volume or claim official HOSE production identity.

The current deny-only behavior and empty source chain are preserved until a fresh design PASS
and a later implementation review.

## 5. Fixed-window, arbitrary-range, and stitched contract

The fixed observation is only the literal reviewed window `2018-08-13..2026-08-19`:

- the requested VNMID start is absent from VPS and SSI; all three observed the requested end;
- VNDirect includes both literal boundaries but has no response-backed identity;
- no official trading-calendar file was used to reclassify absent dates; and
- counts are observed array counts, not provider-declared totals.

A future source must declare its supported horizon and official trading-calendar rule before
accepting arbitrary ranges. An out-of-horizon request is typed `COVERAGE_GAP`/`NOT_SERVED` before
network, never an empty success, zero-volume fill, or false absence. `PARTIAL` is allowed only
when response-backed first/last boundaries and the official calendar explain the boundary; it
must expose `partial_start_coverage` or `partial_end_coverage` and cannot become `FULL`. A
weekend/holiday endpoint is distinct from an unexplained missing date. Internal missing dates,
duplicates, conflicts, invalid points, capped windows, and recent-only responses are explicit
outcomes and never silently repaired.

The explicit stitched path would cover nine calendar segments for this window (`2018`–`2026`). If
later authorized, it remains D1-only, validates each segment's exact VNMID/points/RAW/volume
identity, preserves canonical segment provenance, and fails atomically when any segment fails.
Every segment's identity/history/page/retry dispatch consumes the same request-scoped ledger. It
cannot silently mix sources for strict calls, use another index or basket, or convert a partial
result into a full-span claim. The aggregate must set
`fetched_at_utc = max(segment.fetched_at_utc)` over successful segments; a missing or tz-naive
segment timestamp is `timestamp_invalid` and aborts the aggregate.

## 6. Global budget, accounting, and exhaustion — design only

This is the bounded, deterministic reopen contract, not an implementation authorization. Strict
and stitched calls own one request-scoped ledger and one single deterministic scheduler.
Reservations are atomic and checked before network. Capability skips reserve zero logical or
physical budget and create no `SourceAttempt`.

### 6.1 Exact request budgets and `BudgetGlobalExhausted`

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

## 7. Daily points, volume, time, MIME, and legal gates

A later technical winner must prove every field on the same provider unit:

- **Points:** response-backed index type plus provider scale/point metadata; no VND price
  scaling. `value_unit` and legacy `currency` are both `points`.
- **D1:** exact provider token (`D` or `1D`) and response-backed daily capability; no silent
  resampling or intraday-to-daily conversion.
- **RAW:** provider evidence that the series is unadjusted; route naming alone is insufficient.
- **Time:** documented epoch/date/session convention, timezone-aware `Asia/Ho_Chi_Minh`
  normalization, ordered unique local session dates, and an official calendar/horizon rule.
- **Volume:** an aligned provider-reported `v` field with documented unit/meaning. Missing,
  null, wrong-type, misaligned, negative, non-finite, or malformed volume fails the whole
  attempt; a present integer zero remains zero. No missing-volume-to-zero conversion.
- **MIME/transport:** full `Content-Type` after outer normalization; expected status, redirect,
  host/path, UA/WAF/session policy, and no unapproved cookie reuse. A JSON-shaped body cannot
  override a MIME or status mismatch.
- **Rate/retry/cache:** explicit route policy and finite runtime budgets. Unknown quota is not
  unlimited; no automatic retry, storage, or cache is lawful without written terms.
- **Legal/reuse:** written permission must cover automated access, OSS use, caller-facing return,
  storage/cache, attribution, commercial restrictions, rate limits, UA/session handling, and
  redistribution. VPS terms are at [vps.com.vn/dieu-khoan-su-dung](https://vps.com.vn/dieu-khoan-su-dung);
  SSI terms at [ssi.com.vn/dieu-khoan-dich-vu](https://www.ssi.com.vn/dieu-khoan-dich-vu);
  VNDIRECT terms at [vndirect.com.vn/dieu-khoan-su-dung](https://www.vndirect.com.vn/dieu-khoan-su-dung/).
  None closes this gate today.

## 8. No-false-absence diagnostics

The exact future public diagnostic grammar is finite and fail-closed. `SourceAttempt` retains
`name: str`, `ok: bool`, and `reason: str`; canonical names are only `vps_index`, `ssi_index`,
and `vndirect_index`. Arbitrary injected source names are rejected or skipped before dispatch.
`reason` must match `^[a-z][a-z0-9_]{0,47}$` and belong to this exact allow-list:

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

Attempts are capped at 3 entries for strict mode and 27 entries across one nine-segment stitched
call. `ok` is true only for reason `ok`. Warning tuples are capped at 32 entries per strict call
or segment and 64 for a stitched aggregate. Each warning is ASCII, at most 64 characters, and
must be one of:

```text
stitched_multi_source
partial_start_coverage
partial_end_coverage
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

## 9. Future per-symbol RED/release matrix — `VNMID` (design-only)

This matrix is future-only and executable only after a fresh exact-SHA design PASS. It authorizes
no RED tests, fixtures, network calls, production code, source-chain entry, push, or close in this
commit. All fixtures are synthetic and per-symbol; no VNREAL evidence is reused.

| Future `VNMID` case | Required RED fixture/assertion | Required release gate |
|---|---|---|
| Selector and zero-network | Exact/lower/padded selector positives; wrong sector/proxy/unknown/punctuation/non-string/internal-space/non-D1 failures before network. Current strict and explicit stitched deny-only calls make zero calls. | Existing public errors, imports, served/deny-only selector behavior, and snapshots remain unchanged. |
| Identity and provider routing | Wrong/missing symbol, exchange, index type, D1 token, point scale, timezone, or provenance fails for each canonical role; request echo is insufficient. | Same-provider response identity/history binding is mandatory; VPS/SSI observations are not promoted to complete identity. |
| Status/MIME/metadata | Wrong status, redirect, full MIME, effective host/path, or metadata absence fails closed; JSON-shaped body with wrong complete MIME fails. | Legacy 3-arg GET/4-arg POST string stubs remain valid; private metadata stays unexported. |
| Points/D1/RAW/volume | Non-finite points, wrong interval, timestamp/date errors, unknown RAW, missing/null/wrong-type/misaligned/negative/non-finite volume, and missing-volume-to-zero are RED. | Only finite provider-reported points with documented D1/RAW/time/volume are released. |
| Coverage/calendar/duplicates | Fixed boundary, official calendar/horizon, internal gaps, duplicate/conflicts, invalid rows, page/total/cursor, capped/recent-only, and out-of-horizon cases are distinct. Out-of-horizon is typed `COVERAGE_GAP`/`NOT_SERVED`, never false absence. | Fixed, arbitrary, and `PARTIAL` contracts remain separate; no fabricated or silently repaired bars. |
| Strict atomic failover | Failed capable source gives the next source the same whole range; incapable source consumes zero calls/attempts. No date merge, fill, strict-to-stitched fallback, or partial result. | Strict result is whole-window atomic and canonical. |
| Stitched atomicity/time | Nine segments share one ledger; any failure aborts all output. Seam duplicate/conflict and provenance are RED. UTC-aware synthetic segment times assert `fetched_at_utc=max(segment.fetched_at_utc)`; missing/tz-naive time is `timestamp_invalid` and aborts; no clock fabrication. | Explicit D1 stitched result only, deterministic aggregate time, and no false full span. |
| Budget/diagnostics | Bounds, atomic reservations, 3/6 strict and 27/54 stitched caps, prior-attempt preservation, no sentinel/partial, bounded names/reasons/warnings, and non-synthetic `diagnostics_truncated` are RED. | Exact `BudgetGlobalExhausted` and finite grammar pass. |
| Observer/public release | Private observer fires once per physical dispatch including retry; metadata absence fails metadata-sensitive qualification; legacy stubs remain accepted. | API/AI/tutorial/architecture docs, snapshots, `CHANGELOG`, blacklist/secret/diff/build/import, focused tests, and full merged suite pass together. |

The current completion path remains docs-only SOURCE-GAP; no row above is a current test or code
claim.

## 10. Conjunctive reopen criteria and delivery

TDD may begin only if one named VPS, SSI, or VNDirect unit satisfies all of these in a fresh
review:

1. same-provider response identity binds exact VNMID, HOSE/index type, D1, points, timezone,
   session, and producer provenance;
2. the exact requested span and internal dates are explained by an official calendar/horizon,
   with no unresolved duplicate/conflict/invalid-row or silent cap;
3. points, RAW adjustment, timestamp, and aligned non-null volume semantics are documented;
4. full MIME/status/redirect/WAF/session/rate/retry/pagination/cache behavior is bounded;
5. written legal/reuse permission covers automated retrieval and caller-facing redistribution;
6. strict whole-window and explicit stitched atomic contracts use one finite global ledger and
   sanitized no-false-absence diagnostics; and
7. synthetic RED tests, docs/API compatibility, blacklist/secret/diff/build, and full merged-tree
   gates pass after a later exact design PASS.

If any one condition remains open, keep the chain empty. The current completion path is
**docs-only SOURCE-GAP**: request exact-SHA design review, and only after approval publish the
exact docs anchor, post a clean no-capability resolution, and close/re-read #214. This note does
not authorize RED tests, production code, push, or close.
