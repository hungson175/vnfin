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

import math
from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..exceptions import AllSourcesFailed, SourceError, VnfinError
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


# =========================================================================== #
# STAGE B — the pure HTTP-free core.
#
# ``StatementFetchResult`` is the typed seam the (future) network wrappers
# produce per statement; the two pure transformers consume a tuple of them and
# emit ``MetricReport``s / ``MetricCoverage`` with NO network. All reason strings
# are EXACT, stable constants (the design §5 reason table; tests bind verbatim).
# =========================================================================== #
@dataclass(frozen=True)
class StatementFetchResult:
    """One per-statement fetch outcome (B1/B2).

    ``reports`` is empty (``()``) when the fetch failed / was not served. The
    ``source`` role follows the design rule: OK -> the succeeding source;
    NOT_SERVED -> the responsible (non-serving) source (e.g. "cafef" for
    cashflow); SOURCE_ERROR/MISSING -> ``None``. ``detail`` carries the error
    class/message on failure. This carries SUCCESS and FAILURE so the pure
    transformers can encode both without any hidden wrapper logic.
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
                return StatementProvenance(
                    statement=st,
                    status=StatementCoverageStatus.OK,
                    source=rep.source,
                )
        return StatementProvenance(
            statement=st, status=StatementCoverageStatus.MISSING, source=None
        )
    if result.status is StatementCoverageStatus.SOURCE_ERROR:
        return StatementProvenance(
            statement=st,
            status=StatementCoverageStatus.SOURCE_ERROR,
            source=None,
            detail=result.detail,
        )
    if result.status is StatementCoverageStatus.NOT_SERVED:
        return StatementProvenance(
            statement=st,
            status=StatementCoverageStatus.NOT_SERVED,
            source=result.source,
            detail=result.detail,
        )
    # A bare MISSING result (no reports) — treat as missing this date.
    return StatementProvenance(
        statement=st,
        status=StatementCoverageStatus.MISSING,
        source=None,
        detail=result.detail,
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
    source = report.source
    if source != _MAPPED_SOURCE or defn.codes_by_source.get(source) is None:
        return _unavailable(
            defn,
            MetricAvailability.BLOCKED,
            fiscal_date,
            REASON_SOURCE_NOT_MAPPED.format(source=source),
        )
    # 4. look the code up in the report's code -> LineItem index (B8 — from the
    #    full LineItem object, never via FinancialReport.get() which is float-only).
    code = _code_for(defn, source, is_bank)
    line: Optional[LineItem] = None
    if code is not None:
        for li in report.items:
            if li.item_code == code:
                line = li
                break
    if code is None or line is None:
        return _unavailable(
            defn,
            MetricAvailability.MISSING,
            fiscal_date,
            REASON_MISSING_LINE_ITEM.format(code=code, statement=st_value),
        )
    # 5. AVAILABLE — build lineage from the full LineItem (B8, not via .get()).
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
    # AVAILABLE derived must never be inf / NaN (guards above should ensure this).
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

    NO network, never raises on a per-statement failure. One PeriodCoverage per
    fiscal_date (newest first); NEVER fetches/requires ratios (B7 —
    ratio_status is always NOT_REQUESTED).
    """
    reports = _metrics_from_statement_results(
        symbol, period, is_bank, results, limit
    )
    periods = tuple(
        _build_period_coverage(is_bank, rep, results) for rep in reports
    )
    return MetricCoverage(symbol=symbol, period=period, periods=periods)


# =========================================================================== #
# STAGE C — the thin network wrappers (the ONLY network seam in this module).
#
# ``metrics`` / ``explain_metric_coverage`` fetch each of income/balance/cashflow
# (NEVER ratios — B7) via the existing ``fundamentals.get_financials`` failover,
# turn each outcome into a typed ``StatementFetchResult`` (success OR recoverable
# failure — a per-statement error must NEVER raise out), resolve the concrete
# ``is_bank`` template, then hand the 3 results to the PURE Stage-B transformers.
# A statement no resolved source can serve (CafeF cashflow) is gated OUT before
# any fetch via the static ``serves(...)`` predicate (deterministic, not
# exception-text classification).
# =========================================================================== #
def _resolve_chain_names(source, sources) -> tuple[str, ...]:
    """Resolved source-chain NAMES for the serves-gate (no fetch needed).

    ``source`` wins over ``sources`` (matching ``get_financials``); neither -> the
    default failover chain names ``("vndirect", "cafef")``.
    """
    if source is not None:
        return (source.name,)
    if sources is not None:
        return tuple(s.name for s in sources)
    return ("vndirect", "cafef")


def _fetch_statement_result(
    symbol: str,
    statement: StatementType,
    period: Period,
    names: tuple[str, ...],
    *,
    is_bank,
    limit: int,
    source,
    sources,
    max_attempts: int,
    http_get,
    timeout: float,
) -> StatementFetchResult:
    """Fetch ONE statement and classify it into a typed result (never raises).

    serves-gate first (capability-based): if NO resolved source can serve the
    statement -> ``NOT_SERVED`` with the responsible source(s). Otherwise call
    ``get_financials`` and map success -> ``OK`` / a recoverable ``SourceError``
    or chain-level ``AllSourcesFailed`` -> ``SOURCE_ERROR`` (never exposing the
    attempt trail — C1).
    """
    if not any(serves(n, statement) for n in names):
        joined = ",".join(names)
        return StatementFetchResult(
            statement=statement,
            reports=(),
            status=StatementCoverageStatus.NOT_SERVED,
            source=joined,
            detail=(
                f"statement {statement.value} not served by source '{joined}'"
            ),
        )
    # Lazy import avoids the metric_api <-> fundamentals.__init__ circular import.
    from . import get_financials

    try:
        reports = get_financials(
            symbol,
            statement,
            period,
            is_bank=is_bank,
            limit=limit,
            source=source,
            sources=sources,
            max_attempts=max_attempts,
            http_get=http_get,
            timeout=timeout,
        )
    except (SourceError, AllSourcesFailed) as exc:
        return StatementFetchResult(
            statement=statement,
            reports=(),
            status=StatementCoverageStatus.SOURCE_ERROR,
            source=None,
            detail=f"{type(exc).__name__}: {exc}",
        )
    reports = tuple(reports)
    succeeding = reports[0].source if reports else None
    return StatementFetchResult(
        statement=statement,
        reports=reports,
        status=StatementCoverageStatus.OK,
        source=succeeding,
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
    """Fan out the 3 metric statements and resolve the concrete ``is_bank``.

    Makes EXACTLY THREE ``get_financials`` calls (one per income/balance/
    cashflow), ZERO ratio calls. Returns the per-statement results plus the
    resolved ``is_bank`` template: the explicit arg if given, else the first OK
    report's ``.is_bank``, else the known-bank heuristic on the symbol.
    """
    names = _resolve_chain_names(source, sources)
    results = tuple(
        _fetch_statement_result(
            symbol,
            st,
            period,
            names,
            is_bank=is_bank,
            limit=limit,
            source=source,
            sources=sources,
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

    Mirrors :func:`get_financials`' injection knobs (``is_bank``/``limit``/
    ``source``/``sources``/``http_get``/``timeout``/``max_attempts``).
    """
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
    return _metrics_from_statement_results(
        symbol, pd, resolved_is_bank, results, limit
    )


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
    ``ratio_status`` is always ``not_requested``), but never raises on a
    per-statement failure: it returns a :class:`MetricCoverage` whose ``periods``
    is one :class:`PeriodCoverage` per fiscal_date (newest first), each carrying
    per-statement provenance, named-vs-generic item counts, unmapped codes, and
    every metric's availability + stable reason. Designed for a batch loop over a
    universe that catches nothing and still gets a per-symbol diagnostic.
    """
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
