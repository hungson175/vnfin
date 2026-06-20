# World-reference VND/lượng gold — provenance, method & the domestic-premium caveat

Clean-room: this is a **synthesis** over two already-vetted in-repo sources plus a physical
constant — no new endpoint and no new external data. The composed sources are documented in
[`gold-adapters.md`](gold-adapters.md) (world XAU/USD daily) and
[`fx-history-worldbank.md`](fx-history-worldbank.md) (annual USD/VND). No vnstock / VNStock /
derivative was read, cited, or copied. Design note: `docs/design/gold-world-reference-vnd.md`.

These power **`vnfin.gold.world_reference_history_vnd(start, end, *, http_get=None,
timeout=25.0, max_attempts=3)`** → a `GoldHistory` in **VND/lượng**, **one point per calendar
year** (Jan-1 stamped). `vnfin.gold.domestic_history(...)` is **reserved but not implemented**
(see the bottom of this file).

## What it is — and emphatically is NOT

It is the **world-gold-implied VND value of a lượng**: the international gold price expressed in
VND per lượng. It is **NOT** the VN domestic (SJC / BTMC) gold price. Vietnamese domestic gold
trades at a large, **time-varying premium** over the world reference — historically **+10–21%**
— so this series **systematically understates** the real domestic price. Never present it, chart
it, or compare it as if it were the SJC/BTMC price; rebase/annotate accordingly.

## Method (annual, by construction)

```
VND/lượng[year] = annual_avg( world_gold_USD_per_oz )[year]      # daily series → annual mean
                  × annual_USD_VND[year]                          # World Bank PA.NUS.FCRF (period avg)
                  × (GRAMS_PER_LUONG / GRAMS_PER_TROY_OZ)         # 37.5 / 31.1035 ≈ 1.20566
```

- **Why annual.** USD/VND history is annual-only (World Bank period-average); multiplying a daily
  gold series by a step-function annual FX would manufacture daily wiggles that are gold-only —
  false precision. So the gold leg is reduced to an **annual mean** to match the FX basis
  (annual-avg × annual-avg). A denser line needs a clean-room **daily** USD/VND source (a v2
  follow-up); callers may interpolate for display.
- **The oz→lượng factor scales UP.** 1 lượng = 37.5 g is **heavier** than 1 troy oz = 31.1035 g,
  so USD/oz → USD/lượng multiplies by ≈ **1.20566** (not the inverted ≈ 0.83). Computed from the
  **named constants** `GRAMS_PER_LUONG` / `GRAMS_PER_TROY_OZ` in
  `vnfin/gold/world_reference.py` so the arithmetic is auditable. Cross-check: gold $2000/oz ×
  USD/VND 24,000 × 1.20566 ≈ **57.9M VND/lượng** (the world-equivalent; SJC would sit ~+11–12M
  above on top of that).

## Composed sources & failover

| Leg | Accessor | Unit | Notes |
|---|---|---|---|
| World gold (daily) | `CurrencyApiGoldSource` → `StooqGoldSource` (`FailoverGoldClient`) | `USD/oz` | CurrencyApi covers only ~2024-03+ with a ~1100-day cap, so a **multi-year window** raises range-too-wide (a `SourceError`) and **fails over to Stooq**, the only full-history world-gold source. |
| FX (annual) | `vnfin.fx.history("USD","VND", start, end)` | `VND per 1 USD` | World Bank `PA.NUS.FCRF` period-average, Jan-1 stamped; single-source (no FX-history failover in v1). |

**Stooq is the de-facto workhorse here** for any horizon longer than ~3 years. From datacenter
IPs Stooq sometimes returns a JS anti-bot challenge (`SourceUnavailable`); if that happens on a
wide window where CurrencyApi cannot serve either, the call raises `AllSourcesFailed` (loud, not
silent) — the honest result given the source landscape.

## Disclosure (redundant, never silent)

The result self-discloses world-reference status four ways: the **accessor name**
(`world_reference_history_vnd`), `product="XAU/VND (world-reference)"`, `value_unit="VND/luong"`,
and `source="world-gold (failover) × USD/VND (World Bank)"` — **none** say "domestic". Plus
mechanical tokens on `GoldHistory.warnings`:

- `world_reference_excludes_domestic_premium: … +10–21%, time-varying; NOT the SJC/BTMC domestic price` — **always present.**
- `world_reference_annual_basis: one point per calendar year = annual-avg gold × annual USD/VND × 37.5/31.1035; stamped Jan-1; not a daily series` — always present.
- `world_reference_partial_year_coverage: …` — only when some requested years are dropped for lack of a paired gold-or-FX observation (an honest intersection; never a silent half-result). An **empty** overlap raises `EmptyData`.

```python
from datetime import date
import vnfin

h = vnfin.gold.world_reference_history_vnd(date(2018, 1, 1), date(2024, 12, 31))
print(h.unit, h.currency, len(h.bars))          # 'VND/luong' 'VND' 7
print(h.bars[-1].date, round(h.bars[-1].price)) # date(2024,1,1) <world-equivalent VND/lượng>
for w in h.warnings:
    print(w)                                     # excludes-domestic-premium + annual-basis (+ partial, if any)
```

## Reserved: `gold.domestic_history()`

Raises `NotImplementedError` with a source-gap diagnostic — **never** falls back to this
synthesis. No clean-room, license-clear, stable, multi-year VN **domestic** (SJC/BTMC) gold-price
history source has been vetted yet; the source hunt is tracked in **issue #182**. When such a
source lands, `domestic_history()` will serve the true domestic price (premium included).

## Licensing / redistribution posture

Inherits the composed sources' posture: **runtime-fetch only, no bundled/redistributed data**,
attribute the providers, poll modestly. Stooq is keyless/best-effort with no redistribution
claim; World Bank WDI is open data. The synthesis adds only a physical constant.

## Failover safety

Both legs raise only `vnfin.exceptions` subclasses (`SourceUnavailable` / `InvalidData` /
`EmptyData` / `AllSourcesFailed`), so a leg failure surfaces as a typed error rather than a
crash or a silently-empty result. The synthesis adds a belt-and-suspenders positivity/finiteness
guard on every emitted VND/lượng point.
