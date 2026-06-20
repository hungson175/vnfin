"""Typed data model for the vnfin canonical-metrics layer (#157).

An **additive, offline** layer on top of the existing ``vnfin.fundamentals``
reports: stable canonical metric ids + definitions, per-value lineage,
per-statement provenance, and coverage diagnostics. Clean-room — no VNStock,
no new external source; it transforms the typed ``FinancialReport``s that
``get_financials()`` already produces (see ``docs/design/fundamentals-metrics.md``).

This module holds ONLY the data contracts (enums + frozen dataclasses). The
static catalog and the query/transform functions live in
``vnfin/fundamentals/metric_api.py`` (deliberately NOT ``metrics.py``, which
would shadow the ``fundamentals.metrics`` function attribute — B5).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Mapping, Optional

from .models import Period, StatementType

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


# --------------------------------------------------------------------------- #
# Enums — EXACT .value strings (tests + the public-API snapshot bind to these;
# DataFrame enum columns serialize the .value). B4.
# --------------------------------------------------------------------------- #
class MetricId(str, Enum):
    """Stable canonical metric ids. The ``.value`` is the lower_snake of the
    member name and is the SOLE identity surface (never a provider human label).
    """

    # raw_mapped — corporate-only ----------------------------------------- #
    NET_REVENUE = "net_revenue"
    GROSS_PROFIT = "gross_profit"
    OPERATING_PROFIT = "operating_profit"
    NET_INCOME_PARENT = "net_income_parent"
    CASH_AND_EQUIVALENTS = "cash_and_equivalents"
    CURRENT_ASSETS = "current_assets"
    CURRENT_LIABILITIES = "current_liabilities"
    LONG_TERM_LIABILITIES = "long_term_liabilities"
    OPERATING_CASH_FLOW = "operating_cash_flow"
    INVESTING_CASH_FLOW = "investing_cash_flow"
    FINANCING_CASH_FLOW = "financing_cash_flow"
    NET_CASH_FLOW = "net_cash_flow"
    CASH_END_OF_PERIOD = "cash_end_of_period"
    # raw_mapped — shared (BOTH) ------------------------------------------ #
    PROFIT_BEFORE_TAX = "profit_before_tax"
    NET_INCOME = "net_income"
    TOTAL_ASSETS = "total_assets"
    TOTAL_LIABILITIES = "total_liabilities"
    OWNERS_EQUITY = "owners_equity"
    # raw_mapped — bank-only ---------------------------------------------- #
    NET_INTEREST_INCOME = "net_interest_income"
    LOANS_TO_CUSTOMERS = "loans_to_customers"
    CUSTOMER_DEPOSITS = "customer_deposits"
    # derived ------------------------------------------------------------- #
    GROSS_MARGIN = "gross_margin"
    NET_MARGIN = "net_margin"
    LIABILITIES_TO_EQUITY = "liabilities_to_equity"
    CASH_TO_ASSETS = "cash_to_assets"
    OPERATING_CASH_FLOW_MARGIN = "operating_cash_flow_margin"


class MetricCategory(str, Enum):
    """Coarse grouping for catalog browsing / DataFrame display."""

    PROFITABILITY = "profitability"
    LIQUIDITY = "liquidity"
    LEVERAGE = "leverage"
    CASHFLOW = "cashflow"
    SIZE = "size"


class MetricKind(str, Enum):
    """How a metric value is produced."""

    RAW_MAPPED = "raw_mapped"
    PROVIDER_NATIVE = "provider_native"
    DERIVED = "derived"


class AppliesTo(str, Enum):
    """Which entity taxonomy a metric is defined for."""

    CORPORATE = "corporate"
    BANK = "bank"
    BOTH = "both"


class MetricAvailability(str, Enum):
    """Per-value availability outcome.

    ``NOT_APPLICABLE`` is the bank/non-bank applicability outcome (there is no
    ``UNAPPLICABLE``). ``UNSUPPORTED`` is reserved for v2 valuation metrics
    absent from the v1 catalog.
    """

    AVAILABLE = "available"
    MISSING = "missing"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"
    UNSUPPORTED = "unsupported"


class StatementCoverageStatus(str, Enum):
    """Per-statement fetch outcome for one fiscal period."""

    OK = "ok"
    MISSING = "missing"
    SOURCE_ERROR = "source_error"
    NOT_SERVED = "not_served"


class RatioCoverageStatus(str, Enum):
    """Ratio-fetch status. v1 never fetches ratios -> always ``NOT_REQUESTED``."""

    NOT_REQUESTED = "not_requested"  # v1 only; extends when ratios ship


# --------------------------------------------------------------------------- #
# Frozen dataclasses — exact field names per §4 (tests bind to field order).
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MetricSourceCodes:
    """Item codes for ONE source namespace (B3 — no cross-namespace mixing).

    ``corporate_code``/``bank_code`` are the VNDirect numeric codes for the
    corporate vs bank statement template. A CafeF string code can never sit in a
    VNDirect slot because each source gets its own ``MetricSourceCodes`` keyed in
    ``MetricDefinition.codes_by_source``.
    """

    corporate_code: Optional[str] = None
    bank_code: Optional[str] = None


@dataclass(frozen=True)
class MetricInput:
    """One source line a metric value was built from (lineage).

    ``name`` is the raw ``LineItem.name`` PROVENANCE (e.g. "Doanh thu thuần" or
    the clean-room ``item_<code>`` fallback) — provenance-only, NEVER used for
    metric identity (identity = statement + source namespace + item code).
    """

    statement: StatementType
    item_code: str
    value: float
    value_unit: str
    fiscal_date: date
    source: str
    name: str


@dataclass(frozen=True)
class MetricDefinition:
    """Static catalog entry (no symbol).

    ``codes_by_source`` is EXPLICITLY namespaced by source (B3). v1 ships ONLY
    the ``"vndirect"`` key; v1.x adds ``"cafef"``. Derived metrics carry a human
    ``formula`` and their ``inputs`` (dependency metric ids); raw_mapped metrics
    carry ``statement`` + ``codes_by_source`` instead.
    """

    id: MetricId
    name: str
    category: MetricCategory
    kind: MetricKind
    applies_to: AppliesTo
    value_unit: str
    statement: Optional[StatementType] = None
    codes_by_source: Mapping[str, MetricSourceCodes] = field(default_factory=dict)
    formula: Optional[str] = None
    inputs: tuple[MetricId, ...] = ()


@dataclass(frozen=True)
class MetricValue:
    """One metric's resolved value for one symbol + one fiscal period.

    ``value`` is ``None`` whenever ``availability != AVAILABLE``; ``reason`` then
    carries the exact stable diagnostic string (see the design §5 reason table).
    """

    id: MetricId
    value: Optional[float]
    value_unit: str
    kind: MetricKind
    availability: MetricAvailability
    fiscal_date: date
    inputs: tuple[MetricInput, ...]
    reason: Optional[str] = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class StatementProvenance:
    """Per-statement outcome for one fiscal period.

    ``source`` follows the role rule (B2): OK -> the succeeding source;
    NOT_SERVED -> the responsible (non-serving) source (e.g. "cafef" for
    cashflow); SOURCE_ERROR/MISSING -> ``None``. There is NO failed-attempt
    trail in v1 (C1).
    """

    statement: StatementType
    status: StatementCoverageStatus
    source: Optional[str]
    detail: Optional[str] = None


@dataclass(frozen=True)
class MetricReport:
    """All metrics for one symbol + one fiscal period.

    Carries PER-STATEMENT provenance (``statement_sources``) rather than a
    single report ``source`` (C2 — income/balance/cashflow can resolve to
    different sources; cashflow is VNDirect-only). Per-value lineage lives on
    ``MetricValue.inputs[].source``.
    """

    symbol: str
    period: Period
    fiscal_date: date
    is_bank: bool
    metrics: tuple[MetricValue, ...]
    statement_sources: tuple[StatementProvenance, ...]
    warnings: tuple[str, ...] = ()

    def get(self, metric_id) -> Optional[MetricValue]:
        """Return the ``MetricValue`` for ``metric_id`` (even when unavailable).

        B6: every report carries a value for every v1 catalog metric, so this
        returns a value (possibly ``MISSING``/``BLOCKED``/``NOT_APPLICABLE``)
        for any known id, and ``None`` only for an id absent from the catalog.
        """
        key = metric_id.value if isinstance(metric_id, MetricId) else str(metric_id)
        for mv in self.metrics:
            if mv.id.value == key:
                return mv
        return None

    def to_dataframe(self) -> "pd.DataFrame":  # pragma: no cover - stage C
        """One row per metric (implemented in stage C)."""
        raise NotImplementedError("MetricReport.to_dataframe ships in stage C")


@dataclass(frozen=True)
class MetricCoverageItem:
    """One metric's availability + reason at one fiscal date (B3 — typed record,
    not a bare tuple)."""

    metric_id: MetricId
    availability: MetricAvailability
    fiscal_date: date
    reason: Optional[str] = None


@dataclass(frozen=True)
class PeriodCoverage:
    """Coverage diagnostics for ONE fiscal date (B1 — coverage is per period)."""

    fiscal_date: date
    is_bank: Optional[bool]
    statement_provenance: tuple[StatementProvenance, ...]
    per_metric: tuple[MetricCoverageItem, ...]
    named_item_count: int
    generic_item_count: int
    unmapped_codes: tuple[str, ...]
    ratio_status: RatioCoverageStatus = RatioCoverageStatus.NOT_REQUESTED


@dataclass(frozen=True)
class MetricCoverage:
    """Offline-friendly, non-fatal diagnosis for a symbol over the fetched
    periods (newest first)."""

    symbol: str
    period: Period
    periods: tuple[PeriodCoverage, ...]
    notes: tuple[str, ...] = ()
