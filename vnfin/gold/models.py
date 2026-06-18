"""Typed data contracts for the gold domain.

Two shapes:

* :class:`GoldQuote` — a single spot buy/sell snapshot (VN domestic dealers quote a
  two-sided buy/sell spread; world spot is a single tick where ``buy == sell``).
* :class:`GoldBar` + :class:`GoldHistory` — a daily EOD price series (one value per
  trading day), used by the world XAU/USD history source.

Currency and unit are stated explicitly on every object so downstream callers never
have to guess: VN money is VND (``unit="VND/chi"``, per *chỉ*), world gold is USD
(``unit="USD/oz"``, per troy ounce). ``time`` is timezone-aware where the source
carries an intraday timestamp; ``GoldBar.date`` is a plain date (EOD has no meaningful
intraday time).
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
class GoldQuote:
    """A single spot gold quote.

    ``buy`` is the price the dealer *buys from you*, ``sell`` is the price the dealer
    *sells to you* (so ``sell >= buy`` for a dealer spread). For a single-tick world
    spot source there is no spread and ``buy == sell == price``.
    """

    time: datetime
    product: str
    buy: float
    sell: float
    unit: str
    currency: str
    source: str
    fetched_at_utc: Optional[datetime] = None
    karat: Optional[str] = None
    region: Optional[str] = None

    @property
    def spread(self) -> float:
        """Dealer spread (``sell - buy``); ``0.0`` for a single-tick spot source."""
        return self.sell - self.buy

    @property
    def mid(self) -> float:
        """Midpoint of the buy/sell spread."""
        return (self.buy + self.sell) / 2.0


@dataclass(frozen=True)
class GoldBar:
    """One EOD point in a gold price series. ``date`` is a plain calendar date."""

    date: date_type
    price: float


@dataclass(frozen=True)
class GoldHistory(TimeSeriesResult):
    """A normalized daily gold price series plus provenance metadata.

    ``unit`` is the historical/primary unit field (e.g. ``"USD/oz"``). ``value_unit``
    is the explicit cross-domain alias kept consistent with ``unit`` so callers can
    read the value unit uniformly across every time-series result; it defaults to
    ``unit`` when a source does not set it explicitly.
    """

    product: str
    unit: str
    currency: str
    source: str
    bars: tuple[GoldBar, ...]
    value_unit: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()
    #: Per-source failover diagnostics, attached by the failover client's
    #: ``finalize`` step. Empty for a series fetched directly from one source.
    attempts: tuple[SourceAttempt, ...] = ()

    _items_attr = "bars"
    _index_column = "date"
    _df_columns = ("date", "price")

    def __post_init__(self):
        # value_unit mirrors the primary `unit` when a source omits it, so the
        # explicit cross-domain value-unit field is always populated. Frozen
        # dataclass: assign via object.__setattr__.
        if self.value_unit is None:
            object.__setattr__(self, "value_unit", self.unit)

    def _row_record(self, b: GoldBar) -> dict:
        return {"date": b.date, "price": b.price}

    def _df_attrs(self) -> dict:
        return dict(
            product=self.product,
            unit=self.unit,
            value_unit=self.value_unit,
            currency=self.currency,
            source=self.source,
        )
