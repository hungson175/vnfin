"""Composable typed-result validators (#refactor Phase 3).

Behavior-preserving extractions of the common logic previously copy-pasted across
the per-domain ``_validate_*_result()`` functions. Each rule returns a rejection
**reason string** (recorded as a failover ``SourceAttempt`` reason) or ``None`` if
acceptable. Reason text is **parameterized** so each domain keeps its exact wording
— callers must pass the same message/noun the domain used, and the full suite (which
asserts those messages) enforces byte-exactness.

Phase 3 is incremental: gold migrates first as the approach-proof; price / crypto /
fundamentals / macro follow once the reviewer approves (D-lite).
"""
from __future__ import annotations

from typing import Optional


def result_type_reason(result, expected_type, *, noun: str = "result") -> Optional[str]:
    """Reject a value that is not an instance of ``expected_type``.

    Matches the long-standing ``f"unexpected {noun} type {type(...).__name__}"``
    wording (#125) so a malformed container/row is a recorded rejected attempt, not
    a raw ``AttributeError`` downstream. ``noun`` defaults to ``"result"`` (the
    failover-container wording); pass e.g. ``"report"`` for a per-element check.
    """
    if not isinstance(result, expected_type):
        return f"unexpected {noun} type {type(result).__name__}"
    return None


def non_empty_reason(seq, msg: str = "empty result") -> Optional[str]:
    """Reject an empty sequence with the caller's ``msg`` (default ``"empty result"``)."""
    if len(seq) == 0:
        return msg
    return None
