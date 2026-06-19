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


@pytest.mark.parametrize("bad", [True, ["STOCK"], {"code": "STOCK"}, 123])
def test_list_funds_rejects_non_string_asset_type_before_network(bad):
    called = {"n": 0}

    def _g(url, params=None, headers=None, json_body=None):
        called["n"] += 1
        return _fund_list_payload()

    with pytest.raises(InvalidData):
        FmarketFundSource(http_get=_g).list_funds(asset_type=bad)
    assert called["n"] == 0


@pytest.mark.parametrize("bad", [["TESTCO"], {"q": "TESTCO"}, 123])
def test_list_funds_rejects_non_string_search_before_network(bad):
    called = {"n": 0}

    def _g(url, params=None, headers=None, json_body=None):
        called["n"] += 1
        return _fund_list_payload()

    with pytest.raises(InvalidData):
        FmarketFundSource(http_get=_g).list_funds(search=bad)
    assert called["n"] == 0


def test_list_funds_whitespace_asset_type_treated_as_absent():
    get = _capture_get(_fund_list_payload())
    FmarketFundSource(http_get=get).list_funds(asset_type="   ")
    assert get.calls[0]["json_body"]["fundAssetTypes"] == []


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


@pytest.mark.parametrize("bad", [200.9, 200.5, 199.999, float("inf"), float("nan"), True, False], ids=["frac_2xx", "frac_half", "frac_near200", "inf", "nan", "true", "false"])
def test_list_funds_fractional_or_bool_envelope_status_raises_invalid(bad):
    # Issue #41 (reopen): int(200.9) silently truncates to 200; a fractional/bool
    # application status must be rejected as a malformed envelope, not accepted.
    payload = json.dumps({"status": bad, "code": 200, "data": {"rows": []}})
    with pytest.raises(InvalidData):
        _src(payload).list_funds()


@pytest.mark.parametrize("bad", [200.9, 403.5, True], ids=["frac_2xx", "frac_4xx", "bool"])
def test_list_funds_fractional_or_bool_envelope_code_raises_invalid(bad):
    payload = json.dumps({"status": 200, "code": bad, "data": {"rows": []}})
    with pytest.raises(InvalidData):
        _src(payload).list_funds()


def test_list_funds_integral_float_status_still_accepted():
    # An integral float (e.g. 200.0) is not fractional -> the envelope guard must
    # accept it (success proves it was not rejected as malformed).
    funds = _src(_fund_list_payload(status=200.0, code=200.0)).list_funds()
    assert len(funds) >= 1


def _nav_rows(product_id):
    return [{"id": 1, "createdAt": 1700000000000, "nav": 10100.0, "navDate": "2024-01-02", "productId": product_id}]


def test_nav_history_rejects_mismatched_row_product_id():
    # Issue #21 (reopen): a NAV row whose productId is not the requested fund is a
    # provider/cache identity error, not data to stamp as the requested product.
    payload = _nav_history_payload(rows=_nav_rows(9999))
    with pytest.raises(InvalidData):
        _src(payload).nav_history(FAKE_ID_A)


@pytest.mark.parametrize("bad_pid", [True, float(FAKE_ID_A), str(FAKE_ID_A)], ids=["bool", "float", "str"])
def test_nav_history_rejects_malformed_row_product_id(bad_pid):
    payload = _nav_history_payload(rows=_nav_rows(bad_pid))
    with pytest.raises(InvalidData):
        _src(payload).nav_history(FAKE_ID_A)


def test_nav_history_rejects_present_null_row_product_id():
    # #21 BLOCK: a present `productId: null` must NOT bypass the guard (key-presence
    # is the trigger, not truthiness).
    rows = [{"id": 1, "createdAt": 1700000000000, "nav": 10100.0, "navDate": "2024-01-02", "productId": None}]
    with pytest.raises(InvalidData):
        _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)


def test_nav_history_accepts_matching_and_absent_row_product_id():
    rows = [
        {"id": 1, "createdAt": 1700000000000, "nav": 10100.0, "navDate": "2024-01-02", "productId": FAKE_ID_A},
        {"id": 2, "createdAt": None, "nav": 10000.0, "navDate": "2024-01-01"},  # productId absent
    ]
    hist = _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)
    assert hist.product_id == FAKE_ID_A and len(hist.points) == 2


def _holdings_payload_with(**data_overrides):
    base = json.loads(_holdings_payload())
    base["data"].update(data_overrides)
    return json.dumps(base)


def test_holdings_rejects_mismatched_detail_id():
    with pytest.raises(InvalidData):
        _src(_holdings_payload_with(id=9999)).holdings(FAKE_ID_A)


def test_holdings_rejects_null_detail_id():
    # #21 BLOCK: data.id null must not bypass the identity check.
    with pytest.raises(InvalidData):
        _src(_holdings_payload_with(id=None)).holdings(FAKE_ID_A)


def test_holdings_rejects_missing_detail_id():
    # #21 BLOCK: a detail document with no `id` cannot identify the fund -> reject.
    base = json.loads(_holdings_payload())
    base["data"].pop("id", None)
    with pytest.raises(InvalidData):
        _src(json.dumps(base)).holdings(FAKE_ID_A)


@pytest.mark.parametrize("bad_code", [123, [], {}, "", "   ", " TESTCO", "TESTCO "], ids=["int", "list", "dict", "blank", "ws", "lead_pad", "trail_pad"])
def test_holdings_rejects_malformed_detail_code(bad_code):
    # #21 BLOCK: code must be a non-empty CANONICAL string (padded values rejected).
    with pytest.raises(InvalidData):
        _src(_holdings_payload_with(code=bad_code)).holdings(FAKE_ID_A)


def test_holdings_accepts_matching_detail_identity():
    holdings = _src(_holdings_payload()).holdings(FAKE_ID_A)
    assert len(holdings) >= 1


def test_list_funds_digit_string_status_accepted():
    # Digit-string status/code (e.g. "200") remains valid via int() coercion.
    funds = _src(_fund_list_payload(status="200", code="200")).list_funds()
    assert len(funds) >= 1


def test_list_funds_missing_envelope_status_and_code_raises_invalid():
    # Issue #41: an Fmarket response without `status` or `code` is not a valid envelope.
    payload = json.dumps({"message": "ok", "data": {"total": 0, "page": 1, "pageSize": 100, "rows": []}})
    with pytest.raises(InvalidData):
        _src(payload).list_funds()


def test_list_funds_missing_envelope_but_with_data_raises_invalid():
    payload = json.dumps({"data": {"total": 1, "page": 1, "pageSize": 100, "rows": [{"id": FAKE_ID_A, "code": "TESTCO", "shortName": "TESTCO", "name": "X", "nav": 100.0, "dataFundAssetType": {"code": "STOCK"}, "owner": {"name": "M"}}]}})
    with pytest.raises(InvalidData):
        _src(payload).list_funds()


def test_list_funds_duplicate_code_raises_invalid():
    # Issue #68: duplicate normalized public fund codes within one response must
    # raise InvalidData instead of silently returning ambiguous data.
    rows = [
        {
            "id": FAKE_ID_A,
            "code": "TESTCO",
            "shortName": "TESTCO",
            "name": "X",
            "nav": 100.0,
            "dataFundAssetType": {"code": "STOCK"},
            "owner": {"name": "M"},
        },
        {
            "id": FAKE_ID_B,
            "code": "TESTCO",
            "shortName": "TESTCO",
            "name": "Y",
            "nav": 200.0,
            "dataFundAssetType": {"code": "BOND"},
            "owner": {"name": "N"},
        },
    ]
    with pytest.raises(InvalidData, match="duplicate fund code"):
        _src(_fund_list_payload(rows=rows)).list_funds()


def test_list_funds_case_insensitive_duplicate_code_raises_invalid():
    # Issue #68: codes that normalize to the same value (case-insensitive + surrounding
    # whitespace) must be treated as duplicates, e.g. "TESTCO" vs " testco ".
    rows = [
        {
            "id": FAKE_ID_A, "code": "TESTCO", "shortName": "TESTCO", "name": "X",
            "nav": 100.0, "dataFundAssetType": {"code": "STOCK"}, "owner": {"name": "M"},
        },
        {
            "id": FAKE_ID_B, "code": " testco ", "shortName": " testco ", "name": "Y",
            "nav": 200.0, "dataFundAssetType": {"code": "BOND"}, "owner": {"name": "N"},
        },
    ]
    with pytest.raises(InvalidData, match="duplicate fund code"):
        _src(_fund_list_payload(rows=rows)).list_funds()


def test_list_funds_duplicate_id_raises_invalid():
    # Issue #68: duplicate provider ids within one response must raise InvalidData.
    rows = [
        {
            "id": FAKE_ID_A,
            "code": "TESTCO",
            "shortName": "TESTCO",
            "name": "X",
            "nav": 100.0,
            "dataFundAssetType": {"code": "STOCK"},
            "owner": {"name": "M"},
        },
        {
            "id": FAKE_ID_A,
            "code": "ZZZBOND",
            "shortName": "ZZZBOND",
            "name": "Y",
            "nav": 200.0,
            "dataFundAssetType": {"code": "BOND"},
            "owner": {"name": "N"},
        },
    ]
    with pytest.raises(InvalidData, match="duplicate fund id"):
        _src(_fund_list_payload(rows=rows)).list_funds()


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


def test_list_funds_float_id_raises_invalid():
    # Blocker: float provider IDs must NOT silently truncate.
    rows = [
        {
            "id": 3.7,
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


def test_list_funds_bool_id_raises_invalid():
    # Blocker: bool provider IDs must NOT be accepted as integers.
    rows = [
        {
            "id": True,
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


def test_list_funds_non_string_code_raises_invalid():
    # Blocker: numeric/list/object fund codes must NOT leak AttributeError.
    for bad_code in (123, ["TESTCO"], {"code": "TESTCO"}):
        rows = [
            {
                "id": FAKE_ID_A,
                "code": bad_code,
                "shortName": "TESTCO",
                "name": "X",
                "nav": 100.0,
                "dataFundAssetType": {"code": "STOCK"},
                "owner": {"name": "M"},
            }
        ]
        with pytest.raises(InvalidData):
            _src(_fund_list_payload(rows=rows)).list_funds()


def test_list_funds_non_string_shortName_fallback_raises_invalid():
    # Blocker: numeric/list/object shortName fallback must NOT leak AttributeError.
    for bad_short in (123, ["TESTCO"], {"code": "TESTCO"}):
        rows = [
            {
                "id": FAKE_ID_A,
                "code": None,
                "shortName": bad_short,
                "name": "X",
                "nav": 100.0,
                "dataFundAssetType": {"code": "STOCK"},
                "owner": {"name": "M"},
            }
        ]
        with pytest.raises(InvalidData):
            _src(_fund_list_payload(rows=rows)).list_funds()


def test_list_funds_missing_code_and_shortName_raises_invalid():
    rows = [
        {
            "id": FAKE_ID_A,
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


def test_nav_history_duplicate_nav_date_raises_invalid():
    # Issue #66 (Fmarket part): duplicate navDate values within one response must
    # raise InvalidData because the series would otherwise contain ambiguous observations.
    rows = [
        {"navDate": "2024-01-02", "nav": 10100.0, "productId": FAKE_ID_A},
        {"navDate": "2024-01-03", "nav": 10200.0, "productId": FAKE_ID_A},
        {"navDate": "2024-01-02", "nav": 10300.0, "productId": FAKE_ID_A},
    ]
    with pytest.raises(InvalidData, match="duplicate navDate"):
        _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)


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


# --- Issue #13: NAV parsers must reject zero-valued market observations

def test_nav_history_zero_nav_raises_invalid():
    rows = [{"navDate": "2024-01-02", "nav": 0.0, "productId": FAKE_ID_A}]
    with pytest.raises(InvalidData):
        _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)


def test_nav_history_invalid_product_id_rejected():
    # Issue #8: invalid product_id types/values must raise InvalidData before request.
    for bad in (-1, 0, "x", 3.7, None, "003", True):
        with pytest.raises(InvalidData):
            _src("{}").nav_history(bad)


def test_holdings_invalid_product_id_rejected():
    # Issue #8: invalid product_id types/values must raise InvalidData before request.
    for bad in (-1, 0, "x", 3.7, None, "003", True):
        with pytest.raises(InvalidData):
            _src("{}").holdings(bad)


@pytest.mark.parametrize("bad", [-1, 0, "x", 3.7, None, "003", True])
def test_holdings_invalid_product_id_no_transport(bad):
    # Reviewer B2: every invalid product_id must short-circuit before transport.
    called = {"n": 0}

    def _g(url, params=None, headers=None, json_body=None):
        called["n"] += 1
        return "{}"

    with pytest.raises(InvalidData):
        FmarketFundSource(http_get=_g).holdings(bad)
    assert called["n"] == 0, f"transport was called for {bad!r}"


def test_nav_history_string_numeric_product_id_no_transport():
    # Blocker: numeric strings must NOT be silently coerced and must NOT reach transport.
    called = {"n": 0}

    def _g(url, params=None, headers=None, json_body=None):
        called["n"] += 1
        return "{}"

    with pytest.raises(InvalidData):
        FmarketFundSource(http_get=_g).nav_history("003")
    assert called["n"] == 0


def test_nav_history_bool_float_product_id_no_transport():
    for bad in (True, 3.7):
        called = {"n": 0}

        def _g(url, params=None, headers=None, json_body=None):
            called["n"] += 1
            return "{}"

        with pytest.raises(InvalidData):
            FmarketFundSource(http_get=_g).nav_history(bad)
        assert called["n"] == 0, f"transport was called for {bad!r}"


@pytest.mark.parametrize("bad", [-1, 0, "x", 3.7, None, "003", True])
def test_nav_history_invalid_product_id_no_transport(bad):
    # Reviewer B2: every invalid product_id must short-circuit before transport.
    called = {"n": 0}

    def _g(url, params=None, headers=None, json_body=None):
        called["n"] += 1
        return "{}"

    with pytest.raises(InvalidData):
        FmarketFundSource(http_get=_g).nav_history(bad)
    assert called["n"] == 0, f"transport was called for {bad!r}"


def test_holdings_string_numeric_product_id_no_transport():
    # Blocker: numeric strings must NOT be silently coerced and must NOT reach transport.
    called = {"n": 0}

    def _g(url, params=None, headers=None, json_body=None):
        called["n"] += 1
        return "{}"

    with pytest.raises(InvalidData):
        FmarketFundSource(http_get=_g).holdings("003")
    assert called["n"] == 0


def test_holdings_bool_float_product_id_no_transport():
    for bad in (True, 3.7):
        called = {"n": 0}

        def _g(url, params=None, headers=None, json_body=None):
            called["n"] += 1
            return "{}"

        with pytest.raises(InvalidData):
            FmarketFundSource(http_get=_g).holdings(bad)
        assert called["n"] == 0, f"transport was called for {bad!r}"


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


def test_list_funds_non_object_data_raises_invalid():
    # Issue #91: success envelope with string `data` must not leak AttributeError.
    payload = json.dumps({"status": 200, "code": 200, "message": "success", "data": "not-an-object"})
    with pytest.raises(InvalidData, match="data is not an object"):
        _src(payload).list_funds()


def test_holdings_non_object_data_raises_invalid():
    payload = json.dumps({"status": 200, "code": 200, "message": "success", "data": "not-an-object"})
    with pytest.raises(InvalidData, match="data is not an object"):
        _src(payload).holdings(FAKE_ID_A)


def test_list_funds_bool_nav_raises_invalid():
    # Issue #87: JSON booleans must not coerce into plausible NAV values.
    rows = [
        {
            "id": FAKE_ID_A,
            "code": "TESTCO",
            "shortName": "TESTCO",
            "name": "X",
            "nav": True,
            "dataFundAssetType": {"code": "STOCK"},
            "owner": {"name": "M"},
        }
    ]
    with pytest.raises(InvalidData, match="bool is not numeric"):
        _src(_fund_list_payload(rows=rows)).list_funds()


@pytest.mark.parametrize(
    "mutator",
    [
        lambda r: r.update(name=["BAD", "NAME"]),
        lambda r: r.update(name={"en": "BAD"}),
        lambda r: r["owner"].update(name=["BAD", "MANAGER"]),
        lambda r: r["dataFundAssetType"].update(code=["STOCK"]),
        lambda r: r["dataFundAssetType"].update(code=True),
    ],
    ids=["name_list", "name_dict", "manager_list", "asset_type_list", "asset_type_bool"],
)
def test_list_funds_rejects_malformed_metadata(mutator):
    # Issue #97: classification/display fields must be strings, not str(...) coercions.
    row = {
        "id": FAKE_ID_A,
        "code": "TESTCO",
        "shortName": "TESTCO",
        "name": "FAKE FUND",
        "nav": 100.0,
        "dataFundAssetType": {"code": "STOCK"},
        "owner": {"name": "FAKE MANAGER"},
    }
    row = dict(row)
    row["owner"] = dict(row["owner"])
    row["dataFundAssetType"] = dict(row["dataFundAssetType"])
    mutator(row)
    with pytest.raises(InvalidData, match="is not a string"):
        _src(_fund_list_payload(rows=[row])).list_funds()


@pytest.mark.parametrize(
    "industry",
    [["BANKING"], {"name": "BANKING"}, 123, True],
    ids=["list", "dict", "int", "bool"],
)
def test_holdings_rejects_malformed_industry(industry):
    # Issue #99: industry classification must be a string or absent.
    top = [{"stockCode": "FAKE1", "netAssetPercent": 5.0, "industry": industry}]
    with pytest.raises(InvalidData, match="industry is not a string"):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_malformed_weight_raises_invalid():
    top = [{"stockCode": "FAKE1", "netAssetPercent": "bad", "industry": "X"}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_weight_out_of_range_raises_invalid():
    top = [{"stockCode": "FAKE1", "netAssetPercent": 150.0, "industry": "X"}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_aggregate_weight_above_100_raises_invalid():
    # Issue #90: top disclosed holdings must not sum above 100%.
    top = [
        {"stockCode": "FAKE1", "netAssetPercent": 80.0, "industry": "X"},
        {"stockCode": "FAKE2", "netAssetPercent": 70.0, "industry": "Y"},
    ]
    with pytest.raises(InvalidData, match="aggregate holdings weight exceeds 100%"):
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
# envelope validation regressions
# ---------------------------------------------------------------------------


def test_unwrap_missing_status_and_code_raises_invalid():
    # Issue #41: a response missing both `status` and `code` is not a valid Fmarket
    # application envelope and must raise InvalidData regardless of payload content.
    with pytest.raises(InvalidData, match="missing status/code envelope"):
        FmarketFundSource._unwrap({"message": "ok", "data": {}}, who="regression")


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


# ---------------------------------------------------------------------------
# Issue #97: present non-dict owner / dataFundAssetType must raise InvalidData
# ---------------------------------------------------------------------------


def _valid_fund_row():
    return {
        "id": FAKE_ID_A,
        "code": "TESTCO",
        "shortName": "TESTCO",
        "name": "FAKE FUND",
        "nav": 100.0,
        "dataFundAssetType": {"code": "STOCK"},
        "owner": {"name": "FAKE MANAGER"},
    }


@pytest.mark.parametrize("owner", ["", [], False, 0])
def test_parse_fund_present_non_dict_owner_raises_invalid(owner):
    row = _valid_fund_row()
    row["owner"] = owner
    with pytest.raises(InvalidData, match="owner is not an object"):
        FmarketFundSource._parse_fund(row)


@pytest.mark.parametrize("asset", ["", [], False, 0])
def test_parse_fund_present_non_dict_asset_type_raises_invalid(asset):
    row = _valid_fund_row()
    row["dataFundAssetType"] = asset
    with pytest.raises(InvalidData, match="dataFundAssetType is not an object"):
        FmarketFundSource._parse_fund(row)


@pytest.mark.parametrize("owner", [None, {}])
@pytest.mark.parametrize("asset", [None, {}])
def test_parse_fund_absent_or_empty_owner_and_asset_allowed(owner, asset):
    row = _valid_fund_row()
    row["owner"] = owner
    row["dataFundAssetType"] = asset
    fund = FmarketFundSource._parse_fund(row)
    assert fund.manager == ""
    assert fund.asset_type == ""


# ---------------------------------------------------------------------------
# Issue #109: present non-list primary array fields must raise InvalidData
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rows", [{}, "", False, 0])
def test_list_funds_present_non_list_rows_raises_invalid(rows):
    payload = json.dumps(
        {"status": 200, "code": 200, "message": "success", "data": {"rows": rows}}
    )
    with pytest.raises(InvalidData, match="rows is not an array"):
        _src(payload).list_funds()


def test_list_funds_absent_rows_raises_empty():
    payload = json.dumps(
        {"status": 200, "code": 200, "message": "success", "data": {}}
    )
    with pytest.raises(EmptyData):
        _src(payload).list_funds()


@pytest.mark.parametrize("data", [{}, "", False, 0])
def test_nav_history_present_non_list_data_raises_invalid(data):
    payload = json.dumps(
        {"status": 200, "code": 200, "message": "success", "data": data}
    )
    with pytest.raises(InvalidData, match="nav-history data is not an array"):
        _src(payload).nav_history(FAKE_ID_A)


def test_nav_history_absent_data_raises_empty():
    payload = json.dumps({"status": 200, "code": 200, "message": "success"})
    with pytest.raises(EmptyData):
        _src(payload).nav_history(FAKE_ID_A)


@pytest.mark.parametrize("top", [{}, "", False, 0])
def test_holdings_present_non_list_top_holding_raises_invalid(top):
    payload = json.dumps(
        {
            "status": 200,
            "code": 200,
            "message": "success",
            "data": {
                "id": FAKE_ID_A,
                "code": "TESTCO",
                "shortName": "TESTCO",
                "nav": FAKE_NAV_A,
                "productTopHoldingList": top,
                "productAssetHoldingList": [],
                "productIndustriesHoldingList": [],
            },
        }
    )
    with pytest.raises(InvalidData, match="productTopHoldingList is not an array"):
        _src(payload).holdings(FAKE_ID_A)


def test_holdings_absent_top_holding_raises_empty():
    payload = json.dumps(
        {
            "status": 200,
            "code": 200,
            "message": "success",
            "data": {
                "id": FAKE_ID_A,
                "code": "TESTCO",
                "shortName": "TESTCO",
                "nav": FAKE_NAV_A,
                "productAssetHoldingList": [],
                "productIndustriesHoldingList": [],
            },
        }
    )
    with pytest.raises(EmptyData):
        _src(payload).holdings(FAKE_ID_A)


# ---------------------------------------------------------------------------
# Issue #110: YYYY-MM-DD paths must reject non-zero-padded month/day
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_date", ["2024-1-1", "2024-01-1", "2024-1-01"])
def test_nav_history_rejects_non_zero_padded_caller_from_date(bad_date):
    with pytest.raises(InvalidData, match="malformed"):
        _src(_nav_history_payload()).nav_history(FAKE_ID_A, from_date=bad_date)


@pytest.mark.parametrize("bad_date", ["2024-1-1", "2024-01-1", "2024-1-01"])
def test_nav_history_rejects_non_zero_padded_caller_to_date(bad_date):
    with pytest.raises(InvalidData, match="malformed"):
        _src(_nav_history_payload()).nav_history(FAKE_ID_A, to_date=bad_date)


@pytest.mark.parametrize("bad_date", ["2024-1-1", "2024-01-1", "2024-1-01"])
def test_parse_nav_point_rejects_non_zero_padded_nav_date(bad_date):
    row = {"navDate": bad_date, "nav": 100.0, "productId": FAKE_ID_A}
    with pytest.raises(InvalidData, match="malformed navDate"):
        FmarketFundSource._parse_nav_point(row)
