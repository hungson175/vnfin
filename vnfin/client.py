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

from dataclasses import replace

from datetime import date

from .calendar import as_date, expected_latest_trading_day
from .exceptions import AllSourcesFailed, InvalidData, UnsupportedInterval
from .failover import FailoverClient
from .models import AdjustmentPolicy, Interval, PriceHistory


def _price_unit(source):
    """Declared price unit of a source (``"VND"`` / ``"points"`` / ``None``)."""
    return getattr(source, "unit", None)


def _require_date_range(start, end) -> None:
    """Validate the requested window BEFORE any source/failover call (B5).

    The price API requires an explicit ``start`` and ``end`` (a ``date`` or
    ``datetime``). Missing dates, a wrong type, or an inverted range raise a stable
    :class:`~vnfin.exceptions.InvalidData` (a ``VnfinError``) up front. This keeps
    the public surface from leaking the raw ``TypeError`` that
    ``datetime.combine(None, ...)`` would otherwise produce deep inside a source,
    and avoids burning failover attempts on a caller-input mistake.
    """
    if start is None or end is None:
        missing = [n for n, v in (("start", start), ("end", end)) if v is None]
        raise InvalidData(
            "price history requires both 'start' and 'end' dates; missing: "
            + ", ".join(missing)
        )
    if not isinstance(start, date) or not isinstance(end, date):
        raise InvalidData(
            "price history 'start' and 'end' must be datetime.date or datetime.datetime"
        )
    try:
        reversed_range = start > end
    except TypeError as exc:  # mixing naive date with datetime, etc.
        raise InvalidData(
            "price history 'start' and 'end' must be comparable (same date/datetime type)"
        ) from exc
    if reversed_range:
        raise InvalidData(
            f"price history requires start <= end, got start={start} > end={end}"
        )


def _validate_symbol(symbol) -> None:
    """Validate a price/index/crypto-style symbol before any source call (Issue #9)."""
    if not isinstance(symbol, str) or not symbol.strip():
        raise InvalidData(f"symbol must be a non-empty string, got {symbol!r}")


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
        self._engine = FailoverClient(
            sources,
            operation=lambda src, symbol, interval, start, end: src.get_history(
                symbol, interval, start, end
            ),
            capability=lambda src, symbol, interval, start, end: src.supports(interval),
            reject=lambda hist, _sym, _interval, start, end: FailoverPriceClient._reject_reason(
                hist, start, end
            ),
            unit_of=_price_unit,
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
        _validate_symbol(symbol)
        _require_date_range(start, end)
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

    @staticmethod
    def _finalize(hist, attempts, symbol, interval, start, end) -> PriceHistory:
        warnings = tuple(hist.warnings) + FailoverPriceClient._coverage_warnings(
            hist, start, end
        )
        return replace(hist, attempts=attempts, warnings=warnings)

    @staticmethod
    def _reject_reason(hist, start, end) -> str | None:
        if hist is None or len(hist.bars) == 0:
            return "empty result"
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
