# #215 source/design note — stock dividends and bonus shares

**Issue:** #215
**Packet:** `tasks/215-stock-bonus-distributions-source-spec.md` at reviewer anchor `4a6780b`
**Date:** 23 August 2026 (Vietnam time, UTC+7)
**Status:** `SOURCE-GAP CLOSURE` — docs/design only; no RED, model, accessor, source registration, or runtime capability
**Current published base:** `origin/master` exact `8126dd5510b6390f91c9feeb43e047b2b9b88bc1`
**Annotated historical `v0.2.0` boundary:** exact `2fe50df4f27064140ff9f7a680227a2b337ec74a`; no `vnfin/corp_actions` tree; not current cash behavior
**Research:** [`docs/research/2026-08-23-vn-stock-bonus-distributions-source-vetting.md`](../docs/research/2026-08-23-vn-stock-bonus-distributions-source-vetting.md)

## 0. Decision and hard boundary

The accepted product scope is stock-dividend and bonus-share history for long-term investors. The
breadth/signal remains caller-side. This note does **not** widen the current cash-dividend surface:

```text
vnfin.corp_actions.dividends(...) -> DividendHistory[CashDividendEvent(kind="CASH")]
VsdcCashDividendSource                 = unchanged
new stock/bonus source registry         = empty and disabled
new public model/accessor               = not created
RED tests / production code              = not authorized
```

The source-gate result is `SOURCE-GAP CLOSURE`. Official notices for both kinds exist, but no single
no-login owner/route set currently proves identity, kind, ex/effective date, unit, event revision,
full coverage, bounded runtime, and lawful reuse together for the inclusive request
`2018-08-13..2026-08-19`. A docs-only source-gap PASS may authorize publication, remote verification,
the clean no-capability resolution, and close/re-read only; it never authorizes TDD or implementation.
A new implementation requires a fresh exact-SHA design PASS after all reopen conditions in section 8
are evidenced.

## 1. Clean-room and compatibility contract

`docs/vnstock-blacklist.md` was read on 23 August 2026 before the research pass. Search queries used
the mandatory negative exclusions, and no excluded result or derived material was opened, cited, or
used. Only official/provider-owned VSDC, VNDIRECT, HOSE, and HNX material is considered here.

The following current contracts are outside this issue and must remain byte-for-byte compatible:

- `CashDividendEvent.kind` remains `"CASH"`; it is not widened to stock or bonus values.
- `CashDividendEvent.ex_date` remains unavailable under the current VSDC cash source; no record-date
  arithmetic is added to that surface.
- `vnfin.corp_actions.dividends()` keeps its existing arguments, warnings, explicit-seed behavior,
  legacy bounded scan behavior, injected HTTP seam, and VSDC parser semantics.
- No VSDC search/detail/announcement route observed by this research is added to the runtime chain.
- No live provider row, ratio, date, cookie, token, query-bearing URL, response digest, or screenshot
  is committed.

## 2. Source-gate disposition

The detailed direct observations and official links are in the [source-vetting report](../docs/research/2026-08-23-vn-stock-bonus-distributions-source-vetting.md).
The candidate cells below are intentionally independent. One source's positive axis cannot fill
another source's gap.

| Unit | Technical observation | Required missing axes | Disposition |
|---|---|---|---|
| VSDC / `STOCK_DIVIDEND` | An **unqualified notice observation** exposes issuer/ticker/ISIN/venue, record-date labels, reason/title, and a rights ratio section. Search/detail/announcement routes are reachable without login in the bounded probe. | No route-to-row identity, owner-backed event-kind token, response-backed ex/effective date, ratio orientation/fraction rule, stable revision/cancellation identity, complete page/coverage contract, or automation/redistribution grant. | `SOURCE_GAP` |
| VSDC / `BONUS_SHARE` | An **unqualified notice observation** exposes capital-from-equity/bonus-like reason text and identity fields; older official notices use bonus-share wording. | Free text is not an allow-listed kind token or route-to-row identity; same date, unit, revision, coverage, and rights gaps remain. | `SOURCE_GAP` |
| VNDIRECT finfo / `STOCK_DIVIDEND` | Official `/v4/events` returned 200 JSON with page totals and row fields including `id`, `code`, `type`, `effectiveDate`, `ratio`, and `numberOfShares`; `STOCKDIV` was observed as an **unqualified** token. | No legal-issuer binding, same-owner semantic/type contract, ex-date meaning, ratio orientation, complete 2018–2026 history, revision rule, or data-row automation/redistribution grant. | `SOURCE_GAP` |
| VNDIRECT finfo / `BONUS_SHARE` | Same route family returned 200 JSON; `KINDDIV` was observed as an **unqualified** separate provider filter/row kind. | No legal-issuer binding or same-owner proof that the token means the exact normalized bonus kind, plus the same date/unit/coverage/revision/legal gaps. | `SOURCE_GAP` |
| HOSE issuer disclosure | Official route returned an HTML application shell in the bounded strict probe. | No accepted structured response envelope, event identity/type/date/unit/page/coverage contract, or reuse grant. | `NOT_SERVED` / `TRANSPORT_INCONCLUSIVE` |
| HNX listed and UPCoM disclosure | Strict certificate-chain verification failed for both official route probes; no insecure retry. | No response-backed identity, schema, date/unit, coverage, rate, or reuse evidence. | `NOT_SERVED` / `TRANSPORT_INCONCLUSIVE` |

### 2.1 Total status axes

Every future source attempt must report exactly one technical disposition from this allow-list, with
no provider exception text:

```text
QUALIFIED
PARTIAL
NOT_SERVED
IDENTITY_GAP
EVENT_TYPE_GAP
EFFECTIVE_DATE_GAP
RATIO_UNIT_GAP
COVERAGE_GAP
PAGINATION_GAP
REVISION_GAP
LEGAL_GAP
RATE_POLICY_GAP
TRANSPORT_INCONCLUSIVE
SCHEMA_DRIFT
RESPONSE_TOO_LARGE
BUDGET_EXHAUSTED
```

`SOURCE_GAP` is the issue-level disposition when no candidate unit is `QUALIFIED`; it is not a
provider row or a confirmed-empty event result. A `PARTIAL` candidate never becomes `QUALIFIED` by
combining another owner.

## 3. Deferred implementation contract — non-authoritative

This source-gap packet deliberately freezes no public function signature, module, export, enum,
dataclass, exception, field name, source token, selector grammar, serialization shape, or numeric
scheduler ceiling. It creates no symbol and is not an implementation recipe. A later qualified-source
packet must define those decisions against the provider's real response and legal contract, then pass a
fresh exact-SHA design review before RED or code.

The following invariants are retained and are not public API claims:

- The current cash-dividend surface remains unchanged and the new stock/bonus registry remains empty
  and disabled.
- One request uses one qualified provider/route unit only. There is no implicit multi-source
  failover, per-event merge, cross-source stitch, basket, archive, or cash-to-stock synthesis.
- No event row is returned without provider-backed kind, symbol/issuer identity, ex/effective date,
  ratio unit, and stable event/revision evidence. No record, publish, pay, listing, retrieval, or
  calculated trading date may substitute for ex/effective date.
- A later design must choose exact public fields, optionality, identity visibility, ordering,
  deduplication, revision/cancellation precedence, serialization/DataFrame behavior, and constructor
  compatibility from a qualified source rather than freezing them here.

## 4. Future event, identity, date, and unit gate

A candidate can reopen only when `STOCK_DIVIDEND` and `BONUS_SHARE` pass independently for the same
owner and route set. The future design must response-bind the requested symbol, provider symbol, legal
issuer, venue, ISIN or owner-equivalent, stable owner event ID, exact kind token, and announcement or
event identity. It must decide which identity fields are public and which are validation-only; neither
an issuer/title search result nor a URL/local ordinal is sufficient.

It must also define and validate all provider temporal semantics: response-backed ex/effective date,
record date, provider publish/update/revision time, retrieval time, and timezone awareness. Date-only
provider fields remain date-only, and no UTC midnight/session/exchange inference is admitted.

The normalized ratio is new shares per 100 existing shares. The provider contract must bind orientation,
finite decimal validation/serialization, fractional entitlement, rounding, cancellation, and the
meaning of any total-new-share field. Total-new-share values never infer or silently alter the ratio.
Selector grammar, canonicalization, date bounds, unknown-symbol preflight, and behavior outside the
vetted `2018-08-13..2026-08-19` interval are future design decisions and must be tested before code.

## 5. Future coverage and no-false-absence gate

Coverage is proved separately for each kind; one undifferentiated history result cannot prove both.
The next design must define one mutually exclusive result/error disposition for every response:

- `FULL` only for a reconciled exact requested window;
- `PARTIAL` only for a provider-declared bounded interval whose pages reconcile;
- `UNKNOWN` when rows or emptiness are observed but completeness/absence is unproved;
- `EMPTY_CONFIRMED` only for a complete provider-backed empty proof; and
- `NOT_SERVED` when transport, authentication, legal, or schema gates prevent an admissible result.

The future design must explicitly choose whether each status is a returned result or a typed source
error; no condition may be both. Fatal transport/schema/identity/pagination/revision/budget failure
returns no history and never masquerades as an empty result. Page/cursor totals, first/last boundaries,
empty semantics, duplicate/locale/revision reconciliation, and cancellation precedence must be bound
before any partial or full result is allowed.

## 6. Future atomic budget and diagnostic gate

The runtime design is one-source and sequential, not a four-source scheduler. A qualified provider's
real route, pagination, rate, and retry contract must determine finite logical/physical/page/retry/
response-byte ceilings in a later design review; no numeric scheduler ceiling is frozen here.

The future request-scoped ledger must reserve every route/page/retry dispatch atomically: validate all
caps before committing keys, counters, page charges, or physical ordinals; a rejected reservation sends
no request and has no side effect. Retry generations are contiguous, dispatch order is deterministic,
responses are byte-accounted while streamed, and fatal or exhausted calls discard uncommitted rows.
Prior sanitized attempts and counters survive budget exhaustion; no fabricated empty or truncated
attempt may be emitted, and no partial output is allowed after a fatal boundary.

The future public diagnostic grammar must be finite, allow-listed, bounded in tuple length and text,
deterministically ordered, and fully sanitized. It must cover every technical/legal/rate/transport/
coverage outcome without provider text, URLs, cookies, tokens, arbitrary MIME parameters, or source
names. Warning overflow, response overflow, and budget exhaustion must have one exact typed behavior;
these are reopen requirements, not current public exceptions or warning tokens.

## 7. Candidate-specific future route contracts

These are reopen requirements, not enabled routes.

### 7.1 VSDC route family

A future VSDC unit would need an owner-confirmed exact route set for security identity, rights/history
pages, and announcement detail. The observed search/detail/first-party AJAX shapes are not enough.
The route contract must bind:

- method, canonical host/path, request parameters/body, session/token/cookie lifecycle, redirects,
  TLS, full normalized MIME, and route-specific HTML headings;
- security identity response containing ticker, issuer, ISIN/equivalent, and venue;
- rights/history row containing a stable provider event ID and an explicit stock/bonus token;
- announcement detail bound to the selected row and carrying a response-backed ex/effective date;
- page/cursor totals, inclusive date semantics, complete-history/empty semantics, and revision rule;
- owner permission for automated fetching, derived rows, cache/retention, rate, attribution, and
  caller-facing redistribution.

A `GET /vi/ad/{id}` page with only a record date cannot qualify `ex_date`. A general VSDC article
explaining ex-rights timing cannot be used to calculate it. Numeric announcement adjacency and a
search miss cannot establish coverage or absence.

### 7.2 VNDIRECT finfo route

The observed official `/v4/events` JSON shape is a candidate only. A future gate must bind:

- exact `code`, `id`, `type`, `group`, locale, date, ratio, and total/page field semantics;
- same-owner meanings of `STOCKDIV` and `KINDDIV`, including whether `typeDesc` is authoritative;
- `effectiveDate` as ex/effective date for each exact kind, rather than expected execution, listing,
  or another provider date;
- `expiredDate`, `disclosureDate`, `actualDate`, `numberOfShares`, and `ratio` separately;
- locale duplication, stable event/revision identity, update/cancellation precedence, and full
  requested-window coverage;
- exact page-index and page-size limits, retry/rate policy, response byte cap, and legal/reuse
  permission for runtime and derived output.

The JSON envelope's totals are not enough to claim `FULL`, and the presence of a row is not enough to
claim an admissible ex-date or kind.

### 7.3 HOSE/HNX

No implementation path is proposed. A later exchange candidate would need a published or owner-
confirmed machine route, strict TLS/MIME/redirect contract, response-backed symbol/issuer/event
identity, date/unit/revision semantics, full pagination/coverage, and written runtime/redistribution
permission. HTML application shells and certificate failures remain `NOT_SERVED`, not empty history.

## 8. Conjunctive reopen and release gate

A future exact-SHA design review may reopen implementation only if **all** conditions pass separately
for `STOCK_DIVIDEND` and `BONUS_SHARE`:

1. one owner/route unit has written permission for runtime fetching, caching, derived rows,
   attribution, redistribution, rate/concurrency, retry, and retention;
2. exact route, method, parameter/body, redirect, strict TLS, full normalized MIME, response envelope,
   and session/token contract is fixed;
3. response-backed symbol/issuer/venue identity and stable event/revision identity pass positive and
   malicious/wrong-issuer/duplicate/cancellation cases;
4. exact provider kind tokens map independently to stock dividend and bonus share;
5. ex/effective date meaning is response-backed and tested; record/publish/pay dates remain distinct;
6. exact shares-per-100 orientation, finite bounds, decimal precision, fractional entitlement, and
   rounding behavior pass synthetic fixtures;
7. requested `2018-08-13..2026-08-19` coverage, page/cursor totals, served boundaries, duplicate and
   revision rules, and confirmed-empty semantics pass without false absence;
8. the source-approved finite logical/physical/page/retry/byte budget, atomic reservations,
   deterministic exhaustion, preserved sanitized attempts, and bounded diagnostics pass;
9. a source result uses one provider only; no cross-source stitch, basket, archive, signal, or
   cash-to-stock synthesis is introduced; and
10. RED tests, implementation, docs/snapshots/changelog, merged-tree full/focused gates, blacklist,
    no-secrets, API/import compatibility, and isolated build gates pass in a later authorized round.

Until all ten conditions pass, the new share-distribution chain stays empty and the current cash-only
VSDC behavior stays unchanged.

## 9. Future RED/release matrix — not authorized in this commit

After a fresh design PASS only, synthetic offline fixtures must cover:

| Area | Required positives | Required fail-closed cases |
|---|---|---|
| Selector/bounds | canonical padded/lowercase symbol normalization; inclusive start/end | malformed/unknown symbol, inverted bounds, empty selector; zero network |
| Kind | one exact stock-dividend row; one exact bonus-share row | cash, rights, listing, mixed/unknown token; no free-text inference |
| Date | explicit response-backed ex/effective and optional record date | record-only, announcement-only, pay-only, inferred prior-trading-day, ambiguous timezone |
| Ratio | exact synthetic `held:new` and direct shares-per-100 values | percent-of-par, cash amount, zero/negative/non-finite, reversed/ambiguous orientation |
| Identity/revision | stable event ID, revision update, cancellation under owner rule | wrong issuer, wrong symbol, duplicate locale, same-ID conflict, missing ID |
| Coverage | reconciled full, provider-declared partial, typed unknown | page gap, changing total, empty page without full proof, false absence |
| Budget | source-approved finite logical/physical/page/retry/byte boundaries; prior attempts preserved | duplicate reservation, retry overrun, phantom ordinal, empty attempts on exhaustion |
| Compatibility | cash VSDC, diagnostics, snapshots, DataFrame/docs/imports unchanged | cash kind widened, ex-date fabricated, source chain silently populated |

No RED test, provider fixture, production code, public export, skill, changelog, or runtime registry
is part of #215's source-gap design commit.

## 10. Delivery boundary

The #215 source/design handoff consists of these two packet artifacts plus the required lifecycle
record in `tasks/active-backlog.md`:

- `docs/research/2026-08-23-vn-stock-bonus-distributions-source-vetting.md`
- `tasks/215-design-note.md`
- `tasks/active-backlog.md`

The approved exact range must enumerate all three paths; the backlog record is not local-only and must
not be described as excluded from a proposed push. A docs-only source-gap PASS may publish the approved
range, verify remote ancestry/paths, post the clean no-capability resolution, and close/re-read #215;
it never authorizes models, accessors, RED, or runtime capability. Reviewer: please spawn parallel
source/legal, identity/date/unit, and budget/coverage sub-agents for exact-SHA review.
