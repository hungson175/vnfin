"""Offline unit tests for the #198 LIVE probe seams (B10 + R5/R9/R10/R16/R18).

The probe ``scripts/probe_corporate_itemcodes.py`` is a manually-invoked script,
NOT an importable package, so we load it by path with ``importlib`` and exercise
its pure helpers + the three legs with NO network — ``_raw_fetch`` is
monkeypatched to return synthetic envelopes, and the two adapter legs receive a
fake ``src``. These pin the probe's own fail-closed logic so the live evidence
tool cannot silently rot.

Clean-room: synthetic fixtures only; no vnstock / no derivative material.
"""
from __future__ import annotations

import importlib.util
import pathlib
from datetime import date
from decimal import Decimal

import pytest

from vnfin.fundamentals.models import Period, StatementType


# --------------------------------------------------------------------------- #
# Load the probe SCRIPT by path (it is not a package). Top-level imports are
# stdlib-only and main() is __main__-guarded, so import triggers no network.
# --------------------------------------------------------------------------- #
_PROBE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_corporate_itemcodes.py"
)


def _load_probe():
    spec = importlib.util.spec_from_file_location("probe_corporate_itemcodes", _PROBE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def probe():
    return _load_probe()


# =========================================================================== #
# _canonical_int — strict, Decimal-aware canonical non-negative int key (R18).
# =========================================================================== #
@pytest.mark.parametrize(
    "raw,expected",
    [
        (True, None),
        (1.9, None),
        (Decimal("1.9"), None),
        (Decimal("1.0"), 1),
        (Decimal("11000.9"), None),
        (Decimal("11000.0"), 11000),
        ("11000", 11000),
        ("011000", None),
        (-5, None),
        (1.0, 1),
    ],
)
def test_canonical_int(probe, raw, expected):
    assert probe._canonical_int(raw) == expected


# =========================================================================== #
# _valid_iso — exact unpadded YYYY-MM-DD AND a real calendar date.
# =========================================================================== #
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2025-12-31", True),
        ("2025-99-99", False),
        ("2024-02-30", False),
        (" 2025-12-31", False),
        (date(2025, 12, 31), False),
    ],
)
def test_valid_iso(probe, raw, expected):
    assert probe._valid_iso(raw) is expected


# =========================================================================== #
# _row_identity_ok — code / ANNUAL cadence / EXACT template (strict model).
# =========================================================================== #
def _idrow(code="VIC", report_type="ANNUAL", model_type=1):
    return {"code": code, "reportType": report_type, "modelType": model_type}


def test_row_identity_ok_exact_match(probe):
    assert probe._row_identity_ok(_idrow(), "VIC", 1) is True


def test_row_identity_ok_wrong_code(probe):
    assert probe._row_identity_ok(_idrow(code="HPG"), "VIC", 1) is False


def test_row_identity_ok_wrong_report_type(probe):
    assert probe._row_identity_ok(_idrow(report_type="QUARTER"), "VIC", 1) is False


def test_row_identity_ok_wrong_model(probe):
    assert probe._row_identity_ok(_idrow(model_type=2), "VIC", 1) is False


def test_row_identity_ok_fractional_decimal_model_rejected(probe):
    assert probe._row_identity_ok(_idrow(model_type=Decimal("1.9")), "VIC", 1) is False


def test_row_identity_ok_integral_decimal_model_ok(probe):
    assert probe._row_identity_ok(_idrow(model_type=Decimal("1.0")), "VIC", 1) is True


# =========================================================================== #
# _raw_newest_group_oracle — finite, validated, fail-closed newest-date group.
# _raw_fetch monkeypatched to serve page envelopes by requested page.
# =========================================================================== #
_A, _B = "2025-12-31", "2024-12-31"


def _prow(fd, item_code, value, *, code="VIC", report_type="ANNUAL", model_type=1):
    return {
        "code": code,
        "itemCode": item_code,
        "reportType": report_type,
        "modelType": model_type,
        "numericValue": value,
        "fiscalDate": fd,
    }


def _penv(rows, *, current_page=1, total_pages=1, include_total_pages=True):
    env = {"data": rows, "currentPage": current_page, "size": len(rows)}
    if include_total_pages:
        env["totalPages"] = total_pages
    return env


def _patch_fetch(probe, monkeypatch, pages_by_page):
    """Route ``_raw_fetch`` by requested ``page`` (page defaults to 1)."""

    def _fake(sym, model, *, size=300, page=None):
        return pages_by_page[page if page is not None else 1]

    monkeypatch.setattr(probe, "_raw_fetch", _fake)


def test_oracle_happy_path(probe, monkeypatch):
    pages = {1: _penv([_prow(_A, 12700, 100), _prow(_A, 13000, 50)], total_pages=1)}
    _patch_fetch(probe, monkeypatch, pages)
    built = probe._raw_newest_group_oracle("VIC", 1)
    assert built is not None
    newest_fd, oracle = built
    assert newest_fd == _A
    assert oracle == {"12700": Decimal("100"), "13000": Decimal("50")}


def test_oracle_premature_empty_page2(probe, monkeypatch):
    pages = {
        1: _penv([_prow(_A, 12700, 100)], current_page=1, total_pages=2),
        2: _penv([], current_page=2, include_total_pages=False),
    }
    _patch_fetch(probe, monkeypatch, pages)
    assert probe._raw_newest_group_oracle("VIC", 1) is None


def test_oracle_duplicate_code_in_newest_group(probe, monkeypatch):
    pages = {1: _penv([_prow(_A, 12700, 100), _prow(_A, 12700, 101)], total_pages=1)}
    _patch_fetch(probe, monkeypatch, pages)
    assert probe._raw_newest_group_oracle("VIC", 1) is None


def test_oracle_out_of_order_boundary_date(probe, monkeypatch):
    # Older date B before newer date A in the raw stream -> not strictly descending.
    pages = {1: _penv([_prow(_B, 12700, 90), _prow(_A, 12700, 100)], total_pages=1)}
    _patch_fetch(probe, monkeypatch, pages)
    assert probe._raw_newest_group_oracle("VIC", 1) is None


def test_oracle_newest_date_reappearance(probe, monkeypatch):
    # A ... B (closes A) ... A again -> reappearance of the closed newest date.
    pages = {
        1: _penv(
            [_prow(_A, 12700, 100), _prow(_B, 12700, 90), _prow(_A, 13000, 50)],
            total_pages=1,
        )
    }
    _patch_fetch(probe, monkeypatch, pages)
    assert probe._raw_newest_group_oracle("VIC", 1) is None


def test_oracle_non_int_total_pages(probe, monkeypatch):
    env = {"data": [_prow(_A, 12700, 100)], "currentPage": 1, "totalPages": 2.0, "size": 1}
    _patch_fetch(probe, monkeypatch, {1: env})
    assert probe._raw_newest_group_oracle("VIC", 1) is None


def test_oracle_malformed_calendar_date(probe, monkeypatch):
    pages = {1: _penv([_prow("2025-99-99", 12700, 100)], total_pages=1)}
    _patch_fetch(probe, monkeypatch, pages)
    assert probe._raw_newest_group_oracle("VIC", 1) is None


def test_oracle_raw_identity_mismatch(probe, monkeypatch):
    # Wrong model tag on the row -> identity mismatch -> fail closed.
    pages = {1: _penv([_prow(_A, 12700, 100, model_type=999)], total_pages=1)}
    _patch_fetch(probe, monkeypatch, pages)
    assert probe._raw_newest_group_oracle("VIC", 1) is None


# =========================================================================== #
# leg_b_adapter — asserts the FULL provenance tuple, not just code presence.
# =========================================================================== #
class _FakeReport:
    def __init__(self, statement_type, model_type, items, *, is_bank=False, source="vndirect"):
        self.statement_type = statement_type
        self.model_type = model_type
        self.is_bank = is_bank
        self.source = source
        self._items = items

    def get(self, code):
        return self._items.get(code)


class _FakeSrc:
    def __init__(self, by_statement):
        self._by = by_statement

    def get_financials(self, sym, statement, period, *, is_bank=False, limit=1):
        rep = self._by.get(statement)
        return [rep] if rep is not None else []


def test_leg_b_rejects_bogus_model_type(probe):
    # A report tagged model_type=999 (headline codes present) must FAIL.
    balance = _FakeReport(
        StatementType.BALANCE, 999, {"12700": 1.0, "13000": 1.0, "14000": 1.0}
    )
    income = _FakeReport(
        StatementType.INCOME, 2, {"21001": 1.0, "23800": 1.0, "23003": 1.0}
    )
    src = _FakeSrc({StatementType.BALANCE: balance, StatementType.INCOME: income})
    assert probe.leg_b_adapter(src, "VIC", StatementType, Period) is False


def test_leg_b_accepts_correct_tuples(probe):
    balance = _FakeReport(
        StatementType.BALANCE, 1, {"12700": 1.0, "13000": 1.0, "14000": 1.0}
    )
    income = _FakeReport(
        StatementType.INCOME, 2, {"21001": 1.0, "23800": 1.0, "23003": 1.0}
    )
    src = _FakeSrc({StatementType.BALANCE: balance, StatementType.INCOME: income})
    assert probe.leg_b_adapter(src, "VIC", StatementType, Period) is True


# =========================================================================== #
# leg_c_pagination value guard — fail closed on unverifiable-via-float values.
# _raw_newest_group_oracle monkeypatched to inject the oracle directly.
# =========================================================================== #
class _FakeLine:
    def __init__(self, item_code, value):
        self.item_code = item_code
        self.value = value


class _FakeBalanceReport:
    def __init__(self, fiscal_date, items):
        self.fiscal_date = fiscal_date
        self.items = items


class _FakeBalanceSrc:
    def __init__(self, report):
        self._report = report

    def get_financials(self, sym, statement, period, *, is_bank=False, limit=1):
        return [self._report] if self._report is not None else []


def _patch_oracle(probe, monkeypatch, newest_fd, oracle):
    monkeypatch.setattr(
        probe, "_raw_newest_group_oracle", lambda *a, **k: (newest_fd, oracle)
    )


@pytest.mark.parametrize(
    "bad_value",
    [
        Decimal(2 ** 53),            # >= 2**53
        Decimal(-(2 ** 53)),         # negative, abs >= 2**53
        Decimal("1.5"),              # non-integral
    ],
    ids=["ge_two53", "neg_ge_two53", "non_integral"],
)
def test_leg_c_value_guard_fails_closed(probe, monkeypatch, bad_value):
    oracle = {"12700": bad_value}
    _patch_oracle(probe, monkeypatch, _A, oracle)
    # A matching adapter report exists, but the guard must trip BEFORE trusting it.
    report = _FakeBalanceReport(date(2025, 12, 31), [_FakeLine("12700", float(bad_value))])
    src = _FakeBalanceSrc(report)
    assert probe.leg_c_pagination(src, StatementType, Period) is False


def test_leg_c_in_range_exact_match_passes(probe, monkeypatch):
    oracle = {"12700": Decimal("100"), "13000": Decimal("50")}
    _patch_oracle(probe, monkeypatch, _A, oracle)
    report = _FakeBalanceReport(
        date(2025, 12, 31),
        [_FakeLine("12700", 100.0), _FakeLine("13000", 50.0)],
    )
    src = _FakeBalanceSrc(report)
    assert probe.leg_c_pagination(src, StatementType, Period) is True
