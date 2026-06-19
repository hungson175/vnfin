"""FRED (Federal Reserve Bank of St. Louis) macro source — optional BYOK.

Clean-room: the endpoint and response shape were taken only from FRED's own
official API docs (``api.stlouisfed.org/fred/series/observations``) and the
project's research note ``docs/research/2026-06-18-macro-no-key-byok.md``. No
third-party library was consulted.

**Bring-your-own-key (BYOK).** FRED's JSON API requires a free 32-char key. The
library NEVER bundles, ships, or commits a key — the *user* supplies their own via
the ``api_key`` argument or the ``FRED_API_KEY`` environment variable. When no key
is configured the source is cleanly skippable: ``has_key`` is ``False`` and any
data call raises :class:`~vnfin.exceptions.SourceUnavailable` (a catchable
``SourceError`` subclass) BEFORE any network call — so a failover chain skips it
silently and a missing key is never a hard crash and never leaks a raw exception.

**Official API only — never ``fredgraph.csv``.** FRED's Terms of Use prohibit
automated scraping outside the API (June-2024 anti-caching/anti-AI clauses), so we
only ever hit ``/fred/series/observations``.

Provider contract:
- Endpoint: ``/fred/series/observations?series_id={ID}&api_key={KEY}&file_type=json``
- Body: ``{"units": "...", "observations": [{"date": "YYYY-MM-DD",
  "value": "<str>"}, ...]}`` where the string ``"."`` denotes a missing value.

Failure mapping (failover-safe, reuses ``vnfin.exceptions``):
- no key configured                  -> ``SourceUnavailable`` (skippable)
- transport/network error            -> ``SourceUnavailable``
- non-JSON / missing observations key -> ``InvalidData``
- malformed scalar / bad date        -> ``InvalidData``
- empty / all-missing                 -> ``EmptyData``
"""
from __future__ import annotations

import math
import os
from datetime import date, datetime, timezone
from typing import Optional

from ..coerce import parse_provider_float
from ..exceptions import EmptyData, InvalidData, SourceUnavailable
from ..transport import DEFAULT_UA, HttpDataSource
from .models import IndicatorSeries


class FREDMacroSource(HttpDataSource):
    """Optional BYOK FRED adapter (official JSON API only).

    The key is read from the ``api_key`` argument or the ``FRED_API_KEY`` env var.
    With no key the source is skippable (``has_key`` False; data calls raise a
    catchable :class:`~vnfin.exceptions.SourceUnavailable`).
    """

    NAME = "fred"
    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: Optional[str] = None, http_get=None, timeout: float = 25.0):
        super().__init__(http_get=http_get, timeout=timeout)
        self._api_key = self._normalize_key(api_key) or self._normalize_key(
            os.environ.get("FRED_API_KEY")
        )

    @staticmethod
    def _normalize_key(raw) -> str | None:
        """Return a stripped non-empty string key, or None for missing/bad keys."""
        if not isinstance(raw, str):
            return None
        key = raw.strip()
        return key if key else None

    def _redact_key(self, text):
        """Remove the configured API key from provider-controlled text."""
        if self._api_key and isinstance(text, str):
            return text.replace(self._api_key, "***")
        return text

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def has_key(self) -> bool:
        return bool(self._api_key)

    def supports(self, indicator) -> bool:
        """Capability probe for failover chains (no network call).

        C4 contract: a missing ``FRED_API_KEY`` makes the source **not capable**
        (returns ``False``) so a failover chain skips it BEFORE any network call —
        it is never advertised-as-implemented-then-crashing. With a key, capability
        is left to the actual fetch (FRED series are not pre-enumerated here), so
        this returns ``True`` whenever a key is configured.
        """
        return self.has_key

    def get_series(self, series_id: str, start=None, end=None) -> IndicatorSeries:
        """Fetch one FRED series via the official observations endpoint.

        Raises a ``vnfin.exceptions.SourceError`` subclass on any failure
        (including a missing key), so it composes safely with failover.
        """
        if not self._api_key:
            # BYOK: cleanly skippable — catchable SourceError, no network call.
            raise SourceUnavailable(
                f"{self.NAME}: no FRED_API_KEY configured (bring-your-own-key); "
                "source skipped"
            )
        if not isinstance(series_id, str) or not series_id:
            raise InvalidData(f"{self.NAME}: series_id must be a non-empty string")
        sid = series_id.strip()
        if not sid:
            raise InvalidData(f"{self.NAME}: empty series_id")

        url = f"{self.BASE_URL}/series/observations"
        params = {"series_id": sid, "api_key": self._api_key, "file_type": "json"}
        if start is not None:
            params["observation_start"] = self._as_iso(start, "start")
        if end is not None:
            params["observation_end"] = self._as_iso(end, "end")

        data = self._request_json(url, params=params, headers=self._headers())

        # Issue #51: FRED application-level error envelopes (error_code/error_message)
        # must not be confused with no-data or parsed as successful observations.
        # The provider-controlled error message may echo the BYOK key, so redact it.
        if isinstance(data, dict) and ("error_code" in data or "error_message" in data):
            safe_message = self._redact_key(data.get("error_message"))
            raise InvalidData(
                f"{self.NAME}: provider error "
                f"code={data.get('error_code')!r} message={safe_message!r}"
            )

        units, points = self._build_points(data, sid)
        if not points:
            raise EmptyData(f"{self.NAME}: no observations for {sid}")

        return IndicatorSeries(
            country="",  # FRED series are not inherently country-keyed
            indicator_code=sid,
            indicator_name=sid,
            points=tuple(points),
            source=self.NAME,
            unit=units or "",
            # An arbitrary FRED series may be any unit (%, index, USD, persons,
            # ...); the money currency is unknown here, so do not stamp USD (B7).
            currency=None,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    # --- parsing helpers ------------------------------------------------- #

    def _build_points(self, data, sid):
        if not isinstance(data, dict) or "observations" not in data:
            raise InvalidData(f"{self.NAME}: missing 'observations' in response")
        observations = data.get("observations")
        if not isinstance(observations, list):
            raise InvalidData(f"{self.NAME}: 'observations' is not a list")
        units = data.get("units") if isinstance(data.get("units"), str) else ""

        points: list[tuple[date, float]] = []
        seen_dates: set[date] = set()
        for obs in observations:
            if not isinstance(obs, dict):
                raise InvalidData(f"{self.NAME}: observation is not an object")
            raw = obs.get("value")
            if raw is None or (isinstance(raw, str) and raw.strip() == "."):
                continue  # FRED uses "." for missing -> skip
            try:
                d = date.fromisoformat(str(obs.get("date")).strip())
                value = parse_provider_float(raw, label=f"observation for {sid}", source=self.NAME)
            except (TypeError, ValueError) as exc:
                raise InvalidData(f"{self.NAME}: malformed observation for {sid}") from exc
            if not math.isfinite(value):
                raise InvalidData(f"{self.NAME}: non-finite value for {sid}")
            if d in seen_dates:
                raise InvalidData(
                    f"{self.NAME}: duplicate observation date for {sid}: {d.isoformat()}"
                )
            seen_dates.add(d)
            points.append((d, value))
        points.sort(key=lambda p: p[0])
        return units, points

    @staticmethod
    def _as_iso(d, label: str) -> str:
        if isinstance(d, (date, datetime)):
            return d.strftime("%Y-%m-%d")
        if not isinstance(d, str):
            raise InvalidData(f"fred: {label} date must be a date/datetime or YYYY-MM-DD string")
        s = d.strip()
        try:
            parsed = datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError as exc:
            raise InvalidData(f"fred: malformed {label} date {d!r}") from exc
        return parsed.strftime("%Y-%m-%d")

    def _headers(self) -> dict:
        return {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
