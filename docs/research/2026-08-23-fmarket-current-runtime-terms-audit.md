# Fmarket current-runtime terms audit (#221)

**Retrieved:** 23 August 2026, Vietnam time (UTC+07).
**Scope:** the existing no-key Fmarket mutual-fund runtime only: listing, NAV history,
holdings, and asset allocation/detail.
**Disposition:** **`DISABLE_PENDING_PERMISSION`**.
**Status:** source/legal design only; no Fmarket API request or production change was made.

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

## Required future transition (not implemented here)

Because the current evidence does not clear the source, a later code change must be RED-first and
must be reviewed separately. The design boundary is:

- disable the Fmarket source **before network dispatch** while permission is absent or expired;
- use the existing typed `SourceUnavailable` family with one bounded public reason token such as
  `SOURCE_DISABLED_PENDING_PERMISSION`; never expose provider legal prose, contact correspondence,
  raw headers, or an unbounded terms excerpt;
- make direct `FmarketFundSource` calls and the funds facade/factory fail with zero network calls;
- preserve imports and models where compatible, but document the availability change and release
  boundary in API docs, user docs, the vnfin skill, `CHANGELOG.md`, and release notes;
- do not add fallback, proxy, session bypass, unofficial mirror, paid feed, or alternate source;
- retain fabricated/offline fixtures only. No live provider rows or permission correspondence may
  enter the repository.

The future RED/release matrix must cover each of the four operations, direct and facade entrypoints,
zero-network behavior, stable exception/type/reason, source registration, docs/API/skill/
CHANGELOG/release compatibility, full offline tests, and isolated wheel/sdist build. This audit does
not authorize any of those changes.

## Reopen and review gates

Re-open the disposition only on a fresh official document or written owner response. The evidence
must be conjunctive across route applicability, all four operations, automation, caller return,
commercial use, storage/retention/deletion, redistribution/attribution, rate/session policy, and
revision/revocation. Reachability, robots.txt, a browser User-Agent, or a third-party integration
reference is never sufficient by itself.

Until that gate is satisfied, the source remains `DISABLE_PENDING_PERMISSION`; #219, #220, and #222
remain queued and this audit does not authorize probes, RED tests, production code, push, or close.

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
caller-facing reuse for any of listing, NAV history, holdings, or allocation. Obtain written owner
coverage or complete a separately reviewed fail-before-network transition; do not silently continue
or add a fallback.
