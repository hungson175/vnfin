# #229 design note — official VN30 review/rebalance event history

**Access date:** 24 August 2026 (UTC+7)
**Packet:** `5b8d2f8` / public receipt `issuecomment-5391811465`
**Published base:** `origin/master` `d9bcf0478336aa1fb906e88d9d72f7a370911da5`
**Phase:** `SOURCE_DESIGN`
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
logical_units / physical_dispatches / archive_pages / documents / retries / redirects /
compressed_bytes / decompressed_bytes = 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0
```

Static research traffic is not converted into candidate-call counts. No `SourceAttempt`, zero-row
result, `EMPTY_AUTHORITATIVE`, or `diagnostics_truncated` record is fabricated. `NOT_RETAINED` and
`NOT_PROBED` are evidence gaps, never permission, absence, empty history, unchanged membership, or
complete coverage.

## 2. Decision

No candidate proves all identity, archive coverage, runtime, and reuse axes. The safe disposition is
`SOURCE-GAP CLOSURE`; the new chain remains empty. The existing `vnfin.indices.index_constituents(index)` and
`IndexClient.constituents(index)` expose a present-state snapshot with no date/effective-date
argument. They, the SSI source, routing, cache, warnings, diagnostics, DataFrame behavior, public
models, and exports stay unchanged. The snapshot stays present-state only and must not establish
historical unchanged members, no-change events, effective dates, or archive completeness.

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
| `U01b` | [HOSE-Index Ground Rules v3.1](https://staticfile.hsx.vn/Uploads/LocalFiles/aa9fc7f802f54c8cb39e6a10347ef2e4/20221026_20221025%20QĐ%20788%20ban%20hành%20QTCS%20HOSE-Index%20ver%203.1.pdf), prior official rule version. | Version/calendar control only; it is not an event archive and does not reconcile historical announcements or reuse rights. | `RULE_CONTROL_ONLY` + `COVERAGE_UNPROVEN` + `LEGAL_GAP` |
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
| `U14` | [HOSE index hub](https://www.hsx.vn/vi/Modules/Listed/Web/HoseIndexView/), official navigation/search surface. | JavaScript shell/navigation only; no VN30 event response, stable archive pagination, or historical bound is retained. | `NAVIGATION_ONLY` + `COVERAGE_UNPROVEN` + `TRANSPORT_INCONCLUSIVE` |
| `U15` | [VNX information archive](https://vnx.vn/vi/thong-tin-tu-sgdck/VNX_QLHD), official paginated disclosure archive. | Generic VNX archive, not a VN30 event archive; its page/document totals cannot be charged as VN30 event coverage without exact classification and identity. | `ARCHIVE_HUB_ONLY` + `COVERAGE_UNPROVEN` + `LEGAL_GAP` |

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

## 4a. Version-aware calendar and event classes
### Bounded July 2025 document evidence

The April and July 2025 official basket materials support only a bounded document-level comparison:
the two main VN30 tables are 30-row snapshots with separate reserve-list sections, and the retained
document evidence records one outgoing `BVH`, one incoming `DGC`, and a 29-member document-level
intersection. This is `DOCUMENT_SNAPSHOT_ONLY`, not event-level `unchanged_members`, no-change, or a
revision result. The July improvement release is a bounded delta explanation; its body must be bound
to the exact landing/document identity, publication date, effective date, active revision, and any
intervening change before an event field can be published. No such event-level binding is admitted
in this round.


The calendar is bound to the active rule version and its effective boundary; it is not applied
backward from the current rules. The retained prior Version 3.1 uses a third-Monday January/July
constituent-disclosure schedule, while Version 4.0 uses the third Wednesday and is stated to apply
from March 2025 (exact effective day `NOT_RETAINED`). Holiday and first-subsequent-trading-day
rules remain part of the source interpretation.

January/July constituent reviews are separate event classes from quarterly outstanding-share,
free-float, and capping updates in January/April/July/October. In particular, April/October
parameter-update evidence is not promoted to a constituent review; non-periodic/extraordinary
removals, replacements, corrections, postponements, and withdrawals are separate classes with their
own dates and revision rules. A future archive reconciliation must count each class against the
applicable version-aware calendar without mixing them.

## 5. Per-unit legal and runtime axis matrix

The following is deliberately bounded. `Not observed` means no affirmative observation was made;
`not disclosed` means the reviewed official material does not grant or state the axis. It never means
allowed. No HTTP data endpoint, hidden JSON route, or provider row operation was probed.

| Unit | Public access / login-session-UA-WAF observation | Automation | Caller return | Cache / storage / retention | Derivative / commercial | Attribution | Redistribution / resale | Amendment / revocation | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `U01` rules v4.0 | Static PDF readable from official URL; no login/challenge observed in that static read; session, UA, WAF, redirect, rate, and MIME behavior not probed/retained | Not granted | Not granted | Not disclosed | HOSE permission gate for index products; other commercial use not cleared | No licence/attribution grant | Publishing/copying/distribution of the rules document expressly prohibited in §12; resale not granted | Rules may be amended/withdrawn at any time; no user revocation process stated | **Block** |
| `U01b` rules v3.1 | Prior HOSE static rules version; no event response; calendar control only | Not granted | Not granted | Not disclosed | No derivative/commercial permission | No licence/attribution grant | No OSS reuse grant retained | Version/revision history and amendment terms for event documents `NOT_RETAINED` | **Block** |
| `U02` Apr-2025 update PDF | Static official PDF was indexed/read; no login/challenge observation is limited to that static artifact; no automated route contract | Not granted | Not disclosed | Not disclosed | No derivative/commercial permission | Not disclosed | Not granted; no resale terms | No document revision/supersession contract stated; later corrections/revocation unknown | **Block** |
| `U03` Jul-2025 URL lead | Static fetch timed out on 24 August 2026; no auth/session/UA/WAF conclusion can be drawn | Not established | Not established | Not established | Not established | Not established | Not established | Not established | **Block** |
| `U04–U06` factsheets | Static official PDFs readable/indexed; no automated access policy, cookie/session, UA, WAF, or rate evidence | Not granted | Not granted | Not disclosed | Product use requires HOSE approval; analytical derivative/commercial rights otherwise unclear | Notice/contact is not a licence | Not granted; resale not addressed | Factsheet revision/withdrawal history not stated | **Block** |
| `U07–U08` web applications | Public navigation shell visible; JavaScript required/no-data shell observed; underlying route, login/session, UA/WAF, MIME, redirects, pagination, and rate not probed | Not established | Not established | Not disclosed | Not established | Not established | Not established | Not established | **Block** |
| `U09` data-feed page | Login shell observed; no credential used; service/session/UA/WAF behavior beyond that page not probed | No-login automation not supported by observation | Not disclosed | Not disclosed | Commercial product lead; contract needed | Not disclosed | Not disclosed | Contract amendment/revocation unknown | **Block** |
| `U10` tariff | Static commercial document; no data route was called | Tariff does not grant automation | Tariff does not grant caller return | Not disclosed | Paid display/non-display and HOSE Index Feed categories; exact product rights require contract | Not disclosed | Not disclosed | Not disclosed | **Block** |
| `U11` VNX final register/attachment | Register is public; final attachment fetch timed out; no data route | Not granted | Not granted | Not disclosed | Governance/contract posture only | Site copyright is not data attribution permission | Not granted | Final-rule amendment/revocation text not retained | **Block** |
| `U12` VNX conference page | Public static article; no data operation | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Article does not set data rights | **Block** |
| `U13` VNX draft | Public static draft; clearly non-operative; no data operation | No grant | No grant | Confidentiality/contract concepts are not OSS permission | Draft points toward written index-use contracts; no permission for this library | Not stated | Not granted | Draft may change; final rule controls | **Block** |
| `U14–U15` hubs/archives | Navigation or generic paginated archive; no event response admitted | Not established | Not established | Not disclosed | Not established | Not established | Not established | Not established | **Block** |

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
   and pagination semantics; streamed attachment identity, complete MIME after the first colon,
   redirect/status checks, archive-page/document budgets, finite rate/concurrency/retry/byte budgets,
   and sanitized source/document diagnostics;
5. written or exact published rights for automation, caller return, cache/storage/retention/deletion,
   attribution, commercial/derivative use, redistribution/resale, amendment, and revocation; and
6. a deterministic revision/supersession rule for corrections, withdrawals, postponements, and
   conflicting documents.

No current unit satisfies this predicate. No new transport seam is authorized in this
source-gap packet; it remains deferred until the same source/legal/coverage gates pass. A future API
must atomically fail on unknown archive
intervals, WAF/challenge, timeout, malformed document, revision conflict, budget exhaustion, or
rights uncertainty; it must never return partial/empty/zero-filled history or infer a no-change event.

## 7. Atomic global archive budget

No numeric ceiling is frozen in this source-gap note. If a future owner route is legally and
technically qualified, one deterministic sequential ledger must cover the entire archive traversal:

```text
logical_units, physical_dispatches, archive_pages, documents, retries,
redirects, compressed_bytes, decompressed_bytes
```

Archive-page and document reservations are separate. The future scheduler uses `max_concurrency = 1`
and reserves every dimension before dispatch. Each retry and followed redirect is a new physical
operation. Compressed bytes are charged while streaming; decompressed bytes are charged after decode.
Caller-malformed inputs fail before cache/network. A malformed attachment fails after the real
dispatch but before cache/return. Reconcile each dimension as `reserved = charged + released` without
decrementing charged work. Exhaustion of any dimension is globally fatal: discard private rows and
return no empty, partial, zero-filled, or false-complete history. Diagnostics contain only real
bounded attempts/counters; no fabricated retry, redirect, byte total, or truncation marker.

## 8. Deferred API/model/RED/release matrix

All rows remain `DEFERRED / NOT_AUTHORIZED`. The lifecycle is exact:

```text
source qualification -> API/model contract freeze -> separate RED authorization
-> reviewer verifies RED and authorizes implementation -> GREEN -> code review -> publication
```

| Future gate | Required proof | Status now |
| --- | --- | --- |
| Current snapshot | Existing current constituent API/model, cache, warnings, diagnostics, DataFrame, docs, and exports unchanged | Not authorized |
| API/model | Separate event-history facade; immutable event/history/coverage/provenance; publication/effective filters; exact optionality for unavailable unchanged members | Not authorized |
| Identity/revision | Exact VN30/document/revision; unique/disjoint deltas; complete-basket versus delta-only; correction/withdrawal/postponement/conflict cases | Not authorized |
| Coverage | 2018-current reconciliation; provider-declared partial; missing middle event/document; no-false-FULL/no-false-absence | Not authorized |
| Streaming transport | Attachment identity, complete post-first-colon MIME, status/redirect/WAF/TLS/UA/session, archive pagination, split page/document budgets, malformed/truncated/oversized inputs | Not authorized |
| Cache/diagnostics | Cache only after a valid complete result; UTC-aware retrieval time; finite real attempts; sanitized source/document diagnostics with no URL/query/raw body/header/cookie/local-path/provider-exception leakage | Not authorized |
| Release | Full offline suite, imports/version, docs/public snapshots, blacklist/secret/diff/path/object/clean-tree, wheel/sdist, exact remote anchor/ancestry/three paths | Not authorized |

No public name, enum, model, source registration, RED test, implementation, live integration test,
coverage claim, or runtime capability is authorized here.

## 9. Deferred implementation and release gates

All implementation, RED, source registration, API/model, and public-schema work is
`DEFERRED / NOT_AUTHORIZED`. If written rights and a reconciled archive later arrive, the sequence
is: source-design PASS → API/model freeze → separate RED authorization → reviewer RED verification →
TDD implementation → merged-tree tests/docs/build/blacklist/secret/scope gates → reviewer approval.

## 10. Reopen request

Ask HOSE/VNX for a written licence or exact service terms naming the exact review-history operation
and granting the legal/runtime axes above. Use first-party [HOSE contact](https://www1.hsx.vn/vi/lien-he)
and [HOSE index contact listed in the rules](https://staticfile.hsx.vn/Uploads/LocalFiles/ef15ff11e799483abd11677ad0443887/20250114_20241230_QD%20747%20HOSE%20Index%20Ground%20Rules.pdf).
Do not probe or implement before the evidence is reviewed and the reviewer gives an exact design
PASS.

## Sources

- [HOSE Ground Rules v4.0](https://staticfile.hsx.vn/Uploads/LocalFiles/ef15ff11e799483abd11677ad0443887/20250114_20241230_QD%20747%20HOSE%20Index%20Ground%20Rules.pdf)
- [HOSE-Index Ground Rules Version 3.1](https://staticfile.hsx.vn/Uploads/LocalFiles/aa9fc7f802f54c8cb39e6a10347ef2e4/20221026_20221025%20QĐ%20788%20ban%20hành%20QTCS%20HOSE-Index%20ver%203.1.pdf)
- [HOSE index hub](https://www.hsx.vn/vi/Modules/Listed/Web/HoseIndexView/)
- [VNX information archive](https://vnx.vn/vi/thong-tin-tu-sgdck/VNX_QLHD)
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
