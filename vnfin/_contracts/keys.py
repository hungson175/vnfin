"""Canonical provider keys and enum tags (#refactor).

Provider line-item keys (``itemCode`` / ``Code`` / ``ratioCode``) and cadence/enum
tags (``reportType`` / ``ReportType``) are public identifiers used by
``FinancialReport.get()``, joins, exports, and duplicate detection — so they must
be canonical, not whatever ``str(raw).strip()`` happens to produce. These helpers
centralize the canonicalization/deny policy that adapters previously duplicated.
"""
from __future__ import annotations

import math
import re
from typing import Any, Iterable

from .errors import contract_error
from .fields import MISSING, require_non_empty_str

#: A canonical non-numeric provider key: starts with a letter, then letters /
#: digits / underscore (e.g. ``EPS``, ``ROE1``, ``GROSS_MARGIN``). This rejects
#: decimals (``11000.5``), punctuation/containers-as-strings (``{}``), and
#: internal whitespace (``A B``) that broad stringification used to let through.
_ALPHA_KEY_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")

#: A canonical security/fund identifier: letter-start then uppercase alphanumerics,
#: no dot/hyphen/slash/punctuation/internal-space and not digit-first (#34/#33/#30/#9).
#: Validated AFTER ``strip().upper()`` so padded/lower public inputs normalize (live
#: Fmarket codes e.g. ``VCBFBCF``/``VFMVF1``/``RVPF24`` and index/security examples
#: ``VN30``/``E1VFVN30``/``FUEVFVND`` all match).
_SECURITY_ID_RE = re.compile(r"[A-Z][A-Z0-9]*")


def canonical_provider_key(
    value: Any,
    ctx: str,
    *,
    allow_int: bool = True,
    allow_integral_float: bool = True,
    allow_alpha: bool = True,
) -> str:
    """Return a canonical non-empty provider key string, or raise ``InvalidData``.

    Accepts (subject to the ``allow_*`` flags):

    * a non-negative ``int`` (never ``bool``) -> its decimal string;
    * a non-negative, integral, finite ``float`` (providers send e.g. ``11000.0``)
      -> integer string; a fractional / non-finite / negative float is rejected;
    * a ``str`` -> only if non-empty, not whitespace-padded, not signed
      (``+``/``-``); a digit string must have no leading zero (``"11000"``,
      ``"0"``); a non-numeric string must match ``[A-Za-z][A-Za-z0-9_]*``
      (``"EPS"``, ``"ROE1"``) — decimals, punctuation, and internal spaces reject.

    ``bool``, negatives, containers, ``None``, and other types raise. This is the
    single answer to "which provider key shapes are canonical".
    """
    if isinstance(value, bool):
        raise contract_error(ctx, f"key must not be a bool, got {value!r}")
    if isinstance(value, int):
        if not allow_int:
            raise contract_error(ctx, f"integer key not allowed, got {value!r}")
        if value < 0:
            raise contract_error(ctx, f"key must not be negative, got {value!r}")
        return str(value)
    if isinstance(value, float):
        if not allow_integral_float:
            raise contract_error(ctx, f"float key not allowed, got {value!r}")
        if not math.isfinite(value) or value != int(value):
            raise contract_error(ctx, f"key must be an integral number, got {value!r}")
        if value < 0:
            raise contract_error(ctx, f"key must not be negative, got {value!r}")
        return str(int(value))
    if isinstance(value, str):
        if not value or value != value.strip():
            raise contract_error(
                ctx, f"key must be a non-empty unpadded string, got {value!r}"
            )
        if value[0] in "+-":
            raise contract_error(ctx, f"key must not be signed, got {value!r}")
        if value.isdigit():
            if len(value) > 1 and value[0] == "0":
                raise contract_error(
                    ctx, f"numeric key must not have leading zeros, got {value!r}"
                )
            return value
        if not allow_alpha:
            raise contract_error(ctx, f"non-numeric key not allowed, got {value!r}")
        if not _ALPHA_KEY_RE.fullmatch(value):
            raise contract_error(
                ctx, f"non-canonical key {value!r}: expected [A-Za-z][A-Za-z0-9_]*"
            )
        return value
    raise contract_error(
        ctx, f"key must be a string or integral number, got {type(value).__name__}"
    )


def _canonical_identifier(value, ctx: str, *, pattern=_SECURITY_ID_RE) -> str:
    """Shared core for security/fund identifiers: ``strip().upper()`` then validate.

    Normalizes first (so padded/lower public input like ``"  vcbf "`` -> ``"VCBF"``
    stays friendly and dedup runs on the normalized form), then requires a non-empty
    string matching ``pattern``. ``None``/containers/bool/number and shapes with
    internal space / punctuation / digit-first fail closed.
    """
    if not isinstance(value, str):
        raise contract_error(
            ctx, f"expected a string identifier, got {type(value).__name__}"
        )
    norm = value.strip().upper()
    if not norm:
        raise contract_error(ctx, f"expected a non-empty identifier, got {value!r}")
    if not pattern.fullmatch(norm):
        raise contract_error(
            ctx, f"non-canonical identifier {value!r}: expected [A-Z][A-Z0-9]*"
        )
    return norm


def canonical_security_symbol(value, ctx: str) -> str:
    """Canonical security ticker (#30/#9): see :func:`_canonical_identifier`."""
    return _canonical_identifier(value, ctx)


def canonical_fund_code(value, ctx: str) -> str:
    """Canonical Fmarket fund code (#33/#34): see :func:`_canonical_identifier`.

    Separate wrapper from :func:`canonical_security_symbol` so the fund-code and
    security-ticker grammars can diverge later without touching call sites.
    """
    return _canonical_identifier(value, ctx)


def canonical_enum_tag(
    value: Any,
    allowed: Iterable[str],
    ctx: str,
    *,
    missing_ok: bool = False,
    normalize=str.upper,
) -> str | None:
    """Return a normalized enum tag from ``allowed``, or raise ``InvalidData``.

    A ``MISSING`` value returns ``None`` when ``missing_ok`` (an absent key may be
    legacy-compatible); a present value must be a non-empty canonical string whose
    normalized form is in ``allowed``. Present malformed/falsey values fail closed
    rather than collapsing to "absent".
    """
    allowed_set = set(allowed)
    if value is MISSING:
        if missing_ok:
            return None
        raise contract_error(ctx, "missing required tag")
    tag = require_non_empty_str(value, ctx, canonical=True)
    if normalize is not None:
        tag = normalize(tag)
    if tag not in allowed_set:
        raise contract_error(
            ctx, f"{value!r} is not one of {sorted(allowed_set)}"
        )
    return tag
