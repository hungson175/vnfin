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
# Crawl safety: bounded multi-hop BFS — visited-id dedup + cycle guard, and the
# never-silent truncation token (reviewer MUST-ADDS 2026-06-21). Synthetic
# page-graphs are built inline (test-only, fabricated) — never a network call.
# --------------------------------------------------------------------------- #
def _mk_page(code: str, record_dmy, *, sidebar=()) -> str:
    """A minimal synthetic VSDC cash-dividend page with a chosen same-org sidebar.

    ``record_dmy=None`` omits the 'Ngày đăng ký cuối cùng:' row (an undated page whose
    amounts + pay date still parse) — used to test the never-silent undated-event path.
    """
    links = "".join(
        f'<li><a href="/vi/ad/{i}">{code}: Chi trả cổ tức bằng tiền</a></li>'
        for i in sidebar
    )
    record_row = (
        ""
        if record_dmy is None
        else (
            '<div class="row"><div class="col-md-4 item-info">Ngày đăng ký cuối cùng:</div>'
            f'<div class="col-md-8 item-info item-info-main">{record_dmy}</div></div>'
        )
    )
    return (
        '<!DOCTYPE html><html lang="vi"><body>'
        f'<h3 class="title-category">{code}: Chi trả cổ tức năm 2024 bằng tiền</h3>'
        '<div class="row"><div class="col-md-4 item-info">Mã chứng khoán:</div>'
        f'<div class="col-md-8 item-info item-info-main">{code}</div></div>'
        f"{record_row}"
        '<div class="row"><div class="col-md-4 item-info">Lý do mục đích:</div>'
        '<div class="col-md-8 item-info item-info-main">Chi trả cổ tức năm 2024 bằng tiền</div></div>'
        '<p><div style="text-align: justify;">- Tỷ lệ thực hiện: 10%/cổ phiếu '
        '(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br /></div></p>'
        '<aside class="news-sidebar"><div class="sub-cate">Tin cùng tổ chức</div>'
        f'<ul class="list-same-org">{links}</ul></aside>'
        "</body></html>"
    )


def _counting_http_get(graph):
    """A GET stub over an id->HTML graph that records a per-id fetch count."""
    calls: dict[int, int] = {}

    def http_get(url, params=None, headers=None):
        ann_id = int(url.rstrip("/").rsplit("/", 1)[-1])
        calls[ann_id] = calls.get(ann_id, 0) + 1
        if ann_id not in graph:
            raise SourceUnavailable(f"stub: no page for id {ann_id}")
        return graph[ann_id]

    return http_get, calls


def test_dividends_crawl_dedup_and_cycle_guard():
    """#9.14 — a cyclic, multi-hop same-org graph terminates and fetches each id once.

    Graph (all TST): 500 -> [501]; 501 -> [502, 500]; 502 -> [501]. Node 502 is reachable
    ONLY via two hops (500->501->502), and 500/501 are re-listed (back-edges = a cycle). A
    correct bounded BFS must (a) follow multi-hop sidebar links to reach 502, and (b) never
    re-fetch an already-visited id despite the back-edges (so the crawl terminates).
    """
    graph = {
        500: _mk_page("TST", "10/05/2024", sidebar=(501,)),
        501: _mk_page("TST", "20/06/2024", sidebar=(502, 500)),
        502: _mk_page("TST", "30/07/2024", sidebar=(501,)),
    }
    http_get, calls = _counting_http_get(graph)
    src = VsdcCashDividendSource(http_get=http_get)
    hist = src.dividends("TST", seed_id=500)
    # multi-hop: the 2-hop-only node 502 was reached.
    assert set(calls) == {500, 501, 502}
    # cycle/dedup guard: no id is ever fetched more than once.
    assert all(n == 1 for n in calls.values()), calls
    # all three distinct cash events are present.
    assert {e.record_date for e in hist.events} == {
        date(2024, 5, 10),
        date(2024, 6, 20),
        date(2024, 7, 30),
    }


def test_dividends_crawl_truncation_emits_never_silent_token():
    """#9.15 — stopping at max_fetch with an unexhausted frontier emits the cap token.

    Seed 700's sidebar links four more ids (701-704). With ``max_fetch=2`` the crawl stops
    with ids still un-fetched, so the result MUST carry ``coverage_truncated_at_max_fetch``
    (never return a partial history as if complete). With a ``max_fetch`` that exhausts the
    frontier the token MUST be absent.
    """
    graph = {
        700: _mk_page("TST", "10/01/2024", sidebar=(701, 702, 703, 704)),
        701: _mk_page("TST", "10/02/2024"),
        702: _mk_page("TST", "10/03/2024"),
        703: _mk_page("TST", "10/04/2024"),
        704: _mk_page("TST", "10/05/2024"),
    }
    http_get, calls = _counting_http_get(graph)
    src = VsdcCashDividendSource(http_get=http_get)
    truncated = src.dividends("TST", seed_id=700, max_fetch=2)
    assert "coverage_truncated_at_max_fetch" in truncated.warnings
    assert "corp_action_source_partial" in truncated.warnings
    assert sum(calls.values()) == 2  # the cap bounds the number of fetches

    http_get2, calls2 = _counting_http_get(graph)
    src2 = VsdcCashDividendSource(http_get=http_get2)
    full = src2.dividends("TST", seed_id=700, max_fetch=10)
    assert "coverage_truncated_at_max_fetch" not in full.warnings
    assert len(full.events) == 5


# --------------------------------------------------------------------------- #
# Reviewer-verify hardening (adversarial self-verify, 2026-06-21): never-silent
# fetch-failure disclosure, max_fetch validation, undated-event window fallback,
# and bundled-line ratio fabrication guard.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad", [0, -1, -100])
def test_dividends_rejects_nonpositive_max_fetch(bad):
    """#9.16 — a non-positive max_fetch is a caller error: raise, never silently return an
    empty (zero-fetch) history as if the issuer simply paid no dividends."""
    http_get, _ = _counting_http_get({1: _mk_page("TST", "15/03/2024")})
    src = VsdcCashDividendSource(http_get=http_get)
    with pytest.raises(InvalidData):
        src.dividends("TST", seed_id=1, max_fetch=bad)


def test_dividends_discloses_fetch_failure_never_silent():
    """#9.17 — a same-org page that fails to fetch leaves coverage incomplete; the result
    MUST disclose `corp_action_fetch_incomplete` (the crawl tolerates the failure but never
    hides the resulting gap), mirroring the equities `board_unavailable` invariant."""
    # seed 10 links hub 11, which is absent from the graph -> SourceUnavailable (hub down).
    graph = {10: _mk_page("TST", "10/01/2024", sidebar=(11,))}
    http_get, calls = _counting_http_get(graph)
    src = VsdcCashDividendSource(http_get=http_get)
    hist = src.dividends("TST", seed_id=10, max_fetch=300)
    assert any(
        w == "corp_action_fetch_incomplete" or w.startswith("corp_action_fetch_incomplete:")
        for w in hist.warnings
    ), hist.warnings
    assert "corp_action_source_partial" in hist.warnings
    # the seed event still came back — a per-page failure is tolerated, not fatal.
    assert any(e.record_date == date(2024, 1, 10) for e in hist.events)
    assert 11 in calls  # the failing hub was actually attempted


def test_dividends_keeps_undated_event_via_pay_date_and_flags_degraded():
    """#9.18 — a cash event whose record date is unparseable is NOT silently dropped under a
    window: it is windowed by its pay_date and carries `vsdc_parse_degraded` (never silent)."""
    http_get, _ = _counting_http_get({800: _mk_page("TST", None)})  # no record row; pay 10/04/2024
    src = VsdcCashDividendSource(http_get=http_get)
    hist = src.dividends(
        "TST", seed_id=800, start=date(2024, 1, 1), end=date(2024, 12, 31)
    )
    assert len(hist.events) == 1
    ev = hist.events[0]
    assert ev.record_date is None
    assert ev.pay_date == date(2024, 4, 10)
    assert ev.cash_per_share == 1000.0  # amounts parsed fine — a real, surfaced event
    assert "vsdc_parse_degraded" in ev.warnings


def test_parse_pairs_cash_ratio_closest_before_parenthetical():
    """#9.19 — the ratio paired with the cash amount is the `%/cổ phiếu` CLOSEST BEFORE the
    cash parenthetical, never the first `%` on a bundled un-split line (which would fabricate
    the bonus ratio onto the cash amount)."""
    html = (
        '<h3 class="title-category">TST: Chi trả cổ tức năm 2024 bằng tiền</h3>'
        '<div class="row"><div class="col-md-4 item-info">Mã chứng khoán:</div>'
        '<div class="col-md-8 item-info item-info-main">TST</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Ngày đăng ký cuối cùng:</div>'
        '<div class="col-md-8 item-info item-info-main">15/03/2024</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Lý do mục đích:</div>'
        '<div class="col-md-8 item-info item-info-main">Chi trả cổ tức năm 2024 bằng tiền</div></div>'
        '<p><div style="text-align: justify;">- Cổ phiếu thưởng 100%/cổ phiếu; cổ tức tiền mặt '
        '12%/cổ phiếu (01 cổ phiếu được nhận 1.200 đồng)<br />- Ngày thanh toán: 10/04/2024<br /></div></p>'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1200.0
    assert ev.ratio_pct == 12.0  # NOT 100.0 (the bonus ratio listed first)


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
