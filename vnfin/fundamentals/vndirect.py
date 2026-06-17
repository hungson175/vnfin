"""VNDirect api-finfo fundamental adapter.

Endpoints (no auth; needs IPv4 + a browser UA — see research doc
docs/research/2026-06-18-vn-fundamental-data-sources.md):

  STATEMENTS:
    https://api-finfo.vndirect.com.vn/v4/financial_statements
      ?q=code:{T}~reportType:{QUARTER|ANNUAL}~modelType:{N}
      &sort=fiscalDate:desc&size={N}
    Rows are LONG/tall: {code, itemCode(float), reportType, modelType(float),
    numericValue, fiscalDate, ...} — one row per (line-item, period). We pivot
    per fiscalDate into one FinancialReport. Units = RAW VND.
    Corporate IS/BS/CF -> modelType 1/2/3. Banks -> 101/102/103.

  RATIOS:
    https://api-finfo.vndirect.com.vn/v4/ratios?q=code:{T}&size={N}
    Rows: {code, group, reportDate, itemCode(str), ratioCode, itemName, value}
    — one row per (ratioCode, reportDate). We pivot per reportDate.

Clean-room: endpoint shapes were learned only from the provider's own server +
the research doc. No vnstock or derivative material was consulted.
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone

from ..exceptions import EmptyData, InvalidData, SourceUnavailable
from .base import FundamentalSource
from .itemcodes import item_name
from .models import FinancialReport, LineItem, Period, StatementType

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Corporate (single-digit) modelType per statement; bank adds the 10x prefix.
_CORP_MODEL = {
    StatementType.INCOME: 1,
    StatementType.BALANCE: 2,
    StatementType.CASHFLOW: 3,
}
_BANK_MODEL = {
    StatementType.INCOME: 102,
    StatementType.BALANCE: 101,
    StatementType.CASHFLOW: 103,
}


class VNDirectFundamentalSource(FundamentalSource):
    """Fundamental reports from VNDirect api-finfo (statements + ratios)."""

    NAME = "vndirect"
    BASE_URL = "https://api-finfo.vndirect.com.vn"
    STATEMENTS_PATH = "/v4/financial_statements"
    RATIOS_PATH = "/v4/ratios"

    def __init__(self, http_get=None, timeout: float = 25.0):
        # http_get(url, params, headers) -> response text. Injectable for tests.
        self._http_get = http_get or self._default_http_get
        self._timeout = timeout

    @property
    def name(self) -> str:
        return self.NAME

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.strip().upper()

    @staticmethod
    def model_type_for(statement: StatementType, *, is_bank: bool) -> int:
        table = _BANK_MODEL if is_bank else _CORP_MODEL
        return table[statement]

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
        psym = self.normalize_symbol(symbol)
        if statement is StatementType.RATIOS:
            return self._get_ratios(psym, period, is_bank=is_bank, limit=limit)
        return self._get_statements(psym, statement, period, is_bank=is_bank, limit=limit)

    # ------------------------------------------------------------------ #
    def _fetch_json(self, url, params):
        try:
            text = self._http_get(url, params, self._headers())
        except Exception as exc:  # transport-level
            raise SourceUnavailable(f"{self.name} transport error: {exc}") from exc
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError) as exc:
            raise InvalidData(f"{self.name}: non-JSON response") from exc
        return parsed

    def _rows(self, parsed) -> list:
        if not isinstance(parsed, dict) or "data" not in parsed:
            raise EmptyData(f"{self.name}: no data envelope")
        data = parsed.get("data")
        if not data:
            raise EmptyData(f"{self.name}: empty data array")
        if not isinstance(data, list):
            raise InvalidData(f"{self.name}: data is not a list")
        return data

    # --- statements (LONG/tall numeric-itemCode rows -> pivot per fiscalDate) #
    def _get_statements(self, psym, statement, period, *, is_bank, limit):
        model_type = self.model_type_for(statement, is_bank=is_bank)
        q = f"code:{psym}~reportType:{period.value}~modelType:{model_type}"
        params = {"q": q, "sort": "fiscalDate:desc", "size": self._row_budget(limit)}
        parsed = self._fetch_json(self.BASE_URL + self.STATEMENTS_PATH, params)
        rows = self._rows(parsed)

        # group rows by fiscalDate, preserving first-seen order (API is desc)
        order: list[str] = []
        buckets: dict[str, list[LineItem]] = {}
        for row in rows:
            fd = row.get("fiscalDate")
            if not fd:
                raise InvalidData(f"{self.name}: row missing fiscalDate")
            code = self._item_code_str(row.get("itemCode"))
            value = self._num(row.get("numericValue"))
            li = LineItem(
                item_code=code,
                name=item_name(code, is_bank=is_bank),
                value=value,
            )
            if fd not in buckets:
                buckets[fd] = []
                order.append(fd)
            buckets[fd].append(li)

        fetched = datetime.now(timezone.utc)
        reports = [
            FinancialReport(
                symbol=psym,
                statement_type=statement,
                period=period,
                fiscal_date=self._parse_date(fd),
                items=tuple(buckets[fd]),
                source=self.name,
                currency="VND",
                is_bank=is_bank,
                model_type=model_type,
                provider_symbol=psym,
                fetched_at_utc=fetched,
            )
            for fd in order
        ]
        # newest first by fiscal_date (defensive; API already sorts desc)
        reports.sort(key=lambda r: r.fiscal_date, reverse=True)
        return tuple(reports[:limit])

    # --- ratios (ratioCode/reportDate/value rows -> pivot per reportDate) ---- #
    def _get_ratios(self, psym, period, *, is_bank, limit):
        params = {"q": f"code:{psym}", "sort": "reportDate:desc", "size": self._row_budget(limit)}
        parsed = self._fetch_json(self.BASE_URL + self.RATIOS_PATH, params)
        rows = self._rows(parsed)

        order: list[str] = []
        buckets: dict[str, list[LineItem]] = {}
        seen: dict[str, set] = {}
        for row in rows:
            rd = row.get("reportDate")
            if not rd:
                raise InvalidData(f"{self.name}: ratio row missing reportDate")
            ratio_code = row.get("ratioCode")
            if not ratio_code:
                raise InvalidData(f"{self.name}: ratio row missing ratioCode")
            value = self._num(row.get("value"))
            name = (row.get("itemName") or ratio_code).strip()
            if rd not in buckets:
                buckets[rd] = []
                seen[rd] = set()
                order.append(rd)
            if ratio_code in seen[rd]:
                continue  # keep first (newest) occurrence within a date
            seen[rd].add(ratio_code)
            buckets[rd].append(LineItem(item_code=ratio_code, name=name, value=value))

        fetched = datetime.now(timezone.utc)
        reports = [
            FinancialReport(
                symbol=psym,
                statement_type=StatementType.RATIOS,
                period=period,
                fiscal_date=self._parse_date(rd),
                items=tuple(buckets[rd]),
                source=self.name,
                currency="VND",
                is_bank=is_bank,
                model_type=None,
                provider_symbol=psym,
                fetched_at_utc=fetched,
            )
            for rd in order
        ]
        reports.sort(key=lambda r: r.fiscal_date, reverse=True)
        return tuple(reports[:limit])

    # ------------------------------------------------------------------ #
    @staticmethod
    def _row_budget(limit: int) -> int:
        # Statements are tall (many line items per period). Request generously
        # so ``limit`` distinct periods come back. 200 covers headline lines for
        # several periods; callers wanting deep history can subclass/override.
        return max(50, min(1000, limit * 80))

    @staticmethod
    def _item_code_str(raw) -> str:
        if raw is None:
            raise InvalidData("vndirect: row missing itemCode")
        try:
            f = float(raw)
        except (TypeError, ValueError):
            return str(raw)
        # itemCode comes as a float (e.g. 11000.0) -> stable integer string
        if math.isfinite(f) and f == int(f):
            return str(int(f))
        return str(raw)

    @staticmethod
    def _num(raw) -> float:
        try:
            v = float(raw)
        except (TypeError, ValueError) as exc:
            raise InvalidData(f"vndirect: malformed numericValue {raw!r}") from exc
        if not math.isfinite(v):
            raise InvalidData(f"vndirect: non-finite numericValue {raw!r}")
        return v

    @staticmethod
    def _parse_date(raw) -> date:
        try:
            return datetime.strptime(str(raw), "%Y-%m-%d").date()
        except (TypeError, ValueError) as exc:
            raise InvalidData(f"vndirect: bad date {raw!r}") from exc

    def _headers(self) -> dict:
        return {"User-Agent": _UA}

    def _default_http_get(self, url, params, headers):  # pragma: no cover - network
        import httpx

        transport = httpx.HTTPTransport(local_address="0.0.0.0")  # force IPv4
        with httpx.Client(transport=transport, timeout=self._timeout, headers=headers) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.text
