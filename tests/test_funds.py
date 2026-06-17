"""Tests for the Fmarket funds adapter.

All payloads are hand-crafted SYNTHETIC JSON matching the verified real shape
(see docs/sources/funds-fmarket.md). No real provider rows are committed.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable
from vnfin.funds import (
    Fund,
    FundHolding,
    FundList,
    FmarketFundSource,
    NavHistory,
    NavPoint,
)

# ---------------------------------------------------------------------------
# synthetic payloads (shapes mirror api.fmarket.vn, no real rows)
# ---------------------------------------------------------------------------


def _fund_list_payload(rows=None, status=200):
    if rows is None:
        rows = [
            {
                "id": 20,
                "code": "AAAA",
                "shortName": "AAAA",
                "name": "QUY SYNTHETIC A",
                "nav": 34942.66,
                "lastYearNav": 30000.0,
                "managementFee": 1.75,
                "avgAnnualReturn": 12.3,
                "dataFundAssetType": {"id": 1, "name": "Quy co phieu", "code": "STOCK"},
                "owner": {"id": 1, "name": "CONG TY QUAN LY QUY A", "shortName": "AAM"},
            },
            {
                "id": 21,
                "code": "BBBB",
                "shortName": "BBBB",
                "name": "QUY SYNTHETIC B",
                "nav": 12345.0,
                "dataFundAssetType": {"id": 2, "name": "Quy trai phieu", "code": "BOND"},
                "owner": {"id": 2, "name": "CONG TY QUAN LY QUY B", "shortName": "BBM"},
            },
        ]
    return json.dumps(
        {
            "status": status,
            "code": 200,
            "message": "success",
            "data": {"total": len(rows), "page": 1, "pageSize": 100, "rows": rows},
            "extra": None,
        }
    )


def _nav_history_payload(rows=None, status=200):
    if rows is None:
        rows = [
            {"id": 1, "createdAt": 1761537393929, "nav": 10000.0, "navDate": "2024-01-02", "productId": 20},
            {"id": 2, "createdAt": 1761537393929, "nav": 10250.5, "navDate": "2024-01-03", "productId": 20},
            # intentionally out of order to prove sorting
            {"id": 3, "createdAt": None, "nav": 10180.25, "navDate": "2024-01-01", "productId": 20},
        ]
    return json.dumps(
        {
            "status": status,
            "code": 200,
            "message": "success",
            "data": rows,
            "extra": None,
        }
    )


def _holdings_payload(top=None, asset=None, industries=None, status=200, code="AAAA", nav=34942.66):
    if top is None:
        top = [
            {"stockCode": "MBB", "netAssetPercent": 7.99, "industry": "Ngan hang", "type": "STOCK", "price": 25.2},
            {"stockCode": "FPT", "netAssetPercent": 6.5, "industry": "Cong nghe", "type": "STOCK", "price": 120.0},
        ]
    if asset is None:
        asset = [
            {"assetType": {"code": "STOCK", "name": "Co phieu"}, "assetPercent": 97.44},
            {"assetType": {"code": "CASH", "name": "Tien"}, "assetPercent": 2.56},
        ]
    if industries is None:
        industries = [
            {"industry": "Ngan hang", "assetPercent": 33.36},
            {"industry": "Cong nghe", "assetPercent": 12.5},
        ]
    return json.dumps(
        {
            "status": status,
            "code": 200,
            "message": "success",
            "data": {
                "id": 20,
                "code": code,
                "shortName": code,
                "nav": nav,
                "productTopHoldingList": top,
                "productAssetHoldingList": asset,
                "productIndustriesHoldingList": industries,
            },
            "extra": None,
        }
    )


def _capture_get(text):
    """An http_get that records its call args and returns canned text."""
    calls = []

    def _g(url, params=None, headers=None, json_body=None):
        calls.append({"url": url, "params": params, "headers": headers, "json_body": json_body})
        return text

    _g.calls = calls
    return _g


def _raising_get(exc):
    def _g(url, params=None, headers=None, json_body=None):
        raise exc

    return _g


def _src(text):
    return FmarketFundSource(http_get=_capture_get(text))


# ---------------------------------------------------------------------------
# list_funds
# ---------------------------------------------------------------------------


def test_list_funds_parses_normal():
    funds = _src(_fund_list_payload()).list_funds()
    assert isinstance(funds, FundList)
    assert funds.source == "fmarket"
    assert funds.currency == "VND"
    assert funds.fetched_at_utc is not None
    assert funds.fetched_at_utc.tzinfo is not None
    assert len(funds) == 2
    f = funds.funds[0]
    assert isinstance(f, Fund)
    assert f.code == "AAAA"
    assert f.id == 20
    assert f.name == "QUY SYNTHETIC A"
    assert f.nav == pytest.approx(34942.66)
    assert f.manager == "CONG TY QUAN LY QUY A"
    assert f.asset_type == "STOCK"


def test_list_funds_iteration_and_indexing():
    funds = _src(_fund_list_payload()).list_funds()
    codes = [f.code for f in funds]  # __iter__
    assert codes == ["AAAA", "BBBB"]


def test_list_funds_asset_type_filter_passed_as_body():
    get = _capture_get(_fund_list_payload())
    src = FmarketFundSource(http_get=get)
    src.list_funds(asset_type="STOCK")
    body = get.calls[0]["json_body"]
    assert body["fundAssetTypes"] == ["STOCK"]


def test_list_funds_search_field_passed_as_body():
    get = _capture_get(_fund_list_payload())
    src = FmarketFundSource(http_get=get)
    src.list_funds(search="VESAF")
    body = get.calls[0]["json_body"]
    assert body["searchField"] == "VESAF"


def test_list_funds_empty_rows_raises_empty():
    with pytest.raises(EmptyData):
        _src(_fund_list_payload(rows=[])).list_funds()


def test_list_funds_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("<html>nope</html>").list_funds()


def test_list_funds_malformed_nav_raises_invalid():
    rows = [
        {
            "id": 20,
            "code": "AAAA",
            "shortName": "AAAA",
            "name": "X",
            "nav": "garbage",
            "dataFundAssetType": {"code": "STOCK"},
            "owner": {"name": "M"},
        }
    ]
    with pytest.raises(InvalidData):
        _src(_fund_list_payload(rows=rows)).list_funds()


def test_list_funds_missing_id_raises_invalid():
    rows = [
        {
            "code": "AAAA",
            "shortName": "AAAA",
            "name": "X",
            "nav": 100.0,
            "dataFundAssetType": {"code": "STOCK"},
            "owner": {"name": "M"},
        }
    ]
    with pytest.raises(InvalidData):
        _src(_fund_list_payload(rows=rows)).list_funds()


def test_list_funds_transport_error_wrapped():
    src = FmarketFundSource(http_get=_raising_get(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        src.list_funds()


# ---------------------------------------------------------------------------
# nav_history
# ---------------------------------------------------------------------------


def test_nav_history_parses_and_sorts():
    hist = _src(_nav_history_payload()).nav_history(20)
    assert isinstance(hist, NavHistory)
    assert hist.source == "fmarket"
    assert hist.currency == "VND"
    assert hist.product_id == 20
    assert hist.fetched_at_utc is not None
    assert len(hist) == 3
    # sorted ascending by date
    dates = [p.date for p in hist]
    assert dates == [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
    p = hist.points[0]
    assert isinstance(p, NavPoint)
    assert p.date == date(2024, 1, 1)
    assert p.nav == pytest.approx(10180.25)


def test_nav_history_sends_all_data_flag_and_id():
    # Server requires fromDate+toDate always (absent pair -> HTTP 400); default
    # full-history request sends isAllData:1 plus a far-past from + today to.
    get = _capture_get(_nav_history_payload())
    FmarketFundSource(http_get=get).nav_history(20)
    body = get.calls[0]["json_body"]
    assert body["productId"] == 20
    assert body["isAllData"] == 1
    assert "fromDate" in body and "toDate" in body  # both mandatory upstream


def test_nav_history_date_window_passes_dates():
    get = _capture_get(_nav_history_payload())
    FmarketFundSource(http_get=get).nav_history(
        20, from_date=date(2024, 1, 1), to_date=date(2024, 6, 30)
    )
    body = get.calls[0]["json_body"]
    assert body["fromDate"] == "2024-01-01"
    assert body["toDate"] == "2024-06-30"
    assert body["isAllData"] == 1


def test_nav_history_from_date_filters_client_side():
    # Server only enforces toDate; the lower bound is applied client-side. The
    # synthetic payload spans 2024-01-01..2024-01-03; from_date=2024-01-02 keeps 2.
    hist = _src(_nav_history_payload()).nav_history(
        20, from_date=date(2024, 1, 2), to_date=date(2024, 12, 31)
    )
    assert [p.date for p in hist] == [date(2024, 1, 2), date(2024, 1, 3)]


def test_nav_history_empty_raises_empty():
    with pytest.raises(EmptyData):
        _src(_nav_history_payload(rows=[])).nav_history(20)


def test_nav_history_malformed_nav_raises_invalid():
    rows = [{"navDate": "2024-01-02", "nav": None, "productId": 20}]
    with pytest.raises(InvalidData):
        _src(_nav_history_payload(rows=rows)).nav_history(20)


def test_nav_history_bad_date_raises_invalid():
    rows = [{"navDate": "not-a-date", "nav": 100.0, "productId": 20}]
    with pytest.raises(InvalidData):
        _src(_nav_history_payload(rows=rows)).nav_history(20)


def test_nav_history_negative_nav_raises_invalid():
    rows = [{"navDate": "2024-01-02", "nav": -5.0, "productId": 20}]
    with pytest.raises(InvalidData):
        _src(_nav_history_payload(rows=rows)).nav_history(20)


def test_nav_history_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("not json at all").nav_history(20)


def test_nav_history_transport_error_wrapped():
    src = FmarketFundSource(http_get=_raising_get(TimeoutError("slow")))
    with pytest.raises(SourceUnavailable):
        src.nav_history(20)


def test_nav_history_to_dataframe():
    pd = pytest.importorskip("pandas")
    hist = _src(_nav_history_payload()).nav_history(20)
    df = hist.to_dataframe()
    assert list(df.columns) == ["nav"]
    assert df.index.name == "date"
    assert len(df) == 3
    assert df.attrs["currency"] == "VND"
    assert df.attrs["product_id"] == 20


# ---------------------------------------------------------------------------
# holdings
# ---------------------------------------------------------------------------


def test_holdings_parses_top_holdings():
    holdings = _src(_holdings_payload()).holdings(20)
    assert len(holdings) == 2
    h = holdings[0]
    assert isinstance(h, FundHolding)
    assert h.stock_code == "MBB"
    assert h.weight_pct == pytest.approx(7.99)
    assert h.industry == "Ngan hang"


def test_holdings_uses_id_in_path():
    get = _capture_get(_holdings_payload())
    FmarketFundSource(http_get=get).holdings(20)
    assert get.calls[0]["url"].endswith("/res/products/20")


def test_holdings_empty_raises_empty():
    with pytest.raises(EmptyData):
        _src(_holdings_payload(top=[])).holdings(20)


def test_holdings_malformed_weight_raises_invalid():
    top = [{"stockCode": "MBB", "netAssetPercent": "bad", "industry": "X"}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(20)


def test_holdings_weight_out_of_range_raises_invalid():
    top = [{"stockCode": "MBB", "netAssetPercent": 150.0, "industry": "X"}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(20)


def test_holdings_missing_stock_code_raises_invalid():
    top = [{"netAssetPercent": 7.99, "industry": "X"}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(20)


def test_holdings_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("<html/>").holdings(20)


def test_holdings_transport_error_wrapped():
    src = FmarketFundSource(http_get=_raising_get(OSError("net down")))
    with pytest.raises(SourceUnavailable):
        src.holdings(20)


# ---------------------------------------------------------------------------
# model immutability / contract
# ---------------------------------------------------------------------------


def test_models_are_frozen():
    f = Fund(code="X", name="N", id=1, nav=1.0, manager="M", asset_type="STOCK")
    with pytest.raises(Exception):
        f.nav = 2.0  # type: ignore[misc]


def test_fund_list_carries_fetched_at_utc():
    funds = _src(_fund_list_payload()).list_funds()
    # fetched_at must be tz-aware UTC
    assert funds.fetched_at_utc.tzinfo is timezone.utc or funds.fetched_at_utc.utcoffset() is not None
