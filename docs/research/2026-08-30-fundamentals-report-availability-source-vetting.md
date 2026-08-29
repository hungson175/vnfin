# Issue #234 — provider-native fundamentals report-availability source vetting

**Research cut:** 30 August 2026 (UTC+7)
**Packet:** tasks/234-fundamentals-report-availability-source-spec.md @ f801d44
**Clean published base:** 10028e0334aa52987942250f92d5593749f3d77c
**Builder phase:** SOURCE_DESIGN
**Disposition:** SOURCE_GAP_CLOSURE; new availability chain remains empty
**Observation mode:** retained evidence plus official static pages only; no provider API dispatch
**Clean-room exclusion:** VNStock and all derived material were excluded; no such result was opened or cited.

This is a source, legal, and design qualification record. It adds no source, endpoint, model,
API field, fixture, provider row, RED test, or runtime capability.

## 1. Decision

Neither the retained VNDirect route nor the retained CafeF route qualifies for a new
provider-native report-availability field.

The two routes provide existing fiscal statements in the current library, but this task asks for
a different primitive: a publication or availability date whose meaning is established by the
provider and bound to the same report. The qualification intersection is not closed:

1. VNDirect exposes retained candidate keys named createdDate and modifiedDate, but their
   publication, ingestion, correction, or availability meaning is not documented.
2. CafeF's retained statement shape exposes fiscal-period and audit-label fields, but no retained
   provider-defined publication or availability field.
3. Request anchors, fiscal dates, retrieval time, response time, cache time, generic update time,
   and revision time cannot be relabelled as first availability.
4. Existing static terms and pages do not grant route-local no-login automation, retention,
   caching, caller return, or redistribution for public OSS.
5. Coverage of statement values does not establish coverage of availability metadata.

The correct result is documentation-only SOURCE_GAP_CLOSURE. Existing annual/quarterly value
sources and failover order remain unchanged. The new chain has no members, and no mostly-None
public field is introduced.

## 2. Clean-room and method boundary

The required project blacklist was read before this task. Searches used the required negative
terms; no blacklisted or derived material was opened, cited, copied, installed, or used. The
source set is limited to:

- official VNDirect pages and the VNDirect route shape already retained in the repository;
- official CafeF pages, guidance, robots document, and the CafeF route shape already retained;
- immutable local source/provenance documents from the 18 June 2026 research round.

No new provider request, query-bearing endpoint call, curl request, browser session, login,
registration, download, cookie, token, header capture, response body, raw financial row, or live
candidate dispatch was performed for #234.

A page read on 30 August 2026 is static evidence only. Retained route observations are historical
project evidence and are not a current response recheck.

### 2.1 Evidence references

| Evidence ID | Evidence | Date/state | Use and limit |
|---|---|---|---|
| RET-VD-20260618 | docs/research/2026-06-18-vn-fundamental-data-sources.md @ ce6a97ab553004714c5ae9fb4de07ce262f99698 | retained response-shape research | VNDirect route/shape/period/bound context; no new availability proof |
| RET-CF-20260618 | docs/research/2026-06-18-vn-fundamental-data-sources.md @ ce6a97ab553004714c5ae9fb4de07ce262f99698 | retained response-shape research | CafeF route/shape/period/bound context; no new availability proof |
| SRC-VD | docs/sources/fundamentals-vndirect.md @ 7437ec38ee5a558c5c57e6f4a90b22e99548f6ef | immutable source note | current adapter compatibility facts; no new dispatch |
| SRC-CF | docs/sources/fundamentals-cafef.md @ a90527802bce9d6a6b20c83ca759a6fb04585bad | immutable source note | current adapter compatibility facts; no new dispatch |
| WEB-VD-TERMS | VNDIRECT online-application terms | static page read 2026-08-30 | official disclaimer/copyright context; not an API reuse grant |
| WEB-VD-IR | VNDIRECT contact/investor-relations page | static page read 2026-08-30 | official annual/quarterly report-navigation context; not API semantics |
| WEB-CF-GUIDE | CafeF data-tool guidance | static page read 2026-08-30 | public data/history/export context; not an automation licence |
| WEB-CF-ROBOTS | CafeF robots document | static page read 2026-08-30 | crawl instruction only; not a reuse or redistribution grant |

## 3. Official source references

These official pages are provenance, not permission to automate or redistribute.

- [VNDirect online-application terms](https://www.vndirect.com.vn/dieu-khoan-su-dung/)
  discuss website information, disclaimers, access data, and copyright. They do not publish exact
  API candidate-timestamp semantics or a public OSS data licence.
- [VNDirect contact and investor-relations page](https://www.vndirect.com.vn/lien-he/) links
  annual and quarterly financial-report areas. It does not define API response fields,
  publication timestamp, rate policy, or redistribution rights.
- [VNDirect financial-statements route family](https://api-finfo.vndirect.com.vn/v4/financial_statements)
  is recorded only as a sanitized route template below; no request was made here.
- [CafeF data-tool guidance](https://cafef.vn/du-lieu/ScreenerHelper.aspx) describes public
  historical lookup and export features for site users. It does not define a public API contract
  or redistribution grant.
- [CafeF robots document](https://cafef.vn/robots.txt) was read as a crawl-policy document.
  An Allow directive is not permission to automate, retain, cache, return, commercially use, or
  redistribute financial data.
- [CafeF FinanceReport route family](https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx)
  is recorded only as a sanitized route template below; no request was made here.

The official pages establish owner/site context, not a qualified availability field. Absence of a
grant is recorded as a legal gap, not as a legal opinion.

## 4. Qualification vocabulary

The following labels are binding:

- RESPONSE_SHAPE_RETAINED means old project evidence records a response shape, not that #234
  re-dispatched the route.
- STATIC_DOCUMENTED means an official page describes a site, product, or user-facing function.
- SEMANTICS_GAP means a key or label is observed but the provider has not defined the requested
  publication/availability meaning for that exact route.
- NOT_RETAINED means this round did not preserve the requested detail; it is not proof of absence.
- NOT_MEASURED means no counter or header telemetry was collected.
- LEGAL_GAP means no route-local public grant was found in the reviewed official material.
- SOURCE_GAP means at least one mandatory qualification axis remains open.
- SOURCE_GAP_CLOSURE means the new chain is intentionally empty and current behavior is retained.

No label permits inference from a request parameter, field name, page title, fiscal period, or
generic timestamp.

## 5. Independent route-unit inventory

The qualification unit is one provider, route family, statement kind, cadence, route-version
state, and exact response identity. The six VNDirect rows and six CafeF rows below are independent.
A field or legal result from one row cannot qualify another row.

### 5.1 Unit ledger

| Unit | Provider, owner, operator | Canonical sanitized route and method | Evidence and dispatch state | Response identity and period | Availability field result | Coverage result | Legal result | Outcome |
|---|---|---|---|---|---|---|---|---|
| VD-A-INC | provider=VNDirect; owner=VNDIRECT; operator=api-finfo; underlying publisher=NOT_RETAINED | GET https://api-finfo.vndirect.com.vn/v4/financial_statements?q=code:{SYMBOL}~reportType:ANNUAL~modelType:{MODEL}&sort=fiscalDate:desc&size:{SIZE}&page:{PAGE} | RET-VD-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=code; statement=income; model=corporate 2 or bank 102; unit=(code,reportType,modelType,fiscalDate); cadence=ANNUAL; fiscal=fiscalDate; pagination=currentPage/totalPages/size | fiscalDate=period-end only; createdDate and modifiedDate=row-level candidates; semantics=SEMANTICS_GAP; report-level equality=NOT_RETAINED | retained FPT annual bound reaches 2002-12-31; distinct-period count=NOT_RETAINED; provider availability bounds=NOT_RETAINED; all-symbol coverage=NOT_PROVEN | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-VD-TERMS; rights=LEGAL_GAP | SOURCE_GAP |
| VD-A-BAL | provider=VNDirect; owner=VNDIRECT; operator=api-finfo; underlying publisher=NOT_RETAINED | GET https://api-finfo.vndirect.com.vn/v4/financial_statements?q=code:{SYMBOL}~reportType:ANNUAL~modelType:{MODEL}&sort=fiscalDate:desc&size:{SIZE}&page:{PAGE} | RET-VD-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=code; statement=balance; model=corporate 1 or bank 101; unit=(code,reportType,modelType,fiscalDate); cadence=ANNUAL; fiscal=fiscalDate; pagination=currentPage/totalPages/size | fiscalDate=period-end only; createdDate and modifiedDate=row-level candidates; semantics=SEMANTICS_GAP; report-level equality=NOT_RETAINED | retained FPT/VCB annual value-route context only; distinct-period count=NOT_RETAINED; availability bounds=NOT_RETAINED | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-VD-TERMS; rights=LEGAL_GAP | SOURCE_GAP |
| VD-A-CF | provider=VNDirect; owner=VNDIRECT; operator=api-finfo; underlying publisher=NOT_RETAINED | GET https://api-finfo.vndirect.com.vn/v4/financial_statements?q=code:{SYMBOL}~reportType:ANNUAL~modelType:{MODEL}&sort=fiscalDate:desc&size:{SIZE}&page:{PAGE} | RET-VD-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=code; statement=cashflow; model=corporate 3 or bank 103; unit=(code,reportType,modelType,fiscalDate); cadence=ANNUAL; fiscal=fiscalDate; pagination=currentPage/totalPages/size | fiscalDate=period-end only; createdDate and modifiedDate=row-level candidates; semantics=SEMANTICS_GAP; report-level equality=NOT_RETAINED | retained cashflow shape only; distinct-period count=NOT_RETAINED; availability bounds=NOT_RETAINED | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-VD-TERMS; rights=LEGAL_GAP | SOURCE_GAP |
| VD-Q-INC | provider=VNDirect; owner=VNDIRECT; operator=api-finfo; underlying publisher=NOT_RETAINED | GET https://api-finfo.vndirect.com.vn/v4/financial_statements?q=code:{SYMBOL}~reportType:QUARTER~modelType:{MODEL}&sort=fiscalDate:desc&size:{SIZE}&page:{PAGE} | RET-VD-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=code; statement=income; model=corporate 2 or bank 102; unit=(code,reportType,modelType,fiscalDate); cadence=QUARTER; fiscal=fiscalDate; pagination=currentPage/totalPages/size | fiscalDate=period-end only; createdDate and modifiedDate=row-level candidates; semantics=SEMANTICS_GAP; report-level equality=NOT_RETAINED | retained quarterly example reaches 2026-03-31; distinct-period count=NOT_RETAINED; availability bounds=NOT_RETAINED | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-VD-TERMS; rights=LEGAL_GAP | SOURCE_GAP |
| VD-Q-BAL | provider=VNDirect; owner=VNDIRECT; operator=api-finfo; underlying publisher=NOT_RETAINED | GET https://api-finfo.vndirect.com.vn/v4/financial_statements?q=code:{SYMBOL}~reportType:QUARTER~modelType:{MODEL}&sort=fiscalDate:desc&size:{SIZE}&page:{PAGE} | RET-VD-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=code; statement=balance; model=corporate 1 or bank 101; unit=(code,reportType,modelType,fiscalDate); cadence=QUARTER; fiscal=fiscalDate; pagination=currentPage/totalPages/size | fiscalDate=period-end only; createdDate and modifiedDate=row-level candidates; semantics=SEMANTICS_GAP; report-level equality=NOT_RETAINED | retained quarterly value-route context only; distinct-period count=NOT_RETAINED; availability bounds=NOT_RETAINED | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-VD-TERMS; rights=LEGAL_GAP | SOURCE_GAP |
| VD-Q-CF | provider=VNDirect; owner=VNDIRECT; operator=api-finfo; underlying publisher=NOT_RETAINED | GET https://api-finfo.vndirect.com.vn/v4/financial_statements?q=code:{SYMBOL}~reportType:QUARTER~modelType:{MODEL}&sort=fiscalDate:desc&size:{SIZE}&page:{PAGE} | RET-VD-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=code; statement=cashflow; model=corporate 3 or bank 103; unit=(code,reportType,modelType,fiscalDate); cadence=QUARTER; fiscal=fiscalDate; pagination=currentPage/totalPages/size | fiscalDate=period-end only; createdDate and modifiedDate=row-level candidates; semantics=SEMANTICS_GAP; report-level equality=NOT_RETAINED | retained quarterly cashflow context only; distinct-period count=NOT_RETAINED; availability bounds=NOT_RETAINED | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-VD-TERMS; rights=LEGAL_GAP | SOURCE_GAP |
| CF-A-INC | provider=CafeF; owner=CafeF/VCCorp identity; operator=cafef.vn; upstream publisher=NOT_RETAINED | GET https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx?Type=1&Symbol={SYMBOL}&TotalRow={TOTAL_ROW}&EndDate={YEAR}&ReportType=NAM&Sort=DESC | RET-CF-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=NOT_RETAINED; statement=income; Type=1; unit=(request Symbol,Type,ReportType,Year,Quater); cadence=NAM/ANNUAL; fiscal=derived from Year; pagination=TotalRow/Count; response identity=IDENTITY_GAP | Time/Year/Quater/ReportType/Conten are fiscal or audit/status fields; EndDate=request anchor; publication/availability=NOT_RETAINED; semantics=SEMANTICS_GAP | retained FPT annual example=25 periods to 2001; value-blind distinct-period count=25; provider availability bounds=NOT_RETAINED; not current | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; robots=ALLOW_ALL_OBSERVED_NOT_LICENCE; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-CF-GUIDE/WEB-CF-ROBOTS; rights=LEGAL_GAP | SOURCE_GAP |
| CF-A-BAL | provider=CafeF; owner=CafeF/VCCorp identity; operator=cafef.vn; upstream publisher=NOT_RETAINED | GET https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx?Type=2&Symbol={SYMBOL}&TotalRow={TOTAL_ROW}&EndDate={YEAR}&ReportType=NAM&Sort=DESC | RET-CF-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=NOT_RETAINED; statement=balance; Type=2; unit=(request Symbol,Type,ReportType,Year,Quater); cadence=NAM/ANNUAL; fiscal=derived from Year; pagination=TotalRow/Count; response identity=IDENTITY_GAP | Time/Year/Quater/ReportType/Conten are fiscal or audit/status fields; EndDate=request anchor; publication/availability=NOT_RETAINED; semantics=SEMANTICS_GAP | retained balance count/bound=NOT_RETAINED; no current claim | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; robots=ALLOW_ALL_OBSERVED_NOT_LICENCE; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-CF-GUIDE/WEB-CF-ROBOTS; rights=LEGAL_GAP | SOURCE_GAP |
| CF-A-CF | provider=CafeF; owner=CafeF/VCCorp identity; operator=cafef.vn; upstream publisher=NOT_RETAINED | GET https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx?Type=3&Symbol={SYMBOL}&TotalRow={TOTAL_ROW}&EndDate={YEAR}&ReportType=NAM&Sort=DESC | RET-CF-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=NOT_RETAINED; statement=cashflow; Type=3; retained route note=empty/not served; response identity=UNPROVEN; cadence=NAM/ANNUAL | no positive availability field; empty route is not authoritative nonpublication or provider absence | value-blind count=NOT_APPLICABLE for retained negative route; no current probe | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; robots=ALLOW_ALL_OBSERVED_NOT_LICENCE; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-CF-GUIDE/WEB-CF-ROBOTS; rights=LEGAL_GAP | SOURCE_GAP |
| CF-Q-INC | provider=CafeF; owner=CafeF/VCCorp identity; operator=cafef.vn; upstream publisher=NOT_RETAINED | GET https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx?Type=1&Symbol={SYMBOL}&TotalRow={TOTAL_ROW}&EndDate={QUARTER_YEAR}&ReportType=QUY&Sort=DESC | RET-CF-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=NOT_RETAINED; statement=income; Type=1; unit=(request Symbol,Type,ReportType,Year,Quater); cadence=QUY/QUARTER; fiscal=derived from Year/Quater; pagination=TotalRow/Count; response identity=IDENTITY_GAP | Time/Year/Quater/ReportType/Conten are fiscal or audit/status fields; EndDate=request anchor; publication/availability=NOT_RETAINED; semantics=SEMANTICS_GAP | retained FPT quarterly example=85 periods to Q1 2006; value-blind distinct-period count=85; provider availability bounds=NOT_RETAINED; not current | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; robots=ALLOW_ALL_OBSERVED_NOT_LICENCE; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-CF-GUIDE/WEB-CF-ROBOTS; rights=LEGAL_GAP | SOURCE_GAP |
| CF-Q-BAL | provider=CafeF; owner=CafeF/VCCorp identity; operator=cafef.vn; upstream publisher=NOT_RETAINED | GET https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx?Type=2&Symbol={SYMBOL}&TotalRow={TOTAL_ROW}&EndDate={QUARTER_YEAR}&ReportType=QUY&Sort=DESC | RET-CF-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=NOT_RETAINED; statement=balance; Type=2; unit=(request Symbol,Type,ReportType,Year,Quater); cadence=QUY/QUARTER; fiscal=derived from Year/Quater; pagination=TotalRow/Count; response identity=IDENTITY_GAP | Time/Year/Quater/ReportType/Conten are fiscal or audit/status fields; EndDate=request anchor; publication/availability=NOT_RETAINED; semantics=SEMANTICS_GAP | retained balance quarterly example=71 periods; annual count=NOT_RETAINED; availability bounds=NOT_RETAINED | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; robots=ALLOW_ALL_OBSERVED_NOT_LICENCE; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-CF-GUIDE/WEB-CF-ROBOTS; rights=LEGAL_GAP | SOURCE_GAP |
| CF-Q-CF | provider=CafeF; owner=CafeF/VCCorp identity; operator=cafef.vn; upstream publisher=NOT_RETAINED | GET https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx?Type=3&Symbol={SYMBOL}&TotalRow={TOTAL_ROW}&EndDate={QUARTER_YEAR}&ReportType=QUY&Sort=DESC | RET-CF-20260618; response=RESPONSE_SHAPE_RETAINED; status=NOT_RETAINED; complete_mime=NOT_RETAINED; redirects=NOT_RETAINED; #234_dispatch=NONE | requested_symbol={SYMBOL}; returned_symbol=NOT_RETAINED; statement=cashflow; Type=3; retained route note=empty/not served; response identity=UNPROVEN; cadence=QUY/QUARTER | no positive availability field; empty route is not authoritative nonpublication or provider absence | value-blind count=NOT_APPLICABLE for retained negative route; no current probe | automation=UNRESOLVED; cache=UNRESOLVED; retention=UNRESOLVED; caller_return=UNRESOLVED; attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED; redistribution=NO_PUBLISHED_GRANT; robots=ALLOW_ALL_OBSERVED_NOT_LICENCE; rate_retry_backoff=NOT_RETAINED; legal_ref=WEB-CF-GUIDE/WEB-CF-ROBOTS; rights=LEGAL_GAP | SOURCE_GAP |

The Type=3 CafeF rows are negative retained route evidence, not new observations. An empty
response is not classified as authoritative nonpublication because the route does not expose the
required provider identity and availability semantics.

### 5.2 Route-specific conclusions

- VNDirect is tall: one response row represents a line item and fiscal period. Any candidate
  timestamp repeated across rows would have to be exactly equal for the complete report after
  pagination. Equality was not rechecked.
- CafeF is period-object based. The request Symbol is not sufficient to prove returned provider
  identity. Time, Year, Quater, and ReportType describe fiscal periods; Conten is audit/status;
  EndDate is a retrieval anchor.
- Old evidence supports selected annual and quarterly value retrieval only. It does not establish
  current all-symbol availability coverage, publication dates, or first-known dates.
- Ratios and ratio-specific routes are outside this report. No ratio availability semantics are
  borrowed for statement routes.
- Static page reads are not candidate API dispatches. The #234 candidate API dispatch state is
  typed NOT_DISPATCHED, not zero.

## 6. Candidate-field ledger

Every candidate field is recorded with key, retained type status, nullability, grammar,
timezone/precision, level, and semantics. Unknown details stay explicit.

### 6.1 VNDirect

| Exact key | Retained type | Nullability | Grammar, timezone, precision | Level and agreement | Provider semantics | Use |
|---|---|---|---|---|---|---|
| fiscalDate | string in retained shape | NOT_RETAINED | date-only ISO form; timezone=N/A; precision=day | row-level fiscal identity; report grouping; not availability | no provider binding to publication | FISCAL_PERIOD_END_ONLY |
| createdDate | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | row-level candidate; complete-report equality=NOT_RETAINED | SEMANTICS_GAP | never substitute |
| modifiedDate | NOT_RETAINED | NOT_RETAINED | NOT_RETAINED | row-level candidate; complete-report equality=NOT_RETAINED | SEMANTICS_GAP | never substitute |
| reportType | string in retained shape | NOT_RETAINED | ANNUAL/QUARTER route identity; timezone=N/A | report/cadence identity; not availability | retained adapter mapping only | cadence |
| modelType | numeric in retained shape | NOT_RETAINED | corporate/bank model mapping retained; timezone=N/A | report/template identity; not availability | retained adapter mapping only | template |
| publishedAt, publicationDate, availableAt, releaseDate, asOf, updatedAt | NOT_RETAINED as exact keys | NOT_RETAINED | NOT_RETAINED | level/agreement=NOT_RETAINED | no reviewed provider definition | not qualified |

### 6.2 CafeF

| Exact key or label | Retained type | Nullability | Grammar, timezone, precision | Level and agreement | Provider semantics | Use |
|---|---|---|---|---|---|---|
| Time | string in retained shape | NOT_RETAINED | provider period label; timezone=N/A | period-object fiscal identity | no availability definition | fiscal context |
| Year | integer in retained shape | NOT_RETAINED | calendar-year component; timezone=N/A | period-object fiscal identity | no availability definition | fiscal context |
| Quater | integer in retained shape | NOT_RETAINED | 0 or 1..4 in retained shape; timezone=N/A | period-object fiscal identity | no availability definition | fiscal context |
| ReportType | string in retained statement shape | NOT_RETAINED | NAM/QUY route identity; timezone=N/A | period-object cadence identity | no availability definition | cadence |
| Conten | string/nullability NOT_RETAINED | NOT_RETAINED | audit/status text; timezone=N/A | period-object descriptive label | no availability definition | audit context |
| Symbol | not echoed in retained shape | NOT_RETAINED | NOT_RETAINED | request-only identity; response identity gap | no provider definition | cannot qualify identity |
| EndDate | request parameter | NOT_APPLICABLE | newest retrieval anchor; timezone=N/A | request-level | no availability definition | never publication time |
| publishedAt, publicationDate, availableAt, releaseDate, asOf, updatedAt | NOT_RETAINED as exact keys | NOT_RETAINED | NOT_RETAINED | level/agreement=NOT_RETAINED | no reviewed provider definition | not qualified |

### 6.3 Static-page candidate labels

The static official pages expose additional human-facing labels. Each is kept separate from the
API response-field ledger and is not transferred into a provider response or availability field.

| Provider / page | Exact visible label or metadata | Retained type and grammar | Level and identity | Provider meaning | Disposition |
|---|---|---|---|---|---|
| VNDirect annual/quarterly archive | posting date/time on an archive entry | human-rendered date/time; exact machine type, timezone, precision, nullability=NOT_RETAINED | VNDIRECT's own disclosure/archive entry; not arbitrary-symbol API report identity | archive posting semantics not bound to api-finfo availability | STATIC_DOCUMENTED; SEMANTICS_GAP |
| VNDirect financial-report navigation | Full-Year, Quarter 1-4, period-count and VND labels | human-rendered labels; exact schema=NOT_RETAINED | investor-relations presentation identity | period/cadence and unit context only | not availability |
| CafeF disclosure list | Thời gian gửi | human-rendered date/time; exact type, timezone, precision, nullability=NOT_RETAINED | disclosure-list item; upstream sender, CafeF ingestion, and API report binding=NOT_RETAINED | semantics not defined as first public availability | STATIC_DOCUMENTED; SEMANTICS_GAP |
| CafeF document list | Thời gian cập nhật | human-rendered label; exact machine type and semantics=NOT_RETAINED | document-list item | not bound to API report availability or revision | STATIC_DOCUMENTED; SEMANTICS_GAP |
| CafeF document/article pages | page or article date/time and Thời gian | human-rendered page metadata; timezone and precision=NOT_RETAINED | page/disclosure article, not response report unit | no provider definition tying it to public financial-data availability | SEMANTICS_GAP |
| CafeF company page | Cập nhật | human-rendered quote/current-snapshot label | quote/profile context, not statement identity | cannot substitute for report availability | reject as availability |
| CafeF report navigation | Năm, Quý, Theo quý, Theo năm, Lũy kế 6 tháng, Qn/YYYY, CN/YYYY | period labels; timezone=N/A | fiscal/cadence identity | period selection only | fiscal context only |
| CafeF document page | Định dạng and Tải về | file/access affordances; no availability type | document access context | access indicator only; no reuse permission | not availability |
| CafeF analysis-report pages | Ngày phát hành | page-family label outside the financial-statement route | analysis-report identity, not statement response identity | semantics cannot be borrowed across report families | not qualified |

The exact static sources are [VNDirect annual archive](https://www.vndirect.com.vn/danh_muc_bao_cao/thong-tin-tai-chinh/?key=bao-cao-tai-chinh-hang-nam), [VNDirect quarterly archive](https://www.vndirect.com.vn/danh_muc_bao_cao/thong-tin-tai-chinh/?key=bao-cao-tai-chinh-hang-quy), [CafeF disclosure landing](https://cafef.vn/du-lieu/cong-bo-thong-tin.chn), [CafeF announcement reports](https://cafef.vn/du-lieu/announcement-reports.chn), and [CafeF financial landing](https://cafef.vn/du-lieu/BaoCaoTaiChinh.aspx). Static labels prove presentation only.

The tables do not assert that an unretained key can never exist. They record that this clean-room
round has no response-backed and provider-documented candidate.

## 7. Coverage and identity boundaries

Coverage is independent for each provider, statement, and cadence. Historical examples are not
promoted to current availability coverage.

| Provider unit | Value-route evidence | Availability coverage | Identity limitation | Disposition |
|---|---|---|---|---|
| VNDirect annual | FPT annual example reaches fiscal 2002-12-31; exact period count not retained | provider bounds, publication bounds, nonpublication calendar, current upper bound NOT_RETAINED | complete current identity not rechecked | SOURCE_GAP |
| VNDirect quarterly | retained example reaches fiscal 2026-03-31; exact period count not retained | same gaps; no current upper-bound claim | timestamp agreement not rechecked | SOURCE_GAP |
| CafeF annual income | FPT example has 25 fiscal periods to 2001 | publication bounds and current upper bound NOT_RETAINED | request Symbol not response echo | SOURCE_GAP |
| CafeF quarterly income | FPT example has 85 fiscal periods to Q1 2006 | publication bounds and current upper bound NOT_RETAINED | request Symbol not response echo | SOURCE_GAP |
| CafeF balance routes | retained evidence includes a 71-period quarterly example | annual/availability bounds NOT_RETAINED | same response-identity gap | SOURCE_GAP |
| CafeF cashflow | Type=3 retained as empty/not served | not authoritative nonpublication | no qualified response identity | SOURCE_GAP |

The counts are value-blind period counts from retained project evidence, not values and not new
measurements. They do not prove all symbols, statements, or periods share the same bound. No
current upper bound, pagination reconciliation, duplicate policy, correction/revision policy, or
publication calendar was newly established.

FULL requires provider-declared bounds plus complete period and page reconciliation. PARTIAL
requires a provider-declared narrower bound plus reconciliation. Empty, parser failure, or
unreconciled page is not proof of no report or no publication.

## 8. Legal, access, and reuse assessment

This assessment is route-local and per provider. Public visibility is not a licence.

### 8.1 VNDirect

- The official online-application terms discuss website information, disclaimers, access data,
  and copyright. They do not publish a route-specific API schema, no-login automation grant,
  quota/rate policy, cache/retention right, caller-facing return right, or public-OSS
  redistribution licence.
- The official investor-relations page navigates to VNDIRECT's own annual and quarterly reports.
  It does not prove that the finfo route has the same document function or availability semantics.
- The retained source note describes the API as intended for web/app clients and records no
  published redistribution grant. This remains a conservative route-local legal gap.
- Retained no-login/browser compatibility is transport context only, not permission.
- Per-unit status: automation=UNRESOLVED; transient_use=UNRESOLVED; cache=UNRESOLVED;
  storage=UNRESOLVED; retention=UNRESOLVED; deletion=UNRESOLVED; caller_return=UNRESOLVED;
  attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED;
  redistribution=NO_PUBLISHED_GRANT; rate=NOT_RETAINED; retry=NOT_RETAINED;
  backoff=NOT_RETAINED; amendment=NOT_RETAINED; revocation=NOT_RETAINED;
  correction=NOT_RETAINED; outcome=LEGAL_GAP.

### 8.2 CafeF

- The official data-tool guide describes historical lookup, sharing of saved filters, and Excel
  export for site users. These user-facing features do not establish programmatic automation,
  storage, retention, caller-return, commercial, derivative, or redistribution rights.
- The official robots document exposes an Allow directive and sitemap entries. This is crawl
  guidance only; it does not grant an API, rate quota, retention right, or public-OSS
  redistribution right.
- The retained source note records the AJAX handler as a site-data route with no published
  redistribution grant. This remains a legal gap.
- Per-unit status: automation=UNRESOLVED; transient_use=UNRESOLVED; cache=UNRESOLVED;
  storage=UNRESOLVED; retention=UNRESOLVED; deletion=UNRESOLVED; caller_return=UNRESOLVED;
  attribution=UNRESOLVED; commercial=UNRESOLVED; derivative=UNRESOLVED;
  redistribution=NO_PUBLISHED_GRANT; robots=ALLOW_ALL_OBSERVED_NOT_LICENCE;
  rate=NOT_RETAINED; retry=NOT_RETAINED; backoff=NOT_RETAINED;
  amendment=NOT_RETAINED; revocation=NOT_RETAINED; correction=NOT_RETAINED;
  outcome=LEGAL_GAP.

## 9. Transport and budget boundary

No #234 candidate API route was dispatched. Static official page reads and retained historical
route observations are not candidate runtime calls.

The ledger uses typed states, not fabricated zeros:

- candidate logical dispatch: NOT_DISPATCHED;
- candidate physical network dispatch: NOT_DISPATCHED;
- retries: NOT_MEASURED;
- redirects: NOT_MEASURED;
- complete and decompressed bytes: NOT_MEASURED;
- status and complete Content-Type: NOT_RETAINED for old route evidence;
- static page read count: NOT_MEASURED by the provider-route ledger.

No numeric request budget is authorized by this source-design pass. If a reviewer later approves a
finite observation plan, its reservation must atomically cover, per exact unit and globally:

1. logical and physical dispatches;
2. pages and documents;
3. retries and backoff waits;
4. redirects;
5. compressed and decompressed byte ceilings;
6. concurrency and rate-window slots; and
7. bounded diagnostic entries.

A retry charges the same reservation. A page is reserved before dispatch. Exhaustion, status/MIME
failure, redirect or decompression overrun, identity mismatch, duplicate/correction conflict,
or unreconciled pagination discards all private partial state and returns no partial public result.
The implementation must never fabricate an attempt, truncation marker, success, or nonpublication
conclusion.

Diagnostics, if ever authorized, must use bounded sanitized provider/source names and finite
reason tokens. Raw URLs, query values, response bodies, headers, cookies, credentials, and
unbounded provider text remain private.

## 10. Exact non-substitution and mixed-source rules

1. fiscal_date is fiscal-period end and never publication availability.
2. fetched_at_utc, retrieval time, response time, cache time, and current-snapshot time are
   observation times only.
3. A generic updated_at, createdDate, or modifiedDate is not availability without provider
   documentation binding that exact key and route to public report availability.
4. A revision/correction timestamp is not automatically original publication time.
5. A request EndDate, reportDate, fiscalDate, audit label, or period string cannot substitute.
6. Missing remains None. No zero-fill, forward-fill, interpolation, session mapping, timezone
   assumption, or cross-source inference is permitted.
7. Date-only and timestamp values remain distinct. Date-only is YYYY-MM-DD; a datetime needs an
   explicit UTC offset and ISO-8601 serialization. Naive datetime values fail closed.
8. Every source observation keeps provider, role, route/version, symbol, statement, cadence,
   fiscal period, and timestamp semantics together. A request symbol cannot stand in for a
   response symbol.
9. Mixed income, balance, and cashflow providers may remain statement-level observations. No
   report-level winner is selected from different source semantics. A convenience value would
   require an explicit deterministic consensus and exact agreement.
10. Market-session and calendar alignment is caller-side and out of scope.

## 11. Future conjunctive reopen gate

The new chain remains empty unless every condition below is proven for each exact
provider/route/statement/cadence unit:

- provider-owned documentation names the exact availability/publication field and binds its
  meaning to the same report, not retrieval, ingestion, fiscal period, or generic update;
- a retained response from the exact route proves key, JSON type, nullability, grammar, timezone,
  precision, report-versus-row level, and response identity;
- annual and quarterly evidence are independent, with statement/template and symbol identity
  bound in the same response;
- repeated row-level availability values are exactly equal across all pages, or the source is
  rejected as conflict/malformed;
- provider-declared bounds, cadence, nonpublication behavior, pagination/totals, duplicate and
  correction/revision rules, and value-blind distinct-period counts reconcile;
- status, complete MIME, redirects, decompression, retry, byte, rate-window, concurrency, and
  atomic no-partial behavior fit a finite reviewer-approved plan;
- route-local terms or written permission explicitly cover no-login automation, caller return,
  caching, storage, retention/deletion, attribution, commercial/derivative use, and
  redistribution/OSS;
- no source observation is cross-qualified from the other provider;
- exact API/model design review passes before RED; RED is synthetic/offline only; implementation
  and code review remain separate.

If any one condition is open, the result remains SOURCE_GAP and the current API/value chain is
unchanged. New probe work requires a separate finite plan and reviewer authorization.

## 12. Deferred typed design

If, and only if, a future source-design review qualifies a source, the preferred additive carrier
is a typed statement-level observation attached to StatementProvenance/provider role. This is a
guardrail, not a model or API change.

The future observation would need provider role and route/version, response-backed report identity,
availability semantic kind, date precision, optional provider-defined value, explicit date-only
versus UTC-offset datetime representation, null for absent field, and fail-closed malformed or
conflicting values. It must preserve each source observation when statements use different
providers, and never create a misleading single MetricReport.source winner.

Any report-level convenience value would require an explicit deterministic consensus; conflict
remains visible. Parser, pagination, retry/failover, cache-key, diagnostics, DataFrame,
serialization, documentation, API snapshot, packaging, and compatibility behavior would need a
separate design decision. No field is added by #234.

## 13. Deferred RED and release matrix

No RED authorization is requested by this handoff. If a separate exact design PASS later authorizes
RED, tests must use fabricated fixtures only and cover:

- annual and quarterly timezone-aware provider timestamps;
- date-only round-trip with explicit date precision;
- absent/null candidate -> None, with no fiscal/retrieval/update fallback;
- blank, padded, malformed, naive, non-finite, impossible, or wrong-type values fail closed;
- exact symbol/statement/cadence/fiscal-date/provider binding;
- repeated row-level values must agree across one report; conflicts and duplicate-page
  disagreements fail closed;
- same-source and mixed-source statement results, missing observations, and provider disagreement;
- no silent earliest/latest/min/max choice and no session/calendar conversion;
- unchanged 26 metric values, lineage, failover order, annual/quarterly return ordering, cache keys,
  public signatures, and offline/no-login behavior;
- DataFrame attrs/columns, serialization, diagnostics, documentation, API snapshot, security,
  blacklist, build, and wheel/sdist contents.

No provider rows, credentials, live endpoints, or network calls may enter tests.

## 14. Closure state

The source/legal evidence is complete enough to establish a clean negative, not a qualified
availability source:

- disposition: SOURCE_GAP_CLOSURE;
- new availability chain: empty;
- current annual/quarterly fundamentals values: unchanged;
- 26-metric catalog: unchanged;
- source/failover order: unchanged;
- session mapping: caller-side and unchanged;
- no provider probe, RED test, API/model change, code, fixture, source registration, push, or
  issue close is authorized by this document.

A later exact design review may reopen only under section 11. A public OSS release cannot rely on
no-login reachability, browser compatibility, a robots Allow directive, a fiscal date, a retrieval
timestamp, or a generic update field as permission or availability proof.

### Bottom summary

- Result: no qualified provider-native report-availability source for #234.
- VNDirect createdDate/modifiedDate are SEMANTICS_GAP; fiscalDate is period-end only.
- CafeF has no qualified availability field and no retained response symbol echo.
- Annual/quarterly value bounds are historical evidence only, not availability coverage.
- Route-local automation, retention, caching, caller-return, and public-OSS redistribution remain LEGAL_GAP.
- New chain stays empty; current values, 26 metrics, failover order, and session boundary stay unchanged.
- No probe, RED, API/model, code, fixture, source registration, push, or close is authorized.
- Reopen requires exact semantics, identity, coverage, legal rights, finite budgets, and separate review.
