"""Typed data contracts for the precious-metals domain (#196).

Two shapes mirroring the gold domain's :class:`~vnfin.gold.models.GoldBar` /
:class:`~vnfin.gold.models.GoldHistory`, so callers get identical ``.to_dataframe()``
ergonomics and an honest, distinctly-named public type:

* :class:`MetalBar` — one annual price point (Jan-1-stamped, USD per troy ounce).
* :class:`MetalHistory` — a frozen annual price series plus provenance metadata.

Unlike ``GoldHistory``, ``MetalHistory`` carries the **never-silent** ``frequency``
(``"annual"``) and CC-BY ``attribution`` as TYPED fields (always present, machine-readable
— stronger than a warning string), so the metals result states its annual cadence and its
World Bank attribution natively. No new ``.warnings`` token is introduced.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_type
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from ..models import SourceAttempt
from ..timeseries import TimeSeriesResult

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


@dataclass(frozen=True)
class MetalBar:
    """One annual point in a precious-metal price series.

    ``date`` is the Jan-1 reference date of the calendar year; ``price`` is USD per troy
    ounce (the World Bank CMO annual nominal-USD value).
    """

    date: date_type
    price: float


@dataclass(frozen=True)
class MetalHistory(TimeSeriesResult):
    """A normalized annual precious-metal price series plus provenance metadata.

    ``unit`` is the primary unit field (``"USD/oz"``). ``value_unit`` is the explicit
    cross-domain alias kept consistent with ``unit`` (defaults to ``unit`` when a source
    does not set it). ``frequency`` (``"annual"``) and ``attribution`` (the CC-BY string)
    are typed never-silent fields — always present on every served result.
    """

    product: str
    unit: str
    currency: str
    source: str
    bars: tuple[MetalBar, ...]
    frequency: str = "annual"
    attribution: str = "Source: The World Bank — Commodity Markets (Pink Sheet)"
    value_unit: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()
    #: Per-source failover diagnostics (parity with GoldHistory). Empty for a series
    #: fetched directly from one source.
    attempts: tuple[SourceAttempt, ...] = ()

    _items_attr = "bars"
    _index_column = "date"
    _df_columns = ("date", "price")

    def __post_init__(self):
        # value_unit mirrors the primary `unit` when a source omits it, so the explicit
        # cross-domain value-unit field is always populated (same as GoldHistory). Frozen
        # dataclass: assign via object.__setattr__.
        if self.value_unit is None:
            object.__setattr__(self, "value_unit", self.unit)

    def _row_record(self, b: MetalBar) -> dict:
        return {"date": b.date, "price": b.price}

    def _df_attrs(self) -> dict:
        return dict(
            product=self.product,
            unit=self.unit,
            value_unit=self.value_unit,
            currency=self.currency,
            source=self.source,
            frequency=self.frequency,
            attribution=self.attribution,
        )
