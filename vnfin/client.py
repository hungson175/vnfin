"""Sequential multi-source failover client for price history."""
from __future__ import annotations

from dataclasses import replace

from datetime import datetime

from .exceptions import AllSourcesFailed, SourceError, UnsupportedInterval
from .models import Interval, PriceHistory, SourceAttempt


class FailoverPriceClient:
    """Try sources in priority order, up to ``max_attempts`` actual calls.

    A result is returned only if it passes acceptance validation; otherwise the
    client records the failure reason and falls through to the next source. Sources
    that do not support the requested interval are skipped without a network call
    and do not count against ``max_attempts``.
    """

    def __init__(self, sources, max_attempts: int = 3):
        self.sources = list(sources)
        self.max_attempts = max_attempts

    def get_history(self, symbol, interval: Interval = Interval.D1, start=None, end=None) -> PriceHistory:
        attempts: list[SourceAttempt] = []
        capable = [s for s in self.sources if s.supports(interval)]
        if not capable:
            raise UnsupportedInterval(
                f"no configured source supports interval {interval.value}"
            )
        for src in capable:
            if len(attempts) >= self.max_attempts:
                break
            try:
                hist = src.get_history(symbol, interval, start, end)
            except SourceError as exc:
                attempts.append(SourceAttempt(src.name, False, f"{type(exc).__name__}: {exc}"))
                continue
            reason = self._reject_reason(hist)
            if reason:
                attempts.append(SourceAttempt(src.name, False, reason))
                continue
            attempts.append(SourceAttempt(src.name, True, "ok"))
            warnings = tuple(hist.warnings) + self._coverage_warnings(hist, start, end)
            return replace(hist, attempts=tuple(attempts), warnings=warnings)
        raise AllSourcesFailed(symbol, interval, tuple(attempts))

    def get_daily(self, symbol, start, end) -> PriceHistory:
        return self.get_history(symbol, Interval.D1, start, end)

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
