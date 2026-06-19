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

from datetime import date, datetime, timedelta, timezone

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


def test_fundamental_invalid_source_marker_cannot_collide_with_source_name():
    # #126 B4: even if a (pathological) producing source is named exactly like the
    # old string marker, a malformed list report.source must NOT be accepted. The
    # invalid-source sentinel is a tuple, which can never equal a string name.
    colliding = "<non-string source: list>"
    primary = FakeSource(colliding, result=(_report("TESTCO", ["vndirect"], 1.0),))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "cafef"

    # And with no backup it must raise cleanly, never accept the malformed result.
    solo = FailoverFundamentalClient(
        [FakeSource(colliding, result=(_report("TESTCO", ["vndirect"], 1.0),))]
    )
    with pytest.raises(AllSourcesFailed):
        solo.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)


# Issue #125 (reopen) — malformed inner line-item object (reject before deref).
@pytest.mark.parametrize("bad_item", [object(), None, {}, 42, "x"], ids=["object", "none", "dict", "int", "str"])
def test_rejects_malformed_line_item_object(bad_item):
    _assert_fundamental_rejected(
        lambda: _report_with_items([bad_item]), "malformed line item object"
    )


def test_malformed_line_item_object_falls_over_to_backup():
    primary = FakeSource("vndirect", result=(_report_with_items([object()]),))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "cafef"
    assert primary.calls == 1 and backup.calls == 1


# --- Issue #129: fundamentals report fiscal_date must be a plain datetime.date ---
def _report_with_fiscal_date(fiscal_date):
    return FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.INCOME,
        period=Period.ANNUAL,
        fiscal_date=fiscal_date,
        items=(LineItem(item_code="11000", name="net revenue", value=1.0, value_unit="VND"),),
        source="vndirect",
        currency="VND",
    )


@pytest.mark.parametrize(
    "bad_fd",
    [
        datetime(2025, 12, 31),
        datetime(2025, 12, 31, tzinfo=timezone.utc),
        "2025-12-31",
        None,
        20251231,
        [],
    ],
    ids=["naive_datetime", "aware_datetime", "str", "none", "int", "list"],
)
def test_rejects_malformed_report_fiscal_date(bad_fd):
    _assert_fundamental_rejected(lambda: _report_with_fiscal_date(bad_fd), "malformed fiscal_date")


def test_malformed_fiscal_date_falls_over_to_backup():
    primary = FakeSource("vndirect", result=(_report_with_fiscal_date(datetime(2025, 12, 31)),))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "cafef"


def test_accepts_plain_report_fiscal_date():
    primary = FakeSource("vndirect", result=(_report_with_fiscal_date(date(2025, 12, 31)),))
    client = FailoverFundamentalClient([primary])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].fiscal_date == date(2025, 12, 31)


def test_malformed_fiscal_date_takes_precedence_over_empty_items():
    # Ordering: a malformed fiscal_date with zero items must report fiscal_date,
    # proving the #129 guard runs before the zero-line check.
    bad = FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.INCOME,
        period=Period.ANNUAL,
        fiscal_date=datetime(2025, 12, 31),
        items=(),
        source="vndirect",
        currency="VND",
    )
    _assert_fundamental_rejected(lambda: bad, "malformed fiscal_date")


# Issue #127 — present-malformed fundamentals fetched_at_utc rejected (per report; None allowed).
def _report_with_ts(fetched_at_utc):
    return FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.INCOME,
        period=Period.ANNUAL,
        fiscal_date=date(2025, 12, 31),
        items=(LineItem(item_code="11000", name="net revenue", value=1.0, value_unit="VND"),),
        source="vndirect",
        currency="VND",
        fetched_at_utc=fetched_at_utc,
    )


@pytest.mark.parametrize(
    "bad_ts",
    [datetime(2026, 6, 19, 3), datetime(2026, 6, 19, 10, tzinfo=timezone(timedelta(hours=7))), "2026-06-19T03:00:00Z", 1718766000],
    ids=["naive", "non_utc", "str", "int"],
)
def test_rejects_malformed_fundamental_fetched_at_utc(bad_ts):
    _assert_fundamental_rejected(lambda: _report_with_ts(bad_ts), "fetched_at_utc")


def test_accepts_none_fundamental_fetched_at_utc():
    primary = FakeSource("vndirect", result=(_report_with_ts(None),))
    client = FailoverFundamentalClient([primary])
    assert client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)[0].source == "vndirect"


# Issue #128 — fundamentals warnings must be tuple[str, ...] (per report).
def _report_with_warnings(warnings):
    return FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.INCOME,
        period=Period.ANNUAL,
        fiscal_date=date(2025, 12, 31),
        items=(LineItem(item_code="11000", name="net revenue", value=1.0, value_unit="VND"),),
        source="vndirect",
        currency="VND",
        warnings=warnings,
    )


@pytest.mark.parametrize(
    "bad_warnings",
    [None, ["w"], "w", (1,), (None,)],
    ids=["none", "list", "str", "int_member", "none_member"],
)
def test_rejects_malformed_fundamental_warnings(bad_warnings):
    _assert_fundamental_rejected(lambda: _report_with_warnings(bad_warnings), "warnings")


def test_accepts_valid_fundamental_warnings():
    primary = FakeSource("vndirect", result=(_report_with_warnings(("a note",)),))
    client = FailoverFundamentalClient([primary])
    assert client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)[0].source == "vndirect"


# --- Issue #130: returned report metadata (is_bank/model_type/provider_symbol) ---
def _report_meta(*, is_bank=False, model_type=1, provider_symbol="TESTCO"):
    return FinancialReport(
        symbol="TESTCO",
        statement_type=StatementType.INCOME,
        period=Period.ANNUAL,
        fiscal_date=date(2025, 12, 31),
        items=(LineItem(item_code="11000", name="net revenue", value=1.0, value_unit="VND"),),
        source="vndirect",
        currency="VND",
        is_bank=is_bank,
        model_type=model_type,
        provider_symbol=provider_symbol,
    )


@pytest.mark.parametrize("bad", ["False", "true", 1, 0, [], {}, None], ids=["str_false", "str_true", "int1", "int0", "list", "dict", "none"])
def test_rejects_malformed_report_is_bank(bad):
    _assert_fundamental_rejected(lambda: _report_meta(is_bank=bad), "malformed is_bank")


@pytest.mark.parametrize(
    "bad",
    [True, False, 1.9, "1", "01", "+1", [], {}, "x", -1, 0, 4, 99, 104, 999],
    ids=["true", "false", "float", "s1", "s01", "splus1", "list", "dict", "sx", "neg1", "zero", "four", "n99", "n104", "n999"],
)
def test_rejects_malformed_report_model_type(bad):
    # #130 follow-up: model_type must be None or a canonical template id; arbitrary
    # non-bool ints (-1/0/4/99/104/999) are not real templates and are rejected.
    _assert_fundamental_rejected(lambda: _report_meta(model_type=bad), "malformed model_type")


@pytest.mark.parametrize("mt", [1, 2, 3, 101, 102, 103, None], ids=["c1", "c2", "c3", "b101", "b102", "b103", "none"])
def test_accepts_canonical_report_model_type(mt):
    primary = FakeSource("vndirect", result=(_report_meta(model_type=mt),))
    client = FailoverFundamentalClient([primary])
    out = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)[0]
    assert out.model_type == mt


@pytest.mark.parametrize("bad", [[], {}, True, 123, "", "   "], ids=["list", "dict", "bool", "int", "blank", "whitespace"])
def test_rejects_malformed_report_provider_symbol(bad):
    _assert_fundamental_rejected(lambda: _report_meta(provider_symbol=bad), "malformed provider_symbol")


def test_accepts_valid_report_metadata_incl_none_optionals():
    primary = FakeSource("vndirect", result=(_report_meta(is_bank=True, model_type=None, provider_symbol=None),))
    client = FailoverFundamentalClient([primary])
    out = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL, is_bank=True)[0]
    assert out.is_bank is True and out.model_type is None and out.provider_symbol is None


def test_malformed_report_metadata_falls_over_to_backup():
    primary = FakeSource("vndirect", result=(_report_meta(is_bank="False"),))
    backup = FakeSource("cafef", result=(_report("TESTCO", "cafef", 22.0),))
    client = FailoverFundamentalClient([primary, backup])
    reports = client.get_financials("TESTCO", StatementType.INCOME, Period.ANNUAL)
    assert reports[0].source == "cafef"
