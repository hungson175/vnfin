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
from .cafef import CafeFFundamentalSource
from .client import (
    FailoverFundamentalClient,
    default_fundamental_client,
    default_fundamental_sources,
)
from .models import FinancialReport, LineItem, Period, StatementType
from .vndirect import VNDirectFundamentalSource

__all__ = [
    "FinancialReport",
    "LineItem",
    "Period",
    "StatementType",
    "FundamentalSource",
    "VNDirectFundamentalSource",
    "CafeFFundamentalSource",
    "FailoverFundamentalClient",
    "default_fundamental_sources",
    "default_fundamental_client",
    "get_financials",
    "client",
    "source",
]


def source(http_get=None, timeout: float = 25.0) -> VNDirectFundamentalSource:
    """Primary fundamentals SOURCE: the default :class:`VNDirectFundamentalSource`.

    Standard ``<domain>.source(...)`` factory — a single primary adapter (no
    failover). Use ``.get_financials(symbol, statement, period, ...)`` on it, or
    prefer :func:`client` / :func:`get_financials` for the failover chain.
    Reports are RAW VND.
    """
    return VNDirectFundamentalSource(http_get=http_get, timeout=timeout)


def client(
    http_get=None, timeout: float = 25.0, max_attempts: int = 3
) -> FailoverFundamentalClient:
    """Primary fundamentals CLIENT: failover over VNDirect -> CafeF (RAW VND).

    Standard ``<domain>.client(...)`` factory. Returns a
    :class:`FailoverFundamentalClient` whose sources all emit RAW VND (the
    unit-homogeneity guard enforces this). Use ``.get_financials(...)`` on it.
    """
    return default_fundamental_client(
        http_get=http_get, timeout=timeout, max_attempts=max_attempts
    )


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
    sources=None,
    max_attempts: int = 3,
    http_get=None,
    timeout: float = 25.0,
) -> tuple[FinancialReport, ...]:
    """Fetch typed fundamental reports for ``symbol``, newest fiscal period first.

    Fails over VNDirect (primary) -> CafeF (backup) by default; both emit RAW VND
    so the unit-homogeneity guard accepts the chain.

    ``statement`` accepts a ``StatementType`` or its string value (e.g. "income",
    "balance", "cashflow", "ratios"); ``period`` accepts a ``Period`` or
    "QUARTER"/"ANNUAL" (case-insensitive). Pass ``is_bank=True`` for banks so the
    VNDirect bank statement template (modelType 101/102/103) is used.

    Source selection (most specific wins):

    * ``source=`` — a single :class:`FundamentalSource` (no failover; back-compat).
    * ``sources=`` — an explicit list to chain (must share one unit).
    * neither — the default failover chain (VNDirect -> CafeF).
    """
    st = _coerce_statement(statement)
    pd = _coerce_period(period)
    if source is not None:
        return source.get_financials(symbol, st, pd, is_bank=is_bank, limit=limit)
    chain = (
        sources
        if sources is not None
        else default_fundamental_sources(http_get=http_get, timeout=timeout)
    )
    client_ = FailoverFundamentalClient(chain, max_attempts=max_attempts)
    return client_.get_financials(symbol, st, pd, is_bank=is_bank, limit=limit)
