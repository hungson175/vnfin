# #192 — def-use trace to close the #188 forward-discovery blind spot (SPEC)

**Scope:** TEST-INFRA ONLY — `tests/_warning_token_scan.py` (extend the extractor) + one synthetic-snippet
unit test in `tests/test_docs_contract.py`. No `vnfin/` change, no new token, snapshot frozen,
`_WARNING_TOKENS_180` unchanged. TDD: write the failing `dup_notes`-shape unit test FIRST.

## Problem
#188's extractor keys on accumulators matching `(^|_)warnings$` (+ `warnings=` kwargs + `_*warning(s)`
helper returns). Five DOCUMENTED tokens emit via intermediate accumulators NOT named `*warnings`, so they
are NOT forward-discovered (reverse #180 test still pins them, so not unguarded — but a NEW such token
would be invisible):
- `partial_start_coverage`, `partial_end_coverage` — via a `warns` accumulator.
- `skipped_period_rows` — `vnfin/sources/cafef.py:~530`, `note = ...`.
- `skipped_mismatched_report_rows` — `vnfin/sources/vndirect.py:~511`, `note = ...`.
- `cross_board_duplicate_symbol` — `vnfin/equities/sources.py:156-177`, `dup_notes` →
  `warnings=tuple(warnings) + tuple(dup_notes)`.

## Fix — a small intra-function def-use trace (NOT a generic var-name broadening)
Broadening the name regex to `warns`/`note`/`dup_notes` would over-match unrelated code → false-positive
reds (the reason #188 chose the conservative match). Instead, trace dataflow INTO a warnings sink:

Within each `FunctionDef` scope:
1. Build `local_literals: dict[str, set[str]]` — for every local var, the set of normalized token
   candidates assigned/`.append`/`.extend`-ed to it (reuse the existing `_collect_from_value` +
   `_normalize`, applied to ALL list/accumulator vars, not just `*warnings`).
2. Identify **sink-flowing locals** — a local Name that appears:
   (a) inside a `warnings=` kwarg value — directly, or wrapped (`tuple(VAR)`), or as a `BinOp` operand
       of the warnings value (e.g. `tuple(warnings) + tuple(dup_notes)`); OR
   (b) as the argument of `.extend(...)` / a `+`/`+=` concatenation **into** a `(^|_)warnings$` accumulator.
3. For each sink-flowing local, add its `local_literals[name]` to the discovered candidate set.

Keep it intra-function (no cross-function flow needed for these 5). This catches `dup_notes`/`warns`/
`note` precisely BECAUSE they demonstrably flow into a warnings sink — without matching incidental
`note`/`warns` vars that never reach `.warnings`.

## Verify (TDD)
1. **Fail-first unit test** `test_extract_traces_dup_notes_style_accumulator` — synthetic snippet:
   a local `dup_notes = []`; `dup_notes.append(f"cross_board_duplicate_symbol: {s} ...")`;
   `return EquityUniverse(..., warnings=tuple(warnings) + tuple(dup_notes))`. Assert the extractor now
   yields `cross_board_duplicate_symbol`. (Also a `warns`/`note = ...` variant.)
2. **Negative test** — a local `note = "debug: not a warning"` that is logged but NEVER flows into a
   `warnings=` sink → extractor must NOT surface it (proves we trace flow, not the name).
3. **Whole-repo guard stays green** — after the trace, `_discover_emitted_warning_tokens` over `vnfin/`
   includes all 5 previously-blind tokens, ALL still `_covered` by the tuple.
4. **Update the KNOWN-LIMITATION note** in `_warning_token_scan.py` — change it from "blind spot exists"
   to "def-use trace closes it (#192 landed)"; the existing #188 tests stay green.

## Interaction with #189 (batch note)
#189's `board_unavailable` is appended to the `warnings` list (already forward-discovered, no dep on
#192). #192 is purely additive — it makes the 5 EXISTING blind-spot tokens discoverable too. Order-
independent with #189/#190 except both edit `tests/test_docs_contract.py` (additive — integrator merges).

## Done
Extractor extended, 5 tokens discovered, unit + negative tests green, whole-repo guard green, limitation
note updated. Report the discovered-set delta + green suite. No `vnfin/` edit.
