"""Crypto domain: USD-denominated OHLCV for major coins via keyless public exchange APIs.

Public API:
    - :class:`CryptoBar`, :class:`CryptoHistory` — typed data contracts (USD, tz-aware UTC).
    - :class:`BinanceCryptoSource` — Binance public ``/api/v3/klines`` adapter.

Example::

    from vnfin.crypto import BinanceCryptoSource
    from vnfin.models import Interval
    from datetime import date

    src = BinanceCryptoSource()
    hist = src.get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 3, 1))
    df = hist.to_dataframe()
"""
from __future__ import annotations

from .binance import BinanceCryptoSource
from .models import CryptoBar, CryptoHistory

__all__ = ["BinanceCryptoSource", "CryptoBar", "CryptoHistory"]
