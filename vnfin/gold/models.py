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
class GoldHistory:
    """A normalized daily gold price series plus provenance metadata."""

    product: str
    unit: str
    currency: str
    source: str
    bars: tuple[GoldBar, ...]
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()

    def __len__(self) -> int:
        return len(self.bars)

    def __iter__(self):
        return iter(self.bars)

    def to_dataframe(self) -> "pd.DataFrame":
        """Return a pandas DataFrame indexed by date. Metadata is on ``df.attrs``."""
        import pandas as pd

        rows = [{"date": b.date, "price": b.price} for b in self.bars]
        df = pd.DataFrame(rows, columns=["date", "price"])
        if not df.empty:
            df = df.set_index("date")
        df.attrs.update(
            product=self.product,
            unit=self.unit,
            currency=self.currency,
            source=self.source,
        )
        return df
