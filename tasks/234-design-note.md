# #234 provider-native fundamentals report-availability design note

**Phase:** SOURCE_DESIGN
**Disposition:** SOURCE_GAP_CLOSURE
**Clean published base:** 10028e0334aa52987942250f92d5593749f3d77c
**Packet:** tasks/234-fundamentals-report-availability-source-spec.md @ f801d44
**Public triage:** issuecomment-5465144377
**Artifact:** docs/research/2026-08-30-fundamentals-report-availability-source-vetting.md
**Final handoff actor/next:** vnfin-oss-reviewer / RETURN_EXACT_SHA_DESIGN_VERDICT
**Implementation authorization:** none
**Clean-room exclusion:** VNStock and all derived material were excluded; no such result was used.

## Decision

The new provider-native report-availability chain remains empty. Neither VNDirect nor CafeF closes
the exact response semantics, report identity, coverage, legal, and finite-transport gates
conjunctively. This is a source-gap result, not an API or capability claim.

The companion research report is the evidence ledger. It keeps six VNDirect and six CafeF
provider/statement/cadence units independent; separates retained 18 June route evidence from
30 August static pages; and records availability, identity, coverage, transport, budget, and legal
unknowns without inference.

No provider/API route was dispatched for #234. No source, field, model, fixture, RED test,
diagnostic carrier, or runtime code is added.

## Scope and non-substitution contract

This task is only provider-native publication/availability metadata for existing financial
reports. It is not market-session alignment.

The following are binding:

- fiscal_date is fiscal-period end and never availability;
- fetched_at_utc, retrieval time, response time, cache time, current-snapshot time, generic
  updated_at, request EndDate, and audit labels are not availability without exact provider
  semantics;
- a provider modifiedDate or createdDate is a SEMANTICS_GAP until the owner documents it as the
  report's publication/availability field;
- missing remains None; no zero-fill, forward-fill, timezone assumption, session mapping,
  cross-source repair, or derived publication date;
- date-only and explicit-offset datetime values are distinct; naive datetime is invalid;
- request and returned symbol, statement/template, cadence, fiscal date, provider role,
  route/version, and timestamp semantics must be one response-backed atomic report identity;
- a row-level availability value repeated through a paginated report must be exactly equal on all
  rows; disagreement is conflict/failure, never first/last/earliest/latest selection;
- mixed income, balance, and cashflow source observations remain statement-level and do not select
  a single MetricReport.source winner;
- the current 26-metric catalogue, annual/quarterly values, lineage, failover order, and
  caller-side session boundary remain unchanged.

## Source and legal result

### VNDirect

Retained route family:

~~~text
GET https://api-finfo.vndirect.com.vn/v4/financial_statements?q=code:{SYMBOL}~reportType:{ANNUAL|QUARTER}~modelType:{MODEL}&sort=fiscalDate:desc&size={SIZE}&page={PAGE}
~~~

The documentation-only route grammar gate accepts the equals assignments `&size={SIZE}` and
`&page={PAGE}` in both #234 artifacts and rejects any colon assignment immediately after `size` or
`page` (for example, `&size:<value>` or `&page:<value>`). This is a static evidence check only; it
authorizes no provider dispatch, parser, RED test, or API change.

Corporate model identities remain income=2, balance=1, cashflow=3; bank identities remain
income=102, balance=101, cashflow=103. These are existing route identity facts, not a new
availability contract.

Retained candidate fields are fiscalDate, createdDate, and modifiedDate. fiscalDate is the
fiscal-period end. createdDate and modifiedDate are row-level candidate keys whose exact type,
nullability, grammar, timezone/precision, report-level meaning, and all-row agreement were not
re-established in this round. Provider publication semantics are SEMANTICS_GAP.

The official [VNDirect terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/) and
[investor-relations page](https://www.vndirect.com.vn/lien-he/) do not publish a route-specific
public automation, retention, caching, caller-return, rate, or public-OSS redistribution grant.
This remains LEGAL_GAP; retained no-login/browser compatibility is not permission. Candidate
VNDirect archive/navigation labels (posting date/time, Full-Year, Quarter 1-4, period-count, and VND)
are each `NOT_RETAINED` at exact URL plus retained snapshot/blob plus locator granularity, so none is
transferred into the API contract.

### CafeF

Retained route family:

~~~text
GET https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx?Type={1|2|3}&Symbol={SYMBOL}&TotalRow={TOTAL_ROW}&EndDate={ANCHOR}&ReportType={NAM|QUY}&Sort=DESC
~~~

Type 1 and 2 are income and balance route units. Retained Type 3 behavior is an empty/not-served
cashflow control; it is not an authoritative provider nonpublication result.

Time, Year, Quater, and ReportType describe fiscal period/cadence; Conten is an audit/status
label; EndDate is the request anchor. Symbol is not retained as an echoed response identity.
No provider-defined publication/availability field is qualified. CafeF static labels such as
Thời gian gửi, Thời gian cập nhật, article date/time, Cập nhật, and Ngày phát hành remain page or
document metadata with undocumented report binding; Năm, Quý, and Lũy kế 6 tháng remain fiscal or
cadence labels; Định dạng and Tải về remain access affordances. Each candidate label is
`NOT_RETAINED` at exact URL plus retained snapshot/blob plus locator granularity, and none can be
copied into the API contract.

The official [CafeF data-tool guide](https://cafef.vn/du-lieu/ScreenerHelper.aspx) describes
historical lookup, sharing, and export for site users. [CafeF robots](https://cafef.vn/robots.txt)
is crawl guidance only. Neither establishes programmatic automation, retention, caching, caller
return, rate, or public-OSS redistribution. Legal outcome remains LEGAL_GAP.

All six VNDirect and six CafeF route units explicitly carry
`terms_version=NOT_RETAINED` and `terms_effective_date=NOT_RETAINED`; no provider-wide term fact is
transferred across a route, statement, or cadence unit.

## Qualification and coverage

The research ledger records historical value-route examples separately:

- VNDirect annual retained example: FPT fiscal history to 2002-12-31; no retained distinct-period
  count for availability.
- VNDirect quarterly retained example: a 2026-03-31 fiscal example; no current availability
  bound or distinct-period count.
- CafeF annual income retained example: 25 value-blind periods to 2001.
- CafeF quarterly income retained example: 85 value-blind periods to Q1 2006.
- CafeF balance retained evidence includes a 71-period quarterly example.
- CafeF cashflow Type 3 is retained as a negative route control.

These are historical value-route facts, not current provider availability bounds. Annual and
quarterly availability must be qualified independently. FULL requires provider-declared bounds
and complete reconciliation; PARTIAL requires a provider-declared narrower bound and reconciliation;
empty, parser failure, or unreconciled pagination is not proof of nonpublication.

## Typed transport and budget boundary

No #234 provider route was dispatched. Candidate logical/physical dispatch is
NOT_DISPATCHED; retries, redirects, bytes, status headers, and complete MIME are NOT_MEASURED or
NOT_RETAINED, not fabricated zeros.

A future reviewer-approved finite plan must reserve atomically before each dispatch:

- logical and physical requests;
- documents/pages;
- retries and backoff waits;
- redirects;
- compressed and decompressed bytes;
- concurrency and rate-window slots; and
- bounded sanitized diagnostic entries.

Retries charge the same reservation. Any exhaustion, redirect/decompression limit, unexpected
status/MIME, identity mismatch, duplicate/correction conflict, or unreconciled pagination
discards private partial state and returns no partial public result. It must not fabricate an
attempt, truncation marker, success, or nonpublication outcome. No numeric budget is promised by
this design.

## Deferred API/model seam

No public field is added now. If a future exact design qualifies a route, prefer an additive typed
availability observation attached to StatementProvenance/provider role rather than a single
MetricReport.source. The future type must carry exact provider/route/report identity, semantic
kind, precision, date-only versus explicit-offset datetime, nullable value, and conflict state.

It must preserve mixed-source statement provenance, exact repeated-row equality, fail-closed
malformed values, serialization/DataFrame behavior, diagnostics, cache and failover contracts,
API snapshot, docs, packaging, and compatibility. This paragraph freezes no API, model, enum, or
source registration.

## Deferred RED and release gates

RED is not authorized. After a separate exact design PASS, a fresh RED review would be required for:

- annual/quarterly timezone-aware timestamps and date-only round trips;
- absent/null without fiscal/retrieval/update fallback;
- malformed, padded, naive, impossible, non-finite, and wrong-type values;
- exact symbol/statement/cadence/fiscal/provider binding;
- repeated-row equality and duplicate-page conflict;
- same-source/mixed-source observations and provider disagreement;
- no arbitrary earliest/latest/min/max or session conversion;
- unchanged 26 metrics, lineage, failover order, signatures, cache keys, annual/quarterly order,
  and no-login behavior;
- DataFrame/serialization/diagnostics/docs/API snapshot/security/blacklist/build/wheel/sdist.

Fixtures would be fabricated and offline only. No provider row, endpoint, credential, or network
call enters tests.

## Source-gap reopen gate

Reopen only when all following are proven for each exact route unit:

1. Provider-owned docs bind an exact field to public report availability.
2. Retained response proves exact key/type/nullability/grammar/timezone/precision and response
   identity.
3. Annual and quarterly, statement/template, symbol, and route/version identity are atomic.
4. Repeated row-level values agree across all pages; pagination, duplicates, corrections, and
   revisions reconcile.
5. Provider-declared bounds, cadence, nonpublication, and value-blind counts are complete.
6. Status/complete MIME/redirect/decompression/retry/byte/rate/concurrency behavior fits a finite
   reviewer-approved plan with atomic no-partial results.
7. Route-local written rights cover automation, caller return, caching, storage, retention,
   deletion, attribution, commercial/derivative use, and redistribution.
8. A separate API/model design PASS precedes RED, implementation, code review, and release.

Until then: SOURCE_GAP_CLOSURE, empty new chain, unchanged current runtime/API, and no early work.

## Lifecycle and allowed transition

This source/design handoff follows the verified intake:

- packet f801d44;
- public receipt issuecomment-5465144377;
- clean published base 10028e0334aa52987942250f92d5593749f3d77c;
- intake/backlog commit 95466ac76ba1ab71e7c9de787b94b635de2077c4;
- actor at intake vnfin-oss, next PREPARE_EXACT_SHA_SOURCE_DESIGN.

After the exact artifact and backlog handoff, the reviewer-owned next action is
RETURN_EXACT_SHA_DESIGN_VERDICT. A design PASS, if granted, would authorize only the reviewed
next transition. This handoff authorizes no probe, RED, API/model change, code, source
registration, push, or close.

### Bottom summary

- #234 is SOURCE_GAP_CLOSURE with an empty new availability chain.
- VNDirect createdDate/modifiedDate are SEMANTICS_GAP; fiscalDate remains fiscal-period end.
- CafeF has no qualified availability field; fiscal/audit/request fields cannot substitute.
- Value-route history examples are retained and value-blind, not current availability bounds.
- The VNDirect route requires equals query assignments; the static gate rejects colon separators.
- Static labels and all twelve terms version/effective-date fields remain `NOT_RETAINED` without
  exact retained locators.
- Route-local legal automation, retention, cache, caller-return, and redistribution rights remain open.
- Current values, 26 metrics, failover order, and session boundary are unchanged.
- RED, API/model changes, code, probes, source registration, push, and close are not authorized.
- Final reviewer action: return the exact-SHA design verdict.
