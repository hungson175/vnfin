"""IMF DataMapper (WEO) macro source — no-key cross-country backup.

Clean-room: the endpoint and response shape were learned only from the IMF's own
DataMapper API (``www.imf.org/external/datamapper/api/v1``, verified live
2026-06-18) and the project's research note
``docs/research/2026-06-18-macro-no-key-byok.md``. No third-party library was
consulted.

Provider contract (verified):
- Endpoint: ``/api/v1/{INDICATOR}/{ISO3}`` (one indicator, one or more ISO3s).
- No auth. All-rights-reserved data; on-demand fetch only (no bundling).
- Success body:
  ``{"values": {"<INDICATOR>": {"<ISO3>": {"<year-str>": <float|null>, ...}}},
     "api": {"version": "1", "output-method": "json"}}``
  Years are annual (WEO), 1980.. incl. projections; values are floats.
- A requested country absent from ``values[indicator]`` means "no data".

Projections (B8): IMF WEO mixes historical actuals with multi-year forecasts and
the basic DataMapper response carries no per-point actual/forecast flag. We use a
deterministic, conservative rule — any year **>= the current calendar year** is a
projection — and stamp ``projection_from_year`` on the result so ``latest()``
returns the most recent actual and never a forecast. This rule is intentionally
cautious (it may mark a not-yet-published current year as a projection rather than
ever returning a forecast as an actual).

Indicator coverage (canonical -> WEO code), percent-unit only so the chain is
unit-homogeneous with World Bank for these indicators:
- GDP_GROWTH  -> NGDP_RPCH (real GDP growth, %)
- INFLATION   -> PCPIPCH   (CPI inflation, %)
- UNEMPLOYMENT-> LUR       (unemployment, %)
- GDP         -> NGDPD     (GDP, USD bn) — *USD bn*, NOT the canonical "current US$"
  level, so the failover unit guard will keep IMF GDP out of the WB-USD chain.

Failure mapping (failover-safe, reuses ``vnfin.exceptions``):
- transport/network error          -> ``SourceUnavailable``
- non-JSON / wrong shape            -> ``InvalidData``
- unsupported indicator for IMF     -> ``InvalidData``
- malformed scalar / NaN / bad year -> ``InvalidData``
- country absent / all-null         -> ``EmptyData``
"""
from __future__ import annotations

import math
from datetime import date, datetime, timezone

from ..exceptions import EmptyData, InvalidData
from ..transport import DEFAULT_UA, HttpDataSource
from .indicators import Frequency, MacroIndicator, normalize_indicator, validate_indicator_values
from .models import IndicatorSeries

# Canonical indicator -> (IMF WEO code, unit IMF emits).
_IMF_MAP: dict[MacroIndicator, tuple[str, str]] = {
    MacroIndicator.GDP_GROWTH: ("NGDP_RPCH", "%"),
    MacroIndicator.INFLATION: ("PCPIPCH", "%"),
    MacroIndicator.UNEMPLOYMENT: ("LUR", "%"),
    MacroIndicator.GDP: ("NGDPD", "USD bn"),  # distinct unit -> guard keeps it out of WB chain
}


class IMFDataMapperSource(HttpDataSource):
    """Adapter over the IMF DataMapper v1 API (no key)."""

    NAME = "imf_datamapper"
    BASE_URL = "https://www.imf.org/external/datamapper/api/v1"

    def __init__(self, http_get=None, timeout: float = 25.0):
        super().__init__(http_get=http_get, timeout=timeout)

    @property
    def name(self) -> str:
        return self.NAME

    @staticmethod
    def _validate_country_iso3(value) -> str:
        """Validate ``country_iso3`` before any string operation or network call."""
        name = IMFDataMapperSource.NAME
        if not isinstance(value, str):
            raise InvalidData(
                f"{name}: country must be a 3-letter ISO3 code, got {type(value).__name__}"
            )
        c = value.strip().upper()
        if not (len(c) == 3 and c.isalpha()):
            raise InvalidData(f"{name}: country must be a 3-letter ISO3 code, got {value!r}")
        return c

    @staticmethod
    def normalize_country(country_iso3: str) -> str:
        return country_iso3.strip().upper()

    def supports(self, indicator) -> bool:
        """True if this source maps the (canonical) indicator (no network call)."""
        try:
            return normalize_indicator(indicator) in _IMF_MAP
        except ValueError:
            return False

    def unit_for(self, indicator) -> str:
        """Unit IMF emits for ``indicator``. Raises ``InvalidData`` if unsupported."""
        ind = normalize_indicator(indicator)
        try:
            return _IMF_MAP[ind][1]
        except KeyError as exc:
            raise InvalidData(f"{self.NAME}: unsupported indicator {ind.value}") from exc

    def get_indicator(self, country_iso3: str, indicator) -> IndicatorSeries:
        """Fetch one IMF WEO indicator series for one country (annual)."""
        # Validate caller input before any network call or string operation.
        country = self._validate_country_iso3(country_iso3 or "")
        try:
            ind = normalize_indicator(indicator)
        except ValueError as exc:
            raise InvalidData(f"{self.NAME}: unsupported indicator {indicator!r}") from exc
        try:
            code, unit = _IMF_MAP[ind]
        except KeyError as exc:
            raise InvalidData(f"{self.NAME}: unsupported indicator {ind.value}") from exc

        url = f"{self.BASE_URL}/{code}/{country}"
        data = self._request_json(url, headers=self._headers())

        obs = self._extract_obs(data, code, country)
        points = self._build_points(obs, code)
        if not points:
            raise EmptyData(f"{self.NAME}: no observations for {country}/{code}")
        # Level indicators (GDP, CPI) must be strictly positive; percent/rate
        # indicators may be negative.
        validate_indicator_values(ind, points, self.NAME)

        # IMF WEO mixes actuals with forecasts. Conservatively mark the current
        # calendar year and beyond as projections so latest() never returns a
        # forecast as an actual (B8). Only flag if the series actually reaches it.
        proj_from = datetime.now(timezone.utc).year
        max_year = max(d.year for (d, _v) in points)
        projection_from_year = proj_from if max_year >= proj_from else None

        warnings = ()
        if projection_from_year is not None:
            warnings = (
                f"imf_weo: years >= {projection_from_year} are WEO projections "
                "(forecasts), excluded from latest()",
            )

        return IndicatorSeries(
            country=country,
            indicator_code=code,
            indicator_name=f"{ind.value} ({code})",
            points=tuple(points),
            source=self.NAME,
            unit=unit,
            # Currency is meaningful only for the money-denominated GDP level
            # (USD bn); percent indicators carry no currency (B7).
            currency="USD" if ind == MacroIndicator.GDP else None,
            frequency=Frequency.ANNUAL,
            projection_from_year=projection_from_year,
            warnings=warnings,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    # --- parsing helpers ------------------------------------------------- #

    def _extract_obs(self, data, code, country) -> dict:
        if not isinstance(data, dict) or "values" not in data:
            raise InvalidData(f"{self.NAME}: missing 'values' in response")
        values = data.get("values")
        if not isinstance(values, dict):
            raise InvalidData(f"{self.NAME}: 'values' is not an object")
        per_country = values.get(code)
        if per_country is None:
            # indicator key absent -> no data for this indicator
            raise EmptyData(f"{self.NAME}: no series for indicator {code}")
        if not isinstance(per_country, dict):
            raise InvalidData(f"{self.NAME}: indicator block is not an object")
        obs = per_country.get(country)
        if obs is None:
            raise EmptyData(f"{self.NAME}: country {country} absent for {code}")
        if not isinstance(obs, dict):
            raise InvalidData(f"{self.NAME}: country block is not an object")
        return obs

    def _build_points(self, obs, code):
        points: list[tuple[date, float]] = []
        for year_str, raw in obs.items():
            if raw is None:
                continue  # missing year -> skip
            try:
                year = int(str(year_str).strip())
                value = float(raw)
            except (TypeError, ValueError) as exc:
                raise InvalidData(f"{self.NAME}: malformed observation for {code}") from exc
            if not math.isfinite(value):
                raise InvalidData(f"{self.NAME}: non-finite value for {code} at {year}")
            try:
                d = date(year, 1, 1)
            except ValueError as exc:
                # Issue #61: out-of-range years must raise InvalidData, not leak
                # raw ValueError from the date constructor.
                raise InvalidData(f"{self.NAME}: invalid year {year} for {code}") from exc
            points.append((d, value))
        points.sort(key=lambda p: p[0])
        return points

    def _headers(self) -> dict:
        return {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
