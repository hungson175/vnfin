"""FRED (Federal Reserve Bank of St. Louis) macro source — STUB.

TODO(requires FRED_API_KEY env): the FRED JSON API
(``https://api.stlouisfed.org/fred/series/observations``) requires a free 32-char
API key. The key is NOT present in ``~/dev/.env`` yet, and the research note
(``docs/research/2026-06-18-macro-global-cross-country.md``) confirmed the
endpoint/param shape but could not pull a live row without it.

Boss wants FRED, so this thin stub is intentionally present and importable but
NOT implemented. It mirrors the ``WorldBankMacroSource`` constructor/shape so the
adapter can be fleshed out later without touching callers. Until then,
``get_series`` raises ``NotImplementedError`` (a programmer signal, deliberately
NOT a ``SourceError`` — there is nothing to fail over from yet).

Planned contract (from the research note, unverified live):
- Endpoint: ``/fred/series/observations?series_id={ID}&api_key={KEY}&file_type=json``
- Body: ``{"observations": [{"date": "YYYY-MM-DD", "value": "<str>"}, ...], "units", ...}``
  ('.' denotes a missing value). Frequencies daily/monthly/quarterly.
- Auth: REQUIRED free key (env ``FRED_API_KEY``). Attribution required.
"""
from __future__ import annotations

import os
from typing import Optional


class FREDMacroSource:
    """Placeholder FRED adapter. Not yet implemented (no API key available).

    The key is read from the ``api_key`` argument or the ``FRED_API_KEY`` env var.
    All data methods raise ``NotImplementedError`` until the key is provisioned
    and the adapter is completed.
    """

    NAME = "fred"
    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: Optional[str] = None, http_get=None, timeout: float = 25.0):
        self._api_key = api_key or os.environ.get("FRED_API_KEY")
        self._http_get = http_get
        self._timeout = timeout

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def has_key(self) -> bool:
        return bool(self._api_key)

    def get_series(self, series_id: str, start=None, end=None):
        """TODO(requires FRED_API_KEY): implement /fred/series/observations parsing."""
        raise NotImplementedError(
            "FREDMacroSource is a stub. TODO(requires FRED_API_KEY env): no FRED API "
            "key is available yet. Use WorldBankMacroSource for cross-country macro "
            "data in the meantime."
        )
