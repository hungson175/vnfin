# #207 design note — daily USD/VND FX history

**Packet:** `tasks/207-daily-usdvnd-fx-history-spec.md` (`3d60102`)  
**Design phase:** source/design gate only  
**Disposition:** **SOURCE-GAP CLOSURE**  
**Requested proof window:** inclusive `2018-08-01..2026-08-19`  
**Production status:** no daily source, RED tests, production code, push, or issue closure.

Evidence and provider/legal details are in
[`docs/research/2026-08-23-daily-usdvnd-fx-history-source-vetting.md`](../docs/research/2026-08-23-daily-usdvnd-fx-history-source-vetting.md).
This note binds the compatibility and future API contract without claiming that the future path
exists.

## 1. Decision and boundary

No candidate currently passes all of: response-backed identity, exact central-rate basis, full
requested-span coverage, daily calendar semantics, bounded pagination/WAF behavior, owner-approved
reuse, and runtime/rate policy. The source chain therefore stays empty. In particular:

- SBV remains a **candidate**, not a qualified provider. The current route returned HTTP-200 HTML
  WAF rejection pages rather than a JSON envelope, and no written automation/redistribution
  permission or rate policy was established.
- BIS's response-backed Vietnam/VND cell is monthly end-of-period, not daily central rate.
- H.10 and ECB do not serve a qualifying VND daily cell; Vietcombank is a spot bank quote with
  coverage, basis, cadence, and reuse gaps; World Bank is annual period-average only.
- No source may be substituted, cross-quoted, stitched, forward-filled, interpolated, or expanded
  from spot/annual data merely to make the requested date span appear complete.

This is a source-gap resolution, not a partial daily release. The current public call continues to
reject `Frequency.DAILY` before network. Only a later exact design PASS followed by an explicit
TDD authorization can change that.

## 2. Annual compatibility invariant

The following must remain byte-for-byte behaviorally compatible while #207 is unresolved and during
any later implementation:

| Contract | Required behavior |
| --- | --- |
| Entry point | Keep `vnfin.fx.history(base="USD", quote="VND", start=None, end=None, *, frequency=Frequency.ANNUAL, http_get=None, timeout=25.0)`. |
| Default | `ANNUAL` remains the default. |
| Annual provider | `WorldBankFXHistorySource`, source `worldbank_fx`, WDI `PA.NUS.FCRF`. |
| Annual meaning | Official annual period-average LCU per US$, VND per 1 USD; not SBV central, not year-end, not daily. |
| Bounds | Existing pre-network validation and inclusive calendar-year filtering remain unchanged. |
| Model | Reuse `FXPoint`/`FXHistory`; keep `unit=value_unit="VND per 1 USD"`, ascending unique points, UTC retrieval timestamp, and sanitized warnings. |
| Accessors | `rate_on()` remains exact-only. A future daily object must make `rate_for_year()` raise `InvalidData`; it must not treat a daily Jan 1 point as an annual rate. |
| Diagnostics | Existing annual `_FX_HISTORY_CAPS` and annual `explain_fx_coverage()` statuses/messages remain unchanged except for separately reviewed additive clarification. |
| Unsupported frequencies | Until a qualified daily source exists, daily/monthly/quarterly/unknown values remain typed zero-network rejections. |

`fetched_at_utc` is retrieval time only. It is never a publication, observation, or first-
knowability timestamp.

## 3. Future daily qualification unit

The only provisional future SBV identity is:

```text
provider    = State Bank of Vietnam (SBV)
route       = https://sbv.gov.vn/o/headless-delivery/v1.0/content-structures/137473/structured-contents
source      = sbv_central_fx
frequency   = daily
rate_basis  = official_daily_central_rate
pair/unit   = USD/VND, VND per 1 USD
reference   = provider effective date, converted from explicit UTC to Asia/Ho_Chi_Minh
```

These tokens are design vocabulary, not a claim of current support. A qualification unit is the
same provider, route/version, economic basis, date/publication convention, and legal/runtime
contract. A monthly BIS series, bank transfer quote, ECB cross-rate, annual World Bank average, or
current spot quote cannot be a fallback for this unit. If exactly one source qualifies later, the
implementation is single-source and exposes no fabricated failover attempts. A failover chain is
allowed only if at least two independently qualified sources have the same basis and date
semantics; it selects one source for the entire window and never stitches by date.

## 4. Future request/result contract (not implemented)

After a separate implementation authorization, a daily call would have to:

1. accept only `USD`/`VND`, `Frequency.DAILY`, and plain `datetime.date` inclusive `start`/`end`;
2. validate pair, frequency, bounds, and the fixed budget before any network call;
3. prove one qualified provider response contains both literal endpoint dates
   `2018-08-01` and `2026-08-19` and reconciles all pages;
4. return only provider observations in strictly ascending, unique reference-date order, without
   weekend/holiday fabrication or any fill/backfill/interpolation/resampling/nearest match;
5. reject HTML/XML/missing/wrong media type, malformed envelope, duplicate/overlapping pages,
   mismatched totals, wrong pair/direction/basis, out-of-window rows, invalid dates, bool/string/
   non-finite/non-positive rates, and empty or materially truncated responses;
6. parse `NgayBatDau` as an explicit UTC instant and take the date after conversion to
   `Asia/Ho_Chi_Minh`. Keep `NgayBanHanh` separate unless the provider documents it as a typed
   publication timestamp with timezone and revision semantics; and
7. preserve `fetched_at_utc` as retrieval-only, keep `rate_on()` exact, and reject
   `rate_for_year()` for a daily history.

The source response must prove its own identity. A URL, query parameter, title, or assumed field
label cannot establish direction. The future parser must bind the official central-rate definition
and the response's numeric field to `VND per 1 USD`, preserving source scale/rounding rather than
guessing or inverting.

### 4.1 Deterministic physical budget

The future SBV scheduler is bounded as an explicit contract, not a library-wide retry promise:

| Item | Ceiling/behavior |
| --- | --- |
| Source attempts | one logical source attempt; no incompatible failover |
| Page size | 100, only if the owner-confirmed route accepts it |
| Logical pages | 20 (`0..19`) for the observed `totalCount=1947` boundary; a larger reconciled count fails before page 20 |
| Physical HTTP calls | 40 total, including all page calls and retries |
| Retry | at most one reserved retry per page; no hidden transport retries, jitter, concurrency, or page reordering |
| Reservation | atomically reserve `(page, retry_index)` and one physical unit before transport; failed reservation makes zero network calls |
| WAF | HTTP-200 HTML or challenge consumes its reserved unit and is `transport_inconclusive`; after its one retry, stop with no partial output |
| Exhaustion | stop deterministically with `call_budget_gap`; do not fabricate a final attempt, empty success, or coverage absence |
| Rate policy | no numeric delay is claimed until SBV supplies an owner-approved rate limit/pacing policy; without it, the future source is not runnable/qualified |

The count/page envelope must be in each successful response family. A separate unbounded count
scan is prohibited. Logical page counts and physical request counts are distinct diagnostic
metrics; only actual reserved calls increment the physical count.

## 5. Future diagnostics and no-false-absence contract

The annual capability registry remains as-is. A later additive daily capability entry may report
the exact source/basis, full-span boundary, single-source status, and publication-time limitation.
Until a daily source qualifies, daily is `unsupported_frequency`, not a claimed coverage gap.

Future public warning/reason values are limited to these finite tokens:

```text
ok
unsupported_frequency
unsupported_pair
source_gap
coverage_gap
provider_nonpublication
holiday_gap
unexplained_gap
transport_inconclusive
schema_error
identity_mismatch
call_budget_gap
legal_gap
revision_or_release_lag
publication_time_unavailable
```

The distinction is mandatory:

- `transport_inconclusive`, `schema_error`, `identity_mismatch`, `call_budget_gap`, and `source_gap`
  are unresolved capability/runtime outcomes, never provider absence;
- `coverage_gap` is allowed only after a qualified response and provider calendar/status explain
  the boundary;
- `provider_nonpublication` and `holiday_gap` require provider-owned evidence;
- unexplained internal gaps fail closed or produce a bounded warning under the approved design;
- no response body, URL, query, cookie, credential, raw exception, provider free text, or live rate
  may enter public diagnostics; and
- counts are bounded non-negative integers and warning tuples are bounded allow-listed tokens.

No `SourceAttempt` entry is manufactured for a source that was skipped for capability or for an
unreserved budget unit. A successful single-source result has no failover-attempt surface.

## 6. Reopen gate

All criteria are conjunctive. The issue remains source-gap closed if any one is missing:

- written SBV owner permission for the exact route, automation, pacing, retries, caching/storage,
  caller-facing redistribution, attribution, commercial use, and revisions/retention;
- fresh-session strict JSON transport with no challenge/private-cookie/proxy bypass and a published
  compatible rate policy;
- response-backed envelope, field nesting, central-rate identity/direction, numeric validation,
  document identity, and explicit UTC-to-Vietnam effective-date semantics;
- complete page/count reconciliation within 20 pages and 40 physical calls, with deterministic
  reservations and no hidden retries;
- exact requested endpoints, provider-calendar explanation for any non-publication dates, no
  duplicate/out-of-window rows, and no fabricated observations;
- separate reference/publication/retrieval/revision semantics and the strict-prior caveat;
- annual source/model/diagnostic compatibility; and
- a new exact-SHA reviewer design PASS before any RED-first TDD work.

The official SBV portal contact path is evidence for how an owner permission request may be routed,
not evidence that permission already exists. The research report records the path and its limits.

## 7. TDD boundary

There is intentionally no RED commit in this design range. If the source gate later passes, the
next transition must be a separate RED-first commit with synthetic, fabricated provider fixtures
only. That future matrix must cover annual compatibility, pre-network validation, exact SBV route
and identity, MIME/envelope/WAF failures, page overlaps/count mismatch, budget reservation and
exhaustion, endpoint/gap/holiday semantics, numeric guards, strict-prior behavior, sanitized
diagnostics, and no-stitch/single-source behavior. It must not contain live FX values, raw provider
responses, screenshots, or prohibited-source material.

**Current result:** preserve the empty daily source chain and annual World Bank behavior; request
review of this docs-only source-gap design, not implementation authorization.
