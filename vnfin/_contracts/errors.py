"""Context-rich error construction for the private contract layer (#refactor).

Every contract primitive raises :class:`~vnfin.exceptions.InvalidData` through
:func:`contract_error` so messages share one ``"<ctx>: <detail>"`` shape. ``ctx``
is a short human label naming the provider/field/row being validated (e.g.
``"vndirect statement row"`` or ``"cafef line item Code"``), which makes failover
``SourceAttempt.reason`` strings and logs self-describing without leaking secrets.
"""
from __future__ import annotations

from ..exceptions import InvalidData


def contract_error(ctx: str, detail: str) -> InvalidData:
    """Return an ``InvalidData`` with a standardized ``"<ctx>: <detail>"`` message."""
    return InvalidData(f"{ctx}: {detail}")
