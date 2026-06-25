"""vnfin.metals — clean-room annual precious-metals (silver + platinum) history (#196).

One obvious entry: :func:`history` (annual USD/oz history for **silver** or **platinum**)
served from the SAME World Bank Commodity Markets "Pink Sheet" annual ``.xlsx`` the
internal gold source parses. ``source()`` exposes the underlying
:class:`~vnfin.metals.sources.WorldBankCmoMetalSource` for symmetry and injected-``http_get``
testing.

    import vnfin
    from datetime import date

    h = vnfin.metals.history("silver", date(2000, 1, 1), date(2025, 12, 31))
    for bar in h:
        print(bar.date, bar.price)   # USD/oz, one Jan-1 point per year
    # h.product == "XAG", h.unit == "USD/oz", h.frequency == "annual"

``metal`` accepts a **name** (``"silver"``/``"platinum"``, case-insensitive) or an
**ISO-4217 product code** (``"XAG"``/``"XPT"``). ``start``/``end`` are ``datetime.date``
bounds (one Jan-1 ``MetalBar`` per year in ``[start.year, end.year]``).

Never-fabricate routing:

* ``history("gold")`` raises :class:`~vnfin.exceptions.InvalidData` routing the caller to
  ``vnfin.gold`` (gold annual history is served there, not here).
* any other unsupported metal (``"palladium"``/``"XPD"``/``"copper"``/…) raises
  :class:`~vnfin.exceptions.InvalidData` naming the metal — BEFORE any network call; a
  metal's column is never relabelled as another's.
"""
from __future__ import annotations

from ..exceptions import InvalidData
from .models import MetalBar, MetalHistory
from .sources import WorldBankCmoMetalSource

__all__ = ["MetalBar", "MetalHistory", "history", "source", "SUPPORTED_METALS"]

#: Canonical lower-case metal names served by this domain.
SUPPORTED_METALS = ("silver", "platinum")

#: Accepted aliases (name or ISO-4217 product code, case-insensitive) -> canonical name.
_CANON = {
    "silver": "silver",
    "xag": "silver",
    "platinum": "platinum",
    "xpt": "platinum",
}

#: Gold codes/names routed to vnfin.gold (NOT served here) — gate ruling 2.
_GOLD_ALIASES = frozenset({"gold", "xau"})


def _canon_metal(metal) -> str:
    """Canonicalize a metal argument to a supported lower-case name, or raise.

    GOLD specifically routes the caller to ``vnfin.gold`` (gold annual history lives
    there, untouched). Any other unknown metal (``palladium``/``XPD``/``copper``/garbage)
    raises :class:`~vnfin.exceptions.InvalidData` naming it + listing
    :data:`SUPPORTED_METALS` — raised BEFORE any network call.
    """
    if not isinstance(metal, str) or not metal.strip():
        raise InvalidData(
            f"metal must be a non-empty string (name or product code), got {metal!r}; "
            f"supported: {', '.join(SUPPORTED_METALS)}"
        )
    key = metal.strip().lower()
    if key in _GOLD_ALIASES:
        raise InvalidData(
            "gold annual history is served via vnfin.gold "
            "(world_reference_history_vnd), not metals.history; "
            f"metals.history supports: {', '.join(SUPPORTED_METALS)}"
        )
    if key not in _CANON:
        raise InvalidData(
            f"metal {metal!r} not supported by metals.history; "
            f"supported: {', '.join(SUPPORTED_METALS)}"
        )
    return _CANON[key]


def history(metal, start, end, *, http_get=None, timeout: float = 25.0) -> MetalHistory:
    """One-shot annual USD/oz history for ``metal`` (``"silver"``/``"platinum"`` or
    ``"XAG"``/``"XPT"``) over the inclusive ``[start.year, end.year]`` span.

    ``start``/``end`` are ``datetime.date`` bounds. Returns a :class:`MetalHistory`.
    Unsupported metals (incl. gold, which routes to ``vnfin.gold``) raise
    :class:`~vnfin.exceptions.InvalidData` BEFORE any network call.
    """
    return WorldBankCmoMetalSource(
        _canon_metal(metal), http_get=http_get, timeout=timeout
    ).get_history(start, end)


def source(metal, *, http_get=None, timeout: float = 25.0) -> WorldBankCmoMetalSource:
    """Construct the underlying :class:`WorldBankCmoMetalSource` for ``metal``.

    Symmetric with ``history`` for explicit/source-level use (e.g. injected ``http_get``).
    Unsupported metals raise :class:`~vnfin.exceptions.InvalidData`.
    """
    return WorldBankCmoMetalSource(
        _canon_metal(metal), http_get=http_get, timeout=timeout
    )
