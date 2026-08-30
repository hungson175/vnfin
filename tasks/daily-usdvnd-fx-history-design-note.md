# Design note — daily USD/VND history (future, source-gated)

**Date:** 30 August 2026 (UTC+7)<br>
**Status:** `SOURCE_GAP_CLOSURE / API_BLOCKED`; design-only, not implemented<br>
**Request:** `quant-researcher-frontier` frozen no-login USD/VND daily history<br>
**Companion source record:** [`docs/research/2026-08-30-daily-usdvnd-fx-history-source-status.md`](../docs/research/2026-08-30-daily-usdvnd-fx-history-source-status.md)

This note separates the future API shape from the current source result. The current v0.2.0
facade rejects `Frequency.DAILY` before transport with the exact annual-only `InvalidData`; the
daily source chain remains empty. No provider route, numeric budget, or public API change is
claimed by this note.

## 1. Current boundary

The existing public contract remains:

```python
vnfin.fx.history(
    base="USD", quote="VND", start=None, end=None,
    frequency=Frequency.ANNUAL,
) -> FXHistory
```

It serves World Bank `PA.NUS.FCRF` annual period-average USD/VND only. Current spot sources are
not historical sources. `rate_on()` and `rate_for_year()` remain exact lookup accessors; neither
fills or interpolates. The daily request's exact gate evidence is retained outside the repository
under:

```text
/home/hungson175/dev/trading-projects/quant-trading/quant-researcher-frontier/research/2026-08-30-vnfin-usdvnd-daily-cross-asset-anatomy/tdd/
```

No annual point, current quote, documented market start, or cross-rate may be relabeled as a daily
observation.

## 2. Proposed future API, only after source qualification

The requested call is an additive frequency path, not a replacement for annual behavior:

```python
fx.history(
    "USD",
    "VND",
    start=date(2000, 1, 1),
    end=date(2026, 8, 30),
    frequency=Frequency.DAILY,
) -> FXHistory
```

The exact public model fields must be reviewed against the qualified provider before coding. At
minimum the daily result must make these facts inspectable without inference:

| Field/diagnostic | Future requirement |
| --- | --- |
| `base`, `quote` | Response-backed `USD` and `VND`; reject wrong pair before network. |
| `points[].date` | Provider's observed/reference date, not retrieval date; plain date with documented timezone/date convention. |
| `points[].rate` | Finite, positive, non-boolean numeric value in the provider-backed direction; no inversion or scale guess. |
| `unit` / `value_unit` | Exact canonical `VND per 1 USD`, only after the provider's rate basis and scale are proven. |
| `frequency` | Explicit `Frequency.DAILY`; annual results remain `Frequency.ANNUAL`. |
| `source` | Canonical provider/route identity, not a generic alias or a guessed operator. |
| `fetched_at_utc` | Retrieval time only; never an observation/publication/knowability timestamp. |
| `coverage` | Requested bounds, real response-backed observed bounds, provider-declared non-publication, and unresolved gaps kept distinct. |
| `warnings` | Finite, deterministic, sanitized tokens; no raw URL/body/header/exception/provider text. |
| rights/rate/cache metadata | Documented source contract and diagnostic posture; unknown axes fail closed rather than being inferred. |

Whether `coverage`, `rate_basis`, or rights metadata are fields on `FXHistory` or a typed
`RequestDiagnostic` is an API decision for the design gate. The current dataclass is not modified
speculatively. Any additive field must update constructors, repr/equality/serialization,
DataFrame attributes, snapshots, docs, and CHANGELOG together.

### 2.1 Date and missingness semantics

The implementation must preserve the provider's observations exactly within the inclusive request:

- no annual substitution, interpolation, forward-fill, stale carry, nearest lookup, or current
  spot backfill;
- no weekend/holiday rows unless the provider actually publishes one;
- a provider-declared non-publication calendar may explain an absent date only when its semantics are
  documented and response-backed; otherwise the date is an unresolved gap;
- no provider publication timestamp may be invented from `fetched_at_utc`, HTTP headers, or a
  request date; and
- `rate_for_year()` must reject a daily history rather than treating a daily Jan-1 row as annual.

A complete result is not “one response looked non-empty.” The route must reconcile its pages/counts,
identity, bounds, and gaps. Any malformed page, duplicate, out-of-window row, unresolved missing
date, or incomplete boundary fails the whole retrieval and returns no partial history.

### 2.2 Source identity and no cross-synthesis

One qualification unit is exactly one owner, canonical route/version, direct USD/VND basis, date
semantics, response schema, and legal/runtime contract. ECB EUR-base legs, World Bank annual points,
commercial-bank spot quotes, or different provider calendars cannot be combined to manufacture a
direct daily USD/VND series. A failover chain is deferred until two independent providers qualify
the same basis and semantics; if one source qualifies, it serves the complete window alone.

## 3. Future qualification/reopen gate

Before any RED test or code, a new source/design review must prove all axes below in one exact
provider unit:

1. **Direct identity:** the response itself identifies USD/VND, the provider, the requested daily
   frequency, the rate direction, and the economic basis.
2. **Real coverage:** earliest/latest observed dates, requested-window behavior, page totals, and
   non-publication calendar are response/document-backed. A market start date or API maximum is not
   a coverage claim.
3. **Schema and numerics:** exact field names, MIME, envelope, date parsing, unit scale, positive
   finite rate, duplicate identity, and revision behavior are known. No source body is bundled.
4. **Legal/runtime rights:** no-login automation, rate policy, retries, caching/storage/retention,
   attribution, commercial use, caller-facing return/redistribution, and revisions are permitted
   for a public OSS runtime client. “Public,” “free,” or “for reference only” is insufficient.
5. **Bounded retrieval:** a source-specific finite request/page/date budget, concurrency bound,
   decompressed-byte bound, retry policy, and redirect policy are owner-backed and deterministic.
6. **Diagnostics:** transport, MIME, schema, identity, coverage, legal, and budget failures have
   separate typed outcomes; no failure is converted into a zero or coverage warning.
7. **Compatibility:** annual World Bank behavior, defaults, validation order, spot sources, and
   current diagnostics remain unchanged. Any additive model/API/snapshot/doc change is separately
   reviewed.

If any one axis is unknown, disposition remains `SOURCE_GAP` and the daily chain remains empty.

## 4. Budget and scheduler design (future, no constants frozen)

The exact numeric ceilings must come from the qualified provider and a design review; this note
does not promise a page count or retry count. The mechanism is fixed conceptually:

- one global atomic reservation ledger covers logical source attempts, physical HTTP calls,
  retries, redirects, pages/date fan-out, concurrent workers, and decompressed bytes;
- every physical call reserves its unit before dispatch; a failed reservation makes no request;
- a retry is a new reserved physical unit, never an invisible library retry;
- one deterministic scheduler owns reservation order (ascending page/date key and retry index), so
  concurrent callers cannot overspend or double-charge;
- redirects are either prohibited or separately reserved and source-authorized; they cannot silently
  change provider identity; and
- exhaustion fails closed with a typed budget outcome and no partial `FXHistory`, never a fabricated
  `SourceAttempt`, zero rows, or a `coverage_gap` warning.

Provider rate windows and cache terms are source-specific. No current spot five-minute/daily-cache
behavior may be transferred to a future historical source.

## 5. TDD / implementation sequence

This sequence is mandatory and is not started by this design note:

| Phase | Authorization and deliverable |
| --- | --- |
| A. Source gate | Static official/legal evidence plus separately reviewed bounded plan; no live probe until authorized. |
| B. Design PASS | Reviewer approves exact source unit, result metadata, missingness, legal posture, budgets, diagnostics, and compatibility. |
| C. RED | Only after design PASS, add synthetic fixtures/tests for valid daily response, exact date/rate/unit/source, malformed MIME/envelope/identity/numeric/date, duplicate/out-of-window rows, missing/non-publication, page reconciliation, retry ledger, atomic budget exhaustion, cache/rights docs, and zero-network current unsupported behavior. |
| D. Reviewer RED check | Reviewer verifies failures are real and fixtures are synthetic/no provider rows. No implementation yet. |
| E. GREEN implementation | Add the minimal adapter/facade/model changes; no provider fallback, cross-rate, fill, or unbounded retrieval. |
| F. Merged review | Run full suite, focused tests, import/API snapshot, docs/blacklist/secret/diff/build gates on the merged tree; request exact-SHA code review. |
| G. Publish | Push/close only after reviewer code PASS and explicit publication authorization. |

The current request is at **A, failed at the installed API boundary, and remains at
`SOURCE_GAP_CLOSURE`**. No RED, implementation, or runtime capability is authorized.

## 6. Reopen checklist

The daily capability can reopen only with a new exact source/design handoff that includes:

- a primary-source owner and canonical route/version;
- an exact response-backed USD/VND daily identity and direct rate basis;
- real first/last observed bounds for the requested window and explicit calendar/missingness rules;
- response schema, MIME, numeric/date/revision semantics and sanitized diagnostic vocabulary;
- written rights for automation, rate limits, retries, caching/storage, retention, attribution,
  commercial use, and caller-facing redistribution;
- a deterministic atomic budget and no-false-absence contract; and
- reviewer-approved RED-first transition before any code.

Until then, the only honest public behavior is the existing annual result or the exact
`InvalidData` annual-only rejection for `Frequency.DAILY`.
