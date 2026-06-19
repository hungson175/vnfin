"""Tests for shared provider scalar coercion helpers."""
from __future__ import annotations

import pytest

from vnfin.coerce import parse_provider_float
from vnfin.exceptions import InvalidData


def test_parse_provider_float_accepts_numeric_scalars():
    assert parse_provider_float("12.5", label="x", source="probe") == 12.5
    assert parse_provider_float(7, label="x", source="probe") == 7.0


def test_parse_provider_float_rejects_bool():
    with pytest.raises(InvalidData, match="bool is not numeric"):
        parse_provider_float(True, label="open", source="probe")


def test_parse_provider_float_rejects_none_and_non_finite():
    with pytest.raises(InvalidData):
        parse_provider_float(None, label="x", source="probe")
    with pytest.raises(InvalidData):
        parse_provider_float("not-a-number", label="x", source="probe")
    with pytest.raises(InvalidData):
        parse_provider_float(float("inf"), label="x", source="probe")


def test_parse_provider_int_accepts_numeric_scalars():
    from vnfin.coerce import parse_provider_int

    assert parse_provider_int("1700000000", label="t", source="probe") == 1700000000
    assert parse_provider_int(1700000000.0, label="t", source="probe") == 1700000000


def test_parse_provider_int_rejects_bool():
    from vnfin.coerce import parse_provider_int

    with pytest.raises(InvalidData, match="bool is not numeric"):
        parse_provider_int(True, label="t", source="probe")
