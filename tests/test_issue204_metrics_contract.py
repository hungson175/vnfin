"""RED contract tests for issue #204 metrics diagnostics and safe routing.

All fixtures are synthetic typed reports.  No provider rows or live calls are
used here; the tests exercise only the public wrapper seams and their injected
source doubles.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
import math

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceError, VnfinError
from vnfin.fundamentals import (
    FinancialReport,
    LineItem,
    MetricAvailability,
    MetricCoverage,
    Period,
    StatementType,
    StatementCoverageStatus,
    explain_metric_coverage,
    metrics,
)
from vnfin.fundamentals.metric_api import _role_composite


_DATE = date(2025, 12, 31)
_EMPTY_METRICS_MESSAGE = (
    "no usable annual fiscal periods for symbol 'TESTCO'; "
    "call explain_metric_coverage()"
)


def _report(statement: StatementType, source, *, symbol="TESTCO"):
    code = {
        StatementType.INCOME: "21001",
        StatementType.BALANCE: "11000",
        StatementType.CASHFLOW: "32000",
    }[statement]
    model_type = {
        StatementType.INCOME: 2,
        StatementType.BALANCE: 1,
        StatementType.CASHFLOW: 3,
    }[statement]
    return FinancialReport(
        symbol=symbol,
        statement_type=statement,
        period=Period.ANNUAL,
        fiscal_date=_DATE,
        items=(LineItem(code, f"line_{code}", 100.0, "VND"),),
        source=source,
        currency="VND",
        is_bank=False,
        model_type=model_type if source == "vndirect" else None,
    )


def _income_payload(mutator):
    """Build one synthetic income result for direct/chain parity tests."""
    base = _report(StatementType.INCOME, "vndirect")
    payload = mutator(base)
    return payload if isinstance(payload, tuple) else (payload,)


def _source_with_income_payload(payload):
    return _Source(
        "vndirect",
        {
            StatementType.INCOME: payload,
            StatementType.BALANCE: (_report(StatementType.BALANCE, "vndirect"),),
            StatementType.CASHFLOW: (_report(StatementType.CASHFLOW, "vndirect"),),
        },
    )


class _Source:
    """Small source double with call tracking and scripted statement results."""

    unit = "VND"

    def __init__(self, name, per_statement, *, calls=None):
        self.name = name
        self.per_statement = per_statement
        self.calls = calls if calls is not None else []

    def get_financials(self, symbol, statement, period, *, is_bank=None, limit=8):
        self.calls.append((symbol, statement))
        outcome = self.per_statement.get(statement)
        if outcome is None:
            raise AssertionError(f"unexpected physical call: {statement!r}")
        if callable(outcome):
            return outcome(symbol, period, is_bank, limit)
        return outcome


class _MissingNameSource:
    unit = "VND"

    def __init__(self):
        self.calls = []

    def get_financials(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        raise AssertionError("custom source must be filtered before a physical call")


class _RaisingNameSource(_MissingNameSource):
    def __init__(self, raw_error):
        super().__init__()
        self.raw_error = raw_error

    @property
    def name(self):
        raise RuntimeError(self.raw_error)


def _empty_source(name="vndirect"):
    return _Source(
        name,
        {
            StatementType.INCOME: (),
            StatementType.BALANCE: (),
            StatementType.CASHFLOW: (),
        },
    )


def _all_success_source(name="vndirect"):
    return _Source(
        name,
        {
            statement: (_report(statement, name),)
            for statement in (
                StatementType.INCOME,
                StatementType.BALANCE,
                StatementType.CASHFLOW,
            )
        },
    )


def _status_by_statement(outcomes):
    return {outcome.statement: outcome for outcome in outcomes}


@pytest.mark.parametrize("wrapper", [metrics, explain_metric_coverage], ids=["metrics", "coverage"])
def test_empty_effective_chain_is_exact_and_zero_call(wrapper):
    with pytest.raises(VnfinError, match=r"^sources must contain at least one source$"):
        wrapper("TESTCO", period="annual", source=None, sources=[])


@pytest.mark.parametrize("wrapper", [metrics, explain_metric_coverage], ids=["metrics", "coverage"])
def test_direct_source_wins_over_empty_sources(wrapper):
    source = _empty_source("vndirect")

    if wrapper is metrics:
        with pytest.raises(EmptyData, match=r"^no usable annual fiscal periods") as caught:
            wrapper(" testco ", period="annual", source=source, sources=[])
        assert str(caught.value) == _EMPTY_METRICS_MESSAGE
    else:
        coverage = wrapper(" testco ", period="annual", source=source, sources=[])
        assert coverage.periods == ()
        assert coverage.notes == ("no_fiscal_periods",)
        assert [o.status for o in coverage.statement_fetches] == [
            StatementCoverageStatus.MISSING,
            StatementCoverageStatus.MISSING,
            StatementCoverageStatus.MISSING,
        ]
    assert [statement.value for _, statement in source.calls] == [
        "income",
        "balance",
        "cashflow",
    ]


def test_all_recoverable_failures_are_fail_loud_but_coverage_is_typed():
    def _boom(symbol, period, is_bank, limit):
        raise EmptyData("raw body SECRET-204 https://example.invalid/?token=red")

    source = _Source(
        "vndirect",
        {
            StatementType.INCOME: _boom,
            StatementType.BALANCE: _boom,
            StatementType.CASHFLOW: _boom,
        },
    )
    with pytest.raises(EmptyData, match=r"^no usable annual fiscal periods") as caught:
        metrics(" testco ", period="annual", source=source)
    assert str(caught.value) == _EMPTY_METRICS_MESSAGE
    assert "SECRET-204" not in str(caught.value)
    assert "example.invalid" not in str(caught.value)

    coverage = explain_metric_coverage(" testco ", period="annual", source=source)
    assert coverage.symbol == "TESTCO"
    assert coverage.period is Period.ANNUAL
    assert coverage.periods == ()
    assert coverage.notes == ("no_fiscal_periods",)
    assert len(coverage.statement_fetches) == 3
    assert all(o.status is StatementCoverageStatus.SOURCE_ERROR for o in coverage.statement_fetches)
    assert all(o.source is None for o in coverage.statement_fetches)
    assert all(o.detail == "recoverable source error" for o in coverage.statement_fetches)
    assert coverage.to_dataframe().attrs["statement_fetches"] == (
        ("income", "source_error", None, "recoverable source error"),
        ("balance", "source_error", None, "recoverable source error"),
        ("cashflow", "source_error", None, "recoverable source error"),
    )


def test_partial_source_error_keeps_dates_and_sanitizes_every_public_surface():
    def _income_boom(symbol, period, is_bank, limit):
        raise SourceError("RAW-204 https://example.invalid/?secret=red")

    source = _Source(
        "vndirect",
        {
            StatementType.INCOME: _income_boom,
            StatementType.BALANCE: (_report(StatementType.BALANCE, "vndirect"),),
            StatementType.CASHFLOW: (_report(StatementType.CASHFLOW, "vndirect"),),
        },
    )
    reports = metrics(" testco ", period="annual", source=source)
    assert len(reports) == 1
    report = reports[0]
    assert report.symbol == "TESTCO"
    income = _status_by_statement(report.statement_sources)[StatementType.INCOME]
    assert income.status is StatementCoverageStatus.SOURCE_ERROR
    assert income.source is None
    assert income.detail == "recoverable source error"
    value = report.get("net_revenue")
    assert value.availability is MetricAvailability.MISSING
    assert value.reason == "statement income unavailable: recoverable source error"
    assert "RAW-204" not in repr(report)
    assert "example.invalid" not in repr(report)
    assert report.to_dataframe().attrs["statement_sources"][0] == (
        "income",
        "source_error",
        None,
        "recoverable source error",
    )

    coverage = explain_metric_coverage(" testco ", period="annual", source=source)
    assert len(coverage.periods) == 1
    aggregate_income = _status_by_statement(coverage.statement_fetches)[StatementType.INCOME]
    period_income = _status_by_statement(
        coverage.periods[0].statement_provenance
    )[StatementType.INCOME]
    assert aggregate_income == period_income
    assert aggregate_income.detail == "recoverable source error"
    assert coverage.periods[0].per_metric[0].reason == (
        "statement income unavailable: recoverable source error"
    )
    attrs = coverage.periods[0].to_dataframe().attrs
    assert attrs["statement_provenance"][0] == (
        "income",
        "source_error",
        None,
        "recoverable source error",
    )
    public = repr(coverage) + repr(attrs)
    assert "RAW-204" not in public
    assert "example.invalid" not in public


@pytest.mark.parametrize(
    "label,mutator",
    [
        (
            "cross_symbol",
            lambda report: replace(report, symbol="OTHER"),
        ),
        (
            "wrong_statement",
            lambda report: replace(report, statement_type=StatementType.BALANCE),
        ),
        (
            "wrong_period",
            lambda report: replace(report, period=Period.QUARTER),
        ),
        (
            "malformed_date",
            lambda report: replace(report, fiscal_date=datetime(2025, 12, 31)),
        ),
        (
            "foreign_model_type_89",
            lambda report: replace(
                report,
                model_type=89,
                items=(LineItem("23003", "net_income", 100.0, "VND"),),
            ),
        ),
        (
            "foreign_model_type_90",
            lambda report: replace(
                report,
                model_type=90,
                items=(LineItem("23003", "net_income", 100.0, "VND"),),
            ),
        ),
        (
            "foreign_model_type_91",
            lambda report: replace(
                report,
                model_type=91,
                items=(LineItem("23003", "net_income", 100.0, "VND"),),
            ),
        ),
        (
            "mixed_model_types",
            lambda report: (
                replace(report, model_type=89),
                replace(
                    report,
                    fiscal_date=date(2024, 12, 31),
                    model_type=2,
                ),
            ),
        ),
        (
            "entity_model_mismatch",
            lambda report: replace(report, is_bank=True, model_type=2),
        ),
        (
            "wrong_currency",
            lambda report: replace(report, currency="USD"),
        ),
        (
            "wrong_unit_or_scale",
            lambda report: replace(
                report,
                items=(LineItem("21001", "net_revenue", 100.0, "VND/1000"),),
            ),
        ),
        (
            "nonfinite_value",
            lambda report: replace(
                report,
                items=(LineItem("21001", "net_revenue", math.inf, "VND"),),
            ),
        ),
        (
            "duplicate_item_codes",
            lambda report: replace(
                report,
                items=(
                    LineItem("21001", "net_revenue", 100.0, "VND"),
                    LineItem("21001", "net_revenue_again", 101.0, "VND"),
                ),
            ),
        ),
        (
            "duplicate_fiscal_dates",
            lambda report: (
                report,
                replace(
                    report,
                    items=(LineItem("21002", "other_revenue", 101.0, "VND"),),
                ),
            ),
        ),
        ("malformed_report", lambda report: object()),
    ],
    ids=[
        "cross_symbol",
        "wrong_statement",
        "wrong_period",
        "malformed_date",
        "foreign_model_type_89",
        "foreign_model_type_90",
        "foreign_model_type_91",
        "mixed_model_types",
        "entity_model_mismatch",
        "wrong_currency",
        "wrong_unit_or_scale",
        "nonfinite_value",
        "duplicate_item_codes",
        "duplicate_fiscal_dates",
        "malformed_report",
    ],
)
def test_direct_and_explicit_chain_validate_the_same_complete_report_contract(
    label, mutator
):
    payload = _income_payload(mutator)
    for selection in ("direct", "chain"):
        source = _source_with_income_payload(payload)
        kwargs = {"source": source} if selection == "direct" else {"sources": [source]}
        reports = metrics("TESTCO", period="annual", **kwargs)
        assert len(reports) == 1, (label, selection)
        report = reports[0]
        income = _status_by_statement(report.statement_sources)[StatementType.INCOME]
        assert income.status is StatementCoverageStatus.SOURCE_ERROR, (label, selection)
        assert income.source is None
        assert income.detail == "recoverable source error"
        assert report.get("net_revenue").availability is MetricAvailability.MISSING
        assert report.get("net_income").availability is MetricAvailability.MISSING

        coverage = explain_metric_coverage("TESTCO", period="annual", **kwargs)
        aggregate_income = _status_by_statement(coverage.statement_fetches)[
            StatementType.INCOME
        ]
        assert aggregate_income.status is StatementCoverageStatus.SOURCE_ERROR
        assert aggregate_income.source is None
        assert aggregate_income.detail == "recoverable source error"


def test_direct_and_explicit_chain_accept_the_same_valid_report_contract():
    for selection in ("direct", "chain"):
        source = _source_with_income_payload(
            (_report(StatementType.INCOME, "vndirect"),)
        )
        kwargs = {"source": source} if selection == "direct" else {"sources": [source]}
        report = metrics("TESTCO", period="annual", **kwargs)[0]
        income = _status_by_statement(report.statement_sources)[StatementType.INCOME]
        assert income.status is StatementCoverageStatus.OK
        assert income.source == "vndirect"
        assert report.get("net_revenue").availability is MetricAvailability.AVAILABLE
        coverage = explain_metric_coverage("TESTCO", period="annual", **kwargs)
        aggregate_income = _status_by_statement(coverage.statement_fetches)[
            StatementType.INCOME
        ]
        assert aggregate_income.status is StatementCoverageStatus.OK
        assert aggregate_income.source == "vndirect"


def test_heading_contract_rejects_every_noncanonical_89_90_91_template_for_ssi_and_tcx():
    for symbol_input, canonical_symbol in ((" ssi ", "SSI"), ("tcx", "TCX")):
        for model_type in (89, 90, 91):
            bad = replace(
                _report(StatementType.INCOME, "vndirect", symbol=canonical_symbol),
                model_type=model_type,
                items=(LineItem("23003", "net_income", 100.0, "VND"),),
            )
            for selection in ("direct", "chain"):
                source = _Source(
                    "vndirect",
                    {
                        StatementType.INCOME: (bad,),
                        StatementType.BALANCE: (),
                        StatementType.CASHFLOW: (),
                    },
                )
                kwargs = (
                    {"source": source}
                    if selection == "direct"
                    else {"sources": [source]}
                )
                with pytest.raises(EmptyData, match=r"^no usable annual fiscal periods"):
                    metrics(symbol_input, period="annual", **kwargs)
                coverage = explain_metric_coverage(
                    symbol_input, period="annual", **kwargs
                )
                assert coverage.symbol == canonical_symbol
                income = _status_by_statement(coverage.statement_fetches)[
                    StatementType.INCOME
                ]
                assert income.status is StatementCoverageStatus.SOURCE_ERROR
                assert income.detail == "recoverable source error"
                assert coverage.periods == ()


@pytest.mark.parametrize("symbol", [" ssi ", "tcx"], ids=["ssi", "tcx"])
def test_ssi_tcx_empty_chain_diagnostics_are_normalized_and_fail_loud_metrics(symbol):
    source = _empty_source("vndirect")
    coverage = explain_metric_coverage(symbol, period="annual", source=source)
    assert coverage.symbol == symbol.strip().upper()
    assert coverage.periods == ()
    assert coverage.notes == ("no_fiscal_periods",)
    assert len(coverage.statement_fetches) == 3
    assert all(
        outcome.status is StatementCoverageStatus.MISSING
        for outcome in coverage.statement_fetches
    )
    with pytest.raises(EmptyData, match=r"^no usable annual fiscal periods"):
        metrics(symbol, period="annual", source=source)


@pytest.mark.parametrize("wrapper", [metrics, explain_metric_coverage], ids=["metrics", "coverage"])
def test_malformed_symbol_is_rejected_before_any_source_call(wrapper):
    source = _all_success_source("vndirect")
    with pytest.raises(InvalidData):
        wrapper("BAD SYMBOL", period="annual", source=source)
    assert source.calls == []


def test_not_served_composite_is_canonical_and_at_the_exact_bounded_maximum():
    composite = _role_composite(("vndirect", "cafef", "custom", "vndirect"))
    assert composite == "vndirect,cafef,custom"
    assert len(composite) == 21


@pytest.mark.parametrize(
    "label,source_factory,raw_text",
    [
        ("missing", _MissingNameSource, "missing-name-secret"),
        (
            "raising",
            lambda: _RaisingNameSource("raising-name-secret"),
            "raising-name-secret",
        ),
        ("none", lambda: _Source(None, {}), "None"),
        ("scalar", lambda: _Source(7, {}), "7"),
        ("list", lambda: _Source(["list-secret"], {}), "list-secret"),
        ("dict", lambda: _Source({"token": "dict-secret"}, {}), "dict-secret"),
        ("empty", lambda: _Source("", {}), "''"),
        ("whitespace", lambda: _Source(" \t\n", {}), "\\t"),
        ("case", lambda: _Source("VNDirect", {}), "VNDirect"),
        ("case_cafef", lambda: _Source("CafeF", {}), "CafeF"),
        ("unknown", lambda: _Source("unknown-role", {}), "unknown-role"),
        (
            "url",
            lambda: _Source("https://example.invalid/?token=name-secret", {}),
            "name-secret",
        ),
        ("overlong", lambda: _Source("x" * 1000, {}), "x" * 1000),
    ],
    ids=[
        "missing",
        "raising",
        "none",
        "scalar",
        "list",
        "dict",
        "empty",
        "whitespace",
        "case",
        "case_cafef",
        "unknown",
        "url",
        "overlong",
    ],
)
def test_malicious_source_names_are_custom_zero_call_and_bounded(
    label, source_factory, raw_text
):
    source = source_factory()
    with pytest.raises(EmptyData, match=r"^no usable annual fiscal periods") as caught:
        metrics("TESTCO", period="annual", source=source)
    assert str(caught.value) == _EMPTY_METRICS_MESSAGE
    assert raw_text not in str(caught.value)
    coverage = explain_metric_coverage("TESTCO", period="annual", source=source)

    assert coverage.periods == ()
    assert len(coverage.statement_fetches) == 3
    assert all(o.status is StatementCoverageStatus.NOT_SERVED for o in coverage.statement_fetches)
    assert all(o.source == "custom" for o in coverage.statement_fetches)
    assert all(
        o.detail == f"statement {o.statement.value} not served by source 'custom'"
        for o in coverage.statement_fetches
    )
    assert getattr(source, "calls", []) == []
    attrs = coverage.to_dataframe().attrs
    assert attrs["statement_fetches"] == (
        ("income", "not_served", "custom", "statement income not served by source 'custom'"),
        ("balance", "not_served", "custom", "statement balance not served by source 'custom'"),
        ("cashflow", "not_served", "custom", "statement cashflow not served by source 'custom'"),
    )
    public = repr(coverage) + repr(attrs)
    assert raw_text not in public, label


def test_default_cashflow_failure_never_invokes_cafef(monkeypatch):
    def _cashflow_boom(symbol, period, is_bank, limit):
        raise EmptyData("cashflow unavailable")

    vndirect = _Source(
        "vndirect",
        {
            StatementType.INCOME: (_report(StatementType.INCOME, "vndirect"),),
            StatementType.BALANCE: (_report(StatementType.BALANCE, "vndirect"),),
            StatementType.CASHFLOW: _cashflow_boom,
        },
    )
    cafef = _Source(
        "cafef",
        {
            StatementType.INCOME: (_report(StatementType.INCOME, "cafef"),),
            StatementType.BALANCE: (_report(StatementType.BALANCE, "cafef"),),
            StatementType.CASHFLOW: (_report(StatementType.CASHFLOW, "cafef"),),
        },
    )
    monkeypatch.setattr(
        "vnfin.fundamentals.default_fundamental_sources",
        lambda **kwargs: [vndirect, cafef],
    )
    reports = metrics("TESTCO", period="annual", is_bank=False)
    assert len(reports) == 1
    cashflow = _status_by_statement(reports[0].statement_sources)[StatementType.CASHFLOW]
    assert cashflow.status is StatementCoverageStatus.SOURCE_ERROR
    assert vndirect.calls == [
        ("TESTCO", StatementType.INCOME),
        ("TESTCO", StatementType.BALANCE),
        ("TESTCO", StatementType.CASHFLOW),
    ]
    assert cafef.calls == []


def test_incapable_custom_fallback_is_filtered_before_a_failed_allowed_source():
    def _boom(symbol, period, is_bank, limit):
        raise EmptyData("upstream-secret")

    vndirect = _Source(
        "vndirect",
        {
            StatementType.INCOME: _boom,
            StatementType.BALANCE: _boom,
            StatementType.CASHFLOW: _boom,
        },
    )
    custom = _MissingNameSource()
    with pytest.raises(EmptyData, match=r"^no usable annual fiscal periods"):
        metrics("TESTCO", period="annual", sources=[vndirect, custom])
    coverage = explain_metric_coverage(
        "TESTCO", period="annual", sources=[vndirect, custom]
    )
    assert all(
        outcome.status is StatementCoverageStatus.SOURCE_ERROR
        for outcome in coverage.statement_fetches
    )
    assert custom.calls == []


def test_cafef_custom_cashflow_is_not_served_with_bounded_composite():
    cafef = _Source(
        "cafef",
        {
            StatementType.INCOME: (_report(StatementType.INCOME, "cafef"),),
            StatementType.BALANCE: (_report(StatementType.BALANCE, "cafef"),),
        },
    )
    custom = _MissingNameSource()
    coverage = explain_metric_coverage(
        "TESTCO", period="annual", sources=[cafef, custom]
    )
    outcomes = _status_by_statement(coverage.statement_fetches)
    cashflow = outcomes[StatementType.CASHFLOW]
    assert cashflow.status is StatementCoverageStatus.NOT_SERVED
    assert cashflow.source == "cafef,custom"
    assert cashflow.detail == (
        "statement cashflow not served by source 'cafef,custom'"
    )
    assert [statement for _, statement in cafef.calls] == [
        StatementType.INCOME,
        StatementType.BALANCE,
    ]
    assert custom.calls == []


@pytest.mark.parametrize(
    "bad_source,raw_text",
    [
        ("https://example.invalid/?token=provenance-secret", "provenance-secret"),
        ("x" * 1000, "x" * 1000),
        (None, None),
        (["non-string-secret"], "non-string-secret"),
        ({"token": "dict-provenance-secret"}, "dict-provenance-secret"),
    ],
)
def test_mismatched_report_provenance_is_sanitized(
    bad_source, raw_text
):
    source = _Source(
        "vndirect",
        {
            StatementType.INCOME: (_report(StatementType.INCOME, bad_source),),
            StatementType.BALANCE: (_report(StatementType.BALANCE, "vndirect"),),
            StatementType.CASHFLOW: (_report(StatementType.CASHFLOW, "vndirect"),),
        },
    )
    report = metrics("TESTCO", period="annual", source=source)[0]
    income = _status_by_statement(report.statement_sources)[StatementType.INCOME]
    assert income.status is StatementCoverageStatus.SOURCE_ERROR
    assert income.source is None
    assert income.detail == "recoverable source error"
    assert report.get("net_revenue").reason == (
        "statement income unavailable: recoverable source error"
    )
    attrs = report.to_dataframe().attrs
    assert attrs["statement_sources"][0] == (
        "income",
        "source_error",
        None,
        "recoverable source error",
    )
    if raw_text is not None:
        assert raw_text not in repr(report)
        assert raw_text not in repr(attrs)

    coverage = explain_metric_coverage("TESTCO", period="annual", source=source)
    aggregate_income = _status_by_statement(coverage.statement_fetches)[
        StatementType.INCOME
    ]
    assert aggregate_income.status is StatementCoverageStatus.SOURCE_ERROR
    assert aggregate_income.source is None
    assert aggregate_income.detail == "recoverable source error"
    coverage_attrs = coverage.to_dataframe().attrs
    assert coverage_attrs["statement_fetches"][0] == (
        "income",
        "source_error",
        None,
        "recoverable source error",
    )
    if raw_text is not None:
        public = repr(coverage) + repr(coverage_attrs)
        assert raw_text not in public


@pytest.mark.parametrize(
    "bad_source",
    [
        "https://example.invalid/?token=raised-secret",
        "x" * 1000,
        None,
        ["non-string-raised-secret"],
        {"token": "dict-raised-secret"},
    ],
)
def test_all_mismatched_report_provenance_raises_sanitized_message(bad_source):
    source = _Source(
        "vndirect",
        {
            statement: (_report(statement, bad_source),)
            for statement in (
                StatementType.INCOME,
                StatementType.BALANCE,
                StatementType.CASHFLOW,
            )
        },
    )
    with pytest.raises(EmptyData, match=r"^no usable annual fiscal periods") as caught:
        metrics("TESTCO", period="annual", source=source)
    assert str(caught.value) == _EMPTY_METRICS_MESSAGE
    assert repr(bad_source) not in str(caught.value)


def test_metric_coverage_appends_defaulted_statement_fetches_without_breaking_old_constructors():
    coverage = MetricCoverage("TESTCO", Period.ANNUAL, (), ("no_fiscal_periods",))
    assert coverage.statement_fetches == ()
