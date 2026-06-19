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
    StooqGoldSource,
)

# --------------------------------------------------------------------------- #
# Synthetic fixtures (hand-crafted to match the verified real shapes).        #
# --------------------------------------------------------------------------- #

# BTMC: indexed-key JSON. SYNTHETIC, obviously-fake names + fabricated round numbers that
# preserve the REAL provider shape:
#   * GOLD rows carry karat "24k" and quote a PER-CHỈ price (no weight token in the name).
#   * Some GOLD rows are buy-only (partner quotes) with sell == 0 — those must be skipped.
#   * SILVER rows carry karat "" and a "BẠC ..." name, and quote the TOTAL price for a
#     stated weight (1 LƯỢNG / 5 LƯỢNG / 1 KG / 500 GRAM) — those must be excluded entirely.
#   * A weighted GOLD row ("... 5 LƯỢNG") proves weight parsing -> canonical VND/lượng.
# Canonical unit is VND/LƯỢNG (1 lượng = 10 chỉ = 37.5 g).
# Fabricated per-chỉ gold tick: buy 10,000,000 / sell 20,000,000  -> per-lượng 100M / 200M.
_BTMC_ROWS = [
    # name, karat, buy, sell, worldflag, datetime
    ("VÀNG MIẾNG TESTCO (Vàng TESTCO)", "24k", "10000000", "20000000", "4322", "17/06/2026 15:38"),
    ("NHẪN TRÒN ZZZ (Vàng ZZZ)", "24k", "10000000", "20000000", "4322", "17/06/2026 15:38"),
    # buy-only partner gold row: sell == 0, must be skipped (not emitted, not a 0-price quote)
    ("VÀNG THƯƠNG HIỆU FAKEPARTNER (Vàng Đối Tác)", "24k", "9000000", "0", "4322", "17/06/2026 15:38"),
    # silver bars: total price for a stated weight, must be EXCLUDED (not gold)
    ("BẠC MIẾNG FAKE1 Ag 999 1 LƯỢNG (FAKE1)", "", "2000000", "3000000", "4322", "17/06/2026 15:38"),
    ("BẠC MIẾNG FAKE1 Ag 999 5 LƯỢNG (FAKE1)", "", "10000000", "15000000", "4322", "17/06/2026 15:38"),
    ("BẠC THỎI FAKE2 999 1 KG (1000 GRAM) (FAKE2)", "", "50000000", "55000000", "4322", "17/06/2026 15:38"),
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


# PNJ: prices in THOUSAND VND per CHỈ (giaban/giamua). Canonical = VND/LƯỢNG = x1000 x10.
# SYNTHETIC obviously-fake codes/names + fabricated round numbers.
# giaban 20000 (thousand VND/chỉ) -> 20,000,000 VND/chỉ -> 200,000,000 VND/lượng.
_PNJ_ROWS = [
    ("TESTCO", "Vàng miếng TESTCO 999.9", 20000, 10000),
    ("ZZZ", "Nhẫn Trơn ZZZ 999.9", 20000, 9000),
    ("FAKE1", "Vàng nữ trang FAKE1 999.9", 19000, 8000),
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
        product="TESTCO",
        buy=100_000_000.0,
        sell=200_000_000.0,
        unit="VND/luong",
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
# BTMC (VN domestic, canonical VND/lượng; gold-only, weight-normalized)        #
# --------------------------------------------------------------------------- #


def test_btmc_parses_quotes():
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    quotes = s.get_quotes()
    # gold-only: 2 priced per-chỉ rows + 0 buy-only (sell==0) + 0 silver rows
    assert len(quotes) == 2
    testco = next(q for q in quotes if "TESTCO" in q.product)
    # per-chỉ tick buy 10M / sell 20M  -> canonical per-lượng 100M / 200M (x10)
    assert testco.buy == pytest.approx(100_000_000.0)
    assert testco.sell == pytest.approx(200_000_000.0)
    assert testco.currency == "VND"
    assert testco.unit == "VND/luong"
    assert testco.source == "btmc"
    assert testco.fetched_at_utc is not None


def test_btmc_excludes_silver():
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    quotes = s.get_quotes()
    # no BẠC/silver products survive the gold filter
    assert all("BẠC" not in q.product.upper() for q in quotes)
    assert all(q.karat for q in quotes)  # gold rows carry a karat; silver karat is ""


def test_btmc_skips_buy_only_zero_sell_rows():
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    quotes = s.get_quotes()
    # the FAKEPARTNER gold row has sell == 0 (buy-only) and must not be emitted
    assert all("FAKEPARTNER" not in q.product for q in quotes)
    assert all(q.sell > 0 for q in quotes)


def test_btmc_normalizes_weighted_gold_to_per_luong():
    # A gold row that states its weight (5 LƯỢNG) quoting the TOTAL price must be
    # divided back to the canonical per-lượng price, matching the per-chỉ rows.
    rows = [
        ("VÀNG MIẾNG TESTCO (Vàng TESTCO)", "24k", "10000000", "20000000", "4322", "17/06/2026 15:38"),
        ("VÀNG MIẾNG TESTCO 5 LƯỢNG (Vàng TESTCO)", "24k", "500000000", "1000000000", "4322", "17/06/2026 15:38"),
    ]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=rows)))
    quotes = s.get_quotes()
    assert len(quotes) == 2
    for q in quotes:
        assert q.unit == "VND/luong"
        assert q.buy == pytest.approx(100_000_000.0)
        assert q.sell == pytest.approx(200_000_000.0)


def test_btmc_weight_token_strictness():
    # Issue #116: when a product name carries an explicit recognized weight unit, the quantity
    # must be a clean positive token. Malformed signed/partial/zero/leading-zero quantities must
    # raise InvalidData instead of substring-matching (".5 LUONG" -> "5 LUONG") or silently
    # falling back to the per-chi default, which would mis-scale the price.
    def _row(name):
        return [(name, "24k", "10000000", "20000000", "4322", "17/06/2026 15:38")]

    def _buy(name):
        return BTMCGoldSource(
            http_get=_static_get(_btmc_json(rows=_row(name)))
        ).get_quotes()[0].buy

    _PER_GRAM = 1000.0 / 37.5  # 1000 GRAM = 1 KG in luong

    # No recognized weight unit -> per-chi default; "VANG" must NOT trigger the bare 'g' unit.
    assert _buy("VANG TESTCO") == pytest.approx(100_000_000.0)              # /0.1 luong
    # Canonical positive weights scaled to per-luong.
    assert _buy("VANG TESTCO 5 LUONG") == pytest.approx(10_000_000.0 / 5.0)
    assert _buy("VANG TESTCO 1 KG") == pytest.approx(10_000_000.0 / _PER_GRAM)
    assert _buy("VANG TESTCO 1000 GRAM") == pytest.approx(10_000_000.0 / _PER_GRAM)
    assert _buy("VANG TESTCO 1000 G") == pytest.approx(10_000_000.0 / _PER_GRAM)
    assert _buy("VANG TESTCO 1 CHI") == pytest.approx(100_000_000.0)        # 1 chi = 0.1 luong
    assert _buy("VANG TESTCO 0.5 LUONG") == pytest.approx(10_000_000.0 / 0.5)  # fractional ok

    for bad in (
        "VANG TESTCO 0 LUONG", "VANG TESTCO 0 KG", "VANG TESTCO 0 GRAM", "VANG TESTCO 0 CHI",
        "VANG TESTCO 0 G",
        "VANG TESTCO 00 LUONG", "VANG TESTCO 05 LUONG",   # leading-zero integer
        "VANG TESTCO -5 LUONG", "VANG TESTCO .5 LUONG",   # signed / partial decimal
        "VANG TESTCO -5 G", "VANG TESTCO .5 G",
    ):
        with pytest.raises(InvalidData):
            _buy(bad)


def test_btmc_same_timestamp_conflict_is_order_independent():
    # Issue #117: two rows with the same product identity and same @d_N timestamp but different
    # prices must raise InvalidData regardless of provider row order — not silently take the last
    # row. Identical same-ts duplicates dedupe; older→newer keeps the newer snapshot.
    def _rows(a, b):
        return [
            ("VANG TESTCO", "24k", a[0], a[1], "4322", a[2]),
            ("VANG TESTCO", "24k", b[0], b[1], "4322", b[2]),
        ]

    def _quotes(a, b):
        return BTMCGoldSource(http_get=_static_get(_btmc_json(rows=_rows(a, b)))).get_quotes()

    TS = "17/06/2026 15:38"
    # Conflicting prices at the same timestamp -> raise in BOTH orders (order-independent).
    a = ("10000000", "20000000", TS)
    b = ("11000000", "21000000", TS)
    for first, second in ((a, b), (b, a)):
        with pytest.raises(InvalidData):
            _quotes(first, second)

    # Identical duplicate at the same timestamp -> dedupe to a single quote (keep-first).
    out = _quotes(a, a)
    assert len(out) == 1
    assert out[0].buy == pytest.approx(100_000_000.0)

    # Older/newer is order-independent: newer snapshot wins in BOTH row orders (the strict-older
    # branch must ignore an older row that arrives after a newer one).
    older = ("10000000", "20000000", "17/06/2026 13:38")
    for first, second in ((older, b), (b, older)):
        out2 = _quotes(first, second)
        assert len(out2) == 1
        assert out2[0].time.hour == 15
        assert out2[0].buy == pytest.approx(110_000_000.0)

    # Same product + same timestamp + same prices but conflicting karat is also inconsistent
    # provider data -> InvalidData (the karat part of the identity must not regress silently).
    karat_rows = [
        ("VANG TESTCO", "24k", "10000000", "20000000", "4322", TS),
        ("VANG TESTCO", "18k", "10000000", "20000000", "4322", TS),
    ]
    with pytest.raises(InvalidData):
        BTMCGoldSource(http_get=_static_get(_btmc_json(rows=karat_rows))).get_quotes()


def test_btmc_rejects_malformed_row_index():
    # Issue #118: a present @row must be a canonical positive index. Malformed values must raise
    # InvalidData rather than being str()'d into a field-lookup suffix. Fallback @n_N discovery
    # stays only when @row is absent/empty, and the discovered suffix must also be canonical.
    def _fields(suffix):
        return {
            f"@n_{suffix}": "VANG TESTCO",
            f"@k_{suffix}": "24k",
            f"@pb_{suffix}": "10000000",
            f"@ps_{suffix}": "20000000",
            f"@d_{suffix}": "17/06/2026 15:38",
        }

    def _quotes(row):
        body = json.dumps({"DataList": {"Data": [row]}})
        return BTMCGoldSource(http_get=_static_get(body)).get_quotes()

    # Canonical @row accepted (string digits and plain int).
    for idx in ("1", 1):
        assert _quotes({"@row": idx, **_fields("1")})[0].product == "VANG TESTCO"

    # Absent or empty @row -> fallback discovery off a canonical @n_N suffix.
    assert _quotes(_fields("1"))[0].product == "VANG TESTCO"
    assert _quotes({"@row": "", **_fields("1")})[0].product == "VANG TESTCO"

    # Present-malformed @row -> InvalidData. Each crafts matching suffixed fields so only the
    # index guard (not a missing-field error) can reject it.
    for idx in (1.0, True, "01", " 1 ", "  ", "x", "0", "-1", -1, 0, [1], {"i": 1}):
        row = {"@row": idx, **_fields(str(idx))}
        with pytest.raises(InvalidData):
            _quotes(row)

    # Fallback path with a non-canonical @n_N suffix must also raise.
    with pytest.raises(InvalidData):
        _quotes(_fields("01"))


def test_btmc_parses_dd_mm_yyyy_timestamp_as_vn_tz():
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    q = next(q for q in s.get_quotes() if "TESTCO" in q.product)
    # 17/06/2026 15:38 Asia/Ho_Chi_Minh (+07)
    assert q.time.utcoffset().total_seconds() == 7 * 3600
    assert q.time.date() == date(2026, 6, 17)
    assert (q.time.hour, q.time.minute) == (15, 38)


def test_btmc_rejects_noncanonical_timestamp():
    # Issue #114: @d_N is contracted as DD/MM/YYYY HH:MM. Non-canonical padding or a
    # different timestamp shape must raise stable InvalidData at the parser boundary
    # instead of being normalized into a plausible GoldQuote.time.
    def _row(ts):
        return [("VÀNG TESTCO", "24k", "10000000", "20000000", "4322", ts)]

    ok = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=_row("17/06/2026 15:38"))))
    q = ok.get_quotes()[0]
    assert q.time.isoformat() == "2026-06-17T15:38:00+07:00"

    for bad in (
        "1/1/2026 9:00",
        "01/1/2026 09:00",
        "1/01/2026 09:00",
        "17/06/2026 5:08",
        "2026-06-17T15:38:00",
        "not-a-date",
        "99/99/2026 99:99",  # right shape, impossible values -> strptime still rejects
        "",                  # missing/blank @d_N
        " 17/06/2026 15:38",   # leading space -> not the exact contracted shape
        "17/06/2026 15:38 ",   # trailing space
        "\t17/06/2026 15:38",  # leading tab
        "17/06/2026 15:38\n",  # trailing newline
    ):
        src = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=_row(bad))))
        with pytest.raises(InvalidData):
            src.get_quotes()


def test_btmc_get_quote_by_product_substring():
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    q = s.get_quote("testco")  # case-insensitive substring
    assert "TESTCO" in q.product


def test_btmc_no_match_raises_empty():
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    with pytest.raises(EmptyData):
        s.get_quote("DOES_NOT_EXIST")


@pytest.mark.parametrize("bad_product", ["", "   ", "\t", None])
def test_btmc_empty_product_selector_raises_vnfin_error(bad_product):
    s = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    with pytest.raises(VnfinError):
        s.get_quote(bad_product)


def test_btmc_empty_datalist_raises_empty():
    s = BTMCGoldSource(http_get=_static_get(json.dumps({"DataList": {"Data": []}})))
    with pytest.raises(EmptyData):
        s.get_quotes()


def test_btmc_only_silver_raises_empty():
    # a feed with no gold rows (all silver) yields no quotes -> EmptyData
    rows = [
        ("BẠC MIẾNG FAKE1 Ag 999 1 LƯỢNG (FAKE1)", "", "2000000", "3000000", "4322", "17/06/2026 15:38"),
    ]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=rows)))
    with pytest.raises(EmptyData):
        s.get_quotes()


def test_btmc_malformed_price_raises_invalid():
    bad = [("VÀNG MIẾNG TESTCO", "24k", "not-a-number", "20000000", "4322", "17/06/2026 15:38")]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=bad)))
    with pytest.raises(InvalidData):
        s.get_quotes()


@pytest.mark.parametrize(
    "name",
    [["BAD"], {"name": "BAD"}, 123, True],
    ids=["list", "dict", "int", "bool"],
)
def test_btmc_malformed_product_name_raises_invalid(name):
    rows = [(name, "24k", "10000000", "20000000", "4322", "17/06/2026 15:38")]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=rows)))
    with pytest.raises(InvalidData, match="product name"):
        s.get_quotes()


@pytest.mark.parametrize(
    "karat",
    [["24k"], {"k": "24k"}, 24, True],
    ids=["list", "dict", "int", "bool"],
)
def test_btmc_malformed_karat_raises_invalid(karat):
    rows = [("VÀNG MIẾNG TESTCO (Vàng TESTCO)", karat, "10000000", "20000000", "4322", "17/06/2026 15:38")]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=rows)))
    with pytest.raises(InvalidData, match="karat"):
        s.get_quotes()


def test_btmc_negative_price_raises_invalid():
    bad = [("VÀNG MIẾNG TESTCO", "24k", "-5", "20000000", "4322", "17/06/2026 15:38")]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=bad)))
    with pytest.raises(InvalidData):
        s.get_quotes()


@pytest.mark.parametrize(
    "buy,sell",
    [(True, "20000000"), ("10000000", True), (True, True)],
    ids=["bool_buy", "bool_sell", "bool_both"],
)
def test_btmc_boolean_price_raises_invalid(buy, sell):
    # Issue #87: JSON booleans must not coerce into positive-looking VND prices.
    bad = [("VÀNG MIẾNG TESTCO", "24k", buy, sell, "4322", "17/06/2026 15:38")]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=bad)))
    with pytest.raises(InvalidData, match="bool"):
        s.get_quotes()


def test_btmc_bad_timestamp_raises_invalid():
    bad = [("VÀNG MIẾNG TESTCO", "24k", "10000000", "20000000", "4322", "garbage-time")]
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
# PNJ (VN domestic, THOUSAND-VND/chỉ -> canonical VND/lượng = x1000 x10)       #
# --------------------------------------------------------------------------- #


def test_pnj_scales_thousand_vnd_chi_to_vnd_luong():
    s = PNJGoldSource(http_get=_static_get(_pnj_json()))
    quotes = s.get_quotes()
    testco = next(q for q in quotes if q.product == "TESTCO" or "TESTCO" in q.product)
    # giaban 20000 (thousand VND/chỉ) -> 20,000,000 VND/chỉ -> 200,000,000 VND/lượng
    assert testco.sell == pytest.approx(200_000_000.0)
    assert testco.buy == pytest.approx(100_000_000.0)
    assert testco.currency == "VND"
    assert testco.unit == "VND/luong"
    assert testco.source == "pnj"


def test_pnj_uses_same_canonical_unit_as_btmc():
    # Cross-source parity at the unit level: identical synthetic per-chỉ tick must yield
    # identical canonical VND/lượng numbers from both dealers.
    btmc = BTMCGoldSource(http_get=_static_get(_btmc_json()))
    pnj = PNJGoldSource(http_get=_static_get(_pnj_json()))
    b = next(q for q in btmc.get_quotes() if "TESTCO" in q.product)
    p = next(q for q in pnj.get_quotes() if "TESTCO" in q.product)
    assert b.unit == p.unit == "VND/luong"
    assert b.buy == pytest.approx(p.buy)
    assert b.sell == pytest.approx(p.sell)


def test_pnj_skips_blank_buy_only_rows():
    # Real feed includes RAW_* "raw gold purchase" rows where giaban (sell) is "" because
    # PNJ buys but does not sell that grade. Those rows must be skipped, not fail the feed.
    rows = [
        ("TESTCO", "Vàng miếng TESTCO 999.9", 20000, 10000),
        ("RAW_9999", "Vàng nguyên liệu mua ngoài 99.99", "", 9000),
        ("RAW_9900", "Vàng nguyên liệu mua ngoài 99", "", 8000),
    ]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows)))
    quotes = s.get_quotes()
    assert len(quotes) == 1
    assert quotes[0].product == "TESTCO"


def test_pnj_all_rows_blank_raises_empty():
    rows = [("RAW_9999", "Vàng nguyên liệu mua ngoài", "", 9000)]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows)))
    with pytest.raises(EmptyData):
        s.get_quotes()


def test_pnj_empty_data_raises_empty():
    s = PNJGoldSource(http_get=_static_get(json.dumps({"data": []})))
    with pytest.raises(EmptyData):
        s.get_quotes()


@pytest.mark.parametrize("bad_product", ["", "   ", "\t", None])
def test_pnj_empty_product_selector_raises_vnfin_error(bad_product):
    s = PNJGoldSource(http_get=_static_get(_pnj_json()))
    with pytest.raises(VnfinError):
        s.get_quote(bad_product)


def test_pnj_malformed_price_raises_invalid():
    bad = [("TESTCO", "Vàng miếng TESTCO 999.9", "oops", 10000)]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=bad)))
    with pytest.raises(InvalidData):
        s.get_quotes()


def test_pnj_negative_price_raises_invalid():
    bad = [("TESTCO", "Vàng miếng TESTCO 999.9", -1, 10000)]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=bad)))
    with pytest.raises(InvalidData):
        s.get_quotes()


@pytest.mark.parametrize(
    "giamua,giaban",
    [(True, 10000), (20000, True), (True, True)],
    ids=["bool_buy", "bool_sell", "bool_both"],
)
def test_pnj_boolean_price_raises_invalid(giamua, giaban):
    # Issue #87: JSON booleans must not coerce into positive-looking VND prices.
    bad = [("TESTCO", "Vàng miếng TESTCO 999.9", giaban, giamua)]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=bad)))
    with pytest.raises(InvalidData, match="bool"):
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


@pytest.mark.parametrize(
    "bad_ts",
    ["2026-06-17", "2024-1-1T00:00:00Z", "2024-01-1T00:00:00Z", "2024-1-01T00:00:00Z"],
    ids=["date_only", "compact_month_day", "compact_day", "compact_month"],
)
def test_goldapi_rejects_non_timestamp_updatedat(bad_ts):
    # Issue #112: datetime.fromisoformat is lenient on Python 3.11+; require full timestamp.
    s = GoldApiSource(http_get=_static_get(_goldapi_json(updated=bad_ts)))
    with pytest.raises(InvalidData, match="updatedAt"):
        s.get_quote()


def test_goldapi_silver_symbol():
    s = GoldApiSource(http_get=_static_get(_goldapi_json(price=71.48, symbol="XAG")), symbol="XAG")
    q = s.get_quote()
    assert q.product == "XAG"
    assert q.sell == pytest.approx(71.48)


# --------------------------------------------------------------------------- #
# Issue #21 (reopen) — gold-api returned symbol identity must match the request #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "req,payload",
    [("XAU", "XAG"), ("XAG", "XAU")],
    ids=["xau_req_xag_payload", "xag_req_xau_payload"],
)
def test_goldapi_rejects_mismatched_payload_symbol(req, payload):
    s = GoldApiSource(http_get=_static_get(_goldapi_json(symbol=payload)), symbol=req)
    with pytest.raises(InvalidData, match="returned symbol"):
        s.get_quote()


@pytest.mark.parametrize("bad", [123, [], {}, ""], ids=["int", "list", "dict", "blank"])
def test_goldapi_rejects_nonstring_payload_symbol(bad):
    s = GoldApiSource(http_get=_static_get(_goldapi_json(symbol=bad)), symbol="XAU")
    with pytest.raises(InvalidData, match="returned symbol"):
        s.get_quote()


def test_goldapi_uses_requested_symbol_as_product_case_insensitive():
    # A present lowercase payload symbol matches case-insensitively; product is the
    # validated requested symbol, never the trusted payload value.
    s = GoldApiSource(http_get=_static_get(_goldapi_json(symbol="xau")), symbol="XAU")
    assert s.get_quote().product == "XAU"


def test_goldapi_absent_payload_symbol_uses_requested():
    s = GoldApiSource(http_get=_static_get(_goldapi_json(symbol=None)), symbol="XAU")
    assert s.get_quote().product == "XAU"


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


# --- Issue #52: GoldApiSource symbol input validation -------------------------

@pytest.mark.parametrize("bad_symbol", [None, 123, b"XAU", "", "   "])
def test_goldapi_invalid_symbol_raises_vnfin_error(bad_symbol):
    with pytest.raises(VnfinError):
        GoldApiSource(http_get=_static_get(_goldapi_json()), symbol=bad_symbol)


def test_goldapi_symbol_is_normalized_uppercase():
    s = GoldApiSource(http_get=_static_get(_goldapi_json()), symbol="  xau  ")
    assert s.symbol == "XAU"


def test_goldapi_invalid_symbol_does_not_call_network():
    called = {"n": 0}

    def _g(url, params=None, headers=None):
        called["n"] += 1
        return _goldapi_json()

    with pytest.raises(VnfinError):
        GoldApiSource(http_get=_g, symbol="")
    assert called["n"] == 0


# --- Issue #52 follow-up: only XAU/XAG are supported world spot symbols ------

@pytest.mark.parametrize("bad_symbol", ["BTC", "USD", "XAU/USD", "SILVER"])
def test_goldapi_unsupported_symbol_raises_before_network(bad_symbol):
    called = {"n": 0}

    def _g(url, params=None, headers=None):
        called["n"] += 1
        return _goldapi_json()

    with pytest.raises(VnfinError):
        GoldApiSource(http_get=_g, symbol=bad_symbol)
    assert called["n"] == 0


def test_goldapi_xag_supported():
    s = GoldApiSource(http_get=_static_get(_goldapi_json()), symbol="  xag  ")
    assert s.symbol == "XAG"


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


# --- Issue #42: world-gold history must validate date bounds ---------------------

@pytest.mark.parametrize("bad_start", [None, "2024-01-01", 12345])
def test_currencyapi_invalid_start_date_raises_vnfin_error(bad_start):
    s = CurrencyApiGoldSource(http_get=_static_get("{}"))
    with pytest.raises(VnfinError):
        s.get_history(bad_start, date(2024, 1, 1))


@pytest.mark.parametrize("bad_end", [None, "2024-01-01", 12345])
def test_currencyapi_invalid_end_date_raises_vnfin_error(bad_end):
    s = CurrencyApiGoldSource(http_get=_static_get("{}"))
    with pytest.raises(VnfinError):
        s.get_history(date(2024, 1, 1), bad_end)


@pytest.mark.parametrize("bad_start", [None, "2024-01-01"])
def test_stooq_invalid_start_date_raises_vnfin_error(bad_start):
    csv = "Date,Open,High,Low,Close,Volume\n2024-01-01,2000,2100,1900,2050,0\n"
    s = StooqGoldSource(http_get=_static_get(csv))
    with pytest.raises(VnfinError):
        s.get_history(bad_start, date(2024, 1, 1))


def test_default_world_gold_client_invalid_bounds_raises_vnfin_error():
    from vnfin.gold import default_world_gold_client

    sources = [
        CurrencyApiGoldSource(http_get=_static_get("{}")),
        StooqGoldSource(http_get=_static_get("Date,Open,High,Low,Close,Volume\n2024-01-01,2000,2100,1900,2050,0\n")),
    ]
    with pytest.raises(VnfinError):
        default_world_gold_client(sources=sources).get_history(None, date(2024, 1, 1))


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


# --------------------------------------------------------------------------- #
# Regression — issue #35: date-pinned history documents must match the requested
# date; otherwise the wrong date is stamped onto the price.
# --------------------------------------------------------------------------- #
def test_currencyapi_history_rejects_mismatched_document_date():
    # Document says 2024-01-03 but we requested 2024-01-01 -> data integrity error.
    payload = json.dumps({"date": "2024-01-03", "usd": {"xau": 0.0005}})
    s = CurrencyApiGoldSource(http_get=lambda *a: payload)
    with pytest.raises(InvalidData):
        s.get_history(date(2024, 1, 1), date(2024, 1, 1))


def test_currencyapi_history_uses_requested_date_when_doc_date_missing():
    # Document omits date -> fall back to the requested loop date.
    payload = json.dumps({"usd": {"xau": 0.0005}})
    s = CurrencyApiGoldSource(http_get=lambda *a: payload)
    hist = s.get_history(date(2024, 1, 1), date(2024, 1, 1))
    assert len(hist) == 1
    assert hist.bars[0].date == date(2024, 1, 1)
    assert hist.bars[0].price == pytest.approx(2000.0)


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


# --------------------------------------------------------------------------- #
# Batch 8 — gold spot validation + reversed windows (#15 #12 #6)
# --------------------------------------------------------------------------- #


def test_btmc_skips_reversed_buy_sell_spread():
    # TESTCO is normal; FAKE has sell < buy (negative spread). FAKE must not be emitted.
    rows = [
        ("VÀNG MIẾNG TESTCO (Vàng TESTCO)", "24k", "10000000", "20000000", "4322", "17/06/2026 15:38"),
        ("VÀNG MIẾNG FAKE (Vàng FAKE)", "24k", "20000000", "10000000", "4322", "17/06/2026 15:38"),
    ]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=rows)))
    quotes = s.get_quotes()
    assert len(quotes) == 1
    assert "FAKE" not in quotes[0].product
    assert "TESTCO" in quotes[0].product


def test_pnj_skips_reversed_buy_sell_spread():
    rows = [
        ("TESTCO", "Vàng miếng TESTCO 999.9", 20000, 10000),
        ("FAKE", "Vàng miếng FAKE 999.9", 10000, 20000),
    ]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows)))
    quotes = s.get_quotes()
    assert len(quotes) == 1
    assert quotes[0].product == "TESTCO"


def test_goldapi_zero_price_rejected():
    s = GoldApiSource(http_get=_static_get(_goldapi_json(price=0.0)))
    with pytest.raises(InvalidData):
        s.get_quote()


def test_goldapi_non_usd_currency_rejected():
    payload = json.dumps(
        {
            "currency": "EUR",
            "currencySymbol": "€",
            "exchangeRate": 1.0,
            "name": "Gold",
            "price": 4296.9,
            "symbol": "XAU",
            "updatedAt": "2026-06-17T18:10:08Z",
        }
    )
    s = GoldApiSource(http_get=_static_get(payload))
    with pytest.raises(InvalidData):
        s.get_quote()


def test_currencyapi_reversed_date_range_raises_invalid():
    s = CurrencyApiGoldSource(http_get=_static_get("{}"))
    with pytest.raises(InvalidData):
        s.get_history(date(2026, 6, 17), date(2026, 6, 15))


def test_stooq_reversed_date_range_raises_invalid():
    csv = "Date,Open,High,Low,Close,Volume\n2026-06-15,4000.0,4050.0,3990.0,4010.0,0\n"
    s = StooqGoldSource(http_get=_static_get(csv))
    with pytest.raises(InvalidData):
        s.get_history(date(2026, 6, 17), date(2026, 6, 15))


# --- Issue #80: gold factory selectors reject malformed input ----------------


@pytest.mark.parametrize("bad", [None, 123, "", "   "])
def test_vn_factory_rejects_malformed_provider(bad):
    from vnfin.gold import vn

    with pytest.raises(ValueError):
        vn(bad)


@pytest.mark.parametrize("bad", [None, 123, "", "   "])
def test_world_factory_rejects_malformed_provider(bad):
    from vnfin.gold import world

    with pytest.raises(ValueError):
        world(bad)


@pytest.mark.parametrize("bad", [None, 123, "", "   ", "unknown"])
def test_source_factory_rejects_malformed_or_unknown_provider(bad):
    from vnfin.gold import source

    with pytest.raises(ValueError):
        source(bad)


def test_vn_factory_unknown_provider_lists_valid():
    from vnfin.gold import vn

    with pytest.raises(ValueError, match="btmc|pnj"):
        vn("weird")


# --------------------------------------------------------------------------- #
# Regression — issue #15: GoldQuote hard-rejects invalid spreads/prices       #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "buy,sell",
    [
        (2.0, 1.0),  # negative spread
        (0.0, 1.0),
        (1.0, 0.0),
        (-1.0, 1.0),
        (1.0, -1.0),
    ],
)
def test_goldquote_rejects_non_positive_or_negative_spread(buy, sell):
    with pytest.raises(InvalidData):
        GoldQuote(
            time=datetime(2026, 6, 17, tzinfo=timezone.utc),
            product="X",
            buy=buy,
            sell=sell,
            unit="USD/oz",
            currency="USD",
            source="test",
            fetched_at_utc=datetime.now(timezone.utc),
        )


@pytest.mark.parametrize(
    "buy,sell",
    [(True, 1.0), (1.0, True), (True, True)],
    ids=["bool_buy", "bool_sell", "bool_both"],
)
def test_goldquote_rejects_boolean_prices(buy, sell):
    # bool is a subclass of int and must not be accepted as a numeric price.
    with pytest.raises(InvalidData, match="bool"):
        GoldQuote(
            time=datetime(2026, 6, 17, tzinfo=timezone.utc),
            product="X",
            buy=buy,
            sell=sell,
            unit="USD/oz",
            currency="USD",
            source="test",
            fetched_at_utc=datetime.now(timezone.utc),
        )


@pytest.mark.parametrize(
    "buy,sell",
    [
        (float("nan"), 1.0),
        (1.0, float("nan")),
        (float("inf"), 1.0),
        (1.0, float("inf")),
    ],
)
def test_goldquote_rejects_non_finite_prices(buy, sell):
    with pytest.raises(InvalidData):
        GoldQuote(
            time=datetime(2026, 6, 17, tzinfo=timezone.utc),
            product="X",
            buy=buy,
            sell=sell,
            unit="USD/oz",
            currency="USD",
            source="test",
            fetched_at_utc=datetime.now(timezone.utc),
        )


# Regression — issue #15: adapters must not emit rows with invalid prices/spreads


def test_btmc_skips_zero_priced_rows():
    rows = [
        ("VÀNG MIẾNG ZERO (Vàng ZERO)", "24k", "0", "0", "4322", "17/06/2026 15:38"),
    ]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=rows)))
    with pytest.raises(EmptyData):
        s.get_quotes()


def test_btmc_rejects_non_finite_price():
    bad = [("VÀNG MIẾNG BAD", "24k", "NaN", "20000000", "4322", "17/06/2026 15:38")]
    s = BTMCGoldSource(http_get=_static_get(_btmc_json(rows=bad)))
    with pytest.raises(InvalidData):
        s.get_quotes()


def test_pnj_skips_zero_priced_rows():
    rows = [("ZERO", "Vàng miếng ZERO 999.9", 0, 0)]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows)))
    with pytest.raises(EmptyData):
        s.get_quotes()


def test_pnj_rejects_non_finite_price():
    bad = [("BAD", "Vàng miếng BAD 999.9", float("nan"), 10000)]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=bad)))
    with pytest.raises(InvalidData):
        s.get_quotes()


# --------------------------------------------------------------------------- #
# Regression — issue #67: PNJ product keys must be non-empty, unique strings   #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "masp,tensp",
    [
        (None, None),
        ("", ""),
        ("   ", "   "),
        (123, None),
        (None, 456),
    ],
    ids=[
        "both_none",
        "both_empty",
        "both_whitespace",
        "masp_int_no_fallback",
        "fallback_int",
    ],
)
def test_pnj_rejects_missing_or_non_string_product_key(masp, tensp):
    rows = [(masp, tensp, 20000, 10000)]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows)))
    # #143: a present non-string tensp now fails closed earlier ("tensp is not a
    # string"); a truly missing product key still raises "row missing product key".
    with pytest.raises(InvalidData, match="product key|tensp is not a string"):
        s.get_quotes()


def test_pnj_rejects_duplicate_normalized_product_keys():
    rows = [
        ("TESTCO", "Vàng miếng TESTCO 999.9", 20000, 10000),
        ("testco", "Nhẫn TESTCO 999.9", 19000, 9000),
    ]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows)))
    with pytest.raises(InvalidData, match="duplicate product key"):
        s.get_quotes()


# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Regression — issue #110: currency-api must reject malformed document dates
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("bad_date", ["2024-1-1", "2024-01-1", "2024-1-01"])
def test_currencyapi_doc_date_rejects_non_zero_padded_dates(bad_date):
    s = CurrencyApiGoldSource(http_get=_static_get("{}"))
    with pytest.raises(InvalidData, match="malformed date"):
        s._doc_date({"date": bad_date})


@pytest.mark.parametrize("bad_date", ["2024-1-1", "2024-01-1", "2024-1-01"])
def test_currencyapi_get_quote_rejects_malformed_doc_date(bad_date):
    s = CurrencyApiGoldSource(http_get=_static_get(_currency_usd_json(d=bad_date)))
    with pytest.raises(InvalidData, match="malformed date"):
        s.get_quote()


@pytest.mark.parametrize("bad_date", ["2024-1-1", "2024-01-1", "2024-1-01"])
def test_currencyapi_history_rejects_malformed_doc_date(bad_date):
    def _g(url, params=None, headers=None):
        return _currency_usd_json(d=bad_date)

    s = CurrencyApiGoldSource(http_get=_g)
    with pytest.raises(InvalidData, match="malformed date"):
        s.get_history(date(2024, 1, 1), date(2024, 1, 1))


@pytest.mark.parametrize("bad", [False, 0, "", [], {}], ids=["false", "zero", "blank", "list", "dict"])
def test_currencyapi_history_rejects_present_falsey_doc_date(bad):
    # Issue #35 (reopen): a PRESENT falsey/non-string `date` is corrupted provider
    # identity and must raise, not be silently relabeled with the requested date.
    s = CurrencyApiGoldSource(http_get=_static_get(_currency_usd_json(d=bad)))
    with pytest.raises(InvalidData, match="malformed date"):
        s.get_history(date(2024, 1, 1), date(2024, 1, 1))


def test_currencyapi_history_absent_doc_date_falls_back_to_requested():
    # A truly absent/null `date` keeps the documented fallback to the loop date.
    def _g(url, params=None, headers=None):
        return json.dumps({"usd": {"eur": 0.86, "vnd": 26000.0, "xau": 0.000231}})

    s = CurrencyApiGoldSource(http_get=_g)
    hist = s.get_history(date(2024, 1, 1), date(2024, 1, 1))
    assert hist.bars[0].date == date(2024, 1, 1)


# Regression — issue #35: currency-api history document date identity          #
# --------------------------------------------------------------------------- #


def test_currencyapi_history_rejects_mismatched_document_date_among_valid_dates():
    # One document in the middle of the range carries the wrong date -> integrity error.
    by_date = {
        "2026-06-15": _currency_usd_json(d="2026-06-15", usd_xau=0.000231),
        "2026-06-16": _currency_usd_json(d="2026-06-15", usd_xau=0.0002312),
        "2026-06-17": _currency_usd_json(d="2026-06-17", usd_xau=0.0002313114),
    }

    def _g(url, params=None, headers=None):
        for d, body in by_date.items():
            if d in url:
                return body
        raise FileNotFoundError("404")

    s = CurrencyApiGoldSource(http_get=_g)
    with pytest.raises(InvalidData, match="document date"):
        s.get_history(date(2026, 6, 15), date(2026, 6, 17))


# --------------------------------------------------------------------------- #
# Issue #112 (reopen) — gold-api present-but-falsey updatedAt must NOT fall back
# to now(); only absent/null falls back.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad", [False, 0, "", [], {}, "not-a-timestamp"], ids=["false", "zero", "blank", "list", "dict", "garbage"])
def test_goldapi_rejects_present_falsey_updated_at(bad):
    s = GoldApiSource(http_get=_static_get(_goldapi_json(updated=bad)), symbol="XAU")
    with pytest.raises(InvalidData, match="updatedAt"):
        s.get_quote()


def test_goldapi_absent_updated_at_falls_back_to_now():
    s = GoldApiSource(http_get=_static_get(_goldapi_json(updated=None)), symbol="XAU")
    q = s.get_quote()
    assert q.time.tzinfo is not None
    assert abs((datetime.now(timezone.utc) - q.time).total_seconds()) < 300


# Issue #143 — PNJ must classify silver by BOTH masp code and descriptive tensp name.
def test_pnj_silver_named_row_with_gold_code_excluded_all_silver_empty():
    # masp code carries NO 'bạc' marker, but the tensp NAME does -> must be excluded;
    # an all-silver feed yields EmptyData (not a misclassified gold quote).
    rows = [("AG999", "Bạc PNJ 999.9", 20000, 10000)]
    s = PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows)))
    with pytest.raises(EmptyData):
        s.get_quotes()


def test_pnj_mixed_silver_and_gold_returns_only_gold():
    rows = [
        ("TESTCO", "Vàng miếng TESTCO 999.9", 20000, 10000),  # gold
        ("AG999", "Bạc PNJ 999.9", 21000, 11000),             # silver by name only
    ]
    quotes = PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows))).get_quotes()
    assert [q.product for q in quotes] == ["TESTCO"]


def test_pnj_silver_by_code_marker_excluded():
    # control: a 'bac' marker in the masp code still excludes (all-silver -> EmptyData).
    rows = [("BAC999", "Trang sức 999.9", 20000, 10000)]
    with pytest.raises(EmptyData):
        PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows))).get_quotes()


def test_pnj_silver_row_with_malformed_price_is_skipped_not_fatal():
    # silver exclusion happens BEFORE price parsing, so a silver row's garbage price
    # is skipped, not a fatal InvalidData; the gold row still returns.
    rows = [
        ("AG999", "Bạc PNJ 999.9", "garbage", "garbage"),     # silver + bad price
        ("TESTCO", "Vàng miếng TESTCO 999.9", 20000, 10000),  # gold
    ]
    quotes = PNJGoldSource(http_get=_static_get(_pnj_json(rows=rows))).get_quotes()
    assert [q.product for q in quotes] == ["TESTCO"]
