"""Typed data contracts for vnfin fund data (VN open-ended mutual funds).

All monetary values are in VND per fund unit. ``NavPoint.date`` is a plain
``datetime.date`` (NAV is a daily/business-day quantity with no intraday meaning).
Every result container carries source attribution + ``fetched_at_utc``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from ..timeseries import TimeSeriesResult

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


@dataclass(frozen=True)
class Fund:
    """A single VN open-ended mutual fund.

    ``id`` is the provider's internal product id (used as ``product_id`` for the
    NAV-history and holdings endpoints). ``nav`` is the latest NAV per unit in VND.
    ``asset_type`` is the provider asset-class code (e.g. ``STOCK``/``BOND``/
    ``BALANCED``).
    """

    code: str
    name: str
    id: int
    nav: float
    manager: str
    asset_type: str
    currency: str = "VND"


@dataclass(frozen=True)
class FundList:
    """A snapshot list of funds plus provenance metadata."""

    funds: tuple[Fund, ...]
    source: str
    currency: str = "VND"
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()

    def __len__(self) -> int:
        return len(self.funds)

    def __iter__(self):
        return iter(self.funds)

    def __getitem__(self, idx):
        return self.funds[idx]


@dataclass(frozen=True)
class NavPoint:
    """A single NAV observation: ``nav`` (VND per unit) on ``date``."""

    date: date
    nav: float


@dataclass(frozen=True)
class NavHistory(TimeSeriesResult):
    """A NAV time series for one fund plus provenance/diagnostics metadata.

    ``value_unit`` is ``"VND/unit"`` — NAV is a money amount *per fund unit*, so
    ``currency`` is ``"VND"`` and the explicit value unit records the per-unit basis.
    """

    product_id: int
    points: tuple[NavPoint, ...]
    source: str
    currency: str = "VND"
    value_unit: str = "VND/unit"
    code: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()

    _items_attr = "points"
    _index_column = "date"
    _df_columns = ("date", "nav")

    def _row_record(self, p: NavPoint) -> dict:
        return {"date": p.date, "nav": p.nav}

    def _df_attrs(self) -> dict:
        return dict(
            source=self.source,
            currency=self.currency,
            value_unit=self.value_unit,
            product_id=self.product_id,
            code=self.code,
        )


@dataclass(frozen=True)
class FundHolding:
    """A single disclosed portfolio holding.

    ``weight_pct`` is the holding's percent of net asset value (0-100) — the only
    safely-normalized numeric field on this model.

    ``price_raw`` is the provider's last-disclosed price for the underlying *exactly
    as reported*, with **no normalization applied**. Its meaning is documented by
    ``price_unit`` (e.g. ``"raw"`` — the literal provider scalar). We do NOT claim a
    canonical money unit (the provider's price scale is unverified and ambiguous),
    so callers must treat ``price_raw`` as opaque until a live-verified unit exists.
    Both may be ``None`` when the provider omits the price.
    """

    stock_code: str
    weight_pct: float
    industry: Optional[str] = None
    price_raw: Optional[float] = None
    price_unit: Optional[str] = None
