"""KIS Vietnam price source (TradingView-UDF backend).

KIS Securities Vietnam exposes a TradingView-UDF style chart-history endpoint.
The response is a BARE UDF object (top-level ``t/o/h/l/c/v/s`` parallel arrays),
so no envelope unwrap is needed. Prices are in RAW VND (``PRICE_SCALE = 1.0``).

Provenance, auth, robots/ToS, rate-limit, adjustment, and compliance notes live in
``docs/sources/kis.md``. Built clean-room against the provider's own server and the
public UDF query protocol only.
"""
from __future__ import annotations

from ..models import AdjustmentPolicy, Interval
from .udf import UDFSource


class KISVietnamSource(UDFSource):
    """KIS Vietnam adapter over the shared UDF transport base."""

    NAME = "kis"
    BASE_URL = "https://api.ikis.kisvn.vn"
    HISTORY_PATH = "/api/v3/chart/history"

    # Daily + all verified intraday resolutions (1/5/15/30/60 min).
    SUPPORTED = frozenset(
        {
            Interval.D1,
            Interval.H1,
            Interval.M30,
            Interval.M15,
            Interval.M5,
            Interval.M1,
        }
    )
    RESOLUTION_MAP = {
        Interval.D1: "1D",
        Interval.H1: "60",
        Interval.M30: "30",
        Interval.M15: "15",
        Interval.M5: "5",
        Interval.M1: "1",
    }

    # Feed prints raw VND (recent FPT closes ~72,900) -> no scaling.
    PRICE_SCALE = 1.0

    # History is non-homogeneous: an adjusted historical tail (fractional, scaled
    # to a different basis) plus a raw-VND recent head. See docs/sources/kis.md.
    ADJUSTMENT_POLICY = AdjustmentPolicy.MIXED

    # Exchange is symbol-dependent; left lazy/None for the MVP.
    EXCHANGE = None

    def _build_params(self, provider_symbol, resolution, frm, to):
        # Live contract: ?symbol=FPT&resolution=1D&from=UNIX&to=UNIX
        return {
            "symbol": provider_symbol,
            "resolution": resolution,
            "from": frm,
            "to": to,
        }
