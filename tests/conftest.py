"""Shared pytest fixtures and constants."""

import pytest

# Known reference dates (German calendar 2026)
#
# 2026-01-01 Thu: New Year's Day (holiday)
# 2026-04-03 Fri: Good Friday (holiday)
# 2026-04-06 Mon: Easter Monday (holiday)
# 2026-04-21 Tue: regular business day
# 2026-05-01 Fri: Labor Day (holiday)
# 2026-05-14 Thu: Ascension Day (holiday)
# 2026-05-25 Mon: Whit Monday (holiday)
# 2026-10-03 Sat: German Unity Day (holiday on weekend)
# 2026-12-25 Fri: Christmas Day (holiday)
# 2026-12-26 Sat: Boxing Day (weekend)


@pytest.fixture
def de_business_day() -> str:
    """A known DE business day."""
    return "2026-04-21"  # Tuesday, no holiday


@pytest.fixture
def de_holiday() -> str:
    """A known DE holiday on a weekday."""
    return "2026-05-01"  # Friday, Labor Day


@pytest.fixture
def de_weekend() -> str:
    """A known weekend date."""
    return "2026-04-25"  # Saturday


@pytest.fixture
def us_business_day() -> str:
    """A known US business day."""
    return "2026-04-21"  # Tuesday


@pytest.fixture
def us_holiday() -> str:
    """A known US holiday on a weekday."""
    return "2026-07-03"  # Independence Day observed (July 4 is Saturday)
