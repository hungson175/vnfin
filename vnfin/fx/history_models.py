"""Historical FX domain typed results (issue #159).

A historical FX series is a **time series** (unlike the point-in-time :class:`FXRate`),
so it adopts the shared :class:`~vnfin.timeseries.TimeSeriesResult` mixin (same as
``IndicatorSeries`` / ``PriceHistory``) and gains ``__len__`` / ``__iter__`` /
``to_dataframe`` with provenance in ``df.attrs`` for free.

Canonical unit is **quote per 1 base** (e.g. VND per 1 USD), matching the spot
:class:`FXRate.rate` convention. v1 serves **annual** USD/VND from World Bank WDI
``PA.NUS.FCRF`` (period-average) — see ``docs/design/fx-history.md``.

Conversion is intentionally **exact-lookup only**: :meth:`FXHistory.rate_on` (and its
year-sugar :meth:`FXHistory.rate_for_year`) return an exact observation or raise — they
never forward-fill, interpolate, or pick a "nearest" date. Asset-join / normalization
helpers are deliberately out of scope (a separate, later design).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from ..exceptions import InvalidData
from ..timeseries import TimeSeriesResult
from ..macro.indicators import Frequency


@dataclass(frozen=True)
class FXPoint:
    """One historical FX observation: ``rate`` = quote per 1 base, keyed by ``date``.

    Annual observations are stamped on Jan 1 of the reference year (the WB
    ``PA.NUS.FCRF`` series is an annual period-average).
    """

    date: date
    rate: float  # quote per 1 base (e.g. VND per 1 USD), > 0, finite


@dataclass(frozen=True)
class FXHistory(TimeSeriesResult):
    """A historical FX time series for one ``base``/``quote`` pair.

    ``points`` is an ascending (oldest-first) tuple of :class:`FXPoint`. ``unit`` is the
    canonical convention string (``"VND per 1 USD"``); ``value_unit`` mirrors it for
    cross-domain uniformity. ``frequency`` is explicit so a caller can see that the
    series is annual (and never silently align it to a daily asset series).
    """

    base: str  # ISO 4217 base currency, e.g. "USD"
    quote: str  # quote currency, "VND" in v1
    points: tuple[FXPoint, ...]
    unit: str  # canonical unit string, e.g. "VND per 1 USD"
    frequency: Frequency
    source: str  # adapter name, e.g. "worldbank_fx"
    value_unit: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    _items_attr = "points"
    _index_column = "date"
    _df_columns = ("date", "rate")

    def __post_init__(self):
        # value_unit mirrors `unit` for cross-domain uniformity when not set. Frozen -> setattr.
        if self.value_unit is None:
            object.__setattr__(self, "value_unit", self.unit)

    def rate_on(self, d: date) -> float:
        """Exact rate for observation date ``d``; :class:`InvalidData` if absent.

        NEVER forward-fills, interpolates, or picks a nearest date. For the annual v1
        series the caller must pass the stamped key (Jan 1 of the year) — use
        :meth:`rate_for_year` for year-keyed sugar.

        This is a public, user-facing accessor, so it fails closed: ``d`` must be a
        plain :class:`datetime.date`. A :class:`datetime.datetime` (a ``date`` subclass),
        ``bool``, ``str``, ``None``, etc. raises :class:`InvalidData` rather than leaking
        a raw ``AttributeError``/``TypeError``.
        """
        # `datetime` is a subclass of `date`; require the exact type so a datetime's
        # time component cannot silently never-match an annual Jan-1 key.
        if type(d) is not date:
            raise InvalidData(
                f"{self.source}: rate_on requires a plain datetime.date, "
                f"got {type(d).__name__}"
            )
        for p in self.points:
            if p.date == d:
                return p.rate
        raise InvalidData(
            f"{self.source}: no {self.base}/{self.quote} observation on {d.isoformat()} "
            f"(exact-match only; this series does not fill or interpolate)"
        )

    def rate_for_year(self, year: int) -> float:
        """Exact rate for ``year`` (sugar over ``rate_on(date(year, 1, 1))``).

        Public accessor: ``year`` must be a non-bool ``int`` in ``1..9999``; a ``str``,
        ``float``, ``bool``, or out-of-range value raises :class:`InvalidData` (a ``bool``
        is never coerced to year 0/1).
        """
        if isinstance(year, bool) or not isinstance(year, int):
            raise InvalidData(
                f"{self.source}: rate_for_year requires an int year, got {year!r}"
            )
        if not 1 <= year <= 9999:
            raise InvalidData(
                f"{self.source}: rate_for_year year {year} is out of range 1..9999"
            )
        return self.rate_on(date(year, 1, 1))

    def latest(self) -> Optional[FXPoint]:
        """Most recent observation, or ``None`` if the series is empty."""
        return self.points[-1] if self.points else None

    def _row_record(self, item: FXPoint) -> dict:
        return {"date": item.date, "rate": item.rate}

    def _df_attrs(self) -> dict:
        return dict(
            base=self.base,
            quote=self.quote,
            unit=self.unit,
            value_unit=self.value_unit,
            frequency=self.frequency.value,
            source=self.source,
        )
