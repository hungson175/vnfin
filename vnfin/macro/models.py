"""Typed data contracts for vnfin macro (cross-country indicator) data.

Mirrors the conventions in ``vnfin.models``: frozen dataclasses, explicit
``source`` attribution + ``fetched_at_utc`` provenance, an indicator-specific
``currency`` (``None`` for percent/index series), and a ``to_dataframe()`` helper
that stamps metadata onto ``df.attrs``.

Macro indicators are time series. Frequency is explicit (annual / quarterly /
monthly / daily) rather than assumed-annual, because the no-key providers differ
(World Bank/IMF WEO are annual, DBnomics IFS CPI is monthly, FRED varies). Each
point is keyed by a plain ``date`` (no intraday meaning).

Actual vs projection (B8): some providers (IMF WEO) mix historical actuals with
future projections in one series. ``projection_from_year`` records the first year
that is a projection; ``latest()`` returns the most recent **actual** so callers
never mistake a forecast for a realized value, and ``latest_including_projections()``
is available when the forecast is explicitly wanted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from ..timeseries import TimeSeriesResult
from .indicators import Frequency

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


@dataclass(frozen=True)
class IndicatorSeries(TimeSeriesResult):
    """A single macroeconomic indicator time series for one country.

    ``points`` is an ascending (oldest-first) tuple of ``(date, value)`` pairs.
    ``date`` is a plain calendar date (annual observations are stamped Jan 1 of
    the reference year; monthly are the month-start day).

    ``unit`` is the authoritative per-indicator unit (``"%"``, ``"current US$"``,
    ``"index"``, ...). ``value_unit`` is the explicit cross-domain alias for
    ``unit`` (populated from ``unit`` when a source omits it). ``currency`` is set
    **only** when the indicator is money-denominated (e.g. GDP); for percent/index
    indicators it is ``None`` so a non-money series is never stamped with a
    misleading currency.

    ``frequency`` states the observation cadence. ``projection_from_year``, when
    set, is the first calendar year whose observations are forecasts/projections
    rather than realized actuals (IMF WEO). ``latest()`` excludes those.
    """

    country: str  # ISO3, e.g. "USA", "VNM"
    indicator_code: str  # e.g. "FP.CPI.TOTL.ZG"
    indicator_name: str  # human-readable, e.g. "Inflation, consumer prices (annual %)"
    points: tuple[tuple[date, float], ...]
    source: str
    unit: str = ""
    value_unit: Optional[str] = None
    currency: Optional[str] = None
    frequency: Frequency = Frequency.ANNUAL
    projection_from_year: Optional[int] = None
    country_name: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    _items_attr = "points"
    _index_column = "date"
    _df_columns = ("date", "value", "is_projection")

    def __post_init__(self):
        # Macro keeps its per-indicator `unit` as authoritative; value_unit mirrors it
        # for cross-domain uniformity when a source doesn't set it. Frozen -> setattr.
        if self.value_unit is None:
            object.__setattr__(self, "value_unit", self.unit)

    def _is_projection_year(self, d: date) -> bool:
        return self.projection_from_year is not None and d.year >= self.projection_from_year

    def is_projection(self, point) -> bool:
        """Whether a ``(date, value)`` point is a forecast/projection (not an actual)."""
        d, _v = point
        return self._is_projection_year(d)

    @property
    def actual_points(self) -> tuple[tuple[date, float], ...]:
        """Only the realized (non-projection) observations, oldest-first."""
        if self.projection_from_year is None:
            return self.points
        return tuple(p for p in self.points if not self._is_projection_year(p[0]))

    def latest(self) -> Optional[tuple[date, float]]:
        """Most recent realized (non-projection) ``(date, value)``, or ``None``.

        Projections (IMF WEO future years) are intentionally excluded so a
        forecast is never returned as an actual. Use
        :meth:`latest_including_projections` to include them explicitly.
        """
        actuals = self.actual_points
        return actuals[-1] if actuals else None

    def latest_including_projections(self) -> Optional[tuple[date, float]]:
        """Most recent point including forecasts/projections, or ``None`` if empty."""
        return self.points[-1] if self.points else None

    def _row_record(self, point) -> dict:
        d, v = point
        return {"date": d, "value": v, "is_projection": self._is_projection_year(d)}

    def _df_attrs(self) -> dict:
        return dict(
            country=self.country,
            country_name=self.country_name,
            indicator_code=self.indicator_code,
            indicator_name=self.indicator_name,
            unit=self.unit,
            value_unit=self.value_unit,
            currency=self.currency,
            frequency=self.frequency.value,
            projection_from_year=self.projection_from_year,
            source=self.source,
        )
