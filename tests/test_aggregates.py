"""Tests for last_business_day_of_month and business_days_between."""

import pytest

from business_day_mcp.server import (
    business_days_between,
    last_business_day_of_month,
)

# ─── last_business_day_of_month ─────────────────────────────────────────


class TestLastBusinessDayOfMonth:
    def test_april_2026_de(self):
        # April 2026 ends Thu 2026-04-30 → that's the last business day
        # (May 1 Fri is Labor Day but it's a new month)
        result = last_business_day_of_month(year=2026, month=4, country="DE")
        assert result["last_business_day"] == "2026-04-30"
        assert result["last_calendar_day"] == "2026-04-30"
        assert result["year"] == 2026
        assert result["month"] == 4
        assert result["country"] == "DE"

    def test_may_2026_de_whit_monday(self):
        # May 2026: last calendar day is Sun 2026-05-31
        # Last business day: Fri 2026-05-29 (May 25 Whit Monday is earlier)
        result = last_business_day_of_month(year=2026, month=5, country="DE")
        assert result["last_business_day"] == "2026-05-29"
        assert result["last_calendar_day"] == "2026-05-31"

    def test_december_2026_de(self):
        # Dec 2026: Thu 31 is Silvester (not a public holiday in DE federally)
        # Fri 25 = Christmas, Sat 26 = Boxing Day
        # Dec 31 Thu is a business day
        result = last_business_day_of_month(year=2026, month=12, country="DE")
        assert result["last_business_day"] == "2026-12-31"

    def test_february_leap_year(self):
        # 2024 is leap — Feb 29 Thu is a business day in US
        result = last_business_day_of_month(year=2024, month=2, country="US")
        assert result["last_business_day"] == "2024-02-29"
        assert result["last_calendar_day"] == "2024-02-29"

    def test_invalid_month_raises(self):
        with pytest.raises(ValueError, match=r"Invalid month:.*1-12"):
            last_business_day_of_month(year=2026, month=13, country="DE")
        with pytest.raises(ValueError, match=r"Invalid month:.*1-12"):
            last_business_day_of_month(year=2026, month=0, country="DE")

    def test_unknown_country_raises(self):
        import pytest

        with pytest.raises(ValueError, match=r"Unknown country code:.*get_supported_countries"):
            last_business_day_of_month(year=2026, month=4, country="ZZ")


# ─── business_days_between ──────────────────────────────────────────────


class TestBusinessDaysBetween:
    def test_same_day_non_inclusive(self):
        result = business_days_between(start_date="2026-04-21", end_date="2026-04-21", country="DE")
        # Non-inclusive: end not counted, start is Tue (business day) counted
        assert result["business_days"] == 0
        assert result["calendar_days"] == 0

    def test_same_day_inclusive(self):
        result = business_days_between(
            start_date="2026-04-21",
            end_date="2026-04-21",
            country="DE",
            inclusive=True,
        )
        assert result["business_days"] == 1
        assert result["calendar_days"] == 1

    def test_two_week_span_with_labor_day(self):
        # 2026-04-20 Mon → 2026-05-04 Mon inclusive
        # Business days: Mon-Fri x 2 + Mon = 11
        # BUT 2026-05-01 Fri is Labor Day → 11 - 1 = 10
        result = business_days_between(
            start_date="2026-04-20",
            end_date="2026-05-04",
            country="DE",
            inclusive=True,
        )
        assert result["business_days"] == 10
        assert result["calendar_days"] == 15
        assert len(result["holidays_in_range"]) == 1
        assert result["holidays_in_range"][0]["date"] == "2026-05-01"
        assert result["country"] == "DE"
        assert result["start_date"] == "2026-04-20"
        assert result["end_date"] == "2026-05-04"

    def test_holidays_in_range_reported(self):
        # April 2026: Good Friday (03), Easter Monday (06)
        result = business_days_between(
            start_date="2026-04-01",
            end_date="2026-04-10",
            country="DE",
            inclusive=True,
        )
        holiday_dates = [h["date"] for h in result["holidays_in_range"]]
        assert "2026-04-03" in holiday_dates
        assert "2026-04-06" in holiday_dates

    def test_reversed_range_raises(self):
        with pytest.raises(ValueError, match="on or before"):
            business_days_between(
                start_date="2026-05-01",
                end_date="2026-04-01",
                country="DE",
            )

    def test_year_crossing(self):
        # 2025-12-29 Mon → 2026-01-05 Mon inclusive
        # Dec 29 30 31 = 3 business days
        # Jan 1 = New Year holiday, Jan 2 Fri = business day
        # Jan 5 Mon = business day
        # Total: 3 + 0 + 1 + 1 = 5
        result = business_days_between(
            start_date="2025-12-29",
            end_date="2026-01-05",
            country="DE",
            inclusive=True,
        )
        assert result["business_days"] == 5
        holiday_dates = [h["date"] for h in result["holidays_in_range"]]
        assert "2026-01-01" in holiday_dates

    def test_unknown_country_raises(self):
        import pytest

        with pytest.raises(ValueError, match=r"Unknown country code:.*get_supported_countries"):
            business_days_between(start_date="2026-04-20", end_date="2026-04-24", country="ZZ")

    def test_weekend_holiday_not_in_range(self):
        # 2026-10-03 Sat = German Unity Day — weekend holiday, must not appear
        result = business_days_between(
            start_date="2026-10-01",
            end_date="2026-10-05",
            country="DE",
            inclusive=True,
        )
        dates = [h["date"] for h in result["holidays_in_range"]]
        assert "2026-10-03" not in dates
