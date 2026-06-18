"""Focused tests for the opt-in retry/backoff and response cache added to
``vnfin.transport.HttpDataSource``.

Everything is synthetic: a fake ``http_get`` callable, an obviously-fake URL, and
fabricated payloads. No network, no real provider data. Sleep/clock/rand are injected
so the tests run instantly and deterministically.
"""
from __future__ import annotations

import json

import pytest

from vnfin.exceptions import InvalidData, SourceUnavailable
from vnfin.transport import HttpDataSource, _is_transient

FAKE_URL = "https://fake.invalid/api/v1/thing"


class _Probe(HttpDataSource):
    NAME = "probe"


def _seq_get(*results):
    """A fake http_get that yields ``results`` in order.

    Each item is either an Exception (raised) or a value (returned). Records every
    call so call-count assertions are possible.
    """
    seq = list(results)

    def _g(url, params=None, headers=None, json_body=None):
        _g.calls.append({"url": url, "params": params, "json_body": json_body})
        item = seq[min(len(_g.calls) - 1, len(seq) - 1)]
        if isinstance(item, BaseException):
            raise item
        return item

    _g.calls = []
    return _g


class _FakeClock:
    """A monotonic clock whose value the test advances explicitly."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, dt):
        self.now += dt


def _no_sleep():
    """A sleep stub that records requested delays without actually sleeping."""
    delays = []

    def _s(d):
        delays.append(d)

    _s.delays = delays
    return _s


# --- transient classification ------------------------------------------- #

def test_stdlib_connection_and_timeout_are_transient():
    assert _is_transient(ConnectionError("reset"))
    assert _is_transient(ConnectionResetError("peer reset"))
    assert _is_transient(TimeoutError("slow"))


def test_value_error_is_not_transient():
    assert not _is_transient(ValueError("malformed"))


def test_httpx_transport_error_is_transient():
    import httpx

    assert _is_transient(httpx.ConnectTimeout("connect timed out"))
    assert _is_transient(httpx.ReadTimeout("read timed out"))
    assert _is_transient(httpx.ConnectError("conn refused"))


def test_httpx_429_and_5xx_are_transient_but_4xx_is_not():
    import httpx

    req = httpx.Request("GET", FAKE_URL)

    def _status_err(code):
        resp = httpx.Response(code, request=req)
        return httpx.HTTPStatusError("boom", request=req, response=resp)

    assert _is_transient(_status_err(429))
    assert _is_transient(_status_err(500))
    assert _is_transient(_status_err(503))
    assert not _is_transient(_status_err(404))
    assert not _is_transient(_status_err(400))
    assert not _is_transient(_status_err(403))


# --- retry on transient then success ------------------------------------ #

def test_retry_on_transient_then_success():
    get = _seq_get(ConnectionError("reset"), ConnectionError("reset"), "OK")
    sleep = _no_sleep()
    probe = _Probe(http_get=get, max_retries=3, sleep=sleep, rand=lambda: 1.0)

    assert probe._request_text(FAKE_URL) == "OK"
    assert len(get.calls) == 3  # two failures + one success
    assert len(sleep.delays) == 2  # one backoff before each retry


def test_retry_backoff_is_exponential_and_jittered():
    get = _seq_get(ConnectionError("x"), ConnectionError("x"), ConnectionError("x"), "OK")
    sleep = _no_sleep()
    # rand fixed at 1.0 => full backoff (no shrinking) so we can assert the curve.
    probe = _Probe(
        http_get=get,
        max_retries=3,
        backoff_base=0.5,
        backoff_max=8.0,
        sleep=sleep,
        rand=lambda: 1.0,
    )
    assert probe._request_text(FAKE_URL) == "OK"
    # 0.5 * 2**0, 0.5 * 2**1, 0.5 * 2**2
    assert sleep.delays == [0.5, 1.0, 2.0]


def test_backoff_is_capped_at_backoff_max():
    probe = _Probe(http_get=_seq_get("x"), backoff_base=1.0, backoff_max=3.0, rand=lambda: 1.0)
    # attempt 10 would be 1024 without the cap.
    assert probe._backoff_delay(10) == 3.0


def test_jitter_shrinks_the_delay():
    probe = _Probe(http_get=_seq_get("x"), backoff_base=4.0, rand=lambda: 0.25)
    # full-jitter: rand * capped => 0.25 * 4.0
    assert probe._backoff_delay(0) == 1.0


# --- exhausting the retry budget still raises --------------------------- #

def test_transient_failures_beyond_budget_raise_source_unavailable():
    get = _seq_get(ConnectionError("a"), ConnectionError("b"))
    sleep = _no_sleep()
    probe = _Probe(http_get=get, max_retries=1, sleep=sleep, rand=lambda: 0.0)
    with pytest.raises(SourceUnavailable):
        probe._request_text(FAKE_URL)
    assert len(get.calls) == 2  # first attempt + one retry, then give up


# --- no retry on non-transient ------------------------------------------ #

def test_no_retry_on_non_transient():
    get = _seq_get(ValueError("malformed"), "SHOULD_NOT_REACH")
    sleep = _no_sleep()
    probe = _Probe(http_get=get, max_retries=3, sleep=sleep, rand=lambda: 0.0)
    with pytest.raises(SourceUnavailable):
        probe._request_text(FAKE_URL)
    assert len(get.calls) == 1  # raised immediately, no retry
    assert sleep.delays == []


def test_no_retry_on_http_404():
    import httpx

    req = httpx.Request("GET", FAKE_URL)
    resp = httpx.Response(404, request=req)
    err = httpx.HTTPStatusError("not found", request=req, response=resp)
    get = _seq_get(err, "SHOULD_NOT_REACH")
    probe = _Probe(http_get=get, max_retries=3, sleep=_no_sleep(), rand=lambda: 0.0)
    with pytest.raises(SourceUnavailable):
        probe._request_text(FAKE_URL)
    assert len(get.calls) == 1


# --- retries off by default (behavior unchanged) ------------------------ #

def test_retries_off_by_default_single_attempt():
    get = _seq_get(ConnectionError("reset"), "OK")
    probe = _Probe(http_get=get)  # no max_retries => default 0
    with pytest.raises(SourceUnavailable):
        probe._request_text(FAKE_URL)
    assert len(get.calls) == 1  # exactly one attempt, no backoff path


# --- cache off by default ------------------------------------------------ #

def test_cache_off_by_default_every_call_hits_http_get():
    get = _seq_get("A", "B", "C")
    probe = _Probe(http_get=get)  # no cache_ttl => caching disabled
    assert probe._request_text(FAKE_URL) == "A"
    assert probe._request_text(FAKE_URL) == "B"
    assert probe._request_text(FAKE_URL) == "C"
    assert len(get.calls) == 3


# --- cache hit avoids second call --------------------------------------- #

def test_cache_hit_avoids_second_call():
    get = _seq_get("FIRST", "SECOND")
    clock = _FakeClock()
    probe = _Probe(http_get=get, cache_ttl=60.0, clock=clock)
    assert probe._request_text(FAKE_URL, params={"sym": "FAKESYM"}) == "FIRST"
    # Same url+params within TTL: served from cache, http_get not called again.
    assert probe._request_text(FAKE_URL, params={"sym": "FAKESYM"}) == "FIRST"
    assert len(get.calls) == 1


def test_cache_key_param_order_independent():
    get = _seq_get("FIRST", "SECOND")
    probe = _Probe(http_get=get, cache_ttl=60.0, clock=_FakeClock())
    a = probe._request_text(FAKE_URL, params={"a": 1, "b": 2})
    b = probe._request_text(FAKE_URL, params={"b": 2, "a": 1})
    assert a == b == "FIRST"
    assert len(get.calls) == 1


def test_cache_distinguishes_different_params():
    get = _seq_get("FOR_X", "FOR_Y")
    probe = _Probe(http_get=get, cache_ttl=60.0, clock=_FakeClock())
    assert probe._request_text(FAKE_URL, params={"sym": "FAKEX"}) == "FOR_X"
    assert probe._request_text(FAKE_URL, params={"sym": "FAKEY"}) == "FOR_Y"
    assert len(get.calls) == 2


def test_cache_distinguishes_post_json_body():
    get = _seq_get("BODY1", "BODY2")
    probe = _Probe(http_get=get, cache_ttl=60.0, clock=_FakeClock())
    assert probe._request_text(FAKE_URL, json_body={"page": 1}) == "BODY1"
    assert probe._request_text(FAKE_URL, json_body={"page": 2}) == "BODY2"
    assert len(get.calls) == 2


def test_cache_includes_headers_in_key():
    get = _seq_get("CACHED", "FRESH")
    probe = _Probe(http_get=get, cache_ttl=60.0, clock=_FakeClock())
    assert probe._request_text(FAKE_URL, headers={"X": "1"}) == "CACHED"
    # Different headers, same url+params => cache miss (headers carry auth/entitlement).
    assert probe._request_text(FAKE_URL, headers={"X": "2"}) == "FRESH"
    assert len(get.calls) == 2


# --- TTL expiry ---------------------------------------------------------- #

def test_ttl_expiry_triggers_refetch():
    get = _seq_get("OLD", "NEW")
    clock = _FakeClock()
    probe = _Probe(http_get=get, cache_ttl=30.0, clock=clock)
    assert probe._request_text(FAKE_URL) == "OLD"
    clock.advance(29.0)  # still within TTL
    assert probe._request_text(FAKE_URL) == "OLD"
    assert len(get.calls) == 1
    clock.advance(2.0)  # now 31s elapsed > 30s TTL
    assert probe._request_text(FAKE_URL) == "NEW"
    assert len(get.calls) == 2


def test_ttl_expiry_then_re_caches_fresh_value():
    get = _seq_get("V1", "V2", "V3")
    clock = _FakeClock()
    probe = _Probe(http_get=get, cache_ttl=10.0, clock=clock)
    assert probe._request_text(FAKE_URL) == "V1"
    clock.advance(11.0)
    assert probe._request_text(FAKE_URL) == "V2"  # refetch
    # The fresh value is now cached for another TTL window.
    assert probe._request_text(FAKE_URL) == "V2"
    assert len(get.calls) == 2


# --- cache + retry interplay -------------------------------------------- #

def test_cache_stores_only_successful_value_after_retry():
    get = _seq_get(ConnectionError("flap"), "GOOD", "UNUSED")
    sleep = _no_sleep()
    probe = _Probe(
        http_get=get,
        max_retries=2,
        cache_ttl=60.0,
        sleep=sleep,
        rand=lambda: 0.0,
        clock=_FakeClock(),
    )
    assert probe._request_text(FAKE_URL) == "GOOD"  # 1 fail + 1 success
    assert probe._request_text(FAKE_URL) == "GOOD"  # served from cache
    assert len(get.calls) == 2  # the cached call did not re-hit http_get


def test_failed_request_is_not_cached():
    get = _seq_get(ConnectionError("a"), ConnectionError("b"), "RECOVERED")
    probe = _Probe(http_get=get, max_retries=0, cache_ttl=60.0, clock=_FakeClock())
    with pytest.raises(SourceUnavailable):
        probe._request_text(FAKE_URL)
    # Nothing cached => the next call actually fetches again.
    with pytest.raises(SourceUnavailable):
        probe._request_text(FAKE_URL)
    assert len(get.calls) == 2


# --- request_json benefits from cache + retry --------------------------- #

def test_request_json_uses_cache_layer():
    payload = {"price": 12345.6, "symbol": "FAKEXAU"}
    get = _seq_get(json.dumps(payload), json.dumps({"other": 1}))
    probe = _Probe(http_get=get, cache_ttl=60.0, clock=_FakeClock())
    assert probe._request_json(FAKE_URL) == payload
    assert probe._request_json(FAKE_URL) == payload  # cache hit
    assert len(get.calls) == 1


def test_request_json_retries_then_parses():
    payload = {"ok": True, "v": 7}
    get = _seq_get(ConnectionError("flap"), json.dumps(payload))
    probe = _Probe(http_get=get, max_retries=2, sleep=_no_sleep(), rand=lambda: 0.0)
    assert probe._request_json(FAKE_URL) == payload
    assert len(get.calls) == 2


def test_request_json_non_json_is_not_retried():
    # InvalidData is raised during parse (after a successful fetch), not a transient.
    get = _seq_get("<html>blocked</html>")
    probe = _Probe(http_get=get, max_retries=3, sleep=_no_sleep(), rand=lambda: 0.0)
    with pytest.raises(InvalidData):
        probe._request_json(FAKE_URL)
    assert len(get.calls) == 1
