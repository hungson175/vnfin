"""CafeF backup fundamental adapter (no-auth AJAX handlers).

Endpoints (no auth; needs IPv4 + a browser UA — see research doc
docs/research/2026-06-18-vn-fundamental-data-sources.md):

  STATEMENTS (income / balance):
    https://cafef.vn/du-lieu/Ajax/PageNew/FinanceReport.ashx
      ?Type={1=income,2=balance}&Symbol={T}&TotalRow={N}
      &EndDate={anchor}&ReportType={NAM|QUY}&Sort=DESC
    Shape: {"Data":{"Count":<periods avail>,"Value":[
              {"Time":"2025","Year":2025,"Quater":0,"ReportType":"HK",
               "Conten":"Đã kiểm toán ",
               "Value":[{"Code":"DTTBHCCDV","Name":"...","Value":70207688945}, ...]},
              ...]},"Message":null,"Success":true}
    One object per fiscal period (newest first); ``Quater`` 0 = annual, 1..4 =
    quarter. Money values are RAW VND (unscaled), the SAME unit as VNDirect — so
    this source declares ``unit = "VND"`` and can back VNDirect in one failover
    chain. CafeF's summary handlers do NOT serve cash flow (Type=3 returns an
    empty ``Value``), so a CASHFLOW request raises ``EmptyData`` (failover-safe).

  RATIOS (EPS / BV / PE / ROA / ROE ...):
    https://cafef.vn/du-lieu/Ajax/PageNew/GetDataChiSoTaiChinh.ashx
      ?Symbol={T}&TotalRow={N}&EndDate={anchor}&ReportType={NAM|QUY}&Sort=DESC
    Same outer shape; ratio ``Code``s; values are dimensionless / per-share VND,
    NOT monetary VND (currency=None, value_unit="ratio").

Clean-room: endpoint shapes were learned only from CafeF's own server + the
research doc. No vnstock or derivative material was consulted.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timezone

from ..exceptions import EmptyData, InvalidData, VnfinError
from ..transport import DEFAULT_UA, HttpDataSource
from .base import FundamentalSource
from .models import FinancialReport, LineItem, Period, StatementType

# FinanceReport.ashx ``Type`` per statement (income / balance only). CafeF's
# summary handlers do not serve cash flow.
_STATEMENT_TYPE = {
    StatementType.INCOME: 1,
    StatementType.BALANCE: 2,
}

# Quarter -> (month, day) of the Vietnamese fiscal quarter-end.
_QUARTER_END = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}


class CafeFFundamentalSource(HttpDataSource, FundamentalSource):
    """Backup fundamental reports from CafeF AJAX handlers (statements + ratios)."""

    NAME = "cafef"
    #: Statement money lines are RAW VND (unscaled) — same scale/currency as the
    #: VNDirect primary, so the failover unit-homogeneity guard accepts the chain.
    unit = "VND"
    BASE_URL = "https://cafef.vn/du-lieu/Ajax/PageNew"
    FINANCE_REPORT_PATH = "/FinanceReport.ashx"
    RATIOS_PATH = "/GetDataChiSoTaiChinh.ashx"

    def __init__(self, http_get=None, timeout: float = 25.0):
        # http_get(url, params, headers) -> response text. Injectable for tests.
        super().__init__(http_get=http_get, timeout=timeout)

    @property
    def name(self) -> str:
        return self.NAME

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.strip().upper()

    def _validate_symbol(self, symbol) -> str:
        """Reject empty/whitespace-only symbols before touching the network.

        Bad caller input is a usage error, not a recoverable source failure, so
        we raise the public ``VnfinError`` base rather than a ``SourceError``."""
        if not isinstance(symbol, str) or not symbol.strip():
            raise VnfinError("symbol must be a non-empty string")
        return self.normalize_symbol(symbol)

    @staticmethod
    def _validate_limit(limit) -> None:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise VnfinError(f"limit must be a positive integer, got {limit!r}")

    # ------------------------------------------------------------------ #
    def get_financials(
        self,
        symbol: str,
        statement: StatementType,
        period: Period,
        *,
        is_bank: bool = False,
        limit: int = 8,
    ) -> tuple[FinancialReport, ...]:
        psym = self._validate_symbol(symbol)
        self._validate_limit(limit)
        if statement is StatementType.RATIOS:
            return self._get_ratios(psym, period, is_bank=is_bank, limit=limit)
        return self._get_statements(psym, statement, period, is_bank=is_bank, limit=limit)

    # ------------------------------------------------------------------ #
    def _fetch_json(self, url, params):
        return self._request_json(url, params=params, headers=self._headers())

    @staticmethod
    def _report_type(period: Period) -> str:
        return "QUY" if period is Period.QUARTER else "NAM"

    def _periods(self, parsed) -> list:
        """Validate the outer envelope and return the list of period objects.

        Maps the CafeF failure / empty shapes onto failover-safe exceptions:
        ``Data: null`` (unknown symbol) or ``Success: false`` or an empty
        ``Value`` array -> :class:`EmptyData`; structurally wrong types ->
        :class:`InvalidData`.
        """
        if not isinstance(parsed, dict):
            raise InvalidData(f"{self.name}: response is not a JSON object")
        if parsed.get("Success") is False:
            raise EmptyData(f"{self.name}: Success=false ({parsed.get('Message')!r})")
        data = parsed.get("Data")
        if data is None:
            raise EmptyData(f"{self.name}: null Data ({parsed.get('Message')!r})")
        if not isinstance(data, dict):
            raise InvalidData(f"{self.name}: Data is not an object")
        value = data.get("Value")
        if value is None or (isinstance(value, list) and not value):
            raise EmptyData(f"{self.name}: no periods returned")
        if not isinstance(value, list):
            raise InvalidData(f"{self.name}: Data.Value is not a list")
        return value

    # --- statements (income / balance) -------------------------------------- #
    def _get_statements(self, psym, statement, period, *, is_bank, limit):
        rtype = _STATEMENT_TYPE.get(statement)
        if rtype is None:
            # CafeF summary endpoints do not serve cash flow. Treat as a
            # recoverable per-source miss so a failover chain falls through.
            raise EmptyData(f"{self.name}: {statement.value} not served by CafeF summary")
        params = {
            "Type": rtype,
            "Symbol": psym,
            "TotalRow": self._total_row(limit),
            "EndDate": self._end_date_anchor(period),
            "ReportType": self._report_type(period),
            "Sort": "DESC",
        }
        parsed = self._fetch_json(self.BASE_URL + self.FINANCE_REPORT_PATH, params)
        periods = self._periods(parsed)

        fetched = datetime.now(timezone.utc)
        reports = []
        for pobj in periods:
            items = self._line_items(pobj, value_unit="VND")
            reports.append(
                FinancialReport(
                    symbol=psym,
                    statement_type=statement,
                    period=period,
                    fiscal_date=self._fiscal_date(pobj, period),
                    items=items,
                    source=self.name,
                    currency="VND",
                    is_bank=is_bank,
                    model_type=None,
                    provider_symbol=psym,
                    fetched_at_utc=fetched,
                )
            )
        reports.sort(key=lambda r: r.fiscal_date, reverse=True)
        return tuple(reports[:limit])

    # --- ratios (period-agnostic, NOT monetary VND) ------------------------- #
    def _get_ratios(self, psym, period, *, is_bank, limit):
        params = {
            "Symbol": psym,
            "TotalRow": self._total_row(limit),
            "EndDate": self._end_date_anchor(period),
            "ReportType": self._report_type(period),
            "Sort": "DESC",
        }
        parsed = self._fetch_json(self.BASE_URL + self.RATIOS_PATH, params)
        periods = self._periods(parsed)

        fetched = datetime.now(timezone.utc)
        reports = []
        for pobj in periods:
            items = self._line_items(pobj, value_unit="ratio")
            reports.append(
                FinancialReport(
                    symbol=psym,
                    statement_type=StatementType.RATIOS,
                    # CafeF ratios have no real period dimension we can trust the
                    # same way as statements; report Period.UNKNOWN so we never
                    # mislabel dimensionless ratios as the requested cadence
                    # (mirrors the VNDirect ratios contract).
                    period=Period.UNKNOWN,
                    fiscal_date=self._fiscal_date(pobj, period),
                    items=items,
                    source=self.name,
                    # ratios are dimensionless / per-share, not monetary VND
                    currency=None,
                    is_bank=is_bank,
                    model_type=None,
                    provider_symbol=psym,
                    fetched_at_utc=fetched,
                )
            )
        reports.sort(key=lambda r: r.fiscal_date, reverse=True)
        return tuple(reports[:limit])

    # ------------------------------------------------------------------ #
    def _line_items(self, period_obj, *, value_unit) -> tuple[LineItem, ...]:
        if not isinstance(period_obj, dict):
            raise InvalidData(f"{self.name}: period entry is not an object")
        raw_items = period_obj.get("Value")
        if not isinstance(raw_items, list):
            raise InvalidData(f"{self.name}: period 'Value' is not a list")
        items: list[LineItem] = []
        for it in raw_items:
            if not isinstance(it, dict):
                raise InvalidData(f"{self.name}: line item is not an object")
            code = it.get("Code")
            if code is None or str(code).strip() == "":
                raise InvalidData(f"{self.name}: line item missing Code")
            name = (it.get("Name") or str(code)).strip()
            value = self._num(it.get("Value"))
            items.append(
                LineItem(
                    item_code=str(code).strip(),
                    name=name,
                    value=value,
                    value_unit=value_unit,
                )
            )
        return tuple(items)

    def _fiscal_date(self, period_obj, period: Period) -> date:
        """Synthesize a fiscal-date CafeF does not expose directly.

        Annual periods (``Quater`` 0) -> Dec 31 of ``Year``. Quarterly periods
        (``Quater`` 1..4) -> the Vietnamese fiscal quarter-end. CafeF gives us a
        numeric ``Year`` and ``Quater``; we parse them defensively.
        """
        year = self._int(period_obj.get("Year"), field="Year")
        quater = period_obj.get("Quater")
        try:
            q = int(quater)
        except (TypeError, ValueError) as exc:
            raise InvalidData(f"{self.name}: bad Quater {quater!r}") from exc
        if q == 0:
            return date(year, 12, 31)
        if q in _QUARTER_END:
            month, day = _QUARTER_END[q]
            return date(year, month, day)
        raise InvalidData(f"{self.name}: out-of-range Quater {q!r}")

    # ------------------------------------------------------------------ #
    @staticmethod
    def _total_row(limit: int) -> int:
        # One period object per fiscal period -> request a generous cap so
        # ``limit`` distinct periods come back. Bounded to avoid huge pulls.
        return max(10, min(400, limit * 4))

    def _end_date_anchor(self, period: Period) -> str:
        """Newest anchor for the request.

        Annual -> current calendar year. Quarterly -> "Q-YYYY" (e.g. "2-2026").
        EndDate is the NEWEST period to start from; using 'now' returns the
        latest available rows (CafeF clamps to what exists).
        """
        now = datetime.now(timezone.utc)
        if period is Period.QUARTER:
            quarter = (now.month - 1) // 3 + 1
            return f"{quarter}-{now.year}"
        return str(now.year)

    @staticmethod
    def _num(raw) -> float:
        try:
            v = float(raw)
        except (TypeError, ValueError) as exc:
            raise InvalidData(f"cafef: malformed Value {raw!r}") from exc
        if not math.isfinite(v):
            raise InvalidData(f"cafef: non-finite Value {raw!r}")
        return v

    @staticmethod
    def _int(raw, *, field) -> int:
        try:
            return int(raw)
        except (TypeError, ValueError) as exc:
            raise InvalidData(f"cafef: bad {field} {raw!r}") from exc

    def _headers(self) -> dict:
        return {"User-Agent": DEFAULT_UA}
