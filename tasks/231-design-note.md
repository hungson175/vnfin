# Issue #231 design note — SSI/TCX annual cash flow and net income

**Status:** `SOURCE_GAP_CLOSURE` / design review requested; no implementation authorization
**Date:** 24 August 2026 (UTC+7)
**Packet:** `/home/hungson175/tools/vnfin-oss-reviewer/tasks/231-ssi-tcx-annual-cashflow-net-income-spec.md`
**Packet commit:** `5d499a050dfc7c57302d0abe8ab19953954551ad`
**Published base:** `dbeea0e897e2c6688dd0b01b1cafbf4f04cd358c`
**Research:** [`docs/research/2026-08-24-ssi-tcx-annual-operating-cash-flow-net-income-source-vetting.md`](../docs/research/2026-08-24-ssi-tcx-annual-operating-cash-flow-net-income-source-vetting.md)

## 1. Decision

This packet is a docs/source design handoff only. No provider probe, RED test, API/model change,
production code, push, or issue close is authorized before exact design PASS.

No candidate satisfies the complete source gate for either `SSI` or `TCX`, or for either target
metric. The four cells are therefore:

| Symbol | Annual `operating_cash_flow` | Annual `net_income` |
|---|---|---|
| `SSI` | `BLOCKED` / `SOURCE_GAP` | `BLOCKED` / `SOURCE_GAP` |
| `TCX` | `BLOCKED` / `SOURCE_GAP` | `BLOCKED` / `SOURCE_GAP` |

The new qualified source chain remains empty. This is not a claim that statements or history are
absent. It is a fail-closed disposition for unproven provider identity, template/item semantics,
VND scale, coverage/revision, no-login legal posture, and redistribution rights.

## 2. Non-negotiable boundaries

* Preserve exactly the existing 26 `MetricId`s, catalog order, signatures, exports, report models,
  diagnostics, cache keys, source-selection behavior, annual cadence, and DataFrame/public snapshot
  contracts.
* Preserve #204's independent negative `modelType=89`, `90`, and `91` evidence and blocked
  SSI/TCX `NET_INCOME` boundary. Do not reuse a bank/corporate template, force `is_bank=True`,
  map by human label or neighboring code, or place CafeF string codes in a VNDirect namespace.
* Keep `operating_cash_flow` distinct from cash balance, investing/financing/net cash flow,
  EBITDA, and any derived proxy. Keep total consolidated net income distinct from parent-
  attributable income, ordinary-shareholder appropriation, and profit before tax.
* Keep foreign-flow replay, the 20-pair rule, cohorts, cash-accrual score, VN30 membership,
  thresholds, portfolios, and report generation out of this library source contract.
* Keep #232 queued after #231. No #232 probe, RED, API/model work, code, push, or close starts in
  this design round.

## 3. Clean-room and source boundary

The mandatory repository blacklist was applied. Every search used:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No blacklisted or derived source, code, schema, endpoint map, example, test, package, comparison,
or `finkit` material was opened, cited, copied, or used. The research note uses only official
issuer/provider/terms pages plus the previously approved #204 bounded observations. Raw responses,
live rows, credentials, cookies, headers, and secret-bearing URLs are not committed.

The candidate acquisition units are only the official routes previously observed without credentials; current/formal no-login, session, and automation posture remains unproven:

1. VNDirect `api-finfo.vndirect.com.vn/v4/financial_statements`, evaluated independently for
   income candidates `modelType=2` and `modelType=102` independently, and cashflow candidates `modelType=3` and `modelType=103` independently.
2. CafeF `cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx`, evaluated independently for
   income `Type=1` and cashflow `Type=3`.
3. Official SSI and TCBS/TCX filings are cross-check evidence, never a provider adapter or a
   redistribution license.

The #231 round made zero provider dispatches. All prior counts and outcomes are labelled as
22 August 2026 inherited evidence in the research note; no new current behavior is asserted.

## 4. Source-unit and coverage contract

Every candidate is keyed by this complete tuple, with no flattening across symbols, statements,
or providers:

```text
(symbol, source owner, canonical host/path, route/version, operation,
 statement, cadence, requested window, provider template/model)
```

The research artifact contains 12 independent request units (`SSI`/`TCX` × VNDirect
`modelType=2|102|3|103` and CafeF direct `Type=1|3`), two separate zero-dispatch CafeF capability
checks, six independently retained negative `89/90/91` rows with exact #204 page accounting, a
14-row static-evidence ledger with independent transport/legal axes, exact non-secret request shapes,
inherited logical/physical ledgers, and zero #231 dispatches. A response that is empty, timed out, WAF-limited, redirected, or missing
search evidence is not an issuer-history absence proof.

### 4.1 Positive identity contract for any future reopen

For each symbol and statement separately, a qualified response must prove:

```text
requested symbol + source namespace + exact statement + annual cadence
+ securities-company template/model + provider item code + fiscal date
+ entity/consolidation scope + explicit unit/scale + revision identity
```

URL parameters alone do not establish response identity. Mixed, absent, redirected, cross-symbol,
cross-statement, cross-cadence, or unverified model identity fails closed.

### 4.2 Metric meanings and source item rules

* `operating_cash_flow` is the provider-backed line for net cash generated from operating
  activities. A balance, investing, financing, net-cash, EBITDA, or derived value is invalid.
* `net_income` is total consolidated net income under the verified template. Parent-attributable
  income, ordinary-shareholder appropriation, and profit before tax are separate lines.
* The current catalog codes `32000`, corporate `23003`, and bank `23000` remain unchanged. They
  are not proof that either securities-company symbol can use those namespaces.
* Every positive mapping must have one exact provider item code in the provider's own namespace;
  a human label, an issuer filing line alone, or a neighboring numeric code is insufficient.
* The official SSI and TCBS filings cross-check securities-company statement semantics, annual
  fiscal date, and VND. SSI's `B03b-CTCK/HN` code `60` and TCX's `B03-CTCK` code `60` are issuer
  operating-cash-flow line anchors, not provider item codes. They do not prove provider item
  identity or provider reuse rights; both exact 2025 code-60 amounts are `NOT_RETAINED`.

### 4.3 Date, unit, and coverage outcomes

* Keep provider fiscal dates exactly. Publication, retrieval, effective, quarter, YTD, TTM, and
  restatement dates cannot be relabelled as annual fiscal dates.
* Emit finite raw VND only after explicit source scale or a repeatable exact filing cross-check.
  No guessed multiplier, conversion, rounding, or apparent-value match is allowed.
* `FULL` means all requested annual periods within provider-declared inclusive bounds are present
  and reconciled. `QUALIFIED_PARTIAL` requires provider-declared bounds plus reconciled pages;
  arbitrary truncation, timeout, or empty response cannot qualify.
* `COVERAGE_UNPROVEN`, `DATE_GAP`, `IDENTITY_GAP`, `UNIT_GAP`, `LEGAL_GAP`, `RATE_POLICY_GAP`,
  and transport/source-error are bounded design dispositions, not new public enums. They must not
  be flattened into `MISSING`, silent zero, or fabricated history.

## 5. API/model compatibility freeze

Before any RED authorization, the future implementation design must bind the behavior of:

* `fundamentals.metrics(symbol, period="annual", ...)` and
  `explain_metric_coverage(...)`;
* all 26 metric IDs and catalog order, including the unchanged `operating_cash_flow` and
  `net_income` definitions;
* `MetricReport`, `MetricValue`, `MetricInput`, `StatementProvenance`, `MetricCoverage`,
  equality/repr, DataFrame columns/attrs, serialization, warnings, and sanitized errors;
* per-statement source selection/failover, direct-source precedence, cache keys, and empty/fail
  behavior; and
* no ratio calls or extra statement calls for this request.

The preferred outcome is **no public model change**. Do not add provider-specific enums,
snapshot helpers, pair counts, replay result shapes, or an aggregate `report.source` that erases
per-statement lineage. If a future qualified source needs an additive field, it requires a fresh
exact contract freeze and review; this source-gap handoff authorizes none.

Current public behavior remains the #204 boundary: no qualified SSI/TCX source means the new
chain stays empty, diagnostics remain fail-loud/recoverable according to the existing typed
contract, and no synthetic value is returned as a success.

## 6. Legal, runtime, and budget contract

Public/no-login reachability in the inherited observation is not permission. The source owner must
provide a written or clearly applicable license covering all of:

```text
runtime automation + caller return + caching/retention + attribution
+ derivative/commercial use + redistribution/resale + amendment + revocation
```

SSI's official disclaimer restricts publication/reproduction/distribution without written consent;
TCBS's official Terms of Use prohibit reproduction/distribution/republication/modification absent
prior written consent and describe personal, non-commercial use. VNDirect and CafeF public terms or
robots do not supply an OSS redistribution grant. No candidate clears this gate.

No provider publishes a numeric quota in the retained evidence. A future qualified route must
reserve a finite budget before dispatch, without inventing a provider SLA. The summary and detailed
matrices use the same dimensions:

1. reserve logical source units and physical pages atomically;
2. charge redirects and retries to that same reservation;
3. charge compressed and decompressed bytes separately;
4. reserve request-rate-window tokens;
5. reserve a concurrency slot;
6. record deterministic backoff/wait charges for every retry or scheduled wait;
7. stop before a dispatch that would exceed any reservation; and
8. discard incomplete results atomically on logical, page, retry, redirect, byte, rate, concurrency,
   or wait exhaustion, with bounded public diagnostics.

No retry count, page ceiling, byte ceiling, concurrency ceiling, rate window, or backoff value is
a current runtime contract. Exact numeric values require a separate qualified-source design and RED
review; the reservation dimensions, deterministic charging, and atomic exhaustion contract are
already fixed here.

## 7. Conjunctive reopen gate

Reopen is per `(symbol, source, statement, metric)` and requires every gate below:

1. owner permission/license covers the complete runtime and reuse posture, including amendment
   and revocation;
2. stable official route/version, no-login or explicitly approved credentials, and bounded
   transport behavior;
3. response-backed symbol identity with no redirect/mixed-source payload;
4. statement-specific securities-company template/model, independently for income and cashflow;
   `89`, `90`, and `91` are each qualified separately or remain negative;
5. exact provider item code and semantics for total consolidated net income or operating cash
   flow, plus official filing cross-checks for both SSI and TCX;
6. exact annual fiscal dates, explicit VND unit/scale, revision/supersession identity, and no
   fabricated dates or missing years;
7. provider-declared coverage bounds with reconciled pages, `FULL`/`QUALIFIED_PARTIAL` semantics,
   and no false absence;
8. finite atomic logical/physical/page/retry/redirect/byte reservation, request-rate window,
   concurrency ceiling, and deterministic backoff/wait accounting; each charge occurs exactly once
   and any exhaustion fails atomically without dropping prior private/internal sanitized accounting;
9. no ratio/extra calls, validated-result-only cache, fail-before-cache/network caller validation,
   stable source/error sanitization, and direct/chain parity; and
10. exact API, docs, tests, build, blacklist, secret, diff, path, object, and merged-ancestry
    gates in a later review.

Failure of any one gate keeps the source gap closed. A candidate's apparent numeric agreement with
an issuer filing cannot compensate for a missing identity, template, unit, legal, or budget axis.

## 8. Deferred RED-first matrix and release contract

This matrix is a future authorization contract only. It contains no live values, no RED commit, and
no implementation authorization. All fixtures are synthetic and offline.

### 8.1 Positive identity rows

* Evaluate all 12 request units independently: `SSI|TCX` × VNDirect `modelType=2|102|3|103`
  and CafeF direct `Type=1|3`. Keep the two CafeF adapter capability checks as separate
  zero-dispatch evidence rows, and keep six inherited `89/90/91` rows independently negative.
* For every qualified statement, retain response-backed symbol, exact template/model, provider
  item code, annual fiscal date, finite raw VND, revision identity, complete `MetricInput`, and
  matching per-statement provenance. Income and cashflow sources may differ.
* `FULL` requires every requested period in provider-declared inclusive bounds; declared,
  reconciled bounds may yield `QUALIFIED_PARTIAL`. No missing year or empty page is fabricated.

### 8.2 Required API/RED scenario matrix

The attempt-history boundary is frozen: private/internal scheduler, budget, and synthetic-test state
may retain bounded sanitized attempts for accounting and assertions, but v0.2.0 public
`MetricReport`, `StatementProvenance`, reprs, DataFrame attrs, and raised messages expose no failed-
attempt trail. Recoverable failures remain the existing bounded aggregate `recoverable source error`;
any additive public attempt field requires a separate model review.

| Row | Required positive/negative behavior |
|---|---|
| `API-01 zero-qualified-source` | Both target statements stay typed unavailable/source-gap; coverage explanation is non-fatal and truthful; no cache write, false absence, or silent zero. |
| `API-02 explicit multi-source chain/failover` | Caller-provided source order is honored; incapable sources are not dispatched; per-statement provenance is preserved. Any sanitized attempt ledger is private/internal test and budget state only; the public v0.2.0 model remains trail-free. |
| `API-03 partial per-statement success` | Income success/cashflow failure and the inverse preserve the successful statement and isolated failure independently. |
| `API-04 all-sources-failed` | All failures yield a bounded sanitized public aggregate; private/internal state may retain bounded accounting, but no cache write, false absence, silent zero, or unbounded public exception/attempt trail is allowed. |
| `API-05 formula and statement isolation` | Freeze all 26 IDs, order, public shape, and guards. `net_margin = net_income / net_revenue` and `operating_cash_flow_margin = operating_cash_flow / net_revenue` follow existing formulas only when validated inputs and non-zero guards pass; the remaining 22 unrelated metrics retain their existing values/statuses/order/source behavior, and mapping cannot rewrite unrelated statement items. |
| `API-06 direct/chain source selection + cache` | Direct precedence, explicit-chain routing, cache-hit no-dispatch, and validated-result-only cache-write behavior are deterministic and snapshot-compatible. |
| `API-07 v0.2.0 compatibility` | Imports/version, signatures, constructors, 26-ID catalog/order, DataFrame columns/attrs, serialization, warning/status vocabulary, and public snapshots remain compatible with v0.2.0. |
| `API-08 income/cashflow failure isolation` | A failure in one statement cannot erase, rewrite, or downgrade the other statement's value, provenance, or public warning. Prior sanitized accounting is private/internal; public `MetricReport`, `StatementProvenance`, reprs, DataFrame attrs, and raised messages remain trail-free under v0.2.0. |
| `API-09 rate/concurrency/backoff atomicity` | Every request reserves rate-window tokens and a concurrency slot, records deterministic waits, and charges logical/physical/pages/retries/redirects/compressed/decompressed bytes exactly once; any exhaustion atomically fails before returning partial data. Budget accounting may retain private/internal attempts only. |

### 8.3 Identity, payload, and coverage negatives

Synthetic negatives include wrong/absent/contradictory symbol, redirect, mixed owner, wrong
statement/cadence/template/model, wrong source namespace/item code, each independent `89`/`90`/`91`
row, parent-attributable/profit-before-tax/cash-balance/other-cash-flow substitutes, missing or
mixed VND unit/scale, non-finite values, duplicate/conflicting dates, publication/YTD/TTM dates,
wrong revision, empty/malformed payload, missing middle year, unreconciled pages, and bounds that
are absent or contradictory. All fail closed without false absence or silent zero. Browser/static
visibility cannot substitute for retained response identity, MIME/final URL, current no-login
posture, provider unit, or reuse rights.

### 8.4 API, budget, diagnostics, and release gates

Caller malformed inputs fail before cache/network; malformed provider responses fail after dispatch
but before cache/return; cache writes occur only after complete validation. Reservations are finite,
deterministic, and atomic across logical units, physical pages, redirects, retries, compressed and
decompressed bytes, request-rate window, concurrency, and deterministic backoff/wait. No fallback
exceeds the reservation or erases prior private/internal sanitized accounting. Ratio calls remain zero and no extra
statement calls occur.

The existing 26 IDs/catalog order, signatures, exports, dataclass construction, DataFrame
columns/attrs, serialization, warning/status vocabulary, cache keys, and #204 SSI/TCX negative
snapshots remain unchanged. No secrets, cookies, raw headers, secret-bearing URLs, local paths,
provider exception prose, raw rows, or unbounded diagnostics may enter public outputs.

A later qualified-source implementation requires RED first, reviewer verification of RED, explicit
implementation authorization, GREEN merged tests, code review, focused/full offline tests,
imports/version, docs/API/units as applicable, `git diff --check`, blacklist/secret scans, isolated
wheel/sdist builds, and exact merged ancestry/path gates. A source-gap PASS authorizes only
research/design/backlog publication, clean remote verification, no-capability resolution, and
issue close/re-read; it never transitions to RED/TDD/API-model/provider registration.

## 9. Handoff

The research and design artifacts intentionally leave the SSI/TCX annual fundamentals chain empty.
The exact artifact SHA and lifecycle handoff are recorded in `tasks/active-backlog.md` after this
docs commit. Review only the research/design/backlog range from published base `dbeea0e`; preserve
the durable #232 queue entry in the corrected backlog, keep it closure-gated after #231, and exclude
only local receipt `a2ccd393f9f3283cc54eb33f4ec3e9d4804d243c` from the #231 publish ancestry. No probe,
RED, API-model change, production code, push, or close is allowed before exact design PASS.
