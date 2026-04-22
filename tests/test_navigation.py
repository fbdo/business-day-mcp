"""Tests for next_business_day and previous_business_day."""

import pytest

from business_day_mcp.server import next_business_day, previous_business_day

# ─── next_business_day ──────────────────────────────────────────────────


class TestNextBusinessDay:
    def test_skip_weekend(self):
        # Friday 2026-04-17 → next business day is Monday 2026-04-20
        result = next_business_day(date="2026-04-17", country="DE")
        assert result["next_business_day"] == "2026-04-20"
        assert result["skipped_days"] == 3
        assert result["country"] == "DE"
        assert result["input_date"] == "2026-04-17"

    def test_skip_holiday_and_weekend(self):
        # 2026-05-01 Fri (Labor Day) → next business day is 2026-05-04 Mon
        result = next_business_day(date="2026-05-01", country="DE")
        assert result["next_business_day"] == "2026-05-04"
        assert result["skipped_days"] == 3

    def test_inclusive_on_business_day(self):
        # Business day with inclusive=True returns the date itself
        result = next_business_day(date="2026-04-21", country="DE", inclusive=True)
        assert result["next_business_day"] == "2026-04-21"
        assert result["skipped_days"] == 0

    def test_inclusive_on_holiday(self):
        # Holiday with inclusive=True still skips forward
        result = next_business_day(date="2026-05-01", country="DE", inclusive=True)
        assert result["next_business_day"] == "2026-05-04"
        assert result["skipped_days"] == 3

    def test_non_inclusive_on_business_day(self):
        # Business day with inclusive=False moves forward
        result = next_business_day(date="2026-04-21", country="DE")
        assert result["next_business_day"] == "2026-04-22"
        assert result["skipped_days"] == 1
        assert result["country"] == "DE"
        assert result["input_date"] == "2026-04-21"

    def test_year_boundary(self):
        # 2025-12-31 Wed → next DE business day is 2026-01-02 Fri
        # (2026-01-01 is New Year's Day)
        result = next_business_day(date="2025-12-31", country="DE")
        assert result["next_business_day"] == "2026-01-02"

    def test_unknown_country_raises(self):
        with pytest.raises(ValueError, match=r"Unknown country code:.*get_supported_countries"):
            next_business_day(date="2026-04-21", country="ZZ")


# ─── previous_business_day ──────────────────────────────────────────────


class TestPreviousBusinessDay:
    def test_skip_weekend(self):
        # Monday 2026-04-20 → previous is Friday 2026-04-17
        result = previous_business_day(date="2026-04-20", country="DE")
        assert result["previous_business_day"] == "2026-04-17"
        assert result["skipped_days"] == 3
        assert result["country"] == "DE"
        assert result["input_date"] == "2026-04-20"

    def test_skip_easter_monday(self):
        # 2026-04-07 Tue → previous DE business day is 2026-04-02 Thu
        # (2026-04-06 Mon = Easter Monday, 2026-04-03 Fri = Good Friday,
        # 2026-04-04 and 2026-04-05 = weekend)
        result = previous_business_day(date="2026-04-07", country="DE")
        assert result["previous_business_day"] == "2026-04-02"
        assert result["skipped_days"] == 5

    def test_inclusive_on_business_day(self):
        result = previous_business_day(date="2026-04-21", country="DE", inclusive=True)
        assert result["previous_business_day"] == "2026-04-21"
        assert result["skipped_days"] == 0

    def test_year_boundary(self):
        # 2026-01-02 Fri → previous DE business day is 2025-12-31 Wed
        # (2026-01-01 = New Year's Day)
        result = previous_business_day(date="2026-01-02", country="DE")
        assert result["previous_business_day"] == "2025-12-31"

    def test_unknown_country_raises(self):
        with pytest.raises(ValueError, match=r"Unknown country code:.*get_supported_countries"):
            previous_business_day(date="2026-04-21", country="ZZ")
