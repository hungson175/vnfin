"""Crypto failover client (Binance primary -> Coinbase backup).

A thin **specialization** of the domain-agnostic :class:`vnfin.failover.FailoverClient`,
mirroring :class:`vnfin.client.FailoverPriceClient`. It wires the crypto-domain
operation (``source.get_klines``), capability (``source.supports(interval)``),
acceptance (non-empty series), and unit guard (``source.unit``) into the generic engine.

All configured sources must emit USD (the unit-homogeneity guard enforces this), so a
Binance USD-stablecoin-quoted series can fail over to a Coinbase native-USD series
without ever silently mixing currencies/scales.

Two layers of unit safety:

* **Construction guard (source-level):** the generic engine's unit-homogeneity guard
  rejects a chain whose sources declare different ``unit`` values.
* **Result guard (request-level):** the accept path also checks each returned series'
  actual ``currency``/``value_unit`` against the chain's declared unit. Both adapters
  can serve a non-USD pair (e.g. ``ETHBTC`` -> ``currency="BTC"``); such a result is
  rejected in a USD chain so the client never silently serves a BTC series as USD.

Failover order: Binance (deepest daily history back to 2017, all intervals, 1000
rows/call) -> Coinbase (native fiat USD, ~300 candles/call, no weekly/monthly). When
the requested interval is unavailable on a source (e.g. Coinbase has no weekly bar),
that source is skipped by the capability guard without a network call.
"""
from __future__ import annotations

import math
from datetime import date, datetime

from .binance import BinanceCryptoSource, _KNOWN_QUOTES as _BINANCE_QUOTES
from .coinbase import CoinbaseCryptoSource, _KNOWN_QUOTES as _COINBASE_QUOTES
from .models import CryptoBar, CryptoHistory

from ..exceptions import AllSourcesFailed, InvalidData, UnsupportedInterval
from ..failover import FailoverClient
from ..models import Interval
from ..validation import validate_date_range, validate_non_empty_string

# Default crypto failover chain (deepest/widest first).
_DEFAULT_CRYPTO_SOURCE_CLASSES = (BinanceCryptoSource, CoinbaseCryptoSource)


def default_crypto_sources(http_get=None, timeout: float = 25.0):
    """Instantiate the default crypto failover chain (all USD): Binance primary, Coinbase backup."""
    return [c(http_get=http_get, timeout=timeout) for c in _DEFAULT_CRYPTO_SOURCE_CLASSES]


def _crypto_unit(source):
    """Declared crypto unit/currency of a source (``"USD"`` for the default chain)."""
    return getattr(source, "unit", None)


# Quotes recognized by the crypto adapters, longest-first, so stripping a known
# quote suffix yields the base asset for identity checks.
_KNOWN_QUOTES = tuple(
    sorted(frozenset(_BINANCE_QUOTES) | frozenset(_COINBASE_QUOTES), key=len, reverse=True)
)


def _normalize_crypto_symbol(symbol: str) -> str:
    """Issue #9: reject empty/malformed symbols before the failover engine runs."""
    return validate_non_empty_string(symbol, "crypto symbol")


def _base_asset(symbol: str) -> str | None:
    """Extract the base asset from a crypto pair, normalizing case and format.

    Accepts both hyphenated products (``BTC-USD``) and concatenated pairs
    (``BTCUSDT``). Unknown or malformed inputs return ``None``.
    """
    if not isinstance(symbol, str):
        return None
    sym = symbol.strip().upper()
    if not sym:
        return None
    if "-" in sym:
        return sym.split("-", 1)[0]
    for quote in _KNOWN_QUOTES:
        if sym.endswith(quote) and len(sym) > len(quote):
            return sym[: -len(quote)]
    return sym


class FailoverCryptoClient:
    """Try crypto sources in priority order, up to ``max_attempts`` actual calls.

    A result is returned only if it has at least one bar; otherwise the failure reason
    is recorded and the client falls through to the next source. Sources that do not
    support the requested interval are skipped without a network call and do not count
    against ``max_attempts``. All configured sources must emit the same unit/currency
    (see :class:`vnfin.failover.FailoverClient` unit guard).
    """

    def __init__(self, sources, max_attempts: int = 3):
        sources = list(sources)
        # The unit this chain promises callers (e.g. "USD" for the default chain),
        # taken from the sources' declared ``unit`` (already homogeneity-checked by the
        # generic engine). A result whose actual currency/value_unit differs from this
        # declared unit (e.g. a BTC-quoted ETHBTC series in a USD chain) is REJECTED in
        # the accept path so the client never silently serves a non-USD series as USD.
        self._chain_unit = next(
            (u for u in (_crypto_unit(s) for s in sources) if u is not None), None
        )
        self._engine = FailoverClient(
            sources,
            operation=lambda src, symbol, interval, start, end: src.get_klines(
                symbol, interval, start, end
            ),
            capability=lambda src, symbol, interval, start, end: src.supports(interval),
            reject=self._reject_reason,
            unit_of=_crypto_unit,
            provenance_of=lambda hist: getattr(hist, "source", None),  # #126
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
        # Issue #9/#77: validate caller inputs before the failover engine runs.
        symbol = _normalize_crypto_symbol(symbol)
        if not isinstance(interval, Interval):
            raise InvalidData(
                f"interval must be a vnfin.models.Interval, got {type(interval).__name__}"
            )
        if start is not None or end is not None:
            validate_date_range(start, end, name="crypto klines", allow_none=True)
        return self._engine.run(symbol, interval, start, end)

    def _reject_reason(self, hist, symbol, interval, start, end) -> str | None:
        return _validate_crypto_result(
            hist,
            symbol=symbol,
            interval=interval,
            chain_unit=self._chain_unit,
            start=start,
            end=end,
        )


def _validate_crypto_result(
    hist,
    *,
    symbol: str,
    interval: Interval,
    chain_unit: str | None,
    start,
    end,
) -> str | None:
    """Return a rejection reason or ``None`` if the crypto result is acceptable."""
    # Issue #125: a malformed (non-typed) result container must be recorded as a
    # rejected source attempt, not leak a raw AttributeError from len(hist.bars).
    if not isinstance(hist, CryptoHistory):
        return f"unexpected result type {type(hist).__name__}"
    if len(hist.bars) == 0:
        return "empty result"

    # Identity checks (#82). Crypto sources may return their provider-specific
    # product symbol (e.g. "BTC-USD" for a "BTCUSDT" request), so a strict string
    # match would break legitimate failover. Instead we compare the parsed base
    # asset, which rejects wrong-asset results (e.g. ETHUSDT for a BTCUSDT request)
    # while still accepting the same base across product formats.
    if not isinstance(hist.symbol, str) or not hist.symbol.strip():
        return f"malformed returned symbol {hist.symbol!r}"
    req_base = _base_asset(symbol)
    result_base = _base_asset(hist.base_asset) if hist.base_asset else _base_asset(hist.symbol)
    if req_base is None or result_base != req_base:
        return (
            f"symbol mismatch: returned {hist.symbol!r} "
            f"(base {result_base!r}) != requested {symbol!r} (base {req_base!r})"
        )
    if hist.interval != interval:
        return f"interval mismatch: returned {hist.interval!r} != requested {interval!r}"

    # Unit/currency/value_unit consistency (#69).
    if chain_unit is not None:
        for field in ("currency", "value_unit"):
            actual = getattr(hist, field, None)
            if not isinstance(actual, str):
                return f"malformed unit: result {field} has type {type(actual).__name__}"
            if not actual:
                return f"missing unit: result {field} is missing or empty"
            if actual != chain_unit:
                return f"unit mismatch: result {field} {actual!r} != chain unit {chain_unit!r}"

    # Issue #124: each bar key must be a timezone-AWARE datetime (the documented
    # CryptoBar.time contract — candle open time, tz-aware UTC). A naive datetime
    # or non-datetime key is rejected before the ascending-order compare and the
    # window .date() call, so a malformed key is a recorded rejected attempt.
    for bar in hist.bars:
        t = bar.time
        if not isinstance(t, datetime) or t.utcoffset() is None:
            return f"malformed bar time {t!r}: expected a timezone-aware datetime"

    # Sorting (#85).
    for i in range(len(hist.bars) - 1):
        if not (hist.bars[i].time < hist.bars[i + 1].time):
            return "bars are not strictly ascending by time"

    # Row-level financial invariants (#86).
    for bar in hist.bars:
        reason = _validate_crypto_bar(bar)
        if reason:
            return reason

    # Window coverage (preserved).
    def _as_date(val):
        if val is None:
            return None
        if hasattr(val, "date"):
            return val.date()
        return val if isinstance(val, date) else None

    sd, ed = _as_date(start), _as_date(end)
    if sd is not None or ed is not None:
        in_window = False
        for bar in hist.bars:
            d = bar.time.date()
            if sd is not None and d < sd:
                continue
            if ed is not None and d > ed:
                continue
            in_window = True
            break
        if not in_window:
            return "no bars in requested date range"
    return None


def _validate_crypto_bar(bar: CryptoBar) -> str | None:
    """Return a rejection reason if ``bar`` violates OHLC invariants (#86)."""
    for field in ("open", "high", "low", "close", "volume"):
        value = getattr(bar, field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"bar {bar.time}: {field} has malformed type {type(value).__name__}"
        if not math.isfinite(value):
            return f"bar {bar.time}: {field} must be finite, got {value!r}"
    for field in ("open", "high", "low", "close"):
        value = getattr(bar, field)
        if value <= 0:
            return f"bar {bar.time}: {field} must be positive, got {value!r}"
    if bar.volume < 0:
        return f"bar {bar.time}: volume must be non-negative, got {bar.volume!r}"
    if not (bar.low <= bar.open <= bar.high):
        return (
            f"bar {bar.time}: open {bar.open} not in [low {bar.low}, high {bar.high}]"
        )
    if not (bar.low <= bar.close <= bar.high):
        return (
            f"bar {bar.time}: close {bar.close} not in [low {bar.low}, high {bar.high}]"
        )
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
