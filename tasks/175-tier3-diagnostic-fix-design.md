# #175 Tier-3 design note — fix misleading index-constituents diagnostic guidance

**Issue #175, Tier-3** (small, NO source, NO #180/#188 lockstep — these are diagnostic
`suggested_actions`, not `result.warnings` tokens). Follows Tier-1 (`current_snapshot_only`, shipped
3d33859). Tier-2 (historical PIT membership) stays the reviewer's source-gate.

## The bug (active misdirection)
Two diagnostic strings tell users to do the EXACT thing Tier-1 warns against:
- `vnfin/diagnostics.py:155` — `_INDEX_CONSTITUENTS_CAPS[0].suggested_action =
  "treat membership as point-in-time; do not expect weights"`
- `vnfin/diagnostics.py:266` — `explain_index_constituents(...).suggested_actions[0] =
  "treat the membership basket as point-in-time"`

The basket is the **current** snapshot, NOT point-in-time; "treat as point-in-time" is precisely the
misuse that injects survivorship/look-ahead bias into backtests. The offline diagnostic currently
contradicts the live `current_snapshot_only` warning — a real correctness bug in user-facing guidance.

## Fix (surface-neutral — string values only; signatures/types/snapshot unchanged)
1. `diagnostics.py:155` → `suggested_action="treat the basket as the CURRENT membership snapshot, NOT
   point-in-time — backtests using it inherit survivorship/look-ahead bias; do not expect weights"`.
2. `diagnostics.py:266` → first suggested action becomes `"treat the membership basket as the CURRENT
   snapshot, NOT point-in-time — backtests using it inherit survivorship and look-ahead bias"` (keep
   the second "do not expect constituent weights ..." action unchanged).
3. (additive, optional) add one `notes` entry to `explain_index_constituents` stating point-in-time /
   historical membership is not available from this source (consistent with Tier-2's source gap).

No new public symbol (`explain_index_constituents` + `source_capabilities()` already exist in the
frozen surface). String values are NOT captured by the public-API snapshot → byte-unchanged; do NOT
run `dump_api_surface.py`.

## TDD (fail-first; this is a bug → regression test required)
In `tests/test_diagnostics.py` (or wherever these are asserted):
1. RED: assert `explain_index_constituents(...).suggested_actions` contains NO advice to treat
   membership as point-in-time, AND contains the "current snapshot / NOT point-in-time" correction.
   (Fails against the current strings.)
2. RED: assert the `_INDEX_CONSTITUENTS_CAPS`/`source_capabilities()` entry for indices/constituents
   carries the corrected `suggested_action` (no "treat membership as point-in-time" advice).
3. GREEN after the string fix. Regression: status stays `single_source`; the no-weights guidance is
   preserved; canonicalization/fail-closed behavior unchanged.
4. Update any existing test that asserts the OLD strings (it currently locks in the bug).

## After Tier-3 lands
Close #175 as source-gap-documented for Tier-2 (no clean redistributable historical-membership feed;
HOSE = date-stamped human PDFs) with reopen criteria — same pattern as #182. (Reviewer confirms close.)
