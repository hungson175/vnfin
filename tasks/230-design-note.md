# #230 design note — daily foreign-room / ownership-capacity history

**Packet:** /home/hungson175/tools/vnfin-oss-reviewer/tasks/230-daily-foreign-room-history-spec.md
**Packet reviewer anchor:** 7439d74e40a9e26a2819f7a93ad6f91917d17c5e
**Public receipt:** issuecomment-5392141986
**Design base:** origin/master 3dd3125281efdc6e89479306a64213dfc26a6987
**Activation receipt:** local backlog 302d73d1dc8694d9eb2156dd77533a85e21cb8d0
**Phase:** SOURCE_DESIGN
**Disposition:** **SOURCE-GAP CLOSURE**
**Runtime:** empty new chain; current behavior unchanged

This note freezes no public name, enum, model, source, API, warning, or error. It authorizes no probe,
RED test, implementation, source registration, live integration test, push, or close.

## 1. Scope and exclusions

The proposed primitive is provider-published daily point-in-time foreign room / ownership capacity
for an explicit equity symbol and exchange. It excludes foreign flow, current foreign holding
without room semantics, legal-limit notices alone, percentage-only limits, inferred shares
outstanding, current-VN30 backfill, replay/hash/strategy, and caller-side
remaining_room / foreign_limit <= 0.10.

The exact exclusion appended to every web search was:

~~~
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
~~~

Only official VSDC, HOSE/VNX, and SSC material was reviewed. No raw row, live value, raw response,
header, cookie, token, response digest, unofficial route, wrapper, paid/private feed, or third-party
dataset was retained.

## 2. Decision

No single owner + exact route/version + operation passes identity, semantics, coverage, transport,
budget, and legal/reuse gates. Record SOURCE-GAP CLOSURE and keep the new chain empty.

The VSDC archive is a strong official lead: the public foreign-ownership category shows dated
disclosures, separate update text, detail pages, attachments, date controls, and pagination. It
does not prove a no-login automation contract, stable attachment identity, field units,
correction/revision semantics, or 2018-current complete coverage.

The retained HOSE static foreign-investor shareholding document exposes useful provider labels
(maximum ratio, total room, foreign ownership volume/ratio, current room) and one effective-date
label. It is one bounded snapshot without a proven daily archive or reuse grant. HOSE's data-feed
page is a credentialed/commercial lead. VSDC, HOSE, VNX, SSC, and any issuer notice are not
interchangeable fallbacks.

## 3. Independent source-unit matrix

| Unit | Owner + canonical route/operation | Evidence retained | Gaps/disposition |
| --- | --- | --- | --- |
| VSDC-A | VSDC; https://vsd.vn/en/alc/82; archive/listing | Dated foreign-ownership disclosure titles, separate date-update labels, date controls, paginated listing, attachment links | No exact API, field schema, 2018 bound, complete symbol/session totals, rate policy, or reuse grant; ARCHIVE_LEAD/COVERAGE_GAP/LEGAL_GAP |
| VSDC-B | VSDC; https://vsd.vn/en/ad/{numeric-id}; disclosure detail | Publication title/date, separate update value, attachment relationship | Session/publication/effective/revision semantics, headers/MIME, final attachment identity and document schema are not retained; IDENTITY_GAP/DATE_GAP/ATTACHMENT_GAP |
| VSDC-C | VSDC; attachment reached from VSDC-B; exact path/version NOT_RETAINED; document operation | Only the fact that an attachment link is advertised | No schema, units, row bounds, correction identity, or rights; no attachment dispatch; NOT_PROBED/FIELD_GAP/UNIT_GAP/LEGAL_GAP |
| HOSE-A | HOSE; https://www.hsx.vn/vi/cac-bo-chi-so; discovery/landing | Official market/index navigation | No daily room operation, archive enumeration, stable pagination, or automation terms; NAVIGATION_ONLY |
| HOSE-B | HOSE; staticfile.hsx.vn/Uploads/News/{opaque-id}/{filename}; static shareholding document | Effective date and provider-labelled room/ownership fields | Snapshot only; route identity, archive bounds, correction/retention, runtime and rights gaps; SNAPSHOT_LEAD/COVERAGE_GAP/LEGAL_GAP |
| HOSE-C | HOSE; https://www.hsx.vn/vi/data-feed; data-feed/service | Public page presents login/commercial posture | No no-login automation/caller-return/cache/redistribution contract; AUTH_REQUIRED/RATE_POLICY_GAP/LEGAL_GAP |
| VNX-A | VNX legal navigation; governance/legal operation | Governance/legal context only | Not a data operation and no reuse grant; GOVERNANCE_ONLY/LEGAL_CONTEXT_ONLY |
| SSC-A | SSC legal navigation; legal interpretation operation | Legal context only | Not a data operation, not a provider response identifying requested scope outside service, and no reuse grant; LEGAL_CONTEXT_ONLY/NOT_A_DATA_OPERATION/LEGAL_GAP |

The exact source unit wins the whole request. No source may be selected for one field and another
source for a date, limit, holding, or missing symbol.

### 3.1 Finite static-evidence ledger (not a runtime ledger)

The observations below are finite static page/document observations, not provider dispatches and not
`SourceAttempt` values. The candidate runtime ledger in section 6 remains zero. `logical` and
`physical` are candidate-runtime counters; `pages` and `documents` here count retained static
observations. `NOT_RETAINED` means the detail was not preserved; `NOT_PROBED` means no endpoint or
attachment operation was dispatched.

| Unit | Retained static observations | HTTP method | Static observation mode | Access/auth posture | Session / UA / WAF | Status / MIME / redirects | logical / physical / pages / documents / retries | Compressed / decompressed bytes | Rate / concurrency | Native bulk / per-symbol |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VSDC-A | 1 archive landing plus 1 date/pagination view | NOT_RETAINED | STATIC_BROWSER_PAGE_READ | PUBLIC_ARCHIVE_VISIBLE; credential state NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | 0 / 0 / 2 static / 0 / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED | NOT_PROBED / NOT_PROBED | NOT_RETAINED / NOT_RETAINED |
| VSDC-B | 1 disclosure-detail page | NOT_RETAINED | STATIC_BROWSER_PAGE_READ | PUBLIC_DETAIL_PAGE_VISIBLE; credential state NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | 0 / 0 / 1 static / 0 / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED | NOT_PROBED / NOT_PROBED | NOT_RETAINED / NOT_RETAINED |
| VSDC-C | 1 attachment-link observation; no attachment document retained | NOT_PROBED | STATIC_LINK_INSPECTION | PUBLIC_DETAIL_PAGE_VISIBLE; attachment access NOT_PROBED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | 0 / 0 / 0 / 0 / NOT_PROBED | NOT_PROBED / NOT_PROBED | NOT_PROBED / NOT_PROBED | NOT_RETAINED / NOT_RETAINED |
| HOSE-A | 1 official index/market-information landing page | NOT_RETAINED | STATIC_BROWSER_PAGE_READ | PUBLIC_NAVIGATION_VISIBLE; credential state NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | 0 / 0 / 1 static / 0 / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED | NOT_PROBED / NOT_PROBED | NOT_RETAINED / NOT_RETAINED |
| HOSE-B | 1 official snapshot title/date/landing observation; no raw row retained | NOT_RETAINED | STATIC_DOCUMENT_READ | PUBLIC_SNAPSHOT_DOCUMENT_VISIBLE; credential state NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | 0 / 0 / 0 / 1 static / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED | NOT_PROBED / NOT_PROBED | NOT_RETAINED / NOT_RETAINED |
| HOSE-C | 1 data-feed/service landing page | NOT_RETAINED | STATIC_BROWSER_PAGE_READ | PUBLIC_SERVICE_LANDING_VISIBLE; service access CREDENTIAL_REQUIRED_OR_CONTRACTED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | 0 / 0 / 1 static / 0 / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED | NOT_PROBED / NOT_PROBED | NOT_RETAINED / NOT_RETAINED |
| VNX-A | 1 legal/document navigation page | NOT_RETAINED | STATIC_BROWSER_PAGE_READ | PUBLIC_LEGAL_PAGE_VISIBLE; credential state NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | 0 / 0 / 1 static / 0 / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED | NOT_APPLICABLE / NOT_APPLICABLE | NOT_APPLICABLE / NOT_APPLICABLE |
| SSC-A | 1 legal navigation page | NOT_RETAINED | STATIC_BROWSER_PAGE_READ | PUBLIC_LEGAL_PAGE_VISIBLE; credential state NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED / NOT_RETAINED | 0 / 0 / 1 static / 0 / NOT_RETAINED | NOT_RETAINED / NOT_RETAINED | NOT_APPLICABLE / NOT_APPLICABLE | NOT_APPLICABLE / NOT_APPLICABLE |

The HOSE-B retained tuple is deliberately sanitized: official landing
`https://www.hsx.vn/vi/cac-bo-chi-so`, title `Foreign Investors Shareholding Data`, effective-date
label `15 April 2025`, and route template
`staticfile.hsx.vn/Uploads/News/{opaque-id}/{filename}`. The opaque ID, filename, raw rows, and live
values are NOT_RETAINED. This tuple proves traceability of a bounded snapshot claim, not a daily
runtime route or reuse permission.

## 4. Frozen semantic gates (future qualification only)

A provider must response-back all of these in one route set:

- canonical symbol and exchange;
- provider trading-session date, effective date, publication date, UTC-aware retrieval time, and
  revision as separate fields;
- exact meaning of maximum ownership ratio, total room, foreign ownership volume/ratio, current
  room, permitted shares, capacity, and remaining room;
- share/lot/scaled integer unit, scale, precision, percentage range, nullability, zero/missing/
  nonpublication semantics;
- duplicate/conflict, request/response mismatch, cross-exchange, correction, restatement, limit
  change, listing/delisting, corporate-action, and publication-lag behavior.

current_room, holding, legal limit, capacity, and flow cannot be combined or arithmetically repaired
without a same-source contract. A blank/negative/zero value is not an automatic zero or empty
result.

## 5. Coverage and result contract (not public yet)

FULL would require every requested symbol and provider-declared eligible session in the requested
interval, reconciled page/document totals, exact point-in-time semantics, and no unexplained gap.

QUALIFIED_PARTIAL would require an exact provider-declared narrower symbol/date/retention bound with
the same reconciliation and must expose both served and unserved/unknown symbol/date bounds (or a
typed gap). It cannot silently omit a symbol/date.

NOT_SERVED would be emitted only from an authoritative provider response identifying a symbol or
scope as outside service. Local empty pages, missing attachments, unknown bounds, timeout, WAF,
truncation, or an unverified archive are COVERAGE_GAP/TRANSPORT_INCONCLUSIVE, not NOT_SERVED, empty,
or zero.

Non-trading dates have no synthetic row. A true empty requires request/source identity, provider
bounds/totals, calendar, and explicit nonpublication semantics to reconcile.

Native provider bulk is preferred. A per-symbol loop cannot qualify unless the provider explicitly
documents rate and concurrency posture, finite retention, and a reconciled request-global budget for
all symbols, pages, documents, retries, redirects, and bytes. A future multi-symbol request is
atomic: duplicate or conflicting rows, cross-exchange or request/response identity mismatch, mixed
revisions, malformed provider data, any fatal symbol outcome, or exhaustion of any global dimension
invalidates the complete request. Private accumulators are discarded and no partial, false-complete,
zero-filled, or stitched result is returned.

## 6. Legal and runtime gates

No reviewed unit grants all of:

~~~
automation, caller return, cache, storage/retention/deletion, attribution,
commercial/derivative use, redistribution/resale, rate/retry/concurrency,
amendment, revocation
~~~

VSDC's public page/footer and HOSE's public documents/data-feed posture are not an OSS licence.
A future permission must name the exact owner, route/version, fields, served dates/symbols, and
every axis above.

No candidate operation was probed. If one is later qualified, use one sequential request-scoped
ledger:

~~~
symbols, logical_units, physical_dispatches, archive_pages, documents, retries,
redirects, compressed_bytes, decompressed_bytes
~~~

Reserve before dispatch; charge actual retries/redirects and stream/decompression bytes
incrementally. Keep page and document reservations separate; enforce per-entry and aggregate
decompressed ceilings. Caller-malformed inputs fail before cache/network. Malformed provider
responses fail after dispatch before cache/return. Any exhaustion discards all private accumulators
and returns no partial/false-complete/zero-filled/stitched result. Diagnostics contain only real
bounded attempts/counters.

All current candidate ledgers are zero:

~~~
symbols / logical_units / physical_dispatches / archive_pages / documents / retries / redirects /
compressed_bytes / decompressed_bytes = 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0
~~~

## 7. Deferred API/RED/release matrix

All rows are DEFERRED / NOT_AUTHORIZED.

| Gate | Required future proof | Status |
| --- | --- | --- |
| Input/preflight | Explicit symbols/plain dates/daily interval/exchange; malformed/reversed/bool inputs fail before cache/network with zero-call proof | Not authorized |
| Duplicate/lazy construction | Duplicate requested symbols, lazy construction, and every invalid-input path have deterministic failures and zero network; no request starts before complete validation | Not authorized |
| Single-symbol success | One valid symbol has response-backed identity, a complete valid result, deterministic ordering/attrs, cache-after-complete-only, and no false empty; offline positive and malformed-provider cases are explicit | Not authorized |
| Multi-symbol success | Native bulk or expressly permitted per-symbol retrieval serves every requested symbol with served/unserved/unknown terminal outcomes, deterministic aggregate ordering, and atomic no-partial behavior | Not authorized |
| Identity | Symbol/exchange/session/publication/effective/revision tuple; request/response match; duplicate/conflict, cross-exchange, and mixed-revision rejection | Not authorized |
| Field/unit | Provider-backed room/capacity/limit/holding meanings, types, units, scale, precision, nullability; no arithmetic repair | Not authorized |
| Coverage | FULL/declared partial/unknown; served and unserved bounds; terminal outcome per symbol; non-trading/nonpublication; listing/delisting/limit-change/corporate-action/revision boundaries; no silent drop | Not authorized |
| Ordering/surface | Deterministic symbol/date ordering; exact DataFrame columns and attrs; serialization, repr, equality, exports, and public snapshots are specified and tested without live data | Not authorized |
| Source/cache | Source selection, zero-source behavior, cache-key identity, cache-after-complete-only, and current-cohort survivorship warning behavior are explicit and compatible | Not authorized |
| Transport | Status/MIME/redirect/WAF/TLS/session/envelope; attachment identity; pagination truncation/cycle/duplicate/late-page; streaming and byte ceilings | Not authorized |
| Budget/atomicity | Reservation-before-dispatch; symbols/pages/documents/retries/redirects/bytes; native-bulk preference; global exhaustion; private accumulators discarded on any fatal outcome; no partial/no stitch | Not authorized |
| Diagnostics | Sanitized bounded attempts/counters; stable warning/error grammar; no query URL/raw body/header/cookie/path/live values/provider exception | Not authorized |
| Public carriers/exports | Result, error, warning, source-selection, and diagnostic carriers plus import/export/snapshot compatibility are defined only after a fresh API decision | Not authorized |
| Docs compatibility | `docs/api.md`, `docs/units.md`, tutorial, architecture, source/skill documentation, and CHANGELOG compatibility set is enumerated and updated together only after authorization | Not authorized |
| Version compatibility | Existing package/API version behavior, source/route version identity, serialized snapshots, and documented compatibility promises remain explicit; any breaking change requires a fresh design review | Not authorized |
| Import/API surface | Existing import paths, new exports, public snapshots, serialization, repr, and equality are checked without changing current APIs | Not authorized |
| Build | Clean-tree `uv build` produces the required wheel and sdist with the exact source manifest; no generated artifact is hand-edited or published early | Not authorized |
| Remote release | Reviewer-approved exact anchor, ancestry, changed paths, remote HEAD, issue resolution/re-read, and no later commit are verified before publication or close | Not authorized |
| Release | Current equities/index/foreign-flow behavior and public snapshots unchanged; full offline suite, build, blacklist/secret/scope, diff, import, wheel/sdist, and remote-release gates pass together | Not authorized |

Lifecycle:

~~~
source qualification -> API/model contract freeze -> separate RED authorization
-> reviewer verifies RED and authorizes implementation -> GREEN -> code review -> publication
~~~

No public API/model, source registration, RED, implementation, runtime capability, or coverage
claim is authorized by this source-gap note.

## 8. Lifecycle and exact anchors

| Fact | Value |
| --- | --- |
| Clean published base | `3dd3125281efdc6e89479306a64213dfc26a6987` |
| Local activation receipt | `302d73d1dc8694d9eb2156dd77533a85e21cb8d0` |
| Prior substantive docs anchor | `2fb93fc03ff79b404bc2bd36bdb85a8bcf1a4c90` |
| Reviewed merged head (BLOCK) | `d18c0cdc2a1af1ce7c94ccb1fc78bf07bb9e553b` |
| Review report | `/home/hungson175/tools/vnfin-oss-reviewer/reviews/review-202608241522-issue230-design-source-gate.md` |
| Reviewer report commit | `b7d805a` |
| Verified BLOCK delivery | `158a5527` |
| Latest reviewed head (BLOCK) | `5f0d2db315d283320f6fdbfdae7cc90130f3c063` |
| Latest review report | `/home/hungson175/tools/vnfin-oss-reviewer/reviews/review-202608241537-issue230-corrected-design-rereview.md` |
| Latest reviewer report commit | `1e4eef3` |
| Latest verified BLOCK delivery | `85ee50bd` |
| BLOCK-first local record | `09cb8dcaec90d158129eebbb3cb98abb8d5bb596` (excluded from the clean correction ancestry) |
| Latest closure reviewed head (BLOCK) | `4608c2818f54a4fa1f676ff1325e3b2bf190533e` |
| Latest closure review report | `/home/hungson175/tools/vnfin-oss-reviewer/reviews/review-202608241547-issue230-narrow-closure-rereview.md` |
| Latest closure reviewer report commit | `d2d05a8` |
| Latest closure BLOCK delivery | `8bb5199e` |
| Latest BLOCK-first local record | `9f452c018a368fbf403079513d3dd089728bef07` (excluded from the clean correction ancestry) |
| Correction actor | `vnfin-oss` |
| Review-handoff actor | `vnfin-oss-reviewer` |
| Next action | `RETURN_EXACT_SHA_DESIGN_VERDICT` |
| Queue preservation | #231 remains queued; #232 receipt `a2ccd39`, prior #230 handoffs, and `d11f33a` remain excluded from the clean correction ancestry |

The corrected substantive docs anchor is recorded in the separate final backlog handoff after this
docs-only correction. No later local queue receipt is part of the reviewed target unless explicitly
listed there.

## 9. Conjunctive reopen evidence

Reopen only after one owner route set proves all of:

1. no-login or expressly permitted automation plus exact response/status/MIME/redirect/pagination;
2. symbol/exchange/session/publication/effective/revision identity;
3. field meanings, units, types, scale, precision, nullability, and empty/zero semantics;
4. reconciled provider-declared coverage and a useful complete 2018-current or declared partial span;
5. corrections, revisions, limit changes, listing/delisting and corporate-action boundaries;
6. finite rate/concurrency/retry/page/document/byte budgets with atomic exhaustion; and
7. written/exact rights for automation, caller return, cache/retention, attribution, commercial/
   derivative use, redistribution/resale, amendment, and revocation.

## 10. Source references

- [VSDC foreign-ownership archive](https://vsd.vn/en/alc/82)
- [VSDC disclosure detail route template](https://vsd.vn/en/ad/{numeric-id})
- [VSDC official home](https://vsd.vn/en/)
- [HOSE index/market-information navigation](https://www.hsx.vn/vi/cac-bo-chi-so)
- [HOSE data-feed page](https://www.hsx.vn/vi/data-feed)
- [VNX legal navigation](https://vnx.vn/vi/van-ban-phap-ly/6)
- [SSC legal navigation](https://ssc.gov.vn/webcenter/portal/ssc/pages_r/l/chitit)

## Bottom summary

- **Decision:** SOURCE-GAP CLOSURE; new foreign-room history chain stays empty.
- VSDC is an official archive lead, not yet a rights-cleared or response-typed runtime source.
- One retained HOSE snapshot document exposes provider labels but only proves a bounded snapshot.
- No flow, current snapshot, legal notice, percentage, or inferred denominator substitutes for room history.
- No cross-source stitch, silent zero, false empty, missing-row drop, or current-VN30 backfill.
- Candidate dispatch/page/retry/redirect/byte ledgers are zero; no live rows were retained.
- API/RED/runtime work remains deferred until conjunctive reopen evidence arrives.
- Need from Boss: nothing.
