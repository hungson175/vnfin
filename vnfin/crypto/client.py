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

import dataclasses
import math
from datetime import date, datetime

from .binance import BinanceCryptoSource, _KNOWN_QUOTES as _BINANCE_QUOTES, _USD_STABLE_QUOTES
from .coinbase import CoinbaseCryptoSource, _KNOWN_QUOTES as _COINBASE_QUOTES
from .models import CryptoBar, CryptoHistory

from .._contracts import (
    canonical_crypto_pair,
    non_empty_reason,
    result_type_reason,
    row_object_and_aware_datetime_reason,
    strictly_ascending_reason,
)
from ..exceptions import AllSourcesFailed, InvalidData, SourceError, UnsupportedInterval
from ..failover import FailoverClient, _fetched_at_utc_reason, _warnings_reason
from ..models import Interval, SourceAttempt
from ..validation import validate_date_range, validate_non_empty_string

# Default crypto failover chain (deepest/widest first).
_DEFAULT_CRYPTO_SOURCE_CLASSES = (BinanceCryptoSource, CoinbaseCryptoSource)


def default_crypto_sources(http_get=None, timeout: float = 25.0):
    """Instantiate the default crypto failover chain (all USD): Binance primary, Coinbase backup."""
    return [c(http_get=http_get, timeout=timeout) for c in _DEFAULT_CRYPTO_SOURCE_CLASSES]


def _crypto_unit(source):
    """Declared crypto unit/currency of a source (``"USD"`` for the default chain)."""
    return getattr(source, "unit", None)


#: Issue #169: exact warning emitted on a returned crypto history that does NOT fully cover the
#: requested bounded window (after failover-first found no fully-covering source). It names the
#: requested start/end AND the returned first/last dates so the gap is explicit, never silent.
#: Tests bind this verbatim. ``open`` marks an unbounded side (start or end not requested).
_PARTIAL_COVERAGE_WARNING_TEMPLATE = (
    "partial_coverage: requested {start}..{end}, returned {first}..{last}"
)


def _partial_coverage_warning(sd, ed, first: date, last: date) -> str:
    """Format the exact #169 ``partial_coverage`` warning for a best-available result."""
    return _PARTIAL_COVERAGE_WARNING_TEMPLATE.format(
        start=sd.isoformat() if sd is not None else "open",
        end=ed.isoformat() if ed is not None else "open",
        first=first.isoformat(),
        last=last.isoformat(),
    )


def _as_request_date(val):
    """Coerce a request bound (date | datetime | None) to a plain ``date`` (or ``None``)."""
    if val is None:
        return None
    if hasattr(val, "date"):
        return val.date()
    return val if isinstance(val, date) else None


def _coverage_facts(bars, sd, ed):
    """Return ``(fully_covers, overlap, first_date, last_date)`` for a bounded request.

    ``bars`` is the validated, strictly-ascending bar tuple. ``fully_covers`` requires the series to
    reach the requested start AND end (an unbounded side imposes no requirement). ``overlap`` is the
    number of bars whose date falls inside the requested window — the best-available ranking key.
    """
    dates = [b.time.date() for b in bars]
    first, last = dates[0], dates[-1]
    fully = (sd is None or first <= sd) and (ed is None or last >= ed)
    overlap = sum(
        1 for d in dates if (sd is None or d >= sd) and (ed is None or d <= ed)
    )
    return fully, overlap, first, last


# Quotes recognized by the crypto adapters, longest-first, so stripping a known
# quote suffix yields the base asset for identity checks.
_KNOWN_QUOTES = tuple(
    sorted(frozenset(_BINANCE_QUOTES) | frozenset(_COINBASE_QUOTES), key=len, reverse=True)
)
_KNOWN_QUOTES_SET = frozenset(_KNOWN_QUOTES)


def _normalize_crypto_symbol(symbol: str) -> str:
    """Issue #9 (crypto): a crypto symbol is a canonical trading PAIR, not a security
    ticker. Reject malformed shapes (slash, internal whitespace/control/newline,
    leading/trailing/double hyphen, non-string, blank) AND pairs whose quote asset is
    not a recognized quote — all before the failover engine runs (zero source call),
    so an unservable pair fails closed with InvalidData, never AllSourcesFailed.
    Accept concatenated (BTCUSDT) or hyphenated (BTC-USD), normalized upper."""
    sym = canonical_crypto_pair(symbol, "crypto symbol")
    # B1: require a recognized quote (longest-known-quote parsing) so an unknown-quote
    # pair (e.g. BTC-FAKE / BTCXYZ / FAKE1ZZZ) fails closed here, not deep in adapters.
    if "-" in sym:
        if sym.split("-", 1)[1] not in _KNOWN_QUOTES_SET:
            raise InvalidData(f"crypto symbol: unknown quote asset in {symbol!r}")
    elif not any(sym.endswith(q) and len(sym) > len(q) for q in _KNOWN_QUOTES):
        raise InvalidData(f"crypto symbol: cannot determine quote asset in {symbol!r}")
    return sym


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
            # Issue #169: a BOUNDED request needs requested-window coverage validation +
            # failover-first + best-available, which the first-accepted-wins engine cannot express
            # (it would AllSourcesFailed when every source is partial). Orchestrate here.
            return self._run_with_coverage(symbol, interval, start, end)
        # Unbounded: no coverage check — preserve the existing engine behavior exactly.
        return self._engine.run(symbol, interval, start, end)

    def _run_with_coverage(self, symbol, interval, start, end) -> CryptoHistory:
        """Issue #169 (option B): failover-first, then best-available + ``partial_coverage`` warning.

        1. A source whose VALID series fully covers the requested window wins immediately (no warning).
        2. A partial (but otherwise valid) series is collected, not accepted as a clean success, so
           later sources still get a chance.
        3. If no source fully covers, return the best-available valid series (max requested-day
           overlap, then source order) with an exact ``partial_coverage`` warning.
        Hard guards (type/identity/unit/value/ascending) still hard-reject; a series with ZERO
        in-window bars is a failed attempt (not a misleading best-available). No valid series at all
        -> ``AllSourcesFailed`` (same as the engine).
        """
        sd, ed = _as_request_date(start), _as_request_date(end)
        capable = [s for s in self._engine.sources if s.supports(interval)]
        if not capable:
            raise UnsupportedInterval(
                f"no configured crypto source supports interval "
                f"{getattr(interval, 'value', interval)}"
            )
        attempts: list[SourceAttempt] = []
        candidates: list[tuple[int, int, CryptoHistory]] = []  # (overlap, order, hist)
        for order, src in enumerate(capable):
            if len(attempts) >= self.max_attempts:
                break
            try:
                hist = self._operation_get_klines(src, symbol, interval, start, end)
            except SourceError as exc:
                attempts.append(SourceAttempt(src.name, False, f"{type(exc).__name__}: {exc}"))
                continue
            reason = _hard_reject_reason(
                hist, symbol=symbol, interval=interval, chain_unit=self._chain_unit
            )
            if reason:
                attempts.append(SourceAttempt(src.name, False, reason))
                continue
            # Provenance (#126): a crypto result carries a plain string ``source``.
            prov = getattr(hist, "source", None)
            if prov != src.name:
                attempts.append(
                    SourceAttempt(
                        src.name,
                        False,
                        f"provenance mismatch: result stamped source {prov!r} "
                        f"but produced by source {src.name!r}",
                    )
                )
                continue
            fully, overlap, _first, _last = _coverage_facts(hist.bars, sd, ed)
            if overlap == 0:
                attempts.append(SourceAttempt(src.name, False, "no bars in requested date range"))
                continue
            if fully:
                attempts.append(SourceAttempt(src.name, True, "ok"))
                return hist  # failover-first: first fully-covering source wins, no warning
            attempts.append(SourceAttempt(src.name, True, "partial_coverage"))
            candidates.append((overlap, order, hist))
        if candidates:
            # Best-available: maximize covered requested-day overlap, then source order.
            candidates.sort(key=lambda c: (-c[0], c[1]))
            best = candidates[0][2]
            first, last = best.bars[0].time.date(), best.bars[-1].time.date()
            warning = _partial_coverage_warning(sd, ed, first, last)
            return dataclasses.replace(best, warnings=tuple(best.warnings) + (warning,))
        raise AllSourcesFailed(symbol, interval, tuple(attempts))

    @staticmethod
    def _operation_get_klines(src, symbol, interval, start, end):
        return src.get_klines(symbol, interval, start, end)

    def _reject_reason(self, hist, symbol, interval, start, end) -> str | None:
        return _validate_crypto_result(
            hist,
            symbol=symbol,
            interval=interval,
            chain_unit=self._chain_unit,
            start=start,
            end=end,
        )


def _hard_reject_reason(
    hist,
    *,
    symbol: str,
    interval: Interval,
    chain_unit: str | None,
) -> str | None:
    """Return a HARD rejection reason (type/identity/unit/value/ascending) or ``None``.

    Window coverage is intentionally NOT checked here — it is the softer #169 dimension handled by
    :meth:`FailoverCryptoClient._run_with_coverage` for bounded requests.
    :func:`_validate_crypto_result` wraps this with the legacy in-window check for the unbounded
    engine path.
    """
    # Issue #125: a malformed (non-typed) result container must be recorded as a
    # rejected source attempt, not leak a raw AttributeError from len(hist.bars).
    reason = result_type_reason(hist, CryptoHistory)
    if reason:
        return reason
    reason = non_empty_reason(hist.bars)
    if reason:
        return reason

    # Issue #127: reject present-malformed fetched_at_utc freshness metadata.
    reason = _fetched_at_utc_reason(hist.fetched_at_utc)
    if reason:
        return reason
    # Issue #128: reject malformed warnings (must be tuple[str, ...]).
    reason = _warnings_reason(hist.warnings)
    if reason:
        return reason

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

    # Issue #69: returned crypto quote metadata must be canonical and internally
    # consistent (exact strings, no strip/coerce). In a USD chain the quote asset
    # must be a recognized USD-equivalent quote; the human unit strings must match
    # the parsed legs. Contradictory metadata (currency='USD' but quote_asset='BTC',
    # or price_unit='BTC per BTC') is rejected so it cannot block a healthy backup.
    ba = hist.base_asset
    qa = hist.quote_asset
    if ba is not None and (not isinstance(ba, str) or not ba or ba != ba.strip()):
        return f"malformed base_asset {ba!r}: expected a non-empty canonical string"
    if qa is not None:
        if not isinstance(qa, str) or not qa or qa != qa.strip():
            return f"malformed quote_asset {qa!r}: expected a non-empty canonical string"
        if chain_unit is not None and qa not in _USD_STABLE_QUOTES:
            return (
                f"quote_asset mismatch: {qa!r} is not a USD-equivalent quote "
                f"for a {chain_unit} chain"
            )
    # The human price/volume unit strings are quote-per-base / base. Validating
    # them requires the base leg, so a present unit string with NO base_asset is
    # itself inconsistent (B1: do not silently skip). When base is present the
    # price_unit may legitimately name EITHER the literal quote_asset (Binance,
    # "USDT per BTC") OR the normalized currency (Coinbase USDC product, "USD per
    # ETH") — accept both forms (B2), reject anything else.
    if (hist.price_unit is not None or hist.volume_unit is not None) and not (
        isinstance(ba, str) and ba
    ):
        return "malformed unit metadata: price_unit/volume_unit present without a base_asset"
    if hist.price_unit is not None:
        pu = hist.price_unit
        if not isinstance(pu, str) or not pu:
            return f"malformed price_unit {pu!r}: expected a non-empty string"
        allowed = set()
        cur = hist.currency
        if isinstance(cur, str) and cur:
            allowed.add(f"{cur} per {ba}")
        if isinstance(qa, str) and qa:
            allowed.add(f"{qa} per {ba}")
        if pu not in allowed:
            return f"price_unit mismatch: {pu!r} not in {sorted(allowed)}"
    if hist.volume_unit is not None:
        vu = hist.volume_unit
        if not isinstance(vu, str):
            return f"malformed volume_unit {vu!r}: expected a string"
        if vu != ba:
            return f"volume_unit mismatch: {vu!r} != base asset {ba!r}"
    if hist.provider_symbol is not None:
        ps = hist.provider_symbol
        if not isinstance(ps, str) or not ps or ps != ps.strip():
            return f"malformed provider_symbol {ps!r}: expected a non-empty canonical string"

    # Issue #124: each bar key must be a timezone-AWARE datetime (the documented
    # CryptoBar.time contract — candle open time, tz-aware UTC). A naive datetime
    # or non-datetime key is rejected before the ascending-order compare and the
    # window .date() call, so a malformed key is a recorded rejected attempt.
    # Issue #124/#125 (reopen): each bar must be a CryptoBar whose .time key is a
    # timezone-aware datetime (candle open time, tz-aware UTC). Per-bar, before the
    # ascending compare and window .date() call, so a malformed row/key is a
    # recorded rejected attempt rather than a raw Type/AttributeError.
    reason = row_object_and_aware_datetime_reason(
        hist.bars, CryptoBar, key=lambda b: b.time, noun="bar"
    )
    if reason:
        return reason

    # Sorting (#85).
    reason = strictly_ascending_reason(
        hist.bars, key=lambda b: b.time, msg="bars are not strictly ascending by time"
    )
    if reason:
        return reason

    # Row-level financial invariants (#86).
    for bar in hist.bars:
        reason = _validate_crypto_bar(bar)
        if reason:
            return reason

    return None


def _validate_crypto_result(
    hist,
    *,
    symbol: str,
    interval: Interval,
    chain_unit: str | None,
    start,
    end,
) -> str | None:
    """Return a rejection reason or ``None`` (engine / unbounded path).

    Hard guards then the legacy in-window check. Bounded requests no longer reach this — the client
    routes them to :meth:`FailoverCryptoClient._run_with_coverage` (#169). Kept correct for the
    unbounded engine path, where ``start``/``end`` are ``None`` and the window check is a no-op.
    """
    reason = _hard_reject_reason(
        hist, symbol=symbol, interval=interval, chain_unit=chain_unit
    )
    if reason:
        return reason
    sd, ed = _as_request_date(start), _as_request_date(end)
    if sd is not None or ed is not None:
        in_window = any(
            (sd is None or bar.time.date() >= sd) and (ed is None or bar.time.date() <= ed)
            for bar in hist.bars
        )
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
