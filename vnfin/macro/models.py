"""Typed data contracts for vnfin macro (cross-country indicator) data.

Mirrors the conventions in ``vnfin.models``: frozen dataclasses, explicit
``source`` attribution + ``fetched_at_utc`` provenance, explicit ``currency``,
and a ``to_dataframe()`` helper that stamps metadata onto ``df.attrs``.

Macro indicators are annual time series, so each point is keyed by a plain
``date`` (no intraday meaning) rather than a tz-aware datetime.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from ..timeseries import TimeSeriesResult

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


@dataclass(frozen=True)
class IndicatorSeries(TimeSeriesResult):
    """A single macroeconomic indicator time series for one country.

    ``points`` is an ascending (oldest-first) tuple of ``(date, value)`` pairs.
    ``date`` is a plain calendar date (annual observations are stamped Jan 1 of
    the reference year). ``currency`` states the money unit when relevant
    (USD for World Bank world-money series); for ratio/percent indicators it is
    advisory and the meaningful unit is in ``unit``. ``value_unit`` is the explicit
    cross-domain alias for ``unit`` (the per-indicator unit is authoritative for
    macro), populated from ``unit`` when a source omits it.
    """

    country: str  # ISO3, e.g. "USA", "VNM"
    indicator_code: str  # e.g. "FP.CPI.TOTL.ZG"
    indicator_name: str  # human-readable, e.g. "Inflation, consumer prices (annual %)"
    points: tuple[tuple[date, float], ...]
    source: str
    unit: str = ""
    value_unit: Optional[str] = None
    currency: str = "USD"
    country_name: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    _items_attr = "points"
    _index_column = "date"
    _df_columns = ("date", "value")

    def __post_init__(self):
        # Macro keeps its per-indicator `unit` as authoritative; value_unit mirrors it
        # for cross-domain uniformity when a source doesn't set it. Frozen -> setattr.
        if self.value_unit is None:
            object.__setattr__(self, "value_unit", self.unit)

    def latest(self) -> Optional[tuple[date, float]]:
        """Most recent ``(date, value)`` point, or ``None`` if the series is empty."""
        return self.points[-1] if self.points else None

    def _row_record(self, point) -> dict:
        d, v = point
        return {"date": d, "value": v}

    def _df_attrs(self) -> dict:
        return dict(
            country=self.country,
            country_name=self.country_name,
            indicator_code=self.indicator_code,
            indicator_name=self.indicator_name,
            unit=self.unit,
            value_unit=self.value_unit,
            currency=self.currency,
            source=self.source,
        )
