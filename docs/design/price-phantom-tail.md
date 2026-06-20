# Design — Delisted/suspended phantom-tail detection (#176)

- Status: **DESIGN — awaiting reviewer convergence (design gate; the threshold is the decision)**
- Date: 2026-06-20
- Issue: #176 (reporter `motsach1984-alord`), reviewer-VERIFIED spec
  review-202606201601-issue176-delisted-phantom-tail-VERIFIED.md (+ multi-source addendum)
- Architecture map: Explore recon 2026-06-20 (insertion point + precedents verified in-tree)

## 1. Problem & evidence

After a symbol is suspended/delisted, some price sources keep emitting a **trailing run of forward-
filled phantom bars** — each `volume == 0` and `open == high == low == close` (a flat carried-forward
price) — instead of ending the series at the last real trading day. A flat phantom line silently
corrupts survivorship-aware backtests (drawdown/return/vol). Same class as the #157 mislabel: a
**wrong-but-plausible typed result**.

Reviewer-reproduced (library probe, `prices.history(sym, D1, ...)`):

| ticker | source | trailing phantom run | distinct closes | last real bar |
|---|---|---:|---|---|
| FLC | `vps` | 819 | 3500/3570 | ~2022-09-08 |
| HAI | `vps` | 821 | 1500/1580 | ~2022-09-08 |
| **TGG** | **`vndirect`** | **677** | 2300/2370 | ~2023-09-15 |
| ROS | `vps` | ~14 | — | ~2022-08-11 |

**Multi-source CONFIRMED** (FLC/HAI via vps, TGG via vndirect) → a per-adapter patch would miss TGG.
Only `partial_end_coverage` warns today (the gap to *today*); the phantom tail itself is silent.

## 2. Location decision — canonical, source-agnostic post-processing

Implement detect+WARN in the **one place every equity price-history flows through after the failover
engine picks a winner**, not per adapter:

- **`FailoverPriceClient._finalize(hist, attempts, symbol, interval, start, end)`** —
  `vnfin/client.py:178-183`. It already appends the #169 coverage warnings here and rebuilds the
  frozen `PriceHistory` via `dataclasses.replace(...)`. `interval` is in scope.

This covers FLC/HAI/TGG/ROS and any future delisted symbol in one place. **Scope:** equity prices
(and `vnfin.liquidity`, which consumes `prices.history` and passes warnings through —
`liquidity.py:158`, so it inherits the phantom warning for free). **Market indices are out of scope**
— they use a separate `indices/client.py` and do not delist.

## 3. Detection algorithm

```
trailing phantom run = the maximal SUFFIX of bars where EVERY bar satisfies
    bar.volume == 0  AND  bar.open == bar.high == bar.low == bar.close
warn iff  interval is Interval.D1  AND  len(run) >= THRESHOLD
```

- **Primary discriminator = the per-bar signature** (`V==0 AND O==H==L==C`). A real flat-but-traded
  day (limit-locked, `O==H==L==C` with `V>0`) is excluded by the `V==0` requirement.
- **TRAILING only.** An interior zero-volume flat stretch (a mid-series halt that later resumed, real
  data) is NOT warned — only the suffix that runs to the end of the returned series.
- **Exact equality** is intended: a forward-fill copies the identical float, so `==` (no epsilon) is
  correct; `volume` is `int` so `== 0` is exact.
- **"last real bar"** = the bar immediately before the run starts (the last genuine trading day). If
  the entire series is the run, there is no real bar in-window (message says so).

## 4. THE threshold decision (the design gate)

The reviewer framed this as the decision: **catch ROS's ~14-bar tail, but never a normal 1–2-day
zero-volume illiquid tail; trustworthy, not noisy.** ROS (~14) is the binding lower constraint, so any
threshold `≤ 14` catches every reported case (14/677/819/821). The question is how far below 14 to go
without false-warning a merely-illiquid listed name.

**Recommendation: `THRESHOLD = 10` trailing D1 bars** (run-length only).
- 10 consecutive D1 bars ≈ **two calendar weeks** of no real trading, flat, right up to the window
  end. For a *listed* name that is genuinely abnormal — it means halted/suspended (which is exactly
  what we want to flag) or a source forward-fill (the phantom bug). A normal 1–2-day (even a 1-week)
  illiquidity gap stays quiet.
- Catches ROS(14) with a 4-bar safety margin and all the egregious 600–800 cases.
- Run-length (in bars), not calendar span: for D1, bars ≈ trading days, so a span guard adds
  complexity with no real benefit. Considered and rejected for v1.

Trade-off for the reviewer to ratify:

| THRESHOLD | catches | risk |
|---:|---|---|
| 5 | more (incl. short post-halt tails) | slightly noisier on very-illiquid UPCOM names |
| **10 (rec.)** | ROS(14)+all reported, halts ≥2wk | low; balanced |
| 14 | only ROS-exactly + the big cases | too tight — a 13-bar phantom slips |

(False positives are low-cost here — a *warning*, never a drop — but the message claims
"suspended/delisted/halted," so we keep it conservative enough to stay credible.)

## 5. Warning format

Token-prefixed string (matches the existing `partial_coverage` / `deduped_duplicate_daily_index_bars`
style so callers can match programmatically), with human detail:

```
stale_or_delisted_tail: {N} trailing zero-volume flat (O=H=L=C) bars through {last_date};
last real-volume bar {last_real_date} — likely suspended/delisted/halted or source forward-fill;
treat the tail as non-tradeable
```

- Constant `_STALE_OR_DELISTED_TAIL = "stale_or_delisted_tail"` near the other warning tokens.
- `{last_real_date}` = `"none in window"` when the whole series is phantom.
- Appended to `PriceHistory.warnings` via `replace()`; **bars are NOT dropped** (v1 = warn only).

## 6. Implementation sketch (no code until approved)

```python
# vnfin/client.py
@staticmethod
def _phantom_tail_warning(hist, interval) -> tuple[str, ...]:
    if interval is not Interval.D1 or not hist.bars:
        return ()
    run = 0
    for bar in reversed(hist.bars):
        if bar.volume == 0 and bar.open == bar.high == bar.low == bar.close:
            run += 1
        else:
            break
    if run < _PHANTOM_TAIL_MIN_RUN:          # = 10 (pending ratification)
        return ()
    first_phantom = hist.bars[-run]
    last_real = hist.bars[-run - 1] if run < len(hist.bars) else None
    last_real_date = last_real.time.date().isoformat() if last_real else "none in window"
    return (f"{_STALE_OR_DELISTED_TAIL}: {run} trailing zero-volume flat (O=H=L=C) bars "
            f"through {hist.bars[-1].time.date().isoformat()}; last real-volume bar "
            f"{last_real_date} — likely suspended/delisted/halted or source forward-fill; "
            f"treat the tail as non-tradeable",)

# in _finalize(...):
warnings = (tuple(hist.warnings)
            + FailoverPriceClient._coverage_warnings(hist, start, end)
            + FailoverPriceClient._phantom_tail_warning(hist, interval))
return replace(hist, attempts=attempts, warnings=warnings)
```

## 7. Test plan (synthetic, offline; TDD red-first; `tests/test_client.py`)
Using the existing `FakeSource` + `_history_through`/`synth.make_history` fixtures:
- **Multi-source/ticker fixtures:** a D1 series with a trailing `V==0, O==H==L==C` run ≥ threshold →
  `stale_or_delisted_tail` warning naming the run length, through-date, and last real bar; **bars
  still returned** (not dropped). Build FLC/HAI-shaped (long run) and TGG-shaped fixtures.
- **Threshold boundary:** run length exactly `THRESHOLD` → warn; `THRESHOLD-1` → no warn.
- **Normal illiquid tail:** 1–2 trailing zero-volume bars → NO warning (not noisy).
- **Interior, not trailing:** a zero-volume flat stretch mid-series followed by real bars → NO warning.
- **Legit flat trading:** trailing flat bars with `V>0` (limit-locked) → NO warning (signature needs
  `V==0`).
- **Fully-phantom series:** every bar phantom → warns, `last_real_date == "none in window"`.
- **Interval gate:** the same phantom-tail series at `Interval.H1` → NO warning (D1-only).
- **Liquidity propagation:** `LiquidityProfile` built from a phantom-tail history carries the warning
  through (no new code; assert the inherited warning — `tests/test_liquidity.py`).
- **No double-warn / order:** coexists cleanly with `partial_end_coverage` (both may appear).

## 8. Out of scope for v1 (design-eval follow-ups)
- **Trim** the phantom tail — riskier (silently dropping bars can drop legit halted data). Only on a
  strong signature, conservative, and warned, or opt-in. Default v1 = warn, not drop.
- **Cross-source coverage reconciliation** — the failover engine returns different source/coverage by
  window (vps phantom-end vs ssi real-end), giving non-reproducible histories. Bigger design
  (source-selection determinism) related to the unit-homogeneity guard. The v1 warning mitigates the
  worst harm meanwhile.
- **Intraday (H1/M*)** phantom semantics (zero-volume bars are normal off-hours) — v2.

## 9. Open questions for the reviewer
- **Q1 (threshold):** ratify `THRESHOLD = 10` D1 bars, or pick 5 / 14 per §4?
- **Q2 (warning token):** `stale_or_delisted_tail` good, or prefer e.g. `trailing_zero_volume_tail`
  (more mechanical, less interpretive — the cause is inferred)?
- **Q3 (signature strictness):** require only `V==0 AND O==H==L==C` per bar (my pick), or ALSO require
  the flat value to equal the last real close (stronger forward-fill proof, but misses drifted fills)?
- **Q4 (liquidity):** v1 just propagates the warning into `LiquidityProfile.warnings`. Acceptable, or
  do you want ADV to exclude the phantom tail now (that's effectively the trim follow-up)?
