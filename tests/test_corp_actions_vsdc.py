"""TDD suite for the VSDC cash-dividend corp-actions adapter (issue #163).

All HTTP is stubbed: the pure parser is fixture-tested, and the discovery/adapter
paths inject an ``http_get`` mapping announcement id -> committed fixture HTML. No
network call is ever made (synthetic fixtures only — fabricated values).
"""
from __future__ import annotations

import math
from datetime import date, datetime
from pathlib import Path

import pytest

from vnfin.corp_actions import (
    CashDividendEvent,
    CorpActionSource,
    DividendHistory,
    VsdcCashDividendSource,
    dividends,
)
from vnfin.corp_actions.base import VN_TZ
from vnfin.exceptions import InvalidData, SourceUnavailable

_FIXTURES = Path(__file__).parent / "fixtures" / "corp_actions"


def _fx(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


# Map the fabricated sidebar IDs (from vsdc_sidebar_same_org.html) to fixtures so a
# stub http_get can resolve a sidebar crawl deterministically.
_CLEAN = "vsdc_cash_dividend_clean.html"
_THOIGIAN = "vsdc_cash_dividend_paylabel_thoigian.html"
_BUNDLED = "vsdc_bundled_voting_plus_cash.html"
_WARRANT = "vsdc_non_dividend_warrant.html"
_DEGRADED = "vsdc_cash_dividend_degraded.html"
_SIDEBAR = "vsdc_sidebar_same_org.html"


# --------------------------------------------------------------------------- #
# Parser (pure, no network)
# --------------------------------------------------------------------------- #
def test_parse_clean_cash_dividend():
    """#9.1 — the clean fixture parses to exactly the documented oracle values."""
    src = VsdcCashDividendSource()
    ev = src.parse_announcement(_fx(_CLEAN), announcement_id=197001)
    assert ev is not None
    assert ev.code == "TST"
    assert ev.kind == "CASH"
    assert ev.exchange == "HOSE"
    assert ev.record_date == date(2024, 3, 15)
    assert ev.pay_date == date(2024, 4, 10)
    assert ev.ratio_pct == 12.0
    assert ev.cash_per_share == 1200.0
    assert ev.div_year == 2024
    assert ev.source == "vsdc"
    assert ev.announcement_id == 197001
    # provider publish time from time-newstcph (VN tz)
    assert ev.as_of == datetime(2024, 3, 2, 9, 36, 57, tzinfo=VN_TZ)
    # ex-date is held in v1; always None + always tokenized.
    assert ev.ex_date is None
    assert "ex_date_unavailable" in ev.warnings
    # a clean parse must NOT flag degraded.
    assert "vsdc_parse_degraded" not in ev.warnings


def test_parse_paylabel_thoigian():
    """#9.2 — 'Thời gian thực hiện:' is accepted as the pay-date label."""
    src = VsdcCashDividendSource()
    ev = src.parse_announcement(_fx(_THOIGIAN))
    assert ev is not None
    assert ev.code == "TST"
    assert ev.record_date == date(2022, 6, 20)
    assert ev.pay_date == date(2022, 7, 18)
    assert ev.ratio_pct == 14.0
    assert ev.cash_per_share == 1400.0
    assert ev.div_year == 2022
    assert "vsdc_parse_degraded" not in ev.warnings


def test_parse_bundled_picks_cash_line_ignores_voting():
    """#9.3 — bundled voting+cash page: select the CASH ratio via the parenthetical."""
    src = VsdcCashDividendSource()
    ev = src.parse_announcement(_fx(_BUNDLED))
    assert ev is not None
    assert ev.code == "BAR"
    assert ev.exchange == "HNX"
    assert ev.record_date == date(2025, 6, 25)
    assert ev.pay_date == date(2025, 7, 7)
    assert ev.ratio_pct == 5.0
    assert ev.cash_per_share == 500.0
    assert ev.div_year == 2025
    assert "vsdc_parse_degraded" not in ev.warnings


def test_parse_non_dividend_warrant_returns_none():
    """#9.4 — covered-warrant page with the trap word 'Bằng tiền' -> None, no degraded token."""
    src = VsdcCashDividendSource()
    ev = src.parse_announcement(_fx(_WARRANT))
    assert ev is None  # correctly "not a cash dividend"


def test_parse_degraded_emits_token_without_amounts():
    """#9.5 — cash-dividend intent + record date but unparseable ratio -> degraded event."""
    src = VsdcCashDividendSource()
    ev = src.parse_announcement(_fx(_DEGRADED))
    assert ev is not None
    assert ev.code == "TST"
    assert ev.record_date == date(2024, 9, 10)
    assert ev.cash_per_share is None
    assert ev.ratio_pct is None
    assert "vsdc_parse_degraded" in ev.warnings
    # still always carries the held-ex-date token
    assert ev.ex_date is None
    assert "ex_date_unavailable" in ev.warnings


def test_parse_pairs_by_class_not_column_width():
    """#9.6 — label->value pairing is by item-info/item-info-main class, never col-md width.

    The fixtures use col-md-4/col-md-8; this regression mutates the widths to an
    asymmetric 3/9 (and 7/5) split and asserts the SAME values still parse — proving the
    parser keys on the item-info classes, not the column geometry.
    """
    html = _fx(_CLEAN)
    mutated = html.replace("col-md-4 item-info", "col-md-3 item-info").replace(
        "col-md-8 item-info item-info-main", "col-md-9 item-info item-info-main"
    )
    assert "col-md-3 item-info" in mutated and "col-md-9 item-info" in mutated
    src = VsdcCashDividendSource()
    ev = src.parse_announcement(mutated)
    assert ev is not None
    assert ev.exchange == "HOSE"
    assert ev.record_date == date(2024, 3, 15)
    assert ev.ratio_pct == 12.0
    assert ev.cash_per_share == 1200.0


# --------------------------------------------------------------------------- #
# Models (boundary validation)
# --------------------------------------------------------------------------- #
def _valid_event_kwargs(**overrides):
    base = dict(
        code="TST",
        kind="CASH",
        cash_per_share=1200.0,
        ratio_pct=12.0,
        ex_date=None,
        record_date=date(2024, 3, 15),
        pay_date=date(2024, 4, 10),
        div_year=2024,
        source="vsdc",
        as_of=datetime(2024, 3, 2, 9, 36, 57, tzinfo=VN_TZ),
        exchange="HOSE",
        announcement_id=197001,
        warnings=("ex_date_unavailable",),
    )
    base.update(overrides)
    return base


def test_event_rejects_bad_kind():
    """#9.7 — kind != 'CASH' is rejected at the model boundary."""
    with pytest.raises(InvalidData):
        CashDividendEvent(**_valid_event_kwargs(kind="STOCK"))


def test_event_rejects_empty_code():
    with pytest.raises(InvalidData):
        CashDividendEvent(**_valid_event_kwargs(code="   "))


@pytest.mark.parametrize("bad", [0.0, -5.0, float("nan"), float("inf"), True])
def test_event_rejects_nonpositive_or_bool_cash(bad):
    """#9.7 — cash_per_share when present must be finite and > 0 (reject bool/NaN/<=0)."""
    with pytest.raises(InvalidData):
        CashDividendEvent(**_valid_event_kwargs(cash_per_share=bad))


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), True])
def test_event_rejects_nonpositive_or_bool_ratio(bad):
    with pytest.raises(InvalidData):
        CashDividendEvent(**_valid_event_kwargs(ratio_pct=bad))


def test_event_rejects_non_date_record():
    with pytest.raises(InvalidData):
        CashDividendEvent(**_valid_event_kwargs(record_date="2024-03-15"))


def test_event_requires_ex_date_unavailable_token_when_ex_date_none():
    """#9.8 — an event with ex_date=None must carry 'ex_date_unavailable' (enforced)."""
    with pytest.raises(InvalidData):
        CashDividendEvent(**_valid_event_kwargs(warnings=()))


def test_event_allows_degraded_none_amounts():
    """A degraded event (None amounts) is valid at the boundary."""
    ev = CashDividendEvent(
        **_valid_event_kwargs(
            cash_per_share=None,
            ratio_pct=None,
            warnings=("ex_date_unavailable", "vsdc_parse_degraded"),
        )
    )
    assert ev.cash_per_share is None
    assert ev.ratio_pct is None


# --------------------------------------------------------------------------- #
# Discovery + adapter (inject http_get mapping id -> fixture HTML)
# --------------------------------------------------------------------------- #
def test_discover_same_org_ids():
    """#9.9 — extract sidebar /vi/ad/{id} IDs, ignoring nav/category links."""
    src = VsdcCashDividendSource()
    ids = src.discover_same_org_ids(_fx(_SIDEBAR))
    assert ids == (100001, 100002, 100003)


def _stub_http_get(mapping):
    """Build a 3-arg GET stub that maps a /vi/ad/{id} URL to fixture HTML."""

    def http_get(url, params=None, headers=None):
        # url = https://vsd.vn/vi/ad/{id}
        ann_id = int(url.rstrip("/").rsplit("/", 1)[-1])
        if ann_id not in mapping:
            raise SourceUnavailable(f"stub: no fixture for id {ann_id}")
        return _fx(mapping[ann_id])

    return http_get


def test_dividends_seed_then_sidebar_crawl():
    """#9.10 — dividends('TST', seed=...) returns a DividendHistory of TST cash events."""
    # seed page = sidebar fixture (TST, 2023 div) linking 100001/100002/100003.
    mapping = {
        197900: _SIDEBAR,   # seed: TST 2023 cash div + sidebar
        100001: _THOIGIAN,  # TST 2022 cash div
        100002: _WARRANT,   # not a dividend (and not even TST -> excluded)
        100003: _CLEAN,     # TST 2024 cash div
    }
    src = VsdcCashDividendSource(http_get=_stub_http_get(mapping))
    hist = src.dividends("TST", seed_id=197900)
    assert isinstance(hist, DividendHistory)
    assert hist.code == "TST"
    assert hist.source == "vsdc"
    assert hist.currency == "VND"
    # list-level partial token always present in v1
    assert "corp_action_source_partial" in hist.warnings
    # the three TST cash events (seed 2023 + 2022 + 2024), warrant excluded.
    record_dates = {e.record_date for e in hist.events}
    assert date(2023, 5, 10) in record_dates
    assert date(2022, 6, 20) in record_dates
    assert date(2024, 3, 15) in record_dates
    assert all(e.code == "TST" for e in hist.events)
    assert all("ex_date_unavailable" in e.warnings for e in hist.events)
    # deterministic order by record_date
    assert [e.record_date for e in hist.events] == sorted(e.record_date for e in hist.events)
    # provider-derived list as_of = max event as_of (never fabricated now())
    assert hist.as_of == max(e.as_of for e in hist.events)


def test_dividends_date_range_filter():
    """#9.11 — start/end filter events by record_date."""
    mapping = {197900: _SIDEBAR, 100001: _THOIGIAN, 100002: _WARRANT, 100003: _CLEAN}
    src = VsdcCashDividendSource(http_get=_stub_http_get(mapping))
    # window covering only 2024 -> only the clean (2024-03-15) event survives.
    hist = src.dividends(
        "TST", seed_id=197900, start=date(2024, 1, 1), end=date(2024, 12, 31)
    )
    assert [e.record_date for e in hist.events] == [date(2024, 3, 15)]


def test_dividends_factory_matches_source():
    """The package-level factory builds a VsdcCashDividendSource and returns the same shape."""
    mapping = {197900: _SIDEBAR, 100001: _THOIGIAN, 100002: _WARRANT, 100003: _CLEAN}
    hist = dividends("TST", seed_id=197900, http_get=_stub_http_get(mapping))
    assert isinstance(hist, DividendHistory)
    assert hist.code == "TST"
    assert "corp_action_source_partial" in hist.warnings


def test_transport_failure_wrapped_as_source_unavailable():
    """#9.12 — a transport error from fetch surfaces as SourceUnavailable."""

    def boom(url, params=None, headers=None):
        raise ConnectionError("network down")

    src = VsdcCashDividendSource(http_get=boom)
    with pytest.raises(SourceUnavailable):
        src.fetch_announcement(197001)


def test_corp_action_source_is_a_port():
    assert issubclass(VsdcCashDividendSource, CorpActionSource)
    assert VsdcCashDividendSource.name == "vsdc"


# --------------------------------------------------------------------------- #
# Diagnostic
# --------------------------------------------------------------------------- #
def test_explain_corp_actions_coverage_offline():
    """#9.13 — explain_corp_actions_coverage discloses cash-only + ex-date-unavailable + v2 scope."""
    from vnfin.diagnostics import (
        RequestDiagnostic,
        explain_corp_actions_coverage,
        source_capabilities,
    )

    d = explain_corp_actions_coverage()
    assert isinstance(d, RequestDiagnostic)
    assert d.domain == "corp_actions"
    blob = " ".join(d.notes + d.suggested_actions).lower()
    assert "cash" in blob
    assert "ex-date" in blob or "ex date" in blob
    assert "vsdc" in blob
    # STOCK/RIGHTS/BONUS deferred to v2
    assert "v2" in blob
    # capability registry includes the corp-actions leg
    caps = source_capabilities()
    assert any(c.domain == "corp_actions" for c in caps)
    # these warning tokens belong on results, not on the diagnostic notes/actions.
    assert "corp_action_source_partial" not in blob
    assert "vsdc_parse_degraded" not in blob
