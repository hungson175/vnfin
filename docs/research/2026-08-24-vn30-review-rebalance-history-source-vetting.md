# VN30 review/rebalance history — official-source legal and runtime audit

**Access date:** 24 August 2026 (UTC+7)
**Packet:** `5b8d2f8` / public receipt `issuecomment-5391811465`
**Published base:** `origin/master` `d9bcf0478336aa1fb906e88d9d72f7a370911da5`
**Phase:** `SOURCE_DESIGN`
**Companion design note:** `tasks/229-design-note.md`
**Disposition:** **`SOURCE-GAP CLOSURE`**
**New history chain:** empty; no runtime/API/model change

This is a docs-only source, runtime-posture, and reuse audit for official VN30 periodic
review/rebalance history. It authorizes no endpoint probe, RED test, production code, source
registration, API/model decision, provider data retention, push, or issue close.

## 1. Scope and clean-room boundary

The target is an authoritative event history, not a current snapshot: publication date, effective
date, review type, revision/supersession, additions/deletions, and a complete before/after basket
only when each basket is independently proven complete. The requested history window is inclusive
from 01 January 2018 through the current completed review. Foreign-flow calculations and VN30F
strategy remain caller-side and are not source substitutes.

The exact exclusion appended to **every web search query** was:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

Only official HOSE/VNX pages and first-party static documents were used. No blacklisted material,
third-party summary, endpoint map, live basket row, raw payload, credential, or copied dataset was
opened or retained. Static document reading is evidence review, not a candidate data dispatch.

This source-design round dispatched no candidate event-data operation. Its exact candidate ledger is:

```text
logical_units / physical_dispatches / pages_or_documents / retries /
redirects / compressed_bytes / decompressed_bytes = 0 / 0 / 0 / 0 / 0 / 0 / 0
```

Static research traffic is not converted into candidate-call counts. No `SourceAttempt`, zero-row
result, `EMPTY_AUTHORITATIVE`, or `diagnostics_truncated` record is fabricated. `NOT_RETAINED` and
`NOT_PROBED` are evidence gaps, never permission, absence, empty history, unchanged membership, or
complete coverage.

## 2. Decision

No candidate proves all identity, archive coverage, runtime, and reuse axes. The safe disposition is
`SOURCE-GAP CLOSURE`; the new chain remains empty. The existing `index_constituents` snapshot stays
present-state only and must not establish historical unchanged members, no-change events, effective
dates, or archive completeness.

The strongest official lead is a period-specific HOSE constituent document. The 16 April 2025
period-04 update is structurally useful as one bounded 2025 snapshot, but April is a
shares/free-float/capping update under the rules, not automatically a membership-change event. The
July 2025 evidence includes the bounded BVH-to-DGC release context; its official document URL
timed out in this round, so no body or row is admitted. Neither 2025 item proves a 2018-current
archive, revision/supersession history, or no-change event. The rules and factsheets establish
cadence and ownership, not a reusable historical archive.

## 3. Exact official units

Each unit is one tuple `(owner, canonical host/path, route/version, operation)`. Dates below are
document dates or explicit source dates; when the source does not disclose a day, that absence is
recorded rather than inferred from a filename or crawl date.

| ID | Exact unit and bounded observation | History qualification | Status |
| --- | --- | --- | --- |
| `U01` | [HOSE-Index Ground Rules v4.0](https://staticfile.hsx.vn/Uploads/LocalFiles/ef15ff11e799483abd11677ad0443887/20250114_20241230_QD%20747%20HOSE%20Index%20Ground%20Rules.pdf), Decision 747/QĐ-SGDHCM dated **30 December 2024**; the official July 2025 notice says effective from **March 2025** (day not stated). | Rules identify VN30, review cadence, disclosure/effective timing, amendments and rights posture; they are not an event archive. | `RULE_CONTROL_ONLY` + `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| `U02` | [HOSE VN30 period-04/2025 update](https://staticfile.hsx.vn/Uploads/News/88b97ff751554244b186d5c0323a49fe/20250416_20250416%20CBTT%20Cap%20nhat%20thong%20tin%20BCS%20HOSE-Index%20thang%2004.2025.pdf), URL/document date **16 April 2025**, source label `Kỳ 04/2025`. | Search-indexed official document exposes constituent and reserve-list sections; it is one period snapshot, not a before/after event pair. | `SNAPSHOT_LEAD` + `EVENT_TYPE_GAP` + `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| `U03` | [HOSE July 2025 constituent-document URL lead](https://staticfile.hsx.vn/Uploads/UploadDocuments/2388633/20250716%20CBTT-Danh%20muc%20thanh%20phan%20HOSE-Index%20thang%207.2025.pdf), filename date **16 July 2025**, source label `tháng 7.2025`; direct static read timed out on **24 August 2026**. The bounded official July release context includes BVH-to-DGC. | The URL is retained only as an official-host lead; no response/document body, publication date, effective date, revision, or rows are retained. The bounded release is not a revision/supersession or no-change proof. | `UNVERIFIED_LEAD` + `TRANSPORT_INCONCLUSIVE` + `LEGAL_GAP` |
| `U03b` | [HOSE July 2025 VN30-improvement release](https://staticfile.hsx.vn/Uploads/UploadDocuments/2391309/TCBC_%20Cai%20tien%20chi%20so%20VN30%20t7.2025.pdf), official two-page release context with the bounded `BVH → DGC` replacement statement. | Delta explanation only; no complete before/after basket, publication/effective binding, revision/supersession, archive bound, or no-change result is admitted. | `DELTA_ONLY` + `DATE_GAP` + `LEGAL_GAP` |
| `U04` | [HOSE VN30 factsheet](https://staticfile.hsx.vn/Uploads/UploadDocuments/2374581/Form_Factsheet_MCIndices_VN_T05.2025.pdf), updated **29 April 2025**. | Present-state factsheet; it reports VN30 identity/count and summary material, not a complete review archive or complete before/after basket. | `CURRENT_SNAPSHOT_ONLY` + `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| `U05` | [HOSE-Index factsheet](https://staticfile.hsx.vn/Uploads/UploadDocuments/2396611/Form_Factsheet_MCIndices_VN_T08.2025.pdf), updated **31 July 2025**. | Present-state factsheet after the July review window; summary/top-list material cannot establish a complete historical basket or delta. | `CURRENT_SNAPSHOT_ONLY` + `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| `U06` | [HOSE-Index factsheet](https://staticfile.hsx.vn/Uploads/UploadDocuments/2438018/Form_Factsheet_MCIndices_VN_T02.2026.pdf), updated **30 January 2026**. | Later present-state snapshot; it cannot be backdated or used to infer the January 2026 event's unchanged members. | `CURRENT_SNAPSHOT_ONLY` + `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| `U07` | [HOSE index-set navigation](https://www.hsx.vn/vi/cac-bo-chi-so), statically read **24 August 2026**; page exposes rules, periodic reports, and news navigation but the static shell reports no data. | Discovery/navigation only; no dated event operation, pagination, archive bound, or response schema is retained. | `NAVIGATION_ONLY` + `TRANSPORT_INCONCLUSIVE` + `LEGAL_GAP` |
| `U08` | [HOSE VN30 date-range trading-size page](https://www.hsx.vn/vi/du-lieu-giao-dich/quy-mo-giao-dich/bo-chi-so), statically read **24 August 2026**. | A date-filtered trading-statistics surface is not a review-history basket operation; underlying JavaScript calls were not probed. | `FIELD_GAP` + `TRANSPORT_INCONCLUSIVE` + `LEGAL_GAP` |
| `U09` | [HOSE data-feed page](https://www.hsx.vn/vi/data-feed), statically read **24 August 2026**; the visible shell presents username/password login. | Paid/credentialed service lead, not a no-login public review archive. | `AUTH_REQUIRED` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| `U10` | [HOSE information/data-service tariff](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf), document date not visible in retained text; statically indexed by **24 August 2026**. | Lists Market Data Feed/Webservice and HOSE Index Feed, including display/non-display and ID/Terminal concepts; it is a commercial service catalogue, not an OSS grant. | `COMMERCIAL_SERVICE_LEAD` + `LEGAL_GAP` + `RATE_POLICY_GAP` |
| `U11` | [VNX legal-document register](https://vnx.vn/vi/van-ban-phap-ly/6), read **24 August 2026**; Decision 67/QĐ-HĐTV is issued/effective **12 December 2025** and concerns construction, management, operation, and exploitation of VNX/subsidiary indices. | Governance control only. The final attachment was not used as a candidate operation after a static fetch timeout; no event rows or rights grant are retained. | `GOVERNANCE_ONLY` + `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
| `U12` | [VNX Member Conference 2025](https://vnx.vn/vi/ad/10003662), dated **14 March 2025**. | VNX states it trained members on HOSE-Index rules and discussed VN30 improvement; this is governance context, not an event archive. | `GOVERNANCE_ONLY` + `FIELD_GAP` + `LEGAL_GAP` |
| `U13` | [Official VNX draft index regulation](https://stream.vnx.vn/VNX/Article/20250808092250149VNX_Du-thao-QC-chi-so-15.7.2025.pdf), explicitly marked `Dự thảo 07/2025`. | Non-operative draft describes contract-based index-use authorization and confidentiality; it is a legal lead only and cannot grant reuse. | `NON_OPERATIVE_LEAD` + `LEGAL_GAP` |

The July 2025 URL lead and the VNX final attachment are deliberately not upgraded by URL shape,
filename, search absence, or timeout. No search-result absence is treated as proof that a review or
document did not exist.

## 4. Rules and owner posture

The current HOSE rules say HOSE manages the HOSE-Index series under VNX direction and define VN30 as
30 eligible high-capitalization/liquidity constituents. They specify constituent-change disclosure
on the third Wednesdays of January and July, effectiveness from the first Mondays of February and
August, and separate outstanding-share/free-float/capping updates on the third Wednesdays of
January, April, July, and October. Non-periodic removal/replacement is to be announced at least five
business days before its effective date. ([HOSE Ground Rules v4.0](https://staticfile.hsx.vn/Uploads/LocalFiles/ef15ff11e799483abd11677ad0443887/20250114_20241230_QD%20747%20HOSE%20Index%20Ground%20Rules.pdf))

The same official rules state that they may be supplemented, amended, or withdrawn in whole or in
part at any time, and that those changes may affect index construction or management. Their English
reference section says the document is copyrighted and prohibits publishing, copying, or
distribution; the document also says the Vietnamese version prevails. This is a direct restriction
on the rules document, not an OSS licence for event attachments. ([HOSE Ground Rules v4.0, §2.4 and §12](https://staticfile.hsx.vn/Uploads/LocalFiles/ef15ff11e799483abd11677ad0443887/20250114_20241230_QD%20747%20HOSE%20Index%20Ground%20Rules.pdf))

HOSE factsheets state that the HOSE-Index names are registered and exclusively owned by HOSE, and
that HOSE approval is required before the index series is used to create index funds, derivatives,
or related products. They also frame the publication as information-only and disclaim liability for
use of the information/data. That is a permission gate, not a blanket ban on every analytical use,
but it leaves derivative, commercial, and redistribution rights uncleared for this library.
([HOSE factsheet dated 30 January 2026](https://staticfile.hsx.vn/Uploads/UploadDocuments/2438018/Form_Factsheet_MCIndices_VN_T02.2026.pdf))

The official HOSE tariff lists paid Market Data Feed, Webservice, and HOSE Index Feed categories,
with display/non-display and online/delayed/end-of-day variants; its note describes an API and
ID/Terminal credentials. The [HOSE data-feed page](https://www.hsx.vn/vi/data-feed) itself presents
a username/password login shell. This establishes a commercial/authenticated service lead, not a
public no-login automation or caller-return right. The tariff does not state cache, storage,
retention, derivative, resale, attribution, amendment, or revocation terms for this OSS use.

The VNX legal register identifies the final index-regulation decision dated 12 December 2025, while
the official July 2025 draft is explicitly non-operative. The draft's contract-based concepts are
useful for routing a written permission request, but they cannot be treated as final terms or as a
licence. The VNX register footer carries a site copyright notice; that is not a data-reuse grant.
([VNX legal register](https://vnx.vn/vi/van-ban-phap-ly/6), [official VNX draft](https://stream.vnx.vn/VNX/Article/20250808092250149VNX_Du-thao-QC-chi-so-15.7.2025.pdf))

## 5. Per-unit legal and runtime axis matrix

The following is deliberately bounded. `Not observed` means no affirmative observation was made;
`not disclosed` means the reviewed official material does not grant or state the axis. It never means
allowed. No HTTP data endpoint, hidden JSON route, or provider row operation was probed.

| Unit | Public access / login-session-UA-WAF observation | Automation | Caller return | Cache / storage / retention | Derivative / commercial | Attribution | Redistribution / resale | Amendment / revocation | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `U01` rules v4.0 | Static PDF readable from official URL; no login/challenge observed in that static read; session, UA, WAF, redirect, rate, and MIME behavior not probed/retained | Not granted | Not granted | Not disclosed | HOSE permission gate for index products; other commercial use not cleared | No licence/attribution grant | Publishing/copying/distribution of the rules document expressly prohibited in §12; resale not granted | Rules may be amended/withdrawn at any time; no user revocation process stated | **Block** |
| `U02` Apr-2025 update PDF | Static official PDF was indexed/read; no login/challenge observation is limited to that static artifact; no automated route contract | Not granted | Not disclosed | Not disclosed | No derivative/commercial permission | Not disclosed | Not granted; no resale terms | No document revision/supersession contract stated; later corrections/revocation unknown | **Block** |
| `U03` Jul-2025 URL lead | Static fetch timed out on 24 August 2026; no auth/session/UA/WAF conclusion can be drawn | Not established | Not established | Not established | Not established | Not established | Not established | Not established | **Block** |
| `U04–U06` factsheets | Static official PDFs readable/indexed; no automated access policy, cookie/session, UA, WAF, or rate evidence | Not granted | Not granted | Not disclosed | Product use requires HOSE approval; analytical derivative/commercial rights otherwise unclear | Notice/contact is not a licence | Not granted; resale not addressed | Factsheet revision/withdrawal history not stated | **Block** |
| `U07–U08` web applications | Public navigation shell visible; JavaScript required/no-data shell observed; underlying route, login/session, UA/WAF, MIME, redirects, pagination, and rate not probed | Not established | Not established | Not disclosed | Not established | Not established | Not established | Not established | **Block** |
| `U09` data-feed page | Login shell observed; no credential used; service/session/UA/WAF behavior beyond that page not probed | No-login automation not supported by observation | Not disclosed | Not disclosed | Commercial product lead; contract needed | Not disclosed | Not disclosed | Contract amendment/revocation unknown | **Block** |
| `U10` tariff | Static commercial document; no data route was called | Tariff does not grant automation | Tariff does not grant caller return | Not disclosed | Paid display/non-display and HOSE Index Feed categories; exact product rights require contract | Not disclosed | Not disclosed | Not disclosed | **Block** |
| `U11` VNX final register/attachment | Register is public; final attachment fetch timed out; no data route | Not granted | Not granted | Not disclosed | Governance/contract posture only | Site copyright is not data attribution permission | Not granted | Final-rule amendment/revocation text not retained | **Block** |
| `U12` VNX conference page | Public static article; no data operation | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Article does not set data rights | **Block** |
| `U13` VNX draft | Public static draft; clearly non-operative; no data operation | No grant | No grant | Confidentiality/contract concepts are not OSS permission | Draft points toward written index-use contracts; no permission for this library | Not stated | Not granted | Draft may change; final rule controls | **Block** |

**Conclusion across all legal axes:** no unit has a published, exact, affirmative grant covering
automation, caller-facing return, transient cache, durable storage/retention/deletion, attribution,
commercial or derivative use, redistribution/resale, amendment, and revocation for the proposed
library. Public visibility, a search result, an information-only disclaimer, a fee table, or a
login page is not a licence.

## 6. Future qualification contract (design only)

Before any API/model decision, one exact unit must prove:

1. provider-issued VN30 identity, review type, publication date, effective date, UTC-aware retrieval
   timestamp, and active revision;
2. a complete official before/after basket or explicit delta-only semantics, with no inferred
   unchanged members;
3. a provider-declared archive bound and reconciled event/document totals from 01 January 2018 to
   the current completed review, or a declared narrower complete bound;
4. no-login or expressly permitted automation, auth/session/UA/WAF behavior, complete MIME, redirect
   and pagination semantics, finite rate/concurrency/retry/document/byte budgets;
5. written or exact published rights for automation, caller return, cache/storage/retention/deletion,
   attribution, commercial/derivative use, redistribution/resale, amendment, and revocation; and
6. a deterministic revision/supersession rule for corrections, withdrawals, postponements, and
   conflicting documents.

No current unit satisfies this predicate. A future API must atomically fail on unknown archive
intervals, WAF/challenge, timeout, malformed document, revision conflict, budget exhaustion, or
rights uncertainty; it must never return partial/empty/zero-filled history or infer a no-change event.

## 7. Historical event and coverage invariants

These are deferred source-qualification predicates, not public enums or warnings in this commit.
Every accepted event must have response/document-backed `VN30` identity, official publication date,
official effective date, a UTC-aware retrieval timestamp separate from those event dates, event type,
source/document identity, active revision, and bounded sanitized provenance. A filename, URL date,
crawl date, or current snapshot cannot replace an official event date.

Additions and deletions must be unique canonical security symbols, disjoint within one event, and tied
to the same official revision. Blank, malformed, duplicate, cross-index, or conflicting symbols fail.
A delta-only document exposes only proven deltas; it does not imply a complete basket or turn an
unavailable unchanged list into `()`.

`unchanged_members` is allowed only after two independently qualified complete official before/after
baskets establish the intersection for the exact effective event. The bounded April/July 2025
materials and `BVH → DGC` release context do not satisfy that gate: they remain 2025 evidence only,
with no admitted revision/no-change result in this round. Current `index_constituents`, a delta-only
announcement, an ETF, broker commentary, or an incomplete archive cannot establish unchanged members.
Revised, withdrawn, postponed, or conflicting documents require deterministic active-revision and
supersession rules; they are never silently merged.

Future coverage labels are conjunctive:

- `FULL` requires the official calendar/rule, every applicable event from 01 January 2018 through the
  current completed review, reconciled provider/document totals, and no unexplained middle interval.
- `QUALIFIED_PARTIAL` requires an exact provider-declared narrower served bound, reconciled totals, no
  unknown interval inside that bound, and every other identity, transport, budget, and rights gate.
- `COVERAGE_UNPROVEN` means no provider-declared bound or reconciled event/document set was retained.
- `COVERAGE_GAP` means a provider or qualified response explicitly establishes an excluded interval;
  it is never inferred from a search absence.
- `NOT_SERVED`, `IDENTITY_GAP`, `DATE_GAP`, `LEGAL_GAP`, `RATE_POLICY_GAP`, `CALL_BUDGET_GAP`, and
  `TRANSPORT_INCONCLUSIVE` are finite diagnostics for explicit unsupported, identity/date, rights,
  budget, or unknown/fatal transport conditions. None is a no-change event.

Search-result absence, a missing attachment, current-snapshot non-change, timeout, WAF challenge,
redirect loop, unexpected status/MIME, malformed/truncated document, unknown pagination, or budget
exhaustion is unknown/fatal. There is no silent missing event, zero fill, false partial, or false
`FULL`.

## 8. Atomic global archive budget

No numeric ceiling is frozen by this source-gap note. After a future owner route is legally and
technically qualified, one deterministic sequential ledger must cover all archive traversal and
documents:

```text
logical_units, physical_dispatches, pages_or_documents, retries,
redirects, compressed_bytes, decompressed_bytes
```

The future contract must set `max_concurrency = 1`, reserve every dimension before dispatch, count
every retry and followed redirect as a new physical operation, charge compressed bytes while
streaming and decompressed bytes after decoding, and reconcile each dimension as
`reserved = charged + released` without decrementing charged work. Caller-malformed dates/options fail
before cache/network; malformed provider documents fail after the real dispatch but before cache or
return. Exhaustion of any dimension is globally fatal: discard private rows and return no empty,
partial, zero-filled, or false-complete history. Diagnostics contain only real bounded attempts and
counters; no fake retry, redirect, byte total, or truncation marker.

## 9. Deferred API/model/RED/release gates

All rows below remain `DEFERRED / NOT_AUTHORIZED`. The lifecycle is exact:

```text
source qualification -> API/model contract freeze -> separate RED authorization
-> reviewer verifies RED and authorizes implementation -> GREEN -> code review -> publication
```

| Future gate | Required proof | Status now |
| --- | --- | --- |
| Current snapshot | Existing `index_constituents` API/model, cache, warnings, diagnostics, DataFrame, docs, and exports unchanged | Not authorized |
| API/model | Separate event-history facade; immutable event/history/coverage/provenance; publication/effective filters; exact optionality for unavailable unchanged members | Not authorized |
| Input preflight | Inclusive/reversed/malformed/bool dates/options fail before cache/network with zero-call proof | Not authorized |
| Identity and revision | Exact VN30/document/revision; unique/disjoint deltas; complete-basket versus delta-only; correction/withdrawal/postponement/conflict cases | Not authorized |
| Coverage | 2018-current reconciliation; missing middle event/document; declared partial; no-false-FULL/no-false-absence | Not authorized |
| Transport/document | HTML/PDF/XLS/XLSX/CSV identity; full post-first-colon MIME; status/redirect/WAF/TLS/UA/session; malformed/truncated/oversized input | Not authorized |
| Shared budget/cache | Sequential reservation; retry/redirect/page/document/byte charging; atomic exhaustion; cache only after valid complete result | Not authorized |
| Diagnostics/security | UTC-aware retrieval time; finite real attempts; sanitized source identity; no URL/query/raw body/header/cookie/local path/provider-exception leakage | Not authorized |
| Release | Full offline suite, import/version, docs snapshots, blacklist/secret/diff/path/object/clean-tree, wheel/sdist, exact remote anchor/ancestry/three paths | Not authorized |

No public name, enum, model, source registration, RED test, implementation, live integration test,
coverage claim, or runtime capability is authorized here.

## 10. Conjunctive reopen and source-gap closure

A future reopen request must provide all of these together:

1. one exact official operation with response/document-backed `VN30` identity, publication/effective
   dates, UTC-aware retrieval timestamp, event type, delta/complete-basket semantics, revision,
   correction, and supersession rules;
2. the official review calendar plus reconciled full 01 January 2018 through current coverage, or an
   exact provider-declared narrower `QUALIFIED_PARTIAL` bound with no unknown middle interval;
3. written or exact published rights covering automation, caller return, cache/storage/retention,
   attribution, derivative/commercial use, redistribution/resale, amendment, and revocation;
4. bounded auth/session/UA/WAF, status/MIME/redirect/pagination, rate/concurrency/retry,
   page/document, compressed/decompressed-byte evidence;
5. frozen API/model compatibility and no-false-absence/unchanged-member semantics;
6. separate RED authorization followed by reviewer verification; and
7. exact merged-tree ancestry, exclusion, path, diff, build, and test gates.

For the current `SOURCE-GAP CLOSURE`, after exact design PASS the only permitted sequence is rerun
merged docs/full/build/blacklist/secret/diff/clean-tree gates; push the exact approved
research/design/backlog anchor; verify remote HEAD, base ancestry, exclusions, and exactly the three
approved paths; post a clean no-capability `SOURCE-GAP` resolution; close and re-read #229. No TDD or
runtime follow-on is authorized by this issue.

## 11. Deferred implementation and release gates

All implementation, RED, source registration, API/model, and public-schema work is
`DEFERRED / NOT_AUTHORIZED`. If written rights and a reconciled archive later arrive, the sequence
is: source-design PASS → API/model freeze → separate RED authorization → reviewer RED verification →
TDD implementation → merged-tree tests/docs/build/blacklist/secret/scope gates → reviewer approval.

## 12. Permission contact path

Ask HOSE/VNX for a written licence or exact service terms naming the exact review-history operation
and granting the legal/runtime axes above. Use first-party [HOSE contact](https://www1.hsx.vn/vi/lien-he)
and [HOSE index contact listed in the rules](https://staticfile.hsx.vn/Uploads/LocalFiles/ef15ff11e799483abd11677ad0443887/20250114_20241230_QD%20747%20HOSE%20Index%20Ground%20Rules.pdf).
Do not probe or implement before the evidence is reviewed and the reviewer gives an exact design
PASS.

## Sources

- [HOSE Ground Rules v4.0](https://staticfile.hsx.vn/Uploads/LocalFiles/ef15ff11e799483abd11677ad0443887/20250114_20241230_QD%20747%20HOSE%20Index%20Ground%20Rules.pdf)
- [HOSE VN30 period-04/2025 update](https://staticfile.hsx.vn/Uploads/News/88b97ff751554244b186d5c0323a49fe/20250416_20250416%20CBTT%20Cap%20nhat%20thong%20tin%20BCS%20HOSE-Index%20thang%2004.2025.pdf)
- [HOSE July 2025 VN30-improvement release](https://staticfile.hsx.vn/Uploads/UploadDocuments/2391309/TCBC_%20Cai%20tien%20chi%20so%20VN30%20t7.2025.pdf)
- [HOSE July 2025 constituent-document URL lead](https://staticfile.hsx.vn/Uploads/UploadDocuments/2388633/20250716%20CBTT-Danh%20muc%20thanh%20phan%20HOSE-Index%20thang%207.2025.pdf)
- [HOSE factsheet dated 29 April 2025](https://staticfile.hsx.vn/Uploads/UploadDocuments/2374581/Form_Factsheet_MCIndices_VN_T05.2025.pdf)
- [HOSE factsheet dated 31 July 2025](https://staticfile.hsx.vn/Uploads/UploadDocuments/2396611/Form_Factsheet_MCIndices_VN_T08.2025.pdf)
- [HOSE factsheet dated 30 January 2026](https://staticfile.hsx.vn/Uploads/UploadDocuments/2438018/Form_Factsheet_MCIndices_VN_T02.2026.pdf)
- [HOSE index-set navigation](https://www.hsx.vn/vi/cac-bo-chi-so)
- [HOSE VN30 date-range trading-size page](https://www.hsx.vn/vi/du-lieu-giao-dich/quy-mo-giao-dich/bo-chi-so)
- [HOSE data-feed page](https://www.hsx.vn/vi/data-feed)
- [HOSE information/data-service tariff](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf)
- [VNX legal-document register](https://vnx.vn/vi/van-ban-phap-ly/6)
- [VNX Member Conference 2025](https://vnx.vn/vi/ad/10003662)
- [Official VNX draft index regulation, July 2025](https://stream.vnx.vn/VNX/Article/20250808092250149VNX_Du-thao-QC-chi-so-15.7.2025.pdf)

## Bottom summary

- **Decision:** `SOURCE-GAP CLOSURE`; no VN30 review-history unit is admitted.
- HOSE v4.0 proves cadence/ownership and allows amendment/withdrawal, not a reusable archive.
- April 2025 is one official snapshot; July 2025 is only a timed-out URL lead here.
- HOSE factsheets/current pages are present-state or navigation surfaces, not before/after history.
- HOSE Index Feed is paid/authenticated in the reviewed posture; reuse rights are not granted.
- VNX Decision 67 is governance evidence; its final attachment text was not retained.
- No probes, raw rows, code, RED, API/model, or runtime capability were added.
- **Need from Boss:** written HOSE/VNX rights and a reconciled archive, or approval to keep closed.
