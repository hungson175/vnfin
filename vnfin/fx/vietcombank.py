"""Vietcombank public XML FX feed adapter (clean-room, no-key).

Built only against Vietcombank's own public feed
``GET https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10`` and its
live-verified XML shape — see ``docs/sources/fx-vietcombank.md`` for provenance and terms
(marked "for reference only"; respect the self-declared 1-request/5-min cadence).

Each ``<Exrate CurrencyCode Buy Transfer Sell/>`` is already **VND per 1 unit of the foreign
currency**. We use ``Transfer`` (telegraphic-transfer quote) as the rate, ``Buy``→bid, ``Sell``→ask.
NOTE: ``Transfer`` is a commercial-bank reference quote, **not** the SBV central rate. Spot only.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET

from ..coerce import parse_provider_float
from ..exceptions import EmptyData, InvalidData
from ..transport import DEFAULT_UA
from .base import FXSource
from .models import FXRate

_VN_TZ = timezone(timedelta(hours=7))  # Asia/Ho_Chi_Minh; feed timestamps are VN-local

# Issue #113: VCB <DateTime> uses M/D/YYYY H:MM:SS with an optional AM/PM marker. Padding
# varies (live feed sends "6/18/2026 3:53:15 PM"), so the shape guard allows 1-2 digit
# month/day/hour; strptime then validates the actual values. This gates a present-but-
# malformed timestamp so it raises instead of silently falling back to now().
_VCB_TS = re.compile(r"^\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2}(?: [AP]M)?$")


class VietcombankFXSource(FXSource):
    NAME = "vietcombank"
    BASE_URL = "https://portal.vietcombank.com.vn"
    XML_PATH = "/Usercontrols/TVPortal.TyGia/pXML.aspx"

    def get_rates(self, quote: str = "VND") -> tuple[FXRate, ...]:
        self._check_quote(quote)
        url = self.BASE_URL + self.XML_PATH
        text = self._request_text(url, params={"b": "10"}, headers={"User-Agent": DEFAULT_UA})
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            raise InvalidData(f"{self.name}: malformed XML response") from exc

        as_of = self._as_of(root)
        out: list[FXRate] = []
        for node in root.iter("Exrate"):
            code = (node.get("CurrencyCode") or "").strip().upper()
            # Issue #47: skip the provider's VND/VND self-rate (and any row whose
            # base is the quote currency).
            if code == self.QUOTE:
                continue
            transfer = self._num(node.get("Transfer"), required=True, label="Transfer")
            if not code or transfer is None or transfer <= 0:
                continue  # no usable transfer (VND-per-unit) rate
            bid = self._num(node.get("Buy"), label="Buy")
            ask = self._num(node.get("Sell"), label="Sell")
            try:
                out.append(self._build_rate(code, transfer, as_of, bid=bid, ask=ask))
            except InvalidData:
                continue
        if not out:
            raise EmptyData(f"{self.name}: no usable rates in feed")
        out.sort(key=lambda r: r.base)
        return tuple(out)

    @staticmethod
    def _num(value, *, required: bool = False, label: str = "rate"):
        """Parse a VCB rate string like ``"26,111.00"`` -> float.

        Returns ``None`` only when the field is absent or empty/whitespace.
        A present but non-numeric, non-finite, or boolean value raises
        :class:`InvalidData` so provider schema drift is not silently erased.
        """
        if value is None:
            return None
        text = str(value).strip()
        if text == "":
            return None
        normalized = text.replace(",", "")
        return parse_provider_float(normalized, label=label, source="vietcombank")

    @staticmethod
    def _as_of(root) -> datetime:
        node = root.find("DateTime")
        text = node.text.strip() if node is not None and node.text else ""
        if not text:
            # Missing/blank <DateTime>: keep the documented fallback-to-now contract.
            return datetime.now(timezone.utc)
        # Present & non-blank: it must be a real VCB timestamp. A malformed value is
        # provider freshness-metadata corruption and must surface, not be masked as now().
        if _VCB_TS.fullmatch(text):
            for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S"):
                try:
                    naive = datetime.strptime(text, fmt)
                    return naive.replace(tzinfo=_VN_TZ).astimezone(timezone.utc)
                except ValueError:
                    continue
        raise InvalidData(f"vietcombank: malformed <DateTime> {text!r}")
