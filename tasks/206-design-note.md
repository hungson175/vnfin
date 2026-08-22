# #206 design note — VNFIN daily sector-index history

**Issue:** #206
**Date:** 2026-08-23 (UTC+7)
**Phase:** SOURCE_DESIGN / docs-only
**Builder:** `vnfin-oss`
**Initial capability:** none; current `VNFIN` index-history chain remains unreachable
**Disposition:** **SOURCE-GAP CLOSURE**
**Review gate:** exact-SHA design review required before any production change, push, or close

The source facts and sanitized probe record are in
[`docs/research/2026-08-23-vnfin-sector-index-history-source-vetting.md`](../docs/research/2026-08-23-vnfin-sector-index-history-source-vetting.md).
This note binds the implementation boundary if a later written permission and design
PASS reopen the work. It does not authorize TDD now.

## 1. Product boundary

The only requested public primitive is the existing strict call:

```python
vnfin.indices.index_history(
    "VNFIN",
    date(2020, 5, 11),
    date(2026, 8, 19),
    interval=Interval.D1,
)
```

It would return provider-reported daily OHLCV **points** for the canonical `VNFIN`
HOSE Financials sector index. This batch does not implement VNFIN-minus-VN30,
VN30F/session logic, constituents, weights, signals, backtests, intraday history,
other sector indices, or a new public API. `index_history_stitched()` is not a silent
substitute: it remains an explicit D1-only opt-in with its existing multi-source
provenance and a separate warning grammar; the strict VNFIN adapter token grammar below
does not silently replace or erase that legacy stitched provenance.

The current public behavior is preserved until a later gate passes:

- `VNFIN` is recognized by the index namespace and rejected from stock-price history
  before network;
- it is absent from the index value-history allow-list, so the current index chain is
  empty/unreachable for this selector;
- all other deny-only identifiers and headline-index behavior remain unchanged; and
- no production code, live rows, cache, fixture, example, push, or issue close is part
  of this docs commit.

## 2. Evidence decision

| Source | Identity | Requested D1 boundary/rows | Volume/shape | Decision |
|---|---|---:|---|---|
| VPS | History echo plus same-owner symbol metadata | `2020-05-11..2026-08-19`; raw 1,603 rows / 1,569 dates; current parser 1,534 bars | Aligned `v`; 34 duplicate dates, 33 conflicts, two invalid OHLC rows | `PARTIAL`; cannot be the exact clean winner without a duplicate/quality contract |
| SSI | Same-owner metadata binds `VNFIN`, HOSE, index; history body has no echo | 1,569 rows/dates; both boundaries | Aligned `v`, no duplicate/invalid observation | Technical `QUALIFIED`; legal gate remains `LEGAL_GAP` |
| VNDirect | No history echo; no usable same-owner metadata route; control only | 1,570 rows/dates; both boundaries | Aligned `v`, no duplicate/invalid observation | `IDENTITY_GAP`; not a qualified fallback |

All three are vendor feeds, not official HOSE output. The requested full-span
capability is not claimed: SSI and VNDirect differ on `2025-05-05`, VPS and the other
two differ on `2021-06-28`, and the official calendar classification is unresolved.
All three vendors also lack an explicit licence permitting the library's automated
retrieval plus caller-facing redistribution. The correct current status is therefore
`SOURCE-GAP CLOSURE`, not “qualified for TDD.”

The table is not a mix-and-match matrix. Each qualification unit is one named provider
plus its exact history route and same-provider metadata route (or the documented absence
of one). Legal permission, selector identity, fixed-window/date quality, points/RAW
semantics, and aligned volume must all pass for that one unit before it can produce a
result. VPS permission cannot qualify SSI rows; SSI metadata or volume cannot repair a
VPS or VNDirect history response.

## 3. Registry and interval guard (future design, not implemented)

Use two private capability predicates, not a one-line allow-list edit and not a
public-API branch:

1. Add exactly one member, `VNFIN`, to `_VALUE_HISTORY_INDICES`. The set union keeps
   `VNFIN` in `_KNOWN_INDEX_IDENTIFIERS`, so `prices.history("VNFIN", ...)` remains a
   typed zero-network rejection.
2. Normalize once with `canonical_security_symbol`: `" vnfin "` and `"vnfin"` become
   `VNFIN`; malformed/non-string/punctuation selectors fail before network.
3. Define request capability as `(normalized symbol, interval)`. Resolve the interval
   before `apply_interval`. For canonical `VNFIN`, only
   `Interval.D1` is capable. Reject every intraday member (`M1/M5/M15/M30/H1`) and
   every coarser/resampled member (`W1/MN1/Q1/Y1`) with one stable typed
   `UnsupportedInterval` diagnostic that states D1-only and zero network calls.
4. Define separate per-source capability as `(source role, normalized symbol, interval)`.
   Apply it after request capability and before transport for the default chain and for
   every injected source chain. A role that cannot enforce the exact VNFIN D1
   history/metadata route pair is skipped, makes zero physical calls, consumes no
   `max_attempts` slot, and creates no `SourceAttempt`; request capability alone must
   not make every source role capable.
5. Do not alter headline-index native intraday or coarser-resampling behavior. The
   guard must run before the current `apply_interval` branch, otherwise a VNFIN W1
   request could fetch D1 and a VNFIN intraday request could reach inherited adapter
   capabilities.
6. Keep `index_history_stitched("VNFIN", ..., interval=Interval.D1)` opt-in only. It
   may pass the registry because its existing public method is already D1-only, but
   it must never be used by strict `index_history` to fill a source gap.

The two predicates must be covered by zero-network tests for all non-D1 intervals,
malformed selectors, padded/lowercase normalization, stock-price denial, the exact
one-member allow-list delta, unchanged deny-only/headline behavior, default-chain
incapable roles, and injected incapable roles. The latter must assert zero calls, no
attempt-budget consumption, and no fabricated `SourceAttempt`.

## 4. Strict source/failover contract

The future source order may remain `VPSIndexSource → SSIIndexSource →
VNDirectIndexSource`, but a source is accepted only after all result checks pass. A
source that cannot meet identity/legal/quality requirements is not documented as
supported. For the current evidence:

- VPS must fail closed for the observed conflicting/quarantined VNFIN rows rather
  than returning a partial winner for an exact-span request; it may be attempted and
  recorded as a failed source if the source-specific validator can identify the
  failure without leaking raw provider text.
- SSI is the only observed technical candidate, subject to written permission and a
  stable runtime binding between its metadata route and history request.
- VNDirect is incapable for VNFIN until it supplies response-backed identity; it is
  skipped before transport and therefore contributes no fabricated `SourceAttempt`.

For an authorized implementation, one logical `index_history` call makes at most one
bounded adapter attempt per capable source. `max_attempts` remains a positive per-call
budget and counts adapter attempts in deterministic order; a capability skip does not
consume it and creates no attempt record. A recoverable source failure causes the next
capable source to receive the **same** requested range. The first accepted result owns
the whole series. There is no per-date merge, retry storm, stitching, forward-fill,
backfill, interpolation, or hidden fallback to `index_history_stitched()`.

The SSI adapter's one attempt has an independent physical-call budget of **at most two**:
it first calls `/statistics/charts/symbol?symbol=VNFIN`, then calls the history route
only after metadata succeeds. Metadata must match `code=SUCCESS`, `status=ok`,
`symbol=ticker=name=VNFIN`, `exchange=listed_exchange=HOSE`, `type=Chỉ số`,
`timezone=Asia/Ho_Chi_Minh`, `has_daily=true`, and `has_no_volume=false`. Metadata
transport/HTTP/schema/identity failure ends the attempt without a history call;
history transport/HTTP/schema/identity/coverage/quality failure ends the attempt after
the second call. There is no retry, hidden parallel call, cookie/session retention, or
reuse. Injected HTTP stubs count route invocations while preserving their existing
string-returning arity. `max_attempts` counts this one adapter attempt, not its two
physical subrequests.

Every accepted result must satisfy:

- `symbol == "VNFIN"`, exact `provider_symbol`, and a canonical producer identity.
  Strict adapter producer tokens are exactly `vps_index`, `ssi_index`, `vndirect_index`,
  and `custom`; `PriceHistory.source` must be one of those tokens and must equal the
  source role token stamped before the call. Built-in roles retain their named token;
  an explicitly allowed injected producer is stamped `custom`, while an injected role
  that cannot make that promise is incapable for VNFIN. A returned raw name, URL,
  non-string value, or other mismatch fails provenance validation rather than being
  copied or implicitly trusted. The separate stitched wrapper uses only the canonical
  producer token `stitched_index_history` for its final `PriceHistory.source`;
- `interval is Interval.D1`, `AdjustmentPolicy.RAW`, `value_unit == currency ==
  "points"`, `proxy_for is None`;
- non-empty, ascending, unique VN-local dates with timezone-aware `PriceBar.time`;
- finite positive OHLC, `low <= open/close <= high`, and point scale 1.0;
- raw volume validated as an aligned non-string `list`/`tuple` of finite,
  non-negative `int` values excluding `bool`; and
- bounded sanitized `warnings` and exact ordered `SourceAttempt` records, with no
  URL, response body, credential, raw exception, or unbounded provider text.

The fixed-window qualification observation is exact for this batch: both literal
`2020-05-11` and `2026-08-19` were observed at the endpoints of a candidate response,
but that does not require those dates for every caller range. Runtime acceptance for
arbitrary ranges is a separate future contract. It must either name an official
trading calendar and supported horizon, compare first/last expected trading days plus
internal expected dates, and test weekend/holiday boundaries, or retain honest
partial/calendar-horizon diagnostics until that calendar gate is designed. Calendar
year segments used by `index_history_stitched()` may begin/end on non-trading literal
dates; their seams must be checked without fabricating endpoint bars. Actual internal
dates are preserved and an unexplained missing date is a diagnostic/source failure,
never a synthetic bar. The fixed observation, arbitrary ranges, and stitched segments
must never be presented as one coverage claim.

Public diagnostic fields are mechanically bounded, with separate contracts for the
strict adapter/failover path and the pre-existing explicit stitched wrapper. On the
strict path, `SourceAttempt.reason` and each strict `PriceHistory.warnings` entry must
be an ASCII token matching `^[a-z][a-z0-9_]{0,31}$` (maximum 32 characters) from the
exact allow-list `ok`, `transport_error`, `invalid_data`, `empty_data`,
`identity_mismatch`, `metadata_mismatch`, `coverage_gap`, `coverage_partial`,
`calendar_horizon`, `volume_missing`, `volume_invalid`, `duplicate_conflict`,
`unsupported_source`, `budget_exhausted`, `body_invalid`, `conflicts_many`,
`gaps_many`, `source_failures_many`, and `diagnostics_truncated`. No colon suffix,
URL, query string, response body, cookie, credential, raw exception, date sample, or
provider/source free text may be copied. Public strict `SourceAttempt.name` is one of
the finite role tokens `vps_index`, `ssi_index`, `vndirect_index`, or `custom`; an
oversized injected name maps to `custom` and the same token is used for
`PriceHistory.source` after provenance validation.

The explicit `index_history_stitched()` compatibility path is not silently forced into
that bare-token grammar. It preserves its existing two warning surfaces under this
separate bounded grammar: exactly `stitched_multi_source`, plus one segment warning per
calendar segment matching
`^stitched_segment: [0-9]{4} (vps_index|ssi_index|vndirect_index|custom) \((0|[1-9][0-9]{0,5}|many) bars\)$`.
The year is the four-digit segment year, the role is the canonical producer token, and
the bar count is decimal through `999999` or the literal `many`; no raw source name,
URL, exception, body, cookie, credential, or other prose is allowed. The final
stitched `PriceHistory.source` is exactly `stitched_index_history`, and a segment with
an uncanonical producer identity fails rather than leaking it. This future VNFIN
stitched mode is capped at 128 calendar segments and fails before publishing if the
range would exceed that cap; it never drops segment provenance or substitutes a
truncation warning. The existing non-VNFIN stitched API is not changed by this packet.

The scheduler has a real attempt ceiling independent of warning truncation:
`effective_attempt_limit = min(max_attempts, 8)`. It makes at most eight actual capable
adapter calls, and every exposed `SourceAttempt` is one of those actual calls with a
canonical role and complete token reason; skipped or unattempted sources never produce
a record. If the limit is reached while capable sources remain, an accepted result
may receive one `diagnostics_truncated` **warning token only**. It is never a
`SourceAttempt`, does not consume `max_attempts`, and is never inserted into
`AllSourcesFailed.attempts`; an all-source failure exposes only the actual attempted
records. For strict warnings, retain the deterministic first 15 tokens and append the
sentinel as the 16th (deduplicated) when either warning-list or attempt-scheduler
truncation occurs. `max_attempts > 8` therefore still makes at most eight calls, and a
nine-capable-source fixture must expose at most eight real attempts and no synthetic
truncation record. Large conflict/gap sets and oversized source text must have RED
coverage for caps and complete text sanitization.

## 5. Volume contract

The raw probes found aligned `v` arrays on all three routes, and VPS/SSI metadata
declared `has_no_volume=false`. The current shared UDF parser nevertheless turns an
absent or null `v` into zeroes. That shortcut is unsafe for VNFIN and is not part of
this design.

The future VNFIN-specific parser seam is one total fail-loud contract, before the
shared parser can erase field presence:

- raw `v` must be present and be a non-string `list` or `tuple` of exactly
  `len(t)` elements;
- every element must be a finite, non-negative `int` that is not `bool`;
- missing, `None`, wrong container type, wrong length, bool, fractional/float,
  negative, non-finite, or malformed volume raises `InvalidData` for the entire
  source attempt, records one recoverable failed attempt, and cannot publish any
  shortened or quarantined VNFIN series; and
- a genuinely present provider-reported integer zero remains `0` and is not treated
  as missing.

This identical rule applies to direct and default failover paths. A qualified result
documents that its volume is provider-reported and does not silently represent missing
volume. No optional `volume`, `NaN`, sentinel zero, row-level quarantine, constructor
migration, or public snapshot change is authorized.

If later evidence proves that the only legally qualified source
does not provide volume, stop and open a separate additive typed missing-volume design.

## 6. Legal/runtime and reopen gate

No-auth access is only a transport observation. It is not a licence. The bounded probe
used the repository's desktop-Chrome `User-Agent`
(`Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36`)
because the provider routes may reject an ordinary client; this browser-UA dependency
is an access/transport axis, not evidence of public automation permission, and remains
part of the legal/provider gap. No credential, login, cookie/session reuse, browser automation, challenge-solving,
proxy bypass, or private route was used. Current legal status is `LEGAL_GAP` for VPS,
SSI, and VNDirect: the provider terms either restrict copying/reproduction/distribution
or provide no affirmative route-specific API/data reuse grant. The runtime posture
remains no cache, no bundled rows, no archive, no bulk export, and no public live-value
examples.

Reopen to TDD only when all gates below are evidenced in a new review packet:

1. One named provider `P` and its exact history/metadata route pair have written
   permission/licence covering automated retrieval, OSS use, caller-facing
   return/redistribution, storage/caching, attribution, rate-limit policy, and
   commercial restrictions. Permission for another provider cannot qualify `P`.
2. That same `P` route pair binds the requested selector in the response or in a
   documented same-owner metadata contract that the runtime adapter can enforce with
   the bounded SSI-style route order. VNDirect needs a new identity route or
   equivalent provider-backed contract.
3. For the fixed reviewed observation, that same `P` gives the exact boundaries and a
   documented/officially accounted internal date set; no conflicting duplicates or
   invalid OHLC rows are accepted as a clean full-span winner. This does not by itself
   qualify arbitrary caller ranges or stitched calendar-year segments.
4. A separate runtime range contract names the official calendar and supported
   horizon, or explicitly retains partial/calendar-horizon diagnostics. Weekend and
   holiday boundaries plus stitched year seams are tested without requiring
   non-trading literal endpoints or fabricating bars.
5. That same `P` route pair returns aligned non-null volume on every successful
   response under the total fail-loud contract above; a violation fails the whole
   attempt and a present integer zero is preserved.
6. The request/per-source registry guards, strict failover, SSI at-most-two physical-call
   budget, adapter-attempt budget, warning/attempt sanitization caps, public
   compatibility, offline synthetic fixtures, docs, and full merged-tree gates pass.

## 7. TDD matrix after a future design PASS only

No RED tests or production code are part of this commit. If the conjunctive reopen
gate passes, the first code commit must begin with synthetic RED tests for:

1. baseline VNFIN D1 zero-network rejection, then exact one-member allow-list delta;
2. lowercase/padded normalization and malformed zero-network failure;
3. all non-D1 zero-network failures with unchanged headline behavior;
4. direct-success only for a synthetic source whose **same-provider route unit** has
   passed the written-permission, response-identity, coverage/quality, points/RAW,
   and total-volume gates. The SSI success fixture must perform metadata then history
   in that order and stay within at most two physical calls. The observed VPS duplicate/
   quality fixture remains fail-closed; it is not a direct-success fixture merely
   because its transport returned HTTP 200;
5. default and injected per-source capability skips for VNDirect/other incapable roles,
   proving zero physical calls, no attempt-budget consumption, and no fabricated
   `SourceAttempt`;
6. SSI metadata mismatch/transport failure with zero history call, history failure after
   metadata, exact at-most-two physical-call ceiling, no retry, no cookie/session reuse, and preserved
   injected string-stub arity;
7. primary success, primary recoverable failure then SSI fallback, all-source failure,
   exact bounded ordered adapter attempts, separate SSI physical-call accounting, and
   no per-date source mixing;
8. response identity mismatch, metadata absence, malformed envelopes/body,
   misaligned arrays, invalid OHLC, duplicate/conflicting dates, and out-of-range
   padding. MIME is **not** an enforceable VNFIN runtime invariant in this design:
   injected transport returns body text and preserves its existing string-stub API, so
   no wrong-MIME assertion is made. A future response-metadata seam would require a
   separate compatibility review;
9. missing/null/wrong-type/misaligned/bool/fractional/negative/non-finite/malformed
   volume all fail the entire source attempt, while a present integer zero remains 0;
10. fixed-window endpoint and internal-gap checks separately from arbitrary caller
    ranges, weekend/holiday boundaries, calendar-horizon diagnostics, and stitched
    calendar-year seams; no fill/reconstruction and strict versus stitched separation;
11. strict token versus stitched-warning grammars, canonical `PriceHistory.source`,
    canonical stitched segment roles, 128-segment fail-closed cap, real-attempt
    ceiling for `max_attempts > 8`, nine-capable-source behavior with no synthetic
    `SourceAttempt`, 16-warning/`9999` count caps, `*_many` overflow token,
    deterministic truncation, oversized source text, and large conflict/gap sets with
    complete URL/body/cookie/credential/exception sanitization; and
12. API/docs/build/blacklist/secret/diff gates on the merged tree.

This document itself requests only source/design review. It does not authorize TDD,
production code, push, or issue closure.
