"""vnfin.gold — clean-room gold price adapters (Vietnam domestic + world XAU).

Public surface:

* Models — :class:`GoldQuote` (spot buy/sell), :class:`GoldBar` + :class:`GoldHistory`
  (a daily series, for the world-XAU history source).
* Port — :class:`GoldSource` (the small interface every adapter implements).
* VN domestic adapters (spot-only, VND/chỉ) — :class:`BTMCGoldSource`, :class:`PNJGoldSource`.
* World adapters — :class:`GoldApiSource` (spot XAU/USD, no history) and
  :class:`CurrencyApiGoldSource` (daily XAU/USD EOD history + spot).

Currency/unit is always stated explicitly on the result object: VN sources return
``currency="VND"`` / ``unit="VND/chi"`` (price per *chỉ* = 1/10 lượng); world sources
return ``currency="USD"`` / ``unit="USD/oz"`` (USD per troy ounce). Every result carries
its source name and ``fetched_at_utc``. All adapters wrap transport failures as
:class:`vnfin.exceptions.SourceUnavailable` and malformed/garbage data as
:class:`vnfin.exceptions.InvalidData`, so they are failover-safe.

Clean-room: endpoints, units and shapes were learned only from the provider's own
servers and the project's research docs — never from vnstock or any derivative.
"""
from __future__ import annotations

from .base import GoldSource
from .currency_api import CurrencyApiGoldSource
from .gold_api import GoldApiSource
from .models import GoldBar, GoldHistory, GoldQuote
from .vn import BTMCGoldSource, PNJGoldSource

__all__ = [
    # models
    "GoldQuote",
    "GoldBar",
    "GoldHistory",
    # port
    "GoldSource",
    # VN domestic (spot-only)
    "BTMCGoldSource",
    "PNJGoldSource",
    # world
    "GoldApiSource",
    "CurrencyApiGoldSource",
]
