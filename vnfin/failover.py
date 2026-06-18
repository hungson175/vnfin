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

from typing import Any, Callable, Iterable, Optional

from .exceptions import AllSourcesFailed, SourceError, UnitMismatchError
from .models import SourceAttempt


def _always_capable(source, *args, **kwargs) -> bool:
    return True


def _accept_all(result) -> Optional[str]:
    return None


def _unit_attr(source):
    """Default unit accessor: read a ``unit`` attribute, else ``None`` (undeclared)."""
    return getattr(source, "unit", None)


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
    ):
        if on_unit_mismatch not in ("raise", "skip"):
            raise ValueError(
                f"on_unit_mismatch must be 'raise' or 'skip', got {on_unit_mismatch!r}"
            )
        self._operation = operation
        self._capability = capability
        self._reject = reject
        self._unit_of = unit_of
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
            reason = self._reject(result)
            if reason:
                attempts.append(SourceAttempt(src.name, False, reason))
                continue
            attempts.append(SourceAttempt(src.name, True, "ok"))
            if self._finalize is not None:
                return self._finalize(result, tuple(attempts), *args, **kwargs)
            return result
        if self._failure_factory is not None:
            raise self._failure_factory(tuple(attempts), *args, **kwargs)
        raise AllSourcesFailed("", kwargs.get("interval"), tuple(attempts))
