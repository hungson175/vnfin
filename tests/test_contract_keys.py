"""Phase 1 contract primitives — canonical keys + enum tags (#refactor)."""
from __future__ import annotations

import pytest

from vnfin._contracts import MISSING, canonical_enum_tag, canonical_provider_key
from vnfin.exceptions import InvalidData

CTX = "test key"

# Shared malformed-key matrix (mirrors the refactor plan's BAD_PROVIDER_KEYS).
# Includes Checkpoint-B1 cases: negatives, decimal/punctuation/internal-space strings.
BAD_PROVIDER_KEYS = [
    True, False, 11000.5, float("inf"), float("nan"),
    [11000], {"code": 11000}, None, "", "   ", "+11000", "-11000", "011000", " 11000 ",
    -1, -1.0, "11000.5", "{}", "A B", "EPS.1", "1A", "_X", "A-B", "A.B",
]


@pytest.mark.parametrize("bad", BAD_PROVIDER_KEYS)
def test_canonical_provider_key_rejects_malformed(bad):
    with pytest.raises(InvalidData):
        canonical_provider_key(bad, CTX)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("11000", "11000"),
        ("0", "0"),
        ("EPS", "EPS"),         # clean alpha key allowed by default
        ("ROE1", "ROE1"),       # letter-start, then alphanumeric
        ("GROSS_MARGIN", "GROSS_MARGIN"),  # underscore allowed
        (11000, "11000"),       # int -> decimal string
        (11000.0, "11000"),     # integral float -> integer string
        (0, "0"),
    ],
)
def test_canonical_provider_key_accepts_canonical(value, expected):
    assert canonical_provider_key(value, CTX) == expected


def test_canonical_provider_key_flags_can_deny():
    with pytest.raises(InvalidData):
        canonical_provider_key("EPS", CTX, allow_alpha=False)
    with pytest.raises(InvalidData):
        canonical_provider_key(11000, CTX, allow_int=False)
    with pytest.raises(InvalidData):
        canonical_provider_key(11000.0, CTX, allow_integral_float=False)


# --- canonical_enum_tag -----------------------------------------------------
ANNUAL_QUARTER = {"ANNUAL", "QUARTER"}


def test_canonical_enum_tag_normalizes_and_accepts_member():
    assert canonical_enum_tag("annual", ANNUAL_QUARTER, CTX) == "ANNUAL"
    assert canonical_enum_tag("QUARTER", ANNUAL_QUARTER, CTX) == "QUARTER"


def test_canonical_enum_tag_missing_ok_returns_none():
    assert canonical_enum_tag(MISSING, ANNUAL_QUARTER, CTX, missing_ok=True) is None


def test_canonical_enum_tag_missing_not_ok_raises():
    with pytest.raises(InvalidData, match="missing required tag"):
        canonical_enum_tag(MISSING, ANNUAL_QUARTER, CTX, missing_ok=False)


@pytest.mark.parametrize("bad", ["", "   ", None, [], {}, False, True, 123])
def test_canonical_enum_tag_present_malformed_raises(bad):
    with pytest.raises(InvalidData):
        canonical_enum_tag(bad, ANNUAL_QUARTER, CTX, missing_ok=True)


def test_canonical_enum_tag_present_valid_but_unknown_raises():
    with pytest.raises(InvalidData, match="not one of"):
        canonical_enum_tag("MONTHLY", ANNUAL_QUARTER, CTX, missing_ok=True)


# Phase 4 — canonical security/fund identifier (#34/#33/#30/#9).
from vnfin._contracts import canonical_fund_code, canonical_security_symbol


@pytest.mark.parametrize("fn", [canonical_security_symbol, canonical_fund_code])
class TestCanonicalIdentifier:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("VCBFBCF", "VCBFBCF"), ("VFMVF1", "VFMVF1"), ("RVPF24", "RVPF24"),
            ("VN30", "VN30"), ("E1VFVN30", "E1VFVN30"), ("FUEVFVND", "FUEVFVND"),
            ("  vcbf ", "VCBF"),   # strip().upper() normalization
            ("fpt", "FPT"),
        ],
    )
    def test_accepts_and_normalizes(self, fn, value, expected):
        assert fn(value, "ctx") == expected

    @pytest.mark.parametrize(
        "bad",
        [None, "", "   ", [], {}, True, False, 123, 1.5,
         "A B", "A.B", "A-B", "A/B", "1ABC", "+ABC", "AB\nC", "AB%"],
    )
    def test_rejects_malformed(self, fn, bad):
        with pytest.raises(InvalidData):
            fn(bad, "ctx")
