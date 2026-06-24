# #194 BUILD SPEC — port the #186 quarantine to the Fmarket NAV parser (TDD, RED-first)

**Authority:** design note `tasks/194-nav-quarantine-design.md` (`1408f08`) + the APPROVED gate
`~/tools/vnfin-oss-reviewer/reviews/gate-202606241535-issue194-design-note.md`. All 3 rulings + 5 binding
correctness notes below are BINDING. Read the design note for rationale; THIS file is the build contract.

**Scope = exactly one source file + its tests + the doc/token lockstep:**
`vnfin/funds/fmarket.py` · `tests/test_funds.py` (the `nav_history` tests live here) ·
`tests/test_docs_contract.py` · `skills/vnfin/SKILL.md` · `CHANGELOG`. **ONE commit.**

**Existing synthetic-injection pattern in `tests/test_funds.py` (mirror it — no live calls, no real rows):**
`_nav_history_payload(rows=[...])` builds the upstream JSON `data` array; `_src(text)` =
`FmarketFundSource(http_get=_capture_get(text))`; tests call `_src(payload).nav_history(FAKE_ID_A)`. Each
NAV row is a dict `{"id":N, "createdAt":<ms>, "nav":<float>, "navDate":"YYYY-MM-DD", "productId":FAKE_ID_A}`.
The current #158 conflict test (`test_nav_history_*`, ~`:490-520`) asserts `pytest.raises(InvalidData)` on a
conflicting navDate — that test INVERTS under this change (conflict now serves-with-warning unless
above-threshold); update/replace it and note the intended contract change.

Runner: `.venv/bin/python -m pytest`. **No VNStock. Synthetic fixtures only (no real issuer rows). Do NOT
run `scripts/dump_api_surface.py`; do NOT regen `tests/snapshots/public_api_v0_2_0.json`.**

---

## The bug (current behavior)

`vnfin/funds/fmarket.py :: nav_history()` parse loop (`:355-369`): a single conflicting `navDate`
(same date, two DIFFERENT NAV values) raises `InvalidData` and aborts the fund's ENTIRE series.
Repro: `vnfin.funds.source().nav_history(21)` (VFF) → `InvalidData: fmarket: conflicting navDate
2018-07-31 ... (15091.0 vs 15120.0)`. ~21/65 VN funds lose all NAV over one bad date.

The window-filter (`:342-343`, skip out-of-window rows), productId guard (`:349-354`), and the
identical-value dedup keep-first + `deduped_duplicate_nav_rows` token are CORRECT — keep them.

## The fix — quarantine the conflicting date (mirror #186), never abort, never average

Replace the `raise InvalidData` conflict branch with a quarantine-the-date branch + a threshold verdict +
a never-silent warning. Behavior contract (BINDING):

- **Q1 — DROP the conflicting date entirely.** Keep neither value (never pick, never average). The date is
  absent from `points`.
- **Q3 — threshold:** reuse `_QUARANTINE_FRACTION = 0.10` and `_QUARANTINE_ABS_FLOOR = 3` UNCHANGED (the
  #186 values; import from `vnfin.sources.udf` OR define identical module-level constants in `fmarket.py` —
  do NOT invent funds-specific numbers). **Count each conflicting DATE once** (NOT #186's `+2` rows).
  `considered` = number of DISTINCT in-window dates (kept + quarantined; identical-value dups excluded).
  Raise `InvalidData` (systematically broken) iff `considered and len(poisoned) > max(_QUARANTINE_ABS_FLOOR,
  _QUARANTINE_FRACTION * considered)`. Message NAMES the ratio: `{len(poisoned)}/{considered}`.
- **Note 1 — conflict beats dedup on the same date:** a date that has BOTH an identical-value dup AND a
  conflicting value is QUARANTINED (not silently deduped); its earlier dup occurrences must NOT inflate the
  `deduped` count (they belong to a now-quarantined date).
- **Note 2 — never average/pick** (already covered by Q1; assert it in tests).
- **Note 3 — quarantine runs BEFORE the #172 empty/stale handling** (see ORDER below).

### Binding ORDER inside `nav_history` (this is the one subtle part)

```
for r in rows:
    ... navDate parse + max_navdate(#172) + window-filter(:342-343) + productId guard(:349-354) ...  # UNCHANGED
    point = self._parse_nav_point(r)
    d = point.date
    if d in poisoned:
        continue                              # date already quarantined → ignore further rows (counted once)
    if d in seen:
        if point.nav == seen[d]:
            dedup_count[d] = dedup_count.get(d, 0) + 1     # identical-value dup → keep-first (#158/#162)
            continue
        # CONFLICT (#194): quarantine the date — conflict beats dedup, never pick, never average
        poisoned.add(d)
        conflict_dates.append(d.isoformat())
        seen.pop(d, None)
        dedup_count.pop(d, None)              # Note 1: a poisoned date's earlier dups do NOT count as dedup
        continue
    seen[d] = point.nav
    points.append(point)

if poisoned:                                  # drop the previously-kept point for any poisoned date (#186 :410-414)
    points = [p for p in points if p.date not in poisoned]
points.sort(key=lambda p: p.date)

# (A) QUARANTINE VERDICT — runs BEFORE the #172 block (Note 3). Above-threshold ⇒ InvalidData.
considered = len(points) + len(poisoned)      # distinct in-window dates (identical dups excluded)
if considered and len(poisoned) > max(_QUARANTINE_ABS_FLOOR, _QUARANTINE_FRACTION * considered):
    raise InvalidData(
        f"fmarket: {len(poisoned)}/{considered} in-window navDate(s) conflict "
        f"(> max(floor={_QUARANTINE_ABS_FLOOR}, {int(_QUARANTINE_FRACTION*100)}%)) — "
        f"source systematically broken")

# (B) #172 empty/stale handling — UNCHANGED. A window EMPTY after a SUB-threshold quarantine still
#     yields the existing StaleData/EmptyData (Note 3, case 8).
if not points:
    ... existing #172 StaleData (max_navdate < lo) / EmptyData block, UNCHANGED ...

# (C) warnings: dedup FIRST (unchanged convention), then the NEW quarantine token, then nav_end_gap last.
deduped = sum(dedup_count.values())
warnings: tuple[str, ...] = ()
if deduped:
    warnings += (f"deduped_duplicate_nav_rows: {deduped} duplicate navDate row(s) with identical NAV",)
if poisoned:
    warnings += (
        f"{QUARANTINED_CONFLICTING_NAVDATES}: dropped {len(poisoned)} conflicting navDate(s) — "
        f"{', '.join(sorted(conflict_dates))}",
    )
warnings += _nav_end_gap_warning(points, hi, _today())
return NavHistory(..., warnings=warnings)     # all other NavHistory fields UNCHANGED
```

Why order (A) before (B): an above-threshold all-conflict window must raise `InvalidData` (systematically
broken), NOT `EmptyData`. A sub-threshold all-conflict tiny window (≤3 conflicts, nothing left) falls
through (A) and is handled by the existing (B) #172 block — that is the intended case-8 behavior.

## Token lockstep — SAME commit (#180 doc↔code + #188 forward-scanner), 47 → 48

1. `vnfin/funds/fmarket.py`: module constant beside `_NAV_END_GAP` (`:66`):
   `QUARANTINED_CONFLICTING_NAVDATES = "quarantined_conflicting_navdates"`. Emit it ONLY as the sink
   f-string in (C) above (the #188 anchor — a quoted literal at a `warnings += (...)` site).
2. `tests/test_docs_contract.py`: add `"quarantined_conflicting_navdates"` to `_WARNING_TOKENS_180`
   (tuple 47 → 48). Run the docs-contract suite and satisfy BOTH #180 (doc↔code bijection) and #188
   (forward-scanner: code-emitted ⊆ documented). If any Shape-E/scanner fixture enumerates tokens, update
   per the test's failure — do not guess; let the test drive it.
3. `skills/vnfin/SKILL.md`: add a warning-token table row (mirror the `deduped_duplicate_nav_rows` /
   `nav_end_gap` rows): `` `quarantined_conflicting_navdates` `` | `funds.nav_history` | "Same-date NAV
   conflict(s) quarantined — two different NAV values for one navDate; the date is dropped and the rest of
   the series is served." | #194.
4. `CHANGELOG`: a behavior-change entry — `funds.nav_history` no longer aborts the whole series on a single
   conflicting navDate; it quarantines the conflicting date(s), serves the rest, and emits
   `quarantined_conflicting_navdates`; a systematically-conflicting feed still raises `InvalidData`.

## Snapshot / surface — NO change

`NavHistory.warnings: tuple[str, ...] = ()` already exists (`vnfin/funds/models.py:97`, defaulted) and is
already in the FROZEN `tests/snapshots/public_api_v0_2_0.json`. Only a failure MODE changes (raise →
served+warning). Do NOT touch the snapshot; the surface test stays additive-green.

---

## TDD test matrix — 8 cases, RED-first (synthetic fixtures, offline)

Locate the existing `nav_history` tests (likely `tests/test_funds_fmarket.py`) and follow their
synthetic-row fixture pattern (build the upstream JSON `data` array of NAV rows; inject via the existing
http stub/recorder — NO live calls, NO real issuer rows). For EACH new test, **verify it is RED on the
current `master`** (the conflict-raise + missing token make cases 1, 3-low, 5, 6, 7 fail) before
implementing — report the red-first evidence (the exact assertion/exception each test fails on pre-fix).

1. **One conflicting navDate** → returns `NavHistory`; the conflicting date is ABSENT from `points`; the
   other dates are present; `result.warnings` contains a `quarantined_conflicting_navdates:` token naming
   the date; **NOT** `InvalidData`. (primary fail-first — currently raises)
2. **Systematically-conflicting** → e.g. 5 conflicting dates + 3 clean (`considered=8`, `5 > max(3,0.8)=3`)
   → still raises `InvalidData`, message contains `5/8` and "systematically broken".
3. **Threshold boundary (short series, floor dominates):**
   - 3 conflicting dates + 4 clean (`poisoned=3, considered=7`): `3 > max(3,0.7)=3` is False → SERVES 4
     points + warning lists the 3 dropped dates.
   - 4 conflicting dates + 4 clean (`poisoned=4, considered=8`): `4 > max(3,0.8)=3` → RAISES. Pins floor=3.
4. **Identical-value duplicate (regression, behavior UNCHANGED)** → same date, same NAV → keep-first, emits
   `deduped_duplicate_nav_rows`, NO quarantine token, the date is PRESENT in points.
5. **Never-averages** → conflict (15091.0 vs 15120.0) → NO point in the result equals or is near the mean
   15105.5 for that date; the date is simply absent. (degrade-not-fabricate)
6. **Two distinct conflicting dates UNDER threshold (long series)** → e.g. 2 conflicts + many clean → both
   dropped, the rest served, the warning lists BOTH dropped dates (sorted).
7. **Conflict beats dedup on the same date (Note 1)** → one date has an identical dup AND a conflicting row
   → the date is QUARANTINED (in the quarantine token, ABSENT from points), and it does NOT inflate the
   `deduped_duplicate_nav_rows` count (assert the dedup token is absent OR its count excludes this date).
8. **Quarantine before #172 empty/stale (Note 3)** → a window whose ONLY in-window dates all conflict,
   SUB-threshold (e.g. 2 conflicting dates, 0 clean → `poisoned=2 ≤ floor 3`, `points=[]`) → falls through
   the quarantine verdict and yields the existing `EmptyData` (or `StaleData` if `max_navdate < lo`) — NOT
   a `NavHistory`, NOT the systematically-broken `InvalidData`.

### Existing tests that CHANGE vs STAY (verify each — the suite is RED until the inversions are updated)

**INVERT (currently assert `pytest.raises(InvalidData, match="conflicting navDate")` — must be rewritten
to the new contract; note the intended behavior change in a comment):**
- `tests/test_funds.py::test_nav_history_duplicate_nav_date_raises_invalid` (`:888`) — rows = one
  conflicting date (2024-01-02: 10100 vs 10300) + one clean (2024-01-03). New behavior: `poisoned=1,
  considered=2`, `1 > max(3,0.2)=3` is False → **SERVES `[2024-01-03]`**, 2024-01-02 ABSENT, warnings
  carries `quarantined_conflicting_navdates:` naming 2024-01-02. NOT `InvalidData`.
- `tests/test_funds.py::test_nav_history_in_window_conflicting_duplicate_fatal` (`:1953`) — rows = ONE
  conflicting date (2024-04-04: 100 vs 101), no clean rows. New behavior: `poisoned=1, considered=1,
  points=[]`, sub-threshold → falls through the quarantine verdict to the existing #172 block → **raises
  `EmptyData`** (max_navdate=2024-04-04 ≥ lo → plain EmptyData "no NAV history … in range"). NOT
  `InvalidData`. (This IS matrix case 8 — you may fold case 8 into this test or keep both.)

**MUST STAY GREEN (do NOT break — your change is conditional on `poisoned`/conflict, so these are
untouched):**
- `test_nav_history_in_window_identical_duplicate_deduped_with_warning` (`:1961`) — identical-value dup →
  keep-first + `deduped_duplicate_nav_rows`, NO quarantine token (= matrix case 4).
- `test_nav_history_out_of_window_duplicate_not_fatal` (`:1945`) — out-of-window dup skipped pre-guard.
- `test_nav_history_no_duplicates_has_no_dedupe_warning` (`:1975`) — clean series → `warnings == ()`.
- `test_nav_history_end_gap_coexists_with_dedup_dedup_first` (`:2363`) — asserts `len(warnings)==2`,
  `warnings[0]`=dedup, `warnings[1]`=`nav_end_gap:`. NO conflict here ⇒ `poisoned` empty ⇒ NO new token ⇒
  stays len-2. Your ordering (dedup → quarantine-IF-poisoned → nav_end_gap) MUST preserve this.
- The whole #172 stale/empty block (`:2005-2075`) — quarantine runs before it but only DROPS poisoned
  dates; a non-conflicting window reaches #172 unchanged.

Plus confirm the FULL suite stays green (no collateral break to existing `nav_history` / #144 / #158 /
#162 / #172 tests).

## Acceptance (green MERGED tree)

- `.venv/bin/python -m pytest` FULL suite green (all prior + the 8 new). Report pass count.
- `tests/test_docs_contract.py` green: #180 bijection + #188 forward-scanner; tuple = 48; new token in
  `_WARNING_TOKENS_180` AND in SKILL.md.
- Snapshot `public_api_v0_2_0.json` UNMODIFIED (did NOT run `dump_api_surface.py`).
- `grep -rn "raise InvalidData" vnfin/funds/fmarket.py` no longer fires on a single conflicting navDate
  (the only conflict-related raise is the systematically-broken THRESHOLD raise).
- Zero VNStock; no secrets; synthetic fixtures only.

**Return a diff + summary (files, new tests with their red-first evidence, pass count, token-tuple delta).
Do NOT push, do NOT close the issue, do NOT message the reviewer.** The main agent integrates, runs the
gates on the merged tree, adversarially verifies, and routes to Codex×2.
