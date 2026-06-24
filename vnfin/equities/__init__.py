"""vnfin.equities — the investable VN equity universe (clean-room, SSI iBoard).

One obvious entry: :func:`universe` (a convenience over :class:`SsiIboardUniverseSource`).
It enumerates the investable equities per board with source-backed per-symbol reference
metadata + honest coverage diagnostics — a data primitive only, NOT a screener/ranker/
advisor. :func:`profile` returns one symbol's sector-enriched ``EquitySecurity``;
:func:`sectors` lists the 10 derived GICS L1 sectors; :func:`by_sector` returns one
sector's basket members.

    import vnfin
    from vnfin.equities import universe, profile, sectors, by_sector

    hose = universe("HOSE")          # one board (no sector fetch)
    rich = universe("HOSE", with_sector=True)   # rows enriched with derived GICS sector
    everything = universe()          # merges HOSE + HNX + UPCOM (cross-board keep-first)
    fpt = profile("FPT")             # one symbol, sector-enriched EquitySecurity
    tech = by_sector("Information Technology")  # the basket members (code or name)
    for s in sectors():
        print(s.code, s.name)        # the 10 GICS L1 (code, name) pairs

The board token is non-obvious (plain HOSE/HNX/UPCOM return empty); the source maps each
board to its index-group token. The raw payload carries no sector field, so the GICS
sector is **derived** (clean-room) by inverting the 10 VNAllShare sector baskets — HOSE-
only (~74%); unmapped HOSE + all HNX/UPCoM rows keep all four sector fields ``None``,
never fabricated (the ``sector_partial_coverage`` token discloses the gap). The result's
``warnings`` ALWAYS disclose the known gaps and never fabricate data.
"""
from __future__ import annotations

from ..exceptions import EmptyData, InvalidData
from .models import EquitySecurity, EquitySector, EquityUniverse, GicsSector
from .sectors import _GICS_L1, _SECTOR_SCHEME, _SECTOR_SOURCE, SectorClassifier
from .sources import SsiIboardUniverseSource

__all__ = [
    "EquitySecurity",
    "EquitySector",
    "EquityUniverse",
    "GicsSector",
    "SsiIboardUniverseSource",
    "by_sector",
    "client",
    "profile",
    "sectors",
    "source",
    "universe",
]


def source(http_get=None, timeout: float = 25.0) -> SsiIboardUniverseSource:
    """Primary equities entry: the default :class:`SsiIboardUniverseSource` (SSI iBoard).

    Standard ``<domain>.source(...)`` factory. Call ``.universe(exchange=...)`` on the
    returned object.
    """
    return SsiIboardUniverseSource(http_get=http_get, timeout=timeout)


# ``client`` is an alias of ``source`` so the equities domain matches the shared
# ``<domain>.client(...)`` naming; equities has a single source surface (mirror funds).
client = source


def _classifier(http_get=None, timeout: float = 25.0, _fetch_constituents=None) -> SectorClassifier:
    """Construct the sector classifier (inject ``_fetch_constituents`` in tests)."""
    return SectorClassifier(
        fetch_constituents=_fetch_constituents, http_get=http_get, timeout=timeout
    )


# Honest-coverage disclosure lines. BOTH literal sinks start with the ``sector_partial_
# coverage:`` prefix so the single #180 token covers them; the helpers are named ``_*warning``
# so the #188 forward-scanner (Shape D — scans every RETURN of a ``_*warnings?`` helper)
# discovers the token from each sink directly.
def _sector_coverage_warning(scope: str) -> str:
    return (
        f"sector_partial_coverage: {scope} — GICS sector derived from VNAllShare baskets "
        f"(HOSE-only ~74%); unmapped {scope} rows → null, never fabricated"
    )


def _sector_overlap_warning(symbol: str, codes: tuple[str, ...]) -> str:
    return (
        f"sector_partial_coverage: {symbol} → null — appears in {len(codes)} baskets "
        f"({', '.join(codes)}); no unique GICS L1 sector"
    )


def universe(
    exchange=None,
    *,
    with_sector: bool = False,
    http_get=None,
    timeout: float = 25.0,
    _fetch_constituents=None,
) -> EquityUniverse:
    """One-shot equity-universe enumeration.

    ``exchange=None`` merges all three boards (HOSE, HNX, UPCOM) with cross-board
    keep-first dedup; an ``exchange`` board name returns just that board.

    ``with_sector=False`` (default) is **byte-for-byte** as before — no sector basket is
    fetched and the per-board ``sector_not_available`` token is retained. ``with_sector=
    True`` enriches each :class:`EquitySecurity` with the derived GICS L1 sector (all four
    sector fields set when mapped, all ``None`` as a unit otherwise) and swaps the
    per-board ``sector_not_available`` token for ``sector_partial_coverage`` (plus a named
    overlap line per multi-basket symbol). The inverted map is built once and reused.
    """
    base = source(http_get=http_get, timeout=timeout).universe(exchange)
    if not with_sector:
        return base
    clf = _classifier(http_get=http_get, timeout=timeout, _fetch_constituents=_fetch_constituents)
    return _enrich_universe(base, clf)


def _enrich_universe(base: EquityUniverse, clf: SectorClassifier) -> EquityUniverse:
    """Replace each security with its sector-enriched copy + swap the coverage warnings."""
    import dataclasses

    enriched = tuple(_enrich_security(sec, clf) for sec in base.securities)

    # Swap every per-board ``sector_not_available`` line for a ``sector_partial_coverage``
    # coverage line; preserve all other tokens (partial_universe_coverage, etc.).
    new_warnings: list[str] = []
    for w in base.warnings:
        if w.startswith("sector_not_available:"):
            scope = w.split(":", 1)[1].split("—", 1)[0].strip() or "universe"
            new_warnings.append(_sector_coverage_warning(scope))
        else:
            new_warnings.append(w)
    # One overlap disclosure line per multi-basket symbol (deterministic order).
    for symbol in sorted(clf.overlaps()):
        new_warnings.append(_sector_overlap_warning(symbol, clf.overlaps()[symbol]))

    return dataclasses.replace(base, securities=enriched, warnings=tuple(new_warnings))


def _enrich_security(sec: EquitySecurity, clf: SectorClassifier) -> EquitySecurity:
    import dataclasses

    classified = clf.classify(sec.symbol)
    if classified is None:
        # unmapped / HNX / UPCoM / overlap → all four None as a unit (never fabricated).
        return dataclasses.replace(
            sec, sector_code=None, sector_name=None, sector_scheme=None, sector_source=None
        )
    code, name, scheme, src = classified
    return dataclasses.replace(
        sec, sector_code=code, sector_name=name, sector_scheme=scheme, sector_source=src
    )


def profile(
    symbol,
    *,
    http_get=None,
    timeout: float = 25.0,
    _fetch_constituents=None,
) -> EquitySecurity:
    """Return one symbol's sector-enriched :class:`EquitySecurity` (full row, not a
    fragment) from the merged all-board universe.

    The returned security carries every reference field PLUS the four derived GICS sector
    fields (all ``None`` as a unit when the symbol is unmapped / HNX / UPCoM / overlap).
    A symbol absent from every board raises :class:`~vnfin.exceptions.EmptyData` naming
    the symbol.
    """
    if not isinstance(symbol, str) or not symbol.strip():
        raise InvalidData(f"equities.profile: symbol must be a non-empty string, got {symbol!r}")
    canon = symbol.strip().upper()
    merged = universe(
        http_get=http_get,
        timeout=timeout,
        with_sector=True,
        _fetch_constituents=_fetch_constituents,
    )
    for sec in merged.securities:
        if sec.symbol == canon:
            return sec
    raise EmptyData(
        f"equities.profile: symbol {canon!r} not found in any board (HOSE/HNX/UPCOM)"
    )


def sectors(*, _fetch_constituents=None) -> tuple[GicsSector, ...]:
    """Return the 10 derived GICS L1 sectors as ``GicsSector(code, name)`` pairs, sorted
    by code. **Static** — no basket fetch, no warning token (``_fetch_constituents`` is
    accepted for API symmetry but never called)."""
    return tuple(GicsSector(code=code, name=_GICS_L1[code]) for code in sorted(_GICS_L1))


def _resolve_sector(code_or_name: str) -> str:
    """Resolve a sector code (``"VNFIN"``) or GICS name (``"Financials"``),
    case-insensitive, to the canonical sector code. Unknown → ``InvalidData``."""
    if not isinstance(code_or_name, str) or not code_or_name.strip():
        raise InvalidData(
            f"equities.by_sector: sector must be a non-empty string, got {code_or_name!r}"
        )
    token = code_or_name.strip()
    upper = token.upper()
    if upper in _GICS_L1:
        return upper
    for code, name in _GICS_L1.items():
        if name.lower() == token.lower():
            return code
    raise InvalidData(
        f"equities.by_sector: unknown sector {code_or_name!r} "
        f"(expected a GICS code {sorted(_GICS_L1)} or name)"
    )


def by_sector(
    code_or_name,
    *,
    http_get=None,
    timeout: float = 25.0,
    _fetch_constituents=None,
) -> EquitySector:
    """Return the :class:`EquitySector` for a sector code or GICS name (case-insensitive).

    ``by_sector("VNFIN")`` and ``by_sector("Financials")`` are equivalent. Fetches that
    one VNAllShare sector basket and returns its sorted members; HOSE-only by nature, so
    the result carries the ``sector_partial_coverage`` coverage token. An unknown sector
    raises :class:`~vnfin.exceptions.InvalidData`.
    """
    code = _resolve_sector(code_or_name)
    clf = _classifier(http_get=http_get, timeout=timeout, _fetch_constituents=_fetch_constituents)
    constituents = clf._fetch_constituents(code)
    members = tuple(sorted(m.symbol for m in constituents.members))
    return EquitySector(
        sector_code=code,
        sector_name=_GICS_L1[code],
        sector_scheme=_SECTOR_SCHEME,
        sector_source=_SECTOR_SOURCE,
        members=members,
        warnings=(_sector_coverage_warning(_GICS_L1[code]),),
    )
