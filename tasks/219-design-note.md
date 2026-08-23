# #219 design note — Vietnam monthly industrial-production YoY

**Date:** 2026-08-23 (UTC+7)
**Packet:** `tasks/219-vietnam-monthly-industrial-production-yoy-spec.md` at `f2d0187`
**Phase:** `SOURCE_DESIGN` / docs-only
**Disposition:** **SOURCE-GAP CLOSURE**
**Current source chain:** empty
**Requested window:** `2018-01-01..2026-08-19` inclusive
**Implementation status:** no enum, registry, adapter, API, model, test, or runtime capability

The companion report is
[`docs/research/2026-08-23-vietnam-monthly-industrial-production-yoy-source-vetting.md`](../docs/research/2026-08-23-vietnam-monthly-industrial-production-yoy-source-vetting.md).
This note binds the design gate and authorizes no implementation.

## 1. Clean-room and scope boundary

`docs/vnstock-blacklist.md` was read before research. Searches used:

```text
-vnstock -"VNStock" -vnstocks.com -"thinh-vu/vnstock" -vnstock-hq -"vnstock-agent"
```

No prohibited or derivative material was opened, cited, compared, installed, imported, or used.
Only official NSO/GSO, IMF, World Bank, and UN Statistics Division sources and their official
terms/metadata routes were considered. No raw response, live value, query-bearing URL, cookie,
header, token, response digest, or credential is committed.

The only future product primitive is the existing macro call:

```python
vnfin.macro.get_indicator(
    "VNM", vnfin.macro.MacroIndicator.INDUSTRIAL_PRODUCTION_YOY
) -> IndicatorSeries
```

If—and only if—a later source passes, its contract is exactly:

- canonical indicator `industrial_production_yoy`, name `Industrial Production Year-over-Year`;
- unit/value-unit `%`, currency `None`, frequency `MONTHLY`;
- provider observation month normalized to a plain month-start point key, never release date;
- exact `VNM` capability checked before network; unsupported country/indicator is zero-network;
- finite, non-boolean values, including valid negative and zero observations, ascending unique
  month keys, and no fabricated missing/zero points; and
- one provider/series/revision convention for the whole result, with no silent stitch or fallback.

Do not substitute annual, quarterly, cumulative, index-level, manufacturing-only, CPI, GDP,
market, interpolated, or locally derived values. Acceleration, first difference, VN30F alignment,
signals, and backtests remain caller-side.

## 2. Source decision

| Candidate unit | Identity/measure | Coverage/runtime | Legal/reuse | Total decision |
|---|---|---|---|---|
| Official NSO release family + PXWeb catalogue | Strong owner and narrative national IIP same-period-last-year semantics; no exact machine row/series binding | Archive reaches the requested era, but no reconciled monthly row set, totals/cursors, revision contract, or stable no-login YoY API; PXWeb table is not proven exact monthly YoY | NSO attribution/copyright language found; open/commercial OSS redistribution permission not established | `SOURCE_GAP` |
| IMF Production Index/API/DSBB | Monthly Vietnam Production Index metadata, not exact direct national YoY values | Current API access documentation points to sign-in/beta flow; exact no-login route, span, pages, and revision runtime not proven | Exact-series reuse terms not established | `SOURCE_GAP` |
| World Bank GEM/dashboard | Public industrial-production catalogue and secondary Vietnam YoY dashboard | Direct VNM row identity, raw-vs-derived provenance, current span, pages, and vintages not proven | Dataset visibility is not an exact redistribution grant | `SOURCE_GAP` |
| UN MBS | No-login Vietnam industrial-production viewer/web service | Observed unit is a `2010=100` index level and bounded target-window display had no data; not provider-published YoY | Conditions-of-use/copyright visible; OSS redistribution licence not established | `SOURCE_GAP` |

Qualification requires all axes on one owner unit. No partial provider result is safe to expose:
the NSO narrative family cannot be reconciled into a stable series, and the UN index cannot repair
the exact-measure gap. The empty chain is deliberate and fail-closed.

## 3. Qualification unit and mandatory axes

One candidate can qualify only as:

```text
owner + canonical route/version + exact VNM national IIP YoY series/release template
+ observation-month/revision convention + requested coverage
+ response/runtime contract + rate/retry/storage policy + written reuse rights
```

The source/design gate is conjunctive across these axes:

1. **Transport and access:** official owner, method, stable host/path, expected status, complete
   normalized MIME, effective route, redirect policy, no-login or explicit automation permission,
   WAF/challenge behavior, bounded bytes, and no hidden dispatches.
2. **Response identity:** response/catalogue binds `VNM`, national whole industry, exact monthly
   provider-published YoY, `%`, series/release identifier, and nullability. Request echo or page
   title alone is insufficient.
3. **Semantics:** observation month differs from publication date; precision/rounding,
   seasonal-adjustment, base/rebase, preliminary/final/revised, and as-of/vintage behavior are
   typed. No local index-to-YoY transformation is authorized here.
4. **Coverage:** provider-declared bounds, exact requested span, monthly calendar, first/last
   observation, distinct/duplicate/conflict behavior, gaps, page/cursor/totals reconciliation,
   and historical-vintage limits. Unresolved truncation is not `FULL` or empty.
5. **Legal/runtime:** rate, retry, cache/storage, retention, attribution, commercial use,
   derivative use, and redistribution rights are explicit for the exact values and route.
6. **Failure contract:** empty, not-yet-published, missing-month, boundary, transport, schema,
   budget, and non-service outcomes are finite and never converted to false absence.

## 4. Evidence and bounded observations

The report records no-credential official-owner observations only. A browser-like UA was a bounded
transport choice; no no-UA control was run, so UA necessity and automation permission remain
unknown. No cookies or sessions were retained. Research dispatches were sequential and had zero
recorded retries; logical and physical counts are preserved per evidence cell in the report.

The important boundaries are:

- NSO archive and release-calendar HTML were reachable without login, and the archive contains
  monthly release material spanning the requested era. It does not provide one reconciled machine
  series with a provider total, row identity, revision map, or exact redistribution licence.
- NSO PXWeb `E07.01` is an official industrial-production index table with activity/year metadata;
  its visible table identity does not prove a month-keyed provider-published YoY series. Three
  no-credential API-path candidates and one bounded UI transport attempt timed out; this is
  `TRANSPORT_INCONCLUSIVE`, never confirmed absence.
- IMF DSBB monthly periodicity is metadata, not a direct exact YoY response. The current IMF API
  access documentation points to sign-in/beta access, so no login workaround is permitted.
- The World Bank dashboard is a secondary compilation citing multiple inputs and staff
  calculation. It cannot act as an owner, identity, coverage, or redistribution oracle.
- UN MBS is technically reachable without login, but the bounded viewer identifies a general
  industrial-production index with `2010=100`; its target-window view has no data and a wider
  bounded view ends before the requested span. No local YoY derivation is allowed.

## 5. Exact no-false-absence contract — design only

The future source adapter must map every attempt to exactly one finite outcome:

```text
FULL | PARTIAL | PUBLISHED_EMPTY | NOT_YET_PUBLISHED | MISSING_MONTH |
COVERAGE_BOUNDARY | NOT_SERVED | TRANSPORT_FAILURE | SCHEMA_DRIFT |
BUDGET_EXHAUSTED | LEGAL_GAP | IDENTITY_GAP
```

Definitions are strict:

- `FULL` requires all provider-declared monthly keys in the requested span, finite values,
  ascending unique points, and reconciled pages/totals/calendar/revision checks.
- `PARTIAL` requires provider-declared supported bounds and reconciled returned pages; an
  unexplained interior gap is fatal and cannot be downgraded to partial.
- `PUBLISHED_EMPTY`, `NOT_YET_PUBLISHED`, `MISSING_MONTH`, and `COVERAGE_BOUNDARY` each require
  provider-backed declaration. An empty body/array, timeout, WAF/403, or one missing page is not
  any of them.
- `NOT_SERVED` is a pre-network capability/country/indicator/interval decision and says nothing
  about provider history.
- `TRANSPORT_FAILURE`, `SCHEMA_DRIFT`, `BUDGET_EXHAUSTED`, `LEGAL_GAP`, and `IDENTITY_GAP` never
  produce an empty successful `IndicatorSeries` or a partial result.

Public diagnostics, if later approved, use only finite source tokens (`nso`, `imf`, `world_bank`,
`un_mbs`), finite outcome/warning tokens, and bounded integer logical/physical/page/retry/byte
counters. Raw URL/query, body, headers, cookies, exceptions, arbitrary provider text, and
unbounded names are forbidden. Missing publication/revision metadata is a bounded warning, never
a fabricated date.

## 6. Deterministic budget contract — design only

No numeric ceiling is frozen before a qualifying route and published rate policy exist. The future
implementation must nevertheless reserve atomically:

1. one logical source attempt before adapter entry;
2. one physical dispatch immediately before each HTTP request, page, cursor, retry, redirect
   follow-up, or bounded byte/decompression operation;
3. zero budget and zero attempt record for an incapable source skipped before network; and
4. one request-scoped global ledger with no per-source, page, or fallback reset.

Exhaustion must discard private partial rows and return only the reviewed bounded
`BUDGET_EXHAUSTED` outcome/diagnostic; it must never publish a partial `IndicatorSeries` or imply
historical absence. Any future numeric limits must be derived from owner rate/byte/retry policy
and reviewed as part of a fresh design packet.

## 7. Reopen gate and release sequence

Reopen is allowed only when a fresh primary-source packet proves all of the following together:

- real owner route/version and contact path, full status/MIME/effective-route/redirect contract,
  no-login or explicit automation permission, and bounded WAF/bytes/rate/retry behavior;
- response-backed VNM national whole-industry monthly provider-published YoY identity, `%` unit,
  observation-month key, nullability, precision, and typed revision/as-of semantics;
- requested coverage or an explicitly provider-bounded partial range with page/totals/cursor,
  calendar, gaps, and vintage reconciliation;
- lawful attribution, storage, cache, retention, commercial use, derivative use, and
  redistribution rights for the exact data; and
- finite sanitized outcomes, atomic budget behavior, stable existing macro compatibility, and a
  complete RED/release matrix.

One release page, one numeric observation, an index table, a secondary dashboard, a guessed API,
or a timeout/no-data response cannot reopen this closure. A future `QUALIFIED_PARTIAL` result must
expose its provider-declared boundary and cannot silently become `FULL`.

For this source-gap disposition, after exact-SHA design PASS the only allowed sequence is merged
docs/full/build/blacklist/diff gates, exact approved docs push, remote HEAD/ancestry/path check,
clean no-capability resolution, close/re-read #219, and local completion. This does not authorize
TDD or runtime work. #220, #222, #223, and #224 remain queued.

## 8. Review handoff

The two requested source/design artifacts and the backlog lifecycle are the complete scope of this
handoff. The exact artifact SHA is recorded in `tasks/active-backlog.md` after commit. Request
review of the merged tree only, with the empty chain and no-code/no-push/no-close invariant intact.

## Bottom summary

- #219 decision: **SOURCE-GAP CLOSURE**; no candidate qualifies for TDD or partial publication.
- NSO has the right semantic lead but no reconciled exact monthly YoY runtime/legal unit.
- IMF and World Bank remain identity/coverage/revision/reuse gaps; UN MBS is index-level and stale.
- New source chain stays empty; current macro API and behavior are unchanged.
- No false absence, local derivation, fallback stitch, or numeric budget promise is allowed.
- Only the research note, this design note, and backlog lifecycle are in scope.
- No RED, production code, push, or close before exact-SHA design PASS.
- Reviewer needs the final committed SHA and merged docs/full/build/blacklist gate results.
