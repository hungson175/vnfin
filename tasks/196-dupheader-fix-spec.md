# #196 follow-up fix spec — dup-header ambiguity guard in the shared CMO parser

**Origin:** adversarial-verify Workflow `wf_e3ddaf5a-b2e`, lens NEVER-FABRICATE (severity medium).
**Completes gate condition (d)** (`reviews/gate-202606251627-issue196-design-note.md`): "never relabel
another column." **TDD: fail-first regression, then the minimum guard. No tests → no code.**

## The defect (verified by real probe)

`vnfin/_contracts/worldbank_cmo.py` `parse_cmo_annual(raw, spec)` locates the metal column by the split
header (name row + `($/troy oz)` units row directly below, same column) and **`break`s on the FIRST
match** (lines ~299-308). If a sheet carries **two** columns that both satisfy a metal's split header,
the first-in-scan silently wins and the second is ignored — **no ambiguity error**. Weaponized via the
documented band overlap (gold ~35-3442 sits fully inside platinum's band [50,5000]): a decoy `Platinum`
column carrying gold-magnitude data is served as `product=XPT` with no warning. This contradicts the
parser's own docstring ("anything unexpected fails safe as InvalidData"). Gold shares the identical
behavior (same shared parser) — so the fix hardens gold too.

**Reachability:** the genuine World Bank CMO file has exactly ONE Gold/Silver/Platinum column each, so
this is NOT reachable from real data and NOT a #196 regression — but the never-fabricate contract
(treat all provider data as untrusted) requires the parser to fail safe on a forged/duplicate-header
file rather than serve a wrong-metal value relabelled.

## The fix (minimum)

In `parse_cmo_annual`, replace the first-match-`break` with: collect **every** distinct column whose
cell text strips to `spec.name_row` AND has `spec.units_row` directly below it (same column). Then:
- **0 matches** → keep the existing missing/units-mismatch diagnostics (unchanged).
- **exactly 1 match** → proceed exactly as today (`metal_col`, `units_row`).
- **>1 distinct matching column** → `raise InvalidData` naming the metal and the ambiguity, e.g.
  `f"worldbank_cmo: ambiguous — multiple {spec.name_row!r} ({spec.units_row}) columns in sheet {_SHEET_NAME!r}"`.

Keep it inside the existing `with`/parse block; do not change any other guard (duplicate-year,
non-monotonic-year, band, rels-resolution all stay). Do not change `coerce_price` or `MetalSpec`.

## Tests (RED-first — add to `tests/test_metals.py` or a parser test file; reuse the synthetic xlsx builder)

1. **RED→GREEN dup-header (metals):** build a synthetic sheet with TWO `Silver` split-headers in
   different columns (both with `($/troy oz)` below; e.g. col A=year, one Silver col value 20.0, the
   other 39.8). `parse_cmo_annual(raw, <silver spec>)` must `raise InvalidData` whose message contains
   `Silver` (and "ambiguous"/"multiple"). **Prove RED:** against current code it returns `{...: 20.0}`
   (first match) and the test fails with "DID NOT RAISE" — i.e. RED is on the new guard, not an import.
2. **RED→GREEN dup-header weaponized (never-fabricate):** a decoy `Platinum` column carrying
   gold-magnitude values (1942/2386/3441, all inside platinum's band) PLUS the real `Platinum` column
   (966/955/1278), decoy first-in-scan. `M.history("platinum", ...)` (injected fetch) must raise (the
   source wraps the parser `InvalidData`) — assert it does NOT return `bars` with the gold-magnitude
   values. This is the fabrication the guard prevents.
3. **Dup-header gold parity:** a synthetic sheet with TWO `Gold` split-headers →
   `parse_cmo_annual(raw, _GOLD_SPEC)` (or `_parse_cmo_annual_gold(raw)`) raises `InvalidData` naming
   `Gold`. (Confirms the shared guard covers gold.)
4. **Single-column unchanged (regression-negative):** a normal single-`Silver` sheet still parses to
   the correct value; assert no false-positive ambiguity raise.

## Invariants to hold after the fix (verify on the MERGED tree)

- **Gold observably unchanged on REAL data:** `WorldBankCmoGoldSource(http_get=fixture).get_history`
  over 1960..2025 returns identical values (2025=3441.51, 2024=2387.70); the real fixture has one Gold
  column so the new guard never fires on it. All existing gold tests stay green.
- Full suite **exit 0**; gate files green (`tests/test_metals.py`, `tests/test_worldbank_cmo_gold.py`,
  `tests/test_gold_world_reference.py`, `tests/test_public_api_surface.py`, `tests/test_docs_contract.py`,
  `tests/test_no_secrets.py`).
- `_WARNING_TOKENS_180` stays **49**; snapshot `public_api_v0_2_0.json` **byte-identical** (do NOT
  regen); zero vnstock; no new warning token (the guard raises, it does not append to `.warnings`).

## Out of scope (do NOT touch)

- `fetched_at_utc` semantics (separate reviewer ruling pending).
- Gold's public surface, the bands, the snapshot baseline, any docs beyond what the guard requires
  (this is a pure internal-parser hardening — no public-surface change, so no docs/CHANGELOG lockstep
  needed unless you add a public symbol, which you must not).

Return a diff/summary. Do NOT push, do NOT message the reviewer, do NOT close anything.
