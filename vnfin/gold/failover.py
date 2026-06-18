"""Sequential multi-source failover client for world-gold daily history.

``FailoverGoldClient`` is a thin **specialization** of the domain-agnostic
:class:`vnfin.failover.FailoverClient`, exactly mirroring how
:class:`vnfin.client.FailoverPriceClient` wraps the same engine. It wires the
gold-history operation (``source.get_history``), a history capability gate
(``source.provides_history``), acceptance (non-empty series), the unit guard
(``source.unit`` -> all sources must be ``USD/oz``), and result finalization
(attach per-source attempts) into the generic engine.

Only same-unit world sources belong here: the unit-homogeneity guard enforces a
single ``USD/oz`` chain, so a VN domestic (VND/lượng) source can never be mixed in.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

from ..exceptions import AllSourcesFailed, UnsupportedInterval
from ..failover import FailoverClient
from .models import GoldHistory


def _gold_unit(source):
    """Declared gold unit of a source (``"USD/oz"`` for world sources, else ``None``)."""
    return getattr(source, "unit", None)


class FailoverGoldClient:
    """Try gold-history sources in priority order, up to ``max_attempts`` calls.

    A result is returned only if it is a non-empty series; otherwise the failure
    reason is recorded and the client falls through to the next source. Sources that
    do not provide history are skipped without a network call and do not count
    against ``max_attempts``. All configured sources must emit the same unit (the
    :class:`vnfin.failover.FailoverClient` unit-homogeneity guard enforces ``USD/oz``).
    """

    def __init__(self, sources, max_attempts: int = 3):
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
        return self._engine.run(start, end)

    @staticmethod
    def _finalize(hist, attempts, start, end) -> GoldHistory:
        return replace(hist, attempts=attempts)

    @staticmethod
    def _reject_reason(hist) -> str | None:
        if hist is None or len(hist.bars) == 0:
            return "empty result"
        return None
