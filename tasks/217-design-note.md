# #217 design note — daily CNY/VND FX history

**Status:** SOURCE-GAP CLOSURE; design/source evidence only
**Packet:** `tasks/217-daily-cnyvnd-fx-history-spec.md` at reviewer `4159d74`
**Research:** [`docs/research/2026-08-23-daily-cnyvnd-fx-history-source-vetting.md`](../docs/research/2026-08-23-daily-cnyvnd-fx-history-source-vetting.md)
**Requested span:** inclusive `2018-01-01..2026-08-19`
**Current source chain:** empty; no daily CNY/VND capability

This note is the exact design handoff for #217.  It does not authorize RED tests, a source
registration, a model/accessor change, production code, a provider token, a push, or issue
closure.  Those require a later design PASS followed by a separate implementation review.

## 1. Decision

`SOURCE-GAP CLOSURE` is the only honest disposition.  No same-provider unit currently proves
all of direct CNY/VND identity, one economic basis, exact scale, the requested historical
coverage, bounded runtime, and lawful reuse.  The evidence is not a license to combine:

- SBV USD/VND central-rate data with any CNY/USD data;
- ECB EUR/CNY with a VND leg;
- BIS USD-bilateral series with another provider;
- Vietcombank cash/transfer/sell fields with each other or with a central rate; or
- current/spot values with historical observations.

The daily chain therefore remains `()`.  Existing annual `USD`/`VND` World Bank behavior,
signature, source token, period-average semantics, diagnostics, and documentation remain
unchanged.  Monthly/quarterly frequencies, unsupported pairs, and unknown values remain
typed zero-network failures under the current implementation.

## 2. Qualification unit

One candidate is qualified only as this complete tuple:

```text
provider_token
+ exact owner route/version
+ response-backed base=CNY, quote=VND
+ one provider-observed numeric field
+ one closed economic-basis token
+ VND per 1 CNY direction and proven scale
+ provider observation-date/calendar/revision contract
+ full or provider-declared bounded coverage
+ legal/runtime contract for the exact use
```

Every element is conjunctive.  A candidate with a valid number but an unknown field direction,
date meaning, scale, rate policy, or reuse right is not `QUALIFIED` or `PARTIAL`; it is a
source-gap axis.  Provider names, route URLs, response prose, and arbitrary basis labels are
not public values.  A future basis must be a finite closed token such as
`bank_transfer_buy` or `official_daily_central_parity` only if the owner response and written
semantics prove that exact basis.  Those examples are not current capabilities.

If a provider quotes `100 CNY`, division by 100 is allowed only when the same response or
owner documentation proves the scale.  Missing or ambiguous scale is `BASIS_GAP`.  Reversal,
midpoint, interpolation, forward-fill, backfill, resampling, nearest-date matching, and
cross-rate arithmetic are always rejected.

## 3. Candidate disposition matrix

| Candidate unit | What is proven | What is missing | Disposition |
| --- | --- | --- | --- |
| Vietcombank dated API | Recent response-backed CNY object with cash/transfer/sell fields; 2018 probe returned an empty envelope; no bulk/full-span proof | Selected bank basis, machine-readable unit/direction, retention, full coverage, revisions, API rate policy, and reuse rights | `IDENTITY_GAP` + `BASIS_GAP` + `COVERAGE_UNKNOWN` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| Vietcombank XML | Current CNY row and `Buy`/`Transfer`/`Sell`; complete XML MIME; explicit reference-only/five-minute note | Historical retention, dated route semantics, caller-facing/reuse permission, and a selected basis for the requested span | `BASIS_GAP` + `COVERAGE_GAP` + `LEGAL_GAP` |
| SBV reference/cross/central routes | Official menu separates rate products; direct route probes timed out | Any response-backed direct CNY/VND row, schema, scale, date/calendar, coverage, rate policy, and reuse permission | `TRANSPORT_INCONCLUSIVE` + `IDENTITY_GAP` + `LEGAL_GAP` |
| PBOC/CFETS | Official PBOC/CFETS published lists inspected; VND absent from the shown direct RMB instruments; CFETS requires written authorization for data use | A public direct CNY/VND route and license | `NOT_SERVED` + `LEGAL_GAP` |
| BIS `XRU` | Official VND/USD page and USD-bilateral documentation | Direct CNY/VND identity and requested daily basis | `NOT_SERVED` + `BASIS_GAP` |
| ECB/Frankfurter | Official EUR-base CNY reference page; VND absent from ECB roster | Direct CNY/VND owner series and compatible basis; facade cannot supply either | `NOT_SERVED` + `BASIS_GAP` |
| World Bank WDI | Existing annual USD/VND period-average source | Daily CNY/VND pair/frequency | `NOT_SERVED` for #217; preserve annual |
| Federal Reserve H.10/FRED | H.10 has no VND row; concrete FRED CNY series is CNY/USD | Direct CNY/VND pair; cross-conversion is forbidden | `NOT_SERVED` + `BASIS_GAP` |
| Current open-rate APIs | Existing no-key open endpoint is current/spot only and has restrictive redistribution terms | Historical retention and lawful historical redistribution | `NOT_SERVED` + `LEGAL_GAP` |

The detailed route, MIME, count, date, and legal evidence is in the research artifact.  No
candidate is promoted by an empty response, a 404, a timeout, a page title, or a current quote.

## 4. Future API boundary (non-authoritative)

There is no new API in this change.  The following is a compatibility boundary for a future
implementation only:

1. `vnfin.fx.history()` keeps its current signature and annual default.
2. Annual `USD`/`VND` continues to use World Bank WDI `PA.NUS.FCRF`, period average, and its
   current date/source/diagnostic behavior.
3. A future daily path may serve only exact CNY/VND after common validation, with plain-date
   bounds, `unit == value_unit == "VND per 1 CNY"`, ascending unique provider dates, finite
   positive non-boolean rates, and an explicit finite `rate_basis`.
4. Any future `rate_basis` addition is trailing and compatibility-safe.  It must not alter
   annual positional construction, equality, repr, serialization, or existing DataFrame
   columns.  Annual history would carry its own annual-period-average token; it must not be
   relabeled as a daily basis.
5. `FXPoint.date` remains the provider observation/reference date.  `fetched_at_utc` is
   retrieval time only and is not publication time or a same-day availability promise.
6. `rate_on()` remains exact-match-only.  `rate_for_year()` remains annual-only and must not
   reinterpret a daily Jan-1 observation.
7. There is no automatic fallback between bank cash, bank transfer, bank sale, central parity,
   market close, period average, or any cross-derived basis.  A chain can be considered only
   after at least two independent sources qualify for identical pair, basis, date, and revision
   semantics; the request uses one source for the whole window and never stitches by date.

Until a new implementation review authorizes this shape, current runtime behavior remains the
annual-only contract and the new chain remains empty.

## 5. Future retrieval contract

### 5.1 Request and response identity

After input validation, a future daily request must carry the exact normalized tuple
`(base="CNY", quote="VND", frequency="daily", start, end)`.  The successful response family
must prove the same tuple; a URL parameter, a provider page title, or a guessed currency key
does not prove it.  A successful observation is represented internally as:

```text
observation_date: plain ISO date from the provider's documented reference field
rate: finite positive non-boolean number, VND per 1 CNY
basis: one closed provider-independent token
scale: explicit one-unit or documented 100-unit normalization
provider: canonical provider token, not a URL or response prose
```

No response may be accepted when its pair, basis, scale, date, revision, or MIME is missing,
ambiguous, inverted, or inconsistent across pages.  `Date` and `UpdatedDate` fields alone do
not establish publication or point-in-time availability; the provider must document their
meaning.

### 5.2 Coverage and no-false-absence rules

The exact full-span contract is inclusive `2018-01-01..2026-08-19`.

- The provider's total/count/page/cursor ledger must reconcile exactly with returned rows.
- Every page/cursor required by that ledger must be fetched successfully under the global
  budget.  A no-row or malformed page before reconciliation is a typed failure, never a zero
  contribution.
- Returned dates are strictly ascending and unique, within bounds, and are not filled or
  shifted.  Weekend/holiday holes are explainable only by provider-owned calendar/status data.
- `FULL` requires provider-declared or response-backed bounds, exact counts, no duplicate
  dates, no unexplained internal gaps, and a revision/update rule.
- `PARTIAL` is permitted only when the same provider independently declares the observed bounds
  and all returned pages reconcile.  The diagnostic must expose exact `observed_start` and
  `observed_end`; it must never imply the requested full span or silently continue with a
  different provider.
- Empty, truncated, timeout, WAF, HTML, 404, budget-exhausted, and unreconciled responses are
  `UNKNOWN`/failure outcomes unless the provider explicitly identifies a non-publication date.
  They do not prove historical absence.
- No partial `FXHistory` is returned after a failed full-span retrieval.  If a later public
  API deliberately exposes a provider-declared `PARTIAL`, that must be a separately reviewed
  typed contract, not an accidental half-result.

### 5.3 One atomic global budget

The scheduler owns one request-scoped ledger.  It is not reset per source and cannot be
expanded by a retry helper:

| Counter | Exact ceiling | Reservation rule |
| --- | ---: | --- |
| logical source attempts | 4 | fixed candidate order; capability skips consume zero |
| logical page/cursor dispatches | 64 | one reservation per page/cursor; no per-day fan-out |
| retry reservations | 32 | at most one retry per page/cursor |
| physical HTTP calls | 96 | every initial/retry call reserves one unit before dispatch |
| redirect hops | 0 | do not follow or change host; 3xx is a transport failure |
| decompressed response bytes | 64 MiB total and 8 MiB per response | streaming/body cap; overflow is failure |

Reservation is an atomic operation over
`(source_attempts, page_dispatches, retries, physical_calls, response_bytes_total)`.  It checks the
global ceiling, the per-page identity, and the retry index before dispatch.  A failed
reservation performs no network call.  An HTTP error, complete-MIME mismatch, WAF/HTML page,
parse error, or body overflow consumes the reservation that was actually dispatched.  A retry
must reserve both the same page/cursor and its one retry slot.

The scheduler is sequential, processes candidates/pages in fixed order, and stops at the first
complete qualified source.  It may try another source only after the prior source has failed
as a whole; it never combines rows.  Exhaustion emits `FX_CALL_BUDGET_GAP`, returns no partial
series, and is not translated to no-data.  Unknown provider rate policy emits
`FX_RATE_POLICY_GAP`; the implementation must not invent a delay or claim a library default.

Each dispatched page/cursor owns one ledger row with `(provider_token, logical_page,
retry_index, dispatch_status, complete_mime, row_count, provider_cursor_or_page_total)`.
The row is created before dispatch, updated exactly once after the response, and may be
retried only with `retry_index=1` for that same logical page.  A missing, duplicate, or
unreconciled row makes the whole source attempt fail; a later source cannot reuse its rows.

### 5.4 Attempt and diagnostic typing

Coverage, attempt, and transport are independent axes:

```text
coverage_status = FULL | PARTIAL | UNKNOWN | NOT_SERVED
attempt_status  = SKIPPED | STARTED | SUCCEEDED | FAILED | BUDGET_EXHAUSTED
transport_status = NOT_RUN | SUCCESS | TIMEOUT | HTTP_ERROR | MIME_ERROR | REDIRECT
                  | BODY_LIMIT | PARSE_ERROR | WAF_OR_HTML
```

Only HTTP 200 with an exact allow-listed complete MIME can be a successful data response.
Every 3xx (redirect disabled), 204, 4xx, and 5xx response is `FX_HTTP_STATUS_UNEXPECTED`;
it is never an empty successful page. DNS, connection, TLS, and timeout failures map to the
single finite offline token `FX_OFFLINE`.  HTML/challenge/WAF bodies map to
`FX_WAF_OR_HTML`; a complete MIME mismatch maps to `FX_MIME_MISMATCH`.  No raw status code,
response body, or exception text is public.

The future public diagnostic contract uses only this closed error token set:

```text
FX_UNSUPPORTED_PAIR
FX_UNSUPPORTED_FREQUENCY
FX_SOURCE_GAP
FX_IDENTITY_GAP
FX_BASIS_GAP
FX_COVERAGE_GAP
FX_COVERAGE_UNKNOWN
FX_TRANSPORT_INCONCLUSIVE
FX_OFFLINE
FX_HTTP_STATUS_UNEXPECTED
FX_MIME_MISMATCH
FX_WAF_OR_HTML
FX_RESPONSE_INVALID
FX_BODY_LIMIT
FX_CALL_BUDGET_GAP
FX_RATE_POLICY_GAP
FX_LEGAL_GAP
```

Finite warning tokens are:

```text
FX_PARTIAL_PROVIDER_BOUNDS
FX_PROVIDER_NONPUBLICATION
FX_REVISION_POSSIBLE
FX_RETRIEVAL_TIME_ONLY
```

Diagnostics may expose canonical provider tokens, typed statuses, integer logical/physical
counts, plain ISO dates, and UTC retrieval time.  They must not expose URLs, query strings,
headers, cookies, credentials, response text, raw exceptions, live rates, or provider prose.
If a future attempt record exists, it must use the canonical provider token and be emitted
only for a real reserved dispatch.  No fabricated empty attempt or diagnostics-truncation
sentinel is permitted.

## 6. Legal/runtime gate

The following rights are separate booleans/decisions, not one `public=true` shortcut:

```text
owner_identity
automated_access
caller_facing_return
storage_or_cache
redistribution
attribution
commercial_use
rate_and_retry
revision_and_correction
```

Every required axis must be `GRANTED` or covered by an explicit licence for the exact route;
`UNKNOWN`, “public page”, “reference only”, and a provider's publication duty are gaps.  The
same source unit must have a stable host/path, no-login access, bounded request policy, and a
written legal posture before it can reach TDD.  Login, paid keys, broker credentials, browser
automation, challenge solving, proxy bypass, cookie reuse, and private endpoints are excluded.

## 7. Conjunctive source-gap reopen criteria

The disposition can change only when all gates below pass for one provider/route/basis tuple:

1. **Transport:** owner response has an exact allow-listed complete MIME parsed after the
   first colon; HTML/WAF/challenge, redirect, truncation, or a generic content type fails.
2. **Identity/basis:** response plus owner documentation prove CNY/VND, VND per 1 CNY, one
   selected field, exact scale, observation date, publication/update meaning, and revision
   behavior; no cross or midpoint.
3. **Coverage:** requested bounds or an independently useful provider-declared PARTIAL are
   proven with reconciled pages/cursors, distinct dates, provider calendar/status, and no
   unreconciled no-row page.
4. **Budget/runtime:** route pagination, rate, retry, redirect, body, and WAF behavior fits
   the single atomic global ledger without date fan-out.
5. **Legal:** all nine legal/runtime axes are explicit for automated access, caller return,
   storage/cache, redistribution, attribution, commercial use, rate/retry, and revisions.
6. **Compatibility:** annual behavior stays byte-compatible; daily output has a typed basis,
   exact dates, finite sanitized diagnostics, and zero-network validation failures.

No one gate may be satisfied by another provider, a facade, a current spot response, a search
snippet, a guessed API key, or an empty response.  Until this conjunction is met, this note
remains SOURCE-GAP CLOSURE and the daily chain remains empty.

## 8. Future RED/release matrix (not authorized now)

Only after a fresh design PASS and an explicit implementation handoff may RED tests be written.
That handoff must cover, at minimum:

- annual USD/VND default and explicit-frequency compatibility, existing snapshots/docs, and
  exact zero-network rejection for unsupported pair/frequency/bounds;
- exact/lower/upper/mixed-case CNY/VND normalization and reversed/unsupported pair rejection;
- direct response identity, one basis/scale/direction, 100-unit positive/negative cases,
  no inversion, midpoint, cross-rate, interpolation, or fill;
- complete MIME/status/effective-route/redirect/HTML-WAF/body-limit failures;
- pagination/count/cursor reconciliation, duplicate/internal-gap/revision cases, full versus
  provider-declared partial versus unknown coverage, and atomic global budget exhaustion;
- exact source/basis/unit/frequency/date/retrieval-time/warning provenance and sanitization;
- `FXHistory` model compatibility, `rate_on()` exact lookup, annual-only `rate_for_year()`,
  DataFrame attrs, repr/equality/serialization/API snapshots, build, docs, and CHANGELOG;
- focused/full offline tests with synthetic fabricated fixtures only, zero-network guards,
  import/version, API/architecture/tutorial checks, blacklist/secret/diff/path/object/clean-tree
  checks, and a second exact-SHA reviewer gate.

This section is a release checklist only.  No RED commit, runtime capability, source
registration, or daily coverage claim is part of #217's source-design handoff.
