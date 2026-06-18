"""Crypto domain: USD-denominated OHLCV for major coins via keyless public exchange APIs.

Public API:
    - :class:`CryptoBar`, :class:`CryptoHistory` — typed data contracts (USD, tz-aware UTC).
    - :class:`BinanceCryptoSource` — Binance public ``/api/v3/klines`` adapter (primary).
    - :class:`CoinbaseCryptoSource` — Coinbase Exchange ``/products/.../candles`` adapter (backup).
    - :func:`default_crypto_sources`, :func:`default_crypto_client`,
      :class:`FailoverCryptoClient` — Binance -> Coinbase failover chain (unit guard: USD).

Example (single source)::

    from vnfin.crypto import BinanceCryptoSource
    from vnfin.models import Interval
    from datetime import date

    src = BinanceCryptoSource()
    hist = src.get_klines("BTCUSDT", Interval.D1, date(2024, 1, 1), date(2024, 3, 1))
    df = hist.to_dataframe()

Example (failover: Binance -> Coinbase)::

    from vnfin.crypto import default_crypto_client
    from vnfin.models import Interval

    client = default_crypto_client()
    hist = client.get_klines("BTCUSDT", Interval.D1)  # falls over to Coinbase if Binance fails
"""
from __future__ import annotations

from .binance import BinanceCryptoSource
from .client import (
    FailoverCryptoClient,
    default_crypto_client,
    default_crypto_sources,
)
from .coinbase import CoinbaseCryptoSource
from .models import CryptoBar, CryptoHistory

__all__ = [
    "BinanceCryptoSource",
    "CoinbaseCryptoSource",
    "CryptoBar",
    "CryptoHistory",
    "FailoverCryptoClient",
    "default_crypto_sources",
    "default_crypto_client",
    "client",
    "source",
]


def source(http_get=None, timeout: float = 25.0) -> BinanceCryptoSource:
    """Primary crypto entry: the default :class:`BinanceCryptoSource` (Binance, no-auth).

    Standard ``<domain>.source(...)`` factory. Use ``.get_klines(symbol, interval, ...)``
    on the returned object. Crypto OHLCV is USD-denominated.
    """
    return BinanceCryptoSource(http_get=http_get, timeout=timeout)


def client(http_get=None, timeout: float = 25.0) -> FailoverCryptoClient:
    """Standard ``<domain>.client(...)`` — the Binance->Coinbase failover chain (USD).

    Consistent with the other domains, ``client()`` returns the multi-source failover
    client; use :func:`source` for the bare primary (:class:`BinanceCryptoSource`).
    """
    return default_crypto_client(http_get=http_get, timeout=timeout)
