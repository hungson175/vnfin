"""Annual precious-metals (silver + platinum) history source (#196).

``WorldBankCmoMetalSource`` fetches the SAME World Bank Commodity Markets annual ``.xlsx``
(Pink Sheet) the internal gold source already parses, via the SHARED
:func:`~vnfin._contracts.worldbank_cmo.parse_cmo_annual`, and wraps the per-metal dict
into a :class:`~vnfin.metals.models.MetalHistory`.

Mirrors :class:`~vnfin.gold.worldbank_cmo.WorldBankCmoGoldSource`'s fetch structure: it
iterates :data:`~vnfin._contracts.worldbank_cmo._CMO_ANNUAL_URLS` (per-URL SourceError →
next; all-fail → SourceUnavailable), validates bounds BEFORE any network call, and emits
one Jan-1 ``MetalBar`` per year in the inclusive ``[start.year, end.year]`` span.

Error discipline (gate note N2): every recoverable failure raises a
:class:`~vnfin.exceptions.SourceError` subclass (``SourceUnavailable`` / ``InvalidData`` /
``EmptyData``) so the source stays failover-safe.

Per-metal plausibility bands (evidence-based, gate-approved — re-derived per metal from its
own measured range, not byte-copied from gold):

* Silver ``XAG`` ``[0.10, 75.0]`` USD/oz — ceiling sits below platinum's all-time floor
  (80.93), so a platinum mis-read rejects by magnitude; floor ≪ silver's real min (0.91).
* Platinum ``XPT`` ``[50.0, 5000.0]`` USD/oz — floor sits above silver's all-time ceiling
  (39.80), so a silver mis-read rejects by magnitude; ceiling ≈ 2.9× platinum's high.

Clean-room: endpoint, sheet name, split-header layout and units were learned only from the
World Bank's own server. Zero vnstock.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from .._contracts.worldbank_cmo import (
    _CMO_ANNUAL_URLS,
    _USD_PER_OZ,
    MetalSpec,
    parse_cmo_annual,
)
from ..exceptions import EmptyData, InvalidData, SourceError, SourceUnavailable
from ..transport import HttpDataSource
from ..validation import validate_date_range
from .models import MetalBar, MetalHistory

#: Per-metal specs (canonical lower-case metal name -> MetalSpec). Bands are gate-approved.
_SILVER_SPEC = MetalSpec(product="XAG", name_row="Silver", min_usd_oz=0.10, max_usd_oz=75.0)
_PLATINUM_SPEC = MetalSpec(
    product="XPT", name_row="Platinum", min_usd_oz=50.0, max_usd_oz=5000.0
)


class WorldBankCmoMetalSource(HttpDataSource):
    """Annual silver/platinum (USD/oz) history from the World Bank CMO Pink Sheet xlsx.

    ``http_get(url, params, headers) -> response bytes`` is injectable so unit tests never
    touch the network (an injected stub returns the xlsx bytes directly). ``metal`` is the
    canonical lower-case name (``"silver"`` / ``"platinum"``) — the public facade
    canonicalizes a name or product code into it before constructing this source.
    """

    NAME = "worldbank_cmo_metal"

    _SPECS = {"silver": _SILVER_SPEC, "platinum": _PLATINUM_SPEC}

    def __init__(self, metal: str, *, http_get=None, timeout: float = 25.0):
        super().__init__(http_get=http_get, timeout=timeout)
        if metal not in self._SPECS:
            # Defensive: the facade canonicalizes first, but guard direct construction.
            valid = ", ".join(sorted(self._SPECS))
            raise InvalidData(
                f"metal {metal!r} not supported by {self.NAME}; supported: {valid}"
            )
        self._metal = metal
        self._spec = self._SPECS[metal]

    @property
    def name(self) -> str:
        return self.NAME

    def get_history(self, start: date, end: date) -> MetalHistory:
        """Fetch the CMO annual series for this metal and emit one Jan-1 ``MetalBar`` per
        year in the inclusive ``[start.year, end.year]`` span.

        Validates bounds fail-closed BEFORE any network call. Iterates
        :data:`_CMO_ANNUAL_URLS` in order: a per-URL transport/non-xlsx/parse failure falls
        through to the next; all-fail → :class:`~vnfin.exceptions.SourceUnavailable`. No
        years in span → :class:`~vnfin.exceptions.EmptyData` naming the metal. Every
        recoverable failure is a :class:`~vnfin.exceptions.SourceError` subclass (N2).
        """
        lo, hi = validate_date_range(
            start, end, name=f"{self.NAME}.{self._metal}.history"
        )

        annual = self._fetch_annual()  # {year: usd_per_oz}

        lo_year, hi_year = lo.year, hi.year
        bars = [
            MetalBar(date=date(year, 1, 1), price=price)
            for year, price in sorted(annual.items())
            if lo_year <= year <= hi_year
        ]
        if not bars:
            raise EmptyData(
                f"{self.NAME}: no annual {self._metal} ({self._spec.product}) "
                f"observations in {lo_year}..{hi_year}"
            )
        return MetalHistory(
            product=self._spec.product,
            unit=_USD_PER_OZ,
            value_unit=_USD_PER_OZ,
            currency="USD",
            source=self.NAME,
            bars=tuple(bars),
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def _fetch_annual(self) -> dict:
        """Try each vintage URL in order; return ``{year: usd_per_oz}`` from the first that
        fetches + parses for this metal's spec. A per-URL ``SourceError`` (transport/
        non-xlsx/parse/out-of-band) is recorded and the next URL is tried; all-fail →
        ``SourceUnavailable`` carrying the per-URL reasons. A non-``SourceError``
        propagates (N2: a programmer bug fails loud)."""
        reasons = []
        for url in _CMO_ANNUAL_URLS:
            try:
                raw = self._request_bytes(url)
                return parse_cmo_annual(raw, self._spec)
            except SourceError as exc:
                reasons.append(f"{url}: {type(exc).__name__}: {exc}")
                continue
        joined = "; ".join(reasons) or "no CMO URLs configured"
        raise SourceUnavailable(f"{self.NAME}: all CMO annual URLs failed -> {joined}")
