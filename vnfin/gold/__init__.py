"""vnfin.gold — clean-room gold price adapters (Vietnam domestic + world XAU).

Public surface:

* Models — :class:`GoldQuote` (spot buy/sell), :class:`GoldBar` + :class:`GoldHistory`
  (a daily series, for the world-XAU history source).
* Port — :class:`GoldSource` (the small interface every adapter implements).
* VN domestic adapters (spot-only, VND/lượng) — :class:`BTMCGoldSource`, :class:`PNJGoldSource`.
  These are TWO SEPARATE spot adapters (no runtime failover client); a live cross-source
  parity test checks they agree, but at runtime you pick one provider via :func:`vn` /
  :func:`source`.
* World adapters — :class:`GoldApiSource` (spot XAU/USD, no history) and
  :class:`CurrencyApiGoldSource` (daily XAU/USD EOD history + spot).

Currency/unit is always stated explicitly on the result object: VN sources return
``currency="VND"`` / ``unit="VND/luong"`` (price per *lượng*; PNJ raw thousand VND/chỉ is
converted to VND/lượng); world sources return ``currency="USD"`` / ``unit="USD/oz"``
(USD per troy ounce). VN VND/lượng and world USD/oz are different unit families, so gold
has no single cross-unit ``client()`` (see ``docs/units.md``). Every result carries
its source name and ``fetched_at_utc``. All adapters wrap transport failures as
:class:`vnfin.exceptions.SourceUnavailable` and malformed/garbage data as
:class:`vnfin.exceptions.InvalidData`, so they are failover-safe.

Clean-room: endpoints, units and shapes were learned only from the provider's own
servers and the project's research docs — never from vnstock or any derivative.
"""
from __future__ import annotations

from .base import GoldSource
from .currency_api import CurrencyApiGoldSource
from .failover import FailoverGoldClient
from .gold_api import GoldApiSource
from .models import GoldBar, GoldHistory, GoldQuote
from .stooq import StooqGoldSource
from .vn import BTMC_PUBLIC_WIDGET_KEY, BTMCGoldSource, PNJGoldSource

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
    "BTMC_PUBLIC_WIDGET_KEY",
    # world
    "GoldApiSource",
    "CurrencyApiGoldSource",
    "StooqGoldSource",
    # failover (world XAU/USD daily history)
    "FailoverGoldClient",
    "default_world_gold_sources",
    "default_world_gold_client",
    # facade
    "vn",
    "world",
    "source",
]

_VN_PROVIDERS = {"btmc": BTMCGoldSource, "pnj": PNJGoldSource}
_WORLD_PROVIDERS = {"currency_api": CurrencyApiGoldSource, "gold_api": GoldApiSource}


def default_world_gold_sources(*, http_get=None, timeout: float = 25.0) -> list[GoldSource]:
    """Default world-gold (XAU/USD) **daily-history** failover chain.

    The default chain contains only reliable, no-key sources that serve real data
    from server infrastructure: currently just :class:`CurrencyApiGoldSource`
    (CDN-hosted, no key, daily EOD history). ``GoldApiSource`` is spot-only and so
    is intentionally not in the history chain.

    :class:`StooqGoldSource` is **deliberately excluded from the default chain**:
    from server/datacenter IPs Stooq commonly answers with a JavaScript anti-bot
    proof-of-work challenge page instead of CSV (it surfaces as
    :class:`~vnfin.exceptions.SourceUnavailable`), so it is not reliable enough to
    be a default backup. It remains available as an **explicit opt-in** source — add
    it yourself, e.g.::

        from vnfin.gold import (
            default_world_gold_sources, StooqGoldSource, default_world_gold_client,
        )

        sources = default_world_gold_sources() + [StooqGoldSource()]
        client = default_world_gold_client(sources=sources)

    Both emit **USD/oz**, so adding Stooq still satisfies the unit-homogeneity guard.
    See ``docs/sources/gold-adapters.md`` for Stooq's anti-bot caveat.
    """
    return [
        CurrencyApiGoldSource(http_get=http_get, timeout=timeout),
    ]


def default_world_gold_client(
    sources=None, *, http_get=None, timeout: float = 25.0, max_attempts: int = 3
) -> FailoverGoldClient:
    """Build the world-gold daily-history failover client (USD/oz).

    Pass ``sources`` to supply a custom chain (e.g. with injected ``http_get`` stubs
    for testing, or to opt Stooq back in as a backup — see
    :func:`default_world_gold_sources`); otherwise the default
    ``[CurrencyApiGoldSource]`` chain is used. The unit-homogeneity guard enforces a
    single ``USD/oz`` chain.
    """
    if sources is None:
        sources = default_world_gold_sources(http_get=http_get, timeout=timeout)
    return FailoverGoldClient(sources, max_attempts=max_attempts)


def _normalize_provider(provider, valid_names):
    """Issue #80: validate a gold factory selector before dispatch."""
    if not isinstance(provider, str) or not provider.strip():
        raise ValueError(f"gold provider must be a non-empty string, got {provider!r}")
    return provider.strip().lower()


def vn(provider: str = "btmc", *, http_get=None, timeout: float = 25.0) -> GoldSource:
    """VN domestic gold spot source (canonical **VND/lượng**).

    ``provider`` is ``"btmc"`` (Bảo Tín Minh Châu, default) or ``"pnj"``. Use
    ``.get_quotes()`` for current spot quotes. VN domestic sources are spot-only.
    """
    key = _normalize_provider(provider, _VN_PROVIDERS)
    try:
        cls = _VN_PROVIDERS[key]
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
    key = _normalize_provider(provider, _WORLD_PROVIDERS)
    try:
        cls = _WORLD_PROVIDERS[key]
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
    if not isinstance(provider, str) or not provider.strip():
        raise ValueError(f"gold provider must be a non-empty string, got {provider!r}")
    key = provider.strip().lower()
    if key in _VN_PROVIDERS:
        return vn(key, http_get=http_get, timeout=timeout)
    if key in _WORLD_PROVIDERS:
        return world(key, http_get=http_get, timeout=timeout)
    valid = ", ".join(sorted({*_VN_PROVIDERS, *_WORLD_PROVIDERS}))
    raise ValueError(f"unknown gold provider {provider!r}; expected one of: {valid}")
