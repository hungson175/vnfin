"""vnfin.corp_actions — clean-room corporate-actions adapters (cash dividends, v1).

Public surface:

* Models — :class:`CashDividendEvent` (one cash-dividend announcement),
  :class:`DividendHistory` (a company's ordered events + provenance).
* Port — :class:`CorpActionSource` (the small interface every adapter implements).
* Adapter — :class:`VsdcCashDividendSource` (the VSDC announcement-page scrape).
* Facade — :func:`dividends` (build the VSDC source and return a company's history).

**v1 scope (read carefully):**

* **CASH dividends only.** STOCK / RIGHTS / BONUS are deferred to v2.
* **ex-date is UNAVAILABLE.** The VSDC depository publishes the record date, the pay
  date, and the ratio/cash — but **no ex-date** — so every event's ``ex_date`` is
  ``None`` and carries the ``ex_date_unavailable`` token (the VNDirect finfo
  enrichment leg is held for v2). Never fabricate/derive an ex-date.
* **Scrape source.** The data is scraped from ``https://vsd.vn/vi/ad/{id}`` HTML, which
  is materially more fragile than the library's JSON sources; a recognized cash dividend
  whose amounts cannot be parsed emits the never-silent ``vsdc_parse_degraded`` token
  rather than corrupting/dropping the event, and every result carries
  ``corp_action_source_partial`` (the result is from the VSDC spine alone).

Currency/unit is stated explicitly: cash is **VND per share** (``currency="VND"``).
Clean-room: endpoints/shapes were learned only from the provider's own pages — never
from vnstock or any derivative.
"""
from __future__ import annotations

from typing import Optional

from .base import CorpActionSource
from .models import CashDividendEvent, DividendHistory
from .vsdc import VsdcCashDividendSource

__all__ = [
    "CashDividendEvent",
    "DividendHistory",
    "CorpActionSource",
    "VsdcCashDividendSource",
    "dividends",
]


def dividends(
    symbol: str,
    *,
    start=None,
    end=None,
    http_get=None,
    timeout: float = 25.0,
    **kw,
) -> DividendHistory:
    """Return a company's cash-dividend history from the VSDC depository spine.

    Builds a :class:`VsdcCashDividendSource` and calls it. ``seed_id`` / ``max_fetch``
    (and any other adapter kwarg) pass through via ``**kw``. v1 = CASH only, ``ex_date``
    is always ``None`` (depository publishes none; finfo leg held), data is scraped.
    """
    seed_id = kw.pop("seed_id", None)
    max_fetch = kw.pop("max_fetch", None)
    latest_id = kw.pop("latest_id", None)
    src_kwargs = {}
    if latest_id is not None:
        src_kwargs["latest_id"] = latest_id
    src = VsdcCashDividendSource(http_get=http_get, timeout=timeout, **src_kwargs)
    call_kwargs = {"start": start, "end": end, "seed_id": seed_id}
    if max_fetch is not None:
        call_kwargs["max_fetch"] = max_fetch
    return src.dividends(symbol, **call_kwargs)
