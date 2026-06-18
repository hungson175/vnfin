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
import random as _random
import time as _time

from .exceptions import InvalidData, SourceUnavailable

#: Browser User-Agent sent by the default client. Several VN/finance feeds reject the
#: stock httpx UA, so every source presents a common desktop-Chrome UA.
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

#: Default per-request timeout (seconds).
DEFAULT_TIMEOUT = 25.0

#: Default number of *extra* attempts after the first on a transient failure. ``0``
#: keeps the historical behavior (one attempt, no backoff) so existing behavior and
#: test timing are unchanged. Opt in by passing ``max_retries=N`` (small, e.g. 3).
DEFAULT_MAX_RETRIES = 0

#: Base backoff (seconds) for the first retry; doubles each subsequent retry and is
#: then jittered. Only used when ``max_retries`` > 0.
DEFAULT_BACKOFF_BASE = 0.5

#: Upper bound (seconds) on any single backoff sleep, before jitter.
DEFAULT_BACKOFF_MAX = 8.0


def _is_transient(exc: BaseException) -> bool:
    """Return True if ``exc`` is a *transient* transport failure worth retrying.

    Transient = the request might well succeed if retried shortly:

    * stdlib :class:`ConnectionError` / :class:`TimeoutError` (covers
      ``ConnectionResetError`` and friends),
    * any ``httpx.TransportError`` (connect/read/write/pool timeouts, network resets,
      protocol errors) — detected structurally so ``httpx`` need not be importable,
    * an HTTP ``429`` or ``5xx`` surfaced as ``httpx.HTTPStatusError``.

    Everything else (e.g. a ``4xx`` other than 429, a ``ValueError``) is treated as
    non-transient and re-raised immediately by the caller.
    """
    # stdlib network failures (ConnectionResetError is a ConnectionError subclass).
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True

    # httpx is optional at import time; classify by attribute/structure so this module
    # never hard-depends on httpx being installed for the injected-stub path.
    try:
        import httpx  # noqa: WPS433 (local import keeps stdlib-only callers light)
    except Exception:  # pragma: no cover - httpx is a declared dep; defensive only
        return False

    if isinstance(exc, httpx.TransportError):
        # Connect/read/write/pool timeouts + network/protocol errors are all transient.
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status = getattr(getattr(exc, "response", None), "status_code", None)
        return status == 429 or (isinstance(status, int) and 500 <= status <= 599)
    return False


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

    def __init__(
        self,
        http_get=None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        backoff_max: float = DEFAULT_BACKOFF_MAX,
        cache_ttl: float | None = None,
        sleep=None,
        rand=None,
        clock=None,
    ):
        # ``http_get`` is injectable for testing. GET callers use the
        # ``(url, params, headers)`` signature; POST callers additionally pass
        # ``json_body`` as a 4th positional arg. The default client accepts both.
        self._http_get = http_get or self._default_http_get
        self._timeout = timeout

        # --- retry/backoff (opt-in) -------------------------------------- #
        # ``max_retries`` is the number of *extra* attempts after the first. ``0``
        # (default) reproduces the historical single-attempt behavior exactly, so no
        # existing test changes timing or call count.
        self._max_retries = max(0, int(max_retries))
        self._backoff_base = backoff_base
        self._backoff_max = backoff_max
        # Injectable so tests run instantly and deterministically.
        self._sleep = sleep or _time.sleep
        self._rand = rand or _random.random

        # --- response cache (opt-in, OFF by default) --------------------- #
        # ``cache_ttl=None`` (default) means no caching: behavior is unchanged. A
        # positive TTL enables an in-memory cache keyed by (url, params, json_body).
        self._cache_ttl = cache_ttl
        self._clock = clock or _time.monotonic
        self._cache: dict = {} if cache_ttl is not None else None

    # --- name used in error messages ------------------------------------- #
    @property
    def _source_name(self) -> str:
        # Prefer an instance/class ``name`` (property or attribute) when present,
        # else fall back to ``NAME`` so error strings stay stable per adapter.
        name = getattr(self, "name", None)
        if isinstance(name, str) and name:
            return name
        return self.NAME

    # --- cache key ------------------------------------------------------- #
    @staticmethod
    def _cache_key(url, params, json_body):
        """Stable, hashable key for the response cache.

        ``params``/``json_body`` are dict-like, so they are normalized to a sorted,
        JSON-serialized form to be hashable and order-independent.
        """
        def _norm(obj):
            if obj is None:
                return None
            try:
                return _json.dumps(obj, sort_keys=True, default=str)
            except TypeError:
                return repr(obj)

        return (url, _norm(params), _norm(json_body))

    # --- transport helpers ----------------------------------------------- #
    def _request_text(self, url, params=None, headers=None, json_body=None) -> str:
        """Fetch ``url`` and return the response text.

        Issues a POST with ``json_body`` when provided, else a GET. Any transport-level
        error (network, timeout, non-2xx) is wrapped as
        :class:`~vnfin.exceptions.SourceUnavailable` so callers/failover can recover.

        The injected ``http_get`` is invoked with the exact positional arity each
        domain already used: 3 args (``url, params, headers``) for GET and 4 args
        (``..., json_body``) for POST. This keeps every existing test stub valid.

        When ``max_retries`` > 0, *transient* failures (timeouts, connection resets,
        HTTP 429/5xx) are retried with jittered exponential backoff; non-transient
        errors raise immediately. When a positive ``cache_ttl`` was configured, a hit
        within the TTL window returns the cached text without calling ``http_get``.
        ``headers`` does not participate in the cache key.
        """
        # --- cache lookup ------------------------------------------------ #
        key = None
        if self._cache is not None:
            key = self._cache_key(url, params, json_body)
            hit = self._cache.get(key)
            if hit is not None:
                expires_at, value = hit
                if self._clock() < expires_at:
                    return value
                # expired entry: drop it and fall through to a fresh fetch.
                del self._cache[key]

        text = self._fetch_with_retry(url, params, headers, json_body)

        # --- cache store ------------------------------------------------- #
        if self._cache is not None:
            self._cache[key] = (self._clock() + self._cache_ttl, text)
        return text

    def _fetch_with_retry(self, url, params, headers, json_body):
        """Call ``http_get`` with bounded, jittered exponential backoff on transients.

        Returns the response text. Non-transient errors (and transient errors after the
        retry budget is exhausted) are wrapped as
        :class:`~vnfin.exceptions.SourceUnavailable`.
        """
        attempt = 0
        while True:
            try:
                if json_body is not None:
                    return self._http_get(url, params, headers, json_body)
                return self._http_get(url, params, headers)
            except Exception as exc:  # transport-level
                # Retry only transient failures, and only while budget remains.
                if attempt < self._max_retries and _is_transient(exc):
                    self._sleep(self._backoff_delay(attempt))
                    attempt += 1
                    continue
                raise SourceUnavailable(
                    f"{self._source_name} transport error: {exc}"
                ) from exc

    def _backoff_delay(self, attempt: int) -> float:
        """Jittered exponential backoff for retry ``attempt`` (0-based).

        ``base * 2**attempt`` capped at ``backoff_max``, then full-jittered into
        ``[0, capped]`` so concurrent clients don't retry in lockstep.
        """
        capped = min(self._backoff_base * (2 ** attempt), self._backoff_max)
        return self._rand() * capped

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
