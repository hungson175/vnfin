# Design — long index-history windows (#147)

**Status: IMPLEMENTED — Option 2 v1 shipped** (reviewer-approved spec review-202606200913).
`vnfin.indices.index_history_stitched` (opt-in, D1, calendar-year segments via the failover chain,
`source="stitched_index_history"`, `stitched_multi_source` + per-segment warnings, absolute
points/points/RAW/canonical-symbol enforcement, seam dedup) is the delivered fix; the default
strict `index_history` is unchanged. **Option 1 (diagnostic) and Option 3 (lenient quarantine) are
deferred** — not in this batch. The original analysis/options are retained below for context.

> **Superseded note (#186):** the root cause described in *Problem* below — "the strict per-row guard
> raises `InvalidData` on one bad day, failing the whole source" — was fixed at the source by #186:
> `UDFSource._build_bars` now **quarantines** isolated bad bars (drops + `quarantined_invalid_bars`
> warning) instead of raising, with a threshold guard for systematically-broken sources. This is
> effectively a built-in form of Option 3, now the **default** for both `index_history` and
> `prices.history` (the "strict raise on one bad day" default no longer exists). `index_history_stitched`
> remains the multi-source long-window stitcher; the two are complementary. See
> `docs/architecture/failover-and-validation.md` → "Source-side bad-bar quarantine".

## Problem

`vnfin.indices.index_history("VNINDEX", 2016-01-01, 2026-06-01)` fails with `AllSourcesFailed`
because **each** source has a single OHLC-invariant-violating day inside the 10-year window
(vps_index @2018-08-22, ssi_index @2016-10-24, vndirect_index @2020-09-29). The strict per-row
guard (`udf.py` "OHLC invariant violated") raises `InvalidData` on that one bad day, failing the
whole source — and since every source has *some* bad day in a long window, the whole chain fails.
Yet per-segment the window succeeds, because a different source is clean for each bad segment
(the issue shows calendar-year windows all OK via varying sources).

## Constraints (from the tech-lead)

- **No silent row-drop** in the default strict API. Any lenient/stitched behavior must be explicit,
  opt-in or a distinct entrypoint, with documented provenance + warnings.
- Preserve units (`points`), the canonical symbol, and existing strict semantics for callers who
  rely on them.
- Serve the long-term-investor workflow: a 10-year VNINDEX window should be obtainable.

## Options

### Option 1 — diagnostic helper (cheap, reactive)
Add `vnfin.diagnostics.explain_index_history(symbol, start, end)` (or extend diagnostics): when a
long window fails, identify the failing day(s) per source and which sub-windows succeed via which
source; suggest narrower windows. **Pros:** low risk, no behavior change, immediate guidance.
**Cons:** does not return the 10-year series — only explains the failure.

### Option 2 — segment-stitching (the real workflow fix) — RECOMMENDED
A stitching path splits the request into segments (e.g. calendar-year, or adaptive bisection around
a failing day), fetches each segment through the **existing failover chain** (so a source's bad day
is routed around by another clean source for that segment), and stitches the segments into one
`PriceHistory`. **Provenance (explicit, never implied single-source):** result `source="stitched"`
(or composite), with per-segment `segment -> source` attribution surfaced in `warnings` (and the
`attempts` of each segment retained/summarized); an explicit `stitched_multi_source` warning.
Seam handling: strictly-ascending dedup at segment boundaries; reject overlapping/conflicting seam
bars. **Open:** default `index_history` vs a new opt-in entrypoint/mode (see questions). **Risks:**
multi-source provenance semantics; adjustment-policy homogeneity across sources; N segment calls
(cost); boundary continuity. **Benefit:** directly unblocks the 10-year workflow with honest
provenance.

### Option 3 — strict/lenient quarantine mode (weaker fallback)
Opt-in `lenient=True` / `on_bad_row="quarantine"` that skips a single OHLC-violating day **with an
explicit warning listing the dropped date(s)**; strict-raise stays the default. **Cons:** a single
source still has the gap (doesn't use other sources' clean data for that day); closest to the
"silent drop" the tech-lead is wary of (mitigated only by opt-in + explicit dropped-date warning).

## Outcome (what shipped)

The reviewer approved **Option 2 v1 only** as the fix: opt-in `index_history_stitched`, calendar-year
D1 segments, explicit multi-source provenance (`stitched_multi_source` + per-segment warnings),
absolute points/points/RAW/canonical-symbol enforcement, seam dedup with conflict → `InvalidData`;
the strict default `index_history` is unchanged. **Option 1 (diagnostic) and Option 3 (lenient
quarantine) were deferred** to possible later batches. The options analysis below is kept for record.

## Open questions for reviewer

1. Stitching as a new entrypoint (e.g. `index_history(..., stitch=True)` or
   `vnfin.indices.index_history_stitched(...)`) vs changing the default? (I lean opt-in.)
2. Segmentation: fixed calendar-year vs adaptive bisection that isolates the failing day and keeps
   the largest clean spans?
3. Provenance representation: `source="stitched"` + per-segment in `warnings`/`attempts`, or a new
   typed field? Any SemVer/public-API-snapshot impact to confirm.
4. Adjustment-policy homogeneity: is a stitched series mixing sources acceptable given index levels
   are points (no adjustment families like equities)? Expected yes, but confirm.
5. Scope for v1: diagnostic-only first (smaller, safe), then stitching as a follow-up — or both now?
