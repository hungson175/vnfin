"""VNDirect price-history adapter.

Clean-room TradingView-UDF adapter over the VNDirect public charting backend
(``dchart-api.vndirect.com.vn``). Built only against the provider's own server
and the public UDF protocol. See ``docs/sources/vndirect.md`` for provenance,
the live-verified response shape, price-scale/adjustment reasoning, intraday
capability, and the compliance caveat (runtime fetch only, no redistribution).

Response shape (verified live): a BARE UDF object ``{t, o, h, l, c, v, s}`` —
no envelope — so ``_extract`` is inherited unchanged.
"""
from __future__ import annotations

from ..models import AdjustmentPolicy, Interval
from .udf import UDFSource


class VNDirectSource(UDFSource):
    NAME = "vndirect"
    BASE_URL = "https://dchart-api.vndirect.com.vn"
    HISTORY_PATH = "/dchart/history"

    # Daily is required; intraday 1/5/15/30/60-min are all verified live to return bars.
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
        Interval.D1: "D",
        Interval.M1: "1",
        Interval.M5: "5",
        Interval.M15: "15",
        Interval.M30: "30",
        Interval.H1: "60",
    }

    # FPT close prints ~72 in the feed (~72,000 VND market price) -> feed is in
    # thousands of VND. Scale up to plain VND.
    PRICE_SCALE = 1000.0

    # FPT 2015 close ~7.1 vs 2026 close ~72.3 -> series is split/dividend
    # back-adjusted by the provider.
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
