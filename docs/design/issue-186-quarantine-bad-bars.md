# Design note — #186 quarantine-and-warn for bad upstream bars (unblocks the 10y/Max VN-Index chart)

**Status:** SHORT pre-code design note for the reviewer LEAD gate. No code written yet. **TOP CODE PRIORITY**
(jumps ahead of #185 code — core VN-Index view blocker).
**Issue:** #186 (bug+enhancement). **First-consumer signal:** vf-advisor's 10y/Max VN-Index chart is
unrenderable.
**Process:** this note → reviewer LEAD gate → TDD (red-first) → Codex×2 (data-quality posture change to a
shared parse path) → on APPROVE push + close #186.

---

## 1. Problem & root cause (confirmed in code)

`UDFSource._build_bars` (`vnfin/sources/udf.py:150-247`) is the **shared** parse loop behind every UDF adapter
(equity `prices.history` AND index `index_history`). It **`raise`s `InvalidData` on the FIRST per-bar
data-quality failure**, aborting the entire response. Because a bad bar (2018-08-22 OHLC-invariant,
2020-12-25 conflicting same-date) exists in BOTH `vps_index` and `ssi_index`, every source fails the same
date → `AllSourcesFailed` → **one bad bar anywhere in a 10-year window blocks the whole chart.** The
per-bar validation is *correct* (the data IS bad); failing the entire multi-year range on one isolated bar
is the wrong response for a long-horizon series.

Per-bar raises today (all inside the row loop, `udf.py`):
- malformed scalar (unparseable t/o/h/l/c/v) `:203-206`
- non-finite OHLCV `:207-208`
- non-positive price `:211-212`
- negative volume `:213-214`
- fractional volume `:217-218`
- OHLC invariant violated `:220-221`
- duplicate/conflicting key `:231-242` (equity exact-timestamp #66; index D1 date-keyed #162)

Structural raises (NOT per-bar — the whole response is untrustworthy): non-sequence / misaligned arrays
`:175-178`; malformed UDF envelope / non-object data / bad status `get_history:88-131`.

## 2. Fix — quarantine-and-warn (never-silent), with a threshold fail-over guard

Replace the per-bar `raise` with **drop-the-bad-bar-keep-the-rest + record it**, then surface a mechanical
warning. A systematically-broken source still fails over via a threshold guard. Decisions D1–D6 below.

### D1 — Which validations QUARANTINE vs stay a HARD RAISE
- **QUARANTINE (drop the row, keep the rest, record):** the per-row value-quality checks —
  non-finite `:208`, non-positive `:212`, negative volume `:214`, fractional volume `:218`, OHLC invariant
  `:221`. (These are exactly the issue's enumerated set.)
- **HARD RAISE (unchanged — whole response untrustworthy):** structural/shape failures — non-sequence /
  misaligned arrays `:175-178`, malformed envelope / non-object / bad status (`get_history`). The issue is
  explicit: keep structural/parse-shape failures as hard raises.
- **⚠️ ONE JUDGMENT CALL for the gate — malformed scalar `:206`** (a single unparseable value in one row,
  e.g. `null`/`"N/A"`). It is row-level (like non-finite), NOT array/shape-level, so I **recommend
  QUARANTINING it too** (consistent per-row treatment; the D3 threshold still fails over a systematically
  null column → preserves the original "fail over instead of crash" intent). This is the one item beyond the
  issue's enumerated list — **gate to confirm or keep it a hard raise.**

### D2 — Conflicting / duplicate handling (the #66-equity vs #162-index nuance)
- **Index D1, identical same-date dup (#162):** UNCHANGED — dedupe keep-first + set `_dedup_occurred` (the
  existing `deduped_duplicate_daily_index_bars` warning). NOT a quarantine.
- **Index D1, conflicting same-date bar** (was a hard raise `:239-241`): now **drop the date ENTIRELY** —
  remove the already-kept first bar for that date too (we can't tell which is right) + record it as
  quarantined. (Issue: "conflicting same-date → drop the date entirely + warn.")
- **Equity exact-timestamp duplicate (#66, was a hard raise `:242`):** a duplicate/conflicting EXACT
  timestamp → **drop that timestamp entirely + record**. This preserves #66's *spirit* (never silently pick
  among conflicting rows) while not failing the whole fetch. **Gate to confirm** this generalization (vs
  keeping equity exact-ts duplicate a hard raise). I recommend the generalization for consistency — the D3
  threshold catches systematic duplication.
- Each dropped row (including a dropped-date's already-kept first bar) counts toward the D3 fraction; the
  #162 identical-dedupe does NOT.

### D3 — Threshold guard (mirror the gold coverage gate)
- Over the `n` provider rows (before the range filter), if **`quarantined_rows / n > _MAX_QUARANTINE_FRACTION`**
  → `raise InvalidData(f"{name}: {q}/{n} bars invalid (>{pct}) — source systematically broken")`. As a
  `SourceError` this drives `FailoverPriceClient` to the next source; all-sources-exceed → `AllSourcesFailed`
  (correct — the date-range is genuinely untrustworthy everywhere). A few isolated glitches → quarantine+serve.
- **Recommended default `_MAX_QUARANTINE_FRACTION = 0.10`** (tolerate ≤10% isolated bad rows; the gold gate's
  `warn_coverage=0.9` is the analogue). The actual #186 case is 2 bad / ~2487 rows = 0.08% → quarantines.
  **This number is the key tunable — gate to set it** (5% / 10% / 20%).
- **Known property to ratify:** the gate is a *fraction*, so the SAME isolated bad date quarantines in a long
  window (2/2487 → serve) but can trip the threshold in a very short window (1/5 = 20% → fail over). That is
  defensible (a tiny window dominated by bad data IS untrustworthy) and protects the advisor's long-window
  use case. *Optional mitigation if the gate prefers:* an absolute floor (always allow ≥K quarantines
  regardless of fraction). I lean pure-fraction for v1 simplicity — **gate's call.**

> **Implemented as (supersedes the D3 prose above):** the gate **adds the absolute floor** —
> constants `_QUARANTINE_FRACTION = 0.10` **and** `_QUARANTINE_ABS_FLOOR = 3`; the source fails over
> iff `bad_inrange > max(_QUARANTINE_ABS_FLOOR, _QUARANTINE_FRACTION × considered)`. **The threshold is
> judged over the requested window, NOT all provider rows** — the range filter runs *inside*
> `_build_bars`, so `considered` = in-range timestamp-parseable rows (each calendar date counted once)
> and `bad_inrange` = how many of those failed; out-of-range padding, unplaceable (timestamp-unparseable)
> rows, and identical #162 same-date duplicates are excluded. This corrects two reviewer-found
> regressions: (1) computing the threshold over *all* provider rows (before the range filter) let bad
> rows OUTSIDE `[start, end]` spuriously fail over a clean window — re-creating the #186 bug in the
> padding region; (2) counting identical same-date duplicates in the denominator let a feed that emits
> each date twice dilute the bad-fraction and flip a marginal failover into a serve. See
> `docs/architecture/failover-and-validation.md` → "A systematically-broken source still fails over".

### D4 — The warning (never-silent) + how it threads to BOTH paths
- Mechanical token **`quarantined_invalid_bars`**; human tail names the dropped dates + reasons, e.g.
  `quarantined_invalid_bars: dropped 2 of 2487 bars — 2018-08-22: OHLC invariant violated; 2020-12-25: conflicting same-date bars`.
- `_build_bars` records `self._quarantined: list[tuple[str, str]]` (date/timestamp, reason) — mirroring
  `self._dedup_occurred`. The token is attached in the **shared** `UDFSource.get_history` `PriceHistory(...)`
  construction (`udf.py:137-148`, currently `warnings`-less) so **both** equity and index results carry it.
  The index subclass (`indices/sources.py:103-107`) still appends its `deduped_duplicate_daily_index_bars`
  token on top — order: quarantine warning first, dedupe token second.

### D5 — Scope & non-goals
- Change is confined to the **shared `udf.py` parse path** → benefits `index_history` AND `prices.history`
  at once. `FailoverPriceClient` is UNCHANGED (a threshold-exceeded raise drives failover exactly as the
  per-bar raise did today; the only behavioral change is that isolated bad bars no longer raise).
- **Do NOT hardcode-repair** 2018-08-22 / 2020-12-25 — the general quarantine handles them and any future
  bad dates ([[staleness-warning-prefer-bounded-false-positive]]: bounded false-positive (drop+warn) over a
  false-negative (silently serving a wrong bar); the threshold guards the other tail).
- Public-API surface UNCHANGED (no signature/shape change; new token is just a warning string) →
  `public_api_v0_2_0.json` stays **FROZEN** ([[public-api-snapshot-is-release-time-not-per-feature]]).

### D6 — Docs/skill/CHANGELOG in the same change
- CHANGELOG entry; document the `quarantined_invalid_bars` warning + the threshold behavior wherever the
  data-quality posture is described (skill + the relevant tutorial/source doc). Per the maintainer rule
  (public-facing behavior change ⇒ docs + skill + CHANGELOG together).

## 3. Test plan (offline, synthetic — TDD red-first; [[fork-echoes-context-use-fresh-agent-for-delegated-impl]])
- **RED regression (the reported bug):** a synthetic UDF envelope with one OHLC-invariant row (2018-08-22)
  and, separately, a conflicting same-date index pair (2020-12-25), across an otherwise-clean multi-year
  span → today raises `InvalidData`/`AllSourcesFailed`; after the fix → returns the clean bars + a
  `quarantined_invalid_bars` warning naming the dropped date(s)+reason(s).
- **Per-validation quarantine:** one row each of non-finite / non-positive / negative-vol / fractional-vol /
  OHLC-invariant → dropped + named in the warning; the rest served.
- **Conflict/dup:** index conflicting same-date → date dropped entirely (neither bar served) + warned;
  index identical same-date → still #162 dedupe (kept-first + `deduped_duplicate_daily_index_bars`, NOT
  quarantine); equity exact-ts duplicate → timestamp dropped + warned (per D2 gate decision).
- **Threshold:** below `_MAX_QUARANTINE_FRACTION` → quarantine+serve; above → `InvalidData` → failover (and
  all-sources-bad → `AllSourcesFailed`). Cover the short-window property (D3).
- **Hard-raise preserved:** misaligned/non-sequence arrays + malformed envelope/status still raise (NOT
  quarantined).
- **Both accessors:** assert the warning surfaces via `prices.history` AND `index_history` (shared-path
  proof); index keeps its dedupe token alongside.
- **Clean-room:** synthetic fixtures only; zero VNStock.

---

**Ask of the LEAD gate:** ratify D1–D6 — especially **(a) `_MAX_QUARANTINE_FRACTION` value** (recommend
0.10), **(b) the equity exact-timestamp duplicate generalization** (D2), and **(c) the malformed-scalar
judgment call** (D1, recommend quarantine). On APPROVE I TDD red-first → Codex×2 → push + close #186, then
return to #185 code.
