"""Crypto failover client (Binance primary -> Coinbase backup).

A thin **specialization** of the domain-agnostic :class:`vnfin.failover.FailoverClient`,
mirroring :class:`vnfin.client.FailoverPriceClient`. It wires the crypto-domain
operation (``source.get_klines``), capability (``source.supports(interval)``),
acceptance (non-empty series), and unit guard (``source.unit``) into the generic engine.

All configured sources must emit USD (the unit-homogeneity guard enforces this), so a
Binance USD-stablecoin-quoted series can fail over to a Coinbase native-USD series
without ever silently mixing currencies/scales.

Failover order: Binance (deepest daily history back to 2017, all intervals, 1000
rows/call) -> Coinbase (native fiat USD, ~300 candles/call, no weekly/monthly). When
the requested interval is unavailable on a source (e.g. Coinbase has no weekly bar),
that source is skipped by the capability guard without a network call.
"""
from __future__ import annotations

from .binance import BinanceCryptoSource
from .coinbase import CoinbaseCryptoSource
from .models import CryptoHistory

from ..exceptions import AllSourcesFailed, UnsupportedInterval
from ..failover import FailoverClient
from ..models import Interval

# Default crypto failover chain (deepest/widest first).
_DEFAULT_CRYPTO_SOURCE_CLASSES = (BinanceCryptoSource, CoinbaseCryptoSource)


def default_crypto_sources(http_get=None, timeout: float = 25.0):
    """Instantiate the default crypto failover chain (all USD): Binance primary, Coinbase backup."""
    return [c(http_get=http_get, timeout=timeout) for c in _DEFAULT_CRYPTO_SOURCE_CLASSES]


def _crypto_unit(source):
    """Declared crypto unit/currency of a source (``"USD"`` for the default chain)."""
    return getattr(source, "unit", None)


class FailoverCryptoClient:
    """Try crypto sources in priority order, up to ``max_attempts`` actual calls.

    A result is returned only if it has at least one bar; otherwise the failure reason
    is recorded and the client falls through to the next source. Sources that do not
    support the requested interval are skipped without a network call and do not count
    against ``max_attempts``. All configured sources must emit the same unit/currency
    (see :class:`vnfin.failover.FailoverClient` unit guard).
    """

    def __init__(self, sources, max_attempts: int = 3):
        self._engine = FailoverClient(
            sources,
            operation=lambda src, symbol, interval, start, end: src.get_klines(
                symbol, interval, start, end
            ),
            capability=lambda src, symbol, interval, start, end: src.supports(interval),
            reject=self._reject_reason,
            unit_of=_crypto_unit,
            max_attempts=max_attempts,
            failure_factory=lambda attempts, symbol, interval, start, end: AllSourcesFailed(
                symbol, interval, attempts
            ),
            no_capable_factory=lambda symbol, interval, start, end: UnsupportedInterval(
                f"no configured crypto source supports interval "
                f"{getattr(interval, 'value', interval)}"
            ),
        )

    @property
    def sources(self):
        return self._engine.sources

    @property
    def max_attempts(self) -> int:
        return self._engine.max_attempts

    @property
    def unit(self):
        return self._engine.unit

    def get_klines(
        self, symbol, interval: Interval = Interval.D1, start=None, end=None
    ) -> CryptoHistory:
        return self._engine.run(symbol, interval, start, end)

    @staticmethod
    def _reject_reason(hist) -> str | None:
        if hist is None or len(hist.bars) == 0:
            return "empty result"
        return None


def default_crypto_client(
    sources=None,
    *,
    http_get=None,
    timeout: float = 25.0,
    max_attempts: int = 3,
) -> FailoverCryptoClient:
    """Construct the default crypto failover client (Binance -> Coinbase, USD).

    Pass ``sources`` to override the chain (e.g. in tests); otherwise the default
    Binance-primary/Coinbase-backup chain is built. All sources must emit USD.
    """
    if sources is None:
        sources = default_crypto_sources(http_get=http_get, timeout=timeout)
    return FailoverCryptoClient(sources, max_attempts=max_attempts)
