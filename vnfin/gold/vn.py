"""Vietnam domestic gold adapters (spot-only, VND per *chỉ*).

Both dealers quote a two-sided buy/sell spread. Prices are normalized to **VND per
chỉ** (1 chỉ = 1/10 lượng/tael):

* **BTMC** (Bảo Tín Minh Châu) — indexed-key JSON; prices are full-digit VND strings.
* **PNJ** — clean JSON; prices are in *thousand* VND per chỉ, so multiply by 1000.

Neither exposes a usable multi-day history endpoint (BTMC's feed carries only same-day
intraday snapshots), so both are spot-only: ``provides_history = False``.

Shapes, units and the public widget key for BTMC were taken from the provider's own
servers and docs/research/2026-06-18-gold-vietnam-domestic.md (clean-room; no vnstock).
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone

from ..exceptions import EmptyData, InvalidData, SourceUnavailable
from .base import VN_TZ, GoldSource
from .models import GoldQuote

_VND_PER_CHI = "VND/chi"


class _VNGoldSource(GoldSource):
    """Shared logic for VN dealers: transport wrapping, JSON parse, quote selection."""

    provides_spot = True
    provides_history = False

    def _fetch_json(self, url, params=None):
        try:
            text = self._http_get(url, params, None)
        except Exception as exc:  # transport-level
            raise SourceUnavailable(f"{self.name} transport error: {exc}") from exc
        try:
            return json.loads(text)
        except (ValueError, TypeError) as exc:
            raise InvalidData(f"{self.name}: non-JSON response") from exc

    @staticmethod
    def _price(raw, name: str) -> float:
        try:
            val = float(raw)
        except (TypeError, ValueError) as exc:
            raise InvalidData(f"{name}: malformed price {raw!r}") from exc
        if not math.isfinite(val):
            raise InvalidData(f"{name}: non-finite price {raw!r}")
        if val < 0:
            raise InvalidData(f"{name}: negative price {raw!r}")
        return val

    def get_quote(self, product: str) -> GoldQuote:
        """Return the first quote whose product name contains ``product`` (case-insensitive)."""
        needle = product.strip().lower()
        for q in self.get_quotes():
            if needle in q.product.lower():
                return q
        raise EmptyData(f"{self.name}: no product matching {product!r}")


class BTMCGoldSource(_VNGoldSource):
    """Bảo Tín Minh Châu public price API (api.btmc.vn). VND/chỉ, full-digit strings."""

    name = "btmc"
    BASE_URL = "http://api.btmc.vn/api/BTMCAPI/getpricebtmc"
    # Fixed public widget key shipped client-side by BTMC's own ticker (no login/token).
    WIDGET_KEY = "3kd8ub1llcg9t45hnoh8hmn7t5kc2v"

    def get_quotes(self) -> tuple[GoldQuote, ...]:
        parsed = self._fetch_json(self.BASE_URL, {"key": self.WIDGET_KEY})
        try:
            rows = parsed["DataList"]["Data"]
        except (KeyError, TypeError) as exc:
            raise InvalidData(f"{self.name}: missing DataList.Data") from exc
        if not rows:
            raise EmptyData(f"{self.name}: empty DataList")

        now = datetime.now(timezone.utc)
        quotes: list[GoldQuote] = []
        for row in rows:
            if not isinstance(row, dict):
                raise InvalidData(f"{self.name}: row is not an object")
            idx = self._row_index(row)
            name = row.get(f"@n_{idx}")
            if not name:
                raise InvalidData(f"{self.name}: row {idx} missing name")
            buy = self._price(row.get(f"@pb_{idx}"), self.name)
            sell = self._price(row.get(f"@ps_{idx}"), self.name)
            karat = row.get(f"@k_{idx}") or None
            tm = self._parse_dt(row.get(f"@d_{idx}"))
            quotes.append(
                GoldQuote(
                    time=tm,
                    product=name,
                    buy=buy,
                    sell=sell,
                    unit=_VND_PER_CHI,
                    currency="VND",
                    source=self.name,
                    fetched_at_utc=now,
                    karat=karat,
                )
            )
        return tuple(quotes)

    def _row_index(self, row: dict) -> str:
        # Keys carry a per-row index suffix (@row + @n_N/@pb_N/...). Prefer @row;
        # fall back to parsing it off an indexed key.
        idx = row.get("@row")
        if idx:
            return str(idx)
        for k in row:
            if k.startswith("@n_"):
                return k[len("@n_"):]
        raise InvalidData(f"{self.name}: cannot determine row index")

    def _parse_dt(self, raw):
        if not raw:
            raise InvalidData(f"{self.name}: missing timestamp")
        try:
            naive = datetime.strptime(raw.strip(), "%d/%m/%Y %H:%M")
        except (ValueError, TypeError, AttributeError) as exc:
            raise InvalidData(f"{self.name}: bad timestamp {raw!r}") from exc
        return naive.replace(tzinfo=VN_TZ)


class PNJGoldSource(_VNGoldSource):
    """PNJ ecom-frontend gold-price API (edge-api.pnj.io). Thousand-VND/chỉ -> x1000."""

    name = "pnj"
    BASE_URL = "https://edge-api.pnj.io/ecom-frontend/v1/get-gold-price"
    PRICE_SCALE = 1000.0  # feed is in thousand VND per chỉ

    def get_quotes(self) -> tuple[GoldQuote, ...]:
        parsed = self._fetch_json(self.BASE_URL)
        try:
            rows = parsed["data"]
        except (KeyError, TypeError) as exc:
            raise InvalidData(f"{self.name}: missing data array") from exc
        if not rows:
            raise EmptyData(f"{self.name}: empty data array")

        now = datetime.now(timezone.utc)
        # PNJ has no timestamp in its body; stamp the fetch time as the quote time.
        quotes: list[GoldQuote] = []
        for row in rows:
            if not isinstance(row, dict):
                raise InvalidData(f"{self.name}: row is not an object")
            code = row.get("masp")
            name = row.get("tensp") or code
            if not name:
                raise InvalidData(f"{self.name}: row missing product name")
            raw_buy = row.get("giamua")
            raw_sell = row.get("giaban")
            # "Raw gold purchase" rows (masp RAW_*) are buy-only: one side is blank ("")
            # because PNJ buys but does not sell that grade. Skip incomplete rows rather
            # than failing the whole feed; only NON-empty garbage prices are InvalidData.
            if self._is_blank(raw_buy) or self._is_blank(raw_sell):
                continue
            buy = self._price(raw_buy, self.name) * self.PRICE_SCALE
            sell = self._price(raw_sell, self.name) * self.PRICE_SCALE
            quotes.append(
                GoldQuote(
                    time=now,
                    product=code or name,
                    buy=buy,
                    sell=sell,
                    unit=_VND_PER_CHI,
                    currency="VND",
                    source=self.name,
                    fetched_at_utc=now,
                )
            )
        if not quotes:
            raise EmptyData(f"{self.name}: no priced rows in feed")
        return tuple(quotes)

    @staticmethod
    def _is_blank(raw) -> bool:
        return raw is None or (isinstance(raw, str) and raw.strip() == "")
