"""Typed data contracts for the corp-actions domain (issue #163).

v1 serves **CASH dividends** scraped from the VSDC (Vietnam Securities Depository &
Clearing) public announcement pages. The depository publishes the **record date**, the
**pay date**, and the **ratio / cash-per-share**, but **NO ex-date** — so every event's
``ex_date`` is ``None`` in v1 and carries the ``ex_date_unavailable`` warning token. The
VNDirect finfo ex-date-enrichment leg is held for v2; STOCK/RIGHTS/BONUS are v2 as well.

Two shapes:

* :class:`CashDividendEvent` — one cash-dividend announcement (record/pay/ratio/cash).
* :class:`DividendHistory` — a company's ordered cash-dividend events plus provenance.

Units/currency are stated explicitly: cash is **VND per share** (``currency="VND"``),
``ratio_pct`` is a percent of par. ``as_of`` is the provider's own publish time (parsed
from the page's ``Cập nhật ngày …`` stamp) — never fabricated from ``now()``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date as date_type
from datetime import datetime
from typing import Optional

from ..exceptions import InvalidData

#: Per-event token: v1 never has an ex-date (finfo enrichment leg held).
EX_DATE_UNAVAILABLE = "ex_date_unavailable"
#: Per-event token: a recognized cash dividend whose ratio/cash could not be parsed.
VSDC_PARSE_DEGRADED = "vsdc_parse_degraded"
#: Per-result token: a v1 result is the VSDC depository spine ALONE (no ex-date leg).
CORP_ACTION_SOURCE_PARTIAL = "corp_action_source_partial"


def _validate_optional_amount(value, label: str) -> None:
    """Reject a present amount that is bool, non-finite, or <= 0 (mirror GoldQuote)."""
    if value is None:
        return
    if isinstance(value, bool):
        raise InvalidData(f"CashDividendEvent.{label} must be numeric, got bool {value!r}")
    if not isinstance(value, (int, float)):
        raise InvalidData(f"CashDividendEvent.{label} must be numeric, got {value!r}")
    if not math.isfinite(value):
        raise InvalidData(f"CashDividendEvent.{label} must be finite, got {value!r}")
    if value <= 0:
        raise InvalidData(f"CashDividendEvent.{label} must be positive, got {value!r}")


@dataclass(frozen=True)
class CashDividendEvent:
    """A single VSDC cash-dividend announcement.

    ``ex_date`` is ALWAYS ``None`` in v1 (the depository does not publish it and the
    finfo enrichment leg is held), so ``warnings`` always contains
    ``ex_date_unavailable``. A *recognized* cash dividend whose amounts could not be
    parsed keeps ``cash_per_share``/``ratio_pct`` as ``None`` and adds
    ``vsdc_parse_degraded`` (never silently dropped).
    """

    code: str  # ticker, upper-cased, non-empty
    kind: str  # always "CASH" in v1
    cash_per_share: Optional[float]  # VND per share; None if degraded
    ratio_pct: Optional[float]  # percent of par; None if degraded
    ex_date: Optional[date_type]  # ALWAYS None in v1 (finfo leg held)
    record_date: Optional[date_type]
    pay_date: Optional[date_type]
    div_year: Optional[int]
    source: str  # "vsdc"
    as_of: Optional[datetime]  # provider publish time (time-newstcph)
    exchange: Optional[str] = None
    announcement_id: Optional[int] = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.code, str) or not self.code.strip():
            raise InvalidData(f"CashDividendEvent.code must be a non-empty string, got {self.code!r}")
        if self.kind != "CASH":
            raise InvalidData(f"CashDividendEvent.kind must be 'CASH' in v1, got {self.kind!r}")
        _validate_optional_amount(self.cash_per_share, "cash_per_share")
        _validate_optional_amount(self.ratio_pct, "ratio_pct")
        for label, value in (
            ("ex_date", self.ex_date),
            ("record_date", self.record_date),
            ("pay_date", self.pay_date),
        ):
            if value is not None and not isinstance(value, date_type):
                raise InvalidData(
                    f"CashDividendEvent.{label} must be a datetime.date when present, got {value!r}"
                )
            # datetime is a date subclass; reject it explicitly (these are calendar dates).
            if isinstance(value, datetime):
                raise InvalidData(
                    f"CashDividendEvent.{label} must be a date, not a datetime, got {value!r}"
                )
        # The held-ex-date contract: ex_date is None in v1 ⇒ the token must be present.
        if self.ex_date is None and EX_DATE_UNAVAILABLE not in self.warnings:
            raise InvalidData(
                "CashDividendEvent with ex_date=None must carry the "
                f"{EX_DATE_UNAVAILABLE!r} warning token"
            )


@dataclass(frozen=True)
class DividendHistory:
    """A company's ordered cash-dividend events plus provenance metadata.

    ``warnings`` always contains ``corp_action_source_partial`` in v1 — the result is
    served from the VSDC depository spine alone (the ex-date enrichment leg is not
    active). ``as_of`` is the max event publish time (provider-derived, never ``now()``).
    """

    code: str
    source: str  # "vsdc"
    currency: str  # "VND"
    events: tuple[CashDividendEvent, ...]
    fetched_at_utc: Optional[datetime] = None
    as_of: Optional[datetime] = None  # max event as_of, provider-derived
    warnings: tuple[str, ...] = ()  # list-level; ALWAYS contains corp_action_source_partial in v1

    def __iter__(self):
        return iter(self.events)

    def __len__(self):
        return len(self.events)
