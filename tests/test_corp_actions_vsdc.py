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
from vnfin.exceptions import InvalidData, SourceError, SourceUnavailable

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
    """#9.19 — the ratio paired with the cash amount is NOT the bonus `%` listed first on a
    bundled un-split line. The `Mệnh giá` par cross-check (cash ≈ ratio/100 × par) recovers the
    cash ratio 12% (12% × 10.000 = 1.200 = cash), never the 100% bonus (= 10.000 ≠ cash)."""
    html = (
        '<h3 class="title-category">TST: Chi trả cổ tức năm 2024 bằng tiền</h3>'
        '<div class="row"><div class="col-md-4 item-info">Mã chứng khoán:</div>'
        '<div class="col-md-8 item-info item-info-main">TST</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Mệnh giá:</div>'
        '<div class="col-md-8 item-info item-info-main">10.000 đồng</div></div>'
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
# Reviewer BLOCK 2026-06-21 (Codex x2): 3 fresh blockers, fix phase. B1 parse-crash
# in the crawl boundary; B2 multi-tranche silent-drop + sau-thuế ratio mis-pair (the
# heaviest); NOTE-1 no-seed silent-empty. Each gets a fail-first regression.
# --------------------------------------------------------------------------- #
# A cash-dividend page (detected via title) with NO resolvable ticker -> parse_announcement
# raises InvalidData (not a SourceError). Used to prove a bad SIBLING never sinks the crawl.
_NO_TICKER_CASH_PAGE = (
    '<!DOCTYPE html><html lang="vi"><body>'
    '<h3 class="title-category">Chi trả cổ tức bằng tiền</h3>'  # no ":" -> no title-prefix code
    '<div class="row"><div class="col-md-4 item-info">Lý do mục đích:</div>'
    '<div class="col-md-8 item-info item-info-main">Chi trả cổ tức năm 2024 bằng tiền</div></div>'
    '</body></html>'
)


def test_no_ticker_cash_page_raises_invalid_data():
    """#9.20a — guard the test premise: the no-ticker page raises InvalidData. (InvalidData IS
    a SourceError subtype, so the real B1 bug was NOT the class hierarchy — it was that the
    `_crawl` `parse_announcement` call sat OUTSIDE the `try`, so the `except` never applied and
    one bad sibling propagated up and crashed `dividends()`.)"""
    with pytest.raises(InvalidData):
        VsdcCashDividendSource().parse_announcement(_NO_TICKER_CASH_PAGE)
    assert issubclass(InvalidData, SourceError)  # documents the true hierarchy


def test_dividends_parse_failure_on_sibling_does_not_crash_crawl():
    """#9.20 (B1) — a same-org page that PARSES to InvalidData (empty body / no resolvable
    ticker) must NOT crash dividends(): the crawl tolerates it like a fetch failure, counting +
    disclosing via `corp_action_fetch_incomplete`. Regression: parse_announcement was called
    OUTSIDE the `_crawl` `except SourceError`, so one bad sibling sank the whole call."""
    graph = {
        20: _mk_page("TST", "10/01/2024", sidebar=(21,)),
        21: _NO_TICKER_CASH_PAGE,  # valid HTTP body, but parse -> InvalidData
    }
    http_get, calls = _counting_http_get(graph)
    src = VsdcCashDividendSource(http_get=http_get)
    hist = src.dividends("TST", seed_id=20, max_fetch=300)  # must NOT raise
    assert any(
        w == "corp_action_fetch_incomplete" or w.startswith("corp_action_fetch_incomplete:")
        for w in hist.warnings
    ), hist.warnings
    assert any(e.record_date == date(2024, 1, 10) for e in hist.events)  # seed still returned
    assert 21 in calls  # the bad sibling was actually attempted


def test_parse_multitranche_discloses_dropped_tranche():
    """#9.21 (B2) — a page with >1 cash parenthetical (multi-tranche, e.g. tạm ứng đợt 1 + đợt
    2) must NOT silently drop the 2nd: v1 surfaces the FIRST tranche but flags
    `vsdc_parse_degraded` so the dropped tranche is disclosed, never hidden."""
    html = (
        '<h3 class="title-category">TST: Chi trả cổ tức năm 2024 bằng tiền</h3>'
        '<div class="row"><div class="col-md-4 item-info">Mã chứng khoán:</div>'
        '<div class="col-md-8 item-info item-info-main">TST</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Ngày đăng ký cuối cùng:</div>'
        '<div class="col-md-8 item-info item-info-main">15/03/2024</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Lý do mục đích:</div>'
        '<div class="col-md-8 item-info item-info-main">Chi trả cổ tức năm 2024 bằng tiền</div></div>'
        '<p><div style="text-align: justify;">'
        '- Đợt 1: 8%/cổ phiếu (01 cổ phiếu được nhận 800 đồng)<br />'
        '- Đợt 2: 12%/cổ phiếu (01 cổ phiếu được nhận 1.200 đồng)<br />'
        '- Ngày thanh toán: 10/04/2024<br /></div></p>'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 800.0  # the first tranche is surfaced...
    assert "vsdc_parse_degraded" in ev.warnings  # ...but the dropped 2nd is disclosed
    assert "vsdc_ratio_tax_deferred" not in ev.warnings  # no tax token: distinct semantics


def test_parse_sau_thue_with_par_is_withheld_not_classified():
    """#9.22 (#163 v1 DE-SCOPE) — the ratio line carries a 'sau thuế' tax signal, so under the
    de-scope the % is net-vs-gross ambiguous and is WITHHELD (ratio_pct=None) + disclosed via
    vsdc_ratio_tax_deferred — NOT classified. The old par-recovery / before-tax-override mechanism
    is DELETED; even with Mệnh giá present, a tax-signal line is never classified. Cash intact."""
    html = (
        '<h3 class="title-category">TST: Chi trả cổ tức năm 2024 bằng tiền</h3>'
        '<div class="row"><div class="col-md-4 item-info">Mã chứng khoán:</div>'
        '<div class="col-md-8 item-info item-info-main">TST</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Mệnh giá:</div>'
        '<div class="col-md-8 item-info item-info-main">10.000 đồng</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Ngày đăng ký cuối cùng:</div>'
        '<div class="col-md-8 item-info item-info-main">15/03/2024</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Lý do mục đích:</div>'
        '<div class="col-md-8 item-info item-info-main">Chi trả cổ tức năm 2024 bằng tiền</div></div>'
        '<p><div style="text-align: justify;">- Tỷ lệ thực hiện: 12%/cổ phiếu; sau thuế '
        '10%/cổ phiếu (01 cổ phiếu được nhận 1.200 đồng)<br />- Ngày thanh toán: 10/04/2024<br /></div></p>'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1200.0
    assert ev.ratio_pct is None  # tax-signal line withheld, not classified (de-scope)
    assert "vsdc_ratio_tax_deferred" in ev.warnings
    assert "vsdc_parse_degraded" not in ev.warnings


def test_parse_sau_thue_without_par_degrades_not_wrong_ratio():
    """#9.23 (#163 v1 DE-SCOPE) — the ratio line carries a 'sau thuế' tax signal → withheld
    (de-scope): ratio_pct=None disclosed via the NEW vsdc_ratio_tax_deferred token, NOT
    vsdc_parse_degraded (the two are semantically distinct: intentional withholding vs a parse
    fault). The cash amount is still surfaced."""
    html = (
        '<h3 class="title-category">TST: Chi trả cổ tức năm 2024 bằng tiền</h3>'
        '<div class="row"><div class="col-md-4 item-info">Mã chứng khoán:</div>'
        '<div class="col-md-8 item-info item-info-main">TST</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Ngày đăng ký cuối cùng:</div>'
        '<div class="col-md-8 item-info item-info-main">15/03/2024</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Lý do mục đích:</div>'
        '<div class="col-md-8 item-info item-info-main">Chi trả cổ tức năm 2024 bằng tiền</div></div>'
        '<p><div style="text-align: justify;">- Tỷ lệ thực hiện: 12%/cổ phiếu; sau thuế '
        '10%/cổ phiếu (01 cổ phiếu được nhận 1.200 đồng)<br />- Ngày thanh toán: 10/04/2024<br /></div></p>'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1200.0
    assert ev.ratio_pct is None  # tax-signal line withheld (de-scope)
    assert "vsdc_ratio_tax_deferred" in ev.warnings
    assert "vsdc_parse_degraded" not in ev.warnings


def test_parse_rejects_implausible_over_100_ratio():
    """#9.24 (B2) — a `%/cổ phiếu` > 100 is implausible for a per-share CASH ratio (a parse
    artifact or a misread); it is rejected rather than fabricated onto the cash amount, and the
    event is flagged degraded (the cash amount is still surfaced)."""
    html = (
        '<h3 class="title-category">TST: Chi trả cổ tức năm 2024 bằng tiền</h3>'
        '<div class="row"><div class="col-md-4 item-info">Mã chứng khoán:</div>'
        '<div class="col-md-8 item-info item-info-main">TST</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Ngày đăng ký cuối cùng:</div>'
        '<div class="col-md-8 item-info item-info-main">15/03/2024</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Lý do mục đích:</div>'
        '<div class="col-md-8 item-info item-info-main">Chi trả cổ tức năm 2024 bằng tiền</div></div>'
        '<p><div style="text-align: justify;">- Tỷ lệ thực hiện: 200%/cổ phiếu '
        '(01 cổ phiếu được nhận 1.200 đồng)<br />- Ngày thanh toán: 10/04/2024<br /></div></p>'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1200.0
    assert ev.ratio_pct is None  # 200%/share rejected, not fabricated
    assert "vsdc_parse_degraded" in ev.warnings
    assert "vsdc_ratio_tax_deferred" not in ev.warnings  # no tax token: distinct semantics


def test_parse_multitranche_with_sau_thue_no_misparse_and_discloses():
    """#9.26 (#163 v1 DE-SCOPE) — a multi-tranche page whose FIRST tranche ALSO carries a
    'sau thuế' tax signal: both failure modes are now disclosed via DISTINCT tokens — the
    multi-tranche drop via vsdc_parse_degraded, and the tax-signal line via the new
    vsdc_ratio_tax_deferred. The ratio is WITHHELD (de-scope), no longer par-recovered."""
    html = (
        '<h3 class="title-category">TST: Chi trả cổ tức năm 2024 bằng tiền</h3>'
        '<div class="row"><div class="col-md-4 item-info">Mã chứng khoán:</div>'
        '<div class="col-md-8 item-info item-info-main">TST</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Mệnh giá:</div>'
        '<div class="col-md-8 item-info item-info-main">10.000 đồng</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Ngày đăng ký cuối cùng:</div>'
        '<div class="col-md-8 item-info item-info-main">15/03/2024</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Lý do mục đích:</div>'
        '<div class="col-md-8 item-info item-info-main">Chi trả cổ tức năm 2024 bằng tiền</div></div>'
        '<p><div style="text-align: justify;">'
        '- Đợt 1: 12%/cổ phiếu; sau thuế 10%/cổ phiếu (01 cổ phiếu được nhận 1.200 đồng)<br />'
        '- Đợt 2: 8%/cổ phiếu (01 cổ phiếu được nhận 800 đồng)<br />'
        '- Ngày thanh toán: 10/04/2024<br /></div></p>'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1200.0  # first tranche surfaced
    assert ev.ratio_pct is None  # tax-signal line withheld (de-scope), no longer par-recovered
    assert "vsdc_ratio_tax_deferred" in ev.warnings  # the tax line is disclosed
    assert "vsdc_parse_degraded" in ev.warnings  # the dropped 2nd tranche is disclosed


# --------------------------------------------------------------------------- #
# Reviewer BLOCK round-2 (2026-06-21): net-of-tax + dot-decimal ratio + alt-phrased
# tranche + cross-line union. Each fail-first on the current code (#163 B2 fix-2).
# --------------------------------------------------------------------------- #
def _justify_page(body_lines: str, *, par: bool = False) -> str:
    """Build a synthetic VSDC cash-dividend page whose justify block is ``body_lines``
    (already containing the <br />-separated lines). ``par=True`` adds a Mệnh giá row."""
    par_row = (
        '<div class="row"><div class="col-md-4 item-info">Mệnh giá:</div>'
        '<div class="col-md-8 item-info item-info-main">10.000 đồng</div></div>'
        if par
        else ""
    )
    return (
        '<h3 class="title-category">TST: Chi trả cổ tức năm 2024 bằng tiền</h3>'
        '<div class="row"><div class="col-md-4 item-info">Mã chứng khoán:</div>'
        '<div class="col-md-8 item-info item-info-main">TST</div></div>'
        f"{par_row}"
        '<div class="row"><div class="col-md-4 item-info">Ngày đăng ký cuối cùng:</div>'
        '<div class="col-md-8 item-info item-info-main">15/03/2024</div></div>'
        '<div class="row"><div class="col-md-4 item-info">Lý do mục đích:</div>'
        '<div class="col-md-8 item-info item-info-main">Chi trả cổ tức năm 2024 bằng tiền</div></div>'
        f'<p><div style="text-align: justify;">{body_lines}</div></p>'
    )


def test_parse_dot_decimal_ratio_not_x10():
    """#9.27 (D-REV) — '8.5%/cổ phiếu' is a DECIMAL 8.5, NOT 85 (a % never uses a thousands
    separator). No par, single clean fractional candidate → served cleanly, NOT degraded."""
    html = _justify_page(
        '- Tỷ lệ thực hiện: 8.5%/cổ phiếu (01 cổ phiếu được nhận 850 đồng)<br />'
        '- Ngày thanh toán: 10/04/2024<br />'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 850.0
    assert ev.ratio_pct == 8.5  # decimal-aware
    assert ev.ratio_pct != 85.0  # NOT the _parse_vn_number ".=thousands" misread
    assert "vsdc_parse_degraded" not in ev.warnings  # clean single fractional


def test_parse_comma_decimal_ratio():
    """#9.28 (D-REV comma) — '8,5%/cổ phiếu' is also a DECIMAL 8.5 (comma is the decimal point
    in a ratio)."""
    html = _justify_page(
        '- Tỷ lệ thực hiện: 8,5%/cổ phiếu (01 cổ phiếu được nhận 850 đồng)<br />'
        '- Ngày thanh toán: 10/04/2024<br />'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 850.0
    assert ev.ratio_pct == 8.5


def test_parse_net_only_ratio_degrades_no_par():
    """#9.29 (#163 v1 DE-SCOPE) — a 'sau thuế' line carries a tax signal → withheld (de-scope):
    ratio_pct=None disclosed via vsdc_ratio_tax_deferred, NOT vsdc_parse_degraded (distinct
    semantics). Cash intact."""
    html = _justify_page(
        '- Tỷ lệ thực hiện sau thuế: 10%/cổ phiếu (01 cổ phiếu được nhận 1.200 đồng)<br />'
        '- Ngày thanh toán: 10/04/2024<br />'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1200.0
    assert ev.ratio_pct is None  # tax-signal line withheld (de-scope)
    assert "vsdc_ratio_tax_deferred" in ev.warnings
    assert "vsdc_parse_degraded" not in ev.warnings


def test_parse_gross_plus_net_no_par_degrades():
    """#9.30 (#163 v1 DE-SCOPE) — '12%/cổ phiếu; thực nhận sau thuế 11,4%/cổ phiếu (…1.140)' with
    NO par: the line carries a 'sau thuế' tax signal → withheld (de-scope): ratio_pct=None via
    vsdc_ratio_tax_deferred, NOT vsdc_parse_degraded. The net 11.4% is never served."""
    html = _justify_page(
        '- Tỷ lệ thực hiện: 12%/cổ phiếu; thực nhận sau thuế 11,4%/cổ phiếu '
        '(01 cổ phiếu được nhận 1.140 đồng)<br />- Ngày thanh toán: 10/04/2024<br />'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1140.0
    assert ev.ratio_pct is None  # tax-signal line withheld (de-scope)
    assert ev.ratio_pct != 11.4
    assert "vsdc_ratio_tax_deferred" in ev.warnings
    assert "vsdc_parse_degraded" not in ev.warnings


def test_parse_gross_plus_net_with_par_net_cash_degrades():
    """#9.31 (#163 v1 DE-SCOPE) — same gross+net line WITH Mệnh giá 10.000: the 'sau thuế' tax
    signal means the line is withheld (de-scope) regardless of par — ratio_pct=None via
    vsdc_ratio_tax_deferred, NOT vsdc_parse_degraded. The old par cross-check is DELETED."""
    html = _justify_page(
        '- Tỷ lệ thực hiện: 12%/cổ phiếu; thực nhận sau thuế 11,4%/cổ phiếu '
        '(01 cổ phiếu được nhận 1.140 đồng)<br />- Ngày thanh toán: 10/04/2024<br />',
        par=True,
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1140.0
    assert ev.ratio_pct is None  # tax-signal line withheld (de-scope)
    assert "vsdc_ratio_tax_deferred" in ev.warnings
    assert "vsdc_parse_degraded" not in ev.warnings


def test_parse_alt_phrased_tranche_discloses_dropped():
    """#9.32 (D3) — a 2nd tranche phrased '…số tiền 1.200 đồng/cổ phiếu' (not the 'được nhận'
    phrasing) must STILL be counted as a tranche: the first tranche (800) is surfaced and the
    dropped 2nd is disclosed via degraded — never silently lost."""
    html = _justify_page(
        '- Đợt 1: 8%/cổ phiếu (01 cổ phiếu được nhận 800 đồng)<br />'
        '- Đợt 2: số tiền 1.200 đồng/cổ phiếu<br />'
        '- Ngày thanh toán: 10/04/2024<br />'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 800.0  # first tranche surfaced
    assert "vsdc_parse_degraded" in ev.warnings  # alt-phrased 2nd tranche disclosed
    assert "vsdc_ratio_tax_deferred" not in ev.warnings  # no tax token: distinct semantics


def test_parse_cross_line_ratio_unpaired_degrades():
    """#9.33 (NOTE cross-line) — the ratio '10%/cổ phiếu' lives on a DIFFERENT <br /> line than
    the cash anchor 'được nhận 1.000 đồng': v1 does not pair across lines, so the ratio is left
    None — but the page DOES state a ratio, so the result must be degraded, never a silent
    undegraded ratio None."""
    html = _justify_page(
        '- Tỷ lệ thực hiện: 10%/cổ phiếu<br />'
        '- Số tiền: (01 cổ phiếu được nhận 1.000 đồng)<br />'
        '- Ngày thanh toán: 10/04/2024<br />'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1000.0
    assert ev.ratio_pct is None  # not paired across lines
    assert "vsdc_parse_degraded" in ev.warnings  # but a ratio IS stated -> degrade (never silent)
    assert "vsdc_ratio_tax_deferred" not in ev.warnings  # no tax token: distinct semantics


def test_parse_par_confirmed_twins_degrade():
    """#9.34 (L1) — par 10.000 + '10%/cổ phiếu; sau điều chỉnh 10,04%/cổ phiếu (…1.000 đồng)':
    BOTH 10% and 10.04% par-confirm against 1.000 within tolerance (1000 and 1004), so the
    pairing is ambiguous — ratio None + degraded, NEVER a silent order-dependent 10.04."""
    html = _justify_page(
        '- Tỷ lệ thực hiện: 10%/cổ phiếu; sau điều chỉnh 10,04%/cổ phiếu '
        '(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />',
        par=True,
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1000.0
    assert ev.ratio_pct is None  # ambiguous par-confirmed twins, not a silent 10.04
    assert "vsdc_parse_degraded" in ev.warnings
    assert "vsdc_ratio_tax_deferred" not in ev.warnings  # no tax token: distinct semantics


def test_parse_clean_single_gross_ratio_still_serves_no_over_degrade():
    """#9.35 (reviewer NEGATIVE guard) — the round-2 net-of-tax / cross-line / twin logic must
    NOT over-degrade the common clean case: a single gross '%/cổ phiếu' ratio on the cash line,
    no par, no net marker, one tranche → the ratio IS served and the result is NOT degraded."""
    html = _justify_page(
        '- Tỷ lệ thực hiện: 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />'
        '- Ngày thanh toán: 10/04/2024<br />'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1000.0
    assert ev.ratio_pct == 10.0  # served, not degraded
    assert "vsdc_parse_degraded" not in ev.warnings


def test_parse_truoc_thue_line_is_withheld_under_descope():
    """#9.36 (#163 v1 DE-SCOPE) — under the de-scope we no longer distinguish before-tax from
    after-tax: ANY line carrying a tax signal (here 'trước thuế', which still contains the 'thuế'
    tax noun) is net-vs-gross ambiguous and WITHHELD (ratio_pct=None) + vsdc_ratio_tax_deferred.
    The old before-tax-override that served 12.0 is DELETED. Cash intact."""
    html = _justify_page(
        '- Tỷ lệ thực hiện (trước thuế): 12%/cổ phiếu (01 cổ phiếu được nhận 1.200 đồng)<br />'
        '- Ngày thanh toán: 10/04/2024<br />'
    )
    ev = VsdcCashDividendSource().parse_announcement(html)
    assert ev is not None
    assert ev.cash_per_share == 1200.0
    assert ev.ratio_pct is None  # tax-signal line withheld (de-scope)
    assert "vsdc_ratio_tax_deferred" in ev.warnings
    assert "vsdc_parse_degraded" not in ev.warnings


# --------------------------------------------------------------------------- #
# #163 round-7 DE-SCOPE corpus (replaces the deleted net-vs-gross classifier tests #9.37-#9.55).
# Under v1 we no longer classify net-vs-gross: ANY tax/withholding signal in the ratio line ->
# ratio withheld (ratio_pct=None) + vsdc_ratio_tax_deferred. These phrasings are the v2 corpus seed.
# --------------------------------------------------------------------------- #
_TAX_DEFERRED_CORPUS = [
    # (id, justify-body, expected_cash, par)
    ("9.37 trailing sau thuế, no par",
     "- Tỷ lệ thực hiện: 11,4%/cổ phiếu sau thuế (01 cổ phiếu được nhận 1.140 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1140.0, False),
    ("9.38 gross + trailing sau thuế + par",
     "- Tỷ lệ thực hiện: 12%/cổ phiếu; 11,4%/cổ phiếu sau thuế "
     "(01 cổ phiếu được nhận 1.140 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1140.0, True),
    ("9.39 leading sau thuế + par confirms net",
     "- Tỷ lệ thực hiện sau thuế 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, True),
    ("9.40 đã khấu trừ thuế",
     "- Tỷ lệ thực hiện đã khấu trừ thuế 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.41 đã trừ thuế",
     "- Tỷ lệ thực hiện đã trừ thuế: 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.42 trailing trước thuế (was served gross, now withheld under de-scope)",
     "- Tỷ lệ thực hiện: 12%/cổ phiếu trước thuế (01 cổ phiếu được nhận 1.200 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1200.0, False),
    ("9.43 trước thuế TNCN (was served gross, now withheld)",
     "- Tỷ lệ thực hiện: 12%/cổ phiếu trước thuế TNCN (01 cổ phiếu được nhận 1.200 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1200.0, False),
    ("9.44 bare khấu trừ, thuế elided",
     "- Tỷ lệ thực hiện: đã thực hiện khấu trừ 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.45 chưa khấu trừ thuế (was served gross, now withheld)",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu chưa khấu trừ thuế (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.46 sau thuế + (chưa gồm phí)",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế (chưa gồm phí) "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.47 đã trừ thuế, chưa gồm phí",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu đã trừ thuế, chưa gồm phí "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.48 trước khi khấu trừ thuế (was served gross, now withheld)",
     "- Tỷ lệ thực hiện: 12%/cổ phiếu trước khi khấu trừ thuế "
     "(01 cổ phiếu được nhận 1.200 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1200.0, False),
    ("9.49 sau thuế (không gồm phí)",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế (không gồm phí) "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.50 sau thuế, miễn phí",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế, miễn phí giao dịch "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.51 sau thuế, trước ngày",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế, dự kiến trả trước ngày 20/04 "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.52 sau thuế (chưa gồm phí) + par",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế (chưa gồm phí) "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, True),
    ("9.53 khấu trừ thuế + fee clause",
     "- Tỷ lệ thực hiện: khấu trừ thuế 10%/cổ phiếu, chưa khấu trừ phí lưu ký "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("9.54 đã trừ thuế + bare trừ fee",
     "- Tỷ lệ thực hiện: đã trừ thuế 12%/cổ phiếu, chưa trừ phí quản lý "
     "(01 cổ phiếu được nhận 1.200 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1200.0, False),
    ("9.55 thuế TNCN + không trừ phí",
     "- Tỷ lệ thực hiện: thuế TNCN 8%/cổ phiếu, không trừ phí dịch vụ "
     "(01 cổ phiếu được nhận 800 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 800.0, False),
    # NEW round-7 attack cases (the BLOCK6 multi-tax + hunter bug#7 + multi-candidate leak):
    ("NEW multi-tax (BLOCK6: TNCN + GTGT)",
     "- Tỷ lệ thực hiện: đã khấu trừ thuế TNCN 10%/cổ phiếu, chưa bao gồm thuế GTGT "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("NEW hunter bug#7 (net-first, sau thuế trailing non-last) + par",
     "- Tỷ lệ thực hiện: 8,5%/cổ phiếu sau thuế; 10%/cổ phiếu "
     "(01 cổ phiếu được nhận 850 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 850.0, True),
    ("NEW multi-candidate leak (tax token on candidate A only)",
     "- Tỷ lệ thực hiện: đã khấu trừ thuế TNCN 10%/cổ phiếu, 12%/cổ phiếu "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    # round-7 adversarial-verify catch: thuế-ELIDED net markers (thực nhận / thực lĩnh / thực lãnh /
    # ròng / net) are the standard VN terms for the after-tax figure a holder pockets. The first gate
    # ({thue,tncn}|khấu-trừ) leaked them → served a net % as gross (THE bar). Must withhold too.
    ("NET-marker thực nhận (thuế elided)",
     "- Tỷ lệ cổ tức thực nhận: 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("NET-marker thực lĩnh (thuế elided)",
     "- Cổ tức thực lĩnh: 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("NET-marker thực lãnh (thuế elided)",
     "- Cổ tức thực lãnh: 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("NET-marker ròng (thuế elided)",
     "- Tỷ lệ cổ tức ròng: 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
    ("NET-marker net (thuế elided)",
     "- Tỷ lệ cổ tức net: 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False),
]


@pytest.mark.parametrize("label,body,cash,par", _TAX_DEFERRED_CORPUS, ids=[c[0] for c in _TAX_DEFERRED_CORPUS])
def test_parse_tax_qualified_ratio_deferred_never_served(label, body, cash, par):
    """#163 v1 DE-SCOPE — NO tax/withholding-qualified ratio is EVER served. Every accumulated
    phrasing (the 6-round corpus + hunter bug#7 + multi-tax/multi-candidate) yields ratio_pct=None +
    vsdc_ratio_tax_deferred, with cash + dates intact. Single-tranche -> NOT vsdc_parse_degraded
    (the two tokens are semantically distinct: intentional withholding vs a parse fault)."""
    ev = VsdcCashDividendSource().parse_announcement(_justify_page(body, par=par))
    assert ev is not None, label
    assert ev.cash_per_share == cash, label
    assert ev.ratio_pct is None, label  # never a net/gross-ambiguous rate served as gross
    assert "vsdc_ratio_tax_deferred" in ev.warnings, label
    assert "vsdc_parse_degraded" not in ev.warnings, label  # distinct token, single-tranche


_CLEAN_SERVED_CORPUS = [
    ("plain integer 10%", "- Tỷ lệ thực hiện: 10%/cổ phiếu (01 cổ phiếu được nhận 1.000 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 1000.0, False, 10.0),
    ("dot decimal 8.5%", "- Tỷ lệ thực hiện: 8.5%/cổ phiếu (01 cổ phiếu được nhận 850 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 850.0, False, 8.5),
    ("comma decimal 8,5%", "- Tỷ lệ thực hiện: 8,5%/cổ phiếu (01 cổ phiếu được nhận 850 đồng)<br />"
     "- Ngày thanh toán: 10/04/2024<br />", 850.0, False, 8.5),
    ("bonus + cash, par recovers 12%",
     "- Cổ phiếu thưởng 100%/cổ phiếu; cổ tức tiền mặt 12%/cổ phiếu "
     "(01 cổ phiếu được nhận 1.200 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1200.0, True, 12.0),
    # round-7 adversarial-verify catch (over-withhold guard): 'khấu hao' (depreciation) co-occurring
    # with a non-adjacent 'trừ' must NOT trip the withholding-pair gate — the 'khấu trừ' signal is the
    # ADJACENT bigram, not incidental khau+tru co-occurrence. A clean gross ratio still serves.
    ("depreciation khấu hao + non-adjacent trừ still serves",
     "- Tỷ lệ thực hiện: 10%/cổ phiếu sau khi trừ chi phí khấu hao "
     "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", 1000.0, False, 10.0),
]


@pytest.mark.parametrize("label,body,cash,par,expect", _CLEAN_SERVED_CORPUS, ids=[c[0] for c in _CLEAN_SERVED_CORPUS])
def test_parse_clean_ratio_still_served_no_over_degrade(label, body, cash, par, expect):
    """De-scope NEGATIVE guard — the tax-signal gate must NOT over-degrade a clean, tax-free ratio
    line: it is still served and carries NEITHER degrade token."""
    ev = VsdcCashDividendSource().parse_announcement(_justify_page(body, par=par))
    assert ev is not None, label
    assert ev.cash_per_share == cash, label
    assert ev.ratio_pct == expect, label
    assert "vsdc_ratio_tax_deferred" not in ev.warnings, label
    assert "vsdc_parse_degraded" not in ev.warnings, label


def test_parse_tax_and_nontax_degrade_tokens_are_distinct():
    """#163 round-7 semantic distinction (reviewer check #6) — a TAX line emits ONLY
    vsdc_ratio_tax_deferred (intentional withholding, not a parse fault); a NON-tax ambiguous line
    (par-confirmed twins) emits ONLY vsdc_parse_degraded. The two tokens never collapse."""
    tax = VsdcCashDividendSource().parse_announcement(_justify_page(
        "- Tỷ lệ thực hiện: 10%/cổ phiếu sau thuế (01 cổ phiếu được nhận 1.000 đồng)<br />"
        "- Ngày thanh toán: 10/04/2024<br />"))
    assert tax.ratio_pct is None
    assert "vsdc_ratio_tax_deferred" in tax.warnings
    assert "vsdc_parse_degraded" not in tax.warnings
    nontax = VsdcCashDividendSource().parse_announcement(_justify_page(
        "- Tỷ lệ thực hiện: 10%/cổ phiếu; sau điều chỉnh 10,04%/cổ phiếu "
        "(01 cổ phiếu được nhận 1.000 đồng)<br />- Ngày thanh toán: 10/04/2024<br />", par=True))
    assert nontax.ratio_pct is None
    assert "vsdc_parse_degraded" in nontax.warnings
    assert "vsdc_ratio_tax_deferred" not in nontax.warnings


def test_dividends_no_seed_found_discloses_not_silent_empty():
    """#9.25 (NOTE-1) — when no-seed auto-discovery exhausts its recent-ID window WITHOUT
    finding a seed page for the ticker, the empty history must be DISTINGUISHABLE from a genuine
    never-paid-a-dividend: it carries `corp_action_seed_not_found` (never a silent empty)."""
    # latest_id=5 -> _find_seed scans ids 5..1; every page is a DIFFERENT ticker -> no seed.
    other = _mk_page("OTH", "10/01/2024")
    graph = {i: other for i in range(1, 6)}
    http_get, calls = _counting_http_get(graph)
    src = VsdcCashDividendSource(http_get=http_get, latest_id=5)
    hist = src.dividends("TST", max_fetch=300)  # no seed_id -> auto-discovery
    assert hist.events == ()
    assert "corp_action_seed_not_found" in hist.warnings
    assert "corp_action_source_partial" in hist.warnings
    assert set(calls) == {1, 2, 3, 4, 5}  # the whole window was actually scanned


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
