"""Minimal tests targeting remaining coverage gaps (defensive branches & entry points)."""

from __future__ import annotations

import importlib

import pytest

from business_day_mcp import server
from business_day_mcp.server import (
    _country_display_name,
    _country_subdivisions,
    business_days_between,
    last_business_day_of_month,
    next_business_day,
    previous_business_day,
)


class TestSubdivBranchesOnNavAndAggregates:
    def test_next_business_day_with_subdiv(self):
        # 2026-01-06 is Epiphany in DE-BY; next business day skips it.
        result = next_business_day(date="2026-01-05", country="DE", subdiv="BY")
        assert result["subdiv"] == "BY"
        assert result["next_business_day"] == "2026-01-07"

    def test_previous_business_day_with_subdiv(self):
        result = previous_business_day(date="2026-01-07", country="DE", subdiv="BY")
        assert result["subdiv"] == "BY"
        assert result["previous_business_day"] == "2026-01-05"

    def test_last_business_day_of_month_with_subdiv(self):
        result = last_business_day_of_month(year=2026, month=1, country="DE", subdiv="BY")
        assert result["subdiv"] == "BY"

    def test_business_days_between_with_subdiv(self):
        result = business_days_between(
            start_date="2026-01-05", end_date="2026-01-09", country="DE", subdiv="BY"
        )
        assert result["subdiv"] == "BY"


class TestDosGuards:
    def test_step_business_day_exceeds_iteration_limit(self, monkeypatch):
        monkeypatch.setattr(server, "_MAX_STEP_ITERATIONS", 0)
        with pytest.raises(ValueError, match=r"within 10 years"):
            # 2026-05-01 Fri Labor Day (DE); next candidate is Sat → loop runs → guard trips.
            next_business_day(date="2026-05-01", country="DE")

    def test_business_days_between_span_too_large(self):
        with pytest.raises(ValueError, match=r"Date range too large"):
            business_days_between(start_date="1900-01-01", end_date="2026-01-01", country="DE")


class TestCountryDisplayNameFallbacks:
    def test_unknown_code_returns_code(self):
        # cls is None branch.
        assert _country_display_name("ZZZ") == "ZZZ"

    def test_country_name_attr_used(self, monkeypatch):
        class Fake:
            country_name = "Fakeland"

        monkeypatch.setattr(server.holidays, "XX", Fake, raising=False)
        assert _country_display_name("XX") == "Fakeland"

    def test_no_name_no_doc_returns_code(self, monkeypatch):
        class Fake:
            __doc__ = None

        monkeypatch.setattr(server.holidays, "XX", Fake, raising=False)
        assert _country_display_name("XX") == "XX"


class TestCountrySubdivisionsExceptionBranch:
    def test_exception_returns_empty(self):
        # Unknown code makes holidays.country_holidays raise.
        assert _country_subdivisions("ZZZ") == []


class TestEntryPoints:
    def test_main_invokes_mcp_run(self, monkeypatch):
        called = {}
        monkeypatch.setattr(server.mcp, "run", lambda: called.setdefault("ran", True))
        server.main()
        assert called == {"ran": True}

    def test_dunder_main_module_imports(self, monkeypatch):
        # Importing __main__ executes the top-level `from ... import main`.
        import business_day_mcp.__main__ as dunder_main

        importlib.reload(dunder_main)
