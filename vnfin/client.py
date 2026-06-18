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

from datetime import datetime

from .exceptions import AllSourcesFailed, UnsupportedInterval
from .failover import FailoverClient
from .models import Interval, PriceHistory


def _price_unit(source):
    """Declared price unit of a source (``"VND"`` / ``"points"`` / ``None``)."""
    return getattr(source, "unit", None)


class FailoverPriceClient:
    """Try sources in priority order, up to ``max_attempts`` actual calls.

    A result is returned only if it passes acceptance validation; otherwise the
    client records the failure reason and falls through to the next source. Sources
    that do not support the requested interval are skipped without a network call
    and do not count against ``max_attempts``. All configured sources must emit the
    same unit/currency (see :class:`vnfin.failover.FailoverClient` unit guard).
    """

    def __init__(self, sources, max_attempts: int = 3):
        self._engine = FailoverClient(
            sources,
            operation=lambda src, symbol, interval, start, end: src.get_history(
                symbol, interval, start, end
            ),
            capability=lambda src, symbol, interval, start, end: src.supports(interval),
            reject=self._reject_reason,
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
    def _reject_reason(hist) -> str | None:
        if hist is None or len(hist.bars) == 0:
            return "empty result"
        return None

    @staticmethod
    def _coverage_warnings(hist, start, end, tolerance_days: int = 7) -> tuple[str, ...]:
        """Soft, non-failing range-coverage diagnostics (P2).

        We warn (not fail) when the returned series starts well after the requested
        start or ends well before the requested end — partial coverage may be a clamped
        history, a recent listing, or a stale source. Hard rejection awaits a VN
        trading-calendar + listing-date source (avoids weekend/holiday false-fails).
        """

        def as_date(d):
            return d.date() if isinstance(d, datetime) else d

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
        if ed is not None and (ed - last).days > tolerance_days:
            warns.append(
                f"partial_end_coverage: last bar {last} is >{tolerance_days}d before requested end {ed}"
            )
        return tuple(warns)
