# Design note — #196 public ANNUAL precious-metals history (silver + platinum)

**Issue:** #196 (reporter `hungle03111987`, 3rd-party; reviewer ACCEPTED, scoped to precious metals).
**Stage:** DESIGN-NOTE-FIRST — this note is the reviewer gate artifact; no code until APPROVE.
**Binding spec:** `~/tools/vnfin-oss-reviewer/tasks/196-precious-metals-spec.md`.
**Grounded in:** `vnfin/gold/worldbank_cmo.py` (read in full), `vnfin/gold/models.py`,
`vnfin/gold/__init__.py`, `vnfin/gold/world_reference.py:44,241` (the only gold-annual consumer),
`vnfin/_contracts/` (shared-internal home), and a direct stdlib probe of the committed fixture
`tests/fixtures/cmo/CMO-Historical-Data-Annual.xlsx` (ranges below are measured, not guessed).

---

## Q1 — Domain placement + public shape

### Recommendation (one line)
**New public domain `vnfin/metals/`** with **new `MetalBar` + `MetalHistory` types** and a thin
facade `metals.history(metal, start, end)`; the xlsx parser is **extracted once** to
`vnfin/_contracts/worldbank_cmo.py` and **shared** (no duplication) by both the existing gold source
and the new metals source. Gold's observable behaviour stays **byte-for-byte identical**.

### 1a. Reuse `GoldHistory` vs new `MetalHistory` → **new `MetalHistory`** (and `MetalBar`)
Justification (the reviewer asked me to justify the type choice):

1. **Public-surface honesty/naming.** `metals.history("silver")` returning a type literally named
   `GoldHistory` is a wart on a clean typed public API (the library's whole ethos). A `MetalHistory`
   with `product="XAG"` reads correctly; `GoldHistory(product="XAG")` does not.
2. **The metals result needs fields gold's doesn't carry.** The never-silent invariant requires every
   result to state **`frequency` (annual)** and the **CC-BY `attribution`**. `GoldHistory`
   (`vnfin/gold/models.py:89`) has neither field. Adding them to `GoldHistory` would mutate the gold
   public surface (snapshot + docs) and risk the *gold-untouched* constraint. A fresh `MetalHistory`
   carries them natively as **typed fields** (stronger than a warning string — always present,
   machine-readable), so **no new `.warnings` token is needed** (#180 table stays at 49; #188 untouched).
3. **Reuse where it matters, distinct where it matters.** `MetalHistory` *mirrors* `GoldHistory`'s
   structure (frozen, `TimeSeriesResult`-derived, `bars: tuple[MetalBar]`, same `.to_df()` ergonomics)
   so callers get identical handling — and the **parser is fully shared**, so there is zero xlsx
   duplication (the reviewer's explicit lean). We reuse the expensive thing (the parser) and keep the
   cheap thing (a 2-field-richer public type) honest.

### 1b. Domain name → **`vnfin/metals/`** (not `commodities/`)
Scope is precious metals only. `commodities` would over-promise energy / agriculture / base-metals,
which the spec explicitly **defers**. Name the domain for what it actually serves.

### 1c. Proposed public API (`vnfin/metals/__init__.py`)
```python
def history(metal, start, end, *, http_get=None, timeout=25.0) -> MetalHistory: ...
def source(metal, *, http_get=None, timeout=25.0) -> WorldBankCmoMetalSource: ...
SUPPORTED_METALS = ("silver", "platinum")          # canonical lower-case names
# __all__ = ["MetalBar", "MetalHistory", "history", "source", "SUPPORTED_METALS"]
```
- `metal` accepts the **name** (`"silver"`/`"platinum"`, case-insensitive) **or product code**
  (`"XAG"`/`"XPT"`). Canonicalised once at the facade.
- `start`/`end` are `datetime.date` bounds (mirrors gold's `WorldBankCmoGoldSource.get_history`);
  emits one Jan-1 `MetalBar` per year in `[start.year, end.year]`. Bounds validated **before** network.
- Returns `MetalHistory` (below). `source()` exposes the underlying source for symmetry with
  `gold.source()` and for injected-`http_get` testing.

### 1d. `MetalBar` / `MetalHistory` (`vnfin/metals/models.py`)
```python
@dataclass(frozen=True)
class MetalBar:
    date: date_type          # Jan-1 of the year (annual)
    price: float             # USD/oz

@dataclass(frozen=True)
class MetalHistory(TimeSeriesResult):
    product: str             # "XAG" | "XPT"
    unit: str                # "USD/oz"
    currency: str            # "USD"
    source: str              # "worldbank_cmo_metal"
    bars: tuple[MetalBar, ...]
    frequency: str = "annual"                                  # never-silent: explicit
    attribution: str = "Source: The World Bank — Commodity Markets (Pink Sheet)"  # CC-BY 4.0
    value_unit: Optional[str] = None     # mirrors `unit` in __post_init__ (same as GoldHistory)
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()       # kept for future tokens; v1 emits none
    # _items_attr="bars", _index_column="date", _df_columns=("date","price")
```
**Never-silent coverage:** product / unit / value_unit / currency / source / **frequency** /
fetched_at_utc / **attribution** all present on every served result.

### 1e. Parser generalization (the "no duplication" mechanics) + gold-untouched protection
Extract the domain-neutral xlsx mechanics + a small spec object into
**`vnfin/_contracts/worldbank_cmo.py`** (the repo's established shared-internal home — sits beside
`timeseries.py`, `results.py`, `rows.py`):
```python
@dataclass(frozen=True)
class _MetalSpec:
    product: str            # XAU / XAG / XPT
    name_row: str           # "Gold" / "Silver" / "Platinum"  (split-header NAME cell)
    units_row: str = "($/troy oz)"     # shared across all three
    min_usd_oz: float       # per-metal band (Q2)
    max_usd_oz: float

def parse_cmo_annual(raw: bytes, spec: _MetalSpec) -> dict[int, float]: ...   # {year: usd_per_oz}
#   shared: _shared_strings, _resolve_worksheet_path (rels, never index), _cell_text, ref parsing
#   per-metal: name-row match + band (_coerce_price uses spec.min/max + names the metal on reject)
```
- **Gold** (`vnfin/gold/worldbank_cmo.py`): `WorldBankCmoGoldSource` keeps its `NAME`, constructor
  `(http_get=, timeout=)`, and `get_history(start, end) -> GoldHistory(product="XAU", ...)` **exactly**
  — it just builds the GOLD `_MetalSpec` (name `"Gold"`, band `20.0/10000.0` unchanged) and calls the
  shared `parse_cmo_annual`. The consumer `world_reference.py:241` is untouched.
- **Metals** (`vnfin/metals/sources.py`): `WorldBankCmoMetalSource` builds the silver/platinum spec
  and wraps the shared parser's dict into `MetalHistory`.
- **Gold-untouched is regression-protected explicitly:** all existing gold tests stay green **+** a new
  assertion that `WorldBankCmoGoldSource.get_history` output is value-identical (years + prices) to the
  pre-refactor path (gold 2025≈3441.51, 2024≈2387.70), and a `world_reference_history_vnd` smoke stays
  green. "Byte-for-byte" = observable output identical; internal extraction is invisible to callers.

*Alternative considered (noted for the gate, not recommended):* keep the parser in
`vnfin/gold/worldbank_cmo.py` and have `vnfin/metals/` import it from there — less file movement but a
`metals → gold` internal coupling (a metals domain importing gold internals). The `_contracts`
extraction is the clean-room-correct placement (the parser is genuinely domain-neutral). I recommend
the extraction; happy to take the in-place fallback if you prefer minimal movement.

---

## Q2 — Per-metal plausibility bands (evidence-based)

Measured from the committed fixture across the **full 1960–2025 history** (66 annual points each;
direct stdlib probe, independent of the module):

| Metal | col | real min (yr) | real max (yr) | 2025 |
|-------|-----|--------------|--------------|------|
| Gold | 67 | **34.95** (1967) | **3441.51** (2025) | 3441.51 |
| Platinum | 68 | **80.93** (1963) | **1719.48** (2011) | 1278.29 |
| Silver | 69 | **0.91** (1960) | **39.80** (2025) | 39.80 |

**Structural fact that drives the bands:** silver's all-time ceiling (39.80) sits **below** platinum's
all-time floor (80.93). So silver's band *can* reject a platinum mis-read (cols 68/69 are **adjacent**
— the realistic off-by-one) by magnitude; platinum can reject silver; but gold's range (35–3442)
**fully overlaps** platinum's (81–1719), so platinum's band **cannot** reject gold by magnitude — the
split-header **name-match is the primary defense**, the band is the magnitude backstop.

### Proposed bands
| Metal | band (USD/oz) | headroom vs real | rejects by magnitude | name-match covers |
|-------|--------------|------------------|---------------------|-------------------|
| **Gold** (UNCHANGED) | `[20.0, 10000.0]` | floor 0.57× / ceil 2.9× | (sanity only) | silver, platinum |
| **Silver** (new) | `[0.10, 75.0]` | floor 0.11× / ceil 1.88× | platinum (≥80.93), gold-recent (≥~1900) | gold-1960s (~35, overlaps silver top) |
| **Platinum** (new) | `[50.0, 5000.0]` | floor 0.62× / ceil 2.9× | silver (≤39.80) | gold (full overlap) |

Rationale:
- **Silver `[0.10, 75.0]`** — deliberately capped **below platinum's historical floor (80.93)** so it
  rejects the **adjacent-column** (platinum) misparse, the most likely off-by-one. Still 1.88× above
  silver's all-time-high annual average (39.80); breaching 75 USD/oz *annual average* would be an
  unprecedented >85% move past the record. Floor 0.10 ≪ real min 0.91 (generous-low). Satisfies the
  spec's required test ("gold's column under silver → raises": recent gold ≥1900 ≫ 75).
- **Platinum `[50.0, 5000.0]`** — floor 50.0 sits above silver's ceiling (39.80, rejects a silver
  misparse) and below platinum's real floor (80.93, generous-low). Ceiling 5000.0 ≈ 2.9× platinum's
  all-time high (1719.48), matching gold's generosity; kept generous (not tightened to catch gold)
  precisely because gold/platinum overlap means the **name-match**, not magnitude, separates them —
  tightening platinum's ceiling to catch gold would risk false-rejecting a real platinum rally.
- **Gold `[20.0, 10000.0]`** — **unchanged** (`_GOLD_MIN/MAX_USD_OZ`); gold-untouched.

This is the porting-guards lesson applied: the constants are **re-derived per metal from each metal's
own measured range**, not byte-copied from gold; each new band catches at least the adjacent-column
misparse + the spec-required gold-under-silver case.

---

## Error discipline (never-fabricate)
- **Unsupported metal argument** (`palladium`, `XPD`, `copper`, gold-via-this-facade, garbage) →
  `InvalidData(f"metal {metal!r} not supported by metals.history; supported: silver, platinum")`,
  raised **before** network. Names the metal; never relabels another column.
- **Supported metal whose column is absent in a fetched vintage** → `EmptyData` naming the metal
  (`f"{metal} column ('{name_row}' + '($/troy oz)') not found in CMO sheet"`). Parsed-but-no-data; never
  serve a different column relabelled.
- Every recoverable transport/parse failure → existing `SourceUnavailable`/`InvalidData` discipline
  (inherited from the shared parser + `HttpDataSource`), so the source stays failover-safe.

---

## Test matrix (maps 1:1 to the spec's 6 tests; offline, fixture-driven, injected fetch)
1. **Parse correctness** — Silver 2025≈39.80 & 2024≈28.27; Platinum 2025≈1278.29 & 2024≈955.17; Gold
   still 2025≈3441.51 (unchanged path).
2. **Band rejects mis-column (RED-without-fix on the band)** — feed gold's recent column value
   (3441.51) under silver's identity → `InvalidData` (3441.51 > 75); symmetric: feed silver's value
   (39.80) under platinum's identity → `InvalidData` (39.80 < 50). Proven RED by temporarily widening
   the band, not by ImportError.
3. **Unsupported metal** — `history("palladium")` → `InvalidData`/`EmptyData` naming "palladium";
   never a silent wrong column.
4. **Result metadata** — unit=`USD/oz`, currency=`USD`, product∈{XAG,XPT}, frequency=`annual`,
   source=`worldbank_cmo_metal`, attribution=CC-BY string, `fetched_at_utc` set — all asserted present.
5. **Public-surface lockstep** — `MetalBar`/`MetalHistory`/`history`/`source`/`SUPPORTED_METALS`
   exported + in `__all__`; `docs/api.md`, `skills/vnfin/SKILL.md`, `CHANGELOG.md` updated in lockstep;
   **no new warning token** (#180 table stays 49, #188 unaffected); snapshot `public_api_v0_2_0.json`
   **additive** (`vnfin.metals` absent from baseline → wholly additive, no `breaking` diff; **no regen**
   — release task).
6. **Gold-untouched regression** — explicit value-identity test on `WorldBankCmoGoldSource` +
   `world_reference_history_vnd` smoke green; all current gold tests green.
7. **Clean-room** — zero vnstock in the diff; `docs/sources/` recon updated to document the generalized
   multi-metal CMO source (columns, units, per-metal bands, attribution, license).

TDD: each invariant test RED-first before its code.

## Files touched (planned)
- **new** `vnfin/_contracts/worldbank_cmo.py` (shared parser + `_MetalSpec`)
- **edit** `vnfin/gold/worldbank_cmo.py` (build gold spec, call shared parser; output identical)
- **new** `vnfin/metals/__init__.py`, `vnfin/metals/models.py`, `vnfin/metals/sources.py`
- **new** `tests/test_metals.py`; **edit** gold regression test (value-identity assertion)
- **docs** generalize `docs/sources/cmo-gold-annual.md` → multi-metal CMO source doc; `docs/api.md`;
  `skills/vnfin/SKILL.md`; `CHANGELOG.md`

## Open questions for the gate
1. **Parser placement:** `_contracts/worldbank_cmo.py` extraction (recommended) vs in-place in
   `gold/worldbank_cmo.py` (less movement, `metals→gold` coupling). Your call.
2. **Gold symmetry:** v1 facade serves **silver + platinum only** (spec scope); `history("gold")`
   raises unsupported (gold annual stays on its internal path, untouched). Acceptable, or do you want a
   public `history("gold")` (product XAU) added for symmetry? I recommend **deferring** gold-public to
   keep this slice tight and the gold path untouched.
3. **Bounds type:** `start`/`end` as `datetime.date` (mirrors gold). OK, or also accept year ints?
