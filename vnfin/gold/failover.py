"""Sequential multi-source failover client for world-gold daily history.

``FailoverGoldClient`` is a thin **specialization** of the domain-agnostic
:class:`vnfin.failover.FailoverClient`, exactly mirroring how
:class:`vnfin.client.FailoverPriceClient` wraps the same engine. It wires the
gold-history operation (``source.get_history``), a history capability gate
(``source.provides_history``), acceptance (non-empty **and materially-complete**
series), the unit guard (``source.unit`` -> all sources must be ``USD/oz``), and
result finalization (attach per-source attempts + soft coverage warnings) into
the generic engine.

Range-coverage acceptance (B11)
-------------------------------
A daily world-gold source (e.g. :class:`vnfin.gold.CurrencyApiGoldSource`) fans
out one request per calendar day and *skips* days it cannot fetch (404 /
transient miss). Without a coverage check, a one-day partial primary result would
be "non-empty" and would block failover to a complete backup. So acceptance is
two-tier, measured against the **expected trading days** (Mon-Fri weekdays) in the
requested ``[start, end]`` window — XAU/USD is a global OTC market that does not
trade on weekends:

* **Reject (fall through to backup)** when the covered fraction of expected
  weekdays is below ``min_coverage`` (default ``0.5``). A materially-incomplete
  primary result must not pre-empt a complete backup.
* **Accept with a soft ``partial_coverage`` warning** when coverage is between
  ``min_coverage`` and ``warn_coverage`` (default ``0.9``): usable, but the caller
  is told the series is gappy.
* **Accept silently** at/above ``warn_coverage``.

When the requested window contains no weekdays at all (e.g. a single Saturday),
any non-empty result is accepted (there is nothing to be incomplete against).

Only same-unit world sources belong here: the unit-homogeneity guard enforces a
single ``USD/oz`` chain, so a VN domestic (VND/lượng) source can never be mixed in.
"""
from __future__ import annotations

import math
from dataclasses import replace
from datetime import date, datetime, timedelta

from ..exceptions import AllSourcesFailed, InvalidData, UnsupportedInterval
from ..failover import FailoverClient
from ..validation import validate_date_range
from .models import GoldBar, GoldHistory


def _gold_unit(source):
    """Declared gold unit of a source (``"USD/oz"`` for world sources, else ``None``)."""
    return getattr(source, "unit", None)


def _as_date(x):
    return x.date() if isinstance(x, datetime) else x


def _expected_trading_days(lo: date, hi: date) -> int:
    """Count weekdays (Mon-Fri) in the inclusive ``[lo, hi]`` window.

    XAU/USD is a global OTC market with no weekend sessions, so weekdays are the
    coverage denominator. We deliberately do not subtract public holidays here:
    that would make acceptance country-specific, and erring toward a *larger*
    denominator only makes the coverage check more conservative (it never causes a
    false-complete acceptance).
    """
    if hi < lo:
        lo, hi = hi, lo
    days = (hi - lo).days + 1
    full_weeks, rem = divmod(days, 7)
    count = full_weeks * 5
    wd = lo.weekday()  # Mon=0 .. Sun=6
    for i in range(rem):
        if (wd + i) % 7 < 5:
            count += 1
    return count


class FailoverGoldClient:
    """Try gold-history sources in priority order, up to ``max_attempts`` calls.

    A result is returned only if it is a non-empty series **and** covers at least
    ``min_coverage`` of the expected trading days in the requested window;
    otherwise the failure reason is recorded and the client falls through to the
    next source. Accepted-but-gappy series (coverage below ``warn_coverage``) carry
    a soft ``partial_coverage`` warning. Sources that do not provide history are
    skipped without a network call and do not count against ``max_attempts``. All
    configured sources must emit the same unit (the
    :class:`vnfin.failover.FailoverClient` unit-homogeneity guard enforces ``USD/oz``).
    """

    def __init__(
        self,
        sources,
        max_attempts: int = 3,
        *,
        min_coverage: float = 0.5,
        warn_coverage: float = 0.9,
    ):
        sources = list(sources)  # materialize once; guard + engine both need the list
        min_coverage = self._coverage_threshold(min_coverage, "min_coverage")
        warn_coverage = self._coverage_threshold(warn_coverage, "warn_coverage")
        if warn_coverage < min_coverage:
            raise ValueError(
                f"warn_coverage ({warn_coverage!r}) must be >= min_coverage ({min_coverage!r})"
            )
        self.min_coverage = min_coverage
        self.warn_coverage = warn_coverage
        # The generic engine's ``reject`` callable only receives the result, but the
        # coverage check needs the requested window. ``get_history`` stashes the
        # current request range here before delegating to ``run`` (each call is
        # self-contained; the client is not designed for concurrent reuse).
        self._request_range: tuple = (None, None)
        self._chain_unit = _gold_unit(next((s for s in sources if _gold_unit(s) is not None), None))
        self._engine = FailoverClient(
            sources,
            operation=lambda src, start, end: src.get_history(start, end),
            capability=lambda src, start, end: getattr(src, "provides_history", False),
            reject=self._reject_reason,
            unit_of=_gold_unit,
            max_attempts=max_attempts,
            failure_factory=lambda attempts, start, end: AllSourcesFailed(
                "XAU/USD", "1d", attempts
            ),
            no_capable_factory=lambda start, end: UnsupportedInterval(
                "no configured gold source provides daily history"
            ),
            finalize=self._finalize,
        )

    @staticmethod
    def _coverage_threshold(value, name: str) -> float:
        if isinstance(value, bool):
            raise ValueError(f"{name} must be a numeric threshold in [0, 1], got bool")
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"{name} must be a numeric threshold in [0, 1], got {type(value).__name__}"
            )
        threshold = float(value)
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"{name} must be in [0, 1], got {value!r}")
        return threshold

    @property
    def sources(self):
        return self._engine.sources

    @property
    def max_attempts(self) -> int:
        return self._engine.max_attempts

    @property
    def unit(self):
        return self._engine.unit

    def get_history(self, start: date, end: date) -> GoldHistory:
        # Issue #76: validate request dates before any source call.
        validate_date_range(start, end, name="gold history")
        self._request_range = (start, end)
        return self._engine.run(start, end)

    # --- coverage helpers ------------------------------------------------- #
    def _coverage(self, hist) -> tuple[int, int]:
        """Return ``(covered_weekdays, expected_weekdays)`` for ``hist`` vs request."""
        start, end = self._request_range
        lo, hi = _as_date(start), _as_date(end)
        if lo is None or hi is None:
            return (len(hist.bars), 0)
        if hi < lo:
            lo, hi = hi, lo
        expected = _expected_trading_days(lo, hi)
        covered = sum(
            1 for b in hist.bars if lo <= b.date <= hi and b.date.weekday() < 5
        )
        return (covered, expected)

    def _reject_reason(self, hist, *args, **kwargs) -> str | None:
        reason = _validate_gold_result(hist, self._chain_unit)
        if reason:
            return reason
        covered, expected = self._coverage(hist)
        if expected <= 0:
            # No weekday sessions expected in the window: nothing to be incomplete
            # against, so a non-empty result is acceptable.
            return None
        frac = covered / expected
        if frac < self.min_coverage:
            return (
                f"materially-incomplete range: covered {covered}/{expected} "
                f"expected trading days ({frac:.0%} < {self.min_coverage:.0%} min)"
            )
        return None

    def _finalize(self, hist, attempts, start, end) -> GoldHistory:
        warnings = tuple(hist.warnings) + self._coverage_warnings(hist)
        return replace(hist, attempts=attempts, warnings=warnings)

    def _coverage_warnings(self, hist) -> tuple[str, ...]:
        """Soft ``partial_coverage`` warning for an accepted-but-gappy series."""
        if not hist.bars:
            return ()
        covered, expected = self._coverage(hist)
        if expected <= 0:
            return ()
        frac = covered / expected
        if frac < self.warn_coverage:
            return (
                f"partial_coverage: covered {covered}/{expected} expected trading "
                f"days ({frac:.0%} < {self.warn_coverage:.0%}); series may be gappy",
            )
        return ()


def _validate_gold_result(hist, chain_unit: str | None) -> str | None:
    """Return a rejection reason or ``None`` if the world-gold result is acceptable."""
    if hist is None or len(hist.bars) == 0:
        return "empty result"

    # Identity / product (#74, #82).
    if hist.product not in ("XAU", "XAU/USD"):
        return f"product mismatch: returned {hist.product!r} is not world gold XAU/USD"

    # Unit metadata checks (#74).
    if chain_unit is not None:
        if hist.unit != chain_unit:
            return f"unit mismatch: returned {hist.unit!r} != chain unit {chain_unit!r}"
        if hist.value_unit != chain_unit:
            return f"value_unit mismatch: returned {hist.value_unit!r} != chain unit {chain_unit!r}"
    if hist.currency != "USD":
        return f"currency mismatch: returned {hist.currency!r} != 'USD'"

    # Sorting (#85).
    for i in range(len(hist.bars) - 1):
        if not (hist.bars[i].date < hist.bars[i + 1].date):
            return "bars are not strictly ascending by date"

    # Row-level financial invariants (#86).
    for bar in hist.bars:
        reason = _validate_gold_bar(bar)
        if reason:
            return reason
    return None


def _validate_gold_bar(bar: GoldBar) -> str | None:
    """Return a rejection reason if ``bar`` has an impossible price (#86)."""
    if isinstance(bar.price, bool) or not isinstance(bar.price, (int, float)):
        return f"bar {bar.date}: price has malformed type {type(bar.price).__name__}"
    if not math.isfinite(bar.price) or bar.price <= 0:
        return f"bar {bar.date}: price must be positive and finite, got {bar.price!r}"
    return None
