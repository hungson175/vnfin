"""The fundamental-source port (interface) all fundamental adapters implement."""
from __future__ import annotations

from abc import ABC, abstractmethod

from .models import FinancialReport, Period, StatementType

#: ``is_bank`` sentinel meaning "the caller did not declare bank vs corporate —
#: the adapter should auto-detect". Distinct from ``True``/``False`` (explicit
#: overrides that always win). Auto-detection is what makes ``get_financials``
#: usable WITHOUT the caller knowing whether a ticker is a bank.
AUTO = None

#: Small, clean-room heuristic of well-known Vietnamese bank tickers. This is a
#: fast hint ONLY — it is never authoritative and explicit ``is_bank`` always
#: wins. Adapters that can probe the provider (e.g. VNDirect's modelType-filtered
#: statements) treat this list as a starting guess and still verify against the
#: response, so an out-of-date list cannot produce wrong data, only an extra
#: probe. The list was compiled from public exchange listings, not vnstock.
KNOWN_BANK_SYMBOLS: frozenset[str] = frozenset(
    {
        "ABB",
        "ACB",
        "BAB",
        "BID",
        "BVB",
        "CTG",
        "EIB",
        "HDB",
        "KLB",
        "LPB",
        "MBB",
        "MSB",
        "NAB",
        "NVB",
        "OCB",
        "PGB",
        "SGB",
        "SHB",
        "SSB",
        "STB",
        "TCB",
        "TPB",
        "VAB",
        "VBB",
        "VCB",
        "VIB",
        "VPB",
    }
)


def is_known_bank(symbol: str) -> bool:
    """Best-effort guess from the known-bank heuristic (never authoritative)."""
    return isinstance(symbol, str) and symbol.strip().upper() in KNOWN_BANK_SYMBOLS


def resolve_is_bank(symbol: str, is_bank) -> bool:
    """Collapse an ``is_bank`` request into a concrete bank/corporate flag.

    Explicit ``True``/``False`` is returned unchanged (caller override always
    wins). The :data:`AUTO` sentinel (``None``) falls back to the known-bank
    heuristic, defaulting to corporate (``False``) for anything unrecognised.
    Adapters that can probe the provider should prefer their own probe over this
    static guess; this helper is the cheap last resort.
    """
    if is_bank is AUTO:
        return is_known_bank(symbol)
    return bool(is_bank)


class FundamentalSource(ABC):
    """A swappable source of typed fundamental reports.

    Adapters are constructed once and reused. Implementations MUST raise a
    ``vnfin.exceptions.SourceError`` subclass on failure (transport ->
    ``SourceUnavailable``, no rows -> ``EmptyData``, malformed ->
    ``InvalidData``) so the source stays failover-safe.
    """

    name: str = "base"
    #: Unit/currency this source's monetary statement lines are denominated in,
    #: used by the failover unit-homogeneity guard. Statement money is RAW VND,
    #: so adapters serving raw-VND statements declare ``unit = "VND"``. ``None``
    #: means undeclared (treated as compatible with any chain).
    unit: str | None = None

    @abstractmethod
    def get_financials(
        self,
        symbol: str,
        statement: StatementType,
        period: Period,
        *,
        is_bank: bool | None = AUTO,
        limit: int = 8,
    ) -> tuple[FinancialReport, ...]:
        """Fetch one ``FinancialReport`` per available fiscal period, newest first.

        ``is_bank`` accepts ``True``/``False`` (explicit override) or the
        :data:`AUTO` sentinel (``None``, the default) asking the adapter to
        auto-detect bank vs corporate so callers need not know.
        """

    def health(self) -> bool:  # pragma: no cover - default liveness probe
        return True
