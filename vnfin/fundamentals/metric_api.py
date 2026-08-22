"""Canonical-metrics query API + static v1 catalog (#157).

STAGE A surface: the immutable v1 metric catalog, the static ``serves(...)``
capability predicate, and the two fully-offline query functions
``metric_catalog`` / ``explain_metric``. The metrics wrappers and pure
transformers use the same typed fundamentals reports and remain source-gap
bounded: no new provider capability is implied by this module.

Module is ``metric_api`` (NOT ``metrics``) so the ``fundamentals.metrics``
function attribute is not shadowed by a submodule (B5). It is built only on
the existing fundamentals codes and does not add a provider source.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Optional

from .._contracts import canonical_security_symbol
from ..exceptions import AllSourcesFailed, EmptyData, SourceError, VnfinError
from .base import AUTO, is_known_bank
from .models import (
    FinancialReport,
    LineItem,
    Period,
    StatementType,
    _coerce_period,
    _coerce_statement,
)
from .metric_models import (
    AppliesTo,
    MetricAvailability,
    MetricCategory,
    MetricCoverage,
    MetricCoverageItem,
    MetricDefinition,
    MetricId,
    MetricInput,
    MetricKind,
    MetricReport,
    MetricSourceCodes,
    MetricValue,
    PeriodCoverage,
    RatioCoverageStatus,
    StatementCoverageStatus,
    StatementProvenance,
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
    if not isinstance(source_name, str):
        return False
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
    # Corporate codes hard-remapped to the live-probe-verified namespace (#198);
    # every code is identity- + official-filing-cross-checked (see
    # docs/design/corporate-itemcodes-probe-20260720.md). Bank codes unchanged.
    _raw(MetricId.NET_REVENUE, "Net revenue", MetricCategory.SIZE,
         AppliesTo.CORPORATE, StatementType.INCOME, corporate_code="21001"),
    _raw(MetricId.GROSS_PROFIT, "Gross profit", MetricCategory.PROFITABILITY,
         AppliesTo.CORPORATE, StatementType.INCOME, corporate_code="23100"),
    # OPERATING_PROFIT has NO verified corporate code (#198 §5): ships
    # corporate_code=None -> honest BLOCKED via the unmapped-code contract,
    # never a guessed mapping.
    _raw(MetricId.OPERATING_PROFIT, "Operating profit",
         MetricCategory.PROFITABILITY, AppliesTo.CORPORATE,
         StatementType.INCOME, corporate_code=None),
    _raw(MetricId.NET_INCOME_PARENT, "Net income (parent)",
         MetricCategory.PROFITABILITY, AppliesTo.CORPORATE,
         StatementType.INCOME, corporate_code="23000"),
    _raw(MetricId.CASH_AND_EQUIVALENTS, "Cash and equivalents",
         MetricCategory.LIQUIDITY, AppliesTo.CORPORATE,
         StatementType.BALANCE, corporate_code="11100"),
    _raw(MetricId.CURRENT_ASSETS, "Current assets", MetricCategory.LIQUIDITY,
         AppliesTo.CORPORATE, StatementType.BALANCE, corporate_code="11000"),
    _raw(MetricId.CURRENT_LIABILITIES, "Current liabilities",
         MetricCategory.LEVERAGE, AppliesTo.CORPORATE,
         StatementType.BALANCE, corporate_code="13100"),
    _raw(MetricId.LONG_TERM_LIABILITIES, "Long-term liabilities",
         MetricCategory.LEVERAGE, AppliesTo.CORPORATE,
         StatementType.BALANCE, corporate_code="13300"),
    _raw(MetricId.OPERATING_CASH_FLOW, "Operating cash flow",
         MetricCategory.CASHFLOW, AppliesTo.CORPORATE,
         StatementType.CASHFLOW, corporate_code="32000"),
    _raw(MetricId.INVESTING_CASH_FLOW, "Investing cash flow",
         MetricCategory.CASHFLOW, AppliesTo.CORPORATE,
         StatementType.CASHFLOW, corporate_code="33000"),
    _raw(MetricId.FINANCING_CASH_FLOW, "Financing cash flow",
         MetricCategory.CASHFLOW, AppliesTo.CORPORATE,
         StatementType.CASHFLOW, corporate_code="34000"),
    _raw(MetricId.NET_CASH_FLOW, "Net cash flow", MetricCategory.CASHFLOW,
         AppliesTo.CORPORATE, StatementType.CASHFLOW, corporate_code="35000"),
    _raw(MetricId.CASH_END_OF_PERIOD, "Cash at end of period",
         MetricCategory.CASHFLOW, AppliesTo.CORPORATE,
         StatementType.CASHFLOW, corporate_code="37000"),
    # ---- raw_mapped: shared (BOTH) — corporate_code + bank_code --------- #
    _raw(MetricId.PROFIT_BEFORE_TAX, "Profit before tax",
         MetricCategory.PROFITABILITY, AppliesTo.BOTH, StatementType.INCOME,
         corporate_code="23800", bank_code="23800"),
    _raw(MetricId.NET_INCOME, "Net income", MetricCategory.PROFITABILITY,
         AppliesTo.BOTH, StatementType.INCOME,
         corporate_code="23003", bank_code="23000"),
    _raw(MetricId.TOTAL_ASSETS, "Total assets", MetricCategory.SIZE,
         AppliesTo.BOTH, StatementType.BALANCE,
         corporate_code="12700", bank_code="12700"),
    _raw(MetricId.TOTAL_LIABILITIES, "Total liabilities",
         MetricCategory.LEVERAGE, AppliesTo.BOTH, StatementType.BALANCE,
         corporate_code="13000", bank_code="13000"),
    _raw(MetricId.OWNERS_EQUITY, "Owners' equity", MetricCategory.SIZE,
         AppliesTo.BOTH, StatementType.BALANCE,
         corporate_code="14000", bank_code="14000"),
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


# =========================================================================== #
# STAGE B — the pure HTTP-free core.
#
# ``StatementFetchResult`` is the typed seam the network wrappers
# produce per statement; the two pure transformers consume a tuple of them and
# emit ``MetricReport``s / ``MetricCoverage`` with NO network. All reason strings
# are EXACT, stable constants (the design §5 reason table; tests bind verbatim).
# =========================================================================== #
@dataclass(frozen=True)
class StatementFetchResult:
    """One per-statement fetch outcome (B1/B2).

    ``reports`` is empty (``()``) when the fetch failed / was not served. The
    ``source`` role follows the bounded design rule: OK -> the succeeding
    canonical source; NOT_SERVED -> the responsible canonical source/composite
    (e.g. ``"cafef"`` for cashflow); SOURCE_ERROR/MISSING -> ``None``.
    ``detail`` is bounded: SOURCE_ERROR uses the trail-free public constant and
    direct MISSING uses the normalized cadence detail. This carries SUCCESS and
    FAILURE so the pure transformers can encode both without hidden wrapper
    logic.
    """

    statement: StatementType
    reports: tuple[FinancialReport, ...]
    status: StatementCoverageStatus
    source: Optional[str]
    detail: Optional[str] = None


# --------------------------------------------------------------------------- #
# Exact reason-string constants (design §5 / brief §D). ``{...}`` placeholders
# are substituted via ``str.format``; tests bind these verbatim. Interpolation:
# {statement}=StatementType.value, {input_id}/{id}=MetricId.value,
# {availability}=MetricAvailability.value, {fiscal_date}=date.isoformat(),
# {source}=name, {code}=item-code str, {value}=repr(float), {entity}=bank|non-bank.
# --------------------------------------------------------------------------- #
REASON_SOURCE_NOT_MAPPED = "metric map not available for source '{source}'"
REASON_STATEMENT_MISSING = "missing statement {statement} for {fiscal_date}"
REASON_STATEMENT_UNAVAILABLE = "statement {statement} unavailable: {detail}"
REASON_STATEMENT_NOT_SERVED = (
    "statement {statement} not served by source '{source}'"
)
REASON_MISSING_LINE_ITEM = "missing line item {code} in {statement}"
REASON_METRIC_CODE_UNMAPPED = (
    "metric '{id}' has no verified code for source '{source}' and {entity} entities"
)
REASON_NOT_APPLICABLE = (
    "metric '{id}' does not apply to {entity} entities"
)
REASON_DERIVED_INPUT_MISSING = "missing input metric {input_id}"
REASON_DERIVED_INPUT_BLOCKED = "input metric {input_id} is {availability}"
REASON_DENOMINATOR_ZERO = "denominator {input_id} is zero"
REASON_DENOMINATOR_NEGATIVE = "denominator {input_id} is negative ({value})"
REASON_DENOMINATOR_NOT_FINITE = "denominator {input_id} is not finite"

#: The only source namespace the v1 catalog maps (C3).
_MAPPED_SOURCE = "vndirect"

#: Statements the metrics layer consumes (NEVER ratios — B7).
_METRIC_STATEMENTS = (
    StatementType.INCOME,
    StatementType.BALANCE,
    StatementType.CASHFLOW,
)

# Public diagnostics are deliberately allow-listed.  Provider exception text,
# response bodies, URLs, and failed-attempt trails never cross this boundary.
_PUBLIC_SOURCE_ERROR_DETAIL = "recoverable source error"
_CUSTOM_ROLE = "custom"
_CANONICAL_ROLES = frozenset({"vndirect", "cafef", _CUSTOM_ROLE})
_EMPTY_METRICS_MESSAGE = (
    "no usable {cadence} fiscal periods for symbol '{symbol}'; "
    "call explain_metric_coverage()"
)


def _entity_label(is_bank: bool) -> str:
    return "bank" if is_bank else "non-bank"


def _applies(defn: MetricDefinition, is_bank: bool) -> bool:
    """Whether ``defn`` applies to the resolved entity type."""
    if defn.applies_to is AppliesTo.BOTH:
        return True
    if is_bank:
        return defn.applies_to is AppliesTo.BANK
    return defn.applies_to is AppliesTo.CORPORATE


def _code_for(defn: MetricDefinition, source: str, is_bank: bool) -> Optional[str]:
    """The item code for ``defn`` under ``source`` for the entity type, or None."""
    codes = defn.codes_by_source.get(source)
    if codes is None:
        return None
    return codes.bank_code if is_bank else codes.corporate_code


def _union_fiscal_dates(
    results: tuple[StatementFetchResult, ...], limit: int
) -> tuple[date, ...]:
    """Union of fiscal_dates across OK results, newest-first, capped AFTER union."""
    seen: set[date] = set()
    for r in results:
        if r.status is StatementCoverageStatus.OK:
            for rep in r.reports:
                seen.add(rep.fiscal_date)
    ordered = sorted(seen, reverse=True)
    if limit is not None and limit >= 0:
        ordered = ordered[:limit]
    return tuple(ordered)


def _provenance_for_date(
    result: StatementFetchResult, fiscal_date: date
) -> StatementProvenance:
    """Per-statement provenance at one fiscal_date (brief §D).

    OK with a report at this date -> OK/source; OK without -> MISSING/None;
    SOURCE_ERROR -> SOURCE_ERROR/None/detail; NOT_SERVED -> NOT_SERVED/source.
    """
    st = result.statement
    if result.status is StatementCoverageStatus.OK:
        for rep in result.reports:
            if rep.fiscal_date == fiscal_date:
                source = _safe_atomic_role(_safe_report_source(rep))
                if source is None:
                    return StatementProvenance(
                        statement=st,
                        status=StatementCoverageStatus.SOURCE_ERROR,
                        source=None,
                        detail=_PUBLIC_SOURCE_ERROR_DETAIL,
                    )
                return StatementProvenance(
                    statement=st,
                    status=StatementCoverageStatus.OK,
                    source=source,
                )
        return StatementProvenance(
            statement=st, status=StatementCoverageStatus.MISSING, source=None
        )
    if result.status is StatementCoverageStatus.SOURCE_ERROR:
        return StatementProvenance(
            statement=st,
            status=StatementCoverageStatus.SOURCE_ERROR,
            source=None,
            detail=_PUBLIC_SOURCE_ERROR_DETAIL,
        )
    if result.status is StatementCoverageStatus.NOT_SERVED:
        source = _safe_not_served_source(result.source)
        return StatementProvenance(
            statement=st,
            status=StatementCoverageStatus.NOT_SERVED,
            source=source,
            detail=f"statement {st.value} not served by source '{source}'",
        )
    # A bare MISSING result (no reports) — treat as missing this date.
    return StatementProvenance(
        statement=st,
        status=StatementCoverageStatus.MISSING,
        source=None,
        detail=(
            result.detail
            if isinstance(result.detail, str)
            and result.detail.startswith("no usable ")
            and result.detail.endswith(" fiscal periods")
            else None
        ),
    )


def _report_at(
    result: StatementFetchResult, fiscal_date: date
) -> Optional[FinancialReport]:
    if result.status is not StatementCoverageStatus.OK:
        return None
    for rep in result.reports:
        if rep.fiscal_date == fiscal_date:
            return rep
    return None


def _resolve_raw(
    defn: MetricDefinition,
    is_bank: bool,
    fiscal_date: date,
    result: StatementFetchResult,
    report: Optional[FinancialReport],
    prov: StatementProvenance,
) -> MetricValue:
    """Resolve one raw_mapped metric for one fiscal period (design §5 order)."""
    st = defn.statement
    st_value = st.value if st is not None else ""
    # 1. applies_to mismatch.
    if not _applies(defn, is_bank):
        return _unavailable(
            defn,
            MetricAvailability.NOT_APPLICABLE,
            fiscal_date,
            REASON_NOT_APPLICABLE.format(
                id=defn.id.value, entity=_entity_label(is_bank)
            ),
        )
    # 2. statement-level outcomes (no usable report this date).
    if prov.status is StatementCoverageStatus.MISSING:
        return _unavailable(
            defn,
            MetricAvailability.MISSING,
            fiscal_date,
            REASON_STATEMENT_MISSING.format(
                statement=st_value, fiscal_date=fiscal_date.isoformat()
            ),
        )
    if prov.status is StatementCoverageStatus.SOURCE_ERROR:
        return _unavailable(
            defn,
            MetricAvailability.MISSING,
            fiscal_date,
            REASON_STATEMENT_UNAVAILABLE.format(
                statement=st_value, detail=prov.detail
            ),
        )
    if prov.status is StatementCoverageStatus.NOT_SERVED:
        return _unavailable(
            defn,
            MetricAvailability.MISSING,
            fiscal_date,
            REASON_STATEMENT_NOT_SERVED.format(
                statement=st_value, source=prov.source
            ),
        )
    # 3. source-namespace gate (C3): the succeeding source must be mapped.
    source = prov.source
    if source != _MAPPED_SOURCE or defn.codes_by_source.get(source) is None:
        return _unavailable(
            defn,
            MetricAvailability.BLOCKED,
            fiscal_date,
            REASON_SOURCE_NOT_MAPPED.format(source=source),
        )
    # 4. look the code up in the report's code -> LineItem index (B8 — from the
    #    full LineItem object, never via FinancialReport.get() which is float-only).
    #    Split the two failure modes (#198 §5): no verified code for this entity
    #    type is an honest BLOCKED (the statement exists; the library lacks a
    #    mapping), NOT a false MISSING claiming the provider omitted a line.
    code = _code_for(defn, source, is_bank)
    if code is None:
        return _unavailable(
            defn,
            MetricAvailability.BLOCKED,
            fiscal_date,
            REASON_METRIC_CODE_UNMAPPED.format(
                id=defn.id.value,
                source=source,
                entity=("bank" if is_bank else "corporate"),
            ),
        )
    line: Optional[LineItem] = None
    for li in report.items:
        if li.item_code == code:
            line = li
            break
    if line is None:  # code IS mapped but genuinely absent upstream
        return _unavailable(
            defn,
            MetricAvailability.MISSING,
            fiscal_date,
            REASON_MISSING_LINE_ITEM.format(code=code, statement=st_value),
        )
    # 5. AVAILABLE — build lineage from the full LineItem (B8, not via .get()).
    #    No local finiteness guard on line.value: every LineItem.value is already
    #    finite because coerce.parse_provider_float rejects inf/NaN at the parser
    #    boundary (preserve that invariant if the parser boundary is refactored).
    mi = MetricInput(
        statement=st,
        item_code=code,
        value=float(line.value),
        value_unit=line.value_unit if line.value_unit is not None else defn.value_unit,
        fiscal_date=fiscal_date,
        source=source,
        name=line.name,
    )
    return MetricValue(
        id=defn.id,
        value=float(line.value),
        value_unit=defn.value_unit,
        kind=defn.kind,
        availability=MetricAvailability.AVAILABLE,
        fiscal_date=fiscal_date,
        inputs=(mi,),
    )


def _resolve_derived(
    defn: MetricDefinition,
    is_bank: bool,
    fiscal_date: date,
    resolved: dict[str, MetricValue],
) -> MetricValue:
    """Resolve one derived metric from already-resolved inputs (design §5)."""
    # 1. applies_to mismatch.
    if not _applies(defn, is_bank):
        return _unavailable(
            defn,
            MetricAvailability.NOT_APPLICABLE,
            fiscal_date,
            REASON_NOT_APPLICABLE.format(
                id=defn.id.value, entity=_entity_label(is_bank)
            ),
        )
    inputs = [resolved[i.value] for i in defn.inputs]
    # 2. an input BLOCKED / NOT_APPLICABLE -> BLOCKED (names the first such).
    for iv in inputs:
        if iv.availability in (
            MetricAvailability.BLOCKED,
            MetricAvailability.NOT_APPLICABLE,
        ):
            return _unavailable(
                defn,
                MetricAvailability.BLOCKED,
                fiscal_date,
                REASON_DERIVED_INPUT_BLOCKED.format(
                    input_id=iv.id.value, availability=iv.availability.value
                ),
            )
    # 3. an input MISSING -> MISSING (names the first such).
    for iv in inputs:
        if iv.availability is not MetricAvailability.AVAILABLE:
            return _unavailable(
                defn,
                MetricAvailability.MISSING,
                fiscal_date,
                REASON_DERIVED_INPUT_MISSING.format(input_id=iv.id.value),
            )
    # 4. denominator guards (all v1 formulas are inputs[0] / inputs[1]).
    numerator = inputs[0]
    denominator = inputs[1]
    den = float(denominator.value)
    if not math.isfinite(den):
        return _unavailable(
            defn,
            MetricAvailability.MISSING,
            fiscal_date,
            REASON_DENOMINATOR_NOT_FINITE.format(input_id=denominator.id.value),
        )
    if den == 0.0:
        return _unavailable(
            defn,
            MetricAvailability.MISSING,
            fiscal_date,
            REASON_DENOMINATOR_ZERO.format(input_id=denominator.id.value),
        )
    if den < 0.0:
        return _unavailable(
            defn,
            MetricAvailability.MISSING,
            fiscal_date,
            REASON_DENOMINATOR_NEGATIVE.format(
                input_id=denominator.id.value, value=repr(den)
            ),
        )
    value = float(numerator.value) / den
    # AVAILABLE derived must never be inf / NaN. Unreachable in practice: the
    # upstream parser (coerce.parse_provider_float) rejects a non-finite numerator
    # AND denominator before they reach a LineItem.value, and the denom guards
    # above cover zero/negative — so this branch is purely defensive.
    if not math.isfinite(value):  # pragma: no cover - defensive
        return _unavailable(
            defn,
            MetricAvailability.MISSING,
            fiscal_date,
            REASON_DENOMINATOR_NOT_FINITE.format(input_id=denominator.id.value),
        )
    # lineage = the inputs' lineage (carry the raw lines used).
    lineage: tuple[MetricInput, ...] = tuple(
        mi for iv in inputs for mi in iv.inputs
    )
    # mixed_source: inputs span >1 source.
    src = {mi.source for mi in lineage}
    warnings = ("mixed_source",) if len(src) > 1 else ()
    return MetricValue(
        id=defn.id,
        value=value,
        value_unit=defn.value_unit,
        kind=defn.kind,
        availability=MetricAvailability.AVAILABLE,
        fiscal_date=fiscal_date,
        inputs=lineage,
        warnings=warnings,
    )


def _unavailable(
    defn: MetricDefinition,
    availability: MetricAvailability,
    fiscal_date: date,
    reason: str,
) -> MetricValue:
    """A MetricValue with no value carrying the exact stable reason."""
    return MetricValue(
        id=defn.id,
        value=None,
        value_unit=defn.value_unit,
        kind=defn.kind,
        availability=availability,
        fiscal_date=fiscal_date,
        inputs=(),
        reason=reason,
    )


def _build_report(
    symbol: str,
    period: Period,
    is_bank: bool,
    fiscal_date: date,
    results: tuple[StatementFetchResult, ...],
) -> MetricReport:
    """Build one MetricReport (full catalog) for one fiscal period."""
    by_statement = {r.statement: r for r in results}
    prov_by_statement: dict[StatementType, StatementProvenance] = {}
    statement_sources: list[StatementProvenance] = []
    for st in _METRIC_STATEMENTS:
        r = by_statement.get(st)
        if r is None:
            prov = StatementProvenance(
                statement=st, status=StatementCoverageStatus.MISSING, source=None
            )
        else:
            prov = _provenance_for_date(r, fiscal_date)
        prov_by_statement[st] = prov
        statement_sources.append(prov)

    resolved: dict[str, MetricValue] = {}
    # raw_mapped first.
    for defn in _V1_CATALOG:
        if defn.kind is not MetricKind.RAW_MAPPED:
            continue
        st = defn.statement
        r = by_statement.get(st)
        prov = prov_by_statement[st]
        report = _report_at(r, fiscal_date) if r is not None else None
        resolved[defn.id.value] = _resolve_raw(
            defn, is_bank, fiscal_date, r, report, prov
        )
    # derived from resolved raw values.
    for defn in _V1_CATALOG:
        if defn.kind is not MetricKind.DERIVED:
            continue
        resolved[defn.id.value] = _resolve_derived(
            defn, is_bank, fiscal_date, resolved
        )

    # preserve catalog order; collect report-level warnings.
    metrics = tuple(resolved[d.id.value] for d in _V1_CATALOG)
    report_warnings: tuple[str, ...] = (
        ("mixed_source",)
        if any("mixed_source" in mv.warnings for mv in metrics)
        else ()
    )
    return MetricReport(
        symbol=symbol,
        period=period,
        fiscal_date=fiscal_date,
        is_bank=is_bank,
        metrics=metrics,
        statement_sources=tuple(statement_sources),
        warnings=report_warnings,
    )


def _metrics_from_statement_results(
    symbol: str,
    period: Period,
    is_bank: bool,
    results: tuple[StatementFetchResult, ...],
    limit: int,
) -> tuple[MetricReport, ...]:
    """PURE transformer: synthetic StatementFetchResults -> MetricReports.

    NO network. Aligns by the union of fiscal_dates across OK results
    (newest-first, capped to ``limit`` AFTER the union); every report carries a
    MetricValue for ALL v1 catalog metrics (availability, never omission).
    """
    dates = _union_fiscal_dates(results, limit)
    return tuple(
        _build_report(symbol, period, is_bank, d, results) for d in dates
    )


# --------------------------------------------------------------------------- #
# Coverage transformer.
# --------------------------------------------------------------------------- #
#: All item codes the v1 catalog maps (any source/entity slot) — for unmapped_codes.
_MAPPED_CODES: frozenset[str] = frozenset(
    c
    for d in _V1_CATALOG
    for codes in d.codes_by_source.values()
    for c in (codes.corporate_code, codes.bank_code)
    if c is not None
)


def _build_period_coverage(
    is_bank: bool,
    report: MetricReport,
    results: tuple[StatementFetchResult, ...],
) -> PeriodCoverage:
    """Coverage diagnostics for one fiscal period (from its MetricReport)."""
    fiscal_date = report.fiscal_date
    named = 0
    generic = 0
    unmapped: list[str] = []
    seen_codes: set[str] = set()
    for r in results:
        rep = _report_at(r, fiscal_date)
        if rep is None:
            continue
        for li in rep.items:
            if li.name == f"item_{li.item_code}":
                generic += 1
            else:
                named += 1
            if li.item_code not in _MAPPED_CODES and li.item_code not in seen_codes:
                seen_codes.add(li.item_code)
                unmapped.append(li.item_code)
    per_metric = tuple(
        MetricCoverageItem(
            metric_id=mv.id,
            availability=mv.availability,
            fiscal_date=fiscal_date,
            reason=mv.reason,
        )
        for mv in report.metrics
    )
    return PeriodCoverage(
        fiscal_date=fiscal_date,
        is_bank=is_bank,
        statement_provenance=report.statement_sources,
        per_metric=per_metric,
        named_item_count=named,
        generic_item_count=generic,
        unmapped_codes=tuple(unmapped),
        ratio_status=RatioCoverageStatus.NOT_REQUESTED,
    )


def _coverage_from_statement_results(
    symbol: str,
    period: Period,
    is_bank: bool,
    results: tuple[StatementFetchResult, ...],
    limit: int,
) -> MetricCoverage:
    """PURE transformer: synthetic StatementFetchResults -> MetricCoverage.

    NO network, does not raise on a recoverable per-statement source failure. One PeriodCoverage per
    fiscal_date (newest first); NEVER fetches/requires ratios (B7 —
    ratio_status is always NOT_REQUESTED).
    """
    reports = _metrics_from_statement_results(
        symbol, period, is_bank, results, limit
    )
    periods = tuple(
        _build_period_coverage(is_bank, rep, results) for rep in reports
    )
    by_statement = {result.statement: result for result in results}
    statement_fetches = tuple(
        _aggregate_statement_provenance(
            by_statement.get(
                statement,
                StatementFetchResult(
                    statement=statement,
                    reports=(),
                    status=StatementCoverageStatus.MISSING,
                    source=None,
                ),
            ),
            period,
        )
        for statement in _METRIC_STATEMENTS
    )
    notes = ("no_fiscal_periods",) if not periods else ()
    return MetricCoverage(
        symbol=symbol,
        period=period,
        periods=periods,
        notes=notes,
        statement_fetches=statement_fetches,
    )


# =========================================================================== #
# STAGE C — the thin network wrappers (the ONLY network seam in this module).
#
# ``metrics`` / ``explain_metric_coverage`` fetch each of income/balance/cashflow
# (NEVER ratios — B7) via the existing ``fundamentals.get_financials`` failover,
# turn each outcome into a typed ``StatementFetchResult`` (success OR recoverable
# failure — a recoverable per-statement error must not raise out), resolve the concrete
# ``is_bank`` template, then hand the 3 results to the PURE Stage-B transformers.
# A statement no resolved source can serve is gated OUT before any fetch via the
# static ``serves(...)`` predicate (deterministic, not exception-text
# classification).  Source names and returned provenance are normalized at this
# seam so malformed objects cannot leak into public diagnostics.
# =========================================================================== #
def _safe_source_role(source) -> str:
    """Return one bounded canonical role without reading arbitrary source text."""
    try:
        name = getattr(source, "name")
    except BaseException:
        return _CUSTOM_ROLE
    return _safe_atomic_role(name) or _CUSTOM_ROLE


def _safe_atomic_role(value) -> Optional[str]:
    """Return an allow-listed atomic role, never arbitrary caller text."""
    try:
        if type(value) is str and value in ("vndirect", "cafef"):
            return value
    except BaseException:
        pass
    return None


def _role_composite(roles) -> str:
    """Deduplicate canonical roles in configured order for NOT_SERVED."""
    ordered: list[str] = []
    for role in roles:
        if role not in _CANONICAL_ROLES:
            role = _CUSTOM_ROLE
        if role not in ordered:
            ordered.append(role)
    return ",".join(ordered) or _CUSTOM_ROLE


def _safe_not_served_source(value) -> str:
    """Keep a public NOT_SERVED source value inside the canonical role set."""
    if type(value) is not str:
        return _CUSTOM_ROLE
    parts = tuple(value.split(","))
    if not parts or any(part not in _CANONICAL_ROLES for part in parts):
        return _CUSTOM_ROLE
    return _role_composite(parts)


def _safe_report_source(report):
    """Read a returned provenance value without propagating hostile properties."""
    try:
        return getattr(report, "source")
    except BaseException:
        return None


def _reports_match_roles(reports, allowed_roles: tuple[str, ...]) -> bool:
    """Require one consistent producing canonical role for all reports."""
    observed: list[str] = []
    for report in reports:
        source_name = _safe_atomic_role(_safe_report_source(report))
        if source_name is None or source_name not in allowed_roles:
            return False
        if source_name not in observed:
            observed.append(source_name)
    return len(observed) == 1


def _validate_metric_reports(
    reports,
    *,
    symbol: str,
    statement: StatementType,
    period: Period,
    is_bank,
    source,
) -> bool:
    """Apply the complete fundamentals result contract at the metric seam.

    The top-level ``get_financials(source=...)`` compatibility branch returns a
    source result without constructing :class:`FailoverFundamentalClient`, so a
    metrics wrapper must not treat that branch as trusted.  Reuse the same
    private validator used by the failover client and discard its detailed
    reason; public metric diagnostics have one fixed source-error string.
    Duplicate fiscal dates are rejected by that shared result-level contract.
    """
    try:
        from .client import _fundamental_unit, _validate_fundamental_result

        declared_unit = _fundamental_unit(source)
        # Metrics consume raw VND statement money, not merely any homogeneous
        # unit accepted by the generic fundamentals client.  An undeclared unit
        # remains compatible for legacy injected doubles; an explicit non-VND
        # declaration fails closed before the report can be published.
        if declared_unit is not None and (
            type(declared_unit) is not str or declared_unit != "VND"
        ):
            return False
        chain_unit = "VND"
        reason = _validate_fundamental_result(
            reports,
            symbol=symbol,
            statement=statement,
            period=period,
            is_bank=is_bank,
            chain_unit=chain_unit,
        )
        if reason is not None:
            return False

    except BaseException:
        # Validation is a fail-closed trust boundary.  Never expose a custom
        # property/value exception or the validator's raw reason publicly.
        return False
    return True


def _source_error_result(statement: StatementType) -> StatementFetchResult:
    return StatementFetchResult(
        statement=statement,
        reports=(),
        status=StatementCoverageStatus.SOURCE_ERROR,
        source=None,
        detail=_PUBLIC_SOURCE_ERROR_DETAIL,
    )


def _missing_detail(period: Period) -> str:
    return f"no usable {period.value.lower()} fiscal periods"


def _effective_sources(source, sources, *, http_get, timeout):
    """Materialize the effective chain while preserving direct-source precedence."""
    if source is not None:
        return (source,), True
    if sources is not None:
        effective = tuple(sources)
    else:
        # Lazy import avoids the metric_api <-> fundamentals.__init__ cycle.
        from . import default_fundamental_sources

        effective = tuple(
            default_fundamental_sources(http_get=http_get, timeout=timeout)
        )
    if not effective:
        raise VnfinError("sources must contain at least one source")
    return effective, False


def _resolve_chain_names(source, sources) -> tuple[str, ...]:
    """Return bounded role names for compatibility with the old internal seam."""
    if source is not None:
        return (_safe_source_role(source),)
    if sources is not None:
        return tuple(_safe_source_role(s) for s in tuple(sources))
    return ("vndirect", "cafef")


def _fetch_statement_result(
    symbol: str,
    statement: StatementType,
    period: Period,
    effective_sources: tuple,
    *,
    direct_source: bool,
    is_bank,
    limit: int,
    max_attempts: int,
    http_get,
    timeout: float,
) -> StatementFetchResult:
    """Fetch one statement and classify it into a bounded typed result."""
    pairs = tuple((source, _safe_source_role(source)) for source in effective_sources)
    roles = tuple(role for _, role in pairs)
    capable = tuple((source, role) for source, role in pairs if serves(role, statement))
    if not capable:
        joined = _role_composite(roles)
        return StatementFetchResult(
            statement=statement,
            reports=(),
            status=StatementCoverageStatus.NOT_SERVED,
            source=joined,
            detail=f"statement {statement.value} not served by source '{joined}'",
        )

    # Lazy import avoids the metric_api <-> fundamentals.__init__ circular import.
    from . import get_financials

    capable_sources = tuple(source for source, _ in capable)
    allowed_roles = tuple(role for _, role in capable)
    try:
        if direct_source:
            reports = get_financials(
                symbol,
                statement,
                period,
                is_bank=is_bank,
                limit=limit,
                source=capable_sources[0],
                sources=None,
                max_attempts=max_attempts,
                http_get=http_get,
                timeout=timeout,
            )
        else:
            reports = get_financials(
                symbol,
                statement,
                period,
                is_bank=is_bank,
                limit=limit,
                source=None,
                sources=capable_sources,
                max_attempts=max_attempts,
                http_get=http_get,
                timeout=timeout,
            )
    except (SourceError, AllSourcesFailed):
        return _source_error_result(statement)

    try:
        reports = tuple(reports)
    except Exception:
        return _source_error_result(statement)

    if not reports:
        if direct_source:
            return StatementFetchResult(
                statement=statement,
                reports=(),
                status=StatementCoverageStatus.MISSING,
                source=None,
                detail=_missing_detail(period),
            )
        return _source_error_result(statement)

    if not _validate_metric_reports(
        reports,
        symbol=symbol,
        statement=statement,
        period=period,
        is_bank=is_bank,
        source=capable_sources[0],
    ):
        return _source_error_result(statement)

    if not _reports_match_roles(reports, allowed_roles):
        return _source_error_result(statement)

    succeeding = _safe_atomic_role(_safe_report_source(reports[0]))
    if succeeding is None:
        return _source_error_result(statement)
    return StatementFetchResult(
        statement=statement,
        reports=reports,
        status=StatementCoverageStatus.OK,
        source=succeeding,
    )


def _aggregate_statement_provenance(
    result: StatementFetchResult, period: Period
) -> StatementProvenance:
    """Map one logical result to its bounded aggregate public outcome."""
    if result.status is StatementCoverageStatus.SOURCE_ERROR:
        return StatementProvenance(
            statement=result.statement,
            status=StatementCoverageStatus.SOURCE_ERROR,
            source=None,
            detail=_PUBLIC_SOURCE_ERROR_DETAIL,
        )
    if result.status is StatementCoverageStatus.NOT_SERVED:
        source = _safe_not_served_source(result.source)
        return StatementProvenance(
            statement=result.statement,
            status=StatementCoverageStatus.NOT_SERVED,
            source=source,
            detail=f"statement {result.statement.value} not served by source '{source}'",
        )
    if result.status is StatementCoverageStatus.MISSING or not result.reports:
        return StatementProvenance(
            statement=result.statement,
            status=StatementCoverageStatus.MISSING,
            source=None,
            detail=_missing_detail(period),
        )
    source = _safe_atomic_role(result.source)
    if source is None or not _reports_match_roles(result.reports, (source,)):
        return StatementProvenance(
            statement=result.statement,
            status=StatementCoverageStatus.SOURCE_ERROR,
            source=None,
            detail=_PUBLIC_SOURCE_ERROR_DETAIL,
        )
    return StatementProvenance(
        statement=result.statement,
        status=StatementCoverageStatus.OK,
        source=source,
    )


def _fetch_all_statements(
    symbol: str,
    period: Period,
    *,
    is_bank,
    limit: int,
    source,
    sources,
    max_attempts: int,
    http_get,
    timeout: float,
) -> tuple[tuple[StatementFetchResult, ...], bool]:
    """Fan out exactly three logical statements with per-statement filtering."""
    effective_sources, direct_source = _effective_sources(
        source, sources, http_get=http_get, timeout=timeout
    )
    results = tuple(
        _fetch_statement_result(
            symbol,
            st,
            period,
            effective_sources,
            direct_source=direct_source,
            is_bank=is_bank,
            limit=limit,
            max_attempts=max_attempts,
            http_get=http_get,
            timeout=timeout,
        )
        for st in _METRIC_STATEMENTS
    )
    if is_bank is not None:
        resolved_is_bank = bool(is_bank)
    else:
        first_ok = next(
            (
                r
                for r in results
                if r.status is StatementCoverageStatus.OK and r.reports
            ),
            None,
        )
        if first_ok is not None:
            resolved_is_bank = bool(first_ok.reports[0].is_bank)
        else:
            resolved_is_bank = is_known_bank(symbol)
    return results, resolved_is_bank


def metrics(
    symbol: str,
    period="annual",
    *,
    is_bank: "bool | None" = AUTO,
    limit: int = 8,
    source=None,
    sources=None,
    max_attempts: int = 3,
    http_get=None,
    timeout: float = 25.0,
) -> tuple[MetricReport, ...]:
    """Canonical metrics for ``symbol``, newest fiscal period first.

    Fetches income+balance+cashflow ``FinancialReport``s (NEVER ratios — B7),
    each through the existing :func:`get_financials` failover, then transforms
    them OFFLINE into one :class:`MetricReport` per fiscal period (every report
    carries the FULL v1 catalog — applicability is expressed by ``availability``,
    never omission). Per-statement failures are non-fatal: a recoverable
    ``SourceError``/``AllSourcesFailed`` becomes a ``source_error`` statement and
    its metrics are ``MISSING`` rather than raising. Sources can differ per
    statement (CafeF does not serve cashflow), so provenance is PER STATEMENT
    (``MetricReport.statement_sources``) — there is no single report ``source``.

    If the three logical statements yield no usable fiscal date, raises the
    exact bounded :class:`EmptyData` message ``no usable {cadence} fiscal
    periods for symbol '{SYMBOL}'; call explain_metric_coverage()``. Source
    precedence is ``source=`` over ``sources=`` (including ``sources=[]``);
    only an empty effective chain with ``source is None`` raises the exact
    empty-chain :class:`VnfinError`. Incapable source roles are filtered before
    failover, malformed roles are zero-call ``custom``, and public source
    errors are sanitized to ``recoverable source error``.

    Mirrors :func:`get_financials`' injection knobs (``is_bank``/``limit``/
    ``source``/``sources``/``http_get``/``timeout``/``max_attempts``).
    """
    symbol = canonical_security_symbol(symbol, "symbol")
    pd = _coerce_period(period)
    results, resolved_is_bank = _fetch_all_statements(
        symbol,
        pd,
        is_bank=is_bank,
        limit=limit,
        source=source,
        sources=sources,
        max_attempts=max_attempts,
        http_get=http_get,
        timeout=timeout,
    )
    reports = _metrics_from_statement_results(
        symbol, pd, resolved_is_bank, results, limit
    )
    if not reports:
        raise EmptyData(
            _EMPTY_METRICS_MESSAGE.format(
                cadence=pd.value.lower(), symbol=symbol
            )
        )
    return reports


def explain_metric_coverage(
    symbol: str,
    period="annual",
    *,
    is_bank: "bool | None" = AUTO,
    limit: int = 8,
    source=None,
    sources=None,
    max_attempts: int = 3,
    http_get=None,
    timeout: float = 25.0,
) -> MetricCoverage:
    """Offline-friendly, NON-FATAL coverage diagnostics for ``symbol``.

    Same 3-statement fetch as :func:`metrics` (NEVER ratios — B7,
    ``ratio_status`` is always ``not_requested``), but does not raise on a
    *recoverable* per-statement source failure (``SourceError``/``AllSourcesFailed``):
    it returns a :class:`MetricCoverage` whose ``periods``
    is one :class:`PeriodCoverage` per fiscal_date (newest first), each carrying
    per-statement provenance, named-vs-generic item counts, unmapped codes, and
    every metric's availability + stable reason. Designed for a batch loop over a
    universe that catches nothing and still gets a per-symbol diagnostic.
    The returned object always carries exactly three aggregate
    ``statement_fetches`` in income/balance/cashflow order, including an empty
    ``periods`` result, with ``notes == ("no_fiscal_periods",)`` in that case.
    Invalid input and non-recoverable contract errors still raise normally.
    Source errors expose only the bounded ``recoverable source error`` detail;
    response text, URLs, exception text, and attempt trails are not public.
    """
    symbol = canonical_security_symbol(symbol, "symbol")
    pd = _coerce_period(period)
    results, resolved_is_bank = _fetch_all_statements(
        symbol,
        pd,
        is_bank=is_bank,
        limit=limit,
        source=source,
        sources=sources,
        max_attempts=max_attempts,
        http_get=http_get,
        timeout=timeout,
    )
    return _coverage_from_statement_results(
        symbol, pd, resolved_is_bank, results, limit
    )
