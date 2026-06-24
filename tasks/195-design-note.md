# #195 design note — `vnfin.equities` GICS sector classification (clean-room, derived)

**Status:** design-note-first → awaiting reviewer GATE before any code.
**Spec:** `/tmp/spec-195.md` (tech-lead packet, ACCEPTED, source CONFIRMED clean).
**Clean-room:** ZERO vnstock. Derive GICS sector by inverting the 10 VNAllShare sector baskets vnfin
already fetches. Do NOT adopt vnstock's `industryID`/`industryIDv2`/Vietnamese `industry_name`.

---

## 0. Fact-check (all claims verified in-repo before this note)

| Claim | Verified | Anchor |
|---|---|---|
| 10 sector codes registered | ✅ VNCOND,VNCONS,VNENE,VNFIN,VNHEAL,VNIND,VNIT,VNMAT,VNREAL,VNUTI | `vnfin/_contracts/index_registry.py:80-91` |
| Derivation feasible (no allow-list gate on constituents) | ✅ `get_constituents` canonicalizes then passes straight to `/stock/group/{group}`; "VNFIN" passes the same gates as "VN30" (the registry deny-list is price/history-only) | `vnfin/indices/sources.py:167-173` |
| Provenance string | ✅ `IndexConstituentsSource.NAME == "ssi_iboard_query"` (== spec `sector_source`) | `vnfin/indices/sources.py:155` |
| Basket member shape | ✅ `IndexMember(symbol, exchange, company_name, isin, weight=None)`, symbols canonicalized + dedup'd within basket | `vnfin/indices/sources.py:194-219` |
| Baskets are current-snapshot (survivorship) | ✅ always-on `current_snapshot_only` warning on every basket | `vnfin/indices/sources.py:235-238` |
| `EquitySecurity` frozen, 8 fields, additive-safe | ✅ `@dataclass(frozen=True)`, fields end at `currency` | `vnfin/equities/models.py:18-38` |
| `profile`/`sectors`/`by_sector` do NOT exist; `profile` documented DEFERRED | ✅ facade exports only `source`/`client`/`universe` | `vnfin/equities/__init__.py:27-34`, docstring :3-7 |
| `sector_not_available` always-on per board today | ✅ `_board_warnings` | `vnfin/equities/sources.py:202-209` |
| Warning-token tuple length | ✅ **48** (not 37) → lockstep `sector_partial_coverage` takes it **48→49** | `tests/test_docs_contract.py` `_WARNING_TOKENS_180` |
| Surface test is additive-subset (no mid-feature regen) | ✅ only `breaking` diffs fail; additive printed + folded at release | `tests/test_public_api_surface.py:273-286` |
| Cache precedent to mirror | ✅ AlphaVantage `cache_ttl` (6h) per-instance | `vnfin/indices/world_sources.py:74,146-157` |

---

## 1. Derivation + caching (confirm-point 1)

**Derivation.** A new component `vnfin/equities/sectors.py :: SectorClassifier` owns the clean-room map:

1. Fetch the 10 sector baskets **once** via `IndexConstituentsSource.get_constituents(code)` for
   `code ∈ {VNFIN, VNIT, VNREAL, VNMAT, VNCONS, VNCOND, VNIND, VNENE, VNHEAL, VNUTI}`.
2. **Invert membership** → `dict[symbol → sector_code]`. Each basket's members are already
   canonicalized + intra-basket-dedup'd by the constituents source.
3. `classify(symbol) → (sector_code, sector_name, "GICS", "ssi_iboard_query") | None`.

**Injection / testability (TDD).** `SectorClassifier(fetch_constituents=...)` takes an injected
constituents callable (default = a private `IndexConstituentsSource(...).get_constituents`). Tests inject
synthetic baskets (`{"VNFIN": ["AAA","BBB"], "VNIT": ["CCC"], ...}`) — **CI never hits iboard**. This is
the equities→indices composition seam; equities depends on the indices *source*, not vice-versa.

**Caching.** Mirror the AV per-instance TTL cache: build the inverted map **lazily on first sector
access**, cache it on the classifier instance, TTL-bounded (`_SECTOR_MAP_CACHE_TTL`, propose 6h to match
AV). One build (10 fetches) then serves `profile`/`by_sector`/`universe`-enrich/`sectors` for the
instance's lifetime. **Honesty:** the map is built from **current** baskets (`current_snapshot_only`),
so the derived sector is the symbol's *current* GICS sector, not point-in-time — disclosed in docs.

---

## 2. Honest-coverage contract — the core never-silent invariant (confirm-point 2)

- Baskets are **HOSE-only, partial** (spec: ~74%, ~297/403 HOSE). HNX/UPCoM have **no** GICS basket here.
- An **unmapped HOSE symbol** and **every HNX/UPCoM symbol** → **all four** sector fields `None`. **NEVER
  fabricate or guess.** (Reconciles the spec's two statements: the field block types scheme/source as
  `str` for the *mapped* case; the coverage contract says *None-on-all-four* when unmapped — so the
  dataclass makes all four `Optional[str] = None`, populated as a unit.)
- **One new never-silent token, `sector_partial_coverage`** (full #180/#188 lockstep), present on any
  result that carries derived sector data. Mirrors the existing `sector_not_available` honesty pattern.
  The exact % is **never pinned in code** — the contract is "HOSE-only / partial / None-elsewhere /
  never-fabricated," not a magic number (per `staleness-warning-prefer-bounded-false-positive` family:
  encode the invariant, not a tuned constant).
- **Two-basket symbol** (should not happen for GICS L1): **degrade-not-fabricate → `None`** (refuse to
  pick), deterministically (stable None across runs), **flagged** under the *same* `sector_partial_coverage:`
  prefix with a distinct detail (`sector_partial_coverage: <SYM> in N baskets (...) → null`). Using one
  documented **prefix** for both the always-on coverage line and the conditional overlap line keeps the
  lockstep at exactly **+1** token (the #188 scanner / `_covered()` match on prefix). **Never silently picked.**

---

## 3. Clean field shape — HOSE GICS naming, NOT vnstock's (confirm-point 3)

4 additive `Optional[str] = None` fields on `EquitySecurity`, after `currency` (frozen → additive → snapshot-safe):

```python
sector_code:   Optional[str] = None   # "VNFIN".."VNUTI"     (None if unmapped)
sector_name:   Optional[str] = None   # GICS L1 English        (None if unmapped)
sector_scheme: Optional[str] = None   # "GICS"  when mapped, else None
sector_source: Optional[str] = None   # "ssi_iboard_query"     when mapped, else None
```

**Pinned GICS L1 code→name map** (public MSCI/S&P standard names — clean-room safe, a module constant
`_GICS_L1` in `vnfin/equities/sectors.py`): VNFIN=Financials · VNIT=Information Technology · VNREAL=Real
Estate · VNMAT=Materials · VNCONS=Consumer Staples · VNCOND=Consumer Discretionary · VNIND=Industrials ·
VNENE=Energy · VNHEAL=Health Care · VNUTI=Utilities. **No** `industryID`/`industryIDv2`/`industry_name`.

---

## 4. API surface — v1 GICS L1 only, honestly no finer tier (confirm-point 4)

- **`equities.profile(symbol)`** → the symbol's 4 sector fields (None if unmapped) + the coverage token.
  *(This un-defers the documented-deferred `profile`; docstring + docs updated in the same change.)*
- **`equities.sectors()`** → the 10 GICS `(code, name)` pairs. **Static from `_GICS_L1` — no fetch, no token.**
- **`equities.by_sector(code_or_name)`** → the basket members (`by_sector("VNFIN")` ≡ `by_sector("Financials")`,
  case-insensitive name→code reverse lookup). HOSE-only by nature; carries the coverage token.
- **`EquitySecurity` enrichment** — the 4 fields exist always (default None); **populated** when sector
  data is requested. See gate-Q1 for *when* `universe()` populates them.
- **NO `industries()`/`by_industry()` tier** — no clean finer data exists; do not imply data we lack.
  **`industry_peers(symbol)` DEFERRED** — a thin `by_sector(profile(symbol).sector) − self` filter; out of
  the v1 data-primitive scope.

---

## 5. Open gate questions (my recommendation first)

- **Q1 — `universe()` enrichment: always-on vs opt-in?** Always-on adds **10 basket fetches** to every
  `universe()` call (cost + token-meaning collision with `sector_not_available`). **REC: opt-in
  `universe(..., with_sector=True)`.** Plain `universe()` stays byte-for-byte as today (cheap, still emits
  `sector_not_available` — the raw payload genuinely lacks sector). The `with_sector=True` path enriches +
  emits `sector_partial_coverage`. `profile`/`by_sector` always populate. This **partitions the two tokens
  cleanly by path** (both stay emitted → #180 bijection intact) and avoids surprising a plain `universe()`
  caller with 10 extra HTTP calls. *(If you prefer the spec's literal "enrich the universe rows" as
  always-on, I'll make it always-on + lazy-cached and refine `sector_not_available` → "derived separately".)*
- **Q2 — overlap disclosure: fold under `sector_partial_coverage:` prefix (REC, +1 token) vs a distinct
  token (+2 lockstep)?** REC fold — overlap is "should not happen for GICS L1," and prefix-sharing keeps
  the honesty (None + named symbols) at one documented token.
- **Q3 — cache TTL.** REC 6h to match the AV precedent; lazy build, per-instance. (Or "build-once, no TTL"
  if you'd rather a sector map never refetch within a process — your call.)

---

## 6. Test matrix (offline synthetic baskets; CI never live)

1. Known symbol in VNFIN basket → `sector_code="VNFIN"`, `sector_name="Financials"`, scheme/source set;
   `_GICS_L1` correct for **all 10** codes.
2. Unmapped HOSE symbol → all 4 fields `None` + `sector_partial_coverage` present; **never fabricated**.
3. HNX/UPCoM symbol → `None` + coverage token (no basket exists).
4. `by_sector("VNFIN")` ≡ `by_sector("Financials")` → basket members; `sectors()` → exactly the 10 `(code,name)`.
5. Coverage token present **whenever** sector data is served.
6. **Overlap:** symbol synthesized into 2 baskets → `None` (not picked) + `sector_partial_coverage: <sym>
   in N baskets` detail; **deterministic** (stable None across re-runs).
7. **Caching:** building the map fetches **each of the 10 baskets exactly once**; a 2nd sector call reuses
   the cache (assert fetch-count==10 / no 2nd network).
8. **Token lockstep:** `sector_partial_coverage` in tuple (48→49) + SKILL.md row + literal sink in the same
   commit; #180 bijection + #188 forward-scanner green; the prefix covers BOTH emission sites.
9. **Snapshot additive-green (NO regen):** EquitySecurity +4 optional fields + new methods → only additive
   diffs; `test_live_surface_introduces_no_breaking_changes` passes. Fold the baseline at release, not now.
10. **Offline only:** injected `fetch_constituents` / synthetic baskets; assert zero network in CI.

---

## 7. Docs / deliverable order

`docs/api.md` (sector primitives + HOSE-only/GICS/None contract + current-snapshot caveat) · a `docs/sources/`
provenance note (derived from VNAllShare sector indices via SSI iboard-query; GICS scheme; runtime-fetch,
no redistribution; survivorship/current-membership) · SKILL.md token row · CHANGELOG (`### Added`) · un-defer
`profile` in the equities docstring. Public surface additive only; **snapshot frozen** (no genuinely-new
*field type* forces a regen — all 4 are `Optional[str]`).

**Order:** this note → reviewer GATE (rule on Q1–Q3) → TDD per the matrix → merged-tree green + Codex×2 →
push + close #195.
