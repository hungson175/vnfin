"""Provider field access with explicit absent-vs-present semantics (#refactor).

The recurring malformed-provider-data bug class came from two anti-patterns:

* **truthiness collapse** — ``obj.get(k) or ""`` erases a *present* malformed value
  (``None``/``False``/``[]``/``{}``/``""``) into "absent", which then gets stamped
  as the requested identity/cadence;
* conflating a **missing key** (often legacy-compatible — providers omit fields)
  with a **present-null/blank** value (corrupt data that must fail closed).

These primitives make the distinction explicit. Key presence is tested with
``key in obj`` (NOT truthiness); absence yields the :data:`MISSING` sentinel so a
caller can deliberately allow a missing key while still rejecting present garbage.
"""
from __future__ import annotations

from typing import Any

from .errors import contract_error


class _Missing:
    """Singleton marker for an absent provider field (distinct from a present ``None``)."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return "MISSING"

    def __bool__(self) -> bool:
        return False


#: Sentinel returned by :func:`optional_present` when a key is absent. It is NOT
#: ``None`` (a present ``null`` is a real, usually-malformed value) and is falsey
#: only so ``if value:`` guards read naturally — never use truthiness to decide
#: presence; compare against ``MISSING`` explicitly.
MISSING = _Missing()


def has_present_key(obj: Any, key: str) -> bool:
    """Return True iff ``obj`` is a dict that *contains* ``key`` (present, any value)."""
    return isinstance(obj, dict) and key in obj


def require_present(obj: dict, key: str, ctx: str) -> Any:
    """Return ``obj[key]``; raise ``InvalidData`` if the key is absent.

    The returned value may itself be ``None`` (present null) — shape validation is
    the caller's next step.
    """
    if not has_present_key(obj, key):
        raise contract_error(ctx, f"missing required field {key!r}")
    return obj[key]


def optional_present(obj: Any, key: str) -> Any:
    """Return ``obj[key]`` if present, else :data:`MISSING`.

    Distinguishes a missing key (``MISSING``) from a present ``null`` (``None``),
    so a caller can allow the former while rejecting the latter.
    """
    if isinstance(obj, dict) and key in obj:
        return obj[key]
    return MISSING


def require_non_empty_str(value: Any, ctx: str, *, canonical: bool = True) -> str:
    """Return a non-empty string ``value`` or raise ``InvalidData``.

    With ``canonical=True`` (default) the value must already be free of surrounding
    whitespace (a padded ``" FPT "`` is rejected, not silently stripped) and is
    returned as-is. With ``canonical=False`` the value is stripped and the stripped
    form returned (legacy-lenient).
    """
    if not isinstance(value, str):
        raise contract_error(ctx, f"expected a string, got {type(value).__name__}")
    if canonical:
        if not value or value != value.strip():
            raise contract_error(
                ctx, f"expected a non-empty canonical string, got {value!r}"
            )
        return value
    if not value.strip():
        raise contract_error(ctx, f"expected a non-empty string, got {value!r}")
    return value.strip()


def optional_present_non_empty_str(
    obj: Any, key: str, ctx: str, *, canonical: bool = True
) -> str | None:
    """Validate an optional identity string field.

    A *missing* key returns ``None`` (legacy-compatible). A *present* value
    (including ``null``/blank/non-string) must be a non-empty string, else
    ``InvalidData``. This is the key-presence-not-truthiness fix for fields like
    ``Symbol`` / ``code`` that historically may be omitted but must never be
    stamped from a present-malformed value.
    """
    value = optional_present(obj, key)
    if value is MISSING:
        return None
    return require_non_empty_str(value, ctx, canonical=canonical)
