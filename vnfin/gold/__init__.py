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
    # facade
    "vn",
    "world",
    "source",
]

_VN_PROVIDERS = {"btmc": BTMCGoldSource, "pnj": PNJGoldSource}
_WORLD_PROVIDERS = {"currency_api": CurrencyApiGoldSource, "gold_api": GoldApiSource}


def vn(provider: str = "btmc", *, http_get=None, timeout: float = 25.0) -> GoldSource:
    """VN domestic gold spot source (canonical **VND/lượng**).

    ``provider`` is ``"btmc"`` (Bảo Tín Minh Châu, default) or ``"pnj"``. Use
    ``.get_quotes()`` for current spot quotes. VN domestic sources are spot-only.
    """
    try:
        cls = _VN_PROVIDERS[provider.strip().lower()]
    except KeyError as exc:
        valid = ", ".join(sorted(_VN_PROVIDERS))
        raise ValueError(f"unknown VN gold provider {provider!r}; expected one of: {valid}") from exc
    return cls(http_get=http_get, timeout=timeout)


def world(provider: str = "currency_api", *, http_get=None, timeout: float = 25.0) -> GoldSource:
    """World gold (XAU) source in **USD/oz**.

    ``provider`` is ``"currency_api"`` (CurrencyApi, default — spot + daily history)
    or ``"gold_api"`` (Gold-API, spot only). Use ``.get_quotes()`` for spot; sources
    where ``provides_history`` is True also expose ``.get_history(start, end)``.
    """
    try:
        cls = _WORLD_PROVIDERS[provider.strip().lower()]
    except KeyError as exc:
        valid = ", ".join(sorted(_WORLD_PROVIDERS))
        raise ValueError(
            f"unknown world gold provider {provider!r}; expected one of: {valid}"
        ) from exc
    return cls(http_get=http_get, timeout=timeout)


def source(provider: str = "btmc", *, http_get=None, timeout: float = 25.0) -> GoldSource:
    """Primary gold entry: build any gold source by provider name.

    Gold has both VN domestic (``"btmc"``, ``"pnj"``; VND/lượng) and world XAU
    (``"currency_api"``, ``"gold_api"``; USD/oz) providers — there is no single
    cross-unit default, so the provider is explicit (default ``"btmc"``).
    """
    key = provider.strip().lower()
    if key in _VN_PROVIDERS:
        return vn(key, http_get=http_get, timeout=timeout)
    if key in _WORLD_PROVIDERS:
        return world(key, http_get=http_get, timeout=timeout)
    valid = ", ".join(sorted({*_VN_PROVIDERS, *_WORLD_PROVIDERS}))
    raise ValueError(f"unknown gold provider {provider!r}; expected one of: {valid}")
