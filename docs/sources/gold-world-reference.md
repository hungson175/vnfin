# World-reference VND/lượng gold — provenance, method & the domestic-premium caveat

Clean-room: this is a **synthesis** over already-vetted in-repo sources plus a physical
constant — no new external data is bundled. The composed sources are documented in
[`cmo-gold-annual.md`](cmo-gold-annual.md) (**primary** world-gold annual leg, World Bank CMO),
[`gold-adapters.md`](gold-adapters.md) (world XAU/USD daily — the **fallback** leg) and
[`fx-history-worldbank.md`](fx-history-worldbank.md) (annual USD/VND). No vnstock / VNStock /
derivative was read, cited, or copied. Design notes: `docs/design/gold-world-reference-vnd.md`
(#178) and `docs/design/issue-185-annual-world-gold-source.md` (#185, the CMO annual primary).

These power **`vnfin.gold.world_reference_history_vnd(start, end, *, http_get=None,
timeout=25.0, max_attempts=3)`** → a `GoldHistory` in **VND/lượng**, **one point per calendar
year** (Jan-1 stamped). `vnfin.gold.domestic_history(...)` is **reserved but not implemented**
(see the bottom of this file).

## End-to-end gold coverage & backup paths (#171)

vnfin exposes gold through distinct paths; this is the full coverage + opt-in/backup map so you
pick the right one and always know when a backup engaged.

| Path | Accessor | Unit | Coverage | Primary → backup |
|---|---|---|---|---|
| VN domestic **spot** | `gold.vn("btmc"\|"pnj").get_quotes()` | VND/lượng | current snapshot only (no history) | single dealer; no failover |
| World gold **daily** | `gold.world().get_history(start, end)` | USD/oz | CurrencyApi ≈2024-03→today (~1100-day cap) | CurrencyApi default; **Stooq full-history is opt-in** (anti-bot-blocked from datacenters) — see [`gold-adapters.md`](gold-adapters.md) |
| World-reference **annual** | `gold.world_reference_history_vnd(start, end)` | VND/luong | **1960→present**, one point per calendar year | **World Bank CMO annual PRIMARY** → daily `CurrencyApi→Stooq` averaged-to-annual FALLBACK (disclosed) — see [`cmo-gold-annual.md`](cmo-gold-annual.md) |
| _reserved_ | `gold.domestic_history()` | — | — | `NotImplementedError` (source-gap #182); **never** silently falls back to this synthesis |

**Which to use.** For a long multi-year VND gold chart (incl. server-side), use
`world_reference_history_vnd` — its CMO annual primary is reachable from datacenter hosts and needs
**no opt-in**. For daily spot or a recent daily USD/oz series, use `gold.world()`. The daily Stooq
backup is **opt-in only** (append `StooqGoldSource()` to the chain) because it is anti-bot-blocked
from many hosts.

**Backups are never silent.**
- World-reference CMO primary fails → `world_reference_gold_source_fallback` on the result, plus any
  `world_reference_gold_leg_*` warnings forwarded from the daily fallback leg.
- A gappy-but-accepted daily leg → `partial_coverage` (forwarded as
  `world_reference_gold_leg_partial_coverage`).
- Everything unreachable → raises `AllSourcesFailed` (loud) — never an empty or silently-partial
  result.

## What it is — and emphatically is NOT

It is the **world-gold-implied VND value of a lượng**: the international gold price expressed in
VND per lượng. It is **NOT** the VN domestic (SJC / BTMC) gold price. Vietnamese domestic gold
trades at a large, **time-varying premium** over the world reference — historically **+10–21%**
— so this series **systematically understates** the real domestic price. Never present it, chart
it, or compare it as if it were the SJC/BTMC price; rebase/annotate accordingly.

## Method (annual, by construction)

```
VND/lượng[year] = annual world_gold_USD_per_oz[year]             # CMO annual gold (primary); daily-mean on fallback
                  × annual_USD_VND[year]                          # World Bank PA.NUS.FCRF (period avg)
                  × (GRAMS_PER_LUONG / GRAMS_PER_TROY_OZ)         # 37.5 / 31.1035 ≈ 1.20565
```

- **Why annual.** USD/VND history is annual-only (World Bank period-average); multiplying a daily
  gold series by a step-function annual FX would manufacture daily wiggles that are gold-only —
  false precision. So the gold leg is annual to match the FX basis (annual × annual). The
  **primary** gold leg (World Bank CMO, #185) is **published annually** and is already an
  *annual average of daily spot* (LBMA-sourced), so it slots in losslessly — the
  `annual-avg × annual-avg` basis is preserved exactly. The **fallback** daily leg
  (CurrencyApi → Stooq) is reduced to an annual mean for the same basis. A denser line needs a
  clean-room **daily** USD/VND source (a v2 follow-up); callers may interpolate for display.
- **Whole-calendar-year window.** `start`/`end` are interpreted as an inclusive **calendar-year**
  window: any portion of a year yields that year's annual point, and each emitted year's gold mean
  is computed from the **full calendar year** (the fetch window is snapped to `Jan-1 … Dec-31` of
  the boundary years). This matches the FX leg, which already widens bounds to whole calendar
  years, so a mid-year `start`/`end` never produces a partial-year gold mean silently multiplied
  by a full-year FX average. (An inverted range — even within one year — is rejected up front with
  `InvalidData`.)
- **The oz→lượng factor scales UP.** 1 lượng = 37.5 g is **heavier** than 1 troy oz = 31.1035 g,
  so USD/oz → USD/lượng multiplies by ≈ **1.20565** (not the inverted ≈ 0.83). Computed from the
  **named constants** `GRAMS_PER_LUONG` / `GRAMS_PER_TROY_OZ` in
  `vnfin/gold/world_reference.py` so the arithmetic is auditable. Cross-check: gold $2000/oz ×
  USD/VND 24,000 × 1.20565 ≈ **57.9M VND/lượng** (the world-equivalent; SJC would sit ~+11–12M
  above on top of that).

## Composed sources & failover

| Leg | Accessor | Unit | Notes |
|---|---|---|---|
| World gold (annual) — **PRIMARY** | `WorldBankCmoGoldSource` (internal) — World Bank CMO "Pink Sheet" annual `.xlsx` | `USD/oz` | #185. **Annual** and reachable server-side; CMO annual gold IS the annual average of daily spot, so it preserves the synthesis basis exactly. Fetched **directly** (bypassing `FailoverGoldClient` — the daily 50%-weekday coverage gate would wrongly reject a 1-bar-per-year series). See [`cmo-gold-annual.md`](cmo-gold-annual.md). |
| World gold (daily) — **FALLBACK** | `CurrencyApiGoldSource` → `StooqGoldSource` (`FailoverGoldClient`) | `USD/oz` | Engaged only when the CMO leg raises a recoverable `SourceError` (unreachable/malformed/no-years-in-span). CurrencyApi covers only ~2024-03+ with a ~1100-day cap, so a **multi-year window** fails over to Stooq, the only full-history daily world-gold source. The result then carries a `world_reference_gold_source_fallback` warning. |
| FX (annual) | `vnfin.fx.history("USD","VND", start, end)` | `VND per 1 USD` | World Bank `PA.NUS.FCRF` period-average, Jan-1 stamped; single-source (no FX-history failover in v1). |

**The CMO annual leg is the workhorse server-side** (it is the very source that unblocks the
chart from a datacenter host). If CMO is unavailable the synthesis falls back to the daily path:
from datacenter IPs Stooq sometimes returns a JS anti-bot challenge (`SourceUnavailable`); if that
happens on a wide window where CurrencyApi cannot serve either, **and** CMO already failed, the
call raises `AllSourcesFailed` (loud, not silent) — the honest result given the source landscape.

## Disclosure (redundant, never silent)

The result self-discloses world-reference status four ways: the **accessor name**
(`world_reference_history_vnd`), `product="XAU/VND (world-reference)"`, `value_unit="VND/luong"`,
and `source="world-gold (failover) × USD/VND (World Bank)"` — **none** say "domestic". Plus
mechanical tokens on `GoldHistory.warnings`:

- `world_reference_excludes_domestic_premium: … +10–21%, time-varying; NOT the SJC/BTMC domestic price` — **always present.**
- `world_reference_annual_basis: one point per calendar year = annual-avg gold × annual USD/VND × 37.5/31.1035; stamped Jan-1; not a daily series` — always present.
- `world_reference_partial_year_coverage: …` — only when some requested years are dropped for lack of a paired gold-or-FX observation (an honest intersection; never a silent half-result). An **empty** overlap raises `EmptyData`.
- `world_reference_gold_leg_partial_coverage: …` (and `world_reference_fx_leg_*`) — the world-gold failover client accepts a *gappy-but-not-rejected* series (coverage 50–90% of trading days) and attaches a soft `partial_coverage` warning; that is the only signal a year's annual mean came from an incomplete subset of days, so it is **forwarded** (namespaced by leg) onto the synthesized result — never dropped.
- `world_reference_trailing_year_incomplete: …` — only when the **latest emitted year is the current calendar year**: that year is still in progress, so its annual mean is a *year-to-date* partial average, not a full-year mean. This is flagged **independently** of the gold-leg `partial_coverage` aggregate (a long window of complete prior years dilutes the in-progress year's coverage back above the threshold, silencing that signal), keyed only on today's year — so the trailing point is never mistaken for a settled full-year value.
- `world_reference_gold_source_fallback: CMO annual source unavailable; used daily-averaging path` — **only when the primary World Bank CMO annual leg failed** and the synthesis fell back to the daily `CurrencyApi → Stooq` path (#185). Present together with any `world_reference_gold_leg_*` warnings from that daily leg. Absent when CMO served (the normal server-side case).

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

Every leg raises only `vnfin.exceptions` subclasses (`SourceUnavailable` / `InvalidData` /
`EmptyData` / `AllSourcesFailed`), so a leg failure surfaces as a typed error rather than a
crash or a silently-empty result. The CMO→daily fallback `except` catches **`SourceError`** (the
base of `SourceUnavailable`/`InvalidData`/`EmptyData`), **not** bare `Exception` — so every
recoverable CMO failure reliably engages the daily fallback, while a non-`SourceError` programmer
bug propagates (fails loud) instead of being silently swallowed. The synthesis adds a
belt-and-suspenders positivity/finiteness guard on every emitted VND/lượng point.
