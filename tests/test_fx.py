"""FX domain tests — daily/current VND rates from no-key sources (synthetic fixtures only).

Sources: open.er-api.com (primary, JSON) and Vietcombank XML (failover). Both are normalized
to the canonical unit **VND per 1 unit of the base currency**. Fixtures use obviously-fake
round numbers (USD/VND = 25,000) so no real provider snapshot is committed.
"""
from __future__ import annotations

import datetime as dt
import pathlib

import pytest

from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable, UnitMismatchError
from vnfin.fx import (
    FailoverFXClient,
    FXRate,
    OpenErApiFXSource,
    VietcombankFXSource,
    client,
    default_fx_client,
    default_fx_sources,
    get_rate,
    source,
)

_FIX = pathlib.Path(__file__).parent / "fixtures" / "fx"
_OPEN_ER = (_FIX / "open_er_api_usd.json").read_text()
_VCB_XML = (_FIX / "vietcombank.xml").read_text()
_NOW = dt.datetime(2026, 6, 18, 3, 0, 0, tzinfo=dt.timezone.utc)


def _http(text):
    """An http_get stub returning fixed text regardless of url/params/headers."""
    def _get(url, params=None, headers=None, json_body=None):
        return text
    return _get


def _raise(exc):
    def _get(url, params=None, headers=None, json_body=None):
        raise exc
    return _get


# --------------------------------------------------------------------------- #
# open.er-api source
# --------------------------------------------------------------------------- #
def test_open_er_api_usd_vnd():
    src = OpenErApiFXSource(http_get=_http(_OPEN_ER))
    r = src.get_rate("USD")
    assert isinstance(r, FXRate)
    assert r.base == "USD" and r.quote == "VND"
    assert r.rate == pytest.approx(25000.0)
    assert r.unit == "VND per 1 USD"
    assert r.source == "open_er_api"
    assert r.as_of_utc.tzinfo is not None


def test_open_er_api_cross_rate_eur_vnd():
    # EUR/VND = (VND per USD) / (EUR per USD) = 25000 / 0.9
    src = OpenErApiFXSource(http_get=_http(_OPEN_ER))
    r = src.get_rate("EUR")
    assert r.base == "EUR"
    assert r.rate == pytest.approx(25000.0 / 0.9)
    assert r.unit == "VND per 1 EUR"


def test_open_er_api_get_rates_excludes_vnd_itself():
    src = OpenErApiFXSource(http_get=_http(_OPEN_ER))
    rates = src.get_rates()
    bases = {r.base for r in rates}
    assert "VND" not in bases
    assert {"USD", "EUR", "CNY", "JPY"} <= bases
    assert all(r.quote == "VND" and r.rate > 0 for r in rates)


def test_open_er_api_lowercase_base_normalized():
    src = OpenErApiFXSource(http_get=_http(_OPEN_ER))
    assert src.get_rate("usd").base == "USD"


def test_open_er_api_unknown_base_is_empty():
    src = OpenErApiFXSource(http_get=_http(_OPEN_ER))
    with pytest.raises(EmptyData):
        src.get_rate("ZZZ")


def test_open_er_api_error_result_is_source_error():
    bad = '{"result": "error", "error-type": "unsupported-code"}'
    src = OpenErApiFXSource(http_get=_http(bad))
    with pytest.raises((EmptyData, InvalidData)):
        src.get_rate("USD")


def test_open_er_api_missing_vnd_anchor_is_invalid():
    bad = '{"result": "success", "base_code": "USD", "rates": {"USD": 1, "EUR": 0.9}}'
    src = OpenErApiFXSource(http_get=_http(bad))
    with pytest.raises(InvalidData):
        src.get_rate("EUR")


def test_open_er_api_bool_vnd_anchor_is_invalid():
    # Issue #87: JSON booleans must not become FX rates.
    bad = '{"result": "success", "base_code": "USD", "rates": {"VND": true, "USD": 1, "EUR": 0.9}}'
    src = OpenErApiFXSource(http_get=_http(bad))
    with pytest.raises(InvalidData):
        src.get_rates()


def test_open_er_api_drifted_usd_self_rate_is_invalid():
    # Issue #93: USD-base payloads must carry rates["USD"] == 1.
    bad = (
        '{"result": "success", "base_code": "USD", "time_last_update_unix": 1781740800, '
        '"rates": {"USD": 2.0, "VND": 25000.0, "EUR": 0.9}}'
    )
    src = OpenErApiFXSource(http_get=_http(bad))
    with pytest.raises(InvalidData, match="USD self-rate"):
        src.get_rates()


def test_open_er_api_unsupported_quote_rejected():
    src = OpenErApiFXSource(http_get=_http(_OPEN_ER))
    with pytest.raises((InvalidData, ValueError)):
        src.get_rate("EUR", quote="USD")


# --------------------------------------------------------------------------- #
# Vietcombank source
# --------------------------------------------------------------------------- #
def test_vietcombank_usd_transfer_with_bid_ask():
    src = VietcombankFXSource(http_get=_http(_VCB_XML))
    r = src.get_rate("USD")
    assert r.base == "USD" and r.quote == "VND"
    assert r.rate == pytest.approx(25000.0)   # Transfer
    assert r.bid == pytest.approx(24900.0)    # Buy
    assert r.ask == pytest.approx(25200.0)    # Sell
    assert r.unit == "VND per 1 USD"
    assert r.source == "vietcombank"


def test_vietcombank_jpy():
    src = VietcombankFXSource(http_get=_http(_VCB_XML))
    assert src.get_rate("JPY").rate == pytest.approx(150.0)


def test_vietcombank_skips_zero_transfer():
    # DKK has Transfer="0.00" -> not a usable VND-per-unit rate -> excluded
    src = VietcombankFXSource(http_get=_http(_VCB_XML))
    assert "DKK" not in {r.base for r in src.get_rates()}


def test_vietcombank_as_of_is_utc_from_vn_local():
    # "6/18/2026 3:53:15 PM" VN local (UTC+7) -> 08:53:15 UTC
    src = VietcombankFXSource(http_get=_http(_VCB_XML))
    r = src.get_rate("USD")
    assert r.as_of_utc == dt.datetime(2026, 6, 18, 8, 53, 15, tzinfo=dt.timezone.utc)


# --- Issue #47: Vietcombank must skip the VND/VND self-rate ----------------------

def test_vietcombank_skips_vnd_self_rate():
    xml = """
    <ExrateList>
      <DateTime>01/02/2024 03:04:05 PM</DateTime>
      <Exrate CurrencyCode="VND" Transfer="1" Buy="1" Sell="1"/>
      <Exrate CurrencyCode="USD" Transfer="25000" Buy="24900" Sell="25100"/>
    </ExrateList>
    """
    src = VietcombankFXSource(http_get=_http(xml), cache_ttl=None)
    rates = src.get_rates()
    bases = {r.base for r in rates}
    assert "VND" not in bases
    assert "USD" in bases


def test_vietcombank_get_rate_vnd_raises_empty():
    xml = """
    <ExrateList>
      <DateTime>01/02/2024 03:04:05 PM</DateTime>
      <Exrate CurrencyCode="VND" Transfer="1" Buy="1" Sell="1"/>
    </ExrateList>
    """
    src = VietcombankFXSource(http_get=_http(xml), cache_ttl=None)
    with pytest.raises(EmptyData):
        src.get_rate("VND")


# --- Issue #43: OpenErApi timestamp overflow must not leak OverflowError ----------

def test_open_er_api_huge_timestamp_falls_back_to_now():
    payload = '{"result":"success","base_code":"USD","time_last_update_unix":1e30,"rates":{"USD":1,"VND":25000}}'
    r = OpenErApiFXSource(http_get=_http(payload)).get_rate("USD")
    assert r.as_of_utc.tzinfo is not None


def test_open_er_api_timestamp_overflow_does_not_crash_get_rates():
    payload = '{"result":"success","base_code":"USD","time_last_update_unix":999999999999999999999999,"rates":{"USD":1,"VND":25000,"EUR":0.9}}'
    rates = OpenErApiFXSource(http_get=_http(payload)).get_rates()
    assert any(r.base == "USD" for r in rates)


def test_open_er_api_negative_timestamp_falls_back_to_now():
    payload = '{"result":"success","base_code":"USD","time_last_update_unix":-1,"rates":{"USD":1,"VND":25000}}'
    r = OpenErApiFXSource(http_get=_http(payload)).get_rate("USD")
    assert r.as_of_utc.tzinfo is not None


def test_vietcombank_malformed_xml_is_invalid():
    src = VietcombankFXSource(http_get=_http("<not-xml<<<"))
    with pytest.raises(InvalidData):
        src.get_rate("USD")


# --------------------------------------------------------------------------- #
# failover client + unit guard
# --------------------------------------------------------------------------- #
class _FakeFX:
    def __init__(self, name, *, unit="VND-per-foreign-unit", rate=25000.0, raises=None, bad_unit=False):
        self.name = name
        self.unit = unit
        self._rate = rate
        self._raises = raises
        self._bad_unit = bad_unit

    def get_rate(self, base, quote="VND"):
        if self._raises is not None:
            raise self._raises
        u = "USD per 1 VND" if self._bad_unit else f"VND per 1 {base}"
        return FXRate(base=base, quote=quote, rate=self._rate, unit=u, as_of_utc=_NOW, source=self.name)


def test_failover_uses_backup_when_primary_unavailable():
    c = FailoverFXClient([_FakeFX("a", raises=SourceUnavailable("down")), _FakeFX("b", rate=26000.0)])
    r = c.get_rate("USD")
    assert r.source == "b" and r.rate == pytest.approx(26000.0)


def test_failover_unit_guard_rejects_mixed_family_at_construction():
    with pytest.raises(UnitMismatchError):
        FailoverFXClient([_FakeFX("a"), _FakeFX("b", unit="POINTS")])


def test_failover_rejects_inverted_result_and_falls_over():
    c = FailoverFXClient([_FakeFX("a", bad_unit=True), _FakeFX("b", rate=26000.0)])
    r = c.get_rate("USD")
    assert r.source == "b"  # 'a' produced an inverted-unit result -> rejected


def test_failover_rejects_non_positive_rate():
    c = FailoverFXClient([_FakeFX("a", rate=0.0), _FakeFX("b", rate=26000.0)])
    assert c.get_rate("USD").source == "b"


def test_failover_rejects_infinite_rate():
    from math import inf

    c = FailoverFXClient([_FakeFX("a", rate=inf), _FakeFX("b", rate=26000.0)])
    assert c.get_rate("USD").source == "b"


def test_failover_rejects_bool_rate():
    c = FailoverFXClient([_FakeFX("a", rate=True), _FakeFX("b", rate=26000.0)])
    assert c.get_rate("USD").source == "b"


# --------------------------------------------------------------------------- #
# real-source failover + facade
# --------------------------------------------------------------------------- #
def test_default_chain_open_er_then_vietcombank():
    sources = default_fx_sources(http_get=_http(_OPEN_ER))
    assert [s.name for s in sources] == ["open_er_api", "vietcombank"]


def test_facade_client_and_source_types():
    assert isinstance(source(http_get=_http(_OPEN_ER)), OpenErApiFXSource)
    assert isinstance(client(http_get=_http(_OPEN_ER)), FailoverFXClient)
    assert isinstance(default_fx_client(http_get=_http(_OPEN_ER)), FailoverFXClient)


def test_facade_get_rate_one_shot():
    r = get_rate("USD", http_get=_http(_OPEN_ER))
    assert r.base == "USD" and r.rate == pytest.approx(25000.0)


# --------------------------------------------------------------------------- #
# resilience / edge cases
# --------------------------------------------------------------------------- #
def test_open_er_api_as_of_falls_back_to_now_without_timestamp():
    payload = '{"result":"success","base_code":"USD","rates":{"USD":1,"VND":25000.0}}'
    r = OpenErApiFXSource(http_get=_http(payload)).get_rate("USD")
    assert r.as_of_utc.tzinfo is not None  # tz-aware fallback, no crash


def test_open_er_api_bool_timestamp_does_not_become_epoch():
    payload = (
        '{"result":"success","base_code":"USD","time_last_update_unix":true,'
        '"rates":{"USD":1,"VND":25000.0,"EUR":0.9}}'
    )
    rates = OpenErApiFXSource(http_get=_http(payload), cache_ttl=0.01).get_rates()
    assert rates[0].as_of_utc.year >= 2024


def test_open_er_api_all_zero_rates_is_empty():
    payload = '{"result":"success","base_code":"USD","rates":{"USD":1,"VND":0}}'
    with pytest.raises(InvalidData):
        OpenErApiFXSource(http_get=_http(payload)).get_rate("USD")


def test_vietcombank_as_of_falls_back_without_datetime():
    xml = (
        '<ExrateList><Exrate CurrencyCode="USD" Buy="24,900.00" '
        'Transfer="25,000.00" Sell="25,200.00"/></ExrateList>'
    )
    r = VietcombankFXSource(http_get=_http(xml)).get_rate("USD")
    assert r.as_of_utc.tzinfo is not None


def test_open_er_api_transport_error_propagates_as_source_error():
    src = OpenErApiFXSource(http_get=_raise(SourceUnavailable("boom")))
    with pytest.raises(SourceUnavailable):
        src.get_rate("USD")


# --------------------------------------------------------------------------- #
# gate-4 hardening: wrong-base guard, base_code validation, caching, ISO shape
# --------------------------------------------------------------------------- #
class _WrongBaseFX:
    name = "wrong"
    unit = "VND-per-foreign-unit"

    def get_rate(self, base, quote="VND"):  # ignores requested base -> always EUR
        return FXRate(base="EUR", quote="VND", rate=27000.0, unit="VND per 1 EUR",
                      as_of_utc=_NOW, source="wrong")


def test_failover_rejects_wrong_base_and_falls_over():
    c = FailoverFXClient([_WrongBaseFX(), _FakeFX("b", rate=26000.0)])
    r = c.get_rate("USD")
    assert r.source == "b" and r.base == "USD"


def test_failover_wrong_base_with_no_backup_raises():
    from vnfin.exceptions import AllSourcesFailed

    with pytest.raises(AllSourcesFailed):
        FailoverFXClient([_WrongBaseFX()]).get_rate("USD")


def test_open_er_api_rejects_non_usd_base_code():
    # drifted payload claiming a non-USD base must not be cross-rated with the USD formula
    bad = '{"result":"success","base_code":"EUR","rates":{"USD":1.1,"EUR":1,"VND":27000}}'
    with pytest.raises(InvalidData):
        OpenErApiFXSource(http_get=_http(bad)).get_rate("USD")


def _counting(text):
    state = {"n": 0}

    def _get(url, params=None, headers=None, json_body=None):
        state["n"] += 1
        return text

    _get.state = state
    return _get


def test_open_er_api_caches_within_ttl():
    getter = _counting(_OPEN_ER)
    src = OpenErApiFXSource(http_get=getter)
    src.get_rate("USD")
    src.get_rate("EUR")  # served from the cached daily response, no second HTTP call
    assert getter.state["n"] == 1


@pytest.mark.parametrize("bad_code", ["US", "USDD", "12A", "U$D"])
def test_malformed_iso_rejected_before_network(bad_code):
    getter = _counting(_OPEN_ER)
    src = OpenErApiFXSource(http_get=getter)
    with pytest.raises(InvalidData):
        src.get_rate(bad_code)
    assert getter.state["n"] == 0  # rejected before any network call


def test_malformed_quote_rejected_before_network():
    getter = _counting(_OPEN_ER)
    src = OpenErApiFXSource(http_get=getter)
    with pytest.raises(InvalidData):
        src.get_rate("USD", quote="VNDD")  # malformed quote
    assert getter.state["n"] == 0


def test_default_client_malformed_input_raises_without_network():
    from vnfin.exceptions import AllSourcesFailed

    getter = _counting(_OPEN_ER)
    c = client(http_get=getter)
    # malformed inputs are rejected by every source before any fetch -> all sources fail
    with pytest.raises((AllSourcesFailed, InvalidData)):
        c.get_rate("US")
    assert getter.state["n"] == 0


# --- Issue #9: malformed FX base must raise InvalidData, not AllSourcesFailed ----


@pytest.mark.parametrize("bad_base", ["US", "USDD", "", "   ", None, 123])
def test_fx_client_rejects_malformed_base_before_failover(bad_base):
    getter = _counting(_OPEN_ER)
    c = client(http_get=getter)
    with pytest.raises(InvalidData):
        c.get_rate(bad_base)
    assert getter.state["n"] == 0


# --------------------------------------------------------------------------- #
# Batch 8 — FX spot validation (#28 #14)
# --------------------------------------------------------------------------- #


def test_open_er_api_skips_malformed_provider_currency_codes():
    # Provider row keys can be malformed (too short/long, digits, symbols). They
    # must be rejected by the ISO-4217 guard and NOT leak into the returned rates.
    payload = (
        '{"result":"success","base_code":"USD","rates":{'
        '"USD":1,"EUR":0.9,"US":1.0,"USDD":1.0,"12A":1.0,"U$D":1.0,"VND":25000}}'
    )
    src = OpenErApiFXSource(http_get=_http(payload))
    rates = src.get_rates()
    bases = {r.base for r in rates}
    assert {"USD", "EUR"} <= bases
    assert bases.isdisjoint({"US", "USDD", "12A", "U$D"})
    assert "VND" not in bases


def test_vietcombank_skips_reversed_bid_ask_spread():
    # USD has bid > ask (invalid metadata); EUR is normal. Only EUR survives.
    xml = """
    <ExrateList>
      <DateTime>6/18/2026 3:53:15 PM</DateTime>
      <Exrate CurrencyCode="USD" Buy="25,200.00" Transfer="25,000.00" Sell="24,900.00"/>
      <Exrate CurrencyCode="EUR" Buy="27,500.00" Transfer="27,800.00" Sell="29,000.00"/>
    </ExrateList>
    """
    src = VietcombankFXSource(http_get=_http(xml), cache_ttl=None)
    rates = src.get_rates()
    bases = {r.base for r in rates}
    assert "USD" not in bases
    assert "EUR" in bases


def test_vietcombank_skips_non_positive_bid_ask():
    xml = """
    <ExrateList>
      <DateTime>6/18/2026 3:53:15 PM</DateTime>
      <Exrate CurrencyCode="USD" Buy="0.00" Transfer="25,000.00" Sell="25,200.00"/>
      <Exrate CurrencyCode="EUR" Buy="27,500.00" Transfer="27,800.00" Sell="29,000.00"/>
    </ExrateList>
    """
    src = VietcombankFXSource(http_get=_http(xml), cache_ttl=None)
    rates = src.get_rates()
    assert "USD" not in {r.base for r in rates}
    assert "EUR" in {r.base for r in rates}
