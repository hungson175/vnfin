"""Pinetree Securities price-history adapter (TradingView UDF, bare).

Clean-room: built only from the provider's own charting backend
(``https://charts.pinetree.vn``) and the public TradingView UDF protocol. No
third-party financial library was consulted.

Verified live (see ``docs/sources/pinetree.md``):

- The history endpoint returns a **bare** UDF object (top-level ``t/o/h/l/c/v/s``,
  no envelope), so no ``_extract`` override is needed.
- FPT daily closes print in **raw VND** (~73,000), so ``PRICE_SCALE = 1.0``.
- 2015 FPT opens (~7,300 raw VND) vs ~73,000 today indicate a back-adjusted
  series -> ``ADJUSTMENT_POLICY = PROVIDER_ADJUSTED``.
- Daily plus 1/5/15/30/60-minute resolutions all return data.
"""
from __future__ import annotations

from ..models import AdjustmentPolicy, Interval
from .udf import UDFSource


class PinetreeSource(UDFSource):
    NAME = "pinetree"
    BASE_URL = "https://charts.pinetree.vn"
    HISTORY_PATH = "/tv/history"

    # Daily is required; intraday tokens below were all verified to return data.
    SUPPORTED = frozenset(
        {
            Interval.D1,
            Interval.M1,
            Interval.M5,
            Interval.M15,
            Interval.M30,
            Interval.H1,
        }
    )
    RESOLUTION_MAP = {
        Interval.D1: "1D",
        Interval.M1: "1",
        Interval.M5: "5",
        Interval.M15: "15",
        Interval.M30: "30",
        Interval.H1: "60",
    }

    # FPT prints ~73,000 -> already raw VND, no thousands multiplier.
    PRICE_SCALE = 1.0
    # 2015 FPT (~7,300) vs ~73,000 now -> split/dividend back-adjusted series.
    ADJUSTMENT_POLICY = AdjustmentPolicy.PROVIDER_ADJUSTED
    # Exchange is symbol-dependent; left lazy/None for the MVP.
    EXCHANGE = None

    def _build_params(self, provider_symbol, resolution, frm, to):
        return {
            "symbol": provider_symbol,
            "resolution": resolution,
            "from": frm,
            "to": to,
        }
