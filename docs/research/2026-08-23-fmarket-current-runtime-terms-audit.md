# Fmarket current-runtime terms audit (#221)

**Retrieved:** 23 August 2026, Vietnam time (UTC+07).
**Scope:** the existing no-key Fmarket mutual-fund runtime only: listing, NAV history,
holdings, and asset allocation/detail.
**Disposition:** **`DISABLE_PENDING_PERMISSION`**.
**Status at design anchor:** source/legal design only; no Fmarket API request or production change
was made in this artifact. **Current implementation status (#221):** the approved
`DISABLE_PENDING_PERMISSION` transition is now implemented in the runtime; valid public calls fail
closed before cache/network with `SourceUnavailable("SOURCE_DISABLED_PENDING_PERMISSION")`. This
report remains the source/legal evidence record, not a live-access instruction.

This is conservative engineering compliance triage, not legal advice.  A reachable public
response is not evidence of permission to automate, retain, return, or redistribute it.

## Clean-room and research boundary

The VNStock exclusion was applied before and throughout this research. Search exclusion string:
`-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"`.
No blacklisted result, code, endpoint map, schema, package, or derivative was opened, cited, or
used. Sources below are official Fmarket/Fincorp pages only. No Fmarket API route was probed.

The repository's existing adapter code and synthetic-test contract were used only to identify the
four already-shipped operation surfaces. Existing technical reachability, prior live probes, and
anonymous browser access are **not** permission evidence.

## Decision in one paragraph

Fincorp's current public Terms of Use grant only a limited, non-exclusive website right for
personal access and access to financial products. The same page prohibits software/programmatic
collection, copying, monitoring, aggregation, reproduction, retaining copies of copyrighted
electronic material, widespread distribution, and commercial use without Fincorp permission. The
terms do not state whether `api.fmarket.vn` is an authorized software interface, do not grant
caller-facing return or redistribution, and publish no quota/retry/session policy. No public
developer/API licence or written owner permission was found. Therefore none of the four current
operations is clearable; the least-assumptive transition is `DISABLE_PENDING_PERMISSION`, not
`CLEARED_AS_IS` and not an unqualified continuation of the current runtime.

## Official source ledger

| ID | Official owner/path | Document identity and language | Retrieved / effective / revision evidence | What it establishes |
|---|---|---|---|---|
| T1 | [Fmarket legal page](https://fmarket.vn/legal), Terms of Use tab | “Điều khoản sử dụng (Terms of Use)”; Vietnamese and English; no displayed version, document number, or revision date | Retrieved 23 August 2026. The page says the terms bind on access/use and may be updated with notice through an account, email, or electronic site notices. | Personal-use limit; commercial-use permission requirement; no software collection/copy/monitoring; no aggregation/copy/reproduction; no broad distribution; termination for violation. |
| T2 | [Fmarket legal page](https://fmarket.vn/legal), Privacy tab as indexed by the official page | “Chính sách xử lý dữ liệu cá nhân (Personal Data Handling Policy)”; Vietnamese and English; indexed text states effective 1 July 2023 | Retrieved/indexed 23 August 2026. A direct unauthenticated GET of the tab URL rendered the Terms of Use tab instead; the tab-selection behavior is therefore recorded as a source-integrity caveat. The policy says it may be modified/updated. | Personal-data handling context only. It is not a data-content, API, software-collection, or redistribution grant and is not used to clear any operation. |
| T3 | [Fincorp/Fmarket contact page](https://fmarket.vn/lien-he) | Fincorp JSC; Vietnamese official contact page; business registration and fund-distribution licence are displayed | Retrieved 23 August 2026. No owner response or permission letter was found on the page. | Canonical permission/contact path: `hello@fmarket.vn`, 1900 571 299 / 028 3636 0755, and the listed Fincorp address. |
| T4 | [Fmarket Platform](https://fmarket.vn/fmarketPlatform) | Official platform description; Vietnamese; footer identifies FINCORP JSC | Retrieved 23 August 2026. No API/developer licence or data-reuse grant displayed. | Fmarket presents itself as a licensed fund-distribution platform; that operating role does not grant third-party software collection or redistribution. |
| T5 | [Fmarket partners](https://fmarket.vn/doi-tac) | Official partner/integrated-partner page; Vietnamese; footer identifies FINCORP JSC | Retrieved 23 August 2026. It describes relationships with fund managers and integrated partners but gives no public API/data licence terms. | Partnership language is not written permission for this library or its callers. |
| T6 | [Fmarket fund information](https://fmarket.vn/help-center/thong-tin-ve-fmarket/fmarket-la-gi) | Official help page; Vietnamese; footer identifies FINCORP JSC | Retrieved 23 August 2026. Describes website/mobile-app fund access and trading; no programmatic-access grant. | Confirms the first-party website/app use case, not an external automated collection right. |
| T7 | [Fmarket robots.txt](https://fmarket.vn/robots.txt) | Plain-text crawl directive; no licence or permission language | Retrieved 23 August 2026. It disallows selected search paths and provides a sitemap. | Robots directives are operational crawl hints only; they are not a licence, API grant, or redistribution permission. |

**Document/version rule:** T1 has no public effective date or revision identifier. Its effective
rule is “on access/use,” and its amendment mechanism is notice through the account, supplied email,
or electronic site notices. T2 has an indexed effective date of 1 July 2023 but its current tab
rendering was inconsistent at retrieval. No authoritative versioned API terms were found. Any future
review must record the retrieval date and the visible document identity again; it must not assume
that a later page is byte-equivalent to this audit.

## Clause-to-runtime mapping

The terms refer to the Fmarket website/content/services rather than naming the separate
`api.fmarket.vn` host. That creates an applicability gap, not an exemption. The four adapter
operations consume provider content that is presented by the same Fmarket service, so the
conservative gate treats each as unapproved until Fincorp expressly confirms the API and the
specific caller-facing use.

| Current operation | Current result surface | Relevant T1 restriction family | Automated access / auth | Caller return, storage, retention, redistribution | Decision |
|---|---|---|---|---|---|
| Product listing / discovery (`list_funds`) | Typed fund identity, code, name, manager, asset type, latest NAV and metadata | Personal website right; no software collection/copy/monitoring; no aggregate/copy/reproduce; commercial use requires permission | No-key reachability is not authorization. The terms do not publish an API grant or rate/retry/session policy. | No grant for returning typed rows to library callers, caching/retaining them, or redistributing them; no attribution/deletion rule is stated. | `DISABLE_PENDING_PERMISSION` |
| NAV history (`nav_history`) | Typed daily NAV series and metadata | Same restrictions; historical series is collected/retained content, not a separately licensed feed | No public API/developer terms; no quota, WAF, retry, timeout, or anonymous automation policy | No grant for caller-facing series, persistence, commercial use, or redistribution. Runtime-only fetching does not cure the collection restriction. | `DISABLE_PENDING_PERMISSION` |
| Holdings (`holdings`) | Typed disclosed holding rows, weights, instrument type and timestamps | Same restrictions; aggregation/copying/reproduction maps directly to a portfolio collection | API host applicability is not stated; no owner confirmation | No grant for returning, retaining, storing, or redistributing typed holdings; no deletion or attribution contract. | `DISABLE_PENDING_PERMISSION` |
| Asset allocation/detail (`asset_allocation`) | Typed asset classes, sector weights and detail metadata from the product document | Same restrictions; detail/allocations are provider content and may be copied/aggregated by the adapter | No public API licence or bounded anonymous-use rule | No grant for caller-facing return, cache/storage, retention, or downstream redistribution. A typed empty allocation does not alter the rights analysis. | `DISABLE_PENDING_PERMISSION` |

### Axis verdicts shared by all four operations

- **Owner/route:** Fincorp is the official Fmarket owner/contact identity. T1 is a
  `fmarket.vn` website/service document; explicit application to `api.fmarket.vn` is **unknown**.
- **Automated collection:** the current terms expressly identify programs, algorithms, or software
  used to collect, copy, and monitor the site as prohibited. No API-specific exception is public.
- **Authentication:** no-key reachability is a transport fact only. It is not a grant of anonymous
  automated access.
- **Personal/internal use:** the limited personal website right cannot be expanded into a library
  that automates collection and returns typed data to arbitrary callers.
- **Commercial use:** expressly requires Fincorp permission; no such permission was found.
- **Caller-facing return:** not granted. The terms' personal-access language does not authorize
  this library to serve provider content to third parties.
- **Storage/cache/retention:** no retention or cache permission is stated; copy/retain restrictions
  make the absence material. The adapter's current no-disk-cache behavior does not resolve the
  collection and caller-return questions.
- **Attribution:** no attribution format or safe-harbor is published. Attribution alone cannot
  cure the restrictions.
- **Deletion/withdrawal:** no data-retention/deletion contract exists for this library's copies;
  terms may change and access may terminate after violation.
- **Rate/retry/timeout/WAF/session:** no public numeric quota or anonymous software policy was
  found. Do not infer a safe retry or crawl budget from observed reachability.
- **Revision:** T1 can change by notice; no stable version/effective-date identifier was visible.
  A later review must re-fetch the official page and re-evaluate all four operations.

## Pre-#221 transport/cache seam (historical design evidence)

This section records the pre-#221 design-anchor transport/cache/retry seam, not current runtime
behavior. Current valid calls do not build request bodies, enter cache lookup, dispatch, parse, or produce `EmptyData`.
They fail closed with `SOURCE_DISABLED_PENDING_PERMISSION` before that seam.
The matrices below are retained to explain compatibility and the reviewed RED contract, not to
authorize or describe a live Fmarket call.

At the design anchor, this was a code-contract inventory, not evidence that the provider permits the
calls. The pre-#221 `FmarketFundSource` inherited the public `HttpDataSource` controls `max_retries`
and `cache_ttl`.
The defaults are `max_retries=0` (one physical attempt, with no retry) and `cache_ttl=None` (cache
off). A positive `cache_ttl` stores the raw response text in an in-memory transport cache and a
valid cache hit is returned before the HTTP callback is invoked. A positive `max_retries` permits
additional physical attempts for transient failures. Neither behavior supplies a legal, quota, or
redistribution grant.

| Public operation | Pre-#221 transport seam | Pre-#221 cache/retry path | Approved current disabled boundary |
|---|---|---|---|
| `list_funds()` | `POST https://api.fmarket.vn/res/products/filter` | Shared text transport; cache can short-circuit the POST; retry can add physical POST attempts. | After valid-argument validation, fail before cache lookup/cached return and before POST. |
| `nav_history()` | `POST https://api.fmarket.vn/res/product/get-nav-history` | Shared text transport; cache can short-circuit the POST; retry can add physical POST attempts. | After valid-argument validation, fail before cache lookup/cached return and before POST. |
| `holdings()` | `GET https://api.fmarket.vn/res/products/{id}` | Shared detail text transport; cache can short-circuit the GET; retry can add physical GET attempts. | After valid-argument validation, fail before cache lookup/cached return and before GET. |
| `asset_allocation()` | `GET https://api.fmarket.vn/res/products/{id}` (shared with holdings) | Shared detail text transport; cache can short-circuit the GET; retry can add physical GET attempts. | After valid-argument validation, fail before cache lookup/cached return and before GET. |

At the design anchor, the planned disabled gate was an operation-level gate immediately before the
transport seam: it had to run before `_request_text` cache lookup, before a cached response could be
returned, before `_http_get`/HTTP dispatch, and before any retry or backoff. The approved current
implementation now enforces that boundary. Existing invalid-argument validation remains first and
keeps its current `InvalidData`/`TypeError`/`ValueError` behavior; the disabled result applies only
to a valid call. This preserves validation precedence without allowing a valid disabled call to
read provider data.

The design-anchor RED matrix has two explicit scopes. For each of the four operations, default
disabled valid calls use the direct `FmarketFundSource`, `source()`, and `client()` entrypoints with
a synthetic transport spy. The positive cache/retry cases use the direct public constructor only:
`source()` and `client()` accept only `http_get` and `timeout` and must not gain cache/retry
parameters.

| RED fixture and entrypoint scope | Required result |
|---|---|
| Disabled source, default `cache_ttl=None`, `max_retries=0` — direct class, `source()`, and `client()` | Existing `SourceUnavailable`; exact public message/reason is `SOURCE_DISABLED_PENDING_PERMISSION`; zero transport calls and no provider data. |
| Disabled direct `FmarketFundSource` with a pre-populated positive-`cache_ttl` cache entry | The same exact `SourceUnavailable` before cache lookup; no cached return, zero transport calls, and no provider data. Pre-seed only the existing test-only internal seam `HttpDataSource._cache` using `HttpDataSource._cache_key(url, params, json_body, headers)` with `(expires_at, fabricated_response_text)`; make no provider call. |
| Disabled direct `FmarketFundSource` with positive `max_retries` | The same exact `SourceUnavailable` before the first attempt; zero physical attempts, zero retries/backoff, and no provider data. |
| `FmarketFundSource(...)`, `source()`, and `client()` construction | Return the source object lazily with zero network calls; a valid disabled operation call, not construction, raises the exact exception. |

The approved current disabled public carrier is the existing `SourceUnavailable` exception with
`str(exc) == "SOURCE_DISABLED_PENDING_PERMISSION"`; that token is the only accepted public
message/reason spelling in the approved implementation contract. The current exception has no new
structured field in this docs packet. Provider text, legal prose, cache contents, headers, contact
correspondence, and unbounded diagnostics are never included. Any later structured reason would
require an explicitly reviewed exception/public-snapshot change; no new opt-in, enum, fallback,
proxy, or alternate-source grammar is introduced here. Imports, models, method signatures, and the
`client` alias remain compatible.

## What would clear or limit the source

No permission request was sent in this docs-only round. The official contact path is T3. A written
owner response must identify Fincorp/Fmarket authority and explicitly cover all of the following,
not merely say that the website is public:

1. the `api.fmarket.vn` host and the exact four operation families;
2. automated no-key requests, user-agent requirements, rate limits, concurrency, retry/backoff,
   timeout, WAF/session behavior, and maintenance/withdrawal notice;
3. personal/internal and commercial use;
4. returning typed listing, NAV, holdings, and allocation results to library callers;
5. transient memory, cache, persistence, retention, deletion, and backup behavior;
6. attribution, source labeling, and downstream redistribution/resale rights; and
7. the permission's document version/effective date, amendment/supersession rule, and revocation
   handling.

A future `CLEARED_WITH_LIMITS` outcome is possible only if every current operation is covered by an
exact written limit that can be enforced and documented. A future `CLEARED_AS_IS` outcome requires
an authoritative grant covering all current operations and caller-facing uses without a production
restriction. If the owner confirms that the shipped use is prohibited and no compatible permission
or lawful mode exists, a later design review may choose `REMOVE_SOURCE`.

## Historical transition contract and current implementation boundary

At the design anchor, the exact lifecycle was **design PASS → fresh RED-first implementation/API
packet → exact-SHA code review → publish/close**. That lifecycle is a completed historical receipt
through the B1-B4 implementation review. The Fmarket source is implemented and remains disabled
before cache/network while this final R1-R2 documentation/fixture/lifecycle correction is reviewed.
No push, resolution, close, or #219 activation is authorized until this final review and merged-tree
verification; #219 remains behind verified #221 closure, followed by #220 and #222 in queue order.

The approved implementation boundary is:

- disable the Fmarket source **before cache lookup and network dispatch** while permission is absent
  or expired, using the exact `SourceUnavailable`/`SOURCE_DISABLED_PENDING_PERMISSION` contract
  above;
- make direct `FmarketFundSource` calls and the `source()`/`client()` facade/factory paths fail
  with zero transport calls; positive cache/retry settings are tested on the direct constructor
  only because the factory/alias signatures do not expose those knobs;
- preserve imports, models, method signatures, and aliases; do not add fallback, proxy, session
  bypass, unofficial mirror, paid feed, alternate source, or new opt-in/config/enum grammar;
- expose only bounded sanitized diagnostics and never provider legal prose, correspondence, raw
  headers, cookies, cache text, or unbounded reasons; and
- update every public availability statement and release artifact in the same approved code range.

### Exact route, version, and release matrix (historical design evidence)

The route identity was fixed for the design-anchor RED and release checks: listing is `POST
/res/products/filter`; NAV history is `POST /res/product/get-nav-history`; holdings and allocation
share `GET /res/products/{id}`. The dereferenced `v0.2.0^{}` commit is
`2fe50df4f27064140ff9f7a680227a2b337ec74a`, where list/NAV/holdings are the relevant shipped
surfaces. Current `master` is the compatibility boundary that adds allocation and additive
signatures/models; the approved implementation does not silently rewrite the v0.2.0 claims.

The exact design-anchor RED/release matrix bound those routes to direct class, `source()` factory,
and `client()` alias assertions, exact `source_capabilities()` registry/export behavior, diagnostics
status/capabilities, and the v0.2.0/current distinction. The approved implementation inspected and
updated only claims that became false:

- `vnfin/diagnostics.py:318-348,663-728` and
  `tests/test_diagnostics.py:257-282`;
- `README.md:122-130`, `docs/api.md:85-95,354-360`, `docs/ai-usage.md:161-188`,
  `docs/tutorials/funds-and-indices.md:5-42`, and `docs/how-to/source-diagnostics.md`;
- `docs/sources/funds-fmarket.md`, the Fmarket-bearing source/design docs, and the relevant
  architecture docs (`docs/architecture/data-domains.md`,
  `docs/architecture/provider-contracts.md`, `docs/architecture/system-overview.md`);
- `skills/vnfin/SKILL.md:63-67` and `skills/vnfin/reference/domains.md:77`; and
- `CHANGELOG.md` and release notes.

The diagnostics contract is frozen rather than conditional. The current
`source_capabilities()` export retains exactly one offline Fmarket provenance record with
`domain="funds"`, `endpoint="fund_metadata"`, `source="fmarket"`,
`instruments=("VN open-ended mutual fund metadata",)`, `granularity="snapshot"`,
`coverage_start=None`, `coverage_end=None`, `is_default=False`, `is_opt_in=False`,
`is_single_source=True`, `limitations=("SOURCE_DISABLED_PENDING_PERMISSION",)`, and
`suggested_action=None`. The current `explain_fund_coverage()` returns
`status="source_disabled_pending_permission"`, that exact one-record `sources` tuple,
`notes=("SOURCE_DISABLED_PENDING_PERMISSION; no provider call.",)`, and
`suggested_actions=()`. It makes no availability claim or source-call suggestion. The approved current
diagnostic returns this record, and the RED/implementation tests cover it together with the
`tests/test_diagnostics.py:257-282`
expectations together with the four route calls.

The release handoff must name three exact values: `APPROVED_ANCHOR` (the final reviewed docs+RED+
code commit), `APPROVED_BASE` (the reviewed design/base anchor), and `APPROVED_PATH_SET` (the exact
changed paths in the approved range). Only the approved anchor may be pushed. Remote verification
must assert `origin/master == APPROVED_ANCHOR`, `APPROVED_BASE` is an ancestor of that anchor, and
`git diff --name-only APPROVED_BASE..origin/master == APPROVED_PATH_SET`; a later local receipt or
commit must not cross the remote anchor. Only then may the clean resolution comment, close,
`CLOSED`/`COMPLETED` re-read, and ordered activation occur: activate #219 after verified #221
closure, then #220 after #219, then #222 after #220.

The remaining release surfaces are explicit: `docs/units.md:19`,
`docs/design/redundancy-failover.md:26-30,56-57`, `vnfin/funds/__init__.py:1-17,48-59`,
`vnfin/funds/fmarket.py:1-26`, `vnfin/exceptions.py:33-34`,
`tests/test_public_api_surface.py`, and `tests/snapshots/public_api_v0_2_0.json`. The approved
implementation keeps the `SourceUnavailable` import/class/constructor/signatures frozen, keeps the
exact disabled string, and documents policy-disabled sources in addition to transport/network
failures. Public-surface and snapshot checks remain green with no new reason field or carrier.

The matrix must assert exact routes, all four operation outcomes, direct/factory/alias zero-call
behavior, direct-only positive cache/retry cross-product, exact exception/message, exact diagnostics
registry/export record, import/model/signature compatibility, full offline tests, and isolated
wheel/sdist build. At the design anchor, this audit and its correction did not authorize any RED
test, production code, source registration, probe, push, or close. Those gates have since been
completed for the implementation; the current final R1-R2 correction remains docs/fixture/lifecycle
only and makes no provider request or capability claim.

At the design anchor, this section was documentation-only. The approved implementation now exists
and the source remains disabled; this audit remains historical source/legal evidence and does not
describe a permission to call Fmarket.

## Reopen and review gates

At the design anchor, before design PASS, this audit was documentation-only and no Fmarket probe,
RED test, production code, push, or close was authorized. Design PASS and the RED-first implementation
review have since occurred. The Fmarket source is implemented and remains disabled before
cache/network while permission is absent; the current final review changes no runtime behavior.

Fresh official evidence or a written owner response may reopen the **source/legal disposition** while
the implemented disable remains in force. Such evidence must be conjunctive across route applicability,
all four operations, automation, caller return, commercial use, storage/retention/deletion,
redistribution/attribution, rate/session policy, and revision/revocation. Reachability, robots.txt,
a browser User-Agent, or a third-party integration reference is never sufficient by itself. A fresh
review may change the outcome to `CLEARED_AS_IS`, `CLEARED_WITH_LIMITS`, or `REMOVE_SOURCE`; it does
not authorize a new RED/implementation path or runtime capability in this completed review. #219,
#220, and #222 remain queued.

## Sources

All URLs below are official Fmarket/Fincorp pages retrieved or checked on 23 August 2026. The
repository stores links and short paraphrases only, not full terms, raw HTML, provider rows, query
parameters, headers, cookies, tokens, or correspondence.

- [Fmarket legal page — Terms of Use tab](https://fmarket.vn/legal)
- [Fmarket contact / Fincorp identity](https://fmarket.vn/lien-he)
- [Fmarket Platform](https://fmarket.vn/fmarketPlatform)
- [Fmarket partners and integrated partners](https://fmarket.vn/doi-tac)
- [Fmarket help — what is Fmarket](https://fmarket.vn/help-center/thong-tin-ve-fmarket/fmarket-la-gi)
- [Fmarket robots.txt](https://fmarket.vn/robots.txt) (crawl directive only, not permission)

## Bottom line

`DISABLE_PENDING_PERMISSION` is the only defensible current design disposition. The terms' public
website right and current technical reachability do not establish lawful automated collection or
caller-facing reuse for any of listing, NAV history, holdings, or allocation. Written owner coverage
may reopen that disposition; absent it, the implemented fail-before-network transition remains
disabled. No transition remains to complete in this docs-only correction. Do not silently continue or
add a fallback.
