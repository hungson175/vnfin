"""FX domain: daily/current foreign-exchange reference rates vs VND (no-key).

Canonical unit: **VND per 1 unit of the base currency** (e.g. USD/VND ≈ 26,000). Spot/current
only — no history in v0.2 (see ``docs/design/fx-sources.md``). Standard facade verbs:

    import vnfin
    r  = vnfin.fx.get_rate("USD")          # one-shot FXRate (failover chain)
    c  = vnfin.fx.client()                 # FailoverFXClient (open.er-api -> Vietcombank)
    s  = vnfin.fx.source()                 # OpenErApiFXSource (primary only)

Sources are clean-room, no-key: open.er-api (primary) + Vietcombank XML (failover). Both quote
VND-per-foreign-unit, so the unit-homogeneity guard is satisfied. Data is runtime-fetch only;
open.er-api prohibits redistribution and Vietcombank is "for reference only" — do not bundle.
"""
from __future__ import annotations

from datetime import date

from ..exceptions import InvalidData
from ..macro.indicators import Frequency
from ..validation import validate_date_range
from .base import FXSource, _ISO4217
from .client import (
    FailoverFXClient,
    default_fx_client,
    default_fx_sources,
)
from .history_models import FXHistory, FXPoint
from .history_worldbank import WorldBankFXHistorySource
from .models import FXRate
from .open_er_api import OpenErApiFXSource
from .vietcombank import VietcombankFXSource

__all__ = [
    "FXRate",
    "FXSource",
    "FXHistory",
    "FXPoint",
    "OpenErApiFXSource",
    "VietcombankFXSource",
    "WorldBankFXHistorySource",
    "FailoverFXClient",
    "default_fx_sources",
    "default_fx_client",
    "client",
    "source",
    "get_rate",
    "history",
]


def source(http_get=None, timeout: float = 25.0) -> OpenErApiFXSource:
    """Primary FX entry: :class:`OpenErApiFXSource` (open.er-api, no-key)."""
    return OpenErApiFXSource(http_get=http_get, timeout=timeout)


def client(http_get=None, timeout: float = 25.0, max_attempts: int = 3) -> FailoverFXClient:
    """Standard ``<domain>.client(...)`` — the open.er-api -> Vietcombank failover chain (VND)."""
    return default_fx_client(http_get=http_get, timeout=timeout, max_attempts=max_attempts)


def get_rate(base: str, quote: str = "VND", *, http_get=None, timeout: float = 25.0) -> FXRate:
    """One-shot convenience: current ``base``/``quote`` rate via the failover chain."""
    return client(http_get=http_get, timeout=timeout).get_rate(base, quote)


def _normalize_fx_ccy(code, label: str) -> str:
    """Validate an ISO-4217 alphabetic code (3 letters) and upper-case it.

    Rejects non-string/blank/malformed codes BEFORE any network call (mirrors the
    spot :class:`FXSource._normalize_ccy` contract)."""
    if not isinstance(code, str) or not _ISO4217.fullmatch(code.strip()):
        raise InvalidData(f"fx.history: invalid ISO-4217 {label} currency code {code!r}")
    return code.strip().upper()


def history(
    base: str = "USD",
    quote: str = "VND",
    start: date | None = None,
    end: date | None = None,
    *,
    frequency: Frequency | str = Frequency.ANNUAL,
    http_get=None,
    timeout: float = 25.0,
) -> FXHistory:
    """Historical FX time series (issue #159) — annual ``base``/``quote`` via World Bank.

    v1 serves **annual USD/VND** from World Bank WDI ``PA.NUS.FCRF`` (no key). ``base``
    must be ``USD``, ``quote`` must be ``VND``, and ``frequency`` must be annual; any
    other pair/frequency raises :class:`~vnfin.exceptions.InvalidData` (loud, never a
    silent half-result) — monthly and non-USD cross-quotes are deferred to v2.

    ``start``/``end`` are an inclusive **calendar-year** window (filtered by ``.year``,
    so a mid-year ``start`` never drops that year's Jan-1-stamped annual point). Annual
    points are an annual **period-average** rate stamped on Jan 1. ``None`` bounds mean
    no lower/upper limit. Reversed bounds raise before any call.
    """
    b = _normalize_fx_ccy(base, "base")
    q = _normalize_fx_ccy(quote, "quote")
    # Normalize the frequency deterministically (enum or string), then enforce annual-only.
    try:
        freq = frequency if isinstance(frequency, Frequency) else Frequency(str(frequency).strip().lower())
    except ValueError as exc:
        raise InvalidData(f"fx.history: unknown frequency {frequency!r}") from exc
    if freq is not Frequency.ANNUAL:
        raise InvalidData(
            f"fx.history: only annual frequency is supported in v1, got {freq.value!r}"
        )
    if q != "VND" or b != "USD":
        raise InvalidData(
            f"fx.history: only USD/VND is supported in v1, got {b}/{q}"
        )
    validate_date_range(start, end, allow_none=True, name="fx.history")
    src = WorldBankFXHistorySource(http_get=http_get, timeout=timeout)
    return src.get_history(b, q, start, end)
