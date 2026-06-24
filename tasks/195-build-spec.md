# #195 BUILD SPEC (binding) — `vnfin.equities` GICS sector classification

**Authoritative contract for the build. TDD: RED-first → GREEN → refactor-on-green.**
Design note: `tasks/195-design-note.md`. Gate (APPROVED): `~/tools/vnfin-oss-reviewer/reviews/gate-202606250135-issue195-design-note.md`.

## Clean-room (HARD)
ZERO vnstock. Do NOT search/open/read/cite/import vnstock or any derivative. Do NOT adopt
`industryID`/`industryIDv2`/Vietnamese `industry_name`. Derive sector ONLY by inverting the 10
VNAllShare sector baskets via the existing `vnfin.indices.sources.IndexConstituentsSource`.
Synthetic fixtures only — CI never hits iboard (inject `http_get`/the constituents fetcher; assert no network).

## Gate rulings (DECIDED — binding, do not re-litigate)
- **Q1 OPT-IN.** Plain `universe()` stays **byte-for-byte** as today (same warnings incl. `sector_not_available`,
  sector fields `None`, **no** basket fetch). `universe(with_sector=True)` enriches rows + emits
  `sector_partial_coverage` **in place of** `sector_not_available`. Reuse the **cached** map (no per-row refetch).
- **Q2 FOLD.** Overlap (a symbol in ≥2 baskets) → deterministic **`None`, never picked**, disclosed under the
  **same `sector_partial_coverage:` prefix** with a distinct detail naming the symbol + baskets. (+1 token total.)
- **Q3 CACHE.** Lazy, per-instance, **6h TTL** (mirror `_AV_DEFAULT_CACHE_TTL`). Build once (≤10 fetches), reuse.
- **Binding invariants:** unmapped HOSE + EVERY HNX/UPCoM → **all 4 sector fields `None` as a unit, NEVER
  fabricated**; `_GICS_L1` correct for all 10; token lockstep (tuple + SKILL.md row + literal sink) in the SAME
  commit, the prefix covering BOTH sinks; `sectors()` is **static, no fetch**; current-snapshot caveat in docs.
- **Snapshot:** new `profile`/`sectors`/`by_sector` + new types ARE real surface → they show as **additive**
  diffs (non-breaking → `test_live_surface_introduces_no_breaking_changes` PASSES). **DO NOT** edit
  `tests/snapshots/public_api_v0_2_0.json` and **DO NOT** run `scripts/dump_api_surface.py` — the regen is a
  RELEASE task, not this commit.

## `_GICS_L1` pinned map (module constant in `vnfin/equities/sectors.py`) — exact strings, asserted
```
VNFIN  = "Financials"             VNCOND = "Consumer Discretionary"
VNIT   = "Information Technology"  VNIND  = "Industrials"
VNREAL = "Real Estate"            VNENE  = "Energy"
VNMAT  = "Materials"              VNHEAL = "Health Care"
VNCONS = "Consumer Staples"       VNUTI  = "Utilities"
```

## Files

### NEW `vnfin/equities/sectors.py` — `SectorClassifier`
- `__init__(self, *, fetch_constituents=None, cache_ttl=_SECTOR_MAP_CACHE_TTL, clock=...)`.
  `fetch_constituents` is an injected callable `code -> IndexConstituents` (default: a private
  `IndexConstituentsSource(...).get_constituents`). `_SECTOR_MAP_CACHE_TTL = 21600.0  # 6h`.
- `_build_map()` (lazy, cached, TTL-bounded): for each of the 10 codes call `fetch_constituents(code)`,
  invert membership → `dict[symbol -> sector_code]`. A symbol seen in **≥2** baskets → record as **overlap**
  and set its mapping to a sentinel meaning "ambiguous → None" (track overlap symbols + their baskets).
  Each basket fetched **exactly once** per build; subsequent calls within TTL reuse the cached map.
- `classify(symbol) -> Optional[tuple[code, name, "GICS", "ssi_iboard_query"]]`: mapped→4-tuple;
  unmapped/overlap→`None`.
- `overlaps() -> dict[symbol, tuple[code,...]]` (for the disclosure detail).
- `coverage_warnings(...)` / a helper that yields the `sector_partial_coverage:` lines (see Tokens).
- Guard circular imports (equities→indices is one-way; import inside the module top is fine).

### MODIFY `vnfin/equities/models.py`
- `EquitySecurity`: add **after `currency`** (frozen dataclass → additive):
  ```python
  sector_code:   Optional[str] = None
  sector_name:   Optional[str] = None
  sector_scheme: Optional[str] = None   # "GICS" when mapped, else None
  sector_source: Optional[str] = None   # "ssi_iboard_query" when mapped, else None
  ```
- NEW `GicsSector` frozen dataclass: `code: str`, `name: str`.
- NEW `EquitySector` frozen dataclass: `sector_code: str`, `sector_name: str`,
  `sector_scheme: str = "GICS"`, `sector_source: str = "ssi_iboard_query"`,
  `members: tuple[str, ...] = ()` (sorted symbols), `warnings: tuple[str, ...] = ()`.

### MODIFY `vnfin/equities/__init__.py` (facade) + add to `__all__`
- `universe(exchange=None, *, with_sector=False, http_get=None, timeout=25.0) -> EquityUniverse`
  - `with_sector=False` → **identical to today** (no map build, `sector_not_available` retained).
  - `with_sector=True` → enrich each `EquitySecurity` via `dataclasses.replace` with the 4 fields
    (mapped → all 4 set; unmapped/HNX/UPCoM/overlap → all 4 `None` as a unit); per-board warning swaps
    `sector_not_available` → `sector_partial_coverage` (see Tokens); overlap detail line appended once.
- `profile(symbol, *, http_get=None, timeout=25.0) -> EquitySecurity` — fetch the merged (all-board)
  universe **with_sector=True**, return the matching symbol's enriched `EquitySecurity`. Symbol absent
  from every board → raise a clear `EmptyData`/not-found `VnfinError` naming the symbol. **(REVIEW-FOCUS #1:
  profile returns the full enriched row, not a sector-only fragment — reuses EquitySecurity, no half-None.)**
- `sectors() -> tuple[GicsSector, ...]` — **static** from `_GICS_L1` (exactly 10, sorted by code). **No fetch, no token.**
- `by_sector(code_or_name, *, http_get=None, timeout=25.0) -> EquitySector` — resolve `code_or_name`
  (case-insensitive: accept `"VNFIN"` or `"Financials"`; reverse-lookup names via `_GICS_L1`); unknown →
  clear `InvalidData`/`ValueError`. Fetch that one basket via the classifier's constituents fetcher; return
  `EquitySector(code, name, members=sorted(symbols), warnings=(sector_partial_coverage line,))`.

### Tokens — `sector_partial_coverage` (ONE new prefix, two sinks)
- `tests/test_docs_contract.py` `_WARNING_TOKENS_180`: add `"sector_partial_coverage"` → **48→49**
  (place near the equities family, after `sector_not_available`).
- `skills/vnfin/SKILL.md` warning-tokens table: add a row
  `| sector_partial_coverage | equities.profile / by_sector / universe(with_sector) | Derived GICS sector is HOSE-only (~74%); unmapped HOSE + all HNX/UPCoM → null, never fabricated; also flags any multi-basket symbol | #195 |`.
- **Literal sinks (both MUST start `sector_partial_coverage:` so the #180 prefix + #188 forward-scanner cover both):**
  - coverage (per board on `with_sector`; once on `by_sector`/`profile`):
    `f"sector_partial_coverage: {board} — GICS sector derived from VNAllShare baskets (HOSE-only ~74%); unmapped {board} rows → null, never fabricated"`
  - overlap (only when ≥1 symbol in ≥2 baskets):
    `f"sector_partial_coverage: {sym} → null — appears in {n} baskets ({codes}); no unique GICS L1 sector"`
- `sector_not_available` stays emitted on the plain `universe()` path (bijection intact). Both `#180`
  bijection + `#188` forward-scanner MUST stay green.

### Docs (same commit)
- `docs/api.md`: the sector primitives + HOSE-only/GICS/None contract + the current-snapshot caveat.
- `docs/sources/` note: provenance (derived from VNAllShare sector indices via SSI iboard-query; GICS;
  runtime-fetch / no redistribution; survivorship/current-membership).
- `CHANGELOG.md`: `### Added` entry.
- `vnfin/equities/__init__.py` module docstring: **un-defer** `profile` (it now exists).

## Test matrix (RED-first; `tests/test_equities.py` + token in `tests/test_docs_contract.py`)
1. Known symbol in the VNFIN basket → `sector_code="VNFIN"`, `sector_name="Financials"`, scheme/source set;
   `_GICS_L1` correct for **all 10** codes (assert every pair).
2. Unmapped HOSE symbol → **all 4 fields `None`** + `sector_partial_coverage` present; never fabricated.
3. HNX/UPCoM symbol → all 4 `None` + coverage token (no basket).
4. `by_sector("VNFIN")` ≡ `by_sector("Financials")` (case-insensitive) → the basket members; `sectors()` →
   exactly the 10 `GicsSector(code,name)`; unknown sector → clear error.
5. Coverage token present whenever sector data is served (`profile`, `by_sector`, `universe(with_sector=True)`).
6. **Overlap:** a symbol synthesized into 2 baskets → `None` (not picked) + a `sector_partial_coverage: <sym>
   … baskets …` detail; **deterministic** (stable `None` across re-runs).
7. **Caching:** building the map fetches **each of the 10 baskets exactly once** (assert call-count==10); a
   2nd sector call within TTL triggers **no** new fetch.
8. **Token lockstep:** tuple 48→49 + SKILL.md row + literal sinks in this commit; `#180` bijection + `#188`
   forward-scanner green; the prefix covers BOTH emission sites.
9. **Plain `universe()` unchanged:** with `with_sector=False` (default) the result is byte-for-byte as before
   (still `sector_not_available`, sector fields `None`, and **no** basket fetch — assert the constituents
   fetcher is NOT called).
10. **Offline only:** injected `fetch_constituents`/synthetic baskets; assert **zero network** in CI. Snapshot
    additive-green (no regen): `test_live_surface_introduces_no_breaking_changes` passes with only additive diffs.

## Discipline
- RED-first: write each failing test, watch it fail, then minimal code to green. No backfilled tests.
- Full suite green before AND after any refactor; one logical commit per milestone is fine, but deliver the
  feature as a coherent set. Run: `.venv/bin/python -m pytest`.
- **Out of scope:** `industries()`/`by_industry()` (no clean finer data); `industry_peers()` (defer); snapshot regen.
- Commit footer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- Do NOT push, do NOT close the issue, do NOT message the reviewer — return a diff/summary to the orchestrator.
