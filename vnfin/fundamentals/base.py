"""The fundamental-source port (interface) all fundamental adapters implement."""
from __future__ import annotations

from abc import ABC, abstractmethod

from .models import FinancialReport, Period, StatementType


class FundamentalSource(ABC):
    """A swappable source of typed fundamental reports.

    Adapters are constructed once and reused. Implementations MUST raise a
    ``vnfin.exceptions.SourceError`` subclass on failure (transport ->
    ``SourceUnavailable``, no rows -> ``EmptyData``, malformed ->
    ``InvalidData``) so the source stays failover-safe.
    """

    name: str = "base"

    @abstractmethod
    def get_financials(
        self,
        symbol: str,
        statement: StatementType,
        period: Period,
        *,
        is_bank: bool = False,
        limit: int = 8,
    ) -> tuple[FinancialReport, ...]:
        """Fetch one ``FinancialReport`` per available fiscal period, newest first."""

    def health(self) -> bool:  # pragma: no cover - default liveness probe
        return True
