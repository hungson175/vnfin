"""World Bank Indicators API (v2) macro source — the primary no-key cross-country backbone.

Clean-room: endpoints and response shapes were learned only from the World Bank's
own server (api.worldbank.org/v2, verified live 2026-06-18) and the project's
research note ``docs/research/2026-06-18-macro-global-cross-country.md``. No
third-party library behaviour was consulted.

Provider contract (verified):
- Endpoint: ``/v2/country/{ISO3}/indicator/{CODE}?format=json&per_page=...&date=Y1:Y2``
- No auth (no key, no token). Public open data, CC-BY 4.0 (attribution required).
- Success body is a 2-element JSON array: ``[meta, [obs, ...]]``. Each obs has
  ``indicator{id,value}``, ``country{id,value}``, ``countryiso3code``,
  ``date`` (year string), ``value`` (float | null), ``unit``.
- Invalid country/indicator -> ``[{"message": [{"id","key","value"}]}]``.
- Valid but no rows -> ``[{...,"total":0}, null]`` (second element null) or ``[meta, []]``.
- A single missing year inside a valid series has ``value: null`` -> skipped.
- The response may carry a UTF-8 BOM (decode tolerantly).

Failure mapping (failover-safe, reuses ``vnfin.exceptions``):
- transport/network error            -> ``SourceUnavailable``
- non-JSON / wrong top-level shape    -> ``InvalidData``
- provider ``message`` error envelope -> ``InvalidData``
- malformed/garbage scalar / NaN date -> ``InvalidData``
- no usable points                    -> ``EmptyData``
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone

from ..exceptions import EmptyData, InvalidData, SourceUnavailable

from .models import IndicatorSeries

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class WorldBankMacroSource:
    """Adapter over the World Bank Indicators API v2.

    ``http_get(url, params, headers) -> response text`` is injectable so unit
    tests never touch the network; the default forces IPv4, a browser UA, and a
    25s timeout to mirror the broker price sources.
    """

    NAME = "worldbank"
    BASE_URL = "https://api.worldbank.org/v2"
    DEFAULT_PER_PAGE = 20000  # one page is enough for any single-country annual series

    def __init__(self, http_get=None, timeout: float = 25.0, per_page: int = DEFAULT_PER_PAGE):
        self._http_get = http_get or self._default_http_get
        self._timeout = timeout
        self._per_page = per_page

    @property
    def name(self) -> str:
        return self.NAME

    @staticmethod
    def normalize_country(country_iso3: str) -> str:
        return country_iso3.strip().upper()

    def get_indicator(
        self,
        country_iso3: str,
        indicator_code: str,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> IndicatorSeries:
        """Fetch one indicator series for one country.

        Raises a ``vnfin.exceptions.SourceError`` subclass on any failure so it
        composes safely with failover/orchestration like the price sources.
        """
        country = self.normalize_country(country_iso3)
        code = indicator_code.strip()
        url = f"{self.BASE_URL}/country/{country}/indicator/{code}"
        params = {"format": "json", "per_page": self._per_page}
        if start_year is not None or end_year is not None:
            lo = start_year if start_year is not None else end_year
            hi = end_year if end_year is not None else start_year
            params["date"] = f"{int(lo)}:{int(hi)}"

        try:
            text = self._http_get(url, params, self._headers())
        except Exception as exc:  # transport-level
            raise SourceUnavailable(f"{self.NAME} transport error: {exc}") from exc

        parsed = self._parse_envelope(text)
        meta, observations = parsed

        country_name, indicator_name, unit, points = self._build_points(observations, code)
        if not points:
            raise EmptyData(
                f"{self.NAME}: no observations for {country}/{code}"
                + (f" {params['date']}" if "date" in params else "")
            )

        return IndicatorSeries(
            country=country,
            indicator_code=code,
            indicator_name=indicator_name or code,
            points=tuple(points),
            source=self.NAME,
            unit=unit,
            currency="USD",
            country_name=country_name,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    # --- parsing helpers -------------------------------------------------

    def _parse_envelope(self, text):
        """Decode the JSON, tolerate a BOM, and validate the top-level shape.

        Returns ``(meta, observations)`` where ``observations`` may be ``None``
        or an empty list (both meaning 'no data'). Raises ``InvalidData`` on a
        non-JSON body, an unexpected top-level type, or a provider error envelope.
        """
        if isinstance(text, (bytes, bytearray)):
            text = text.decode("utf-8-sig")
        elif isinstance(text, str):
            text = text.lstrip("﻿")

        try:
            parsed = json.loads(text)
        except (ValueError, TypeError) as exc:
            raise InvalidData(f"{self.NAME}: non-JSON response") from exc

        if not isinstance(parsed, list) or not parsed:
            raise InvalidData(f"{self.NAME}: unexpected top-level shape")

        first = parsed[0]
        # Provider error envelope: [{"message": [...]}]
        if isinstance(first, dict) and "message" in first:
            msgs = first.get("message") or []
            detail = "; ".join(
                str(m.get("value") or m.get("key")) for m in msgs if isinstance(m, dict)
            )
            raise InvalidData(f"{self.NAME}: provider error: {detail or 'invalid parameter'}")

        if len(parsed) < 2:
            # A lone metadata object with no observation slot is not a shape we expect.
            raise InvalidData(f"{self.NAME}: missing observations element")

        observations = parsed[1]
        if observations is not None and not isinstance(observations, list):
            raise InvalidData(f"{self.NAME}: observations element is not a list")
        return first, observations

    def _build_points(self, observations, code):
        """Turn the raw observation list into sorted (date, value) points.

        Null-valued observations (missing years) are skipped. A malformed scalar
        (non-numeric value, NaN/inf, or non-year date) raises ``InvalidData`` so
        the failure is recoverable rather than a hard crash.
        """
        country_name = None
        indicator_name = None
        unit = ""
        points: list[tuple[date, float]] = []

        for obs in observations or []:
            if not isinstance(obs, dict):
                raise InvalidData(f"{self.NAME}: observation is not an object")

            ind = obs.get("indicator") or {}
            if indicator_name is None and isinstance(ind, dict):
                indicator_name = ind.get("value")
            ctry = obs.get("country") or {}
            if country_name is None and isinstance(ctry, dict):
                country_name = ctry.get("value")
            if not unit and obs.get("unit"):
                unit = obs.get("unit")

            raw_value = obs.get("value")
            if raw_value is None:
                continue  # missing observation for this year — skip, not an error

            try:
                year = int(str(obs.get("date")).strip())
                value = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise InvalidData(f"{self.NAME}: malformed observation for {code}") from exc
            if not math.isfinite(value):
                raise InvalidData(f"{self.NAME}: non-finite value for {code} at {year}")

            points.append((date(year, 1, 1), value))

        points.sort(key=lambda p: p[0])
        return country_name, indicator_name, unit, points

    def _headers(self) -> dict:
        return {"User-Agent": _UA, "Accept": "application/json"}

    def _default_http_get(self, url, params, headers):  # pragma: no cover - network
        import httpx

        transport = httpx.HTTPTransport(local_address="0.0.0.0")  # force IPv4
        with httpx.Client(transport=transport, timeout=self._timeout, headers=headers) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.text
