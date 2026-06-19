"""News domain (#140) — Alpha Vantage NEWS_SENTIMENT, BYOK, offline synthetic only."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

import vnfin
from vnfin.news import AlphaVantageNewsSource, NewsItem, NewsResult, search, source
from vnfin.exceptions import EmptyData, InvalidData, SourceUnavailable, VnfinError

_KEY = "SECRETKEY123"


def _feed(rows):
    return json.dumps({"items": "n/a", "feed": rows})


def _row(**over):
    r = {
        "title": "Headline A",
        "url": "https://pub.example/a",
        "source": "Example Wire",
        "time_published": "20250115T143000",
        "summary": "short snippet",
        "overall_sentiment_score": 0.21,
        "overall_sentiment_label": "Somewhat-Bullish",
        "ticker_sentiment": [{"ticker": "AAPL"}],
        "topics": [{"topic": "Finance"}],
    }
    r.update(over)
    return r


def _capture():
    calls = []

    def _g(url, params=None, headers=None):
        calls.append({"url": url, "params": params, "headers": headers})
        return _feed([_row(), _row(url="https://pub.example/b", title="Headline B", time_published="20250116T090000")])

    _g.calls = calls
    return _g


def _no_network(url, params=None, headers=None):
    raise AssertionError("must not perform a network call")


# 1. missing key -> stable exception before network
def test_missing_key_raises_before_network():
    src = AlphaVantageNewsSource(api_key=None, http_get=_no_network)
    with pytest.raises(SourceUnavailable):
        src.search(tickers=("AAPL",))


# 2. exact query params
def test_query_params_exactly_shaped():
    get = _capture()
    search(tickers=("aapl", "msft"), topics=("finance",), start=date(2025, 1, 1),
           end=date(2025, 1, 31), sort="earliest", limit=25, api_key=_KEY, http_get=get)
    p = get.calls[0]["params"]
    assert p["function"] == "NEWS_SENTIMENT"
    assert p["tickers"] == "AAPL,MSFT" and p["topics"] == "finance"
    assert p["time_from"] == "20250101T0000" and p["time_to"] == "20250131T2359"
    assert p["sort"] == "EARLIEST" and p["limit"] == 25 and p["apikey"] == _KEY


# 3. secret redaction
def test_api_key_redacted_in_provider_error():
    def _g(url, params=None, headers=None):
        return json.dumps({"Information": f"invalid key {_KEY} rate limited"})
    with pytest.raises(VnfinError) as ei:
        search(tickers=("AAPL",), api_key=_KEY, http_get=_g)
    assert _KEY not in str(ei.value)


# 4. input matrices — zero network
@pytest.mark.parametrize("kw", [
    {"tickers": ("A B",)}, {"tickers": ("AAPL/X",)}, {"tickers": ("a\nb",)}, {"tickers": (123,)},
    {"tickers": tuple("T%d" % i for i in range(11))}, {"topics": ("nope",)}, {"topics": (123,)},
    {"tickers": ("AAPL",), "sort": "sideways"}, {"tickers": ("AAPL",), "limit": 0},
    {"tickers": ("AAPL",), "limit": 101}, {"tickers": ("AAPL",), "limit": True},
    {"tickers": ("AAPL",), "start": "2025-01-01"}, {"tickers": ("AAPL",), "start": date(2025, 6, 1), "end": date(2025, 1, 1)},
    {},  # neither tickers nor topics
])
def test_malformed_inputs_fail_closed_zero_network(kw):
    with pytest.raises((InvalidData, VnfinError)):
        AlphaVantageNewsSource(api_key=_KEY, http_get=_no_network).search(**kw)


# 5. happy path
def test_happy_path_parses_two_rows():
    res = search(tickers=("AAPL",), api_key=_KEY, http_get=_capture())
    assert isinstance(res, NewsResult) and len(res) == 2
    a = res.items[0]
    assert isinstance(a, NewsItem) and a.source == "Example Wire"
    assert a.published_at_utc == datetime(2025, 1, 15, 14, 30, tzinfo=timezone.utc)
    assert a.tickers == ("AAPL",) and a.overall_sentiment_score == pytest.approx(0.21)
    assert res.fetched_at_utc is not None and res.source == "alpha_vantage"


# 6. empty feed
def test_empty_feed_raises_empty():
    with pytest.raises(EmptyData):
        search(tickers=("AAPL",), api_key=_KEY, http_get=lambda *a, **k: _feed([]))


# 7. error envelopes
@pytest.mark.parametrize("env", [{"Error Message": "bad"}, {"Information": "rate"}, {"Note": "limit"}])
def test_provider_error_envelopes_raise_source_unavailable(env):
    with pytest.raises(SourceUnavailable):
        search(tickers=("AAPL",), api_key=_KEY, http_get=lambda *a, e=env, **k: json.dumps(e))


def test_missing_feed_is_invaliddata():
    with pytest.raises(InvalidData):
        search(tickers=("AAPL",), api_key=_KEY, http_get=lambda *a, **k: json.dumps({"x": 1}))


# 8. malformed rows
@pytest.mark.parametrize("bad", [
    {"title": ""}, {"url": ""}, {"source": ""}, {"time_published": "nope"},
    {"time_published": ""}, {"overall_sentiment_score": float("nan")},
    {"overall_sentiment_score": "x"}, {"summary": 5}, {"overall_sentiment_label": 5},
    {"ticker_sentiment": [{"x": 1}]}, {"ticker_sentiment": [{"ticker": "A B"}]},
])
def test_malformed_provider_row_fails_closed(bad):
    with pytest.raises(InvalidData):
        search(tickers=("AAPL",), api_key=_KEY, http_get=lambda *a, b=bad, **k: _feed([_row(**b)]))


# 9. duplicate url
def test_identical_duplicate_url_kept_once():
    res = search(tickers=("AAPL",), api_key=_KEY,
                 http_get=lambda *a, **k: _feed([_row(), _row()]))
    assert len(res) == 1


def test_conflicting_duplicate_url_raises():
    rows = [_row(), _row(title="Different headline same url")]
    with pytest.raises(InvalidData, match="duplicate"):
        search(tickers=("AAPL",), api_key=_KEY, http_get=lambda *a, **k: _feed(rows))


# env-var BYOK + namespace
def test_env_var_key_and_namespace(monkeypatch):
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", _KEY)
    res = vnfin.news.search(topics=("finance",), http_get=_capture())
    assert len(res) == 2
    assert source("alpha_vantage", api_key=_KEY).name == "alpha_vantage"


def test_unknown_provider_rejected():
    with pytest.raises(ValueError):
        source("finnhub", api_key=_KEY)


# B1 — control/newline must NOT be stripped into valid tickers/topics (zero network).
@pytest.mark.parametrize("bad", ["AAPL\n", "AA\tPL", "AAPL\r", "AA PL", "\nAAPL"])
def test_ticker_control_chars_fail_closed(bad):
    with pytest.raises(InvalidData):
        AlphaVantageNewsSource(api_key=_KEY, http_get=_no_network).search(tickers=(bad,))


@pytest.mark.parametrize("bad", ["finance\n", "fin ance", "finance\t"])
def test_topic_control_chars_fail_closed(bad):
    with pytest.raises(InvalidData):
        AlphaVantageNewsSource(api_key=_KEY, http_get=_no_network).search(topics=(bad,))


# B2 — provider ticker_sentiment accepts official CRYPTO:/FOREX: forms.
@pytest.mark.parametrize("prov,expected", [
    ("CRYPTO:BTC", "CRYPTO:BTC"), ("FOREX:USD", "FOREX:USD"), ("AAPL", "AAPL"), ("brk.b", "BRK.B"),
])
def test_provider_ticker_sentiment_accepts_official_forms(prov, expected):
    rows = [_row(ticker_sentiment=[{"ticker": prov}])]
    res = search(tickers=("AAPL",), api_key=_KEY, http_get=lambda *a, **k: _feed(rows))
    assert res.items[0].tickers == (expected,)


@pytest.mark.parametrize("bad", ["BAD:BTC", "CRYPTO:bt c", "CRYPTO:BTC\n", "STOCK:AAPL"])
def test_provider_ticker_sentiment_rejects_malformed(bad):
    rows = [_row(ticker_sentiment=[{"ticker": bad}])]
    with pytest.raises(InvalidData):
        search(tickers=("AAPL",), api_key=_KEY, http_get=lambda *a, **k: _feed(rows))


# B3 — datetime params emit documented YYYYMMDDTHHMM (no seconds).
def test_datetime_params_emit_hhmm_no_seconds():
    get = _capture()
    search(tickers=("AAPL",), start=datetime(2025, 1, 1, 9, 30, 45),
           end=datetime(2025, 1, 31, 16, 0, 5), api_key=_KEY, http_get=get)
    p = get.calls[0]["params"]
    assert p["time_from"] == "20250101T0930"  # HHMM, seconds dropped
    assert p["time_to"] == "20250131T1600"
