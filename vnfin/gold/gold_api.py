"""World gold spot adapter — api.gold-api.com (XAU/USD, also XAG/USD).

Single latest tick only (no history): ``provides_history = False``. ``price`` is USD
per troy ounce; there is no two-sided spread, so the returned :class:`GoldQuote` sets
``buy == sell == price``. ``updatedAt`` is ISO-8601 UTC.

Shape from docs/research/2026-06-18-gold-world.md and the provider's own server
(clean-room; no vnstock).
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone

from ..coerce import parse_provider_float
from ..exceptions import EmptyData, InvalidData, VnfinError
from .base import GoldSource
from .models import GoldQuote

_USD_PER_OZ = "USD/oz"

# Issue #112: ``updatedAt`` is documented as a full ISO-8601 UTC timestamp
# (YYYY-MM-DDTHH:MM:SSZ). ``datetime.fromisoformat`` also accepts date-only,
# compact-date, and ISO week-date strings, which would silently become a
# midnight-UTC quote. Require an explicit calendar date + ``T`` + ``HH:MM:SS``
# (optional fractional seconds and offset) before parsing so non-timestamp
# freshness metadata raises stable ``InvalidData`` instead.
_FULL_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$"
)

# Supported world spot symbols for api.gold-api.com (XAU/USD and XAG/USD).
_GOLD_API_SYMBOLS = frozenset({"XAU", "XAG"})


class GoldApiSource(GoldSource):
    """Live world gold (or silver) spot in USD/oz. ``symbol`` selects XAU or XAG."""

    name = "gold-api"
    provides_spot = True
    provides_history = False
    #: Declared unit for the failover unit-homogeneity guard (world gold = USD/oz).
    unit = _USD_PER_OZ
    BASE_URL = "https://api.gold-api.com/price"

    def __init__(self, http_get=None, timeout: float = 25.0, symbol: str = "XAU"):
        super().__init__(http_get=http_get, timeout=timeout)
        # Issue #52: validate symbol before any provider call; reject non-string,
        # empty, or whitespace-only values with a stable VnfinError.
        if not isinstance(symbol, str) or not symbol.strip():
            raise VnfinError(f"gold-api: symbol must be a non-empty string, got {symbol!r}")
        normalized = symbol.strip().upper()
        if normalized not in _GOLD_API_SYMBOLS:
            raise VnfinError(
                f"gold-api: unsupported symbol {symbol!r}; supported: {sorted(_GOLD_API_SYMBOLS)}"
            )
        self.symbol = normalized

    def get_quotes(self) -> tuple[GoldQuote, ...]:
        return (self.get_quote(),)

    def get_quote(self) -> GoldQuote:
        url = f"{self.BASE_URL}/{self.symbol}"
        parsed = self._request_json(url, params=None, headers=None)
        if not isinstance(parsed, dict):
            raise InvalidData(f"{self.name}: unexpected payload type")
        # Provider signals an unknown symbol with {"error": "..."}.
        if "error" in parsed:
            raise EmptyData(f"{self.name}: {parsed.get('error')}")
        if "price" not in parsed:
            raise InvalidData(f"{self.name}: missing price field")
        price = parse_provider_float(parsed["price"], label="price", source=self.name)
        # Issue #12: zero price is not a valid spot, and the unit is USD/oz so the
        # reported currency must be USD (or missing, in which case we default to USD).
        if not math.isfinite(price) or price <= 0:
            raise InvalidData(f"{self.name}: non-positive/invalid price {parsed.get('price')!r}")
        currency = parsed.get("currency")
        if currency is not None and currency != "USD":
            raise InvalidData(f"{self.name}: expected USD currency, got {currency!r}")

        tm = self._parse_iso(parsed.get("updatedAt"))
        symbol = parsed.get("symbol") or self.symbol
        return GoldQuote(
            time=tm,
            product=symbol,
            buy=price,
            sell=price,
            unit=_USD_PER_OZ,
            currency=currency or "USD",
            source=self.name,
            fetched_at_utc=datetime.now(timezone.utc),
        )

    def _parse_iso(self, raw):
        if not raw:
            return datetime.now(timezone.utc)
        text = str(raw)
        # Reject date-only / compact / ISO-week / time-only forms that
        # ``fromisoformat`` would otherwise accept as midnight UTC (issue #112).
        if not _FULL_TIMESTAMP_RE.match(text):
            raise InvalidData(f"{self.name}: bad updatedAt {raw!r}")
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except (ValueError, TypeError) as exc:
            raise InvalidData(f"{self.name}: bad updatedAt {raw!r}") from exc
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
