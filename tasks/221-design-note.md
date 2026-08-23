# #221 design note — Fmarket current-runtime source/legal audit

**Phase:** `SOURCE_DESIGN`
**Decision:** **`DISABLE_PENDING_PERMISSION`**
**Scope:** existing `FmarketFundSource` only; listing, NAV history, holdings, and asset allocation/detail.
**Research artifact:** `docs/research/2026-08-23-fmarket-current-runtime-terms-audit.md`
**Retrieved:** 23 August 2026 (UTC+07)
**Clean-room status:** VNStock blacklist applied; official Fmarket/Fincorp pages only.
**Implementation status:** no API probe, no RED test, no production change, no push/close.

This is an engineering source-compliance design, not legal advice. The exact public decision is one
of the four packet outcomes: `DISABLE_PENDING_PERMISSION`. It is not `CLEARED_AS_IS`,
`CLEARED_WITH_LIMITS`, or `REMOVE_SOURCE`.

## 1. Evidence boundary and source identity

The authoritative source set is:

- **T1 — Terms of Use:** [Fmarket legal page](https://fmarket.vn/legal), Terms of Use tab,
  Vietnamese/English. Retrieved 23 August 2026. No public version, document number, or effective
  date is displayed. The page says the terms bind on access/use and may be amended with notice
  through an account, supplied email, or electronic site notices.
- **T2 — Privacy tab:** [same official legal page](https://fmarket.vn/legal), Privacy tab. Official
  indexed text identifies a personal-data policy effective 1 July 2023 and says it may be updated.
  A direct unauthenticated retrieval of the tab URL rendered the Terms of Use tab during this audit,
  so this policy is context only and never a content-reuse grant.
- **T3 — Owner/contact:** [Fmarket contact page](https://fmarket.vn/lien-he) identifies Fincorp JSC,
  the official email `hello@fmarket.vn`, telephone contacts, address, business registration, and
  fund-distribution licence. No written permission is published there.
- **T4/T5 — Platform and partners:** [Fmarket Platform](https://fmarket.vn/fmarketPlatform) and
  [Fmarket partners](https://fmarket.vn/doi-tac) identify the Fincorp platform/distribution and
  integrated-partner context. Neither publishes an API/data-reuse licence for this library.
- **T6 — First-party use case:** [Fmarket help page](https://fmarket.vn/help-center/thong-tin-ve-fmarket/fmarket-la-gi)
  describes website/mobile-app access and fund trading, not third-party programmatic collection.
- **T7 — Robots:** [robots.txt](https://fmarket.vn/robots.txt) is only a crawl directive. It is not
  permission and is not used to clear any operation.

Search exclusion used before research:
`-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"`.
No blacklisted result or derivative was opened, cited, or used. No `api.fmarket.vn` request was made.

## 2. Clause-to-runtime contract

T1 supplies a limited, non-exclusive personal website right; requires Fincorp permission for
commercial use; and prohibits software/program/algorithm collection, copying, monitoring,
aggregation, reproduction, retaining copies of copyrighted electronic material, and widespread
distribution. T1 does not name `api.fmarket.vn`, does not publish an API/developer licence, and
does not grant caller-facing return, retention, redistribution, attribution, deletion, rate, retry,
WAF, or session terms.

The host-applicability gap is **not** a permission. The existing runtime's anonymous reachability,
normal browser User-Agent, no-disk-cache behavior, synthetic fixtures, or typed models cannot cure
the missing API and caller-use grant.

| Operation | Current adapter surface | Evidence verdict | Public design result |
|---|---|---|---|
| Listing/discovery | `FmarketFundSource.list_funds()` | Software collection/copy/monitoring and aggregation are prohibited or not expressly licensed; API host applicability and caller return are unknown. | `DISABLE_PENDING_PERMISSION` |
| NAV history | `FmarketFundSource.nav_history()` | Historical collection is not separately licensed; no API, rate, retention, or redistribution grant. | `DISABLE_PENDING_PERMISSION` |
| Holdings | `FmarketFundSource.holdings()` | Portfolio rows are provider content; no automation or downstream-use grant. | `DISABLE_PENDING_PERMISSION` |
| Allocation/detail | `FmarketFundSource.asset_allocation()` | Detail/allocation content is provider content; no automation or downstream-use grant. | `DISABLE_PENDING_PERMISSION` |

The four rows are independent for review but have one common outcome. No operation is silently
cleared because another operation has a different shape or current UI exposure.

## 3. Current runtime transport/cache/retry inventory

This is an implementation inventory, not permission evidence. `FmarketFundSource` inherits the
public `HttpDataSource` controls `max_retries` and `cache_ttl`. Defaults are `max_retries=0` (one
physical attempt) and `cache_ttl=None` (cache disabled). A positive `cache_ttl` stores raw response
text in the in-memory transport cache and a valid hit returns before the HTTP callback; a positive
`max_retries` can create additional physical attempts for transient failures.

| Operation | Exact current method/path | Shared seam and future disabled gate |
|---|---|---|
| `list_funds()` | `POST /res/products/filter` | Text transport; after valid-argument validation, fail before cache lookup/cached return, POST dispatch, retry, or backoff. |
| `nav_history()` | `POST /res/product/get-nav-history` | Text transport; after valid-argument validation, fail before cache lookup/cached return, POST dispatch, retry, or backoff. |
| `holdings()` | `GET /res/products/{id}` | Shared product-detail text transport; after valid-argument validation, fail before cache lookup/cached return, GET dispatch, retry, or backoff. |
| `asset_allocation()` | `GET /res/products/{id}` | Same shared product-detail seam as holdings; after valid-argument validation, fail before cache lookup/cached return, GET dispatch, retry, or backoff. |

Invalid public arguments retain current validation precedence and existing error types; the exact
disable behavior below applies to valid calls. The future RED matrix has two scopes. Default
disabled valid calls cover every operation through direct `FmarketFundSource`, `source()`, and
`client()` with a transport spy. Positive cache/retry cases cover the direct public constructor
only: `source()` and `client()` accept only `http_get` and `timeout` and must not gain those knobs.

- default disabled calls through the direct class, `source()`, and `client()` raise
  `SourceUnavailable` with exact `str(exc) == "SOURCE_DISABLED_PENDING_PERMISSION"`, return no
  provider data, and make zero transport calls;
- a disabled direct constructor with a pre-populated positive-`cache_ttl` entry still raises before
  cache lookup/cached return, with zero transport calls and no cached provider data. Pre-seed only
  the existing test-only internal seam `HttpDataSource._cache` using
  `HttpDataSource._cache_key(url, params, json_body, headers)` and a
  `(expires_at, fabricated_response_text)` tuple; make no provider call;
- a disabled direct constructor with positive `max_retries` still makes zero physical attempts and
  zero retry/backoff calls; and
- `FmarketFundSource(...)`, `source()`, and `client()` remain lazy object-returning constructors
  with zero network calls; only a valid disabled operation call raises.

This exact message/reason token is the sole accepted public spelling. The current
`SourceUnavailable` has no new structured field in this docs packet. Provider prose, cache text,
headers, correspondence, and unbounded diagnostics are forbidden. Imports, models, signatures,
aliases, and current invalid-argument behavior remain compatible; no new opt-in/config/enum,
fallback, proxy, or alternate-source grammar is proposed.

## 4. Required legal/runtime axes

The following axes are explicit, total, and fail-closed for all four operations:

| Axis | Current status | Required evidence to clear |
|---|---|---|
| Owner/route | Fincorp is the public owner/contact; T1 does not expressly identify `api.fmarket.vn`. `LEGAL_GAP`. | Written Fincorp authority binding the API host and each operation. |
| Automated access | T1 prohibits software collection/copy/monitoring; no API exception. `BLOCKED_PENDING_PERMISSION`. | Explicit automated-access permission, including allowed client/user-agent. |
| Authentication | No-key reachability is observed in existing runtime history only; no permission inference. `UNKNOWN`. | Written authorization for anonymous/no-key automation or a documented credential flow. |
| Personal/internal use | Limited personal website right does not cover a software library returning typed results. `NOT_GRANTED`. | Explicit library/internal-use scope. |
| Commercial use | T1 requires Fincorp permission. `BLOCKED_PENDING_PERMISSION`. | Commercial-use wording naming the library/callers. |
| Caller-facing return | No grant. `NOT_GRANTED`. | Permission to return all four result families to downstream callers. |
| Storage/cache/retention | No safe retention rule; copy/retain restrictions apply. `NOT_GRANTED`. | Allowed transient/cache/persistent storage, retention duration, deletion and backup rules. |
| Attribution | No required format or safe-harbor is published. `UNKNOWN`. | Exact attribution and source-label requirements. |
| Redistribution/resale | No grant; broad distribution and commercial use are restricted. `BLOCKED_PENDING_PERMISSION`. | Downstream redistribution/resale and caller terms. |
| Rate/retry/timeout/WAF/session | No public quota or automation policy. `UNKNOWN`. | Numeric/concurrent budget, retry/backoff, timeout, WAF/session and withdrawal rules. |
| Revision/supersession | T1 can be updated by notice; no visible version/date. `DYNAMIC_UNVERIFIED`. | Version/effective date, amendment notice, revocation, and transition window. |

A missing or conflicting axis remains a blocker. `robots.txt`, the UI, a partner reference, and
normal browser behavior cannot satisfy any missing axis.

## 5. Disposition and future transition boundary

### 5.1 Current state

Keep this commit documentation-only. Do not probe the Fmarket API, change the registry, disable a
runtime path, add a fallback, or close #221 before exact design review. The current mutual-fund
runtime remains technically unchanged until a separately approved implementation transition.

### 5.2 If permission remains absent

A later RED-first implementation must make the source fail before cache lookup and network dispatch
while permission is absent or expired. After design PASS, absent permission is sufficient to start
this authorized RED/API transition; owner evidence is not a prerequisite for the fail-closed
disable. It must:

1. preserve public imports/models where compatible but make availability change explicit;
2. raise the existing typed `SourceUnavailable` family with the exact bounded public token
   `SOURCE_DISABLED_PENDING_PERMISSION`;
3. avoid provider legal prose, correspondence, raw headers, cookies, and unbounded reasons;
4. make direct source calls and the `source()`/`client()` facade/factory zero-network and
   deterministic; positive cache/retry settings are tested on the direct constructor only because
   the factory/alias signatures do not expose those knobs;
5. avoid fallback, proxy, session bypass, unofficial mirror, paid feed, or alternate provider; and
6. update API docs, user docs, the vnfin skill, `CHANGELOG.md`, and release notes in the same
   implementation change.

The later RED matrix must cover all four operations through direct and facade entrypoints, zero
network calls before cache and retry, stable exception/type/reason, import/model/signature/alias
compatibility, source registration, docs/API/skill/CHANGELOG/release behavior, the full offline
suite, and isolated wheel/sdist build. No part of that matrix is authorized by this docs commit.

### 5.3 What a written owner response must cover

A future permission request through T3 must identify the authority and explicitly cover:

- `api.fmarket.vn` plus the exact listing, NAV, holdings, and allocation operation families;
- automated no-key access, user-agent, rate/concurrency, retry/backoff, timeout, WAF/session,
  maintenance and withdrawal behavior;
- personal/internal, commercial, and caller-facing return rights;
- transient memory, cache, persistent storage, retention, deletion, and backups;
- attribution, source labels, redistribution, and resale; and
- document version/effective date, amendment/supersession, revocation, and transition handling.

A later `CLEARED_WITH_LIMITS` review must prove each limit is enforceable. A later
`CLEARED_AS_IS` review must prove all four operations and downstream use are covered without a
production restriction. `REMOVE_SOURCE` is reserved for an authoritative prohibition with no
compatible lawful mode.

## 6. Exact compatibility and release matrix

The route contract is fixed: listing is `POST /res/products/filter`; NAV history is `POST
/res/product/get-nav-history`; holdings and allocation share `GET /res/products/{id}`. The
dereferenced `v0.2.0^{}` commit is `2fe50df4f27064140ff9f7a680227a2b337ec74a`; it contains the
list/NAV/holdings boundary. Current `master` adds allocation and additive signatures/models. Future
RED/release checks must keep those boundaries explicit and bind direct class, `source()` factory,
and `client()` alias behavior to the exact routes.

The matrix must cover every live availability statement that becomes false after disabling Fmarket:

- `vnfin/diagnostics.py:318-348,663-728` and `tests/test_diagnostics.py:257-282`;
- `README.md:122-130`, `docs/api.md:85-95,354-360`, `docs/ai-usage.md:161-188`,
  `docs/tutorials/funds-and-indices.md:5-42`, and `docs/how-to/source-diagnostics.md`;
- `docs/sources/funds-fmarket.md`, Fmarket source/design docs, and
  `docs/architecture/data-domains.md`, `docs/architecture/provider-contracts.md`,
  `docs/architecture/system-overview.md`;
- `skills/vnfin/SKILL.md:63-67`, `skills/vnfin/reference/domains.md:77`, `CHANGELOG.md`,
  and release notes.

Each row must assert route, operation, direct/factory/alias zero-call behavior, direct-only positive
cache/retry cases, exact `SourceUnavailable`/message, exact `source_capabilities()` registry/export
record, diagnostics status/capabilities, source registration, the
v0.2.0/current compatibility boundary, and full offline test/build gates. No docs-only PASS may
publish or close #221: it must transition to `RED_FIRST_IMPLEMENTATION_AND_API_REVIEW`, remain
open, and receive a fresh exact-SHA implementation/API review. Only that code approval permits
push, remote verification, clean resolution, close, and re-read; #219 activates after verified
#221 closure, #220 after #219 closure, and #222 after #220 closure.

Diagnostics values are frozen, not conditional. The future `source_capabilities()` export retains
exactly one offline Fmarket provenance record with `domain="funds"`, `endpoint="fund_metadata"`,
`source="fmarket"`, `instruments=("VN open-ended mutual fund metadata",)`,
`granularity="snapshot"`, `coverage_start=None`, `coverage_end=None`, `is_default=False`,
`is_opt_in=False`, `is_single_source=True`, `limitations=("SOURCE_DISABLED_PENDING_PERMISSION",)`,
and `suggested_action=None`. The future `explain_fund_coverage()` must return
`status="source_disabled_pending_permission"`, that exact one-record `sources` tuple,
`notes=("SOURCE_DISABLED_PENDING_PERMISSION; no provider call.",)`, and `suggested_actions=()`.
It must make no availability claim or source-call suggestion. The RED matrix must assert this
complete record alongside `tests/test_diagnostics.py:257-282` and the four route calls.

The release handoff must name `APPROVED_ANCHOR` (the final reviewed docs+RED+code commit),
`APPROVED_BASE` (the reviewed design/base anchor), and `APPROVED_PATH_SET` (the exact changed-path
set). Only `APPROVED_ANCHOR` may be pushed. Remote verification must assert
`origin/master == APPROVED_ANCHOR`, `APPROVED_BASE` is an ancestor of that anchor, and
`git diff --name-only APPROVED_BASE..origin/master == APPROVED_PATH_SET`; no later local receipt
or commit may cross the remote anchor. Only then may the clean resolution comment, close,
`CLOSED`/`COMPLETED` re-read, and ordered activation occur: #219 after verified #221 closure, #220
after #219, and #222 after #220.

The remaining release surfaces are explicit: `docs/units.md:19`,
`docs/design/redundancy-failover.md:26-30,56-57`, `vnfin/funds/__init__.py:1-17,48-59`,
`vnfin/funds/fmarket.py:1-26`, `vnfin/exceptions.py:33-34`,
`tests/test_public_api_surface.py`, and `tests/snapshots/public_api_v0_2_0.json`. The future
implementation must keep the `SourceUnavailable` import/class/constructor/signatures frozen, keep
the exact disabled string, and update its public documentation to cover policy-disabled sources in
addition to transport/network failures. Public-surface and snapshot checks remain green with no
new reason field or carrier.

## 7. Review/reopen and release gates

The exact-SHA design reviewer must verify:

- official source links and retrieval date are present;
- T1/T2 identity/effective/revision caveats are not overstated;
- all four operation rows and every legal/runtime axis are total;
- no API probe, provider row, query-bearing URL, header, cookie, token, full-term text, or
  correspondence is committed;
- blacklist, secret, diff/path, and clean-tree gates pass; and
- before design PASS, no RED/code/push/close is authorized; after design PASS, absent permission
  authorizes the exact `RED_FIRST_IMPLEMENTATION_AND_API_REVIEW` transition;
- owner evidence is a disposition-reopen input, not a prerequisite for the fail-closed disable;
  a fresh conjunctive owner-evidence review may change `DISABLE_PENDING_PERMISSION` before the
  implementation transition; and
- post-PASS lifecycle preserves `DISABLE_PENDING_PERMISSION` unless that fresh disposition review
  changes it.

No push or close is allowed before design PASS. A design PASS at this docs-only stage does not
authorize publication or closure. It authorizes only the fresh
`RED_FIRST_IMPLEMENTATION_AND_API_REVIEW` transition described above. Any implementation transition
requires RED-first tests, the exact docs/API/runtime release matrix, and another exact-SHA code
review before publication or closure.

The final implementation review must freeze `APPROVED_ANCHOR`, `APPROVED_BASE`, and
`APPROVED_PATH_SET` in its handoff. It may authorize publication only when
`origin/master == APPROVED_ANCHOR`, `APPROVED_BASE` is an ancestor, and the remote diff path set
equals `APPROVED_PATH_SET` with no later local receipt crossing the anchor; then and only then may
the clean resolution, close/re-read, and ordered #219 → #220 → #222 activation occur.

## 8. Lifecycle

- Current phase: `SOURCE_DESIGN`.
- Actor: `vnfin-oss`.
- Next action after this correction: `RETURN_EXACT_SHA_DESIGN_REVIEW`.
- #219, #220, and #222 remain queued; no queue item is activated by this design note.
- No probe/RED/code/push/close before exact-SHA design PASS.

## Bottom summary

- Decision: `DISABLE_PENDING_PERMISSION` for listing, NAV, holdings, and allocation/detail.
- T1's personal website right and software-collection restrictions are current evidence; API scope
  and caller-facing reuse remain ungranted/unknown.
- Fincorp owner/contact path is recorded; no written API/data permission was found.
- Current runtime is unchanged; no API probe or production capability was added.
- A design PASS cannot publish/close; absent permission, the disable transition follows the exact
  RED-first implementation and code-review path above, while clear/remove requires a fresh
  source/legal review.
- Exact artifacts are this note, the source-vetting report, and the backlog lifecycle entry only.
