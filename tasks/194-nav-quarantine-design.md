# #194 DESIGN NOTE — port the #186 quarantine to the Fmarket NAV parser

**Issue:** `vnfin.funds.source().nav_history(product_id)` raises `InvalidData` and aborts a fund's
ENTIRE NAV series on a SINGLE conflicting `navDate` (same date, two different NAV values).
Repro: product 21 (VFF) → `InvalidData: fmarket: conflicting navDate 2018-07-31 ... (15091.0 vs
15120.0)`. Reporter says ~21/65 VN funds are affected (VFF, VEOF, VESAF, SSISCA, VFMVF1/4, MAFBAL,
MAFEQI, VCBFFIF/TBF/BCF, BVPF, KSIF, VBIF, LPLF, ABEF, LHFCF, USIF, MBBOND, SSIBF, VFMVFC, …).

**Disposition (reviewer triage, ACCEPTED):** mirror the #186 VN-Index quarantine — quarantine the
conflicting date, emit a never-silent warning, return the rest; keep the threshold guard so a
systematically-broken feed still fails over; **never average**.

This note answers the 3 design-gate questions, specifies the surgical change, the token lockstep,
the snapshot caveat, and the TDD test matrix. **No code until this note is gated.**

---

## Current behavior (the target seam)

`vnfin/funds/fmarket.py :: nav_history()` (parse loop `:329-369`). Per row, in order:
parse navDate → track `max_navdate` (#172) → **window-filter: skip out-of-window rows** (`:342-343`)
→ productId guard (#21) → `_parse_nav_point` → dup/conflict guard (`:360-367`):

```python
if point.date in seen:
    if point.nav != seen[point.date]:
        raise InvalidData(f"fmarket: conflicting navDate {point.date.isoformat()} ...")  # ← #194 bug
    deduped += 1            # identical-value dup → keep-first (#158/#162)
    continue
seen[point.date] = point.nav
points.append(point)
```

Two things are already CORRECT and **must not change**: (a) the conflict check is **post-window-filter**
(only in-window dates are judged — the `0.10/floor` threshold inherits #186's "in-range only" semantics
for free); (b) the identical-value dup path keep-firsts and emits `deduped_duplicate_nav_rows`
(`:386-390`). The ONLY change is: the `raise` branch becomes a quarantine-the-date branch.

## The #186 template (what we are porting — `vnfin/sources/udf.py`)

- Constants (`:44-45`): `_QUARANTINE_FRACTION = 0.10`, `_QUARANTINE_ABS_FLOOR = 3`.
- Conflict (`:399-405`): poison the date key, drop BOTH colliding bars, `bad_inrange += 2`. Never picks,
  **never averages** (no mean/median anywhere).
- Identical dup (`:353-367`): keep-first, `considered -= 1` (a dup must not dilute the denominator).
- `considered` (`:300`, `-=1` at `:366/:397`) = count of DISTINCT in-range observations (served-or-bad).
- Threshold (`:423-430`): `if considered and bad_inrange > max(_QUARANTINE_ABS_FLOOR,
  _QUARANTINE_FRACTION * considered): raise InvalidData("... source systematically broken")`.
- Token (`:26`) `QUARANTINED_INVALID_BARS = "quarantined_invalid_bars"`; sink helper
  `_quarantine_warnings()` (`:183-197`) → `f"{QUARANTINED_INVALID_BARS}: dropped {n} bar(s) — {detail}"`.

---

## Design-gate question 1 — keep-policy → **DROP the conflicting date** (mirror #186)

**Recommendation: DROP the date entirely** (keep neither value), exactly like #186 — not the reporter's
keep-first/keep-last.

*Why:* (1) a NAV is a precise money-per-unit figure; when two sources disagree we cannot know which is
right, so **serving either silently is a wrong-data risk** (the cardinal sin), whereas a one-date gap is
honest and the consumer can interpolate it; (2) keep-first/last would be a *silent* pick — it leaves no
trace that the date was contested; the quarantine+warning is never-silent; (3) consistency: indices and
NAV then behave identically on a same-date conflict (drop + disclose), one mental model across the lib.

*Alternative (rejected):* keep-first/last — silently picks a possibly-wrong NAV; violates degrade-not-
fabricate. Only revisit if a consumer specifically needs a populated point over a correct one (none asked).

## Design-gate question 2 — warning token → **NEW token `quarantined_conflicting_navdates`**

**Recommendation: a NEW funds-domain token**, e.g. `quarantined_conflicting_navdates`. I am
**respectfully diverging from the triage's preliminary lean** (reuse `quarantined_invalid_bars` as one
cross-domain token) — this is the one genuinely open call for the gate.

*Why a new token, not reuse:*
- The existing token literally says **`..._bars`**; `NavHistory` has **`points`, not bars** — emitting a
  "bars" token on a bar-less NAV result is a name/domain mismatch (the kind of honesty wart this gate
  blocks). Its documented meaning (`skills/vnfin/SKILL.md:131`) is **OHLC-specific** ("OHLC-invariant,
  non-positive/non-finite, bad volume, duplicate timestamp") — reuse forces broadening an OHLC contract
  to cover a date-value collision.
- The funds domain already has a parallel token family the new token slots into:
  `deduped_duplicate_nav_rows`, `nav_end_gap`, `fund_nav_stale`, `fund_missing_fees`,
  `fund_partial_holdings`. A conflict-quarantine token belongs there; the reporter themselves suggested
  `conflicting_navdate`. The `quarantined_` prefix keeps continuity with the #186 quarantine vocabulary.
- Cost is trivial and fully gated: tuple **47 → 48**, one SKILL.md row, a module constant + the sink
  literal — the #180 lockstep + #188 forward-scanner enforce it in the same commit either way.

*Alternative (reviewer's lean):* reuse `quarantined_invalid_bars` — keeps tuple at 47 and gives ONE
cross-domain "quarantine happened" signal, BUT requires broadening the SKILL.md row's scope+meaning to
`prices.history` / `index_history` / `funds.nav_history` and tolerating the "bars" name on a NAV result.
**Gate, please rule.** (Either choice obeys lockstep; I will implement whichever you pick.)

Shorter name option if the gate prefers brevity: `conflicting_navdates` (matches the existing raise
message vocabulary). I lean to the `quarantined_`-prefixed form for cross-domain pattern continuity.

## Design-gate question 3 — threshold constants → **reuse `0.10` / floor `3`, but count each conflicting DATE once**

**Recommendation: reuse `_QUARANTINE_FRACTION = 0.10` and `_QUARANTINE_ABS_FLOOR = 3` UNCHANGED**
(import or mirror #186's values — do not invent funds-specific magic numbers), **with a deliberate,
documented counting adaptation: a conflicting date counts as ONE bad unit, not #186's `+2`.**

*Why this solves the reviewer's short-series worry without a magic floor:* the gate question worried that
short series (new funds / sparse reporters; the repro dates are month-ends though the parser is framed as
daily, so cadence varies by issuer) let the abs floor dominate. With #186's `+2`-per-conflict charge, a
SHORT fund with just 2 conflicting dates would hit `bad=4 > floor=3` and still abort — re-creating the
bug at a higher threshold. The clean fix is to make the bad-unit the **date** (the natural unit of NAV
corruption: "this date can't be trusted" is ONE bad date, regardless of how many rows collided on it),
not two physical rows. Then:

- `considered` = number of DISTINCT in-window dates examined (kept + quarantined; identical-value dups
  excluded, exactly as #186 backs them out of the denominator).
- `bad = len(poisoned)` = number of distinct quarantined dates.
- `if considered and bad > max(_QUARANTINE_ABS_FLOOR, _QUARANTINE_FRACTION * considered): raise`.

Consequence: **any fund with ≤ 3 conflicting dates always serves** (floor 3), and a long feed needs
> 10 % of its dates conflicting to abort — VFF's 2 conflicts serve regardless of series length, while a
genuinely-broken feed still fails over. This keeps the constants identical to #186 (the triage's stated
preference) AND makes short/new funds safe, which a raw `+2` port would not.

*Implementation sketch (illustrative — binding behavior is the bullets above, not this code):*
```python
seen: dict[date, float] = {}
points: list[NavPoint] = []
poisoned: set[date] = set()
deduped = 0
conflict_dates: list[str] = []          # for the warning detail, sorted on emit
for r in rows:
    ... window-filter (:342-343), productId guard (:349-354) ...   # UNCHANGED
    point = self._parse_nav_point(r)
    d = point.date
    if d in poisoned:
        continue                         # date already quarantined → ignore further rows (counted once)
    if d in seen:
        if point.nav == seen[d]:
            deduped += 1                 # identical-value dup → keep-first (#158/#162)  [UNCHANGED]
            continue
        poisoned.add(d)                  # CONFLICT (#194): quarantine the date — never pick, never average
        conflict_dates.append(d.isoformat())
        del seen[d]
        continue
    seen[d] = point.nav
    points.append(point)
if poisoned:                              # drop the previously-kept point for any poisoned date (#186 :410-414)
    points = [p for p in points if p.date not in poisoned]
points.sort(key=lambda p: p.date)
# ... existing #172 empty/stale handling on `not points` is UNCHANGED ...
considered = len(points) + len(poisoned)  # distinct in-window dates (dups excluded)
if considered and len(poisoned) > max(_QUARANTINE_ABS_FLOOR, _QUARANTINE_FRACTION * considered):
    raise InvalidData(
        f"fmarket: {len(poisoned)}/{considered} in-window navDates conflict "
        f"(> max(floor={_QUARANTINE_ABS_FLOOR}, {int(_QUARANTINE_FRACTION*100)}%)) — "
        f"source systematically broken")
# warnings: existing dedup token FIRST, then the new quarantine token, then nav_end_gap (unchanged order)
```

The warning (sink literal, #188 anchor), emitted only when `poisoned` is non-empty, before `nav_end_gap`:
```python
f"{QUARANTINED_CONFLICTING_NAVDATES}: dropped {len(poisoned)} conflicting navDate(s) — "
f"{', '.join(sorted(conflict_dates))}"
```

---

## Token lockstep plan (#180 + #188) — for the recommended NEW token

In the SAME commit as the code:
1. `vnfin/funds/fmarket.py`: module constant `QUARANTINED_CONFLICTING_NAVDATES =
   "quarantined_conflicting_navdates"` (beside `_NAV_END_GAP`), and the sink f-string above.
2. `tests/test_docs_contract.py`: add the literal to `_WARNING_TOKENS_180` → tuple **47 → 48**
   (and to the `_discover`/Shape-E fixtures if a specific list must enumerate it).
3. `skills/vnfin/SKILL.md`: new warning-token row — token | `funds.nav_history` | "Same-date NAV
   conflict(s) quarantined (two different NAV values for one navDate); the rest of the series is
   served." | #194.
4. CHANGELOG entry (behavior change: `nav_history` no longer aborts on a single conflicting navDate).

The #188 forward-scanner auto-asserts the emitted literal ⊆ documented; #180 asserts doc↔code lockstep.
*(If the gate picks reuse instead: tuple stays 47, no new constant, but the SKILL.md row's scope+meaning
must broaden to include `funds.nav_history` + the date-conflict cause — a doc-only change, still gated.)*

## Snapshot / public-API surface — NO change (additive-green)

`NavHistory.warnings: tuple[str, ...] = ()` already exists (`vnfin/funds/models.py:97`, **defaulted**) and
is already in the FROZEN baseline `tests/snapshots/public_api_v0_2_0.json` (`has_default: true`). The fix
only changes a *failure mode* (raise → successful return + warning); the type, fields, and signature of
`nav_history()`/`NavHistory` are unchanged. **Do NOT run `scripts/dump_api_surface.py`; do NOT regen the
snapshot.** The surface test stays additive-green against the frozen baseline.

## TDD test matrix (RED-first; synthetic fixtures only; offline — never live in CI)

All NAV rows are **synthetic** (no real issuer rows as fixtures). Each test is fail-first (cases 1, 3-low,
5, 6 currently raise `InvalidData`; assert the new served-with-warning behavior so they RED on `master`).

1. **One conflicting navDate** → returns `NavHistory` with the *other* dates; the conflicting date is
   ABSENT from `points`; `result.warnings` contains the `quarantined_conflicting_navdates` token naming
   the date; **NOT** `InvalidData`. (primary fail-first)
2. **Systematically-conflicting** (e.g. 5 conflicting dates in an 8-date window → `5 > max(3, 0.8)`) →
   still raises `InvalidData` (threshold preserved; "source systematically broken").
3. **Threshold boundary** (short series): exactly **3** conflicting dates → SERVES (3 not > floor 3);
   **4** conflicting dates → RAISES. Pins the floor.
4. **Identical-value duplicate** (same date, same NAV) → keep-first, emits `deduped_duplicate_nav_rows`,
   NO quarantine token, date present. (regression — behavior unchanged)
5. **Never-averages** → with conflict (15091 vs 15120) the result contains NO point equal to (or near) the
   mean 15105.5 for that date; the date is simply absent. Asserts degrade-not-fabricate.
6. **Two distinct conflicting dates under threshold** (long series) → both dropped, rest served, warning
   lists BOTH dates (sorted).
7. **Conflict-vs-dedup precedence on the same date** → an identical dup AND a conflicting row on one date
   → the date is quarantined (conflict wins; dropped), not silently deduped.
8. **#172 empty/stale interaction unchanged** → a window that becomes empty after quarantine still yields
   the existing `EmptyData`/`StaleData` (quarantine runs before the existing `not points` handling).

## Clean-room / safety

Fmarket NAV is the library's existing licensed source; this is a pure refactor of our own parser. **Zero
VNStock** involvement (no search/read/port). No secrets; synthetic fixtures only; `gh` only via
`bin/gh-maintainer`; ship to `master` only after reviewer APPROVE + green merged tree.

---

## Open decision for the gate (one)

**Q2 token** is the only genuinely open call: NEW `quarantined_conflicting_navdates` (my rec) vs reuse
`quarantined_invalid_bars` (triage lean). Q1 (drop) and Q3 (reuse `0.10`/floor `3` with date-unit
counting) I recommend firmly. On APPROVE I delegate the TDD build to a fresh general-purpose agent against
this committed spec, integrate + adversarially verify on the merged tree, then route for code review.
