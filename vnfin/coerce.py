"""Shared coercion helpers for provider JSON scalars."""
from __future__ import annotations

import math

from .exceptions import InvalidData


def parse_provider_float(value, *, label: str, source: str) -> float:
    """Coerce a provider JSON scalar to a finite float.

    Rejects JSON booleans before coercion because ``bool`` is an ``int`` subclass
    and ``float(True) == 1.0`` would otherwise produce plausible financial values.
    """
    if isinstance(value, bool):
        raise InvalidData(f"{source}: malformed number ({label}): bool is not numeric")
    if value is None:
        raise InvalidData(f"{source}: missing numeric value ({label})")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidData(f"{source}: malformed number ({label})") from exc
    if not math.isfinite(out):
        raise InvalidData(f"{source}: non-finite number ({label})")
    return out


def parse_provider_int(value, *, label: str, source: str) -> int:
    """Coerce a provider JSON scalar to an integer timestamp/count.

    Rejects JSON booleans before coercion because ``bool`` is an ``int`` subclass
    and ``int(True) == 1`` would otherwise produce epoch timestamps.
    """
    if isinstance(value, bool):
        raise InvalidData(f"{source}: malformed integer ({label}): bool is not numeric")
    if value is None:
        raise InvalidData(f"{source}: missing integer ({label})")
    try:
        if isinstance(value, float):
            if not math.isfinite(value):
                raise InvalidData(f"{source}: non-finite integer ({label})")
            if value != int(value):
                raise InvalidData(f"{source}: malformed integer ({label})")
        return int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise InvalidData(f"{source}: malformed integer ({label})") from exc
