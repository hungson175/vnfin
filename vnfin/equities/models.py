"""Typed data contracts for the VN equity universe (#167).

The universe enumerates investable equities per board with source-backed per-symbol
reference metadata + honest coverage diagnostics. It is a data primitive only — NOT a
screener/ranker/advisor. Mirrors the shape of ``vnfin.indices.models`` (frozen
dataclasses, ``__len__``/``__iter__``/``.symbols``/``.to_dataframe()``).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


@dataclass(frozen=True)
class EquitySecurity:
    """One investable equity with source-backed reference metadata.

    Every optional field is ``None`` whenever the provider does not publish it for a
    row — it is never fabricated. ``par_value`` is parsed to a number via the shared
    provider-float parser; ``security_type`` is intentionally absent (it is always
    ``"s"`` after the equity filter, so it would be misleading) and ``listing_date``
    is absent because the provider's ``firstTradingDate`` is ``'0'`` for ~all rows
    (surfaced as a ``listing_date_not_available`` warning on the universe instead).
    """

    symbol: str
    exchange: Optional[str] = None
    company_name_en: Optional[str] = None
    company_name_vi: Optional[str] = None
    isin: Optional[str] = None
    listing_status: Optional[str] = None
    par_value: Optional[float] = None
    currency: Optional[str] = None
    # #195 — derived GICS L1 sector (clean-room, inverted from the 10 VNAllShare sector
    # baskets). All four are populated AS A UNIT when the symbol maps to exactly one
    # basket, and are ALL ``None`` when unmapped / HNX / UPCoM / multi-basket overlap —
    # NEVER fabricated. ``sector_scheme`` is ``"GICS"`` and ``sector_source`` is
    # ``"ssi_iboard_query"`` only on the mapped path. Additive (frozen dataclass,
    # appended after ``currency``, all defaulted) so the public-API surface stays
    # non-breaking.
    sector_code: Optional[str] = None
    sector_name: Optional[str] = None
    sector_scheme: Optional[str] = None
    sector_source: Optional[str] = None


@dataclass(frozen=True)
class GicsSector:
    """One GICS L1 sector — a ``(code, name)`` pair (e.g. ``"VNFIN"`` / ``"Financials"``).

    Returned by :func:`vnfin.equities.sectors` (the static 10-sector list). Carries NO
    membership — that is :class:`EquitySector` (a separate basket fetch).
    """

    code: str
    name: str


@dataclass(frozen=True)
class EquitySector:
    """A GICS L1 sector plus its current basket membership.

    Returned by :func:`vnfin.equities.by_sector`. ``members`` is the sorted tuple of
    member symbols of the one VNAllShare sector basket; HOSE-only by nature. ``warnings``
    always carries the ``sector_partial_coverage`` honest-coverage token.
    """

    sector_code: str
    sector_name: str
    sector_scheme: str = "GICS"
    sector_source: str = "ssi_iboard_query"
    members: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class EquityUniverse:
    """The investable equity universe for one board (or ``"ALL"`` for a merge).

    ``warnings`` ALWAYS carries the honest-gap tokens (partial coverage, no listing
    date, no sector) per contributing board; a cross-board duplicate symbol adds a
    ``cross_board_duplicate_symbol`` token (keep-first), never silently dropped.
    """

    board: Optional[str]            # "HOSE"/"HNX"/"UPCOM" or "ALL" for a merge
    source: str
    securities: tuple[EquitySecurity, ...]
    fetched_at_utc: Optional[datetime] = None
    as_of: Optional[datetime] = None
    warnings: tuple[str, ...] = ()

    def __len__(self) -> int:
        return len(self.securities)

    def __iter__(self):
        return iter(self.securities)

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(s.symbol for s in self.securities)

    def to_dataframe(self) -> "pd.DataFrame":
        """Return a pandas DataFrame of securities. Metadata is attached to ``df.attrs``."""
        import pandas as pd

        columns = [
            "symbol",
            "exchange",
            "company_name_en",
            "company_name_vi",
            "isin",
            "listing_status",
            "par_value",
            "currency",
        ]
        rows = [
            {
                "symbol": s.symbol,
                "exchange": s.exchange,
                "company_name_en": s.company_name_en,
                "company_name_vi": s.company_name_vi,
                "isin": s.isin,
                "listing_status": s.listing_status,
                "par_value": s.par_value,
                "currency": s.currency,
            }
            for s in self.securities
        ]
        df = pd.DataFrame(rows, columns=columns)
        df.attrs.update(board=self.board, source=self.source)
        return df
