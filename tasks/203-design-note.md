# #203 design/source note — VSDC corporate-action seed discovery

**Status:** `BLOCKED — docs-only source-gap closure correction; no new source enabled`
**Issue:** #203
**Reviewer packet:** `tasks/203-corp-action-seed-discovery-spec.md` at reviewer `c75a86e`
**Blocked review:** `reviews/review-202608221623-issue203-design-source-gate.md` at reviewer `f2e9e51`, reviewed SHA `fa8a05a74c6791ad2921937bf5fa5689777c912f`
**Research:** [`docs/research/2026-08-22-vsdc-corp-action-seed-discovery.md`](../docs/research/2026-08-22-vsdc-corp-action-seed-discovery.md)
**Clean-room:** official VSDC-owned pages and first-party HTML/JavaScript observations only; the mandatory repository blacklist was applied to every search and no excluded material was opened or used.
**Authorization boundary:** this correction authorizes no production code, parser, new source-chain entry, runtime request, cache, bundled index, redistribution, push, or issue close.

## 0. Corrected decision

The source/legal conclusion remains unchanged: none of the newly observed VSDC candidates has both a
reliable owner-backed route contract and resolved runtime/caching/redistribution permission.
Therefore:

```text
new_candidate_chain_C1_C2_C3 = EMPTY_AND_DISABLED
legacy_C4_numeric_scan = ACTIVE_IN_MERGED_RUNTIME_BUT_NON_AUTHORITATIVE
source_gap = OPEN_UNTIL_CONJUNCTIVE_REOPEN_EVIDENCE
production_code = NOT_AUTHORIZED
```

This note is a source-gap closure, not an implementation design. The observations in the research
report document why C1-C3 are worth a later source-gate review; they do not authorize treating those
HTML/JavaScript routes as an executable API or claiming complete corporate-action coverage.

## 1. Current merged-runtime truth and compatibility boundary

The accepted packet follows the existing #163 implementation. This correction must describe it
truthfully and must not silently remove or redefine it.

### 1.1 Existing facade and explicit-seed path

The shipped public facade remains:

```text
vnfin.corp_actions.dividends(
    symbol,
    start=None,
    end=None,
    http_get=None,
    timeout=25.0,
    seed_id=None,
    latest_id=None,
    max_fetch=None,
)
```

The actual facade forwards an optional `seed_id`, `latest_id`, and positive `max_fetch` to
`VsdcCashDividendSource`. Explicit `seed_id` remains supported. Its bounded same-organisation BFS,
visited-ID cycle guard, deduplication, FIFO queue order, parse behavior, and current injected
`http_get` compatibility are preserved.

No new C1-C3 source is registered. The current adapter's existing VSDC announcement-page path is
not replaced by this note.

### 1.2 Existing no-seed behavior is legacy C4 and remains active

When `seed_id` is omitted, the merged implementation still performs the legacy C4 operation:

1. `_find_seed()` scans numeric announcement IDs downward from `latest_id`;
2. its scan window is `min(max_fetch, DEFAULT_MAX_FETCH)` and each scanned page is attempted until a
   matching ticker is found or the window is exhausted;
3. after a seed is found, `_crawl()` runs the existing same-organisation BFS; and
4. the seed page may be fetched again by the BFS, as in the shipped implementation.

C4 is bounded and useful only as a non-authoritative legacy fallback. Numeric adjacency does not
prove issuer identity, complete announcement coverage, or requested-date coverage. It is therefore
not promoted to a reliable new discovery source, but it remains active for compatibility.

The existing `max_fetch` contract is preserved exactly; this note does **not** impose a new hard
upper bound, change its type/range, or redefine its unit:

- the public adapter accepts a positive integer `max_fetch`;
- the legacy no-seed scan uses `min(max_fetch, DEFAULT_MAX_FETCH)` as its numeric window;
- the BFS stops after its existing `max_fetch` page-fetch counter while the queue has a frontier;
- each visited ID is fetched at most once by the BFS; and
- no new physical-request, retry, or bulk interpretation is introduced here.

The current result/warning behavior is also preserved:

```text
corp_action_source_partial
corp_action_seed_not_found
coverage_truncated_at_max_fetch
corp_action_fetch_incomplete: <bounded count and explanation>
```

`corp_action_seed_not_found` discloses that the active legacy scan found no matching page in its
bounded window; it is not a confirmed never-paid result. `corp_action_fetch_incomplete` may carry the
existing bounded count suffix and must not be collapsed to a finite token without a future additive
compatibility decision.

## 2. New candidate chain: empty and disabled

The newly researched candidates are recorded as conditional source evidence only:

| Candidate | Observed official facility | Current status | Reopen issue |
|---|---|---|---|
| C1 | Global search/list: `GET /vi/search?...type=4...`; later pages observed through `POST` to the same route with JSON page state | `DISABLED`; not in the runtime chain | route/method/response envelope, pagination, identity, coverage, legal/runtime terms |
| C1a | Search suggestion: observed `POST /search-suggest` with JSON hints | `DISABLED`; hint only, not an absence source | JSON response semantics, no pagination/total, identity and transport seam |
| C2 | Security detail `GET /vi/s-detail/{id}` plus observed `POST /isuisser-thq/search` | `DISABLED`; strongest technical candidate | persistent session metadata, exact route schema, identity/row binding, coverage, legal terms |
| C3 | Observed `POST /isuisser-tcdk/search` after the same detail identity | `DISABLED`; noisy fallback only | route-specific headings, bounded all-candidate evaluation, coverage, legal terms |
| C4 | Existing bounded numeric-ID scan and announcement-page fetch | `ACTIVE_LEGACY_ONLY`; not reliable new discovery | preserve current behavior; no claim of complete or lawful reusable coverage |

No C1-C3 response is used by the merged runtime. C4 is not silently disabled. The official rights
calendar, issuer-detail, and broad category lists remain research observations outside the new chain;
they are not fallbacks or source registrations.

## 3. What the research proves, and what it does not

The [official VSDC search page](https://vsd.vn/vi/search), [security detail example](https://vsd.vn/vi/s-detail/166),
and [announcement example](https://vsd.vn/vi/ad/195957) establish sampled first-party reachability
and useful response fields. The [official contact navigation](https://vsd.vn/vi/) and the contact
information recorded in the research report provide an owner path for permission questions.

The samples do **not** establish:

- a published API or stable route contract;
- a response/status/header/effective-URL/session seam compatible with the shipped adapter;
- a persistent anonymous cookie plus `__VPToken` GET-to-POST session in the injected runtime path;
- complete issuer/date coverage, page-bound semantics, or the meaning of an empty list;
- an exact identity proof for every C1, C2, or C3 candidate;
- a legal grant for automated fetching, caching, derived rows, attribution, or redistribution; or
- provider-approved rate, concurrency, retry, retention, or operational limits.

The current shared transport returns body text through the preserved injected seam: three positional
arguments for GET and four for POST. The default transport creates a fresh client per request and
does not expose response status, headers, redirect history, effective URL, or a persistent cookie jar
through that seam. This is an explicit reopen blocker, not a license to change the seam in a docs-only
commit.

## 4. Candidate-specific response and identity gaps

These are reopen requirements, not implementation claims.

### 4.1 Transport and route metadata

A future approved implementation would need an additive, metadata-bearing session/response seam that
can observe, without breaking the existing three/four-argument `http_get` callers:

- request method, canonical URL, exact query/body serialization, and request headers;
- HTTP status, response headers, complete `Content-Type`, effective URL, and redirect history;
- persistent cookie state and the ephemeral `__VPToken` required by the observed AJAX flow; and
- route-specific HTML versus JSON bodies without treating body text alone as a successful response.

For each C1-C3 route, the owner-approved contract must bind the exact method, path, parameters/body,
request MIME, response MIME, session/token acquisition, page serialization, redirect policy, TLS
requirements, and semantic error/empty shape. C1 must bind both its page-1 GET and later-page POST;
C1a must bind JSON separately from HTML; C2/C3 must bind their exact POST bodies and headings. A
future design must list every route/method pair explicitly; an allow-list containing only `GET
/vi/search` cannot authorize the observed `POST /vi/search` pagination.

No redirect, generic maintenance page, login page, missing metadata, wrong MIME, or certificate
failure may be interpreted as empty corporate-action data.

### 4.2 Response-backed identity and seed binding

A later implementation must fail closed on identity, but this closure does not pretend that the
predicate is executable through the current body-only seam. Reopen evidence must prove all of the
following for every enabled candidate path:

1. the requested symbol is canonicalized once and compared exactly with a structured response ticker;
2. issuer name/anchor, security type, and available ISIN/venue are captured from the same identity
   response and cannot conflict across responses;
3. all bounded exact-symbol candidates are evaluated in deterministic order before a conflicting
   candidate is selected or rejected;
4. the rights/news table has unique normalized heading positions, with duplicate, permuted, shifted,
   and heading-only negatives;
5. the accepted announcement link is bound to the mapped `Tên quyền`/event cell in that same table,
   not merely found elsewhere in the page or in another table;
6. `/ad/{id}` is canonicalized to `/vi/ad/{id}` without following a redirect;
7. the announcement response independently echoes the exact ticker and consistent issuer identity;
   and
8. an HTTP 200 empty/removed-article page, non-target page, ambiguous identity, or missing required
   field is a rejected response, never a seed and never a confirmed absence.

C1 hints without a prior detail identity need a complete, source-specific proof path before they can
be used. C2/C3 need bounded exhaustive/deduplicated candidate handling; a single matching string is
not sufficient.

### 4.3 Coverage, outcome, and no-false-absence gaps

The current public result has the existing warning contract, not the speculative typed outcome enum in
the previous note. A future additive design must first define a total, mutually exclusive result
constructor/XOR matrix that covers at least:

- no seed found by the active legacy C4 window;
- a proven seed with no qualifying rows while requested coverage remains unknown;
- proven rows with later partial or truncated crawl, including deterministic precedence between
  `rows_present` and `partial/truncated`;
- all C1-C3 candidates exhausted without a seed;
- source unavailable, redirect/TLS/transport failure; and
- schema/identity drift.

Only an owner-backed complete response/date-coverage proof may introduce a future confirmed-empty
state. An empty search/list, a valid empty page, a numeric scan miss, a bounded page cap, a failed
transport, or a non-target 200 can never become a confirmed “no dividend” claim. The future result
must make candidate exhaustion conjunctive: every permitted candidate/page bound must complete with
valid route shape, identity, and coverage semantics before absence is even considered.

No public or bulk result model, facade, warning token, serialization contract, or API snapshot is
introduced by this correction.

## 5. Legal and operational gate

The legal posture remains unresolved:

```text
official_host_ownership = sampled_pass
no_login_reachability = sampled_pass
route_contract = unresolved_non_authoritative
identity = sampled_only
coverage_and_empty_semantics = unresolved
rate_concurrency_retry_retention = unresolved
runtime_permission = unresolved_permission_required
redistribution = not_granted
new_source_disposition = disabled
```

The [official VSDC legal/rules section](https://vsd.vn/vi/lel) did not provide a public API licence or
redistribution grant in the inspected material. The [official robots path](https://vsd.vn/robots.txt)
did not provide a usable crawl policy. These observations are not permission or legal advice.
Written VSDC owner permission must cover runtime no-login fetching, session/token handling, caching,
derived normalized event rows, attribution, redistribution, rate/concurrency, and retention.

Conservative probe ceilings in the research report are evidence bounds only. They do not change
`max_fetch`, add retry behavior, or authorize a bulk API. A reopened design must separately define
logical candidate/page limits and physical request/retry limits, but this closure deliberately does
not choose or publish those runtime values.

## 6. Conjunctive reopen evidence

A new design/implementation gate may reopen C1-C3 only when **every** condition below is evidenced;
any one unresolved axis keeps the chain empty:

1. **Owner/legal:** written VSDC permission covers the exact routes, automated runtime fetches,
   anonymous session/token mechanism, cache duration, derived outputs, attribution, redistribution,
   rate, concurrency, and retention.
2. **Transport/session:** an additive response/session seam preserves existing `http_get` arity while
   exposing method/body, status, headers, effective URL, redirects, TLS result, cookie state, and
   token lifecycle; exact per-route MIME and redirect rules are testable.
3. **Route/schema:** C1 GET/POST, C1a JSON, C2 detail/THQ, and C3 TCDK methods, bodies, page bounds,
   date serialization, empty/error shapes, and route-specific headings are each fixed by evidence;
   generic HTML cannot pass as a route response.
4. **Identity/seed:** unique heading-column mapping, exact link-cell binding, complete bounded
   candidate disambiguation, response-backed issuer/ticker/ISIN proof, canonical announcement
   validation, and all malformed/non-target/HTTP-200-empty negatives pass synthetic tests.
5. **Coverage/outcomes:** a total/exclusive result matrix covers no seed, proven seed/no matching rows,
   rows-plus-partial/truncated precedence, candidate exhaustion, source failure, schema drift, and
   the only allowed confirmed-empty proof. Candidate exhaustion is conjunctive across all enabled
   candidates and pages.
6. **Logical/physical budgets:** separate atomic ledgers charge a logical key once and a physical
   `(logical_key, retry_number)` transmission separately; retries cannot consume page/candidate
   cardinality; every physical send has one contiguous ordinal; zero-send budget diagnostics have no
   physical-send ordinal; duplicate reservations, boundaries, and non-sequential retries are tested.
7. **Compatibility and evidence:** explicit-seed BFS, legacy C4 no-seed scan, existing `max_fetch`
   behavior, dynamic warning suffixes, cycle/dedup/FIFO behavior, and the current body-only test seam
   remain unchanged until an additive design is separately approved.
8. **Merged-tree gate:** synthetic fixtures and red-first tests pass on the merged tree, live official
   probes remain opt-in, no provider response/token/cookie is committed, the mandatory blacklist scan
   is clean, and the reviewer grants a new design PASS before production code, push, or close.

These conditions are intentionally conjunctive. A technical route pass cannot waive legal permission;
legal permission cannot waive identity/coverage proof; and a budget model cannot waive compatibility.

## 7. Scope of this correction

This commit changes documentation only:

- it records the active legacy C4 scan and the empty/disabled new C1-C3 chain;
- it removes the prior speculative public/bulk API sketch and the proposed changed `max_fetch`
  semantics;
- it preserves the shipped facade, explicit-seed path, legacy no-seed behavior, warnings, and
  body-only seam as the compatibility boundary; and
- it retains source observations, legal gaps, probe bounds, and conjunctive reopen evidence.

No production code, tests, fixtures, API snapshot, skill, changelog, source registration, push, or
issue close is included. Reviewer: please spawn parallel source/legal, identity/schema, and
logical/physical-budget sub-agents and perform exact-SHA design/source re-review. No implementation is
authorized before PASS.
