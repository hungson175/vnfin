"""Focused tests for the shared HTTP transport base (``vnfin.transport``).

Everything here is synthetic: a fake ``http_get`` callable, an obviously-fake URL,
and fabricated JSON. No network and no real provider data.
"""
from __future__ import annotations

import json

import pytest

from vnfin.exceptions import InvalidData, SourceUnavailable
from vnfin.transport import (
    DEFAULT_TIMEOUT,
    DEFAULT_UA,
    HttpDataSource,
    redact_secrets,
)

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


# --- B4: secret redaction in wrapped errors / cache keys ----------------- #

# OBVIOUSLY-FAKE dummy BYOK key. Deliberately NOT a single high-entropy blob:
# hyphen-separated all-caps words so the no-secrets scanner (and any human reader)
# can see at a glance it is fabricated, never a real-looking credential.
FAKE_API_KEY = "FAKE-DUMMY-KEY-NOT-REAL-0000"


def test_redact_secrets_redacts_query_param_in_url():
    leaky = (
        "https://fake.invalid/series/observations"
        f"?series_id=FAKESERIES&api_key={FAKE_API_KEY}&file_type=json"
    )
    out = redact_secrets(leaky)
    assert FAKE_API_KEY not in out
    assert "api_key=REDACTED" in out
    # Non-secret params are left intact.
    assert "series_id=FAKESERIES" in out
    assert "file_type=json" in out


def test_redact_secrets_handles_key_token_access_token():
    leaky = f"url?key={FAKE_API_KEY}&token=FAKETOKEN111&access_token=FAKEACCESS222"
    out = redact_secrets(leaky)
    for secret in (FAKE_API_KEY, "FAKETOKEN111", "FAKEACCESS222"):
        assert secret not in out
    assert out.count("REDACTED") == 3


def test_redact_secrets_redacts_params_dict_repr():
    # Mirrors a wrapped error that embeds repr({"api_key": "..."}).
    leaky = "transport error: {'series_id': 'FAKESERIES', 'api_key': '" + FAKE_API_KEY + "'}"
    out = redact_secrets(leaky)
    assert FAKE_API_KEY not in out
    assert "FAKESERIES" in out  # non-secret survives


def test_redact_secrets_redacts_authorization_header():
    leaky = "headers={'Authorization': 'Bearer FAKEBEARERTOKEN333'}"
    out = redact_secrets(leaky)
    assert "FAKEBEARERTOKEN333" not in out
    assert "Authorization" in out


def _fred_style_http_status_error():
    """Build a real ``httpx.HTTPStatusError`` whose message embeds the full FRED
    request URL (query string + dummy api_key) exactly as ``raise_for_status``
    would — the precise leak path described in review B4.
    """
    import httpx

    url = (
        "https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=FAKESERIES&api_key={FAKE_API_KEY}&file_type=json"
    )
    request = httpx.Request("GET", url)
    response = httpx.Response(400, request=request, text="Bad Request: invalid api_key")
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return exc
    raise AssertionError("raise_for_status did not raise")  # pragma: no cover


def test_fred_4xx_does_not_leak_api_key_in_source_unavailable():
    """An HTTP 4xx from a FRED-style request carrying a dummy api_key must NOT leak
    the key in the raised SourceUnavailable message (B4 regression)."""
    err = _fred_style_http_status_error()
    # Sanity: the raw error string really does contain the secret (the leak).
    assert FAKE_API_KEY in str(err)

    probe = _Probe(http_get=_raising(err))
    with pytest.raises(SourceUnavailable) as ei:
        probe._request_text(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": "FAKESERIES", "api_key": FAKE_API_KEY, "file_type": "json"},
        )
    message = str(ei.value)
    assert FAKE_API_KEY not in message
    assert "REDACTED" in message


def test_fred_5xx_does_not_leak_api_key_in_source_unavailable():
    """Same redaction guarantee for a 5xx surfaced as HTTPStatusError."""
    import httpx

    url = (
        "https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=FAKESERIES&api_key={FAKE_API_KEY}"
    )
    request = httpx.Request("GET", url)
    response = httpx.Response(503, request=request, text="Service Unavailable")
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as err:
        probe = _Probe(http_get=_raising(err))
        with pytest.raises(SourceUnavailable) as ei:
            probe._request_text(url)
        assert FAKE_API_KEY not in str(ei.value)


def test_transport_error_does_not_leak_api_key_via_cause_or_traceback():
    """B4 regression: the redacted SourceUnavailable must NOT re-expose the BYOK key
    through Python's exception chaining (``__cause__``) or a formatted traceback.

    The raw ``httpx.HTTPStatusError`` carries the full request URL (api_key and all)
    in its own ``str``. Chaining it with ``raise ... from exc`` would surface that
    secret in ``exc.__cause__`` and in ``traceback.format_exception(...)`` even though
    the user-facing message is redacted. The wrap must use ``from None`` (or chain a
    sanitized exception) so the secret never travels with the exception.
    """
    import traceback

    err = _fred_style_http_status_error()
    # Sanity: the raw cause really does contain the secret (this is the leak source).
    assert FAKE_API_KEY in str(err)

    probe = _Probe(http_get=_raising(err))
    with pytest.raises(SourceUnavailable) as ei:
        probe._request_text(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": "FAKESERIES", "api_key": FAKE_API_KEY, "file_type": "json"},
        )
    raised = ei.value

    # (a) The user-facing message is redacted.
    assert FAKE_API_KEY not in str(raised)

    # (b) The exception chain carries no secret: either no cause at all, or a cause
    #     whose string is itself free of the key.
    assert raised.__cause__ is None or FAKE_API_KEY not in str(raised.__cause__)

    # (b2) ``__context__`` must also be clean: ``from None`` only suppresses display,
    #      so the fix raises OUTSIDE the except suite to clear the implicit context.
    assert raised.__context__ is None or FAKE_API_KEY not in str(raised.__context__)

    # (c) A fully-formatted traceback (the realistic log/CI failure path) is clean.
    formatted = "".join(
        traceback.format_exception(type(raised), raised, raised.__traceback__)
    )
    assert FAKE_API_KEY not in formatted


def test_cache_key_redacts_secret_params():
    """The response cache key must not embed BYOK secrets (B4)."""
    key = HttpDataSource._cache_key(
        f"https://fake.invalid/obs?api_key={FAKE_API_KEY}",
        {"series_id": "FAKESERIES", "api_key": FAKE_API_KEY},
        None,
        {"Authorization": f"Bearer {FAKE_API_KEY}"},
    )
    flat = repr(key)
    assert FAKE_API_KEY not in flat
    assert "FAKESERIES" in flat  # non-secret survives, key stays useful


def test_invalid_max_retries_non_numeric_raises():
    with pytest.raises(TypeError):
        HttpDataSource(http_get=lambda *a: "ok", max_retries="not-an-int")


def test_invalid_max_retries_negative_raises():
    with pytest.raises(ValueError):
        HttpDataSource(http_get=lambda *a: "ok", max_retries=-1)


def test_invalid_cache_ttl_non_numeric_raises():
    with pytest.raises(TypeError):
        HttpDataSource(http_get=lambda *a: "ok", cache_ttl="x")


def test_invalid_cache_ttl_negative_raises():
    with pytest.raises(ValueError):
        HttpDataSource(http_get=lambda *a: "ok", cache_ttl=-1.0)


def test_cache_includes_headers_in_key():
    """Issue #31: different auth headers must not share cache entries."""
    calls = []
    now = [0.0]

    def fake_get(url, params, headers):
        calls.append(dict(headers or {}))
        return f"response-for-{headers.get('Authorization')}"

    probe = HttpDataSource(http_get=fake_get, cache_ttl=3600, clock=lambda: now[0])
    assert probe._request_text("u", headers={"Authorization": "Bearer A"}) == "response-for-Bearer A"
    assert probe._request_text("u", headers={"Authorization": "Bearer B"}) == "response-for-Bearer B"
    assert len(calls) == 2


def test_cache_distinguishes_requests_with_different_secret_params():
    """Issue #22: requests differing only by secret param values must not collide."""
    calls = []
    now = [0.0]

    def fake_get(url, params, headers):
        calls.append(dict(params or {}))
        return f"response-for-{params.get('api_key')}"

    probe = HttpDataSource(http_get=fake_get, cache_ttl=3600, clock=lambda: now[0])
    assert probe._request_text("u", params={"api_key": "A", "q": "x"}) == "response-for-A"
    assert probe._request_text("u", params={"api_key": "B", "q": "x"}) == "response-for-B"
    assert len(calls) == 2


def test_redact_secrets_covers_access_key_and_apikey():
    """Issue #38: common API-key variants must be redacted."""
    for name in ("access_key", "apikey", "apiKey"):
        raw = f"url?{name}=SECRET123&x=1"
        out = redact_secrets(raw)
        assert "SECRET123" not in out
        assert f"{name}=REDACTED" in out


def test_redact_secrets_covers_required_camelcase_variants():
    """B2 regression: issue #38 camelCase secret names must be redacted."""
    for name in ("accessKey", "secretKey", "authToken", "apiToken", "appKey"):
        raw = f"url?{name}=SECRET123&x=1"
        out = redact_secrets(raw)
        assert "SECRET123" not in out, name
        assert f"{name}=REDACTED" in out, name


def test_cache_key_hashes_url_secret_identity():
    """B1 regression: secret values embedded directly in the URL must participate
    in the cache key identity so different credentials do not share a cache entry.
    """
    key_a = HttpDataSource._cache_key("https://fake.invalid/data?api_key=ALPHA", None, None, None)
    key_b = HttpDataSource._cache_key("https://fake.invalid/data?api_key=BETA", None, None, None)
    assert key_a != key_b
    flat = repr(key_a) + repr(key_b)
    assert "ALPHA" not in flat
    assert "BETA" not in flat
    assert "REDACTED" in flat


def test_cache_distinguishes_url_secret_query_values():
    """B1 regression end-to-end: URLs differing only by a secret query value."""
    calls = []
    now = [0.0]

    def fake_get(url, params=None, headers=None, json_body=None):
        calls.append(url)
        return "response-for-" + url.rsplit("=", 1)[-1]

    probe = HttpDataSource(http_get=fake_get, cache_ttl=3600, clock=lambda: now[0])
    assert probe._request_text("https://fake.invalid/data?api_key=ALPHA") == "response-for-ALPHA"
    assert probe._request_text("https://fake.invalid/data?api_key=BETA") == "response-for-BETA"
    assert len(calls) == 2


def test_cache_distinguishes_x_api_key_header_values():
    """B3 regression: X-API-Key header values must participate in cache identity."""
    calls = []
    now = [0.0]

    def fake_get(url, params=None, headers=None, json_body=None):
        calls.append(dict(headers or {}))
        return "response-for-" + headers.get("X-API-Key", "")

    probe = HttpDataSource(http_get=fake_get, cache_ttl=3600, clock=lambda: now[0])
    assert probe._request_text("u", headers={"X-API-Key": "ALPHA"}) == "response-for-ALPHA"
    assert probe._request_text("u", headers={"X-API-Key": "BETA"}) == "response-for-BETA"
    assert len(calls) == 2
    # The cached key representation must not leak the plaintext header value.
    flat = repr(list(probe._cache.keys()))
    assert "ALPHA" not in flat
    assert "BETA" not in flat
