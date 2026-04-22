"""Edge case tests that justify why this MCP exists vs prompt heuristics."""

from business_day_mcp.server import (
    is_business_day,
    last_business_day_of_month,
    next_business_day,
)


class TestGermanHolidayEdgeCases:
    """Cases where a naive 'last weekday of month' heuristic fails."""

    def test_labor_day_falls_on_friday_affects_next_business_day(self):
        # 2026-05-01 Fri = Labor Day. Thursday 2026-04-30 is the last
        # April business day. Friday May 1 is a holiday. Weekend follows.
        # Naive "is today last weekday of April?" on Thu April 30 → NO
        # (because Fri May 1 is a weekday).
        # Correct answer: YES — last DE business day of April is Thu April 30.
        # But wait: April ends on April 30, May 1 is May. So for April:
        result = last_business_day_of_month(year=2026, month=4, country="DE")
        assert result["last_business_day"] == "2026-04-30"

        # For May: last calendar day is Sun May 31
        # Last business day: Fri May 29 (not May 25 Whit Monday)
        result = last_business_day_of_month(year=2026, month=5, country="DE")
        assert result["last_business_day"] == "2026-05-29"

    def test_ascension_day_thursday(self):
        # 2026-05-14 Thu = Ascension Day (DE public holiday)
        # Wed 2026-05-13 → next DE business day is Fri 2026-05-15
        result = next_business_day(date="2026-05-13", country="DE")
        assert result["next_business_day"] == "2026-05-15"

    def test_german_unity_on_saturday(self):
        # 2026-10-03 Sat = Tag der Deutschen Einheit (holiday on weekend)
        # The date itself is a holiday, but since it's Saturday,
        # it's both a weekend AND a holiday
        result = is_business_day(date="2026-10-03", country="DE")
        assert result["is_business_day"] is False
        assert result["is_weekend"] is True
        assert result["is_holiday"] is True


class TestUSHolidayEdgeCases:
    def test_christmas_on_friday_2026(self):
        # 2026-12-25 Fri = Christmas Day
        # Last US business day of Dec 2026: Thu Dec 31
        result = last_business_day_of_month(year=2026, month=12, country="US")
        # Dec 31 2026 is Thursday — a business day
        assert result["last_business_day"] == "2026-12-31"

    def test_july_4_weekend_observance(self):
        # July 4 2026 is Saturday, typically observed Friday July 3
        # is_business_day for July 3 should report is_holiday=true
        result = is_business_day(date="2026-07-03", country="US")
        assert result["is_holiday"] is True
        assert result["is_business_day"] is False


class TestTimeZoneEdgeCases:
    """Rarely-tested timezone behavior."""

    def test_asia_tokyo(self):
        from business_day_mcp.server import get_current_date

        result = get_current_date(timezone="Asia/Tokyo")
        assert result["timezone"] == "Asia/Tokyo"

    def test_unknown_timezone(self):
        import pytest

        from business_day_mcp.server import get_current_date

        with pytest.raises(ValueError, match=r"Unknown timezone:.*IANA"):
            get_current_date(timezone="Mars/Olympus")
