"""Object / list / envelope guards and duplicate-key policy (#refactor).

Adapters and result validators repeatedly need to (a) assert a value is an object
or a list before dereferencing it, and (b) reject duplicate canonical keys within
one response. Centralizing these stops the raw ``AttributeError`` / ``ValueError``
leaks and the inconsistent ad-hoc duplicate checks.
"""
from __future__ import annotations

from typing import Any, MutableSet

from .errors import contract_error


def require_object(value: Any, ctx: str) -> dict:
    """Return ``value`` if it is a ``dict``, else raise ``InvalidData``."""
    if not isinstance(value, dict):
        raise contract_error(ctx, f"expected an object, got {type(value).__name__}")
    return value


def require_list(value: Any, ctx: str) -> list:
    """Return ``value`` if it is a ``list``, else raise ``InvalidData``."""
    if not isinstance(value, list):
        raise contract_error(ctx, f"expected a list, got {type(value).__name__}")
    return value


def reject_duplicate(key: Any, seen: MutableSet, ctx: str) -> None:
    """Atomically reject a duplicate ``key``: raise if already in ``seen``, else add it.

    Doing the membership check and the insert in one call keeps every caller's
    duplicate policy identical (no "check here, forget to add there" drift).
    """
    if key in seen:
        raise contract_error(ctx, f"duplicate key {key!r}")
    seen.add(key)
