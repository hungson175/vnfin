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

import math
import re
from datetime import date, datetime, timezone

import dataclasses

from ..exceptions import EmptyData, InvalidData, VnfinError
from ..transport import DEFAULT_UA, HttpDataSource
from ..validation import validate_iso_date_string
from .base import AUTO, FundamentalSource, is_known_bank, resolve_is_bank
from .itemcodes import item_name
from .models import (
    FinancialReport,
    LineItem,
    Period,
    StatementType,
    _coerce_period,
    _coerce_statement,
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

#: Allowed per-line units emitted by this source. Statement money is VND;
#: ratios are dimensionless or per-share VND. Anything else is a contract
#: violation and raises InvalidData (see issue #70).
_ALLOWED_LINE_UNITS = frozenset({"VND", "vnd_per_share", "ratio", None})

_CANONICAL_INT_STR = re.compile(r"[1-9]\d*|0")


def _parse_model_type(raw):
    """Issue #121: ``modelType`` is integer statement-template identity, not a lossy
    coercion target. Accept an ``int`` (excluding ``bool``), an integral ``float``
    (the provider sends e.g. ``1.0``), or a canonical digit-only string (``"1"``,
    ``"102"``). Reject ``bool``, fractional numbers/strings, and non-canonical shapes
    with :class:`InvalidData`. ``None`` (absent tag) returns ``None`` so the caller can
    skip the row, preserving the tag-less fallback behavior.
    """
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise InvalidData(f"vndirect: malformed modelType {raw!r}")
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        if raw.is_integer():
            return int(raw)
        raise InvalidData(f"vndirect: malformed modelType {raw!r}")
    if isinstance(raw, str) and _CANONICAL_INT_STR.fullmatch(raw):
        return int(raw)  # exact (no strip): " 1 ", "+1", "01" are non-canonical -> rejected
    raise InvalidData(f"vndirect: malformed modelType {raw!r}")


class VNDirectFundamentalSource(HttpDataSource, FundamentalSource):
    """Fundamental reports from VNDirect api-finfo (statements + ratios)."""

    NAME = "vndirect"
    #: Statement money lines are RAW VND (unscaled) — declared for the failover
    #: unit-homogeneity guard so a same-unit backup (CafeF) can be chained.
    unit = "VND"
    BASE_URL = "https://api-finfo.vndirect.com.vn"
    STATEMENTS_PATH = "/v4/financial_statements"
    RATIOS_PATH = "/v4/ratios"

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

    @staticmethod
    def model_type_for(statement: StatementType, *, is_bank: bool) -> int:
        table = _BANK_MODEL if is_bank else _CORP_MODEL
        return table[statement]

    # ------------------------------------------------------------------ #
    def get_financials(
        self,
        symbol: str,
        statement: StatementType | str,
        period: Period | str,
        *,
        is_bank: bool | None = AUTO,
        limit: int = 8,
    ) -> tuple[FinancialReport, ...]:
        """Fetch typed reports, auto-detecting bank vs corporate when needed.

        ``is_bank`` may be ``True``/``False`` (explicit override, original
        behavior preserved) or :data:`AUTO` (the default ``None``) asking the
        adapter to detect the template itself: it picks a starting guess from
        the known-bank heuristic and, for statements, verifies it against the
        provider's ``modelType``-filtered response — if that template returns no
        rows it transparently re-probes the other template. Callers therefore no
        longer need to know whether a ticker is a bank.

        ``statement`` and ``period`` accept either the enum or its string value,
        matching the top-level :func:`get_financials` convenience API.
        """
        psym = self._validate_symbol(symbol)
        self._validate_limit(limit)
        st = _coerce_statement(statement)
        pd = _coerce_period(period)
        if pd is Period.UNKNOWN and st is not StatementType.RATIOS:
            raise VnfinError(f"vndirect: Period.UNKNOWN is not valid for {st.value} statements")
        # Resolve is_bank once, with strict bool validation (rejects strings).
        resolved = resolve_is_bank(psym, is_bank)
        if st is StatementType.RATIOS:
            # Ratios have no modelType template; ``is_bank`` is only metadata.
            return self._get_ratios(psym, pd, is_bank=resolved, limit=limit)
        if is_bank is AUTO:
            return self._get_statements_auto(psym, st, pd, limit=limit)
        return self._get_statements(
            psym, st, pd, is_bank=resolved, limit=limit
        )

    def _get_statements_auto(self, psym, statement, period, *, limit):
        """Auto-detect bank vs corporate, then parse the matching statements.

        Step 1: pick a starting template from the known-bank heuristic (corporate
        for unrecognised tickers) and fetch with that ``modelType`` filter.

        Step 2: read the dominant ``modelType`` actually present in the response
        rows. The provider tags each row with its real template (corporate
        1/2/3, bank 101/102/103), so the response itself reveals whether the
        ticker is a bank — even if our starting guess was wrong. We re-derive
        ``is_bank`` from that tag and parse the rows under the correct template
        (so line-item names/metadata match).

        Step 3: if the starting template returned NO rows (the provider filtered
        them out because the guess was wrong), re-probe the other template once.
        If both are empty we re-raise the first miss so a failover chain still
        sees an ``EmptyData`` and can fall through to the backup source.
        """
        prefer_bank = is_known_bank(psym)
        order = (True, False) if prefer_bank else (False, True)
        first_miss: EmptyData | None = None
        for candidate in order:
            try:
                rows = self._fetch_statement_rows(psym, statement, period, is_bank=candidate, limit=limit)
            except EmptyData as exc:
                if first_miss is None:
                    first_miss = exc
                continue
            detected = self._detect_is_bank(rows, default=candidate)
            return self._build_statement_reports(
                psym, statement, period, rows, is_bank=detected, limit=limit
            )
        raise first_miss  # both templates empty -> failover-safe EmptyData

    @staticmethod
    def _detect_is_bank(rows, *, default: bool) -> bool:
        """Infer bank vs corporate from the dominant ``modelType`` in the rows.

        VNDirect tags every statement row with its template's ``modelType``
        (corporate 1/2/3, bank 101/102/103). We pick the most common parseable
        tag and classify it (>= 100 -> bank). Rows with no usable tag fall back
        to ``default`` (the template we requested), so a tag-less response keeps
        the original behavior.
        """
        votes = {True: 0, False: 0}
        for row in rows:
            raw = row.get("modelType") if isinstance(row, dict) else None
            mt = _parse_model_type(raw)  # Issue #121: strict; None -> skip, malformed -> raise
            if mt is None:
                continue
            votes[mt >= 100] += 1
        if votes[True] == 0 and votes[False] == 0:
            return default
        return votes[True] > votes[False]

    # ------------------------------------------------------------------ #
    def _fetch_json(self, url, params):
        return self._request_json(url, params=params, headers=self._headers())

    def _rows(self, parsed) -> list:
        if not isinstance(parsed, dict) or "data" not in parsed:
            raise EmptyData(f"{self.name}: no data envelope")
        data = parsed.get("data")
        # Issue #111: validate type BEFORE truthiness. Only an actual empty list is clean
        # no-data; a present non-list container ({}, "", False, 0, "str", {...}) is schema
        # drift and must raise InvalidData regardless of truthiness.
        if not isinstance(data, list):
            raise InvalidData(f"{self.name}: data is not a list")
        if not data:
            raise EmptyData(f"{self.name}: empty data array")
        return data

    # --- statements (LONG/tall numeric-itemCode rows -> pivot per fiscalDate) #
    def _get_statements(self, psym, statement, period, *, is_bank, limit):
        rows = self._fetch_statement_rows(psym, statement, period, is_bank=is_bank, limit=limit)
        return self._build_statement_reports(
            psym, statement, period, rows, is_bank=is_bank, limit=limit
        )

    def _fetch_statement_rows(self, psym, statement, period, *, is_bank, limit):
        """Fetch the raw long/tall statement rows for one template (one network call)."""
        model_type = self.model_type_for(statement, is_bank=is_bank)
        q = f"code:{psym}~reportType:{period.value}~modelType:{model_type}"
        params = {"q": q, "sort": "fiscalDate:desc", "size": self._row_budget(limit)}
        parsed = self._fetch_json(self.BASE_URL + self.STATEMENTS_PATH, params)
        return self._rows(parsed)

    def _build_statement_reports(self, psym, statement, period, rows, *, is_bank, limit):
        """Pivot long/tall rows into one ``FinancialReport`` per fiscalDate.

        ``is_bank`` here drives the line-item name map and report metadata; the
        auto-detect path passes the *detected* flag so names/metadata match the
        provider's actual template regardless of the initial guess.
        """
        model_type = self.model_type_for(statement, is_bank=is_bank)
        # group rows by fiscalDate, preserving first-seen order (API is desc)
        order: list[str] = []
        buckets: dict[str, list[LineItem]] = {}
        skipped_rows = 0
        code_mismatches = 0  # Issue #21: rows dropped for a wrong provider `code`
        for row in rows:
            fd = row.get("fiscalDate")
            if not fd:
                raise InvalidData(f"{self.name}: row missing fiscalDate")
            # Skip rows that contradict the requested contract (wrong reportType
            # or modelType). These are provider-side mislabels, not fatal errors.
            row_report = str(row.get("reportType") or "").strip().upper()
            if row_report and row_report != period.value:
                skipped_rows += 1
                continue
            row_model = _parse_model_type(row.get("modelType"))  # Issue #121: strict
            if row_model is not None and row_model != model_type:
                skipped_rows += 1
                continue
            # Issue #21 (+16:55 add-on): validate provider-exposed identity before
            # stamping the requested symbol. Key-presence is the trigger (not
            # truthiness): a PRESENT code that is null/falsey/non-string/blank or a
            # different symbol must NOT bypass the check (the old `or ""` collapsed
            # all of those to "" and accepted the row). An absent `code` key keeps
            # the legacy no-identity behavior.
            if "code" in row:
                raw_code = row["code"]
                if (
                    not isinstance(raw_code, str)
                    or not raw_code.strip()
                    or raw_code.strip().upper() != psym
                ):
                    skipped_rows += 1
                    code_mismatches += 1
                    continue
            code = self._item_code_str(row.get("itemCode"))
            value = self._num(row.get("numericValue"))
            self._validate_value_unit("VND")
            li = LineItem(
                item_code=code,
                name=item_name(code, is_bank=is_bank),
                value=value,
                value_unit="VND",  # statement money lines are raw, unscaled VND
            )
            if fd not in buckets:
                buckets[fd] = []
                order.append(fd)
            # Duplicate itemCode within the same period is a contract violation.
            if any(existing.item_code == code for existing in buckets[fd]):
                raise InvalidData(f"{self.name}: duplicate itemCode {code} for {fd}")
            buckets[fd].append(li)

        # Issue #21 (reopen): if EVERY row was dropped because its provider `code`
        # contradicts the requested symbol, the response is a wrong-identity payload
        # (provider/cache mixup), not legitimate no-data. Surface it as malformed
        # response identity rather than an empty successful tuple.
        if not buckets and code_mismatches > 0:
            raise InvalidData(
                f"{self.name}: all {code_mismatches} statement rows have a provider code "
                f"!= requested {psym}; refusing to return wrong-identity data"
            )
        # Issue #44 (reopen): a non-empty provider response whose rows are ALL
        # skipped because their reportType/modelType contradicts the requested
        # statement contract is a template/cadence mismatch, not clean no-data.
        # Raise rather than return () so it cannot read as a successful empty.
        # (A mix of valid + skipped rows still returns the valid reports with a
        # skip warning; the auto-probe falls through on an EMPTY provider response
        # via _fetch_statement_rows -> EmptyData, which is a different path.)
        if not buckets and skipped_rows > 0:
            raise InvalidData(
                f"{self.name}: all {skipped_rows} statement rows skipped "
                f"(reportType/modelType mismatch); response does not match the "
                f"requested {statement.value}/{period.value} contract"
            )

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
        reports = self._with_skip_warning(reports, skipped_rows, note_suffix="/code")
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
        skipped_rows = 0
        code_mismatches = 0  # Issue #21: ratio rows dropped for a wrong provider `code`
        for row in rows:
            if not isinstance(row, dict):
                raise InvalidData(
                    f"{self.name}: ratio row is not an object, got {type(row).__name__}"
                )
            rd = row.get("reportDate")
            if not rd:
                raise InvalidData(f"{self.name}: ratio row missing reportDate")
            # Issue #21 (+16:55 add-on): present code (null/falsey/non-string/blank
            # or wrong symbol) must not bypass the identity check; absent key keeps
            # the legacy behavior.
            if "code" in row:
                raw_code = row["code"]
                if (
                    not isinstance(raw_code, str)
                    or not raw_code.strip()
                    or raw_code.strip().upper() != psym
                ):
                    skipped_rows += 1
                    code_mismatches += 1
                    continue
            # Issue #62: ratioCode and itemName must be strings; non-string values
            # leak raw TypeError/AttributeError and must be caught here.
            ratio_code = row.get("ratioCode")
            if not isinstance(ratio_code, str) or not ratio_code.strip():
                raise InvalidData(f"{self.name}: ratio row missing or malformed ratioCode")
            ratio_code = ratio_code.strip()
            raw_name = row.get("itemName")
            if raw_name is not None and not isinstance(raw_name, str):
                raise InvalidData(f"{self.name}: ratio row malformed itemName")
            value = self._num(row.get("value"))
            name = (raw_name or ratio_code).strip()
            if rd not in buckets:
                buckets[rd] = []
                seen[rd] = set()
                order.append(rd)
            # Issue #26 (reopen): a duplicate ratioCode within one reportDate is an
            # ambiguous/conflicting observation key (downstream report.get() would
            # be non-deterministic), not data to silently keep-first. Reject it, as
            # the statement path already rejects a duplicate itemCode.
            if ratio_code in seen[rd]:
                raise InvalidData(
                    f"{self.name}: duplicate ratioCode {ratio_code} for {rd}"
                )
            seen[rd].add(ratio_code)
            # EPS/BV are per-share monetary values; everything else is dimensionless.
            if ratio_code in {"EPS", "BV"}:
                unit = "vnd_per_share"
            else:
                unit = "ratio"
            self._validate_value_unit(unit)
            buckets[rd].append(
                LineItem(
                    item_code=ratio_code,
                    name=name,
                    value=value,
                    value_unit=unit,
                )
            )

        # Issue #21 (reopen): an all-wrong-`code` ratio response is wrong-identity
        # data, not legitimate no-data.
        if not buckets and code_mismatches > 0:
            raise InvalidData(
                f"{self.name}: all {code_mismatches} ratio rows have a provider code "
                f"!= requested {psym}; refusing to return wrong-identity data"
            )

        fetched = datetime.now(timezone.utc)
        reports = [
            FinancialReport(
                symbol=psym,
                statement_type=StatementType.RATIOS,
                # The ratios endpoint has no period filter (rows are keyed by
                # reportDate only), so do NOT echo the caller's requested period
                # — that would falsely label dimensionless ratios as quarterly/
                # annual figures.
                period=Period.UNKNOWN,
                fiscal_date=self._parse_date(rd),
                items=tuple(buckets[rd]),
                source=self.name,
                # ratios are dimensionless / per-share, not monetary VND
                currency=None,
                is_bank=is_bank,
                model_type=None,
                provider_symbol=psym,
                fetched_at_utc=fetched,
            )
            for rd in order
        ]
        reports = self._with_skip_warning(reports, skipped_rows, note_suffix="/code")
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
    def _with_skip_warning(reports: list, skipped: int, *, note_suffix: str = "") -> list:
        """Surface skipped (contract-violating) rows on every returned report."""
        if not skipped:
            return reports
        note = f"skipped {skipped} row(s) with mismatched reportType/modelType{note_suffix}"
        return [dataclasses.replace(r, warnings=tuple(r.warnings) + (note,)) for r in reports]

    @staticmethod
    def _validate_value_unit(unit) -> None:
        """Reject line-item units that are not allowed in a VND chain."""
        if unit not in _ALLOWED_LINE_UNITS:
            raise InvalidData(f"vndirect: value_unit {unit!r} is not allowed")

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
        from ..coerce import parse_provider_float

        return parse_provider_float(raw, label="numericValue", source="vndirect")

    @staticmethod
    def _parse_date(raw) -> date:
        try:
            return validate_iso_date_string(raw, label="date")
        except InvalidData as exc:
            raise InvalidData(f"vndirect: bad date {raw!r}") from exc

    def _headers(self) -> dict:
        return {"User-Agent": DEFAULT_UA}
