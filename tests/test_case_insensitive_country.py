"""Principle #5: country codes are case-insensitive, uniformly across all tools."""

from __future__ import annotations

import pytest

from business_day_mcp.server import (
    business_days_between,
    is_business_day,
    last_business_day_of_month,
    list_holidays,
    next_business_day,
    previous_business_day,
)


@pytest.mark.parametrize(
    "fn,kwargs",
    [
        (is_business_day, {"date": "2026-04-21"}),
        (next_business_day, {"date": "2026-04-21"}),
        (previous_business_day, {"date": "2026-04-21"}),
        (last_business_day_of_month, {"year": 2026, "month": 4}),
        (business_days_between, {"start_date": "2026-04-20", "end_date": "2026-04-24"}),
        (list_holidays, {"year": 2026}),
    ],
)
def test_country_case_insensitive(fn, kwargs):
    lower = fn(**kwargs, country="de")
    upper = fn(**kwargs, country="DE")
    assert lower == upper
