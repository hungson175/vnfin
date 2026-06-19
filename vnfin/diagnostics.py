"""Source-coverage diagnostics for allocation workflows (issue #145).

A small, **additive, offline** API that explains *source coverage* and source-limit
gaps for long-horizon allocation notebooks — so a caller can understand a coverage
gap or single-source leg WITHOUT a large, doomed network fan-out. It is metadata /
preflight only:

* it never performs a network call,
* it never fabricates missing rows, index weights, or bundles provider data,
* it is NOT a live health monitor — for that, use :mod:`vnfin._health` /
  ``scripts/healthcheck.py``.

Public API::

    import vnfin
    from datetime import date

    vnfin.diagnostics.source_capabilities()
    vnfin.diagnostics.explain_world_gold_history(date(2024, 1, 1), date(2024, 1, 7))
    vnfin.diagnostics.explain_index_constituents("VN30")

This first version focuses on the two source-limited legs raised by #145: world-gold
daily history and index constituents.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ._contracts import canonical_security_symbol
from .gold.currency_api import COVERAGE_START as _WORLD_GOLD_COVERAGE_START
from .validation import validate_date_range

__all__ = [
    "SourceCapability",
    "RequestDiagnostic",
    "source_capabilities",
    "explain_world_gold_history",
    "explain_index_constituents",
]


@dataclass(frozen=True)
class SourceCapability:
    """Conservative, documented coverage metadata for one source/endpoint leg.

    Coverage bounds are *known lower bounds*, not promises: ``coverage_end=None`` means
    rolling/unknown end, and a ``None`` ``coverage_start`` means no documented bound.
    """

    domain: str  # "gold" / "indices"
    endpoint: str  # "world_history" / "constituents"
    source: str  # e.g. "currency-api", "stooq", "ssi_iboard_query"
    instruments: tuple[str, ...]
    granularity: str | None
    coverage_start: date | None
    coverage_end: date | None
    is_default: bool
    is_opt_in: bool
    is_single_source: bool
    limitations: tuple[str, ...]
    suggested_action: str | None


@dataclass(frozen=True)
class RequestDiagnostic:
    """Offline diagnosis of a specific request against known source capabilities."""

    domain: str
    endpoint: str
    request: dict
    status: str  # "ok" | "coverage_gap" | "partial_coverage" | "single_source" | "unknown"
    sources: tuple[SourceCapability, ...]
    notes: tuple[str, ...] = ()
    suggested_actions: tuple[str, ...] = field(default=())


# --- known capability registry (static, offline) --------------------------- #
_WORLD_GOLD_CAPS: tuple[SourceCapability, ...] = (
    SourceCapability(
        domain="gold",
        endpoint="world_history",
        source="currency-api",
        instruments=("XAU/USD",),
        granularity="daily",
        coverage_start=_WORLD_GOLD_COVERAGE_START,
        coverage_end=None,  # rolling / unknown end
        is_default=True,
        is_opt_in=False,
        is_single_source=False,
        limitations=(
            "no-key daily EOD; one date-pinned request per calendar day; missing days "
            "(weekends/holidays/pre-coverage) are skipped; all-missing -> EmptyData",
            f"no known coverage before {_WORLD_GOLD_COVERAGE_START.isoformat()}",
        ),
        suggested_action="request a window on/after the known coverage start",
    ),
    SourceCapability(
        domain="gold",
        endpoint="world_history",
        source="stooq",
        instruments=("XAU/USD",),
        granularity="daily",
        coverage_start=None,
        coverage_end=None,
        is_default=False,
        is_opt_in=True,
        is_single_source=False,
        limitations=(
            "opt-in only (not in the default chain); same unit USD/oz; anti-bot caveat",
        ),
        suggested_action="opt in explicitly if a non-default daily backup is needed",
    ),
)

_INDEX_CONSTITUENTS_CAPS: tuple[SourceCapability, ...] = (
    SourceCapability(
        domain="indices",
        endpoint="constituents",
        source="ssi_iboard_query",
        instruments=("index constituents",),
        granularity=None,
        coverage_start=None,
        coverage_end=None,
        is_default=True,
        is_opt_in=False,
        is_single_source=True,
        limitations=(
            "membership only (no weights)",
            "single-source: no clean no-auth fallback currently configured",
        ),
        suggested_action="treat membership as point-in-time; do not expect weights",
    ),
)


def source_capabilities() -> tuple[SourceCapability, ...]:
    """Return immutable coverage metadata for the source-limited legs (offline)."""
    return _WORLD_GOLD_CAPS + _INDEX_CONSTITUENTS_CAPS


def explain_world_gold_history(start, end) -> RequestDiagnostic:
    """Diagnose a world-gold daily-history window vs known coverage (no network).

    Validates the bounds with the same contract as the live call, then classifies:
    a window entirely before the known coverage start is ``coverage_gap``; a window
    straddling it is ``partial_coverage``; an otherwise-covered window is ``ok``.
    """
    lo, hi = validate_date_range(start, end, name="explain_world_gold_history")
    cov = _WORLD_GOLD_COVERAGE_START
    notes: list[str] = []
    suggested: list[str] = []
    if hi < cov:
        status = "coverage_gap"
        notes.append(
            f"requested window {lo}..{hi} is entirely before the default source's known "
            f"coverage start {cov.isoformat()}; no data is expected (live call fails fast)"
        )
        suggested.append(f"request a window on/after {cov.isoformat()}")
        suggested.append("or opt in to a non-default daily backup (e.g. stooq) explicitly")
    elif lo < cov:
        status = "partial_coverage"
        notes.append(
            f"window starts before the known coverage start {cov.isoformat()}; the "
            f"pre-coverage portion ({lo}..{cov.isoformat()}) may be absent"
        )
        suggested.append(f"start the window on/after {cov.isoformat()} for full coverage")
    else:
        status = "ok"
        notes.append("window is within known coverage; daily EOD via the default no-key source")
    return RequestDiagnostic(
        domain="gold",
        endpoint="world_history",
        request={"start": lo.isoformat(), "end": hi.isoformat()},
        status=status,
        sources=_WORLD_GOLD_CAPS,
        notes=tuple(notes),
        suggested_actions=tuple(suggested),
    )


def explain_index_constituents(index) -> RequestDiagnostic:
    """Diagnose an index-constituents request (no network).

    Canonicalizes the selector with the same identifier contract as the live call
    (malformed selectors fail closed), then reports the single-source / no-weights
    limitation.
    """
    canonical = canonical_security_symbol(index, "index")
    return RequestDiagnostic(
        domain="indices",
        endpoint="constituents",
        request={"index": canonical},
        status="single_source",
        sources=_INDEX_CONSTITUENTS_CAPS,
        notes=(
            f"index {canonical!r} membership is served by a single default source "
            "(ssi_iboard_query); membership only, no weights, no clean no-auth fallback",
        ),
        suggested_actions=(
            "treat the membership basket as point-in-time",
            "do not expect constituent weights from this endpoint",
        ),
    )
