"""World Bank historical-FX source (issue #159).

Serves **annual** USD/VND history from the World Bank WDI indicator ``PA.NUS.FCRF``
("Official exchange rate, LCU per US$, period average"). For country ``VNM`` this is
**VND per 1 USD** — already vnfin's canonical FX convention — so no unit re-derivation
is needed.

Clean-room: this adapter does **not** re-parse the World Bank envelope. It composes the
already-tested :class:`~vnfin.macro.worldbank.WorldBankMacroSource` (BOM-tolerant
``[meta, [obs…]]`` parsing, null-year skip, duplicate-date reject, country/indicator
identity guards) and only (a) maps the returned ``(date, value)`` points to
:class:`FXPoint`, applying an explicit **positive-rate** guard (macro series may validly
be negative; an FX rate must be ``> 0`` and finite), and (b) filters to the requested
inclusive **calendar-year** window. Runtime-fetch only; no bundled provider rows.

Provider terms: World Bank WDI is CC-BY 4.0 (attribution "Source: World Bank"). See
``docs/sources/fx-history-worldbank.md``. ``PA.NUS.FCRF`` is an annual **period-average**
rate — not year-end and not the SBV central rate.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timezone
from typing import Optional

from ..exceptions import InvalidData
from ..macro.indicators import Frequency
from ..macro.worldbank import WorldBankMacroSource
from .history_models import FXHistory, FXPoint

#: WB official exchange rate indicator (LCU per US$, period average), annual.
_FCRF_CODE = "PA.NUS.FCRF"
#: Quote currency -> World Bank country whose LCU is that currency. v1: VND -> VNM.
_QUOTE_COUNTRY = {"VND": "VNM"}


class WorldBankFXHistorySource:
    """Annual FX-history adapter over World Bank ``PA.NUS.FCRF`` (composition).

    ``http_get(url, params, headers) -> response text`` is injectable so unit tests
    never touch the network (it is forwarded to the underlying World Bank source).
    """

    NAME = "worldbank_fx"

    def __init__(self, http_get=None, timeout: float = 25.0):
        self._wb = WorldBankMacroSource(http_get=http_get, timeout=timeout)

    @property
    def name(self) -> str:
        return self.NAME

    def get_history(
        self,
        base: str = "USD",
        quote: str = "VND",
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> FXHistory:
        """Fetch the annual ``base``/``quote`` series and map it to :class:`FXHistory`.

        ``start``/``end`` are interpreted as an inclusive **calendar-year** window
        (by ``.year``), so a mid-year ``start`` never drops the Jan-1-stamped annual
        point of that year. ``None`` bounds mean "no lower/upper limit".
        """
        country = _QUOTE_COUNTRY[quote]
        unit = f"{quote} per 1 {base}"
        # Fetch the full annual series (one page) and filter locally by year so the
        # one-sided/two-sided window semantics are fully under our control (the WB
        # raw fetch treats a single year bound as a single-year window, which is wrong here).
        series = self._wb.get_indicator(country, _FCRF_CODE)

        lo_year = start.year if start is not None else None
        hi_year = end.year if end is not None else None

        points: list[FXPoint] = []
        for d, value in series.points:
            if lo_year is not None and d.year < lo_year:
                continue
            if hi_year is not None and d.year > hi_year:
                continue
            points.append(FXPoint(date=d, rate=self._validate_rate(value, d)))

        if not points:
            from ..exceptions import EmptyData

            raise EmptyData(
                f"{self.NAME}: no {base}/{quote} observations in requested window"
            )

        points.sort(key=lambda p: p.date)
        return FXHistory(
            base=base,
            quote=quote,
            points=tuple(points),
            unit=unit,
            frequency=Frequency.ANNUAL,
            source=self.NAME,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def _validate_rate(self, value, d: date) -> float:
        """Explicit FX positive-rate guard. Macro values may be negative; an FX rate
        must be a finite ``float`` strictly ``> 0`` (reject bool/non-finite/<=0)."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InvalidData(f"{self.NAME}: non-numeric FX rate {value!r} at {d.isoformat()}")
        if not math.isfinite(value) or value <= 0:
            raise InvalidData(
                f"{self.NAME}: non-positive/invalid FX rate {value!r} at {d.isoformat()}"
            )
        return float(value)
