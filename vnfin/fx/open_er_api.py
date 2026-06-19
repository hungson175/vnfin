"""ExchangeRate-API open endpoint adapter (clean-room, no-key).

Built only against the provider's documented open endpoint
``GET https://open.er-api.com/v6/latest/USD`` and its live-verified JSON shape — see
``docs/sources/fx-open-er-api.md`` for provenance, terms (redistribution prohibited; attribution
requested), and rate limits.

Convention: with ``base_code = USD``, ``rates[X]`` is *X per 1 USD*. The canonical vnfin unit is
**VND per 1 base**, so ``X/VND = rates["VND"] / rates[X]`` (USD/VND is just ``rates["VND"]``).
One fetch (base=USD) yields every pair versus VND. Spot/current only — no history.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

from ..exceptions import EmptyData, InvalidData
from ..transport import DEFAULT_UA
from .base import FXSource
from .models import FXRate


class OpenErApiFXSource(FXSource):
    NAME = "open_er_api"
    BASE_URL = "https://open.er-api.com"
    LATEST_PATH = "/v6/latest/USD"  # USD base; cross-rates derived vs VND

    def get_rates(self, quote: str = "VND") -> tuple[FXRate, ...]:
        self._check_quote(quote)
        url = self.BASE_URL + self.LATEST_PATH
        payload = self._request_json(url, headers={"User-Agent": DEFAULT_UA})
        if not isinstance(payload, dict):
            raise InvalidData(f"{self.name}: unexpected payload type {type(payload).__name__}")
        if payload.get("result") != "success":
            raise EmptyData(f"{self.name}: provider result {payload.get('result')!r}")
        # The cross-rate math assumes USD-base data (rates[X] == X per 1 USD). If the
        # provider ever drifts the base, refuse rather than silently mis-derive rates.
        if payload.get("base_code") != "USD":
            raise InvalidData(
                f"{self.name}: expected USD-base payload, got base_code={payload.get('base_code')!r}"
            )
        rates = payload.get("rates")
        if not isinstance(rates, dict):
            raise InvalidData(f"{self.name}: missing rates object")
        vnd_per_usd = rates.get(self.QUOTE)
        if isinstance(vnd_per_usd, bool) or not isinstance(vnd_per_usd, (int, float)) or vnd_per_usd <= 0:
            raise InvalidData(f"{self.name}: missing/invalid {self.QUOTE} anchor")
        usd_self = rates.get("USD")
        if (
            isinstance(usd_self, bool)
            or not isinstance(usd_self, (int, float))
            or not math.isfinite(usd_self)
            or usd_self <= 0
            or abs(usd_self - 1.0) > 1e-9
        ):
            raise InvalidData(f"{self.name}: invalid USD self-rate anchor")
        as_of = self._as_of(payload)

        out: list[FXRate] = []
        for code, per_usd in rates.items():
            if code == self.QUOTE:
                continue  # skip VND/VND
            # Issue #28: reject malformed provider currency codes before building a rate.
            try:
                code = self._normalize_ccy(code)
            except InvalidData:
                continue
            if isinstance(per_usd, bool) or not isinstance(per_usd, (int, float)) or per_usd <= 0:
                continue  # unusable leg
            vnd_per_unit = vnd_per_usd / per_usd  # VND per 1 `code`
            try:
                out.append(self._build_rate(code, vnd_per_unit, as_of))
            except InvalidData:
                continue
        if not out:
            raise EmptyData(f"{self.name}: no usable rates")
        out.sort(key=lambda r: r.base)
        return tuple(out)

    @staticmethod
    def _as_of(payload: dict) -> datetime:
        ts = payload.get("time_last_update_unix")
        if isinstance(ts, (int, float)) and ts > 0:
            try:
                return datetime.fromtimestamp(int(ts), tz=timezone.utc)
            except (ValueError, OverflowError, OSError):
                # Issue #43: an out-of-range timestamp must not crash the source;
                # fall back to a tz-aware "now" so the rate remains usable.
                pass
        return datetime.now(timezone.utc)
