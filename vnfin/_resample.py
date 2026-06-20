"""#183 — client-side aggregation of an already-fetched D1 series into coarser
calendar periods (W1/MN1/Q1/Y1).

The VN equity/index sources are daily-native — none serves a native weekly/monthly
endpoint. So an aggregated cadence series is built *in memory* from the fetched D1 bars;
no new source and no new network call. The aggregation is OHLC-per-period and applies
identically to prices (VND) and index (points) — :func:`resample_history` preserves the
enclosing :class:`PriceHistory`'s ``value_unit``/``currency``/``source`` etc. via
:func:`dataclasses.replace`.

Two never-silent provenance signals are appended to the result's ``warnings``:

* :data:`RESAMPLED_FROM_D1` — ALWAYS, so the series discloses it is aggregated, not native.
* a :data:`PARTIAL_PERIOD_TOKEN`-prefixed warning when the first/last emitted bar covers an
  incomplete calendar period relative to the requested window (the bars are KEPT, not dropped).

⚠️ ``Interval.M1`` is one MINUTE; monthly is ``Interval.MN1``. The pandas alias ``'M'``
maps to ``MN1`` (MONTH), never ``M1``.
"""
from __future__ import annotations

import calendar
from dataclasses import replace
from datetime import date, datetime
from typing import Callable

from .exceptions import InvalidData, UnsupportedInterval
from .models import Interval, PriceBar, PriceHistory

# Coarser-than-daily periods this module can produce from a D1 series.
_RESAMPLE_INTERVALS = (Interval.W1, Interval.MN1, Interval.Q1, Interval.Y1)

# pandas-style aliases (case-insensitive). 'M' -> MN1 (MONTH, never minute).
_PANDAS_ALIASES = {
    "D": Interval.D1,
    "W": Interval.W1,
    "M": Interval.MN1,
    "Q": Interval.Q1,
    "Y": Interval.Y1,
}

RESAMPLED_FROM_D1 = "resampled_from_d1"
PARTIAL_PERIOD_TOKEN = "resample_partial_period"


def resolve_interval(value) -> Interval:
    """Resolve ``value`` to an :class:`Interval`.

    * an :class:`Interval` member -> itself;
    * a pandas alias string (``'D'``/``'W'``/``'M'``/``'Q'``/``'Y'``, case-insensitive,
      whitespace-stripped) -> the corresponding member, with ``'M'`` -> ``MN1`` (MONTH);
    * anything else -> :class:`~vnfin.exceptions.InvalidData` listing the accepted forms.

    A raw provider token like ``'1d'`` is NOT an accepted alias — pass ``Interval.D1``.
    """
    if isinstance(value, Interval):
        return value
    if isinstance(value, str):
        key = value.strip().upper()
        if key in _PANDAS_ALIASES:
            return _PANDAS_ALIASES[key]
    raise InvalidData(
        f"interval {value!r} is not recognized; pass an Interval member "
        f"(e.g. Interval.D1/W1/MN1/Q1/Y1) or a pandas alias string "
        f"('D','W','M','Q','Y'; case-insensitive). Note 'M' = MONTH (MN1), not minute (M1)."
    )


def apply_interval(value, start, end, fetch: Callable[[Interval], PriceHistory]) -> PriceHistory:
    """Resolve ``value`` and return the requested series.

    * ``W1``/``MN1``/``Q1``/``Y1`` (coarser than daily, NOT natively served) ->
      :func:`resample_history` of a ``fetch(Interval.D1)`` daily series;
    * everything else — ``D1`` AND the intraday intervals (``M1``/``M5``/``M15``/``M30``/
      ``H1``) — -> ``fetch(interval)`` UNCHANGED. These are served **natively** by the
      sources that support them, so #183 adds resampling *without removing any pre-existing
      native path* (it is purely additive). A truly-unsupported interval is rejected by the
      source's own ``supports()`` capability gate (``UnsupportedInterval``), exactly as
      before this feature — the resample layer never rejects intraday.

    ``fetch`` is called with the interval to fetch; ``start``/``end`` are the requested
    window (used only for partial-period detection on a resampled result).
    """
    interval = resolve_interval(value)
    if interval in _RESAMPLE_INTERVALS:
        return resample_history(fetch(Interval.D1), interval, start, end)
    return fetch(interval)


# --------------------------------------------------------------------------- #
# period keys + calendar bounds
# --------------------------------------------------------------------------- #
def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    return value


def _period_key(d: date, interval: Interval):
    if interval is Interval.W1:
        iso = d.isocalendar()
        return (iso[0], iso[1])  # (iso_year, iso_week)
    if interval is Interval.MN1:
        return (d.year, d.month)
    if interval is Interval.Q1:
        return (d.year, (d.month - 1) // 3 + 1)
    if interval is Interval.Y1:
        return (d.year,)
    raise UnsupportedInterval(f"cannot resample to interval {interval}")  # pragma: no cover


def _period_calendar_start(key, interval: Interval) -> date:
    if interval is Interval.W1:
        iso_year, iso_week = key
        return date.fromisocalendar(iso_year, iso_week, 1)  # Monday of the ISO week
    if interval is Interval.MN1:
        year, month = key
        return date(year, month, 1)
    if interval is Interval.Q1:
        year, quarter = key
        return date(year, (quarter - 1) * 3 + 1, 1)
    if interval is Interval.Y1:
        (year,) = key
        return date(year, 1, 1)
    raise UnsupportedInterval(f"cannot resample to interval {interval}")  # pragma: no cover


def _period_calendar_end(key, interval: Interval) -> date:
    if interval is Interval.W1:
        iso_year, iso_week = key
        return date.fromisocalendar(iso_year, iso_week, 7)  # Sunday of the ISO week
    if interval is Interval.MN1:
        year, month = key
        return date(year, month, calendar.monthrange(year, month)[1])
    if interval is Interval.Q1:
        year, quarter = key
        last_month = quarter * 3
        return date(year, last_month, calendar.monthrange(year, last_month)[1])
    if interval is Interval.Y1:
        (year,) = key
        return date(year, 12, 31)
    raise UnsupportedInterval(f"cannot resample to interval {interval}")  # pragma: no cover


# --------------------------------------------------------------------------- #
# aggregation
# --------------------------------------------------------------------------- #
def resample_history(daily: PriceHistory, interval: Interval, start, end) -> PriceHistory:
    """Aggregate a D1 :class:`PriceHistory` into ``interval`` calendar periods.

    OHLC-per-period (open=first, high=max, low=min, close=last, volume=sum); each
    aggregated bar is labelled at the **last actual trading day** in the period (a real
    market date, never a synthetic calendar boundary). Works for prices AND index — the
    enclosing result's ``value_unit``/``currency``/``source``/etc. are preserved.
    """
    base_warnings = tuple(daily.warnings)

    # Empty daily series: no bars to group, no partial-period concept — disclose + return.
    if not daily.bars:
        return replace(
            daily,
            interval=interval,
            bars=(),
            warnings=base_warnings + (RESAMPLED_FROM_D1,),
        )

    # Group chronologically by calendar-period key (defensive sort by time).
    ordered = sorted(daily.bars, key=lambda b: b.time)
    groups: dict = {}  # key -> list[PriceBar] in chronological order
    key_order: list = []
    for bar in ordered:
        key = _period_key(bar.time.date(), interval)
        if key not in groups:
            groups[key] = []
            key_order.append(key)
        groups[key].append(bar)

    new_bars = []
    for key in key_order:
        members = groups[key]
        first, last = members[0], members[-1]
        new_bars.append(
            PriceBar(
                time=last.time,  # last ACTUAL trading day in the period
                open=first.open,
                high=max(b.high for b in members),
                low=min(b.low for b in members),
                close=last.close,
                volume=sum(b.volume for b in members),
            )
        )

    warnings = base_warnings + (RESAMPLED_FROM_D1,)

    # Partial-period detection vs the requested window (dates normalized from date|datetime).
    partial = _partial_warning(key_order[0], key_order[-1], interval, start, end)
    if partial is not None:
        warnings = warnings + (partial,)

    return replace(daily, interval=interval, bars=tuple(new_bars), warnings=warnings)


def _partial_warning(first_key, last_key, interval: Interval, start, end):
    """Return a single partial-period warning string if the leading and/or trailing
    emitted bar covers an incomplete calendar period relative to the requested window,
    else ``None``. ``start``/``end`` may be ``None`` (no bound -> no partiality on that edge).
    """
    leading = False
    trailing = False
    if start is not None:
        as_start = _as_date(start)
        if _period_calendar_start(first_key, interval) < as_start:
            leading = True
    if end is not None:
        as_end = _as_date(end)
        if _period_calendar_end(last_key, interval) > as_end:
            trailing = True

    if not leading and not trailing:
        return None

    if leading and trailing:
        edges = "leading and trailing"
    elif leading:
        edges = "leading"
    else:
        edges = "trailing"
    return (
        f"{PARTIAL_PERIOD_TOKEN}: the {edges} period(s) are incomplete relative to the "
        f"requested window; those bars are provisional (aggregate only the in-window days)."
    )
