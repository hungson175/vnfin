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
import math as _math
import random as _random
import re as _re
import time as _time

from .exceptions import InvalidData, SourceUnavailable

#: Query-param names whose VALUES are secrets and must never surface in an error
#: message, a cache/debug string, or a log line. Matching is case-insensitive.
#: ``key`` is intentionally last so the longer, more specific names win when a
#: param name contains another (e.g. ``api_key`` is matched as a whole word).
#: Camel-case variants are included for issue #38.
SENSITIVE_PARAMS = (
    "access_key",
    "accessKey",
    "api_key",
    "apiKey",
    "apikey",
    "api_token",
    "apiToken",
    "app_key",
    "appKey",
    "auth_token",
    "authToken",
    "secret_key",
    "secretKey",
    "access_token",
    "accessToken",
    "client_secret",
    "clientSecret",
    "token",
    "key",
)

#: Placeholder substituted for any redacted secret value.
_REDACTED = "REDACTED"

#: Names whose values are secrets for the purpose of cache-key identity. We still
#: redact them in logs/errors, but we keep a deterministic hash of the original
#: value in the cache key so two requests with different credentials do not share
#: a cached response (issues #22, #31, #37, #38).
_SECRET_HASH_KEYS = frozenset(SENSITIVE_PARAMS + ("Authorization",))


def _norm_secret_name(name):
    """Normalize a key name for case/separator-insensitive secret matching.

    Strips ``-`` and ``_`` and lowercases so ``api_key``, ``api-key``,
    ``apiKey`` and ``APIKEY`` all collapse to the same token.
    """
    return str(name).lower().replace("-", "").replace("_", "")


#: Normalized set used for exact-match identity hashing.
_NORMALIZED_SECRET_HASH_KEYS = frozenset(_norm_secret_name(k) for k in _SECRET_HASH_KEYS)

#: Token fragments that mark a key/header name as secret-bearing when present
#: after splitting on ``-``/``_`` (issue #38 residual: ``X-Client-Secret``).
_SENSITIVE_NAME_TOKENS = frozenset({"secret"})


def _is_secret_key_name(name):
    """Return True if ``name`` looks like a secret-bearing key.

    Matches exact normalized names (e.g. ``api_key``, ``Authorization``) and
    also tokenizes on ``-``/``_`` so API-key-style headers such as
    ``X-API-Key`` are recognized via their ``key``/``api`` tokens.
    """
    norm = _norm_secret_name(name)
    if norm in _NORMALIZED_SECRET_HASH_KEYS:
        return True
    # Split on separators so X-API-Key -> {'x', 'api', 'key'} and check tokens.
    tokens = {t.lower() for t in _re.split(r"[-_]", str(name)) if t}
    if tokens & _NORMALIZED_SECRET_HASH_KEYS:
        return True
    return bool(tokens & _SENSITIVE_NAME_TOKENS)

# Matches ``<name>=<value>`` for a sensitive param inside a URL query string or a
# (JSON/repr) dict, e.g. ``api_key=...``, ``"api_key": "..."``, ``'key': '...'``.
# ``<sep>`` tolerates an optional closing quote after the name (JSON/repr style),
# the ``=``/``:`` delimiter, whitespace, and an optional opening quote on the value.
# ``<value>`` runs until the next delimiter (``&``, ``?``, whitespace, quote, comma,
# brace/paren) so neither real URLs nor dict reprs leak the secret.
_QS_SECRET_RE = _re.compile(
    r"(?i)(?P<name>\b(?:" + "|".join(SENSITIVE_PARAMS) + r")\b)"
    r"(?P<sep>['\"]?\s*[=:]\s*['\"]?)"
    r"(?P<val>[^&?\s'\"},)]+)"
)

# Matches an ``Authorization`` header value (``Authorization: <scheme> <creds>``
# or ``'Authorization': '<...>'``) in any wrapped string.
_AUTH_HEADER_RE = _re.compile(
    r"(?i)(?P<name>Authorization)(?P<sep>['\"]?\s*[=:]\s*['\"]?)(?P<val>[^'\"},)\r\n]+)"
)

# Matches quoted dict/JSON key/value pairs so secret-bearing header/param names
# such as ``X-Client-Secret`` are redacted even when absent from
# :data:`SENSITIVE_PARAMS`.
_DICT_KV_RE = _re.compile(
    r"(?P<q>['\"])"
    r"(?P<key>[^'\"\\]+)"
    r"(?P=q)\s*:\s*"
    r"(?P<vq>['\"])"
    r"(?P<val>[^'\"]*)"
    r"(?P=vq)"
)


def _redact_dict_kv_secrets(text: str) -> str:
    def _repl(match: _re.Match[str]) -> str:
        key = match.group("key")
        if not _is_secret_key_name(key):
            return match.group(0)
        q, vq = match.group("q"), match.group("vq")
        return f"{q}{key}{q}: {vq}{_REDACTED}{vq}"

    return _DICT_KV_RE.sub(_repl, text)


def _redact_url_query_secrets(url: str) -> str:
    """Redact secret-bearing query param values in a URL (issue #38 hyphenated names)."""
    from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.query:
        return url
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    if not any(_is_secret_key_name(k) for k, _ in pairs):
        return url
    redacted = [(k, _REDACTED if _is_secret_key_name(k) else v) for k, v in pairs]
    return urlunparse(parsed._replace(query=urlencode(redacted)))


_URL_IN_TEXT_RE = _re.compile(r"https?://[^\s'\"<>]+")


def _redact_urls_in_text(text: str) -> str:
    return _URL_IN_TEXT_RE.sub(lambda m: _redact_url_query_secrets(m.group(0)), text)


def redact_secrets(text):
    """Return ``text`` with any sensitive query-param value or ``Authorization``
    header value replaced by ``REDACTED``.

    Covers the leak paths flagged in review B4: a wrapped transport error whose
    message embeds the request URL (``httpx.raise_for_status`` includes the full
    URL, query string and all) or a ``repr`` of the params/headers dict. Applied
    before any secret can surface in a :class:`SourceUnavailable` message, a cache
    key, or a debug string.
    """
    if text is None:
        return text
    s = text if isinstance(text, str) else str(text)
    s = _AUTH_HEADER_RE.sub(lambda m: m.group("name") + m.group("sep") + _REDACTED, s)
    s = _QS_SECRET_RE.sub(lambda m: m.group("name") + m.group("sep") + _REDACTED, s)
    s = _redact_dict_kv_secrets(s)
    s = _redact_urls_in_text(s)
    return s

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


def _validate_positive_number(value, name: str) -> float:
    """Issue #37: reject bool/string/non-positive transport options up front."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    if not (value > 0 and _math.isfinite(value)):
        raise ValueError(f"{name} must be a positive finite number, got {value!r}")
    return float(value)


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
        self._timeout = _validate_positive_number(timeout, "timeout")

        # --- retry/backoff (opt-in) -------------------------------------- #
        # ``max_retries`` is the number of *extra* attempts after the first. ``0``
        # (default) reproduces the historical single-attempt behavior exactly, so no
        # existing test changes timing or call count.
        if not isinstance(max_retries, int) or isinstance(max_retries, bool):
            raise TypeError(f"max_retries must be an int, got {type(max_retries).__name__}")
        if max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {max_retries}")
        self._max_retries = max_retries
        self._backoff_base = _validate_positive_number(backoff_base, "backoff_base")
        self._backoff_max = _validate_positive_number(backoff_max, "backoff_max")
        if self._backoff_max < self._backoff_base:
            raise ValueError(
                f"backoff_max ({backoff_max!r}) must be >= backoff_base ({backoff_base!r})"
            )
        # Injectable so tests run instantly and deterministically.
        self._sleep = sleep or _time.sleep
        self._rand = rand or _random.random

        # --- response cache (opt-in, OFF by default) --------------------- #
        # ``cache_ttl=None`` (default) means no caching: behavior is unchanged. A
        # positive TTL enables an in-memory cache keyed by (url, params, json_body,
        # headers) so authenticated/entitlement-specific responses are isolated.
        if cache_ttl is not None:
            if not isinstance(cache_ttl, (int, float)) or isinstance(cache_ttl, bool):
                raise TypeError(f"cache_ttl must be a number or None, got {type(cache_ttl).__name__}")
            if cache_ttl <= 0:
                raise ValueError(f"cache_ttl must be positive, got {cache_ttl}")
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
    def _cache_key(url, params, json_body, headers):
        """Stable, hashable key for the response cache.

        ``params``/``json_body``/``headers`` are dict-like, so they are normalized to
        a sorted, JSON-serialized form to be hashable and order-independent. Sensitive
        values (api_key/key/token/access_token and Authorization) are redacted from
        the loggable key components (B4), but their *hashes* participate in the key
        so requests with different credentials remain isolated (issues #22, #31).
        """
        import hashlib
        from urllib.parse import parse_qsl, urlparse

        def _secret_hash(value):
            # Deterministic, one-way identity for a secret value. Never store the
            # plaintext secret; never embed it in a repr/log/error.
            return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]

        def _collect_secret_identities(obj, prefix=""):
            """Recursively collect hashes for every secret-bearing key value.

            Walks dicts and the items of list/tuple sequences so nested secrets
            (e.g. ``json_body={"auth": {"api_key": "A"}}``) still distinguish
            requests with different credentials (issue #22).
            """
            identity = {}
            if isinstance(obj, dict):
                for k, v in obj.items():
                    key_path = f"{prefix}.{k}" if prefix else k
                    if _is_secret_key_name(k):
                        identity[key_path] = _secret_hash(v)
                    identity.update(_collect_secret_identities(v, key_path))
            elif isinstance(obj, (list, tuple)):
                for i, item in enumerate(obj):
                    identity.update(
                        _collect_secret_identities(item, f"{prefix}[{i}]")
                    )
            return identity

        def _norm(obj, keep_secret_identity=False):
            if obj is None:
                return None
            try:
                serialized = _json.dumps(obj, sort_keys=True, default=str)
            except TypeError:
                serialized = repr(obj)
            if keep_secret_identity:
                # Build a parallel identity token for each secret value so two
                # requests with different credentials do not collide.
                identity = _collect_secret_identities(obj)
                # Redact first, then pair with identity hashes. This guarantees the
                # plaintext secret never appears in the returned key tuple.
                serialized = (redact_secrets(serialized), _json.dumps(identity, sort_keys=True))
                return serialized
            return redact_secrets(serialized)

        def _url_secret_identity(url):
            # Secret values embedded directly in the URL query string are redacted
            # in the display portion of the key; keep a deterministic hash of each
            # so two credentials do not share a cached response (issue #37/B1).
            parsed = urlparse(url)
            identity = {}
            for k, v in parse_qsl(parsed.query, keep_blank_values=True):
                if _is_secret_key_name(k):
                    identity[k] = _secret_hash(v)
            if not identity:
                return None
            return _json.dumps(identity, sort_keys=True)

        return (
            _redact_url_query_secrets(url),
            _url_secret_identity(url),
            _norm(params, keep_secret_identity=True),
            _norm(json_body, keep_secret_identity=True),
            _norm(headers, keep_secret_identity=True),
        )

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
        ``headers`` participates in the cache key so auth/entitlement-specific
        responses remain isolated.
        """
        # --- cache lookup ------------------------------------------------ #
        key = None
        if self._cache is not None:
            key = self._cache_key(url, params, json_body, headers)
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
                # B4: the raw transport exception (e.g. ``httpx.HTTPStatusError``)
                # keeps the full request URL — query string and ``api_key=...``
                # included — in its own ``str``. Capture a REDACTED message here, then
                # raise OUTSIDE this except suite (below). Raising outside means no
                # exception is being handled, so the ``SourceUnavailable`` carries the
                # secret in neither ``__cause__`` NOR ``__context__`` — ``from None``
                # alone only suppresses display, it does not clear ``__context__``.
                redacted_error = redact_secrets(
                    f"{self._source_name} transport error: {exc}"
                )
            # Reached only on the non-retry failure path; the except suite has exited,
            # so this SourceUnavailable has a clean __context__/__cause__.
            raise SourceUnavailable(redacted_error)

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
