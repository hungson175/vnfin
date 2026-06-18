"""Typed data contracts for crypto OHLCV data.

Crypto prices are denominated in the pair's QUOTE asset, which the result states
explicitly (``currency``/``quote_asset``). For USD-stablecoin quote pairs
(USDT/USDC/BUSD/FDUSD/TUSD/USD) the currency is reported as ``"USD"`` (treated
~1:1); for non-USD quotes (e.g. ``ETHBTC`` -> quote BTC) the currency reflects
the actual quote asset, so callers never mistake a BTC-quoted price for USD.
Timestamps are timezone-aware UTC — crypto markets are 24/7 and have no
exchange-local trading day, so UTC is the natural, unambiguous reference.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from ..models import Interval
from ..timeseries import TimeSeriesResult

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


@dataclass(frozen=True)
class CryptoBar:
    """A single crypto OHLCV candle.

    ``time`` is the candle open time, timezone-aware UTC. Prices are in the pair's
    quote asset (see :class:`CryptoHistory.currency`/``quote_asset``). ``volume`` is
    base-asset volume and is kept as a float because crypto base volumes are
    fractional (e.g. 14302.058 BTC).
    """

    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class CryptoHistory(TimeSeriesResult):
    """A normalized crypto OHLCV series plus provenance metadata.

    Mirrors :class:`vnfin.models.PriceHistory` for the crypto domain. Every result
    carries source attribution and ``fetched_at_utc`` and states its units:

    - ``currency`` — the price unit (the pair's QUOTE asset). ``"USD"`` for
      USD-stablecoin quote pairs (USDT/USDC/...); otherwise the actual quote asset
      (e.g. ``"BTC"`` for ETHBTC).
    - ``value_unit`` — the explicit price unit string; for crypto it equals the quote
      asset / ``currency`` (prices ARE money in the quote asset).
    - ``base_asset`` / ``quote_asset`` — the parsed pair legs (prices are
      quote-per-base; ``volume`` is denominated in ``base_asset``).
    - ``price_unit`` / ``volume_unit`` — human-readable unit strings for callers.
    """

    symbol: str
    interval: Interval
    source: str
    bars: tuple[CryptoBar, ...]
    currency: str = "USD"
    value_unit: str = "USD"
    provider_symbol: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()
    base_asset: Optional[str] = None
    quote_asset: Optional[str] = None
    price_unit: Optional[str] = None
    volume_unit: Optional[str] = None

    _items_attr = "bars"
    _index_column = "time"
    _df_columns = ("time", "open", "high", "low", "close", "volume")

    def _row_record(self, b: CryptoBar) -> dict:
        return {
            "time": b.time,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
        }

    def _df_attrs(self) -> dict:
        return dict(
            symbol=self.symbol,
            interval=self.interval.value,
            source=self.source,
            currency=self.currency,
            value_unit=self.value_unit,
            provider_symbol=self.provider_symbol,
            base_asset=self.base_asset,
            quote_asset=self.quote_asset,
            price_unit=self.price_unit,
            volume_unit=self.volume_unit,
        )
