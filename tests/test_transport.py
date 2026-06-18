"""Focused tests for the shared HTTP transport base (``vnfin.transport``).

Everything here is synthetic: a fake ``http_get`` callable, an obviously-fake URL,
and fabricated JSON. No network and no real provider data.
"""
from __future__ import annotations

import json

import pytest

from vnfin.exceptions import InvalidData, SourceUnavailable
from vnfin.transport import DEFAULT_TIMEOUT, DEFAULT_UA, HttpDataSource

FAKE_URL = "https://fake.invalid/api/v1/thing"


class _Probe(HttpDataSource):
    """Minimal concrete source so the base helpers can be exercised directly."""

    NAME = "probe"


def _capture(text):
    """A fake http_get recording every call; returns canned ``text``."""

    def _g(url, params=None, headers=None, json_body=None):
        _g.calls.append(
            {"url": url, "params": params, "headers": headers, "json_body": json_body}
        )
        return text

    _g.calls = []
    return _g


def _raising(exc):
    def _g(url, params=None, headers=None, json_body=None):
        raise exc

    return _g


# --- constants ----------------------------------------------------------- #

def test_default_ua_is_a_browser_string():
    assert "Mozilla/5.0" in DEFAULT_UA
    assert "Chrome" in DEFAULT_UA


def test_default_timeout_is_positive_number():
    assert isinstance(DEFAULT_TIMEOUT, (int, float))
    assert DEFAULT_TIMEOUT > 0


# --- injection wiring ---------------------------------------------------- #

def test_injected_http_get_is_used():
    get = _capture("hello")
    probe = _Probe(http_get=get)
    assert probe._request_text(FAKE_URL) == "hello"
    assert get.calls[0]["url"] == FAKE_URL


def test_default_http_get_used_when_none_injected():
    probe = _Probe()
    # Without injection the base wires its own default client (network-bound, not
    # called here) — we only assert it is the bound default method.
    assert probe._http_get == probe._default_http_get


def test_custom_timeout_is_stored():
    probe = _Probe(timeout=3.5)
    assert probe._timeout == 3.5


# --- GET request_text ---------------------------------------------------- #

def test_request_text_get_passes_three_positional_args():
    """GET callers must keep the legacy (url, params, headers) 3-arg signature."""
    seen = {}

    def _g(url, params, headers):  # exactly 3 positional, no json_body kwarg
        seen.update(url=url, params=params, headers=headers)
        return "ok"

    probe = _Probe(http_get=_g)
    out = probe._request_text(FAKE_URL, params={"q": "FAKESYM"}, headers={"X": "1"})
    assert out == "ok"
    assert seen == {"url": FAKE_URL, "params": {"q": "FAKESYM"}, "headers": {"X": "1"}}


def test_request_text_get_does_not_pass_json_body():
    get = _capture("ok")
    _Probe(http_get=get)._request_text(FAKE_URL, params={"a": 1})
    # json_body stays None on a GET (default kwarg of the capture stub).
    assert get.calls[0]["json_body"] is None


# --- POST request_text --------------------------------------------------- #

def test_request_text_post_passes_json_body():
    """POST callers get the 4-arg signature with json_body."""
    get = _capture("posted")
    body = {"productId": 99999, "isAllData": 1}
    out = _Probe(http_get=get)._request_text(FAKE_URL, json_body=body)
    assert out == "posted"
    assert get.calls[0]["json_body"] == body


def test_request_text_post_uses_four_positional_args():
    seen = {}

    def _g(url, params, headers, json_body):  # exactly 4 positional
        seen.update(url=url, params=params, headers=headers, json_body=json_body)
        return "ok"

    body = {"k": "v"}
    _Probe(http_get=_g)._request_text(FAKE_URL, headers={"H": "1"}, json_body=body)
    assert seen == {"url": FAKE_URL, "params": None, "headers": {"H": "1"}, "json_body": body}


# --- transport error wrapping -------------------------------------------- #

@pytest.mark.parametrize(
    "exc",
    [ConnectionError("boom"), TimeoutError("slow"), OSError("net down"), ValueError("x")],
)
def test_transport_error_wrapped_as_source_unavailable(exc):
    probe = _Probe(http_get=_raising(exc))
    with pytest.raises(SourceUnavailable):
        probe._request_text(FAKE_URL)


def test_source_unavailable_message_includes_source_name():
    probe = _Probe(http_get=_raising(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable) as ei:
        probe._request_text(FAKE_URL)
    assert "probe" in str(ei.value)


def test_post_transport_error_also_wrapped():
    probe = _Probe(http_get=_raising(ConnectionError("down")))
    with pytest.raises(SourceUnavailable):
        probe._request_text(FAKE_URL, json_body={"a": 1})


# --- request_json -------------------------------------------------------- #

def test_request_json_parses_object():
    payload = {"price": 12345.6, "symbol": "FAKEXAU"}
    probe = _Probe(http_get=_capture(json.dumps(payload)))
    assert probe._request_json(FAKE_URL) == payload


def test_request_json_parses_array():
    payload = [[111, "1", "2", "0", "1.5", "9"]]
    probe = _Probe(http_get=_capture(json.dumps(payload)))
    assert probe._request_json(FAKE_URL) == payload


def test_request_json_non_json_raises_invalid_data():
    probe = _Probe(http_get=_capture("<html>blocked</html>"))
    with pytest.raises(InvalidData):
        probe._request_json(FAKE_URL)


def test_request_json_tolerates_utf8_bom():
    payload = {"ok": True, "v": 42}
    probe = _Probe(http_get=_capture("﻿" + json.dumps(payload)))
    assert probe._request_json(FAKE_URL) == payload


def test_request_json_decodes_bytes_with_bom():
    payload = {"ok": True}
    raw = ("﻿" + json.dumps(payload)).encode("utf-8")
    probe = _Probe(http_get=_capture(raw))
    assert probe._request_json(FAKE_URL) == payload


def test_request_json_transport_error_still_source_unavailable():
    probe = _Probe(http_get=_raising(ConnectionError("boom")))
    with pytest.raises(SourceUnavailable):
        probe._request_json(FAKE_URL)


def test_request_json_post_round_trip():
    payload = {"data": {"rows": [{"code": "FAKEFUND", "id": 70001}]}}
    get = _capture(json.dumps(payload))
    out = _Probe(http_get=get)._request_json(FAKE_URL, json_body={"page": 1})
    assert out == payload
    assert get.calls[0]["json_body"] == {"page": 1}


# --- source name resolution ---------------------------------------------- #

def test_source_name_prefers_name_property():
    class WithName(HttpDataSource):
        NAME = "fallback"

        @property
        def name(self):
            return "preferred"

    probe = WithName(http_get=_raising(ConnectionError("x")))
    with pytest.raises(SourceUnavailable) as ei:
        probe._request_text(FAKE_URL)
    assert "preferred" in str(ei.value)


def test_source_name_falls_back_to_NAME():
    class OnlyNAME(HttpDataSource):
        NAME = "only_name"

    probe = OnlyNAME(http_get=_raising(ConnectionError("x")))
    with pytest.raises(SourceUnavailable) as ei:
        probe._request_text(FAKE_URL)
    assert "only_name" in str(ei.value)
