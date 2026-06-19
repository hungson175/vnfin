"""DBnomics (IMF / IFS) macro source — no-key broad backup.

Clean-room: the endpoint and response shape were learned only from DBnomics' own
public API (``api.db.nomics.world/v22``, verified live 2026-06-18) and the
project's research note ``docs/research/2026-06-18-macro-no-key-byok.md``. No
third-party library was consulted.

Provider contract (verified):
- Endpoint: ``/v22/series/IMF/IFS/{series}?observations=1`` (one IFS series).
  The IFS series id is ``{FREQ}.{CC}.{IFS_CODE}`` where ``FREQ`` is ``A``/``M``,
  ``CC`` is the IMF 2-letter country code, ``IFS_CODE`` is the IFS concept.
- No auth. ODbL + upstream (IMF) terms; on-demand fetch, no bundling.
- Success body:
  ``{"series": {"docs": [{"period_start_day": [<ISO date>...],
                           "period": [<label>...], "value": [<float|null|"NA">...],
                           "series_code", "dataset_code", ...}]}}``
  ``period_start_day`` / ``value`` are PARALLEL arrays (zip in order). Missing
  observations are ``null`` or the string ``"NA"``.

Indicator coverage (canonical -> IFS series template, unit DBnomics emits):
- GDP -> ``A.{CC}.NGDP_XDC``  (GDP, *national currency* — NOT canonical USD level)
- CPI -> ``M.{CC}.PCPI_IX``   (CPI index level)

Both DBnomics units differ from the WB-USD GDP level / WB percent indicators, so
the per-indicator unit guard keeps them in their own homogeneous chains.

Failure mapping (failover-safe, reuses ``vnfin.exceptions``):
- transport/network error            -> ``SourceUnavailable``
- non-JSON / wrong shape / mismatched -> ``InvalidData``
- unsupported indicator / unknown ISO3-> ``InvalidData``
- malformed scalar / bad period       -> ``InvalidData``
- period date contradicts frequency   -> ``InvalidData``
- no docs / all-null                  -> ``EmptyData``
"""
from __future__ import annotations

import math
from datetime import date, datetime, timezone

from ..coerce import parse_provider_float
from ..exceptions import EmptyData, InvalidData
from ..transport import DEFAULT_UA, HttpDataSource
from .indicators import Frequency, MacroIndicator, normalize_indicator, validate_indicator_values
from .models import IndicatorSeries

# Canonical indicator -> (IFS frequency code, IFS concept code, unit DBnomics
# emits, result frequency). GDP NGDP_XDC is annual national currency (the actual
# currency varies by country, so the result carries no fixed currency); CPI
# PCPI_IX is a monthly index level (no currency).
_DBN_MAP: dict[MacroIndicator, tuple[str, str, str, Frequency]] = {
    MacroIndicator.GDP: ("A", "NGDP_XDC", "national currency", Frequency.ANNUAL),
    MacroIndicator.CPI: ("M", "PCPI_IX", "index", Frequency.MONTHLY),
}

# Minimal ISO3 -> IMF/IFS 2-letter country code map for the documented coverage
# (US, China, Japan, Germany, Vietnam) plus an obviously-fake ``ZZZ`` used by the
# synthetic tests. Unknown ISO3 -> InvalidData (clean, catchable).
_ISO3_TO_IFS_CC: dict[str, str] = {
    "USA": "US",
    "CHN": "CN",
    "JPN": "JP",
    "DEU": "DE",
    "VNM": "VN",
    "ZZZ": "ZZ",  # synthetic test sentinel
}


class DBnomicsSource(HttpDataSource):
    """Adapter over the DBnomics v22 series API (IMF / IFS dataset, no key)."""

    NAME = "dbnomics"
    BASE_URL = "https://api.db.nomics.world/v22/series/IMF/IFS"

    def __init__(self, http_get=None, timeout: float = 25.0):
        super().__init__(http_get=http_get, timeout=timeout)

    @property
    def name(self) -> str:
        return self.NAME

    @staticmethod
    def normalize_country(country_iso3: str) -> str:
        return country_iso3.strip().upper()

    def supports(self, indicator) -> bool:
        try:
            return normalize_indicator(indicator) in _DBN_MAP
        except ValueError:
            return False

    def unit_for(self, indicator) -> str:
        ind = normalize_indicator(indicator)
        try:
            return _DBN_MAP[ind][2]
        except KeyError as exc:
            raise InvalidData(f"{self.NAME}: unsupported indicator {ind.value}") from exc

    def frequency_for(self, indicator) -> Frequency:
        """Result frequency DBnomics emits for ``indicator``."""
        ind = normalize_indicator(indicator)
        try:
            return _DBN_MAP[ind][3]
        except KeyError as exc:
            raise InvalidData(f"{self.NAME}: unsupported indicator {ind.value}") from exc

    def get_indicator(self, country_iso3: str, indicator) -> IndicatorSeries:
        """Fetch one IMF/IFS series for one country via DBnomics."""
        ind = normalize_indicator(indicator)
        country = self.normalize_country(country_iso3 or "")
        if not country:
            raise InvalidData(f"{self.NAME}: empty country code")
        try:
            freq, concept, unit, result_freq = _DBN_MAP[ind]
        except KeyError as exc:
            raise InvalidData(f"{self.NAME}: unsupported indicator {ind.value}") from exc
        cc = _ISO3_TO_IFS_CC.get(country)
        if cc is None:
            raise InvalidData(f"{self.NAME}: no IFS country code for ISO3 {country}")

        series_id = f"{freq}.{cc}.{concept}"
        url = f"{self.BASE_URL}/{series_id}"
        data = self._request_json(url, params={"observations": 1}, headers=self._headers())

        doc = self._extract_doc(data)
        points = self._build_points(doc, series_id, result_freq)
        if not points:
            raise EmptyData(f"{self.NAME}: no observations for {series_id}")
        # Level indicators (GDP, CPI) must be strictly positive; percent/rate
        # indicators may be negative.
        validate_indicator_values(ind, points, self.NAME)

        return IndicatorSeries(
            country=country,
            indicator_code=series_id,
            indicator_name=f"{ind.value} ({concept})",
            points=tuple(points),
            source=self.NAME,
            unit=unit,
            # GDP is in *national* currency (varies by country) and CPI is an
            # index — neither is a fixed USD figure, so carry no currency (B7).
            currency=None,
            frequency=result_freq,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    # --- parsing helpers ------------------------------------------------- #

    def _extract_doc(self, data):
        if not isinstance(data, dict) or "series" not in data:
            raise InvalidData(f"{self.NAME}: missing 'series' in response")
        series = data.get("series")
        if not isinstance(series, dict):
            raise InvalidData(f"{self.NAME}: 'series' is not an object")
        docs = series.get("docs")
        if docs is None or not isinstance(docs, list):
            raise InvalidData(f"{self.NAME}: missing 'docs' list")
        if not docs:
            raise EmptyData(f"{self.NAME}: empty docs")
        doc = docs[0]
        if not isinstance(doc, dict):
            raise InvalidData(f"{self.NAME}: doc is not an object")
        return doc

    def _build_points(self, doc, series_id, result_freq: Frequency):
        # Issue #21: the returned doc must be the requested series. The series_code must be a
        # non-blank string equal to the requested series_id; a present-but-malformed, blank, or
        # null series_code must not be stamped with the requested indicator identity.
        got_code = doc.get("series_code")
        if not isinstance(got_code, str) or not got_code.strip():
            raise InvalidData(f"{self.NAME}: malformed series_code {got_code!r}")
        if got_code != series_id:
            raise InvalidData(
                f"{self.NAME}: returned series_code {got_code!r} != requested {series_id!r}"
            )
        periods = doc.get("period_start_day")
        values = doc.get("value")
        if not isinstance(periods, list) or not isinstance(values, list):
            raise InvalidData(f"{self.NAME}: parallel period/value arrays missing")
        if len(periods) != len(values):
            raise InvalidData(
                f"{self.NAME}: period/value length mismatch "
                f"({len(periods)} vs {len(values)})"
            )

        points: list[tuple[date, float]] = []
        for period, raw in zip(periods, values):
            if raw is None or (isinstance(raw, str) and raw.strip().upper() in ("NA", "")):
                continue  # missing observation -> skip
            try:
                d = self._parse_period_day(period)
                self._validate_period_boundary(d, result_freq)
                value = parse_provider_float(raw, label=f"observation at {period}", source=self.NAME)
            except (TypeError, ValueError) as exc:
                raise InvalidData(
                    f"{self.NAME}: malformed observation for {series_id}: {exc}"
                ) from exc
            if not math.isfinite(value):
                raise InvalidData(f"{self.NAME}: non-finite value for {series_id} at {period}")
            points.append((d, value))
        points.sort(key=lambda p: p[0])
        return points

    @staticmethod
    def _validate_period_boundary(d: date, freq: Frequency) -> None:
        """Ensure ``period_start_day`` matches the declared observation frequency."""
        if freq == Frequency.ANNUAL and (d.month != 1 or d.day != 1):
            raise ValueError(f"annual period must be Jan 1, got {d.isoformat()}")
        if freq == Frequency.MONTHLY and d.day != 1:
            raise ValueError(f"monthly period must be month-start, got {d.isoformat()}")

    @staticmethod
    def _parse_period_day(period) -> date:
        """Parse an ISO ``YYYY-MM-DD`` period-start day into a ``date``.

        Raises ``ValueError`` (caught upstream -> ``InvalidData``) on anything
        that is not a strict ISO calendar date.
        """
        s = str(period).strip()
        # ``date.fromisoformat`` is strict and rejects garbage; exactly what we want.
        return date.fromisoformat(s)

    def _headers(self) -> dict:
        return {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
