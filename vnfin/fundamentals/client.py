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
from numbers import Real

from ..exceptions import AllSourcesFailed, InvalidData, VnfinError
from ..failover import FailoverClient
from ..validation import validate_non_empty_string, validate_positive_int
from .base import AUTO, FundamentalSource, resolve_is_bank
from .cafef import CafeFFundamentalSource
from .models import FinancialReport, Period, StatementType, _coerce_period, _coerce_statement
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
        if not isinstance(report, FinancialReport):
            return f"unexpected report type {type(report).__name__}"

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
