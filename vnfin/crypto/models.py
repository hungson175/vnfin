"""Typed data contracts for crypto OHLCV data.

Crypto bars are denominated in USD (Binance USDT spot pairs are treated as
USD ~1:1; the quote asset is stated explicitly on the result). Timestamps are
timezone-aware UTC — crypto markets are 24/7 and have no exchange-local trading
day, so UTC is the natural, unambiguous reference.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from ..models import Interval

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


@dataclass(frozen=True)
class CryptoBar:
    """A single crypto OHLCV candle.

    ``time`` is the candle open time, timezone-aware UTC. Prices are in the quote
    currency (USD for USDT pairs). ``volume`` is base-asset volume and is kept as a
    float because crypto base volumes are fractional (e.g. 14302.058 BTC).
    """

    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class CryptoHistory:
    """A normalized crypto OHLCV series plus provenance metadata.

    Mirrors :class:`vnfin.models.PriceHistory` for the crypto domain. Every result
    carries source attribution and ``fetched_at_utc`` and states its ``currency``.
    """

    symbol: str
    interval: Interval
    source: str
    bars: tuple[CryptoBar, ...]
    currency: str = "USD"
    provider_symbol: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()

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
            source=self.source,
            currency=self.currency,
            provider_symbol=self.provider_symbol,
        )
        return df
