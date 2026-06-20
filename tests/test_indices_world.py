"""Tests for ``vnfin.indices.world`` (#177) — SYNTHETIC + OFFLINE only.

A US/global equity index (S&P 500) accessor backed by its OWN 2-source failover
chain: Alpha Vantage (PRIMARY, BYOK; SPY ETF, USD/share) -> Stooq (FALLBACK,
keyless; ^SPX index points). All HTTP is injected via ``http_get`` stubs; no
network is ever touched. The VN HOSE/HNX ``index_history`` path is untouched.

Mirrors the design note ``docs/design/world-index-sp500.md`` §6 test matrix
(all 11 items) and the existing macro/gold synthetic-injection test style.
"""
from __future__ import annotations

import json
from datetime import date, datetime

import pytest

import vnfin
from vnfin.exceptions import (
    AllSourcesFailed,
    EmptyData,
    InvalidData,
    SourceUnavailable,
)
from vnfin.indices import (
    AlphaVantageIndexSource,
    StooqIndexSource,
    default_world_index_client,
    default_world_index_sources,
    world,
)
from vnfin.models import AdjustmentPolicy, Interval, PriceHistory


# --------------------------------------------------------------------------- #
# synthetic fixtures
# --------------------------------------------------------------------------- #
_FAKE_KEY = "fake-av-key-1234567890"  # placeholder; hyphens keep alnum runs < the secret-scanner floor


def _av_payload(rows=None):
    """A minimal Alpha Vantage TIME_SERIES_DAILY JSON body with fabricated bars."""
    if rows is None:
        rows = {
            "2024-01-02": ("470.0", "475.0", "468.0", "472.0", "1000000"),
            "2024-01-03": ("472.0", "478.0", "471.0", "476.0", "1100000"),
            "2024-01-04": ("476.0", "480.0", "474.0", "479.0", "1200000"),
        }
    series = {
        d: {
            "1. open": o,
            "2. high": h,
            "3. low": lo,
            "4. close": c,
            "5. volume": v,
        }
        for d, (o, h, lo, c, v) in rows.items()
    }
    return json.dumps(
        {
            "Meta Data": {"2. Symbol": "SPY"},
            "Time Series (Daily)": series,
        }
    )


def _stooq_csv(rows=None):
    """A Stooq ^SPX daily CSV body (index points)."""
    if rows is None:
        rows = [
            ("2024-01-02", "4700", "4750", "4680", "4720", "0"),
            ("2024-01-03", "4720", "4780", "4710", "4760", "0"),
            ("2024-01-04", "4760", "4800", "4740", "4790", "0"),
        ]
    lines = ["Date,Open,High,Low,Close,Volume"]
    for r in rows:
        lines.append(",".join(r))
    return "\n".join(lines) + "\n"


def _av_source(payload, *, api_key=_FAKE_KEY, recorder=None, **kw):
    def _g(url, params=None, headers=None):
        if recorder is not None:
            recorder.append((url, params, headers))
        return payload

    return AlphaVantageIndexSource(api_key=api_key, http_get=_g, **kw)


def _stooq_source(csv_text, *, recorder=None):
    def _g(url, params=None, headers=None):
        if recorder is not None:
            recorder.append((url, params, headers))
        return csv_text

    return StooqIndexSource(http_get=_g)


# --------------------------------------------------------------------------- #
# Matrix #1 — AV full payload -> typed daily PriceHistory, USD/share, source, window
# --------------------------------------------------------------------------- #
def test_av_full_payload_typed_pricehistory_usd_per_share():
    src = _av_source(_av_payload())
    hist = src.get_history("SPY")
    assert isinstance(hist, PriceHistory)
    assert hist.source == "alphavantage"
    assert hist.symbol == "SPY"
    assert hist.provider_symbol == "SPY"
    assert hist.currency == "USD"
    assert hist.value_unit == "USD/share (SPY ETF, S&P 500 proxy)"
    assert hist.interval is Interval.D1
    assert hist.adjustment_policy is AdjustmentPolicy.RAW
    assert isinstance(hist.fetched_at_utc, datetime) and hist.fetched_at_utc.tzinfo is not None
    # full history, ascending
    assert [b.time.date() for b in hist.bars] == [
        date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)
    ]
    assert hist.bars[0].open == pytest.approx(470.0)
    assert hist.bars[-1].close == pytest.approx(479.0)
    assert hist.bars[0].volume == 1000000
    # SPY success path carries NO fallback warning (matrix #11 negative)
    assert not any("fallback_instrument_served" in w for w in hist.warnings)


def test_av_window_filter():
    src = _av_source(_av_payload())
    hist = src.get_history("SPY", start=date(2024, 1, 3), end=date(2024, 1, 3))
    assert [b.time.date() for b in hist.bars] == [date(2024, 1, 3)]


# --------------------------------------------------------------------------- #
# Matrix #2 — AV error text -> key redacted
# --------------------------------------------------------------------------- #
def test_av_error_message_redacts_key():
    payload = json.dumps({"Error Message": f"Invalid apikey {_FAKE_KEY} supplied"})
    src = _av_source(payload)
    with pytest.raises(InvalidData) as ei:
        src.get_history("SPY")
    assert _FAKE_KEY not in str(ei.value)
    assert "***" in str(ei.value)


def test_av_transport_error_redacts_key():
    # A wrapped transport error must not leak the key embedded in the URL/params.
    def _g(url, params=None, headers=None):
        raise ConnectionError(f"boom apikey={_FAKE_KEY}")

    src = AlphaVantageIndexSource(api_key=_FAKE_KEY, http_get=_g)
    with pytest.raises(SourceUnavailable) as ei:
        src.get_history("SPY")
    assert _FAKE_KEY not in str(ei.value)


# --------------------------------------------------------------------------- #
# Matrix #3 — keyless -> AV skipped with NO network call + Stooq fallback used
# --------------------------------------------------------------------------- #
def test_keyless_av_skipped_no_network(monkeypatch):
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    av_calls = []

    def av_get(url, params=None, headers=None):
        av_calls.append(url)
        return _av_payload()

    av = AlphaVantageIndexSource(api_key=None, http_get=av_get)
    assert av.has_key is False
    assert av.supports("SPY") is False
    stooq = _stooq_source(_stooq_csv())
    client = default_world_index_client(sources=[av, stooq])
    hist = client.get_history("SPY")
    assert hist.source == "stooq"
    assert av_calls == []  # keyless AV never touched the network


def test_keyless_av_raises_source_unavailable_before_network(monkeypatch):
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    av_calls = []

    def av_get(url, params=None, headers=None):
        av_calls.append(url)
        return _av_payload()

    av = AlphaVantageIndexSource(api_key=None, http_get=av_get)
    with pytest.raises(SourceUnavailable):
        av.get_history("SPY")
    assert av_calls == []


# --------------------------------------------------------------------------- #
# Matrix #4 — AV "Note"/"Information" throttle -> SourceUnavailable -> Stooq fallback
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("throttle_key", ["Note", "Information"])
def test_av_throttle_is_source_unavailable(throttle_key):
    payload = json.dumps({throttle_key: "Thank you for using Alpha Vantage! ... 25 requests/day"})
    src = _av_source(payload)
    with pytest.raises(SourceUnavailable):
        src.get_history("SPY")


@pytest.mark.parametrize("throttle_key", ["Note", "Information"])
def test_av_throttle_falls_over_to_stooq(throttle_key):
    payload = json.dumps({throttle_key: "rate limit"})
    av = _av_source(payload)
    stooq = _stooq_source(_stooq_csv())
    client = default_world_index_client(sources=[av, stooq])
    hist = client.get_history("SPY")
    assert hist.source == "stooq"


# --------------------------------------------------------------------------- #
# Matrix #5 — Stooq ^SPX CSV -> index-points series, source=stooq
# --------------------------------------------------------------------------- #
def test_stooq_csv_index_points():
    src = _stooq_source(_stooq_csv())
    hist = src.get_history("SPY")
    assert isinstance(hist, PriceHistory)
    assert hist.source == "stooq"
    assert hist.value_unit == "index points"
    assert hist.currency == "points"
    assert hist.provider_symbol == "^SPX"
    assert hist.adjustment_policy is AdjustmentPolicy.RAW
    assert [b.time.date() for b in hist.bars] == [
        date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)
    ]
    assert hist.bars[-1].close == pytest.approx(4790.0)


def test_stooq_window_filter():
    src = _stooq_source(_stooq_csv())
    hist = src.get_history("SPY", start=date(2024, 1, 4), end=date(2024, 1, 4))
    assert [b.time.date() for b in hist.bars] == [date(2024, 1, 4)]


def test_stooq_request_uses_spx_symbol():
    rec = []
    src = _stooq_source(_stooq_csv(), recorder=rec)
    src.get_history("SPY")
    assert rec, "stooq should make a request"
    url, params, _headers = rec[0]
    # ^spx is requested either in the URL or the params
    assert "^spx" in (str(url) + str(params)).lower()


# --------------------------------------------------------------------------- #
# Matrix #6 — Stooq anti-bot HTML/403 -> SourceUnavailable; AV also down -> AllSourcesFailed
# --------------------------------------------------------------------------- #
def test_stooq_anti_bot_html_is_source_unavailable():
    html = "<!DOCTYPE html><html><body><noscript>enable js</noscript></body></html>"
    src = _stooq_source(html)
    with pytest.raises(SourceUnavailable):
        src.get_history("SPY")


def test_both_down_raises_all_sources_failed():
    av = _av_source(json.dumps({"Note": "throttled"}))
    stooq = _stooq_source("<html><noscript>bot</noscript></html>")
    client = default_world_index_client(sources=[av, stooq])
    with pytest.raises(AllSourcesFailed) as ei:
        client.get_history("SPY")
    reasons = "; ".join(a.reason for a in ei.value.attempts)
    assert "alphavantage" in {a.name for a in ei.value.attempts}
    assert "stooq" in {a.name for a in ei.value.attempts}
    assert reasons  # clear per-source reasons present


# --------------------------------------------------------------------------- #
# Matrix #7 — malformed payloads (both) -> InvalidData
# --------------------------------------------------------------------------- #
def test_av_non_dict_payload_invalid():
    src = _av_source(json.dumps([1, 2, 3]))
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_av_missing_series_invalid():
    src = _av_source(json.dumps({"Meta Data": {}}))
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_av_non_finite_value_invalid():
    bad = _av_payload({"2024-01-02": ("470.0", "nan", "468.0", "472.0", "1000000")})
    src = _av_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_av_non_numeric_value_invalid():
    bad = _av_payload({"2024-01-02": ("470.0", "x", "468.0", "472.0", "1000000")})
    src = _av_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_av_negative_price_invalid():
    # The OHLC-ordering invariant (lo<=o<=h, lo<=c<=h) is satisfied by all-negative
    # values, so without a positivity guard a corrupt series is served as the trusted
    # primary. AV must reject like the Stooq fallback already does (review 011cffa).
    bad = _av_payload({"2024-01-02": ("-5", "-1", "-10", "-3", "1000000")})
    src = _av_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_av_zero_price_invalid():
    bad = _av_payload({"2024-01-02": ("0", "0", "0", "0", "1000000")})
    src = _av_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_stooq_malformed_csv_invalid():
    bad = "Date,Open,High,Low,Close,Volume\n2024-01-02,4700,4750,4680,notanumber,0\n"
    src = _stooq_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_stooq_missing_close_column_invalid():
    bad = "Date,Open,High,Low,Volume\n2024-01-02,4700,4750,4680,0\n"
    src = _stooq_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


# --------------------------------------------------------------------------- #
# Matrix #8 — cache_ttl -> 2nd same-process call makes no 2nd network call
# --------------------------------------------------------------------------- #
def test_av_cache_ttl_single_network_call():
    calls = []
    src = _av_source(_av_payload(), recorder=calls)  # default cache_ttl on AV source
    h1 = src.get_history("SPY")
    h2 = src.get_history("SPY")
    assert len(calls) == 1  # second call served from in-memory cache
    assert [b.time for b in h1.bars] == [b.time for b in h2.bars]


def test_av_has_default_cache_ttl():
    src = _av_source(_av_payload())
    # the AV source must have an in-memory cache configured by default (~6h)
    assert src._cache is not None
    assert src._cache_ttl == pytest.approx(21600.0)


# --------------------------------------------------------------------------- #
# Matrix #9 — non-SPY symbol in v1 -> clear error
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("sym", ["QQQ", "AAPL", "^GSPC", "spx", ""])
def test_non_spy_symbol_clear_error(sym):
    with pytest.raises((InvalidData, ValueError)) as ei:
        world(sym, http_get=lambda *a, **k: _stooq_csv())
    assert "SPY" in str(ei.value)


def test_spy_lowercase_accepted():
    # SPY is the only supported symbol; case-insensitive acceptance is fine.
    rec = []
    hist = world(
        "spy",
        sources=[_stooq_source(_stooq_csv(), recorder=rec)],
    )
    assert hist.source == "stooq"


# --------------------------------------------------------------------------- #
# Matrix #10 — public-API additive: accessor + sources + factories exported; reuse PriceHistory
# --------------------------------------------------------------------------- #
def test_public_api_exports_world_accessor_and_sources():
    for name in (
        "world",
        "AlphaVantageIndexSource",
        "StooqIndexSource",
        "default_world_index_sources",
        "default_world_index_client",
    ):
        assert name in vnfin.indices.__all__, name
        assert hasattr(vnfin.indices, name), name
    assert callable(vnfin.indices.world)


def test_default_world_index_sources_chain_order():
    srcs = default_world_index_sources(api_key=_FAKE_KEY)
    assert isinstance(srcs[0], AlphaVantageIndexSource)
    assert isinstance(srcs[1], StooqIndexSource)
    assert len(srcs) == 2


def test_default_world_index_sources_keyless_drops_av(monkeypatch):
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    srcs = default_world_index_sources()
    # keyless: AV is either omitted, or present-but-incapable (supports() False).
    av = [s for s in srcs if isinstance(s, AlphaVantageIndexSource)]
    assert all(s.supports("SPY") is False for s in av)
    assert any(isinstance(s, StooqIndexSource) for s in srcs)


def test_vn_index_history_untouched():
    # The VN HOSE/HNX index path must keep its own behavior (not routed through world()).
    assert callable(vnfin.indices.index_history)
    assert callable(vnfin.indices.index_history_stitched)
    assert callable(vnfin.indices.index_constituents)


# --------------------------------------------------------------------------- #
# Matrix #11 — fallback_instrument_served warning on BOTH substitution paths +
# survives finalize; ABSENT on the SPY-primary success path.
# --------------------------------------------------------------------------- #
_FALLBACK_TOKEN = "fallback_instrument_served"


def test_throttle_fallback_emits_warning():
    av = _av_source(json.dumps({"Note": "throttled"}))
    stooq = _stooq_source(_stooq_csv())
    hist = default_world_index_client(sources=[av, stooq]).get_history("SPY")
    assert hist.source == "stooq"
    warn = [w for w in hist.warnings if w.startswith(f"{_FALLBACK_TOKEN}:")]
    assert len(warn) == 1
    # human magnitude cause in the tail
    assert "SPY" in warn[0] and "^SPX" in warn[0]
    assert "magnitude" in warn[0].lower() or "rebase" in warn[0].lower()


def test_keyless_fallback_emits_warning(monkeypatch):
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    av = AlphaVantageIndexSource(api_key=None, http_get=lambda *a, **k: _av_payload())
    stooq = _stooq_source(_stooq_csv())
    hist = default_world_index_client(sources=[av, stooq]).get_history("SPY")
    assert hist.source == "stooq"
    assert any(w.startswith(f"{_FALLBACK_TOKEN}:") for w in hist.warnings)


def test_spy_primary_success_has_no_fallback_warning():
    av = _av_source(_av_payload())
    stooq = _stooq_source(_stooq_csv())
    hist = default_world_index_client(sources=[av, stooq]).get_history("SPY")
    assert hist.source == "alphavantage"
    assert not any(w.startswith(f"{_FALLBACK_TOKEN}:") for w in hist.warnings)


def test_fallback_warning_survives_finalize_via_world_accessor():
    # Drive the whole world() accessor (the finalize seam) and confirm the warning rides through.
    av = _av_source(json.dumps({"Note": "throttled"}))
    stooq = _stooq_source(_stooq_csv())
    hist = world("SPY", sources=[av, stooq])
    assert hist.source == "stooq"
    assert any(w.startswith(f"{_FALLBACK_TOKEN}:") for w in hist.warnings)
    # and the finalize attached failover attempts too
    assert any(a.name == "alphavantage" for a in hist.attempts)
    assert any(a.name == "stooq" and a.ok for a in hist.attempts)


def test_stooq_only_chain_still_warns():
    # A Stooq-only chain (no AV at all) still substitutes ^SPX for the requested SPY,
    # so the mechanical warning must fire.
    hist = world("SPY", sources=[_stooq_source(_stooq_csv())])
    assert hist.source == "stooq"
    assert any(w.startswith(f"{_FALLBACK_TOKEN}:") for w in hist.warnings)


# --------------------------------------------------------------------------- #
# Additional defensive-branch coverage (still synthetic + offline)
# --------------------------------------------------------------------------- #
def test_av_redact_noop_when_no_key():
    # _redact_key must be a safe no-op when there is no key (and for non-str input).
    src = AlphaVantageIndexSource(api_key=None, http_get=lambda *a, **k: "")
    assert src._redact_key("plain text") == "plain text"
    assert src._redact_key(None) is None


def test_av_empty_window_raises_empty_data():
    src = _av_source(_av_payload())
    with pytest.raises(EmptyData):
        src.get_history("SPY", start=date(2030, 1, 1), end=date(2030, 1, 2))


def test_av_start_after_end_invalid():
    src = _av_source(_av_payload())
    with pytest.raises(InvalidData):
        src.get_history("SPY", start=date(2024, 1, 4), end=date(2024, 1, 2))


def test_av_bad_date_key_invalid():
    bad = json.dumps(
        {"Time Series (Daily)": {"not-a-date": {
            "1. open": "1", "2. high": "2", "3. low": "1", "4. close": "2", "5. volume": "0"}}}
    )
    src = _av_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_av_missing_open_field_invalid():
    bad = json.dumps(
        {"Time Series (Daily)": {"2024-01-02": {
            "2. high": "2", "3. low": "1", "4. close": "2", "5. volume": "0"}}}
    )
    src = _av_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_av_malformed_bar_object_invalid():
    bad = json.dumps({"Time Series (Daily)": {"2024-01-02": "not-a-dict"}})
    src = _av_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_av_ohlc_invariant_invalid():
    # low > high is impossible.
    bad = _av_payload({"2024-01-02": ("470.0", "468.0", "475.0", "472.0", "1000000")})
    src = _av_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_av_missing_volume_defaults_zero():
    body = json.dumps(
        {"Time Series (Daily)": {"2024-01-02": {
            "1. open": "470", "2. high": "475", "3. low": "468", "4. close": "472"}}}
    )
    src = _av_source(body)
    hist = src.get_history("SPY")
    assert hist.bars[0].volume == 0


def test_av_blank_symbol_arg_defaults_spy():
    # An empty/blank symbol falls back to the canonical SPY label.
    src = _av_source(_av_payload())
    hist = src.get_history("  ")
    assert hist.symbol == "SPY"


def test_stooq_empty_body_empty_data():
    src = _stooq_source("")
    with pytest.raises(EmptyData):
        src.get_history("SPY")


def test_stooq_no_data_sentinel_empty():
    src = _stooq_source("No data\n")
    with pytest.raises(EmptyData):
        src.get_history("SPY")


def test_stooq_empty_window_empty_data():
    src = _stooq_source(_stooq_csv())
    with pytest.raises(EmptyData):
        src.get_history("SPY", start=date(2030, 1, 1), end=date(2030, 1, 2))


def test_stooq_short_row_invalid():
    bad = "Date,Open,High,Low,Close,Volume\n2024-01-02,4700\n"
    src = _stooq_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_stooq_duplicate_date_invalid():
    bad = (
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-02,4700,4750,4680,4720,0\n"
        "2024-01-02,4700,4750,4680,4720,0\n"
    )
    src = _stooq_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_stooq_ohlc_invariant_invalid():
    bad = "Date,Open,High,Low,Close,Volume\n2024-01-02,4700,4680,4750,4720,0\n"
    src = _stooq_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_stooq_missing_close_value_invalid():
    bad = "Date,Open,High,Low,Close,Volume\n2024-01-02,4700,4750,4680,,0\n"
    src = _stooq_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_stooq_non_positive_close_invalid():
    bad = "Date,Open,High,Low,Close,Volume\n2024-01-02,4700,4750,4680,0,0\n"
    src = _stooq_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_stooq_bad_date_invalid():
    bad = "Date,Open,High,Low,Close,Volume\nnotadate,4700,4750,4680,4720,0\n"
    src = _stooq_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_stooq_no_volume_column_defaults_zero():
    csv_text = "Date,Open,High,Low,Close\n2024-01-02,4700,4750,4680,4720\n"
    src = _stooq_source(csv_text)
    hist = src.get_history("SPY")
    assert hist.bars[0].volume == 0


def test_stooq_blank_volume_defaults_zero():
    csv_text = "Date,Open,High,Low,Close,Volume\n2024-01-02,4700,4750,4680,4720,\n"
    src = _stooq_source(csv_text)
    hist = src.get_history("SPY")
    assert hist.bars[0].volume == 0


def test_stooq_malformed_volume_invalid():
    bad = "Date,Open,High,Low,Close,Volume\n2024-01-02,4700,4750,4680,4720,xx\n"
    src = _stooq_source(bad)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_stooq_bytes_body_decoded():
    raw = _stooq_csv().encode("utf-8-sig")
    src = StooqIndexSource(http_get=lambda *a, **k: raw)
    hist = src.get_history("SPY")
    assert hist.source == "stooq"
    assert hist.bars[-1].close == pytest.approx(4790.0)


def test_default_world_index_client_builds_default_chain(monkeypatch):
    # Exercise the no-sources path of the factory (no network; just construction).
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    client = default_world_index_client(http_get=lambda *a, **k: _stooq_csv())
    assert len(client.sources) == 2
    assert client.max_attempts == 3


def test_av_duplicate_date_invalid():
    # Two distinct string keys that normalize to the SAME calendar date ("2024-01-02"
    # and "2024-01-02 " with a trailing space) collide -> a duplicate-date InvalidData.
    raw = (
        '{"Time Series (Daily)": {'
        '"2024-01-02": {"1. open": "1", "2. high": "2", "3. low": "1", "4. close": "2", "5. volume": "0"}, '
        '"2024-01-02 ": {"1. open": "1", "2. high": "2", "3. low": "1", "4. close": "2", "5. volume": "0"}}}'
    )
    # "2024-01-02 " (trailing space) normalizes to the same date -> duplicate.
    src = _av_source(raw)
    with pytest.raises(InvalidData):
        src.get_history("SPY")


def test_stooq_start_after_end_invalid():
    src = _stooq_source(_stooq_csv())
    with pytest.raises(InvalidData):
        src.get_history("SPY", start=date(2024, 1, 4), end=date(2024, 1, 2))


def test_stooq_header_only_empty_data():
    src = _stooq_source("Date,Open,High,Low,Close,Volume\n")
    with pytest.raises(EmptyData):
        src.get_history("SPY")


def test_stooq_window_skips_out_of_range_rows():
    # A 3-row CSV with a [middle, middle] window keeps only the middle bar, exercising
    # both the below-start and above-end skip branches.
    src = _stooq_source(_stooq_csv())
    hist = src.get_history("SPY", start=date(2024, 1, 3), end=date(2024, 1, 3))
    assert [b.time.date() for b in hist.bars] == [date(2024, 1, 3)]


def test_world_client_relabels_served_symbol():
    # The Stooq leg stamps symbol="SPY" already; force a mismatch to exercise the
    # relabel branch by serving a source whose result carries a different symbol.
    from dataclasses import replace as _replace

    base = _stooq_source(_stooq_csv())

    class _Mislabel(StooqIndexSource):
        def get_history(self, symbol="SPY", start=None, end=None, *, interval=Interval.D1):
            hist = base.get_history(symbol, start, end, interval=interval)
            return _replace(hist, symbol="WRONG")

    hist = world("SPY", sources=[_Mislabel(http_get=lambda *a, **k: _stooq_csv())])
    assert hist.symbol == "SPY"


def test_world_default_chain_keyless_serves_stooq(monkeypatch):
    # world() with no injected sources builds the default chain; keyless AV is
    # skipped and Stooq serves (http_get injected so no real network).
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    hist = world("SPY", http_get=lambda *a, **k: _stooq_csv())
    assert hist.source == "stooq"
    assert any(w.startswith(f"{_FALLBACK_TOKEN}:") for w in hist.warnings)
