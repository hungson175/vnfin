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
def _report(symbol, source, value, fiscal_date="2025-12-31"):
    fd = datetime.strptime(fiscal_date, "%Y-%m-%d").date()
    return FinancialReport(
        symbol=symbol,
        statement_type=StatementType.INCOME,
        period=Period.ANNUAL,
        fiscal_date=fd,
        items=(LineItem(item_code="11000", name="net revenue", value=value, value_unit="VND"),),
        source=source,
        currency="VND",
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


def test_failover_passes_is_bank_and_limit_through():
    captured = {}

    class Recorder(FakeSource):
        def get_financials(self, symbol, statement, period, *, is_bank=False, limit=8):
            captured["is_bank"] = is_bank
            captured["limit"] = limit
            return super().get_financials(symbol, statement, period, is_bank=is_bank, limit=limit)

    primary = Recorder("vndirect", result=(_report("ZZBANK", "vndirect", 5.0),))
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
