# #209 + #210 M1/M5 historical cash-equity source design note

**Date:** 23 August 2026 (UTC+7)
**Packet:** `/home/hungson175/tools/vnfin-oss-reviewer/tasks/209-210-historical-vn-cash-intraday-spec.md`
**Packet commit:** `bff996a`
**Disposition:** **SOURCE-GAP CLOSURE**, independently for M1 and M5
**Implementation status:** no RED tests, production code, push, or issue closure is authorized

This is the exact companion design artifact for
[`docs/research/2026-08-23-vn-cash-m1-m5-history-source-vetting.md`](../docs/research/2026-08-23-vn-cash-m1-m5-history-source-vetting.md).
Issues #209 and #210 share a source audit, but each interval is a separate qualification
unit: M1 evidence never qualifies M5, and M5 evidence never qualifies M1.

## 1. Boundary and clean-room record

The requested public paths remain the existing one-symbol primitives:

```python
prices.history(symbol, interval, start, end, *, max_attempts, http_get, timeout)
```

The requested inclusive window is `2018-08-13..2026-08-19`. This batch does not add a
basket/archive/backtest/helper, historical constituent reconstruction, first-ten helper,
VN30F join, local archive, cross-source stitch, M1-to-M5 synthesis, advice, or signal
behavior. Current/frozen basket choice and downstream slicing remain caller-side.

Before research, `docs/vnstock-blacklist.md` was read. Every web search used exactly:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No blacklisted or derivative material was opened, cited, compared, installed, or used.
Evidence is limited to provider-owned routes and metadata, official provider terms,
official provider documentation, and the official [TradingView UDF
protocol](https://www.tradingview.com/charting-library-docs/latest/connecting_data/UDF/).
Only sanitized structure, counts, bounds, identities, MIME/status, and legal facts are
committed; no raw response, OHLCV value, cookie, screenshot, or payload is committed.

## 2. Bounded evidence and frozen cohort

The direct matrix made exactly one sequential, no-credential IPv4 request for every
candidate, representative symbol, and interval:

| Observation set | Logical calls | Physical calls | Retry/follow-up |
|---|---:|---:|---|
| 5 providers × 8 symbols × M1/M5 | 80 | 80 | none |
| SSI/VPS same-provider identity controls | 16 | 16 | none |
| SSI current VN30 group snapshot | 1 | 1 | none |

The 97 observations used a 25-second transport timeout, no cookies/session reuse, no
parallelism, no pagination follow, and one desktop browser `User-Agent` because the
existing adapters use it. That UA is an observed transport condition, not automation
permission, a rate contract, or a legal grant. The requested local bounds were
`2018-08-13T00:00:00+07:00..2026-08-19T23:59:59+07:00` (Unix
`1534093200..1787158799`). Empty, recent-tail, and failed responses prove only those
bounded observations; none is historical absence.

The SSI no-login group route returned a **current snapshot only** on
`2026-08-23T04:18:57Z`, with `as_of=None`, HTTP 200, full `Content-Type`
`application/json; charset=utf-8`, normalized media type `application/json`,
`SUCCESS`, 30 rows, and 30 unique HOSE cash symbols. The SSI-derived member values
are withheld because the provider terms do not grant publication/reproduction rights.
Only the safe aggregate facts and the
fact that the eight issue-required controls were present are retained. This is not a
historical VN30 membership claim and no all-30 history audit was run because no
candidate passed the source/legal gate.

## 3. Independent source matrix and dispositions

The full per-symbol row/count/boundary tables are in the research artifact. The
following total ledger records exact non-secret parameters, effective host/redirect,
full `Content-Type`, normalized media type, response identity, day/gap coverage, and
all known gap axes without using the failover winner as source evidence. In the
coverage column, `rows; dates; start/end; day-count; gap` means row-count range,
distinct-date range, cells containing each literal boundary, nonzero rows per observed
  day, and non-reproducible cadence-observation range across eight controls. The `g`
  values are private probe annotations only and are excluded from every qualification
  and release gate; they are not a reproducible calendar/session claim.

| Provider / unit | Exact non-secret params (`from=1534093200`, `to=1787158799`) | Effective host / redirect | Status; full `Content-Type`; normalized media type | Response identity | Coverage (`rows; dates; start/end; day-count; gap`) | Pagination / rate | Disposition |
|---|---|---|---|---|---|---|---|
| SSI / M1 | `symbol=<control>; resolution=1` | canonical history host/path; none | 200; `application/json; charset=utf-8`; `application/json` | history symbol absent; same-provider metadata control only | `0–0; 0–0; 0/0; —; 0` | no page/total/cursor; no route-specific rate policy | `TRANSPORT_INCONCLUSIVE + IDENTITY_GAP + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP` |
| SSI / M5 | `symbol=<control>; resolution=5` | same; none | 200; `application/json; charset=utf-8`; `application/json` | history symbol absent; same-provider metadata control only | `0–0; 0–0; 0/0; —; 0` | same | same |
| VNDirect / M1 | `symbol=<control>; resolution=1` | canonical history host/path; none | 200; `text/plain;charset=UTF-8`; `text/plain` | response symbol absent; symbol control 404 | `23164–34823; 128–154; 0/8; 30–228; 20–32` | no page/total/cursor; no route-specific rate policy | `IDENTITY_GAP + COVERAGE_GAP + TIMESTAMP_GAP + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP` |
| VNDirect / M5 | `symbol=<control>; resolution=5` | same; none | 200; `text/plain;charset=UTF-8`; `text/plain` | response symbol absent; symbol control 404 | `5787–7106; 128–154; 0/8; 20–48; 13–19` | same | same |
| VPS / M1 | `symbol=<control>; resolution=1` | canonical history host/path; none | 200; `application/json; charset=utf-8`; `application/json` | response symbol and metadata matched controls | `385–678; 3–3; 0/8; 112–226; 3–15` | no page/total/cursor; no route-specific rate policy | `PARTIAL + COVERAGE_GAP + TIMESTAMP_GAP + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP` |
| VPS / M5 | `symbol=<control>; resolution=5` | same; none | 200; `application/json; charset=utf-8`; `application/json` | response symbol and metadata matched controls | `354–368; 8–8; 0/8; 40–46; 4–5` | same | same |
| Pinetree / M1 | `symbol=<control>; resolution=1` | canonical history host/path; none | 200; `text/plain;charset=UTF-8`; `text/plain` | response symbol absent; negative `nextTime` not a proven cursor | `7489–10131; 45–45; 0/8; 106–226; 5–22` | no proven page/cursor; no route-specific rate policy | `IDENTITY_GAP + COVERAGE_GAP + TIMESTAMP_GAP + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP` |
| Pinetree / M5 | `symbol=<control>; resolution=5` | same; none | 200; `text/plain;charset=UTF-8`; `text/plain` | response symbol absent; negative `nextTime` not a proven cursor | `7489–10131; 45–45; 0/8; 106–226; 5–14`; observed cadence 60 seconds | same; token rejected as native-M5 evidence | same |
| KIS / M1 | `symbol=<control>; resolution=1` | canonical history host/path; none; effective host matched | 500; no usable full header/body; `—` | no response identity or typed bars | `0; 0; 0/0; —; —` | no page/total/cursor; no route-specific rate policy | `TRANSPORT_INCONCLUSIVE + ADJUSTMENT_GAP + LEGAL_GAP + PAGINATION_GAP + RATE_POLICY_GAP` |
| KIS / M5 | `symbol=<control>; resolution=5` | same; none; effective host matched | 500; no usable full header/body; `—` | no response identity or typed bars | `0; 0; 0/0; —; —` | same | same |

The full header is not a normalized media type: successful JSON cells normalize to
`application/json`, and successful JSON bodies served as text normalize to `text/plain`.
The eight issue-provided control names are republished in the research tables; only the
SSI-derived 30-member membership values are withheld. The ledger uses the required
controls and safe aggregate observations without publishing that derived membership.

The mandatory semantic axes are explicit for every unit, even when unresolved:

| Unit | Timestamp unit / timezone / candle label | Price/value unit and scale | Volume unit and accumulation | Adjustment policy / basis |
|---|---|---|---|---|
| SSI / M1 | no history timestamp; metadata advertises `Asia/Ho_Chi_Minh`; candle label unresolved | no bar scale observed; adapter scale is not provider proof | empty arrays; unit/accumulation unresolved | adapter declares `PROVIDER_ADJUSTED`; intraday basis unproven |
| SSI / M5 | same | same | same | same |
| VNDirect / M1 | epoch seconds → `Asia/Ho_Chi_Minh`; 60-second spacing; open/close label unresolved | adapter feed scale `1000` → VND; provider proof unresolved | integer array; unit and incremental/cumulative semantics unresolved | adapter declares `PROVIDER_ADJUSTED`; homogeneity unproven |
| VNDirect / M5 | epoch seconds; `Asia/Ho_Chi_Minh`; 300-second spacing; candle label unresolved | same | integer array; unit/accumulation unresolved | same |
| VPS / M1 | epoch seconds → `Asia/Ho_Chi_Minh`; 60-second spacing; candle label unresolved | adapter feed scale `1000` → VND; provider proof unresolved | integer array; unit and incremental/cumulative semantics unresolved | adapter declares `PROVIDER_ADJUSTED`; homogeneity unproven |
| VPS / M5 | epoch seconds; `Asia/Ho_Chi_Minh`; 300-second spacing; candle label unresolved | same | integer array; unit/accumulation unresolved | same |
| Pinetree / M1 | epoch seconds observed; provider timezone/bar label unresolved; 60-second spacing | adapter raw-VND `scale=1`; provider proof unresolved | floating array; unit and accumulation unresolved | adapter declares `PROVIDER_ADJUSTED`; homogeneity unproven |
| Pinetree / M5 | epoch seconds; timezone/bar label unresolved; observed spacing 60 seconds, not native M5 | same | floating array; unit/accumulation unresolved | same |
| KIS / M1 | no typed timestamp; timezone/candle label unresolved | no typed price/scale | no typed volume | registered `MIXED`; no homogeneous basis |
| KIS / M5 | same | same | same | same |

### 3.1 Observed coverage and semantic controls

- **SSI:** all M1/M5 cells were exact empty `200` observations, not absence proof.
- **VNDirect:** M1/M5 returned aligned integer-volume arrays with 60/300-second
  spacing. Seven mandatory symbols began `2021-11-05`; VPL began `2025-08-29`.
  All ended `2026-08-19`. The response did not prove candle label, volume unit or
  adjustment basis, and did not cover `2018-08-13`.
- **VPS:** response-backed symbol and metadata controls passed, but M1 only covered
  `2026-08-17..2026-08-19` and M5 `2026-08-10..2026-08-19` in the bounded probe.
  Integer volume, VND price scale, and 60/300-second spacing were observed; timestamp
  meaning, volume semantics, adjustment homogeneity, and legal reuse remain gaps.
- **Pinetree:** M1 and M5 both returned 60-second cadence and matching row counts
  from `2026-06-18..2026-08-19`; the `resolution=5` token cannot be relabeled as a
  native M5 series. Volume was floating-point and interval/identity semantics were
  unresolved.
- **KIS:** all target-window cells failed with HTTP 500. Its existing `MIXED`
  adjustment policy is a hard exclusion from the provider-adjusted chain.

No candidate proved all of response-backed identity, exact interval/candle semantics,
real volume unit, homogeneous adjustment, target coverage, bounded pagination, rate
policy, lawful reuse, and sanitized diagnostics for either interval. Therefore neither
M1 nor M5 is `QUALIFIED` or implementation-ready `PARTIAL`; both are **SOURCE-GAP
CLOSURE**.

### 3.2 Legal and runtime posture

No-login reachability is access only. It does not authorize automation, multi-year
backfill, retrying, caching/storage, caller-facing return, attribution, commercial use,
or redistribution.

| Provider | Official legal/runtime finding | Required disposition |
|---|---|---|
| SSI | [Service terms](https://www.ssi.com.vn/dieu-khoan-dich-vu) limit use and reserve publication/reproduction; [FastConnect terms](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments) are a separate keyed/approved product. | Route-specific written permission or licence required. |
| VNDirect | [Datafeed terms](https://datafeed.vndirect.com.vn/term-full) require written approval for copying, distribution, publication, or unauthorized use. | Anonymous chart access is not a Datafeed licence. |
| VPS | [Terms](https://vps.com.vn/dieu-khoan-su-dung) restrict copying, transfer, distribution, storage, and derivatives without written consent. | Written route-specific permission required. |
| Pinetree | Official [provider/contact](https://pinetree.vn/post/dich-vu/lien-he/) identity exists, but no chart-route open-data licence was found; [Stock123 terms](https://pinetree.vn/wp-content/uploads/2019/11/PINETREE-dieu-khoan-su-dung.pdf) are not one. | Request automation, retention, reuse, and redistribution permission. |
| KIS | [Terms](https://kisvn.vn/dieu-khoan-su-dung/) reserve copying/distribution/storage and prohibit commercial website-information use without written consent. | Written permission plus one explicit adjustment mode required. |

The new qualified deep-history chain stays empty. The compatibility-safe choice is **option 3: keep
current runtime behavior and document the source gap**. Preserve the existing
SSI → VNDirect → VPS → Pinetree adjusted chain, keep KIS out because it is `MIXED`,
preserve `max_attempts` and soft partial warnings, and do not reorder D1 or other
intervals. A current partial tail is not a retention oracle and must not be stitched
to another provider.

### 3.3 Annotated `v0.2.0` versus current-master boundary

The annotated `v0.2.0` tag is `2fe50df4f27064140ff9f7a680227a2b337ec74a`. This is a
read-only source boundary; the live 23 August observations belong only to current
master, not to the tag. Current code means the correction base `5f9c4d6`; later local
commits in this batch change only docs/backlog.

| Axis for M1/M5 | `v0.2.0` tag | Current master before this correction |
|---|---|---|
| Public one-shot signature | `prices.history(symbol: str, interval: Interval = Interval.D1, start: Optional[date] = None, end: Optional[date] = None, *, max_attempts: int = 3, http_get=None, timeout: float = 25.0) -> PriceHistory` | same |
| Default order | SSI → VNDirect → VPS → Pinetree; KIS registered but excluded as `MIXED` | same |
| Logical budget | `max_attempts=3`; capability skips do not consume calls | same |
| Interval dispatch | direct `FailoverPriceClient.get_history` for requested interval | `apply_interval` wraps the call; M1/M5 still dispatch unchanged, only coarser intervals resample D1 |
| Adapter behavior | one physical range request per called adapter; no pagination/`nextTime` follow | same |
| Winner/warnings | first accepted nonempty result wins; partial start/end warnings are appended after winner | same for M1/M5; current validation/finalization retains other existing diagnostics |
| Declared M1/M5 capabilities | all five advertise M1/M5; KIS remains outside adjusted default chain | same |
| Live evidence | no current live matrix is attributed to the tag | 80 history + 16 metadata + 1 aggregate cohort observation, bounded and non-authoritative |

The tag cannot prove current live coverage, and current live observations cannot be
back-projected into the release.

## 4. Conditional future design (not implementation authorization)

This is a bounded reopen contract only. It cannot authorize RED tests or production
code until a later exact design review passes.

### 4.1 API and qualification unit

Keep the existing signature and default `Interval.D1` behavior unchanged. A future
qualified unit is one provider, one canonical route/version, one symbol namespace,
one exact interval, one timestamp/volume/adjustment contract, one page plan, and one
legal/runtime contract. M1 and M5 require separate evidence and may reopen separately.
No `history_bulk`, basket, archive, cross-source stitch, or local M1→M5 synthesis is
part of this design.

### 4.2 Public facade reachability gate

Direct-source qualification is insufficient. A future unit passes the public-path gate
only when `prices.history(..., interval=Interval.M1/M5, max_attempts=n)` reaches that
same unit and returns the same provenance contract. The future matrix must execute
`n=1,2,3,4`, capability skips, an earlier valid recent tail, and a later qualified
source. A capability skip consumes zero logical attempts; an invoked source consumes
one; page calls never alter `max_attempts`.

The qualified unit must either deepen the already reachable winner through same-source
pagination or receive a separately reviewed M1/M5-only order/attempt change that leaves
D1 and every other interval byte-for-byte compatible. An earlier recent-tail result
cannot silently shadow a later `FULL_SPAN` or `QUALIFIED_PARTIAL` unit. Tests must
assert exact direct-source versus facade calls/results for every attempt value,
including the negative case where a qualified source lies beyond the allowed budget.
The current facade remains option 3 and adds no capability now.

### 4.3 Deterministic physical budgets

The following are hard safety ceilings, not claims that any current source can meet:

| Counter | Exact ceiling | Reservation rule |
|---|---:|---|
| Logical source attempts | existing `max_attempts=3` default | one logical attempt per adapter; capability skips consume zero |
| Pages per logical source attempt | 8 | same-source monotone pagination only |
| Calls per page | 2 | one initial call plus at most one owner-permitted retry |
| Physical calls per source attempt | 16 | reserve before dispatch; initial and retry both charge |
| Request-scoped physical calls per public call | 32 | one shared per-call ceiling across all sources/pages/retries |
| Audit-global physical calls | `audit_global_physical_ceiling` | absolute hard envelope `30 × 2 × 16 = 960`; exact finite plan `A_plan` must be `≤ 960` and include every identity call |
| Concurrency | 1 | deterministic sequential scheduler; no hidden parallelism |

`FailoverPriceClient.get_history()` owns one private request-scoped coordinator (the
facade ledger). `prices.history()` creates/configures that client and delegates to its
`get_history()`; it does not create a second or nested coordinator. A direct
`PriceSource.get_history()` call made outside the facade gets its own coordinator. The
client passes the same coordinator to every eligible source attempt; it is never
recreated inside an adapter. Its reservation key is
`(request_id, source_role, symbol, interval, logical_attempt, kind, page_ordinal,
retry_ordinal)`, where `kind` is exactly `identity` or `history_page`; duplicate keys
are planning errors and send no request.

Every network request, including an identity control, initial page, or retry, reserves
one unit from both source and global counters before dispatch. Capability skips, input
validation, parsing, and local reconciliation consume zero. The two budget checks plus
key insertion are one atomic operation under the coordinator's private lock, even
though the approved scheduler is sequential. A retry is a new reservation and is
charged independently.

If the first reservation for an eligible source fails, the coordinator returns the
typed terminal `BudgetGlobalExhausted(symbol, interval, attempts=(),
diagnostic="budget_global_exhausted")`; the adapter is not invoked and no
`SourceAttempt` is appended. This future typed result/error is distinct from current
`AllSourcesFailed`'s ambiguous `no sources attempted` message and must preserve the
global-budget reason. If exhaustion occurs after an adapter is invoked (for example
before a later page or identity control), its private buffer is discarded and the
coordinator emits one failed logical attempt with the canonical budget reason;
page/retry reservations never create their own attempts. The pre-dispatch terminal is
not thrown through the current engine; this is a future private/public engine seam, not
current runtime behavior.

The aggregate ceiling is distinct from the request-scoped 32-call ceiling and is named
`audit_global_physical_ceiling`. It is a finite absolute envelope of
`30 symbols × 2 intervals × 16 calls = 960`. For each unit `u`, let `I_u` be its
unit-local identity requests, `P_u` its exact initial page count, and `R_u` its exact
permitted retry count; `C_u = I_u + P_u + R_u ≤ 16`. Every physical identity request
is assigned to exactly one explicit unit ledger row, even when a provider reuses an
identity result; it is counted once, not added as an open-ended shared term. The
approved finite audit plan is exactly `A_plan = Σ(u in 30×{M1,M5}) C_u`, with
`A_plan ≤ audit_global_physical_ceiling` and all terms enumerated before dispatch.
`A_plan` must fit written provider/rate permission. No cohort audit is authorized or
claimed in this pass.

### 4.4 Atomic no-false-partial result

For one provider and one interval, the future adapter must:

1. validate the symbol, exact interval, bounds, route allow-list, normalized media type,
   response identity, and adjustment role before publishing any row;
2. reserve each physical page/retry before dispatch and parse into a private buffer;
3. require aligned OHLCV arrays with real volume, exact timestamp unit/convention,
   monotone in-range cursor, no overlap/conflict, and reconciled provider totals/pages
   when declared;
4. reject wrong symbol/interval, status/MIME/envelope drift, generic HTML/challenge
   bodies, missing middle pages, repeated/reversing/out-of-range cursors, unknown
   candle convention, adjustment mismatch, and budget exhaustion; and
5. publish one provider's reconciled `PriceHistory` only after the complete claimed
   coverage is proven. Any unreconciled page/error discards the private buffer
   atomically. No cross-source segment may be returned, and no page may create a
   synthetic logical attempt.

If a later release intentionally serves a bounded partial horizon, it must preserve
the existing machine-matchable partial-start/end warnings and exact per-symbol first/
last dates; it must never relabel a recent tail as the requested full span.

### 4.5 Reopen gates and future RED matrix

There are two mutually exclusive future qualification outcomes:

Before either outcome is audited, a future release must reacquire a legally publishable,
reproducible frozen cohort, or use a separately approved caller-supplied manifest. The
current SSI-derived membership values are withheld and may not be used as an implicit
future audit input.

- **`FULL_SPAN`:** one provider/route/interval unit accounts for every applicable
  frozen-cohort cell across the complete inclusive `2018-08-13..2026-08-19` window,
  with listing/transfer boundaries separately documented. No recent-tail warning,
  second provider, or resampled interval may complete the claim.
- **`QUALIFIED_PARTIAL`:** one unit passes every identity, MIME/status, timestamp,
  volume, adjustment, legal, rate, pagination, atomicity, and facade gate but proves
  a bounded horizon short of one or both requested edges. Its approved manifest must pin each
  symbol/interval's `first_local`, `last_local`, row count, boundary flags, and
  machine-matchable `partial_start_coverage`/`partial_end_coverage` diagnostics.
  “Materially deeper” is executable only when the design review pins that exact
  manifest and minimum boundary; a partial unit never implies full span.

Both outcomes qualify M1 and M5 independently. If neither manifest passes, the new
qualified deep-history chain remains empty and the disposition remains SOURCE-GAP.

Reopen either issue only when **all** applicable gates pass for one named provider,
one exact interval, and one route/legal unit:

1. written permission covers automation, pacing, retries, retention, caching/storage,
   attribution, caller return, redistribution, and commercial use;
2. response or same-provider metadata binds symbol, listing identity, exact interval,
   VND price/value unit, volume unit/semantics, and one homogeneous adjustment basis;
3. exact status, normalized media type, envelope, redirect/browser/WAF behavior,
   authentication/session requirements, and finite page/window contract are stable;
4. timestamp epoch, timezone, candle open/close convention, session/no-trade policy,
   volume incremental/cumulative meaning, and adjustment revision limits are proved;
5. the selected outcome's manifest passes: `FULL_SPAN` covers the requested span for
   every applicable reacquired/approved frozen-cohort cell, or `QUALIFIED_PARTIAL` pins the approved
   materially-deeper per-symbol/per-interval horizon and exact warnings; neither
   outcome permits source stitching;
6. provider totals/pages/cursors, retry policy, rate policy, and the 8/16/32 safety
   envelope reconcile deterministically; and
7. public diagnostics are bounded/sanitized and D1/other-interval compatibility is
   preserved, including KIS `MIXED` exclusion unless independently changed and reviewed.

Only after a future design PASS may a RED-first matrix be written. It must cover
single/multi/final pages, totals, cursor stalls/reversal/overlap/conflict, MIME/status
drift, wrong symbol/interval, timestamp and volume semantics, adjustment mismatch,
retry and both budget caps, atomic discard, no calls after success/fatal failure,
no date fan-out/concurrency, diagnostic sanitization, `FULL_SPAN` and
`QUALIFIED_PARTIAL` manifests, facade attempts 1/2/3/4, capability skips, earlier
partial winners, later-source reachability, direct/facade parity, M1-vs-M5 separation,
and D1/source-order compatibility. All fixtures must be synthetic.

### 4.6 Conditional public diagnostics grammar

This is a future executable contract, not current runtime behavior. Canonical source
roles are exactly `ssi`, `vndirect`, `vps`, `pinetree`, and `kis`. Future attempts use
one role, `ok`, or one token from this total mapping:

| Failure class | Canonical reason tokens |
|---|---|
| transport/offline | `transport_timeout`, `transport_unavailable` |
| HTTP/redirect/challenge | `http_status_unexpected`, `redirect_or_challenge` |
| MIME/envelope | `mime_unexpected`, `envelope_invalid` |
| schema/identity/interval | `schema_invalid`, `identity_missing`, `identity_mismatch`, `interval_mismatch` |
| timestamp/volume/adjustment | `timestamp_invalid`, `volume_invalid`, `adjustment_unproven` |
| page/cursor/coverage | `pagination_unavailable`, `pagination_cursor_stalled`, `pagination_overlap_conflict`, `pagination_total_mismatch`, `coverage_unreconciled` |
| rate/legal | `rate_policy_unproven`, `legal_reuse_unproven` |
| budget/facade | `budget_source_exhausted`, `budget_global_exhausted`, `facade_unreachable` |
| bounded coverage | `partial_start_coverage`, `partial_end_coverage` |

The future qualified built-in M1/M5 facade grammar uses the frozen public field
`SourceAttempt.name`, matching `^(ssi|vndirect|vps|pinetree|kis)$`; it never refers to
a `.source` field. This finite role allow-list applies only to that future qualified
built-in facade path. The exported `FailoverPriceClient` remains compatible with
arbitrary custom `PriceSource` members and their configured `SourceAttempt.name`
values; it must not reject or rewrite custom names merely because they are outside the
built-in role list. A new qualified `SourceAttempt.reason` is exactly `ok` or one
listed ASCII token of 1–48 characters. It may contain no exception text, URL, query,
provider free text, body excerpt, cursor, or live value. Capability skips are private
routing events and create no `SourceAttempt` or public reason token. A future qualified
facade finalizer sanitizes every returned attempt, including earlier failures, not only
the winner. Existing UDF warning prefixes `quarantined_invalid_bars`,
`recovered_midnight_open_placeholder`, `partial_start_coverage`, and
`partial_end_coverage` are preserved as bounded allow-listed warnings with their
existing meaning; unknown provider warnings are mapped to a safe token or fail closed.
A future warning is one listed token or `TOKEN: count=<1..999999>`; legacy partial
coverage messages may retain ISO-date/count fields but remain bounded, ASCII, and
URL/provider-text free. The warning tuple is capped at 16 entries, each 160
characters; attempts are capped at four entries for the qualified `max_attempts=1..4`
matrix; counts are non-negative integers no wider than six digits. Any unmapped
exception, malformed role/token, over-cap diagnostic, or unsafe text fails closed to
`transport_unavailable` or `schema_invalid` as applicable and is never surfaced raw.

### 4.7 Conditional qualified-release checklist

If a later design reaches `FULL_SPAN` or `QUALIFIED_PARTIAL`, all of these must pass in
one reviewed change; this source-gap commit does none of them:

1. update the qualified research, prices API/AI usage, architecture/failover,
   source/coverage/retention diagnostics, and legal/runtime caveat;
2. preserve the public API snapshot and DataFrame/model compatibility, with any typed
   metadata only after explicit compatibility review;
3. add docs-contract coverage and CHANGELOG/release notes when public behavior or
   capability changes;
4. write synthetic RED fixtures first, then green direct-source/facade, pagination,
   identity/MIME, outcome, budget, atomicity, diagnostic, and D1/other-interval tests;
5. run focused source/failover/docs/blacklist/secret tests, the full offline merged-tree
   suite, offline import/public snapshots, `git diff --check`, and isolated sdist/wheel
   build; and
6. obtain exact-SHA reviewer approval before push or closure. No raw provider rows,
   live values, screenshots, archives, or unlicensed member lists may enter the release.

## 5. Decision and requested review

M1 and M5 are each **SOURCE-GAP CLOSURE**. The new qualified deep-history chain remains
empty and no
runtime capability is claimed. This commit contains only the two required source/design
artifacts; it requests exact-SHA design review and does not authorize TDD, RED tests,
production code, push, or issue closure.
