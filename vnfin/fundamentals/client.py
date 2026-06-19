"""Sequential multi-source failover client for fundamental reports.

``FailoverFundamentalClient`` is a thin **specialization** of the
domain-agnostic :class:`vnfin.failover.FailoverClient`, mirroring how
``vnfin.client.FailoverPriceClient`` wraps the same engine for prices. It wires
the fundamentals operation (``source.get_financials``), acceptance (a non-empty
tuple of reports), and the unit guard (``source.unit``) into the generic engine.

The default chain is VNDirect (primary, deep history) -> CafeF (backup, no-auth
AJAX). BOTH sources emit RAW VND statement money, so the unit-homogeneity guard
accepts the chain; a source declaring any other unit (e.g. USD) is rejected at
construction, making a scale/currency mix structurally impossible.
"""
from __future__ import annotations

from ..exceptions import AllSourcesFailed
from ..failover import FailoverClient
from .base import AUTO, FundamentalSource
from .cafef import CafeFFundamentalSource
from .models import FinancialReport, Period, StatementType, _coerce_period, _coerce_statement
from .vndirect import VNDirectFundamentalSource

# Default fundamentals failover chain: primary first, backup second.
_DEFAULT_SOURCE_CLASSES = (VNDirectFundamentalSource, CafeFFundamentalSource)


def default_fundamental_sources(http_get=None, timeout: float = 25.0):
    """Instantiate the default fundamentals failover chain (all RAW VND).

    Order: :class:`VNDirectFundamentalSource` (primary) ->
    :class:`CafeFFundamentalSource` (backup). Both declare ``unit = "VND"``.
    """
    return [c(http_get=http_get, timeout=timeout) for c in _DEFAULT_SOURCE_CLASSES]


def _fundamental_unit(source):
    """Declared monetary unit of a fundamental source (``"VND"`` / ``None``)."""
    return getattr(source, "unit", None)


class FailoverFundamentalClient:
    """Try fundamental sources in priority order, up to ``max_attempts`` calls.

    A result is accepted only if it is a non-empty tuple of reports; otherwise
    the client records the reason and falls through to the next source. All
    configured sources must emit the same unit/currency (see
    :class:`vnfin.failover.FailoverClient` unit guard).
    """

    def __init__(self, sources, max_attempts: int = 3):
        self._engine = FailoverClient(
            sources,
            operation=lambda src, symbol, statement, period, is_bank, limit: src.get_financials(
                symbol, statement, period, is_bank=is_bank, limit=limit
            ),
            reject=self._reject_reason,
            unit_of=_fundamental_unit,
            max_attempts=max_attempts,
            failure_factory=lambda attempts, symbol, statement, period, is_bank, limit: AllSourcesFailed(
                symbol, getattr(statement, "value", statement), attempts
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

    def get_financials(
        self,
        symbol: str,
        statement: StatementType | str,
        period: Period | str,
        *,
        is_bank: bool | None = AUTO,
        limit: int = 8,
    ) -> tuple[FinancialReport, ...]:
        """Fail over across sources; ``is_bank`` defaults to :data:`AUTO`.

        The bank/corporate flag (explicit ``True``/``False`` or the AUTO sentinel
        asking each source to detect it) is forwarded unchanged to every source
        in the chain, so callers need not know whether a ticker is a bank.

        ``statement`` and ``period`` accept either the enum or its string value,
        matching the top-level :func:`get_financials` convenience API.
        """
        st = _coerce_statement(statement)
        pd = _coerce_period(period)
        return self._engine.run(symbol, st, pd, is_bank, limit)

    @staticmethod
    def _reject_reason(reports, *args, **kwargs) -> str | None:
        if not reports:
            return "empty result"
        return None


def default_fundamental_client(
    http_get=None, timeout: float = 25.0, max_attempts: int = 3
) -> FailoverFundamentalClient:
    """The default fundamentals client: failover over VNDirect -> CafeF."""
    return FailoverFundamentalClient(
        default_fundamental_sources(http_get=http_get, timeout=timeout),
        max_attempts=max_attempts,
    )
