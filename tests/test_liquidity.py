"""Liquidity/position-sizing MVP (#146) — offline synthetic only."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

import vnfin
from vnfin.liquidity import (
    LiquidityPoint,
    LiquidityProfile,
    from_price_history,
    profile,
)
from vnfin.exceptions import InvalidData, VnfinError
from vnfin.models import AdjustmentPolicy, Interval, PriceBar, PriceHistory

UTC = timezone.utc


def _bar(d, close, volume):
    return PriceBar(time=datetime(d.year, d.month, d.day, tzinfo=UTC),
                    open=close, high=close, low=close, close=close, volume=volume)


def _hist(bars, *, symbol="FPT", interval=Interval.D1, currency="VND", value_unit="VND",
          source="ssi", warnings=()):
    return PriceHistory(
        symbol=symbol, interval=interval, adjustment_policy=AdjustmentPolicy.PROVIDER_ADJUSTED,
        source=source, bars=tuple(bars), currency=currency, value_unit=value_unit, warnings=tuple(warnings),
    )


def _three():
    # closes 100/200/300, volumes 10/20/30 -> values 1000/4000/9000
    return _hist([_bar(date(2025, 1, 2), 100.0, 10), _bar(date(2025, 1, 3), 200.0, 20),
                  _bar(date(2025, 1, 6), 300.0, 30)])


# 1 + 3 — exact stats + estimate labeling
def test_from_price_history_exact_stats():
    p = from_price_history(_three(), adv_fraction=0.10, capital_vnd=1_000_000_000.0)
    assert isinstance(p, LiquidityProfile) and len(p) == 3
    assert p.avg_daily_value_vnd == pytest.approx((1000 + 4000 + 9000) / 3)
    assert p.median_daily_value_vnd == pytest.approx(4000.0)
    assert p.avg_daily_volume == pytest.approx((10 + 20 + 30) / 3)
    assert p.median_daily_volume == pytest.approx(20.0)
    assert p.max_order_value_vnd == pytest.approx(p.avg_daily_value_vnd * 0.10)
    assert p.value_kind == "close_x_volume_estimate"
    assert "traded_value_estimated_from_close_x_volume" in p.warnings
    assert p.capital_as_avg_daily_value_pct == pytest.approx(1_000_000_000.0 / p.avg_daily_value_vnd * 100)
    assert p.max_order_as_capital_pct == pytest.approx(p.max_order_value_vnd / 1_000_000_000.0 * 100)
    assert all(isinstance(pt, LiquidityPoint) for pt in p.points)


# 2 — even-count median
def test_even_count_median():
    p = from_price_history(_hist([_bar(date(2025, 1, 2), 100.0, 10), _bar(date(2025, 1, 3), 100.0, 30)]))
    assert p.median_daily_volume == pytest.approx(20.0)
    assert p.median_daily_value_vnd == pytest.approx((1000 + 3000) / 2)


# 4 — existing warnings preserved + appended
def test_preserves_existing_warnings():
    p = from_price_history(_hist([_bar(date(2025, 1, 2), 100.0, 10)], warnings=("partial_coverage",)))
    assert "partial_coverage" in p.warnings
    assert "traded_value_estimated_from_close_x_volume" in p.warnings
    assert p.source == "ssi"


# 5 — empty
def test_empty_history_rejected():
    with pytest.raises(InvalidData):
        from_price_history(_hist([]))


def test_non_pricehistory_rejected():
    with pytest.raises(InvalidData):
        from_price_history(object())


# 6 — non-VND / index points rejected
@pytest.mark.parametrize("kw", [{"value_unit": "points"}, {"currency": "USD"}, {"value_unit": "USD"}])
def test_non_vnd_money_series_rejected(kw):
    with pytest.raises(InvalidData):
        from_price_history(_hist([_bar(date(2025, 1, 2), 100.0, 10)], **kw))


# 7 — non-daily interval rejected
def test_non_daily_interval_rejected():
    with pytest.raises(InvalidData):
        from_price_history(_hist([_bar(date(2025, 1, 2), 100.0, 10)], interval=Interval.H1))


# 8 — bad bar fields
def test_bad_bar_fields_rejected():
    with pytest.raises(InvalidData):
        from_price_history(_hist([_bar(date(2025, 1, 2), float("nan"), 10)]))
    with pytest.raises(InvalidData):
        from_price_history(_hist([_bar(date(2025, 1, 2), -1.0, 10)]))
    with pytest.raises(InvalidData):
        from_price_history(_hist([_bar(date(2025, 1, 2), 100.0, -5)]))
    with pytest.raises(InvalidData):
        from_price_history(_hist([_bar(date(2025, 1, 2), 100.0, True)]))


# zero-liquidity -> warning, ratios None, no div-by-zero
def test_zero_volume_window_is_warned_not_fatal():
    p = from_price_history(_hist([_bar(date(2025, 1, 2), 100.0, 0)]), capital_vnd=1_000.0)
    assert p.avg_daily_value_vnd == 0.0
    assert any("zero_liquidity" in w for w in p.warnings)
    assert p.capital_as_avg_daily_value_pct is None


# 10 — bad params
@pytest.mark.parametrize("frac", [0, -0.1, 1.5, float("nan"), True, "x"])
def test_bad_adv_fraction_rejected(frac):
    with pytest.raises(InvalidData):
        from_price_history(_three(), adv_fraction=frac)


@pytest.mark.parametrize("cap", [0, -5, float("inf"), True, "x"])
def test_bad_capital_rejected(cap):
    with pytest.raises(InvalidData):
        from_price_history(_three(), capital_vnd=cap)


# 9 — profile() uses injected client + canonicalizes symbol; malformed -> zero calls
class _FakeClient:
    def __init__(self, hist):
        self._hist = hist
        self.calls = []

    def get_history(self, symbol, interval=Interval.D1, start=None, end=None):
        self.calls.append((symbol, interval, start, end))
        return self._hist


def test_profile_uses_client_and_canonicalizes_symbol():
    c = _FakeClient(_three())
    p = profile("  fpt  ", date(2025, 1, 1), date(2025, 1, 31), client=c)
    assert c.calls and c.calls[0][0] == "FPT" and c.calls[0][1] is Interval.D1
    assert isinstance(p, LiquidityProfile)


@pytest.mark.parametrize("bad", [None, 123, "F PT", "F/PT", "", "   "])
def test_profile_malformed_symbol_zero_calls(bad):
    c = _FakeClient(_three())
    with pytest.raises((InvalidData, VnfinError)):
        profile(bad, date(2025, 1, 1), date(2025, 1, 31), client=c)
    assert c.calls == []


def test_profile_inverted_dates_rejected_zero_calls():
    c = _FakeClient(_three())
    with pytest.raises(VnfinError):
        profile("FPT", date(2025, 6, 1), date(2025, 1, 1), client=c)
    assert c.calls == []


# namespace
def test_liquidity_namespace():
    assert vnfin.liquidity.from_price_history is from_price_history


# B1 — bar-key contract: aware datetime, strictly-ascending, no duplicates.
def test_naive_datetime_bar_rejected():
    naive = PriceBar(time=datetime(2025, 1, 2), open=100.0, high=100.0, low=100.0, close=100.0, volume=10)
    with pytest.raises(InvalidData, match="timezone-aware"):
        from_price_history(_hist([naive]))


def test_non_datetime_bar_time_rejected():
    bad = PriceBar(time="2025-01-02", open=100.0, high=100.0, low=100.0, close=100.0, volume=10)
    with pytest.raises(InvalidData, match="timezone-aware"):
        from_price_history(_hist([bad]))


def test_duplicate_daily_keys_rejected():
    with pytest.raises(InvalidData, match="ascending"):
        from_price_history(_hist([_bar(date(2025, 1, 2), 100.0, 10), _bar(date(2025, 1, 2), 200.0, 20)]))


def test_unsorted_daily_keys_rejected():
    with pytest.raises(InvalidData, match="ascending"):
        from_price_history(_hist([_bar(date(2025, 1, 3), 100.0, 10), _bar(date(2025, 1, 2), 200.0, 20)]))


# B2 — zero close rejected (inherits price positivity); zero volume still allowed.
def test_zero_close_rejected():
    with pytest.raises(InvalidData, match="positive"):
        from_price_history(_hist([_bar(date(2025, 1, 2), 0.0, 10)]))


def test_zero_volume_with_positive_close_allowed():
    p = from_price_history(_hist([_bar(date(2025, 1, 2), 100.0, 0)]))
    assert p.avg_daily_value_vnd == 0.0 and len(p) == 1


# Issue #176 — a LiquidityProfile built from a phantom-tail history carries the
# trailing_zero_volume_tail warning through (v1 = propagate, no new code in liquidity).
def test_phantom_tail_warning_propagates_into_liquidity_profile():
    warning = (
        "trailing_zero_volume_tail: 12 trailing zero-volume flat (O=H=L=C) bars "
        "through 2024-01-13; last real-volume bar 2024-01-01 — likely "
        "suspended/delisted/halted or source forward-fill; treat the tail as non-tradeable"
    )
    # Real day + a flat zero-volume phantom tail; the history already carries the
    # phantom warning (as _finalize would have attached it).
    bars = [_bar(date(2025, 1, 2), 100.0, 10)]
    bars += [_bar(date(2025, 1, 3 + i), 35.0, 0) for i in range(12)]
    p = from_price_history(_hist(bars, warnings=(warning,)))
    assert any(w.startswith("trailing_zero_volume_tail") for w in p.warnings)
    assert "traded_value_estimated_from_close_x_volume" in p.warnings
