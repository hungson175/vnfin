"""Typed data contracts for vnfin price data."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


class Interval(str, Enum):
    """Supported bar intervals. Daily (``D1``) is the guaranteed common denominator;
    intraday intervals are best-effort and capability-gated per source."""

    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    D1 = "1d"
    W1 = "1w"
    MN1 = "1M"

    @property
    def is_intraday(self) -> bool:
        return self in _INTRADAY


_INTRADAY = frozenset({Interval.M1, Interval.M5, Interval.M15, Interval.M30, Interval.H1})


class AdjustmentPolicy(str, Enum):
    """How a returned price series is adjusted for splits/dividends."""

    PROVIDER_ADJUSTED = "provider_adjusted"
    RAW = "raw"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PriceBar:
    """A single OHLCV bar. Prices are in VND; ``time`` is timezone-aware (Asia/Ho_Chi_Minh)."""

    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class SourceAttempt:
    """One entry in failover diagnostics: which source was tried and the outcome."""

    name: str
    ok: bool
    reason: str


@dataclass(frozen=True)
class PriceHistory:
    """A normalized OHLCV series plus provenance/diagnostics metadata."""

    symbol: str
    interval: Interval
    adjustment_policy: AdjustmentPolicy
    source: str
    bars: tuple[PriceBar, ...]
    currency: str = "VND"
    exchange: Optional[str] = None
    provider_symbol: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()
    attempts: tuple[SourceAttempt, ...] = ()

    def __len__(self) -> int:
        return len(self.bars)

    def __iter__(self):
        return iter(self.bars)

    def to_dataframe(self) -> "pd.DataFrame":
        """Return a pandas DataFrame indexed by time. Metadata is attached to ``df.attrs``."""
        import pandas as pd

        rows = [
            {
                "time": b.time,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            }
            for b in self.bars
        ]
        df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
        if not df.empty:
            df = df.set_index("time")
        df.attrs.update(
            symbol=self.symbol,
            interval=self.interval.value,
            adjustment_policy=self.adjustment_policy.value,
            source=self.source,
            currency=self.currency,
            exchange=self.exchange,
        )
        return df
