# #206 design note — VNFIN daily sector-index history

**Issue:** #206
**Date:** 2026-08-23 (UTC+7)
**Phase:** SOURCE_DESIGN / docs-only
**Builder:** `vnfin-oss`
**Initial capability:** none; current `VNFIN` index-history chain remains unreachable
**Disposition:** **SOURCE-GAP CLOSURE**
**Review gate:** exact-SHA design review required before any production change, push, or close

The source facts and sanitized probe record are in
[`docs/research/2026-08-23-vnfin-sector-index-history-source-vetting.md`](../docs/research/2026-08-23-vnfin-sector-index-history-source-vetting.md).
This note binds the implementation boundary if a later written permission and design
PASS reopen the work. It does not authorize TDD now.

## 1. Product boundary

The only requested public primitive is the existing strict call:

```python
vnfin.indices.index_history(
    "VNFIN",
    date(2020, 5, 11),
    date(2026, 8, 19),
    interval=Interval.D1,
)
```

It would return provider-reported daily OHLCV **points** for the canonical `VNFIN`
HOSE Financials sector index. This batch does not implement VNFIN-minus-VN30,
VN30F/session logic, constituents, weights, signals, backtests, intraday history,
other sector indices, or a new public API. `index_history_stitched()` is not a silent
substitute: it remains an explicit D1-only opt-in with its existing multi-source
provenance.

The current public behavior is preserved until a later gate passes:

- `VNFIN` is recognized by the index namespace and rejected from stock-price history
  before network;
- it is absent from the index value-history allow-list, so the current index chain is
  empty/unreachable for this selector;
- all other deny-only identifiers and headline-index behavior remain unchanged; and
- no production code, live rows, cache, fixture, example, push, or issue close is part
  of this docs commit.

## 2. Evidence decision

| Source | Identity | Requested D1 boundary/rows | Volume/shape | Decision |
|---|---|---:|---|---|
| VPS | History echo plus same-owner symbol metadata | `2020-05-11..2026-08-19`; raw 1,603 rows / 1,569 dates; current parser 1,534 bars | Aligned `v`; 34 duplicate dates, 33 conflicts, two invalid OHLC rows | `PARTIAL`; cannot be the exact clean winner without a duplicate/quality contract |
| SSI | Same-owner metadata binds `VNFIN`, HOSE, index; history body has no echo | 1,569 rows/dates; both boundaries | Aligned `v`, no duplicate/invalid observation | Technical `QUALIFIED`; legal gate remains `LEGAL_GAP` |
| VNDirect | No history echo; no usable same-owner metadata route; control only | 1,570 rows/dates; both boundaries | Aligned `v`, no duplicate/invalid observation | `IDENTITY_GAP`; not a qualified fallback |

All three are vendor feeds, not official HOSE output. The requested full-span
capability is not claimed: SSI and VNDirect differ on `2025-05-05`, VPS and the other
two differ on `2021-06-28`, and the official calendar classification is unresolved.
All three vendors also lack an explicit licence permitting the library's automated
retrieval plus caller-facing redistribution. The correct current status is therefore
`SOURCE-GAP CLOSURE`, not “qualified for TDD.”

## 3. Registry and interval guard (future design, not implemented)

Use a private registry-level capability predicate, not a one-line allow-list edit and
not a public-API branch:

1. Add exactly one member, `VNFIN`, to `_VALUE_HISTORY_INDICES`. The set union keeps
   `VNFIN` in `_KNOWN_INDEX_IDENTIFIERS`, so `prices.history("VNFIN", ...)` remains a
   typed zero-network rejection.
2. Normalize once with `canonical_security_symbol`: `" vnfin "` and `"vnfin"` become
   `VNFIN`; malformed/non-string/punctuation selectors fail before network.
3. Resolve the interval before `apply_interval`. For canonical `VNFIN`, only
   `Interval.D1` is capable. Reject every intraday member (`M1/M5/M15/M30/H1`) and
   every coarser/resampled member (`W1/MN1/Q1/Y1`) with one stable typed
   `UnsupportedInterval` diagnostic that states D1-only and zero network calls.
4. Do not alter headline-index native intraday or coarser-resampling behavior. The
   guard must run before the current `apply_interval` branch, otherwise a VNFIN W1
   request could fetch D1 and a VNFIN intraday request could reach inherited adapter
   capabilities.
5. Keep `index_history_stitched("VNFIN", ..., interval=Interval.D1)` opt-in only. It
   may pass the registry because its existing public method is already D1-only, but
   it must never be used by strict `index_history` to fill a source gap.

The private predicate must be covered by zero-network tests for all non-D1 intervals,
malformed selectors, padded/lowercase normalization, stock-price denial, the exact
one-member allow-list delta, and unchanged deny-only/headline behavior.

## 4. Strict source/failover contract

The future source order may remain `VPSIndexSource → SSIIndexSource →
VNDirectIndexSource`, but a source is accepted only after all result checks pass. A
source that cannot meet identity/legal/quality requirements is not documented as
supported. For the current evidence:

- VPS must fail closed for the observed conflicting/quarantined VNFIN rows rather
  than returning a partial winner for an exact-span request; it may be attempted and
  recorded as a failed source if the source-specific validator can identify the
  failure without leaking raw provider text.
- SSI is the only observed technical candidate, subject to written permission and a
  stable runtime binding between its metadata route and history request.
- VNDirect is incapable for VNFIN until it supplies response-backed identity; it is
  skipped before transport and therefore contributes no fabricated `SourceAttempt`.

For an authorized implementation, one logical `index_history` call makes at most one
bounded full-window history request per capable source. `max_attempts` remains a
positive per-call budget and counts actual source calls in deterministic order; a
capability skip does not consume it. A recoverable source failure causes the next
source to receive the **same** requested range. The first accepted result owns the
whole series. There is no per-date merge, retry storm, stitching, forward-fill,
backfill, interpolation, or hidden fallback to `index_history_stitched()`.

Every accepted result must satisfy:

- `symbol == "VNFIN"`, exact `provider_symbol`, and `source` equal to the producer;
- `interval is Interval.D1`, `AdjustmentPolicy.RAW`, `value_unit == currency ==
  "points"`, `proxy_for is None`;
- non-empty, ascending, unique VN-local dates with timezone-aware `PriceBar.time`;
- finite positive OHLC, `low <= open/close <= high`, and point scale 1.0;
- integer, non-negative provider volume; and
- bounded sanitized `warnings` and exact ordered `SourceAttempt` records, with no
  URL, response body, credential, raw exception, or unbounded provider text.

Range acceptance is exact for this requested batch: both `2020-05-11` and
`2026-08-19` must be present in the winning source. Actual internal dates are
preserved; an unexplained missing date is a diagnostic/source failure, never a
synthetic bar. Existing `partial_start_coverage`, `partial_end_coverage`,
`quarantined_invalid_bars`, and duplicate warnings remain explicit if a later design
chooses a partial capability, but this issue's requested full-span winner cannot
hide them.

## 5. Volume contract

The raw probes found aligned `v` arrays on all three routes, and VPS/SSI metadata
declared `has_no_volume=false`. The current shared UDF parser nevertheless turns an
absent or null `v` into zeroes. That shortcut is unsafe for VNFIN and is not part of
this design.

The future VNFIN-specific parser seam is fail-loud:

- missing `v` → `InvalidData`, recorded as a recoverable source attempt;
- `v is None` → `InvalidData`, recorded as a recoverable source attempt;
- non-list, misaligned, fractional, negative, non-finite, or malformed volume →
  `InvalidData`/quarantine according to the approved row contract, never a zero;
- a present provider-reported integer zero remains `0`; and
- a qualified result documents that its volume is provider-reported and does not
  silently represent missing volume.

No optional `volume`, `NaN`, sentinel zero, constructor migration, or public snapshot
change is authorized. If later evidence proves that the only legally qualified source
does not provide volume, stop and open a separate additive typed missing-volume design.

## 6. Legal/runtime and reopen gate

No-auth access is only a transport observation. It is not a licence. Current legal
status is `LEGAL_GAP` for VPS, SSI, and VNDirect: the provider terms either restrict
copying/reproduction/distribution or provide no affirmative route-specific API/data
reuse grant. The runtime posture remains no cache, no bundled rows, no archive, no
bulk export, and no public live-value examples.

Reopen to TDD only when all gates below are evidenced in a new review packet:

1. Written provider permission/licence names automated retrieval and explicitly covers
   OSS use, caller-facing return/redistribution, storage/caching, attribution,
   rate-limit policy, and commercial restrictions.
2. A named source binds the requested selector in the response or in a documented
   same-owner metadata contract that the runtime adapter can enforce without an
   unbounded hidden request. VNDirect needs a new identity route or equivalent
   provider-backed contract.
3. The same source gives exact requested boundaries and a documented/officially
   accounted internal date set; no conflicting duplicates or invalid OHLC rows are
   accepted as a clean full-span winner.
4. The same source returns aligned non-null volume on every successful response.
5. The registry, strict failover, budget, warning sanitization, public compatibility,
   offline synthetic fixtures, docs, and full merged-tree gates pass.

## 7. TDD matrix after a future design PASS only

No RED tests or production code are part of this commit. If the conjunctive reopen
gate passes, the first code commit must begin with synthetic RED tests for:

1. baseline VNFIN D1 zero-network rejection, then exact one-member allow-list delta;
2. lowercase/padded normalization and malformed zero-network failure;
3. all non-D1 zero-network failures with unchanged headline behavior;
4. VPS/SSI direct success contracts with fabricated boundaries, points/RAW metadata,
   exact provider identity, VN timezone, and aligned integer volume;
5. VNDirect explicit incapable/identity-gap behavior;
6. primary success, primary recoverable failure then SSI fallback, all-source failure,
   exact bounded ordered attempts, and no per-date source mixing;
7. response identity mismatch, metadata absence, malformed envelopes, wrong MIME/body,
   misaligned arrays, invalid OHLC, duplicate/conflicting dates, and out-of-range
   padding;
8. missing/null/fractional/negative volume versus present integer zero;
9. exact boundary coverage, no fill/reconstruction, warning disclosure, and strict
   versus stitched separation; and
10. API/docs/build/blacklist/secret/diff gates on the merged tree.

This document itself requests only source/design review. It does not authorize TDD,
production code, push, or issue closure.
