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


def _av_payload(rows=None, *, meta_symbol="SPY"):
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
            "Meta Data": {"2. Symbol": meta_symbol},
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
# Matrix #9 — unsupported symbol in v1 -> clear error (QQQ is now SUPPORTED, #193)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("sym", ["AAPL", "^GSPC", "spx", ""])
def test_unsupported_symbol_clear_error(sym):
    # QQQ moved to the supported set in #193, so it is no longer here. The error must
    # enumerate the full supported set so a caller learns what IS allowed.
    with pytest.raises((InvalidData, ValueError)) as ei:
        world(sym, http_get=lambda *a, **k: _stooq_csv())
    msg = str(ei.value)
    for supported in ("SPY", "QQQ", "^N225", "^SSEC", "^STI"):
        assert supported in msg, f"{supported!r} not enumerated in error: {msg!r}"


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


# =========================================================================== #
# #193 — coverage to 5 symbols (USD ETF proxies) + MissingKey + proxy labeling
# =========================================================================== #
from vnfin.exceptions import MissingKey  # noqa: E402  (additive #193 export)

_PROXY_TOKEN = "proxy_substitution"

# asked symbol -> (av_ticker, value_unit, proxy_for-or-None)
_SYMBOL_MATRIX = {
    "SPY": ("SPY", "USD/share (SPY ETF, S&P 500 proxy)", None),
    "QQQ": ("QQQ", "USD/share (QQQ ETF, Nasdaq-100 proxy)", None),
    "^N225": ("EWJ", "USD/share (EWJ ETF)", "^N225"),
    "^SSEC": ("FXI", "USD/share (FXI ETF)", "^SSEC"),
    "^STI": ("EWS", "USD/share (EWS ETF)", "^STI"),
}


# --- happy path per new symbol: typed history, USD, correct AV ticker fetched --- #
@pytest.mark.parametrize("asked", ["QQQ", "^N225", "^SSEC", "^STI"])
def test_new_symbol_happy_path_fetches_correct_av_ticker(asked):
    av_ticker, value_unit, _proxy = _SYMBOL_MATRIX[asked]
    rec = []
    src = _av_source(_av_payload(meta_symbol=av_ticker), recorder=rec)
    hist = src.get_history(asked)
    assert isinstance(hist, PriceHistory)
    assert hist.source == "alphavantage"
    assert hist.symbol == asked
    assert hist.currency == "USD"
    assert hist.value_unit == value_unit
    assert hist.provider_symbol == av_ticker
    assert hist.interval is Interval.D1
    assert hist.adjustment_policy is AdjustmentPolicy.RAW
    assert hist.bars, "expected bars"
    # the request actually fetched the av_ticker (not the hard-pinned SPY)
    assert rec, "AV source should make a request"
    _url, params, _headers = rec[0]
    assert params is not None and params.get("symbol") == av_ticker


def test_qqq_lowercase_canonicalized_and_fetches_qqq():
    rec = []
    src = _av_source(_av_payload(meta_symbol="QQQ"), recorder=rec)
    hist = src.get_history("qqq")
    assert hist.symbol == "QQQ"
    assert rec[0][1]["symbol"] == "QQQ"


# --- proxy-labeling: BOTH proxy_for field AND proxy_substitution token (or NEITHER) --- #
@pytest.mark.parametrize("asked", ["^N225", "^SSEC", "^STI"])
def test_proxy_symbol_carries_both_field_and_token(asked):
    av_ticker, _unit, proxy_for = _SYMBOL_MATRIX[asked]
    src = _av_source(_av_payload(meta_symbol=av_ticker))
    hist = default_world_index_client(sources=[src]).get_history(asked)
    # MUST-HAVE structured field
    assert hist.proxy_for == proxy_for, "proxy_for field missing/wrong on a proxy result"
    # AND the loud warning token
    proxy_warns = [w for w in hist.warnings if w.startswith(f"{_PROXY_TOKEN}:")]
    assert len(proxy_warns) == 1, f"expected exactly one proxy_substitution warning, got {hist.warnings!r}"
    w = proxy_warns[0]
    assert asked in w and av_ticker in w


@pytest.mark.parametrize("asked", ["SPY", "QQQ"])
def test_direct_symbol_has_no_proxy_field_or_token(asked):
    av_ticker = _SYMBOL_MATRIX[asked][0]
    src = _av_source(_av_payload(meta_symbol=av_ticker))
    hist = default_world_index_client(sources=[src]).get_history(asked)
    assert hist.proxy_for is None
    assert not any(w.startswith(f"{_PROXY_TOKEN}:") for w in hist.warnings)


def test_proxy_substitution_warning_survives_world_accessor():
    src = _av_source(_av_payload(meta_symbol="EWJ"))
    hist = world("^N225", sources=[src])
    assert hist.proxy_for == "^N225"
    assert any(w.startswith(f"{_PROXY_TOKEN}:") for w in hist.warnings)


# --- unit-correctness: every served unit is USD (NOT the local index currency) --- #
@pytest.mark.parametrize("asked", list(_SYMBOL_MATRIX))
def test_value_unit_is_usd_not_local_currency(asked):
    av_ticker, value_unit, _proxy = _SYMBOL_MATRIX[asked]
    src = _av_source(_av_payload(meta_symbol=av_ticker))
    hist = src.get_history(asked)
    assert hist.currency == "USD"
    assert hist.value_unit == value_unit
    # explicitly NOT the local index currency (the ETF-in-USD-vs-index-local trap)
    for local in ("JPY", "CNY", "SGD"):
        assert local not in hist.value_unit


# --- Q5 hard guard: AV error / missing series for an allowlisted symbol -> InvalidData naming it --- #
@pytest.mark.parametrize("asked", ["QQQ", "^N225", "^SSEC", "^STI"])
def test_av_error_envelope_names_symbol_q5(asked):
    payload = json.dumps({"Error Message": "Invalid API call for this ticker"})
    src = _av_source(payload)
    with pytest.raises(InvalidData) as ei:
        src.get_history(asked)
    assert asked in str(ei.value)


@pytest.mark.parametrize("asked", ["QQQ", "^N225", "^SSEC", "^STI"])
def test_av_missing_series_names_symbol_q5(asked):
    src = _av_source(json.dumps({"Meta Data": {}}))
    with pytest.raises(InvalidData) as ei:
        src.get_history(asked)
    assert asked in str(ei.value)


# --- MissingKey vs AllSourcesFailed clean branch --- #
def test_no_key_walled_fallback_raises_missing_key(monkeypatch):
    # no AV key + anti-bot Stooq -> a config-actionable MissingKey, not opaque AllSourcesFailed.
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    av = AlphaVantageIndexSource(api_key=None, http_get=lambda *a, **k: _av_payload())
    stooq = _stooq_source("<html><noscript>bot</noscript></html>")
    client = default_world_index_client(sources=[av, stooq])
    with pytest.raises(MissingKey) as ei:
        client.get_history("SPY")
    msg = str(ei.value)
    assert "ALPHAVANTAGE_API_KEY" in msg
    assert "SPY" in msg


def test_no_key_walled_fallback_missing_key_via_world_accessor(monkeypatch):
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    av = AlphaVantageIndexSource(api_key=None, http_get=lambda *a, **k: _av_payload())
    stooq = _stooq_source("<html><noscript>bot</noscript></html>")
    with pytest.raises(MissingKey) as ei:
        world("^N225", sources=[av, stooq])
    assert "ALPHAVANTAGE_API_KEY" in str(ei.value) and "^N225" in str(ei.value)


def test_missing_key_has_no_trail_enumeration(monkeypatch):
    # #157 lesson: MissingKey must not fold per-source attempt strings into its message.
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    av = AlphaVantageIndexSource(api_key=None, http_get=lambda *a, **k: _av_payload())
    stooq = _stooq_source("<html><noscript>bot</noscript></html>")
    with pytest.raises(MissingKey) as ei:
        world("SPY", sources=[av, stooq])
    msg = str(ei.value)
    assert "anti-bot" not in msg and "stooq:" not in msg


def test_keyed_av_fail_keeps_all_sources_failed():
    # A key WAS set (synthetic) but AV throttled + Stooq walled -> genuine AllSourcesFailed,
    # NOT MissingKey (key is present, so it is a real all-sources failure).
    av = _av_source(json.dumps({"Note": "throttled"}))  # keyed (_FAKE_KEY) + throttle
    stooq = _stooq_source("<html><noscript>bot</noscript></html>")
    client = default_world_index_client(sources=[av, stooq])
    with pytest.raises(AllSourcesFailed):
        client.get_history("SPY")


def test_av_serves_when_key_set_no_missing_key():
    # When AV serves with a key, neither error is raised (sanity guard for the branch).
    av = _av_source(_av_payload())
    hist = default_world_index_client(sources=[av]).get_history("SPY")
    assert hist.source == "alphavantage"


# =========================================================================== #
# #193 round-2 — Stooq is SPY-only; non-SPY never falls over to ^SPX;
# the failover client is stateless (concurrency-safe). (BLOCK B1/B2/B3)
# =========================================================================== #
_NON_SPY = ["QQQ", "^N225", "^SSEC", "^STI"]


# --- B1: a WORKING Stooq must NEVER serve ^SPX under a non-SPY symbol --- #
@pytest.mark.parametrize("asked", _NON_SPY)
def test_b1_non_spy_keyed_throttled_av_working_stooq_raises_naming_symbol(asked):
    # key set + AV throttled + a fully-WORKING Stooq leg. Because Stooq is SPY-only
    # it is now incapable for a non-SPY symbol, so the only capable source (AV) fails
    # -> AllSourcesFailed naming the symbol. It must NOT relabel ^SPX as `asked`.
    av = _av_source(json.dumps({"Note": "throttled"}))  # keyed (_FAKE_KEY) + throttle
    stooq = _stooq_source(_stooq_csv())  # a genuinely working Stooq CSV leg
    client = default_world_index_client(sources=[av, stooq])
    with pytest.raises(AllSourcesFailed) as ei:
        client.get_history(asked)
    assert asked in str(ei.value)
    # belt-and-suspenders: the Stooq source itself reports it cannot serve a non-SPY symbol
    assert _stooq_source(_stooq_csv()).supports(asked) is False


@pytest.mark.parametrize("asked", _NON_SPY)
def test_b1_non_spy_no_key_working_stooq_raises_missing_key(asked, monkeypatch):
    # no AV key + a fully-WORKING Stooq leg. AV is keyless-incapable, Stooq is SPY-only
    # incapable -> no capable source -> AllSourcesFailed -> caught (no key) -> MissingKey
    # naming the env var + the symbol (never a ^SPX series).
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    av = AlphaVantageIndexSource(api_key=None, http_get=lambda *a, **k: _av_payload())
    stooq = _stooq_source(_stooq_csv())
    client = default_world_index_client(sources=[av, stooq])
    with pytest.raises(MissingKey) as ei:
        client.get_history(asked)
    msg = str(ei.value)
    assert "ALPHAVANTAGE_API_KEY" in msg
    assert asked in msg


def test_b1_stooq_supports_only_spy():
    # SPY (and the keyless/None default) stay capable; every other symbol is skipped.
    stooq = _stooq_source(_stooq_csv())
    assert stooq.supports("SPY") is True
    assert stooq.supports("spy") is True
    assert stooq.supports() is True       # default → SPY → capable (direct-source contract)
    assert stooq.supports(None) is True
    for asked in _NON_SPY:
        assert stooq.supports(asked) is False


def test_b1_stooq_get_history_refuses_non_spy_defense_in_depth():
    # Defense-in-depth: even a DIRECT get_history call on a non-SPY symbol must refuse
    # (InvalidData naming the symbol) rather than relabel the ^SPX series.
    stooq = _stooq_source(_stooq_csv())
    for asked in _NON_SPY:
        with pytest.raises(InvalidData) as ei:
            stooq.get_history(asked)
        assert asked in str(ei.value)
    # and SPY still serves ^SPX as before
    hist = stooq.get_history("SPY")
    assert hist.source == "stooq"
    assert hist.provider_symbol == "^SPX"


# --- B2: empty-window for a proxy symbol must name the symbol, no ^SPX fallover --- #
def test_b2_non_spy_empty_window_raises_naming_symbol_no_spx():
    # A valid AV envelope whose bars all fall OUTSIDE the requested window -> EmptyData
    # naming the symbol; with Stooq now SPY-only there is no capable fallback, so the
    # client raises AllSourcesFailed naming the symbol (never a ^SPX series).
    #
    # The window deliberately OVERLAPS the Stooq CSV (2024-01-03) but NOT the AV bars
    # (AV has only 2024-01-02). Pre-fix, AV's empty-window EmptyData fell over to a
    # WORKING Stooq → ^SPX relabeled as ^N225; the fix (Stooq SPY-only) makes that
    # structurally impossible.
    av = _av_source(  # keyed, valid envelope with a bar ONLY on 2024-01-02
        _av_payload(
            {"2024-01-02": ("100.0", "101.0", "99.0", "100.5", "10")},
            meta_symbol="EWJ",
        )
    )
    stooq = _stooq_source(_stooq_csv())  # working Stooq with 2024-01-02..04 data
    client = default_world_index_client(sources=[av, stooq])
    with pytest.raises(AllSourcesFailed) as ei:
        client.get_history("^N225", start=date(2024, 1, 3), end=date(2024, 1, 3))
    assert "^N225" in str(ei.value)


def test_b2_av_empty_window_error_names_symbol():
    # The AV empty-window EmptyData itself names the symbol (Q5 "name the symbol" rule).
    src = _av_source(_av_payload(meta_symbol="EWJ"))
    with pytest.raises(EmptyData) as ei:
        src.get_history("^N225", start=date(2030, 1, 1), end=date(2030, 1, 2))
    assert "^N225" in str(ei.value)


def test_b2_stooq_empty_window_error_names_symbol():
    # The Stooq empty-window EmptyData names the symbol too (consistency, SPY only).
    src = _stooq_source(_stooq_csv())
    with pytest.raises(EmptyData) as ei:
        src.get_history("SPY", start=date(2030, 1, 1), end=date(2030, 1, 2))
    assert "SPY" in str(ei.value)


# --- B3: stateless client (no _requested_symbol), no cross-call state bleed --- #
def test_b3_client_has_no_requested_symbol_state():
    client = default_world_index_client(sources=[_av_source(_av_payload())])
    assert not hasattr(client, "_requested_symbol")


def test_b3_shared_client_no_cross_call_state_bleed():
    # ONE client, two get_history calls for DIFFERENT symbols served per-call by AV.
    # Each result must carry its OWN symbol + proxy_for (proving no instance-state bleed).
    payloads = {"QQQ": _av_payload(meta_symbol="QQQ"), "^N225": _av_payload(meta_symbol="EWJ")}

    def _g(url, params=None, headers=None):
        ticker = (params or {}).get("symbol")
        # QQQ→QQQ, ^N225→EWJ ; map the fetched AV ticker back to a matching payload
        if ticker == "QQQ":
            return payloads["QQQ"]
        return payloads["^N225"]

    av = AlphaVantageIndexSource(api_key=_FAKE_KEY, http_get=_g)
    client = default_world_index_client(sources=[av])

    h_qqq = client.get_history("QQQ")
    h_n225 = client.get_history("^N225")

    assert h_qqq.symbol == "QQQ"
    assert h_qqq.proxy_for is None
    assert h_qqq.provider_symbol == "QQQ"

    assert h_n225.symbol == "^N225"
    assert h_n225.proxy_for == "^N225"
    assert h_n225.provider_symbol == "EWJ"
