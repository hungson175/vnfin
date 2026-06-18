"""Tests for the VN trading-calendar helper (synthetic / public-holiday dates only)."""
from datetime import date, datetime, timezone

import pytest

from vnfin.calendar import (
    VN_MARKET_HOLIDAYS,
    as_date,
    expected_latest_trading_day,
    is_trading_day,
    is_weekend,
    next_trading_day,
    previous_trading_day,
)


def test_as_date_coerces_datetime_and_passthrough_date():
    assert as_date(datetime(2024, 1, 4, 9, 30, tzinfo=timezone.utc)) == date(2024, 1, 4)
    assert as_date(date(2024, 1, 4)) == date(2024, 1, 4)
    assert as_date(None) is None


def test_as_date_rejects_other_types():
    with pytest.raises(TypeError):
        as_date("2024-01-04")


def test_is_weekend():
    assert is_weekend(date(2024, 1, 6)) is True  # Saturday
    assert is_weekend(date(2024, 1, 7)) is True  # Sunday
    assert is_weekend(date(2024, 1, 5)) is False  # Friday


def test_is_trading_day_plain_weekday():
    # 2024-01-04 is a Thursday with no holiday.
    assert is_trading_day(date(2024, 1, 4)) is True


def test_is_trading_day_false_on_weekend():
    assert is_trading_day(date(2024, 1, 6)) is False  # Saturday


def test_is_trading_day_false_on_holiday():
    # New Year's Day 2024 is a Monday holiday.
    assert date(2024, 1, 1) in VN_MARKET_HOLIDAYS
    assert is_trading_day(date(2024, 1, 1)) is False


def test_is_trading_day_false_during_tet():
    # 2024 Tet weekday closure.
    assert is_trading_day(date(2024, 2, 13)) is False
    assert is_trading_day(date(2025, 1, 28)) is False  # 2025 Tet weekday closure


def test_previous_trading_day_skips_weekend():
    # Monday 2024-01-08 -> previous trading day is Friday 2024-01-05.
    assert previous_trading_day(date(2024, 1, 8)) == date(2024, 1, 5)


def test_previous_trading_day_skips_holiday_block():
    # Tuesday 2024-01-02 -> previous trading day skips New Year (Mon Jan 1) AND the
    # weekend, landing on Friday 2023-12-29.
    assert previous_trading_day(date(2024, 1, 2)) == date(2023, 12, 29)


def test_previous_trading_day_is_strictly_before():
    # Even if the arg is itself a trading day, previous_trading_day is strictly earlier.
    assert previous_trading_day(date(2024, 1, 4)) == date(2024, 1, 3)


def test_next_trading_day_skips_weekend():
    # Friday 2024-01-05 -> next trading day is Monday 2024-01-08.
    assert next_trading_day(date(2024, 1, 5)) == date(2024, 1, 8)


def test_next_trading_day_skips_holiday():
    # Sunday 2023-12-31 -> skip New Year (Mon Jan 1) -> Tuesday 2024-01-02.
    assert next_trading_day(date(2023, 12, 31)) == date(2024, 1, 2)


def test_expected_latest_on_trading_day_is_itself():
    assert expected_latest_trading_day(date(2024, 1, 4)) == date(2024, 1, 4)


def test_expected_latest_on_saturday_rolls_back_to_friday():
    assert expected_latest_trading_day(date(2024, 1, 6)) == date(2024, 1, 5)


def test_expected_latest_on_sunday_rolls_back_to_friday():
    assert expected_latest_trading_day(date(2024, 1, 7)) == date(2024, 1, 5)


def test_expected_latest_during_holiday_rolls_back():
    # New Year's Day (Mon 2024-01-01) -> latest trading day is Friday 2023-12-29.
    assert expected_latest_trading_day(date(2024, 1, 1)) == date(2023, 12, 29)


def test_expected_latest_accepts_datetime():
    assert expected_latest_trading_day(
        datetime(2024, 1, 6, 12, 0, tzinfo=timezone.utc)
    ) == date(2024, 1, 5)


def test_holiday_set_is_frozen_and_nonempty():
    assert isinstance(VN_MARKET_HOLIDAYS, frozenset)
    assert len(VN_MARKET_HOLIDAYS) > 0


def test_year_outside_maintained_range_degrades_to_weekend_logic():
    # Far-future year with no maintained holidays: a plain weekday is a trading day,
    # and the weekend still rolls back correctly. (No crash, graceful degradation.)
    assert is_trading_day(date(2099, 6, 3)) is True  # a Wednesday
    assert is_trading_day(date(2099, 6, 6)) is False  # a Saturday
    assert expected_latest_trading_day(date(2099, 6, 6)) == date(2099, 6, 5)  # Friday
