"""VN equity universe source — clean-room, public SSI iBoard group endpoint.

``SsiIboardUniverseSource`` reads the public SSI iboard-query stock-group endpoint,
which returns the current per-board stock list. It enumerates the investable EQUITY
universe (``stockType == "s"``; covered warrants ``w`` / ETFs ``e`` / funds ``m`` are
dropped — they are simply not equities) with source-backed per-symbol reference
metadata and honest coverage diagnostics.

    GET https://iboard-query.ssi.com.vn/stock/group/{BOARD_TOKEN}

The board token is NON-OBVIOUS: plain ``HOSE``/``HNX``/``UPCOM`` return empty; the
full-board lists are addressed by their index-group token (``VNINDEX`` / ``HnxIndex`` /
``HNXUpcomIndex``). See ``docs/sources/equities-universe.md`` for provenance, the
~96%-of-SSC-roster coverage caveat, and the SSI iBoard runtime-fetch / no-redistribution
terms. This source is index-basket-derived and exposes ``universe()`` only; per-symbol
``profile()`` is deferred (to get one symbol, call ``universe(exchange=...)`` and filter).

This mirrors ``vnfin.indices.sources.IndexConstituentsSource`` (envelope guard,
canonicalize/dedup, fail-closed metadata) but uses instance-method field helpers that
reference ``self.name`` so error labels are correct by construction
(``ssi_iboard_universe``, never the index source's ``ssi_iboard_query``).
"""
from __future__ import annotations

from datetime import datetime, timezone

from .._contracts import canonical_security_symbol, reject_duplicate, require_present
from ..coerce import parse_provider_float
from ..exceptions import EmptyData, InvalidData, SourceError
from ..transport import DEFAULT_UA, HttpDataSource
from .models import EquitySecurity, EquityUniverse

# Canonical board name -> SSI iboard-query group token. NON-OBVIOUS: plain
# HOSE/HNX/UPCOM return empty; the full-board stock list is addressed by the
# board's index-group token (case-sensitive).
_BOARD_TOKENS = {
    "HOSE": "VNINDEX",
    "HNX": "HnxIndex",
    "UPCOM": "HNXUpcomIndex",
}

# Board fetch order for an ``exchange=None`` merge (keep-first dedup order).
_MERGE_ORDER = ("HOSE", "HNX", "UPCOM")


class SsiIboardUniverseSource(HttpDataSource):
    """Current per-board equity universe from the public SSI iBoard group endpoint."""

    NAME = "ssi_iboard_universe"
    BASE_URL = "https://iboard-query.ssi.com.vn"
    GROUP_PATH = "/stock/group"

    @property
    def name(self) -> str:
        return self.NAME

    def normalize_board(self, board: str) -> str:
        """Normalize + validate a board selector, returning the canonical board name.

        Rejects unknown boards BEFORE any network call (mirrors how the lib rejects
        bad input pre-network).
        """
        if not isinstance(board, str):
            raise InvalidData(
                f"{self.name}: board must be a string, got {type(board).__name__}"
            )
        canon = board.strip().upper()
        if canon not in _BOARD_TOKENS:
            raise InvalidData(
                f"{self.name}: unknown board {board!r} "
                f"(expected one of {', '.join(_BOARD_TOKENS)})"
            )
        return canon

    def universe(self, exchange=None) -> EquityUniverse:
        """Enumerate the investable equity universe.

        ``exchange=None`` merges all three boards (HOSE, HNX, UPCOM) with cross-board
        keep-first dedup; a board name returns just that board.
        """
        if exchange is None:
            return self._merged_universe()
        board = self.normalize_board(exchange)
        return self._fetch_board(board)

    # ----------------------------- single board ----------------------------- #

    def _fetch_board(self, board: str) -> EquityUniverse:
        token = _BOARD_TOKENS[board]
        url = f"{self.BASE_URL}{self.GROUP_PATH}/{token}"
        headers = {"User-Agent": DEFAULT_UA, "Accept": "application/json"}

        parsed = self._request_json(url, params=None, headers=headers)

        if not isinstance(parsed, dict):
            raise InvalidData(f"{self.name}: unexpected response shape")

        code = parsed.get("code")
        if code != "SUCCESS":
            raise InvalidData(f"{self.name}: code={code}")

        data = parsed.get("data")
        if not isinstance(data, list):
            raise InvalidData(f"{self.name}: 'data' is not a list")
        if not data:
            raise EmptyData(f"{self.name}: no equities for board {board}")

        securities: list[EquitySecurity] = []
        seen: set[str] = set()
        for i, row in enumerate(data):
            if not isinstance(row, dict):
                raise InvalidData(f"{self.name}: row {i} is not an object")
            # Equities only — drop warrants 'w' / ETFs 'e' / funds 'm'. Failing the
            # filter is NOT an error: they are simply not equities, silently skipped.
            if row.get("stockType") != "s":
                continue
            sym = canonical_security_symbol(
                require_present(row, "stockSymbol", f"{self.name} row {i} stockSymbol"),
                f"{self.name} row {i} stockSymbol",
            )
            reject_duplicate(sym, seen, f"{self.name} row {i} symbol")
            exchange = self._optional_str(row, "exchange", i, "exchange")
            securities.append(
                EquitySecurity(
                    symbol=sym,
                    exchange=exchange.upper() if exchange else None,
                    company_name_en=self._optional_str(row, "companyNameEn", i, "companyNameEn"),
                    company_name_vi=self._optional_str(row, "companyNameVi", i, "companyNameVi"),
                    isin=self._optional_str(row, "isin", i, "isin"),
                    listing_status=self._optional_str(row, "adminStatus", i, "adminStatus"),
                    par_value=self._optional_par_value(row, i),
                    currency=self._optional_str(
                        row, "tradingCurrencyISOCode", i, "tradingCurrencyISOCode"
                    ),
                )
            )

        if not securities:
            raise EmptyData(f"{self.name}: no equities for board {board}")

        return EquityUniverse(
            board=board,
            source=self.name,
            securities=tuple(securities),
            fetched_at_utc=datetime.now(timezone.utc),
            as_of=None,
            warnings=self._board_warnings(board),
        )

    # ------------------------------- merge ---------------------------------- #

    def _merged_universe(self) -> EquityUniverse:
        merged: list[EquitySecurity] = []
        seen: dict[str, str] = {}  # symbol -> board it was kept from
        warnings: list[str] = []
        dup_notes: list[str] = []
        last_error: SourceError | None = None  # for the all-boards-down re-raise
        for board in _MERGE_ORDER:
            # One board down must NOT abort the whole all-boards listing: skip-and-warn on
            # a PARTIAL failure (the other boards still merge), but re-raise on a TOTAL
            # failure (all boards down) so the caller gets the concrete cause, not a
            # near-silent empty universe. A skipped board contributes ONLY this token —
            # its 3 honest-gap tokens come from inside a *successful* _fetch_board return.
            try:
                board_universe = self._fetch_board(board)
            except SourceError as exc:
                last_error = exc
                warnings.append(
                    f"board_unavailable: {board} — fetch skipped "
                    f"({type(exc).__name__}): {exc}"
                )
                continue
            for sec in board_universe.securities:
                if sec.symbol in seen:
                    dup_notes.append(
                        f"cross_board_duplicate_symbol: {sec.symbol} kept from "
                        f"{seen[sec.symbol]}, dropped from {board}"
                    )
                    continue
                seen[sec.symbol] = board
                merged.append(sec)
            # preserve every board's honest-gap tokens, attributed by board
            warnings.extend(board_universe.warnings)

        # TOTAL failure: no board contributed any securities AND at least one board raised
        # → re-raise the LAST SourceError (preserves the concrete cause).
        if not merged and last_error is not None:
            raise last_error

        return EquityUniverse(
            board="ALL",
            source=self.name,
            securities=tuple(merged),
            fetched_at_utc=datetime.now(timezone.utc),
            as_of=None,
            warnings=tuple(warnings) + tuple(dup_notes),
        )

    # ------------------------- honest-gap warnings -------------------------- #

    @staticmethod
    def _board_warnings(board: str) -> tuple[str, ...]:
        """The 3 honest-gap tokens — ALWAYS present, never silent (token prefix STABLE)."""
        return (
            f"partial_universe_coverage: {board} — index-basket-derived, "
            f"~96% of the full SSC roster (not complete)",
            f"listing_date_not_available: {board} — provider firstTradingDate is '0' (unusable)",
            f"sector_not_available: {board} — sector/industry absent from this payload",
        )

    # --------------------------- field helpers ------------------------------ #
    # Instance methods reference ``self.name`` so error labels are correct by
    # construction (#167 §6 NAME-mislabel fix) — never the index source's NAME.

    def _optional_str(self, row: dict, key: str, i: int, field_name: str) -> str | None:
        if key not in row:
            return None
        raw = row.get(key)
        if raw is None or raw == "":
            return None
        if not isinstance(raw, str):
            raise InvalidData(f"{self.name}: row {i} malformed {field_name}")
        stripped = raw.strip()
        return stripped or None

    def _optional_par_value(self, row: dict, i: int) -> float | None:
        key = "parValue"
        if key not in row:
            return None
        raw = row.get(key)
        if raw is None or raw == "":
            return None
        value = parse_provider_float(raw, label=f"row {i} parValue", source=self.name)
        # provider uses 0 as "not set"; a non-positive par value is not meaningful.
        if value <= 0:
            return None
        return value
