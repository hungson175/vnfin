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

import enum
import math
import re
from datetime import date, datetime, timezone

import dataclasses

from .._contracts import (
    MISSING,
    canonical_enum_tag,
    canonical_provider_key,
    optional_present,
    reject_duplicate,
    require_object,
    require_present,
)
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
# Live-probe verified (#198): modelType 1 is the BALANCE sheet and 2 is the
# INCOME statement (the prior INCOME:1/BALANCE:2 mapping was inverted).
_CORP_MODEL = {
    StatementType.BALANCE: 1,
    StatementType.INCOME: 2,
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

#: #198(§8, R3): a fiscalDate must be an EXACT unpadded ``YYYY-MM-DD`` string.
#: This is stricter than :func:`validate_iso_date_string` (which ``.strip()``s and
#: accepts ``date`` objects) so a padded string or a ``date`` object fails closed.
_ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


class _Disposition(enum.Enum):
    """#198(§8, R8+R12): the contract bucket a WELL-FORMED statement row falls in.

    The single shared classifier :meth:`VNDirectFundamentalSource._row_disposition`
    returns one of these; the pagination loop treats only ``ELIGIBLE`` as eligible,
    while the builder preserves its exact counter semantics (``SKIP_CODE`` bumps
    both ``skipped_rows`` and ``code_mismatches``; the cadence/model skips bump
    ``skipped_rows`` only). Structural malformed-value guards still raise inside the
    classifier — this enum only labels valid rows.
    """

    ELIGIBLE = "eligible"
    SKIP_CADENCE = "skip_cadence"
    SKIP_MODEL = "skip_model"
    SKIP_CODE = "skip_code"

#: Issue #44: allowed VNDirect ``reportType`` cadence tags (the request-side enum
#: values). A present tag must be one of these (padded/unknown/blank/null/non-string
#: fail closed); a present valid tag different from the requested period is skipped.
_VNDIRECT_REPORT_TAGS = frozenset({"ANNUAL", "QUARTER"})


def _parse_model_type(raw):
    """Issue #121 + #44(B2): ``modelType`` is integer statement-template identity,
    not a lossy coercion target. Accept an ``int`` (excluding ``bool``), an integral
    ``float`` (the provider sends e.g. ``1.0``), or a canonical digit-only string
    (``"1"``, ``"102"``). Reject ``bool``, fractional numbers/strings, ``None``
    (present-null), and non-canonical shapes with :class:`InvalidData`.

    Callers MUST distinguish an absent ``modelType`` key (legacy: no tag) from a
    PRESENT value via ``optional_present`` and only call this for present values —
    a present ``null`` is malformed provider data and fails closed here.
    """
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
        """Auto-detect the exact statement template, then parse under it (#198 §8).

        The template is identified by the EXACT provider ``modelType`` (corporate
        1/2/3, bank 101/102/103), not the ``is_bank`` class. One atomic pagination
        stream has ONE query/model/metadata envelope, and the eligibility model is
        the DETECTED template — never the initial candidate.

        For each candidate (bank-first for a known bank, else corporate-first):

        1. Fetch page 1 under the candidate's model query. ``EmptyData`` -> record
           the miss and try the other candidate (a wrong ``modelType`` filter
           returns zero rows in production).
        2. Validate the candidate page-1 envelope/rows FIRST (``_rows``,
           ``currentPage==1``, ``totalPages>=1``, STATE-1 row-stream) — before
           trusting its tags — then read ``observed = _dominant_model(...)``.
        3. If ``observed`` is tag-less (``None``) or equals the candidate, confirm
           the candidate and paginate seeded by its already-fetched page 1 (no
           re-fetch). If ``observed`` differs (a redirect, allowed ONCE), discard
           the candidate page, fetch a FRESH page 1 under ``observed``'s query,
           re-validate it, require ``_dominant_model(restart) == observed`` exactly
           (tag-less / same-class-wrong-statement / tie / contradiction / a restart
           ``EmptyData`` after the non-empty candidate all raise ``InvalidData``),
           then paginate on FRESH state under ``observed``. No second redirect.

        If every candidate page 1 is empty, re-raise the first ``EmptyData`` so a
        failover chain can fall through to a backup source.
        """
        prefer_bank = is_known_bank(psym)
        order = (True, False) if prefer_bank else (False, True)
        first_miss: EmptyData | None = None
        for candidate in order:
            candidate_model = self.model_type_for(statement, is_bank=candidate)
            try:
                page1 = self._fetch_statement_page(psym, period, candidate_model, limit=limit, page=1)
                # Validate the candidate envelope/rows BEFORE trusting its tags.
                page1_rows = self._validate_page1(
                    page1, psym=psym, period=period, model_type=candidate_model
                )
            except EmptyData as exc:
                if first_miss is None:
                    first_miss = exc
                continue
            observed = self._dominant_model(page1_rows, statement)
            if observed is None or observed == candidate_model:
                rows = self._paginate(
                    psym, statement, period,
                    model_type=candidate_model, limit=limit, page1_envelope=page1,
                )
                return self._build_statement_reports(
                    psym, statement, period, rows, is_bank=candidate, limit=limit
                )
            # --- redirect (allowed once): discard the candidate, restart fresh ---
            try:
                restart = self._fetch_statement_page(psym, period, observed, limit=limit, page=1)
                restart_rows = self._validate_page1(
                    restart, psym=psym, period=period, model_type=observed
                )
            except EmptyData as exc:
                raise InvalidData(
                    f"{self.name}: modelType redirect to {observed} returned an empty "
                    f"page 1 after a non-empty candidate page"
                ) from exc
            if self._dominant_model(restart_rows, statement) != observed:
                raise InvalidData(
                    f"{self.name}: modelType redirect to {observed} not confirmed by the "
                    f"restarted response (a second redirect is not allowed)"
                )
            detected_is_bank = observed >= 100
            rows = self._paginate(
                psym, statement, period,
                model_type=observed, limit=limit, page1_envelope=restart,
            )
            return self._build_statement_reports(
                psym, statement, period, rows, is_bank=detected_is_bank, limit=limit
            )
        raise first_miss  # both templates empty -> failover-safe EmptyData

    def _dominant_model(self, rows, statement):
        """#198(§8, R19): the unique dominant EXACT model in a validated page.

        ``VALID`` = the two models valid for ``statement`` (corporate + bank).
        Strict-parse each PRESENT ``modelType``:

        * any parsed model outside ``VALID`` -> ``InvalidData`` (even a minority
          tag — a foreign/wrong-statement template can never appear in a clean
          stream);
        * no present tags -> ``None`` (tag-less);
        * a tie between the two ``VALID`` models -> ``InvalidData`` (no dominant
          identity);
        * else -> the unique dominant ``VALID`` model.
        """
        valid = {
            self.model_type_for(statement, is_bank=False),
            self.model_type_for(statement, is_bank=True),
        }
        counts: dict[int, int] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            mt_raw = optional_present(row, "modelType")
            if mt_raw is MISSING:
                continue
            model = _parse_model_type(mt_raw)  # strict; malformed -> InvalidData
            if model not in valid:
                raise InvalidData(
                    f"{self.name}: response carries a foreign modelType {model} "
                    f"(valid for {statement.value}: {sorted(valid)})"
                )
            counts[model] = counts.get(model, 0) + 1
        if not counts:
            return None
        ordered = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        if len(ordered) >= 2 and ordered[0][1] == ordered[1][1]:
            raise InvalidData(
                f"{self.name}: modelType tie {counts}; no dominant template identity"
            )
        return ordered[0][0]

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
        model_type = self.model_type_for(statement, is_bank=is_bank)
        rows = self._paginate(psym, statement, period, model_type=model_type, limit=limit)
        return self._build_statement_reports(
            psym, statement, period, rows, is_bank=is_bank, limit=limit
        )

    def _fetch_statement_page(self, psym, period, model_type, *, limit, page):
        """Fetch ONE raw statement page (the parsed envelope) for a model query."""
        q = f"code:{psym}~reportType:{period.value}~modelType:{model_type}"
        params = {
            "q": q,
            "sort": "fiscalDate:desc",
            "size": self._row_budget(limit),
            "page": page,
        }
        return self._fetch_json(self.BASE_URL + self.STATEMENTS_PATH, params)

    @staticmethod
    def _new_stream_state() -> dict:
        """Fresh raw-stream + eligible-boundary state for one atomic pagination run."""
        return {
            "last_fd": None,       # descending-contiguity cursor (raw-stream state)
            "closed": set(),       # dates whose contiguous group has ended (raw-stream)
            "seen_keys": set(),    # (fiscalDate, itemCode) across ALL fetched rows
            "eligible_order": [],  # distinct ELIGIBLE fiscalDates, newest-first (boundary)
            "all_rows": [],        # every fetched raw row, unfiltered -> handed to builder
        }

    def _validate_metadata(self, resp, *, page, cached_total_pages):
        """#198(§8, B6): envelope + raw-int pagination-metadata guards for one page.

        Returns ``(data, current_page, cached_total_pages)``. ``_rows`` raises
        ``EmptyData`` on an empty list (the caller translates it per the B8 seam)
        and ``InvalidData`` on a non-list container. ``currentPage``/``totalPages``
        must be RAW non-bool ints (so ``True``/``1.0``/``"1"`` fail closed); page 1
        caches ``totalPages>=1``; later pages may omit ``totalPages`` but if present
        it must equal the cached value.
        """
        data = self._rows(resp)  # RAISES EmptyData on []; InvalidData on non-list
        current_page = self._require_raw_int(resp, "currentPage")
        if page == 1:
            cached_total_pages = self._require_raw_int(resp, "totalPages")
            if cached_total_pages < 1:
                raise InvalidData(
                    f"{self.name}: page-1 totalPages must be >= 1, got {cached_total_pages}"
                )
        elif isinstance(resp, dict) and "totalPages" in resp:
            if self._require_raw_int(resp, "totalPages") != cached_total_pages:
                raise InvalidData(
                    f"{self.name}: page {page} totalPages != cached {cached_total_pages}"
                )
        if current_page != page:
            raise InvalidData(
                f"{self.name}: currentPage {current_page} != requested page {page}"
            )
        if not (1 <= current_page <= cached_total_pages):
            raise InvalidData(
                f"{self.name}: currentPage {current_page} out of range "
                f"[1, {cached_total_pages}]"
            )
        return data, current_page, cached_total_pages

    def _consume_rows(self, data, *, psym, period, model_type, state):
        """#198(§8, B7+R12): STATE-1 raw-stream validation on EVERY row + the
        STATE-2 eligible-date boundary (which only drives the stop condition).

        STATE 1 runs on every fetched row (object; exact ISO fiscalDate; canonical
        itemCode; strictly-descending contiguous date groups via ``closed``+
        ``last_fd``; no reappearance of a closed date; no duplicate ``(fd,code)``
        across ALL fetched rows) — an offending row raises even when it is
        ``SKIP_*`` ineligible. STATE 2 appends only distinct ``ELIGIBLE`` dates.
        Every row (eligible or not) is appended to ``state['all_rows']`` for the
        builder.
        """
        row_ctx = f"{self.name} statement row"
        for row in data:
            # === STATE 1: raw-stream validation for EVERY row (eligible or not) ===
            row = require_object(row, row_ctx)
            fd = self._require_iso_fiscal_date(row)
            code = self._require_item_code(row)
            if fd != state["last_fd"]:
                if fd in state["closed"]:
                    raise InvalidData(
                        f"{self.name}: fiscalDate {fd} reappeared after its group closed"
                    )
                if state["last_fd"] is not None:
                    if fd >= state["last_fd"]:
                        raise InvalidData(
                            f"{self.name}: fiscalDate stream not strictly descending "
                            f"({fd} after {state['last_fd']})"
                        )
                    state["closed"].add(state["last_fd"])
                state["last_fd"] = fd
            if (fd, code) in state["seen_keys"]:
                raise InvalidData(
                    f"{self.name}: duplicate (fiscalDate={fd}, itemCode={code})"
                )
            state["seen_keys"].add((fd, code))
            state["all_rows"].append(row)
            # === STATE 2: eligible-date boundary ONLY (does not gate validation) ===
            if (
                self._row_disposition(row, psym=psym, period=period, model_type=model_type)
                is _Disposition.ELIGIBLE
            ):
                if fd not in state["eligible_order"]:
                    state["eligible_order"].append(fd)

    def _validate_page1(self, resp, *, psym, period, model_type):
        """Validate an already-fetched page-1 envelope on FRESH state; return its
        validated raw rows (used by AUTO to read the dominant model before deciding
        whether to seed or redirect). Identical validation to :meth:`_paginate`.
        """
        state = self._new_stream_state()
        data, _cp, _tp = self._validate_metadata(resp, page=1, cached_total_pages=None)
        self._consume_rows(data, psym=psym, period=period, model_type=model_type, state=state)
        return state["all_rows"]

    def _paginate(self, psym, statement, period, *, model_type, limit, page1_envelope=None):
        """#198(§8): a bounded, validated multi-page fetch returning ALL raw rows.

        Eligibility is gated on ``model_type`` (the model reports are BUILT under).
        ``page1_envelope`` (R19) is an ALREADY-FETCHED page-1 response used to SEED
        the loop (the candidate/restarted page); it flows through the SAME page-1
        validation as a fetched page (no double-fetch, no un-validated shortcut).
        All state is LOCAL to this call, so a redirect's fresh invocation shares
        NOTHING with the candidate's. Stops at the first row of the ``(limit+1)``-th
        ELIGIBLE date, or when the provider declares exhaustion
        (``currentPage >= totalPages``). Returns every fetched row unfiltered.
        """
        page = 1
        cached_total_pages = None
        state = self._new_stream_state()
        while True:
            if page == 1 and page1_envelope is not None:
                resp = page1_envelope  # SEED: reuse the already-fetched page 1
            else:
                resp = self._fetch_statement_page(psym, period, model_type, limit=limit, page=page)
            # --- B8 empty-page semantics AT THE ACTUAL _rows() seam (R1) ---
            try:
                data, current_page, cached_total_pages = self._validate_metadata(
                    resp, page=page, cached_total_pages=cached_total_pages
                )
            except EmptyData:
                if page == 1:
                    raise  # template miss -> existing AUTO/failover EmptyData
                raise InvalidData(
                    f"{self.name}: empty page {page} after a non-empty page 1"
                )
            self._consume_rows(
                data, psym=psym, period=period, model_type=model_type, state=state
            )
            # --- stop conditions (eligible boundary; builder caps to `limit`) ---
            if len(state["eligible_order"]) > limit:
                break  # (limit+1)-th ELIGIBLE date seen -> newest `limit` complete
            if current_page >= cached_total_pages:
                break  # provider declares exhaustion
            page += 1
        return state["all_rows"]

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
        row_ctx = f"{self.name} statement row"
        for row in rows:
            # Issue #141: a statement row must be an object before any field access.
            row = require_object(row, row_ctx)
            fd = row.get("fiscalDate")
            if not fd:
                raise InvalidData(f"{self.name}: row missing fiscalDate")
            # #198(§8, R15): the SHARED classifier decides the contract bucket, and
            # the builder preserves its EXACT counter semantics — SKIP_CODE bumps
            # BOTH skipped_rows and code_mismatches (so a mixed wrong-`code` response
            # still warns and the all-wrong-`code` wrong-identity diagnostic fires),
            # while SKIP_CADENCE/SKIP_MODEL bump skipped_rows ONLY. Structural
            # malformed-value guards (reportType/modelType) still raise inside the
            # classifier. The classifier's condition ORDER (cadence -> model -> code)
            # and precedence are identical to the prior inline checks.
            disposition = self._row_disposition(
                row, psym=psym, period=period, model_type=model_type
            )
            if disposition is _Disposition.SKIP_CADENCE or disposition is _Disposition.SKIP_MODEL:
                skipped_rows += 1
                continue
            if disposition is _Disposition.SKIP_CODE:
                skipped_rows += 1
                code_mismatches += 1
                continue
            code = self._item_code_str(row.get("itemCode"))
            value = self._num(row.get("numericValue"))
            self._validate_value_unit("VND")
            li = LineItem(
                item_code=code,
                name=item_name(code, model_type=model_type),
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
        # via _paginate -> _rows -> EmptyData at page 1, which is a different path.)
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
        ratio_ctx = f"{self.name} ratio row"
        for row in rows:
            row = require_object(row, ratio_ctx)
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
            # Issue #62 + #26: ratioCode is a public alpha line-item key (EPS, PE,
            # ROE, ...), so it must be a canonical provider key string — numbers
            # (incl. int/float) and non-string/blank/padded/punctuated values are
            # malformed, not whatever str(raw) yields.
            ratio_code = canonical_provider_key(
                require_present(row, "ratioCode", f"{self.name} ratioCode"),
                f"{self.name} ratioCode",
                allow_int=False,
                allow_integral_float=False,
            )
            raw_name = row.get("itemName")
            if raw_name is not None and not isinstance(raw_name, str):
                raise InvalidData(f"{self.name}: ratio row malformed itemName")
            value = self._num(row.get("value"))
            name = (raw_name or ratio_code).strip()
            if rd not in buckets:
                buckets[rd] = []
                seen[rd] = set()
                order.append(rd)
            # Issue #26: a duplicate ratioCode within one reportDate is an
            # ambiguous/conflicting key; reject atomically (as statements reject a
            # duplicate itemCode).
            reject_duplicate(ratio_code, seen[rd], f"{self.name} ratioCode for {rd}")
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
        # #180: mechanical token prefix (fact-first), cause in the tail.
        note = (
            f"skipped_mismatched_report_rows: {skipped} row(s) with "
            f"mismatched reportType/modelType{note_suffix}"
        )
        return [dataclasses.replace(r, warnings=tuple(r.warnings) + (note,)) for r in reports]

    @staticmethod
    def _validate_value_unit(unit) -> None:
        """Reject line-item units that are not allowed in a VND chain."""
        if unit not in _ALLOWED_LINE_UNITS:
            raise InvalidData(f"vndirect: value_unit {unit!r} is not allowed")

    @staticmethod
    def _require_raw_int(obj, key) -> int:
        """#198(§8, R3): ``obj[key]`` must be present and a RAW non-bool ``int``.

        ``True``/``False`` (``bool`` is an ``int`` subclass), any ``float`` (incl.
        ``1.0``), a numeric ``str`` (``"1"``), and an absent key all raise
        ``InvalidData``. Does NOT reuse ``parse_canonical_int`` (which accepts
        numeric strings) — pagination metadata is a strict raw-int contract.
        """
        if not isinstance(obj, dict) or key not in obj:
            raise InvalidData(f"vndirect: missing required int {key!r}")
        value = obj[key]
        if isinstance(value, bool) or not isinstance(value, int):
            raise InvalidData(
                f"vndirect: {key} must be a raw non-bool int, got {value!r}"
            )
        return value

    @staticmethod
    def _require_iso_fiscal_date(row) -> str:
        """#198(§8, R3): ``row['fiscalDate']`` must be present and an EXACT unpadded
        ``YYYY-MM-DD`` string that is also a REAL calendar date.

        A ``date`` object, a padded/whitespace string, a malformed calendar
        (``2025-99-99``), and an absent key all raise ``InvalidData``. The returned
        canonical string is the grouping/retention key throughout, so the pagination
        window never mismatches a normalized vs. raw form. Does NOT reuse
        ``validate_iso_date_string`` directly for the shape (it ``.strip()``s and
        accepts ``date`` objects), only for the calendar-validity check after the
        strict unpadded ``fullmatch``.
        """
        if not isinstance(row, dict) or "fiscalDate" not in row:
            raise InvalidData("vndirect: row missing fiscalDate")
        raw = row["fiscalDate"]
        if not isinstance(raw, str) or not _ISO_DATE_RE.fullmatch(raw):
            raise InvalidData(
                f"vndirect: bad date {raw!r}: fiscalDate must be an exact unpadded "
                f"YYYY-MM-DD string"
            )
        try:
            validate_iso_date_string(raw, label="fiscalDate")
        except InvalidData as exc:
            raise InvalidData(f"vndirect: bad date {raw!r}") from exc
        return raw

    @classmethod
    def _require_item_code(cls, row) -> str:
        """#198(§8, R20): ``row['itemCode']`` must be present and canonical via
        DIRECT reuse of :meth:`_item_code_str` -> ``canonical_provider_key`` (NOT
        ``str(int(...))``), so the pagination key is byte-for-byte the builder's key.

        ``True``, a fractional float/``Decimal`` (``11000.9``), a negative, a
        padded/signed/non-canonical string, ``null``, and containers all raise;
        an integral provider float (``11000.0`` -> ``"11000"``) and a canonical
        digit string (``"11000"``/``"0"``) pass. An absent key raises too.
        """
        if not isinstance(row, dict) or "itemCode" not in row:
            raise InvalidData("vndirect: row missing itemCode")
        return cls._item_code_str(row["itemCode"])

    @staticmethod
    def _row_disposition(row, *, psym, period, model_type) -> "_Disposition":
        """#198(§8, R8+R12): the SINGLE shared classifier used by BOTH the
        pagination loop and the builder, so the completeness contract and the skip
        contract cannot drift.

        A PRESENT ``reportType`` tag naming a different cadence -> ``SKIP_CADENCE``;
        a PRESENT ``modelType`` (strict-parsed) ``!= model_type`` -> ``SKIP_MODEL``;
        a PRESENT ``code`` that is non-string / blank / ``!= psym`` -> ``SKIP_CODE``;
        otherwise ``ELIGIBLE`` (absent keys keep the legacy no-signal -> eligible
        behavior). The condition ORDER (cadence -> model -> code) is load-bearing:
        it pins the builder's counter precedence. Structural malformed values
        (padded/unknown reportType, malformed/present-null modelType) still raise
        ``InvalidData`` here (they are data-quality errors, not a skip bucket).
        """
        tag = canonical_enum_tag(
            optional_present(row, "reportType"),
            _VNDIRECT_REPORT_TAGS,
            f"vndirect statement reportType",
            missing_ok=True,
        )
        if tag is not None and tag != period.value:
            return _Disposition.SKIP_CADENCE
        mt_raw = optional_present(row, "modelType")
        row_model = None if mt_raw is MISSING else _parse_model_type(mt_raw)
        if row_model is not None and row_model != model_type:
            return _Disposition.SKIP_MODEL
        if "code" in row:
            raw_code = row["code"]
            if (
                not isinstance(raw_code, str)
                or not raw_code.strip()
                or raw_code.strip().upper() != psym
            ):
                return _Disposition.SKIP_CODE
        return _Disposition.ELIGIBLE

    @staticmethod
    def _item_code_str(raw) -> str:
        # Issue #26: itemCode is a public line-item key (FinancialReport.get(),
        # joins, dedup), so it must be a canonical provider key — not whatever
        # str(raw) produces. VNDirect sends an integral float (e.g. 11000.0) which
        # canonicalizes to "11000"; bool/container/None/fractional/non-canonical
        # strings fail closed.
        return canonical_provider_key(raw, "vndirect itemCode")

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
