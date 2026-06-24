# #195 FIX SPEC (binding) — `profile()` must carry the `sector_partial_coverage` token

**Why:** adversarial-verify (`wf_9b83088f-8a9`) confirmed a **major silent-coverage gap** —
`equities.profile(sym)` serves a mapped GICS sector but returns a bare `EquitySecurity`
(no `.warnings`), so the never-silent honesty contract is broken on the single-symbol entry
point. Violates the gate-approved build-spec matrix **case 5**, design-note L91, SKILL.md:164,
docs/api.md:351-355. Full analysis + repro: `/tmp/195-profile-gap-20260625.md`.

**Clean-room (HARD):** ZERO vnstock. No new sector data — this only fixes *disclosure* on the
already-derived sector. Synthetic fixtures only; assert zero network.

**TDD red-first** (Red → Green → Refactor). Runner: `.venv/bin/python -m pytest`.
**Do NOT** regen `tests/snapshots/public_api_v0_2_0.json` or run `scripts/dump_api_surface.py`
(release task). **Do NOT** push / close / message the reviewer — return a diff/summary.

---

## ⏳ PENDING reviewer ruling — type mechanism (a1 primary / a3 fallback)

> Reviewer ruling on a1 vs a3 is OUT (`/tmp/195-profile-gap-20260625.md`). Build the a1 shape
> below unless the reviewer rules a3; the a3 delta is noted inline. Everything else is identical.

### a1 (PRIMARY — my REC): new `EquityProfile` result wrapper
`vnfin/equities/models.py` — add a frozen dataclass AFTER `EquitySector`:
```python
@dataclass(frozen=True)
class EquityProfile:
    """One symbol's full enriched security + honest-coverage warnings (result type)."""
    security: EquitySecurity
    warnings: tuple[str, ...] = ()
```
`vnfin/equities/__init__.py` — `profile()` returns `EquityProfile(security=<enriched sec>,
warnings=(...))`. Export `EquityProfile` in `__all__`.

### a3 (FALLBACK — only if reviewer rules a3): `warnings` field on `EquitySecurity`
Add `warnings: tuple[str, ...] = ()` to `EquitySecurity` (after `sector_source`); `profile()`
returns the enriched `EquitySecurity` with `warnings` populated; universe rows keep `warnings=()`.

---

## profile() warnings content (BOTH mechanisms)
The warnings tuple `profile()` carries:
1. **Always** the coverage line `_sector_coverage_warning(<board of the symbol, e.g. "HOSE">)`
   — reuse the existing helper in `__init__.py`. (Scope = the symbol's own board; mapped or
   not, the derivation is HOSE-only-partial so the disclosure always applies.)
2. **If the symbol is a multi-basket overlap** → ALSO append `_sector_overlap_warning(sym, codes)`
   for that symbol (reuse the existing helper; `clf.overlaps()` already exposes it).
Both helpers already start with the `sector_partial_coverage:` prefix → **token count stays 49**
(no `_WARNING_TOKENS_180` change; #180 bijection + #188 forward-scanner stay green unchanged).

## RED-first tests (`tests/test_equities.py`)
1. **Rewrite the masking test** `test_profile_returns_full_enriched_security_with_coverage_token`
   (currently L696-711 — asserts NO token, passes green). Make it assert the token:
   - a1: `assert isinstance(prof, EquityProfile)`; `prof.security.sector_code == "VNFIN"` etc.;
     `assert any(w.startswith("sector_partial_coverage") for w in prof.warnings)`.
   - a3: keep `isinstance(prof, EquitySecurity)`; `prof.sector_code == "VNFIN"`;
     `assert any(w.startswith("sector_partial_coverage") for w in prof.warnings)`.
   Watch it FAIL on the current build first.
2. **NEW overlap-profile test:** a symbol synthesized into 2 baskets → all 4 sector fields `None`
   (mapped→None as a unit) **AND** `prof.warnings` contains both a `sector_partial_coverage:`
   coverage line and the `sector_partial_coverage: <sym> … baskets …` overlap line. Deterministic.
3. **Update** `test_profile_unmapped_symbol_full_row_all_sector_none` (L714+) and the not-found
   test (L727+) for the new return shape (a1: assert via `prof.security.*`; the unmapped row still
   carries the coverage line in `prof.warnings`). Not-found still raises `EmptyData` naming the symbol.

## Docs / SKILL lockstep (same commit)
- **a1:** `docs/api.md` (profile now returns `EquityProfile`; `.warnings` genuinely present —
  the L351-355 promise becomes TRUE); `skills/vnfin/SKILL.md:77` change profile's return
  `EquitySecurity`→`EquityProfile`; keep SKILL.md:164 (profile stays an emission site — now true);
  `CHANGELOG.md` note the wrapper. **a3:** docs/api.md L351-355 already true; SKILL.md:77 stays
  `EquitySecurity` (note "+ warnings"); CHANGELOG note the field.
- `vnfin/equities/__init__.py` profile() docstring: state it returns the disclosure-carrying result.

## Gates to pass on the merged tree
- Full suite green (`.venv/bin/python -m pytest`).
- `tests/test_docs_contract.py` green; `_WARNING_TOKENS_180` length **still 49** (assert, don't change).
- `tests/test_public_api_surface.py` green — additive only (new `EquityProfile` type / new field is
  additive → no `breaking` diff). Snapshot json **byte-identical** (no regen).
- No vnstock contamination.

## Commit
One coherent commit. Footer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
