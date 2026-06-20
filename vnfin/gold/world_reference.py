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
from dataclasses import replace
from datetime import date, datetime, timezone

from ..exceptions import EmptyData, InvalidData, SourceError
from ..fx.history_models import FXHistory
from ..validation import validate_date_range
from .currency_api import CurrencyApiGoldSource
from .failover import FailoverGoldClient
from .models import GoldBar, GoldHistory
from .stooq import StooqGoldSource
from .worldbank_cmo import WorldBankCmoGoldSource

# Physical weights — auditable named constants. The oz→lượng factor is COMPUTED from them
# (never a hardcoded 1.206) so a reviewer can re-derive it.
GRAMS_PER_LUONG = 37.5  # 1 lượng (tael) = 10 chỉ = 37.5 g (matches vnfin.gold.vn)
GRAMS_PER_TROY_OZ = 31.1035  # 1 troy ounce = 31.1035 g (standard)
# 1 lượng is HEAVIER than 1 troy oz, so USD/oz → USD/lượng scales UP (≈ 1.20565).
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
    "oz→lượng); stamped Jan-1; not a daily series; the latest point may be the in-progress "
    "current year (a year-to-date partial mean, flagged by "
    "world_reference_trailing_year_incomplete)"
)
_PARTIAL_COVERAGE_TOKEN = "world_reference_partial_year_coverage"
_TRAILING_YEAR_TOKEN = "world_reference_trailing_year_incomplete"
# #185: never-silent disclosure that the annual CMO primary gold leg was unavailable and
# the result was built from the daily-averaging fallback (CurrencyApi -> Stooq) instead.
_GOLD_SOURCE_FALLBACK_NOTE = (
    "world_reference_gold_source_fallback: CMO annual source unavailable; "
    "used daily-averaging path"
)


def _today() -> date:
    """Today's date (UTC) — wrapped so tests can PIN the trailing-year check (the #172/#179
    injection pattern, never random). NEVER used for ``fetched_at_utc``, which stays a real
    wall-clock stamp; this only decides whether the current (in-progress) year is emitted.

    Only ``.year`` is consumed, and UTC is deliberate: vs Vietnam (UTC+7) the UTC year can lag
    by at most the ~7h window of VN Jan-1 00:00–06:59. That can only make a JUST-completed year
    still read as "in progress" (a self-clearing, bounded false-positive) — it can never
    suppress a genuinely partial year, so it honors the prefer-bounded-false-positive principle."""
    return datetime.now(timezone.utc).date()


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
    # Forward upstream leg warnings — never drop a freshness/quality signal. The gold leg's
    # soft `partial_coverage` (a gappy-but-accepted series) is the ONLY signal that a year's
    # annual mean came from an incomplete subset of trading days; dropping it would serve a
    # gappy mean with zero disclosure. Namespace by leg so it is unambiguous which leg was gappy.
    for w in gold_hist.warnings:
        warnings.append(f"world_reference_gold_leg_{w}")
    for w in fx_hist.warnings:
        warnings.append(f"world_reference_fx_leg_{w}")

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

    # M1 (#178): if the CURRENT calendar year is emitted, its annual mean is only a YEAR-TO-DATE
    # average — a partial-year point, the SAME 'partial mean served as a trusted annual point'
    # class as the boundary-year bug, just on the trailing edge. The gold leg's `partial_coverage`
    # (a WINDOW-aggregate) does NOT catch this: a long window of complete prior years dilutes the
    # in-progress year's low coverage back above the threshold, so that signal goes silent. Flag
    # it INDEPENDENTLY, keyed only on today's year. (Currently latent behind the World Bank FX lag
    # dropping the current year — environmental, not code-enforced — so enforce it here.) Key on
    # the current year being IN `common` (not merely == common[-1]) so it is still caught if a
    # later-dated year is somehow emitted too — unreachable via the public accessor, but robust on
    # any direct _synthesize call.
    current_year = _today().year
    if current_year in common:
        warnings.append(
            f"{_TRAILING_YEAR_TOKEN}: the emitted year {current_year} is the current calendar "
            f"year and still in progress, so its annual mean is a YEAR-TO-DATE partial average "
            f"— not a full-year mean like the settled points; treat it as provisional"
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

    Composes the world-gold annual leg — PRIMARY: World Bank CMO "Pink Sheet" annual gold
    (USD/oz), fetched directly; FALLBACK on any recoverable failure: the daily
    ``CurrencyApiGoldSource`` → ``StooqGoldSource`` failover averaged to annual (disclosed
    via a ``world_reference_gold_source_fallback`` warning) — with annual USD/VND FX (World
    Bank ``PA.NUS.FCRF``) into a one-point-per-calendar-year VND/lượng series (Jan-1
    stamped). The result carries a
    mandatory ``world_reference_excludes_domestic_premium`` warning: the VN domestic
    (SJC/BTMC) price sits a large, time-varying premium (historically +10–21%) ABOVE this
    world reference, so this series understates it — never present it as the domestic price.

    ``start``/``end`` are required and interpreted as an inclusive **calendar-year** window:
    any portion of a year yields that year's annual point, computed from the FULL calendar
    year (so a mid-year ``start``/``end`` never produces a partial-year mean). The ONE
    unavoidable partial year is the **in-progress current year**: if the latest emitted point
    is the current calendar year, its mean is only a year-to-date average — flagged with a
    mechanical ``world_reference_trailing_year_incomplete`` warning so it is never mistaken for
    a full-year point. A multi-year window exceeds CurrencyApi's coverage/range, so it cleanly
    fails over to Stooq (the long-history world-gold source). A total failure of either leg propagates
    (``AllSourcesFailed`` / ``EmptyData``); a window with no overlapping gold+FX years raises
    :class:`EmptyData` (no silent half-result).

    Pass ``http_get`` (and ``timeout``) to inject a transport stub for offline tests; it is
    forwarded to every underlying source. ``max_attempts`` caps the world-gold failover chain.
    """
    # Validate the ORIGINAL bounds (type + ordering) before widening, so an inverted range —
    # even within a single calendar year — is still rejected up front (no network call).
    lo, hi = validate_date_range(start, end, name="gold world-reference history")
    # Snap the fetch window to WHOLE calendar years so each emitted year's gold mean is a TRUE
    # full-year average, matching the FX leg's calendar-year period-average basis (annual-avg ×
    # annual-avg). Without this, a mid-year start/end would make the boundary year a partial-
    # window gold mean while the FX leg stays full-year, silently biasing the boundary point.
    # The FX leg already widens bounds to whole calendar years internally; this aligns the gold
    # leg to the same basis.
    year_start = date(lo.year, 1, 1)
    year_end = date(hi.year, 12, 31)

    # World-gold leg (USD/oz). #185: the PRIMARY is the World Bank CMO annual "Pink Sheet"
    # source — it is annual (matching the synthesis basis exactly: CMO annual gold IS the
    # annual average of daily spot) AND reachable server-side, unlike the daily legs
    # (CurrencyApi sparse + ~1100-day cap, Stooq anti-bot-blocked from datacenter hosts).
    # CMO is fetched DIRECTLY, bypassing FailoverGoldClient: that client's 50% gate counts
    # covered vs expected WEEKDAY trading days, so an annual series (1 bar/year) is <1% of
    # weekdays and would be wrongly rejected. CMO self-validates instead (its own integrity
    # + magnitude guards, EmptyData if no years in span).
    #
    # On any RECOVERABLE CMO failure (SourceError: unreachable/blocked -> SourceUnavailable,
    # malformed/out-of-band -> InvalidData, no years in span -> EmptyData) fall back to the
    # old daily-averaging path so behavior is NEVER worse than #178. The except catches
    # SourceError (NOT bare Exception, N2) so a non-SourceError programmer bug fails loud.
    used_daily_fallback = False
    try:
        gold_hist = WorldBankCmoGoldSource(http_get=http_get, timeout=timeout).get_history(
            year_start, year_end
        )
    except SourceError:
        used_daily_fallback = True
        # CurrencyApi is primary (reliable, no key) but covers only ~2024-03+ with a
        # ~1100-day cap, so any multi-year window raises range-too-wide (a SourceError) and
        # fails over to Stooq, the only full-history world-gold source.
        gold_sources = [
            CurrencyApiGoldSource(http_get=http_get, timeout=timeout),
            StooqGoldSource(http_get=http_get, timeout=timeout),
        ]
        gold_hist = FailoverGoldClient(gold_sources, max_attempts=max_attempts).get_history(
            year_start, year_end
        )

    # Annual USD/VND (World Bank period-average) — annual-only by construction, which is the
    # exact basis we aggregate the gold leg to. Imported lazily to avoid any import cycle.
    from ..fx import history as _fx_history

    fx_hist = _fx_history("USD", "VND", year_start, year_end, http_get=http_get, timeout=timeout)

    result = _synthesize_world_reference(gold_hist, fx_hist)
    if used_daily_fallback:
        # Never-silent disclosure that the daily fallback was used (the pure synthesis is
        # left byte-identical; the fallback note is appended to the finished result here so
        # _synthesize_world_reference stays unchanged).
        result = replace(result, warnings=result.warnings + (_GOLD_SOURCE_FALLBACK_NOTE,))
    return result


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
