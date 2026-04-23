"""Tests for the optional `subdiv` parameter (regional holidays)."""

from __future__ import annotations

import pytest

from business_day_mcp.server import (
    get_supported_countries,
    get_supported_subdivisions,
    is_business_day,
    list_holidays,
)

# 2026-01-06 is Epiphany — a holiday ONLY in specific German states (e.g. BY),
# not a nationwide German holiday. It is the canonical probe for subdiv support.
_EPIPHANY_2026 = "2026-01-06"


class TestSubdivRegionalHolidays:
    def test_de_by_includes_epiphany(self):
        result = is_business_day(date=_EPIPHANY_2026, country="DE", subdiv="BY")
        assert result["is_holiday"] is True
        assert result["is_business_day"] is False
        assert result["holiday_name"]  # non-empty
        assert result["subdiv"] == "BY"
        assert result["country"] == "DE"

    def test_de_national_excludes_epiphany(self):
        # Regression guard: omitting subdiv must return ONLY nation-wide holidays.
        result = is_business_day(date=_EPIPHANY_2026, country="DE")
        assert result["is_holiday"] is False
        assert result["is_business_day"] is True
        assert "subdiv" not in result

    def test_list_holidays_de_by_contains_epiphany(self):
        result = list_holidays(year=2026, country="DE", subdiv="BY")
        dates = [h["date"] for h in result["holidays"]]
        assert _EPIPHANY_2026 in dates
        assert result["subdiv"] == "BY"

    def test_list_holidays_de_national_omits_epiphany(self):
        result = list_holidays(year=2026, country="DE")
        dates = [h["date"] for h in result["holidays"]]
        assert _EPIPHANY_2026 not in dates
        assert "subdiv" not in result

    def test_invalid_subdiv_raises(self):
        with pytest.raises(ValueError, match=r"Unknown country code:"):
            is_business_day(date=_EPIPHANY_2026, country="DE", subdiv="ZZZ")


class TestGetSupportedCountriesSubdivisions:
    def test_de_entry_exposes_subdivisions(self):
        result = get_supported_countries()
        de = next(c for c in result["countries"] if c["code"] == "DE")
        assert isinstance(de["subdivisions"], list)
        assert "BY" in de["subdivisions"]  # Bavaria

    def test_jp_entry_has_empty_subdivisions(self):
        result = get_supported_countries()
        jp = next(c for c in result["countries"] if c["code"] == "JP")
        assert jp["subdivisions"] == []

    def test_every_entry_has_subdivisions_field(self):
        result = get_supported_countries()
        for entry in result["countries"]:
            assert "subdivisions" in entry
            assert isinstance(entry["subdivisions"], list)


class TestGetSupportedSubdivisions:
    def test_de_returns_canonical_codes(self):
        result = get_supported_subdivisions(country="DE")
        assert result["country"] == "DE"
        assert isinstance(result["subdivisions"], list)
        assert "BY" in result["subdivisions"]
        assert "BW" in result["subdivisions"]

    def test_de_aliases_is_dict(self):
        result = get_supported_subdivisions(country="DE")
        assert isinstance(result["aliases"], dict)

    def test_jp_has_no_subdivisions(self):
        result = get_supported_subdivisions(country="JP")
        assert result["country"] == "JP"
        assert result["subdivisions"] == []
        assert result["aliases"] == {}

    def test_unknown_country_raises(self):
        with pytest.raises(ValueError, match=r"Unknown country code:"):
            get_supported_subdivisions(country="ZZ")
