"""Typed data contracts for index constituents.

Index VALUE history reuses the existing ``vnfin.models.PriceHistory`` (with
``currency="points"``). Constituents need their own typed models, defined here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


@dataclass(frozen=True)
class IndexMember:
    """One constituent of an index.

    ``weight`` is ``None`` whenever the source does not publish per-stock index
    weights (the SSI iboard-query group endpoint exposes membership only). It is
    never fabricated.
    """

    symbol: str
    exchange: Optional[str] = None
    company_name: Optional[str] = None
    isin: Optional[str] = None
    weight: Optional[float] = None


@dataclass(frozen=True)
class IndexConstituents:
    """The current membership basket of an index, plus provenance metadata.

    ``has_weights`` reports whether any member carries a non-null weight. The SSI
    membership endpoint does not expose weights, so this is ``False`` there; the
    official weighted basket lives only in HOSE periodic PDF/Excel (see the
    research doc) and is intentionally not fabricated.
    """

    index: str
    source: str
    members: tuple[IndexMember, ...]
    provider_group: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    as_of: Optional[datetime] = None
    warnings: tuple[str, ...] = ()

    def __len__(self) -> int:
        return len(self.members)

    def __iter__(self):
        return iter(self.members)

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(m.symbol for m in self.members)

    @property
    def has_weights(self) -> bool:
        return any(m.weight is not None for m in self.members)

    def to_dataframe(self) -> "pd.DataFrame":
        """Return a pandas DataFrame of members. Metadata is attached to ``df.attrs``."""
        import pandas as pd

        rows = [
            {
                "symbol": m.symbol,
                "exchange": m.exchange,
                "company_name": m.company_name,
                "isin": m.isin,
                "weight": m.weight,
            }
            for m in self.members
        ]
        df = pd.DataFrame(
            rows, columns=["symbol", "exchange", "company_name", "isin", "weight"]
        )
        df.attrs.update(
            index=self.index,
            source=self.source,
            provider_group=self.provider_group,
            has_weights=self.has_weights,
        )
        return df
