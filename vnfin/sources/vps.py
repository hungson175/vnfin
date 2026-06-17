"""VPS price source — clean-room adapter over the public TradingView UDF feed.

Bare-UDF history endpoint (no envelope). Daily history is deep and reliable;
intraday resolutions (1/5/15/30/60 min) are live-verified but have a limited
retention window — older intraday requests return ``s: "no_data"`` (mapped to
``EmptyData`` by the base).

Implemented solely against the host's own server and the public TradingView UDF
protocol. See ``docs/sources/vps.md`` for provenance, price-scale and
adjustment-policy reasoning, retention notes, and compliance caveats.
"""
from __future__ import annotations

from ..models import AdjustmentPolicy, Interval
from .udf import UDFSource


class VPSSource(UDFSource):
    NAME = "vps"
    BASE_URL = "https://histdatafeed.vps.com.vn"
    HISTORY_PATH = "/tradingview/history"

    # Daily is the guaranteed denominator; intraday tokens (1/5/15/30/60 min)
    # are live-verified to return data for recent windows.
    SUPPORTED = frozenset(
        {Interval.D1, Interval.M1, Interval.M5, Interval.M15, Interval.M30, Interval.H1}
    )
    RESOLUTION_MAP = {
        Interval.D1: "D",
        Interval.M1: "1",
        Interval.M5: "5",
        Interval.M15: "15",
        Interval.M30: "30",
        Interval.H1: "60",
    }

    # FPT prints ~70 daily / ~73 intraday -> feed is in thousands of VND.
    PRICE_SCALE = 1000.0

    # FPT ~8.3 (2015) vs ~70 (2024) on the same series -> split/dividend back-adjusted.
    ADJUSTMENT_POLICY = AdjustmentPolicy.PROVIDER_ADJUSTED

    # Exchange is symbol-dependent; left lazy/unset for the MVP.
    EXCHANGE = None

    def _build_params(self, provider_symbol, resolution, frm, to):
        return {
            "symbol": provider_symbol,
            "resolution": resolution,
            "from": frm,
            "to": to,
        }
