# #215 source/design note — stock dividends and bonus shares

**Issue:** #215  
**Packet:** `tasks/215-stock-bonus-distributions-source-spec.md` at reviewer anchor `4a6780b`  
**Date:** 23 August 2026 (Vietnam time, UTC+7)  
**Status:** `SOURCE-GAP CLOSURE` — docs/design only; no RED, model, accessor, source registration, or runtime capability  
**Current published base:** `origin/master` exact `8126dd5510b6390f91c9feeb43e047b2b9b88bc1`  
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
`2018-08-13..2026-08-19`. A docs-only source-gap PASS may authorize publication and resolution only;
it never authorizes TDD or implementation. A new implementation requires a fresh exact-SHA design
PASS after all reopen conditions in section 10 are evidenced.

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
| VSDC / `STOCK_DIVIDEND` | Official HTML notices expose issuer/ticker/ISIN/venue, record-date labels, reason/title, and a rights ratio section. Search/detail/announcement routes are reachable without login in the bounded probe. | No owner-backed event-kind token, response-backed ex/effective date, ratio orientation/fraction rule, stable revision/cancellation identity, complete page/coverage contract, or automation/redistribution grant. | `SOURCE_GAP` |
| VSDC / `BONUS_SHARE` | Official notices expose capital-from-equity/bonus-like reason text and identity fields; older official notices use bonus-share wording. | Free text is not an allow-listed kind token; same date, unit, revision, coverage, and rights gaps remain. | `SOURCE_GAP` |
| VNDIRECT finfo / `STOCK_DIVIDEND` | Official `/v4/events` returned 200 JSON with page totals and row fields including `id`, `code`, `type`, `effectiveDate`, `ratio`, and `numberOfShares`; `STOCKDIV` was observed. | No same-owner semantic/type contract, ex-date meaning, ratio orientation, complete 2018–2026 history, revision rule, or data-row automation/redistribution grant. | `SOURCE_GAP` |
| VNDIRECT finfo / `BONUS_SHARE` | Same route family returned 200 JSON; `KINDDIV` was observed as a separate provider filter/row kind. | No same-owner proof that the token means the exact normalized bonus kind, plus the same date/unit/coverage/revision/legal gaps. | `SOURCE_GAP` |
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
BUDGET_EXHAUSTED
```

`SOURCE_GAP` is the issue-level disposition when no candidate unit is `QUALIFIED`; it is not a
provider row or a confirmed-empty event result. A `PARTIAL` candidate never becomes `QUALIFIED` by
combining another owner.

## 3. Future public contract (non-authoritative until a source qualifies)

This section records the minimum shape a later implementation must review; it creates no symbols or
exports now. The current cash API remains unchanged.

```python
vnfin.corp_actions.share_distributions(
    symbol,
    *,
    start=None,
    end=None,
    sources=None,
    http_get=None,
    timeout=25.0,
    max_attempts=3,
) -> ShareDistributionHistory
```

The default new source chain is currently empty, so this call is not available. If a source later
qualifies, the implementation must choose one exact public behavior for source-gap, empty `sources`,
transport failure, schema failure, and budget exhaustion before RED. It must not silently fall back
from one provider to another or merge events across providers.

### 3.1 Exact future types

The intended public values are frozen and typed; exact module/export names remain subject to a fresh
implementation review:

```python
class ShareDistributionKind(Enum):
    STOCK_DIVIDEND = "stock_dividend"
    BONUS_SHARE = "bonus_share"

@dataclass(frozen=True)
class ShareDistributionEvent:
    symbol: str
    kind: ShareDistributionKind
    shares_per_100: Decimal
    ex_date: date                 # required, provider-backed, never inferred
    record_date: date | None       # optional, provider-backed, not ex_date
    event_id: str                  # stable owner-issued identifier
    revision: str | None           # owner revision/update token when available
    source: str                    # canonical source-role token
    provider_published_at: datetime | None
    fetched_at_utc: datetime
    warnings: tuple[str, ...]

@dataclass(frozen=True)
class ShareDistributionHistory:
    symbol: str
    events: tuple[ShareDistributionEvent, ...]
    source: str
    requested_start: date | None
    requested_end: date | None
    served_start: date | None
    served_end: date | None
    coverage: CoverageStatus
    fetched_at_utc: datetime
    attempts: tuple[SourceAttempt, ...]
    warnings: tuple[str, ...]
```

`Decimal`/an exact rational is required for `shares_per_100`; binary floating point is not an
acceptable canonical storage unit. `provider_published_at` is optional and must not be substituted
for an event date. Date-only provider fields remain dates; they are not assigned UTC midnight.

The future `SourceAttempt` is a sanitized typed value, not raw transport text:

```text
SourceAttempt.name: canonical source token, never arbitrary provider text
SourceAttempt.role: identity | history | page | detail | legal_probe
SourceAttempt.outcome: one allow-listed disposition
SourceAttempt.logical_count: non-negative integer
SourceAttempt.physical_count: non-negative integer
SourceAttempt.page_count: non-negative integer
SourceAttempt.retry_count: non-negative integer
SourceAttempt.http_status: optional bounded integer
SourceAttempt.mime: optional normalized allow-listed MIME token
SourceAttempt.warnings: tuple of finite warning tokens
```

No URL, query, cookie, token, response body, exception text, arbitrary source name, or unbounded
provider string may enter a public attempt or warning.

### 3.2 Coverage status

```text
FULL       = exact requested window reconciled and complete
PARTIAL    = provider-declared bounded interval, not the exact requested window
UNKNOWN    = response/rows observed but completeness or absence is unproved
NOT_SERVED = no admissible source result
```

`FULL` requires response-backed ex/effective dates, exact kind/unit, symbol identity, all-page
reconciliation, duplicate/revision handling, and a provider completeness statement or equivalent
proof for `2018-08-13..2026-08-19`. `PARTIAL` must expose `served_start`/`served_end` and never claim
full history. `UNKNOWN` may expose no confirmed absence. A source error or budget exhaustion is not
an empty `ShareDistributionHistory`.

## 4. Kind and unit normalization

### 4.1 Kind is response/schema-backed only

The two values are independent:

| Normalized kind | Accepted only when the same owner proves | Rejected inputs |
|---|---|---|
| `STOCK_DIVIDEND` | An exact provider token/schema means dividend paid in newly issued shares. | `DIVIDEND`, cash words, generic `LISTED`, a title-only match, or a free-text inference. |
| `BONUS_SHARE` | An exact provider token/schema means a free/capital-from-equity bonus issue. | Rights purchase, ESOP/listing without a declared kind, generic capital increase, or a title-only match. |

The observed VNDIRECT `STOCKDIV` and `KINDDIV` tokens remain unqualified until the provider's
same-owner documentation binds them to these definitions. VSDC notice headings and Vietnamese free
text remain evidence to investigate, not an executable allow-list. Mixed-purpose notices are rejected
unless the owner supplies distinct typed event records or an exact split rule.

### 4.2 `shares_per_100`

The normalized unit is new shares per 100 existing shares. A future parser may accept a provider
field already labelled in that unit or an explicitly labelled `held:new` ratio. The orientation must
be response/schema-backed; never guess from a colon or percent sign.

For an explicitly labelled `held:new` ratio, the exact formula is:

```text
shares_per_100 = (new_shares / held_shares) * 100
```

Synthetic examples only: `20:1` becomes `5`; `100:6.25` becomes `6.25`. Both are illustrative,
not provider rows. The parser must reject zero/negative/non-finite values, percent-of-par values,
cash amounts, missing orientation, and ratios whose rounding/fraction rule is not documented.
Provider-provided rounding, fractional entitlement, cancellation, and total-new-share fields are
stored separately from the normalized ratio; they never alter the ratio silently.

## 5. Date, identity, and revision contract

### 5.1 Ex/effective date

`ex_date` is required for every returned event. It may come from a field named `exDate` or
`effectiveDate` only after the provider's own documentation proves that field means the ex/right-
trading date for the exact event kind. A field named `effectiveDate` is not self-authenticating.

The following are never substitutes:

- VSDC `Ngày đăng ký cuối cùng` (record date);
- a VSDC explanatory rule that describes the relation between dates;
- disclosure/announcement date;
- pay/actual date;
- listing/trading-start date;
- retrieval time; or
- a calculated previous trading day.

Filtering is inclusive on the response-backed `ex_date` only. Missing, ambiguous, inferred,
timezone-unclear, or semantically conflicting dates produce `EFFECTIVE_DATE_GAP` and no event row.
A record date may be returned as `record_date` only when its provider meaning is separately proven.

### 5.2 Response-backed identity

Before accepting a row, the same response family must bind:

1. canonical requested symbol and provider symbol;
2. legal issuer name and venue;
3. ISIN or owner-equivalent stable security identity;
4. exact owner event ID and, if applicable, revision/cancellation ID;
5. exact provider kind token; and
6. canonical source role.

Search result text, URL numeric IDs, title hashes, query tickers, local sequence numbers, and
cross-provider matching are not identity. Wrong-issuer, renamed-symbol, duplicate-locale,
missing-ID, conflicting-code, and ambiguous response cases fail closed.

### 5.3 Revision/cancellation

A provider must state how amendment, cancellation, supersession, and duplicate locale rows are
represented. Rows with the same `event_id` and identical revision/payload may be deduplicated. Two
different revisions require the provider's precedence rule; otherwise the result is
`REVISION_GAP`/`PARTIAL`, never arbitrary keep-first or keep-last. A cancelled event is not silently
dropped; it must be represented by the provider-backed revision policy or make the window
unqualified.

## 6. Coverage, pagination, and empty-result contract

A future implementation must prove the requested inclusive window independently for each kind and
source. It must not use a current total as a historical coverage claim.

| Predicate | `FULL` requirement | Failure result |
|---|---|---|
| Identity | Every page/row echoes the requested issuer/symbol and stable event identity. | `IDENTITY_GAP`; no confirmed empty. |
| Kind | Every accepted row maps to exactly one allowed kind; rejected kinds are counted by typed outcome. | `EVENT_TYPE_GAP`; no silent remap. |
| Date | Every accepted row has response-backed ex/effective date. | `EFFECTIVE_DATE_GAP`; no inferred date. |
| Unit | Every accepted row has exact positive finite shares-per-100 semantics. | `RATIO_UNIT_GAP`; no cash/percent fallback. |
| Pages | Provider first/last page, cursor, total, and page-size semantics reconcile; no page is skipped. | `PAGINATION_GAP` or `PARTIAL`; no false empty. |
| Boundaries | Served min/max ex dates and requested bounds are known and inclusive. | `COVERAGE_GAP`/`UNKNOWN`; no `FULL`. |
| Revision | Duplicates, amendments, and cancellations reconcile under owner rule. | `REVISION_GAP`; no silent omission. |

The future response must reject page zero, negative pages, changing totals, missing page metadata,
generic maintenance HTML, redirects, missing/wrong MIME, login pages, and a successful-but-wrong
route. A provider-declared empty result is `EMPTY_CONFIRMED` only if all `FULL` predicates pass for
the exact symbol/kind/window and the provider defines empty semantics. Otherwise it is `UNKNOWN` or
`NOT_SERVED`, never proof of no event.

## 7. Atomic global budget and deterministic scheduler

These are future design ceilings, not claims about provider policy. They are deliberately finite and
must be approved again before implementation:

```text
MAX_SOURCE_UNITS_PER_CALL = 4       # independent candidates; final result uses one source only
MAX_LOGICAL_DISPATCHES   = 32       # route/page reservations, retries excluded
MAX_PHYSICAL_DISPATCHES  = 48       # actual network sends, all sources combined
MAX_PAGES_PER_SOURCE     = 24       # page/cursor reservations for one candidate
MAX_RETRIES_PER_PAGE     = 2        # initial send + at most two retries = 3 physical sends
MAX_RESPONSE_BYTES       = 4_000_000
MAX_ATTEMPT_WARNING_CHARS = 1_024
MAX_RESULT_WARNING_CHARS  = 4_096
```

The request-scoped budget is global across all candidates and routes. A source candidate may be
retried only within the same source unit; a later source is never appended to rows from an earlier
source. The default scheduler is sequential and deterministic:

1. preserve explicit source order;
2. for one source, reserve identity before history, then pages in ascending provider page/cursor
   order; and
3. for one page, attempt retry generations `0`, `1`, `2` in order, only when the failure is retryable
   under a later owner-approved policy.

Each logical route/page has one key `(source_name, route_role, scope_id, page_key)`. A retry does not
consume another logical reservation. Each physical dispatch has one key
`(logical_key, retry_generation)` and receives the next contiguous `dispatch_ordinal` only after the
atomic reservation succeeds. A reservation that would exceed any global, page, byte, or retry cap
performs **no network send and receives no physical ordinal**.

The reservation operation is atomic and deterministic:

```text
reserve(logical_key, retry_generation):
  reject duplicate logical reservation unless retry_generation > 0
  reject retry_generation > MAX_RETRIES_PER_PAGE
  reject if logical_used + new_logical > 32
  reject if physical_used + 1 > 48
  reject if page_used(source) + new_page > 24
  otherwise increment counters and assign next physical ordinal
```

At exhaustion, the scheduler stops before the next send. It preserves all prior sanitized attempts and
returns a typed `BUDGET_EXHAUSTED` outcome; it never fabricates an empty `SourceAttempt`, a
`diagnostics_truncated` attempt, or a successful empty event list. A fatal transport/schema/identity
failure discards the uncommitted event accumulator. Only a later provider-declared, reconciled
`PARTIAL` result may return rows, and it must expose the served bounds and `PARTIAL` coverage; budget
exhaustion itself is never a partial-success signal.

## 8. Diagnostics and public failure grammar

Diagnostics are finite and machine-readable. Public text contains only these warning tokens and
bounded counters:

```text
SHARE_DISTRIBUTION_SOURCE_GAP
SHARE_DISTRIBUTION_NOT_SERVED
SHARE_DISTRIBUTION_COVERAGE_UNKNOWN
SHARE_DISTRIBUTION_COVERAGE_PARTIAL
SHARE_DISTRIBUTION_IDENTITY_MISMATCH
SHARE_DISTRIBUTION_EVENT_TYPE_UNMAPPED
SHARE_DISTRIBUTION_EFFECTIVE_DATE_UNPROVEN
SHARE_DISTRIBUTION_RATIO_UNIT_UNPROVEN
SHARE_DISTRIBUTION_REVISION_CONFLICT
SHARE_DISTRIBUTION_PAGINATION_UNRECONCILED
SHARE_DISTRIBUTION_BUDGET_EXHAUSTED
SHARE_DISTRIBUTION_TRANSPORT_INCONCLUSIVE
SHARE_DISTRIBUTION_LEGAL_UNVERIFIED
```

A future typed exception/outcome must use one exact mapping:

| Condition | Public behavior | Rows |
|---|---|---|
| source chain still empty | `ShareDistributionSourceGap` with token `SHARE_DISTRIBUTION_SOURCE_GAP` | none |
| valid response, complete empty proof | return history with `coverage=FULL`, no warning | empty, confirmed only by provider proof |
| valid rows but provider-declared bounded interval | return history with `coverage=PARTIAL` and served bounds | rows only under provider partial contract |
| valid response but absence/fullness unproved | return history with `coverage=UNKNOWN` and token `...COVERAGE_UNKNOWN` | none unless a future design explicitly permits non-fatal unknown rows |
| transport/schema/identity/revision failure | `ShareDistributionSourceError` with one typed outcome and sanitized attempts | none |
| global/page/retry/byte budget exhausted | `BudgetGlobalExhausted` with prior sanitized attempts and counters | none |

No provider error message, raw URL, query, cookie, token, HTML, arbitrary MIME parameter, or source
name can be interpolated into public diagnostics. Attempts already recorded remain present when the
budget exception is raised; the exception must not replace them with an empty tuple.

## 9. Candidate-specific future route contracts

These are reopen requirements, not enabled routes.

### 9.1 VSDC route family

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

### 9.2 VNDIRECT finfo route

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

### 9.3 HOSE/HNX

No implementation path is proposed. A later exchange candidate would need a published or owner-
confirmed machine route, strict TLS/MIME/redirect contract, response-backed symbol/issuer/event
identity, date/unit/revision semantics, full pagination/coverage, and written runtime/redistribution
permission. HTML application shells and certificate failures remain `NOT_SERVED`, not empty history.

## 10. Conjunctive reopen and release gate

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
8. the atomic 32-logical/48-physical/24-page/2-retry scheduler and sanitized diagnostics pass;
9. a source result uses one provider only; no cross-source stitch, basket, archive, signal, or
   cash-to-stock synthesis is introduced; and
10. RED tests, implementation, docs/snapshots/changelog, merged-tree full/focused gates, blacklist,
    no-secrets, API/import compatibility, and isolated build gates pass in a later authorized round.

Until all ten conditions pass, the new chain stays empty and the current cash-only VSDC behavior stays
unchanged.

## 11. Future RED/release matrix — not authorized in this commit

After a fresh design PASS only, synthetic offline fixtures must cover:

| Area | Required positives | Required fail-closed cases |
|---|---|---|
| Selector/bounds | canonical padded/lowercase symbol normalization; inclusive start/end | malformed/unknown symbol, inverted bounds, empty selector; zero network |
| Kind | one exact stock-dividend row; one exact bonus-share row | cash, rights, listing, mixed/unknown token; no free-text inference |
| Date | explicit response-backed ex/effective and optional record date | record-only, announcement-only, pay-only, inferred prior-trading-day, ambiguous timezone |
| Ratio | exact synthetic `held:new` and direct shares-per-100 values | percent-of-par, cash amount, zero/negative/non-finite, reversed/ambiguous orientation |
| Identity/revision | stable event ID, revision update, cancellation under owner rule | wrong issuer, wrong symbol, duplicate locale, same-ID conflict, missing ID |
| Coverage | reconciled full, provider-declared partial, typed unknown | page gap, changing total, empty page without full proof, false absence |
| Budget | exact boundary at 32 logical / 48 physical / 24 pages; prior attempts preserved | duplicate reservation, retry overrun, phantom ordinal, empty attempts on exhaustion |
| Compatibility | cash VSDC, diagnostics, snapshots, DataFrame/docs/imports unchanged | cash kind widened, ex-date fabricated, source chain silently populated |

No RED test, provider fixture, production code, public export, skill, changelog, or runtime registry
is part of #215's source-gap design commit.

## 12. Delivery boundary

Only these two packet artifacts belong in the #215 design handoff:

- `docs/research/2026-08-23-vn-stock-bonus-distributions-source-vetting.md`
- `tasks/215-design-note.md`

The separate local backlog activation receipt is intentionally local-only and is not part of any
approved push. Reviewer: please spawn parallel source/legal, identity/date/unit, and budget/coverage
sub-agents for exact-SHA review. No code, RED, push, or close is authorized before design PASS.
