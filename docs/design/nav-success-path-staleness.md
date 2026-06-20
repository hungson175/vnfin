# Design — Success-path NAV end-gap warning (#172-RESIDUAL)

**Status:** APPROVED_WITH_NOTES (reviewer design-check ×2, review-202606201803). TDD-first.
**Relates to:** #172 (shipped `vnfin.exceptions.StaleData` for the *failure* path). This is the *success*-path
residual. **Follow-up:** `FundList.nav` per-fund as-of is filed as **#181** (out of scope here, §7).

## 1. Problem

`#172` added `StaleData` (subclass of `EmptyData`) raised by `FmarketFundSource.nav_history()`
(`vnfin/funds/fmarket.py:297`) when the **whole** NAV history ends *before* the requested window
(`max_navdate < from_date`) — a stale/closed feed that returns nothing usable.

The **residual** is the quieter failure: `nav_history(...)` **succeeds** (the series reaches into the
window) but its **latest** observation is old — the feed is delayed, paused, or the fund dormant — and the
returned `NavHistory` carries **no signal at all**. A NAV-driven metric (return, drawdown, "current
value") silently computes on a stale tail. The price side already warns on the analogue
(`partial_end_coverage`, `vnfin/client.py:244`); funds do not.

`NavHistory.warnings: tuple[str, ...]` already exists and is already populated (the dedup warning,
`vnfin/funds/fmarket.py:302`), so a soft warning needs **no schema change** — only a new diagnostic.

Complementarity with `StaleData` is structurally clean: the failure path is the *no usable points* branch
(`raise StaleData`), this warning is the *else* branch (points exist, judge the tail) — they cannot both
fire.

## 2. The trap — NAV cadence is NOT the stock trading calendar

The obvious fix (reuse the price `partial_end_coverage` logic keyed on
`calendar.expected_latest_trading_day`) is **wrong** for funds:

- Stocks trade **every** trading day, so "last bar > 7d before the expected latest trading day" is clean.
- Fund NAV cadence **varies by fund**: large equity funds publish ~daily, but many **bond and balanced
  funds** (in scope since #173) publish **weekly or twice-monthly**. A weekly-NAV fund whose latest NAV is
  6–8 days old is **fresh** — a stock-trading-day expectation would false-positive it almost every day.

We must not hardcode which funds are weekly. The robust, self-calibrating signal is **cadence-relative**:
infer the fund's typical inter-NAV gap **from the returned series**, and warn only when the latest point is
older than a multiple of that fund's own cadence.

## 3. Approach — cadence-relative end-gap on the `nav_history()` success path

On a **successful** `nav_history()` return (no `StaleData`; `points` non-empty, ascending, deduped),
compute a soft warning from the data in hand and append it to `NavHistory.warnings`.

**Cadence is inferred over a TRAILING window of the most recent diffs, not the whole series.** A fund that
ran daily for years then switched to weekly keeps a whole-series median gap ≈ 1 → threshold 7 → a normal
weekly gap (7–10d) **false-positives**. The trailing window tracks the *current* publication regime. The
#173 bond/balanced funds are exactly the at-risk population.

### Algorithm (`today` is an injected `date`, never `datetime.now()`; never written to the result)

```
reference = min(to_date, today) if to_date is not None else today
# open/now window → today (can't expect NAV beyond today); past window → its end.

gap_days = (reference - points[-1].date).days
if gap_days <= 0:
    return ()                                  # series reaches the window end → fresh

if len(points) >= 2:
    diffs = [(points[i+1].date - points[i].date).days for i in range(len(points) - 1)]
    window = diffs[-_NAV_END_GAP_CADENCE_WINDOW:]      # last N (all if fewer) — CURRENT regime
    typical_gap = max(1, int(median(window)))          # robust to a single Tet/holiday outlier
    threshold = max(_NAV_END_GAP_FACTOR * typical_gap, _NAV_END_GAP_MIN_DAYS)
else:
    typical_gap = None                                 # single point: cadence unknown
    threshold = _NAV_END_GAP_SINGLE_POINT_DAYS

if gap_days > threshold:
    return (f"nav_end_gap: latest NAV {points[-1].date.isoformat()} is {gap_days}d before "
            f"{reference.isoformat()} (typical cadence ~{typical_gap}d; threshold {threshold}d) "
            f"— fund NAV feed may be delayed, paused, or the fund dormant",)
return ()
```

Constants (Q3 ratified): `_NAV_END_GAP_FACTOR = 2`, `_NAV_END_GAP_MIN_DAYS = 7`,
`_NAV_END_GAP_SINGLE_POINT_DAYS = 14`, `_NAV_END_GAP_CADENCE_WINDOW = 8`.

Worked: **daily** fund (trailing median ≈ 1) → threshold `max(2,7)=7` → warns only when >7 calendar days
stale (a holiday weekend never trips it). **Weekly** fund (trailing median ≈ 7) → threshold `max(14,7)=14`
→ warns only after ~2 missed publications. **Daily→weekly switch** → trailing median ≈ 7 → a fresh weekly
tail does **not** warn. No false positives; daily funds going a week dark are still caught.

### Tet (Lunar New Year) — a TRUE positive, self-clearing (not a bug)

Tet closes the market/funds ~1–2 weeks. Right after Tet a still-**daily** fund's latest NAV is ~9–12 days
old → `gap_days > 7` → `nav_end_gap` **fires correctly** (the feed genuinely paused). `median` keeps the
single long Tet diff from inflating `typical_gap`, so the warning is a true positive that **self-clears**
once daily NAV resumes (`gap_days` drops back under 7). This is documented to pre-empt a "false positive
after Tet" bug report — it is the intended, correct behaviour.

## 4. Warning message format

Token-prefixed (matches `partial_end_coverage` / `trailing_zero_volume_tail` so callers can match
programmatically). The token is **mechanical** — `nav_end_gap` states the observed fact (a gap to the
expected end); the *cause* ("may be delayed, paused, or dormant") stays in the human-detail tail. We do
**not** reuse `partial_end_coverage` — a caller matching that token would wrongly assume the stock-calendar
computation ran. (Same call as #176: `trailing_zero_volume_tail` over `stale_or_delisted_tail`.)

```
nav_end_gap: latest NAV 2026-06-05 is 15d before 2026-06-20 (typical cadence ~1d; threshold 7d)
— fund NAV feed may be delayed, paused, or the fund dormant
```

## 5. Implementation sketch

- New pure helper `_nav_end_gap_warning(points, to_date, today) -> tuple[str, ...]` (module-level or
  staticmethod, mirroring `_coverage_warnings` / `_phantom_tail_warning`). **`today: date` is a required
  param**, injected for deterministic tests; production passes the existing VN-today source (behind
  `_today_ymd()`). The helper never calls `datetime.now()` and never writes `today` into the result —
  `NavHistory.fetched_at_utc` stays the real fetch stamp.
- Call it in `nav_history()` where `warnings` is assembled (`vnfin/funds/fmarket.py:302`), concatenating
  after the existing dedup warning:
  `warnings = dedup_warnings + _nav_end_gap_warning(points, hi, today)`.
- Additive only: `NavHistory.warnings` already exists; no public-API signature change; surface snapshot
  untouched.

## 6. Test plan (synthetic JSON payloads, offline; TDD red-first; `tests/test_funds.py`)

Reuse `_nav_history_payload` / `_capture_get` / window-aware fixtures (the #172 block, lines 1893–1976).
**All threshold tests pass an explicit `today` (deterministic) — never live `date.today()`.**
- **Daily fund, stale tail** (latest NAV 15d before an open/now window) → `nav_end_gap` warns; names gap +
  cadence + threshold.
- **Daily fund, fresh** (latest NAV 1–2d old, weekend) → NO warning (under the 7d floor).
- **Weekly fund, fresh** (trailing cadence ≈ 7, latest NAV 8d old) → NO warning — the key regression that
  the stock-calendar approach would wrongly flag.
- **Weekly fund, stale** (cadence ≈ 7, latest NAV 20d old) → warns.
- **Mid-series cadence change, fresh tail** (years of daily then a recent weekly tail, latest NAV ~6–8d
  old) → NO warning — proves the trailing window (not whole-series median) governs; also folds in the
  Tet-gap robustness.
- **`gap_days == 0`** (latest NAV exactly == reference) → NO warning (boundary).
- **`to_date == today`** and **future `to_date`** → reference clamps to today; behaves like the now-window.
- **Historical window fully covered** (`to_date` in the past, series reaches it) → NO warning (NON-GOAL,
  §7).
- **Historical window, early-ending series** (series ends long before a past `to_date`) → warns vs
  `to_date`.
- **Single-point series** → `_NAV_END_GAP_SINGLE_POINT_DAYS` fallback (one case each side).
- **Two-point weekend** (only diff is a 2–3d weekend gap) → fresh tail → NO warning.
- **Coexists with dedup warning** — both present, no double-warn, dedup stays first.
- **Existing no-window stale-history test** — its returned `NavHistory` now carries `nav_end_gap`; add an
  explicit warning-**presence** assertion (the result object changed; pin it).
- **Never raises / never fabricates now()** — `fetched_at_utc` untouched; `today` injected.

## 7. Out of scope / NON-GOALS

- **Historical-window-fully-covered is a NON-GOAL.** When the caller asks for a past window and the series
  reaches its end, there is nothing stale about it — `gap_days <= 0` returns no warning by design.
- **`FundList` per-fund NAV staleness → filed as #181.** `Fund.nav: float` carries no as-of date
  (`vnfin/funds/models.py:19`); judging its freshness first needs an **additive** `nav_as_of` field
  populated from the provider's per-fund nav date *if `list_funds` supplies one* (gated probe). This is the
  list-NAV half the reporter saw — tracked, not dropped. Deferred to #181.
- **Per-point `NavPoint.as_of`** — NAV is a once-daily calendar observation with no intraday meaning; a
  per-point timestamp adds nothing. Not planned.
- **Holiday-aware NAV calendar** — funds share no published calendar; cadence-relative inference avoids
  needing one.

## 8. Reviewer decisions (ratified — design gate review-202606201803)

- **Q1 (baseline):** **cadence-relative** — RATIFIED (stock-calendar provably false-positives the #173
  weekly/bond funds daily).
- **Q2 (token):** **`nav_end_gap`** (constant `_NAV_END_GAP`) — mechanical; NOT `stale_nav` (a
  conclusion/cause word), NOT a reuse of `partial_end_coverage`.
- **Q3 (constants):** `FACTOR=2`, `MIN_DAYS=7`, `SINGLE_POINT_DAYS=14`, `median` — RATIFIED; plus the
  mandatory **trailing-window** `CADENCE_WINDOW=8` (most-recent diffs, all-if-fewer).
- **Q4 (scope):** v1 = `NavHistory` only — CONFIRMED; `FundList.nav` as-of → **#181**.
- **Q5 (reference date):** `reference = min(to_date, today)` (else `today`) — CONFIRMED.
