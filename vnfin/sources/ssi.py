"""SSI iBoard price-history adapter.

Clean-room implementation against the provider's own public TradingView-UDF
style history endpoint:

    GET https://iboard-api.ssi.com.vn/statistics/charts/history
        ?resolution=<token>&symbol=<TICKER>&from=<unix>&to=<unix>

The response is ENVELOPED: ``{"code":"SUCCESS","data":{t,o,h,l,c,v,s,...},
"status":"ok"}``. The UDF status field ``s`` lives inside ``data``; we override
``_extract`` to hand the shared base a plain UDF dict.

Provenance, compliance, adjustment-policy reasoning, and intraday capability are
documented in ``docs/sources/ssi.md``. Runtime fetch only — no caching or
redistribution of provider data.
"""
from __future__ import annotations

from ..exceptions import InvalidData, SourceUnavailable
from ..models import AdjustmentPolicy, Interval
from .udf import UDFSource


class SSIiBoardSource(UDFSource):
    NAME = "ssi"
    BASE_URL = "https://iboard-api.ssi.com.vn"
    HISTORY_PATH = "/statistics/charts/history"

    # Daily is required; the intraday tokens below were each verified live to
    # return correctly-spaced bars. W1/MN1 are intentionally omitted (their
    # tokens were ambiguous during probing). See docs/sources/ssi.md.
    SUPPORTED = frozenset(
        {Interval.D1, Interval.H1, Interval.M30, Interval.M15, Interval.M5, Interval.M1}
    )
    RESOLUTION_MAP = {
        Interval.D1: "1D",
        Interval.H1: "60",
        Interval.M30: "30",
        Interval.M15: "15",
        Interval.M5: "5",
        Interval.M1: "1",
    }

    # FPT close ~7 in 2015 vs ~72 in 2026 -> historical prices are back-adjusted.
    ADJUSTMENT_POLICY = AdjustmentPolicy.PROVIDER_ADJUSTED
    # Feed prints FPT close ~72 -> thousands of VND; x1000 to reach VND.
    PRICE_SCALE = 1000.0
    # Exchange is symbol-dependent; left lazy/None for the MVP.
    EXCHANGE = None

    def _build_params(self, provider_symbol, resolution, frm, to):
        return {"resolution": resolution, "symbol": provider_symbol, "from": frm, "to": to}

    def _extract(self, parsed):
        # Envelope: the UDF arrays (and status `s`) live under "data". Validate the
        # outer envelope before returning the inner UDF dict so a provider-side
        # error (e.g. code="FAIL" or status="error") never parses as empty/success.
        if not isinstance(parsed, dict):
            raise InvalidData(f"{self.name}: envelope is not an object")
        code = parsed.get("code")
        if code != "SUCCESS":
            if code in ("FAIL", "ERROR"):
                raise SourceUnavailable(f"{self.name}: envelope code={code}")
            raise InvalidData(f"{self.name}: unexpected envelope code={code!r}")
        status = parsed.get("status")
        if status != "ok":
            if status == "error":
                raise SourceUnavailable(f"{self.name}: envelope status={status}")
            raise InvalidData(f"{self.name}: unexpected envelope status={status!r}")
        return parsed.get("data") or {}
