"""TDD for vnfin.fundamentals canonical-metrics layer (#157) — STAGE A.

Stage A is the OFFLINE registry slice: the data model
(``vnfin/fundamentals/metric_models.py``), the static v1 catalog + the static
``serves(...)`` capability predicate, and the pure query functions
``metric_catalog`` / ``explain_metric`` (``vnfin/fundamentals/metric_api.py``).
No network, no transformers (those are stages B/C).

All assertions bind to the EXACT enum ``.value`` strings, dataclass field names,
metric ids, item codes, and ``applies_to`` taxonomy from the FINAL-APPROVED
design (``docs/design/fundamentals-metrics.md`` rev2.6) and the implement brief.
"""
from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from vnfin.exceptions import VnfinError
from vnfin.fundamentals import StatementType
from vnfin.fundamentals.metric_api import (
    explain_metric,
    metric_catalog,
    serves,
)
from vnfin.fundamentals.metric_models import (
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
# §4 — enum .value contracts (tests bind these literally).
# --------------------------------------------------------------------------- #
def test_metric_category_values():
    assert MetricCategory.PROFITABILITY.value == "profitability"
    assert MetricCategory.LIQUIDITY.value == "liquidity"
    assert MetricCategory.LEVERAGE.value == "leverage"
    assert MetricCategory.CASHFLOW.value == "cashflow"
    assert MetricCategory.SIZE.value == "size"


def test_metric_kind_values():
    assert MetricKind.RAW_MAPPED.value == "raw_mapped"
    assert MetricKind.PROVIDER_NATIVE.value == "provider_native"
    assert MetricKind.DERIVED.value == "derived"


def test_applies_to_values():
    assert AppliesTo.CORPORATE.value == "corporate"
    assert AppliesTo.BANK.value == "bank"
    assert AppliesTo.BOTH.value == "both"


def test_metric_availability_values():
    assert MetricAvailability.AVAILABLE.value == "available"
    assert MetricAvailability.MISSING.value == "missing"
    assert MetricAvailability.BLOCKED.value == "blocked"
    assert MetricAvailability.NOT_APPLICABLE.value == "not_applicable"
    assert MetricAvailability.UNSUPPORTED.value == "unsupported"
    # B4: the member is NOT_APPLICABLE — there is no UNAPPLICABLE.
    assert not hasattr(MetricAvailability, "UNAPPLICABLE")


def test_statement_coverage_status_values():
    assert StatementCoverageStatus.OK.value == "ok"
    assert StatementCoverageStatus.MISSING.value == "missing"
    assert StatementCoverageStatus.SOURCE_ERROR.value == "source_error"
    assert StatementCoverageStatus.NOT_SERVED.value == "not_served"


def test_ratio_coverage_status_values():
    assert RatioCoverageStatus.NOT_REQUESTED.value == "not_requested"


def test_metric_id_is_str_enum():
    # MetricId values are the lower_snake of the member name; str subclass.
    assert issubclass(MetricId, str)
    assert MetricId.NET_REVENUE.value == "net_revenue"
    assert MetricId.GROSS_MARGIN.value == "gross_margin"


# --------------------------------------------------------------------------- #
# §4 — dataclass shape contracts (frozen + exact field names).
# --------------------------------------------------------------------------- #
def _field_names(cls):
    return [f.name for f in dataclasses.fields(cls)]


def test_metric_source_codes_shape():
    assert dataclasses.is_dataclass(MetricSourceCodes)
    assert _field_names(MetricSourceCodes) == ["corporate_code", "bank_code"]
    sc = MetricSourceCodes(corporate_code="11000")
    assert sc.bank_code is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        sc.corporate_code = "x"


def test_metric_input_shape_frozen():
    assert dataclasses.is_dataclass(MetricInput)
    assert _field_names(MetricInput) == [
        "statement",
        "item_code",
        "value",
        "value_unit",
        "fiscal_date",
        "source",
        "name",
    ]
    mi = MetricInput(
        statement=StatementType.INCOME,
        item_code="11000",
        value=1.0,
        value_unit="VND",
        fiscal_date=date(2023, 12, 31),
        source="vndirect",
        name="Doanh thu thuần",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        mi.value = 2.0


def test_metric_definition_shape_frozen():
    assert dataclasses.is_dataclass(MetricDefinition)
    assert _field_names(MetricDefinition) == [
        "id",
        "name",
        "category",
        "kind",
        "applies_to",
        "value_unit",
        "statement",
        "codes_by_source",
        "formula",
        "inputs",
    ]
    d = MetricDefinition(
        id=MetricId.NET_REVENUE,
        name="Net revenue",
        category=MetricCategory.SIZE,
        kind=MetricKind.RAW_MAPPED,
        applies_to=AppliesTo.CORPORATE,
        value_unit="VND",
    )
    assert d.statement is None
    assert d.codes_by_source == {}
    assert d.formula is None
    assert d.inputs == ()
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.name = "x"


def test_metric_value_shape_frozen():
    assert dataclasses.is_dataclass(MetricValue)
    assert _field_names(MetricValue) == [
        "id",
        "value",
        "value_unit",
        "kind",
        "availability",
        "fiscal_date",
        "inputs",
        "reason",
        "warnings",
    ]
    v = MetricValue(
        id=MetricId.NET_REVENUE,
        value=None,
        value_unit="VND",
        kind=MetricKind.RAW_MAPPED,
        availability=MetricAvailability.MISSING,
        fiscal_date=date(2023, 12, 31),
        inputs=(),
    )
    assert v.reason is None
    assert v.warnings == ()
    with pytest.raises(dataclasses.FrozenInstanceError):
        v.value = 1.0


def test_statement_provenance_shape_frozen():
    assert dataclasses.is_dataclass(StatementProvenance)
    assert _field_names(StatementProvenance) == [
        "statement",
        "status",
        "source",
        "detail",
    ]
    sp = StatementProvenance(
        statement=StatementType.CASHFLOW,
        status=StatementCoverageStatus.NOT_SERVED,
        source="cafef",
    )
    assert sp.detail is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        sp.source = "x"


def test_metric_report_shape_frozen():
    assert dataclasses.is_dataclass(MetricReport)
    assert _field_names(MetricReport) == [
        "symbol",
        "period",
        "fiscal_date",
        "is_bank",
        "metrics",
        "statement_sources",
        "warnings",
    ]


def test_metric_coverage_item_shape_frozen():
    assert dataclasses.is_dataclass(MetricCoverageItem)
    assert _field_names(MetricCoverageItem) == [
        "metric_id",
        "availability",
        "fiscal_date",
        "reason",
    ]


def test_period_coverage_shape_frozen():
    assert dataclasses.is_dataclass(PeriodCoverage)
    assert _field_names(PeriodCoverage) == [
        "fiscal_date",
        "is_bank",
        "statement_provenance",
        "per_metric",
        "named_item_count",
        "generic_item_count",
        "unmapped_codes",
        "ratio_status",
    ]
    # B7: default ratio_status is the NOT_REQUESTED constant.
    pc = PeriodCoverage(
        fiscal_date=date(2023, 12, 31),
        is_bank=False,
        statement_provenance=(),
        per_metric=(),
        named_item_count=0,
        generic_item_count=0,
        unmapped_codes=(),
    )
    assert pc.ratio_status is RatioCoverageStatus.NOT_REQUESTED


def test_metric_coverage_shape_frozen():
    assert dataclasses.is_dataclass(MetricCoverage)
    assert _field_names(MetricCoverage) == [
        "symbol",
        "period",
        "periods",
        "notes",
    ]


# --------------------------------------------------------------------------- #
# §B — the exact v1 catalog (26 metrics with pinned codes/applies_to/category).
# --------------------------------------------------------------------------- #
# Each row: (metric_id, applies_to, category, kind, corporate_code, bank_code)
# corporate_code / bank_code = the codes_by_source["vndirect"] codes.
_EXPECTED_RAW_MAPPED = {
    # corporate-only (applies_to=CORPORATE) -------------------------------- #
    "net_revenue": ("corporate", "size", "raw_mapped", "11000", None),
    "gross_profit": ("corporate", "profitability", "raw_mapped", "11200", None),
    "operating_profit": ("corporate", "profitability", "raw_mapped", "14000", None),
    "net_income_parent": ("corporate", "profitability", "raw_mapped", "21100", None),
    "cash_and_equivalents": ("corporate", "liquidity", "raw_mapped", "23100", None),
    "current_assets": ("corporate", "liquidity", "raw_mapped", "23000", None),
    "current_liabilities": ("corporate", "leverage", "raw_mapped", "30100", None),
    "long_term_liabilities": ("corporate", "leverage", "raw_mapped", "30200", None),
    "operating_cash_flow": ("corporate", "cashflow", "raw_mapped", "31000", None),
    "investing_cash_flow": ("corporate", "cashflow", "raw_mapped", "32000", None),
    "financing_cash_flow": ("corporate", "cashflow", "raw_mapped", "33000", None),
    "net_cash_flow": ("corporate", "cashflow", "raw_mapped", "34000", None),
    "cash_end_of_period": ("corporate", "cashflow", "raw_mapped", "35000", None),
    # shared (applies_to=BOTH) -------------------------------------------- #
    "profit_before_tax": ("both", "profitability", "raw_mapped", "20000", "23800"),
    "net_income": ("both", "profitability", "raw_mapped", "21000", "23000"),
    "total_assets": ("both", "size", "raw_mapped", "25000", "12700"),
    "total_liabilities": ("both", "leverage", "raw_mapped", "30000", "13000"),
    "owners_equity": ("both", "size", "raw_mapped", "40000", "14000"),
    # bank-only (applies_to=BANK) ----------------------------------------- #
    "net_interest_income": ("bank", "profitability", "raw_mapped", None, "421900"),
    "loans_to_customers": ("bank", "size", "raw_mapped", None, "412000"),
    "customer_deposits": ("bank", "leverage", "raw_mapped", None, "413300"),
}

# Each row: (metric_id, applies_to, formula, inputs)
_EXPECTED_DERIVED = {
    "gross_margin": ("corporate", "gross_profit / net_revenue",
                     ("gross_profit", "net_revenue")),
    "net_margin": ("corporate", "net_income / net_revenue",
                   ("net_income", "net_revenue")),
    "liabilities_to_equity": ("both", "total_liabilities / owners_equity",
                              ("total_liabilities", "owners_equity")),
    "cash_to_assets": ("corporate", "cash_and_equivalents / total_assets",
                       ("cash_and_equivalents", "total_assets")),
    "operating_cash_flow_margin": ("corporate", "operating_cash_flow / net_revenue",
                                   ("operating_cash_flow", "net_revenue")),
}

# Statement each raw_mapped id is sourced from (brief §B).
_RAW_STATEMENT = {
    "net_revenue": "income", "gross_profit": "income", "operating_profit": "income",
    "net_income_parent": "income", "profit_before_tax": "income",
    "net_income": "income", "net_interest_income": "income",
    "cash_and_equivalents": "balance", "current_assets": "balance",
    "current_liabilities": "balance", "long_term_liabilities": "balance",
    "total_assets": "balance", "total_liabilities": "balance",
    "owners_equity": "balance", "loans_to_customers": "balance",
    "customer_deposits": "balance",
    "operating_cash_flow": "cashflow", "investing_cash_flow": "cashflow",
    "financing_cash_flow": "cashflow", "net_cash_flow": "cashflow",
    "cash_end_of_period": "cashflow",
}

# Codes that were DISPROVEN/DEFERRED — must NOT appear anywhere in the catalog.
_DEFERRED_BANK_CODES = {
    "22070", "22160", "421601", "411600", "413100", "414000", "415000",
    "22080", "22120", "22130", "22150", "431000", "432000", "433000",
}
_VERIFIED_BANK_CODES = {
    "421900", "23800", "23000", "412000", "12700", "413300", "13000", "14000",
}


def _by_id(cat):
    return {d.id.value: d for d in cat}


def test_catalog_has_exactly_26_metrics():
    cat = metric_catalog()
    assert isinstance(cat, tuple)
    assert len(cat) == 26
    assert len(_EXPECTED_RAW_MAPPED) + len(_EXPECTED_DERIVED) == 26
    ids = {d.id.value for d in cat}
    assert ids == set(_EXPECTED_RAW_MAPPED) | set(_EXPECTED_DERIVED)
    # all entries are MetricDefinition
    assert all(isinstance(d, MetricDefinition) for d in cat)
    # unique ids — no duplicates
    assert len(ids) == len(cat)


def test_catalog_raw_mapped_defs_exact():
    by_id = _by_id(metric_catalog())
    for mid, (applies, cat, kind, corp, bank) in _EXPECTED_RAW_MAPPED.items():
        d = by_id[mid]
        assert d.applies_to.value == applies, mid
        assert d.category.value == cat, mid
        assert d.kind.value == kind, mid
        assert d.value_unit == "VND", mid
        assert d.statement is not None, mid
        assert d.statement.value == _RAW_STATEMENT[mid], mid
        codes = d.codes_by_source["vndirect"]
        assert isinstance(codes, MetricSourceCodes), mid
        assert codes.corporate_code == corp, mid
        assert codes.bank_code == bank, mid
        # raw_mapped carry no formula/inputs
        assert d.formula is None, mid
        assert d.inputs == (), mid
        # v1 ships ONLY the vndirect namespace key
        assert set(d.codes_by_source) == {"vndirect"}, mid


def test_catalog_derived_defs_exact():
    by_id = _by_id(metric_catalog())
    for mid, (applies, formula, inputs) in _EXPECTED_DERIVED.items():
        d = by_id[mid]
        assert d.applies_to.value == applies, mid
        assert d.kind.value == "derived", mid
        assert d.value_unit == "ratio", mid
        assert d.formula == formula, mid
        assert tuple(i.value for i in d.inputs) == inputs, mid
        # derived carry no raw codes / statement
        assert d.codes_by_source == {}, mid
        assert d.statement is None, mid


def test_catalog_verified_bank_codes_present():
    by_id = _by_id(metric_catalog())
    present = set()
    for d in by_id.values():
        codes = d.codes_by_source.get("vndirect")
        if codes and codes.bank_code is not None:
            present.add(codes.bank_code)
    assert _VERIFIED_BANK_CODES <= present


def test_catalog_deferred_bank_codes_absent():
    # No disproven/deferred code may appear as either a corporate or bank code.
    all_codes = set()
    for d in metric_catalog():
        codes = d.codes_by_source.get("vndirect")
        if codes is None:
            continue
        for c in (codes.corporate_code, codes.bank_code):
            if c is not None:
                all_codes.add(c)
    leaked = _DEFERRED_BANK_CODES & all_codes
    assert leaked == set(), f"deferred/disproven codes leaked into catalog: {leaked}"


def test_catalog_no_deferred_metric_ids():
    ids = {d.id.value for d in metric_catalog()}
    deferred_ids = {
        "net_fee_income", "total_operating_income", "operating_expenses",
        "credit_provision_expense", "roe", "roa", "roic", "free_cash_flow",
        "eps", "book_value_per_share",
    }
    assert deferred_ids & ids == set()


def test_catalog_immutable_tuple():
    cat = metric_catalog()
    assert isinstance(cat, tuple)
    # two calls return equal content (stable registry)
    assert metric_catalog() == cat


# --------------------------------------------------------------------------- #
# §3 / §C — serves(source, statement) static capability predicate.
# --------------------------------------------------------------------------- #
def test_serves_truth_table():
    # vndirect serves income/balance/cashflow/ratios
    for st in (StatementType.INCOME, StatementType.BALANCE,
               StatementType.CASHFLOW, StatementType.RATIOS):
        assert serves("vndirect", st) is True, st
    # cafef serves income/balance/ratios but NOT cashflow
    assert serves("cafef", StatementType.INCOME) is True
    assert serves("cafef", StatementType.BALANCE) is True
    assert serves("cafef", StatementType.RATIOS) is True
    assert serves("cafef", StatementType.CASHFLOW) is False


def test_serves_accepts_string_statement():
    assert serves("cafef", "income") is True
    assert serves("cafef", "cashflow") is False
    assert serves("vndirect", "cashflow") is True


def test_serves_unknown_source_is_false():
    assert serves("nope", StatementType.INCOME) is False


# --------------------------------------------------------------------------- #
# §E — metric_catalog(applies_to) filter.
# --------------------------------------------------------------------------- #
def test_metric_catalog_filter_none_is_all():
    assert len(metric_catalog(None)) == 26
    assert len(metric_catalog()) == 26


def test_metric_catalog_filter_bank_is_bank_plus_both():
    cat = metric_catalog("bank")
    kinds = {d.applies_to.value for d in cat}
    assert kinds <= {"bank", "both"}
    # contains a bank-only id and a shared (both) id, excludes corporate-only
    ids = {d.id.value for d in cat}
    assert "net_interest_income" in ids       # bank-only
    assert "total_assets" in ids              # both
    assert "gross_margin" not in ids          # corporate-only
    assert "net_revenue" not in ids           # corporate-only


def test_metric_catalog_filter_corporate_is_corporate_plus_both():
    cat = metric_catalog("corporate")
    kinds = {d.applies_to.value for d in cat}
    assert kinds <= {"corporate", "both"}
    ids = {d.id.value for d in cat}
    assert "net_revenue" in ids               # corporate-only
    assert "total_assets" in ids              # both
    assert "net_interest_income" not in ids   # bank-only


def test_metric_catalog_filter_non_bank_alias():
    assert metric_catalog("non_bank") == metric_catalog("corporate")


def test_metric_catalog_filter_enum_member():
    assert metric_catalog(AppliesTo.BANK) == metric_catalog("bank")
    assert metric_catalog(AppliesTo.CORPORATE) == metric_catalog("corporate")


def test_metric_catalog_filter_both_partition():
    bank = {d.id.value for d in metric_catalog("bank")}
    corp = {d.id.value for d in metric_catalog("corporate")}
    both = bank & corp
    # the intersection is exactly the BOTH-applies metrics
    expected_both = {
        "profit_before_tax", "net_income", "total_assets",
        "total_liabilities", "owners_equity", "liabilities_to_equity",
    }
    assert both == expected_both


def test_metric_catalog_filter_invalid_string_raises():
    with pytest.raises(VnfinError):
        metric_catalog("banana")


# --------------------------------------------------------------------------- #
# §E — explain_metric(metric_id).
# --------------------------------------------------------------------------- #
def test_explain_metric_by_enum():
    d = explain_metric(MetricId.NET_INCOME)
    assert isinstance(d, MetricDefinition)
    assert d.id is MetricId.NET_INCOME
    assert d.codes_by_source["vndirect"].corporate_code == "21000"
    assert d.codes_by_source["vndirect"].bank_code == "23000"


def test_explain_metric_by_string():
    d = explain_metric("gross_margin")
    assert d.id.value == "gross_margin"
    assert d.kind.value == "derived"
    assert d.formula == "gross_profit / net_revenue"


def test_explain_metric_unknown_raises():
    with pytest.raises(VnfinError):
        explain_metric("not_a_metric")
    with pytest.raises(VnfinError):
        explain_metric("roe")  # deferred to v2 — not in v1 catalog
