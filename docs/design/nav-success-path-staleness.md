# Design — Success-path NAV staleness warning (#172-RESIDUAL)

**Status:** DESIGN (awaiting `vnfin-oss-reviewer` design-check before code). TDD-first when approved.
**Relates to:** #172 (shipped `vnfin.exceptions.StaleData` for the *failure* path). This is the *success*-path residual.

## 1. Problem

`#172` added `StaleData` (a subclass of `EmptyData`) raised by `FmarketFundSource.nav_history()`
(`vnfin/funds/fmarket.py:297`) when the **whole** NAV history ends *before* the requested window
(`max_navdate < from_date`) — a stale/closed feed that returns nothing usable.

The **residual** is the opposite, quieter failure: `nav_history(...)` **succeeds** (the series reaches into
the window) but its **latest** observation is old — the fund's feed is delayed, paused, or the fund has
gone dormant — and today the returned `NavHistory` carries **no staleness signal at all**. A NAV-driven
metric (return, drawdown, "current value") silently computes on a stale tail. The price side already warns
on the analogous case (`partial_end_coverage`, `vnfin/client.py:244`); funds do not.

`NavHistory.warnings: tuple[str, ...]` already exists and is already populated (the dedup warning,
`vnfin/funds/fmarket.py:302`), so a soft warning needs **no schema change** — only a new diagnostic.

## 2. The trap — NAV cadence is NOT the stock trading calendar

The obvious fix (reuse the price `partial_end_coverage` logic keyed on
`calendar.expected_latest_trading_day`) is **wrong** for funds:

- Stocks trade **every** trading day, so "last bar > 7d before the expected latest trading day" is a clean
  staleness signal.
- Fund **NAV publication cadence varies by fund**: large equity funds publish ~daily, but many **bond and
  balanced funds** (now in scope since #173) publish **weekly or twice-monthly**. A weekly-NAV fund whose
  latest NAV is 6 days old is **perfectly fresh** — a stock-trading-day expectation would emit a
  false-positive `partial_end_coverage` for it every single day except publication day.

We must not hardcode which funds are weekly. The robust, self-calibrating signal is **cadence-relative**:
infer the fund's typical inter-NAV gap **from the returned series itself**, and warn only when the latest
point is older than a multiple of that fund's own cadence.

## 3. Approach — cadence-relative staleness on the `nav_history()` success path

On a **successful** `nav_history()` return (no `StaleData` raised; `points` non-empty, ascending,
deduped), compute a soft staleness warning from the data already in hand. Append it to
`NavHistory.warnings`. **Never fabricate `now()`** in the result; `today` is an explicit, injectable
reference date (deterministic in tests) used only for the comparison, not stored.

### Algorithm

```
reference = to_date if (to_date is not None and to_date < today) else today
# historical window → measure vs its end; open/now window → measure vs today (can't expect NAV > today)

gap_days = (reference - points[-1].date).days
if gap_days <= 0:
    return ()                      # series reaches the window end → fresh

# infer the fund's own cadence from consecutive NAV dates (calendar days)
if len(points) >= 2:
    diffs = [(points[i+1].date - points[i].date).days for i in range(len(points)-1)]
    typical_gap = max(1, median(diffs))   # robust to holiday/weekend outliers
    threshold = max(_STALE_NAV_GAP_FACTOR * typical_gap, _STALE_NAV_MIN_DAYS)
else:
    typical_gap = None                    # single point: cadence unknown
    threshold = _STALE_NAV_SINGLE_POINT_DAYS

if gap_days > threshold:
    return (f"stale_nav: latest NAV {points[-1].date.isoformat()} is {gap_days}d before "
            f"{reference.isoformat()} (typical cadence ~{typical_gap}d; threshold {threshold}d) "
            f"— fund NAV feed may be delayed, paused, or the fund dormant",)
return ()
```

Proposed constants (Q3): `_STALE_NAV_GAP_FACTOR = 2`, `_STALE_NAV_MIN_DAYS = 7`,
`_STALE_NAV_SINGLE_POINT_DAYS = 14`.

Worked: a **daily** fund (typical_gap≈1) → threshold `max(2, 7)=7` → warns only when >7 calendar days
stale (a holiday weekend never trips it). A **weekly** fund (typical_gap≈7) → threshold `max(14, 7)=14` →
warns only when it has missed ~2 publications. No false positives on weekly funds; no missed staleness on
daily funds.

Why **no** `expected_latest_trading_day` snap: the `max(…, _STALE_NAV_MIN_DAYS=7)` floor already absorbs
weekend/holiday lag, so snapping `today` to a trading day buys nothing and re-imports the stock-calendar
assumption we are deliberately avoiding.

## 4. Warning message format

Token-prefixed (matches `partial_end_coverage` / `trailing_zero_volume_tail` so callers can match
programmatically), mechanical fact first, inferred cause in the human-detail tail:

```
stale_nav: latest NAV 2026-06-05 is 15d before 2026-06-20 (typical cadence ~1d; threshold 7d)
— fund NAV feed may be delayed, paused, or the fund dormant
```

## 5. Implementation sketch

- New pure helper `_nav_staleness_warning(points, to_date, today) -> tuple[str, ...]` (module-level or
  staticmethod, mirroring `_coverage_warnings` / `_phantom_tail_warning`). `today` injected for
  deterministic tests (reuse the existing VN-today source behind `_today_ymd()` as the production default).
- Call it in `nav_history()` where `warnings` is assembled (`vnfin/funds/fmarket.py:302`), concatenating
  after the existing dedup warning: `warnings = dedup_warnings + _nav_staleness_warning(points, hi, today)`.
- Additive only: `NavHistory.warnings` already exists; no public-API signature change; surface snapshot
  untouched.

## 6. Test plan (synthetic JSON payloads, offline; TDD red-first; `tests/test_funds.py`)

Reuse `_nav_history_payload` / `_capture_get` / window-aware fixtures (the #172 block, lines 1893–1976):
- **Daily fund, stale tail** (latest NAV 15d before an open-ended/now window) → `stale_nav` warns; names
  gap + cadence + threshold.
- **Daily fund, fresh** (latest NAV 1–2d old, weekend) → NO warning (under the 7d floor).
- **Weekly fund, fresh** (cadence≈7, latest NAV 6d old) → NO warning (this is the false-positive the
  stock-calendar approach would wrongly flag — the key regression test).
- **Weekly fund, stale** (cadence≈7, latest NAV 20d old) → warns (missed ~2 publications).
- **Historical window** (`to_date` well in the past, series reaches `to_date`) → NO warning
  (`gap_days <= 0`).
- **Historical window, early-ending series** (series ends long before a past `to_date`) → warns vs
  `to_date`.
- **Single-point series** → uses `_STALE_NAV_SINGLE_POINT_DAYS` fallback (one case each side of it).
- **Coexists with dedup warning** — both present, no double-warn, dedup stays first.
- **Never raises / never fabricates now()** — result `fetched_at_utc` untouched; deterministic `today`.

## 7. Out of scope for v1 (follow-ups)

- **`FundList` per-fund NAV staleness.** `Fund.nav: float` carries **no** as-of date
  (`vnfin/funds/models.py:19`), so its freshness cannot be judged. Fixing it first needs an **additive**
  `nav_as_of` field populated from the provider's per-fund nav date *if `list_funds` supplies one* (needs a
  gated probe of the list endpoint). Tracked against the "typed results carry the provider's own as-of"
  principle. Deferred.
- **Per-point `NavPoint.as_of`** — NAV is a once-daily calendar observation with no intraday meaning;
  retrofitting a per-point timestamp adds nothing. Not planned.
- **Holiday-aware NAV calendar** — funds don't share one published calendar; cadence-relative inference
  intentionally avoids needing it.

## 8. Open questions for the reviewer

- **Q1 (baseline — the critical choice):** ratify **cadence-relative** (infer typical gap from the
  series; recommended, avoids weekly-fund false positives) vs. reuse the stock-calendar
  `expected_latest_trading_day` (simpler, but false-positives weekly/biweekly funds) vs. a flat absolute
  calendar-day tolerance (cadence-agnostic but blind to daily funds going a week stale)?
- **Q2 (token):** `stale_nav` (proposed), or reuse `partial_end_coverage` for cross-domain consistency
  (risks implying the same stock-calendar computation), or a more mechanical name (`nav_end_gap`)?
- **Q3 (constants):** ratify `GAP_FACTOR=2`, `MIN_DAYS=7`, `SINGLE_POINT_DAYS=14`, and `median` (vs mode)
  for typical-gap inference?
- **Q4 (scope):** confirm v1 = `NavHistory` only; `FundList.nav` as-of is a separate probe+additive-field
  follow-up (§7)?
- **Q5 (reference date):** confirm staleness is measured vs `min(to_date, today)` so explicitly-historical
  windows that the series fully covers never warn.
