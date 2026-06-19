import pytest

from datetime import date, datetime

from vnfin.exceptions import InvalidData, VnfinError
from vnfin.validation import (
    validate_country_iso3,
    validate_date_range,
    validate_fraction,
    validate_iso4217,
    validate_non_empty_string,
    validate_positive_int,
)


class TestValidateNonEmptyString:
    def test_returns_stripped_string(self):
        assert validate_non_empty_string("  FPT  ") == "FPT"

    @pytest.mark.parametrize("bad", [None, "", "   ", 123, []])
    def test_rejects_bad_values(self, bad):
        with pytest.raises(InvalidData):
            validate_non_empty_string(bad)


class TestIsoCurrencyCode:
    def test_returns_uppercased_code(self):
        assert validate_iso4217(" usd ") == "USD"

    @pytest.mark.parametrize("bad", [None, "", "US", "USDD", "us1", 123])
    def test_rejects_bad_codes(self, bad):
        with pytest.raises(InvalidData):
            validate_iso4217(bad)


class TestCountryCode:
    def test_returns_uppercased_code(self):
        assert validate_country_iso3(" vnm ") == "VNM"

    @pytest.mark.parametrize("bad", [None, "", "VN", "VNMX", "vn1", 123])
    def test_rejects_bad_codes(self, bad):
        with pytest.raises(InvalidData):
            validate_country_iso3(bad)


class TestValidateDateRange:
    def test_returns_valid_range(self):
        sd, ed = validate_date_range(date(2024, 1, 1), date(2024, 1, 3))
        assert sd == date(2024, 1, 1)
        assert ed == date(2024, 1, 3)

    def test_rejects_inverted_range(self):
        with pytest.raises(InvalidData):
            validate_date_range(date(2024, 1, 3), date(2024, 1, 1))

    def test_rejects_non_date(self):
        with pytest.raises(InvalidData):
            validate_date_range("bad", date(2024, 1, 1))

    def test_rejects_missing_when_required(self):
        with pytest.raises(InvalidData):
            validate_date_range(None, date(2024, 1, 1))

    def test_allows_none_when_configured(self):
        sd, ed = validate_date_range(None, date(2024, 1, 1), allow_none=True)
        assert sd is None
        assert ed == date(2024, 1, 1)

    def test_accepts_datetime(self):
        sd, ed = validate_date_range(
            datetime(2024, 1, 1), datetime(2024, 1, 3), name="price history"
        )
        assert sd == datetime(2024, 1, 1)
        assert ed == datetime(2024, 1, 3)


class TestValidatePositiveInt:
    def test_returns_int(self):
        assert validate_positive_int(8) == 8

    @pytest.mark.parametrize("bad", [0, -1, 1.5, "8", True, False])
    def test_rejects_bad_values(self, bad):
        with pytest.raises(VnfinError):
            validate_positive_int(bad)


class TestValidateFraction:
    def test_returns_float(self):
        assert validate_fraction(0.5) == 0.5

    @pytest.mark.parametrize("bad", [-0.1, 1.1, "x", True])
    def test_rejects_bad_values(self, bad):
        with pytest.raises(ValueError):
            validate_fraction(bad)
