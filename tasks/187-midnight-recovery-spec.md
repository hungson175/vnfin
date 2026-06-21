# #187 — recover the midnight-open placeholder bar (index D1), don't drop both

**Worktree:** `/home/hungson175/dev/vnfin-oss-wt-187` (branch `issue-187-midnight-recovery`, off master incl. #167 local commits). Work ONLY in this worktree. TDD: write failing tests FIRST, then the minimum fix, then refactor on green.

## Root cause (LIVE-CONFIRMED — do NOT re-probe; synthetic fixtures only)
`vps_index` (and any index-D1 UDF source) emits TWO same-date D1 rows: one at **VN-local 00:00 (+07)** and one at the real session time (e.g. 07:00 +07). The two rows are **identical in high/low/close/volume** and differ **only in `open`**. The 00:00 row is a synthetic midnight placeholder (its `open` == the prior session's close); the non-midnight row has the true open. Today `vnfin/sources/udf.py` treats them as a *conflicting* same-date pair and **poisons the whole date (drops BOTH)** → a real trading day vanishes.

## The fix (reviewer-gated decisions — all locked)
At the dedup site in `vnfin/sources/udf.py:_build_bars`, when a same-date conflict is about to be poisoned, FIRST test a precise **recovery signature**; if it matches, **keep the non-midnight row, drop the midnight row, and recover** (no poison, no threshold charge); otherwise fall through to the existing poison behavior UNCHANGED.

**Recovery signature (ALL three must hold):**
1. `(high, low, close, volume)` are IDENTICAL between the two rows, AND
2. `open` DIFFERS, AND
3. EXACTLY ONE of the two rows is at **VN-local 00:00:00** (computed on the VN tz, NOT naive UTC).

**Locked calls:**
- Keep the **NON-MIDNIGHT** row (the 00:00 row is the defect marker).
- New, distinct, never-silent warning token **`recovered_midnight_open_placeholder`** (this is a RECOVERY, not the identical-dedupe `deduped_duplicate_daily_index_bars`).
- General **index-D1** signature (gate on the existing `dedup_by_date` flag), NOT vps-only.
- **NO runtime "midnight open == prior session close" guard.** At the dedup site bars are still in PROVIDER order (the sort is AFTER the loop, `udf.py:372`), so prior-close is not reliably available — and it's unnecessary: because only `open` differs, keeping the non-midnight row is provably non-lossy regardless of the prior-close relationship. The `open == prior-close` fact is **TDD fixture DOCUMENTATION only**, never a runtime condition.

## Must-hold invariants (review against these, not just green)
- Fires ONLY on the exact 3-part signature. A genuine conflict (differs in H/L/C/V) → UNCHANGED poison+quarantine+threshold (#186 gate preserved). A same-date open-only diff where NEITHER row is VN-midnight → UNCHANGED poison (no recovery). Add an explicit regression for BOTH.
- The recovered date does **NOT** count toward the failover threshold (do not increment `bad_inrange`, do not add to `quarantined`/`poisoned`). Mirror the #162 identical-dedupe accounting: back out ONE `considered` increment for the dropped midnight row so it doesn't dilute the denominator.
- The identical 5-tuple same-date dup still dedupes to `deduped_duplicate_daily_index_bars` (unchanged).
- Equity / intraday (exact-timestamp key, `dedup_by_date == False`) is UNAFFECTED — recovery lives inside the `dedup_by_date` branch only. Add a regression: equity duplicate timestamp still poisons.
- Order-independent: recovery must work whether the midnight row arrives FIRST or SECOND in provider order. Test both.
- VN-tz pinning: a row at **17:00 UTC == 00:00 +07** IS the midnight row; a row at **00:00 UTC == 07:00 +07** is NOT. A naive-UTC implementation would misfire — pin this in a fixture.

## Exact implementation sketch (udf.py)
1. Add a module constant near `QUARANTINED_INVALID_BARS`:
   ```python
   RECOVERED_MIDNIGHT_OPEN_PLACEHOLDER = "recovered_midnight_open_placeholder"
   ```
2. In `_build_bars`, alongside `quarantined`/`poisoned` (around line 246), add `recovered: list[tuple[str, str]] = []`.
3. In the `if key in seen:` block, INSIDE `if dedup_by_date:`, AFTER the identical-OHLCV dedupe `continue` (current line 337) and BEFORE the poison block (current line 338), insert the recovery check:
   ```python
   prev_is_mid = (prev.time.hour, prev.time.minute, prev.time.second) == (0, 0, 0)
   this_is_mid = (tm.hour, tm.minute, tm.second) == (0, 0, 0)
   hlcv_identical = (prev.high, prev.low, prev.close, prev.volume) == (hp, lp, cp, vol)
   if hlcv_identical and prev.open != op and (prev_is_mid != this_is_mid):
       # #187: synthetic midnight-open placeholder — keep the non-midnight (real) row,
       # drop the midnight row. Provably non-lossy (only `open` differs). Recovery, not
       # a quality failure: not poisoned, not charged to the failover threshold.
       if this_is_mid:
           # current row is the placeholder -> keep the already-kept prev (real), drop this
           pass
       else:
           # current row is the real one -> replace the midnight prev (already in bars)
           bars = [b for b in bars if b is not prev]
           seen[key] = bar
           bars.append(bar)
       recovered.append((tm.date().isoformat(), "midnight-open placeholder dropped, real open kept"))
       considered -= 1  # the dropped placeholder must not dilute the failover denominator
       continue
   ```
   (`tm` and `prev.time` are already VN-tz aware from line 261's `.astimezone(VN_TZ)`, so `.hour/.minute/.second` ARE the VN-local clock — that satisfies "computed on VN tz, not naive UTC".)
4. Record `self._recovered = recovered` right next to `self._quarantined = quarantined` (current line 371).
5. Add `_recovery_warnings()` mirroring `_quarantine_warnings()`:
   ```python
   def _recovery_warnings(self) -> tuple[str, ...]:
       recovered = getattr(self, "_recovered", None)
       if not recovered:
           return ()
       seen_pairs: list[tuple[str, str]] = []
       for pair in recovered:
           if pair not in seen_pairs:
               seen_pairs.append(pair)
       detail = "; ".join(f"{label}: {reason}" for label, reason in seen_pairs)
       return (
           f"{RECOVERED_MIDNIGHT_OPEN_PLACEHOLDER}: recovered {len(recovered)} bar(s) — {detail}",
       )
   ```
6. Update the `PriceHistory(... warnings=...)` construction (line 170) to concatenate:
   `warnings=self._quarantine_warnings() + self._recovery_warnings(),`
   Keep the token PREFIX (text before the first `:`) stable = `recovered_midnight_open_placeholder`.

## #180 lockstep (33 → 34) — SAME change
- The token literal now lives in `vnfin/` (the module constant) — satisfies the code side.
- Add `"recovered_midnight_open_placeholder"` to `tests/test_docs_contract.py` `_WARNING_TOKENS_180` (currently 33 → 34).
- Add it to the doc side wherever sibling tokens are documented. GREP for `deduped_duplicate_daily_index_bars` across `skills/` and `docs/` and add the new token in the same table(s)/section(s) so the bidirectional guard `test_skill_warning_tokens_section_in_lockstep_with_code` stays GREEN. Read that test first to confirm exactly which doc file + section it scans.
- Add a `CHANGELOG.md` entry under the unreleased section (bug fix #187 + the new warning token).

## Public-API snapshot — FROZEN, do NOT regen
This change adds behavior + a warning string + a module constant. Run `tests/test_public_api_surface.py`: it MUST be green. The surface test is additive-tolerant; if the new module constant registers as an additive surface entry, that is ALLOWED and printed — do **NOT** edit/regen `tests/snapshots/public_api_v0_2_0.json`. (If it is not tracked, there is simply no surface diff.)

## TDD test matrix (synthetic UDF fixtures ONLY — no real provider rows)
Find the existing index/UDF dedup tests (grep for `deduped_duplicate_daily_index_bars`, `conflicting same-date`, `_DEDUPE_IDENTICAL_DUPLICATE_BARS`) and add these in the same file, matching the existing synthetic-payload fixture style. Use an index-D1 source (one that sets `_DEDUPE_IDENTICAL_DUPLICATE_BARS`, e.g. `VPSIndexSource`) with a stubbed HTTP layer. Write ALL of these to FAIL FIRST on the current code, then implement:
1. **Recovery, midnight FIRST** (epoch 17:00 UTC == 00:00 +07 placeholder, then real 07:00 +07): exactly ONE bar for the date, `open` == the REAL row's open, `warnings` contains `recovered_midnight_open_placeholder`, date NOT in any quarantine warning, no failover/raise.
2. **Recovery, real FIRST then midnight**: identical outcome (order-independent).
3. **Genuine conflict (H/L/C/V differ) still poisons**: UNCHANGED — date dropped, `conflicting same-date bars` quarantine token, charged to threshold. No recovery token.
4. **Open-only diff but NEITHER row at VN-midnight** (e.g. 07:00 and 09:00 +07): UNCHANGED poison (signature needs one midnight row). No recovery token.
5. **Identical 5-tuple dup still dedupes**: `deduped_duplicate_daily_index_bars`, no recovery token.
6. **Recovered date NOT charged to threshold**: craft a payload where charging the recovered date WOULD tip past the failover floor/fraction, but with recovery it serves — assert it serves (no `InvalidData`).
7. **VN-tz pinning**: assert the 17:00-UTC row is treated as midnight (recovery fires) and a 00:00-UTC (07:00 +07) row is NOT treated as midnight (so an open-only diff between 00:00-UTC and another non-midnight row poisons, proving the check is VN-tz not naive-UTC).
8. **Equity exact-timestamp unaffected**: an equity source (`dedup_by_date == False`) with a duplicate timestamp still poisons — recovery path never runs.
9. **#180 guard green at 34 tokens** (`test_docs_contract.py`).

## Scope guard (do NOT touch)
ONLY: `vnfin/sources/udf.py`, the index/UDF test file (add tests), `tests/test_docs_contract.py` (token tuple), the SKILL/docs token table(s), `CHANGELOG.md`. Do NOT touch `vnfin/indices/sources.py`, `vnfin/equities/*`, `vnfin/funds/*`, `tests/test_equities.py`, or the snapshot JSON — those belong to #167/#181 and must not collide.

## Done = all green in the worktree
Run the FULL suite from the worktree root: `python -m pytest -q`. All pass (incl. the new tests + the #180 guard at 34). Report: files changed, the test names added, the final `N passed` line, and confirmation the surface test is green WITHOUT regenerating the snapshot. Do NOT commit, push, close issues, or message anyone — return a summary to the orchestrator.
