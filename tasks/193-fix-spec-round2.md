# #193 FIX SPEC — round 2 (Codex×2 BLOCK on c79325a)

**Authority:** `~/tools/vnfin-oss-reviewer/reviews/review-202606241450-issue193-codex2-verdict-BLOCK.md`.
Base commit `c79325a` (AV-only paths + all gate housekeeping are CORRECT — DO NOT touch the token tuple,
snapshot, caveats, MissingKey/AllSourcesFailed/Q5 logic, or any AV-only test). The 3 blockers are ALL in the
**Stooq-fallback + client-reuse seam**. Fix B1+B2+B3 in **ONE commit**. TDD: add the failing regression tests
FIRST (they currently pass-by-omission), confirm they reproduce the defect, then fix. **Keep SPY behavior
byte-for-byte unchanged.** Runner `.venv/bin/python -m pytest`.

---

## ROOT CAUSE (why it shipped)
The AV source was generalized per-symbol, but `StooqIndexSource` still hard-fetches `^spx` for ANY symbol and
`StooqIndexSource.supports()` returns `True` unconditionally (`world_sources.py:359-360`). Every #193 test used
AV-only `sources=[src]` or a *walled* Stooq — so **non-SPY symbol + WORKING Stooq was never exercised**. On that
path `world("^N225")` returns S&P 500 (`^SPX`) data relabeled `symbol="^N225"`, `proxy_for=None`, no
`proxy_substitution` — the Q2 structured guard misreports a wrong-MARKET series as clean/direct.

---

## B1 + B2 — Stooq may serve ONLY the SPY (S&P 500) market

`^SPX`/Stooq is the S&P 500 index; it is a legitimate fallback ONLY for `SPY` (same market). For
`QQQ`/`^N225`/`^SSEC`/`^STI`, AlphaVantage is the **sole** source; on AV failure the call must raise NAMING the
symbol (`MissingKey` no-key / `AllSourcesFailed` key-set / `InvalidData` empty-or-error) — **never fall through
to `^SPX`**.

**Fix 1 (primary gate) — `StooqIndexSource.supports` (`world_sources.py:359-360`):**
```
def supports(self, symbol=None) -> bool:
    # Stooq serves only ^SPX (S&P 500 index points) — a legitimate fallback ONLY for SPY
    # (same market). For QQQ/^N225/^SSEC/^STI the engine must skip Stooq so AV is the sole
    # source and a non-SPY AV failure raises naming the symbol (never relabels ^SPX). #193 B1.
    return AlphaVantageIndexSource._canonical_symbol(symbol) == _PROVIDER_SPY
```
(`_canonical_symbol(None/"")` → `"SPY"`, so `supports()`/`supports(None)` stay True — preserves the
direct-source default + the SPY chain. `supports("QQQ"/"^N225"/...)` → False → engine skips Stooq for them.)

**Fix 2 (defense-in-depth) — `StooqIndexSource.get_history` (`world_sources.py:362-396`):** before fetching,
refuse a non-SPY symbol instead of relabeling `^SPX`:
```
canonical = AlphaVantageIndexSource._canonical_symbol(symbol)
if canonical != _PROVIDER_SPY:
    raise InvalidData(
        f"{self.NAME}: {canonical}: this source serves only the S&P 500 (SPY / ^SPX index "
        f"points); it is not a valid source for {canonical}")
```
This makes a silent wrong-MARKET relabel structurally impossible even on a direct `get_history` call (not just
via the engine skip). Keep the rest of `get_history` (the SPY→^SPX serve + `fallback_instrument_served`) intact.

**Fix 3 (B2, name the symbol on empty-window) — AV source `world_sources.py:248`:** the empty-window
`EmptyData` must name the symbol (extends the Q5 "name the symbol" rule to the empty path):
```
raise EmptyData(f"{self.NAME}: {canonical}: no daily bars in requested window")
```
(Type stays `EmptyData` — for SPY this still legitimately falls over to Stooq `^SPX`; for non-SPY, Stooq is now
incapable so the engine raises `AllSourcesFailed` naming the symbol. Do the same symbol-naming on the Stooq
`get_history` empty-window `EmptyData` at `:384` for consistency: `f"{self.NAME}: {canonical}: no daily bars ..."`.)

---

## B3 — make the failover client STATELESS (drop `self._requested_symbol`)

The engine `FailoverClient.run(*args, **kwargs)` forwards args to every closure
(`operation(src, *args)`, `capability(src, *args)`, `failure_factory(attempts, *args)`,
`finalize(result, attempts, *args)`). So thread `symbol` as the **first positional arg through `run`** — no
instance state. `world_client.py`:

**`__init__`** — drop the `self._requested_symbol` line; change the closures to accept `symbol`:
```
self._engine = FailoverClient(
    list(sources),
    operation=lambda src, symbol, start, end, interval: src.get_history(
        symbol, start, end, interval=interval),
    capability=lambda src, symbol, start, end, interval: src.supports(symbol),
    unit_of=lambda src: None,
    provenance_of=lambda hist: getattr(hist, "source", None),
    max_attempts=max_attempts,
    failure_factory=lambda attempts, symbol, start, end, interval: AllSourcesFailed(
        symbol, getattr(interval, "value", str(interval)), attempts),
    finalize=self._finalize,
)
```
**`get_history`** — pass `canonical` as the first positional arg; remove the `self._requested_symbol = canonical`
write; keep the MissingKey/AllSourcesFailed branch exactly as-is:
```
canonical = _validate_symbol(symbol)
try:
    hist = self._engine.run(canonical, start, end, interval)
except AllSourcesFailed:
    if not any(getattr(s, "has_key", False) for s in self.sources):
        raise MissingKey(canonical) from None
    raise
if hist.symbol != canonical:
    hist = replace(hist, symbol=canonical)
return hist
```
**`_finalize`** — add `symbol` to the signature (the engine now passes it):
```
def _finalize(self, hist, attempts, symbol, start, end, interval) -> PriceHistory:
    warnings = tuple(hist.warnings) + self._substitution_warnings(hist) + self._proxy_warnings(hist)
    return replace(hist, attempts=attempts, warnings=warnings)
```
`self.sources` (the `@property` returning `self._engine.sources`) and the `max_attempts` property are unchanged.
After this there is **no per-call mutable state** → the public `FailoverWorldIndexClient` /
`default_world_index_client` are concurrency-safe. (Optional: add a one-line "stateless / safe to reuse across
threads" note to the class docstring — replacing any "fresh client per call" implication.)

---

## Behavior traces to preserve (verify each)
- `world("^N225")` no key → AV incapable + Stooq incapable (SPY-only) → no capable → `AllSourcesFailed(^N225)` →
  caught, no key → **`MissingKey("^N225")`** (names env var + symbol). ✓
- `world("^N225")` key set, AV throttled, **WORKING Stooq** → only AV capable → AV fails →
  **`AllSourcesFailed("^N225")`** — Stooq NEVER serves `^SPX`. ✓ (B1 fixed)
- `world("^N225")` key set, AV empty-window → `EmptyData("...^N225...")` → no other capable →
  **`AllSourcesFailed("^N225")`**, no `^SPX`. ✓ (B2 fixed)
- `world("SPY")` no key + working Stooq → Stooq capable → serves `^SPX`, `symbol="SPY"`,
  `fallback_instrument_served`. ✓ (unchanged)
- `world("SPY")` key, AV throttled + working Stooq → Stooq serves `^SPX` + `fallback_instrument_served`. ✓
- `world("SPY")` no key + walled Stooq → `MissingKey("SPY")`. ✓ (unchanged)

---

## REQUIRED NEW TESTS (`tests/test_indices_world.py`) — the coverage gap (RED first)
Add a `_stooq_csv()`-backed WORKING-Stooq leg helper (one exists: `_stooq_source(_stooq_csv())`).
1. **B1 — non-SPY + working Stooq never serves ^SPX (per symbol QQQ/^N225/^SSEC/^STI):**
   - key set + throttled AV (`{"Note":"throttled"}`) + WORKING Stooq → raises `AllSourcesFailed`, `asked in str`,
     and assert NO `PriceHistory` returned (the raise is the assertion). Belt-and-suspenders:
     `assert _stooq_source(_stooq_csv()).supports(asked) is False`.
   - no key + WORKING Stooq → raises `MissingKey`, `"ALPHAVANTAGE_API_KEY"` + `asked` in `str`.
2. **B2 — empty-window for a proxy symbol** (valid AV envelope whose bars all fall OUTSIDE the requested
   window) + key set → raises naming the symbol (`AllSourcesFailed` with `asked in str`), NO `^SPX` fallover.
3. **B3 — stateless / no leftover state:**
   - `assert not hasattr(default_world_index_client(sources=[_av_source(_av_payload())]), "_requested_symbol")`.
   - Shared-client correctness: on ONE client built with AV serving, call `get_history("QQQ")` then
     `get_history("^N225")` (give the AV stub per-call payloads via the recorder/lambda) and assert each returns
     its OWN symbol + `proxy_for` (proves no cross-call state bleed).
4. **SPY regression intact:** explicitly assert `StooqIndexSource(...).supports("SPY") is True` and that the
   existing keyless/throttled SPY→^SPX `fallback_instrument_served` path still works (the existing tests cover
   this — confirm none break).

## Acceptance (green merged tree)
- `.venv/bin/python -m pytest -q` FULL suite green (all prior #193 tests + the new ones).
- Snapshot `public_api_v0_2_0.json` UNMODIFIED (do NOT run `dump_api_surface.py`); token tuple still 47.
- `grep -rn "_requested_symbol" vnfin/` → 0 hits (state removed).
- No new wrong-market path: for every non-SPY symbol there is NO input that returns a `^SPX` series.
- Zero VNStock; no secrets. Return a diff/summary; do NOT push, close, or message the reviewer.
