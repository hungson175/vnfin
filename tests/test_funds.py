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
from datetime import date, datetime, timedelta, timezone

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable, StaleData
from vnfin.funds import (
    AssetAllocation,
    AssetClassWeight,
    Fund,
    FundHolding,
    FundList,
    FmarketFundSource,
    NavHistory,
    NavPoint,
    SectorWeight,
)

# ---------------------------------------------------------------------------
# synthetic payloads (shapes mirror api.fmarket.vn, no real rows)
# ---------------------------------------------------------------------------


FAKE_ID_A = 9001  # obviously-fake product ids (not real Fmarket ids)
FAKE_ID_B = 9002
FAKE_NAV_A = 11111.11  # fabricated NAV/unit values
FAKE_NAV_B = 22222.22
# #155: a FABRICATED epoch-MS inception stamp at VN-local midnight.
# 2026-03-14 17:00:00 UTC == VN 2026-03-15 00:00 +07 -> VN calendar 2026-03-15.
_FIRSTISSUEAT_VN_MIDNIGHT = 1773507600000


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
                # #155: detail-doc metadata. firstIssueAt is an epoch-MS inception
                # stamp (FABRICATED); description is a synthetic blurb.
                "firstIssueAt": _FIRSTISSUEAT_VN_MIDNIGHT,
                "description": "FAKE synthetic fund description blurb",
                "managementFee": 1.5,
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


# ---------------------------------------------------------------------------
# #181: Fund.nav_as_of (per-fund NAV freshness date from extra.lastNAVDate)
# ---------------------------------------------------------------------------
#
# extra.lastNAVDate is an epoch-MILLISECOND value at VN-local midnight. We parse
# it into the provider's own NAV calendar date (VN tz), never fabricate one, and
# IGNORE the two distractors (top-level updateAt + productNavChange.updateAt).
#
# Epoch values below are FABRICATED (computed, not real provider rows):
#   17:00:00 UTC 2026-03-14 -> VN 2026-03-15 (00:00 +07) -> NEXT VN day
#   16:59:59 UTC 2026-03-14 -> VN 2026-03-14 (23:59:59 +07) -> previous VN day
_LASTNAVDATE_VN_MIDNIGHT = 1773507600000  # 2026-03-14 17:00:00 UTC == VN 2026-03-15 00:00 +07
_LASTNAVDATE_PREV_VN_DAY = 1773507599000  # 2026-03-14 16:59:59 UTC == VN 2026-03-14 23:59:59 +07


def _fund_row_with_extra(extra="__omit__"):
    """One minimal valid fund row; ``extra`` injected verbatim (omit the key when
    ``"__omit__"``) so a test can exercise present/absent/garbage lastNAVDate."""
    row = {
        "id": FAKE_ID_A,
        "code": "TESTCO",
        "shortName": "TESTCO",
        "name": "FAKE EQUITY FUND ALPHA",
        "nav": FAKE_NAV_A,
        "dataFundAssetType": {"id": 1, "name": "Fake equity", "code": "STOCK"},
        "owner": {"id": 1, "name": "FAKE FUND MANAGER ALPHA", "shortName": "FFMA"},
        # Distractors that must be IGNORED: a top-level updateAt (record edit time)
        # and a productNavChange.updateAt (nav-stats compute time). Neither is the
        # NAV date; if either were used the asserted nav_as_of would be wrong.
        "updateAt": 1700000000000,  # 2023-11-14 UTC -> would give a 2023 VN date
        "productNavChange": {"updateAt": 1781802000000},  # ~today-ish distractor
    }
    if extra != "__omit__":
        row["extra"] = extra
    return row


def _src_one_fund(extra="__omit__"):
    return _src(_fund_list_payload(rows=[_fund_row_with_extra(extra)]))


def test_list_funds_nav_as_of_happy_path():
    # extra.lastNAVDate at VN-local midnight -> fund.nav_as_of is that VN calendar
    # date, and it co-exists with the existing parsed nav.
    fund = _src_one_fund({"lastNAVDate": _LASTNAVDATE_VN_MIDNIGHT}).list_funds()[0]
    assert fund.nav_as_of == date(2026, 3, 15)
    assert fund.nav == pytest.approx(FAKE_NAV_A)  # pairs with the parsed nav


def test_list_funds_nav_as_of_vn_tz_boundary_next_day():
    # 17:00 UTC maps to the NEXT VN calendar day (00:00 +07) -> proves VN tz, not
    # naive UTC (a naive-UTC parse would yield 2026-03-14).
    fund = _src_one_fund({"lastNAVDate": _LASTNAVDATE_VN_MIDNIGHT}).list_funds()[0]
    assert fund.nav_as_of == date(2026, 3, 15)


def test_list_funds_nav_as_of_vn_tz_boundary_prev_day():
    # 16:59:59 UTC (one second before the +07 day rollover) -> previous VN day.
    fund = _src_one_fund({"lastNAVDate": _LASTNAVDATE_PREV_VN_DAY}).list_funds()[0]
    assert fund.nav_as_of == date(2026, 3, 14)


def test_list_funds_nav_as_of_absent_extra_is_none():
    # No `extra` key at all -> None, never a raise, never now().
    fund = _src_one_fund().list_funds()[0]
    assert fund.nav_as_of is None


def test_list_funds_nav_as_of_absent_lastnavdate_is_none():
    # `extra` present but lastNAVDate key missing -> None.
    fund = _src_one_fund({"lastNAV": FAKE_NAV_A}).list_funds()[0]
    assert fund.nav_as_of is None


@pytest.mark.parametrize(
    "bad",
    [None, 0, -1, -1781802000000, "1781802000000", "garbage", float("nan"), True, False, 1781802000000.5],
    ids=["null", "zero", "neg", "neg_epoch", "str_num", "str", "nan", "true", "false", "frac_float"],
)
def test_list_funds_nav_as_of_garbage_is_none(bad):
    # null / non-positive / garbage (string, NaN, bool, fractional float) -> None,
    # no raise (a missing nav date must never blow up the whole fund list).
    fund = _src_one_fund({"lastNAVDate": bad}).list_funds()[0]
    assert fund.nav_as_of is None


def test_fund_nav_as_of_back_compat_defaults_none():
    # Frozen-dataclass additive: an existing-style Fund(...) built without
    # nav_as_of keeps working and defaults to None.
    f = Fund(code="TESTCO", name="X", id=FAKE_ID_A, nav=FAKE_NAV_A, manager="M", asset_type="STOCK")
    assert f.nav_as_of is None


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


def test_nav_history_uses_broad_request_body():
    # #144: the provider mishandles a narrow window, so the request body always uses
    # the WIDE/default window (fromDate=_DEFAULT_FROM, toDate=today); the caller's
    # bounds are applied client-side, not forwarded to the server.
    import re as _re
    from vnfin.funds.fmarket import _DEFAULT_FROM
    get = _capture_get(_nav_history_payload())
    FmarketFundSource(http_get=get).nav_history(
        FAKE_ID_A, from_date=date(2024, 1, 1), to_date=date(2024, 6, 30)
    )
    body = get.calls[0]["json_body"]
    assert body["fromDate"] == _DEFAULT_FROM           # wide lower bound, not the caller's
    assert _re.fullmatch(r"\d{4}-\d{2}-\d{2}", body["toDate"])  # today (wide upper), not 2024-06-30
    assert body["toDate"] != "2024-06-30"
    assert body["isAllData"] == 1


def test_nav_history_date_window_accepts_string_dates():
    # YYYY-MM-DD strings are accepted (validated) and applied client-side; the request
    # body stays broad (#144).
    from vnfin.funds.fmarket import _DEFAULT_FROM
    get = _capture_get(_nav_history_payload())
    FmarketFundSource(http_get=get).nav_history(
        FAKE_ID_A, from_date="2024-01-01", to_date="2024-06-30"
    )
    body = get.calls[0]["json_body"]
    assert body["fromDate"] == _DEFAULT_FROM


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


def test_nav_history_single_conflicting_nav_date_quarantined_not_fatal():
    # Issue #194 (INVERTS the old #66/#158 raise): a SINGLE conflicting navDate no
    # longer aborts the whole series. The date is QUARANTINED (dropped — never picked,
    # never averaged), the rest is served, and the drop is disclosed via the never-silent
    # `quarantined_conflicting_navdates` token. (Was: raise InvalidData "conflicting
    # navDate".) Here poisoned=1, considered=2 -> 1 > max(3, 0.2) is False -> serves.
    rows = [
        {"navDate": "2024-01-02", "nav": 10100.0, "productId": FAKE_ID_A},
        {"navDate": "2024-01-03", "nav": 10200.0, "productId": FAKE_ID_A},
        {"navDate": "2024-01-02", "nav": 10300.0, "productId": FAKE_ID_A},
    ]
    hist = _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)
    assert isinstance(hist, NavHistory)
    # the conflicting date is ABSENT; the clean date is served
    assert [p.date for p in hist.points] == [date(2024, 1, 3)]
    # never-silent token naming the dropped date
    matches = [w for w in hist.warnings if w.startswith("quarantined_conflicting_navdates:")]
    assert len(matches) == 1
    assert "2024-01-02" in matches[0]


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
# Issue #173: bond holdings (productTopHoldingBondList) + instrument_type
# ---------------------------------------------------------------------------


def test_holdings_bond_only_fund_parses_bond_list():
    # A pure BOND fund: equity list empty, bond list populated. Today this returns
    # bare EmptyData (category-wide blind spot); option A must parse the bond list.
    bond = [
        {"stockCode": "ZZZBOND1", "netAssetPercent": 11.59, "industry": "Fake bond industry", "type": "BOND", "price": None},
        {"stockCode": "ZZZBOND2", "netAssetPercent": 12.17, "industry": "Fake bond industry", "type": "BOND", "price": None},
    ]
    holds = _src(
        _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
    ).holdings(FAKE_ID_A)
    assert len(holds) == 2
    assert {h.stock_code for h in holds} == {"ZZZBOND1", "ZZZBOND2"}
    assert all(h.instrument_type == "BOND" for h in holds)
    assert all(h.price_raw is None and h.price_unit is None for h in holds)
    by_code = {h.stock_code: h for h in holds}
    assert by_code["ZZZBOND1"].weight_pct == pytest.approx(11.59)
    assert by_code["ZZZBOND2"].weight_pct == pytest.approx(12.17)


def test_holdings_balanced_fund_combines_equity_and_bond():
    equity = [{"stockCode": "FAKE1", "netAssetPercent": 4.0, "industry": "X", "type": "STOCK", "price": 11.1}]
    bond = [{"stockCode": "ZZZBOND1", "netAssetPercent": 6.0, "industry": "Y", "type": "BOND", "price": None}]
    holds = _src(
        _holdings_payload_with(productTopHoldingList=equity, productTopHoldingBondList=bond)
    ).holdings(FAKE_ID_A)
    assert len(holds) == 2
    by_code = {h.stock_code: h for h in holds}
    assert by_code["FAKE1"].instrument_type == "STOCK"
    assert by_code["FAKE1"].price_raw == pytest.approx(11.1)
    assert by_code["FAKE1"].price_unit == "raw"
    assert by_code["ZZZBOND1"].instrument_type == "BOND"
    assert by_code["ZZZBOND1"].price_raw is None
    # Equity rows come first (stable ordering for existing equity-only tests).
    assert holds[0].stock_code == "FAKE1"


def test_holdings_equity_fund_unchanged_with_instrument_type():
    # The legacy equity-only path is preserved AND now carries instrument_type.
    holds = _src(_holdings_payload()).holdings(FAKE_ID_A)
    assert len(holds) == 2
    assert holds[0].stock_code == "FAKE1"
    assert holds[0].weight_pct == pytest.approx(5.0)
    assert holds[0].industry == "Fake industry one"
    assert holds[0].instrument_type == "STOCK"


def test_holdings_bond_row_without_type_defaults_to_bond():
    # A bond row that omits `type` still gets instrument_type='BOND' via the
    # per-list default (holdings() passes default_type='BOND' for the bond list).
    bond = [{"stockCode": "ZZZBOND1", "netAssetPercent": 5.0, "industry": "Y"}]
    holds = _src(
        _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
    ).holdings(FAKE_ID_A)
    assert holds[0].instrument_type == "BOND"


def test_holdings_equity_row_without_type_defaults_to_stock():
    top = [{"stockCode": "FAKE1", "netAssetPercent": 5.0, "industry": "X"}]
    holds = _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)
    assert holds[0].instrument_type == "STOCK"


def test_holdings_present_unknown_type_maps_to_other():
    # #173 residual: a present-but-unknown but *stringlike* instrument type maps
    # to the honest "OTHER" tag — it must NOT fail-close the whole fund (a
    # tuple-returning accessor has no per-row warning channel, and an unknown
    # provider type is not a data-quality error, just a new value).
    top = [{"stockCode": "FAKE1", "netAssetPercent": 5.0, "type": "WARRANT"}]
    holds = _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)
    assert holds[0].instrument_type == "OTHER"


def test_holdings_unlisted_bond_type_parsed():
    # #173 residual (ASBF id 51, VFF id 21, DCBF id 27): real Fmarket bond funds
    # report type="UNLISTED_BOND" on their unlisted-bond rows. The old
    # {STOCK,BOND} whitelist hard-failed (InvalidData) ~8 such funds; the granular
    # tag must now be accepted and carried (listed vs unlisted is a credit-risk
    # distinction worth keeping).
    bond = [{"stockCode": "ZZZBOND1", "netAssetPercent": 11.59, "type": "UNLISTED_BOND", "price": None}]
    holds = _src(
        _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
    ).holdings(FAKE_ID_A)
    assert len(holds) == 1
    assert holds[0].stock_code == "ZZZBOND1"
    assert holds[0].instrument_type == "UNLISTED_BOND"


def test_holdings_descriptive_bond_stock_code_accepted_verbatim():
    # #173 residual (ASBF id 51): an unlisted-bond row whose stockCode is a
    # descriptive phrase ('Trái phiếu chưa niêm yết' = "unlisted bond") must NOT
    # fail the whole fund. For bond/unlisted-bond/other rows stockCode is relaxed:
    # required present + non-empty, stripped, but NOT forced to the canonical
    # [A-Z][A-Z0-9]* grammar — stored verbatim (no upper-case, no regex).
    bond = [
        {"stockCode": "  Trái phiếu chưa niêm yết  ", "netAssetPercent": 8.0, "type": "UNLISTED_BOND"},
    ]
    holds = _src(
        _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
    ).holdings(FAKE_ID_A)
    assert len(holds) == 1
    assert holds[0].stock_code == "Trái phiếu chưa niêm yết"
    assert holds[0].instrument_type == "UNLISTED_BOND"


def test_holdings_descriptive_code_on_other_type_row_accepted():
    # A present-but-unknown type ⇒ OTHER, which (like bond rows) takes the relaxed
    # stockCode path so a non-canonical identifier on an OTHER row is also accepted.
    bond = [{"stockCode": "some descriptive label", "netAssetPercent": 3.0, "type": "WARRANT"}]
    holds = _src(
        _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
    ).holdings(FAKE_ID_A)
    assert holds[0].instrument_type == "OTHER"
    assert holds[0].stock_code == "some descriptive label"


def test_holdings_equity_row_descriptive_code_still_raises_invalid():
    # Regression guard: equities stay STRICT — a non-canonical/descriptive
    # stockCode on a STOCK row still fails closed (canonical validation preserved).
    top = [{"stockCode": "not a ticker", "netAssetPercent": 5.0, "type": "STOCK"}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_equity_default_type_descriptive_code_still_raises_invalid():
    # Same guard via the per-list default (no `type` on an equity-list row ⇒ STOCK).
    top = [{"stockCode": "not a ticker", "netAssetPercent": 5.0}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


@pytest.mark.parametrize("bad_type", [123, 4.5, True, "", "   "])
def test_holdings_present_malformed_type_still_raises_invalid(bad_type):
    # A present-MALFORMED type (non-string, or empty/blank string) is a genuine
    # data-quality error and STILL fails closed — distinct from an unknown-but-
    # stringlike type (which → OTHER).
    top = [{"stockCode": "FAKE1", "netAssetPercent": 5.0, "type": bad_type}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_holdings_bond_descriptive_code_dedup_still_applies():
    # Dedup spans the resolved stock_code string even for relaxed/phrase codes.
    bond = [
        {"stockCode": "Trái phiếu chưa niêm yết", "netAssetPercent": 4.0, "type": "UNLISTED_BOND"},
        {"stockCode": "Trái phiếu chưa niêm yết", "netAssetPercent": 5.0, "type": "UNLISTED_BOND"},
    ]
    with pytest.raises(InvalidData, match="duplicate holding stock code"):
        _src(
            _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
        ).holdings(FAKE_ID_A)


@pytest.mark.parametrize(
    "bad_code",
    [None, "", "   "],
    ids=["null", "empty", "blank"],
)
def test_holdings_bond_present_null_or_blank_code_still_raises(bad_code):
    # Relaxing the GRAMMAR for bond rows does NOT relax presence: a present-null /
    # empty / blank stockCode on a bond row still fails closed.
    bond = [{"stockCode": bad_code, "netAssetPercent": 5.0, "type": "BOND"}]
    with pytest.raises(InvalidData):
        _src(
            _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
        ).holdings(FAKE_ID_A)


def test_holdings_bond_missing_code_still_raises():
    bond = [{"netAssetPercent": 5.0, "type": "BOND"}]
    with pytest.raises(InvalidData):
        _src(
            _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
        ).holdings(FAKE_ID_A)


def test_holdings_end_to_end_unlisted_bond_fund_populated_not_raising():
    # End-to-end regression: a whole fund whose bond list carries an UNLISTED_BOND
    # row with a descriptive stockCode now returns a POPULATED tuple instead of
    # raising InvalidData (the #173 residual that hard-failed ~8 defensive-credit
    # funds — ASBF/VFF/DCBF). Drives holdings() through the detail/HTTP layer with
    # a synthetic payload.
    bond = [
        {"stockCode": "Trái phiếu chưa niêm yết", "netAssetPercent": 30.0, "type": "UNLISTED_BOND"},
        {"stockCode": "ZZZBOND2", "netAssetPercent": 20.0, "type": "BOND"},
    ]
    holds = _src(
        _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
    ).holdings(FAKE_ID_A)
    assert len(holds) == 2
    by_code = {h.stock_code: h for h in holds}
    assert by_code["Trái phiếu chưa niêm yết"].instrument_type == "UNLISTED_BOND"
    assert by_code["ZZZBOND2"].instrument_type == "BOND"


def test_holdings_per_holding_as_of_from_update_at():
    # The accepted as-of lever: each FundHolding carries the provider's per-row
    # updateAt (epoch-ms) so a holdings tuple is no longer freshness-blind.
    top = [
        {"stockCode": "FAKE1", "netAssetPercent": 5.0, "type": "STOCK", "updateAt": 1700000000000},
        {"stockCode": "FAKE2", "netAssetPercent": 4.0, "type": "STOCK"},  # no updateAt
    ]
    holds = _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)
    by_code = {h.stock_code: h for h in holds}
    assert by_code["FAKE1"].as_of_utc == datetime.fromtimestamp(
        1700000000000 / 1000.0, tz=timezone.utc
    )
    assert by_code["FAKE2"].as_of_utc is None


def test_holdings_malformed_update_at_leaves_as_of_none():
    # A malformed/absent updateAt must NOT fabricate now() — it stays None.
    top = [{"stockCode": "FAKE1", "netAssetPercent": 5.0, "type": "STOCK", "updateAt": "garbage"}]
    holds = _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)
    assert holds[0].as_of_utc is None


def test_holdings_both_lists_empty_raises_empty():
    with pytest.raises(EmptyData):
        _src(
            _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=[])
        ).holdings(FAKE_ID_A)


def test_holdings_both_lists_absent_raises_empty():
    base = json.loads(_holdings_payload())
    base["data"].pop("productTopHoldingList", None)
    # bond key never present in the default payload either
    with pytest.raises(EmptyData):
        _src(json.dumps(base)).holdings(FAKE_ID_A)


@pytest.mark.parametrize(
    "bad_row",
    [
        {"stockCode": "ZZZBOND1", "netAssetPercent": "garbage", "type": "BOND"},
        {"netAssetPercent": 5.0, "type": "BOND"},  # missing stockCode
        {"stockCode": "   ", "netAssetPercent": 5.0, "type": "BOND"},  # blank
        {"stockCode": "ZZZBOND1", "netAssetPercent": 5.0, "type": "BOND", "price": -1.0},  # neg price
        {"stockCode": "ZZZBOND1", "netAssetPercent": 150.0, "type": "BOND"},  # weight oob
        {"stockCode": "ZZZBOND1", "netAssetPercent": 5.0, "type": "BOND", "industry": 123},  # bad industry
    ],
    ids=["weight", "missing_code", "blank_code", "neg_price", "weight_oob", "bad_industry"],
)
def test_holdings_malformed_bond_row_raises_invalid(bad_row):
    # Bond rows get the SAME scalar/identifier validation as equity rows.
    with pytest.raises(InvalidData):
        _src(
            _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=[bad_row])
        ).holdings(FAKE_ID_A)


@pytest.mark.parametrize("bond", [{}, "", False, 0])
def test_holdings_bond_list_not_array_raises_invalid(bond):
    with pytest.raises(InvalidData, match="productTopHoldingBondList is not an array"):
        _src(
            _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
        ).holdings(FAKE_ID_A)


def test_holdings_combined_aggregate_weight_above_100_raises_invalid():
    # #90 guard now sums equity + bond COMBINED (60 + 50 = 110), not per-list.
    equity = [{"stockCode": "FAKE1", "netAssetPercent": 60.0, "type": "STOCK"}]
    bond = [{"stockCode": "ZZZBOND1", "netAssetPercent": 50.0, "type": "BOND"}]
    with pytest.raises(InvalidData, match="aggregate holdings weight exceeds 100%"):
        _src(
            _holdings_payload_with(productTopHoldingList=equity, productTopHoldingBondList=bond)
        ).holdings(FAKE_ID_A)


def test_holdings_dedup_stock_code_across_lists_raises_invalid():
    # The per-fund dedup set spans BOTH lists: the same code in equity and bond
    # is a provider self-inconsistency that fails closed.
    equity = [{"stockCode": "FAKE1", "netAssetPercent": 5.0, "type": "STOCK"}]
    bond = [{"stockCode": "FAKE1", "netAssetPercent": 6.0, "type": "BOND"}]
    with pytest.raises(InvalidData, match="duplicate holding stock code"):
        _src(
            _holdings_payload_with(productTopHoldingList=equity, productTopHoldingBondList=bond)
        ).holdings(FAKE_ID_A)


def test_holdings_bond_only_uses_id_in_path_and_identity_preserved():
    bond = [{"stockCode": "ZZZBOND1", "netAssetPercent": 11.59, "type": "BOND"}]
    get = _capture_get(
        _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
    )
    FmarketFundSource(http_get=get).holdings(FAKE_ID_A)
    assert get.calls[0]["url"].endswith(f"/res/products/{FAKE_ID_A}")


def test_holdings_bond_only_rejects_mismatched_detail_id():
    # #21 identity guard still gates the bond-only path.
    bond = [{"stockCode": "ZZZBOND1", "netAssetPercent": 11.59, "type": "BOND"}]
    with pytest.raises(InvalidData):
        _src(
            _holdings_payload_with(id=9999, productTopHoldingList=[], productTopHoldingBondList=bond)
        ).holdings(FAKE_ID_A)


# ---------------------------------------------------------------------------
# Issue #173: asset_allocation() sibling accessor
# ---------------------------------------------------------------------------


def test_asset_allocation_returns_typed_split():
    asset = [
        {"assetType": {"code": "BOND", "name": "Fake bond"}, "assetPercent": 88.0},
        {"assetType": {"code": "CASH", "name": "Fake cash"}, "assetPercent": 12.0},
    ]
    alloc = _src(_holdings_payload_with(productAssetHoldingList=asset)).asset_allocation(FAKE_ID_A)
    assert isinstance(alloc, AssetAllocation)
    assert alloc.product_id == FAKE_ID_A
    assert alloc.source == "fmarket"
    assert alloc.currency == "VND"
    assert len(alloc) == 2
    assert all(isinstance(c, AssetClassWeight) for c in alloc)
    by_class = {c.asset_class: c.weight_pct for c in alloc}
    assert by_class["BOND"] == pytest.approx(88.0)
    assert by_class["CASH"] == pytest.approx(12.0)


def test_asset_allocation_uses_id_in_path():
    get = _capture_get(_holdings_payload())
    FmarketFundSource(http_get=get).asset_allocation(FAKE_ID_A)
    assert get.calls[0]["url"].endswith(f"/res/products/{FAKE_ID_A}")


def test_asset_allocation_as_of_from_update_at():
    asset = [
        {"assetType": {"code": "BOND", "name": "B"}, "assetPercent": 70.0, "updateAt": 1700000000000},
        {"assetType": {"code": "CASH", "name": "C"}, "assetPercent": 30.0, "updateAt": 1700000100000},
    ]
    alloc = _src(_holdings_payload_with(productAssetHoldingList=asset)).asset_allocation(FAKE_ID_A)
    assert alloc.as_of_utc == datetime.fromtimestamp(1700000100000 / 1000.0, tz=timezone.utc)


def test_asset_allocation_absent_update_at_leaves_as_of_none():
    asset = [{"assetType": {"code": "BOND", "name": "B"}, "assetPercent": 100.0}]
    alloc = _src(_holdings_payload_with(productAssetHoldingList=asset)).asset_allocation(FAKE_ID_A)
    assert alloc.as_of_utc is None


def test_asset_allocation_empty_raises_empty():
    with pytest.raises(EmptyData):
        _src(_holdings_payload_with(productAssetHoldingList=[])).asset_allocation(FAKE_ID_A)


def test_asset_allocation_absent_raises_empty():
    base = json.loads(_holdings_payload())
    base["data"].pop("productAssetHoldingList", None)
    with pytest.raises(EmptyData):
        _src(json.dumps(base)).asset_allocation(FAKE_ID_A)


@pytest.mark.parametrize("rows", [{}, "", False, 0])
def test_asset_allocation_present_non_list_raises_invalid(rows):
    with pytest.raises(InvalidData, match="productAssetHoldingList is not an array"):
        _src(_holdings_payload_with(productAssetHoldingList=rows)).asset_allocation(FAKE_ID_A)


@pytest.mark.parametrize(
    "bad_row",
    [
        {"assetType": {"code": "BOND"}, "assetPercent": "garbage"},
        {"assetType": {"code": "BOND"}, "assetPercent": 150.0},
        {"assetType": "BOND", "assetPercent": 50.0},  # assetType not a dict
        {"assetType": {"code": "   "}, "assetPercent": 50.0},  # blank code
        {"assetType": {}, "assetPercent": 50.0},  # missing code
    ],
    ids=["weight", "weight_oob", "asset_type_str", "blank_code", "missing_code"],
)
def test_asset_allocation_malformed_row_raises_invalid(bad_row):
    with pytest.raises(InvalidData):
        _src(_holdings_payload_with(productAssetHoldingList=[bad_row])).asset_allocation(FAKE_ID_A)


def test_asset_allocation_non_object_row_raises_invalid():
    with pytest.raises(InvalidData):
        _src(_holdings_payload_with(productAssetHoldingList=["not-a-dict"])).asset_allocation(FAKE_ID_A)


def test_asset_allocation_unknown_class_raises_invalid():
    # A present-but-unrecognized asset class fails closed (not STOCK/BOND/CASH).
    asset = [{"assetType": {"code": "DERIVATIVE"}, "assetPercent": 50.0}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload_with(productAssetHoldingList=asset)).asset_allocation(FAKE_ID_A)


def test_asset_allocation_partial_disclosure_under_100_ok():
    # Disclosed weights need NOT sum to 100% (partial disclosure is allowed).
    asset = [{"assetType": {"code": "BOND"}, "assetPercent": 60.0}]
    alloc = _src(_holdings_payload_with(productAssetHoldingList=asset)).asset_allocation(FAKE_ID_A)
    assert len(alloc) == 1
    assert alloc[0].weight_pct == pytest.approx(60.0)


def test_asset_allocation_dedup_class_raises_invalid():
    asset = [
        {"assetType": {"code": "BOND"}, "assetPercent": 50.0},
        {"assetType": {"code": "BOND"}, "assetPercent": 30.0},
    ]
    with pytest.raises(InvalidData):
        _src(_holdings_payload_with(productAssetHoldingList=asset)).asset_allocation(FAKE_ID_A)


def test_asset_allocation_rejects_mismatched_detail_id():
    # #21 identity guard on the new accessor (same endpoint as holdings).
    with pytest.raises(InvalidData):
        _src(_holdings_payload_with(id=9999)).asset_allocation(FAKE_ID_A)


def test_asset_allocation_invalid_product_id_rejected():
    with pytest.raises(InvalidData):
        _src(_holdings_payload()).asset_allocation(0)


def test_asset_allocation_models_are_frozen():
    c = AssetClassWeight(asset_class="BOND", weight_pct=50.0)
    with pytest.raises(Exception):
        c.weight_pct = 1.0  # type: ignore[misc]


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


# Phase 4 funds migration — canonical security/fund identifier contract.
@pytest.mark.parametrize("bad_code", ["VCB F", "A.B", "A-B", "A/B", "1ABC", "AB%", "AB\nC"])
def test_fmarket_fund_list_rejects_malformed_nonblank_code(bad_code):
    # #33: a present non-blank but non-canonical fund code must fail closed.
    row = {
        "id": FAKE_ID_A, "code": bad_code, "shortName": bad_code, "name": "X",
        "nav": 100.0, "dataFundAssetType": {"code": "STOCK"}, "owner": {"name": "M"},
    }
    with pytest.raises(InvalidData):
        _src(_fund_list_payload(rows=[row])).list_funds()


def test_fmarket_fund_list_normalizes_padded_lower_code():
    # reviewer tweak: strip().upper() normalization keeps friendly public input.
    row = {
        "id": FAKE_ID_A, "code": "  testco ", "shortName": "TESTCO", "name": "X",
        "nav": 100.0, "dataFundAssetType": {"code": "STOCK"}, "owner": {"name": "M"},
    }
    funds = _src(_fund_list_payload(rows=[row])).list_funds()
    assert funds.funds[0].code == "TESTCO"


@pytest.mark.parametrize("bad_code", ["FA KE", "A.B", "A-B", "A/B", "1ABC", "AB%"])
def test_fmarket_holdings_rejects_malformed_nonblank_stockcode(bad_code):
    # #34: a present non-blank but non-canonical holding stockCode must fail closed.
    top = [{"stockCode": bad_code, "netAssetPercent": 5.0, "type": "STOCK"}]
    with pytest.raises(InvalidData):
        _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)


def test_fmarket_holdings_normalizes_padded_lower_stockcode():
    top = [{"stockCode": " fpt ", "netAssetPercent": 5.0, "type": "STOCK"}]
    holds = _src(_holdings_payload(top=top)).holdings(FAKE_ID_A)
    assert holds[0].stock_code == "FPT"


def test_fmarket_fund_present_null_code_fails_closed_no_shortname_fallback():
    # #33 B1: a PRESENT code:null must fail closed, NOT fall back to shortName.
    row = {
        "id": FAKE_ID_A, "code": None, "shortName": "TESTCO", "name": "X",
        "nav": 100.0, "dataFundAssetType": {"code": "STOCK"}, "owner": {"name": "M"},
    }
    with pytest.raises(InvalidData):
        _src(_fund_list_payload(rows=[row])).list_funds()


def test_fmarket_fund_absent_code_falls_back_to_shortname():
    # #33 B1: a truly ABSENT code key MAY fall back to a canonical shortName.
    row = {
        "id": FAKE_ID_A, "shortName": "TESTCO", "name": "X",
        "nav": 100.0, "dataFundAssetType": {"code": "STOCK"}, "owner": {"name": "M"},
    }
    funds = _src(_fund_list_payload(rows=[row])).list_funds()
    assert funds.funds[0].code == "TESTCO"


# Issue #144 — broad-window fetch + client-side filter; out-of-window rows must not
# fail the request, in-window duplicates still do.
def _nav_row(navdate, nav=100.0, pid=None):
    r = {"id": 1, "createdAt": 1700000000000, "nav": nav, "navDate": navdate}
    if pid is not None:
        r["productId"] = pid
    return r


def _window_aware_get(full_rows, narrow_rows):
    """Mimic the upstream server: a NARROW fromDate returns a non-overlapping
    inception slice; only the WIDE/default fromDate returns the full history."""
    from vnfin.funds.fmarket import _DEFAULT_FROM

    def _g(url, params=None, headers=None, json_body=None):
        frm = (json_body or {}).get("fromDate")
        rows = full_rows if frm == _DEFAULT_FROM else narrow_rows
        return json.dumps({"status": 200, "code": 200, "message": "success", "data": rows})

    return _g


def test_nav_history_window_returns_in_range_rows_despite_server_narrow_quirk():
    # #144 core repro: full history (broad body) has 2024 rows; a narrow body would
    # return only pre-2024 rows. The fix sends the broad body, so the bounded 2024
    # call returns the in-window rows instead of wrong EmptyData.
    full = [_nav_row("2023-12-29"), _nav_row("2024-03-01"), _nav_row("2024-06-02"), _nav_row("2025-01-05")]
    narrow = [_nav_row("2018-01-12"), _nav_row("2018-01-18")]  # non-overlapping
    src = FmarketFundSource(http_get=_window_aware_get(full, narrow))
    hist = src.nav_history(FAKE_ID_A, date(2024, 1, 1), date(2024, 12, 31))
    got = [p.date for p in hist.points]
    assert got == [date(2024, 3, 1), date(2024, 6, 2)]


def test_nav_history_out_of_window_duplicate_not_fatal():
    # a duplicate navDate OUTSIDE the caller window is skipped before the dup guard.
    full = [_nav_row("2023-05-01"), _nav_row("2023-05-01"), _nav_row("2024-04-04")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    hist = src.nav_history(FAKE_ID_A, date(2024, 1, 1), date(2024, 12, 31))
    assert [p.date for p in hist.points] == [date(2024, 4, 4)]


def test_nav_history_in_window_all_conflict_sub_threshold_falls_to_empty():
    # #194 (INVERTS the old #158 fatal-conflict raise; this is matrix case 8): the ONLY
    # in-window date conflicts (2024-04-04: 100 vs 101). poisoned=1, considered=1,
    # points=[] -> sub-threshold (1 <= floor 3) so the quarantine verdict does NOT fire;
    # the empty result falls through to the existing #172 block. max_navdate (2024-04-04)
    # is >= the window start, so it is plain EmptyData (NOT StaleData, NOT InvalidData).
    full = [_nav_row("2024-04-04", nav=100.0), _nav_row("2024-04-04", nav=101.0)]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    with pytest.raises(EmptyData) as exc:
        src.nav_history(FAKE_ID_A, date(2024, 1, 1), date(2024, 12, 31))
    # not the systematically-broken raise, and not a stale-data subclass
    assert not isinstance(exc.value, StaleData)


def test_nav_history_in_window_identical_duplicate_deduped_with_warning():
    # #158: a duplicate navDate with the SAME NAV is deduped (kept once) + warned, not fatal.
    full = [
        _nav_row("2024-04-04", nav=100.0),
        _nav_row("2024-04-04", nav=100.0),
        _nav_row("2024-04-05", nav=101.0),
    ]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    hist = src.nav_history(FAKE_ID_A, date(2024, 1, 1), date(2024, 12, 31))
    assert [p.date for p in hist.points] == [date(2024, 4, 4), date(2024, 4, 5)]
    # #180: warning carries a namespaced token prefix (not bare prose).
    assert any(w.startswith("deduped_duplicate_nav_rows:") for w in hist.warnings)


def test_nav_history_no_duplicates_has_no_dedupe_warning():
    # to_date == the last point's date so the series reaches the window end (gap 0,
    # no #172-RESIDUAL end-gap warning); proves no dedupe warning when no duplicates.
    full = [_nav_row("2024-04-04", nav=100.0), _nav_row("2024-04-05", nav=101.0)]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    hist = src.nav_history(FAKE_ID_A, date(2024, 1, 1), date(2024, 4, 5))
    assert hist.warnings == ()


@pytest.mark.parametrize("bad", ["not-a-date", "2024-13-01", "20240101", 123, []])
def test_nav_history_caller_date_validation_unchanged(bad):
    src = FmarketFundSource(http_get=_window_aware_get([_nav_row("2024-04-04")], []))
    with pytest.raises(InvalidData):
        src.nav_history(FAKE_ID_A, from_date=bad)


def test_nav_history_inverted_window_rejected():
    src = FmarketFundSource(http_get=_window_aware_get([_nav_row("2024-04-04")], []))
    with pytest.raises(InvalidData):
        src.nav_history(FAKE_ID_A, date(2024, 12, 31), date(2024, 1, 1))


# ---------------------------------------------------------------------------
# Issue #172 — NAV-history staleness. When the provider's history ends BEFORE the
# requested window start (probe-confirmed: Fmarket's get-nav-history is systemically
# stale), a bounded recent window must raise StaleData (an EmptyData subclass naming
# the data gap), not a silent EmptyData indistinguishable from "no data".
# ---------------------------------------------------------------------------


def test_nav_history_stale_window_raises_staledata():
    full = [_nav_row("2025-11-28"), _nav_row("2025-12-05")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    with pytest.raises(StaleData) as exc:
        src.nav_history(FAKE_ID_A, date(2026, 1, 1), date(2026, 6, 20))
    msg = str(exc.value)
    assert "ends at 2025-12-05" in msg
    assert "before requested 2026-01-01..2026-06-20" in msg


def test_nav_history_staledata_is_emptydata_subclass():
    # Backward compatible: existing `except EmptyData` callers still catch the stale case.
    assert issubclass(StaleData, EmptyData)
    full = [_nav_row("2025-12-05")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    with pytest.raises(EmptyData):
        src.nav_history(FAKE_ID_A, date(2026, 1, 1), date(2026, 6, 20))


def test_nav_history_fresh_window_returns_rows_not_stale():
    # When the provider DOES return in-window 2026 rows, the bounded call returns them.
    full = [_nav_row("2025-12-30"), _nav_row("2026-02-02"), _nav_row("2026-03-03")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    hist = src.nav_history(FAKE_ID_A, date(2026, 1, 1), date(2026, 6, 20))
    assert [p.date for p in hist.points] == [date(2026, 2, 2), date(2026, 3, 3)]


def test_nav_history_pre_inception_window_is_plain_empty_not_stale():
    # Window entirely BEFORE the data (latest navDate >= window start) -> EmptyData, NOT stale.
    full = [_nav_row("2014-03-25"), _nav_row("2014-04-01")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    with pytest.raises(EmptyData) as exc:
        src.nav_history(FAKE_ID_A, date(2010, 1, 1), date(2011, 1, 1))
    assert not isinstance(exc.value, StaleData)


def test_nav_history_sparse_straddle_is_plain_empty_not_stale():
    # Window falls in a gap between two points but latest navDate >= window start -> EmptyData.
    full = [_nav_row("2025-12-01"), _nav_row("2025-12-08")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    with pytest.raises(EmptyData) as exc:
        src.nav_history(FAKE_ID_A, date(2025, 12, 2), date(2025, 12, 5))
    assert not isinstance(exc.value, StaleData)


def test_nav_history_stale_ignores_out_of_window_guard_rows():
    # #144/#21/#158 preserved: an out-of-window odd-productId row and an out-of-window
    # conflicting duplicate must NOT fail the request; the max-navDate scan runs no
    # guards on out-of-window rows, so a stale recent window still yields StaleData.
    full = [
        _nav_row("2025-12-04", pid=9999),       # wrong productId, but out of window
        _nav_row("2025-12-05", nav=100.0),
        _nav_row("2025-12-05", nav=200.0),      # conflicting dup, but out of window
    ]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    with pytest.raises(StaleData):
        src.nav_history(FAKE_ID_A, date(2026, 1, 1), date(2026, 6, 20))


def test_nav_history_open_ended_from_only_stale_uses_today_end():
    # from_date only (to_date defaulted to today) on stale history -> StaleData; the
    # message names a concrete end bound (today), never an empty/None end.
    full = [_nav_row("2025-12-05")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    with pytest.raises(StaleData) as exc:
        src.nav_history(FAKE_ID_A, from_date=date(2026, 1, 1))
    assert "ends at 2025-12-05" in str(exc.value)
    assert "before requested 2026-01-01.." in str(exc.value)


def test_nav_history_full_history_call_on_stale_data_returns_all():
    # No window -> no coverage check; the full stale history is returned (no exception).
    full = [_nav_row("2025-11-28"), _nav_row("2025-12-05")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    hist = src.nav_history(FAKE_ID_A)
    assert [p.date for p in hist.points] == [date(2025, 11, 28), date(2025, 12, 5)]
    # #172-RESIDUAL: the returned NavHistory now carries an end-gap warning — this
    # fixture's tail is years before any live today, so a 'nav_end_gap'-prefixed
    # warning is always present (presence-only assertion, robust to live-today).
    assert any(w.startswith("nav_end_gap:") for w in hist.warnings)


# ---------------------------------------------------------------------------
# Issue #172-RESIDUAL — success-path NAV end-gap warning. nav_history() succeeds
# (series reaches the window) but its LATEST observation is old (feed delayed /
# paused / fund dormant). A cadence-relative soft warning is appended to
# NavHistory.warnings, computed against an INJECTED `today` date (never now()).
# Design: docs/design/nav-success-path-staleness.md.
#
# Direct unit tests on the pure helper _nav_end_gap_warning(points, to_date, today)
# pass fixed points/to_date/today -> fully deterministic, no HTTP, no live date.
# ---------------------------------------------------------------------------


def _np(d, nav=100.0):
    """A NavPoint at an ISO date string (ascending order is the caller's job)."""
    return NavPoint(date=date.fromisoformat(d), nav=nav)


def _daily(start, n):
    """n consecutive daily NavPoints starting at ISO `start`, ascending."""
    from datetime import timedelta
    s = date.fromisoformat(start)
    return tuple(NavPoint(date=s + timedelta(days=i), nav=100.0 + i) for i in range(n))


def _weekly(start, n):
    """n weekly (7d-spaced) NavPoints starting at ISO `start`, ascending."""
    from datetime import timedelta
    s = date.fromisoformat(start)
    return tuple(NavPoint(date=s + timedelta(days=7 * i), nav=100.0 + i) for i in range(n))


def test_nav_end_gap_helper_is_pure_and_importable():
    # The helper must be a module-level pure function taking an injected `today`.
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _daily("2026-01-01", 5)
    out = _nav_end_gap_warning(pts, None, date(2026, 1, 5))
    assert isinstance(out, tuple)


def test_nav_end_gap_daily_stale_tail_warns_naming_gap_cadence_threshold():
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _daily("2026-01-01", 10)  # latest 2026-01-10, daily cadence
    today = date(2026, 1, 25)        # 15d after the latest point, open/now window
    out = _nav_end_gap_warning(pts, None, today)
    assert len(out) == 1
    msg = out[0]
    assert msg.startswith("nav_end_gap:")
    assert "latest NAV 2026-01-10" in msg
    assert "15d before 2026-01-25" in msg          # gap named
    assert "typical cadence ~1d" in msg            # cadence named
    assert "threshold 7d" in msg                   # threshold named
    assert "may be delayed, paused, or the fund dormant" in msg


def test_nav_end_gap_daily_fresh_weekend_no_warn():
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _daily("2026-01-01", 10)  # latest 2026-01-10
    today = date(2026, 1, 12)        # 2d (weekend) -> under the 7d floor
    assert _nav_end_gap_warning(pts, None, today) == ()


def test_nav_end_gap_weekly_fund_fresh_8d_no_warn():
    # KEY regression: a weekly fund whose latest NAV is 8d old is FRESH. A stock-
    # calendar approach (>7d before expected trading day) would wrongly flag it.
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _weekly("2026-01-05", 10)  # cadence ~7, latest 2026-03-09
    from datetime import timedelta
    today = pts[-1].date + timedelta(days=8)
    assert _nav_end_gap_warning(pts, None, today) == ()


def test_nav_end_gap_weekly_fund_stale_20d_warns():
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _weekly("2026-01-05", 10)  # cadence ~7 -> threshold max(14,7)=14
    from datetime import timedelta
    today = pts[-1].date + timedelta(days=20)
    out = _nav_end_gap_warning(pts, None, today)
    assert len(out) == 1
    assert out[0].startswith("nav_end_gap:")
    assert "typical cadence ~7d" in out[0]
    assert "threshold 14d" in out[0]


def test_nav_end_gap_midseries_cadence_change_fresh_weekly_tail_no_warn():
    # PROVES the trailing window governs (not whole-series median): years of daily NAV
    # then a SETTLED weekly tail (8 weekly points => trailing window all-7), latest 8d
    # old -> NO warn. gap=8 is deliberately in the 8..14 band: a whole-series-median
    # impl would have median ~1 -> threshold max(2,7)=7 -> 8 > 7 -> WRONGLY warn (so this
    # test genuinely FAILS a whole-series impl); the trailing window -> median 7 ->
    # threshold max(14,7)=14 -> 8 <= 14 -> correctly silent.
    from datetime import timedelta
    from vnfin.funds.fmarket import _nav_end_gap_warning
    daily = list(_daily("2024-01-01", 400))         # long daily history
    last_daily = daily[-1].date
    weekly_tail = [
        NavPoint(date=last_daily + timedelta(days=7 * k), nav=999.0 + k) for k in range(1, 9)
    ]
    pts = tuple(daily + weekly_tail)                 # ascending, daily->weekly switch (settled)
    today = pts[-1].date + timedelta(days=8)         # one normal weekly gap + 1d; in the 8..14 band
    assert _nav_end_gap_warning(pts, None, today) == ()


def test_nav_end_gap_cadence_transition_transient_warns_then_self_clears():
    # ACCEPTED, documented behaviour (design §3 "Bounded transition transient"): right
    # after a daily->weekly switch the trailing window is still daily-dominated
    # (median 1 -> threshold 7), so a fresh weekly NAV (~8d old) is briefly flagged, then
    # self-clears once the window is mostly weekly. We deliberately accept this soft,
    # self-clearing over-warn rather than risk EVER missing real staleness (a false
    # negative would defeat the feature). This test pins both ends of that behaviour.
    from datetime import timedelta
    from vnfin.funds.fmarket import _nav_end_gap_warning
    daily = list(_daily("2024-01-01", 400))
    last_daily = daily[-1].date
    # transient: only 2 weekly points since the switch -> trailing window still daily.
    pts_transient = tuple(daily + [
        NavPoint(date=last_daily + timedelta(days=7 * k), nav=999.0 + k) for k in range(1, 3)
    ])
    fresh = pts_transient[-1].date + timedelta(days=8)   # an on-time weekly NAV (1 gap + 1d)
    out = _nav_end_gap_warning(pts_transient, None, fresh)
    assert len(out) == 1 and out[0].startswith("nav_end_gap:")   # accepted transient over-warn
    # settled: 8 weekly points -> trailing window all-weekly -> the same fresh tail clears.
    pts_settled = tuple(daily + [
        NavPoint(date=last_daily + timedelta(days=7 * k), nav=999.0 + k) for k in range(1, 9)
    ])
    settled_fresh = pts_settled[-1].date + timedelta(days=8)
    assert _nav_end_gap_warning(pts_settled, None, settled_fresh) == ()


def test_nav_end_gap_zero_gap_no_warn():
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _daily("2026-01-01", 10)  # latest 2026-01-10
    assert _nav_end_gap_warning(pts, None, date(2026, 1, 10)) == ()  # gap_days == 0


def test_nav_end_gap_negative_gap_future_today_no_warn():
    # today before the latest point (gap_days < 0) -> fresh, no warn.
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _daily("2026-01-01", 10)  # latest 2026-01-10
    assert _nav_end_gap_warning(pts, None, date(2026, 1, 1)) == ()


def test_nav_end_gap_exactly_at_threshold_no_warn_strictly_greater():
    # threshold is strict (>): gap == threshold -> NO warn; threshold+1 -> warn.
    from datetime import timedelta
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _daily("2026-01-01", 10)  # daily -> threshold 7
    latest = pts[-1].date
    assert _nav_end_gap_warning(pts, None, latest + timedelta(days=7)) == ()
    out = _nav_end_gap_warning(pts, None, latest + timedelta(days=8))
    assert len(out) == 1 and out[0].startswith("nav_end_gap:")


def test_nav_end_gap_reference_clamps_to_today_for_future_to_date():
    # reference = min(to_date, today): a FUTURE to_date must not inflate the gap.
    from datetime import timedelta
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _daily("2026-01-01", 10)  # latest 2026-01-10
    today = pts[-1].date + timedelta(days=2)          # fresh vs today
    future_to_date = date(2030, 1, 1)                 # way beyond today
    assert _nav_end_gap_warning(pts, future_to_date, today) == ()


def test_nav_end_gap_reference_uses_to_date_when_to_date_before_today():
    # to_date == today behaves like the now-window; here to_date precedes today and
    # the series reaches to_date -> reference = to_date -> no warn (NON-GOAL).
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _daily("2026-01-01", 10)  # latest 2026-01-10
    out = _nav_end_gap_warning(pts, date(2026, 1, 10), date(2026, 6, 20))
    assert out == ()


def test_nav_end_gap_historical_window_fully_covered_no_warn():
    # NON-GOAL: past to_date, series reaches it -> gap_days <= 0 -> no warn.
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _daily("2024-01-01", 30)  # latest 2024-01-30
    out = _nav_end_gap_warning(pts, date(2024, 1, 30), date(2026, 6, 20))
    assert out == ()


def test_nav_end_gap_historical_window_early_ending_series_warns_vs_to_date():
    # Series ends long before a PAST to_date -> warns against to_date (not today).
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = _daily("2024-01-01", 30)  # latest 2024-01-30
    out = _nav_end_gap_warning(pts, date(2024, 6, 30), date(2026, 6, 20))
    assert len(out) == 1
    msg = out[0]
    assert msg.startswith("nav_end_gap:")
    assert "latest NAV 2024-01-30" in msg
    assert "before 2024-06-30" in msg               # reference is the past to_date


def test_nav_end_gap_single_point_fresh_under_14d_no_warn():
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = (_np("2026-01-01"),)
    assert _nav_end_gap_warning(pts, None, date(2026, 1, 14)) == ()   # 13d, under 14


def test_nav_end_gap_single_point_stale_over_14d_warns_no_cadence():
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = (_np("2026-01-01"),)
    out = _nav_end_gap_warning(pts, None, date(2026, 1, 20))           # 19d > 14
    assert len(out) == 1
    msg = out[0]
    assert msg.startswith("nav_end_gap:")
    assert "typical cadence unknown (single NAV point)" in msg   # cadence unknown, cleanly phrased
    assert "None" not in msg                          # never the str(None) repr ('~Noned')
    assert "threshold 14d" in msg


def test_nav_end_gap_two_point_weekend_only_gap_fresh_no_warn():
    # Two points spaced 3d (weekend), latest only 2d before reference -> fresh.
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = (_np("2026-01-02"), _np("2026-01-05"))   # 3d diff -> typical_gap 3, threshold max(6,7)=7
    assert _nav_end_gap_warning(pts, None, date(2026, 1, 7)) == ()    # 2d gap


def test_nav_end_gap_cadence_window_clips_to_last_n_diffs():
    # Only the last _NAV_END_GAP_CADENCE_WINDOW diffs feed the median: a long weekly
    # run (>8 diffs) followed by daily would still be governed by the recent diffs.
    from datetime import timedelta
    from vnfin.funds.fmarket import _nav_end_gap_warning, _NAV_END_GAP_CADENCE_WINDOW
    weekly = list(_weekly("2026-01-05", 20))        # 19 weekly diffs of 7
    last = weekly[-1].date
    daily_tail = [NavPoint(date=last + timedelta(days=k), nav=500.0 + k) for k in range(1, 10)]
    pts = tuple(weekly + daily_tail)                # last 8 diffs are all 1 (daily)
    # trailing window all-1 -> typical_gap 1 -> threshold 7; a 10d gap warns.
    today = pts[-1].date + timedelta(days=10)
    out = _nav_end_gap_warning(pts, None, today)
    assert len(out) == 1 and "typical cadence ~1d" in out[0]
    assert _NAV_END_GAP_CADENCE_WINDOW == 8


def test_nav_end_gap_median_robust_to_single_holiday_outlier():
    # A single long Tet/holiday diff among daily diffs must not inflate typical_gap
    # (median, not mean) -> daily threshold (7) still governs.
    from datetime import timedelta
    from vnfin.funds.fmarket import _nav_end_gap_warning
    pts = list(_daily("2026-01-01", 8))
    # inject one 14d holiday gap then resume daily
    gap_start = pts[-1].date
    pts += [NavPoint(date=gap_start + timedelta(days=14 + i), nav=900.0 + i) for i in range(4)]
    pts = tuple(pts)
    latest = pts[-1].date
    # median of the trailing 8 diffs is still 1 (one 14 outlier doesn't move it) -> threshold 7
    assert _nav_end_gap_warning(pts, None, latest + timedelta(days=6)) == ()
    out = _nav_end_gap_warning(pts, None, latest + timedelta(days=10))
    assert len(out) == 1 and "typical cadence ~1d" in out[0]


# --- integration through nav_history() (synthetic payload; deterministic today) ----


def _patch_today(monkeypatch, d):
    """Pin fmarket._today() so success-path end-gap tests are deterministic."""
    import vnfin.funds.fmarket as fm
    monkeypatch.setattr(fm, "_today", lambda: d)


def test_nav_history_appends_end_gap_warning_open_window(monkeypatch):
    # No window -> reference = today (injected). Stale daily tail warns.
    _patch_today(monkeypatch, date(2026, 1, 25))
    full = [_nav_row("2026-01-08"), _nav_row("2026-01-09"), _nav_row("2026-01-10")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    hist = src.nav_history(FAKE_ID_A)
    assert [p.date for p in hist.points][-1] == date(2026, 1, 10)
    assert any(w.startswith("nav_end_gap:") for w in hist.warnings)


def test_nav_history_fresh_tail_no_end_gap_warning(monkeypatch):
    _patch_today(monkeypatch, date(2026, 1, 11))
    full = [_nav_row("2026-01-08"), _nav_row("2026-01-09"), _nav_row("2026-01-10")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    hist = src.nav_history(FAKE_ID_A)
    assert hist.warnings == ()


def test_nav_history_end_gap_coexists_with_dedup_dedup_first(monkeypatch):
    # Both warnings present, dedup stays FIRST, end-gap appended after, no double-warn.
    _patch_today(monkeypatch, date(2026, 1, 25))
    full = [
        _nav_row("2026-01-08", nav=100.0),
        _nav_row("2026-01-08", nav=100.0),   # identical dup -> dedupe + warn
        _nav_row("2026-01-09", nav=101.0),
        _nav_row("2026-01-10", nav=102.0),
    ]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    hist = src.nav_history(FAKE_ID_A)
    assert len(hist.warnings) == 2
    assert "dedup" in hist.warnings[0].lower()                    # dedup first
    assert hist.warnings[1].startswith("nav_end_gap:")           # end-gap second
    assert sum(w.startswith("nav_end_gap:") for w in hist.warnings) == 1  # no double


def test_nav_history_past_to_date_covered_no_end_gap_warning(monkeypatch):
    # Past to_date the series reaches -> no warn, regardless of (much later) today.
    _patch_today(monkeypatch, date(2026, 6, 20))
    full = [_nav_row("2024-01-08"), _nav_row("2024-01-09"), _nav_row("2024-01-10")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    hist = src.nav_history(FAKE_ID_A, date(2024, 1, 1), date(2024, 1, 10))
    assert hist.warnings == ()


def test_nav_history_past_to_date_early_ending_warns(monkeypatch):
    # Series ends well before a past to_date -> warns vs to_date (not today).
    _patch_today(monkeypatch, date(2026, 6, 20))
    full = [_nav_row("2024-01-08"), _nav_row("2024-01-09"), _nav_row("2024-01-10")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    hist = src.nav_history(FAKE_ID_A, date(2024, 1, 1), date(2024, 6, 30))
    matches = [w for w in hist.warnings if w.startswith("nav_end_gap:")]
    assert len(matches) == 1
    assert "before 2024-06-30" in matches[0]


def test_nav_history_end_gap_never_raises_and_fetched_at_is_real(monkeypatch):
    # The helper never raises; fetched_at_utc stays the real fetch stamp (a tz-aware
    # datetime), NOT the injected `today` date.
    _patch_today(monkeypatch, date(2026, 1, 25))
    before = datetime.now(timezone.utc)
    full = [_nav_row("2026-01-08"), _nav_row("2026-01-09"), _nav_row("2026-01-10")]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    hist = src.nav_history(FAKE_ID_A)
    after = datetime.now(timezone.utc)
    assert hist.fetched_at_utc is not None
    assert hist.fetched_at_utc.tzinfo is not None
    assert before <= hist.fetched_at_utc <= after
    assert not isinstance(hist.fetched_at_utc, date) or isinstance(hist.fetched_at_utc, datetime)


def test_nav_today_returns_date_typed_value():
    # _today() is the injected date source: returns a `date`, never a datetime.
    from vnfin.funds.fmarket import _today
    t = _today()
    assert isinstance(t, date) and not isinstance(t, datetime)


# ---------------------------------------------------------------------------
# #190 — list-level `fund_nav_stale` warning on FundList
# (the helper is PURE: tests inject `today` directly — no wall-clock dependency)
# ---------------------------------------------------------------------------


def _mk_fund(code, nav_as_of):
    """A minimal synthetic Fund carrying only the fields the staleness helper reads
    (``code`` + ``nav_as_of``); other fields are obviously-fake placeholders."""
    return Fund(
        code=code,
        name="FAKE FUND " + code,
        id=FAKE_ID_A,
        nav=FAKE_NAV_A,
        manager="FFM",
        asset_type="STOCK",
        nav_as_of=nav_as_of,
    )


def test_fund_nav_stale_warns_when_a_fund_exceeds_threshold():
    from vnfin.funds.fmarket import _fund_nav_stale_warning

    today = date(2026, 6, 20)
    funds = (
        _mk_fund("STALECO", today - timedelta(days=8)),  # stale (gap 8 > 7)
        _mk_fund("FRESHCO", today - timedelta(days=1)),  # fresh
    )
    warns = _fund_nav_stale_warning(funds, today)
    assert len(warns) == 1
    w = warns[0]
    assert w.startswith("fund_nav_stale:")
    # detail names the stale code @ its nav_as_of date; the fresh one is absent
    assert "STALECO@2026-06-12" in w
    assert "FRESHCO" not in w


def test_fund_nav_stale_silent_when_all_fresh():
    from vnfin.funds.fmarket import _fund_nav_stale_warning

    today = date(2026, 6, 20)
    funds = (
        _mk_fund("A", today - timedelta(days=0)),
        _mk_fund("B", today - timedelta(days=7)),  # exactly at threshold -> fresh
        _mk_fund("C", today - timedelta(days=3)),
    )
    assert _fund_nav_stale_warning(funds, today) == ()


def test_fund_nav_stale_boundary():
    from vnfin.funds.fmarket import _fund_nav_stale_warning

    today = date(2026, 6, 20)
    # gap == 7 -> NOT stale
    assert _fund_nav_stale_warning((_mk_fund("EDGE", today - timedelta(days=7)),), today) == ()
    # gap == 8 -> stale
    warns = _fund_nav_stale_warning((_mk_fund("EDGE", today - timedelta(days=8)),), today)
    assert len(warns) == 1 and warns[0].startswith("fund_nav_stale:")


def test_fund_nav_stale_ignores_none_nav_as_of():
    from vnfin.funds.fmarket import _fund_nav_stale_warning

    today = date(2026, 6, 20)
    funds = (
        _mk_fund("UNKNOWN", None),  # nav_as_of unknown -> NEVER flagged
        _mk_fund("FRESHCO", today - timedelta(days=2)),
    )
    assert _fund_nav_stale_warning(funds, today) == ()


def test_fund_nav_stale_detail_caps_enumeration():
    from vnfin.funds.fmarket import _fund_nav_stale_warning

    today = date(2026, 6, 20)
    # 7 stale funds -> detail caps at 5 codes + "+2 more"
    funds = tuple(
        _mk_fund(f"STALE{i}", today - timedelta(days=10 + i)) for i in range(7)
    )
    warns = _fund_nav_stale_warning(funds, today)
    assert len(warns) == 1
    w = warns[0]
    # exactly five enumerated codes
    assert w.count("STALE") == 5
    assert "+2 more" in w
    # the count of stale funds is reported honestly even though enumeration is capped
    assert "7 fund(s)" in w


def test_fund_nav_stale_helper_never_calls_wall_clock():
    # Two different injected `today` values must yield different verdicts on the SAME
    # funds -> proves the verdict is driven by the injected reference, not a baked clock.
    from vnfin.funds.fmarket import _fund_nav_stale_warning

    nav_date = date(2026, 6, 10)
    funds = (_mk_fund("X", nav_date),)
    # today close to nav_date -> fresh
    assert _fund_nav_stale_warning(funds, date(2026, 6, 15)) == ()
    # today far from nav_date -> stale
    later = _fund_nav_stale_warning(funds, date(2026, 7, 1))
    assert len(later) == 1 and later[0].startswith("fund_nav_stale:")


def test_list_funds_appends_fund_nav_stale_warning(monkeypatch):
    # End-to-end wiring: list_funds() supplies `today` via _today() internally and
    # appends the list-level token to FundList.warnings (NO public param change).
    _patch_today(monkeypatch, date(2026, 6, 20))
    rows = [
        _fund_row_with_extra({"lastNAVDate": _LASTNAVDATE_VN_MIDNIGHT}),  # 2026-03-15 -> stale
    ]
    fl = _src(_fund_list_payload(rows=rows)).list_funds()
    matches = [w for w in fl.warnings if w.startswith("fund_nav_stale:")]
    assert len(matches) == 1
    assert "TESTCO@2026-03-15" in matches[0]


# ---------------------------------------------------------------------------
# #155: richer fund metadata (management_fee_pct, inception_date, description),
# SectorWeight, fund_missing_fees / fund_partial_holdings warning tokens.
# ---------------------------------------------------------------------------


# --- management_fee_pct on the LIST row (free; equity-row-only -> Optional) ----

def test_list_funds_management_fee_pct_from_list_row():
    # The default equity row carries managementFee=1.0; the bond row omits it.
    funds = _src(_fund_list_payload()).list_funds()
    equity = funds.funds[0]
    bond = funds.funds[1]
    assert equity.management_fee_pct == pytest.approx(1.0)
    assert bond.management_fee_pct is None  # absent -> None, never fabricated


@pytest.mark.parametrize("bad", ["garbage", True, [], {}, None], ids=["str", "bool", "list", "dict", "null"])
def test_list_funds_management_fee_pct_malformed_is_none(bad):
    # A present-but-malformed managementFee must NOT crash the whole list and must
    # NOT fabricate a value -> left None (fail-soft for an optional display field).
    row = _fund_row_with_extra()
    row["managementFee"] = bad
    fund = _src(_fund_list_payload(rows=[row])).list_funds()[0]
    assert fund.management_fee_pct is None


def test_list_funds_management_fee_pct_negative_is_none():
    # A negative fee is impossible -> dropped to None (never a fabricated/garbage value).
    row = _fund_row_with_extra()
    row["managementFee"] = -1.0
    fund = _src(_fund_list_payload(rows=[row])).list_funds()[0]
    assert fund.management_fee_pct is None


def test_fund_back_compat_new_fields_default_none():
    # Frozen-dataclass additive: an existing-style Fund(...) built without the new
    # fields keeps working and defaults to None for all three.
    f = Fund(code="TESTCO", name="X", id=FAKE_ID_A, nav=FAKE_NAV_A, manager="M", asset_type="STOCK")
    assert f.management_fee_pct is None
    assert f.inception_date is None
    assert f.description is None


def test_list_funds_inception_and_description_none_on_list_path():
    # inception_date / description are DETAIL-doc fields, absent on the list row ->
    # they stay None on the list-sourced Fund (never fabricated from the list).
    funds = _src(_fund_list_payload()).list_funds()
    assert funds.funds[0].inception_date is None
    assert funds.funds[0].description is None


# --- fund_missing_fees warning token (list-level) ------------------------------

def test_list_funds_fund_missing_fees_warns_when_fee_absent(monkeypatch):
    # The default bond row omits managementFee -> list carries fund_missing_fees
    # enumerating the fund(s) with no disclosed fee.
    _patch_today(monkeypatch, date(2024, 1, 1))  # keep nav-stale silent / deterministic
    fl = _src(_fund_list_payload()).list_funds()
    matches = [w for w in fl.warnings if w.startswith("fund_missing_fees")]
    assert len(matches) == 1
    assert "ZZZBOND" in matches[0]
    assert "TESTCO" not in matches[0]  # the equity row HAS a fee -> not listed


def test_list_funds_no_missing_fees_when_all_present(monkeypatch):
    _patch_today(monkeypatch, date(2024, 1, 1))
    rows = [_fund_row_with_extra()]
    rows[0]["managementFee"] = 1.0
    fl = _src(_fund_list_payload(rows=rows)).list_funds()
    assert not any(w.startswith("fund_missing_fees") for w in fl.warnings)


# --- include_metadata toggle (default TRUE; free, no extra request) ------------

def test_list_funds_include_metadata_default_true_populates_fee():
    # Default: management_fee_pct is populated from the row (no extra request).
    funds = _src(_fund_list_payload()).list_funds()
    assert funds.funds[0].management_fee_pct == pytest.approx(1.0)


def test_list_funds_include_metadata_false_skips_fee_and_warning(monkeypatch):
    # Opt-out: management_fee_pct is left None and no fund_missing_fees warning fires.
    _patch_today(monkeypatch, date(2024, 1, 1))
    funds = _src(_fund_list_payload()).list_funds(include_metadata=False)
    assert all(f.management_fee_pct is None for f in funds.funds)
    assert not any(w.startswith("fund_missing_fees") for w in funds.warnings)


def test_list_funds_include_metadata_no_extra_request():
    # The metadata is free off the existing filter call — exactly one request either way.
    get = _capture_get(_fund_list_payload())
    FmarketFundSource(http_get=get).list_funds(include_metadata=True)
    assert len(get.calls) == 1
    get2 = _capture_get(_fund_list_payload())
    FmarketFundSource(http_get=get2).list_funds(include_metadata=False)
    assert len(get2.calls) == 1


# --- inception_date / description on the DETAIL doc (via asset_allocation) -----

def test_asset_allocation_surfaces_inception_and_description():
    alloc = _src(_holdings_payload()).asset_allocation(FAKE_ID_A)
    assert alloc.inception_date == date(2026, 3, 15)  # firstIssueAt epoch-ms -> VN date
    assert alloc.description == "FAKE synthetic fund description blurb"


def test_asset_allocation_inception_absent_is_none():
    base = json.loads(_holdings_payload())
    base["data"].pop("firstIssueAt", None)
    alloc = _src(json.dumps(base)).asset_allocation(FAKE_ID_A)
    assert alloc.inception_date is None


@pytest.mark.parametrize("bad", [None, 0, -1, "garbage", "1773507600000", True, 1.5], ids=["null", "zero", "neg", "str", "str_num", "bool", "frac"])
def test_asset_allocation_inception_garbage_is_none(bad):
    base = json.loads(_holdings_payload())
    base["data"]["firstIssueAt"] = bad
    alloc = _src(json.dumps(base)).asset_allocation(FAKE_ID_A)
    assert alloc.inception_date is None


def test_asset_allocation_description_absent_is_none():
    base = json.loads(_holdings_payload())
    base["data"].pop("description", None)
    alloc = _src(json.dumps(base)).asset_allocation(FAKE_ID_A)
    assert alloc.description is None


@pytest.mark.parametrize("bad", [123, [], {}, True], ids=["int", "list", "dict", "bool"])
def test_asset_allocation_description_non_string_is_none(bad):
    base = json.loads(_holdings_payload())
    base["data"]["description"] = bad
    alloc = _src(json.dumps(base)).asset_allocation(FAKE_ID_A)
    assert alloc.description is None


def test_asset_allocation_description_blank_is_none():
    base = json.loads(_holdings_payload())
    base["data"]["description"] = "   "
    alloc = _src(json.dumps(base)).asset_allocation(FAKE_ID_A)
    assert alloc.description is None


# --- SectorWeight model + parse productIndustriesHoldingList -------------------

def test_sector_weight_model_frozen():
    sw = SectorWeight(industry="Tech", weight_pct=50.0)
    assert sw.industry == "Tech"
    assert sw.weight_pct == pytest.approx(50.0)
    with pytest.raises(Exception):
        sw.weight_pct = 1.0  # type: ignore[misc]


def test_asset_allocation_surfaces_sector_weights():
    alloc = _src(_holdings_payload()).asset_allocation(FAKE_ID_A)
    assert all(isinstance(s, SectorWeight) for s in alloc.sector_weights)
    by_ind = {s.industry: s.weight_pct for s in alloc.sector_weights}
    assert by_ind["Fake industry one"] == pytest.approx(50.0)
    assert by_ind["Fake industry two"] == pytest.approx(25.0)


def test_asset_allocation_sector_weights_absent_is_empty():
    base = json.loads(_holdings_payload())
    base["data"].pop("productIndustriesHoldingList", None)
    alloc = _src(json.dumps(base)).asset_allocation(FAKE_ID_A)
    assert alloc.sector_weights == ()


def test_asset_allocation_sector_weights_empty_list_is_empty():
    alloc = _src(_holdings_payload(industries=[])).asset_allocation(FAKE_ID_A)
    assert alloc.sector_weights == ()


@pytest.mark.parametrize(
    "bad_row",
    [
        {"industry": "", "assetPercent": 10.0},          # blank industry
        {"industry": "   ", "assetPercent": 10.0},       # whitespace industry
        {"industry": 123, "assetPercent": 10.0},         # non-string industry
        {"assetPercent": 10.0},                          # missing industry
        {"industry": "X", "assetPercent": "garbage"},    # non-numeric weight
        {"industry": "X", "assetPercent": 150.0},        # out-of-range weight
        {"industry": "X", "assetPercent": -1.0},         # negative weight
        {"industry": "X"},                               # missing weight
        "not-a-dict",                                    # non-object row
    ],
    ids=["blank", "ws", "non_str", "missing_ind", "bad_weight", "oob", "neg", "missing_weight", "non_obj"],
)
def test_asset_allocation_sector_weights_fail_closed_drops_malformed(bad_row):
    # Fail-closed like _parse_asset_class_row: a malformed sector row is DROPPED
    # (never crashes the whole call, never fabricates) — the good rows still surface.
    good = {"industry": "Good industry", "assetPercent": 30.0}
    alloc = _src(_holdings_payload(industries=[bad_row, good])).asset_allocation(FAKE_ID_A)
    inds = [s.industry for s in alloc.sector_weights]
    assert "Good industry" in inds
    assert len(alloc.sector_weights) == 1  # only the good row survives


def test_asset_allocation_sector_weights_non_array_is_empty():
    # A present-but-non-array productIndustriesHoldingList must not crash -> empty.
    base = json.loads(_holdings_payload())
    base["data"]["productIndustriesHoldingList"] = "not-an-array"
    alloc = _src(json.dumps(base)).asset_allocation(FAKE_ID_A)
    assert alloc.sector_weights == ()


# --- fund_partial_holdings warning token (detail-doc coverage% bound) ----------

def test_asset_allocation_fund_partial_holdings_warns_below_bound():
    # Disclosed top holdings sum to a low coverage% (< the documented bound) ->
    # AssetAllocation.warnings carries fund_partial_holdings.
    top = [
        {"stockCode": "FAKE1", "netAssetPercent": 5.0, "type": "STOCK"},
        {"stockCode": "FAKE2", "netAssetPercent": 4.0, "type": "STOCK"},
    ]  # 9% disclosed -> well below the bound
    alloc = _src(_holdings_payload(top=top)).asset_allocation(FAKE_ID_A)
    matches = [w for w in alloc.warnings if w.startswith("fund_partial_holdings")]
    assert len(matches) == 1


def test_asset_allocation_no_partial_holdings_when_above_bound():
    top = [
        {"stockCode": "FAKE1", "netAssetPercent": 40.0, "type": "STOCK"},
        {"stockCode": "FAKE2", "netAssetPercent": 35.0, "type": "STOCK"},
    ]  # 75% disclosed -> above the bound
    alloc = _src(_holdings_payload(top=top)).asset_allocation(FAKE_ID_A)
    assert not any(w.startswith("fund_partial_holdings") for w in alloc.warnings)


def test_asset_allocation_partial_holdings_counts_bonds_too():
    # Coverage sums equity + bond top-holdings (a bond fund discloses only bonds).
    bond = [
        {"stockCode": "ZZZBOND1", "netAssetPercent": 30.0, "type": "BOND"},
        {"stockCode": "ZZZBOND2", "netAssetPercent": 30.0, "type": "BOND"},
    ]  # 60% disclosed -> above the bound, no warning
    alloc = _src(
        _holdings_payload_with(productTopHoldingList=[], productTopHoldingBondList=bond)
    ).asset_allocation(FAKE_ID_A)
    assert not any(w.startswith("fund_partial_holdings") for w in alloc.warnings)


def test_asset_allocation_partial_holdings_no_disclosed_holdings_warns():
    # No top-holdings disclosed at all -> 0% coverage -> warns (still served, never
    # raises: asset allocation is the meaningful payload here).
    base = json.loads(_holdings_payload())
    base["data"]["productTopHoldingList"] = []
    base["data"].pop("productTopHoldingBondList", None)
    alloc = _src(json.dumps(base)).asset_allocation(FAKE_ID_A)
    assert any(w.startswith("fund_partial_holdings") for w in alloc.warnings)


def test_asset_allocation_back_compat_new_fields_default():
    # Additive: an AssetAllocation built without the new fields keeps working.
    a = AssetAllocation(
        product_id=1, classes=(), source="fmarket"
    )
    assert a.sector_weights == ()
    assert a.inception_date is None
    assert a.description is None


# ---------------------------------------------------------------------------
# Issue #194 — quarantine a conflicting navDate (mirror #186) instead of aborting
# the whole NAV series. DROP the date (never pick, never average); serve the rest;
# disclose via the never-silent `quarantined_conflicting_navdates` token. A
# systematically-conflicting feed still raises InvalidData. Constants reuse #186's
# `_QUARANTINE_FRACTION = 0.10` / `_QUARANTINE_ABS_FLOOR = 3`, counting each
# conflicting DATE once. All fixtures SYNTHETIC (FAKE_ID_A; fabricated NAVs).
# ---------------------------------------------------------------------------


def _conflict_rows(conflicting_dates, clean_dates):
    """Build a synthetic nav-history `data` array: each date in `conflicting_dates`
    gets TWO rows with DIFFERENT NAVs (a same-date conflict); each in `clean_dates`
    gets one row. NAVs are fabricated and obviously fake."""
    rows = []
    nav = 1000.0
    for d in conflicting_dates:
        rows.append({"navDate": d, "nav": nav, "productId": FAKE_ID_A})
        rows.append({"navDate": d, "nav": nav + 7.0, "productId": FAKE_ID_A})
        nav += 100.0
    for d in clean_dates:
        rows.append({"navDate": d, "nav": nav, "productId": FAKE_ID_A})
        nav += 100.0
    return rows


# --- case 1: one conflicting navDate -> served-with-warning, NOT InvalidData -------

def test_nav_history_case1_one_conflict_serves_rest_with_token():
    # poisoned=1, considered=4 (1 quarantined + 3 clean): 1 > max(3, 0.4)=3 is False ->
    # serves the 3 clean dates; 2024-01-02 ABSENT; token names the dropped date.
    rows = _conflict_rows(["2024-01-02"], ["2024-01-01", "2024-01-03", "2024-01-04"])
    hist = _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)
    assert isinstance(hist, NavHistory)
    assert [p.date for p in hist.points] == [
        date(2024, 1, 1), date(2024, 1, 3), date(2024, 1, 4)
    ]
    assert date(2024, 1, 2) not in [p.date for p in hist.points]
    matches = [w for w in hist.warnings if w.startswith("quarantined_conflicting_navdates:")]
    assert len(matches) == 1 and "2024-01-02" in matches[0]


# --- case 2: systematically-conflicting -> still raises (threshold preserved) ------

def test_nav_history_case2_systematic_conflict_raises_invalid():
    # 5 conflicting dates + 3 clean -> considered=8, poisoned=5; 5 > max(3, 0.8)=3 -> RAISE.
    conflicting = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
    clean = ["2024-01-06", "2024-01-07", "2024-01-08"]
    rows = _conflict_rows(conflicting, clean)
    with pytest.raises(InvalidData) as exc:
        _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)
    msg = str(exc.value)
    assert "5/8" in msg
    assert "systematically broken" in msg


# --- case 3: threshold boundary (short series, floor dominates) --------------------

def test_nav_history_case3_three_conflicts_at_floor_serves():
    # 3 conflicting dates + 4 clean -> considered=7, poisoned=3; 3 > max(3, 0.7)=3 is
    # False -> SERVES the 4 clean dates + warning lists the 3 dropped dates.
    conflicting = ["2024-01-01", "2024-01-02", "2024-01-03"]
    clean = ["2024-01-04", "2024-01-05", "2024-01-06", "2024-01-07"]
    rows = _conflict_rows(conflicting, clean)
    hist = _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)
    assert [p.date for p in hist.points] == [
        date(2024, 1, 4), date(2024, 1, 5), date(2024, 1, 6), date(2024, 1, 7)
    ]
    matches = [w for w in hist.warnings if w.startswith("quarantined_conflicting_navdates:")]
    assert len(matches) == 1
    for d in ("2024-01-01", "2024-01-02", "2024-01-03"):
        assert d in matches[0]


def test_nav_history_case3_four_conflicts_above_floor_raises():
    # 4 conflicting dates + 4 clean -> considered=8, poisoned=4; 4 > max(3, 0.8)=3 ->
    # RAISE. Pins the absolute floor at 3.
    conflicting = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
    clean = ["2024-01-05", "2024-01-06", "2024-01-07", "2024-01-08"]
    rows = _conflict_rows(conflicting, clean)
    with pytest.raises(InvalidData) as exc:
        _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)
    assert "4/8" in str(exc.value)
    assert "systematically broken" in str(exc.value)


# --- case 4: identical-value duplicate (regression — behavior UNCHANGED) -----------

def test_nav_history_case4_identical_dup_dedupes_no_quarantine_token():
    # Same date, SAME nav -> keep-first + `deduped_duplicate_nav_rows`, NO quarantine
    # token, date PRESENT in points. (Unchanged #158/#162 behavior.)
    rows = [
        {"navDate": "2024-01-02", "nav": 10100.0, "productId": FAKE_ID_A},
        {"navDate": "2024-01-02", "nav": 10100.0, "productId": FAKE_ID_A},
        {"navDate": "2024-01-03", "nav": 10200.0, "productId": FAKE_ID_A},
    ]
    hist = _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)
    assert [p.date for p in hist.points] == [date(2024, 1, 2), date(2024, 1, 3)]
    assert any(w.startswith("deduped_duplicate_nav_rows:") for w in hist.warnings)
    assert not any(w.startswith("quarantined_conflicting_navdates:") for w in hist.warnings)


# --- case 5: never averages / never picks (degrade-not-fabricate) ------------------

def test_nav_history_case5_never_averages_conflicting_date():
    # The repro values: 15091.0 vs 15120.0 (mean 15105.5). The conflicting date is
    # ABSENT — no served point equals or is near the mean, and neither raw value
    # survives for that date.
    rows = [
        {"navDate": "2018-07-31", "nav": 15091.0, "productId": FAKE_ID_A},
        {"navDate": "2018-07-31", "nav": 15120.0, "productId": FAKE_ID_A},
        {"navDate": "2018-08-01", "nav": 15200.0, "productId": FAKE_ID_A},
    ]
    hist = _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)
    assert [p.date for p in hist.points] == [date(2018, 8, 1)]
    for p in hist.points:
        assert p.date != date(2018, 7, 31)
        # no fabricated value anywhere near the mean / either raw value
        assert abs(p.nav - 15105.5) > 1.0
        assert p.nav not in (15091.0, 15120.0)


# --- case 6: two distinct conflicting dates under threshold (long series) ----------

def test_nav_history_case6_two_conflicts_under_threshold_both_dropped_sorted():
    # 2 conflicting + 18 clean -> considered=20, poisoned=2; 2 > max(3, 2.0)=3 is False
    # -> both dropped, the rest served, the warning lists BOTH dates SORTED.
    conflicting = ["2024-03-15", "2024-01-10"]   # deliberately unsorted on input
    clean = [f"2024-02-{day:02d}" for day in range(1, 19)]  # 18 clean Feb dates
    rows = _conflict_rows(conflicting, clean)
    hist = _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)
    got = [p.date for p in hist.points]
    assert date(2024, 1, 10) not in got and date(2024, 3, 15) not in got
    assert len(got) == 18
    matches = [w for w in hist.warnings if w.startswith("quarantined_conflicting_navdates:")]
    assert len(matches) == 1
    # both dates listed, SORTED (2024-01-10 before 2024-03-15)
    assert matches[0].index("2024-01-10") < matches[0].index("2024-03-15")


# --- case 7: conflict beats dedup on the SAME date (Note 1) ------------------------

def test_nav_history_case7_conflict_beats_dedup_on_same_date():
    # One date has an identical dup AND a conflicting row -> the date is QUARANTINED
    # (conflict wins), ABSENT from points, in the quarantine token, and does NOT inflate
    # the dedup count. The other date's genuine identical dup still dedupes normally.
    rows = [
        # poisoned date: two identical 100.0 rows + one conflicting 101.0 row
        {"navDate": "2024-04-04", "nav": 100.0, "productId": FAKE_ID_A},
        {"navDate": "2024-04-04", "nav": 100.0, "productId": FAKE_ID_A},
        {"navDate": "2024-04-04", "nav": 101.0, "productId": FAKE_ID_A},
        # a separate, genuinely-deduped date (identical dup) so dedup is still exercised
        {"navDate": "2024-04-05", "nav": 200.0, "productId": FAKE_ID_A},
        {"navDate": "2024-04-05", "nav": 200.0, "productId": FAKE_ID_A},
        # a clean date
        {"navDate": "2024-04-06", "nav": 300.0, "productId": FAKE_ID_A},
    ]
    hist = _src(_nav_history_payload(rows=rows)).nav_history(FAKE_ID_A)
    got = [p.date for p in hist.points]
    assert date(2024, 4, 4) not in got           # quarantined, not deduped
    assert got == [date(2024, 4, 5), date(2024, 4, 6)]
    qmatches = [w for w in hist.warnings if w.startswith("quarantined_conflicting_navdates:")]
    assert len(qmatches) == 1 and "2024-04-04" in qmatches[0]
    # the dedup token is present ONLY for the OTHER date (2024-04-05); its count must be
    # exactly 1 (the poisoned date's earlier identical dup does NOT inflate it).
    dmatches = [w for w in hist.warnings if w.startswith("deduped_duplicate_nav_rows:")]
    assert len(dmatches) == 1
    assert "1 duplicate" in dmatches[0]


# --- case 8: quarantine runs BEFORE #172 empty/stale (Note 3) ----------------------
# The EmptyData variant (window emptied by a sub-threshold quarantine -> #172 EmptyData)
# lives in test_nav_history_in_window_all_conflict_sub_threshold_falls_to_empty. Here we
# pin the ORDERING with TWO in-window conflicting dates (still sub-threshold: poisoned=2
# <= floor 3, points=[]): the result is the #172 EmptyData, NOT the systematically-broken
# InvalidData and NOT a NavHistory. (StaleData is unreachable for an in-window quarantine:
# an in-window date means max_navdate >= lo, so #172 yields plain EmptyData, not stale.)

def test_nav_history_case8_two_inwindow_conflicts_sub_threshold_falls_to_empty():
    full = [
        _nav_row("2024-04-04", nav=100.0),
        _nav_row("2024-04-04", nav=101.0),   # conflict #1 (in window)
        _nav_row("2024-05-05", nav=200.0),
        _nav_row("2024-05-05", nav=202.0),   # conflict #2 (in window)
    ]
    src = FmarketFundSource(http_get=_window_aware_get(full, []))
    with pytest.raises(EmptyData) as exc:
        src.nav_history(FAKE_ID_A, date(2024, 1, 1), date(2024, 12, 31))
    # NOT the systematically-broken InvalidData (poisoned=2 <= floor 3), NOT StaleData
    assert not isinstance(exc.value, StaleData)
    assert "in range" in str(exc.value)
