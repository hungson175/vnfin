# Daily foreign-room / ownership-capacity history — official-source and legal audit

**Access date:** 24 August 2026 (UTC+7)
**Packet:** 7439d74e40a9e26a2819f7a93ad6f91917d17c5e / public receipt issuecomment-5392141986
**Published base:** origin/master 3dd3125281efdc6e89479306a64213dfc26a6987
**Activation:** local backlog anchor 302d73d1dc8694d9eb2156dd77533a85e21cb8d0
**Phase:** SOURCE_DESIGN
**Disposition:** **SOURCE-GAP CLOSURE**
**New runtime chain:** empty; no API/model or production change

This is a docs-only source, semantics, coverage, transport, budget, and reuse audit. It authorizes no
endpoint probe, RED test, model/facade/source, provider-row retention, push, or issue close.

## 1. Scope and clean-room boundary

The target is provider-published **daily point-in-time foreign room / ownership capacity** for an
explicit equity symbol and exchange. It is not foreign buy/sell/net flow, a legal ownership-limit
notice by itself, current foreign holding without remaining-room semantics, a percentage-only limit,
shares-outstanding arithmetic, or a current-VN30 panel backfilled into history. The caller's
remaining_room / foreign_limit <= 0.10 threshold, current-VN30 panel, replay, hashing, holdout,
signal, and trading interpretation remain outside vnfin.

The exact exclusion appended to **every web search query** was:

~~~
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
~~~

Only official VSDC, HOSE/VNX, and SSC pages or documents were reviewed. No blacklisted material,
unofficial endpoint map, wrapper, notebook, broker credential, paid/private feed, proxy, reporter
artifact, third-party dataset, raw body, header, cookie, token, response digest, or provider
exception prose was opened or retained. Static page/document reading is evidence review, not a
candidate data dispatch.

The candidate runtime ledger for this round is intentionally zero:

~~~
symbols / logical_units / physical_dispatches / archive_pages / documents / retries / redirects /
compressed_bytes / decompressed_bytes = 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0
~~~

Static research traffic is not converted into candidate-call counts. No SourceAttempt, empty result,
EMPTY_AUTHORITATIVE, or diagnostics_truncated record is fabricated. NOT_RETAINED, NOT_PROBED, and
TRANSPORT_INCONCLUSIVE are evidence gaps, never permission, a zero room, an empty history,
unchanged capacity, or complete coverage.

### 1.1 Finite static-evidence ledger (not a runtime ledger)

The observations below are retained static page/document observations, not provider dispatches and
not `SourceAttempt` values. The runtime candidate ledger above therefore remains zero. `logical` and
`physical` are candidate-runtime counters; `pages` and `documents` in this table are finite static
observations. `NOT_RETAINED` means the observation was not preserved in the clean-room evidence;
`NOT_PROBED` means no endpoint or attachment operation was dispatched.

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

## 2. Decision

No exact owner + route/version + operation currently proves all required identity, field/unit,
point-in-time date, archive, runtime, budget, and reuse axes. The safe disposition is
SOURCE-GAP CLOSURE; the new foreign-room history chain remains empty.

The strongest lead is the official VSDC foreign-ownership disclosure archive. Its public archive
lists dated foreign-ownership disclosures, separate publication/update labels, detail pages, and an
attachment link. The page also exposes date-search controls and a paginated record list. That proves
an official publication family, not a no-login automated route, a stable attachment identity, a
public bulk operation, a 2018-current bound, or permission to automate/cache/redistribute.

The retained HOSE static shareholding document is a useful semantics lead: its field labels include
maximum shareholding ratio, total room, foreign ownership volume, foreign ownership ratio, and
current room, with an effective date. It is one bounded snapshot, not a proven daily history API or
rights-cleared archive. The HOSE data-feed page presents a credentialed/commercial service lead, not
a public no-login route.

VSDC and HOSE must not be stitched by symbol, date, or field. A VSDC publication title/update date
cannot be joined to a HOSE PDF or a statutory limit notice to manufacture a historical room row.

## 3. Independent official source units

Each row is one tuple (owner, canonical host/path, route/version, operation). A route template does
not imply that a hidden attachment or API exists.

| ID | Independent owner/route/operation and bounded evidence | Exact semantic/coverage observation | Disposition |
| --- | --- | --- | --- |
| VSDC-A | [VSDC foreign-ownership archive](https://vsd.vn/en/alc/82); owner VSDC; public archive/listing operation; route version and request contract not disclosed | The page title states maximum foreign-ownership rate and information about shares foreign investors may buy. Dated disclosure entries, date-update text, date controls, and pagination are visible. The observed page exposes a current record slice; no 2018 lower bound or complete symbol/session coverage is declared. | ARCHIVE_LEAD + FIELD_GAP + COVERAGE_GAP + LEGAL_GAP |
| VSDC-B | VSDC disclosure detail route template vsd.vn/en/ad/{numeric-id}; owner VSDC; one disclosure-detail operation | A detail page has a provider publication title, a separate date-update value, and an attachment link. The exact publication/session meaning, revision field, response headers, MIME, final attachment identity, and pagination contract are not retained. | IDENTITY_GAP + DATE_GAP + ATTACHMENT_GAP + TRANSPORT_INCONCLUSIVE |
| VSDC-C | VSDC attachment operation reached from VSDC-B; exact attachment host/path/version is NOT_RETAINED; no attachment dispatch made | The attachment may contain the requested fields, but its schema, units, nullability, correction identity, document date, and complete row bounds were not retained. A detail-page link is not a bulk API or a reuse grant. | NOT_PROBED + FIELD_GAP + UNIT_GAP + LEGAL_GAP |
| HOSE-A | [HOSE index/market-information navigation](https://www.hsx.vn/vi/cac-bo-chi-so); owner HOSE; discovery/landing operation | Official navigation is a discovery lead only. It does not prove a daily room-history operation, stable pagination, archive bounds, or public automation terms. | NAVIGATION_ONLY + COVERAGE_GAP + LEGAL_GAP |
| HOSE-B | HOSE static-document route template staticfile.hsx.vn/Uploads/News/{opaque-id}/{filename}; owner HOSE; dated foreign-investor shareholding document operation | The sanitized official snapshot tuple below retains the landing, title, and 15 April 2025 effective-date label plus provider-labelled maximum ratio, total room, foreign ownership volume/ratio, and current room. The document is a snapshot; exact route/version, archive enumeration, corrections, daily retention, MIME/redirect policy, and reuse rights are not established. | SNAPSHOT_LEAD + DATE_GAP + COVERAGE_GAP + LEGAL_GAP |
| HOSE-C | [HOSE data-feed page](https://www.hsx.vn/vi/data-feed); owner HOSE; data-feed/service operation | The visible posture is username/password and a commercial service lead. No no-login automation, caller-return, cache, retention, redistribution, or rate contract is established. | AUTH_REQUIRED + RATE_POLICY_GAP + LEGAL_GAP |
| VNX-A | [VNX legal/document navigation](https://vnx.vn/vi/van-ban-phap-ly/6); owner VNX; governance/legal operation | Governance and index/market-information ownership context may constrain reuse, but no daily room rows, route, schema, or licence for this library is established. | GOVERNANCE_ONLY + FIELD_GAP + LEGAL_GAP |
| SSC-A | [SSC securities-market legal navigation](https://ssc.gov.vn/webcenter/portal/ssc/pages_r/l/chitit); owner SSC; legal interpretation operation | Official legal material supports the distinction between a legal foreign-ownership limit and published current information. It is not a room-history data operation and does not identify a requested symbol/date as outside service or grant data extraction or redistribution. | LEGAL_CONTEXT_ONLY + NOT_A_DATA_OPERATION + LEGAL_GAP |

The exact attachment identity for VSDC-C and HOSE-B is intentionally not normalized from a filename,
search result, or opaque path. No opaque path token is concatenated, encoded, or retained as a
substitute for response-backed identity.

### 3.1 Traceable official HOSE snapshot tuple

This is a bounded static-evidence tuple, not a live row or runtime `SourceAttempt`. It is retained
only to make the HOSE field/date claim traceable without preserving an opaque URL token, raw row, or
provider value.

| Owner | Official landing | Sanitized official title | Effective-date label | Route or attachment identity | Retained evidence |
| --- | --- | --- | --- | --- | --- |
| HOSE | [HOSE index/market-information navigation](https://www.hsx.vn/vi/cac-bo-chi-so) | Foreign Investors Shareholding Data | 15 April 2025 (effective-date label) | `staticfile.hsx.vn/Uploads/News/{opaque-id}/{filename}`; opaque ID and filename NOT_RETAINED | Title/date/landing and field labels only; no raw rows or live values |

## 4. Response-backed semantics and identity

### 4.1 Provider meanings are not interchangeable

The following concepts remain distinct until one exact provider response defines their relationship:

- maximum_shareholding_ratio: a percentage label;
- total_room: a provider-labelled quantity;
- foreign_ownership_volume: a provider-labelled holding quantity;
- foreign_ownership_ratio: a provider-labelled percentage;
- current_room: a provider-labelled remaining quantity;
- legal foreign-ownership limit, permitted foreign shares, current foreign holding, and remaining
  buyable capacity.

A future parser must use the provider's exact field labels and units. It must not derive
current_room = total_room - foreign_ownership_volume, convert a percentage into shares, infer
shares outstanding, or repair negative/zero values unless the same source contract explicitly states
the relationship for the same symbol, exchange, session, and revision.

### 4.2 Date and revision identity

A source session is the provider's Vietnam trading-session date. It is not the effective date,
retrieval date, publication timestamp, request order, UTC truncation, or a date inferred from a
separate notice. Effective date, publication date, revision date, and `retrieved_at_utc` are separate
fields; `retrieved_at_utc` is UTC-aware.

VSDC detail pages visibly carry both a disclosure title date and a separate date-update value. This
proves that publication/update timestamps are not interchangeable, but it does not prove which one
is the provider's room session. A future response must bind symbol, exchange, session, publication
date, effective date, revision/correction identity, and retrieval time in one source-backed tuple.

Limit-change notices, corporate actions, listing/delisting events, corrections, and publication lag
must not be joined across VSDC, HOSE, SSC, issuers, or brokers unless a separately qualified official
identity/effective-date crosswalk and legal composition design exists.

### 4.3 Value typing and nullability

Future source qualification must prove, per field:

- canonical symbol and exchange identity;
- integer share/lot/scaled unit, scale, precision, and non-negativity;
- percentage representation and numeric bounds;
- None/absent/zero semantics;
- booleans rejected as numeric values;
- non-finite, float-where-integer-promised, negative, and unit-mismatch values rejected;
- whether a field is provider-unavailable versus not applicable;
- whether a row is a true non-trading absence, a nonpublication, or an unknown transport result.

A blank, omitted, negative, or zero room is never silently mapped to an authoritative empty or zero
capacity.

## 5. Coverage, history, and negative boundaries

The VSDC archive proves a publication family with dated records visible in 2025–2026 evidence,
including older 2025 pages found through the official archive. It does **not** prove a provider-
declared 2018 lower bound, a complete current bound, every eligible session, every symbol/exchange,
retention of corrections, or stable archive totals. The visible page count is a time-bounded
observation, not a coverage claim.

The retained HOSE document proves one bounded official snapshot observation dated 15 April 2025. It
does not prove a provider archive, daily point-in-time continuity, symbol/session totals,
listing/delisting boundaries, limit-effective intervals, or correction/supersession history.

Future disposition rules are:

- FULL requires every requested symbol and every provider-declared eligible session within the
  requested interval, reconciled pages/documents/cursors, exact point-in-time limit/revision
  semantics, and no unexplained gap or conflict.
- QUALIFIED_PARTIAL requires a provider-declared narrower symbol/date/retention bound and the same
  reconciliation; it must expose both the served symbol/date bounds and the unserved or unknown
  symbol/date bounds (or a typed gap) and cannot silently omit a symbol or date.
- NOT_SERVED is a typed source response only when the provider response identifies the symbol or
  requested scope as outside service; it is not a local guess from an empty page.
- IDENTITY_GAP, FIELD_GAP, UNIT_GAP, DATE_GAP, COVERAGE_GAP, PAGINATION_GAP, LEGAL_GAP,
  RATE_POLICY_GAP, CALL_BUDGET_GAP, TRANSPORT_INCONCLUSIVE, and NOT_PROBED remain diagnostic design
  vocabulary, not public runtime enums in this packet.
- Non-trading dates have no synthetic row. An empty response is authoritative only when request and
  source identity, provider calendar/bounds, totals, and explicit nonpublication semantics
  reconcile. Timeout, WAF, truncation, unknown bounds, or missing attachment identity is fatal
  unknown, not empty or zero.

Explicitly excluded substitutions are current constituents, foreign flow, prices, volume, shares
outstanding, market cap, corporate-action arithmetic, percentage-only limits, statutory notices
without daily room rows, login/paid feeds, and any cross-source stitch.

Native provider bulk is preferred. A per-symbol loop cannot qualify unless the provider explicitly
documents rate and concurrency posture, finite retention, and a reconciled request-global budget for
all symbols, pages, documents, retries, redirects, and bytes. A future multi-symbol request is
atomic: duplicate or conflicting rows, cross-exchange or request/response identity mismatch, mixed
revisions, malformed provider data, any fatal symbol outcome, or exhaustion of any global dimension
invalidates the complete request. Private accumulators are discarded and no partial, false-complete,
zero-filled, or stitched result is returned.

## 6. Legal, access, and reuse posture

| Unit | Public visibility | Automation | Caller return | Cache/storage/retention | Derivative/commercial | Attribution/redistribution | Amendment/revocation | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VSDC-A/B/C | Public pages and disclosure links are visible without credentials in the reviewed browser posture; hidden session/UA/WAF/MIME/redirect behavior is not retained | No affirmative automation permission | Not granted | Not granted/disclosed | Not granted/disclosed | VSDC site footer says rights are reserved; no OSS/data licence retained | Not disclosed | **Block** |
| HOSE-A/B | Official landing and one retained static snapshot document are public leads; exact automated route behavior is not retained | No affirmative automation permission | Not granted | Not granted/disclosed | HOSE ownership/permission and service terms remain unresolved | No OSS redistribution grant retained | Not disclosed | **Block** |
| HOSE-C | Login/commercial service posture | Credentialed/contracted service lead only | Contract required | Contract required | Contract required | Contract required | Contract required | **Block** |
| VNX-A | Public VNX legal/governance page | Not a data operation | Not applicable | Not applicable | Governance context only | No data licence | Legal changes/revisions possible | **Block** |
| SSC-A | Public SSC legal/interpretation page | Not a data operation | Not applicable | Not applicable | Legal context only | No data licence | Legal changes/revisions possible | **Block** |

Public visibility is not permission. All rights reserved, a tariff, a legal explanation, an
information page, or a public attachment cannot be converted into rights for automation, caller
return, cache/storage, durable retention/deletion, attribution, commercial/derivative use,
redistribution/resale, rate/retry/concurrency, amendment, or revocation.

A source can reopen only with written or exact published terms naming the exact route/version and
granting every required axis. Route owner and rights holder must be identified separately where
VSDC, HOSE, VNX, SSC, an issuer, or a service operator are not the same party.

## 7. Runtime and global-budget design boundary

No endpoint or attachment operation was probed. No numeric ceiling is frozen. If an owner later
qualifies a route set, one request-scoped sequential ledger must cover:

~~~
symbols, logical_units, physical_dispatches, archive_pages, documents, retries, redirects,
compressed_bytes, decompressed_bytes
~~~

Archive-page and document reservations are separate. Reserve before dispatch; charge every actual
retry and redirect; charge compressed bytes while streaming and decompressed bytes incrementally
during decoding. Enforce per-entry and aggregate decompressed ceilings before materialization.
max_concurrency = 1 is the safe starting posture; do not promise it as a public library policy
before source/rate evidence.

Caller-malformed input fails before cache/network. A malformed provider response fails after the
real dispatch but before cache/return. Exhaustion of any dimension is globally fatal: discard all
private accumulators and return no partial, false-complete, zero-filled, or stitched result.
Diagnostics may contain only real bounded attempts and counters; no fabricated retry, redirect,
byte-total, or truncation marker.

A future route must prove status, complete post-first-colon MIME, final identity, redirect-hop
bounds, pagination semantics, compressed/decompressed byte limits, and sanitized diagnostics.
The current runtime has no foreign-room adapter and is not changed by this packet.

## 8. Deferred API/model/RED/release matrix

All rows are DEFERRED / NOT_AUTHORIZED.

| Future gate | Required offline proof | Status now |
| --- | --- | --- |
| Input/preflight | Explicit symbols, plain inclusive dates, daily interval, exchange/source validation; malformed/reversed/bool inputs fail before cache/network with zero-call proof | Not authorized |
| Duplicate/lazy construction | Duplicate requested symbols, lazy construction, and every invalid-input path have deterministic failures and zero network; no request is started before complete validation | Not authorized |
| Single-symbol success | One valid symbol has response-backed identity, a complete valid result, deterministic ordering/attrs, cache-after-complete-only, and no false empty; offline positive and malformed-provider cases are explicit | Not authorized |
| Multi-symbol success | Native bulk or expressly permitted per-symbol retrieval serves every requested symbol with served/unserved/unknown terminal outcomes, deterministic aggregate ordering, and atomic no-partial behavior | Not authorized |
| Identity | Exact symbol/exchange/session/publication/effective/revision tuple; request/response match; duplicate/conflict, cross-exchange, and mixed-revision rejection | Not authorized |
| Semantics | Provider-backed room/capacity/limit/holding meanings, type/unit/scale/precision/nullability; no arithmetic repair; zero versus missing | Not authorized |
| Coverage | FULL/declared QUALIFIED_PARTIAL/unknown; served and unserved bounds; every symbol terminal outcome; non-trading/nonpublication; listing/delisting/limit-change/corporate-action/revision boundaries; no silent drop | Not authorized |
| Ordering/surface | Deterministic symbol/date ordering; exact DataFrame columns and attrs; serialization, repr, equality, exports, and public snapshots are specified and tested without live data | Not authorized |
| Source/cache | Source selection, zero-source behavior, cache-key identity, cache-after-complete-only, and current-cohort survivorship warning behavior are explicit and compatible | Not authorized |
| Transport | Status/MIME/redirect/WAF/TLS/session/envelope; attachment identity; pagination truncation/cycle/duplicate/late-page; decompression and byte ceilings | Not authorized |
| Budget/atomicity | Reservation-before-dispatch; symbols/pages/documents/retries/redirects/bytes; native-bulk preference; global exhaustion; private accumulators discarded on any fatal outcome; no partial/no stitch | Not authorized |
| Diagnostics | Sanitized bounded attempts/counters; stable warning/error grammar; no URL query, raw body/header/cookie, local path, live room values, or provider exception prose | Not authorized |
| Public carriers/exports | Result, error, warning, source-selection, and diagnostic carriers plus import/export/snapshot compatibility are defined only after a fresh API decision | Not authorized |
| Docs compatibility | `docs/api.md`, `docs/units.md`, tutorial, architecture, source/skill documentation, and CHANGELOG compatibility set is enumerated and updated together only after authorization | Not authorized |
| Version compatibility | Existing package/API version behavior, source/route version identity, serialized snapshots, and documented compatibility promises remain explicit; any breaking change requires a fresh design review | Not authorized |
| Import/API surface | Existing import paths, new exports, public snapshots, serialization, repr, and equality are checked without changing current APIs | Not authorized |
| Build | Clean-tree `uv build` produces the required wheel and sdist with the exact source manifest; no generated artifact is hand-edited or published early | Not authorized |
| Remote release | Reviewer-approved exact anchor, ancestry, changed paths, remote HEAD, issue resolution/re-read, and no later commit are verified before publication or close | Not authorized |
| Release | Current equities/index/foreign-flow behavior unchanged; full offline suite; blacklist/secret/path/object/diff/clean-tree gates; wheel/sdist and remote-release gates pass together | Not authorized |

The lifecycle is fixed:

~~~
source qualification -> API/model contract freeze -> separate RED authorization
-> reviewer verifies RED and authorizes implementation -> GREEN -> code review -> publication
~~~

No public name, enum, model, source registration, RED test, implementation, live integration test,
coverage claim, or runtime capability is authorized here.

## 9. Lifecycle and exact anchors

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

## 10. Conjunctive reopen evidence

A future reviewer may reopen only when **all** of the following arrive for one owner route set:

1. exact no-login or expressly permitted automation route, response identity, status/MIME/redirect/
   pagination semantics, and bounded runtime;
2. provider-backed symbol/exchange/session/publication/effective/revision identity;
3. exact field meanings, units, types, scale, precision, nullability, zero/missing/nonpublication
   semantics, and any conditional arithmetic;
4. provider-declared archive/date/symbol bounds with reconciled pages/documents and a useful complete
   2018-current span or explicitly declared narrower partial span;
5. corrections, revisions, limit changes, listing/delisting and corporate-action boundaries;
6. finite rate/concurrency/retry/page/document/byte budgets and executable atomic exhaustion;
7. written or exact published rights for automation, caller return, cache/storage/retention/deletion,
   attribution, commercial/derivative use, redistribution/resale, amendment, and revocation; and
8. a fresh exact design/API decision followed by separate RED authorization.

Evidence for one unit cannot fill a gap in another. Until all gates pass, preserve the empty chain and
current behavior.

## Sources

- [VSDC foreign-ownership archive](https://vsd.vn/en/alc/82)
- [VSDC foreign-ownership disclosure detail route](https://vsd.vn/en/ad/{numeric-id})
- [VSDC official home and rights footer](https://vsd.vn/en/)
- [HOSE index/market-information navigation](https://www.hsx.vn/vi/cac-bo-chi-so)
- [HOSE data-feed page](https://www.hsx.vn/vi/data-feed)
- [VNX legal/document navigation](https://vnx.vn/vi/van-ban-phap-ly/6)
- [SSC securities-market legal navigation](https://ssc.gov.vn/webcenter/portal/ssc/pages_r/l/chitit)

## Bottom summary

- **Decision:** SOURCE-GAP CLOSURE; no daily foreign-room/capacity runtime is authorized.
- VSDC is the strongest official lead: dated disclosure archive, detail pages, and attachments, but no proven reusable route or 2018-current bound.
- One retained HOSE snapshot document proves useful field labels and an effective-date label, not a rights-cleared daily archive.
- Room, capacity, legal limit, holding, percentage, and flow are not interchangeable.
- No cross-source stitch, current-VN30 backfill, arithmetic reconstruction, silent zero, or false empty is allowed.
- All candidate dispatch, page, retry, redirect, and byte ledgers remain zero; no live rows were retained.
- Reopen requires one exact route set, response-backed semantics, reconciled coverage, bounded runtime, and written reuse rights.
- Need from Boss: nothing.
