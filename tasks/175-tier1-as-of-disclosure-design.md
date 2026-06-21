# #175 Tier-1 design note — index_constituents as_of + current-snapshot disclosure

**Issue #175** (point-in-time / historical index membership; labels: bug, enhancement).
**This note = Tier-1 ONLY** (the data-integrity "bug" half). Tier-2 (historical PIT lookup +
change-log) and Tier-3 (offline diagnostic + suggested_action fix) are SEPARATE later gates — Tier-2
is source-gated (no clean machine-readable redistributable historical-membership feed exists; HOSE
publishes only date-stamped human PDFs).

## Reviewer pre-flag compliance (2026-06-21 11:18)
- [x] PURELY `as_of` + current-snapshot disclosure — no PIT lookup, no change-log, no new param.
- [x] Provider as-of carried, NEVER fabricated (no `now()`, no fetch-date stand-in).
- [x] Never-silent warning: `index_constituents` is a CURRENT snapshot, NOT point-in-time → backtests
      inherit survivorship / look-ahead bias.
- [x] NO new source. NO signature change. Public-API snapshot stays FROZEN.
- [x] New token rides the #180 reverse (doc↔code) guard AND the #188 forward-discovery guard.

## Current state (ground truth)
- `vnfin/indices/models.py:47` — `IndexConstituents.as_of: Optional[datetime] = None` **already on the
  frozen dataclass** (present in the frozen surface snapshot). Populating it is behavior-only, not a
  surface change.
- `vnfin/indices/sources.py:221-229` — `get_constituents()` returns
  `IndexConstituents(..., as_of=None, warnings=("weights_not_available: SSI group endpoint exposes
  membership only",))`. The `weights_not_available` token is emitted as a **literal in the
  `warnings=(...)` tuple** → this is the #188 forward-discoverable emission site.
- SSI envelope parsed (`sources.py:176-219`): `{"code":"SUCCESS","data":[{stockSymbol, exchange,
  companyNameEn/Vi, isin}, ...]}`. The parser reads `code` + per-member rows ONLY; **no
  envelope-level data/effective date is read or known to exist.** So today `as_of` can only honestly
  be `None`.

## Proposed change (Tier-1, additive + honest)

**A. Disclosure warning — the load-bearing deliverable (always, never-silent).**
Append a second literal to the `warnings=(...)` tuple at `sources.py:228`, emitted on EVERY successful
basket (next to `weights_not_available`):

```
"current_snapshot_only: membership is the CURRENT basket as fetched; NOT a point-in-time/historical "
"snapshot — backtests using it inherit survivorship and look-ahead bias"
```

Token (leading identifier, fact-first per #180 convention) = **`current_snapshot_only`**.
(Naming is the reviewer's to pin — alternative that signals the risk verb-first:
`point_in_time_not_supported`. I lean `current_snapshot_only` since the token names WHAT the result IS,
mirroring `weights_not_available`. Pick one at the gate; the build uses exactly that string.)

**B. `as_of` population — best-effort-if-present, else honest `None`.**
Today the SSI payload exposes no data date, so `as_of` stays `None` (NEVER `now()` / fetch date).
Design supports carrying a provider date IF one is confirmed to exist:
- If a reviewer-authorized one-off live probe of `iboard-query.ssi.com.vn/stock/group/{GROUP}` reveals
  an envelope-level effective/data-date field, parse it into the existing `Optional[datetime]` `as_of`
  (never fabricated; honor the existing `datetime` type — store the data date, e.g. naive/UTC midnight).
- If no such field exists (current evidence), `as_of` remains `None`; the disclosure warning is the
  honest, complete Tier-1 deliverable. **Tier-1 does NOT block on the probe** — ship the warning now;
  add as_of-population only if/when a provider field is confirmed.

## #180 + #188 lockstep (same change)
- Add `current_snapshot_only` to the `## Warning tokens` table in `skills/vnfin/SKILL.md` AND to
  `_WARNING_TOKENS_180` in `tests/test_docs_contract.py` (reverse doc↔code guard). Baseline is **36**
  post-Wave-1 → **37**; gate on the bidirectional sweep, not a magic count
  ([[new-warning-token-must-update-180-reference]]).
- #188 forward-discovery: because the token is emitted as a literal in `warnings=(...)`, the AST
  forward scan already finds it (Shape: tuple-literal). Confirm `discovered == documented` stays a
  bijection on the merged tree (the build runs both guards).

## Snapshot impact — FROZEN
Surface-neutral: `as_of` field already exists; the addition is a string token + a behavior change. No
new symbol, signature, param, type, or field. `tests/snapshots/public_api_v0_2_0.json` byte-unchanged;
surface test additive-green vs the frozen baseline. **Do NOT run `dump_api_surface.py`** (regen is
release-time only).

## TDD test plan (fail-first; synthetic fixtures only; live SSI opt-in/CI-skipped)
Extend `tests/test_indices.py` (and `_constituents_payload` fixture):
1. `test_constituents_emits_current_snapshot_only_warning` — token present on every successful basket
   (fail-first: RED before the literal is added).
2. `test_constituents_as_of_none_when_provider_has_no_date` — current payload (no date field) →
   `as_of is None`, token still present, and `as_of` is NEVER `now()`/fetched_at_utc.
3. (conditional, only if the probe confirms a date field) `test_constituents_as_of_from_provider_date`
   — synthetic payload with the confirmed date key → `as_of` = that date (datetime), never fabricated.
4. Regression: `weights_not_available` token + member parsing/dedup/validation unchanged; `__len__`,
   `symbols`, `has_weights`, `to_dataframe` unaffected.
5. #180 bidirectional guard test stays green WITH `current_snapshot_only` (RED if token missing from
   either SKILL.md table or the tuple).
6. #188 forward-discovery group green: `current_snapshot_only` forward-discovered at
   `vnfin/indices/sources.py`; `discovered == documented`.
7. Surface additive-green vs frozen baseline (no regen).

## Out of scope (separate gates — flagged, not built here)
- **Tier-2** (`index_constituents(index, *, as_of=date)` PIT lookup + `IndexMembershipChangeLog`):
  source-gated → reviewer's source gate (curated effective-dated data file vs defer; HOSE = human PDFs
  only, no PIT API/redistribution grant).
- **Tier-3** (offline `diagnostics.explain_index_constituents` coverage status + fixing the existing
  misleading `suggested_action: "treat membership as point-in-time"` → current-only): cheap, no source;
  its own small gate after Tier-1.
