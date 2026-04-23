"""Tests for list_holidays and get_supported_countries."""

from business_day_mcp.server import get_supported_countries, list_holidays

# ─── list_holidays ──────────────────────────────────────────────────────


class TestListHolidays:
    def test_germany_2026(self):
        result = list_holidays(year=2026, country="DE")
        assert result["year"] == 2026
        assert result["country"] == "DE"
        # Germany federally recognized: New Year's, Good Friday, Easter Mon,
        # Labor Day, Ascension, Whit Monday, Unity Day, Christmas Day, 2nd Day of Christmas
        # ≈ 9 federal holidays
        assert len(result["holidays"]) >= 9

        dates = [h["date"] for h in result["holidays"]]
        assert "2026-01-01" in dates
        assert "2026-05-01" in dates
        assert "2026-10-03" in dates
        assert "2026-12-25" in dates

    def test_sorted_by_date(self):
        result = list_holidays(year=2026, country="DE")
        dates = [h["date"] for h in result["holidays"]]
        assert dates == sorted(dates)

    def test_us_2026(self):
        result = list_holidays(year=2026, country="US")
        assert result["country"] == "US"
        # US federal holidays ≈ 10 per year
        assert len(result["holidays"]) >= 10

    def test_unknown_country_raises(self):
        import pytest

        with pytest.raises(ValueError, match=r"Unknown country code:.*get_supported_countries"):
            list_holidays(year=2026, country="ZZ")


# ─── get_supported_countries ────────────────────────────────────────────


class TestGetSupportedCountries:
    def test_returns_at_least_50_countries(self):
        result = get_supported_countries()
        assert result["total"] >= 50

    def test_includes_major_countries(self):
        result = get_supported_countries()
        codes = {c["code"] for c in result["countries"]}
        for expected in ["DE", "US", "GB", "FR", "JP", "BR", "CA", "AU"]:
            assert expected in codes, f"Missing {expected}"

    def test_each_entry_has_code_and_name(self):
        result = get_supported_countries()
        for entry in result["countries"]:
            assert "code" in entry
            assert "name" in entry
            assert len(entry["code"]) == 2  # ISO 3166-1 alpha-2
            assert entry["name"]  # non-empty

    def test_name_is_human_readable_not_lazy_loader_doc(self):
        result = get_supported_countries()
        by_code = {c["code"]: c["name"] for c in result["countries"]}
        bad = "Country and financial holidays entities lazy loader."
        assert all(name != bad for name in by_code.values())
        assert "United States" in by_code["US"]
        assert "Germany" in by_code["DE"]
        assert "United Kingdom" in by_code["GB"]
        assert "Japan" in by_code["JP"]
        assert "Brazil" in by_code["BR"]
