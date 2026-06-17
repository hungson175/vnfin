"""Typed data contracts for vnfin fundamental reports.

Mirrors the conventions of ``vnfin.models`` (frozen dataclasses, explicit
currency, source attribution + ``fetched_at_utc`` on every result). A
``FinancialReport`` is one financial statement for one fiscal period: a set of
``LineItem`` rows (item_code -> numeric value) plus provenance.

Provider responses (VNDirect api-finfo) are LONG/tall: one row per (line-item,
period). The adapter pivots those rows into one ``FinancialReport`` per
``fiscalDate``. Statement money values are RAW VND (unscaled); ratio "values"
are dimensionless / per-share VND depending on the ratio.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


class StatementType(str, Enum):
    """Which financial statement a report represents."""

    INCOME = "income"
    BALANCE = "balance"
    CASHFLOW = "cashflow"
    RATIOS = "ratios"


class Period(str, Enum):
    """Reporting cadence. Maps directly to VNDirect ``reportType``."""

    QUARTER = "QUARTER"
    ANNUAL = "ANNUAL"


@dataclass(frozen=True)
class LineItem:
    """A single statement line: a stable provider code, a best-effort human
    name, and the numeric value. For statements ``value`` is RAW VND; for
    ratios it is the ratio value (dimensionless or per-share VND)."""

    item_code: str
    name: str
    value: float


@dataclass(frozen=True)
class FinancialReport:
    """One statement for one fiscal period, with provenance.

    ``items`` are the pivoted line items for this period. ``model_type`` and
    ``is_bank`` record the VNDirect template used (corporate 1/2/3 vs bank
    101/102/103) so downstream code can pick the right line-item interpretation.
    """

    symbol: str
    statement_type: StatementType
    period: Period
    fiscal_date: date
    items: tuple[LineItem, ...]
    source: str
    currency: str = "VND"
    is_bank: bool = False
    model_type: Optional[int] = None
    provider_symbol: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    warnings: tuple[str, ...] = ()

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def get(self, item_code: str) -> Optional[float]:
        """Return the value for ``item_code`` (or ``ratioCode``), else ``None``."""
        key = str(item_code)
        for li in self.items:
            if li.item_code == key:
                return li.value
        return None

    def to_dataframe(self) -> "pd.DataFrame":
        """Return a one-row-per-line-item DataFrame. Metadata in ``df.attrs``."""
        import pandas as pd

        rows = [
            {"item_code": li.item_code, "name": li.name, "value": li.value}
            for li in self.items
        ]
        df = pd.DataFrame(rows, columns=["item_code", "name", "value"])
        df.attrs.update(
            symbol=self.symbol,
            statement_type=self.statement_type.value,
            period=self.period.value,
            fiscal_date=self.fiscal_date.isoformat(),
            source=self.source,
            currency=self.currency,
            is_bank=self.is_bank,
            model_type=self.model_type,
        )
        return df
