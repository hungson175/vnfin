"""Sequential multi-source failover client for price history."""
from __future__ import annotations

from dataclasses import replace

from .exceptions import AllSourcesFailed, SourceError
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
            warnings = tuple(hist.warnings) + self._staleness_warnings(hist, end)
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
    def _staleness_warnings(hist, end) -> tuple[str, ...]:
        # Soft, non-failing. A VN trading-calendar-aware check lands in a later step;
        # for now we never hard-fail on staleness (avoids weekend/holiday false-fails).
        return ()
