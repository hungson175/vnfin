# #203 design/source note — VSDC corporate-action seed discovery

**Status:** `BLOCKED — source/legal/operational gate; no no-seed source enabled; design only`
**Issue:** #203
**Reviewer packet:** `tasks/203-corp-action-seed-discovery-spec.md` at reviewer `c75a86e`
**Research:** [`docs/research/2026-08-22-vsdc-corp-action-seed-discovery.md`](../docs/research/2026-08-22-vsdc-corp-action-seed-discovery.md)
**Clean-room:** official VSDC-owned pages and first-party HTML/JavaScript observations only; the mandatory repository blacklist was applied to every search and no excluded material was opened or used.
**Authorization boundary:** this note authorizes no production code, parser, default source-chain entry, runtime request, cache, bundled index, redistribution, push, or issue close.

## 0. Decision and preserved compatibility

The current no-seed source chain remains **empty**. No candidate meets all of the accepted legal,
identity, coverage, contract, and operational gates. The correct disposition is:

```text
source_disposition = NO_SOURCE_ENABLED
source_gap = LEGAL_AND_NON_AUTHORITATIVE_ROUTE_CONTRACT
runtime_discovery = DISABLED
production_code = NOT_AUTHORIZED
```

This is a design/source closure, not a claim that VSDC has no corporate-action data. The observed
routes are promising technical evidence only. A future implementation requires a new design PASS
after the reopen criteria in §9 are evidenced.

The existing #163 compatibility boundary is unchanged:

- keep `vnfin.corp_actions.dividends(symbol, start=None, end=None, http_get=None, timeout=25.0,
  seed_id=None, latest_id=None, max_fetch=None)` unchanged;
- preserve explicit `seed_id` behavior and its existing bounded same-issuer crawl;
- preserve the existing warnings `corp_action_source_partial`, `corp_action_seed_not_found`,
  `coverage_truncated_at_max_fetch`, and `corp_action_fetch_incomplete` for existing callers;
- do not register a no-seed VSDC candidate, change the public facade, alter the API snapshot, or
  add a new source to the runtime chain in this commit; and
- do not turn a missing seed or an empty list into a confirmed “no dividend” result.

## 1. Candidate source gate

All candidates are first-party routes on the official `vsd.vn` host. The search/detail/list routes
were observed in server HTML or first-party JavaScript, not in a versioned public API specification.
The exact observations and legal findings are in the linked research report.

| Candidate | Exact observed route | Identity / coverage gate | Current disposition |
|---|---|---|---|
| C1 official search/list | `GET /vi/search?text={symbol}&type=4&obj=0&buss=11021&fdate={from}&tdate={to}`; page `POST` to the same URL with `{"SearchKey":4,"CurrentPage":N}` and the page token | Search text and title are fuzzy hints. Every `/vi/ad/{id}` must pass announcement identity. Empty search is not coverage proof. | `DISABLED`; technically useful candidate, legal and route contract unresolved |
| C1a search suggestion | Observed `POST /search-suggest` with `{"text":"{symbol}","type":"5"}`; JSON suggestions point to security-detail links but provide no page total | Hint only: `success: 0` can accompany data, and no-match has no proof. Exact detail identity is still mandatory. | `DISABLED`; optional resolver evidence only, never an absence source |
| C2 issuer/security detail → rights list | `GET /vi/search?text={symbol}&type=5...` → `GET /vi/s-detail/{id}` → observed `POST /isuisser-thq/search` with `{"SearchKey":"{id}","CurrentPage":N,"RecordOnPage":10}` | Detail response must prove exact ticker, issuer, security type, and available ISIN/venue. Rights rows still require announcement identity. | `DISABLED`; strongest technical candidate, no public contract/licence |
| C3 issuer news fallback | Same exact detail identity, then observed `POST /isuisser-tcdk/search` with the same paging body | Broader issuer news is not equivalent to rights coverage. Every seed requires the same announcement proof. | `DISABLED`; fallback candidate only |
| C4 recent numeric-ID scan | Existing `GET /vi/ad/{id}` bounded scan | Numeric adjacency proves neither issuer identity nor date coverage; `/ad/{id}` redirects and is rejected. | `DISABLED`; no-seed fallback not authorized; explicit-seed compatibility preserved |

**Future source order if, and only if, a later gate enables it:** C1 → C2 → C3. C4 remains
unavailable unless a later owner-backed evidence round proves deterministic coverage without abusive
requests. The order does not permit a weaker candidate to override a stronger identity or coverage
failure.

Other observed first-party facilities (`/vi/lich-giao-dich?tab=LICH_THQ` with `/lich-thq/search`,
`/vi/id/{issuer_id}` with `/danh-sach-ck/search`, and broad `/vi/alo/ISSUER`/`/vi/alc/6` lists) are
recorded in the research report. They are conditional hints or issuer corroboration, not part of the
future default chain: the rights-calendar probe mixed `FPT`, `CFPT`, `FOX`, `FTS`, and `FRT`, while
the broad lists have no symbol/date-scoped completeness proof.

## 2. Exact future route contract (non-authoritative)

The following is a future implementation contract, not an API addition in this commit.

### 2.1 Common transport allow-list

Every request must satisfy all of the following before it is sent:

1. scheme is `https`;
2. host is exactly `vsd.vn`, port is 443/default, and the path is one of the allow-listed routes
   below;
3. certificate validation succeeds with the standard trust store; no `--insecure`, `-k`, browser
   trust override, or proxy is permitted;
4. redirects are disabled; any 3xx is a `redirect_rejected` attempt, including a same-host locale
   redirect;
5. the response has exactly one `Content-Type` header; after the first header colon, trim outer
   ASCII whitespace, lowercase ASCII for comparison, and require the complete value to equal exactly
   `text/html; charset=utf-8`; POST request bodies separately use the exact JSON content type shown
   in their route contract; and
6. a 200 response is not accepted until the route-specific HTML shape and identity predicates pass.

A value such as `text/html; charset=utf-8:unexpected`, a duplicate header, missing header, generic
maintenance HTML, login HTML, or a body with only a matching title fails closed. The parser must not
accept a media-type prefix while ignoring a colon-suffixed or extra parameter value.

The allow-list is:

```text
GET  /vi/search
POST /search-suggest              # optional C1a hint; never an absence proof
GET  /vi/s-detail/<decimal-id>
POST /isuisser-thq/search
POST /isuisser-tcdk/search
GET  /vi/ad/<decimal-id>
```

The rights-calendar and broad issuer/category facilities in the research report are deliberately
outside this allow-list. They are not enabled candidates in this design round.

Relative `/ad/<decimal-id>` links returned by a list are parsed only for their decimal ID and are
canonicalized to `/vi/ad/<id>`. The client never follows the relative route as a redirect and never
accepts a host, scheme, path, or query supplied by an HTML link.

### 2.2 Search routes

The symbol is trimmed and uppercased once. Empty, whitespace-only, non-canonical, or overlong input
fails before budget reservation and before network. A non-empty symbol is URL-encoded exactly once.

C1 page 1 uses:

```text
GET https://vsd.vn/vi/search
    ?text={encoded_symbol}
    &type=4
    &obj=0
    &buss=11021
    &fdate={encoded_start_or_empty}
    &tdate={encoded_end_or_empty}
```

C1 pages after page 1 use the exact same URL and:

```text
Content-Type: application/json;charset=utf-8
__VPToken: <ephemeral token from the page>
{"SearchKey":4,"CurrentPage":N}
```

C2's security-code search uses the same official search page with `type=5` and the same non-empty
symbol preflight. It is a candidate locator, not identity proof. A page is valid only when its
route-specific section (`Tin tức` for C1 or `Mã CK` for C2), list shape, and link shape are present.
A route-declared empty list may be recorded as `bounded_seed_discovery_exhausted`; it never proves
that the requested issuer has no relevant event.

The scheduler requests page 1 first, reads the server-declared end page, and requests only ascending
pages `2..min(end_page, configured_page_cap)`. A missing, non-integer, contradictory, or out-of-range
end-page value is `schema_or_identity_drift`; it is never repaired by guessing page 2. GET query
pagination is not accepted for these AJAX pages.

C1a is a single optional hint request using the same fresh anonymous cookie/token pair. Its JSON
shape must be an object whose `data`, when present, is a list of objects with a non-empty `href`
and content field. `success: 0` is not a Boolean success assertion; it may accompany `data`. The
route has no total or pagination and therefore can only supply bounded detail candidates. A no-match
response never establishes an issuer or an empty event set.

### 2.3 Issuer/security identity

Every candidate detail ID is a hint. At most five candidates are inspected in deterministic search
order. A detail response proves identity only if all required predicates pass:

```text
requested_symbol == normalized(response["Mã chứng khoán"])
issuer_name = non-empty response["Tên Tổ chức đăng ký chứng khoán"]
security_type = an allowed share/security value, not an untyped derivative result
issuer_anchor = canonical issuer link/id when present, otherwise a non-ambiguous exact issuer name
```

The response may additionally provide ISIN and trading venue. When present, they become part of the
identity tuple and must agree with later announcement responses. A missing required field, conflicting
ISIN/name/code, derivative-like result, or two candidates with conflicting identity is respectively
`identity_missing`, `identity_mismatch`, or `identity_ambiguous`; it is never treated as “issuer not
found” and never used to accept a seed.

The identity proof carried forward is the immutable tuple:

```text
(symbol, issuer_anchor, issuer_name, security_type, isin_or_none, venue_or_none)
```

A later response must echo the exact symbol and issuer anchor/name. If the later response omits a
field that was available in the identity anchor, the proof is not silently downgraded: it is
`schema_or_identity_drift` unless a future owner contract explicitly marks that field optional.

### 2.4 Rights/news list routes

After an exact C2 identity anchor, the future client may use the observed first-party route:

```text
POST https://vsd.vn/isuisser-thq/search
Content-Type: application/json;charset=utf-8
__VPToken: <ephemeral token acquired by the preceding detail GET>
{"SearchKey":"<decimal-detail-id>","CurrentPage":N,"RecordOnPage":10}
```

C3 uses `/isuisser-tcdk/search` with the same body shape. Page 1 is requested as `CurrentPage: 1`;
there is no GET fallback. The route-specific response must contain the exact observed rights/news
table headings and row/link shape. For the rights route, the required heading set is:

```text
STT
Ngày đăng ký cuối cùng
Tên quyền
```

The three required rights columns and the already-proven issuer identity are bound to one table. A
row is usable only when the mapped values occur at the mapped heading columns, the row is a distinct
non-heading `td` row, and the relevant cell is populated after trimming. A repeated heading row,
blank/whitespace row, generic maintenance table, or a row from a different table is rejected. A
nested valid report table is not rejected merely because it is nested; it must independently satisfy
this same binding.

The response's page metadata controls traversal. At most seven rights pages and 22 issuer-news pages
are attempted in the default discovery plan; the latter is the largest observed VIC sample, not an
owner-backed coverage promise. A future owner-confirmed larger bound requires a new gate. If a page
is valid and declares no rows, that is bounded exhaustion, not confirmed empty.
If page metadata is absent or malformed, stop with `schema_or_identity_drift` and do not request the
next page.

### 2.5 Announcement/seed validation

A seed is accepted only for canonical `GET https://vsd.vn/vi/ad/<decimal-id>` with:

- verified HTTPS and HTTP 200, no redirect;
- exact normalized MIME from §2.1;
- route-specific announcement shape;
- non-empty registered organisation and security fields;
- exact response ticker equal to the requested symbol;
- issuer anchor/name consistent with the detail identity;
- ISIN consistent when both responses provide it; and
- required corporate-action/right fields, including the explicitly labelled record-date field.

A title, sidebar link, ID sequence, or search phrase is never enough. The future adapter must parse
only response-labelled dates. `Ngày đăng ký cuối cùng` is a record-date field; it is not silently
renamed to announcement date, payment date, UTC time, or a market session. Search `fdate`/`tdate`
parameters and page order do not establish event-date coverage.

HTTP 200 is not semantic success: an invalid numeric announcement ID can return an official empty or
removed-article page. Missing title/identity/right fields therefore fails as route-shape or identity
drift, never as a valid non-event and never as confirmed empty. Likewise, a missing or mismatched
anonymous cookie/`__VPToken` pair can produce HTTP 400 with an empty body; that is a token/transport
failure, not an empty list. A future implementation may refresh the anonymous page only under a
source-owner-approved contract; this note does not authorize a hidden retry loop.

## 3. No-false-absence outcome and diagnostic contract

The future result carries independent axes. They must be finite typed values, not provider strings:

```text
SourceStatus   = DISABLED | AVAILABLE | UNAVAILABLE | REDIRECT_OR_TLS | TRANSPORT_FAILED
IdentityStatus = NOT_ATTEMPTED | PROVEN | NOT_PROVEN | MISMATCH | AMBIGUOUS | DRIFT
CoverageStatus = NOT_ATTEMPTED | BOUNDED_UNKNOWN | PAGE_COMPLETE | PROVEN | EMPTY_PROVEN
CrawlStatus    = NOT_STARTED | NO_SEED | COMPLETE | PARTIAL | TRUNCATED
BudgetStatus   = NOT_STARTED | AVAILABLE | EXHAUSTED
```

The stable top-level outcome is exactly one of:

```text
confirmed_event_rows
bounded_seed_discovery_exhausted
source_unavailable
schema_or_identity_drift
seed_obtained_crawl_partial
crawl_truncated
confirmed_empty
```

The outcome mapping is binding:

- `confirmed_event_rows`: at least one response-backed event row passed identity and schema checks;
- `bounded_seed_discovery_exhausted`: all permitted discovery work completed or a valid empty list
  was reached, but no seed was proven; this is **not** confirmed absence;
- `source_unavailable`: every usable candidate was disabled, unreachable, redirected, or failed
  strict transport before a valid response;
- `schema_or_identity_drift`: a required route shape, MIME, page contract, or response identity
  failed and no other candidate produced a valid result;
- `seed_obtained_crawl_partial`: a valid seed produced some rows but the crawl could not establish
  complete traversal for a non-budget reason;
- `crawl_truncated`: a valid seed was obtained but the crawl request budget was exhausted; and
- `confirmed_empty`: only when an owner-backed coverage contract proves the response covers the
  complete requested symbol/date scope, all pages were consumed without drift/transport failure,
  exact identity passed, and no eligible event row exists.

An unmatched ticker, an empty search list, an empty rights table, a seed validation miss, a recent-ID
window with no hit, a page cap, a redirect, a timeout, or an unverified date window can never produce
`confirmed_empty`. Until owner coverage proof exists, the only permitted no-seed result is
`bounded_seed_discovery_exhausted` (or a more specific unavailable/drift outcome).

### 3.1 Attempt, error, warning, and coverage typing

Future diagnostics are immutable tuples with no raw provider body, token, cookie, URL query, or
unbounded provider message:

```text
AttemptStatus = SUCCEEDED | TRANSPORT_FAILED | HTTP_REJECTED | REDIRECT_REJECTED |
                MIME_REJECTED | SHAPE_REJECTED | IDENTITY_REJECTED | BUDGET_EXHAUSTED
AttemptStage  = SEARCH | IDENTITY | RELATED_RIGHTS | RELATED_NEWS | SEED | CRAWL

ErrorCode = PREFLIGHT_INVALID_SYMBOL | SOURCE_DISABLED | TLS_ERROR | TRANSPORT_ERROR |
            REDIRECT_REJECTED | HTTP_4XX | HTTP_5XX | MIME_MISMATCH | ROUTE_SHAPE_MISMATCH |
            PAGE_METADATA_INVALID | IDENTITY_MISSING | IDENTITY_MISMATCH | IDENTITY_AMBIGUOUS |
            COVERAGE_UNPROVEN | BUDGET_EXHAUSTED
```

The future warning vocabulary preserves the existing #163 tokens and adds only design-approved
stable tokens:

```text
corp_action_source_partial
corp_action_seed_not_found
coverage_truncated_at_max_fetch
corp_action_fetch_incomplete
corp_action_source_unavailable
corp_action_schema_or_identity_drift
corp_action_discovery_budget_exhausted
corp_action_confirmed_empty
```

`Attempt` fields are executable-contract fields:

```text
ordinal: positive integer, unique and contiguous in send order
stage: AttemptStage
route: one of the five allow-listed route names
status: AttemptStatus
http_status: None or integer 100..599
mime: None or the exact normalized MIME value
physical_attempts: integer 0..2
identity_proven: boolean
page: None or positive integer
```

`errors` and `warnings` are sorted/deduplicated tuples of the finite codes above. Provider text may
be retained only as redacted local debug data outside the result contract; it is not returned,
serialized, cached, or redistributed. `coverage` must include:

```text
status: CoverageStatus
requested_start: date or None
requested_end: date or None
pages_seen: non-negative integer
pages_expected: None or positive integer
rows_seen: non-negative integer
proof: tuple of finite proof labels, empty unless status is PROVEN/EMPTY_PROVEN
```

Invariants:

1. `ordinal` order is the scheduler's actual physical-send order;
2. `physical_attempts` counts retries, not just logical URLs;
3. `confirmed_empty` requires `CoverageStatus.EMPTY_PROVEN` and a non-empty proof tuple;
4. `BUDGET_EXHAUSTED` is never rewritten as transport failure or empty data;
5. `identity_proven` is true only for the exact response-backed tuple in §2.3; and
6. no diagnostic can include a token, cookie, raw HTML, unbounded URL, or provider-supplied warning.

## 4. Deterministic discovery/crawl/retry budgets

No provider request limit was published. The following are conservative future library limits, not
claims about VSDC. In the current blocked state, no no-seed request is made and all these counters
remain zero.

### 4.1 Single-symbol discovery ledger

The invocation owns one shared ledger. It is not copied per route, candidate, page, or retry.

| Counter | Default and hard limit | Meaning |
|---|---:|---|
| `max_c1_search_pages` | 2 | C1 page 1 plus at most one server-declared next page |
| `max_c1a_suggestion_requests` | 1 | optional C1a hint request; no pagination |
| `max_c2_search_pages` | 2 | C2 page 1 plus at most one server-declared next page |
| `max_identity_candidates` | 5 | detail pages inspected in search/link order |
| `max_thq_pages` | 7 | observed FPT rights-page bound; no guessed extra page |
| `max_tcdk_pages` | 22 | observed VIC issuer-news bound; no guessed extra page |
| `max_seed_validations` | 3 | total across C1/C2/C3, not per route |
| `max_discovery_requests` | 84 physical attempts | hard shared discovery cap, including retries |
| `max_transport_retries` | 1 per logical request | only timeout, connection, 429, and 5xx |
| inter-request delay | 250 ms minimum | sequential policy, not provider promise |
| per-request timeout | 25 s | future default, not a live probe claim |

The maximum logical discovery calls are `2 + 1 + 2 + 5 + 7 + 22 + 3 = 42`; with one retry per call,
`42 * 2 = 84` physical attempts. Therefore the hard ledger cap is executable and exact. A lower
caller-supplied cap may exhaust earlier; no caller may raise a cap above these hard limits.

The scheduler order is deterministic: input symbol order, C1 global-search pages, optional C1a hint,
C2 search pages and candidate order, C2 rights pages, C3 pages, then seed validation in first-seen
numeric-ID order; duplicate IDs are removed before reservation. A retry immediately follows its
failed logical request and consumes a new reservation. A 4xx, redirect, MIME failure, shape failure,
identity failure, token-pair failure, or malformed page is not retried.

### 4.2 Atomic reservation rule

`reserve(kind)` is the only operation allowed to send a request. Under the invocation ledger lock (or
equivalent atomic compare-and-swap when concurrency is introduced), it:

1. checks both the kind-specific remaining limit and the total discovery limit;
2. if either is exhausted, records `BUDGET_EXHAUSTED` and returns no reservation;
3. otherwise increments the charged physical-attempt counter and assigns the next contiguous ordinal;
   and
4. only after the increment returns a reservation does the scheduler call the HTTP seam.

There is no “check then send” split, no private retry counter, no automatic fallback after a failed
reservation, and no request after exhaustion. The reservation is charged before transmission, so a
timeout or connection failure still consumes the attempt. The ledger snapshot must expose
`limit`, `charged`, `remaining`, `logical_requests`, `retry_requests`, and `exhausted` for discovery
and crawl separately.

### 4.3 Crawl ledger and explicit-seed behavior

Discovery and crawl have distinct ledgers. Once a seed is proven, the existing explicit-seed BFS may
use `max_fetch` with these corrected semantics:

- `max_fetch` defaults to 300 and has a hard allowed range of `1..300`;
- it counts physical HTTP attempts, including retries, not IDs inspected or rows returned;
- every unique canonical `/vi/ad/{id}` request reserves from the crawl ledger before transmission;
- duplicate IDs are deduplicated before reservation; and
- exhaustion before the queue is empty yields `crawl_truncated`,
  `coverage_truncated_at_max_fetch`, and the existing incomplete-source diagnostic rather than an
  empty or complete result.

A seed discovery budget cannot be borrowed by crawl, and a crawl budget cannot be borrowed by
another symbol. The current note does not alter the existing explicit-seed implementation; these
are the future correction contracts that code and tests would have to implement after approval.

### 4.4 One-symbol and 30-symbol diagnostic cost

A future bulk diagnostic is discovery-only by default. It is not a historical event crawl and cannot
claim absence. Its exact future shape is:

```python
def discover_seeds_bulk(
    symbols: Sequence[str],
    *,
    start: date | None = None,
    end: date | None = None,
    max_symbols: Literal[30] = 30,
    max_total_discovery_requests: Literal[2520] = 2520,
    max_concurrency: Literal[1] = 1,
    http_get=None,                 # synthetic-fixture seam only
    timeout: float = 25.0,
) -> SeedDiscoveryBulk: ...
```

The single-symbol future shape is the same contract with one symbol and
`max_discovery_requests=84`. Both shapes are **non-authoritative sketches**, not public APIs in
this commit. The bulk scheduler rejects more than 30 symbols, duplicate canonical symbols, and
parallelism above one before network. Each symbol owns an 84-attempt sub-ledger; the bulk ledger is
`30 * 84 = 2520` physical discovery attempts. It processes symbols FIFO and never lets one symbol
borrow another's reserved budget.

Request-count examples, excluding server latency:

| Scenario | One symbol | 30-symbol discovery diagnostic |
|---|---:|---:|
| C1 page 1 + three seed validations, no retries | 4 | 120 |
| C1 page 1 + C2 detail/rights path + three validations, no retries | 7 | 210 |
| Full permitted discovery path with every logical call retried once | 84 | 2,520 hard maximum |
| Explicit-seed crawl, separate from discovery | up to 300 | not part of the default discovery diagnostic |

A separately requested full 30-symbol crawl would need an independently approved total crawl cap of
`30 * 300 = 9,000` physical attempts and a combined hard cap of `2,520 + 9,000 = 11,520`; it is
not the default #203 diagnostic and is not authorized by this note. The counts are budgets, not a
coverage promise.

## 5. Source/legal/coverage status axes

The current candidate status is deliberately split so that a technical 200 cannot mask a legal or
coverage failure:

| Axis | Current C1/C2/C3 finding | Required reopen value |
|---|---|---|
| official ownership | `PASS` for the `vsd.vn` host and VSDC footer | owner confirms exact routes |
| no-login reachability | `PASS` for sampled canonical HTML calls | repeatable route-specific pass |
| response identity | `SAMPLED_ONLY` (FPT detail/announcement) | exact identity contract confirmed across samples |
| pagination/window | `SAMPLED_ONLY` | documented server-bound traversal and date window |
| date semantics | `UNRESOLVED` beyond labelled record-date fields | owner confirms each requested date field |
| completeness/empty meaning | `UNRESOLVED` | response-backed coverage proof |
| TLS/redirect/MIME | sampled HTTPS pass; non-canonical route redirects | strict repeated pass, no redirects |
| rate/concurrency/cache | `UNRESOLVED`; no provider limits found | written operational terms |
| licence/redistribution | `UNRESOLVED_PERMISSION_REQUIRED` | written owner permission |
| runtime disposition | `DISABLED` | all axes pass and design re-review PASS |

The axes are not collapsed into a single “available” flag. In particular, legal permission alone
would not make an unproven empty list safe, and technical reachability alone would not permit runtime
fetching.

## 6. Future diagnostics and no-false-absence rules

A future caller receives a typed diagnostics object even when no rows are returned. At minimum it
must expose `outcome`, all five status axes, ordered attempts, typed errors/warnings, discovery and
crawl ledger snapshots, and the response-backed identity proof when one exists.

The following rules are mandatory:

- `source_unavailable` is used for disabled, TLS, redirect, timeout, connection, or HTTP failures;
- `schema_or_identity_drift` is used for wrong MIME, generic HTML, missing/malformed route shape,
  ambiguous detail rows, or conflicting issuer/ticker/ISIN;
- `bounded_seed_discovery_exhausted` means only that the bounded discovery plan found no proven seed;
- `seed_obtained_crawl_partial` means a proven seed yielded rows but traversal was not complete for a
  non-budget reason;
- `crawl_truncated` is reserved for a proven seed whose separate crawl ledger was exhausted;
- `confirmed_event_rows` requires at least one valid response-backed row; and
- `confirmed_empty` is impossible until the owner-backed coverage proof, complete pagination, exact
  identity, and requested date semantics all pass.

No response-unidentified HOSE-like fallback, numeric-ID guess, title-only match, blank global search,
or request-date assumption is permitted. No response may be described as a daily/event absence merely
because the provider returned an empty HTML list.

## 7. Future TDD/verification matrix (not implemented here)

No production code or test code is changed in this docs-only round. If a later design PASS authorizes
implementation, tests must be written red-first with committed synthetic fixtures and must cover:

1. symbol preflight rejects blank/invalid input without an HTTP call;
2. C1/C2 route URLs, exact JSON bodies, token/cookie handoff, and no GET pagination fallback;
3. route-specific positive pages plus maintenance/login/generic HTML negatives;
4. exact MIME positive and complete post-first-colon/colon-suffixed/duplicate-header negatives;
5. exact detail identity, wrong ticker, missing identity, conflicting ISIN, derivative-like result,
   and ambiguous candidate negatives;
6. rights-table heading/column binding, populated distinct non-heading row, blank-row and repeated-
   heading negatives, plus a valid nested report-table case;
7. missing/malformed page metadata, server end-page bounds, deterministic ascending traversal, and no
   request after a bound or budget is exhausted;
8. announcement identity matching, relative-link canonicalization, redirect rejection, TLS/transport
   failures, and no title-only seed acceptance;
9. exact retry ledger: one retry only for the permitted classes, retry charged before send, atomic
   reservation, no post-exhaustion HTTP call, deterministic FIFO, and separate discovery/crawl caps;
10. empty search/list, no-seed, partial-crawl, and truncated-crawl diagnostics never become
    `confirmed_empty`;
11. explicit `seed_id` BFS compatibility and existing warning-token preservation; and
12. a 30-symbol sequential diagnostic with `120/210/2520` request-count assertions and no bulk
    budget borrowing.

Live tests, if ever added, must be opt-in against official hosts only and never run in CI. No live
response, token, cookie, broker row, or provider body may be committed as a fixture or bundled
artifact.

## 8. Documentation and release boundary

This task adds only the research report and this design/source note. There is no public API change,
source registration, skill change, changelog entry, API snapshot change, production code, or test
fixture in this commit. A later additive implementation would require the normal docs, skill,
CHANGELOG, API-snapshot, synthetic-fixture, full-suite, build/install, secret-scan, and blacklist
checks in the same approved change.

## 9. Reopen criteria and review request

Reopen #203 for implementation only after all of the following are written and verifiable:

1. VSDC owner permission covers automated no-login runtime fetch, ephemeral token/cookie handling,
   cache duration, derived normalized rows, attribution, and redistribution;
2. VSDC confirms the exact route shapes, identity fields, date semantics, pagination/empty semantics,
   rate, concurrency, and retention rules;
3. fresh strict HTTPS probes pass with exact MIME, no redirects, verified TLS, route-specific shape,
   and response-backed identity;
4. coverage proof supports requested date windows and defines the only conditions for
   `confirmed_empty`;
5. synthetic red-first tests implement every §7 contract on the merged tree; and
6. the reviewer grants a new design PASS before any code, push, or issue close.

This note is ready for design review at the exact commit containing it. Reviewer: please spawn
parallel sub-agents for source/legal, parser/identity, and budget/diagnostic checks, then return the
verdict against this SHA. No production code, push, or close is authorized before PASS.
