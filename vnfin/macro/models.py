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

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


@dataclass(frozen=True)
class IndicatorSeries:
    """A single macroeconomic indicator time series for one country.

    ``points`` is an ascending (oldest-first) tuple of ``(date, value)`` pairs.
    ``date`` is a plain calendar date (annual observations are stamped Jan 1 of
    the reference year). ``currency`` states the money unit when relevant
    (USD for World Bank world-money series); for ratio/percent indicators it is
    advisory and the meaningful unit is in ``unit``.
    """

    country: str  # ISO3, e.g. "USA", "VNM"
    indicator_code: str  # e.g. "FP.CPI.TOTL.ZG"
    indicator_name: str  # human-readable, e.g. "Inflation, consumer prices (annual %)"
    points: tuple[tuple[date, float], ...]
    source: str
    unit: str = ""
    currency: str = "USD"
    country_name: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self):
        return iter(self.points)

    def latest(self) -> Optional[tuple[date, float]]:
        """Most recent ``(date, value)`` point, or ``None`` if the series is empty."""
        return self.points[-1] if self.points else None

    def to_dataframe(self) -> "pd.DataFrame":
        """Return a single-column (``value``) DataFrame indexed by date.

        Metadata (country, indicator, unit, currency, source) is attached to
        ``df.attrs`` so downstream code keeps provenance after a merge/concat.
        """
        import pandas as pd

        rows = [{"date": d, "value": v} for (d, v) in self.points]
        df = pd.DataFrame(rows, columns=["date", "value"])
        if not df.empty:
            df = df.set_index("date")
        df.attrs.update(
            country=self.country,
            country_name=self.country_name,
            indicator_code=self.indicator_code,
            indicator_name=self.indicator_name,
            unit=self.unit,
            currency=self.currency,
            source=self.source,
        )
        return df
