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

| Provider unit | Fresh response-backed identity | Requested fixed-window observation | Semantics/quality | Decision |
|---|---|---|---|---|
| VPS history + same-owner symbol route | `VNMID` echo plus `symbol=ticker=name=VNMID`; timezone/session/daily and point-scale metadata | 1,649 rows / 1,615 local dates; first `2020-03-03`, last `2026-08-19`; requested start absent; 34 duplicate dates, including 33 conflicts | Aligned `t/o/h/l/c/v`; provider status `s=ok`; volume present/aligned; four OHLC quality flags in the bounded pass | `COVERAGE_GAP` |
| SSI history + same-owner symbol route | `VNMID`, `HOSE`, `listed_exchange=HOSE`, `type=Chỉ số`; daily/timezone/point-scale metadata | 1,915 rows / 1,915 dates; first `2018-12-11`, last `2026-08-19`; requested start absent; `nextTime=null` | `SUCCESS`/`ok` envelope and `s=ok`; aligned volume; no invalid OHLC flag in bounded pass | `COVERAGE_GAP` |
| VNDirect history + same-owner symbol route | History has no symbol; identity route returned `404`; no usable response identity | 2,003 rows / 2,003 dates; both requested boundaries present | `s=ok`, aligned volume, full MIME `text/plain;charset=UTF-8`; no same-provider scale/type proof | `IDENTITY_GAP` |

Legal/reuse is a separate `LEGAL_GAP` for all three. No source qualifies end-to-end. HTTP
success, a request echo, exact dates, or technical shape cannot substitute for the missing
permission and independent cells. The correct current status is source-gap closure, not
“qualified for TDD” or “qualified partial.”

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

The fixed observation is only the literal requested window. A future implementation must not
turn these observations into a blanket arbitrary-range claim:

- the requested VNMID start is absent from VPS and SSI; all three observed the requested end;
- VNDirect includes both literal boundaries but has no response-backed identity;
- no official trading-calendar file was used to reclassify absent dates; and
- counts are observed array counts, not provider-declared totals.

Arbitrary ranges require a separately reviewed trading-calendar/horizon contract. A weekend or
holiday endpoint may legitimately have no row, but the implementation must distinguish a
calendar boundary from an unexplained gap and must not fabricate a bar. Internal missing dates,
duplicates, conflicts, invalid points, capped windows, and recent-only responses are explicit
outcomes, not silently repaired data.

The existing explicit stitched path would cover nine calendar segments for this window
(`2018`–`2026`). If later authorized, it must remain D1-only, validate each segment's exact
VNMID/points/RAW/volume identity, preserve canonical segment provenance, and fail atomically
when any segment fails. Every segment's identity/history/page/retry dispatch consumes the same
request-scoped ledger. It cannot silently mix sources for a strict call, use another index or
constituent basket, or convert a partial result into a full-span claim.

## 6. Global budget, accounting, and exhaustion — design only

The future scheduler has one atomic ledger for the complete strict or stitched request. It
tracks logical adapter attempts separately from physical HTTP dispatches and reserves before
each dispatch. No hidden concurrency, per-segment reset, unbounded pagination, or retry storm
is allowed.

For the nine-segment requested window:

- maximum logical attempts: `3 providers × 9 segments = 27`;
- maximum physical dispatches: `2 route calls × 27 attempts = 54` (same-owner identity then
  history); and
- retry allowance in this design: **zero**. Any later retry policy needs a new review and every
  retry is another physical reservation under a finite cap.

An identity failure may consume one actual physical call and must not dispatch history. A page or
cursor, if ever authorized, is an additional physical dispatch under the same ledger, not a
free call. This source-gap design admits no page/cursor dispatch for the current source-gap unit;
adding pagination, redirects, retries, or a provider rate policy requires a new reviewed finite
formula. This source-gap note makes no arbitrary-range scheduler or calendar-cap promise; any
such range requires a fresh trading-calendar, segment-cap, and API design review. The
nine-segment request never receives a per-segment budget reset.

Reserve a logical attempt atomically before starting an eligible source. Reserve one physical
slot immediately before each HTTP dispatch and increment the consumed counter only after that
dispatch. If the next reservation would exceed the cap, emit typed `budget_exhausted` before
network and publish no partial/false full-span result. The public call raises the typed future
`BudgetGlobalExhausted` (`VnfinError`) with all prior sanitized attempts and bounded counters; it
returns no sentinel or partial `PriceHistory`. Capability skips reserve neither count. Only
actual capable attempts create attempt records; `diagnostics_truncated` is a warning token, never
a synthetic attempt. Any pagination, redirect, retry, or rate-policy change requires a new
reviewed finite formula.

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

Future diagnostics must retain four independent axes:

- transport: `http_status_unexpected`, `redirect`, `mime_mismatch`, `timeout`,
  `connection_error`, `auth_required`, `waf_challenge`, `rate_limited`;
- identity: `identity_missing`, `identity_mismatch`, `wrong_exchange`, `wrong_index_type`,
  `wrong_interval`, `provenance_mismatch`;
- outcome: `empty_result`, `coverage_gap`, `coverage_partial`, `timestamp_invalid`,
  `duplicate_conflict`, `point_invalid`, `volume_missing`, `volume_invalid`,
  `adjustment_unknown`, `budget_exhausted`, `legal_gap`, `not_served`; and
- accounting: actual logical-attempt, physical-dispatch, page, and retry counts.

All public tokens, warning lengths, warning counts, source names, and bounded counts must be
allow-listed and mechanically capped. No URL, query, body, cookie, credential, raw exception,
HTML, provider prose, or unbounded date list may be exposed. A 404 identity route is
`identity_missing`, not proof that VNMID was never served. Empty/recent-only/capped results,
403/429/5xx, timeout, WAF challenge, wrong MIME, and rate-policy unknown are bounded failures,
not historical absence. `NOT_SERVED`/source-gap closure is allowed only after the finite
candidate set is explicitly exhausted or skipped and unresolved transport/identity states are
not mislabeled as absence.

## 9. Conjunctive reopen criteria and delivery

TDD may begin only if one named VPS, SSI, or VNDirect unit satisfies all of these in a fresh
review:

1. same-provider response identity binds exact VNMID, HOSE/index type, D1, points, timezone,
   session, and producer provenance;
2. the exact requested span and internal dates are explained by an official calendar/horizon,
   with no unresolved duplicate/conflict/invalid-row or silent cap;
3. points, RAW adjustment, timestamp, and aligned non-null volume semantics are documented;
4. full MIME/status/redirect/UA/WAF/session/rate/retry/pagination/cache behavior is bounded;
5. written legal/reuse permission covers automated retrieval and caller-facing redistribution;
6. strict whole-window and explicit stitched atomic contracts use one finite global ledger and
   sanitized no-false-absence diagnostics; and
7. synthetic RED tests, docs/API compatibility, blacklist/secret/diff/build, and full merged-tree
   gates pass after a later exact design PASS.

If any one condition remains open, keep the chain empty. The current completion path is
**docs-only SOURCE-GAP**: request exact-SHA design review, and only after approval publish the
exact docs anchor, post a clean no-capability resolution, and close/re-read #214. This note does
not authorize RED tests, production code, push, or close.
