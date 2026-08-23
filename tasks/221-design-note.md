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
- **T6 — First-party use case:** [Fmarket help page](https://fmarket.vn/help-center/thong-tin-ve-
  fmarket/fmarket-la-gi) describes website/mobile-app access and fund trading, not third-party
  programmatic collection.
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

## 3. Required legal/runtime axes

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

## 4. Disposition and future transition boundary

### 4.1 Current state

Keep this commit documentation-only. Do not probe the Fmarket API, change the registry, disable a
runtime path, add a fallback, or close #221 before exact design review. The current mutual-fund
runtime remains technically unchanged until a separately approved implementation transition.

### 4.2 If permission remains absent

A later RED-first implementation must make the source fail before network dispatch while permission
is absent or expired. It must:

1. preserve public imports/models where compatible but make availability change explicit;
2. raise the existing typed `SourceUnavailable` family with a bounded public token such as
   `SOURCE_DISABLED_PENDING_PERMISSION`;
3. avoid provider legal prose, correspondence, raw headers, cookies, and unbounded reasons;
4. make direct source calls and the funds facade/factory zero-network and deterministic;
5. avoid fallback, proxy, session bypass, unofficial mirror, paid feed, or alternate provider; and
6. update API docs, user docs, the vnfin skill, `CHANGELOG.md`, and release notes in the same
   implementation change.

The later RED matrix must cover all four operations through direct and facade entrypoints, zero
network calls, stable exception/type/reason, import/model compatibility, source registration,
docs/API/skill/CHANGELOG/release behavior, the full offline suite, and isolated wheel/sdist build.
No part of that matrix is authorized by this docs commit.

### 4.3 What a written owner response must cover

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

## 5. Review/reopen and release gates

The exact-SHA design reviewer must verify:

- official source links and retrieval date are present;
- T1/T2 identity/effective/revision caveats are not overstated;
- all four operation rows and every legal/runtime axis are total;
- no API probe, provider row, query-bearing URL, header, cookie, token, full-term text, or
  correspondence is committed;
- blacklist, secret, diff/path, and clean-tree gates pass; and
- post-PASS lifecycle says `DISABLE_PENDING_PERMISSION` remains the disposition unless a fresh
  conjunctive owner-evidence review changes it.

No push or close is allowed before design PASS. After a design PASS, this packet may be published
only as the two named Markdown artifacts plus the backlog lifecycle record. Any code transition
requires a fresh implementation packet, RED-first tests, and another exact-SHA code review.

## 6. Lifecycle

- Current phase: `SOURCE_DESIGN`.
- Actor: `vnfin-oss`.
- Next action after this docs commit: `RETURN_EXACT_SHA_DESIGN_REVIEW`.
- #219, #220, and #222 remain queued; no queue item is activated by this design note.
- No probe/RED/code/push/close before exact-SHA design PASS.

## Bottom summary

- Decision: `DISABLE_PENDING_PERMISSION` for listing, NAV, holdings, and allocation/detail.
- T1's personal website right and software-collection restrictions are current evidence; API scope
  and caller-facing reuse remain ungranted/unknown.
- Fincorp owner/contact path is recorded; no written API/data permission was found.
- Current runtime is unchanged; no API probe or production capability was added.
- Any disable/clear/remove transition requires a fresh RED or source/legal review as applicable.
- Exact artifacts are this note, the source-vetting report, and the backlog lifecycle entry only.
