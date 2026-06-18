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

from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET

from ..exceptions import EmptyData, InvalidData
from ..transport import DEFAULT_UA
from .base import FXSource
from .models import FXRate

_VN_TZ = timezone(timedelta(hours=7))  # Asia/Ho_Chi_Minh; feed timestamps are VN-local


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
            transfer = self._num(node.get("Transfer"))
            if not code or transfer is None or transfer <= 0:
                continue  # no usable transfer (VND-per-unit) rate
            try:
                out.append(
                    self._build_rate(
                        code, transfer, as_of, bid=self._num(node.get("Buy")), ask=self._num(node.get("Sell"))
                    )
                )
            except InvalidData:
                continue
        if not out:
            raise EmptyData(f"{self.name}: no usable rates in feed")
        out.sort(key=lambda r: r.base)
        return tuple(out)

    @staticmethod
    def _num(value):
        """Parse a VCB rate string like ``"26,111.00"`` -> float; None if blank/garbage."""
        if value is None:
            return None
        try:
            return float(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_of(root) -> datetime:
        node = root.find("DateTime")
        if node is not None and node.text:
            for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S"):
                try:
                    naive = datetime.strptime(node.text.strip(), fmt)
                    return naive.replace(tzinfo=_VN_TZ).astimezone(timezone.utc)
                except ValueError:
                    continue
        return datetime.now(timezone.utc)
