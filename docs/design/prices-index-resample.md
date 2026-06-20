# Design note — #183 optional interval/resample on `prices.history` + `index_history`

- Date: 2026-06-21 +07 · Issue: #183 (enhancement) · Status: **DESIGN — for reviewer LEAD gate (pre-code)**
- Reporter (vf-advisor): charts cadence series over 5–15y; a 10y daily pull is ~2,500 rows and overflows
  the agent's context. Wants optional period aggregation; daily stays the default (back-compat).

## Ground truth (verified in code — shapes the whole design)
- `vnfin.prices.history(symbol, interval=Interval.D1, start, end, ...)` and
  `vnfin.indices.index_history(symbol, start, end, interval=Interval.D1)` **already accept `interval`**
  and forward it to the failover chain's capability gate (`source.supports(interval)` →
  `UnsupportedInterval` when none match). The VN equity/index sources are **daily-native** — none serves a
  native weekly/monthly endpoint (and adding one needs a clean-room source). So **#183 is client-side
  resampling of the fetched D1 series**, NOT a new native interval — fundamentally unlike crypto
  `get_klines` (Binance serves all intervals natively).
- **`Interval` enum today:** `M1="1m"`(minute), M5, M15, M30, H1, `D1="1d"`, `W1="1w"`, `MN1="1M"`(month).
  ⚠️ **`M1` is one MINUTE, monthly is `MN1`.** There is **no quarter/year member**. The enum is in the
  public snapshot (`public_api_v0_2_0.json`).

## The crux — the minute-vs-month trap (the reviewer's flagged wrinkle)
The reporter wrote "D1/W1/M1/Q1/Y1" meaning daily/weekly/monthly/quarterly/yearly, but in THIS codebase
`M1` already means **1 minute**. Resolution:
- **Monthly = `Interval.MN1`** (never `M1`).
- **pandas string aliases** map the *intent*, unambiguously: `'D'→D1, 'W'→W1, 'M'→MN1 (MONTH), 'Q'→Q1,
  'Y'→Y1`. `'M'` MUST resolve to monthly (`MN1`), never minute (`M1`). This is the one mapping most likely
  to be mis-coded — it gets an explicit test.
- **Intraday intervals (`M1, M5, M15, M30, H1`) are rejected** for these daily-native accessors with a
  clear `InvalidData`/`UnsupportedInterval` ("intraday not supported for VN equity/index history") — you
  cannot resample a coarser (daily) series into a finer (minute) one.

## Proposed behavior (v1)
1. **Reuse the existing `interval` param** on both accessors (no new param, no signature break). Accept an
   `Interval` member OR a pandas-style alias string. Default `Interval.D1` → **identical to today** (the
   resample path is never entered; existing callers untouched).
2. **Supported resample set = periods COARSER than D1:** `W1, MN1, Q1, Y1`. `D1` = passthrough.
3. **Add `Interval.Q1`/`Interval.Y1`** (additive enum members; resample-only) so the Interval-primary form
   is symmetric with D1/W1/MN1. *(Verify the surface test treats new enum members as additive — expected
   green, no snapshot regen mid-feature.)*
4. **Fetch D1 internally, aggregate client-side, return the coarse series.** Network fetch is still
   full-range daily — the win is the **returned row count / agent context** (10y → ~10 yearly / ~120
   monthly rows), exactly the reported pain. Deterministic + offline-testable (feed synthetic D1, assert
   the aggregate). Returned `PriceHistory.interval` = the requested interval + a `resampled_from_d1`
   provenance warning so the series self-discloses it is aggregated, not native.
5. **Aggregation — prices (equity):** OHLC per period — `open=first, high=max, low=min, close=last,
   volume=sum`.
6. **Grouping + bar date:** group by calendar period (ISO week / calendar month / quarter / year); label
   each aggregated bar at the **last actual trading day** within the period (a real market date, not a
   synthetic calendar boundary). Partial leading/trailing periods (window starts/ends mid-period)
   aggregate only the in-window days.
7. **Partial-period disclosure (the #178/#172 pattern, lightly):** emit a `resample_partial_period`
   warning when the first or last emitted bar covers an incomplete calendar period, so a chart never reads
   a partial month/quarter/year as a full one. Keep the partial bars (don't drop).

## Open questions for the LEAD gate
1. **Index aggregation — my recommendation diverges from your lean.** You leaned *index = period-end*; I
   recommend **OHLC-per-period for BOTH** prices and index: it's a single code path, lossless (period-end
   close is just `close=last`, and you get the period range for free), and index bars already carry OHLC.
   Period-end-only throws away O/H/L for no clear benefit. Your call at the gate.
2. **`Interval.Q1`/`Y1` as real enum members (my rec, additive) vs string-alias-only** (`'Q'`/`'Y'` with
   no enum member)? Adding members keeps the Interval-primary form complete; needs the surface-additive
   check.
3. **Partial leading/trailing period:** warn (`resample_partial_period`, my rec) vs silent vs drop?
4. **Bar label date:** last trading day in period (my rec) vs synthetic calendar period-end date?
5. **`index_history_stitched` resample:** in scope for v1, or follow-up? (I rec **follow-up** — keep v1 to
   `prices.history` + `index_history`; stitched can later stitch D1 then resample.)
6. **Pandas alias set:** confirm the minimal accepted strings — `'D'/'W'/'M'/'Q'/'Y'` (case-insensitive);
   reject everything else with a clear error. (Headline safety: `'M'`→`MN1`.)

## Plan after the gate
Reviewer LEAD gate on this note → TDD (synthetic D1 fixtures → assert OHLC aggregation, the `'M'`→MN1
mapping, intraday rejection, partial-period warning, D1 back-compat passthrough, both accessors) → **Codex
×2** code review (per your routing) → push + close. Clean-room: zero VNStock; pure client-side aggregation
of already-fetched bars, no new source/network.
