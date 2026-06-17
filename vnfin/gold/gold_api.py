"""World gold spot adapter — api.gold-api.com (XAU/USD, also XAG/USD).

Single latest tick only (no history): ``provides_history = False``. ``price`` is USD
per troy ounce; there is no two-sided spread, so the returned :class:`GoldQuote` sets
``buy == sell == price``. ``updatedAt`` is ISO-8601 UTC.

Shape from docs/research/2026-06-18-gold-world.md and the provider's own server
(clean-room; no vnstock).
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone

from ..exceptions import EmptyData, InvalidData, SourceUnavailable
from .base import GoldSource
from .models import GoldQuote

_USD_PER_OZ = "USD/oz"


class GoldApiSource(GoldSource):
    """Live world gold (or silver) spot in USD/oz. ``symbol`` selects XAU or XAG."""

    name = "gold-api"
    provides_spot = True
    provides_history = False
    BASE_URL = "https://api.gold-api.com/price"

    def __init__(self, http_get=None, timeout: float = 25.0, symbol: str = "XAU"):
        super().__init__(http_get=http_get, timeout=timeout)
        self.symbol = symbol.strip().upper()

    def get_quotes(self) -> tuple[GoldQuote, ...]:
        return (self.get_quote(),)

    def get_quote(self) -> GoldQuote:
        url = f"{self.BASE_URL}/{self.symbol}"
        try:
            text = self._http_get(url, None, None)
        except Exception as exc:  # transport-level
            raise SourceUnavailable(f"{self.name} transport error: {exc}") from exc
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError) as exc:
            raise InvalidData(f"{self.name}: non-JSON response") from exc
        if not isinstance(parsed, dict):
            raise InvalidData(f"{self.name}: unexpected payload type")
        # Provider signals an unknown symbol with {"error": "..."}.
        if "error" in parsed:
            raise EmptyData(f"{self.name}: {parsed.get('error')}")
        if "price" not in parsed:
            raise InvalidData(f"{self.name}: missing price field")
        try:
            price = float(parsed["price"])
        except (TypeError, ValueError) as exc:
            raise InvalidData(f"{self.name}: malformed price {parsed.get('price')!r}") from exc
        if not math.isfinite(price) or price < 0:
            raise InvalidData(f"{self.name}: non-finite/negative price {parsed.get('price')!r}")

        tm = self._parse_iso(parsed.get("updatedAt"))
        symbol = parsed.get("symbol") or self.symbol
        return GoldQuote(
            time=tm,
            product=symbol,
            buy=price,
            sell=price,
            unit=_USD_PER_OZ,
            currency=parsed.get("currency") or "USD",
            source=self.name,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def _parse_iso(self, raw):
        if not raw:
            return datetime.now(timezone.utc)
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except (ValueError, TypeError) as exc:
            raise InvalidData(f"{self.name}: bad updatedAt {raw!r}") from exc
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
