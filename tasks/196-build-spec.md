# Build spec — #196 public ANNUAL precious-metals history (silver + platinum)

**Status:** GATE PASSED (`reviews/gate-202606251627-issue196-design-note.md`). Build now, TDD RED-first.
**Binding inputs:** this spec + `tasks/196-design-note.md` + the gate file + the tech-lead spec
`~/tools/vnfin-oss-reviewer/tasks/196-precious-metals-spec.md`. Where they differ, THIS spec wins; if
this spec is silent, the gate wins.
**Do NOT push, do NOT close the issue, do NOT message the reviewer.** Return a diff + summary; the
orchestrator integrates, verifies the merged tree, adversarial-verifies, and routes to Codex×2.

## Runner & environment (read before coding)
- Tests: `.venv/bin/python -m pytest`. **Pytest summary/per-test lines VANISH through pipes in this
  shell (a TTY-control plugin) — EXIT CODES ARE AUTHORITATIVE (0 = all passed).** Do not conclude from
  absent "passed" text; check `echo $?`.
- Never use `git add -A` (private gitignored paths). Use explicit `git add <path>` / `git add -u`.
- Zero vnstock anywhere (search/import/cite/port). World Bank only.
- Do NOT run `scripts/dump_api_surface.py` to regenerate the baseline. Do NOT edit
  `tests/snapshots/public_api_v0_2_0.json`. (Release-only task.)

---

## What you are building (one paragraph)
A new **public** domain `vnfin/metals/` serving **annual USD/oz history for Silver and Platinum** from
the SAME World Bank CMO "Pink Sheet" xlsx the internal gold annual source already parses. The xlsx
parser is **extracted once** to `vnfin/_contracts/worldbank_cmo.py` and shared; gold keeps its exact
observable behaviour. Silver/Platinum get their OWN evidence-based plausibility bands.

---

## STEP 1 — Extract the shared parser to `vnfin/_contracts/worldbank_cmo.py`

Create `vnfin/_contracts/worldbank_cmo.py` containing the **domain-neutral** xlsx machinery, moved
verbatim from `vnfin/gold/worldbank_cmo.py` (do not change behaviour):
- Constants: `_NS`, `_REL_NS`, `_PKG_REL_NS`, `_SHEET_NAME = "Annual Prices (Nominal)"`,
  `_USD_PER_OZ = "USD/oz"`, `_CELL_REF_RE`, `_YEAR_RE`, and `_CMO_ANNUAL_URLS` (the vintage-URL tuple —
  move it here; gold re-exports it, see Step 2).
- Helpers (verbatim): `_local`, `_col_index`, `_parse_ref`, `_shared_strings`,
  `_resolve_worksheet_path`, `_cell_text`.
- New spec object:
  ```python
  @dataclass(frozen=True)
  class MetalSpec:
      product: str            # "XAU" | "XAG" | "XPT"
      name_row: str           # split-header NAME cell: "Gold" | "Silver" | "Platinum"
      min_usd_oz: float       # per-metal plausibility band (Step 3)
      max_usd_oz: float
      units_row: str = "($/troy oz)"   # shared across all three metals
  ```
- Generalized coercion + parser (parameterized by `spec`; KEEP every existing guard — gate cond. (c)):
  ```python
  def coerce_price(text, year: int, spec: MetalSpec) -> float:
      # numeric, finite, positive, AND spec.min_usd_oz <= price <= spec.max_usd_oz.
      # InvalidData messages must NAME the metal (spec.name_row / spec.product) and the band.

  def parse_cmo_annual(raw: bytes, spec: MetalSpec) -> dict:
      # identical mechanics to _parse_cmo_annual_gold but:
      #  - match the split header by spec.name_row + spec.units_row (same column)
      #  - read the matched column; coerce with coerce_price(..., spec)
      #  - KEEP: rels-resolved worksheet (never hard-coded index), finite/positive guard,
      #    DUPLICATE-year guard, NON-MONOTONIC-year guard, EmptyData/InvalidData fail-safe.
      #  - "column absent" (name+units not found) → InvalidData naming the metal (as today).
  ```
  Preserve the existing two-branch "found a name header but no units below" vs "no header at all"
  diagnostics, generalized to `spec.name_row`/`spec.units_row`.

## STEP 2 — Re-point gold to the shared parser (gold OUTPUT byte-for-byte identical)

Edit `vnfin/gold/worldbank_cmo.py`:
- Import from the shared module: `from .._contracts.worldbank_cmo import (MetalSpec, parse_cmo_annual,
  _CMO_ANNUAL_URLS, _USD_PER_OZ)` (and any helper names other modules/tests reference).
- Define `_GOLD_SPEC = MetalSpec(product="XAU", name_row="Gold", min_usd_oz=20.0, max_usd_oz=10000.0)`
  (band unchanged — `_GOLD_MIN_USD_OZ`/`_GOLD_MAX_USD_OZ` may stay as module constants feeding the spec
  so nothing else breaks).
- **Keep `_parse_cmo_annual_gold` as a thin delegator** so the existing gold test file is UNCHANGED:
  ```python
  def _parse_cmo_annual_gold(raw: bytes) -> dict:
      return parse_cmo_annual(raw, _GOLD_SPEC)
  ```
  `_fetch_annual` keeps calling `_parse_cmo_annual_gold(raw)` (so the test monkeypatch at
  `tests/test_worldbank_cmo_gold.py:566` of `vnfin.gold.worldbank_cmo._parse_cmo_annual_gold` still
  works). `WorldBankCmoGoldSource` (NAME, constructor, `get_history` → `GoldHistory(product="XAU")`)
  is UNCHANGED. `_CMO_ANNUAL_URLS` must remain importable as `vnfin.gold.worldbank_cmo._CMO_ANNUAL_URLS`
  (re-export — `tests/test_no_secrets.py:79` and `tests/test_worldbank_cmo_gold.py:29` import it from
  there; the no-secrets allowlist is by-value so the literal living in `_contracts` is still covered).
- **HARD: `vnfin/gold/` tests, `world_reference.py`, and the gold output must not change.** Do not edit
  `tests/test_worldbank_cmo_gold.py` or `tests/test_gold_world_reference.py`.

## STEP 3 — Per-metal bands (evidence-based; gate-approved, do not alter the numbers)

| Metal | `MetalSpec` band (USD/oz) | real range (fixture 1960–2025) |
|-------|--------------------------|-------------------------------|
| Gold (unchanged) | `[20.0, 10000.0]` | 34.95–3441.51 |
| **Silver** | `[0.10, 75.0]` | 0.91–39.80 |
| **Platinum** | `[50.0, 5000.0]` | 80.93–1719.48 |
```python
_SILVER_SPEC   = MetalSpec(product="XAG", name_row="Silver",   min_usd_oz=0.10, max_usd_oz=75.0)
_PLATINUM_SPEC = MetalSpec(product="XPT", name_row="Platinum", min_usd_oz=50.0, max_usd_oz=5000.0)
```

## STEP 4 — New public domain `vnfin/metals/`

### `vnfin/metals/models.py`
```python
@dataclass(frozen=True)
class MetalBar:
    date: date_type          # Jan-1 of the year (annual)
    price: float             # USD/oz

@dataclass(frozen=True)
class MetalHistory(TimeSeriesResult):   # from ..timeseries import TimeSeriesResult
    product: str             # "XAG" | "XPT"
    unit: str                # "USD/oz"
    currency: str            # "USD"
    source: str              # "worldbank_cmo_metal"
    bars: tuple[MetalBar, ...]
    frequency: str = "annual"
    attribution: str = "Source: The World Bank — Commodity Markets (Pink Sheet)"
    value_unit: Optional[str] = None     # __post_init__: mirror `unit` when None (as GoldHistory does)
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()       # kept for parity/future; v1 emits none
    # _items_attr="bars"; _index_column="date"; _df_columns=("date","price")
    # _row_record(b) -> {"date": b.date, "price": b.price}
    # _df_attrs() -> product/unit/value_unit/currency/source/frequency/attribution
```
Mirror `vnfin/gold/models.py:GoldHistory` exactly for the `TimeSeriesResult` plumbing (so `.to_df()`
works identically). **No new `.warnings` token** (gate cond. e) — `frequency`/`attribution` are typed
fields, not warning strings.

### `vnfin/metals/sources.py`
```python
class WorldBankCmoMetalSource(HttpDataSource):
    NAME = "worldbank_cmo_metal"
    _SPECS = {"silver": _SILVER_SPEC, "platinum": _PLATINUM_SPEC}  # canonical lower-case
    def __init__(self, metal, *, http_get=None, timeout: float = 25.0):
        # canonicalize metal (name or product code); store self._spec
    def get_history(self, start: date, end: date) -> MetalHistory:
        # validate_date_range BEFORE network; fetch via _CMO_ANNUAL_URLS loop (mirror gold's
        # _fetch_annual: per-URL SourceError → next; all-fail → SourceUnavailable);
        # parse_cmo_annual(raw, self._spec); emit Jan-1 MetalBar per year in [lo.year, hi.year];
        # no years in span → EmptyData naming the metal; return MetalHistory(...).
```
Reuse gold's fetch structure (`self._request_bytes(url)`, iterate `_CMO_ANNUAL_URLS`). Keep error
discipline N2 (every recoverable failure a `SourceError` subclass).

### `vnfin/metals/__init__.py`
```python
SUPPORTED_METALS = ("silver", "platinum")
_CANON = {"silver":"silver","xag":"silver","platinum":"platinum","xpt":"platinum"}

def _canon_metal(metal) -> str:
    # str/non-empty check; lower-case; map XAG/XPT/name.
    # GOLD specifically → InvalidData ROUTING to vnfin.gold (gate ruling 2):
    #   "gold annual history is served via vnfin.gold (world_reference_history_vnd), not
    #    metals.history; metals.history supports: silver, platinum"
    # any other unknown (palladium/XPD/copper/...) → InvalidData naming it + listing SUPPORTED_METALS.

def history(metal, start, end, *, http_get=None, timeout: float = 25.0) -> MetalHistory:
    return WorldBankCmoMetalSource(_canon_metal(metal), http_get=http_get, timeout=timeout)\
        .get_history(start, end)

def source(metal, *, http_get=None, timeout: float = 25.0) -> WorldBankCmoMetalSource:
    return WorldBankCmoMetalSource(_canon_metal(metal), http_get=http_get, timeout=timeout)

__all__ = ["MetalBar", "MetalHistory", "history", "source", "SUPPORTED_METALS"]
```
`metal` accepts name ("silver"/"platinum", case-insensitive) or product code ("XAG"/"XPT").
`start`/`end` are `datetime.date` only (gate ruling 3 — no year-int overload).

## STEP 5 — Tests (`tests/test_metals.py`) — TDD, RED-FIRST per invariant
Reuse the synthetic xlsx builder pattern from `tests/test_worldbank_cmo_gold.py` (`_build_cmo_xlsx` /
`_col_letters`) — build a synthetic sheet with Gold(67)/Platinum(68)/Silver(69) columns so you can
also feed a wrong column under a metal's identity. Use the committed real fixture
`tests/fixtures/cmo/CMO-Historical-Data-Annual.xlsx` for the real-layout cases. Injected `http_get`
returns the xlsx bytes — NO network. The matrix (maps to gate (a)–(f) + spec tests 1–6):

1. **Parse correctness (real fixture):** silver 2025≈39.80 & 2024≈28.27 (XAG); platinum 2025≈1278.29 &
   2024≈955.17 (XPT). And **gold value-identity (gate a):** `WorldBankCmoGoldSource().get_history` over
   a wide span still yields gold 2025≈3441.51, 2024≈2387.70 — assert against the SAME parsed dict
   pre/post (a dedicated regression in `tests/test_metals.py` is fine; do NOT edit the gold test file).
2. **Band RED on the band (gate b) — prove RED by widening, not ImportError:** feed a synthetic sheet
   whose silver column holds gold's value 3441.51 under the "Silver" header → `history`/`source` for
   silver raises `InvalidData` (3441.51 > 75). Symmetric: platinum column holding silver's 39.80 →
   `InvalidData` (39.80 < 50). To prove the test fails for the right reason, confirm it goes GREEN only
   because of the band (e.g. a comment showing that widening the band to `[0, 1e9]` would let it
   through — you may include a parametrized check that a value INSIDE the band parses).
3. **Unsupported metal (gate d):** `history("palladium", ...)` / `"XPD"` / `"copper"` → `InvalidData`
   naming the metal, BEFORE any network (assert no http_get call). `history("gold", ...)` → `InvalidData`
   whose message routes to `vnfin.gold` (gate ruling 2).
4. **Result metadata (never-silent):** a served `MetalHistory` has product∈{XAG,XPT}, unit="USD/oz",
   value_unit="USD/oz", currency="USD", source="worldbank_cmo_metal", frequency="annual",
   attribution startswith "Source: The World Bank", `fetched_at_utc` set (tz-aware).
5. **Column-absent vintage (gate d):** a synthetic sheet missing the Silver column → `InvalidData`
   (or `EmptyData`) naming silver; never returns platinum's/gold's column relabelled.
6. **Frozen + df:** `MetalHistory`/`MetalBar` frozen (FrozenInstanceError on mutation); `.to_df()` (if
   pandas available in env) yields date/price rows — mirror the gold history df test if present.

## STEP 6 — Public-surface lockstep (gate e) + recon doc (gate f)
- `scripts/dump_api_surface.py`: ADD `"vnfin.metals"` to `DOMAIN_MODULES` (L34–48). REQUIRED — a new
  top-level module is NOT auto-discovered.
- `tests/test_public_api_surface.py`: ADD an additive-capture test mirroring the news/liquidity/
  diagnostics ones (≈L412/424/392): `live = build_surface(); assert "vnfin.metals" in live["modules"]`
  and assert `MetalBar`,`MetalHistory`,`history`,`source`,`SUPPORTED_METALS` present in `["all"]`.
  The main no-breaking assertion must show metals as **additive** vs the baseline (which lacks it).
  **Do NOT regen** `public_api_v0_2_0.json`.
- `docs/sources/cmo-gold-annual.md` → generalize to a multi-metal CMO source doc (rename to
  `docs/sources/cmo-annual.md` and update any references, OR keep the filename and broaden the title —
  pick the lower-churn option; if you rename, grep for inbound links and fix them). Document: the three
  columns (Gold 67 / Platinum 68 / Silver 69 — note index is vintage-unstable, matched by split-header
  text), units (USD/oz), per-metal bands (with the silver-ceiling-below-platinum-floor rationale),
  CC-BY 4.0 attribution, annual-only/runtime-fetch.
- `docs/api.md`: add `vnfin.metals.history(metal, start, end)` → `MetalHistory` (+ `source`,
  `SUPPORTED_METALS`); state never-fabricate (unsupported → raises naming metal; gold routes to
  vnfin.gold) + never-silent (frequency/attribution).
- `skills/vnfin/SKILL.md`: add the metals entry in lockstep (usage + return type + supported metals +
  annual-only + attribution).
- `CHANGELOG.md`: add an entry under the unreleased/next section (additive: new `vnfin.metals` domain).

## STEP 7 — Verify the WHOLE tree green (you, before returning)
```
.venv/bin/python -m pytest -q ; echo "FULL_SUITE_EXIT=$?"
.venv/bin/python -m pytest -q tests/test_metals.py tests/test_worldbank_cmo_gold.py \
  tests/test_gold_world_reference.py tests/test_public_api_surface.py tests/test_docs_contract.py \
  tests/test_no_secrets.py ; echo "GATE_FILES_EXIT=$?"
git --no-pager diff --stat tests/snapshots/public_api_v0_2_0.json   # MUST be empty (no regen)
grep -rin "vnstock" vnfin/ tests/ docs/ skills/ scripts/ CHANGELOG.md | grep -v "blacklist" || echo "NO_VNSTOCK_OK"
```
All exits 0; snapshot diff empty; no vnstock. If the docs-contract or #180/#188 tests reference a token
count, confirm `_WARNING_TOKENS_180` is still **49** (no new token added).

## Deliverable
Return: (1) the list of files created/edited, (2) the two EXIT codes from Step 7, (3) confirmation the
gold test file + snapshot are untouched, (4) any deviation from this spec with its reason. Do not push,
do not close, do not message the reviewer.
