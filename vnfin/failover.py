"""Domain-agnostic sequential multi-source failover.

This is the reusable core behind every vnfin failover client. It knows nothing
about prices, indices, NAVs, or any other domain — a caller supplies four small
callables and the engine does the rest:

* ``operation(source, *args, **kwargs) -> result`` — fetch from ONE source.
* ``capability(source, *args, **kwargs) -> bool`` — whether a source can serve
  this request *without* a network call. Incapable sources are skipped silently
  and do **not** count against ``max_attempts`` (mirrors the price client's
  interval-capability skip).
* ``reject(result) -> str | None`` — acceptance validation. Return a reason
  string to reject a result (record the attempt and fall through) or ``None`` to
  accept it. The default accepts any non-error result.
* ``unit_of(source) -> hashable | None`` — the unit/currency/scale a source
  emits. Used by the **unit-homogeneity guard** (below). ``None`` means the
  source does not declare a unit and is treated as compatible with anything.

Unit-homogeneity guard
-----------------------
A failover client must never silently combine sources that emit different
units/currencies/scales — failing over from a VND source to a "points" source,
or from a x1000-scaled feed to a x1 feed, would return plausible-but-wrong
numbers. At construction the engine collects every *declared* (non-``None``)
unit across all configured sources; if two sources declare different units it
either raises :class:`~vnfin.exceptions.UnitMismatchError` (default) or, when
``on_unit_mismatch="skip"``, keeps only sources matching the first declared
unit. This makes a scale/unit mix structurally impossible, not merely unlikely.
"""
from __future__ import annotations

import inspect
from datetime import datetime, timedelta
from typing import Any, Callable, Iterable, Optional

from .exceptions import AllSourcesFailed, SourceError, UnitMismatchError
from .models import SourceAttempt


def _fetched_at_utc_reason(value) -> Optional[str]:
    """Return a rejection reason for a malformed ``fetched_at_utc`` value (#127).

    ``fetched_at_utc`` is optional audit/freshness metadata: ``None`` is allowed
    (a separate policy choice). A *present* value must be a timezone-aware
    ``datetime`` whose offset is exactly UTC (``utcoffset() == timedelta(0)``);
    a naive datetime, a non-UTC datetime, a string, or any other type is
    malformed provenance and is rejected. The value is never normalized.
    """
    if value is None:
        return None
    if not isinstance(value, datetime):
        return f"malformed fetched_at_utc {value!r}: expected a UTC-aware datetime"
    offset = value.utcoffset()
    if offset is None or offset != timedelta(0):
        return f"malformed fetched_at_utc {value!r}: expected a UTC-aware datetime"
    return None


def _always_capable(source, *args, **kwargs) -> bool:
    return True


def _accept_all(result, *args, **kwargs) -> Optional[str]:
    return None


def _call_reject(
    reject: Callable[..., Optional[str]], result: Any, *args, **kwargs
) -> Optional[str]:
    """Invoke ``reject`` preserving one-arg ``reject(result)`` compatibility."""
    try:
        sig = inspect.signature(reject)
    except (TypeError, ValueError):
        sig = None
    if sig is not None:
        pos = [
            p
            for p in sig.parameters.values()
            if p.kind
            not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        ]
        if len(pos) == 1:
            return reject(result)
    try:
        return reject(result, *args, **kwargs)
    except TypeError:
        return reject(result)


def _unit_attr(source):
    """Default unit accessor: read a ``unit`` attribute, else ``None`` (undeclared)."""
    return getattr(source, "unit", None)


def _provenance_mismatch(claimed, source_name) -> Optional[str]:
    """Return a rejection reason if a result's stamped provenance does not match
    the source that produced it, else ``None`` (#126).

    Strict by design — a wired provenance check must be able to attribute the
    result to the source that produced it, so it accepts only two shapes:

    * a ``str`` claim (the normal single-result case) — accepted only if it equals
      ``source_name``;
    * a ``frozenset`` claim — the explicit COMPOSITE contract for multi-record
      results (e.g. the fundamentals tuple-of-reports extractor) — accepted only
      if it is non-empty and every member equals ``source_name``.

    Everything else is malformed provenance and is rejected: ``None`` (missing
    source), a bare ``list`` / ``set`` / ``tuple`` (a single-result source field
    must be a plain string, not a collection), a number, etc. This prevents a
    result with ``source=None`` or ``source=['actual']`` from being silently
    accepted.
    """
    if isinstance(claimed, str):
        if claimed != source_name:
            return (
                f"provenance mismatch: result stamped source {claimed!r} "
                f"but produced by source {source_name!r}"
            )
        return None
    if isinstance(claimed, frozenset):
        if not claimed:
            return (
                f"missing provenance: composite result carries no source "
                f"but was produced by source {source_name!r}"
            )
        mismatched = {c for c in claimed if c != source_name}
        if mismatched:
            return (
                "provenance mismatch: result stamped source "
                f"{sorted(repr(c) for c in mismatched)} but produced by source {source_name!r}"
            )
        return None
    return (
        f"malformed provenance {claimed!r}: result produced by source {source_name!r} "
        "must carry a matching string source"
    )


class FailoverClient:
    """Generic sequential failover over a homogeneous set of sources.

    Try capable sources in priority order, up to ``max_attempts`` actual calls,
    returning the first result that passes ``reject``. Construction enforces the
    unit-homogeneity guard so the configured set can never mix units/scales.
    """

    def __init__(
        self,
        sources: Iterable[Any],
        *,
        operation: Callable[..., Any],
        capability: Callable[..., bool] = _always_capable,
        reject: Callable[[Any], Optional[str]] = _accept_all,
        unit_of: Callable[[Any], Any] = _unit_attr,
        on_unit_mismatch: str = "raise",
        max_attempts: int = 3,
        failure_factory: Optional[Callable[..., BaseException]] = None,
        no_capable_factory: Optional[Callable[..., BaseException]] = None,
        finalize: Optional[Callable[..., Any]] = None,
        provenance_of: Optional[Callable[[Any], Any]] = None,
    ):
        if on_unit_mismatch not in ("raise", "skip"):
            raise ValueError(
                f"on_unit_mismatch must be 'raise' or 'skip', got {on_unit_mismatch!r}"
            )
        # B13: ``max_attempts`` is the per-call call budget; a non-int, a bool, or a
        # non-positive value would silently degrade failover (``0`` makes the chain
        # try nothing and always raise ``AllSourcesFailed``). Reject it up front with
        # a clear message instead of failing opaquely at run time. ``bool`` is a
        # subclass of ``int`` so it must be excluded explicitly.
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts <= 0:
            raise ValueError(
                f"max_attempts must be a positive int, got {max_attempts!r}"
            )
        self._operation = operation
        self._capability = capability
        self._reject = reject
        self._unit_of = unit_of
        self._provenance_of = provenance_of
        self.max_attempts = max_attempts
        self._failure_factory = failure_factory
        self._no_capable_factory = no_capable_factory
        self._finalize = finalize
        self.sources = self._guard_units(list(sources), on_unit_mismatch)

    # --- unit-homogeneity guard ------------------------------------------- #
    def _guard_units(self, sources: list, on_mismatch: str) -> list:
        """Reject (or, when skipping, drop) sources whose declared unit differs.

        Only *declared* (non-``None``) units participate. The first source that
        declares a unit fixes the canonical unit; any later source declaring a
        different unit is the violation.
        """
        canonical = None
        kept: list = []
        for src in sources:
            unit = self._unit_of(src)
            if unit is None:
                kept.append(src)
                continue
            if canonical is None:
                canonical = unit
                kept.append(src)
            elif unit == canonical:
                kept.append(src)
            elif on_mismatch == "raise":
                raise UnitMismatchError(
                    "failover sources must share one unit/currency; "
                    f"source {getattr(src, 'name', src)!r} declares unit {unit!r} "
                    f"but the chain is {canonical!r}"
                )
            # on_mismatch == "skip": silently drop the mismatched source
        return kept

    @property
    def unit(self):
        """The single declared unit of this chain, or ``None`` if none declared."""
        for src in self.sources:
            u = self._unit_of(src)
            if u is not None:
                return u
        return None

    # --- failover engine -------------------------------------------------- #
    def run(self, *args, **kwargs) -> Any:
        """Execute the operation across capable sources with failover.

        Positional/keyword args are forwarded to ``operation`` and
        ``capability`` unchanged. Returns the first accepted result (after
        ``finalize`` if configured) or raises the configured failure exception.
        """
        attempts: list[SourceAttempt] = []
        capable = [s for s in self.sources if self._capability(s, *args, **kwargs)]
        if not capable:
            if self._no_capable_factory is not None:
                raise self._no_capable_factory(*args, **kwargs)
            raise AllSourcesFailed(
                getattr(args[0], "__str__", lambda: "")() if args else "",
                kwargs.get("interval"),
                (),
            )
        for src in capable:
            if len(attempts) >= self.max_attempts:
                break
            try:
                result = self._operation(src, *args, **kwargs)
            except SourceError as exc:
                attempts.append(
                    SourceAttempt(src.name, False, f"{type(exc).__name__}: {exc}")
                )
                continue
            reason = _call_reject(self._reject, result, *args, **kwargs)
            if reason:
                attempts.append(SourceAttempt(src.name, False, reason))
                continue
            # Issue #126: a result is accepted only if its stamped provenance
            # matches the source that actually produced it. A mismatch (e.g. a
            # primary returning a result labelled with the backup's name) is a
            # recorded rejected attempt — never silently relabelled — so audit
            # logs / backtests / reconciliation can trust ``result.source``.
            if self._provenance_of is not None:
                pmis = _provenance_mismatch(self._provenance_of(result), src.name)
                if pmis is not None:
                    attempts.append(SourceAttempt(src.name, False, pmis))
                    continue
            attempts.append(SourceAttempt(src.name, True, "ok"))
            if self._finalize is not None:
                return self._finalize(result, tuple(attempts), *args, **kwargs)
            return result
        if self._failure_factory is not None:
            raise self._failure_factory(tuple(attempts), *args, **kwargs)
        raise AllSourcesFailed("", kwargs.get("interval"), tuple(attempts))
