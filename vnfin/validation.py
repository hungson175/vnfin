"""Reusable input-validation helpers used across vnfin clients and adapters.

These are intentionally thin, domain-agnostic guards that raise stable
:class:`~vnfin.exceptions.InvalidData` (or ``VnfinError``) for malformed caller
inputs so no source ever sees a raw ``TypeError`` from deep inside an adapter.

Public API
----------
The following stable, caller-facing validators are exposed under
``vnfin.validation`` and are importable via ``from vnfin.validation import *``:

* :func:`validate_non_empty_string`
* :func:`validate_date_range`
* :func:`validate_positive_int`
* :func:`validate_country_iso3`
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from .exceptions import InvalidData, VnfinError

__all__ = [
    "validate_non_empty_string",
    "validate_date_range",
    "validate_positive_int",
    "validate_country_iso3",
]

_ISO4217 = re.compile(r"[A-Za-z]{3}")


def validate_non_empty_string(value, name: str = "symbol") -> str:
    """Return stripped ``value`` or raise ``InvalidData`` if not a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidData(f"{name} must be a non-empty string, got {value!r}")
    return value.strip()


def validate_iso4217(code, name: str = "currency") -> str:
    """Return uppercased ISO-4217 code or raise ``InvalidData``."""
    if not isinstance(code, str) or not _ISO4217.fullmatch(code.strip()):
        raise InvalidData(f"invalid ISO-4217 {name} currency code {code!r}")
    return code.strip().upper()


def validate_country_iso3(value) -> str:
    """Return uppercased 3-letter ISO3 country code or raise ``InvalidData``."""
    if not isinstance(value, str):
        raise InvalidData(
            f"macro: country must be a 3-letter ISO3 code, got {type(value).__name__}"
        )
    c = value.strip().upper()
    if not (len(c) == 3 and c.isalpha()):
        raise InvalidData(f"macro: country must be a 3-letter ISO3 code, got {value!r}")
    return c


def validate_date_range(
    start,
    end,
    *,
    allow_none: bool = False,
    name: str = "history",
) -> tuple[Optional[date], Optional[date]]:
    """Validate ``start``/``end`` are dates and ``start <= end``.

    When ``allow_none`` is True, missing bounds are permitted and returned as
    ``None``. Otherwise both are required.
    """
    if not allow_none and (start is None or end is None):
        missing = [n for n, v in (("start", start), ("end", end)) if v is None]
        raise InvalidData(
            f"{name} requires both 'start' and 'end' dates; missing: "
            + ", ".join(missing)
        )
    for label, val in (("start", start), ("end", end)):
        if val is None:
            continue
        if not isinstance(val, (date, datetime)):
            raise InvalidData(
                f"{name} '{label}' must be datetime.date or datetime.datetime, got {type(val).__name__}"
            )
    if start is not None and end is not None:
        try:
            reversed_range = start > end
        except TypeError as exc:
            raise InvalidData(
                f"{name} 'start' and 'end' must be comparable (same date/datetime type)"
            ) from exc
        if reversed_range:
            raise InvalidData(
                f"{name} requires start <= end, got start={start} > end={end}"
            )
    return start, end


def validate_positive_int(value, name: str = "limit") -> int:
    """Return ``int(value)`` or raise ``VnfinError`` if not a positive integer.

    ``bool`` is rejected because its truthiness is a common source of bugs.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise VnfinError(f"{name} must be a positive integer, got {value!r}")
    if value <= 0:
        raise VnfinError(f"{name} must be positive, got {value!r}")
    return value


def validate_fraction(value, name: str = "threshold") -> float:
    """Return ``float(value)`` or raise ``ValueError`` if not in ``[0, 1]``.

    ``bool`` is rejected to avoid ``True``/``False`` silently becoming ``1.0``/``0.0``.
    """
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a numeric threshold in [0, 1], got bool")
    if not isinstance(value, (int, float)):
        raise ValueError(
            f"{name} must be a numeric threshold in [0, 1], got {type(value).__name__}"
        )
    threshold = float(value)
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"{name} must be in [0, 1], got {value!r}")
    return threshold
