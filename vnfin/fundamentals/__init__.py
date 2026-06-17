"""vnfin fundamentals — typed financial reports (income / balance / cashflow / ratios).

Public API
----------
    from vnfin.fundamentals import get_financials, StatementType, Period

    reports = get_financials("FPT", StatementType.INCOME, Period.ANNUAL)
    reports = get_financials("VCB", "income", "annual", is_bank=True)  # bank template
    latest = reports[0]                 # newest fiscal period first
    revenue = latest.get("11000")       # raw VND, by itemCode
    df = latest.to_dataframe()          # one row per line item

Reports are LONG/tall provider rows pivoted into one ``FinancialReport`` per
fiscal period. Money values are RAW VND (unscaled). Banks use VNDirect
modelType 101/102/103; corporates use 1/2/3 — pass ``is_bank=True`` for banks.
"""
from __future__ import annotations

from ..exceptions import VnfinError
from .base import FundamentalSource
from .models import FinancialReport, LineItem, Period, StatementType
from .vndirect import VNDirectFundamentalSource

__all__ = [
    "FinancialReport",
    "LineItem",
    "Period",
    "StatementType",
    "FundamentalSource",
    "VNDirectFundamentalSource",
    "get_financials",
]


def _coerce_statement(statement) -> StatementType:
    if isinstance(statement, StatementType):
        return statement
    try:
        return StatementType(str(statement).strip().lower())
    except ValueError as exc:
        valid = ", ".join(s.value for s in StatementType)
        raise VnfinError(f"unknown statement {statement!r}; expected one of: {valid}") from exc


def _coerce_period(period) -> Period:
    if isinstance(period, Period):
        return period
    try:
        return Period(str(period).strip().upper())
    except ValueError as exc:
        valid = ", ".join(p.value for p in Period)
        raise VnfinError(f"unknown period {period!r}; expected one of: {valid}") from exc


def get_financials(
    symbol: str,
    statement,
    period,
    *,
    is_bank: bool = False,
    limit: int = 8,
    source: FundamentalSource | None = None,
) -> tuple[FinancialReport, ...]:
    """Fetch typed fundamental reports for ``symbol``, newest fiscal period first.

    ``statement`` accepts a ``StatementType`` or its string value (e.g. "income",
    "balance", "cashflow", "ratios"); ``period`` accepts a ``Period`` or
    "QUARTER"/"ANNUAL" (case-insensitive). Pass ``is_bank=True`` for banks so the
    VNDirect bank statement template (modelType 101/102/103) is used. ``source``
    is injectable; defaults to ``VNDirectFundamentalSource``.
    """
    st = _coerce_statement(statement)
    pd = _coerce_period(period)
    src = source or VNDirectFundamentalSource()
    return src.get_financials(symbol, st, pd, is_bank=is_bank, limit=limit)
