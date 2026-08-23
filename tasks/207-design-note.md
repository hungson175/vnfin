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
- H.10 and ECB do not serve a qualifying VND daily cell; Vietcombank is a commercial-bank quote
  with coverage, basis, unknown date-API rate policy, and reuse gaps; World Bank is annual
  period-average only.
- Vietcombank's five-minute statement belongs to its distinct current XML feed. It is not evidence
  for the date API, whose rate policy is unknown; the date API remains `CALL_BUDGET_GAP` and is not
  bulk-crawled.
- No source may be substituted, cross-quoted, stitched, forward-filled, interpolated, or expanded
  from spot/annual data merely to make the requested date span appear complete.

This is a source-gap resolution, not a partial daily release. The current public call continues to
reject `Frequency.DAILY` before network. Only a later exact design PASS followed by an explicit
TDD authorization can change that.

## 2. Annual compatibility invariant

The following must remain compatible while #207 is unresolved and during any later implementation:
annual routing, validation order, returned annual values, exact lookup behavior, and annual
diagnostics remain unchanged. A future basis field is an additive, separately reviewed model
change; it is not covered by a promise of byte-for-byte object identity.

| Contract | Required behavior |
| --- | --- |
| Entry point | Keep `vnfin.fx.history(base="USD", quote="VND", start=None, end=None, *, frequency=Frequency.ANNUAL, http_get=None, timeout=25.0)`. |
| Default | `ANNUAL` remains the default. |
| Annual provider | `WorldBankFXHistorySource`, source `worldbank_fx`, WDI `PA.NUS.FCRF`. |
| Annual meaning | Official annual period-average LCU per US$, VND per 1 USD; not SBV central, not year-end, not daily. |
| Bounds | Existing pre-network validation and inclusive calendar-year filtering remain unchanged. |
| Model | Reuse `FXPoint`/`FXHistory`; keep `unit=value_unit="VND per 1 USD"`, ascending unique points, UTC retrieval timestamp, and sanitized warnings. A future trailing `rate_basis: str | None = None` field is additive and separately reviewed. |
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

The future public model must bind the basis, rather than leaving these tokens as prose:

```python
FXHistory.rate_basis: str | None = None  # trailing field
```

Accepted non-`None` tokens are exactly `official_annual_period_average` and
`official_daily_central_rate`. The future annual factory populates the annual token and the daily
adapter validates/populates the daily token. `to_dataframe()` writes the same value to
`DataFrame.attrs["rate_basis"]`. A future additive `SourceCapability.rate_basis: str | None = None`
field carries the token in the annual and daily capability entries; the current annual registry
entry is not silently mutated before that reviewed API change. The public snapshot, dataclass field
list, constructor compatibility, repr/equality, serialization, docs contract, and CHANGELOG/release
note are one release surface. Existing positional constructors remain valid because the field is
trailing with a default, while intentional token values are covered by the revised snapshots and
tests. A different typed alternative must receive the same explicit review before reopening.

## 4. Future request/result contract (not implemented)

After a separate implementation authorization, a daily call would have to:

1. accept only `USD`/`VND`, `Frequency.DAILY`, and plain `datetime.date` inclusive `start`/`end`;
2. validate pair, frequency, bounds, and the fixed budget before any network call;
3. prove one **fully reconciled retrieval from one qualified provider** contains both literal
   endpoint dates `2018-08-01` and `2026-08-19`; this is not a requirement that one wire response
   contain all rows;
4. return only provider observations in strictly ascending, unique reference-date order, without
   weekend/holiday fabrication or any fill/backfill/interpolation/resampling/nearest match;
5. reject HTML/XML/missing/wrong media type, malformed envelope, duplicate/overlapping pages,
   incomplete page/count reconciliation, wrong pair/direction/basis, out-of-window rows, invalid
   dates, bool/string/non-finite/non-positive rates, a missing requested endpoint, an unexplained
   internal gap, or an empty response; any such condition fails the entire source and returns no
   partial `FXHistory`;
6. parse `NgayBatDau` as an explicit UTC instant and take the date after conversion to
   `Asia/Ho_Chi_Minh`. Keep `NgayBanHanh` separate unless the provider documents it as a typed
   publication timestamp with timezone and revision semantics; and
7. preserve `fetched_at_utc` as retrieval-only, keep `rate_on()` exact, and reject
   `rate_for_year()` for a daily history.

The source response must prove its own identity. A URL, query parameter, title, or assumed field
label cannot establish direction. The future parser must bind the official central-rate definition
and the response's numeric field to `VND per 1 USD`, preserving source scale/rounding rather than
guessing or inverting.

Only provider-owned calendar/status metadata may justify a missing weekend, holiday, or
non-publication date. Those accepted absences use `provider_nonpublication` or `holiday_gap`; an
unexplained internal gap is a hard source failure, not a successful warning. A fully reconciled
retrieval may therefore contain provider-calendar omissions, but it may not be partial.

### 4.1 Deterministic physical budget

The future SBV scheduler is bounded as an explicit contract, not a library-wide retry promise:

| Item | Ceiling/behavior |
| --- | --- |
| Source attempts | one logical source attempt; no incompatible failover |
| Page size | 100, only if the owner-confirmed route accepts it |
| Logical pages | 20 internal slots (`0..19`) mapped to Liferay wire pages `1..20` for the unverified requested-window `totalCount=1947` observation; a reconciled count needing wire page 21 fails before that request |
| Physical HTTP calls | 40 total, including all page calls and retries |
| Retry | at most one reserved retry per page; no hidden transport retries, jitter, concurrency, or page reordering |
| Reservation | atomically reserve `(page, retry_index)` and one physical unit before transport; failed reservation makes zero network calls |
| WAF | HTTP-200 HTML or challenge consumes its reserved unit and is `transport_inconclusive`; after its one retry, stop with no partial output |
| Exhaustion | stop deterministically with `call_budget_gap`; do not fabricate a final attempt, empty success, or coverage absence |
| Rate policy | no numeric delay is claimed until SBV supplies an owner-approved rate limit/pacing policy; without it, the future source is not runnable/qualified |

Liferay's documented query contract is one-based: wire page 1 is the first page. The official
query documentation is
<https://learn.liferay.com/w/dxp/integration/headless-apis/using-liferay-as-a-headless-platform/consuming-apis/api-query-parameters>.
The `totalCount=1947` value was an unverified intake observation from the requested-window
date-filtered query, not an unfiltered or qualified count. The owner-confirmed `page`, `lastPage`,
total/count fields, exact envelope, and successful response family must all be re-proven. A
separate unbounded count scan is prohibited. Logical page counts and physical request counts are
distinct diagnostic metrics; only actual reserved calls increment the physical count.

### 4.2 Transport outcomes and retry ledger

The future runtime must not follow redirects. The effective host and path must match the canonical
SBV route, and the complete normalized `Content-Type` media type must be exactly
`application/json` (lower-case, trimmed media-type portion; parameters do not make HTML/XML JSON).
The following finite table defines which outcomes may consume the one reserved retry:

| Outcome | Internal reason token | Retry? | Result |
| --- | --- | --- | --- |
| Strict HTTP 200 JSON, non-empty body, valid envelope | `ok` | No | Continue deterministic page reconciliation. |
| HTTP-200 HTML matching the observed WAF/challenge signature | `waf_html` | One reserved retry, only with owner-approved pacing | `transport_inconclusive` on exhaustion; never an empty page. |
| Empty body, `204`, wrong/malformed MIME, XML, or other non-JSON body | `empty_body`, `no_content`, or `mime_mismatch` | No | Fail the whole source; no partial result. |
| Any `3xx`, redirect, or effective-host/path mismatch | `redirect` or `effective_route_mismatch` | No | Fail closed; do not follow or infer identity from the redirected route. |
| `429` or `5xx` | `rate_limited` or `server_error` | One reserved retry, only with owner-approved pacing | `transport_inconclusive` on exhaustion; no partial result. |
| Timeout, TLS, connection, or other transport exception | `timeout`, `tls_error`, or `transport_error` | One reserved retry, only with owner-approved pacing | `transport_inconclusive` on exhaustion; no partial result. |
| JSON parse, schema, identity, numeric, duplicate, count/page, endpoint, or gap failure | matching deterministic token | No | Fail the whole source; never retry a bad deterministic payload. |

The runtime must refuse to schedule any request without the owner-approved rate policy; this table
does not invent a delay. Every retry reserves its physical unit before transport. No raw exception,
URL, body, cookie, credential, or provider text is retained.

## 5. Future diagnostics and no-false-absence contract

The annual capability registry remains unchanged in this source-gap commit. A later additive daily
capability entry may report the exact source/basis, full-span boundary, single-source status, and
publication-time limitation. Its reviewed `SourceCapability.rate_basis` must equal the
`FXHistory.rate_basis` token; the current annual entry is not silently rewritten. Until a daily
source qualifies, daily is `unsupported_frequency`, not a claimed coverage gap.

The three layers are distinct:

1. **Offline `RequestDiagnostic.status`** performs no network call and may use only reviewed
   statuses such as `unsupported_frequency`, `unsupported_pair`, `source_gap`, `coverage_gap`, or
   `ok`. It never reports a transport exception. The `sources` entries carry the typed
   `rate_basis` when the additive capability field is reviewed and populated.
2. **Successful `FXHistory.warnings`** contains only provider-calendar/time caveats:
   `provider_nonpublication`, `holiday_gap`, `publication_time_unavailable`, and
   `revision_or_release_lag`. The exact maximum is four tokens. Deduplicate first, then emit in
   that canonical order; never preserve arbitrary provider/order text. A failed retrieval returns
   no `FXHistory` and therefore no warning tuple.
3. **Internal/failure reasons** use only finite tokens from the transport table plus
   `source_gap`, `coverage_gap`, `provider_nonpublication`, `holiday_gap`, `unexplained_gap`, and
   `call_budget_gap`. These reasons are typed/sanitized and never contain a URL, query, response
   body, raw exception, cookie, credential, provider free text, or live rate.

The distinction is mandatory: `transport_inconclusive`, `schema_error`, `identity_mismatch`,
`call_budget_gap`, and `source_gap` are unresolved outcomes, never provider absence; `coverage_gap`
is allowed only after qualified provider evidence; and `provider_nonpublication`/`holiday_gap`
require provider-owned calendar/status evidence. An unexplained internal gap is a hard source
failure, not a successful partial warning. No `SourceAttempt` entry is manufactured for a source
skipped for capability or an unreserved budget unit. A successful single-source result has no
failover-attempt surface.

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
diagnostics, and no-stitch/single-source behavior. The release matrix must additionally cover:

- plain-`date`/datetime/non-date rejection before network, facade/direct-source parity, and all
  annual/default/unsupported-frequency compatibility;
- trailing-field constructor compatibility, annual/daily `rate_basis` guards,
  `DataFrame.attrs["rate_basis"]`, repr/equality/serialization, public API snapshot, and docs
  contract updates;
- import/version checks, blacklist and secret scans, full focused/full offline suites,
  `git diff --check`, and isolated sdist/wheel build;
- documentation, `CHANGELOG`/release-note, and any public API/skill updates required by the
  reviewed additive model change; and
- no live rates, raw provider responses, screenshots, credentials, cookies, or prohibited-source
  material in fixtures, docs examples, build artifacts, or history.

Those are future release gates only. They do not authorize RED tests, production code, push, or
closure in this source-gap round.

**Current result:** preserve the empty daily source chain and annual World Bank behavior; request
review of this docs-only source-gap design, not implementation authorization.
