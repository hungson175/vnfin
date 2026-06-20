"""Issue #178 — world-reference VND/lượng gold history (a LABELED synthesis).

``gold.world_reference_history_vnd(start, end)`` composes the library's existing
world-gold daily history (USD/oz; CurrencyApi→Stooq failover) with annual USD/VND FX
(World Bank ``PA.NUS.FCRF``) into an ANNUAL VND/lượng reference series:

    VND/lượng[year] = annual_avg(world_gold_usd_oz)[year]
                       × annual_USD_VND[year]
                       × (GRAMS_PER_LUONG / GRAMS_PER_TROY_OZ)

It is the world-gold-IMPLIED VND value, NOT the VN domestic (SJC/BTMC) price — the
domestic price carries a large, time-varying premium, so this series understates it and
self-discloses redundantly (accessor name, ``source``, ``unit``, and a mechanical
``world_reference_excludes_domestic_premium`` warning).

Synthetic fixtures only — fabricated round numbers, no real provider rows, no network.
"""
from __future__ import annotations

import json
import math
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.exceptions import AllSourcesFailed, EmptyData, InvalidData
from vnfin.fx.history_models import FXHistory, FXPoint
from vnfin.gold import GoldBar, GoldHistory, domestic_history, world_reference_history_vnd
from vnfin.gold.models import GoldHistory as _GH  # noqa: F401  (sanity: importable)
from vnfin.gold.world_reference import (
    GRAMS_PER_LUONG,
    GRAMS_PER_TROY_OZ,
    OZ_TO_LUONG,
    _synthesize_world_reference,
)
from vnfin.macro.indicators import Frequency


# --------------------------------------------------------------------------- #
# Physical-weight oz→lượng factor (re-derived here so a regression catches the   #
# inverted-factor bug from the original spec).                                 #
# --------------------------------------------------------------------------- #
def test_module_factor_is_grams_per_luong_over_troy_oz():
    # 1 lượng = 37.5 g is HEAVIER than 1 troy oz = 31.1035 g, so USD/oz → USD/lượng
    # scales UP (factor > 1). The inverted spec ratio (31.1035/37.5 ≈ 0.83) is WRONG.
    assert GRAMS_PER_LUONG == 37.5
    assert GRAMS_PER_TROY_OZ == pytest.approx(31.1035)
    assert OZ_TO_LUONG == pytest.approx(37.5 / 31.1035)
    assert OZ_TO_LUONG > 1.2 and OZ_TO_LUONG < 1.21  # ≈ 1.20566, never the inverted 0.83


# --------------------------------------------------------------------------- #
# Builders for the pure-synthesis unit tests                                   #
# --------------------------------------------------------------------------- #
def _gold_usd_oz(prices_by_date):
    """A world-gold USD/oz GoldHistory from {date: usd_per_oz}."""
    bars = tuple(GoldBar(date=d, price=p) for d, p in sorted(prices_by_date.items()))
    return GoldHistory(
        product="XAU",
        unit="USD/oz",
        value_unit="USD/oz",
        currency="USD",
        source="stooq",
        bars=bars,
        fetched_at_utc=datetime.now(timezone.utc),
    )


def _fx_usd_vnd(rate_by_year):
    """An annual USD/VND FXHistory from {year: rate} (Jan-1 stamped, like World Bank)."""
    points = tuple(FXPoint(date=date(y, 1, 1), rate=r) for y, r in sorted(rate_by_year.items()))
    return FXHistory(
        base="USD",
        quote="VND",
        points=points,
        unit="VND per 1 USD",
        frequency=Frequency.ANNUAL,
        source="worldbank_fx",
        fetched_at_utc=datetime.now(timezone.utc),
    )


def _premium(result):
    return [w for w in result.warnings if w.startswith("world_reference_excludes_domestic_premium")]


# --------------------------------------------------------------------------- #
# _synthesize_world_reference — math, units, labeling                          #
# --------------------------------------------------------------------------- #
def test_synthesis_annual_point_is_gold_x_fx_x_factor():
    gold = _gold_usd_oz({date(2022, 6, 15): 2000.0, date(2023, 6, 15): 2100.0})
    fx = _fx_usd_vnd({2022: 24000.0, 2023: 24500.0})
    out = _synthesize_world_reference(gold, fx)

    assert isinstance(out, GoldHistory)
    assert [b.date for b in out.bars] == [date(2022, 1, 1), date(2023, 1, 1)]
    assert out.bars[0].price == pytest.approx(2000.0 * 24000.0 * OZ_TO_LUONG)
    assert out.bars[1].price == pytest.approx(2100.0 * 24500.0 * OZ_TO_LUONG)


def test_synthesis_uses_annual_average_of_daily_gold():
    # two daily gold bars in 2022 -> the annual point uses their AVERAGE (1900), not last.
    gold = _gold_usd_oz({date(2022, 1, 3): 1800.0, date(2022, 7, 1): 2000.0})
    fx = _fx_usd_vnd({2022: 24000.0})
    out = _synthesize_world_reference(gold, fx)
    assert len(out.bars) == 1
    assert out.bars[0].price == pytest.approx(1900.0 * 24000.0 * OZ_TO_LUONG)


def test_synthesis_labeling_is_world_reference_never_domestic():
    gold = _gold_usd_oz({date(2022, 6, 15): 2000.0})
    fx = _fx_usd_vnd({2022: 24000.0})
    out = _synthesize_world_reference(gold, fx)

    assert out.unit == "VND/luong" and out.value_unit == "VND/luong"
    assert out.currency == "VND"
    assert "world-reference" in out.product
    # Redundant disclosure: NONE of the human-visible labels may say "domestic".
    for label in (out.product, out.unit, out.value_unit, out.source):
        assert "domestic" not in label.lower()
    # provenance names both legs
    assert "World Bank" in out.source and "world-gold" in out.source
    assert out.fetched_at_utc is not None and out.fetched_at_utc.tzinfo is not None


def test_synthesis_factor_not_inverted_regression():
    # gold $2000/oz, USD/VND 24,000 -> ~57.9M VND/lượng. The inverted factor would give
    # ~39.8M (< 50M); assert we are firmly in the correct band.
    gold = _gold_usd_oz({date(2023, 6, 15): 2000.0})
    fx = _fx_usd_vnd({2023: 24000.0})
    out = _synthesize_world_reference(gold, fx)
    expected = 2000.0 * 24000.0 * (37.5 / 31.1035)
    assert out.bars[0].price == pytest.approx(expected)
    assert out.bars[0].price > 50_000_000  # inverted (~39.8M) would fail this


# --------------------------------------------------------------------------- #
# _synthesize_world_reference — mandatory disclosure                           #
# --------------------------------------------------------------------------- #
def test_synthesis_premium_note_is_mechanical_token_with_human_tail():
    out = _synthesize_world_reference(
        _gold_usd_oz({date(2022, 6, 15): 2000.0}), _fx_usd_vnd({2022: 24000.0})
    )
    notes = _premium(out)
    assert len(notes) == 1
    note = notes[0]
    assert note.startswith("world_reference_excludes_domestic_premium")
    assert "+10" in note and "21%" in note  # the time-varying premium band
    assert "SJC" in note or "domestic price" in note.lower()


def test_synthesis_discloses_annual_basis():
    out = _synthesize_world_reference(
        _gold_usd_oz({date(2022, 6, 15): 2000.0}), _fx_usd_vnd({2022: 24000.0})
    )
    assert any(w.startswith("world_reference_annual_basis") for w in out.warnings)


# --------------------------------------------------------------------------- #
# _synthesize_world_reference — year alignment & guards                        #
# --------------------------------------------------------------------------- #
def test_synthesis_intersects_years_and_warns_on_dropped():
    # gold {2021,2022,2023}; fx {2022,2023,2024} -> common {2022,2023}; 2021 (no fx) and
    # 2024 (no gold) dropped -> a non-silent partial-coverage warning naming both.
    gold = _gold_usd_oz(
        {date(2021, 6, 1): 1800.0, date(2022, 6, 1): 1900.0, date(2023, 6, 1): 2000.0}
    )
    fx = _fx_usd_vnd({2022: 24000.0, 2023: 24500.0, 2024: 25000.0})
    out = _synthesize_world_reference(gold, fx)

    assert [b.date.year for b in out.bars] == [2022, 2023]
    partial = [w for w in out.warnings if w.startswith("world_reference_partial_year_coverage")]
    assert len(partial) == 1
    assert "2021" in partial[0] and "2024" in partial[0]


def test_synthesis_full_overlap_has_no_partial_warning():
    gold = _gold_usd_oz({date(2022, 6, 1): 1900.0, date(2023, 6, 1): 2000.0})
    fx = _fx_usd_vnd({2022: 24000.0, 2023: 24500.0})
    out = _synthesize_world_reference(gold, fx)
    assert not any(w.startswith("world_reference_partial_year_coverage") for w in out.warnings)


def test_synthesis_empty_overlap_raises_empty_data():
    gold = _gold_usd_oz({date(2021, 6, 1): 1800.0, date(2022, 6, 1): 1900.0})
    fx = _fx_usd_vnd({2023: 24500.0, 2024: 25000.0})
    with pytest.raises(EmptyData):
        _synthesize_world_reference(gold, fx)


def test_synthesis_non_positive_synthesized_value_raises_invalid():
    # Defensive guard: a zero/garbage gold price -> non-positive product -> InvalidData
    # (inputs are normally positive; this must never be served silently).
    gold = _gold_usd_oz({date(2022, 6, 1): 0.0})
    fx = _fx_usd_vnd({2022: 24000.0})
    with pytest.raises(InvalidData):
        _synthesize_world_reference(gold, fx)


def test_synthesis_negative_value_raises_invalid():
    # The <= 0 arm must reject a negative (not just zero) synthesized value.
    gold = _gold_usd_oz({date(2022, 6, 1): -1900.0})
    fx = _fx_usd_vnd({2022: 24000.0})
    with pytest.raises(InvalidData):
        _synthesize_world_reference(gold, fx)


def test_synthesis_non_finite_value_raises_invalid():
    # The `not math.isfinite(...)` arm must reject a non-finite product (e.g. inf FX).
    gold = _gold_usd_oz({date(2022, 6, 1): 1900.0})
    fx = _fx_usd_vnd({2022: math.inf})
    with pytest.raises(InvalidData):
        _synthesize_world_reference(gold, fx)


def test_synthesis_forwards_gold_leg_partial_coverage_warning():
    # A gappy-but-accepted world-gold leg carries a soft `partial_coverage` warning from
    # FailoverGoldClient; the synthesis must FORWARD it (never drop the only freshness signal
    # that the annual mean came from an incomplete subset of trading days).
    gold = replace(
        _gold_usd_oz({date(2022, 6, 1): 1900.0}),
        warnings=("partial_coverage: covered 5/10 expected trading days (50% < 90%); series may be gappy",),
    )
    fx = _fx_usd_vnd({2022: 24000.0})
    out = _synthesize_world_reference(gold, fx)
    assert any("partial_coverage" in w for w in out.warnings)


def test_synthesis_bars_strictly_ascending():
    gold = _gold_usd_oz(
        {date(2021, 6, 1): 1800.0, date(2022, 6, 1): 1900.0, date(2023, 6, 1): 2000.0}
    )
    fx = _fx_usd_vnd({2021: 23500.0, 2022: 24000.0, 2023: 24500.0})
    out = _synthesize_world_reference(gold, fx)
    dates = [b.date for b in out.bars]
    assert dates == sorted(dates)
    assert len(set(dates)) == len(dates)


# --------------------------------------------------------------------------- #
# domestic_history — reserved, source-gap diagnostic (never the synthesis)     #
# --------------------------------------------------------------------------- #
def test_domestic_history_raises_clear_source_gap_diagnostic():
    with pytest.raises(NotImplementedError) as ei:
        domestic_history(date(2020, 1, 1), date(2024, 12, 31))
    msg = str(ei.value)
    assert "#182" in msg  # points at the source hunt
    assert "world_reference_history_vnd" in msg  # names the non-substitute
    assert "premium" in msg.lower()


def test_domestic_history_never_returns_a_series():
    # belt-and-suspenders: it must RAISE, not return any GoldHistory
    with pytest.raises(NotImplementedError):
        domestic_history()


# --------------------------------------------------------------------------- #
# world_reference_history_vnd — full fetch+compose path (URL-routing fake)      #
# --------------------------------------------------------------------------- #
def _weekdays(lo, hi):
    d, one = lo, timedelta(days=1)
    while d <= hi:
        if d.weekday() < 5:
            yield d
        d += one


def _stooq_csv(gold_by_year):
    """Daily Stooq xauusd CSV: every weekday of each year at that year's constant
    USD/oz close (so the annual average == that year's price exactly)."""
    lines = ["Date,Open,High,Low,Close,Volume"]
    for year in sorted(gold_by_year):
        p = gold_by_year[year]
        for d in _weekdays(date(year, 1, 1), date(year, 12, 31)):
            lines.append(f"{d.isoformat()},{p},{p},{p},{p},0")
    return "\n".join(lines) + "\n"


def _wb_json(fx_by_year):
    """World Bank PA.NUS.FCRF (VNM) envelope for {year: rate}, newest-first like the API."""
    obs = [
        {
            "indicator": {"id": "PA.NUS.FCRF", "value": "Official exchange rate (LCU per US$, period average)"},
            "country": {"id": "VN", "value": "Viet Nam"},
            "countryiso3code": "VNM",
            "date": str(year),
            "value": float(rate),
            "unit": "",
            "obs_status": "",
            "decimal": 0,
        }
        for year, rate in sorted(fx_by_year.items(), reverse=True)
    ]
    meta = {"page": 1, "pages": 1, "per_page": 20000, "total": len(obs), "sourceid": "2", "lastupdated": "2025-07-01"}
    return json.dumps([meta, obs])


def _router(*, gold_by_year=None, fx_by_year=None, stooq_text=None):
    """A URL-routing http_get fake. Serves Stooq CSV for stooq.com and World Bank JSON
    for worldbank.org; 404s currency-api (cdn.jsdelivr.net) so a multi-year window
    cleanly fails over to Stooq. Accepts both the gold (url,params,headers) and the WB
    (..,json_body) call shapes."""
    stooq = stooq_text if stooq_text is not None else _stooq_csv(gold_by_year or {})
    wb = _wb_json(fx_by_year or {})

    def _get(url, params=None, headers=None, json_body=None):
        if "stooq.com" in url:
            return stooq
        if "worldbank.org" in url:
            return wb
        if "jsdelivr.net" in url or "currency-api" in url:
            raise FileNotFoundError("404 (currency-api disabled in test)")
        raise AssertionError(f"unexpected URL in test: {url}")

    return _get


_GOLD = {2021: 1800.0, 2022: 1900.0, 2023: 2000.0, 2024: 2100.0}
_FX = {2021: 23500.0, 2022: 24000.0, 2023: 24500.0, 2024: 25000.0}
_START, _END = date(2021, 1, 1), date(2024, 12, 31)  # 4 whole years (>1100d -> CA fails over)


def test_accessor_happy_path_builds_annual_vnd_luong_series():
    out = world_reference_history_vnd(_START, _END, http_get=_router(gold_by_year=_GOLD, fx_by_year=_FX))
    assert isinstance(out, GoldHistory)
    assert [b.date for b in out.bars] == [date(y, 1, 1) for y in (2021, 2022, 2023, 2024)]
    for b in out.bars:
        y = b.date.year
        assert b.price == pytest.approx(_GOLD[y] * _FX[y] * OZ_TO_LUONG)
    assert out.unit == "VND/luong" and out.currency == "VND"
    assert _premium(out)  # mandatory disclosure rides through the full path


def test_accessor_gold_total_failure_propagates():
    # both world-gold sources fail (CurrencyApi: range-too-wide InvalidData; Stooq: anti-bot
    # HTML -> SourceUnavailable) -> AllSourcesFailed bubbles up (no silent half-result).
    html = "<!DOCTYPE html><html><body><noscript>requires JavaScript</noscript></body></html>"
    with pytest.raises(AllSourcesFailed):
        world_reference_history_vnd(_START, _END, http_get=_router(fx_by_year=_FX, stooq_text=html))


def test_accessor_fx_missing_propagates():
    # gold succeeds but the requested window has no World Bank FX -> EmptyData propagates.
    out_of_window_fx = {2010: 20000.0}
    with pytest.raises(EmptyData):
        world_reference_history_vnd(
            _START, _END, http_get=_router(gold_by_year=_GOLD, fx_by_year=out_of_window_fx)
        )


def test_accessor_rejects_inverted_date_range():
    with pytest.raises(InvalidData):
        world_reference_history_vnd(date(2024, 1, 1), date(2021, 1, 1), http_get=_router())


def _stooq_csv_intra_year_2023():
    """A Stooq CSV where 2023 VARIES within the year (H1 at 1000, H2 at 3000 USD/oz) and
    2024 is constant. Returns (csv_text, {date: price}) so the test can compute the true
    full-calendar-year 2023 mean. The two halves have a large gap so a partial- vs
    full-year mean differ unmistakably."""
    lines = ["Date,Open,High,Low,Close,Volume"]
    prices: dict[date, float] = {}
    for d in _weekdays(date(2023, 1, 1), date(2023, 12, 31)):
        p = 1000.0 if d.month <= 6 else 3000.0
        prices[d] = p
        lines.append(f"{d.isoformat()},{p},{p},{p},{p},0")
    for d in _weekdays(date(2024, 1, 1), date(2024, 12, 31)):
        prices[d] = 2000.0
        lines.append(f"{d.isoformat()},2000.0,2000.0,2000.0,2000.0,0")
    return "\n".join(lines) + "\n", prices


def test_accessor_boundary_year_uses_full_calendar_year_mean():
    # Regression for the boundary-year partial-mean bug: a mid-year `start` must NOT make the
    # boundary year's annual point a partial-window mean. The 2023 annual point must use the
    # FULL calendar-year mean (to match the full-year FX period-average it is multiplied by),
    # NOT just the Jul-Dec slice the caller's raw window would otherwise select.
    csv, prices = _stooq_csv_intra_year_2023()
    fx = {2023: 24000.0, 2024: 25000.0}
    out = world_reference_history_vnd(
        date(2023, 7, 1), date(2024, 12, 31),  # mid-year start in the boundary year
        http_get=_router(fx_by_year=fx, stooq_text=csv),
    )
    by_year = {b.date.year: b.price for b in out.bars}
    days_2023 = [d for d in prices if d.year == 2023]
    full_year_2023_mean = sum(prices[d] for d in days_2023) / len(days_2023)
    # correct: full-calendar-year mean × full-year FX × factor
    assert by_year[2023] == pytest.approx(full_year_2023_mean * 24000.0 * OZ_TO_LUONG)
    # the buggy partial-window mean (Jul-Dec only = 3000) must NOT be what we serve
    assert by_year[2023] != pytest.approx(3000.0 * 24000.0 * OZ_TO_LUONG)
