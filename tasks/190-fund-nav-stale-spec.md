# #190 — list-level `fund_nav_stale` warning on `FundList` (BUILD SPEC)

**GATE: APPROVED** (reviewer batch gate 2026-06-21, `/tmp/vnfin-batch-gate-w1.md`). All decisions LOCKED.
Follow-up to #181 (`Fund.nav_as_of` already shipped). TDD mandatory; fail-first; synthetic fixtures only.

## Problem
`FmarketFundSource.list_funds()` (`vnfin/funds/fmarket.py:164`, builds `FundList(...)` at `:213`) returns
each fund's `nav_as_of` (`Fund.nav_as_of: Optional[date]`, `models.py:39`) but never tells the caller a
fund's NAV is stale — silent staleness, the blindness #172/#173 fixed for series results.

## Change (LOCKED) — mirror the proven `_nav_end_gap_warning` clock seam EXACTLY
`fmarket.py` already has the pattern: `_nav_end_gap_warning(points, to_date, today)` (`:743`) is a PURE
helper taking an **injected** `today` ("MUST NOT call now()/today()"); `nav_history` supplies it via
`_today()` **internally** (`:323`) — NO public param. Do the same:

1. New module constant `_FUND_NAV_STALE_DAYS = 7` (CALENDAR days — confirmed; no holiday-calendar dep).
2. New pure helper `_fund_nav_stale_warning(funds, today, *, threshold_days=_FUND_NAV_STALE_DAYS) -> tuple[str, ...]`:
   - For each `Fund` with `nav_as_of is not None`: `gap = (today - nav_as_of).days`; stale iff `gap > threshold_days`.
   - **Boundary:** `gap == threshold_days` → NOT stale; `gap == threshold_days + 1` → stale.
   - **`nav_as_of is None` → NEVER flagged** (unknown ≠ stale; never invent a date).
   - ≥1 stale → return `(f"fund_nav_stale: {detail}",)`; else `()`.
   - **MUST NOT** call `now()`/`date.today()` — `today` is the injected reference (deterministic tests).
3. `list_funds()` appends at `FundList` construction (`:213` area):
   `warnings = warnings + _fund_nav_stale_warning(funds, _today())`.
   **NO `list_funds` signature change** → `tests/snapshots/public_api_v0_2_0.json` stays FROZEN.

## Token + detail format (LOCKED)
    fund_nav_stale: {N} fund(s) NAV older than {threshold_days}d as of {today}: CODE@YYYY-MM-DD[, ...][, +M more]
- List-level (ONE token on `FundList.warnings`). Detail enumerates stale fund codes + their `nav_as_of`,
  **capped at K=5 codes + `+M more`** (confirmed) so the detail stays bounded on a wholesale outage.
- **Leak-safe:** built only from fund codes + dates — no exception trail, no secrets.

## Required doc/guard updates (SAME change)
- `tests/test_docs_contract.py`: add `fund_nav_stale` to `_WARNING_TOKENS_180` (**+1**, **append at the END
  of the tuple**). Do NOT assert a magic count.
- `skills/vnfin/SKILL.md` "## Warning tokens": new row (append as the LAST row).
- `skills/vnfin/reference/domains.md` funds entry: list the new token if it enumerates tokens.
- `CHANGELOG.md` `[Unreleased]`: `fund_nav_stale` disclosure under `### Added`.
- #188 forward-discovery: the token is added to a var named `warnings` (Shape B-ish concat) AND emitted by
  `_fund_nav_stale_warning` (Shape D `_*warning` helper return) → forward-discovered once in the tuple; NO
  dep on #192.

## Tests (TDD, fail-first; `tests/test_funds*.py` — call `_fund_nav_stale_warning` directly with explicit `today`)
1. `test_fund_nav_stale_warns_when_a_fund_exceeds_threshold` — one fund `nav_as_of = today-8`, others
   fresh → token present, detail names the stale code@date.
2. `test_fund_nav_stale_silent_when_all_fresh` — all within threshold → `()`.
3. `test_fund_nav_stale_boundary` — fund at exactly `today-7` NOT stale; `today-8` stale (locks boundary).
4. `test_fund_nav_stale_ignores_none_nav_as_of` — fund with `nav_as_of=None` never flagged.
5. `test_fund_nav_stale_detail_caps_enumeration` — >5 stale funds → detail shows 5 codes + `+M more`.
6. `test_fund_nav_stale_helper_never_calls_wall_clock` — two different injected `today` values yield
   different verdicts on the same funds (proves no baked-in clock).

## Files touched
`vnfin/funds/fmarket.py` (const + helper + call), `tests/test_funds*.py`, `tests/test_docs_contract.py`
(tuple +1), `skills/vnfin/SKILL.md`, `skills/vnfin/reference/domains.md`, `CHANGELOG.md`. No new module,
NO snapshot change, NO signature change.
