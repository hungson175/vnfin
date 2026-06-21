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
- present malformed descriptive metadata -> ``InvalidData``
- observation outside request window -> skipped; none left -> ``EmptyData``
- no usable points                    -> ``EmptyData``
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone

from ..coerce import parse_provider_float
from ..exceptions import EmptyData, InvalidData
from ..transport import DEFAULT_UA, HttpDataSource
from ..validation import parse_canonical_int

from .._contracts import canonical_country_iso3
from .indicators import (
    Frequency,
    MacroIndicator,
    canonical_currency,
    canonical_macro_indicator,
    normalize_indicator,
    validate_indicator_values,
)
from .models import IndicatorSeries

# Canonical indicator -> (WDI code, unit World Bank emits). World Bank is the
# primary, so its units define the canonical unit for the percent indicators and
# the USD GDP level used by the failover chain. All WB macro series here are
# ANNUAL. Currency is indicator-specific (only GDP is money-denominated) and comes
# from ``canonical_currency`` — never hardcoded USD for percent series (B7).
_WB_MAP: dict[MacroIndicator, tuple[str, str]] = {
    MacroIndicator.GDP: ("NY.GDP.MKTP.CD", "current US$"),
    MacroIndicator.GDP_GROWTH: ("NY.GDP.MKTP.KD.ZG", "%"),
    MacroIndicator.INFLATION: ("FP.CPI.TOTL.ZG", "%"),
    MacroIndicator.UNEMPLOYMENT: ("SL.UEM.TOTL.ZS", "%"),
    # Issue #20: World Bank serves the broad cross-country CPI index level
    # (2010=100) through FP.CPI.TOTL, so include it as a canonical CPI source.
    MacroIndicator.CPI: ("FP.CPI.TOTL", "index"),
    # Issue #152: World Bank WDI annual fixed-income rates (% p.a.). World Bank is
    # the only no-key source mapping these — IMF DataMapper / DBnomics do not, so
    # each reduces to a single-source WB chain (like GDP/CPI). DEPOSIT_RATE is an
    # annual AGGREGATE (no clean per-tenor retail source); REAL_INTEREST may be
    # negative (GDP-deflator-adjusted). Caveats are documented in
    # ``vnfin.diagnostics.explain_fixed_income_coverage``.
    MacroIndicator.LENDING_RATE: ("FR.INR.LEND", "%"),
    MacroIndicator.DEPOSIT_RATE: ("FR.INR.DPST", "%"),
    MacroIndicator.REAL_INTEREST_RATE: ("FR.INR.RINR", "%"),
}


class WorldBankMacroSource(HttpDataSource):
    """Adapter over the World Bank Indicators API v2.

    ``http_get(url, params, headers) -> response text`` is injectable so unit
    tests never touch the network; the default forces IPv4, a browser UA, and a
    25s timeout to mirror the broker price sources.
    """

    NAME = "worldbank"
    BASE_URL = "https://api.worldbank.org/v2"
    DEFAULT_PER_PAGE = 20000  # one page is enough for any single-country annual series

    def __init__(self, http_get=None, timeout: float = 25.0, per_page: int = DEFAULT_PER_PAGE):
        super().__init__(http_get=http_get, timeout=timeout)
        self._per_page = per_page

    @property
    def name(self) -> str:
        return self.NAME

    @staticmethod
    def normalize_country(country_iso3: str) -> str:
        return country_iso3.strip().upper()

    @staticmethod
    def _validate_country_iso3(value) -> str:
        # Issue #32: shared canonical ISO3 contract — validates before any string
        # operation (non-string/blank/wrong-length -> InvalidData, not a raw error).
        return canonical_country_iso3(value, WorldBankMacroSource.NAME)

    # --- canonical-indicator interface (used by the macro failover chain) -- #
    def supports(self, indicator) -> bool:
        """True if World Bank maps the canonical ``indicator`` (no network call)."""
        try:
            return normalize_indicator(indicator) in _WB_MAP
        except ValueError:
            return False

    def unit_for(self, indicator) -> str:
        """Canonical unit World Bank emits for ``indicator``."""
        ind = canonical_macro_indicator(indicator)  # #48: InvalidData, not ValueError
        try:
            return _WB_MAP[ind][1]
        except KeyError as exc:
            raise InvalidData(f"{self.NAME}: unsupported indicator {ind.value}") from exc

    def indicator_identity(self, country_iso3, indicator):
        """Issue #78: expected returned identity (code, name) for ``indicator``.

        The stamped ``indicator_code`` is the WDI code (upper-cased, mirroring
        :meth:`get_indicator`). ``indicator_name`` comes from the provider payload
        (free-form), so the name is ``None`` (code-only validation).
        """
        ind = canonical_macro_indicator(indicator)  # #48: InvalidData, not ValueError
        try:
            code, _unit = _WB_MAP[ind]
        except KeyError as exc:
            raise InvalidData(f"{self.NAME}: unsupported indicator {ind.value}") from exc
        return (code.strip().upper(), None)

    def get_canonical_indicator(self, country_iso3: str, indicator) -> IndicatorSeries:
        """Fetch a canonical :class:`MacroIndicator` (maps it to a WDI code).

        Unlike :meth:`get_indicator` (which takes a raw WDI code), this takes a
        logical :class:`MacroIndicator` so it composes with the failover chain.
        The result's ``unit`` is stamped to the canonical unit (WB percent series
        often omit ``unit`` in the payload).
        """
        ind = canonical_macro_indicator(indicator)  # #48: InvalidData, not ValueError
        try:
            code, unit = _WB_MAP[ind]
        except KeyError as exc:
            raise InvalidData(f"{self.NAME}: unsupported indicator {ind.value}") from exc
        series = self.get_indicator(country_iso3, code)
        # Level indicators (GDP, CPI) must be strictly positive; percent/rate
        # indicators may be negative.
        validate_indicator_values(ind, series.points, self.NAME)
        # Pin the per-indicator unit (WB ZG/ZS series frequently report an empty
        # unit) and the indicator-specific currency (None for percent series).
        from dataclasses import replace

        return replace(
            series,
            unit=unit,
            value_unit=unit,
            currency=canonical_currency(ind),
            frequency=Frequency.ANNUAL,
        )

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
        country = self._validate_country_iso3(country_iso3)
        # Issue #57: indicator_code must be a non-empty string. Reject bytes and
        # other non-string types before any string operation to avoid leaking raw
        # AttributeError/TypeError. Normalize to uppercase WDI convention.
        if not isinstance(indicator_code, str):
            raise InvalidData(f"{self.NAME}: indicator_code must be a non-empty string")
        code = indicator_code.strip().upper()
        if not code:
            raise InvalidData(f"{self.NAME}: empty indicator code")
        url = f"{self.BASE_URL}/country/{country}/indicator/{code}"
        params = {"format": "json", "per_page": self._per_page}
        window_lo: int | None = None
        window_hi: int | None = None
        if start_year is not None or end_year is not None:
            window_lo = self._coerce_year(start_year, "start_year") if start_year is not None else self._coerce_year(end_year, "end_year")
            window_hi = self._coerce_year(end_year, "end_year") if end_year is not None else self._coerce_year(start_year, "start_year")
            if window_lo > window_hi:
                raise InvalidData(
                    f"{self.NAME}: start_year {window_lo} is after end_year {window_hi}"
                )
            params["date"] = f"{window_lo}:{window_hi}"

        text = self._request_text(url, params=params, headers=self._headers())

        parsed = self._parse_envelope(text)
        meta, observations = parsed

        country_name, indicator_name, unit, points = self._build_points(observations, code, country)
        points = self._contained_points(points, window_lo, window_hi)
        if not points:
            raise EmptyData(
                f"{self.NAME}: no observations in requested window for {country}/{code}"
                + (f" {params['date']}" if "date" in params else "")
            )

        return IndicatorSeries(
            country=country,
            indicator_code=code,
            indicator_name=indicator_name or code,
            points=tuple(points),
            source=self.NAME,
            unit=unit,
            # Raw WDI fetch: the canonical indicator is unknown here, so the
            # money currency is unknown -> leave it None rather than guess USD.
            # The canonical entry point (get_canonical_indicator) sets it.
            currency=None,
            frequency=Frequency.ANNUAL,
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

    def _build_points(self, observations, code, country):
        """Turn the raw observation list into sorted (date, value) points.

        Null-valued observations (missing years) are skipped. A malformed scalar
        (non-numeric value, NaN/inf, or non-year date) raises ``InvalidData`` so
        the failure is recoverable rather than a hard crash.
        """
        country_name = None
        indicator_name = None
        unit = ""
        points: list[tuple[date, float]] = []
        seen_dates: set[date] = set()  # Issue #66: reject duplicate observation dates

        for obs in observations or []:
            if not isinstance(obs, dict):
                raise InvalidData(f"{self.NAME}: observation is not an object")

            # Issue #21: the observation must belong to the requested country. The identity
            # field must be a non-blank string equal to the request; a present-but-malformed,
            # blank, or null countryiso3code must not be stamped as the requested identity.
            iso3 = obs.get("countryiso3code")
            if not isinstance(iso3, str) or not iso3.strip():
                raise InvalidData(
                    f"{self.NAME}: malformed observation countryiso3code {iso3!r} for {code}"
                )
            if iso3.strip().upper() != country:
                raise InvalidData(
                    f"{self.NAME}: observation country {iso3!r} != requested {country!r}"
                )

            ind = self._metadata_container(obs, "indicator", code)
            if ind is not None:
                # Issue #21 (reopen): the observation must identify the requested
                # WDI indicator. A present indicator.id must be a non-blank string
                # equal (canonical-normalized) to the requested code; a mismatched
                # or malformed id is a provider/cache/routing error, not data to
                # stamp as the requested indicator.
                ind_id = ind.get("id")
                if not isinstance(ind_id, str) or not ind_id.strip():
                    raise InvalidData(
                        f"{self.NAME}: malformed observation indicator.id {ind_id!r} for {code}"
                    )
                if ind_id.strip().upper() != code:
                    raise InvalidData(
                        f"{self.NAME}: observation indicator.id {ind_id!r} != requested {code!r}"
                    )
            if indicator_name is None and ind is not None:
                indicator_name = self._metadata_str(
                    ind.get("value"), "indicator.value", code
                )
            ctry = self._metadata_container(obs, "country", code)
            if country_name is None and ctry is not None:
                country_name = self._metadata_str(
                    ctry.get("value"), "country.value", code
                )
            if not unit:
                raw_unit = obs.get("unit")
                if raw_unit is not None and raw_unit != "":
                    if not isinstance(raw_unit, str):
                        raise InvalidData(
                            f"{self.NAME}: malformed unit metadata for {code}"
                        )
                    unit = raw_unit

            raw_value = obs.get("value")
            if raw_value is None:
                continue  # missing observation for this year — skip, not an error

            # Issue #108: the observation year must be a canonical integer key; "+2024"
            # and "02024" are malformed provider keys, not year 2024.
            year = parse_canonical_int(obs.get("date"), label=f"observation year for {code}")
            try:
                value = parse_provider_float(
                    raw_value, label=f"observation for {code}", source=self.NAME
                )
            except (TypeError, ValueError) as exc:
                raise InvalidData(f"{self.NAME}: malformed observation for {code}") from exc
            if not math.isfinite(value):
                raise InvalidData(f"{self.NAME}: non-finite value for {code} at {year}")
            try:
                d = date(year, 1, 1)
            except ValueError as exc:
                # Issue #63: out-of-range years must raise InvalidData, not leak
                # raw ValueError from the date constructor.
                raise InvalidData(f"{self.NAME}: invalid year {year} for {code}") from exc

            # Issue #66 (reopen): a duplicate observation date in one response is an
            # ambiguous observation key, not data to silently keep both of.
            if d in seen_dates:
                raise InvalidData(
                    f"{self.NAME}: duplicate observation date {d.isoformat()} for {code}"
                )
            seen_dates.add(d)
            points.append((d, value))

        points.sort(key=lambda p: p[0])
        return country_name, indicator_name, unit, points

    @staticmethod
    def _metadata_container(obs: dict, key: str, code: str) -> dict | None:
        if key not in obs:
            return None
        raw = obs.get(key)
        if raw is None:
            return None
        if not isinstance(raw, dict):
            raise InvalidData(
                f"{WorldBankMacroSource.NAME}: malformed {key} metadata for {code}"
            )
        return raw

    @staticmethod
    def _metadata_str(raw, field: str, code: str) -> str | None:
        """Accept absent/blank metadata or a string; reject other present types."""
        if raw is None or raw == "":
            return None
        if isinstance(raw, str):
            stripped = raw.strip()
            return stripped or None
        raise InvalidData(f"{WorldBankMacroSource.NAME}: malformed {field} for {code}")

    @staticmethod
    def _contained_points(
        points: list[tuple[date, float]],
        window_lo: int | None,
        window_hi: int | None,
    ) -> list[tuple[date, float]]:
        """Keep only observations inside the caller's optional year window."""
        if window_lo is None and window_hi is None:
            return points
        kept: list[tuple[date, float]] = []
        for d, value in points:
            year = d.year
            if window_lo is not None and year < window_lo:
                continue
            if window_hi is not None and year > window_hi:
                continue
            kept.append((d, value))
        return kept

    @staticmethod
    def _coerce_year(value, label: str) -> int:
        """Validate a year bound: int or numeric string only; no bool/float truncation.

        Rejects years that cannot be represented as ``datetime.date`` (i.e. outside
        ``1..9999``) so impossible bounds never reach the provider.
        """
        name = WorldBankMacroSource.NAME
        if isinstance(value, bool):
            raise InvalidData(f"{name}: {label} must be an integer year, got bool")
        if isinstance(value, int):
            year = value
        elif isinstance(value, str):
            s = value.strip()
            if not s.isdigit():
                raise InvalidData(f"{name}: {label} must be an integer year, got {value!r}")
            year = int(s)
        else:
            raise InvalidData(f"{name}: {label} must be an integer year, got {type(value).__name__}")
        if not 1 <= year <= 9999:
            raise InvalidData(f"{name}: {label} {year} is out of supported range 1..9999")
        return year

    def _headers(self) -> dict:
        return {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
