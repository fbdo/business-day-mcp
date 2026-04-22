"""Tests for get_current_date and is_business_day."""

import re

import pytest

from business_day_mcp.server import get_current_date, is_business_day

# ─── get_current_date ───────────────────────────────────────────────────


class TestGetCurrentDate:
    def test_default_timezone_utc(self):
        result = get_current_date()
        assert result["timezone"] == "UTC"
        assert re.match(r"\d{4}-\d{2}-\d{2}", result["date"])
        assert result["day_of_week"] in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        assert 1 <= result["iso_week"] <= 53

    def test_europe_berlin(self):
        result = get_current_date(timezone="Europe/Berlin")
        assert result["timezone"] == "Europe/Berlin"
        assert re.match(r"\d{4}-\d{2}-\d{2}", result["date"])

    def test_invalid_timezone_raises(self):
        with pytest.raises(ValueError, match=r"Unknown timezone:.*IANA"):
            get_current_date(timezone="Not/AZone")


# ─── is_business_day ────────────────────────────────────────────────────


class TestIsBusinessDay:
    def test_regular_tuesday_de(self, de_business_day):
        result = is_business_day(date=de_business_day, country="DE")
        assert result["is_business_day"] is True
        assert result["is_weekend"] is False
        assert result["is_holiday"] is False
        assert result["holiday_name"] is None
        assert result["country"] == "DE"

    def test_labor_day_de(self, de_holiday):
        result = is_business_day(date=de_holiday, country="DE")
        assert result["is_business_day"] is False
        assert result["is_weekend"] is False
        assert result["is_holiday"] is True
        # German holidays library returns "Tag der Arbeit" or "Labor Day"
        # depending on version; just ensure a name is returned
        assert result["holiday_name"] is not None
        assert len(result["holiday_name"]) > 0

    def test_saturday_de(self, de_weekend):
        result = is_business_day(date=de_weekend, country="DE")
        assert result["is_business_day"] is False
        assert result["is_weekend"] is True
        assert result["is_holiday"] is False

    def test_country_case_insensitive(self, de_business_day):
        upper = is_business_day(date=de_business_day, country="DE")
        lower = is_business_day(date=de_business_day, country="de")
        assert upper == lower
        assert upper["country"] == "DE"

    def test_unknown_country_raises(self, de_business_day):
        with pytest.raises(ValueError, match=r"Unknown country code:.*get_supported_countries"):
            is_business_day(date=de_business_day, country="ZZ")

    def test_bad_date_format_raises(self):
        with pytest.raises(ValueError, match=r"Invalid date format:.*ISO 8601"):
            is_business_day(date="not-a-date", country="DE")
        with pytest.raises(ValueError, match=r"Invalid date format:.*ISO 8601"):
            is_business_day(date="04/21/2026", country="DE")

    def test_us_independence_day_observed(self, us_holiday):
        result = is_business_day(date=us_holiday, country="US")
        assert result["is_holiday"] is True
        assert result["is_business_day"] is False

    def test_missing_country_raises_type_error(self):
        import pytest

        with pytest.raises(TypeError):
            is_business_day(date="2026-04-21")  # type: ignore[call-arg]
