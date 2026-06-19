"""Phase 1 contract primitives — field access semantics (#refactor).

The whole point of these primitives is the absent / present-null / present-blank
distinction, so each case is tested separately.
"""
from __future__ import annotations

import pytest

from vnfin._contracts import (
    MISSING,
    has_present_key,
    optional_present,
    optional_present_non_empty_str,
    require_non_empty_str,
    require_present,
)
from vnfin.exceptions import InvalidData

CTX = "test field"


# --- has_present_key --------------------------------------------------------
def test_has_present_key_true_for_present_including_null():
    assert has_present_key({"k": None}, "k") is True
    assert has_present_key({"k": 0}, "k") is True
    assert has_present_key({"k": "v"}, "k") is True


def test_has_present_key_false_for_absent_or_non_dict():
    assert has_present_key({}, "k") is False
    assert has_present_key("not a dict", "k") is False
    assert has_present_key(None, "k") is False


# --- require_present --------------------------------------------------------
def test_require_present_returns_value_including_null():
    assert require_present({"k": None}, "k", CTX) is None
    assert require_present({"k": "v"}, "k", CTX) == "v"


def test_require_present_raises_when_absent():
    with pytest.raises(InvalidData, match="missing required field"):
        require_present({}, "k", CTX)


# --- optional_present: MISSING vs present-null ------------------------------
def test_optional_present_returns_missing_when_absent():
    assert optional_present({}, "k") is MISSING
    assert optional_present("not a dict", "k") is MISSING


def test_optional_present_returns_value_for_present_null_and_blank():
    # present-null and present-blank are NOT MISSING (they are real values).
    assert optional_present({"k": None}, "k") is None
    assert optional_present({"k": ""}, "k") == ""


def test_missing_is_not_none_and_is_falsey():
    assert MISSING is not None
    assert not MISSING
    assert repr(MISSING) == "MISSING"


# --- require_non_empty_str (canonical vs lenient) ---------------------------
@pytest.mark.parametrize("bad", [None, [], {}, False, True, 123, 1.5])
def test_require_non_empty_str_rejects_non_strings(bad):
    with pytest.raises(InvalidData, match="expected a string"):
        require_non_empty_str(bad, CTX)


@pytest.mark.parametrize("bad", ["", "   ", " x", "x ", " x "])
def test_require_non_empty_str_canonical_rejects_blank_and_padded(bad):
    with pytest.raises(InvalidData):
        require_non_empty_str(bad, CTX, canonical=True)


def test_require_non_empty_str_canonical_accepts_clean():
    assert require_non_empty_str("FPT", CTX, canonical=True) == "FPT"


def test_require_non_empty_str_lenient_strips_and_accepts_padded():
    assert require_non_empty_str("  FPT  ", CTX, canonical=False) == "FPT"
    with pytest.raises(InvalidData):
        require_non_empty_str("   ", CTX, canonical=False)


# --- optional_present_non_empty_str -----------------------------------------
def test_optional_present_non_empty_str_absent_returns_none():
    # Missing key -> legacy-compatible None (no identity to check).
    assert optional_present_non_empty_str({}, "Symbol", CTX) is None


@pytest.mark.parametrize("bad", [None, "", "   ", [], {}, False, True, 123])
def test_optional_present_non_empty_str_present_malformed_raises(bad):
    # Present (incl. null/blank/non-string) must fail closed, not be treated absent.
    with pytest.raises(InvalidData):
        optional_present_non_empty_str({"Symbol": bad}, "Symbol", CTX)


def test_optional_present_non_empty_str_present_valid_returns_value():
    assert optional_present_non_empty_str({"Symbol": "FPT"}, "Symbol", CTX) == "FPT"
