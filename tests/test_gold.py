"""Gold domain tests — synthetic fixtures only. No real provider rows committed.

Fixture shapes are hand-crafted to match the verified live shapes documented in
docs/research/2026-06-18-gold-vietnam-domestic.md and docs/research/2026-06-18-gold-world.md.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable, VnfinError
from vnfin.gold import (
    BTMCGoldSource,
    CurrencyApiGoldSource,
    GoldApiSource,
    GoldBar,
    GoldHistory,
    GoldQuote,
    GoldSource,
    PNJGoldSource,
)

# --------------------------------------------------------------------------- #
# Synthetic fixtures (hand-crafted to match the verified real shapes).        #
# --------------------------------------------------------------------------- #

# BTMC: indexed-key JSON. Prices = VND per CHỈ as integer STRINGS. @d = "DD/MM/YYYY HH:MM".
_BTMC_ROWS = [
    # name, karat, buy, sell, worldflag, datetime
    ("VÀNG MIẾNG SJC (Vàng SJC)", "24k", "14880000", "15130000", "4322", "17/06/2026 15:38"),
    ("NHẪN TRÒN TRƠN (Vàng Rồng Thăng Long)", "24k", "14880000", "15130000", "4322", "17/06/2026 15:38"),
    ("BẠC MIẾNG (BẠC RỒNG THĂNG LONG Ag 999)", "", "2637000", "2719000", "4322", "17/06/2026 15:38"),
]


def _btmc_json(rows=None):
    rows = _BTMC_ROWS if rows is None else rows
    data = []
    for i, (n, k, pb, ps, pt, d) in enumerate(rows, start=1):
        data.append(
            {
                "@row": str(i),
                f"@n_{i}": n,
                f"@k_{i}": k,
                f"@h_{i}": "",
                f"@pb_{i}": pb,
                f"@ps_{i}": ps,
                f"@pt_{i}": pt,
                f"@d_{i}": d,
            }
        )
    return json.dumps({"DataList": {"Data": data}})


# PNJ: prices in THOUSAND VND per CHỈ (giaban 15130 -> 15,130,000 VND). No timestamp.
_PNJ_ROWS = [
    ("SJC", "Vàng miếng SJC 999.9", 15130, 14880),
    ("N24K", "Nhẫn Trơn PNJ 999.9", 15130, 14830),
    ("24K", "Vàng nữ trang 999.9", 15030, 14630),
]


def _pnj_json(rows=None):
    rows = _PNJ_ROWS if rows is None else rows
    return json.dumps(
        {"data": [{"masp": m, "tensp": t, "giaban": gb, "giamua": gm} for (m, t, gb, gm) in rows]}
    )


# gold-api: live spot XAU/USD. price = USD per troy ounce.
def _goldapi_json(price=4296.899902, symbol="XAU", updated="2026-06-17T18:10:08Z"):
    return json.dumps(
        {
            "currency": "USD",
            "currencySymbol": "$",
            "exchangeRate": 1.0,
            "name": "Gold",
            "price": price,
            "symbol": symbol,
            "updatedAt": updated,
            "updatedAtReadable": "a few seconds ago",
        }
    )


# currency-api usd base: usd.xau = troy ounces per 1 USD -> invert for USD/oz.
def _currency_usd_json(d="2026-06-17", usd_xau=0.0002313114):
    return json.dumps({"date": d, "usd": {"eur": 0.86, "vnd": 26000.0, "xau": usd_xau}})


def _static_get(text):
    def _g(url, params=None, headers=None):
        return text

    return _g


def _raising_get(exc):
    def _g(url, params=None, headers=None):
        raise exc

    return _g


# --------------------------------------------------------------------------- #
# Port / model basics                                                         #
# --------------------------------------------------------------------------- #


def test_all_adapters_implement_port():
    for cls in (BTMCGoldSource, PNJGoldSource, GoldApiSource, CurrencyApiGoldSource):
        assert issubclass(cls, GoldSource)


def test_capability_flags():
    btmc = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    pnj = PNJGoldSource(http_get=_static_get(_pnj_json()))
    gapi = GoldApiSource(http_get=_static_get(_goldapi_json()))
    capi = CurrencyApiGoldSource(http_get=_static_get(_currency_usd_json()))
    # spot-only sources
    assert btmc.provides_spot and not btmc.provides_history
    assert pnj.provides_spot and not pnj.provides_history
    assert gapi.provides_spot and not gapi.provides_history
    # currency-api gives daily history
    assert capi.provides_spot and capi.provides_history


def test_quote_is_frozen():
    q = GoldQuote(
        time=datetime(2026, 6, 17, tzinfo=timezone.utc),
        product="SJC",
        buy=14_880_000.0,
        sell=15_130_000.0,
        unit="VND/chi",
        currency="VND",
        source="btmc",
        fetched_at_utc=datetime.now(timezone.utc),
    )
    with pytest.raises(Exception):
        q.buy = 1.0  # frozen


def test_gold_errors_are_vnfin_errors():
    assert issubclass(EmptyData, VnfinError)
    assert issubclass(InvalidData, VnfinError)
    assert issubclass(SourceUnavailable, VnfinError)


# --------------------------------------------------------------------------- #
# BTMC (VN domestic, VND/chỉ full-digit strings)                              #
# --------------------------------------------------------------------------- #


def test_btmc_parses_quotes():
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    quotes = s.get_quotes()
    assert len(quotes) == 3
    sjc = next(q for q in quotes if "SJC" in q.product)
    assert sjc.buy == pytest.approx(14_880_000.0)
    assert sjc.sell == pytest.approx(15_130_000.0)
    assert sjc.currency == "VND"
    assert sjc.unit == "VND/chi"
    assert sjc.source == "btmc"
    assert sjc.fetched_at_utc is not None


def test_btmc_parses_dd_mm_yyyy_timestamp_as_vn_tz():
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    sjc = next(q for q in s.get_quotes() if "SJC" in q.product)
    # 17/06/2026 15:38 Asia/Ho_Chi_Minh (+07)
    assert sjc.time.utcoffset().total_seconds() == 7 * 3600
    assert sjc.time.date() == date(2026, 6, 17)
    assert (sjc.time.hour, sjc.time.minute) == (15, 38)


def test_btmc_get_quote_by_product_substring():
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    q = s.get_quote("sjc")  # case-insensitive substring
    assert "SJC" in q.product


def test_btmc_no_match_raises_empty():
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    with pytest.raises(EmptyData):
        s.get_quote("DOES_NOT_EXIST")


def test_btmc_empty_datalist_raises_empty():
    s = BTMCGoldSource(http_get=_static_get(json.dumps({"DataList": {"Data": []}})))
    with pytest.raises(EmptyData):
        s.get_quotes()


def test_btmc_malformed_price_raises_invalid():
    bad = [("VÀNG MIẾNG SJC", "24k", "not-a-number", "15130000", "4322", "17/06/2026 15:38")]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=bad)))
    with pytest.raises(InvalidData):
        s.get_quotes()


def test_btmc_negative_price_raises_invalid():
    bad = [("VÀNG MIẾNG SJC", "24k", "-5", "15130000", "4322", "17/06/2026 15:38")]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=bad)))
    with pytest.raises(InvalidData):
        s.get_quotes()


def test_btmc_bad_timestamp_raises_invalid():
    bad = [("VÀNG MIẾNG SJC", "24k", "14880000", "15130000", "4322", "garbage-time")]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=bad)))
    with pytest.raises(InvalidData):
        s.get_quotes()


def test_btmc_non_json_raises_invalid():
    s = BTMCGoldSource(http_get=_static_get("<html>blocked</html>"))
    with pytest.raises(InvalidData):
        s.get_quotes()


def test_btmc_transport_error_wrapped():
    s = BTMCGoldSource(http_get=_raising_get(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        s.get_quotes()


def test_btmc_history_not_supported():
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    with pytest.raises(VnfinError):
        s.get_history(date(2026, 6, 1), date(2026, 6, 17))


# --------------------------------------------------------------------------- #
# PNJ (VN domestic, THOUSAND-VND/chỉ -> x1000)                                #
# --------------------------------------------------------------------------- #


def test_pnj_scales_thousand_vnd_to_vnd():
    s = PNJGoldSource(http_get=_static_get(_pnj_json()))
    quotes = s.get_quotes()
    sjc = next(q for q in quotes if q.product == "SJC" or "SJC" in q.product)
    # giaban 15130 (thousand VND) -> 15,130,000 VND
    assert sjc.sell == pytest.approx(15_130_000.0)
    assert sjc.buy == pytest.approx(14_880_000.0)
    assert sjc.currency == "VND"
    assert sjc.unit == "VND/chi"
    assert sjc.source == "pnj"


def test_pnj_skips_blank_buy_only_rows():
    # Real feed includes RAW_* "raw gold purchase" rows where giaban (sell) is "" because
    # PNJ buys but does not sell that grade. Those rows must be skipped, not fail the feed.
    rows = [
        ("SJC", "Vàng miếng SJC 999.9", 15130, 14880),
        ("RAW_9999", "Vàng nguyên liệu mua ngoài 99.99", "", 13930),
        ("RAW_9900", "Vàng nguyên liệu mua ngoài 99", "", 13567),
    ]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows)))
    quotes = s.get_quotes()
    assert len(quotes) == 1
    assert quotes[0].product == "SJC"


def test_pnj_all_rows_blank_raises_empty():
    rows = [("RAW_9999", "Vàng nguyên liệu mua ngoài", "", 13930)]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows)))
    with pytest.raises(EmptyData):
        s.get_quotes()


def test_pnj_empty_data_raises_empty():
    s = PNJGoldSource(http_get=_static_get(json.dumps({"data": []})))
    with pytest.raises(EmptyData):
        s.get_quotes()


def test_pnj_malformed_price_raises_invalid():
    bad = [("SJC", "Vàng miếng SJC 999.9", "oops", 14880)]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=bad)))
    with pytest.raises(InvalidData):
        s.get_quotes()


def test_pnj_negative_price_raises_invalid():
    bad = [("SJC", "Vàng miếng SJC 999.9", -1, 14880)]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=bad)))
    with pytest.raises(InvalidData):
        s.get_quotes()


def test_pnj_non_json_raises_invalid():
    s = PNJGoldSource(http_get=_static_get("not json"))
    with pytest.raises(InvalidData):
        s.get_quotes()


def test_pnj_transport_error_wrapped():
    s = PNJGoldSource(http_get=_raising_get(TimeoutError("slow")))
    with pytest.raises(SourceUnavailable):
        s.get_quotes()


# --------------------------------------------------------------------------- #
# gold-api.com (world spot XAU/USD)                                           #
# --------------------------------------------------------------------------- #


def test_goldapi_parses_spot_usd():
    s = GoldApiSource(http_get=_static_get(_goldapi_json(price=4296.9)))
    q = s.get_quote()
    assert q.product == "XAU"
    assert q.currency == "USD"
    assert q.unit == "USD/oz"
    # spot: buy == sell == price (single tick)
    assert q.buy == pytest.approx(4296.9)
    assert q.sell == pytest.approx(4296.9)
    assert q.source == "gold-api"


def test_goldapi_parses_iso_timestamp_utc():
    s = GoldApiSource(http_get=_static_get(_goldapi_json(updated="2026-06-17T18:10:08Z")))
    q = s.get_quote()
    assert q.time == datetime(2026, 6, 17, 18, 10, 8, tzinfo=timezone.utc)


def test_goldapi_silver_symbol():
    s = GoldApiSource(http_get=_static_get(_goldapi_json(price=71.48, symbol="XAG")), symbol="XAG")
    q = s.get_quote()
    assert q.product == "XAG"
    assert q.sell == pytest.approx(71.48)


def test_goldapi_missing_price_raises_invalid():
    s = GoldApiSource(http_get=_static_get(json.dumps({"symbol": "XAU"})))
    with pytest.raises(InvalidData):
        s.get_quote()


def test_goldapi_error_body_raises_empty():
    # provider returns {"error": "Symbol not found"} for bad symbol
    s = GoldApiSource(http_get=_static_get(json.dumps({"error": "Symbol not found"})))
    with pytest.raises(EmptyData):
        s.get_quote()


def test_goldapi_non_finite_raises_invalid():
    s = GoldApiSource(http_get=_static_get('{"symbol":"XAU","price":NaN,"updatedAt":"2026-06-17T18:10:08Z"}'))
    with pytest.raises(InvalidData):
        s.get_quote()


def test_goldapi_non_json_raises_invalid():
    s = GoldApiSource(http_get=_static_get("<html/>"))
    with pytest.raises(InvalidData):
        s.get_quote()


def test_goldapi_transport_error_wrapped():
    s = GoldApiSource(http_get=_raising_get(ConnectionError("net")))
    with pytest.raises(SourceUnavailable):
        s.get_quote()


def test_goldapi_history_not_supported():
    s = GoldApiSource(http_get=_static_get(_goldapi_json()))
    with pytest.raises(VnfinError):
        s.get_history(date(2026, 6, 1), date(2026, 6, 17))


# --------------------------------------------------------------------------- #
# currency-api (world XAU/USD DAILY HISTORY, invert usd.xau)                  #
# --------------------------------------------------------------------------- #


def test_currencyapi_spot_inverts_usd_xau():
    # usd.xau = 0.0002313114 oz/USD -> 1/that = 4323.18 USD/oz
    s = CurrencyApiGoldSource(http_get=_static_get(_currency_usd_json(usd_xau=0.0002313114)))
    q = s.get_quote()
    assert q.product == "XAU"
    assert q.currency == "USD"
    assert q.unit == "USD/oz"
    assert q.sell == pytest.approx(1 / 0.0002313114, rel=1e-9)
    assert q.source == "currency-api"


def test_currencyapi_history_builds_daily_series():
    # Each date is fetched as a separate date-pinned doc; the http_get returns
    # a per-date payload keyed by which date the URL asked for.
    by_date = {
        "2026-06-15": _currency_usd_json(d="2026-06-15", usd_xau=0.000231),
        "2026-06-16": _currency_usd_json(d="2026-06-16", usd_xau=0.0002312),
        "2026-06-17": _currency_usd_json(d="2026-06-17", usd_xau=0.0002313114),
    }

    def _g(url, params=None, headers=None):
        for d, body in by_date.items():
            if d in url:
                return body
        raise FileNotFoundError("404")  # simulate missing date

    s = CurrencyApiGoldSource(http_get=_g)
    hist = s.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert isinstance(hist, GoldHistory)
    assert hist.currency == "USD"
    assert hist.unit == "USD/oz"
    assert hist.source == "currency-api"
    assert len(hist) == 3
    # sorted ascending by date
    dates = [b.date for b in hist.bars]
    assert dates == [date(2026, 6, 15), date(2026, 6, 16), date(2026, 6, 17)]
    assert hist.bars[-1].price == pytest.approx(1 / 0.0002313114, rel=1e-9)
    assert isinstance(hist.bars[0], GoldBar)


def test_currencyapi_history_skips_missing_dates():
    # only the middle date exists; the others 404 -> series still built from what exists
    def _g(url, params=None, headers=None):
        if "2026-06-16" in url:
            return _currency_usd_json(d="2026-06-16", usd_xau=0.0002312)
        raise FileNotFoundError("404")

    s = CurrencyApiGoldSource(http_get=_g)
    hist = s.get_history(date(2026, 6, 15), date(2026, 6, 17))
    assert len(hist) == 1
    assert hist.bars[0].date == date(2026, 6, 16)


def test_currencyapi_history_all_missing_raises_empty():
    s = CurrencyApiGoldSource(http_get=_raising_get(FileNotFoundError("404")))
    with pytest.raises(EmptyData):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


def test_currencyapi_missing_xau_key_raises_invalid():
    s = CurrencyApiGoldSource(http_get=_static_get(json.dumps({"date": "2026-06-17", "usd": {"eur": 0.86}})))
    with pytest.raises(InvalidData):
        s.get_quote()


def test_currencyapi_zero_rate_raises_invalid():
    # usd.xau == 0 would divide-by-zero -> must be InvalidData, not ZeroDivisionError
    s = CurrencyApiGoldSource(http_get=_static_get(_currency_usd_json(usd_xau=0.0)))
    with pytest.raises(InvalidData):
        s.get_quote()


def test_currencyapi_non_json_raises_invalid():
    s = CurrencyApiGoldSource(http_get=_static_get("<html/>"))
    with pytest.raises(InvalidData):
        s.get_quote()


def test_currencyapi_transport_error_wrapped():
    s = CurrencyApiGoldSource(http_get=_raising_get(ConnectionError("net")))
    with pytest.raises(SourceUnavailable):
        s.get_quote()


def test_currencyapi_history_to_dataframe():
    s = CurrencyApiGoldSource(http_get=_static_get(_currency_usd_json(d="2026-06-17", usd_xau=0.0002313114)))
    hist = s.get_history(date(2026, 6, 17), date(2026, 6, 17))
    df = hist.to_dataframe()
    assert list(df.columns) == ["price"]
    assert df.attrs["currency"] == "USD"
    assert df.attrs["unit"] == "USD/oz"
    assert df.attrs["source"] == "currency-api"
