"""Vietnam trading-calendar helper.

A small, dependency-free helper that answers "is this a market trading day?" so
range-coverage diagnostics (see :meth:`vnfin.client.FailoverPriceClient._coverage_warnings`)
do not raise false staleness alarms over weekends and public holidays.

Scope and limitations (intentionally conservative)
--------------------------------------------------
* A *trading day* here is any weekday (Mon-Fri) that is **not** in the maintained
  set of Vietnam public-holiday market closures (:data:`VN_MARKET_HOLIDAYS`).
* The holiday set is a hand-maintained constant covering the years for which
  official statutory dates are known. It is **not** lunar-computed; Tet and other
  lunar-dependent dates must be appended each year as MOLISA/the Ministry of Home
  Affairs announces them. Years outside the maintained range degrade gracefully to
  weekend-only logic (so the worst case is "we don't suppress a holiday gap", never
  a crash).
* Half-day sessions and ad-hoc closures are out of scope; this helper deliberately
  errs toward *not* warning rather than toward false positives.

Clean-room: dates below are transcribed from public government/holiday references,
not from any third-party Python market-data library.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

__all__ = [
    "VN_MARKET_HOLIDAYS",
    "as_date",
    "is_weekend",
    "is_trading_day",
    "previous_trading_day",
    "next_trading_day",
    "expected_latest_trading_day",
]

# Maintained set of Vietnam public-holiday MARKET closures (HOSE/HNX/UPCoM closed).
# Weekends are handled separately and are NOT listed here. When a fixed-date holiday
# falls on a weekend the statutory compensatory weekday is what closes the market, so
# the *observed* weekday closure is what we encode.
#
# Sources (public, non-vnstock):
#   2024: https://www.timeanddate.com/holidays/vietnam/2024
#   2025: https://www.vietnam-briefing.com/news/2025-vietnam-public-holidays-list.html/
#   2026: https://en.baochinhphu.vn/ministry-of-home-affairs-announces-2026-holiday-schedule-...
# Keep this list sorted and append new years as they are officially announced.
VN_MARKET_HOLIDAYS: frozenset[date] = frozenset(
    {
        # --- 2024 ---
        date(2024, 1, 1),  # New Year's Day
        # Tet (Lunar New Year) 2024: Feb 8-14
        date(2024, 2, 8),
        date(2024, 2, 9),
        date(2024, 2, 12),  # Feb 10-11 are Sat/Sun
        date(2024, 2, 13),
        date(2024, 2, 14),
        date(2024, 4, 18),  # Hung Kings' Commemoration (10th day, 3rd lunar month)
        date(2024, 4, 29),  # Reunification Day observed (Apr 30 bridge)
        date(2024, 4, 30),  # Reunification Day
        date(2024, 5, 1),  # International Labour Day
        date(2024, 9, 2),  # National Day
        date(2024, 9, 3),  # National Day (observed extra day)
        # --- 2025 ---
        date(2025, 1, 1),  # New Year's Day
        # Tet 2025: weekday closures Jan 27-31 (Jan 25-26 & Feb 1-2 are weekends)
        date(2025, 1, 27),
        date(2025, 1, 28),
        date(2025, 1, 29),
        date(2025, 1, 30),
        date(2025, 1, 31),
        date(2025, 4, 7),  # Hung Kings' Commemoration (observed)
        date(2025, 4, 30),  # Reunification Day
        date(2025, 5, 1),  # International Labour Day
        date(2025, 5, 2),  # Labor Day bridge (HNX 2025 schedule)
        date(2025, 9, 1),  # National Day (observed)
        date(2025, 9, 2),  # National Day
        # --- 2026 ---
        date(2026, 1, 1),  # New Year's Day
        # Tet 2026: Feb 14-22 -> weekday closures Feb 16-20 (14-15 & 21-22 are weekends)
        date(2026, 2, 16),
        date(2026, 2, 17),
        date(2026, 2, 18),
        date(2026, 2, 19),
        date(2026, 2, 20),
        date(2026, 4, 27),  # Hung Kings' Commemoration (observed, Apr 26 is Sunday)
        date(2026, 4, 30),  # Reunification Day
        date(2026, 5, 1),  # International Labour Day
        date(2026, 8, 31),  # National Day bridge (HNX 2026 schedule)
        date(2026, 9, 1),  # National Day (observed)
        date(2026, 9, 2),  # National Day
    }
)


def as_date(d) -> date | None:
    """Coerce ``date``/``datetime``/``None`` to a plain ``date`` (or ``None``)."""
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    raise TypeError(f"expected date/datetime, got {type(d).__name__}")


def is_weekend(d) -> bool:
    """True if ``d`` is a Saturday or Sunday."""
    return as_date(d).weekday() >= 5  # Mon=0 .. Sat=5, Sun=6


def is_trading_day(d) -> bool:
    """True if ``d`` is a VN market trading day (weekday and not a known holiday).

    Years outside the maintained holiday range fall back to weekend-only logic.
    """
    dd = as_date(d)
    return not is_weekend(dd) and dd not in VN_MARKET_HOLIDAYS


def previous_trading_day(d) -> date:
    """The most recent trading day strictly **before** ``d``."""
    dd = as_date(d) - timedelta(days=1)
    while not is_trading_day(dd):
        dd -= timedelta(days=1)
    return dd


def next_trading_day(d) -> date:
    """The earliest trading day strictly **after** ``d``."""
    dd = as_date(d) + timedelta(days=1)
    while not is_trading_day(dd):
        dd += timedelta(days=1)
    return dd


def expected_latest_trading_day(asof) -> date:
    """The most recent trading day on or before ``asof``.

    If ``asof`` itself is a trading day it is returned unchanged; otherwise we walk
    back to the prior trading day. This is the latest bar a fully up-to-date source
    could be expected to have for a request ending at ``asof``.
    """
    dd = as_date(asof)
    if is_trading_day(dd):
        return dd
    return previous_trading_day(dd)
