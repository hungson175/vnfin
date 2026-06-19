"""Sequential multi-source failover client for fundamental reports.

``FailoverFundamentalClient`` is a thin **specialization** of the
domain-agnostic :class:`vnfin.failover.FailoverClient`, mirroring how
``vnfin.client.FailoverPriceClient`` wraps the same engine for prices. It wires
the fundamentals operation (``source.get_financials``), acceptance (a non-empty
tuple of reports), and the unit guard (``source.unit``) into the generic engine.

The default chain is VNDirect (primary, deep history) -> CafeF (backup, no-auth
AJAX). BOTH sources emit RAW VND statement money, so the unit-homogeneity guard
accepts the chain; a source declaring any other unit (e.g. USD) is rejected at
construction, making a scale/currency mix structurally impossible.
"""
from __future__ import annotations

import math
from datetime import date, datetime
from numbers import Real

from .._contracts import result_type_reason
from ..exceptions import AllSourcesFailed, InvalidData, VnfinError
from ..failover import FailoverClient, _fetched_at_utc_reason, _warnings_reason
from ..validation import validate_non_empty_string, validate_positive_int
from .base import AUTO, FundamentalSource, resolve_is_bank
from .cafef import CafeFFundamentalSource
from .models import FinancialReport, LineItem, Period, StatementType, _coerce_period, _coerce_statement
from .vndirect import VNDirectFundamentalSource

# Default fundamentals failover chain: primary first, backup second.
_DEFAULT_SOURCE_CLASSES = (VNDirectFundamentalSource, CafeFFundamentalSource)


def default_fundamental_sources(http_get=None, timeout: float = 25.0):
    """Instantiate the default fundamentals failover chain (all RAW VND).

    Order: :class:`VNDirectFundamentalSource` (primary) ->
    :class:`CafeFFundamentalSource` (backup). Both declare ``unit = "VND"``.
    """
    return [c(http_get=http_get, timeout=timeout) for c in _DEFAULT_SOURCE_CLASSES]


def _fundamental_unit(source):
    """Declared monetary unit of a fundamental source (``"VND"`` / ``None``)."""
    return getattr(source, "unit", None)


def _fundamental_provenance(reports) -> frozenset:
    """Total/safe provenance extractor for the report-tuple composite result (#126).

    Returns the ``frozenset`` of stamped report sources for the engine's
    provenance guard. A non-string source (including an unhashable ``list`` /
    ``set``) is mapped to a hashable ``tuple`` sentinel so building the
    ``frozenset`` cannot raise a raw ``TypeError``. The sentinel is deliberately a
    ``tuple`` — never a ``str`` — so it can **never** collide with a (string)
    producing ``source.name``; the guard therefore always rejects a malformed
    report source cleanly instead of leaking the exception or, worse, accepting
    it on a string-marker collision.
    """
    names = set()
    for r in reports:
        src = getattr(r, "source", None)
        if isinstance(src, str):
            names.add(src)
        else:
            names.add(("__invalid_non_string_source__", type(src).__name__))
    return frozenset(names)


class FailoverFundamentalClient:
    """Try fundamental sources in priority order, up to ``max_attempts`` calls.

    A result is accepted only if it is a non-empty tuple of reports; otherwise
    the client records the reason and falls through to the next source. All
    configured sources must emit the same unit/currency (see
    :class:`vnfin.failover.FailoverClient` unit guard).
    """

    def __init__(self, sources, max_attempts: int = 3):
        sources = list(sources)  # materialize once; unit guard + engine both need the list
        self._chain_unit = _fundamental_unit(next((s for s in sources if _fundamental_unit(s) is not None), None))
        self._engine = FailoverClient(
            sources,
            operation=lambda src, symbol, statement, period, is_bank, limit: src.get_financials(
                symbol, statement, period, is_bank=is_bank, limit=limit
            ),
            reject=self._reject_reason,
            unit_of=_fundamental_unit,
            # Issue #126: a composite result is a tuple of reports; provenance is
            # the set of stamped report sources, all of which must match the
            # producing source. The extractor is total/safe — a non-string (e.g.
            # unhashable list) report source is mapped to a hashable marker so the
            # frozenset never raises a raw TypeError and the guard rejects cleanly.
            provenance_of=_fundamental_provenance,
            max_attempts=max_attempts,
            failure_factory=lambda attempts, symbol, statement, period, is_bank, limit: AllSourcesFailed(
                symbol, getattr(statement, "value", statement), attempts
            ),
        )

    @property
    def sources(self):
        return self._engine.sources

    @property
    def max_attempts(self) -> int:
        return self._engine.max_attempts

    @property
    def unit(self):
        return self._engine.unit

    def get_financials(
        self,
        symbol: str,
        statement: StatementType | str,
        period: Period | str,
        *,
        is_bank: bool | None = AUTO,
        limit: int = 8,
    ) -> tuple[FinancialReport, ...]:
        """Fail over across sources; ``is_bank`` defaults to :data:`AUTO`.

        The bank/corporate flag (explicit ``True``/``False`` or the AUTO sentinel
        asking each source to detect it) is forwarded unchanged to every source
        in the chain, so callers need not know whether a ticker is a bank.

        ``statement`` and ``period`` accept either the enum or its string value,
        matching the top-level :func:`get_financials` convenience API.
        """
        # Issue #79: validate caller inputs before any source call.
        symbol = validate_non_empty_string(symbol, "symbol")
        st = _coerce_statement(statement)
        pd = _coerce_period(period)
        # AUTO (None) is forwarded to sources for auto-detection; only explicit
        # booleans are accepted from callers.
        if is_bank is not AUTO and not isinstance(is_bank, bool):
            raise VnfinError(
                f"is_bank must be True, False, or AUTO (None), got {is_bank!r}"
            )
        validate_positive_int(limit, "limit")
        return self._engine.run(symbol, st, pd, is_bank, limit)

    def _reject_reason(self, reports, symbol, statement, period, is_bank, limit) -> str | None:
        return _validate_fundamental_result(
            reports,
            symbol=symbol,
            statement=statement,
            period=period,
            is_bank=is_bank,
            chain_unit=self._chain_unit,
        )


# Allowed per-line units for a VND chain. Statement money must be VND; ratios may
# be dimensionless, per-share VND, or VND.
_VND_CHAIN_ALLOWED_LINE_UNITS = frozenset({"VND", "vnd_per_share", "ratio", None})

# Issue #130: canonical VNDirect statement modelType ids — corporate 1/2/3
# (income/balance/cashflow) and bank 101/102/103. CafeF and ratios carry None.
# A returned model_type must be None or one of these; arbitrary ints (-1/0/4/
# 99/104/999) are not real templates and must be rejected.
_CANONICAL_MODEL_TYPES = frozenset({1, 2, 3, 101, 102, 103})


def _validate_fundamental_result(
    reports,
    *,
    symbol: str,
    statement: StatementType,
    period: Period,
    is_bank: bool,
    chain_unit: str | None,
) -> str | None:
    """Return a rejection reason or ``None`` if the reports are acceptable."""
    if not reports:
        return "empty result"

    for report in reports:
        reason = result_type_reason(report, FinancialReport, noun="report")
        if reason:
            return reason

        # Issue #129: fiscal_date must be a plain calendar date (same rule as
        # macro point keys / gold bar dates). ``datetime`` is rejected explicitly
        # because it subclasses ``date`` but carries intraday/tz meaning a fiscal
        # period must not have; str/None/int/list are rejected outright. Checked
        # first so a malformed date is the canonical rejection reason and never
        # leaks through a diagnostic string that interpolates report.fiscal_date.
        fd = report.fiscal_date
        if not isinstance(fd, date) or isinstance(fd, datetime):
            return f"malformed fiscal_date {fd!r}: expected a plain date"

        # Issue #127: reject present-malformed fetched_at_utc metadata (per report).
        reason = _fetched_at_utc_reason(report.fetched_at_utc)
        if reason:
            return reason
        # Issue #128: reject malformed warnings (must be tuple[str, ...]) per report.
        reason = _warnings_reason(report.warnings)
        if reason:
            return reason

        # Issue #81: reject zero-line reports.
        if len(report.items) == 0:
            return f"report {report.fiscal_date} has no line items"

        # Issue #79: identity checks.
        if report.symbol != symbol:
            return (
                f"symbol mismatch: report {report.fiscal_date} has symbol "
                f"{report.symbol!r} != requested {symbol!r}"
            )
        if report.statement_type != statement:
            return (
                f"statement_type mismatch: report {report.fiscal_date} has "
                f"{report.statement_type!r} != requested {statement!r}"
            )
        # Period is only meaningful for non-ratio statements. Ratios are
        # period-agnostic and must report Period.UNKNOWN; statements must match
        # the requested period exactly (UNKNOWN is a regression unless explicitly
        # requested).
        if report.statement_type is StatementType.RATIOS:
            if report.period is not Period.UNKNOWN:
                return (
                    f"period mismatch: ratio report {report.fiscal_date} has period "
                    f"{report.period!r} (expected Period.UNKNOWN)"
                )
        elif report.period != period:
            return (
                f"period mismatch: report {report.fiscal_date} has period "
                f"{report.period!r} != requested {period!r}"
            )
        # Issue #130: returned report metadata must be well-typed regardless of
        # caller AUTO — these fields drive bank/corporate template interpretation,
        # statement joins, display labels, and audit metadata downstream.
        #  - is_bank: a real bool (a truthy string like "False" would misclassify);
        #  - model_type: absent (None) or a canonical non-bool int template id;
        #  - provider_symbol: absent (None) or a non-empty string.
        if not isinstance(report.is_bank, bool):
            return (
                f"malformed is_bank {report.is_bank!r} in report {report.fiscal_date}: "
                "expected a bool"
            )
        mt = report.model_type
        if mt is not None and (
            isinstance(mt, bool)
            or not isinstance(mt, int)
            or mt not in _CANONICAL_MODEL_TYPES
        ):
            return (
                f"malformed model_type {mt!r} in report {report.fiscal_date}: "
                f"expected None or a canonical template id {sorted(_CANONICAL_MODEL_TYPES)}"
            )
        ps = report.provider_symbol
        if ps is not None and (not isinstance(ps, str) or not ps.strip()):
            return (
                f"malformed provider_symbol {ps!r} in report {report.fiscal_date}: "
                "expected None or a non-empty string"
            )

        # Only enforce is_bank identity when the caller supplied an explicit bool.
        if isinstance(is_bank, bool) and report.is_bank != is_bank:
            return (
                f"is_bank mismatch: report {report.fiscal_date} has is_bank "
                f"{report.is_bank!r} != requested {is_bank!r}"
            )

        # Issue #70: VND-chain unit guards.
        if chain_unit is not None and report.currency != chain_unit:
            return (
                f"currency mismatch: report {report.fiscal_date} has currency "
                f"{report.currency!r} != chain unit {chain_unit!r}"
            )
        # Issue #122: a source result is "successful" only if its returned line
        # items are themselves well-formed. A custom/future source can bypass the
        # adapter parsers and hand back NaN/Infinity/bool/str values, blank or
        # non-string item codes, or duplicate-conflicting codes; reject these
        # before the result is accepted so malformed-but-plausible financials
        # never flow downstream as if the source were healthy.
        seen_codes: set[str] = set()
        for item in report.items:
            # Issue #125 (reopen): reject a malformed inner item object before
            # _validate_line_item dereferences .item_code/.value.
            if not isinstance(item, LineItem):
                return (
                    f"malformed line item object {type(item).__name__} in report "
                    f"{report.fiscal_date}"
                )
            reason = _validate_line_item(item, report.fiscal_date)
            if reason is not None:
                return reason
            if item.value_unit not in _VND_CHAIN_ALLOWED_LINE_UNITS:
                return (
                    f"value_unit mismatch: item {item.item_code!r} has value_unit "
                    f"{item.value_unit!r} which is not allowed in a {chain_unit} chain"
                )
            # item_code is a validated non-empty string by this point.
            if item.item_code in seen_codes:
                return (
                    f"duplicate item_code {item.item_code!r} in report "
                    f"{report.fiscal_date}"
                )
            seen_codes.add(item.item_code)
    return None


def _validate_line_item(item, fiscal_date) -> str | None:
    """Return a rejection reason for a malformed returned ``LineItem`` (#122).

    ``item_code`` must be a canonical non-empty string with no surrounding
    whitespace (``FinancialReport.get()`` does exact key matching, so a padded key
    like ``' 11000'`` is a malformed downstream identifier); ``name`` must be a
    string (an empty name is allowed — some provider codes have no human label);
    ``value`` must be a finite real number that is not a ``bool``. ``bool`` is
    rejected explicitly because it is an ``int`` subclass and would otherwise pass
    the numeric check.
    """
    code = item.item_code
    if not isinstance(code, str) or not code.strip() or code != code.strip():
        return (
            f"malformed item_code {code!r} in report {fiscal_date}: "
            "expected a canonical non-empty string with no surrounding whitespace"
        )
    if not isinstance(item.name, str):
        return (
            f"malformed name {item.name!r} for item {code!r} in report "
            f"{fiscal_date}: expected a string"
        )
    value = item.value
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        return (
            f"malformed value {value!r} for item {code!r} in report "
            f"{fiscal_date}: expected a finite number"
        )
    return None


def default_fundamental_client(
    http_get=None, timeout: float = 25.0, max_attempts: int = 3
) -> FailoverFundamentalClient:
    """The default fundamentals client: failover over VNDirect -> CafeF."""
    return FailoverFundamentalClient(
        default_fundamental_sources(http_get=http_get, timeout=timeout),
        max_attempts=max_attempts,
    )
