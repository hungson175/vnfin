"""Sequential multi-source failover client for price history.

``FailoverPriceClient`` is a thin **specialization** of the domain-agnostic
:class:`vnfin.failover.FailoverClient`: it wires the price-domain operation
(``source.get_history``), capability (``source.supports(interval)``),
acceptance (non-empty series), unit guard (``source.unit``), and result
finalization (attach attempts + coverage warnings) into the generic engine.
The public behavior is byte-for-byte what it was when this client owned its own
loop; the engine is now shared so other domains can reuse it.
"""
from __future__ import annotations

import math
from dataclasses import replace
from datetime import date, datetime

from .calendar import as_date, expected_latest_trading_day
from .exceptions import AllSourcesFailed, InvalidData, UnsupportedInterval
from .failover import FailoverClient, _fetched_at_utc_reason, _warnings_reason
from .models import AdjustmentPolicy, Interval, PriceBar, PriceHistory
from .validation import validate_date_range, validate_non_empty_string


def _price_unit(source):
    """Declared price unit of a source (``"VND"`` / ``"points"`` / ``None``)."""
    return getattr(source, "unit", None)


def _chain_adjustment_policy(sources) -> AdjustmentPolicy | None:
    """Return the single declared adjustment policy of ``sources``, or ``None``."""
    seen = set()
    for src in sources:
        pol = (
            getattr(src, "ADJUSTMENT_POLICY", None)
            or getattr(src, "adjustment_policy", None)
            or AdjustmentPolicy.UNKNOWN
        )
        if isinstance(pol, AdjustmentPolicy) and pol != AdjustmentPolicy.UNKNOWN:
            seen.add(pol)
        elif isinstance(pol, str) and pol.strip().lower() != AdjustmentPolicy.UNKNOWN.value:
            try:
                seen.add(AdjustmentPolicy(pol.strip().lower()))
            except ValueError:
                pass
    if len(seen) == 1:
        return seen.pop()
    return None


def _adjustment_policy_guard(sources):
    """Issue #7: reject a price failover chain that mixes adjustment policies.

    A chain is only safe when every source applies the same adjustment semantics.
    Sources that do not declare a policy (UNKNOWN) are ignored for the guard; if all
    sources are unknown the chain is allowed. A mixed declared-policy chain raises
    ``InvalidData`` at construction time.
    """

    def _normalize_policy(pol):
        if isinstance(pol, AdjustmentPolicy):
            return pol.value
        if isinstance(pol, str) and pol.strip():
            return pol.strip().lower()
        return AdjustmentPolicy.UNKNOWN.value

    policies = set()
    for src in sources:
        pol = (
            getattr(src, "ADJUSTMENT_POLICY", None)
            or getattr(src, "adjustment_policy", None)
            or AdjustmentPolicy.UNKNOWN
        )
        pol_value = _normalize_policy(pol)
        if pol_value != AdjustmentPolicy.UNKNOWN.value:
            policies.add(pol_value)
    if len(policies) > 1:
        raise InvalidData(
            f"price failover chain mixes adjustment policies: {sorted(policies)}"
        )


class FailoverPriceClient:
    """Try sources in priority order, up to ``max_attempts`` actual calls.

    A result is returned only if it passes acceptance validation; otherwise the
    client records the failure reason and falls through to the next source. Sources
    that do not support the requested interval are skipped without a network call
    and do not count against ``max_attempts``. All configured sources must emit the
    same unit/currency (see :class:`vnfin.failover.FailoverClient` unit guard) and
    the same adjustment policy.
    """

    def __init__(self, sources, max_attempts: int = 3):
        sources = list(sources)  # materialize once; guard + engine both need the list
        # Issue #7: homogenous adjustment policies before the generic engine runs.
        _adjustment_policy_guard(sources)
        self._chain_unit = _price_unit(next((s for s in sources if _price_unit(s) is not None), None))
        self._chain_policy = _chain_adjustment_policy(sources)
        self._engine = FailoverClient(
            sources,
            operation=lambda src, symbol, interval, start, end: src.get_history(
                symbol, interval, start, end
            ),
            capability=lambda src, symbol, interval, start, end: src.supports(interval),
            reject=self._reject_reason,
            unit_of=_price_unit,
            provenance_of=lambda hist: getattr(hist, "source", None),  # #126
            max_attempts=max_attempts,
            failure_factory=lambda attempts, symbol, interval, start, end: AllSourcesFailed(
                symbol, interval, attempts
            ),
            no_capable_factory=lambda symbol, interval, start, end: UnsupportedInterval(
                f"no configured source supports interval {interval.value}"
            ),
            finalize=self._finalize,
        )

    @property
    def sources(self):
        return self._engine.sources

    @property
    def max_attempts(self) -> int:
        return self._engine.max_attempts

    def get_history(self, symbol, interval: Interval = Interval.D1, start=None, end=None) -> PriceHistory:
        # Issue #9: reject empty/malformed symbols before the failover engine runs.
        # Issue #97: normalize to uppercase so identity checks are case-insensitive
        # and match real sources that canonicalize symbols.
        symbol = validate_non_empty_string(symbol, "symbol").upper()
        validate_date_range(start, end, name="price history")
        # Issue #23: validate the interval is an Interval enum before the failover
        # engine's capability probe / no_capable_factory touches it. This prevents
        # a raw AttributeError from ``interval.value`` on a malformed caller value.
        if not isinstance(interval, Interval):
            raise InvalidData(
                f"interval must be a vnfin.models.Interval, got {type(interval).__name__}"
            )
        return self._engine.run(symbol, interval, start, end)

    def get_daily(self, symbol, start, end) -> PriceHistory:
        return self.get_history(symbol, Interval.D1, start, end)

    def _reject_reason(self, hist, symbol, interval, start, end) -> str | None:
        return _validate_price_result(
            hist,
            symbol=symbol,
            interval=interval,
            chain_unit=self._chain_unit,
            chain_policy=self._chain_policy,
            start=start,
            end=end,
        )

    @staticmethod
    def _finalize(hist, attempts, symbol, interval, start, end) -> PriceHistory:
        warnings = tuple(hist.warnings) + FailoverPriceClient._coverage_warnings(
            hist, start, end
        )
        return replace(hist, attempts=attempts, warnings=warnings)

    @staticmethod
    def _coverage_warnings(hist, start, end, tolerance_days: int = 7) -> tuple[str, ...]:
        """Soft, non-failing range-coverage diagnostics (P2).

        We warn (not fail) when the returned series starts well after the requested
        start or ends well before the requested end — partial coverage may be a clamped
        history, a recent listing, or a stale source. These remain soft warnings: this
        method never hard-fails.

        The ``partial_end_coverage`` (staleness) check is VN trading-calendar aware: a
        market does not trade on weekends or public holidays, so the latest bar an
        up-to-date source could possibly have for a request ending at ``end`` is
        :func:`vnfin.calendar.expected_latest_trading_day` ``(end)``. If the last bar is
        already at (or past) that expected trading day, the series is NOT stale and we
        do not warn — this avoids false staleness over a weekend or holiday. Only when
        the last bar is behind the expected latest trading day do we fall back to the
        day-gap tolerance. ``partial_start_coverage`` is unchanged.
        """
        warns: list[str] = []
        if not hist.bars:
            return ()
        first = hist.bars[0].time.date()
        last = hist.bars[-1].time.date()
        sd = as_date(start)
        ed = as_date(end)
        if sd is not None and (first - sd).days > tolerance_days:
            warns.append(
                f"partial_start_coverage: first bar {first} is >{tolerance_days}d after requested start {sd}"
            )
        if ed is not None:
            expected_last = expected_latest_trading_day(ed)
            # Up to date relative to the calendar: the last bar is the most recent
            # expected trading day (or newer) -> no staleness, regardless of raw gap.
            if last < expected_last and (ed - last).days > tolerance_days:
                warns.append(
                    f"partial_end_coverage: last bar {last} is >{tolerance_days}d before "
                    f"requested end {ed} (expected latest trading day {expected_last})"
                )
        return tuple(warns)


def _validate_price_result(
    hist,
    *,
    symbol: str,
    interval: Interval,
    chain_unit: str | None,
    chain_policy: AdjustmentPolicy | None,
    start,
    end,
) -> str | None:
    """Return a rejection reason or ``None`` if the price result is acceptable."""
    # Issue #125: a malformed (non-typed) result container must be recorded as a
    # rejected source attempt, not leak a raw AttributeError from len(hist.bars).
    if not isinstance(hist, PriceHistory):
        return f"unexpected result type {type(hist).__name__}"
    if len(hist.bars) == 0:
        return "empty result"

    # Issue #127: reject present-malformed fetched_at_utc freshness metadata.
    reason = _fetched_at_utc_reason(hist.fetched_at_utc)
    if reason:
        return reason
    # Issue #128: reject malformed warnings (must be tuple[str, ...]).
    reason = _warnings_reason(hist.warnings)
    if reason:
        return reason

    # Identity checks (#82).
    if hist.symbol != symbol:
        return f"symbol mismatch: returned {hist.symbol!r} != requested {symbol!r}"
    if hist.interval != interval:
        return f"interval mismatch: returned {hist.interval!r} != requested {interval!r}"

    # Unit and adjustment-policy metadata checks (#73).
    if chain_unit is not None:
        if hist.currency != chain_unit:
            return f"currency mismatch: returned {hist.currency!r} != chain unit {chain_unit!r}"
        if hist.value_unit != chain_unit:
            return f"value_unit mismatch: returned {hist.value_unit!r} != chain unit {chain_unit!r}"
    if chain_policy is not None and hist.adjustment_policy != chain_policy:
        return (
            f"adjustment_policy mismatch: returned {hist.adjustment_policy!r} "
            f"!= chain policy {chain_policy!r}"
        )

    # Issue #124: each bar key must be a timezone-AWARE datetime (the documented
    # PriceBar.time contract). A naive datetime or a non-datetime key is rejected
    # here, before the ascending-order compare and the window-coverage .date()
    # call, so a malformed key is a recorded rejected attempt rather than a raw
    # TypeError/AttributeError. ``utcoffset()`` is the robust aware check.
    for bar in hist.bars:
        # Issue #125 (reopen): reject a malformed inner row object before
        # dereferencing .time, so a dict/None/other row is a recorded rejected
        # attempt instead of a raw AttributeError.
        if not isinstance(bar, PriceBar):
            return f"malformed bar object {type(bar).__name__}"
        t = bar.time
        if not isinstance(t, datetime) or t.utcoffset() is None:
            return f"malformed bar time {t!r}: expected a timezone-aware datetime"

    # Sorting (#85).
    for i in range(len(hist.bars) - 1):
        if not (hist.bars[i].time < hist.bars[i + 1].time):
            return "bars are not strictly ascending by time"

    # Row-level financial invariants (#86).
    for bar in hist.bars:
        reason = _validate_price_bar(bar)
        if reason:
            return reason

    # Window coverage (preserved from original reject path).
    sd = as_date(start)
    ed = as_date(end)
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


def _validate_price_bar(bar: PriceBar) -> str | None:
    """Return a rejection reason if ``bar`` violates OHLC invariants (#86)."""
    for field in ("open", "high", "low", "close"):
        value = getattr(bar, field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"bar {bar.time}: {field} has malformed type {type(value).__name__}"
        if not math.isfinite(value) or value <= 0:
            return f"bar {bar.time}: {field} must be positive and finite, got {value!r}"
    if not (bar.low <= bar.open <= bar.high):
        return (
            f"bar {bar.time}: open {bar.open} not in [low {bar.low}, high {bar.high}]"
        )
    if not (bar.low <= bar.close <= bar.high):
        return (
            f"bar {bar.time}: close {bar.close} not in [low {bar.low}, high {bar.high}]"
        )
    if isinstance(bar.volume, bool) or not isinstance(bar.volume, int):
        return f"bar {bar.time}: volume must be an int, got {type(bar.volume).__name__}"
    if not (0 <= bar.volume):
        return f"bar {bar.time}: volume must be non-negative, got {bar.volume!r}"
    return None
