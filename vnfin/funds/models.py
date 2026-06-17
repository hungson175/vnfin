"""Typed data contracts for vnfin fund data (VN open-ended mutual funds).

All monetary values are in VND per fund unit. ``NavPoint.date`` is a plain
``datetime.date`` (NAV is a daily/business-day quantity with no intraday meaning).
Every result container carries source attribution + ``fetched_at_utc``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

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
class NavHistory:
    """A NAV time series for one fund plus provenance/diagnostics metadata."""

    product_id: int
    points: tuple[NavPoint, ...]
    source: str
    currency: str = "VND"
    code: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self):
        return iter(self.points)

    def to_dataframe(self) -> "pd.DataFrame":
        """Return a pandas DataFrame indexed by date with a single ``nav`` column.

        Metadata (source, currency, product_id, code) is attached to ``df.attrs``.
        """
        import pandas as pd

        rows = [{"date": p.date, "nav": p.nav} for p in self.points]
        df = pd.DataFrame(rows, columns=["date", "nav"])
        if not df.empty:
            df = df.set_index("date")
        df.attrs.update(
            source=self.source,
            currency=self.currency,
            product_id=self.product_id,
            code=self.code,
        )
        return df


@dataclass(frozen=True)
class FundHolding:
    """A single disclosed portfolio holding.

    ``weight_pct`` is the holding's percent of net asset value (0-100).
    ``price`` is the provider's last-disclosed price for the underlying (units as
    reported by the provider, may be ``None``).
    """

    stock_code: str
    weight_pct: float
    industry: Optional[str] = None
    price: Optional[float] = None
