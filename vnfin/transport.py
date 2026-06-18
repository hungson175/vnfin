"""Shared HTTP transport base for every vnfin data source.

Before this module each adapter (price UDF, fundamentals, funds, crypto, macro,
gold, indices) carried its own near-identical ``_default_http_get`` plus the same
transport-error wrapping. They all needed the same three things:

1. **IPv4-forced httpx** — datacenter IPv6 is frequently blocked by these providers,
   so the default client binds ``local_address="0.0.0.0"``.
2. **A browser User-Agent** — several feeds reject the default httpx UA.
3. **Transport errors mapped to** :class:`~vnfin.exceptions.SourceUnavailable` — so a
   failover client can move on instead of seeing a raw ``ConnectionError``.

``HttpDataSource`` centralizes all three. Each adapter subclasses it (or constructs
one) and calls :meth:`_request_text` / :meth:`_request_json` instead of re-implementing
the transport. POST-JSON is supported via ``json_body=...`` (used by Fmarket).

Injectable ``http_get`` is **preserved unchanged** so existing unit tests keep working:

* GET callers' stub signature is ``http_get(url, params, headers) -> text``.
* POST callers' stub signature is ``http_get(url, params, headers, json_body) -> text``.

:meth:`_request_*` call the injected callable with exactly the positional arity each
domain already used (3 args for GET, 4 args for POST), so no existing test fixture has
to change. Only when ``json_body`` is given does the 4-arg form get used.
"""
from __future__ import annotations

import json as _json

from .exceptions import InvalidData, SourceUnavailable

#: Browser User-Agent sent by the default client. Several VN/finance feeds reject the
#: stock httpx UA, so every source presents a common desktop-Chrome UA.
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

#: Default per-request timeout (seconds).
DEFAULT_TIMEOUT = 25.0


class HttpDataSource:
    """Mixin/base providing one IPv4-forced, UA-stamped, error-wrapping HTTP transport.

    Subclasses get an injectable ``http_get`` callable (default forces IPv4 + browser
    UA + timeout) and two helpers:

    * :meth:`_request_text` — GET/POST returning the raw response text, transport
      failures wrapped as :class:`~vnfin.exceptions.SourceUnavailable`.
    * :meth:`_request_json` — the same, then JSON-decoded, non-JSON wrapped as
      :class:`~vnfin.exceptions.InvalidData`.

    Parsing/validation of the decoded payload stays in each concrete adapter.
    """

    #: Source name used in wrapped error messages. Subclasses normally set ``NAME``
    #: and/or expose a ``name`` property; this is the fallback.
    NAME = "http"

    def __init__(self, http_get=None, timeout: float = DEFAULT_TIMEOUT):
        # ``http_get`` is injectable for testing. GET callers use the
        # ``(url, params, headers)`` signature; POST callers additionally pass
        # ``json_body`` as a 4th positional arg. The default client accepts both.
        self._http_get = http_get or self._default_http_get
        self._timeout = timeout

    # --- name used in error messages ------------------------------------- #
    @property
    def _source_name(self) -> str:
        # Prefer an instance/class ``name`` (property or attribute) when present,
        # else fall back to ``NAME`` so error strings stay stable per adapter.
        name = getattr(self, "name", None)
        if isinstance(name, str) and name:
            return name
        return self.NAME

    # --- transport helpers ----------------------------------------------- #
    def _request_text(self, url, params=None, headers=None, json_body=None) -> str:
        """Fetch ``url`` and return the response text.

        Issues a POST with ``json_body`` when provided, else a GET. Any transport-level
        error (network, timeout, non-2xx) is wrapped as
        :class:`~vnfin.exceptions.SourceUnavailable` so callers/failover can recover.

        The injected ``http_get`` is invoked with the exact positional arity each
        domain already used: 3 args (``url, params, headers``) for GET and 4 args
        (``..., json_body``) for POST. This keeps every existing test stub valid.
        """
        try:
            if json_body is not None:
                return self._http_get(url, params, headers, json_body)
            return self._http_get(url, params, headers)
        except Exception as exc:  # transport-level
            raise SourceUnavailable(
                f"{self._source_name} transport error: {exc}"
            ) from exc

    def _request_json(self, url, params=None, headers=None, json_body=None):
        """:meth:`_request_text` then JSON-decode.

        Tolerates a UTF-8 BOM. Non-JSON bodies raise
        :class:`~vnfin.exceptions.InvalidData`; transport failures still raise
        :class:`~vnfin.exceptions.SourceUnavailable` (from :meth:`_request_text`).
        """
        text = self._request_text(url, params=params, headers=headers, json_body=json_body)
        if isinstance(text, (bytes, bytearray)):
            text = text.decode("utf-8-sig")
        elif isinstance(text, str):
            text = text.lstrip("﻿")
        try:
            return _json.loads(text)
        except (ValueError, TypeError) as exc:
            raise InvalidData(f"{self._source_name}: non-JSON response") from exc

    # --- default client -------------------------------------------------- #
    def _default_http_get(self, url, params=None, headers=None, json_body=None):  # pragma: no cover - network
        """Default transport: IPv4-forced httpx with a browser UA and timeout.

        GET by default; POST with ``json_body`` when supplied. ``headers`` is merged
        on top of the default ``User-Agent`` so callers can add ``Accept`` /
        ``Content-Type`` without losing the UA.
        """
        import httpx

        transport = httpx.HTTPTransport(local_address="0.0.0.0")  # force IPv4
        hdrs = {"User-Agent": DEFAULT_UA}
        if headers:
            hdrs.update(headers)
        with httpx.Client(transport=transport, timeout=self._timeout, headers=hdrs) as client:
            if json_body is not None:
                resp = client.post(url, params=params, json=json_body)
            else:
                resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.text
