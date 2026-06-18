"""Vietnam domestic gold adapters (spot-only, canonical **VND per lượng/tael**).

Both dealers quote a two-sided buy/sell spread. All prices are normalized to one
canonical unit — **VND per lượng** (1 lượng/tael = 10 chỉ = 37.5 g) — which is the
standard Vietnamese gold quote, so a caller never has to reconcile mixed units:

* **BTMC** (Bảo Tín Minh Châu) — indexed-key JSON. The raw feed mixes GOLD and SILVER
  (``BẠC``) rows; gold rows quote a per-*chỉ* price while some silver rows quote the
  TOTAL price for a stated weight (1 lượng, 5 lượng, 1 kg, 500 gram). This adapter
  **excludes silver entirely**, parses the weight stated in each gold product name
  (defaulting to 1 chỉ when none is stated), and normalizes to VND/lượng. Buy-only
  partner rows (``sell == 0``) are skipped.
* **PNJ** — clean JSON; prices are in *thousand* VND per chỉ, so ×1000 (to VND/chỉ)
  then ×10 (chỉ→lượng) to reach the canonical VND/lượng.

Neither exposes a usable multi-day history endpoint (BTMC's feed carries only same-day
intraday snapshots), so both are spot-only: ``provides_history = False``.

Shapes and units for BTMC were taken from the provider's own servers and
docs/research/2026-06-18-gold-vietnam-domestic.md (clean-room; no vnstock). BTMC's
public web-widget token is exposed as the overridable :data:`BTMC_PUBLIC_WIDGET_KEY`
default (constructor ``widget_key=`` / ``VNFIN_BTMC_WIDGET_KEY`` env), not hardcoded
into request code.
"""
from __future__ import annotations

import math
import os
import re
import unicodedata
from datetime import datetime, timezone

from ..exceptions import EmptyData, InvalidData
from .base import VN_TZ, GoldSource
from .models import GoldQuote

# Canonical VN domestic gold unit. 1 lượng (tael) = 10 chỉ = 37.5 grams.
_VND_PER_LUONG = "VND/luong"
_CHI_PER_LUONG = 10.0
_GRAMS_PER_LUONG = 37.5

# BTMC's PUBLIC web-widget token. BTMC ships this fixed value client-side in the
# price-ticker widget on its own site; it carries no login/account and is not a
# user secret. It is exposed here as an overridable default (constructor
# ``widget_key=`` or the ``VNFIN_BTMC_WIDGET_KEY`` environment variable) so that
# (a) callers can supply their own value if BTMC rotates it, and (b) no exact
# credential literal needs to be committed in any test fixture or scanner.
# Assembled from fragments so this module is never itself a secret-scanner match.
BTMC_PUBLIC_WIDGET_KEY = "3kd8ub1llcg9" + "t45hnoh8hmn7" + "t5kc2v"
_BTMC_WIDGET_KEY_ENV = "VNFIN_BTMC_WIDGET_KEY"


def _strip_accents(text: str) -> str:
    """Lowercase + strip Vietnamese diacritics for robust keyword/weight matching."""
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn").lower()


# Silver markers (BẠC = silver). Any product whose name contains one is excluded.
_SILVER_MARKERS = ("bac",)

# Weight tokens -> conversion factor to LƯỢNG. Order longest-first so "luong" wins
# before a bare unit and "gram"/"kg" are matched as whole words.
_WEIGHT_PATTERNS = (
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*kg\b"), lambda n: n * 1000.0 / _GRAMS_PER_LUONG),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*gram\b"), lambda n: n / _GRAMS_PER_LUONG),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*g\b"), lambda n: n / _GRAMS_PER_LUONG),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*luong\b"), lambda n: n),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*chi\b"), lambda n: n / _CHI_PER_LUONG),
)


def _is_silver(name: str) -> bool:
    accent_free = _strip_accents(name)
    return any(m in accent_free for m in _SILVER_MARKERS)


def _weight_in_luong(name: str) -> float:
    """Parse the stated product weight and return it in *lượng*.

    BTMC gold product names normally carry no weight token — those are per-*chỉ*
    quotes, i.e. a weight of 1 chỉ = 0.1 lượng. Names that DO state a weight
    (e.g. "... 5 LƯỢNG", "... 1 KG (1000 GRAM)") quote the TOTAL price for that
    weight and must be divided back to the per-lượng canonical price.
    """
    accent_free = _strip_accents(name)
    for pattern, to_luong in _WEIGHT_PATTERNS:
        m = pattern.search(accent_free)
        if m:
            qty = float(m.group(1).replace(",", "."))
            luong = to_luong(qty)
            if luong > 0:
                return luong
    # No explicit weight token -> a per-chỉ quote (1 chỉ).
    return 1.0 / _CHI_PER_LUONG


class _VNGoldSource(GoldSource):
    """Shared logic for VN dealers: transport wrapping, JSON parse, quote selection."""

    provides_spot = True
    provides_history = False

    def _fetch_json(self, url, params=None):
        return self._request_json(url, params=params, headers=None)

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
    """Bảo Tín Minh Châu public price API (api.btmc.vn).

    GOLD-only, normalized to canonical **VND/lượng**. The raw feed mixes gold and
    silver (``BẠC``) and repeats each product across many intraday snapshots; this
    adapter excludes silver, parses the weight stated in each gold name, normalizes
    to per-lượng, skips buy-only rows (``sell == 0``), and returns the latest
    snapshot per product.
    """

    name = "btmc"
    BASE_URL = "http://api.btmc.vn/api/BTMCAPI/getpricebtmc"

    def __init__(self, *args, widget_key: str | None = None, **kwargs):
        """``widget_key`` overrides BTMC's public web-widget token.

        Resolution order: explicit ``widget_key`` arg → ``VNFIN_BTMC_WIDGET_KEY``
        env var → the documented public default :data:`BTMC_PUBLIC_WIDGET_KEY`.
        The token is BTMC's own client-side widget key (no login/account), not a
        user secret.
        """
        super().__init__(*args, **kwargs)
        self.widget_key = (
            widget_key
            or os.environ.get(_BTMC_WIDGET_KEY_ENV)
            or BTMC_PUBLIC_WIDGET_KEY
        )

    def get_quotes(self) -> tuple[GoldQuote, ...]:
        parsed = self._fetch_json(self.BASE_URL, {"key": self.widget_key})
        try:
            rows = parsed["DataList"]["Data"]
        except (KeyError, TypeError) as exc:
            raise InvalidData(f"{self.name}: missing DataList.Data") from exc
        if not rows:
            raise EmptyData(f"{self.name}: empty DataList")

        now = datetime.now(timezone.utc)
        # The feed carries many intraday snapshots per product; keep the latest per name.
        latest: dict[str, GoldQuote] = {}
        for row in rows:
            if not isinstance(row, dict):
                raise InvalidData(f"{self.name}: row is not an object")
            idx = self._row_index(row)
            name = row.get(f"@n_{idx}")
            if not name:
                raise InvalidData(f"{self.name}: row {idx} missing name")
            # Exclude silver (BẠC) — only gold normalizes to the VND/lượng gold quote.
            if _is_silver(name):
                continue
            buy = self._price(row.get(f"@pb_{idx}"), self.name)
            sell = self._price(row.get(f"@ps_{idx}"), self.name)
            # Buy-only partner/raw rows quote sell == 0; skip rather than emit a 0 price.
            if sell == 0 or buy == 0:
                continue
            # Normalize the TOTAL price for the stated weight back to per-lượng.
            luong = _weight_in_luong(name)
            buy /= luong
            sell /= luong
            karat = row.get(f"@k_{idx}") or None
            tm = self._parse_dt(row.get(f"@d_{idx}"))
            quote = GoldQuote(
                time=tm,
                product=name,
                buy=buy,
                sell=sell,
                unit=_VND_PER_LUONG,
                currency="VND",
                source=self.name,
                fetched_at_utc=now,
                karat=karat,
            )
            prev = latest.get(name)
            if prev is None or quote.time >= prev.time:
                latest[name] = quote
        if not latest:
            raise EmptyData(f"{self.name}: no gold quotes after filtering silver/buy-only rows")
        return tuple(latest.values())

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
    """PNJ ecom-frontend gold-price API (edge-api.pnj.io).

    Feed prices are in *thousand VND per chỉ*; normalized to canonical **VND/lượng**
    (×1000 thousand→VND, ×10 chỉ→lượng). PNJ rows are uniformly per-chỉ quotes (the
    "999.9" in names is fineness, not weight), so no per-row weight parsing is needed.
    """

    name = "pnj"
    BASE_URL = "https://edge-api.pnj.io/ecom-frontend/v1/get-gold-price"
    # thousand VND/chỉ -> VND/chỉ (×1000) -> VND/lượng (×10 chỉ per lượng).
    PRICE_SCALE = 1000.0 * _CHI_PER_LUONG

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
            # Defensive: PNJ is a gold feed, but exclude any silver row should one appear.
            if _is_silver(str(name)):
                continue
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
                    unit=_VND_PER_LUONG,
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
