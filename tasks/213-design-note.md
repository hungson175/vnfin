# #213 design note — VNREAL daily sector-index history

**Issue:** #213
**Date:** 2026-08-23 (UTC+7)
**Phase:** `SOURCE_DESIGN` / docs-only
**Builder:** `vnfin-oss`
**Requested:** canonical `VNREAL`, D1, inclusive `2018-01-01..2026-08-19`
**Disposition:** **SOURCE-GAP CLOSURE**
**Review gate:** exact-SHA design review required before TDD, production code, push, or close

The fresh source evidence is in
[`docs/research/2026-08-23-vnreal-sector-index-history-source-vetting.md`](../docs/research/2026-08-23-vnreal-sector-index-history-source-vetting.md).
This note binds the future design boundary but does not authorize runtime capability.

## 1. Current behavior and clean release boundary

The clean production boundary is `origin/master` at full SHA
`4c85fbc6a1101b3a904b1dc68ac37bc29477ef6f`. Backlog-only commits `202b5d5` and later
commits record queue/review state only; they do not alter the production boundary,
registry, source chain, or runtime behavior.

At that boundary, `VNREAL` remains in the private index deny namespace but not in the
value-history allow-list. Consequently:

- `prices.history("VNREAL", ...)` remains a typed wrong-namespace rejection before
  network;
- `indices.index_history("VNREAL", ...)` remains a typed terminal unsupported-history
  diagnostic before network;
- `indices.index_history_stitched("VNREAL", ...)` has the same empty-chain behavior;
- existing served indices, other deny-only sectors, points units, and existing stitched
  provenance remain unchanged; and
- this docs-only source-gap round adds no source, endpoint, credential, cache, fixture,
  dataset, or public capability.

The annotated `v0.2.0` tag is
`2fe50df4f27064140ff9f7a680227a2b337ec74a`. It is a historical release boundary and is
not evidence that VNREAL was served; tag-era files must not be mixed with the clean-base
behavior.

## 2. Conservative decision table and total disposition

A provider row is one independent source unit. The identity result must be
response-backed on the same unit: VPS has only history echo plus same-owner metadata,
without provider-backed exchange/index type; SSI has same-owner metadata but no history
symbol and no proven history-to-metadata binding; VNDirect has neither a usable identity
route nor a history symbol. Therefore **no VPS or SSI complete identity is claimed**.

The disposition is a total ordered tuple with no omitted axes:

```text
IDENTITY_GAP, PARTIAL, COVERAGE_GAP, TIMESTAMP_GAP, VOLUME_GAP,
ADJUSTMENT_GAP, PAGINATION_GAP, TRANSPORT_INCONCLUSIVE, LEGAL_GAP, RATE_POLICY_GAP
```

| Source unit | Fresh response-backed identity | Fixed-window observation | **Total disposition** |
|---|---|---|---|
| `vps_index` history + same-owner symbols metadata | `IDENTITY_GAP`: history echo and metadata only; exchange/index binding is incomplete | 1,649 raw / 1,615 distinct local dates; first `2020-03-03`, last `2026-08-19`; 34 duplicates, 33 conflicting; requested start unserved | `IDENTITY_GAP + PARTIAL + COVERAGE_GAP + TIMESTAMP_GAP + VOLUME_GAP + ADJUSTMENT_GAP + PAGINATION_GAP + TRANSPORT_INCONCLUSIVE + LEGAL_GAP + RATE_POLICY_GAP` |
| `ssi_index` history + same-owner charts metadata | `IDENTITY_GAP`: identity response exists, but history has no symbol and exact binding is unproven | 2,148 raw / 2,147 distinct; first `2018-01-02`, last `2026-08-19`; one identical duplicate; no provider total | `IDENTITY_GAP + PARTIAL + COVERAGE_GAP + TIMESTAMP_GAP + VOLUME_GAP + ADJUSTMENT_GAP + PAGINATION_GAP + TRANSPORT_INCONCLUSIVE + LEGAL_GAP + RATE_POLICY_GAP` |
| `vndirect_index` history + same-owner symbol route | `IDENTITY_GAP`: history lacks symbol and identity route returned HTTP 404 | 2,152 raw / 2,152 distinct; first `2018-01-02`, last `2026-08-19`; requested start unproven | `IDENTITY_GAP + PARTIAL + COVERAGE_GAP + TIMESTAMP_GAP + VOLUME_GAP + ADJUSTMENT_GAP + PAGINATION_GAP + TRANSPORT_INCONCLUSIVE + LEGAL_GAP + RATE_POLICY_GAP` |

`PARTIAL` records observed rows/metadata without complete qualification. `VOLUME_GAP`
includes unproven volume unit/meaning; `ADJUSTMENT_GAP` includes unproven provider RAW
semantics; `TRANSPORT_INCONCLUSIVE` includes the untested browser-UA necessity and
unclosed status/MIME/effective-route policy. The source units are not interchangeable:
VPS permission cannot qualify SSI data, SSI metadata cannot repair VNDirect identity, and
matching dates cannot close a missing axis.

## 3. Future strict and stitched boundary (not implemented)

Only after a later exact design PASS on a qualified source may implementation:

1. add exactly `VNREAL` to `_VALUE_HISTORY_INDICES`, leaving its price-path deny entry
   and every other deny-only identifier unchanged;
2. accept only exact `Interval.D1` after typed canonical selector/range validation;
3. enforce capability per `(role, VNREAL, D1)` for default and injected chains before
   transport; an incapable role is a skip, not an attempt;
4. require same-provider response identity, exact status/full Content-Type, effective
   route, success envelope, aligned finite D1 point bars, aligned non-null volume, a
   documented timezone/session/timestamp convention, and `AdjustmentPolicy.RAW`;
5. return one provider's complete validated `PriceHistory` with
   `currency=value_unit="points"`, canonical `source`, and bounded sanitized warnings;
6. fail closed on an unproven fixed-window boundary, duplicate/conflicting date,
   missing/null/unproven volume, wrong MIME/envelope/status, symbol mismatch, invalid
   OHLC, or any unresolved legal/rate/pagination axis; and
7. never substitute `VNFIN`, another sector, a basket, an equity/ETF proxy, or another
   provider's bars inside strict history.

The default strict order may remain VPS → SSI → VNDirect, but only a fully qualified
source unit can be attempted. A source capability skip consumes no logical or physical
budget and creates no fabricated attempt record.

The reviewed fixed horizon is exactly inclusive local dates
`2018-01-01..2026-08-19`. Future arbitrary `from`/`to` inputs are not automatically
qualified: outside or crossing that horizon fails closed before network with reason
`coverage_gap` and warning `out_of_reviewed_horizon`, rather than silently clipping.
A separately reviewed partial range may return only `coverage_partial` with
`partial_start_coverage` and/or `partial_end_coverage`; it must expose bounded observed
bounds and never claim the full horizon. The provider must supply a documented exchange
trading calendar/base date and boundary/internal-gap rule. No calendar inference from a
weekend, holiday, first/last row, `nextTime=null`, or one observation is allowed.

The strict request is one provider, one identity unit, one validated full window. It must
not silently call the opt-in stitcher. The existing
`index_history_stitched()` entrypoint remains D1-only and calendar-year segmented for
`2018..2026` (nine segments), with explicit multi-source provenance. It may be considered
only after strict VNREAL qualification. Any failed/unqualified segment makes the public
stitched call atomic and returns no partial series; strict history never uses stitching
to mask a source, identity, calendar, legal, or rate gap.

## 4. Exact observation and future transport seam

The #213 observation used six route cells per pass (history plus same-owner identity for
three providers) over two sequential passes:

| Quantity | #213 VNREAL | Combined #213 + #214 |
|---|---:|---:|
| Route cells per pass | 6 | 12 (six per symbol) |
| Passes | 2 | 2 |
| Logical route operations | **12** | **24** (12 per symbol) |
| Physical HTTP dispatches | **12** | **24** (12 per symbol) |
| Retries / redirects | 0 / 0 | 0 / 0 |

One logical route operation is exactly one physical HTTP request in this bounded
observation. The combined 24/24 total is batch accounting only; VNREAL and VNMID evidence
remain independent and no runtime quota is implied.

The current injected transport contract remains valid: GET callables take
`(url, params, headers)`, POST callables retain four arguments, and string-returning
stubs remain valid. The future private seam is design-only:

- private immutable `HttpResponseMetadata` has exactly `status_code: int`,
  `content_type: str | None` (the complete value), `effective_url: str`,
  `redirect_count: int`, and optional bounded private `headers` tuple;
- private `HttpResponseText` carries `body: str | bytes` plus that metadata;
- `_request_text` still returns `str` to current callers; a legacy stub returning `str`
  has unavailable metadata and any metadata-sensitive VNREAL path fails closed;
- the default transport captures status, complete Content-Type, effective URL, redirect
  count, and private headers before `raise_for_status`, then unwraps the body;
- an optional private `response_observer(HttpResponseMetadata | None)` is invoked once
  per physical dispatch, including retries; neither type nor observer is public or
  re-exported and raw URL/query/body/provider text never reaches it; and
- future validation reads the complete header value after the first colon, checks exact
  status/full MIME/effective host/path/redirect policy, then normalizes only the media
  type; a colon-suffixed MIME/value is rejected. Maintenance HTML fails closed.

Legacy string stubs remain valid for current APIs and synthetic wrapper fixtures are
offline-only. No response seam or production behavior is added in this docs-only round.

## 5. Exact global budget and diagnostic grammar (design-only)

The future contract reuses the approved #209 `BudgetGlobalExhausted` contract exactly:

```text
vnfin.exceptions.BudgetGlobalExhausted(VnfinError)
  symbol: str
  interval: Interval
  attempts: tuple[SourceAttempt, ...]
  diagnostic: Literal["budget_global_exhausted"]
```

It is not `SourceError`, not a private sentinel, and not a public terminal object or
partial `PriceHistory`. It is exported only from `vnfin.exceptions` (and listed in that
module's `__all__`), not from `vnfin` or `vnfin.prices`; future index wrappers propagate
it. No unspecified public counters are added.

`max_attempts` is one deterministic, atomic logical-source budget in `1..3`, default `3`.
Capability skips consume zero budget. Strict mode permits at most `3` logical attempts and
`6` physical dispatches (identity + history); stitched mode has nine segments and at most
`27` logical / `54` physical dispatches with no segment reset. Reserve each logical source
slot and each physical HTTP slot atomically before dispatch. There are no concurrent
reservations, hidden pages, redirects, retries, or extra rate-policy dispatches in this
contract.

If the first reservation for an eligible source fails, raise the exact exception at the
outer boundary with prior sanitized attempts; fresh zero-call exhaustion has
`attempts=()`, and an uninvoked source adds no attempt. If exhaustion occurs after an
adapter starts, discard its private in-progress buffer and append exactly one failed
logical attempt with reason `budget_global_exhausted`. Page/retry reservations never add
attempts. No partial strict or stitched `PriceHistory` is returned.

### Closed attempt and warning grammar

`SourceAttempt` retains `name, ok, reason`. `name` is exactly one of
`vps_index`, `ssi_index`, or `vndirect_index`; unknown, non-string, unhashable, or
malicious injected members are filtered before dispatch, consume zero budget, and may
produce only the bounded warning `source_unknown`. `ok` is true exactly for reason `ok`.

Every reason is ASCII, matches
`^[a-z][a-z0-9_]{0,47}$`, and belongs to this finite allow-list:

```text
ok, budget_global_exhausted, identity_gap, identity_missing, identity_mismatch,
wrong_exchange, wrong_index_type, wrong_interval, point_invalid, volume_missing,
volume_invalid, adjustment_gap, timestamp_invalid, coverage_gap, coverage_partial,
duplicate_conflict, pagination_gap, transport_inconclusive, mime_mismatch,
http_status_unexpected, redirect_mismatch, auth_required, waf_challenge, legal_gap,
rate_policy_gap, not_served, no_data_observed, source_unknown
```

Attempt tuples are capped at 3 entries in strict mode and 27 in stitched mode. Warning
tuples are capped at 32 tokens per strict call/segment and 64 tokens per stitched
aggregate. Each token is ASCII and at most 64 characters, and must be one of:

```text
stitched_multi_source, partial_start_coverage, partial_end_coverage,
out_of_reviewed_horizon, diagnostics_truncated, deduped_duplicate_daily_index_bars,
quarantined_invalid_bars, source_unknown
```

or match exactly:

```text
^stitched_segment:[0-9]{4}:(vps_index|ssi_index|vndirect_index):[0-9]{1,6}$
```

No attempt/warning token contains a URL, query, body, cookie, header, provider exception
text, credential, or live value. `diagnostics_truncated` is a bounded warning only; it
never creates a synthetic attempt. Current generic failover behavior is unchanged until
a future index-specific implementation sanitizes these values.

## 6. Future-only #213 RED/release matrix

This matrix is executable only after a fresh exact-SHA design PASS. It is **not** a RED
authorization and this commit adds no tests, code, fixtures, network calls, or runtime
capability.

| Case | Required future RED assertion |
|---|---|
| Selector positive | Exact, lower-case, and padded `VNREAL` canonicalize to one selector; exact `Interval.D1` and typed range pass validation without network |
| Selector/namespace negatives | Wrong sector, `VNFIN`, basket/proxy/ETF, unknown, punctuation, malformed range, non-D1, price namespace, and all deny-only identifiers fail typed before network |
| Existing source compatibility | Current served indices, current deny-only behavior, `PriceHistory` fields, source/warnings/attempts, DataFrame conversion, imports, snapshots, and existing stitched output remain byte-compatible |
| Identity positive | Synthetic same-provider history + identity responses prove symbol, exchange/index type, D1, point scale/value, timezone/session, and exact binding before accepting bars |
| Identity negatives | Request echo only, missing/mismatched symbol, unbound SSI history, wrong exchange/type/interval/scale, invalid point/RAW/adjustment, timestamp, or provenance fail with finite reasons |
| Status/MIME/route | Private metadata wrapper tests unexpected status, full Content-Type/normalized MIME mismatch (including a colon-suffixed MIME/value), generic HTML, effective host/path mismatch, redirect mismatch, and missing metadata; all fail closed |
| Coverage positive | Synthetic calendar/base date, reviewed inclusive horizon, provider total/page/cursor/window-cap, one row per session, aligned finite OHLC/volume, and exact boundaries produce one complete strict series |
| Coverage/quality negatives | Recent-only/server-cap, missing boundary without calendar, internal gap, duplicate conflict, missing/null/invalid volume, invalid OHLC, no total/cursor reconciliation, and `nextTime=null` without completeness fail closed; no false absence |
| Horizon/partial | Outside/crossing reviewed horizon causes zero network plus `coverage_gap`/`out_of_reviewed_horizon`; explicitly reviewed partial causes `coverage_partial` and boundary warning only, never a full-range claim or calendar inference |
| Strict atomicity/failover | Failed or unqualified source returns no partial bars; capable-source skips consume zero budget; only one fully validated provider result can be returned |
| Strict budget | `max_attempts=1,2,3` works; other values fail pre-network; 3 logical/6 physical cap, atomic reservation, first-reservation prior-attempt preservation, fresh empty attempts, mid-adapter one budget attempt, and no page/retry attempts are asserted |
| Stitched segments | Nine calendar-year segments share one global 27 logical/54 physical budget with no reset; missing/unqualified/budget-exhausted segment returns no partial aggregate; identical seams deduplicate and conflicts fail |
| Stitched diagnostics | Provenance uses only `stitched_segment:YYYY:role:bar_count`; unknown injected names are skipped with `source_unknown`; bounded warnings are finite; `diagnostics_truncated` never becomes an attempt |
| Stitched fetched time | `fetched_at_utc=max(segment.fetched_at_utc for successful segments)` after UTC normalization; missing or timezone-naive segment time fails the whole aggregate with `timestamp_invalid`; no current clock is fabricated |
| Response seam | Legacy 3-argument GET/4-argument POST string stubs remain valid; private `HttpResponseText` positive metadata is observed once per physical dispatch including retries; unavailable metadata fails metadata-sensitive qualification |
| Release gates | Future release requires focused/full offline tests, zero-network guard, build/import/version, API/snapshot/docs/skill/CHANGELOG, blacklist/secret, object/path/diff/clean-tree gates, and exact-SHA reviewer approval; no live rows are bundled |

## 7. Conjunctive reopen gate and delivery boundary

**VNDIRECT legal/contact limitation (2026-08-23):** direct bounded GETs using the
documented browser-like User-Agent to exactly
`https://www.vndirect.com.vn/dieu-khoan-su-dung/` and exactly
`https://www.vndirect.com.vn/dich-vu-dau-tu-huu-tri/ho-tro/` returned HTTP `403`. No
page content was read, and no terms or support conclusion is derived. These URLs are
unverified official leads/contact paths only; no permitted alternate path or alternate
date is claimed or recorded. `LEGAL_GAP + RATE_POLICY_GAP +
TRANSPORT_INCONCLUSIVE` remain required. Reopen requires a permitted, response-backed
legal/rate path; it must not infer permission from these 403 responses.

Reopen to TDD only when one named provider passes all gates in the same source unit:

1. **Identity:** response-backed `VNREAL`, exchange/index type, point scale/value,
   timezone/session, D1 capability, and exact history/metadata binding;
2. **Coverage:** documented exchange calendar/base date, exact requested inclusive
   horizon or explicitly qualified partial, total/page/cursor/window-cap reconciliation,
   one row per session, no conflicting duplicates, and machine-matchable boundary/gap
   diagnostics;
3. **Semantics:** finite positive OHLC with high/low envelope, aligned non-null volume
   with documented unit, exact D1 token, timestamp convention, and provider RAW points
   declaration; never synthesize zero volume;
4. **Transport:** exact status/full MIME/effective-route behavior through the private seam,
   stable redirect policy, UA necessity tested rather than inferred, explicit session and
   cookie policy, and no maintenance HTML;
5. **Legal/runtime:** written automated-retrieval, OSS, caller-facing, redistribution,
   cache/storage, attribution, commercial, rate, and retry permission for the named route;
6. **Budget/atomicity:** the shared exact `3 / 6` strict and `27 / 54` stitched ledger,
   atomic reservations, whole-window failover, whole-call stitch failure, and no fake
   attempt/partial result; and
7. **Diagnostics/compatibility:** the closed grammar, no-false-absence behavior, current
   deny-only and served-index behavior, snapshots, offline tests, docs/build/blacklist/
   secret checks, and merged-tree gates.

Until all seven pass, the disposition remains `SOURCE-GAP CLOSURE`. This note contains
only source/design evidence and future tests as a specification. It does not authorize:

- RED tests or production code;
- adding `VNREAL` to a runtime allow-list;
- live integration tests, fixtures, cache, archive, or provider rows;
- a cross-source stitch, proxy, basket, signal, or downstream feature;
- push, public resolution, or issue close before exact-SHA design PASS.

The source report retains primary provider/HOSE URLs and no raw payloads. The clean-room
VNStock exclusion was applied as recorded there. Preserve the empty VNREAL chain, all
deny-only behavior, independent #214 evidence, and queued #215; a later source-gap PASS
permits only documentation publication/resolution/remote verification/close-re-read.
