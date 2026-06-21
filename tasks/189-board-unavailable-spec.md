# #189 — `board_unavailable` skip-and-warn for the equities all-boards merge (BUILD SPEC)

**GATE: APPROVED** (reviewer batch gate 2026-06-21, `/tmp/vnfin-batch-gate-w1.md`). All decisions LOCKED
below. TDD mandatory (Red→Green→Refactor); fail-first regression per behavior; synthetic fixtures only.

## Problem (real availability gap)
`vnfin.equities.universe(exchange=None)` → `SsiIboardUniverseSource._merged_universe()`
(`vnfin/equities/sources.py:152-178`) iterates `_MERGE_ORDER = ("HOSE","HNX","UPCOM")` and calls
`self._fetch_board(board)` at **line 158 with NO try/except**. One board down → its `SourceError`
(`SourceUnavailable`/`EmptyData`/`InvalidData`) propagates and aborts the WHOLE merge — the caller gets
nothing even though the other two boards succeeded. Wrong failure mode for an all-boards listing.

## Change (LOCKED) — skip-and-warn on PARTIAL failure, RAISE on TOTAL failure (merge-path ONLY)
Wrap the per-board fetch in `_merged_universe()` in `try/except SourceError`:
- **Success:** unchanged (merge securities + keep-first dedup + `warnings.extend(board_universe.warnings)`).
- **`SourceError`:** append a `board_unavailable` token to the **`warnings` list** (`sources.py:155` — the
  list literally named `warnings`, **NOT `dup_notes`** — required: makes the token #188-forward-discovered
  via Shape B, sidesteps the #192 blind spot), then `continue` to the next board.
- **TOTAL failure (all 3 boards raised → securities empty AND ≥1 board failed):** **RE-RAISE the LAST
  `SourceError`** (preserves the concrete cause). Do NOT return a near-silent empty universe.
- **Single-board path UNCHANGED:** `universe(exchange="HNX")` → `_fetch_board` directly; on failure STILL
  raises (caller asked for exactly that board). `board_unavailable` is merge-only.
- A failed board contributes ONLY `board_unavailable` (its 3 honest-gap tokens come from inside a
  successful `_fetch_board` return, so a skipped board emits none of them).

## Token + format (LOCKED)
    board_unavailable: {board} — fetch skipped ({ExcType}): {reason}
- `{ExcType}` = `type(exc).__name__`; `{reason}` = `str(exc)`. Keep terse (no payload dump).
- **Leak-safe:** single-board LEAF error, not an aggregating `AllSourcesFailed` → no multi-source trail;
  transport errors are key-redacted upstream. INCLUDE `{reason}` (ruled YES).

## Required doc/guard updates (SAME change)
- `tests/test_docs_contract.py`: add `board_unavailable` to `_WARNING_TOKENS_180` (**34→35**, **append at
  the END of the tuple** to minimize the #189-vs-#190 merge conflict). Do NOT assert a magic count.
- `skills/vnfin/SKILL.md` "## Warning tokens" table: new row (append as the LAST row).
- `skills/vnfin/reference/domains.md` equities entry: list the new token if it enumerates tokens.
- `CHANGELOG.md` `[Unreleased]`: partial-availability merge no longer aborts (own bullet under `### Fixed`/`### Changed`).
- #188 forward guard auto-covers it once it's in the tuple (no extra forward test needed).

## Tests (TDD, fail-first; `tests/test_equities.py`, `_board_router()` + `_raising(exc)` fixtures)
1. `test_exchange_none_skips_unavailable_board_and_warns` — HNX `_raising(SourceUnavailable)`, HOSE+UPCOM
   payloads → NO raise; `res.board=="ALL"`; HOSE+UPCOM securities present; `board_unavailable: HNX` in
   `res.warnings`; HNX's 3 honest-gap tokens ABSENT.
2. `test_exchange_none_all_boards_unavailable_raises` — all 3 raise → RAISES (re-raise last SourceError),
   NOT an empty universe.
3. `test_single_board_unavailable_still_raises` — `exchange="HNX"` raising → still raises.
4. `test_board_unavailable_token_format_stable` — prefix `board_unavailable:` + `{board}` + `({ExcType})`.
5. Existing merge tests stay green (`test_exchange_none_merges_all_three_boards`,
   `test_exchange_none_no_cross_board_dup_has_no_dup_warning`).

## Files touched
`vnfin/equities/sources.py` (merge try/except + token), `tests/test_equities.py`,
`tests/test_docs_contract.py` (tuple 34→35), `skills/vnfin/SKILL.md`, `skills/vnfin/reference/domains.md`,
`CHANGELOG.md`. No new module, NO snapshot change (warning strings aren't public surface).
