"""Phase 3 contract primitives — result-level rules (#refactor)."""
from __future__ import annotations

from vnfin._contracts import non_empty_reason, result_type_reason


class _Hist:
    pass


def test_result_type_reason_accepts_expected():
    assert result_type_reason(_Hist(), _Hist) is None


def test_result_type_reason_rejects_with_type_name():
    assert result_type_reason("nope", _Hist) == "unexpected result type str"
    assert result_type_reason(123, _Hist) == "unexpected result type int"


def test_result_type_reason_custom_noun():
    # fundamentals uses noun="report" for its per-element check.
    assert result_type_reason("nope", _Hist, noun="report") == "unexpected report type str"
    assert result_type_reason(_Hist(), _Hist, noun="report") is None


def test_non_empty_reason_default_and_custom_msg():
    assert non_empty_reason([1]) is None
    assert non_empty_reason([]) == "empty result"
    assert non_empty_reason((), msg="no bars") == "no bars"
