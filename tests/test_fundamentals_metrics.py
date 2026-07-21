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
from vnfin.fundamentals import FinancialReport, LineItem, Period, StatementType
from vnfin.fundamentals.metric_api import (
    REASON_DENOMINATOR_NEGATIVE,
    REASON_DENOMINATOR_NOT_FINITE,
    REASON_DENOMINATOR_ZERO,
    REASON_DERIVED_INPUT_BLOCKED,
    REASON_DERIVED_INPUT_MISSING,
    REASON_MISSING_LINE_ITEM,
    REASON_NOT_APPLICABLE,
    REASON_SOURCE_NOT_MAPPED,
    REASON_STATEMENT_MISSING,
    REASON_STATEMENT_NOT_SERVED,
    REASON_STATEMENT_UNAVAILABLE,
    StatementFetchResult,
    _coverage_from_statement_results,
    _metrics_from_statement_results,
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
    # corporate-only (applies_to=CORPORATE) — #198 verified corporate codes ---- #
    "net_revenue": ("corporate", "size", "raw_mapped", "21001", None),
    "gross_profit": ("corporate", "profitability", "raw_mapped", "23100", None),
    # operating_profit has NO verified corporate code -> None -> BLOCKED (§5).
    "operating_profit": ("corporate", "profitability", "raw_mapped", None, None),
    "net_income_parent": ("corporate", "profitability", "raw_mapped", "23000", None),
    "cash_and_equivalents": ("corporate", "liquidity", "raw_mapped", "11100", None),
    "current_assets": ("corporate", "liquidity", "raw_mapped", "11000", None),
    "current_liabilities": ("corporate", "leverage", "raw_mapped", "13100", None),
    "long_term_liabilities": ("corporate", "leverage", "raw_mapped", "13300", None),
    "operating_cash_flow": ("corporate", "cashflow", "raw_mapped", "32000", None),
    "investing_cash_flow": ("corporate", "cashflow", "raw_mapped", "33000", None),
    "financing_cash_flow": ("corporate", "cashflow", "raw_mapped", "34000", None),
    "net_cash_flow": ("corporate", "cashflow", "raw_mapped", "35000", None),
    "cash_end_of_period": ("corporate", "cashflow", "raw_mapped", "37000", None),
    # shared (applies_to=BOTH) -------------------------------------------- #
    "profit_before_tax": ("both", "profitability", "raw_mapped", "23800", "23800"),
    "net_income": ("both", "profitability", "raw_mapped", "23003", "23000"),
    "total_assets": ("both", "size", "raw_mapped", "12700", "12700"),
    "total_liabilities": ("both", "leverage", "raw_mapped", "13000", "13000"),
    "owners_equity": ("both", "size", "raw_mapped", "14000", "14000"),
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


def test_catalog_verified_bank_codes_exactly():
    # HARD RULE (#157): bank metrics ship ONLY on the 8 verified anchor codes.
    # Assert exact set EQUALITY (allowlist), not a subset — so a future UNKNOWN
    # or extra bank code is caught too, not merely a missing one. (Hardened per
    # the adversarial-verify bank-codes finding.)
    by_id = _by_id(metric_catalog())
    present = set()
    for d in by_id.values():
        codes = d.codes_by_source.get("vndirect")
        if codes and codes.bank_code is not None:
            present.add(codes.bank_code)
    assert present == _VERIFIED_BANK_CODES


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
    assert d.codes_by_source["vndirect"].corporate_code == "23003"
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


# =========================================================================== #
# STAGE B — the pure HTTP-free core (StatementFetchResult + the two pure
# transformers + to_dataframe()). Every fixture is a directly-constructed
# FinancialReport / LineItem / StatementFetchResult — NO HTTP, NO JSON.
# =========================================================================== #
import math

D1 = date(2023, 12, 31)
D2 = date(2022, 12, 31)
D3 = date(2021, 12, 31)


def _li(code, value, *, name=None, value_unit="VND"):
    """LineItem with a real human name by default (named, not generic)."""
    return LineItem(
        item_code=code,
        name=name if name is not None else f"name_{code}",
        value=value,
        value_unit=value_unit,
    )


def _report(symbol, statement, fiscal_date, items, *, source="vndirect",
            is_bank=False, period=Period.ANNUAL):
    return FinancialReport(
        symbol=symbol,
        statement_type=statement,
        period=period,
        fiscal_date=fiscal_date,
        items=tuple(items),
        source=source,
        is_bank=is_bank,
    )


def _ok(statement, reports, source="vndirect"):
    return StatementFetchResult(
        statement=statement,
        reports=tuple(reports),
        status=StatementCoverageStatus.OK,
        source=source,
    )


# A complete corporate income/balance/cashflow at D1 (round fabricated VND).
def _corp_income(fiscal_date=D1, source="vndirect", **over):
    # #198 verified corporate INCOME codes. operating_profit (no code) is BLOCKED,
    # so it has no line here.
    base = {
        "21001": 1000.0,   # net_revenue
        "23100": 400.0,    # gross_profit
        "23000": 180.0,    # net_income_parent (PAT to parent)
        "23800": 250.0,    # profit_before_tax
        "23003": 200.0,    # net_income (PAT total consolidated)
    }
    base.update(over)
    return _report("TESTCO", StatementType.INCOME, fiscal_date,
                   [_li(c, v) for c, v in base.items()], source=source)


def _corp_balance(fiscal_date=D1, source="vndirect", **over):
    base = {
        "11100": 500.0,    # cash_and_equivalents
        "11000": 800.0,    # current_assets
        "13100": 300.0,    # current_liabilities
        "13300": 200.0,    # long_term_liabilities
        "12700": 2000.0,   # total_assets
        "13000": 700.0,    # total_liabilities
        "14000": 1300.0,   # owners_equity
    }
    base.update(over)
    return _report("TESTCO", StatementType.BALANCE, fiscal_date,
                   [_li(c, v) for c, v in base.items()], source=source)


def _corp_cashflow(fiscal_date=D1, source="vndirect", **over):
    base = {
        "32000": 350.0,    # operating_cash_flow
        "33000": -120.0,   # investing_cash_flow
        "34000": -80.0,    # financing_cash_flow
        "35000": 150.0,    # net_cash_flow
        "37000": 600.0,    # cash_end_of_period
    }
    base.update(over)
    return _report("TESTCO", StatementType.CASHFLOW, fiscal_date,
                   [_li(c, v) for c, v in base.items()], source=source)


def _corp_results(fiscal_date=D1):
    return (
        _ok(StatementType.INCOME, [_corp_income(fiscal_date)]),
        _ok(StatementType.BALANCE, [_corp_balance(fiscal_date)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(fiscal_date)]),
    )


# A complete bank income/balance (cashflow deferred/RAW in v1).
def _bank_income(fiscal_date=D1, source="vndirect", **over):
    base = {
        "421900": 700.0,   # net_interest_income
        "23800": 500.0,    # profit_before_tax (bank)
        "23000": 400.0,    # net_income (bank)
    }
    base.update(over)
    return _report("ZZBANK", StatementType.INCOME, fiscal_date,
                   [_li(c, v) for c, v in base.items()],
                   source=source, is_bank=True)


def _bank_balance(fiscal_date=D1, source="vndirect", **over):
    base = {
        "412000": 9000.0,  # loans_to_customers
        "12700": 20000.0,  # total_assets (bank)
        "413300": 15000.0, # customer_deposits
        "13000": 17000.0,  # total_liabilities (bank)
        "14000": 3000.0,   # owners_equity (bank)
    }
    base.update(over)
    return _report("ZZBANK", StatementType.BALANCE, fiscal_date,
                   [_li(c, v) for c, v in base.items()],
                   source=source, is_bank=True)


def _bank_results(fiscal_date=D1):
    return (
        _ok(StatementType.INCOME, [_bank_income(fiscal_date)]),
        _ok(StatementType.BALANCE, [_bank_balance(fiscal_date)]),
        StatementFetchResult(
            statement=StatementType.CASHFLOW, reports=(),
            status=StatementCoverageStatus.OK, source="vndirect",
        ),
    )


# --------------------------------------------------------------------------- #
# StatementFetchResult shape.
# --------------------------------------------------------------------------- #
def test_statement_fetch_result_shape_frozen():
    assert dataclasses.is_dataclass(StatementFetchResult)
    assert _field_names(StatementFetchResult) == [
        "statement",
        "reports",
        "status",
        "source",
        "detail",
    ]
    r = StatementFetchResult(
        statement=StatementType.INCOME,
        reports=(),
        status=StatementCoverageStatus.NOT_SERVED,
        source="cafef",
    )
    assert r.detail is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.source = "x"


# --------------------------------------------------------------------------- #
# Corporate extraction — raw_mapped ids/units/values, newest-first.
# --------------------------------------------------------------------------- #
def test_corporate_extraction_raw_mapped():
    reports = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)
    assert len(reports) == 1
    rep = reports[0]
    assert rep.symbol == "TESTCO"
    assert rep.period is Period.ANNUAL
    assert rep.fiscal_date == D1
    assert rep.is_bank is False
    nr = rep.get("net_revenue")
    assert nr.availability is MetricAvailability.AVAILABLE
    assert nr.value == 1000.0
    assert nr.value_unit == "VND"
    assert nr.kind is MetricKind.RAW_MAPPED
    assert nr.reason is None
    # cashflow raw_mapped resolves too
    ocf = rep.get("operating_cash_flow")
    assert ocf.availability is MetricAvailability.AVAILABLE
    assert ocf.value == 350.0


def test_corporate_extraction_newest_first_and_limit_cap_after_union():
    results = (
        _ok(StatementType.INCOME,
            [_corp_income(D1), _corp_income(D2), _corp_income(D3)]),
        _ok(StatementType.BALANCE,
            [_corp_balance(D1), _corp_balance(D2), _corp_balance(D3)]),
        _ok(StatementType.CASHFLOW,
            [_corp_cashflow(D1), _corp_cashflow(D2), _corp_cashflow(D3)]),
    )
    reports = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=2)
    # union of 3 dates, newest-first, capped to 2 AFTER union
    assert [r.fiscal_date for r in reports] == [D1, D2]


# --------------------------------------------------------------------------- #
# Full-catalog invariant — every report carries ALL 26 metrics.
# --------------------------------------------------------------------------- #
def test_full_catalog_invariant_every_metric_present():
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)[0]
    catalog_ids = {d.id.value for d in metric_catalog()}
    report_ids = {mv.id.value for mv in rep.metrics}
    assert report_ids == catalog_ids
    assert len(rep.metrics) == 26
    # get() returns a value (possibly unavailable) for any known id
    for mid in catalog_ids:
        assert rep.get(mid) is not None


# --------------------------------------------------------------------------- #
# Bank vs corporate applicability.
# --------------------------------------------------------------------------- #
def test_bank_extraction_and_applicability():
    rep = _metrics_from_statement_results(
        "ZZBANK", Period.ANNUAL, True, _bank_results(), limit=8)[0]
    assert rep.is_bank is True
    # bank-only id resolves via bank_code
    nii = rep.get("net_interest_income")
    assert nii.availability is MetricAvailability.AVAILABLE
    assert nii.value == 700.0
    # shared id resolves via bank_code
    ta = rep.get("total_assets")
    assert ta.availability is MetricAvailability.AVAILABLE
    assert ta.value == 20000.0
    # corporate-only raw metric -> NOT_APPLICABLE for a bank
    nr = rep.get("net_revenue")
    assert nr.availability is MetricAvailability.NOT_APPLICABLE
    assert nr.value is None
    assert nr.reason == "metric 'net_revenue' does not apply to bank entities"
    # corporate-only derived metric -> NOT_APPLICABLE for a bank
    gm = rep.get("gross_margin")
    assert gm.availability is MetricAvailability.NOT_APPLICABLE
    assert gm.reason == "metric 'gross_margin' does not apply to bank entities"
    # shared derived resolves for a bank
    lte = rep.get("liabilities_to_equity")
    assert lte.availability is MetricAvailability.AVAILABLE
    assert lte.value == 17000.0 / 3000.0


def test_corporate_bank_only_id_not_applicable():
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)[0]
    nii = rep.get("net_interest_income")
    assert nii.availability is MetricAvailability.NOT_APPLICABLE
    assert nii.reason == (
        "metric 'net_interest_income' does not apply to non-bank entities")


# --------------------------------------------------------------------------- #
# Derived metrics — correct values + guards (zero/negative/missing/non-finite).
# --------------------------------------------------------------------------- #
def test_derived_correct_values():
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)[0]
    gm = rep.get("gross_margin")
    assert gm.availability is MetricAvailability.AVAILABLE
    assert gm.value == 400.0 / 1000.0
    assert gm.value_unit == "ratio"
    assert gm.kind is MetricKind.DERIVED
    nm = rep.get("net_margin")
    assert nm.value == 200.0 / 1000.0
    cta = rep.get("cash_to_assets")
    assert cta.value == 500.0 / 2000.0


def test_derived_denominator_zero():
    results = (
        _ok(StatementType.INCOME, [_corp_income(D1, **{"21001": 0.0})]),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    gm = rep.get("gross_margin")
    assert gm.availability is MetricAvailability.MISSING
    assert gm.value is None
    assert gm.reason == "denominator net_revenue is zero"


def test_derived_denominator_negative():
    results = (
        _ok(StatementType.INCOME, [_corp_income(D1, **{"21001": -50.0})]),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    gm = rep.get("gross_margin")
    assert gm.availability is MetricAvailability.MISSING
    assert gm.value is None
    assert gm.reason == f"denominator net_revenue is negative ({(-50.0)!r})"


def test_derived_denominator_non_finite():
    results = (
        _ok(StatementType.INCOME, [_corp_income(D1, **{"21001": float("nan")})]),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    gm = rep.get("gross_margin")
    assert gm.availability is MetricAvailability.MISSING
    assert gm.value is None
    assert gm.reason == "denominator net_revenue is not finite"


def test_derived_input_missing():
    # drop net_revenue line (21001) entirely, keep gross_profit (23100) so the
    # FIRST missing derived input is net_revenue.
    income = _report("TESTCO", StatementType.INCOME, D1,
                     [_li("23100", 400.0), _li("23003", 200.0)])
    results = (
        _ok(StatementType.INCOME, [income]),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    gm = rep.get("gross_margin")
    assert gm.availability is MetricAvailability.MISSING
    assert gm.reason == "missing input metric net_revenue"


def test_derived_input_blocked_propagates():
    # income from cafef -> raw inputs BLOCKED -> derived BLOCKED
    results = (
        _ok(StatementType.INCOME, [_corp_income(D1, source="cafef")],
            source="cafef"),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    gm = rep.get("gross_margin")
    assert gm.availability is MetricAvailability.BLOCKED
    # one of the inputs (gross_profit or net_revenue) is blocked; reason names it
    assert gm.reason in (
        "input metric gross_profit is blocked",
        "input metric net_revenue is blocked",
    )


def test_derived_never_inf_or_nan():
    # craft inputs that could divide to inf — guard must yield None, not inf
    results = (
        _ok(StatementType.INCOME, [_corp_income(D1, **{"21001": 0.0})]),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    for mv in rep.metrics:
        if mv.value is not None:
            assert math.isfinite(mv.value), mv.id


# --------------------------------------------------------------------------- #
# raw mapped code absent -> MISSING with the exact reason.
# --------------------------------------------------------------------------- #
def test_raw_code_absent_missing():
    income = _report("TESTCO", StatementType.INCOME, D1,
                     [_li("23100", 400.0)])  # net_revenue 21001 absent
    results = (
        _ok(StatementType.INCOME, [income]),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    nr = rep.get("net_revenue")
    assert nr.availability is MetricAvailability.MISSING
    assert nr.reason == "missing line item 21001 in income"


# =========================================================================== #
# #198 — corporate catalog remap: positive resolution, negative (old codes),
# and the honest-BLOCKED unmapped-code contract (§5).
# =========================================================================== #
def test_198_catalog_positive_corporate_codes_resolve():
    """Every remapped corporate primitive resolves from a model-1/2/3 synthetic
    report, and the headline accounting identities hold on the fixtures."""
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)[0]

    def _v(mid):
        mv = rep.get(mid)
        assert mv.availability is MetricAvailability.AVAILABLE, mid
        return mv.value

    # income (modelType 2): 21001/23100/23800/23003/23000
    assert _v("net_revenue") == 1000.0            # 21001
    assert _v("gross_profit") == 400.0            # 23100
    assert _v("profit_before_tax") == 250.0       # 23800
    assert _v("net_income") == 200.0              # 23003 (total consolidated)
    assert _v("net_income_parent") == 180.0       # 23000 (parent)
    # balance (modelType 1): 12700/13000/14000/11000/13100/13300/11100
    assert _v("total_assets") == 2000.0           # 12700
    assert _v("total_liabilities") == 700.0       # 13000
    assert _v("owners_equity") == 1300.0          # 14000
    assert _v("current_assets") == 800.0          # 11000
    assert _v("current_liabilities") == 300.0     # 13100
    assert _v("long_term_liabilities") == 200.0   # 13300
    assert _v("cash_and_equivalents") == 500.0    # 11100
    # cashflow (modelType 3): 32000/33000/34000/35000/37000 — both CF identities
    ocf = _v("operating_cash_flow")               # 32000
    inv = _v("investing_cash_flow")               # 33000
    fin = _v("financing_cash_flow")               # 34000
    net = _v("net_cash_flow")                      # 35000
    end = _v("cash_end_of_period")                 # 37000
    assert ocf == 350.0 and end == 600.0
    assert ocf + inv + fin == net                  # sections sum to net change
    # headline balance identity: total_liabilities + owners_equity == total_assets
    assert _v("total_liabilities") + _v("owners_equity") == _v("total_assets")


def test_198_catalog_negative_old_codes_do_not_resolve():
    """The OLD corporate codes must NOT resolve to their former meanings: a report
    carrying only the pre-#198 codes yields MISSING for the remapped primitives."""
    old_income = _report("TESTCO", StatementType.INCOME, D1, [
        _li("11000", 1000.0),  # was net_revenue; now 21001
        _li("21000", 200.0),   # was net_income; now 23003
        _li("20000", 250.0),   # was PBT corp; now 23800
    ])
    old_balance = _report("TESTCO", StatementType.BALANCE, D1, [
        _li("25000", 2000.0),  # was total_assets; now 12700
        _li("30000", 700.0),   # was total_liabilities; now 13000
        _li("40000", 1300.0),  # was owners_equity; now 14000
        _li("23000", 800.0),   # was current_assets; now 11000
    ])
    old_cash = _report("TESTCO", StatementType.CASHFLOW, D1, [
        _li("31000", 350.0),   # was operating CF; now 32000
        _li("35000", 600.0),   # was cash_end; now 37000
    ])
    results = (
        _ok(StatementType.INCOME, [old_income]),
        _ok(StatementType.BALANCE, [old_balance]),
        _ok(StatementType.CASHFLOW, [old_cash]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    for mid in ("net_revenue", "net_income", "profit_before_tax", "total_assets",
                "total_liabilities", "owners_equity", "current_assets",
                "operating_cash_flow", "cash_end_of_period"):
        mv = rep.get(mid)
        assert mv.availability is MetricAvailability.MISSING, mid
        assert mv.value is None, mid


def test_198_operating_profit_blocked_not_missing():
    """OPERATING_PROFIT (corporate_code=None) reports honest BLOCKED with
    REASON_METRIC_CODE_UNMAPPED — never MISSING / 'missing line item None'."""
    from vnfin.fundamentals.metric_api import REASON_METRIC_CODE_UNMAPPED

    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)[0]
    op = rep.get("operating_profit")
    assert op.availability is MetricAvailability.BLOCKED
    assert op.value is None
    assert op.reason == REASON_METRIC_CODE_UNMAPPED.format(
        id="operating_profit", source="vndirect", entity="corporate")
    # explicitly NOT the MISSING / None-line-item wording
    assert "missing line item" not in op.reason
    assert "None" not in op.reason


def test_198_mapped_but_absent_code_is_still_missing():
    """A metric whose code IS mapped but is absent upstream stays MISSING (the
    BLOCKED split must not swallow a genuine upstream omission)."""
    income = _report("TESTCO", StatementType.INCOME, D1, [
        _li("23100", 400.0),  # gross_profit present; net_revenue 21001 absent
    ])
    results = (
        _ok(StatementType.INCOME, [income]),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    nr = rep.get("net_revenue")
    assert nr.availability is MetricAvailability.MISSING
    assert nr.reason == "missing line item 21001 in income"


def test_198_derived_on_none_code_input_propagates_blocked():
    """A derived metric consuming a None-code (BLOCKED) input propagates BLOCKED,
    naming that input — proving the input-BLOCKED->BLOCKED mechanism for the
    None-code case even though no v1 derived consumes OPERATING_PROFIT."""
    from vnfin.fundamentals.metric_api import _resolve_derived, _resolve_raw
    from vnfin.fundamentals.metric_models import (
        MetricDefinition, MetricCategory, MetricKind,
        StatementProvenance, StatementCoverageStatus as _SCS,
    )

    # Resolve OPERATING_PROFIT (corporate_code=None) as a raw -> BLOCKED.
    income = _corp_income(D1)
    prov = StatementProvenance(
        statement=StatementType.INCOME, status=_SCS.OK, source="vndirect")
    op_defn = explain_metric("operating_profit")
    op_mv = _resolve_raw(op_defn, False, D1,
                         _ok(StatementType.INCOME, [income]), income, prov)
    assert op_mv.availability is MetricAvailability.BLOCKED

    nr_defn = explain_metric("net_revenue")
    nr_prov = prov
    nr_mv = _resolve_raw(nr_defn, False, D1,
                         _ok(StatementType.INCOME, [income]), income, nr_prov)
    assert nr_mv.availability is MetricAvailability.AVAILABLE

    # A synthetic derived metric consuming the None-code (BLOCKED) input.
    synth = MetricDefinition(
        id=MetricId.OPERATING_PROFIT,  # id reused only as a handle; kind=DERIVED
        name="synthetic op-derived",
        category=MetricCategory.PROFITABILITY,
        kind=MetricKind.DERIVED,
        applies_to=op_defn.applies_to,
        value_unit="ratio",
        formula="operating_profit / net_revenue",
        inputs=(MetricId.OPERATING_PROFIT, MetricId.NET_REVENUE),
    )
    resolved = {"operating_profit": op_mv, "net_revenue": nr_mv}
    dv = _resolve_derived(synth, False, D1, resolved)
    assert dv.availability is MetricAvailability.BLOCKED
    assert dv.value is None
    assert "operating_profit" in dv.reason


def test_198_derived_end_to_end_exact_values_via_injected_vndirect():
    """All FIVE derived metrics consuming remapped primitives compute exact values
    end-to-end through an injected VNDirect http_get (real adapter + failover)."""
    rep = metrics("TESTCO", period="annual", http_get=_corp_vnd_http_get())[0]

    def _d(mid):
        mv = rep.get(mid)
        assert mv.availability is MetricAvailability.AVAILABLE, mid
        assert mv.value_unit == "ratio", mid
        return mv.value

    assert _d("gross_margin") == 400.0 / 1000.0                 # 23100 / 21001
    assert _d("net_margin") == 200.0 / 1000.0                   # 23003 / 21001
    assert _d("liabilities_to_equity") == 700.0 / 1300.0        # 13000 / 14000
    assert _d("cash_to_assets") == 500.0 / 2000.0               # 11100 / 12700
    assert _d("operating_cash_flow_margin") == 350.0 / 1000.0   # 32000 / 21001


# --------------------------------------------------------------------------- #
# Source-namespace gate (C3) — non-vndirect source -> BLOCKED, not MISSING.
# --------------------------------------------------------------------------- #
def test_cafef_source_blocked_not_missing():
    results = (
        _ok(StatementType.INCOME, [_corp_income(D1, source="cafef")],
            source="cafef"),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    nr = rep.get("net_revenue")
    assert nr.availability is MetricAvailability.BLOCKED
    assert nr.reason == "metric map not available for source 'cafef'"
    # a vndirect-sourced statement on the same report still resolves
    ta = rep.get("total_assets")
    assert ta.availability is MetricAvailability.AVAILABLE


# --------------------------------------------------------------------------- #
# Per-statement failure cases -> per-metric MISSING with the exact reason.
# --------------------------------------------------------------------------- #
def test_statement_source_error_metrics_missing():
    results = (
        StatementFetchResult(
            statement=StatementType.INCOME, reports=(),
            status=StatementCoverageStatus.SOURCE_ERROR, source=None,
            detail="EmptyData: no rows"),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    nr = rep.get("net_revenue")
    assert nr.availability is MetricAvailability.MISSING
    assert nr.reason == "statement income unavailable: EmptyData: no rows"
    # balance metric still resolves
    assert rep.get("total_assets").availability is MetricAvailability.AVAILABLE


def test_statement_not_served_metrics_missing():
    results = (
        _ok(StatementType.INCOME, [_corp_income(D1)]),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        StatementFetchResult(
            statement=StatementType.CASHFLOW, reports=(),
            status=StatementCoverageStatus.NOT_SERVED, source="cafef",
            detail="statement cashflow not served by source 'cafef'"),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    ocf = rep.get("operating_cash_flow")
    assert ocf.availability is MetricAvailability.MISSING
    assert ocf.reason == "statement cashflow not served by source 'cafef'"


def test_per_period_missing_statement():
    # income/balance have D1 + D2; cashflow only D1. At D2 cashflow is MISSING.
    results = (
        _ok(StatementType.INCOME, [_corp_income(D1), _corp_income(D2)]),
        _ok(StatementType.BALANCE, [_corp_balance(D1), _corp_balance(D2)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    reports = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)
    assert [r.fiscal_date for r in reports] == [D1, D2]
    d2 = reports[1]
    # cashflow statement provenance at D2 is MISSING, source None
    sp = {s.statement: s for s in d2.statement_sources}
    assert sp[StatementType.CASHFLOW].status is StatementCoverageStatus.MISSING
    assert sp[StatementType.CASHFLOW].source is None
    ocf = d2.get("operating_cash_flow")
    assert ocf.availability is MetricAvailability.MISSING
    assert ocf.reason == "missing statement cashflow for 2022-12-31"
    # D1 cashflow still available
    assert reports[0].get("operating_cash_flow").availability is (
        MetricAvailability.AVAILABLE)


# --------------------------------------------------------------------------- #
# Label provenance & identity (REV2.5) — match by code, never by label.
# --------------------------------------------------------------------------- #
def test_label_provenance_identity_by_code():
    # 21001 (net_revenue) carries a generic label; 23100 (gross_profit) a
    # semantically surprising one — identity is by CODE, never by label.
    income = _report("TESTCO", StatementType.INCOME, D1, [
        _li("21001", 1000.0, name="item_21001"),     # generic label
        _li("23100", 400.0, name="Totally Wrong Label"),  # surprising
        _li("23003", 200.0),
    ])
    results = (
        _ok(StatementType.INCOME, [income]),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)[0]
    nr = rep.get("net_revenue")
    assert nr.availability is MetricAvailability.AVAILABLE
    assert nr.value == 1000.0
    # raw label preserved in lineage, never used for identity / no mismatch warning
    assert nr.inputs[0].name == "item_21001"
    assert nr.warnings == ()
    gp = rep.get("gross_profit")
    assert gp.availability is MetricAvailability.AVAILABLE
    assert gp.inputs[0].name == "Totally Wrong Label"


# --------------------------------------------------------------------------- #
# Lineage not via get() (B8) — MetricInput carries code/unit/source/name.
# --------------------------------------------------------------------------- #
def test_lineage_from_lineitem_not_via_get():
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)[0]
    nr = rep.get("net_revenue")
    assert len(nr.inputs) == 1
    mi = nr.inputs[0]
    assert isinstance(mi, MetricInput)
    assert mi.statement is StatementType.INCOME
    assert mi.item_code == "21001"
    assert mi.value == 1000.0
    assert mi.value_unit == "VND"
    assert mi.fiscal_date == D1
    assert mi.source == "vndirect"
    assert mi.name == "name_21001"


# --------------------------------------------------------------------------- #
# Per-statement source / multi-source (C2) — mixed_source warning, no source attr.
# --------------------------------------------------------------------------- #
def test_statement_sources_recorded_per_statement():
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)[0]
    sp = {s.statement: s for s in rep.statement_sources}
    assert set(sp) == {
        StatementType.INCOME, StatementType.BALANCE, StatementType.CASHFLOW}
    for st in sp:
        assert sp[st].status is StatementCoverageStatus.OK
        assert sp[st].source == "vndirect"
    # there is no single `source` field on MetricReport
    assert "source" not in {f.name for f in dataclasses.fields(MetricReport)}


def test_single_source_no_mixed_warning():
    # In v1 only the vndirect namespace is mapped, so a normal extraction has a
    # single source per derived metric -> NO mixed_source warning anywhere.
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)[0]
    ocfm = rep.get("operating_cash_flow_margin")
    assert ocfm.availability is MetricAvailability.AVAILABLE
    assert "mixed_source" not in ocfm.warnings
    assert "mixed_source" not in rep.warnings


def test_mixed_source_warning_branch_direct():
    # Directly exercise the mixed_source branch of _resolve_derived: two AVAILABLE
    # input MetricValues whose lineage spans >1 source -> the derived value is
    # AVAILABLE and carries a "mixed_source" warning (C2: honest, never hidden).
    from vnfin.fundamentals.metric_api import _resolve_derived
    from vnfin.fundamentals.metric_models import MetricValue as _MV

    def _input(mid, code, value, source, statement):
        return _MV(
            id=MetricId(mid),
            value=value,
            value_unit="VND",
            kind=MetricKind.RAW_MAPPED,
            availability=MetricAvailability.AVAILABLE,
            fiscal_date=D1,
            inputs=(MetricInput(
                statement=statement, item_code=code, value=value,
                value_unit="VND", fiscal_date=D1, source=source,
                name=f"name_{code}"),),
        )

    resolved = {
        "operating_cash_flow": _input(
            "operating_cash_flow", "31000", 350.0, "vndirect",
            StatementType.CASHFLOW),
        # second input lineage tagged with a DIFFERENT source name
        "net_revenue": _input(
            "net_revenue", "11000", 1000.0, "othersrc", StatementType.INCOME),
    }
    defn = explain_metric("operating_cash_flow_margin")
    mv = _resolve_derived(defn, False, D1, resolved)
    assert mv.availability is MetricAvailability.AVAILABLE
    assert mv.value == 350.0 / 1000.0
    assert "mixed_source" in mv.warnings


# --------------------------------------------------------------------------- #
# to_dataframe() contract (B6).
# --------------------------------------------------------------------------- #
def test_metric_report_to_dataframe_columns_and_attrs():
    rep = _metrics_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)[0]
    df = rep.to_dataframe()
    assert list(df.columns) == [
        "metric_id", "name", "value", "value_unit", "kind", "availability",
        "reason", "category", "applies_to", "fiscal_date", "input_codes",
        "input_sources", "input_names",
    ]
    assert len(df) == 26
    # enum columns serialize .value; fiscal_date is isoformat
    row = df[df["metric_id"] == "net_revenue"].iloc[0]
    assert row["kind"] == "raw_mapped"
    assert row["availability"] == "available"
    assert row["category"] == "size"
    assert row["applies_to"] == "corporate"
    assert row["fiscal_date"] == "2023-12-31"
    assert row["input_codes"] == "21001"
    assert row["input_sources"] == "vndirect"
    assert row["input_names"] == "name_21001"
    assert row["reason"] is None or (isinstance(row["reason"], float) and math.isnan(row["reason"]))
    # df.attrs — exact keys, no "source"
    assert df.attrs["symbol"] == "TESTCO"
    assert df.attrs["period"] == "ANNUAL"
    assert df.attrs["fiscal_date"] == "2023-12-31"
    assert df.attrs["is_bank"] is False
    assert "source" not in df.attrs
    ss = df.attrs["statement_sources"]
    assert ("income", "ok", "vndirect", None) in ss


def test_metric_report_to_dataframe_no_inputs_empty_strings():
    # a NOT_APPLICABLE metric (no inputs) -> "" for the input_* columns
    rep = _metrics_from_statement_results(
        "ZZBANK", Period.ANNUAL, True, _bank_results(), limit=8)[0]
    df = rep.to_dataframe()
    row = df[df["metric_id"] == "net_revenue"].iloc[0]  # NOT_APPLICABLE for bank
    assert row["input_codes"] == ""
    assert row["input_sources"] == ""
    assert row["input_names"] == ""


# --------------------------------------------------------------------------- #
# Coverage transformer.
# --------------------------------------------------------------------------- #
def test_coverage_basic_corporate():
    cov = _coverage_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)
    assert isinstance(cov, MetricCoverage)
    assert cov.symbol == "TESTCO"
    assert cov.period is Period.ANNUAL
    assert len(cov.periods) == 1
    pc = cov.periods[0]
    assert isinstance(pc, PeriodCoverage)
    assert pc.fiscal_date == D1
    assert pc.is_bank is False
    assert pc.ratio_status is RatioCoverageStatus.NOT_REQUESTED
    # per_metric entries are MetricCoverageItem (typed, not tuples)
    assert all(isinstance(i, MetricCoverageItem) for i in pc.per_metric)
    assert len(pc.per_metric) == 26
    # statement_provenance typed
    assert all(isinstance(s, StatementProvenance) for s in pc.statement_provenance)
    assert all(isinstance(s.status, StatementCoverageStatus)
               for s in pc.statement_provenance)


def test_coverage_named_generic_unmapped_counts():
    # income with one generic (item_<code>) line + one unmapped code
    income = _report("TESTCO", StatementType.INCOME, D1, [
        _li("11000", 1000.0),                     # named + mapped
        _li("99999", 5.0, name="item_99999"),     # generic + unmapped
        _li("88888", 7.0, name="Some Extra"),     # named + unmapped
    ])
    results = (
        _ok(StatementType.INCOME, [income]),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    cov = _coverage_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)
    pc = cov.periods[0]
    # generic = name == f"item_{code}"
    assert pc.generic_item_count == 1
    # unmapped = present codes not in any metric def code set
    assert "99999" in pc.unmapped_codes
    assert "88888" in pc.unmapped_codes
    assert "11000" not in pc.unmapped_codes
    # named_item_count counts LineItems whose name is not item_<code>
    assert pc.named_item_count >= 2


def test_coverage_per_fiscal_date():
    results = (
        _ok(StatementType.INCOME, [_corp_income(D1), _corp_income(D2)]),
        _ok(StatementType.BALANCE, [_corp_balance(D1), _corp_balance(D2)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1), _corp_cashflow(D2)]),
    )
    cov = _coverage_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)
    assert [p.fiscal_date for p in cov.periods] == [D1, D2]
    for p in cov.periods:
        assert len(p.per_metric) == 26


def test_coverage_blocked_for_cafef_namespace():
    results = (
        _ok(StatementType.INCOME, [_corp_income(D1, source="cafef")],
            source="cafef"),
        _ok(StatementType.BALANCE, [_corp_balance(D1)]),
        _ok(StatementType.CASHFLOW, [_corp_cashflow(D1)]),
    )
    cov = _coverage_from_statement_results(
        "TESTCO", Period.ANNUAL, False, results, limit=8)
    pc = cov.periods[0]
    by_id = {i.metric_id.value: i for i in pc.per_metric}
    assert by_id["net_revenue"].availability is MetricAvailability.BLOCKED
    assert by_id["net_revenue"].reason == (
        "metric map not available for source 'cafef'")


def test_coverage_never_fetches_ratios():
    # ratio_status is the NOT_REQUESTED constant for every period; the seam never
    # receives a RATIOS result, and the transformer never invents one.
    cov = _coverage_from_statement_results(
        "TESTCO", Period.ANNUAL, False, _corp_results(), limit=8)
    for p in cov.periods:
        assert p.ratio_status is RatioCoverageStatus.NOT_REQUESTED
    # no statement_provenance entry is a RATIOS statement
    for p in cov.periods:
        for s in p.statement_provenance:
            assert s.statement is not StatementType.RATIOS


# --------------------------------------------------------------------------- #
# Reason constants are module-level and interpolate exactly.
# --------------------------------------------------------------------------- #
def test_reason_constants_interpolation():
    assert REASON_SOURCE_NOT_MAPPED.format(source="cafef") == (
        "metric map not available for source 'cafef'")
    assert REASON_STATEMENT_MISSING.format(
        statement="cashflow", fiscal_date="2022-12-31") == (
        "missing statement cashflow for 2022-12-31")
    assert REASON_STATEMENT_UNAVAILABLE.format(
        statement="income", detail="EmptyData: x") == (
        "statement income unavailable: EmptyData: x")
    assert REASON_STATEMENT_NOT_SERVED.format(
        statement="cashflow", source="cafef") == (
        "statement cashflow not served by source 'cafef'")
    assert REASON_MISSING_LINE_ITEM.format(
        code="11000", statement="income") == (
        "missing line item 11000 in income")
    assert REASON_NOT_APPLICABLE.format(
        id="gross_margin", entity="bank") == (
        "metric 'gross_margin' does not apply to bank entities")
    assert REASON_DERIVED_INPUT_MISSING.format(input_id="net_revenue") == (
        "missing input metric net_revenue")
    assert REASON_DERIVED_INPUT_BLOCKED.format(
        input_id="net_revenue", availability="blocked") == (
        "input metric net_revenue is blocked")
    assert REASON_DENOMINATOR_ZERO.format(input_id="net_revenue") == (
        "denominator net_revenue is zero")
    assert REASON_DENOMINATOR_NEGATIVE.format(
        input_id="net_revenue", value=repr(-50.0)) == (
        f"denominator net_revenue is negative ({(-50.0)!r})")
    assert REASON_DENOMINATOR_NOT_FINITE.format(input_id="net_revenue") == (
        "denominator net_revenue is not finite")


# =========================================================================== #
# STAGE C — the thin network wrappers (metrics / explain_metric_coverage) +
# public wiring. These drive the wrappers end-to-end: an injected ``http_get``
# returning synthetic VNDirect envelopes (house style from test_fundamentals.py)
# for the default-chain fan-out, and STUB ``FundamentalSource`` objects for the
# source-override + CafeF-namespace paths (the wrapper only reads ``source.name``
# and delegates to ``get_financials``). NO real network anywhere.
# =========================================================================== #
import json as _json

from vnfin.exceptions import EmptyData, SourceError, VnfinError
from vnfin.fundamentals import metrics, explain_metric_coverage
from vnfin.fundamentals import (
    metrics as _public_metrics,
    explain_metric_coverage as _public_coverage,
)


# --- synthetic VNDirect envelope helpers (mirror test_fundamentals.py) ----- #
def _vnd_row(code, item_code, value, fiscal_date, report_type, model_type):
    return {
        "code": code,
        "itemCode": float(item_code),
        "reportType": report_type,
        "modelType": float(model_type),
        "numericValue": value,
        "fiscalDate": fiscal_date,
        "createdDate": "2000-01-01 00:00:00",
        "modifiedDate": "2000-01-01 00:00:00",
    }


def _vnd_envelope(rows, total=None):
    return _json.dumps(
        {
            "data": rows,
            "currentPage": 1,
            "size": len(rows),
            "totalElements": total if total is not None else len(rows),
            "totalPages": 1,
        }
    )


# A VNDirect http_get that routes by the requested modelType in params["q"].
# #198 corporate routing: BALANCE=mt1, INCOME=mt2, CASHFLOW=mt3. One ANNUAL period.
_FD = "2025-12-31"


def _corp_vnd_http_get(*, record=None):
    income = [  # modelType 2 (#198 verified corporate INCOME codes)
        _vnd_row("TESTCO", 21001, 1000.0, _FD, "ANNUAL", 2),  # net_revenue
        _vnd_row("TESTCO", 23100, 400.0, _FD, "ANNUAL", 2),   # gross_profit
        _vnd_row("TESTCO", 23000, 180.0, _FD, "ANNUAL", 2),   # net_income_parent
        _vnd_row("TESTCO", 23800, 250.0, _FD, "ANNUAL", 2),   # profit_before_tax
        _vnd_row("TESTCO", 23003, 200.0, _FD, "ANNUAL", 2),   # net_income (total)
    ]
    balance = [  # modelType 1
        _vnd_row("TESTCO", 11100, 500.0, _FD, "ANNUAL", 1),   # cash_and_equivalents
        _vnd_row("TESTCO", 11000, 800.0, _FD, "ANNUAL", 1),   # current_assets
        _vnd_row("TESTCO", 13100, 300.0, _FD, "ANNUAL", 1),   # current_liabilities
        _vnd_row("TESTCO", 13300, 200.0, _FD, "ANNUAL", 1),   # long_term_liabilities
        _vnd_row("TESTCO", 12700, 2000.0, _FD, "ANNUAL", 1),  # total_assets
        _vnd_row("TESTCO", 13000, 700.0, _FD, "ANNUAL", 1),   # total_liabilities
        _vnd_row("TESTCO", 14000, 1300.0, _FD, "ANNUAL", 1),  # owners_equity
    ]
    cashflow = [  # modelType 3
        _vnd_row("TESTCO", 32000, 350.0, _FD, "ANNUAL", 3),   # operating_cash_flow
        _vnd_row("TESTCO", 33000, -120.0, _FD, "ANNUAL", 3),  # investing_cash_flow
        _vnd_row("TESTCO", 34000, -80.0, _FD, "ANNUAL", 3),   # financing_cash_flow
        _vnd_row("TESTCO", 35000, 150.0, _FD, "ANNUAL", 3),   # net_cash_flow
        _vnd_row("TESTCO", 37000, 600.0, _FD, "ANNUAL", 3),   # cash_end_of_period
    ]

    def _g(url, params, headers):
        q = params.get("q", "") if isinstance(params, dict) else ""
        if record is not None:
            record.append({"url": url, "q": q})
        if "modelType:3" in q:
            return _vnd_envelope(cashflow)
        if "modelType:2" in q:
            return _vnd_envelope(income)
        # corporate BALANCE (modelType:1) — also the corporate AUTO probe target
        return _vnd_envelope(balance)

    return _g


# --- a fully-controllable STUB source for source-override / cafef tests ---- #
class _StubSource:
    """Minimal FundamentalSource: the wrapper only reads ``.name`` and calls
    ``get_financials``. ``per_statement`` maps StatementType -> a callable
    ``(symbol, period, is_bank, limit) -> tuple[FinancialReport,...]`` (it may
    raise a SourceError to simulate a per-statement failure)."""

    def __init__(self, name, per_statement, *, calls=None):
        self.name = name
        self._per_statement = per_statement
        self._calls = calls

    def get_financials(self, symbol, statement, period, *, is_bank=None, limit=8):
        st = statement if isinstance(statement, StatementType) else StatementType(statement)
        if self._calls is not None:
            self._calls.append(st)
        fn = self._per_statement.get(st)
        if fn is None:
            raise EmptyData(f"stub: no data for {st.value}")
        return fn(symbol, period, is_bank, limit)


def _stub_corp_for(source_name):
    def _income(symbol, period, is_bank, limit):
        return (_corp_income(D1, source=source_name),)

    def _balance(symbol, period, is_bank, limit):
        return (_corp_balance(D1, source=source_name),)

    def _cashflow(symbol, period, is_bank, limit):
        return (_corp_cashflow(D1, source=source_name),)

    return {
        StatementType.INCOME: _income,
        StatementType.BALANCE: _balance,
        StatementType.CASHFLOW: _cashflow,
    }


# --------------------------------------------------------------------------- #
# Public wiring — names are importable from vnfin.fundamentals.
# --------------------------------------------------------------------------- #
def test_public_names_wired_into_fundamentals():
    import vnfin.fundamentals as f

    for name in (
        "metrics", "explain_metric_coverage", "metric_catalog", "explain_metric",
        "MetricReport", "MetricValue", "MetricDefinition", "MetricCoverage",
        "MetricId", "MetricCategory", "MetricKind", "AppliesTo",
        "MetricAvailability", "StatementCoverageStatus", "StatementProvenance",
    ):
        assert hasattr(f, name), name
        assert name in f.__all__, name
    # there is NO `metrics.py` submodule shadowing the function attribute (B5).
    assert callable(f.metrics)


# --------------------------------------------------------------------------- #
# metrics() — default-chain VNDirect fan-out via injected http_get.
# --------------------------------------------------------------------------- #
def test_metrics_default_chain_fanout_three_statements():
    record = []
    http_get = _corp_vnd_http_get(record=record)
    reports = metrics("TESTCO", period="annual", http_get=http_get)
    assert isinstance(reports, tuple)
    assert len(reports) == 1
    rep = reports[0]
    assert isinstance(rep, MetricReport)
    assert rep.symbol == "TESTCO"
    assert rep.period is Period.ANNUAL
    assert rep.is_bank is False
    # raw_mapped from each of the 3 statements resolved
    assert rep.get("net_revenue").value == 1000.0          # income
    assert rep.get("total_assets").value == 2000.0         # balance
    assert rep.get("operating_cash_flow").value == 350.0   # cashflow
    # derived computed from the raw values
    assert rep.get("gross_margin").value == 400.0 / 1000.0
    # provenance: exactly 3 statements, all OK / vndirect (no RATIOS)
    sp = {s.statement: s for s in rep.statement_sources}
    assert set(sp) == {
        StatementType.INCOME, StatementType.BALANCE, StatementType.CASHFLOW}
    for st in sp:
        assert sp[st].status is StatementCoverageStatus.OK
        assert sp[st].source == "vndirect"
    # exactly THREE fetches (one per statement) and ZERO ratio calls
    qs = [c["q"] for c in record]
    assert all("modelType:3" not in q or "RATIO" not in q for q in qs)
    assert not any("ratio" in c["url"].lower() for c in record)
    # at least one fetch per statement template
    assert any("modelType:1" in q for q in qs)
    assert any("modelType:2" in q for q in qs)
    assert any("modelType:3" in q for q in qs)


def test_metrics_full_catalog_and_dataframe_shape_end_to_end():
    reports = metrics(
        "TESTCO", period="annual", http_get=_corp_vnd_http_get())
    rep = reports[0]
    # full-catalog invariant end to end
    assert len(rep.metrics) == 26
    assert {mv.id.value for mv in rep.metrics} == {
        d.id.value for d in metric_catalog()}
    df = rep.to_dataframe()
    assert list(df.columns) == [
        "metric_id", "name", "value", "value_unit", "kind", "availability",
        "reason", "category", "applies_to", "fiscal_date", "input_codes",
        "input_sources", "input_names",
    ]
    assert "source" not in df.attrs
    assert df.attrs["symbol"] == "TESTCO"


# --------------------------------------------------------------------------- #
# metrics() — source override (single stub source).
# --------------------------------------------------------------------------- #
def test_metrics_source_override_uses_given_source():
    calls = []
    stub = _StubSource("vndirect", _stub_corp_for("vndirect"), calls=calls)
    reports = metrics("TESTCO", period="annual", source=stub)
    rep = reports[0]
    assert rep.get("net_revenue").value == 1000.0
    # exactly THREE statement fetches, one each, NEVER ratios (B7)
    assert sorted(c.value for c in calls) == ["balance", "cashflow", "income"]
    assert StatementType.RATIOS not in calls


# --------------------------------------------------------------------------- #
# metrics() — CafeF does NOT serve cashflow -> NOT_SERVED, no cashflow fetch.
# --------------------------------------------------------------------------- #
def test_metrics_cafef_cashflow_not_served():
    calls = []
    # a single CafeF-named stub that serves income/balance only
    per = _stub_corp_for("cafef")
    del per[StatementType.CASHFLOW]  # would raise if ever called
    stub = _StubSource("cafef", per, calls=calls)
    reports = metrics("TESTCO", period="annual", source=stub)
    rep = reports[0]
    # cashflow statement is NOT_SERVED with the responsible source = cafef
    sp = {s.statement: s for s in rep.statement_sources}
    assert sp[StatementType.CASHFLOW].status is StatementCoverageStatus.NOT_SERVED
    assert sp[StatementType.CASHFLOW].source == "cafef"
    # cashflow metrics are MISSING with the exact not-served reason
    ocf = rep.get("operating_cash_flow")
    assert ocf.availability is MetricAvailability.MISSING
    assert ocf.reason == "statement cashflow not served by source 'cafef'"
    # the cashflow statement was NEVER fetched (gated by serves())
    assert StatementType.CASHFLOW not in calls
    # income/balance from CafeF are BLOCKED (namespace not mapped, C3)
    nr = rep.get("net_revenue")
    assert nr.availability is MetricAvailability.BLOCKED
    assert nr.reason == "metric map not available for source 'cafef'"


# --------------------------------------------------------------------------- #
# metrics() — a per-statement SourceError must NOT raise out (-> SOURCE_ERROR).
# --------------------------------------------------------------------------- #
def test_metrics_per_statement_source_error_is_non_fatal():
    per = _stub_corp_for("vndirect")

    def _boom(symbol, period, is_bank, limit):
        raise EmptyData("no rows")

    per[StatementType.INCOME] = _boom
    stub = _StubSource("vndirect", per)
    reports = metrics("TESTCO", period="annual", source=stub)
    rep = reports[0]
    sp = {s.statement: s for s in rep.statement_sources}
    assert sp[StatementType.INCOME].status is StatementCoverageStatus.SOURCE_ERROR
    assert sp[StatementType.INCOME].source is None
    nr = rep.get("net_revenue")
    assert nr.availability is MetricAvailability.MISSING
    assert nr.reason.startswith("statement income unavailable: ")
    # balance + cashflow still resolved (BLOCKED here: stub source is non-vndirect
    # namespace? No — source name is 'vndirect' so they resolve normally)
    assert rep.get("total_assets").availability is MetricAvailability.AVAILABLE
    assert rep.get("operating_cash_flow").availability is (
        MetricAvailability.AVAILABLE)


# --------------------------------------------------------------------------- #
# metrics() — M1/C1: a CHAIN-level AllSourcesFailed must NOT leak the per-source
# failed-attempt trail onto the public StatementProvenance.detail / reason.
# --------------------------------------------------------------------------- #
def test_metrics_all_sources_failed_detail_is_trail_free():
    # AllSourcesFailed.__str__ enumerates "name:reason" for every attempted
    # source; surfacing it would contradict C1 (no attempt trail in v1) and the
    # StatementProvenance docstring. The chain-level branch must reduce detail to
    # a trail-free string. (Single-source SourceError detail stays verbatim.)
    def _mk(name, token):
        per = _stub_corp_for(name)

        def _boom(symbol, period, is_bank, limit):
            raise EmptyData(f"{name}_{token}")

        per[StatementType.INCOME] = _boom
        return _StubSource(name, per)

    rep = metrics(
        "TESTCO",
        period="annual",
        sources=[_mk("vndirect", "TOKENA"), _mk("cafef", "TOKENB")],
    )[0]
    inc = {s.statement: s for s in rep.statement_sources}[StatementType.INCOME]
    assert inc.status is StatementCoverageStatus.SOURCE_ERROR
    assert inc.detail == "AllSourcesFailed: upstream sources failed"
    reason = rep.get("net_revenue").reason
    assert reason == (
        "statement income unavailable: AllSourcesFailed: upstream sources failed"
    )
    for leak in ("TOKENA", "TOKENB", "vndirect:", "cafef:", "all sources failed for"):
        assert leak not in (inc.detail or "")
        assert leak not in (reason or "")


# --------------------------------------------------------------------------- #
# metrics() — bank auto-detect (is_bank resolved from the OK report).
# --------------------------------------------------------------------------- #
def test_metrics_bank_auto_detect_from_report():
    def _bi(symbol, period, is_bank, limit):
        return (_bank_income(D1),)

    def _bb(symbol, period, is_bank, limit):
        return (_bank_balance(D1),)

    def _bc(symbol, period, is_bank, limit):
        return ()  # bank cashflow empty/RAW in v1

    per = {
        StatementType.INCOME: _bi,
        StatementType.BALANCE: _bb,
        StatementType.CASHFLOW: _bc,
    }
    stub = _StubSource("vndirect", per)
    reports = metrics("ZZBANK", period="annual", source=stub)  # is_bank=AUTO
    rep = reports[0]
    assert rep.is_bank is True
    assert rep.get("net_interest_income").value == 700.0
    assert rep.get("total_assets").value == 20000.0
    # corporate-only id NOT_APPLICABLE for the auto-detected bank
    assert rep.get("net_revenue").availability is (
        MetricAvailability.NOT_APPLICABLE)


def test_metrics_is_bank_explicit_arg_wins():
    # force is_bank=True even though the stub reports is_bank=False
    def _bi(symbol, period, is_bank, limit):
        return (_bank_income(D1),)

    def _bb(symbol, period, is_bank, limit):
        return (_bank_balance(D1),)

    per = {StatementType.INCOME: _bi, StatementType.BALANCE: _bb}
    stub = _StubSource("vndirect", per)
    reports = metrics("ZZBANK", period="annual", is_bank=True, source=stub)
    assert reports[0].is_bank is True


# --------------------------------------------------------------------------- #
# explain_metric_coverage() — same fetch, non-fatal, per-fiscal-date coverage.
# --------------------------------------------------------------------------- #
def test_explain_metric_coverage_default_chain():
    cov = explain_metric_coverage(
        "TESTCO", period="annual", http_get=_corp_vnd_http_get())
    assert isinstance(cov, MetricCoverage)
    assert cov.symbol == "TESTCO"
    assert cov.period is Period.ANNUAL
    assert len(cov.periods) == 1
    pc = cov.periods[0]
    assert pc.ratio_status is RatioCoverageStatus.NOT_REQUESTED
    assert len(pc.per_metric) == 26
    # no RATIOS statement in provenance (B7)
    for s in pc.statement_provenance:
        assert s.statement is not StatementType.RATIOS


def test_explain_metric_coverage_cafef_cashflow_not_served_non_fatal():
    per = _stub_corp_for("cafef")
    del per[StatementType.CASHFLOW]
    stub = _StubSource("cafef", per)
    cov = explain_metric_coverage("TESTCO", period="annual", source=stub)
    pc = cov.periods[0]
    sp = {s.statement: s for s in pc.statement_provenance}
    assert sp[StatementType.CASHFLOW].status is StatementCoverageStatus.NOT_SERVED
    assert sp[StatementType.CASHFLOW].source == "cafef"
    by_id = {i.metric_id.value: i for i in pc.per_metric}
    assert by_id["net_revenue"].availability is MetricAvailability.BLOCKED


def test_explain_metric_coverage_total_failure_non_fatal():
    # every statement raises -> coverage still returns (empty periods), no crash
    def _boom(symbol, period, is_bank, limit):
        raise SourceError("down")

    per = {
        StatementType.INCOME: _boom,
        StatementType.BALANCE: _boom,
        StatementType.CASHFLOW: _boom,
    }
    stub = _StubSource("vndirect", per)
    cov = explain_metric_coverage("TESTCO", period="annual", source=stub)
    assert isinstance(cov, MetricCoverage)
    # no OK statement -> union of fiscal_dates is empty -> no periods
    assert cov.periods == ()


# --------------------------------------------------------------------------- #
# limit is threaded through to the fetch + the alignment cap.
# --------------------------------------------------------------------------- #
def test_metrics_limit_capped_after_union():
    def _income(symbol, period, is_bank, limit):
        return (_corp_income(D1), _corp_income(D2), _corp_income(D3))

    def _balance(symbol, period, is_bank, limit):
        return (_corp_balance(D1), _corp_balance(D2), _corp_balance(D3))

    def _cashflow(symbol, period, is_bank, limit):
        return (_corp_cashflow(D1), _corp_cashflow(D2), _corp_cashflow(D3))

    per = {
        StatementType.INCOME: _income,
        StatementType.BALANCE: _balance,
        StatementType.CASHFLOW: _cashflow,
    }
    stub = _StubSource("vndirect", per)
    reports = metrics("TESTCO", period="annual", limit=2, source=stub)
    assert [r.fiscal_date for r in reports] == [D1, D2]
