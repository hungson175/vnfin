# #188 — forward-discovery hardening of the #180 warning-token guard (BUILD SPEC)

**Worktree:** branch off `master`. **TDD mandatory:** failing tests FIRST, then the extractor, then
green. **Design APPROVED** by `vnfin-oss-reviewer` (gate `/tmp/vnfin-188-gate.md`) — build to THIS spec.

## Scope guard — DO NOT cross
- **TEST-INFRASTRUCTURE ONLY.** Touch ONLY `tests/test_docs_contract.py` (and optionally a new
  `tests/` helper module). **NO change to any `vnfin/**` file.** No new warning token.
- `_WARNING_TOKENS_180` stays **exactly 34 entries** (do NOT add/remove tokens).
- Public-API snapshot `tests/snapshots/public_api_v0_2_0.json` is **FROZEN** — never edit/regen.
- The existing `test_skill_warning_tokens_section_in_lockstep_with_code` stays and stays green
  (you AUGMENT it with a new forward-discovery test; you do NOT replace it).

## The gap you are closing (why this matters)
`test_skill_warning_tokens_section_in_lockstep_with_code` iterates **only over the hardcoded
`_WARNING_TOKENS_180` tuple**, so a token a dev EMITS in `vnfin/` but never adds to the tuple is
INVISIBLE to the guard. That exact failure shipped 4 undocumented warnings historically. #188 makes
the guard **discover** the emitted token set straight from the code AST and assert it ⊆ documented —
so a new emission with no doc row goes red automatically. Net invariant triangle once this lands:
**code-emits ⊆ tuple ⊆ {SKILL table ∧ code-literal}**.

## Emission corpus — the scanner MUST find every one of these (verify in your tests)
String literals/constants/f-strings that flow into a `result.warnings` tuple. Inventory (file:line):
- **Shape A — literal in a `warnings=` kwarg / `warnings = (...)` assign:**
  `indices/sources.py:108` `("deduped_duplicate_daily_index_bars",)`; `indices/sources.py:228`
  `("weights_not_available: SSI group endpoint exposes membership only",)`; `indices/client.py:235`
  `("stitched_multi_source",) + tuple(warnings)`; `fundamentals/metric_api.py:614`
  `("mixed_source",) if len(src) > 1 else ()`; `client.py:192`, `macro/dbnomics.py:245`,
  `macro/imf.py:151`, `funds/fmarket.py:316` (multi-line `warnings = (` tuples).
- **Shape B — `.append(literal | f"…")` / `.extend(...)` to a local `warnings` list:**
  `liquidity.py:162` `"zero_liquidity: …"`; `indices/client.py:212` `f"stitched_segment: {year} …"`;
  `equities/sources.py:169` `warnings.extend(board_universe.warnings)` (pass-through — no literal).
- **Shape C — module/class CONSTANT resolved to a literal:** `client.py:41` `_TRAILING_ZERO_VOLUME_TAIL`;
  `_resample.py:43` `PARTIAL_PERIOD_TOKEN` (+ `RESAMPLED_FROM_D1`); `udf.py:26/36`
  `QUARANTINED_INVALID_BARS`/`RECOVERED_MIDNIGHT_OPEN_PLACEHOLDER`; `fmarket.py:65` `_NAV_END_GAP`;
  `liquidity.py:37` `_ESTIMATE_WARNING`; `dbnomics.py:89` `_SERIES_END_GAP`; `world_reference.py:70/71`
  `_PARTIAL_COVERAGE_TOKEN`/`_TRAILING_YEAR_TOKEN`; `world_reference.py` `_PREMIUM_NOTE`/`_ANNUAL_BASIS_NOTE`.
- **Shape D — `_*warnings()` helper RETURN flowing into `warnings=`:** `udf.py:183 _quarantine_warnings`,
  `udf.py:199 _recovery_warnings`, `indices/world_client.py:127 _substitution_warnings`,
  `equities/sources.py:183 _board_warnings`, `client.py:245 _coverage_warnings`,
  `gold/failover.py:204 _coverage_warnings`.
- **Shape E — f-string token forms (TWO sub-shapes — both REAL, both required):**
  - leading static constant text: `world_reference.py:138/140` `f"world_reference_gold_leg_{w}"` /
    `f"world_reference_fx_leg_{w}"`; `macro/client.py:455` `f"failover: {note}"`;
    `indices/client.py:212` `f"stitched_segment: {year} …"`.
  - **leading RESOLVED CONSTANT then `:` then dynamic** (the subtle one): `udf.py:196`
    `f"{QUARANTINED_INVALID_BARS}: dropped {len(quarantined)} — {detail}"`; `udf.py:213`
    `f"{RECOVERED_MIDNIGHT_OPEN_PLACEHOLDER}: recovered {len(recovered)} — {detail}"`;
    `world_reference.py:150` `f"{_PARTIAL_COVERAGE_TOKEN}: years not synthesized …"`;
    `world_reference.py:167` `f"{_TRAILING_YEAR_TOKEN}: the emitted year …"`.

**NOT a token — must be EXCLUDED:** `SourceAttempt(src.name, False, reason)` strings (the `reason`
field, not `.warnings`), and `def _warnings_reason(...)` (name ends in `reason`, not `warnings`) which
returns diagnostic strings. Your scan must not surface these.

## Extractor design
Add to `tests/test_docs_contract.py` (or a `tests/_warning_token_scan.py` helper imported by it):

1. `_extract_warning_tokens_from_source(src_text: str) -> set[str]` — **pure, takes source TEXT**
   (so unit tests feed synthetic snippets). `ast.parse(src_text)`, then a `NodeVisitor` that:
   - Builds a **name→literal map** from every `Assign`/`AnnAssign` with a single str-`Constant` value,
     at module, class, AND function scope (a flat dict is acceptable; collisions are vanishingly rare
     here — if you want, last-write-wins).
   - Collects **emission positions**: (i) any `keyword` arg named `warnings`; (ii) any
     `Assign`/`AugAssign`/`AnnAssign` whose target Name matches `r"(^|_)warnings$"`; (iii) any
     `Call` to `.append`/`.extend` whose receiver is a Name matching `r"(^|_)warnings$"`; (iv) any
     `Return` inside a `FunctionDef` whose name matches `r"_.*warnings$"`.
   - From each position, walks the value expression and extracts **candidate token strings** from:
     `Constant` str → its value; `Name` → resolved via the name→literal map (skip if unresolved);
     `JoinedStr` (f-string) → **build the static prefix** by walking `.values` in order and
     concatenating: a `Constant` str → its value; a `FormattedValue` whose `.value` is a `Name` that
     **resolves** to a str literal → the resolved literal; **STOP at the first `FormattedValue` that
     does NOT resolve** (a dynamic `{detail}`/`{len(...)}`/`{w}`). Non-str/unresolved values are
     skipped (pure pass-throughs like `tuple(hist.warnings)` yield nothing).
2. **Normalize** each candidate → token: `cand.split(":", 1)[0].strip()`. **Keep a trailing `_`**
   (the `*_leg_` family). Drop empties.
3. `_discover_emitted_warning_tokens(repo_root) -> dict[str, list[str]]` — walk `vnfin/**/*.py`, run
   the extractor per file, return `{token: [file:line-ish locations]}` (location for the failure msg;
   a filename is enough if line is awkward).

## Coverage rule — REVIEWER REFINEMENT (do NOT use blanket startswith)
A discovered normalized token `e` is "documented" iff there EXISTS a `t` in `_WARNING_TOKENS_180` s.t.:
```
def _covered(e: str, documented: tuple[str, ...]) -> bool:
    for t in documented:
        if t.endswith("_"):          # declared FAMILY prefix (e.g. world_reference_gold_leg_)
            if e.startswith(t):
                return True
        else:                        # plain token → require EXACT match
            if e == t:
                return True
    return False
```
Rationale: blanket `startswith` would let a documented SHORT token silently cover an undocumented
LONGER emission — the exact false-negative we are closing. So `partial_coverage` does NOT cover a
hypothetical `partial_coverage_xyz` (must be flagged); only the `_`-suffixed leg families prefix-cover.

## Allowlist seam (keep — not YAGNI)
`_NON_TOKEN_WARNING_LITERALS: frozenset[str] = frozenset()` (initially empty). Subtract it from the
discovered set before the coverage check. Any future deliberate non-token literal in a `warnings=`
position goes here **with a `# reason:` comment**, never by weakening the matcher.

## Tests (all fail-first, then implement)
1. **Per-shape extractor unit tests A–E** — feed `_extract_warning_tokens_from_source` a synthetic
   snippet for EACH shape (incl. BOTH Shape-E sub-shapes: leading-constant `f"{TOK}: {x}"` AND
   leading-text `f"tok_{x}"`), assert the exact expected token set. The Shape-E leading-constant test
   is the highest-value one (proves the extractor doesn't silently miss the quarantine/recovery family).
2. **Exclusion test** — a snippet with a `SourceAttempt(..., reason)` literal and a `_warnings_reason`
   def → extractor returns ∅ (proves non-token positions are excluded).
3. **Coverage-rule distinction test** — assert `_covered("partial_coverage_xyz", TOKENS)` is False
   (exact-match token does NOT prefix-absorb) AND `_covered("world_reference_gold_leg_2024", TOKENS)`
   is True (family prefix DOES). This pins the reviewer's refinement.
4. **Whole-repo forward-discovery guard** `test_emitted_warning_tokens_are_all_documented` — discover
   over real `vnfin/`, subtract the allowlist, assert EVERY discovered token is `_covered` by
   `_WARNING_TOKENS_180`; on failure list `token @ location`. Must be GREEN on the current tree
   (the tuple is complete after #187 — if it's red, your extractor surfaced something real or has a bug;
   reconcile, do NOT silence by editing the tuple).
5. **Meta-test (proves the guard CATCHES a gap)** — build a COPY of `_WARNING_TOKENS_180` with one
   real emitted plain token removed (e.g. `zero_liquidity`), run discovery + `_covered` against the
   reduced copy, assert `zero_liquidity` is flagged undocumented. (Do NOT mutate the real tuple.)

## Done = all green in the worktree
`python -m pytest -q` → all pass (incl. the new tests). Report: files changed, the new test names, the
final `N passed` line, confirmation that (a) `_WARNING_TOKENS_180` is still 34, (b) no `vnfin/**` file
changed, (c) the snapshot was NOT regenerated. Do NOT commit/push/close/message anyone — return a
summary to the orchestrator.
