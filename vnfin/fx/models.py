"""FX domain typed result.

Point-in-time (daily/current) reference rate. Canonical unit is **VND per 1 unit of the base
currency** (e.g. USD/VND ≈ 26,000). FX is intentionally *not* a ``TimeSeriesResult`` in v0.2 —
it is a single quote, not a series (see ``docs/design/fx-sources.md``).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FXRate:
    base: str          # ISO 4217 base currency, e.g. "USD"
    quote: str         # quote currency; "VND" in v0.2
    rate: float        # VND per 1 unit of `base`
    unit: str          # canonical unit string, e.g. "VND per 1 USD"
    as_of_utc: datetime  # provider timestamp, normalized to UTC (tz-aware)
    source: str        # adapter name, e.g. "open_er_api" / "vietcombank"
    bid: float | None = None   # provider buy quote (VCB Buy), if available
    ask: float | None = None   # provider sell quote (VCB Sell), if available
