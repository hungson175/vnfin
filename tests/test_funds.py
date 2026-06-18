"""Tests for the Fmarket funds adapter.

All payloads are hand-crafted SYNTHETIC JSON matching the verified provider shape
(see docs/sources/funds-fmarket.md). Per the synthetic-fixture policy (P0.4) every
symbol is OBVIOUSLY FAKE (TESTCO/FAKE*/ZZZ) and every number is FABRICATED — no
real fund codes, ids, NAVs, holdings, or allocation values from the research docs
are reused here. Only the JSON envelope SHAPE, units, and validation cases mirror
the real provider.
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


FAKE_ID_A = 9001  # obviously-fake product ids (not real Fmarket ids)
FAKE_ID_B = 9002
FAKE_NAV_A = 11111.11  # fabricated NAV/unit values
FAKE_NAV_B = 22222.22


def _fund_list_payload(rows=None, status=200, code=200):
    if rows is None:
        rows = [
            {
                "id": FAKE_ID_A,
                "code": "TESTCO",
                "shortName": "TESTCO",
                "name": "FAKE EQUITY FUND ALPHA",
                "nav": FAKE_NAV_A,
                "lastYearNav": 10000.0,
                "managementFee": 1.0,
                "avgAnnualReturn": 9.9,
                "dataFundAssetType": {"id": 1, "name": "Fake equity", "code": "STOCK"},
                "owner": {"id": 1, "name": "FAKE FUND MANAGER ALPHA", "shortName": "FFMA"},
            },
            {
                "id": FAKE_ID_B,
                "code": "ZZZBOND",
                "shortName": "ZZZBOND",
                "name": "FAKE BOND FUND BETA",
                "nav": FAKE_NAV_B,
                "dataFundAssetType": {"id": 2, "name": "Fake bond", "code": "BOND"},
                "owner": {"id": 2, "name": "FAKE FUND MANAGER BETA", "shortName": "FFMB"},
            },
        ]
    return json.dumps(
        {
            "status": status,
            "code": code,
            "message": "success",
            "data": {"total": len(rows), "page": 1, "pageSize": 100, "rows": rows},
            "extra": None,
        }
    )


def _nav_history_payload(rows=None, status=200, code=200):
    if rows is None:
        rows = [
            {"id": 1, "createdAt": 1700000000000, "nav": 10100.0, "navDate": "2024-01-02", "productId": FAKE_ID_A},
            {"id": 2, "createdAt": 1700000000000, "nav": 10200.0, "navDate": "2024-01-03", "productId": FAKE_ID_A},
            # intentionally out of order to prove sorting
            {"id": 3, "createdAt": None, "nav": 10000.0, "navDate": "2024-01-01", "productId": FAKE_ID_A},
        ]
    return json.dumps(
        {
            "status": status,
            "code": code,
            "message": "success",
            "data": rows,
            "extra": None,
        }
    )


def _holdings_payload(top=None, asset=None, industries=None, status=200, code=200, fund_code="TESTCO", nav=FAKE_NAV_A):
    if top is None:
        top = [
            {"stockCode": "FAKE1", "netAssetPercent": 5.0, "industry": "Fake industry one", "type": "STOCK", "price": 11.1},
            {"stockCode": "FAKE2", "netAssetPercent": 4.0, "industry": "Fake industry two", "type": "STOCK", "price": 22.2},
        ]
    if asset is None:
        asset = [
            {"assetType": {"code": "STOCK", "name": "Fake equity"}, "assetPercent": 90.0},
            {"assetType": {"code": "CASH", "name": "Fake cash"}, "assetPercent": 10.0},
        ]
    if industries is None:
        industries = [
            {"industry": "Fake industry one", "assetPercent": 50.0},
            {"industry": "Fake industry two", "assetPercent": 25.0},
        ]
    return json.dumps(
        {
            "status": status,
            "code": code,
            "message": "success",
            "data": {
                "id": FAKE_ID_A,
                "code": fund_code,
                "shortName": fund_code,
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
    assert f.code == "TESTCO"
    assert f.id == FAKE_ID_A
    assert f.name == "FAKE EQUITY FUND ALPHA"
    assert f.nav == pytest.approx(FAKE_NAV_A)
    assert f.manager == "FAKE FUND MANAGER ALPHA"
    assert f.asset_type == "STOCK"


def test_list_funds_iteration_and_indexing():
    funds = _src(_fund_list_payload()).list_funds()
    codes = [f.code for f in funds]  # __iter__
    assert codes == ["TESTCO", "ZZZBOND"]


def test_list_funds_asset_type_filter_passed_as_body():
    get = _capture_get(_fund_list_payload())
    src = FmarketFundSource(http_get=get)
    src.list_funds(asset_type="STOCK")
    body = get.calls[0]["json_body"]
    assert body["fundAssetTypes"] == ["STOCK"]


def test_list_funds_search_field_passed_as_body():
    get = _capture_get(_fund_list_payload())
    src = FmarketFundSource(http_get=get)
    src.list_funds(search="TESTCO")
    body = get.calls[0]["json_body"]
    assert body["searchField"] == "TESTCO"


# --- Issue #56: list_funds filter values must be strings -------------------------

@pytest.mark.parametrize("bad", [True, ["STOCK"], {"code": "STOCK"}, 123])
def test_list_funds_rejects_non_string_asset_type(bad):
    with pytest.raises(InvalidData):
        FmarketFundSource(http_get=_capture_get(_fund_list_payload())).list_funds(asset_type=bad)


@pytest.mark.parametrize("bad", [["TESTCO"], {"q": "TESTCO"}, 123])
def test_list_funds_rejects_non_string_search(bad):
    with pytest.raises(InvalidData):
        FmarketFundSource(http_get=_capture_get(_fund_list_payload())).list_funds(search=bad)


def test_list_funds_rejects_invalid_filter_before_network():
    called = {"n": 0}

    def _g(url, params=None, headers=None, json_body=None):
        called["n"] += 1
        return _fund_list_payload()

    with pytest.raises(InvalidData):
        FmarketFundSource(http_get=_g).list_funds(asset_type=True)
    assert called["n"] == 0


def test_list_funds_empty_rows_raises_empty():
    with pytest.raises(EmptyData):
        _src(_fund_list_payload(rows=[])).list_funds()


def test_list_funds_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("<html>nope</html>").list_funds()


def test_list_funds_non_dict_top_level_raises_invalid():
    with pytest.raises(InvalidData):
        _src("[1, 2, 3]").list_funds()


def test_list_funds_malformed_nav_raises_invalid():
    rows = [
        {
            "id": FAKE_ID_A,
            "code": "TESTCO",
            "shortName": "TESTCO",
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
            "code": "TESTCO",
            "shortName": "TESTCO",
            "name": "X",
            "nav": 100.0,
            "dataFundAssetType": {"code": "STOCK"},
            "owner": {"name": "M"},
        }
    ]
    with pytest.raises(InvalidData):
        _src(_fund_list_payload(rows=rows)).list_funds()


def test_list_funds_owner_not_object_raises_invalid():
    # Provider blocker: a non-dict nested `owner` must NOT leak a raw AttributeError.
    rows = [
        {
            "id": FAKE_ID_A,
            "code": "TESTCO",
            "name": "X",
            "nav": 100.0,
            "dataFundAssetType": {"code": "STOCK"},
            "owner": "not-an-object",
        }
    ]
    with pytest.raises(InvalidData):
        _src(_fund_list_payload(rows=rows)).list_funds()


def test_list_funds_asset_type_not_object_raises_invalid():
    # Provider blocker: a non-dict nested `dataFundAssetType` must raise InvalidData.
    rows = [
        {
            "id": FAKE_ID_A,
            "code": "TESTCO",
            "name": "X",
            "nav": 100.0,
            "dataFundAssetType": ["STOCK"],
            "owner": {"name": "M"},
        }
    ]
    with pytest.raises(InvalidData):
        _src(_fund_list_payload(rows=rows)).list_funds()


def test_list_funds_application_error_status_raises_unavailable():
    # Provider blocker: a 2xx HTTP body carrying application status=500 must NOT
    # parse as success; it should raise SourceUnavailable (failover-safe).
    with pytest.raises(SourceUnavailable):
        _src(_fund_list_payload(status=500)).list_funds()


def test_list_funds_application_error_code_raises_unavailable():
    with pytest.raises(SourceUnavailable):
        _src(_fund_list_payload(code=403)).list_funds()


def test_list_funds_non_integer_envelope_status_raises_invalid():
    payload = json.dumps({"status": "not-an-int", "code": 200, "data": {"rows": []}})
    with pytest.raises(InvalidData):
        _src(payload).list_funds()


def test_list_funds_missing_envelope_status_and_code_raises_invalid():
    # Issue #41: an Fmarket response without `status` or `code` is not a valid envelope.
    payload = json.dumps({"message": "ok", "data": {"total": 0, "page": 1, "pageSize": 100, "rows": []}})
    with pytest.raises(InvalidData):
        _src(payload).list_funds()


def test_list_funds_missing_envelope_but_with_data_raises_invalid():
    payload = json.dumps({"data": {"total": 1, "page": 1, "pageSize": 100, "rows": [{"id": FAKE_ID_A, "code": "TESTCO", "shortName": "TESTCO", "name": "X", "nav": 100.0, "dataFundAssetType": {"code": "STOCK"}, "owner": {"name": "M"}}]}})
    with pytest.raises(InvalidData):
        _src(payload).list_funds()


def test_list_funds_invalid_page_size_rejected():
    # Issue #18: invalid page_size must raise InvalidData before reaching provider.
    for bad in (-1, 0, "x", 10000):
        with pytest.raises(InvalidData):
            _src("{}").list_funds(page_size=bad)


def test_list_funds_malformed_fund_code_raises_invalid():
    # Issue #33: blank/whitespace-only fund codes are not valid identifiers.
    rows = [
        {
            "id": FAKE_ID_A,
            "code": "   ",
            "shortName": "   ",
            "name": "X",
            "nav": 100.0,
            "dataFundAssetType": {"code": "STOCK"},
            "owner": {"name": "M"},
        }
    ]
    with pytest.raises(InvalidData):
        _src(_fund_list_payload(rows=rows)).list_funds()


def test_list_funds_non_positive_id_raises_invalid():
    # Issue #33: provider IDs must be positive integers.
    rows = [
        {
            "id": 0,
            "code": "TESTCO",
            "shortName": "TESTCO",
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
    hist = _src(_nav_history_payload()).nav_history(FAKE_ID_A)
    assert isinstance(hist, NavHistory)
    assert hist.source == "fmarket"
    assert hist.currency == "VND"
    assert hist.product_id == FAKE_ID_A
    assert hist.fetched_at_utc is not None
    assert len(hist) == 3
    # sorted ascending by date
    dates = [p.date for p in hist]
    assert dates == [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
    p = hist.points[0]
    assert isinstance(p, NavPoint)
    assert p.date == date(2024, 1, 1)
    assert p.nav == pytest.approx(10000.0)


def test_nav_history_sends_all_data_flag_and_id():
    # Server requires fromDate+toDate always (absent pair -> HTTP 400); default
    # full-history request sends isAllData:1 plus a far-past from + today to.
    get = _capture_get(_nav_history_payload())
    FmarketFundSource(http_get=get).nav_history(FAKE_ID_A)
    body = get.calls[0]["json_body"]
    assert body["productId"] == FAKE_ID_A
    assert body["isAllData"] == 1
    assert "fromDate" in body and "toDate" in body  # both mandatory upstream


def test_nav_history_date_window_passes_dates():
    get = _capture_get(_nav_history_payload())
    FmarketFundSource(http_get=get).nav_history(
        FAKE_ID_A, from_date=date(2024, 1, 1), to_date=date(2024, 6, 30)
    )
    body = get.calls[0]["json_body"]
    assert body["fromDate"] == "2024-01-01"
    assert body["toDate"] == "2024-06-30"
    assert body["isAllData"] == 1


def test_nav_history_date_window_accepts_string_dates():
    # YYYY-MM-DD strings are accepted and normalized to the request body.
    get = _capture_get(_nav_history_payload())
    FmarketFundSource(http_get=get).nav_history(
        FAKE_ID_A, from_date="2024-01-01", to_date="2024-06-30"
    )
    body = get.calls[0]["json_body"]
    assert body["fromDate"] == "2024-01-01"
    assert body["toDate"] == "2024-06-30"


def test_nav_history_from_date_filters_client_side():
    # Server only enforces toDate; the lower bound is applied client-side. The
    # synthetic payload spans 2024-01-01..2024-01-03; from_date=2024-01-02 keeps 2.
    hist = _src(_nav_history_payload()).nav_history(
        FAKE_ID_A, from_date=date(2024, 1, 2), to_date=date(2024, 12, 31)
    )
    assert [p.date for p in hist] == [date(2024, 1, 2), date(2024, 1, 3)]


def test_nav_history_to_date_filters_client_side():
    # Blocker: to_date must be enforced client-side too (server is unreliable near
    # recent boundaries). Payload spans 2024-01-01..2024-01-03; to_date=2024-01-02
    # keeps only the first two.
    hist = _src(_nav_history_payload()).nav_history(
        FAKE_ID_A, from_date="2024-01-01", to_date="2024-01-02"
    )
    assert [p.date for p in hist] == [date(2024, 1, 1), date(2024, 1, 2)]


def test_nav_history_from_after_to_raises_invalid():
    # Blocker: an inverted window must raise InvalidData, not silently ignore.
    with pytest.raises(InvalidData):
        _src(_nav_history_payload()).nav_history(
            FAKE_ID_A, from_date="2024-06-30", to_date="2024-01-01"
        )


def test_nav_history_malformed_caller_from_date_raises_invalid():
    # Blocker: a malformed caller-supplied date must raise InvalidData, never a
    # raw ValueError leaking out of the public method.
    with pytest.raises(InvalidData):
        _src(_nav_history_payload()).nav_history(FAKE_ID_A, from_date="13/2024")


def test_nav_history_malformed_caller_to_date_raises_invalid():
    with pytest.raises(InvalidData):
        _src(_nav_history_payload()).nav_history(FAKE_ID_A, to_date="not-a-date")


def test_nav_history_empty_raises_empty():
    with pytest.raises(EmptyData):
        _src(_nav_history_payload(rows=[])).nav_history(FAKE_ID_A)


def test_nav_history_application_error_status_raises_unavailable():
    with pytest.raises(SourceUnavailable):
        _src(_nav_history_payload(status=500)).nav_history(FAKE_ID_A)


def test_nav_history_missing_envelope_status_and_code_raises_invalid():
    # Issue #41: NAV history response missing both `status` and `code` is invalid.
    payload = json.dumps({"message": "ok", "data": [{"navDate": "2024-01-02", "nav": 100.0, "productId": FAKE_ID_A}]})
    with pytest.raises(InvalidData):
        _src(payload).nav_history(FAKE_ID_A)


def test_nav_history_malformed_nav_raises_invalid():
    rows = [{"navDate": "2024-01-02", "nav": None, "productId": FAKE_ID_A}]
    with pytest.raises(InvalidData):
        _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)


def test_nav_history_bad_date_raises_invalid():
    rows = [{"navDate": "not-a-date", "nav": 100.0, "productId": FAKE_ID_A}]
    with pytest.raises(InvalidData):
        _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)


def test_nav_history_negative_nav_raises_invalid():
    rows = [{"navDate": "2024-01-02", "nav": -5.0, "productId": FAKE_ID_A}]
    with pytest.raises(InvalidData):
        _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)


def test_nav_history_invalid_product_id_rejected():
    # Issue #8: invalid product_id types/values must raise InvalidData before request.
    for bad in (-1, 0, "x", 3.7, None):
        with pytest.raises(InvalidData):
            _src("{}").nav_history(bad)


def test_holdings_invalid_product_id_rejected():
    # Issue #8: invalid product_id types/values must raise InvalidData before request.
    for bad in (-1, 0, "x", 3.7, None, "003"):
        with pytest.raises(InvalidData):
            _src("{}").holdings(bad)


def test_nav_history_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("not json at all").nav_history(FAKE_ID_A)


def test_nav_history_transport_error_wrapped():
    src = FmarketFundSource(http_get=_raising_get(TimeoutError("slow")))
    with pytest.raises(SourceUnavailable):
        src.nav_history(FAKE_ID_A)


def test_nav_history_to_dataframe():
    import pandas as pd
    hist = _src(_nav_history_payload()).nav_history(FAKE_ID_A)
    df = hist.to_dataframe()
    assert list(df.columns) == ["nav"]
    assert df.index.name == "date"
    assert len(df) == 3
    assert df.attrs["currency"] == "VND"
    assert df.attrs["product_id"] == FAKE_ID_A


# ---------------------------------------------------------------------------
# holdings
# ---------------------------------------------------------------------------


def test_holdings_parses_top_holdings():
    holdings = _src(_holdings_payload()).holdings(FAKE_ID_A)
    assert len(holdings) == 2
    h = holdings[0]
    assert isinstance(h, FundHolding)
    assert h.stock_code == "FAKE1"
    assert h.weight_pct == pytest.approx(5.0)
    assert h.industry == "Fake industry one"


def test_holdings_price_is_raw_with_explicit_unit():
    # Blocker: provider price scale is unverified — must surface as price_raw with
    # an explicit "raw" price_unit, never as a canonically-normalized money value.
    holdings = _src(_holdings_payload()).holdings(FAKE_ID_A)
    h = holdings[0]
    assert h.price_raw == pytest.approx(11.1)
    assert h.price_unit == "raw"
    assert not hasattr(h, "price")  # old ambiguous field is gone


def test_holdings_missing_price_leaves_raw_and_unit_none():
    top = [{"stockCode": "FAKE1", "netAssetPercent": 5.0, "industry": "X"}]
    h = _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)[0]
    assert h.price_raw is None
    assert h.price_unit is None


def test_holdings_uses_id_in_path():
    get = _capture_get(_holdings_payload())
    FmarketFundSource(http_get=get).holdings(FAKE_ID_A)
    assert get.calls[0]["url"].endswith(f"/res/products/{FAKE_ID_A}")


def test_holdings_empty_raises_empty():
    with pytest.raises(EmptyData):
        _src(_holdings_payload(top=[])).holdings(FAKE_ID_A)


def test_holdings_blank_stock_code_raises_invalid():
    # Issue #34: blank/whitespace stock codes are not valid identifiers.
    top = [
        {"stockCode": "   ", "netAssetPercent": 5.0, "industry": "X"},
    ]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_duplicate_stock_code_raises_invalid():
    # Issue #34: duplicate stock codes within one fund's holdings are a contract
    # violation and must raise InvalidData.
    top = [
        {"stockCode": "FAKE1", "netAssetPercent": 5.0, "industry": "X"},
        {"stockCode": "FAKE1", "netAssetPercent": 3.0, "industry": "X"},
    ]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_negative_raw_price_raises_invalid():
    # Issue #29: negative raw prices are impossible and must raise InvalidData.
    top = [{"stockCode": "FAKE1", "netAssetPercent": 5.0, "price": -10.0}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_application_error_status_raises_unavailable():
    with pytest.raises(SourceUnavailable):
        _src(_holdings_payload(status=500)).holdings(FAKE_ID_A)


def test_holdings_missing_envelope_status_and_code_raises_invalid():
    # Issue #41: holdings response missing both `status` and `code` is invalid.
    payload = json.dumps(
        {
            "message": "ok",
            "data": {
                "id": FAKE_ID_A,
                "code": "TESTCO",
                "shortName": "TESTCO",
                "nav": FAKE_NAV_A,
                "productTopHoldingList": [{"stockCode": "FAKE1", "netAssetPercent": 5.0}],
            },
        }
    )
    with pytest.raises(InvalidData):
        _src(payload).holdings(FAKE_ID_A)


def test_holdings_malformed_weight_raises_invalid():
    top = [{"stockCode": "FAKE1", "netAssetPercent": "bad", "industry": "X"}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_weight_out_of_range_raises_invalid():
    top = [{"stockCode": "FAKE1", "netAssetPercent": 150.0, "industry": "X"}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_malformed_price_raises_invalid():
    top = [{"stockCode": "FAKE1", "netAssetPercent": 5.0, "price": "garbage"}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_missing_stock_code_raises_invalid():
    top = [{"netAssetPercent": 5.0, "industry": "X"}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_non_json_raises_invalid():
    with pytest.raises(InvalidData):
        _src("<html/>").holdings(FAKE_ID_A)


def test_holdings_transport_error_wrapped():
    src = FmarketFundSource(http_get=_raising_get(OSError("net down")))
    with pytest.raises(SourceUnavailable):
        src.holdings(FAKE_ID_A)


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
