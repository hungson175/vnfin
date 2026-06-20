"""World-reference VND/lượng gold history (#178) — a LABELED synthesis, NOT the domestic price.

``gold.world_reference_history_vnd(start, end)`` composes the library's existing world-gold
daily history (USD/oz, ``CurrencyApiGoldSource`` → ``StooqGoldSource`` failover) with annual
USD/VND FX (World Bank ``PA.NUS.FCRF`` period-average) into an ANNUAL VND/lượng series:

    VND/lượng[year] = annual_avg(world_gold_usd_per_oz)[year]
                       × annual_USD_VND[year]
                       × (GRAMS_PER_LUONG / GRAMS_PER_TROY_OZ)

This is the world-gold-IMPLIED VND value. VN domestic (SJC/BTMC) gold trades at a large,
time-varying premium over the world reference (historically **+10–21%**), so this series
**systematically understates** the real domestic price and MUST NEVER be presented as it.
The result self-discloses redundantly: the accessor name (``world_reference_*``), the
``source`` attribution, ``value_unit``, and a mechanical
``world_reference_excludes_domestic_premium`` warning.

**Granularity is ANNUAL only.** USD/VND history is annual (World Bank period-average), so the
world-gold leg is reduced to an annual average to MATCH that basis (annual-avg × annual-avg).
A daily output would imply a daily-FX precision the data does not have. Callers needing a
denser line should interpolate for display; a true daily series needs a clean-room daily
USD/VND source (a v2 follow-up).

``gold.domestic_history()`` is **reserved but not implemented**: no clean-room, license-clear,
stable, multi-year VN domestic source has been vetted yet (tracked in issue #182). It raises a
clear source-gap diagnostic — it never silently returns this synthesis.

Clean-room: composes only existing in-repo primitives (CurrencyApi/Stooq world-gold +
World Bank FX) and the physical gram constants below. No new external source; zero vnstock.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timezone
from typing import Optional

from ..exceptions import EmptyData, InvalidData
from ..fx.history_models import FXHistory
from .currency_api import CurrencyApiGoldSource
from .failover import FailoverGoldClient
from .models import GoldBar, GoldHistory
from .stooq import StooqGoldSource

# Physical weights — auditable named constants. The oz→lượng factor is COMPUTED from them
# (never a hardcoded 1.206) so a reviewer can re-derive it.
GRAMS_PER_LUONG = 37.5  # 1 lượng (tael) = 10 chỉ = 37.5 g (matches vnfin.gold.vn)
GRAMS_PER_TROY_OZ = 31.1035  # 1 troy ounce = 31.1035 g (standard)
# 1 lượng is HEAVIER than 1 troy oz, so USD/oz → USD/lượng scales UP (≈ 1.20566).
OZ_TO_LUONG = GRAMS_PER_LUONG / GRAMS_PER_TROY_OZ

_VND_PER_LUONG = "VND/luong"
_PRODUCT = "XAU/VND (world-reference)"
_SOURCE = "world-gold (failover) × USD/VND (World Bank)"

# Mandatory disclosure (mechanical token + human tail) — rides in GoldHistory.warnings.
_PREMIUM_NOTE = (
    "world_reference_excludes_domestic_premium: world-gold-implied VND reference; "
    "excludes the VN domestic premium (historically +10–21%, time-varying); "
    "NOT the SJC/BTMC domestic price"
)
_ANNUAL_BASIS_NOTE = (
    "world_reference_annual_basis: one point per calendar year = annual-average world gold "
    "(USD/oz) × annual-average USD/VND (World Bank period-average) × 37.5/31.1035 (g, "
    "oz→lượng); stamped Jan-1; not a daily series"
)
_PARTIAL_COVERAGE_TOKEN = "world_reference_partial_year_coverage"


def _synthesize_world_reference(gold_hist: GoldHistory, fx_hist: FXHistory) -> GoldHistory:
    """Pure compose: world-gold (USD/oz daily) × USD/VND (annual) → annual VND/lượng.

    Aggregates the daily gold series to an annual average per calendar year, joins it with
    the annual FX rate of the same year, and scales USD/oz → VND/lượng. Synthesizes only the
    years present in BOTH legs (an honest intersection); a non-empty intersection that drops
    requested years emits a ``world_reference_partial_year_coverage`` warning (never silent),
    and an EMPTY intersection raises :class:`EmptyData` rather than returning a half-result.
    """
    sums: dict[int, float] = {}
    counts: dict[int, int] = {}
    for bar in gold_hist.bars:
        y = bar.date.year
        sums[y] = sums.get(y, 0.0) + bar.price
        counts[y] = counts.get(y, 0) + 1
    gold_annual = {y: sums[y] / counts[y] for y in sums}

    # FXHistory points are annual averages stamped Jan-1 -> key by calendar year.
    fx_annual = {p.date.year: p.rate for p in fx_hist.points}

    common = sorted(set(gold_annual) & set(fx_annual))
    if not common:
        raise EmptyData(
            f"{_SOURCE}: no overlapping calendar years between world-gold history "
            f"(years {sorted(gold_annual) or 'none'}) and USD/VND FX "
            f"(years {sorted(fx_annual) or 'none'}); cannot synthesize a VND/luong reference"
        )

    bars = []
    for y in common:
        vnd_per_luong = gold_annual[y] * fx_annual[y] * OZ_TO_LUONG
        # Belt-and-suspenders: inputs are positive (source + FX guards), so a non-positive /
        # non-finite product means corrupt upstream data — fail loudly, never serve it.
        if not math.isfinite(vnd_per_luong) or vnd_per_luong <= 0:
            raise InvalidData(
                f"{_SOURCE}: non-positive/non-finite synthesized VND/luong for {y} "
                f"(gold_avg={gold_annual[y]!r}, fx={fx_annual[y]!r})"
            )
        bars.append(GoldBar(date=date(y, 1, 1), price=vnd_per_luong))

    warnings = [_PREMIUM_NOTE, _ANNUAL_BASIS_NOTE]
    dropped_gold = sorted(set(gold_annual) - set(fx_annual))  # gold years with no FX
    dropped_fx = sorted(set(fx_annual) - set(gold_annual))  # FX years with no gold
    if dropped_gold or dropped_fx:
        parts = []
        if dropped_gold:
            parts.append(f"gold-only (no FX): {dropped_gold}")
        if dropped_fx:
            parts.append(f"FX-only (no gold): {dropped_fx}")
        warnings.append(
            f"{_PARTIAL_COVERAGE_TOKEN}: years not synthesized for lack of a paired "
            f"observation — {'; '.join(parts)}"
        )

    return GoldHistory(
        product=_PRODUCT,
        unit=_VND_PER_LUONG,
        value_unit=_VND_PER_LUONG,
        currency="VND",
        source=_SOURCE,
        bars=tuple(bars),
        fetched_at_utc=datetime.now(timezone.utc),
        warnings=tuple(warnings),
    )


def world_reference_history_vnd(
    start, end, *, http_get=None, timeout: float = 25.0, max_attempts: int = 3
) -> GoldHistory:
    """World-reference gold history in **VND/lượng**, ANNUAL — NOT the VN domestic price.

    Composes world-gold daily history (USD/oz; ``CurrencyApiGoldSource`` →
    ``StooqGoldSource`` failover) with annual USD/VND FX (World Bank ``PA.NUS.FCRF``) into a
    one-point-per-calendar-year VND/lượng series (Jan-1 stamped). The result carries a
    mandatory ``world_reference_excludes_domestic_premium`` warning: the VN domestic
    (SJC/BTMC) price sits a large, time-varying premium (historically +10–21%) ABOVE this
    world reference, so this series understates it — never present it as the domestic price.

    ``start``/``end`` are required calendar bounds. A multi-year window exceeds CurrencyApi's
    coverage/range, so it cleanly fails over to Stooq (the long-history world-gold source).
    A total failure of either leg propagates (``AllSourcesFailed`` / ``EmptyData``); a window
    with no overlapping gold+FX years raises :class:`EmptyData` (no silent half-result).

    Pass ``http_get`` (and ``timeout``) to inject a transport stub for offline tests; it is
    forwarded to every underlying source. ``max_attempts`` caps the world-gold failover chain.
    """
    # World-gold daily history (USD/oz). CurrencyApi is primary (reliable, no key) but covers
    # only ~2024-03+ with a ~1100-day cap, so any multi-year window raises range-too-wide
    # (a SourceError) and fails over to Stooq, the only full-history world-gold source. This
    # validates start/end before any network call.
    gold_sources = [
        CurrencyApiGoldSource(http_get=http_get, timeout=timeout),
        StooqGoldSource(http_get=http_get, timeout=timeout),
    ]
    gold_hist = FailoverGoldClient(gold_sources, max_attempts=max_attempts).get_history(start, end)

    # Annual USD/VND (World Bank period-average) — annual-only by construction, which is the
    # exact basis we aggregate the gold leg to. Imported lazily to avoid any import cycle.
    from ..fx import history as _fx_history

    fx_hist = _fx_history("USD", "VND", start, end, http_get=http_get, timeout=timeout)

    return _synthesize_world_reference(gold_hist, fx_hist)


def domestic_history(start=None, end=None, *, http_get=None, timeout: float = 25.0):
    """Reserved — VN **domestic** (SJC/BTMC) gold-price history. NOT YET AVAILABLE.

    Raises :class:`NotImplementedError` with a source-gap diagnostic. No clean-room,
    license-clear, stable, multi-year domestic source has been vetted (tracked in #182). This
    function will never silently fall back to the world-reference synthesis, which excludes
    the VN domestic premium and is not a domestic proxy — use
    :func:`world_reference_history_vnd` only when you explicitly want the world reference.
    """
    raise NotImplementedError(
        "gold.domestic_history() is not available: no clean-room, license-clear, stable, "
        "multi-year VN domestic (SJC/BTMC) gold-price history source has been vetted yet "
        "(source hunt tracked in issue #182). Do NOT substitute "
        "gold.world_reference_history_vnd() for the domestic price — it is the world-gold-"
        "implied VND reference and EXCLUDES the VN domestic premium (historically +10–21%, "
        "time-varying). See docs/sources/gold-world-reference.md."
    )
