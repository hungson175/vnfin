# Design note — #178 `gold.world_reference_history_vnd()` (world-reference VND/lượng gold)

- Date: 2026-06-21 (vnfin-oss). Concretizes reviewer spec `spec-202606201815-issue178`.
- Status: **APPROVED by vnfin-oss-reviewer (00:35, 2026-06-21) → in TDD.** All three decisions
  locked below (§ "Reviewer decisions — LOCKED"). The spec's inverted factor is corrected.
- Clean-room: composes only existing in-repo primitives + a physical constant. Zero VNStock.

## Goal (unchanged from spec)
Ship an honestly-LABELED world-reference gold series in VND/lượng so vf-advisor gets a long-horizon
gold line now — explicitly NOT the VN domestic (SJC/BTMC) price (which carries a +10–21%, time-varying
premium). Reserve `gold.domestic_history()` → a clear source-gap diagnostic, never the synthesis.

## Existing primitives (verified, file:line)
- **World gold history (USD/oz, DAILY):** `vnfin.gold.default_world_gold_client().get_history(start, end)
  -> GoldHistory` (CurrencyApi primary → Stooq fallback). `unit="USD/oz"`, `bars: tuple[GoldBar(date,
  price)]`, `fetched_at_utc`. (`vnfin/gold/__init__.py:96`, `vnfin/gold/currency_api.py:93`,
  `vnfin/gold/stooq.py:153`.) → I will use the **failover client**, not pin to `stooq.py` (the spec's
  prose named stooq, but the client gives CurrencyApi→Stooq robustness).
- **USD/VND FX history (ANNUAL only):** `vnfin.fx.history("USD","VND", start, end) -> FXHistory`
  (`vnfin/fx/__init__.py:80`). **Hard-enforced annual** (`:109` raises `InvalidData` for any other
  frequency); points are an **annual period-average** rate stamped Jan-1, window filtered by calendar
  year. `value_unit="VND per 1 USD"`, `points: tuple[FXPoint(date, rate)]`, `fetched_at_utc`. No FX
  *history* failover in v1 (World Bank `PA.NUS.FCRF` only).
- **lượng:** `_GRAMS_PER_LUONG = 37.5` (`vnfin/gold/vn.py:40`); docs/tests all state 1 lượng = 37.5 g.
- **Carrier:** `GoldHistory` already has `warnings: tuple[str,...] = ()` (`vnfin/gold/models.py:106`) —
  the same additive mechanism #177 used for `fallback_instrument_served`.

## DECISION 1 — conversion factor (SPEC CORRECTION, high confidence)
The spec writes `× (31.1035/37.5) ≈ 0.8297`. **That ratio is inverted.** Physics:
- 1 troy oz = 31.1035 g; 1 lượng = 37.5 g, so 1 lượng = 37.5/31.1035 = **1.20566 oz** (a lượng is
  heavier than an oz). Therefore **USD/lượng = USD/oz × (37.5 / 31.1035) ≈ × 1.20566** — scales UP.
- Cross-check the spec's OWN figures: world gold ≈ $2000/oz, USD/VND ≈ 24,000 (2023) →
  `2000 × 24000 × (37.5/31.1035) ≈ 57.9M VND/lượng`. The spec cites SJC ≈ +11.7M over the world
  equivalent → world-equiv ≈ 56M, SJC ≈ 67M. **57.9M matches; `× 0.8297` gives 39.8M (way low).**
- Cross-check the repo: `vn.py` weight-parse does `gram → lượng = n / 37.5` and `kg → lượng =
  n*1000/37.5`. Per-gram USD = USD/oz ÷ 31.1035; per-lượng = per-gram × 37.5 = USD/oz × 37.5/31.1035. ✓
**Proposal:** add module constants `_GRAMS_PER_TROY_OZ = 31.1034768` (standard) and reuse
`_GRAMS_PER_LUONG = 37.5`; factor = `_GRAMS_PER_LUONG / _GRAMS_PER_TROY_OZ`. (Spec said the synthesis
*understates* the domestic price — that conclusion is unchanged; only the arithmetic factor is corrected.)

## DECISION 2 — granularity (genuinely open; reviewer holds the vf-advisor signal)
World gold is DAILY; USD/VND history is ANNUAL-only. The two series cannot be multiplied pointwise.
- **(A) Annual output [my lean]:** reduce world-gold to an annual **period-average** (to match FX's
  period-average semantics), × that year's annual FX × factor → **one VND/lượng point per calendar
  year**. Honest to the limiting resolution (FX); 20–26 points is plenty for a long-horizon reference
  chart; implies no false daily-FX precision. Output stamped Jan-1 per year (mirrors FX).
- **(B) Daily output, forward-filled FX:** each daily gold bar × its year's annual FX × factor → a
  dense daily VND/lượng line (visual parity with the #177 S&P line), with a SECOND caveat in the
  warning ("FX is annual World Bank period-average held constant within each year"). More chart-friendly,
  slightly less honest.
**Need the reviewer's call** (A vs B) since it depends on what vf-advisor's chart wants. I lean A.

## DECISION 3 — result carrier + mandatory labeling
**Proposal:** return a `GoldHistory` with `product="XAU/VND (world-reference)"`, `unit="VND/luong"`,
`value_unit="VND/luong"`, `currency="VND"`, `source="world-gold (failover) × USD/VND (World Bank)"`,
`fetched_at_utc` = composition time. The MANDATORY `premium_note` rides in `warnings` (always
populated): *"world-gold-implied VND reference; excludes the VN domestic premium (historically
+10–21%, time-varying); NOT the SJC/BTMC domestic price."* (Established #177 pattern; zero new model
surface.) **Alternative if you prefer:** a dedicated `premium_note: Optional[str]` field on GoldHistory
(additive) for stronger discoverability. I lean `warnings` unless you want the dedicated field.
Accessor name is the mandated `world_reference_*` (`gold.world_reference_history_vnd`).

## DECISION 4 — reserve `gold.domestic_history()`
`gold.domestic_history(...)` raises a clear diagnostic (`NotImplementedError`/`InvalidData`) naming the
source gap and pointing at the #182 source-hunt — **never** returns the synthesis. (No clean, stable,
ToS-clear, multi-year domestic source exists; verified in the spec.)

## Data integrity
World-gold + FX inputs are already positive (source guards + FXRate validation); product of positives
is positive. A year present in gold but missing in FX (or vice-versa) → that year is skipped (option A)
/ fails per the result contract; both-missing → propagate the underlying failover error (no silent
half-result). Add positivity asserts on the synthesized value as a belt-and-suspenders guard
(`new-source-must-mirror-sibling-data-integrity-guards`).

## Tests (offline, synthetic — inject `http_get` for BOTH world-gold and fx)
- happy path: synthetic world-gold bars + synthetic annual USD/VND → assert each VND/lượng point =
  `gold_annual × fx_annual × (37.5/31.1035)` to tolerance; assert `unit="VND/luong"`, source attribution,
  `premium_note` present in `warnings`, `fetched_at_utc` set.
- `gold.domestic_history()` → raises the source-gap diagnostic (asserts it is NOT the synthesis).
- FX-missing / world-gold-missing → fails loudly per the result contract (no silent half-result).
- factor regression: a known oz price converts to the expected VND/lượng (locks 37.5/31.1035, guards
  against the inverted factor ever creeping back).

## Public-API / docs
Additive: new `gold.world_reference_history_vnd` + reserved `gold.domestic_history` in `gold/__init__`
`__all__`. Surface test stays additive-green; **do NOT regen the snapshot** (release-time only). Docs +
skill + CHANGELOG in the same change (provenance note in `docs/sources/`, ai-usage entry, skill row).

## Reviewer decisions — LOCKED (00:35, 2026-06-21)
1. **FACTOR (corrected):** `37.5 / 31.1035 ≈ 1.20566`. **Compute from NAMED constants**
   `GRAMS_PER_LUONG = 37.5` and `GRAMS_PER_TROY_OZ = 31.1035` (auditable; never a hardcoded 1.206).
   Reviewer re-derived + confirmed (`950 × 24000 × 1.206 ≈ 56.4M`). The "understates domestic" point holds.
2. **GRANULARITY: ANNUAL output.** Daily-forward-filled FX is REJECTED as false precision (daily wiggles
   would be gold-only over a step-function FX — a data-integrity anti-pattern). Align the gold aggregation
   basis with the World Bank annual-FX basis: **annual-average gold × annual-average FX × factor**, one
   VND/lượng point per calendar year (mirror FX's Jan-1 stamp). Document the basis. vf-advisor interpolates
   for display parity itself; finer granularity needs a clean-room DAILY USD/VND source = a v2 follow-up.
3. **DISCLOSURE: `premium_note` in `GoldHistory.warnings`** (additive-free). Make it a MECHANICAL token —
   `world_reference_excludes_domestic_premium` — with the human tail "+10–21% time-varying; NOT the
   SJC/BTMC domestic price". Keep disclosure **REDUNDANT**: the accessor name `world_reference_history_vnd`
   + `value_unit="VND/luong"` + `source` must ALSO signal world-reference (never "domestic").
4. **Errors:** FX-missing / world-gold-missing → propagate per the failover/result contract (no silent
   half-result). `gold.domestic_history()` → clear source-gap diagnostic (→ #182), never the synthesis.
5. Clean-room: existing world-gold failover (CurrencyApi→Stooq) + World Bank FX only. Zero VNStock.
   Process: TDD red-first → bring CODE for Codex×2 → push only on APPROVE.
