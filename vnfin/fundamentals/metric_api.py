"""Canonical-metrics query API + static v1 catalog (#157).

STAGE A surface: the immutable v1 metric catalog, the static ``serves(...)``
capability predicate, and the two fully-offline query functions
``metric_catalog`` / ``explain_metric``. The network wrappers (``metrics`` /
``explain_metric_coverage``) and the pure transformers ship in later stages.

Module is ``metric_api`` (NOT ``metrics``) so the future ``fundamentals.metrics``
function attribute is not shadowed by a submodule (B5). Clean-room: built only on
the existing ``vnfin.fundamentals`` codes — no VNStock, no new source.
"""
from __future__ import annotations

from typing import Optional

from ..exceptions import VnfinError
from .models import StatementType, _coerce_statement
from .metric_models import (
    AppliesTo,
    MetricCategory,
    MetricDefinition,
    MetricId,
    MetricKind,
    MetricSourceCodes,
)

# --------------------------------------------------------------------------- #
# Static capability predicate (C / §3.5) — which source serves which statement.
# Deterministic capability sets, NOT exception-text classification. Source name
# strings are ``FundamentalSource.name`` ("vndirect"/"cafef").
# --------------------------------------------------------------------------- #
_SERVES: dict[str, frozenset[StatementType]] = {
    "vndirect": frozenset(
        {
            StatementType.INCOME,
            StatementType.BALANCE,
            StatementType.CASHFLOW,
            StatementType.RATIOS,
        }
    ),
    # CafeF does NOT serve cashflow (Type=3 -> EmptyData).
    "cafef": frozenset(
        {StatementType.INCOME, StatementType.BALANCE, StatementType.RATIOS}
    ),
}


def serves(source_name: str, statement) -> bool:
    """True iff ``source_name`` can serve ``statement`` (static capability set).

    ``statement`` accepts a :class:`StatementType` or its case-insensitive
    string value. An unknown source serves nothing (``False``).
    """
    st = _coerce_statement(statement)
    return st in _SERVES.get(source_name, frozenset())


# --------------------------------------------------------------------------- #
# v1 catalog — 26 MetricDefinitions. Codes are HARD-PINNED to the verified
# VNDirect namespace (brief §B). Bank codes use ONLY the #157-verified anchors;
# the disproven/deferred codes never appear.
# --------------------------------------------------------------------------- #
def _raw(
    metric_id: MetricId,
    name: str,
    category: MetricCategory,
    applies_to: AppliesTo,
    statement: StatementType,
    *,
    corporate_code: Optional[str] = None,
    bank_code: Optional[str] = None,
) -> MetricDefinition:
    return MetricDefinition(
        id=metric_id,
        name=name,
        category=category,
        kind=MetricKind.RAW_MAPPED,
        applies_to=applies_to,
        value_unit="VND",
        statement=statement,
        codes_by_source={
            "vndirect": MetricSourceCodes(
                corporate_code=corporate_code, bank_code=bank_code
            )
        },
    )


def _derived(
    metric_id: MetricId,
    name: str,
    category: MetricCategory,
    applies_to: AppliesTo,
    formula: str,
    inputs: tuple[MetricId, ...],
) -> MetricDefinition:
    return MetricDefinition(
        id=metric_id,
        name=name,
        category=category,
        kind=MetricKind.DERIVED,
        applies_to=applies_to,
        value_unit="ratio",
        formula=formula,
        inputs=inputs,
    )


_V1_CATALOG: tuple[MetricDefinition, ...] = (
    # ---- raw_mapped: corporate-only (CORPORATE) ------------------------- #
    _raw(MetricId.NET_REVENUE, "Net revenue", MetricCategory.SIZE,
         AppliesTo.CORPORATE, StatementType.INCOME, corporate_code="11000"),
    _raw(MetricId.GROSS_PROFIT, "Gross profit", MetricCategory.PROFITABILITY,
         AppliesTo.CORPORATE, StatementType.INCOME, corporate_code="11200"),
    _raw(MetricId.OPERATING_PROFIT, "Operating profit",
         MetricCategory.PROFITABILITY, AppliesTo.CORPORATE,
         StatementType.INCOME, corporate_code="14000"),
    _raw(MetricId.NET_INCOME_PARENT, "Net income (parent)",
         MetricCategory.PROFITABILITY, AppliesTo.CORPORATE,
         StatementType.INCOME, corporate_code="21100"),
    _raw(MetricId.CASH_AND_EQUIVALENTS, "Cash and equivalents",
         MetricCategory.LIQUIDITY, AppliesTo.CORPORATE,
         StatementType.BALANCE, corporate_code="23100"),
    _raw(MetricId.CURRENT_ASSETS, "Current assets", MetricCategory.LIQUIDITY,
         AppliesTo.CORPORATE, StatementType.BALANCE, corporate_code="23000"),
    _raw(MetricId.CURRENT_LIABILITIES, "Current liabilities",
         MetricCategory.LEVERAGE, AppliesTo.CORPORATE,
         StatementType.BALANCE, corporate_code="30100"),
    _raw(MetricId.LONG_TERM_LIABILITIES, "Long-term liabilities",
         MetricCategory.LEVERAGE, AppliesTo.CORPORATE,
         StatementType.BALANCE, corporate_code="30200"),
    _raw(MetricId.OPERATING_CASH_FLOW, "Operating cash flow",
         MetricCategory.CASHFLOW, AppliesTo.CORPORATE,
         StatementType.CASHFLOW, corporate_code="31000"),
    _raw(MetricId.INVESTING_CASH_FLOW, "Investing cash flow",
         MetricCategory.CASHFLOW, AppliesTo.CORPORATE,
         StatementType.CASHFLOW, corporate_code="32000"),
    _raw(MetricId.FINANCING_CASH_FLOW, "Financing cash flow",
         MetricCategory.CASHFLOW, AppliesTo.CORPORATE,
         StatementType.CASHFLOW, corporate_code="33000"),
    _raw(MetricId.NET_CASH_FLOW, "Net cash flow", MetricCategory.CASHFLOW,
         AppliesTo.CORPORATE, StatementType.CASHFLOW, corporate_code="34000"),
    _raw(MetricId.CASH_END_OF_PERIOD, "Cash at end of period",
         MetricCategory.CASHFLOW, AppliesTo.CORPORATE,
         StatementType.CASHFLOW, corporate_code="35000"),
    # ---- raw_mapped: shared (BOTH) — corporate_code + bank_code --------- #
    _raw(MetricId.PROFIT_BEFORE_TAX, "Profit before tax",
         MetricCategory.PROFITABILITY, AppliesTo.BOTH, StatementType.INCOME,
         corporate_code="20000", bank_code="23800"),
    _raw(MetricId.NET_INCOME, "Net income", MetricCategory.PROFITABILITY,
         AppliesTo.BOTH, StatementType.INCOME,
         corporate_code="21000", bank_code="23000"),
    _raw(MetricId.TOTAL_ASSETS, "Total assets", MetricCategory.SIZE,
         AppliesTo.BOTH, StatementType.BALANCE,
         corporate_code="25000", bank_code="12700"),
    _raw(MetricId.TOTAL_LIABILITIES, "Total liabilities",
         MetricCategory.LEVERAGE, AppliesTo.BOTH, StatementType.BALANCE,
         corporate_code="30000", bank_code="13000"),
    _raw(MetricId.OWNERS_EQUITY, "Owners' equity", MetricCategory.SIZE,
         AppliesTo.BOTH, StatementType.BALANCE,
         corporate_code="40000", bank_code="14000"),
    # ---- raw_mapped: bank-only (BANK) — bank_code only ----------------- #
    _raw(MetricId.NET_INTEREST_INCOME, "Net interest income",
         MetricCategory.PROFITABILITY, AppliesTo.BANK, StatementType.INCOME,
         bank_code="421900"),
    _raw(MetricId.LOANS_TO_CUSTOMERS, "Loans to customers",
         MetricCategory.SIZE, AppliesTo.BANK, StatementType.BALANCE,
         bank_code="412000"),
    _raw(MetricId.CUSTOMER_DEPOSITS, "Customer deposits",
         MetricCategory.LEVERAGE, AppliesTo.BANK, StatementType.BALANCE,
         bank_code="413300"),
    # ---- derived (ratio, guarded) -------------------------------------- #
    _derived(MetricId.GROSS_MARGIN, "Gross margin",
             MetricCategory.PROFITABILITY, AppliesTo.CORPORATE,
             "gross_profit / net_revenue",
             (MetricId.GROSS_PROFIT, MetricId.NET_REVENUE)),
    _derived(MetricId.NET_MARGIN, "Net margin", MetricCategory.PROFITABILITY,
             AppliesTo.CORPORATE, "net_income / net_revenue",
             (MetricId.NET_INCOME, MetricId.NET_REVENUE)),
    _derived(MetricId.LIABILITIES_TO_EQUITY, "Liabilities to equity",
             MetricCategory.LEVERAGE, AppliesTo.BOTH,
             "total_liabilities / owners_equity",
             (MetricId.TOTAL_LIABILITIES, MetricId.OWNERS_EQUITY)),
    _derived(MetricId.CASH_TO_ASSETS, "Cash to assets",
             MetricCategory.LIQUIDITY, AppliesTo.CORPORATE,
             "cash_and_equivalents / total_assets",
             (MetricId.CASH_AND_EQUIVALENTS, MetricId.TOTAL_ASSETS)),
    _derived(MetricId.OPERATING_CASH_FLOW_MARGIN, "Operating cash flow margin",
             MetricCategory.CASHFLOW, AppliesTo.CORPORATE,
             "operating_cash_flow / net_revenue",
             (MetricId.OPERATING_CASH_FLOW, MetricId.NET_REVENUE)),
)

#: Catalog indexed by ``MetricId.value`` for O(1) ``explain_metric`` lookups.
_CATALOG_BY_ID: dict[str, MetricDefinition] = {d.id.value: d for d in _V1_CATALOG}


# --------------------------------------------------------------------------- #
# Public offline query functions (zero network).
# --------------------------------------------------------------------------- #
def _coerce_applies_to(applies_to) -> Optional[AppliesTo]:
    """Coerce the ``metric_catalog`` filter to ``AppliesTo`` or ``None``.

    ``None`` -> no filter. ``"non_bank"`` is an alias for ``CORPORATE``. Any
    other string raises :class:`VnfinError`.
    """
    if applies_to is None:
        return None
    if isinstance(applies_to, AppliesTo):
        return applies_to
    text = str(applies_to).strip().lower()
    if text == "non_bank":
        return AppliesTo.CORPORATE
    try:
        return AppliesTo(text)
    except ValueError as exc:
        valid = ", ".join(a.value for a in AppliesTo) + ", non_bank"
        raise VnfinError(
            f"unknown applies_to {applies_to!r}; expected one of: {valid}"
        ) from exc


def metric_catalog(
    applies_to: "AppliesTo | str | None" = None,
) -> tuple[MetricDefinition, ...]:
    """Return the immutable v1 metric catalog (optionally filtered).

    ``applies_to`` (B5): ``None`` -> the full catalog; ``"bank"``/
    ``AppliesTo.BANK`` -> ``BANK`` + ``BOTH``; ``"corporate"``/``"non_bank"``/
    ``AppliesTo.CORPORATE`` -> ``CORPORATE`` + ``BOTH`` (``BOTH`` is always
    included for an entity-typed filter). Any other string raises
    :class:`VnfinError`. Fully offline — no network.
    """
    want = _coerce_applies_to(applies_to)
    if want is None:
        return _V1_CATALOG
    return tuple(
        d
        for d in _V1_CATALOG
        if d.applies_to is AppliesTo.BOTH or d.applies_to is want
    )


def explain_metric(metric_id: "MetricId | str") -> MetricDefinition:
    """Return the :class:`MetricDefinition` for ``metric_id``.

    Accepts a :class:`MetricId` or its string value. An unknown id (including a
    v2-deferred metric absent from the v1 catalog) raises :class:`VnfinError`.
    Fully offline — no network.
    """
    key = metric_id.value if isinstance(metric_id, MetricId) else str(metric_id)
    defn = _CATALOG_BY_ID.get(key)
    if defn is None:
        raise VnfinError(f"unknown metric id {metric_id!r}")
    return defn
