"""TDD for vnfin.fundamentals domain failover (VNDirect -> CafeF).

Exercises the domain wiring that chains the primary (VNDirect) and backup
(CafeF) fundamental sources through the generic
:class:`vnfin.failover.FailoverClient` with the unit-homogeneity guard. Both
sources emit RAW VND, so the guard must accept the chain.

Fixtures are SYNTHETIC: a fake-source double that either returns a fabricated
``FinancialReport`` tuple or raises a ``SourceError`` to drive failover. No
network, no real provider rows.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from vnfin.exceptions import (
    AllSourcesFailed,
    EmptyData,
    SourceUnavailable,
    UnitMismatchError,
    VnfinError,
)
from vnfin.fundamentals import (
    CafeFFundamentalSource,
    FailoverFundamentalClient,
    FinancialReport,
    LineItem,
    Period,
    StatementType,
    VNDirectFundamentalSource,
    default_fundamental_client,
    default_fundamental_sources,
    get_financials,
)
from vnfin.fundamentals.base import FundamentalSource


# --------------------------------------------------------------------------- #
# Test doubles
# --------------------------------------------------------------------------- #
def _report(symbol, source, value, fiscal_date="2025-12-31", is_bank=False):
    fd = datetime.strptime(fiscal_date, "%Y-%m-%d").date()
    return FinancialReport(
        symbol=symbol,
        statement_type=StatementType.INCOME,
        period=Period.ANNUAL,
        fiscal_date=fd,
        items=(LineItem(item_code="11000", name="net revenue", value=value, value_unit="VND"),),
        source=source,
        currency="VND",
        is_bank=is_bank,
        fetched_at_utc=datetime.now(timezone.utc),
    )


class FakeSource(FundamentalSource):
    """A fundamental source double with a declared unit and scripted behavior."""

    def __init__(self, name, *, unit="VND", result=None, error=None):
        self._name = name
        self.unit = unit
        self._result = result
        self._error = error
        self.calls = 0

    @property
    def name(self):
        return self._name

    def get_financials(self, symbol, statement, period, *, is_bank=False, limit=8):
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._result


# --------------------------------------------------------------------------- #
# default_fundamental_sources()
# --------------------------------------------------------------------------- #
def test_default_sources_are_vndirect_then_cafef():
    sources = default_fundamental_sources()
    assert len(sources) == 2
    assert isinstance(sources[0], VNDirectFundamentalSource)
    assert isinstance(sources[1], CafeFFundamentalSource)


def test_default_sources_all_declare_raw_vnd_unit():
    for s in default_fundamental_sources():
        assert getattr(s, "unit", None) == "VND"


# --------------------------------------------------------------------------- #
# Unit-homogeneity guard
# --------------------------------------------------------------------------- #
def test_failover_accepts_same_unit_chain():
    primary = FakeSource("vndirect", unit="VND", result=(_report("TESTCO", "vndirect", 1.0),))
    backup = FakeSource("cafef", unit="VND", result=(_report("TESTCO", "cafef", 1.0),))
    client = FailoverFundamentalClient([primary, backup])
    assert len(client.sources) == 2
    assert client.unit == "VND"


def test_failover_rejects_mismatched_unit_chain():
    primary = FakeSource("vndirect", unit="VND", result=(_report("TESTCO", "vndirect", 1.0),))
    bad = FakeSource("weird", unit="USD", result=(_report("TESTCO", "weird", 1.0),))
    with pytest.raises(UnitMismatchError):
        FailoverFundamentalClient([primary, bad])


# --------------------------------------------------------------------------- #
# Failover behavior
# --------------------------------------------------------------------------- #
def test_primary_success_does_not_touch_backup():
    primary = FakeSource("vndirect", result=(_report("TESTCO", "vndirect", 11.0),))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "vndirect"
    assert primary.calls == 1
    assert backup.calls == 0


def test_fails_over_to_backup_on_transport_error():
    primary = FakeSource("vndirect", error=SourceUnavailable("down"))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "cafef"
    assert primary.calls == 1
    assert backup.calls == 1


def test_fails_over_to_backup_on_empty_data():
    primary = FakeSource("vndirect", error=EmptyData("no rows"))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "cafef"


def test_empty_tuple_result_is_rejected_and_falls_through():
    """A source returning an empty tuple (no reports) is treated as a miss."""
    primary = FakeSource("vndirect", result=())
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "cafef"
    assert primary.calls == 1
    assert backup.calls == 1


def test_all_sources_fail_raises_all_sources_failed():
    primary = FakeSource("vndirect", error=SourceUnavailable("down"))
    backup = FakeSource("cafef", error=EmptyData("empty"))
    client = FailoverFundamentalClient([primary, backup])
    with pytest.raises(AllSourcesFailed):
        client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_failover_accepts_generator_sources_without_dropping_primary():
    """Issue: __init__ consumed the first generator element before passing the
    sources to FailoverClient. A generator must be materialized first so the
    primary source is preserved and used."""
    primary = FakeSource("vndirect", result=(_report("TESTCO", "vndirect", 11.0),))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient((s for s in [primary, backup]))
    assert len(client.sources) == 2
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "vndirect"
    assert primary.calls == 1
    assert backup.calls == 0


def test_failover_passes_is_bank_and_limit_through():
    captured = {}

    class Recorder(FakeSource):
        def get_financials(self, symbol, statement, period, *, is_bank=False, limit=8):
            captured["is_bank"] = is_bank
            captured["limit"] = limit
            return super().get_financials(symbol, statement, period, is_bank=is_bank, limit=limit)

    primary = Recorder("vndirect", result=(_report("ZZBANK", "vndirect", 5.0, is_bank=True),))
    client = FailoverFundamentalClient([primary])
    client.get_financials("ZZBANK", StatementType.INCOME, Period.ANNUAL, is_bank=True, limit=3)
    assert captured == {"is_bank": True, "limit": 3}


def test_failover_default_is_bank_is_auto_sentinel():
    """With no is_bank arg, the client forwards the AUTO sentinel to sources so
    each adapter auto-detects bank vs corporate without the caller knowing."""
    from vnfin.fundamentals.base import AUTO

    captured = {}

    class Recorder(FakeSource):
        def get_financials(self, symbol, statement, period, *, is_bank=False, limit=8):
            captured["is_bank"] = is_bank
            return super().get_financials(symbol, statement, period, is_bank=is_bank, limit=limit)

    primary = Recorder("vndirect", result=(_report("TESTCO", "vndirect", 1.0),))
    client = FailoverFundamentalClient([primary])
    client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)  # no is_bank
    assert captured["is_bank"] is AUTO


# --------------------------------------------------------------------------- #
# default_fundamental_client() + module get_financials() failover
# --------------------------------------------------------------------------- #
def test_default_client_is_failover_over_default_sources():
    client = default_fundamental_client()
    assert isinstance(client, FailoverFundamentalClient)
    assert len(client.sources) == 2
    assert client.unit == "VND"


def test_get_financials_fails_over_when_sources_injected():
    primary = FakeSource("vndirect", error=SourceUnavailable("down"))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    reports = get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, sources=[primary, backup]
    )
    assert reports[0].source == "cafef"


def test_get_financials_still_accepts_single_source():
    """Back-compat: a single injected source still works (no failover needed)."""
    only = FakeSource("vndirect", result=(_report("TESTCO", "vndirect", 1.0),))
    reports = get_financials(
        "TESTCO", StatementType.INCOME, Period.ANNUAL, source=only
    )
    assert reports[0].source == "vndirect"


def test_get_financials_validates_bad_statement_before_sources():
    from vnfin.exceptions import VnfinError

    only = FakeSource("vndirect", result=(_report("TESTCO", "vndirect", 1.0),))
    with pytest.raises(VnfinError):
        get_financials("TESTCO", "nonsense", Period.ANNUAL, source=only)


# --------------------------------------------------------------------------- #
# Regression — issue #25: FailoverFundamentalClient must accept string statement
# and period values, not leak AttributeError/KeyError.
# --------------------------------------------------------------------------- #
def test_client_get_financials_accepts_string_statement_and_period():
    primary = FakeSource("vndirect", result=(_report("TESTCO", "vndirect", 1.0),))
    client = FailoverFundamentalClient([primary])
    reports = client.get_financials("TESTCO", "income", "annual")
    assert reports[0].source == "vndirect"
    assert primary.calls == 1


def test_client_get_financials_rejects_bad_statement_string():
    primary = FakeSource("vndirect", result=(_report("TESTCO", "vndirect", 1.0),))
    client = FailoverFundamentalClient([primary])
    with pytest.raises(VnfinError):
        client.get_financials("TESTCO", "bogus", "annual")


def test_client_get_financials_rejects_bad_period_string():
    primary = FakeSource("vndirect", result=(_report("TESTCO", "vndirect", 1.0),))
    client = FailoverFundamentalClient([primary])
    with pytest.raises(VnfinError):
        client.get_financials("TESTCO", "income", "quaterly")


# --- Batch-1 result guards --------------------------------------------------


def _assert_fundamental_rejected(report_factory, expected_substring, *, is_bank=False):
    client = FailoverFundamentalClient([FakeSource("vndirect", result=(report_factory(),))])
    with pytest.raises(AllSourcesFailed) as ei:
        client.get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=is_bank
        )
    assert expected_substring in ei.value.attempts[0].reason


def test_rejects_empty_line_items():
    empty = FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.INCOME,
        period=Period.ANNUAL,
        fiscal_date=date(2025, 12, 31),
        items=(),
        source="vndirect",
        currency="VND",
    )
    _assert_fundamental_rejected(lambda: empty, "no line items")


def test_rejects_returned_symbol_mismatch():
    _assert_fundamental_rejected(
        lambda: _report("OTHER", "vndirect", 1.0), "symbol mismatch"
    )


def test_rejects_returned_statement_type_mismatch():
    bad = FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.BALANCE,
        period=Period.ANNUAL,
        fiscal_date=date(2025, 12, 31),
        items=(LineItem(item_code="11000", name="x", value=1.0, value_unit="VND"),),
        source="vndirect",
        currency="VND",
    )
    _assert_fundamental_rejected(lambda: bad, "statement_type mismatch")


def test_rejects_returned_period_mismatch():
    bad = FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.INCOME,
        period=Period.QUARTER,
        fiscal_date=date(2025, 12, 31),
        items=(LineItem(item_code="11000", name="x", value=1.0, value_unit="VND"),),
        source="vndirect",
        currency="VND",
    )
    _assert_fundamental_rejected(lambda: bad, "period mismatch")


def test_rejects_unknown_period_for_non_ratio_statements():
    """Issue: Period.UNKNOWN is only valid for ratios. A source returning
    Period.UNKNOWN for an annual income request must be rejected."""
    bad = FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.INCOME,
        period=Period.UNKNOWN,
        fiscal_date=date(2025, 12, 31),
        items=(LineItem(item_code="11000", name="x", value=1.0, value_unit="VND"),),
        source="vndirect",
        currency="VND",
    )
    _assert_fundamental_rejected(lambda: bad, "period mismatch")


def test_rejects_returned_is_bank_mismatch():
    _assert_fundamental_rejected(
        lambda: _report("TESTCO", "vndirect", 1.0, is_bank=True),
        "is_bank mismatch",
        is_bank=False,
    )


def test_rejects_returned_currency_mismatch():
    bad = FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.INCOME,
        period=Period.ANNUAL,
        fiscal_date=date(2025, 12, 31),
        items=(LineItem(item_code="11000", name="x", value=1.0, value_unit="VND"),),
        source="vndirect",
        currency="USD",
    )
    _assert_fundamental_rejected(lambda: bad, "currency mismatch")


def test_rejects_returned_line_item_unit_mismatch():
    bad = FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.INCOME,
        period=Period.ANNUAL,
        fiscal_date=date(2025, 12, 31),
        items=(LineItem(item_code="11000", name="x", value=1.0, value_unit="USD"),),
        source="vndirect",
        currency="VND",
    )
    _assert_fundamental_rejected(lambda: bad, "value_unit mismatch")


# --- Issue #122: strict returned LineItem key/value guards -----------------
#
# FailoverFundamentalClient validated report identity/emptiness/value_unit but
# NOT the actual LineItem.item_code / value shape. A custom or future source can
# bypass the adapter parsers and return NaN/Infinity/bool/str values, blank/bool
# item codes, or duplicate-conflicting codes and still be treated as a clean
# failover success. The result guard must reject these before accepting a result.


def _report_with_items(items):
    return FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.INCOME,
        period=Period.ANNUAL,
        fiscal_date=date(2025, 12, 31),
        items=tuple(items),
        source="vndirect",
        currency="VND",
    )


@pytest.mark.parametrize(
    "bad_value",
    [float("nan"), float("inf"), float("-inf"), True, False, "1000", None, [1.0]],
    ids=["nan", "inf", "-inf", "bool_true", "bool_false", "str", "none", "list"],
)
def test_rejects_malformed_line_item_value(bad_value):
    _assert_fundamental_rejected(
        lambda: _report_with_items(
            [LineItem(item_code="11000", name="net revenue", value=bad_value, value_unit="VND")]
        ),
        "value",
    )


@pytest.mark.parametrize(
    "bad_code",
    ["", "   ", " 11000", "11000 ", " 11000 ", None, True, False, 11000, 11000.0, ["11000"]],
    ids=[
        "blank",
        "whitespace",
        "leading_space",
        "trailing_space",
        "both_spaces",
        "none",
        "bool_true",
        "bool_false",
        "int",
        "float",
        "list",
    ],
)
def test_rejects_malformed_line_item_code(bad_code):
    _assert_fundamental_rejected(
        lambda: _report_with_items(
            [LineItem(item_code=bad_code, name="net revenue", value=1.0, value_unit="VND")]
        ),
        "item_code",
    )


@pytest.mark.parametrize(
    "bad_name",
    [None, True, 123, 1.0, ["name"]],
    ids=["none", "bool", "int", "float", "list"],
)
def test_rejects_non_string_line_item_name(bad_name):
    _assert_fundamental_rejected(
        lambda: _report_with_items(
            [LineItem(item_code="11000", name=bad_name, value=1.0, value_unit="VND")]
        ),
        "name",
    )


def test_accepts_empty_line_item_name():
    """Relaxed policy: an empty human name is allowed (some provider codes have
    no label); only a non-string name is rejected."""
    primary = FakeSource(
        "vndirect",
        result=(
            _report_with_items(
                [LineItem(item_code="11000", name="", value=1.0, value_unit="VND")]
            ),
        ),
    )
    client = FailoverFundamentalClient([primary])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].items[0].name == ""


def test_rejects_duplicate_line_item_code_within_report():
    _assert_fundamental_rejected(
        lambda: _report_with_items(
            [
                LineItem(item_code="11000", name="net revenue", value=1.0, value_unit="VND"),
                LineItem(item_code="11000", name="net revenue", value=2.0, value_unit="VND"),
            ]
        ),
        "duplicate",
    )


def test_malformed_primary_line_items_falls_over_to_backup():
    """A primary returning malformed line items must be rejected and the backup
    (with clean items) used instead."""
    primary = FakeSource(
        "vndirect",
        result=(
            _report_with_items(
                [LineItem(item_code="11000", name="net revenue", value=float("nan"), value_unit="VND")]
            ),
        ),
    )
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "cafef"
    assert primary.calls == 1
    assert backup.calls == 1


def test_rejects_invalid_is_bank_string():
    client = FailoverFundamentalClient([FakeSource("vndirect", result=(_report("TESTCO", "vndirect", 1.0),))])
    with pytest.raises(VnfinError):
        client.get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank="False"
        )


def test_rejects_invalid_limit():
    client = FailoverFundamentalClient([FakeSource("vndirect", result=(_report("TESTCO", "vndirect", 1.0),))])
    with pytest.raises(VnfinError):
        client.get_financials(
            "TESTCO", StatementType.INCOME, Period.ANNUAL, limit="eight"
        )


# --- Issue #126: provenance — a report tuple stamped with a source that is not
# the producing source's name is rejected; failover continues. -----------------
def test_rejects_fundamental_provenance_mismatch_and_failsover():
    primary = FakeSource("vndirect", result=(_report("TESTCO", "claimed_backup", 1.0),))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "cafef"
    assert primary.calls == 1 and backup.calls == 1


def test_fundamental_provenance_match_is_accepted():
    primary = FakeSource("vndirect", result=(_report("TESTCO", "vndirect", 1.0),))
    client = FailoverFundamentalClient([primary])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "vndirect"


def test_rejects_fundamental_report_with_none_source():
    # #126 B2: a composite (report-tuple) result whose member source is None
    # cannot be attributed -> rejected; backup with valid provenance is used.
    primary = FakeSource("vndirect", result=(_report("TESTCO", None, 1.0),))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "cafef"


@pytest.mark.parametrize(
    "bad_source",
    [["vndirect"], {"vndirect"}, ("vndirect",), 123, None],
    ids=["list", "set", "tuple", "int", "none"],
)
def test_rejects_fundamental_unhashable_or_nonstring_source(bad_source):
    # #126 B3: a typed FinancialReport whose source is non-string (incl.
    # unhashable list/set) must be rejected cleanly (never a raw TypeError from
    # building the provenance frozenset); a valid backup is used.
    primary = FakeSource("vndirect", result=(_report("TESTCO", bad_source, 1.0),))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "cafef"
    assert primary.calls == 1 and backup.calls == 1


def test_single_source_unhashable_fundamental_source_raises_clean():
    primary = FakeSource("vndirect", result=(_report("TESTCO", ["vndirect"], 1.0),))
    client = FailoverFundamentalClient([primary])
    with pytest.raises(AllSourcesFailed):
        client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


def test_valid_fundamental_tuple_all_sources_match_is_accepted():
    primary = FakeSource(
        "vndirect",
        result=(_report("TESTCO", "vndirect", 1.0), _report("TESTCO", "vndirect", 2.0, fiscal_date="2024-12-31")),
    )
    client = FailoverFundamentalClient([primary])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert {r.source for r in reports} == {"vndirect"}
